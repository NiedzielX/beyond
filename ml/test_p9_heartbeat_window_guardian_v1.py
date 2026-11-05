from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from ml.p9_heartbeat_window_guardian_v1 import open_windows, cycle

NOW = datetime(2026, 11, 5, 16, 30, tzinfo=timezone.utc)


def summary(now=NOW):
    event = {'ticket_event_id': 449, 'kickoff_at': (NOW+timedelta(hours=48)).isoformat(),
        't48_at': NOW.isoformat(), 't24_at': (NOW+timedelta(hours=24)).isoformat(),
        't48_status': 'READY', 't24_status': 'READY', 'attempt_t48_status': None,
        'attempt_t24_status': None, 'prediction_t48_exists': False, 'prediction_t24_exists': False}
    return {'checked_at': now.isoformat(), 'production_change': False, 'live_adjustment': 0,
        'operational_state': {'p9_preflight': {'version': 'p9-prospective-preflight-v1',
            'production_change': False, 'target_values_used': False, 'checked_at': now.isoformat(), 'events': [event]}}}


class API:
    def __init__(self, value=None, active=None):
        self.value = value if value is not None else summary(); self.active = active or []
        self.active_queries = 0; self.dispatches = 0
    def decision(self): return self.value
    def active_p9_runs(self): self.active_queries += 1; return self.active
    def dispatch_heartbeat(self): self.dispatches += 1


class GuardianTests(unittest.TestCase):
    def test_only_exact_legal_windows_are_open(self):
        for delta, count in [(-1, 0), (0, 1), (5400, 1), (5401, 0)]:
            now = NOW+timedelta(seconds=delta)
            self.assertEqual(len(open_windows(summary(now), now)), count)

    def test_captured_predictions_and_historical_misses_are_not_repaired(self):
        for field, value in [('attempt_t48_status', 'PIT_SUPPORT_INSUFFICIENT'), ('prediction_t48_exists', True)]:
            s = summary(); s['operational_state']['p9_preflight']['events'][0][field] = value
            self.assertEqual(open_windows(s, NOW), [])
        now = NOW+timedelta(hours=5)
        api = API(summary(now)); state = {}
        self.assertFalse(cycle(api, state, lambda: now)['dispatched'])
        self.assertEqual(api.active_queries, 0); self.assertEqual(state, {})

    def test_missing_snapshot_dispatch_is_not_claimed_as_workflow_or_db_success(self):
        s = summary(); s['operational_state']['p9_preflight']['events'][0]['t48_status'] = 'CRITICAL_NO_SNAPSHOT'
        api = API(s); state = {}; result = cycle(api, state, lambda: NOW)
        self.assertTrue(result['dispatched']); self.assertEqual(api.dispatches, 1)
        self.assertFalse(result['hosted_workflow_chain_done'])
        self.assertEqual(sum(state['window_dispatch_counts'].values()), 1)

    def test_active_main_runs_and_global_cooldown_prevent_duplicate_dispatch(self):
        api = API(active=[123]); state = {}
        result = cycle(api, state, lambda: NOW)
        self.assertEqual(result['status'], 'EXISTING_MAIN_P9_OR_HEARTBEAT_ACTIVE')
        self.assertEqual(state, {}); self.assertEqual(api.dispatches, 0)
        state = {'last_dispatch_at': (NOW-timedelta(minutes=9)).isoformat()}
        api = API(); result = cycle(api, state, lambda: NOW)
        self.assertEqual(result['status'], 'DISPATCH_COOLDOWN'); self.assertEqual(api.active_queries, 0)

    def test_three_legal_retries_are_bounded_and_expired_at_dispatch_is_rejected(self):
        state = {}
        for minutes in (0, 10, 20):
            now = NOW+timedelta(minutes=minutes); api = API(summary(now))
            self.assertTrue(cycle(api, state, lambda: now)['dispatched'])
        now = NOW+timedelta(minutes=30)
        self.assertEqual(cycle(API(summary(now)), state, lambda: now)['status'], 'WINDOW_DISPATCH_LIMIT_REACHED')
        start = NOW+timedelta(minutes=89, seconds=59); end = NOW+timedelta(minutes=90, seconds=1)
        clock = iter([start, end]); api = API(summary(start)); state = {}
        self.assertEqual(cycle(api, state, lambda: next(clock))['status'], 'WINDOW_CLOSED_BEFORE_DISPATCH')
        self.assertEqual(api.dispatches, 0); self.assertEqual(state, {})
        api = API(); state = {}
        self.assertEqual(cycle(api, state, lambda: NOW, deadline=NOW)['status'], 'GUARDIAN_DEADLINE_REACHED')
        self.assertEqual(api.dispatches, 0)

    def test_stale_flags_wrong_coordinates_and_duplicate_ids_fail_closed(self):
        variants = []
        s = summary(); s['production_change'] = True; variants.append(s)
        s = summary(); s['checked_at'] = (NOW-timedelta(minutes=3)).isoformat(); variants.append(s)
        s = summary(); s['operational_state']['p9_preflight']['target_values_used'] = True; variants.append(s)
        s = summary(); s['operational_state']['p9_preflight']['checked_at'] = (NOW+timedelta(seconds=30)).isoformat(); variants.append(s)
        s = summary(); s['operational_state']['p9_preflight']['events'][0]['t48_at'] = (NOW-timedelta(seconds=1)).isoformat(); variants.append(s)
        s = summary(); s['operational_state']['p9_preflight']['events'][0]['t48_at'] = '2026-11-05T16:30:00'; variants.append(s)
        s = summary(); s['operational_state']['p9_preflight']['events'].append(deepcopy(s['operational_state']['p9_preflight']['events'][0])); variants.append(s)
        for value in variants:
            api = API(value)
            with self.assertRaises(ValueError): cycle(api, {}, lambda: NOW)
            self.assertEqual(api.dispatches, 0)

    def test_ambiguous_remote_timeout_consumes_durably_reserved_retry(self):
        state, persisted = {}, []
        class TimeoutAPI(API):
            def dispatch_heartbeat(self):
                self.assert_reserved = deepcopy(state)
                if not persisted: raise AssertionError('Intent must precede the remote mutation')
                raise TimeoutError('Remote may already have accepted the dispatch')
        api = TimeoutAPI()
        with self.assertRaises(TimeoutError):
            cycle(api, state, lambda: NOW, persist_state=lambda value: persisted.append(deepcopy(value)))
        self.assertEqual(sum(state['window_dispatch_counts'].values()), 1)
        self.assertEqual(persisted, [state])
        self.assertEqual(cycle(API(), state, lambda: NOW)['status'], 'DISPATCH_COOLDOWN')


if __name__ == '__main__':
    unittest.main()
