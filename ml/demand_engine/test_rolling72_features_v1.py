"""Rolling72 information boundaries, genuine anchors and cold-start acceptance."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.rolling72_features_v1 import build_issue, features


ISSUE = datetime(2026, 11, 8, 13, 47, tzinfo=timezone.utc)


def row(identifier=1, age=0, value=1000, **extra):
    captured = ISSUE - timedelta(hours=age)
    return {"snapshot_id": identifier, "captured_at": captured.isoformat(),
            "known_at": captured.isoformat(), "available_total": value,
            "measurement_key": "provider:source:declared-pool-v1", **extra}


def event(rows=None, days=50):
    return {"ticket_event_id": 1, "club_slug": "club",
            "kickoff_at": (ISSUE + timedelta(days=days, minutes=7)).isoformat(),
            "known_at": (ISSUE - timedelta(days=100)).isoformat(),
            "observations": [row()] if rows is None else rows}


class Rolling72FeaturesTests(unittest.TestCase):
    def test_one_point_at_p50_and_p10_needs_no_day_of_history(self):
        for days in (50, 10):
            issue = build_issue(event(days=days), ISSUE)
            self.assertEqual(issue["status"], "READY")
            for horizon in (24, 48, 72):
                result = features(issue, horizon)
                self.assertEqual(result["status"], "READY")
                self.assertEqual(result["target_at"], (ISSUE + timedelta(hours=horizon)).isoformat())
                self.assertIsNone(result["features"]["slope_24h"])
                self.assertTrue(result["missing"]["delta_24h"])
                self.assertEqual(result["features"]["prefix_span_hours"], 0)

    def test_horizon_uses_actual_issue_not_capture_or_kickoff_clock(self):
        issue = build_issue(event([row(age=2)]), ISSUE)
        result = features(issue, 72)
        self.assertEqual(result["target_at"], (ISSUE + timedelta(hours=72)).isoformat())
        self.assertEqual(result["features"]["latest_staleness_hours"], 2)

    def test_future_and_late_known_payloads_cannot_change_old_issue(self):
        data = event()
        original = build_issue(data, ISSUE)
        data["observations"].extend([
            row(2, age=-1, value=None, source_active=False, target_attendance="forbidden"),
            row(3, age=12, value=-999, known_at=(ISSUE + timedelta(minutes=1)).isoformat()),
        ])
        self.assertEqual(build_issue(data, ISSUE), original)
        self.assertEqual(features(original, 24), features(build_issue(data, ISSUE), 24))

    def test_metadata_must_have_been_known_with_this_version(self):
        data = event()
        data.update(known_at=(ISSUE + timedelta(seconds=1)).isoformat(), kickoff_at="unknown", club_slug=None)
        issue = build_issue(data, ISSUE)
        self.assertEqual(issue["status"], "EVENT_NOT_KNOWN_AS_OF")
        self.assertIsNone(issue["event"])
        self.assertEqual(features(issue, 24)["features"], {})

    def test_missing_knowledge_clocks_are_not_invented_from_capture(self):
        data = event()
        del data["observations"][0]["known_at"]
        with self.assertRaises(ValueError):
            build_issue(data, ISSUE)
        data = event([row(known_at=(ISSUE - timedelta(seconds=1)).isoformat())])
        with self.assertRaisesRegex(ValueError, "precedes"):
            build_issue(data, ISSUE)

    def test_literal_zero_preserved_but_invalid_count_cannot_fallback(self):
        issue = build_issue(event([row(value=0)]), ISSUE)
        self.assertEqual(features(issue, 24)["features"]["last_available_total"], 0)
        for value in (None, True, -1, "0", float("nan"), float("inf")):
            failed = build_issue(event([row(2, age=2), row(value=value)]), ISSUE)
            self.assertEqual(failed["status"], "INVALID_OBSERVATION")
            self.assertEqual(features(failed, 24)["features"], {})

    def test_unknown_flags_remain_unknown_and_false_flags_fail_closed(self):
        unknown = build_issue(event(), ISSUE)
        self.assertFalse(unknown["quality"]["source_flags_complete"])
        self.assertIsNone(unknown["observed_prefix"][0]["source_active"])
        for flag, status in (("source_active", "SOURCE_INACTIVE"), ("source_visible", "SOURCE_HIDDEN")):
            failed = build_issue(event([row(2, age=1), row(**{flag: False})]), ISSUE)
            self.assertEqual(failed["status"], status)
        self.assertEqual(build_issue(event([row(source_active="false")]), ISSUE)["status"], "INVALID_OBSERVATION")

    def test_measurement_and_hidden_state_cannot_be_concealed_by_time_tie(self):
        for older in (row(1, measurement_key="other-pool"), row(1, source_visible=False)):
            issue = build_issue(event([older, row(2)]), ISSUE)
            self.assertNotEqual(issue["status"], "READY")

    def test_identity_conflicts_fail_closed_and_order_is_deterministic(self):
        data = event([row(1, age=2), row(2), row(3)])
        issue = build_issue(data, ISSUE)
        data["observations"].reverse()
        self.assertEqual(build_issue(data, ISSUE), issue)
        self.assertEqual(issue["observed_prefix"][-1]["snapshot_id"], 3)
        conflict = build_issue(event([row(1, age=1), row(1)]), ISSUE)
        self.assertEqual(conflict["status"], "CONFLICTING_OBSERVATION_IDENTITY")

    def test_full_prefix_survives_p60_and_hour_boundaries(self):
        issue = build_issue(event([row(1, age=2000, value=2000), row(2, age=.1), row(3)]), ISSUE)
        self.assertEqual(len(issue["observed_prefix"]), 3)
        self.assertEqual(issue["prefix_span_hours"], 2000)
        self.assertEqual(features(issue, 72)["features"]["observed_delta_since_first"], -1000)

    def test_same_last_level_different_histories_change_actual_value_features(self):
        one = features(build_issue(event([row(1, age=24, value=1200), row(2)]), ISSUE), 72)
        two = features(build_issue(event([row(1, age=24, value=800), row(2)]), ISSUE), 72)
        self.assertEqual(one["features"]["last_available_total"], two["features"]["last_available_total"])
        self.assertEqual(one["quality"], two["quality"])
        self.assertEqual(one["features"]["delta_24h"], -200)
        self.assertEqual(two["features"]["delta_24h"], 200)
        self.assertNotIn("observation_count", one["features"])

    def test_actual_elapsed_window_and_tolerance_without_interpolation(self):
        result = features(build_issue(event([row(1, age=30, value=1300), row(2)]), ISSUE), 48)
        self.assertEqual(result["features"]["delta_24h"], -300)
        self.assertEqual(result["features"]["slope_24h"], -10)
        self.assertEqual(result["window_lineage"]["24"]["elapsed_hours"], 30)
        stale_anchor = features(build_issue(event([row(1, age=30.001), row(2)]), ISSUE), 48)
        self.assertIsNone(stale_anchor["features"]["delta_24h"])
        after_boundary = features(build_issue(event([row(1, age=23.99), row(2)]), ISSUE), 48)
        self.assertIsNone(after_boundary["features"]["delta_24h"])

    def test_staleness_gate_does_not_mean_minimum_history(self):
        self.assertEqual(build_issue(event([row(age=6)]), ISSUE)["status"], "READY")
        self.assertEqual(build_issue(event([row(age=6.001)]), ISSUE)["status"], "STALE_INPUT")

    def test_horizons_at_or_after_kickoff_unavailable(self):
        data = event()
        data["kickoff_at"] = (ISSUE + timedelta(hours=48)).isoformat()
        issue = build_issue(data, ISSUE)
        self.assertEqual(features(issue, 24)["status"], "READY")
        self.assertEqual(features(issue, 48)["status"], "TARGET_NOT_BEFORE_KICKOFF")
        self.assertEqual(features(issue, 72)["features"], {})
        self.assertEqual(build_issue(data, data["kickoff_at"])["status"], "ISSUE_NOT_BEFORE_KICKOFF")

    def test_input_and_old_vintage_unchanged_after_new_observation(self):
        data = event()
        before = deepcopy(data)
        issue = build_issue(data, ISSUE)
        frozen = deepcopy(issue)
        features(issue, 24)
        self.assertEqual(data, before)
        data["observations"].append(row(2, age=-.5, value=900))
        later = build_issue(data, ISSUE + timedelta(hours=.5))
        self.assertEqual(issue, frozen)
        self.assertNotEqual(issue["input_manifest_sha256"], later["input_manifest_sha256"])
        self.assertEqual(build_issue(data, ISSUE), frozen)

    def test_tampered_hashes_and_semantics_rejected(self):
        issue = build_issue(event(), ISSUE)
        for key in ("last_available_total", "input_manifest_sha256", "prefix_sha256"):
            corrupt = deepcopy(issue)
            corrupt[key] = "tampered"
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                features(corrupt, 24)

    def test_outcome_columns_and_naive_clocks_cannot_enter_inputs(self):
        data = event([row(actual_attendance=2000)])
        self.assertEqual(build_issue(data, ISSUE)["status"], "INVALID_OBSERVATION")
        for horizon in (True, 0, 7, 24.0):
            with self.assertRaises(ValueError):
                features(build_issue(event(), ISSUE), horizon)
        with self.assertRaises(ValueError):
            build_issue(event(), ISSUE.replace(tzinfo=None))


if __name__ == "__main__":
    unittest.main()
