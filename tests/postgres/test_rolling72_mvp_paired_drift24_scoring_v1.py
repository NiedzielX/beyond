"""Shared-outcome regressions in a second, dedicated synthetic PostgreSQL DB.

Past rows are explicit test fixtures, never production forecasts or substituted
runtime clocks. The actual scorer still chooses its own database watermark.
"""
from datetime import timedelta
import importlib.util
import os
from pathlib import Path
import unittest
from urllib.parse import urlparse
import uuid

import psycopg
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[2]
PREFIX = 'rolling72_mvp_paired_drift24_v1'

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

Fixtures = _load('paired_runtime_fixture_for_scoring', ROOT / 'tests/postgres/test_rolling72_mvp_paired_drift24_v1.py')
OldFixtures = _load('pers_unknown_fixture_for_scoring', ROOT / 'tests/postgres/test_rolling72_mvp_persistence_v1.py')

class PairedDrift24Scoring(Fixtures.Rolling72MvpPairedDrift24V1):
    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get('ROLLING72_MVP_PAIRED_DRIFT24_SCORING_TEST_DSN', '')
        target = urlparse(dsn)
        if (target.hostname not in {'127.0.0.1', 'localhost'} or target.port != 55440
                or target.path != '/rolling72_mvp_paired_drift24_scoring_test'):
            raise RuntimeError('Only the dedicated localhost paired scoring test DB is allowed')
        cls.dsn = dsn
        cls.db = psycopg.connect(dsn, autocommit=True)
        if not 160000 <= int(cls.db.execute('show server_version_num').fetchone()[0]) < 170000:
            raise RuntimeError('PostgreSQL16 required')
        cls._bootstrap_parent_schema()

    _synthetic_unknown_capture_attempt = OldFixtures.Rolling72MvpPersistenceV1._synthetic_unknown_capture_attempt

    def _past_source(self, admission, *, captured, known, value, status='READY', snapshot=None, sectors=None):
        if snapshot is None:
            snapshot = self._insert_bundle(admission, available=value, captured_at=captured, sectors=sectors)
        payload = self.db.execute("""
          select jsonb_build_object('lane_id','rolling72-mvp-research-v1',
            'source_family','roboticket/roboticket','unit','available_total_seats',
            'admission',to_jsonb(a),'binding',r.binding,'snapshot',to_jsonb(s),
            'sector_price_area_rows',(select jsonb_agg(to_jsonb(x) order by x.sector_source_id,x.price_area_id,x.id)
                from public.sector_price_area_observations_v1 x where x.snapshot_id=s.id),
            'sector_inventory_rows',(select jsonb_agg(to_jsonb(x) order by x.sector,x.available,x.id)
                from public.sector_inventory x where x.snapshot_id=s.id))
          from private.rolling72_mvp_research_v1_registry r
          join private.roboticket_admission_receipts_v2 a on a.id=r.admission_receipt_id
          join public.snapshots s on s.ticket_event_id=r.ticket_event_id
          where s.id=%s and r.ticket_event_id=%s
        """, (snapshot, admission['ticket_event_id'])).fetchone()[0]
        run = uuid.uuid4()
        self.db.execute("insert into private.rolling72_mvp_research_v1_runs values(%s,%s,%s,'COMPLETED',1,1)", (run,known,known))
        attempt = self.db.execute("select nextval(pg_get_serial_sequence('private.rolling72_mvp_research_v1_attempts','id'))").fetchone()[0]
        digest, header = self.db.execute("select private.rolling72_mvp_research_v1_hash(%s),private.rolling72_mvp_research_v1_hash(%s)", (Jsonb(payload),Jsonb(payload['snapshot']))).fetchone()
        binding = self.db.execute("""select jsonb_build_object('attempt_id',%s,'run_id',%s,
          'lane_id','rolling72-mvp-research-v1','ticket_event_id',%s,'snapshot_id',%s,
          'source_content_sha256',%s::text,'read_started_at',%s,'read_completed_at',%s,
          'known_at',%s,'status',%s::text,'reason',null)""",
          (attempt,run,admission['ticket_event_id'],snapshot,digest,captured-timedelta(seconds=1),captured,known,status)).fetchone()[0]
        binding_hash = self.db.execute('select private.rolling72_mvp_research_v1_hash(%s)',(Jsonb(binding),)).fetchone()[0]
        self.db.execute("""insert into private.rolling72_mvp_research_v1_attempts
          (id,run_id,ticket_event_id,snapshot_id,read_started_at,read_completed_at,known_at,captured_at,status,
           reason,source_content_sha256,snapshot_sha256,attempt_binding_sha256,raw_source,binding_payload)
          overriding system value values(%s,%s,%s,%s,%s,%s,%s,%s,%s,null,%s,%s,%s,%s,%s)""",
          (attempt,run,admission['ticket_event_id'],snapshot,captured-timedelta(seconds=1),captured,known,captured,status,digest,header,binding_hash,Jsonb(payload),Jsonb(binding)))
        seal = None
        if status == 'READY':
            seal = self.db.execute("""insert into private.rolling72_mvp_research_v1_seals
              (ticket_event_id,snapshot_id,attempt_id,captured_at,read_started_at,read_completed_at,known_at,
               available_total,sector_count,source_content_sha256,snapshot_sha256,source_payload,phase,
               prior_seal_id,prior_status,transition_status,gap_count,transition)
              values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'ISSUE_WINDOW',null,'NO_PRIOR','NO_PRIOR',0,'{}') returning id""",
              (admission['ticket_event_id'],snapshot,attempt,captured,captured-timedelta(seconds=1),captured,known,value,
               payload['snapshot']['sector_count'],digest,header,Jsonb(payload))).fetchone()[0]
        return {'snapshot':snapshot,'seal':seal,'attempt':attempt,'captured':captured,'known':known,'value':value}

    def _past_pair(self, *, actual=0, label_age=1, issue_age=27, admission=None, origin_value=41, label_sectors=None):
        if admission is None:
            admission = self._admit_fixture(kickoff_in_days=20)
            self._register(admission)
        now = self.db.execute('select clock_timestamp()').fetchone()[0]
        issued = now-timedelta(hours=issue_age)
        captured = issued-timedelta(seconds=3)
        origin = self._past_source(admission,captured=captured,known=issued-timedelta(seconds=1),value=origin_value)
        anchor = self._past_source(admission,captured=captured-timedelta(hours=24),known=captured-timedelta(hours=24)+timedelta(seconds=1),value=origin_value+24)
        ref,calc = issued-timedelta(milliseconds=2),issued-timedelta(milliseconds=1)
        bundle = self.db.execute(f"""insert into private.{PREFIX}_issue_bundles
          (seal_id,ticket_event_id,source_known_at,source_captured_at,projection_reference_at,calculation_completed_at,
           issued_at,issue_latency_seconds,source_age_seconds,kickoff_at,origin_available_total,source_content_sha256,
           origin_sector_count,origin_membership,origin_membership_sha256,origin_transition_status,origin_transition,
           anchor_seal_id,anchor_captured_at,anchor_known_at,anchor_available_total,anchor_sector_count,anchor_membership,
           anchor_membership_sha256,anchor_transition_status,anchor_transition,drift_status,fallback_reason,slope24,age_hours,history_input_sha256)
          select s.id,s.ticket_event_id,s.known_at,s.captured_at,%s,%s,%s,
           extract(epoch from %s::timestamptz-%s::timestamptz),extract(epoch from %s::timestamptz-s.captured_at),r.kickoff_at,s.available_total,s.source_content_sha256,
           s.sector_count,private.{PREFIX}_membership(s.source_payload),private.{PREFIX}_hash(private.{PREFIX}_membership(s.source_payload)),s.transition_status,s.transition,
           a.id,a.captured_at,a.known_at,a.available_total,a.sector_count,private.{PREFIX}_membership(a.source_payload),
           private.{PREFIX}_hash(private.{PREFIX}_membership(a.source_payload)),a.transition_status,a.transition,'READY',null,-1,
           extract(epoch from %s::timestamptz-s.captured_at)/3600.0,repeat('a',64)
          from private.rolling72_mvp_research_v1_seals s
          join private.rolling72_mvp_research_v1_registry r on r.ticket_event_id=s.ticket_event_id
          cross join private.rolling72_mvp_research_v1_seals a
          where s.id=%s and a.id=%s returning id""",
          (ref,calc,issued,issued,ref,issued,ref,origin['seal'],anchor['seal'])).fetchone()[0]
        for h in (24,48,72):
            for method in ('PERS','DRIFT24'):
                value = origin_value if method=='PERS' else max(0,origin_value-(h+(ref-captured).total_seconds()/3600))
                self.db.execute(f"""insert into private.{PREFIX}_predictions
                  (bundle_id,ticket_event_id,horizon_hours,method,issued_at,target_at,kickoff_at,status,prediction,
                   fallback_reason,origin_available_total,source_seal_id,source_content_sha256)
                  select %s,r.ticket_event_id,%s,%s,%s,%s,r.kickoff_at,'READY',%s,null,%s,s.id,s.source_content_sha256
                  from private.rolling72_mvp_research_v1_registry r cross join private.rolling72_mvp_research_v1_seals s
                  where r.ticket_event_id=%s and s.id=%s""",
                  (bundle,h,method,issued,issued+timedelta(hours=h),value,origin_value,admission['ticket_event_id'],origin['seal']))
        target = issued+timedelta(hours=24)
        label = self._past_source(admission,captured=target-timedelta(hours=label_age),known=target-timedelta(hours=label_age)+timedelta(seconds=1),value=actual,sectors=label_sectors)
        return {'bundle':bundle,'admission':admission,'issued':issued,'label':label,'target':target}

    def _score(self, limit=100):
        return self._rpc('score_rolling72_mvp_paired_drift24_v1',limit)

    def _latest_status(self, bundle):
        return self.db.execute(f'select status from private.{PREFIX}_score_attempts where bundle_id=%s order by id desc limit 1',(bundle,)).fetchone()[0]

    def test_shared_zero_label_different_method_errors_and_immutable_retry(self):
        f=self._past_pair(actual=0)
        self.assertEqual(self._score()['labels'],1)
        row=self.db.execute(f'select actual_available_total,pers_absolute_error,drift24_absolute_error,target_seal_id from private.{PREFIX}_labels').fetchone()
        self.assertEqual(row[0],0); self.assertEqual(row[1],41); self.assertLess(row[2],row[1]); self.assertEqual(row[3],f['label']['seal'])
        self.assertEqual(self._score()['labels'],0)
        for suffix in ('lane','runs','issue_bundles','predictions','issue_attempts','labels','score_attempts'):
            with self.assertRaises(psycopg.Error):
                self.db.execute(f'truncate private.{PREFIX}_{suffix} cascade')
        with self.assertRaises(psycopg.Error):
            self.db.execute(f'update private.{PREFIX}_labels set actual_available_total=1')

    def test_latest_invalid_snapshot_does_not_backtrack(self):
        f=self._past_pair()
        cap=f['label']['captured']+timedelta(minutes=10)
        self._past_source(f['admission'],captured=cap,known=cap+timedelta(seconds=1),value=1,status='INVALID_SOURCE')
        self.assertEqual(self._score()['labels'],0); self.assertEqual(self._latest_status(f['bundle']),'SOURCE_INVALID')

    def test_latest_attempt_on_same_snapshot_precedes_validation(self):
        f=self._past_pair()
        self._past_source(f['admission'],captured=f['label']['captured'],known=f['label']['known']+timedelta(minutes=1),value=0,status='INVALID_SOURCE',snapshot=f['label']['snapshot'])
        self.assertEqual(self._score()['labels'],0); self.assertEqual(self._latest_status(f['bundle']),'SOURCE_INVALID')

    def test_identical_no_new_source_resolves_one_ready_seal(self):
        f=self._past_pair()
        self._past_source(f['admission'],captured=f['label']['captured'],known=f['label']['known']+timedelta(minutes=1),value=0,status='NO_NEW_SOURCE',snapshot=f['label']['snapshot'])
        self.assertEqual(self._score()['labels'],1)
        self.assertEqual(self.db.execute(f'select target_seal_id,source_status from private.{PREFIX}_labels').fetchone(),(f['label']['seal'],'NO_NEW_SOURCE'))

    def test_unknown_capture_refuses_an_older_ready_label(self):
        f=self._past_pair()
        self._synthetic_unknown_capture_attempt(f['admission'],known_at=f['label']['known']+timedelta(minutes=1))
        self.assertEqual(self._score()['labels'],0); self.assertEqual(self._latest_status(f['bundle']),'SOURCE_ORDER_UNKNOWN')

    def test_target_age_after_target_and_six_hour_boundary(self):
        stale=self._past_pair(label_age=7)
        edge=self._past_pair(label_age=6)
        after=self._past_pair(label_age=-1)
        self.assertEqual(self._score()['labels'],1)
        self.assertEqual(self._latest_status(stale['bundle']),'SOURCE_STALE')
        self.assertEqual(self._latest_status(edge['bundle']),'SCORED')
        self.assertEqual(self._latest_status(after['bundle']),'WAITING')

    def test_equal_event_weight_and_mature_only_scoring_coverage_export(self):
        self._past_pair(actual=0,origin_value=10)
        f=self._past_pair(actual=0,origin_value=100)
        self._past_pair(actual=0,origin_value=100,admission=f['admission'],issue_age=28)
        self.assertEqual(self._score()['labels'],3)
        status=self._rpc('get_rolling72_mvp_paired_drift24_v1_status')
        card=status['scorecards'][0]
        self.assertEqual(card['pers_event_balanced_mae'],55)
        self.assertEqual(card['accepted_common_labels'],3); self.assertEqual(card['matured_eligible_targets'],3)
        self.assertEqual(card['scoring_coverage'],1)
        self.assertIsNone(status['scorecards'][1]['scoring_coverage'])
        export=self.db.execute((ROOT/'supabase/ops/rolling72_mvp_paired_drift24_v1_scorecard_export.sql').read_text()).fetchone()[0]
        self.assertEqual(export['accepted_shared_labels'],3); self.assertEqual(len(export['rows']),3)
        self.assertEqual(set(export['rows'][0]),{'bundle_id','ticket_event_id','club_id','horizon_hours','actual','pers_prediction','drift24_prediction'})

    def test_score_limit_counts_targets(self):
        self._past_pair(); self._past_pair()
        result=self._score(1)
        self.assertEqual(result['processed'],1); self.assertEqual(result['labels'],1)
        self.assertEqual(self._score(1)['labels'],1)

    def test_valid_changed_scope_is_scored_and_flagged(self):
        self._past_pair(actual=5,label_sectors=[(99999,'Changed sector',5)])
        self.assertEqual(self._score()['labels'],1)
        row=self.db.execute(f'''select actual_available_total,origin_membership_changed,
          origin_sector_count_delta from private.{PREFIX}_labels''').fetchone()
        self.assertEqual(row,(5,True,0))
        card=self._rpc('get_rolling72_mvp_paired_drift24_v1_status')['scorecards'][0]
        self.assertEqual(card['accepted_common_labels'],1)
        self.assertEqual(card['changed_scope_labels'],1)
        self.assertEqual(card['stable_scope_sensitivity']['labels'],0)

    def test_real_capture_issue_with_past_anchor_keeps_future_targets_unscored(self):
        admission=self._admit_fixture(kickoff_in_days=20)
        self._register(admission)
        now=self.db.execute('select clock_timestamp()').fetchone()[0]
        anchor=self._past_source(admission,captured=now-timedelta(hours=25),
                                 known=now-timedelta(hours=25)+timedelta(seconds=1),value=65)
        snapshot=self._insert_bundle(admission,available=41)
        self._capture()
        result=self._rpc('issue_rolling72_mvp_paired_drift24_v1',25)
        self.assertEqual(result['processed_bundles'],1,result)
        bundle=self.db.execute(f'''select id,projection_reference_at,source_captured_at,
          anchor_captured_at,calculation_completed_at,issued_at,drift_status,anchor_seal_id
          from private.{PREFIX}_issue_bundles''').fetchone()
        self.assertEqual(bundle[6:8],('READY',anchor['seal']))
        self.assertLess(bundle[4],bundle[5])
        slope=(41-65)/((bundle[2]-bundle[3]).total_seconds()/3600)
        age=(bundle[1]-bundle[2]).total_seconds()/3600
        rows=self.db.execute(f'''select horizon_hours,prediction,target_at from private.{PREFIX}_predictions
          where method='DRIFT24' order by horizon_hours''').fetchall()
        for horizon,prediction,target in rows:
            self.assertAlmostEqual(prediction,max(0,41+slope*(horizon+age)),places=10)
            self.assertEqual(target,bundle[5]+timedelta(hours=horizon))
        self.assertEqual(self._score()['labels'],0)
        status=self._rpc('get_rolling72_mvp_paired_drift24_v1_status')
        for card in status['scorecards']:
            self.assertEqual(card['forecast_coverage'],1)
            self.assertEqual(card['future_targets'],1)
            self.assertIsNone(card['scoring_coverage'])
            self.assertIsNone(card['pers_event_balanced_mae'])

    def test_own_source_transaction_defers_then_retries_after_commit(self):
        admission=self._admit_fixture(kickoff_in_days=20)
        self._register(admission)
        self._insert_bundle(admission,available=0)
        self.db.execute('begin')
        try:
            self._capture()
            deferred=self._rpc('issue_rolling72_mvp_paired_drift24_v1',25)
            self.assertEqual(deferred['processed_bundles'],0)
            self.assertEqual(deferred['results'][0]['status'],'DEFERRED')
            self.db.execute('commit')
        except BaseException:
            self.db.execute('rollback')
            raise
        issued=self._rpc('issue_rolling72_mvp_paired_drift24_v1',25)
        self.assertEqual(issued['processed_bundles'],1,issued)
        counts=dict(self.db.execute(f'select status,count(*) from private.{PREFIX}_issue_attempts group by status').fetchall())
        self.assertEqual(counts,{'DEFERRED':3,'ISSUED':3})
        self.assertEqual(self._rpc('issue_rolling72_mvp_paired_drift24_v1',25)['processed_bundles'],0)

# Exclude the imported suite while keeping its fixture setup and guards.
for _name in dir(Fixtures.Rolling72MvpPairedDrift24V1):
    if _name.startswith('test_'):
        setattr(PairedDrift24Scoring,_name,None)

if __name__=='__main__':
    unittest.main()
