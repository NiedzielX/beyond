from datetime import datetime, timezone, timedelta
import unittest
from ml.daily_path_window_runner_v1 import windows, tick

NOW = datetime(2026, 11, 6, 17, 15, tzinfo=timezone.utc)
EVENT = {'id': 5091, 'kickoff_at': '2026-11-07T17:00:00Z'}


class WindowTests(unittest.TestCase):
    def invoke(self, now=NOW, events=None, state=None, pending=()):
        calls = []; state = {} if state is None else state
        def execute(): calls.append('full-export'); return {'genuine_cycle': True}
        result = tick([EVENT] if events is None else events, pending, state, now, (), execute,
                      lambda s: calls.append('durable-state'))
        return result, state, calls

    def test_between_windows_does_not_query_or_export(self):
        result, _, calls = self.invoke(now=NOW-timedelta(hours=2))
        self.assertEqual(calls, []); self.assertFalse(result['full_export_executed'])

    def test_actual_daily_slot_records_intent_before_one_full_cycle(self):
        result, state, calls = self.invoke()
        self.assertEqual(calls, ['durable-state', 'full-export', 'durable-state'])
        self.assertEqual(len(state['completed_slots']), 1)
        self.assertTrue(result['full_export_executed'])

    def test_no_new_forecast_before_delay_or_after_genuine_window(self):
        for now in [NOW-timedelta(minutes=10), NOW+timedelta(minutes=76)]:
            self.assertEqual(windows([EVENT], [], now), [])

    def test_exact_window_endpoint_is_included(self):
        self.assertEqual(len(windows([EVENT], [], NOW+timedelta(minutes=75))), 1)

    def test_training_expired_or_beyond_sixty_day_fixtures_do_not_trigger(self):
        self.assertFalse(windows([EVENT], [], NOW, (5091,)))
        self.assertFalse(windows([{'id': 1, 'kickoff_at': '2026-11-05T17:00:00Z'}], [], NOW))
        self.assertFalse(windows([{'id': 1, 'kickoff_at': '2027-02-06T17:00:00Z'}], [], NOW))

    def test_duplicate_bad_identity_and_naive_clocks_fail_closed(self):
        for events in [[EVENT, EVENT], [{**EVENT, 'id': True}], [{**EVENT, 'kickoff_at': '2026-11-07T17:00:00'}]]:
            with self.assertRaises(ValueError): windows(events, [], NOW)

    def test_completed_slot_is_never_run_again(self):
        _, state, _ = self.invoke()
        result, _, calls = self.invoke(state=state)
        self.assertEqual(calls, []); self.assertFalse(result['full_export_executed'])

    def test_pending_target_independently_schedules_existing_label_scoring(self):
        result, _, calls = self.invoke(events=[], pending=[(5091, '2026-11-06T17:00:00Z')])
        self.assertTrue(result['full_export_executed']); self.assertEqual(calls.count('full-export'), 1)

    def test_failed_cycle_keeps_attempt_and_cooldown_without_completed_slot(self):
        state = {}; order = []
        def fail(): order.append('export'); raise ValueError('actual cycle failed')
        with self.assertRaises(ValueError): tick([EVENT], [], state, NOW, (), fail, lambda s: order.append('intent'))
        self.assertEqual(order, ['intent', 'export']); self.assertNotIn('completed_slots', state)
        result, _, calls = self.invoke(state=state)
        self.assertEqual(result['status'], 'RETRY_COOLDOWN_LOCAL_CHECK_ONLY'); self.assertEqual(calls, [])

    def test_retry_budget_is_bounded_per_real_slot(self):
        key = windows([EVENT], [], NOW)[0]
        result, _, calls = self.invoke(state={'slot_attempts': {key: 3}})
        self.assertIn('ATTEMPT_LIMIT', result['status']); self.assertEqual(calls, [])


if __name__ == '__main__': unittest.main()
