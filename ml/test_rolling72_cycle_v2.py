"""Synthetic orchestration contracts; model/ledger semantics have separate tests."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_cycle_v2 import cycle, due_status
from ml.rolling72_paired_shadow_v2 import APPLICATION_ID, SCHEMA
from ml.rolling72_receipt_store_v1 import prepare_receipt
from ml.test_rolling72_cycle_v1 import BASE, Reader, payload


class CycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source.json'; self.source.write_bytes(payload())
        self.registry = self.root / 'registry.json'
        self.events = json.loads(payload())['events']
        self.metadata = [{'id': e['ticket_event_id'], **{k:v for k,v in e.items()
                         if k not in ('ticket_event_id','observations')}} for e in self.events]
        self.registry.write_text(json.dumps(self.metadata))
        self.freeze = self.root / 'freeze.json'; self.freeze.write_text('{}')
        self.artifact = self.root / 'private-model'; self.artifact.mkdir()
        self.database = self.root / 'v2.sqlite'
        with sqlite3.connect(self.database) as db:
            db.executescript(SCHEMA)
            db.execute(f'pragma application_id={APPLICATION_ID}')
        self.issued = BASE + timedelta(minutes=3)
        self.now = self.issued
        self._append(payload(), self.issued)
        self.runtime = self.root / 'cycle'
        self.until = BASE + timedelta(hours=96)
        self.operations = []

    def tearDown(self):
        self.tmp.cleanup()

    def _register_source(self, db, raw):
        receipt = prepare_receipt(raw, self.now)['receipt']
        sha = receipt['source_file_sha256']
        db.execute('insert or ignore into sources values (?,?)',(sha,json.dumps(receipt)))
        return sha

    def _append(self, raw, now):
        count = 0
        with sqlite3.connect(self.database) as db:
            sha = self._register_source(db,raw)
            for event in json.loads(raw)['events']:
                event_id, issued = event['ticket_event_id'], now.isoformat()
                issue = {'event':{'kickoff_at':event['kickoff_at']}}
                db.execute('insert into issues values (?,?,?,?,?,?,?,?)',
                    (event_id,issued,str(event_id),event['club_slug'],sha,issued,json.dumps(issue),'{}'))
                for h in (24,48,72):
                    for model in ('persistence','candidate'):
                        db.execute('insert into predictions values (?,?,?,?,?,?,?)',
                            (event_id,issued,h,model,(now+timedelta(hours=h)).isoformat(),1000.0,'{}'))
                        count += 1
        return {'issued_at':now.isoformat(),'input_issue_count':len(json.loads(raw)['events']),
                'numeric_forecast_count':count}

    def _capture(self, database, raw, artifactdir, freeze, registry, **kwargs):
        self.operations.append('capture')
        self.assertTrue(any(p.read_bytes()==raw for p in (self.runtime/'sources').glob('*.json')))
        return self._append(raw,self.now)

    def _score(self, database, raw, artifactdir, freeze, registry, **kwargs):
        self.operations.append('score')
        self.assertTrue(any(p.read_bytes()==raw for p in (self.runtime/'sources').glob('*.json')))
        accepted=0
        with sqlite3.connect(database) as db:
            sha=self._register_source(db,raw)
            targets=db.execute('select distinct event_id,issued_at,horizon,target_at from predictions').fetchall()
            for event_id,issued,h,target in targets:
                if target > self.now.isoformat(): continue
                identity=(event_id,issued,h)
                if db.execute('select 1 from target_matches where event_id=? and issued_at=? and horizon=?',identity).fetchone():continue
                db.execute('insert into target_matches values (?,?,?,?,?,?)',(*identity,sha,self.now.isoformat(),'{}'))
                for model in ('persistence','candidate'):
                    db.execute('insert into scores values (?,?,?,?,?,?)',(*identity,model,1.,1.))
                accepted+=1
        return {'accepted_targets':accepted,'added_scores':accepted*2}

    def _backup(self,*args,**kwargs):
        self.operations.append('backup')
        return {'read_back_verified':True,'independent_restore_verified':True}

    def run_cycle(self, now, reader=None, backup=None, **kwargs):
        self.now=now
        manifest={'manifest_sha256':'a'*64,'model_file_sha256':'b'*64}
        with ExitStack() as stack:
            stack.enter_context(patch('ml.rolling72_cycle_v2._now',side_effect=lambda:self.now))
            stack.enter_context(patch('ml.rolling72_cycle_v1._now',side_effect=lambda:self.now))
            stack.enter_context(patch('ml.rolling72_cycle_v2._load_freeze',return_value=({}, {'manifest':manifest},{},{},{})))
            stack.enter_context(patch('ml.rolling72_cycle_v2.capture',side_effect=self._capture))
            stack.enter_context(patch('ml.rolling72_cycle_v2.score',side_effect=self._score))
            stack.enter_context(patch('ml.rolling72_cycle_v2.backup',side_effect=backup or self._backup))
            stack.enter_context(patch('ml.rolling72_cycle_v2.report',return_value={'metrics':{}}))
            return cycle(self.database,self.source,self.artifact,self.registry,self.freeze,self.runtime,
                         kwargs.pop('until',self.until),reader=reader,synthetic_test=True,**kwargs)

    def test_not_due_is_local_and_preserves_other_ledger(self):
        before=self.database.read_bytes()
        with patch('ml.rolling72_cycle_v2.BoundedReader',side_effect=AssertionError('no network')):
            result=self.run_cycle(BASE+timedelta(hours=1))
        self.assertEqual(result['status'],'NOT_DUE')
        self.assertEqual(result['network_reads'],0)
        self.assertEqual(self.database.read_bytes(),before)
        self.assertEqual(self.operations,[])

    def test_due_grace_exact_and_after_kickoff_capture_disabled(self):
        before=due_status(self.database,self.issued+timedelta(hours=24,minutes=9,seconds=59))
        at=due_status(self.database,self.issued+timedelta(hours=24,minutes=10))
        self.assertFalse(before['due']);self.assertEqual(at['capture_event_ids'],[24,10500])
        self.assertEqual(len(at['mature_unmatched_targets']),2)
        after=due_status(self.database,BASE+timedelta(days=50))
        self.assertEqual(after['capture_event_ids'],[])

    def test_positive_cycle_orders_source_score_capture_backup_and_keeps_raw(self):
        now=self.issued+timedelta(hours=24,minutes=11)
        reader=Reader(self.metadata)
        result=self.run_cycle(now,reader)
        self.assertEqual(result['status'],'SUCCESS')
        self.assertEqual(result['network_reads'],3)
        self.assertEqual(self.operations,['score','capture','backup'])
        self.assertEqual(result['scoring']['accepted_targets'],2)
        self.assertEqual(result['capture']['issued_at'],now.isoformat())
        self.assertTrue(result['backup']['independent_restore_verified'])
        self.assertTrue((self.runtime/'current-report.json').exists())
        state=json.loads((self.runtime/'state.json').read_text())
        self.assertEqual(state['checkpoint']['issues'],4)
        self.assertEqual(state['checkpoint']['scores'],4)
        for _,parameters in reader.calls[1:]:
            self.assertEqual(dict(parameters)['limit'],'500')
            self.assertTrue(dict(parameters)['id'].startswith('gt.'))

    def test_failed_read_throttles_even_explicit_first_capture(self):
        metadata=deepcopy(self.metadata);metadata[0]['external_event_id']='wrong'
        reader=Reader(metadata)
        failed=self.run_cycle(BASE+timedelta(hours=1),reader,capture_now=True)
        self.assertEqual(failed['status'],'FAILED_CLOSED')
        retry=self.run_cycle(BASE+timedelta(hours=1,minutes=1),reader,capture_now=True)
        self.assertEqual(retry['status'],'RETRY_INTERVAL_NOT_DUE')
        self.assertEqual(len(reader.calls),1)
        self.assertEqual(self.operations,[])

    def test_cap_and_future_snapshot_never_touch_ledger(self):
        now=BASE+timedelta(hours=1)
        reader=Reader(self.metadata,{24:[{}]*500})
        result=self.run_cycle(now,reader,capture_now=True)
        self.assertEqual(result['status'],'FAILED_CLOSED')
        self.assertEqual(self.operations,[])
        with sqlite3.connect(self.database) as db:self.assertEqual(db.execute('select count(*) from issues').fetchone()[0],2)

    def test_committed_write_backup_failure_recovers_without_repoll(self):
        def fail(*args,**kwargs):raise ValueError('private raw error')
        now=BASE+timedelta(hours=1)
        failed=self.run_cycle(now,Reader(self.metadata),backup=fail,capture_now=True)
        self.assertEqual(failed['failure_stage'],'private_backup')
        self.operations=[]
        with patch('ml.rolling72_cycle_v2.BoundedReader',side_effect=AssertionError('no network')):
            recovered=self.run_cycle(now+timedelta(minutes=1))
        self.assertEqual(recovered['status'],'RECOVERED_COMMITTED_LEDGER')
        self.assertEqual(self.operations,['backup'])
        self.assertEqual(recovered['network_reads'],0)
        self.assertNotIn('private raw error',(self.runtime/'state.json').read_text())

    def test_changed_source_model_or_deadline_cannot_rebind_runtime(self):
        self.run_cycle(BASE+timedelta(hours=1))
        with self.assertRaisesRegex(ValueError,'contract changed'):
            self.run_cycle(BASE+timedelta(hours=1,minutes=1),until=self.until-timedelta(hours=1))
        self.source.write_bytes(self.source.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'contract changed'):
            self.run_cycle(BASE+timedelta(hours=1,minutes=1))

    def test_expired_and_oversized_deadlines_never_access_source(self):
        result=self.run_cycle(self.until)
        self.assertEqual(result['status'],'DEADLINE_EXPIRED')
        self.assertEqual(result['network_reads'],0)
        with self.assertRaisesRegex(ValueError,'within96hours'):
            self.run_cycle(BASE,until=BASE+timedelta(hours=97))

    def test_deadline_during_read_blocks_score_and_capture(self):
        now=BASE+timedelta(hours=1);until=now+timedelta(minutes=1)
        reader=Reader(self.metadata,callback=lambda table:setattr(self,'now',until))
        result=self.run_cycle(now,reader,capture_now=True,until=until)
        self.assertEqual(result['status'],'FAILED_CLOSED')
        self.assertEqual(self.operations,[])

    def test_deadline_crossed_by_score_never_issues_new_forecast(self):
        now=BASE+timedelta(hours=1);until=now+timedelta(minutes=1)
        original_score=self._score
        def crosses(*args,**kwargs):
            result=original_score(*args,**kwargs)
            self.now=until
            return result
        self._score=crosses
        result=self.run_cycle(now,Reader(self.metadata),capture_now=True,until=until)
        self.assertEqual(result['status'],'FAILED_CLOSED')
        self.assertEqual(result['failure_stage'],'capture')
        self.assertEqual(self.operations,['score'])

    def test_foreign_v1_ledger_rejected_before_source(self):
        with sqlite3.connect(self.database) as db:db.execute('pragma application_id=1379355697')
        with self.assertRaisesRegex(ValueError,'own rolling72 ledger'):
            self.run_cycle(BASE+timedelta(hours=1),Reader(self.metadata),capture_now=True)


class PairedCycleIntegrationTests(unittest.TestCase):
    """Real synthetic fitted model + ledger + independent recovery in one cycle."""
    @classmethod
    def setUpClass(cls):
        from ml.test_rolling72_backup_v2 import Rolling72V2RecoveryTests
        cls.fixture_type=Rolling72V2RecoveryTests
        cls.fixture_type.setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.fixture_type.tearDownClass()

    def test_actual_synthetic_cycle_scores_three_models_before_next_issue_and_restore(self):
        from threadpoolctl import threadpool_limits
        from ml.test_rolling72_backup_v2 import MemoryStorage
        from ml.rolling72_paired_shadow_v2 import report
        fixture=self.fixture_type(methodName='test_full_restore_keeps_model_and_original_sources_without_deserializing')
        fixture.setUp()
        try:
            issued=fixture.base+timedelta(minutes=3)
            target=issued+timedelta(hours=24)
            now=target+timedelta(minutes=11)
            data=json.loads(fixture.source.read_bytes())
            event=data['events'][0]
            metadata=[{**json.loads(fixture.registry.read_text())[0],
                       'kickoff_at':event['kickoff_at'],'competition':'synthetic',
                       'home_team':'club','away_team':'visitor'}]
            rows={999:[{'id':identifier,'ticket_event_id':999,'captured_at':at.isoformat(),
                        'available_total':value,'source':'roboticket','sector_count':2}
                       for identifier,at,value in ((90005,target-timedelta(minutes=1),800),
                                                   (90006,now-timedelta(minutes=1),790))]}
            reader=Reader(metadata,rows)
            with ExitStack() as stack:
                for module in ('ml.rolling72_cycle_v2','ml.rolling72_cycle_v1',
                               'ml.rolling72_paired_shadow_v2','ml.rolling72_offline_challenger_v2',
                               'ml.rolling72_backup_v2'):
                    stack.enter_context(patch(module+'._now',return_value=now))
                stack.enter_context(threadpool_limits(limits=1))
                result=cycle(fixture.ledger,fixture.source,fixture.artifact,fixture.registry,fixture.freeze,
                             fixture.root/'cycle',now+timedelta(hours=48),reader=reader,
                             storage=MemoryStorage(),synthetic_test=True)
                summary=report(fixture.ledger)
            self.assertEqual(result['status'],'SUCCESS',result)
            self.assertEqual(result['network_reads'],2)
            self.assertEqual(result['scoring']['accepted_targets'],1)
            self.assertEqual(result['scoring']['added_scores'],3)
            self.assertEqual(result['capture']['numeric_forecast_count'],9)
            self.assertTrue(result['backup']['independent_restore_verified'])
            self.assertTrue(result['backup']['model_bytes_verified_without_loading'])
            self.assertEqual(summary['issues'],2)
            self.assertEqual(summary['numeric_forecasts'],18)
            self.assertEqual(summary['scores'],3)
            self.assertIsNotNone(summary['paired_metrics']['+24h/candidate-vs-persistence']['candidate']['event_balanced_mae'])
        finally:
            fixture.tearDown()


if __name__ == '__main__':
    unittest.main()
