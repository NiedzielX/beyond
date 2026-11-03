from copy import deepcopy
from datetime import datetime, timedelta, timezone
import math
import unittest

from ml.demand_engine.daily_inventory_path_dataset_v1 import (
    build_dataset,
    build_issue,
    canonical_hash,
    future_targets,
    issue_manifest,
    match_target,
    parse_timestamp,
)


UTC = timezone.utc


class DailyInventoryPathDatasetTest(unittest.TestCase):
    def setUp(self):
        self.kickoff = datetime(2027, 1, 10, 18, 0, tzinfo=UTC)
        self.issue_at = self.kickoff - timedelta(days=10)
        self.event = {
            "ticket_event_id": 1,
            "club_slug": "test-club",
            "kickoff_at": self.kickoff.isoformat(),
            "observations": [],
        }
        for idx, hours_before_issue in enumerate((48, 25, 12, 0), 1):
            self.add_observation(self.issue_at - timedelta(hours=hours_before_issue), 1000 - idx * 10, idx)

    def add_observation(self, at, value, snapshot_id, **extra):
        row = {
            "snapshot_id": snapshot_id,
            "captured_at": at.isoformat(),
            "available_total": value,
            "measurement_key": "provider:inventory-v1",
            **extra,
        }
        self.event["observations"].append(row)
        return row

    def test_earlier_issue_does_not_use_or_hash_future_values(self):
        before = build_issue(self.event, self.issue_at)
        self.add_observation(self.issue_at + timedelta(minutes=1), -50, 100, source_active=False)
        after = build_issue(self.event, self.issue_at)
        self.assertEqual(before, after)
        self.assertEqual(after["status"], "READY")
        self.assertFalse(after["target_values_used"])

    def test_full_observed_prefix_is_not_truncated_at_168_hours(self):
        earliest = self.kickoff - timedelta(days=50)
        self.add_observation(earliest, 9000, 100)
        issue = build_issue(self.event, self.issue_at)
        self.assertEqual(issue["status"], "READY")
        self.assertEqual(issue["observed_prefix"][0]["snapshot_id"], 100)
        self.assertGreater(issue["prefix_span_hours"], 168)

    def test_observations_earlier_than_p60_are_not_inputs(self):
        before = build_issue(self.event, self.issue_at)
        self.add_observation(self.kickoff - timedelta(days=61), -1, 100)
        self.assertEqual(before, build_issue(self.event, self.issue_at))

    def test_daily_targets_have_both_issue_and_target_coordinates(self):
        issue = build_issue(self.event, self.issue_at)
        targets = future_targets(issue)
        self.assertEqual([point["lead_days"] for point in targets], list(range(1, 10)))
        self.assertEqual(parse_timestamp(targets[0]["target_at"]), self.issue_at + timedelta(days=1))
        self.assertEqual(parse_timestamp(targets[-1]["target_at"]), self.kickoff - timedelta(days=1))
        self.assertEqual(targets[-1]["target_days_to_event"], 1)
        p1 = build_issue(self.event, self.kickoff - timedelta(days=1))
        self.assertEqual(future_targets(p1), [])

    def test_issue_cutoff_is_exact_and_timezone_aware(self):
        bad = build_issue(self.event, self.issue_at + timedelta(seconds=1))
        self.assertEqual(bad["status"], "INVALID_ISSUE_CUTOFF")
        self.assertEqual(build_issue(self.event, self.kickoff)["status"], "INVALID_ISSUE_CUTOFF")
        with self.assertRaises(ValueError):
            build_issue(self.event, self.issue_at.replace(tzinfo=None))
        offset_issue = self.issue_at.astimezone(timezone(timedelta(hours=2)))
        self.assertEqual(build_issue(self.event, offset_issue), build_issue(self.event, self.issue_at))

    def test_timestamp_duplicates_keep_highest_id_then_latest_per_hour(self):
        latest = self.event["observations"][-1]
        replacement = {**latest, "snapshot_id": 8, "available_total": 800}
        self.event["observations"].append(replacement)
        earlier_in_same_hour = {**latest, "snapshot_id": 9, "captured_at": (self.issue_at - timedelta(minutes=5)).isoformat()}
        # The preceding UTC hour is distinct; exercise one hour at a nonzero minute.
        self.event["observations"].append(earlier_in_same_hour)
        issue = build_issue(self.event, self.issue_at)
        self.assertEqual(issue["last_available_total"], 800)
        self.assertEqual(issue["observed_prefix"][-1]["snapshot_id"], 8)
        self.assertEqual(sum(row["captured_at"] == latest["captured_at"] for row in issue["observed_prefix"]), 1)

    def test_latest_observation_in_utc_hour_wins(self):
        self.add_observation(self.issue_at - timedelta(hours=12, minutes=20), 3000, 50)
        # A lower-ID observation later in the same hour wins by capture time.
        self.add_observation(self.issue_at - timedelta(hours=12) + timedelta(minutes=10), 700, 51)
        issue = build_issue(self.event, self.issue_at)
        hour = (self.issue_at - timedelta(hours=12)).replace(minute=0, second=0)
        matching = [row for row in issue["observed_prefix"] if parse_timestamp(row["captured_at"]).replace(minute=0, second=0) == hour]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["snapshot_id"], 51)

    def test_literal_zero_is_observed_but_missing_is_not_zero(self):
        self.event["observations"][-1]["available_total"] = 0
        issue = build_issue(self.event, self.issue_at)
        self.assertEqual(issue["status"], "READY")
        self.assertEqual(issue["last_available_total"], 0.0)
        self.event["observations"][-1]["available_total"] = None
        self.assertEqual(build_issue(self.event, self.issue_at)["status"], "INVALID_OBSERVATION")

    def test_bad_numbers_and_source_states_fail_closed(self):
        for value in (-1, math.inf, math.nan, True, "123"):
            event = deepcopy(self.event)
            event["observations"][-1]["available_total"] = value
            with self.subTest(value=value):
                self.assertEqual(build_issue(event, self.issue_at)["status"], "INVALID_OBSERVATION")
        for flag, status in (("source_active", "SOURCE_INACTIVE"), ("source_visible", "SOURCE_HIDDEN")):
            event = deepcopy(self.event)
            event["observations"][-1][flag] = False
            self.assertEqual(build_issue(event, self.issue_at)["status"], status)

    def test_measurement_change_is_not_hidden_by_hourly_deduplication(self):
        self.add_observation(self.issue_at - timedelta(minutes=10), 1100, 9, measurement_key="another-source")
        self.assertEqual(build_issue(self.event, self.issue_at)["status"], "MEASUREMENT_CHANGED")
        self.event["observations"][-1]["measurement_key"] = ""
        self.assertEqual(build_issue(self.event, self.issue_at)["status"], "INVALID_OBSERVATION")

    def test_minimum_span_and_staleness_boundaries(self):
        event = deepcopy(self.event)
        event["observations"] = []
        for idx, hours in enumerate((30, 20, 10, 6), 1):
            event["observations"].append({
                "snapshot_id": idx, "captured_at": (self.issue_at - timedelta(hours=hours)).isoformat(),
                "available_total": 100, "measurement_key": "source",
            })
        self.assertEqual(build_issue(event, self.issue_at)["status"], "READY")
        event["observations"][-1]["captured_at"] = (self.issue_at - timedelta(hours=6, microseconds=1)).isoformat()
        self.assertEqual(build_issue(event, self.issue_at)["status"], "INSUFFICIENT_PREFIX_SPAN")
        event["observations"][0]["captured_at"] = (self.issue_at - timedelta(hours=31)).isoformat()
        self.assertEqual(build_issue(event, self.issue_at)["status"], "STALE_INPUT")

    def test_target_matching_never_interpolates_and_checks_training_cutoff(self):
        target = self.issue_at + timedelta(days=1)
        self.add_observation(target - timedelta(hours=6), 750, 10)
        self.add_observation(target + timedelta(seconds=1), 1, 11)
        matched = match_target(self.event, target, target, "provider:inventory-v1")
        self.assertEqual(matched["snapshot_id"], 10)
        self.assertEqual(matched["target_staleness_hours"], 6)
        self.assertIsNone(match_target(self.event, target, target - timedelta(seconds=1), "provider:inventory-v1"))
        self.assertIsNone(match_target(self.event, target + timedelta(microseconds=1), target + timedelta(microseconds=1), "provider:inventory-v1"))

    def test_bad_or_changed_latest_target_does_not_fallback_to_older_matching_value(self):
        target = self.issue_at + timedelta(days=1)
        self.add_observation(target - timedelta(hours=1), 800, 10)
        changed = self.add_observation(target, 700, 11, measurement_key="changed")
        self.assertIsNone(match_target(self.event, target, target, "provider:inventory-v1"))
        changed["measurement_key"] = "provider:inventory-v1"
        changed["available_total"] = None
        self.assertIsNone(match_target(self.event, target, target, "provider:inventory-v1"))
        changed["available_total"] = 700
        changed["source_visible"] = False
        self.assertIsNone(match_target(self.event, target, target, "provider:inventory-v1"))

    def test_conflicting_snapshot_identity_fails_closed(self):
        original = self.event["observations"][0]
        self.event["observations"].append({**original, "available_total": 123})
        self.assertEqual(build_issue(self.event, self.issue_at)["status"], "INVALID_OBSERVATION")
        self.event["observations"][-1] = {
            **original, "captured_at": (self.issue_at - timedelta(hours=24)).isoformat(),
        }
        self.assertEqual(build_issue(self.event, self.issue_at)["status"], "INVALID_OBSERVATION")

    def test_post_kickoff_target_is_not_an_inventory_label(self):
        self.add_observation(self.kickoff, 100, 100)
        self.assertIsNone(match_target(self.event, self.kickoff, self.kickoff, "provider:inventory-v1"))

    def test_dataset_distinguishes_mature_missing_and_future_pending_targets(self):
        target = self.issue_at + timedelta(days=1)
        self.add_observation(target, 700, 10)
        dataset = build_dataset([self.event], target)
        coverage = dataset["coverage"]
        self.assertGreater(coverage["ready_issue_count"], 0)
        self.assertEqual(coverage["matched_target_count"], 1)
        self.assertEqual(len(dataset["rows"]), 1)
        self.assertGreater(coverage["pending_target_count"], 0)
        self.assertEqual(coverage["missing_target_count"], coverage["mature_target_count"] - 1)
        self.assertEqual(dataset["rows"][0]["target_snapshot_id"], 10)
        self.assertEqual(dataset["rows"][0]["issue"]["issued_as_of_at"], self.issue_at.isoformat())
        self.assertEqual(dataset["evidence_kind"], "retrospective_diagnostic_not_prospective")
        self.assertFalse(dataset["production_change"])

    def test_dataset_never_includes_future_labels_or_future_issue_times(self):
        target = self.issue_at + timedelta(days=1)
        self.add_observation(target, 700, 10)
        dataset = build_dataset([self.event], self.issue_at)
        self.assertEqual(dataset["rows"], [])
        self.assertTrue(all(parse_timestamp(issue["issued_as_of_at"]) <= self.issue_at for issue in dataset["issues"]))
        self.assertEqual(dataset["coverage"]["pending_target_count"], 9)

    def test_hashes_are_stable_and_bind_prefix_and_issue_identity(self):
        issue = build_issue(self.event, self.issue_at)
        self.assertEqual(issue["prefix_sha256"], canonical_hash(issue["observed_prefix"]))
        self.assertEqual(issue["input_manifest_sha256"], canonical_hash(issue_manifest(issue)))
        reconstructed = {key: self.event[key] for key in ("ticket_event_id", "club_slug", "kickoff_at")}
        reconstructed["observations"] = issue["observed_prefix"]
        rebuilt = build_issue(reconstructed, self.issue_at)
        self.assertEqual(issue["input_manifest_sha256"], rebuilt["input_manifest_sha256"])
        self.event["observations"][0]["available_total"] += 1
        self.assertNotEqual(issue["input_manifest_sha256"], build_issue(self.event, self.issue_at)["input_manifest_sha256"])

    def test_duplicate_event_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            build_dataset([self.event, self.event], self.issue_at)

    def test_empty_and_short_prefix_are_preserved_as_failed_attempts(self):
        empty = deepcopy(self.event)
        empty["observations"] = []
        issue = build_issue(empty, self.issue_at)
        self.assertEqual(issue["status"], "NO_OBSERVATIONS")
        self.assertEqual(issue["observed_prefix"], [])
        short = deepcopy(self.event)
        short["observations"] = short["observations"][-3:]
        self.assertEqual(build_issue(short, self.issue_at)["status"], "INSUFFICIENT_OBSERVATIONS")


if __name__ == "__main__":
    unittest.main()
