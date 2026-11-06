from datetime import timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

from ml.run_postmatch_outcome_closure_v1 import due_slot,dispatch,tick,SLOTS,stamp,find_run,apply_verified,score_support_only
from ml.test_postmatch_outcome_source_v1 import inputs,staged,NOW


class ClosureScheduleTests(unittest.TestCase):
    def test_outside_opportunity_uses_no_remote_call_and_no_database(self):
        with tempfile.TemporaryDirectory() as temp:
            github=Mock();apply=Mock();score=Mock()
            result=tick(Path(temp),{}, {'branch':'research','commit':'a'*40},stamp('2026-11-06T13:00:00Z'),github,apply,score)
            self.assertIsNone(result['due_dispatch']);github.assert_not_called();apply.assert_not_called();score.assert_not_called()

    def test_missed_retrieval_slot_is_never_backfilled(self):
        self.assertIsNone(due_slot(stamp(SLOTS[0])+timedelta(minutes=31),{}))
        self.assertEqual(due_slot(stamp(SLOTS[1]),{}),SLOTS[1])

    def test_intent_precedes_dispatch_and_unknown_response_is_not_retried(self):
        state={};persisted=[]
        def github(path,body=None):
            if body is None:return {'object':{'sha':'a'*40}}
            self.assertEqual(persisted[0]['dispatches'][SLOTS[0]]['status'],'DISPATCH_INTENT_RECORDED')
            raise TimeoutError('unknown remote acceptance')
        with self.assertRaises(TimeoutError):dispatch(state,SLOTS[0],'research','a'*40,stamp(SLOTS[0]),lambda s:persisted.append(json.loads(json.dumps(s))),github)
        with self.assertRaises(ValueError):dispatch(state,SLOTS[0],'research','a'*40,stamp(SLOTS[0]),lambda s:None,github)

    def test_source_branch_substitution_prevents_dispatch(self):
        state={};github=Mock(return_value={'object':{'sha':'b'*40}})
        with self.assertRaises(ValueError):dispatch(state,SLOTS[0],'research','a'*40,stamp(SLOTS[0]),lambda s:None,github)
        self.assertEqual(state,{})

    def test_ambiguous_action_runs_are_not_chosen(self):
        entry={'branch':'research','commit':'a'*40,'intent_at':SLOTS[0]}
        run={'head_sha':'a'*40,'created_at':SLOTS[0],'status':'completed','conclusion':'success'}
        with self.assertRaises(ValueError):find_run(entry,lambda path:{'workflow_runs':[run,run]})

    def test_expired_action_watch_does_not_poll_forever(self):
        with tempfile.TemporaryDirectory() as temp:
            state={'dispatches':{SLOTS[0]:{'status':'DISPATCH_ACCEPTED','intent_at':SLOTS[0]}}};github=Mock()
            tick(Path(temp),state,{'branch':'research','commit':'a'*40},stamp(SLOTS[0])+timedelta(minutes=41),github)
            github.assert_not_called();self.assertEqual(state['dispatches'][SLOTS[0]]['status'],'RUN_NOT_PROVEN_WITHIN_BUDGET')


class ClosureApplyTests(unittest.TestCase):
    def test_pregame_sources_cannot_write_or_sync_outcomes(self):
        sources,raw,events,sporting=inputs();reader=Mock()
        reader.counted.side_effect=[events,[],sporting,[],[]]
        with tempfile.TemporaryDirectory() as temp,patch('ml.run_postmatch_outcome_closure_v1.datetime') as clock,patch('ml.run_postmatch_outcome_closure_v1.urllib.request.urlopen') as post:
            clock.now.return_value=stamp('2026-11-06T13:00:00Z')
            result=apply_verified(Path(temp),{'id':123},sources,raw,reader)
            self.assertEqual(result['appended_rows'],0);self.assertEqual(result['actual_target_outcomes'],0)
            post.assert_not_called();reader.request.assert_not_called()

    def test_positive_append_is_insert_only_read_back_and_old_rows_preserved(self):
        sources,raw,events,sporting=inputs();reader=Mock(base='https://project.invalid',headers={})
        planned=staged(now=stamp(NOW).isoformat())['rows']
        inserted=[{**row,'id':i+100,'created_at':stamp(NOW).isoformat(),'updated_at':stamp(NOW).isoformat()} for i,row in enumerate(planned)]
        old={'id':1,'club_slug':'motorlublin','kickoff_at':'2026-10-01T17:00:00Z','actual_attendance':1000}
        reader.counted.side_effect=[events,[old],sporting,[],[old,*inserted],[]]
        reader.request.return_value=0
        response=Mock(status=201);response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        response.read.return_value=json.dumps(inserted).encode()
        with tempfile.TemporaryDirectory() as temp,patch('ml.run_postmatch_outcome_closure_v1.datetime') as clock,patch('ml.run_postmatch_outcome_closure_v1.urllib.request.urlopen',return_value=response) as post:
            clock.now.return_value=stamp(NOW)
            result=apply_verified(Path(temp),{'id':123},sources,raw,reader)
            self.assertEqual(result['appended_rows'],2)
            request=post.call_args.args[0];self.assertEqual(request.method,'POST')
            self.assertEqual(request.get_header('Prefer'),'return=representation')
            self.assertNotIn('resolution=merge-duplicates',str(request.headers))
            reader.request.assert_called_once_with('rpc/sync_ticket_event_outcomes_from_home_history_v1',{})

    def test_existing_outcome_conflict_prevents_any_append(self):
        sources,raw,events,sporting=inputs();reader=Mock()
        reader.counted.side_effect=[events,[],sporting,[{'ticket_event_id':5091,'actual_attendance':1,'confirmed_at':'2026-11-06T20:10:00Z'}]]
        with tempfile.TemporaryDirectory() as temp,patch('ml.run_postmatch_outcome_closure_v1.datetime') as clock,patch('ml.run_postmatch_outcome_closure_v1.urllib.request.urlopen') as post:
            clock.now.return_value=stamp(NOW)
            with self.assertRaises(ValueError):apply_verified(Path(temp),{'id':123},sources,raw,reader)
            post.assert_not_called();reader.request.assert_not_called()

    def test_active_support_collector_lock_is_never_bypassed(self):
        import fcntl
        with tempfile.TemporaryDirectory() as temp:
            runtime=Path(temp)
            with (runtime/'cycle.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with patch('ml.export_c1_matched_audit_inputs_v1.Reader') as reader:
                    result=score_support_only(runtime)
                    self.assertEqual(result['status'],'DELEGATED_TO_ACTIVE_FROZEN_COLLECTOR');reader.assert_not_called()


if __name__=='__main__':unittest.main()
