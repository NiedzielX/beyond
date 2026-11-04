from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error

from ml.frozen_window_guardian_v1 import GuardianAPI, cycle, guardian_lock, open_checkpoints


NOW = datetime(2026, 11, 4, 11, 20, tzinfo=timezone.utc)


def summary():
    cutoff = NOW-timedelta(minutes=5)
    return {"production_change": False, "live_adjustment": 0, "checked_at": NOW.isoformat(),
            "operational_state": {"trajectory_preflight": {
                "model_version": "trajectory-frozen-encoder-ridge-ratio-head-v1",
                "target_values_used": False, "production_change": False, "checkpoints": [{
                    "ticket_event_id": 603, "days_to_event": 3, "cutoff_at": cutoff.isoformat(),
                    "kickoff_at": (cutoff+timedelta(days=3)).isoformat(),
                    "status": "WINDOW_OPEN_INPUT_INSUFFICIENT", "input_ready": False,
                    "attempted_at": None, "attempt_status": None, "prediction_id": None}]}}}


class GuardianTests(unittest.TestCase):
    def test_insufficient_input_still_dispatches_honest_due_attempt(self):
        api = Mock(); api.decision.return_value = summary(); api.active_main_runs.return_value = []
        state = {}; result = cycle(api, state, NOW)
        self.assertTrue(result["dispatched"])
        self.assertFalse(result["open_checkpoints"][0]["input_ready"])
        self.assertEqual(state["last_dispatch_at"], NOW.isoformat())
        api.dispatch.assert_called_once_with()

    def test_exact_window_boundaries_only(self):
        source = summary(); point = source["operational_state"]["trajectory_preflight"]["checkpoints"][0]
        for age_minutes, expected in ((-1,0),(0,1),(90,1),(90.01,0)):
            point["cutoff_at"] = (NOW-timedelta(minutes=age_minutes)).isoformat()
            point["kickoff_at"] = (NOW-timedelta(minutes=age_minutes)+timedelta(days=3)).isoformat()
            with self.subTest(age=age_minutes):
                self.assertEqual(len(open_checkpoints(source,NOW)),expected)

    def test_missing_and_captured_history_is_never_repaired(self):
        for change in ({"status":"MISSED_WINDOW"}, {"status":"PRE_ACTIVATION_NOT_EXPECTED"},
                       {"attempted_at":NOW.isoformat()}, {"attempt_status":"MODEL_INPUT_INSUFFICIENT"},
                       {"prediction_id":1}):
            source = summary(); source["operational_state"]["trajectory_preflight"]["checkpoints"][0].update(change)
            with self.subTest(change=change):self.assertEqual(open_checkpoints(source,NOW),[])

    def test_wrong_flags_model_stale_summary_or_coordinate_fail_closed(self):
        original = summary()
        variants = []
        bad = deepcopy(original); bad["production_change"] = True; variants.append(bad)
        bad = deepcopy(original); bad["checked_at"] = (NOW-timedelta(minutes=3)).isoformat(); variants.append(bad)
        bad = deepcopy(original); bad["operational_state"]["trajectory_preflight"]["model_version"] = "other"; variants.append(bad)
        bad = deepcopy(original); bad["operational_state"]["trajectory_preflight"]["checkpoints"][0]["days_to_event"] = 1; variants.append(bad)
        for source in variants:
            with self.assertRaises(ValueError):open_checkpoints(source,NOW)

    def test_duplicate_checkpoint_rejected(self):
        source = summary(); points = source["operational_state"]["trajectory_preflight"]["checkpoints"]
        points.append(deepcopy(points[0]))
        with self.assertRaisesRegex(ValueError,"Duplicate"):open_checkpoints(source,NOW)

    def test_existing_main_run_and_dispatch_cooldown_prevent_duplicates(self):
        api = Mock(); api.decision.return_value = summary(); api.active_main_runs.return_value = [123]
        self.assertEqual(cycle(api,{},NOW)["status"],"EXISTING_MAIN_RUN_ACTIVE")
        api.dispatch.assert_not_called()
        api.active_main_runs.return_value = []
        self.assertEqual(cycle(api,{"last_dispatch_at":(NOW-timedelta(minutes=9)).isoformat()},NOW)["status"],"DISPATCH_COOLDOWN")
        api.dispatch.assert_not_called()

    def test_no_due_checkpoint_does_not_query_or_dispatch_workflows(self):
        api = Mock(); source = summary(); source["operational_state"]["trajectory_preflight"]["checkpoints"] = []
        api.decision.return_value = source
        self.assertFalse(cycle(api,{},NOW)["dispatched"])
        api.active_main_runs.assert_not_called(); api.dispatch.assert_not_called()

    def test_single_guardian_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            with guardian_lock(Path(directory)), self.assertRaisesRegex(ValueError,"guardian"):
                with guardian_lock(Path(directory)):pass

    def test_http_errors_do_not_expose_headers_or_response_body(self):
        api = object.__new__(GuardianAPI)
        error = urllib.error.HTTPError('https://api.github.com/test',403,'synthetic-private-body',{},None)
        with patch('ml.frozen_window_guardian_v1.urllib.request.urlopen',side_effect=error):
            with self.assertRaisesRegex(ValueError,r'^Guardian request failed with HTTP403$'):
                api.request('https://api.github.com/test',{'Authorization':'Bearer synthetic-private-token'})


if __name__ == '__main__':unittest.main()
