"""Label knowledge boundaries and honest horizon coverage."""
from copy import deepcopy
from datetime import timedelta
import unittest

from ml.demand_engine.rolling72_features_v1 import build_issue
from ml.demand_engine.rolling72_labels_v1 import match_target
from ml.demand_engine.test_rolling72_features_v1 import ISSUE, event, row


class Rolling72LabelsTests(unittest.TestCase):
    def setUp(self):
        self.data = event([row(1), row(2, age=-18, value=900), row(3, age=-24, value=800)])
        self.issue = build_issue(self.data, ISSUE)
        self.cutoff = ISSUE + timedelta(hours=24)

    def test_real_future_label_keeps_separate_capture_and_knowledge_clocks(self):
        self.data["observations"][-1]["known_at"] = (self.cutoff + timedelta(hours=2)).isoformat()
        result = match_target(self.data, self.issue, 24, self.cutoff + timedelta(hours=2))
        self.assertEqual(result["status"], "MATCHED")
        self.assertEqual(result["label"]["snapshot_id"], 3)
        self.assertEqual(result["label"]["target_staleness_hours"], 0)
        self.assertEqual(result["label"]["delta_from_last_observation"], -200)
        self.assertNotEqual(result["label"]["captured_at"], result["label"]["known_at"])

    def test_late_known_label_cannot_enter_earlier_fit_or_score_cutoff(self):
        self.data["observations"][-1]["known_at"] = (self.cutoff + timedelta(seconds=1)).isoformat()
        result = match_target(self.data, self.issue, 24, self.cutoff)
        self.assertEqual(result["label"]["snapshot_id"], 2)
        self.assertEqual(result["label"]["target_staleness_hours"], 6)
        # An older genuine point is eligible only because the later row was not yet known.
        self.data["observations"][-1]["available_total"] = None
        self.assertEqual(match_target(self.data, self.issue, 24, self.cutoff), result)

    def test_maturity_cannot_be_pulled_forward_by_tolerance(self):
        result = match_target(self.data, self.issue, 24, self.cutoff - timedelta(seconds=1))
        self.assertEqual(result["status"], "PENDING_TARGET")
        self.assertIsNone(result["label"])

    def test_future_payload_and_after_target_values_do_not_change_label(self):
        before = match_target(self.data, self.issue, 24, self.cutoff)
        self.data["observations"].append(row(4, age=-24.01, value=None, source_visible=False, outcome=100))
        self.assertEqual(match_target(self.data, self.issue, 24, self.cutoff), before)

    def test_no_interpolation_or_fake_missing_zero(self):
        self.data["observations"] = [row(1), row(2, age=-17.999)]
        result = match_target(self.data, self.issue, 24, self.cutoff)
        self.assertEqual(result["status"], "STALE_TARGET_OBSERVATION")
        self.assertIsNone(result["label"])
        self.data["observations"] = [row(1)]
        self.assertEqual(match_target(self.data, self.issue, 24, self.cutoff)["status"], "NO_KNOWN_FUTURE_OBSERVATION")

    def test_invalid_or_hidden_latest_never_falls_back_to_old_value(self):
        for change, status in (({"available_total": None}, "INVALID_TARGET_OBSERVATION"),
                               ({"source_visible": False}, "TARGET_SOURCE_UNUSABLE"),
                               ({"source_active": False}, "TARGET_SOURCE_UNUSABLE")):
            data = deepcopy(self.data)
            data["observations"][-1].update(change)
            self.assertEqual(match_target(data, self.issue, 24, self.cutoff)["status"], status)

    def test_real_zero_remains_a_label_unknown_flags_remain_unknown(self):
        self.data["observations"][-1]["available_total"] = 0
        result = match_target(self.data, self.issue, 24, self.cutoff)
        self.assertEqual(result["status"], "MATCHED")
        self.assertEqual(result["label"]["available_total"], 0)
        self.assertIsNone(result["label"]["source_active"])

    def test_changed_measurement_cannot_hide_by_returning_to_original_key(self):
        self.data["observations"][1]["measurement_key"] = "different-pool"
        self.assertEqual(match_target(self.data, self.issue, 24, self.cutoff)["status"], "MEASUREMENT_CHANGED")

    def test_conflicting_future_or_prefix_identity_is_rejected(self):
        data = deepcopy(self.data)
        data["observations"].append(row(3, age=-23, value=700))
        self.assertEqual(match_target(data, self.issue, 24, self.cutoff)["status"], "CONFLICTING_OBSERVATION_IDENTITY")
        data = deepcopy(self.data)
        data["observations"][-1]["snapshot_id"] = 1
        self.assertEqual(match_target(data, self.issue, 24, self.cutoff)["status"], "CONFLICTING_OBSERVATION_IDENTITY")

    def test_original_coordinates_do_not_move_when_event_metadata_changes(self):
        data = deepcopy(self.data)
        data["kickoff_at"] = (ISSUE + timedelta(days=40)).isoformat()
        self.assertEqual(match_target(data, self.issue, 24, self.cutoff)["status"], "EVENT_METADATA_CHANGED")
        self.assertEqual(match_target(self.data, self.issue, 24, self.cutoff)["status"], "MATCHED")

    def test_post_kickoff_horizon_has_no_inventory_label(self):
        data = event([row(1)], days=0)
        issue = build_issue(data, ISSUE)
        self.assertEqual(match_target(data, issue, 24, self.cutoff)["status"], "TARGET_NOT_BEFORE_KICKOFF")

    def test_input_hashes_unchanged_and_invalid_clocks_raise(self):
        original, original_issue = deepcopy(self.data), deepcopy(self.issue)
        match_target(self.data, self.issue, 24, self.cutoff)
        self.assertEqual(self.data, original)
        self.assertEqual(self.issue, original_issue)
        with self.assertRaises(ValueError):
            match_target(self.data, self.issue, 24, ISSUE - timedelta(seconds=1))
        self.data["observations"][-1]["known_at"] = ISSUE.isoformat()
        with self.assertRaisesRegex(ValueError, "precedes"):
            match_target(self.data, self.issue, 24, self.cutoff)


if __name__ == "__main__":
    unittest.main()
