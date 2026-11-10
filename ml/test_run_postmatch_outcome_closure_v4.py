from datetime import timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

from ml import run_postmatch_outcome_closure_v4 as closure
from ml.test_postmatch_outcome_source_v4 import PROFILE,NOW,inputs,staged
from ml.postmatch_outcome_source_v4 import stamp


class ForwardClosureTests(unittest.TestCase):
    def test_local_no_window_check_does_not_call_remote_or_database(self):
        profile,*_=inputs();github=Mock();apply=Mock();scorer=Mock()
        with tempfile.TemporaryDirectory() as temp:
            r=closure.tick(Path(temp),{}, {'branch':'fixed','commit':'a'*40},stamp('2026-11-07T12:00:00Z'),profile,PROFILE,github,apply,scorer)
        self.assertIsNone(r['due_dispatch']);github.assert_not_called();apply.assert_not_called();scorer.assert_not_called()

    def test_missed_or_duplicate_slots_are_not_backfilled(self):
        p,*_=inputs();first=p['slots'][0]
        self.assertIsNone(closure.due_slot(stamp(first)+timedelta(minutes=31),{},p))
        state={'dispatches':{first:{'status':'DISPATCH_INTENT_RECORDED'}}}
        with self.assertRaises(ValueError):closure.dispatch(state,first,'fixed','a'*40,stamp(first),lambda x:None,p,PROFILE)

    def test_profile_path_dispatch_is_intent_first_and_unknown_acceptance_not_retried(self):
        p,*_=inputs();state={};stored=[]
        def github(path,body=None):
            if body is None:return {'object':{'sha':'a'*40}}
            self.assertEqual(body['inputs'],{'forward_outcome_contract':PROFILE})
            self.assertEqual(stored[0]['dispatches'][p['slots'][0]]['status'],'DISPATCH_INTENT_RECORDED')
            raise TimeoutError('unknown dispatch response')
        with self.assertRaises(TimeoutError):closure.dispatch(state,p['slots'][0],'fixed','a'*40,stamp(p['slots'][0]),lambda x:stored.append(json.loads(json.dumps(x))),p,PROFILE,github)
        self.assertIsNone(closure.due_slot(stamp(p['slots'][0]),state,p))

    def test_positive_append_preserves_verification_inputs_and_scopes_new_fixture_ids(self):
        p,sources,raw,events,sporting=inputs();reader=Mock(base='https://synthetic.invalid',headers={})
        planned=staged(p,sources,raw,events,sporting,now=stamp(NOW).isoformat())['rows']
        inserted=[{**r,'id':i+100,'created_at':stamp(NOW).isoformat(),'updated_at':stamp(NOW).isoformat()} for i,r in enumerate(planned)]
        reader.counted.side_effect=[events,[],sporting,[],inserted,[]];reader.request.return_value=0
        response=Mock(status=201);response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False);response.read.return_value=json.dumps(inserted).encode()
        with tempfile.TemporaryDirectory() as temp,patch.object(closure,'datetime') as clock,patch.object(closure.urllib.request,'urlopen',return_value=response) as post:
            clock.now.return_value=stamp(NOW);r=closure.apply_verified(Path(temp),{'id':123},sources,raw,p,reader)
            self.assertEqual(r['appended_rows'],2);self.assertTrue((Path(temp)/'verification-inputs.json').exists())
            self.assertIn('449,7372',str(reader.counted.call_args_list[0]));self.assertEqual(post.call_args.args[0].method,'POST')
            reader.request.assert_called_once_with('rpc/sync_ticket_event_outcomes_from_home_history_v1',{})

    def test_source_recovery_happens_before_any_scoring_and_survives_scorer_failure(self):
        p,sources,raw,*_=inputs();order=[]
        with tempfile.TemporaryDirectory() as temp:
            state={'dispatches':{p['slots'][0]:{'status':'DISPATCH_ACCEPTED','intent_at':p['slots'][0],'branch':'fixed','commit':'a'*40}}}
            run={'id':123};apply=Mock(return_value={'actual_target_outcomes':1})
            def backup(folder):order.append('backup');return {'verified':True}
            def scorer():order.append('score');raise ValueError('immutable score conflict')
            with patch.object(closure,'find_run',return_value=(run,sources,raw)):
                with self.assertRaises(ValueError):closure.tick(Path(temp),state,{'branch':'fixed','commit':'a'*40},stamp(p['slots'][0])+timedelta(minutes=2),p,PROFILE,Mock(),apply,scorer,backup)
            self.assertEqual(order,['backup','score']);self.assertEqual(state['dispatches'][p['slots'][0]]['status'],'APPLY_INTENT_RECORDED')


if __name__=='__main__':unittest.main()
