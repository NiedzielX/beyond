"""Real receipt clocks, source identity groups and first accepted future labels."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_receipt_dataset_v1 import ROOT, build_dataset


BASE = datetime(2026, 11, 1, tzinfo=timezone.utc)


def observation(identifier, hours, value):
    return {"snapshot_id": identifier, "captured_at": (BASE + timedelta(hours=hours)).isoformat(),
            "available_total": value, "measurement_key": "roboticket/roboticket"}


def fixture(rows, identifier=1, kickoff_days=5):
    return {"ticket_event_id": identifier, "club_slug": "club", "provider": "roboticket",
            "kickoff_at": (BASE + timedelta(days=kickoff_days, hours=12)).isoformat(),
            "observations": rows}


def receipt(hours, events):
    data = {"version": "daily-inventory-public-export-v1",
            "exported_at": (BASE + timedelta(hours=hours - .01)).isoformat(),
            "retrieved_at": (BASE + timedelta(hours=hours)).isoformat(), "events": events}
    data["export_sha256"] = _hash(data)
    return json.dumps(data).encode()


def registry(identifiers=(1,), same_source=False):
    return json.dumps([{"id": identifier, "provider": "roboticket", "club_slug": "club",
                        "source_domain": "bilety.club.test",
                        "external_event_id": "physical-event" if same_source else str(identifier)}
                       for identifier in identifiers]).encode()


class ReceiptDatasetTests(unittest.TestCase):
    def setUp(self):
        self.first = receipt(.1, [fixture([observation(1, 0, 1000)])])
        self.last_rows = [observation(1, 0, 1000), observation(2, 24.05, 900),
                          observation(3, 48.05, 800), observation(4, 72.05, 700)]
        self.last = receipt(72.3, [fixture(self.last_rows)])

    def build(self, receipts=None, identity=None):
        return build_dataset([self.first, self.last] if receipts is None else receipts,
                             registry() if identity is None else identity)

    def test_original_receipt_issues_and_late_labels_have_distinct_actual_clocks(self):
        result = self.build()
        self.assertEqual(len(result["rows"]), 3)
        for row in result["rows"]:
            self.assertEqual(set(row), {"issue", "matched_label", "fixture_group", "source_lineage"})
            self.assertEqual(row["issue"]["issued_at"], (BASE + timedelta(hours=.1)).isoformat())
            self.assertEqual(row["issue"]["observed_prefix"][0]["known_at"], row["issue"]["issued_at"])
            self.assertEqual(row["matched_label"]["label"]["known_at"], (BASE + timedelta(hours=72.3)).isoformat())
            self.assertEqual(row["source_lineage"]["label_receipt_known_at"], row["matched_label"]["available_by"])
            self.assertTrue(row["source_lineage"]["identity_proven"])
        self.assertFalse(result["model_fit_performed"])
        self.assertEqual(result["prospective_forecasts_created"], 0)
        self.assertGreater(result["coverage"]["one_observation_input_count"], 0)

    def test_label_before_nominal_target_is_not_accepted_then_first_legal_is_immutable(self):
        older = [observation(1, 0, 1000), observation(2, 18.2, 950)]
        pre_target = receipt(19, [fixture(older)])
        first_mature = receipt(25, [fixture(older)])
        later_better = receipt(30, [fixture(older + [observation(3, 24.05, 800)])])
        result = self.build([self.first, pre_target, first_mature, later_better])
        row = next(r for r in result["rows"] if r["issue"]["issued_at"] == (BASE + timedelta(hours=.1)).isoformat()
                   and r["matched_label"]["horizon_hours"] == 24)
        self.assertEqual(row["matched_label"]["label"]["snapshot_id"], 2)
        self.assertEqual(row["source_lineage"]["label_receipt_known_at"], (BASE + timedelta(hours=25)).isoformat())
        self.assertAlmostEqual(row["matched_label"]["label"]["target_staleness_hours"], 5.9)

    def test_after_cutoff_receipt_cannot_supply_training_labels(self):
        future = json.loads(self.last)
        future["retrieved_at"] = "2026-12-01T00:00:00+00:00"
        future["exported_at"] = future["retrieved_at"]
        future["export_sha256"] = "future-payload-not-inspected"
        result = self.build([self.first, json.dumps(future).encode()])
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["coverage"]["receipts_after_cutoff_excluded"], 1)

    def test_source_hash_and_receipt_capture_clocks_are_checked(self):
        data = json.loads(self.first)
        data["events"][0]["observations"][0]["available_total"] = 1
        with self.assertRaisesRegex(ValueError, "manifest hash"):
            self.build([json.dumps(data).encode()])
        data = json.loads(self.first)
        data["exported_at"] = (BASE - timedelta(hours=1)).isoformat()
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        with self.assertRaisesRegex(ValueError, "Snapshot follows"):
            self.build([json.dumps(data).encode()])
        data = json.loads(self.first)
        data["retrieved_at"] = BASE.isoformat()
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        with self.assertRaisesRegex(ValueError, "precedes"):
            self.build([json.dumps(data).encode()])

    def test_exact_duplicate_receipts_do_not_multiply_support(self):
        one = self.build()
        two = self.build([self.first, self.first, self.last])
        self.assertEqual(one["rows"], two["rows"])
        self.assertEqual(two["coverage"]["original_receipt_count"], 2)
        self.assertEqual(two["coverage"]["duplicate_receipt_files"], 1)

    def test_different_receipts_at_identical_actual_clock_are_conflict(self):
        data = json.loads(self.first)
        data["events"][0]["observations"][0]["available_total"] = 123
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        with self.assertRaisesRegex(ValueError, "share an issue timestamp"):
            self.build([self.first, json.dumps(data).encode()])

    def test_later_revision_of_original_snapshot_invalidates_its_training_group(self):
        changed = deepcopy(self.last_rows)
        changed[0]["available_total"] = 999
        revision = receipt(73, [fixture(changed)])
        result = self.build([self.first, self.last, revision])
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["coverage"]["rows_excluded_for_snapshot_revision"], 3)
        self.assertEqual(len(result["coverage"]["snapshot_revision_conflict_groups"]), 1)

    def test_aliases_share_one_group_and_one_input_per_receipt(self):
        first_events, last_events = [], []
        for identifier in (1, 2):
            first_rows = [observation(1 + 100 * identifier, 0, 1000)]
            last_rows = [{**row, "snapshot_id": row["snapshot_id"] + 100 * identifier} for row in self.last_rows]
            first_events.append(fixture(first_rows, identifier=identifier))
            last_events.append(fixture(last_rows, identifier=identifier))
        first, last = receipt(.1, first_events), receipt(72.3, last_events)
        result = self.build([first, last], registry((1, 2), same_source=True))
        self.assertEqual(len(result["rows"]), 3)
        self.assertEqual(len(result["fixture_groups"]), 1)
        self.assertEqual({r["issue"]["event"]["ticket_event_id"] for r in result["rows"]}, {1})
        self.assertEqual(result["coverage"]["per_horizon"]["72"]["fixture_group_count"], 1)
        self.assertEqual(result["coverage"]["input_status_counts"]["DUPLICATE_ALIAS_ISSUE_EXCLUDED"], 2)

    def test_global_snapshot_cannot_prove_two_different_fixture_owners(self):
        first = receipt(.1, [fixture([observation(1, 0, 1000)], identifier=i) for i in (1, 2)])
        last = receipt(72.3, [fixture(self.last_rows, identifier=i) for i in (1, 2)])
        result = self.build([first, last], registry((1, 2)))
        self.assertEqual(result["rows"], [])
        self.assertEqual(len(result["coverage"]["snapshot_revision_conflict_groups"]), 2)

    def test_label_source_provider_must_still_match_real_registry(self):
        changed = fixture(self.last_rows)
        changed["provider"] = "unverified-provider"
        result = self.build([self.first, receipt(72.3, [changed])])
        self.assertEqual(result["rows"], [])
        self.assertGreater(result["coverage"]["label_attempt_status_counts"]["REGISTRY_LABEL_SOURCE_IDENTITY_MISMATCH"], 0)

    def test_unresolved_or_mismatched_source_identity_has_no_independent_support(self):
        identity = json.loads(registry())
        del identity[0]["external_event_id"]
        result = self.build(identity=json.dumps(identity).encode())
        self.assertEqual(result["rows"], [])
        self.assertGreater(result["coverage"]["input_status_counts"]["SOURCE_IDENTITY_UNKNOWN"], 0)
        identity = json.loads(registry())
        identity[0]["provider"] = "other-provider"
        result = self.build(identity=json.dumps(identity).encode())
        self.assertEqual(result["rows"], [])
        self.assertGreater(result["coverage"]["input_status_counts"]["REGISTRY_SOURCE_IDENTITY_MISMATCH"], 0)

    def test_ongoing_fixture_remains_out_of_training(self):
        first = receipt(.1, [fixture([observation(1, 0, 1000)], kickoff_days=30)])
        last = receipt(72.3, [fixture(self.last_rows, kickoff_days=30)])
        result = self.build([first, last])
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["coverage"]["input_status_counts"]["ONGOING_FIXTURE_EXCLUDED"], 2)

    def test_changed_metadata_and_pool_cannot_be_used_as_same_future_target(self):
        changed = receipt(72.3, [fixture(self.last_rows, kickoff_days=6)])
        result = self.build([self.first, changed])
        self.assertEqual(result["rows"], [])
        self.assertGreater(result["coverage"]["label_attempt_status_counts"]["EVENT_METADATA_CHANGED"], 0)
        rows = deepcopy(self.last_rows)
        rows[1]["measurement_key"] = "other-pool"
        result = self.build([self.first, receipt(72.3, [fixture(rows)])])
        self.assertEqual(result["rows"], [])
        self.assertGreater(result["coverage"]["label_attempt_status_counts"]["MEASUREMENT_CHANGED"], 0)

    def test_latest_invalid_target_does_not_fall_back_to_older_good_point(self):
        rows = deepcopy(self.last_rows)
        rows.insert(1, observation(5, 20, 950))
        rows[2]["available_total"] = None
        result = self.build([self.first, receipt(72.3, [fixture(rows)])])
        self.assertNotIn(24, {r["matched_label"]["horizon_hours"] for r in result["rows"]})
        self.assertGreater(result["coverage"]["label_attempt_status_counts"]["INVALID_TARGET_OBSERVATION"], 0)

    def test_original_files_remain_bound_and_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / str(i) for i in range(2)]
            paths[0].write_bytes(self.first); paths[1].write_bytes(self.last)
            one = self.build(paths)
            two = self.build(list(reversed(paths)))
            self.assertEqual(one, two)
            self.assertEqual(one["dataset_sha256"], _hash({k: v for k, v in one.items() if k != "dataset_sha256"}))

    def test_source_mutation_between_metadata_pass_and_processing_fails(self):
        with patch("ml.rolling72_receipt_dataset_v1._payload", side_effect=[self.first, self.last, b"changed"]):
            with self.assertRaisesRegex(ValueError, "changed while"):
                self.build()

    def test_duplicate_event_and_snapshot_id_cannot_create_extra_rows(self):
        duplicate_events = receipt(.1, [fixture([observation(1, 0, 1000)])] * 2)
        with self.assertRaisesRegex(ValueError, "Duplicate event"):
            self.build([duplicate_events])
        duplicate_rows = receipt(.1, [fixture([observation(1, 0, 1000)] * 2)])
        with self.assertRaisesRegex(ValueError, "Duplicate snapshot"):
            self.build([duplicate_rows])

    def test_cli_writes_only_a_new_private_dataset_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "public-export-first.json").write_bytes(self.first)
            (root / "public-export-last.json").write_bytes(self.last)
            identity = root / "identity.json"
            identity.write_bytes(registry())
            output = root / "dataset.json"
            command = [sys.executable, "-m", "ml.rolling72_receipt_dataset_v1",
                       "--inputsdir", str(root), "--identity-registry", str(identity), "--output", str(output)]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(len(json.loads(output.read_text())["rows"]), 3)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            original = output.read_bytes()
            repeated = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("already exists", repeated.stderr)
            self.assertEqual(output.read_bytes(), original)

    def test_input_counts_and_horizon_counts_are_distinct_denominators(self):
        data = build_dataset([receipt(0, [fixture([observation(1, -.1, 100)], kickoff_days=2)])],
                             registry())
        coverage = data["coverage"]
        self.assertEqual(sum(coverage["input_status_counts"].values()), 1)
        self.assertNotIn("TARGET_NOT_BEFORE_KICKOFF", coverage["input_status_counts"])
        self.assertEqual(coverage["coordinate_status_counts"], {"READY": 2, "TARGET_NOT_BEFORE_KICKOFF": 1})
        self.assertEqual(coverage["mature_missing_target_count"], 2)
        self.assertEqual(coverage["pending_target_count"], 0)

    def test_cli_refuses_private_training_output_inside_the_repository(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "forbidden.json"
            run = subprocess.run([sys.executable, "-m", "ml.rolling72_receipt_dataset_v1",
                                  "--inputsdir", "/does-not-exist", "--identity-registry", "/does-not-exist",
                                  "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("outside Git", run.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
