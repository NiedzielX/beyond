from copy import deepcopy
from datetime import datetime,timezone,timedelta
import unittest
from ml import structural_prior_window_guardian_v1 as guard

NOW=datetime(2026,11,5,17,tzinfo=timezone.utc)
def row(event=5091,**changes):
    return {'ticket_event_id':event,'horizon':'T-1','target_as_of_at':'2026-11-05T17:00:00Z',
            'kickoff_at':'2026-11-06T17:00:00Z','input_status':'ready',**changes}

class API:
    def __init__(self,rows=None,active=False,main=guard.MAIN,fail=False):self.rows=rows if rows is not None else [row()];self.running=active;self.main=main;self.fail=fail;self.calls=[]
    def due(self,now):self.calls.append('read');return self.rows
    def active(self):self.calls.append('active');return self.running
    def main_sha(self):self.calls.append('main');return self.main
    def dispatch(self):
        self.calls.append('dispatch')
        if self.fail:raise ValueError('uncertain HTTP result')

class GuardianTests(unittest.TestCase):
    def tick(self,api,state=None):
        state={} if state is None else state
        def save(s):api.calls.append('saved-intent');self.assertIn('last_dispatch_at',s)
        return guard.tick(api,state,save,NOW,clock=lambda:NOW),state
    def test_dispatch_only_after_durable_intent_and_existing_run_check(self):
        api=API();result,state=self.tick(api)
        self.assertEqual(api.calls,['read','active','main','saved-intent','dispatch'])
        self.assertEqual(result['status'],'MAIN_MATERIALIZER_DISPATCH_ACCEPTED');self.assertFalse(result['db_record_proven'])
    def test_active_main_workflow_prevents_duplicate_dispatch(self):
        api=API(active=True);result,_=self.tick(api);self.assertEqual(result['status'],'EXISTING_MAIN_RUN_ACTIVE');self.assertNotIn('dispatch',api.calls)
    def test_any_closed_ready_input_blocks_the_whole_materializer(self):
        api=API([row(),row(999,target_as_of_at='2026-11-05T14:00:00Z',kickoff_at='2026-11-06T14:00:00Z')])
        result,_=self.tick(api);self.assertIn('NO_BACKFILL',result['status']);self.assertNotIn('active',api.calls)
    def test_future_ready_input_is_unsafe_even_alongside_a_legal_one(self):
        api=API([row(),row(999,target_as_of_at='2026-11-05T18:00:00Z',kickoff_at='2026-11-06T18:00:00Z')])
        result,_=self.tick(api);self.assertIn('NO_BACKFILL',result['status']);self.assertNotIn('dispatch',api.calls)
    def test_nonready_source_stays_nonready_but_cannot_block_legal_input(self):
        api=API([row(),row(999,input_status='missing_capacity',target_as_of_at=None)])
        result,_=self.tick(api);self.assertTrue(result['dispatched']);self.assertEqual(result['nonready_inputs'],1)
    def test_no_legal_inputs_never_checks_or_mutates_github(self):
        api=API([]);result,_=self.tick(api);self.assertEqual(api.calls,['read']);self.assertFalse(result['dispatched'])
    def test_wrong_canonical_horizon_duplicate_id_or_clock_fails_closed(self):
        for rows in [[row(horizon='T-3')],[row(),row()],[row(ticket_event_id=True)],
                     [row(target_as_of_at='2026-11-05T17:00:00')]]:
            with self.assertRaises((ValueError,TypeError)):guard.classify(rows,NOW)
    def test_main_change_cannot_silently_dispatch_unreviewed_source(self):
        api=API(main='different')
        with self.assertRaisesRegex(ValueError,'Main changed'):self.tick(api)
        self.assertNotIn('dispatch',api.calls)
    def test_uncertain_dispatch_still_consumes_attempt_and_cooldown(self):
        api=API(fail=True);state={}
        with self.assertRaisesRegex(ValueError,'uncertain'):self.tick(api,state)
        self.assertEqual(next(iter(state['window_dispatch_counts'].values())),1)
        api.fail=False;result,_=self.tick(api,state);self.assertEqual(result['status'],'DISPATCH_COOLDOWN')
    def test_per_window_attempt_limit_is_never_reset_by_later_poll(self):
        state={'window_dispatch_counts':{guard.window_key(row()):3}}
        api=API();result,_=self.tick(api,state);self.assertEqual(result['status'],'WINDOW_DISPATCH_LIMIT');self.assertNotIn('dispatch',api.calls)
    def test_stale_preflight_is_rejected_before_mutation(self):
        api=API()
        with self.assertRaisesRegex(ValueError,'Stale'):guard.tick(api,{},lambda s:None,NOW,clock=lambda:NOW+timedelta(minutes=3))
        self.assertNotIn('dispatch',api.calls)
    def test_bad_durable_count_cannot_expand_attempt_budget(self):
        with self.assertRaisesRegex(ValueError,'dispatch accounting'):self.tick(API(),{'window_dispatch_counts':{'old':-1}})

if __name__=='__main__':unittest.main()
