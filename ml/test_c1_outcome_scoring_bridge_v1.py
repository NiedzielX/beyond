from datetime import datetime, timezone, timedelta
import unittest
from ml.c1_outcome_scoring_bridge_v1 import tick, PACKAGE

NOW = datetime(2026, 11, 6, 12, tzinfo=timezone.utc)


def report(count=0, **changes):
    return {'package_version': PACKAGE, 'scored_events': count,
            'production_change': False, 'live_adjustment': 0, **changes}


class BridgeTests(unittest.TestCase):
    def invoke(self, value, state=None, fail=False, now=NOW):
        state = {} if state is None else state; calls = []
        def execute():
            calls.append('score')
            if fail: raise ValueError('scorer failed')
            return {'ridge20': {'scored_events': 1}, 'median20': {'scored_events': 1}}
        result = tick(value, state, now, execute, lambda s: calls.append('durable-state'))
        return result, state, calls

    def test_zero_genuine_outcomes_never_calls_a_scorer_or_database(self):
        result, state, calls = self.invoke(report())
        self.assertEqual(calls, []); self.assertFalse(result['source_rpc_polled'])

    def test_new_outcome_intent_precedes_scoring_and_success_advances_frontier(self):
        result, state, calls = self.invoke(report(1))
        self.assertEqual(calls, ['durable-state', 'score', 'durable-state'])
        self.assertEqual(state['last_successful_count'], 1)

    def test_unchanged_count_does_not_repeat_network_work(self):
        _, state, _ = self.invoke(report(1))
        result, _, calls = self.invoke(report(1), state)
        self.assertEqual(calls, [])

    def test_bad_package_or_production_flags_cannot_trigger_scoring(self):
        for changes in [{'package_version': 'other'}, {'production_change': True}, {'live_adjustment': 1}]:
            with self.assertRaises(ValueError): self.invoke(report(1, **changes))

    def test_boolean_negative_and_excessive_counts_are_rejected(self):
        for count in [True, -1, 10001]:
            with self.assertRaises(ValueError): self.invoke(report(count))

    def test_failed_scorer_consumes_attempt_but_not_success_frontier(self):
        state = {}; calls = []
        def fail(): calls.append('scorer'); raise ValueError('failure')
        with self.assertRaises(ValueError): tick(report(1), state, NOW, fail, lambda s: calls.append('intent'))
        self.assertEqual(calls, ['intent', 'scorer']); self.assertEqual(state['attempts']['1'], 1)
        self.assertNotIn('last_successful_count', state)
        result, _, calls = self.invoke(report(1), state)
        self.assertEqual(result['status'], 'RETRY_COOLDOWN'); self.assertEqual(calls, [])

    def test_attempt_budget_does_not_reset_after_cooldown(self):
        result, _, calls = self.invoke(report(1), {'attempts': {'1': 3}})
        self.assertEqual(result['status'], 'ATTEMPT_LIMIT_REQUIRES_REVIEW'); self.assertEqual(calls, [])

    def test_regressed_frontier_or_invalid_retry_accounting_fails_closed(self):
        for state in [{'last_successful_count': 2}, {'attempts': {'1': -1}}]:
            with self.assertRaises(ValueError): self.invoke(report(1), state)


if __name__ == '__main__': unittest.main()
