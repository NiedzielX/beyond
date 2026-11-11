from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ml.demand_engine.daily_inventory_path_dataset_v1 import (
    build_issue,
    canonical_hash,
    issue_manifest,
)
from ml.demand_engine.daily_inventory_path_ledger_v1 import (
    DailyInventoryPathLedger,
    EVIDENCE_KIND,
)
from ml.demand_engine.daily_inventory_path_model_v1 import (
    ALPHA, BASELINE_VERSION, FEATURE_COUNT, FEATURE_VERSION, MODEL_VERSION,
    PRECOMMIT_ID, QUANTILE, predict_path,
)


UTC = timezone.utc


class DailyInventoryPathLedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = DailyInventoryPathLedger(Path(self.tmp.name) / "ledger.sqlite")
        self.kickoff = datetime(2026, 12, 10, 20, tzinfo=UTC)
        self.issued = self.kickoff - timedelta(days=3)
        self.event = {
            "ticket_event_id": 101,
            "club_slug": "test-club",
            "kickoff_at": self.kickoff.isoformat(),
            "observations": [self.observation(index, self.issued + timedelta(hours=offset), 130 - 10 * index)
                             for index, offset in enumerate((-30, -20, -10, 0), start=1)],
        }
        self.issue = build_issue(self.event, self.issued)
        self.assertEqual(self.issue["status"], "READY")
        self.artifact = self.seal({
            "model_version": MODEL_VERSION,
            "baseline_version": BASELINE_VERSION,
            "feature_version": FEATURE_VERSION,
            "feature_count": FEATURE_COUNT,
            "precommit_id": PRECOMMIT_ID,
            "target_kind": "available_total",
            "unit": "places",
            "quantile": QUANTILE,
            "alpha": ALPHA,
            "solver": "highs",
            "fit_intercept": False,
            "trained_through": (self.issued - timedelta(days=1)).isoformat(),
            "fitted_at": (self.issued - timedelta(hours=12)).isoformat(),
            "training_event_ids": [1, 2, 3, 4, 5],
            "training_club_count": 5,
            "training_row_count": 5,
            "training_manifest_sha256": "a" * 64,
            "sklearn_version": "unit-test-fixture",
            "coefficients": [0.0] * FEATURE_COUNT,
            "intercept": 0.0,
            "production_change": False,
            "live_adjustment": 0,
        })
        self.points = self.make_points(self.issue)

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    @staticmethod
    def observation(snapshot_id, captured_at, value, key="public-test-v1"):
        return {"snapshot_id": snapshot_id, "captured_at": captured_at.isoformat(),
                "available_total": value, "measurement_key": key,
                "source_active": True, "source_visible": True}

    @staticmethod
    def seal(artifact):
        result = {key: value for key, value in artifact.items() if key != "model_sha256"}
        result["model_sha256"] = hashlib.sha256(
            json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        return result

    def make_points(self, issue):
        return predict_path(issue, self.artifact)

    def record(self, **overrides):
        return self.ledger.record(overrides.get("issue", self.issue), overrides.get("points", self.points),
                                  overrides.get("artifact", self.artifact),
                                  overrides.get("executed_at", self.issued))

    def test_exact_execution_boundaries_and_first_execution_preserved(self):
        first = self.record()
        retry = self.record(executed_at=self.issued + timedelta(minutes=90))
        self.assertTrue(first["inserted"])
        self.assertFalse(retry["inserted"])
        self.assertEqual(retry["executed_at"], self.issued.isoformat())
        self.assertEqual(len(self.ledger.export_points()), 2)
        self.assertEqual(self.ledger.export_points()[0]["evidence_kind"], EVIDENCE_KIND)

    def test_before_cutoff_and_after_window_refused_including_retry(self):
        for execution in (self.issued - timedelta(microseconds=1),
                          self.issued + timedelta(minutes=90, microseconds=1)):
            with self.assertRaisesRegex(ValueError, "90 minutes"):
                self.record(executed_at=execution)
        self.assertEqual(self.ledger.export_attempts(), [])
        self.record()
        with self.assertRaisesRegex(ValueError, "90 minutes"):
            self.record(executed_at=self.issued + timedelta(hours=2))

    def test_conflicting_retry_does_not_overwrite_prior_vintage(self):
        self.record()
        artifact = deepcopy(self.artifact)
        artifact["coefficients"][0] = -0.1
        artifact = self.seal(artifact)
        points = predict_path(self.issue, artifact)
        with self.assertRaisesRegex(ValueError, "Conflicting retry"):
            self.record(points=points, artifact=artifact, executed_at=self.issued + timedelta(minutes=10))
        self.assertEqual(self.ledger.export_points()[0]["predicted_available_total"],
                         self.points[0]["predicted_available_total"])
        self.assertEqual(len(self.ledger.export_attempts()), 1)

    def test_forged_prediction_with_correct_model_hash_is_refused(self):
        points = deepcopy(self.points)
        points[0]["predicted_available_total"] += 1
        with self.assertRaisesRegex(ValueError, "frozen artifact output"):
            self.record(points=points)
        self.assertEqual(self.ledger.export_attempts(), [])

    def test_valid_hash_does_not_allow_different_model_contract(self):
        artifact = deepcopy(self.artifact)
        artifact["alpha"] = 123
        artifact = self.seal(artifact)
        with self.assertRaisesRegex(ValueError, "precommitted contract"):
            self.record(artifact=artifact)

    def test_bad_or_incomplete_path_is_atomic(self):
        with self.assertRaisesRegex(ValueError, "every remaining"):
            self.record(points=self.points[:1])
        points = deepcopy(self.points)
        points[1]["target_at"] = self.kickoff.isoformat()
        with self.assertRaisesRegex(ValueError, "future daily cutoff"):
            self.record(points=points)
        self.assertEqual(self.ledger.export_attempts(), [])
        self.assertEqual(self.ledger.export_points(), [])

    def test_model_training_and_fit_timestamps_must_precede_issue(self):
        for name in ("trained_through", "fitted_at"):
            artifact = deepcopy(self.artifact)
            artifact[name] = (self.issued + timedelta(seconds=1)).isoformat()
            artifact = self.seal(artifact)
            with self.assertRaisesRegex(ValueError, "precede issue"):
                self.record(artifact=artifact)
        artifact = deepcopy(self.artifact)
        artifact["training_event_ids"].append(101)
        artifact = self.seal(artifact)
        with self.assertRaisesRegex(ValueError, "used in training"):
            self.record(artifact=artifact)

    def test_artifact_and_prefix_tampering_refused(self):
        artifact = deepcopy(self.artifact)
        artifact["training_event_ids"] = [6, 7, 8, 9, 10]
        with self.assertRaisesRegex(ValueError, "artifact hash"):
            self.record(artifact=artifact)
        issue = deepcopy(self.issue)
        issue["observed_prefix"][0]["available_total"] += 1
        with self.assertRaisesRegex(ValueError, "input hash"):
            self.record(issue=issue)

    def test_rehashed_future_prefix_still_refused(self):
        issue = deepcopy(self.issue)
        issue["observed_prefix"][-1]["captured_at"] = (self.issued + timedelta(seconds=1)).isoformat()
        issue["prefix_sha256"] = canonical_hash(issue["observed_prefix"])
        issue["input_manifest_sha256"] = canonical_hash(issue_manifest(issue))
        with self.assertRaisesRegex(ValueError, "genuine issue prefix"):
            self.record(issue=issue)

    def test_latest_inventory_metadata_cannot_forge_baseline(self):
        issue = deepcopy(self.issue)
        issue["last_available_total"] = 999
        points = deepcopy(self.points)
        for point in points:
            point["baseline_available_total"] = 999
        with self.assertRaisesRegex(ValueError, "Latest inventory lineage"):
            self.record(issue=issue, points=points)

    def test_noncanonical_issue_and_baseline_refused(self):
        issue = deepcopy(self.issue)
        issue["issued_as_of_at"] = (self.issued + timedelta(minutes=1)).isoformat()
        with self.assertRaisesRegex(ValueError, "exact daily cutoff"):
            self.record(issue=issue)
        points = deepcopy(self.points)
        points[0]["baseline_available_total"] += 1
        with self.assertRaisesRegex(ValueError, "Persistence baseline"):
            self.record(points=points)

    def test_failed_input_attempt_persisted_without_predictions(self):
        event = {**self.event, "observations": []}
        issue = build_issue(event, self.issued)
        self.assertEqual(issue["status"], "NO_OBSERVATIONS")
        result = self.record(issue=issue, points=[])
        self.assertEqual(result["point_count"], 0)
        self.assertEqual(self.ledger.export_attempts()[0]["issue"]["status"], "NO_OBSERVATIONS")
        with self.assertRaisesRegex(ValueError, "Failed-input"):
            self.record(issue=issue)

    def test_nan_and_negative_predictions_refused(self):
        for value in (float("nan"), float("inf"), -1):
            points = deepcopy(self.points)
            points[0]["predicted_available_total"] = value
            with self.assertRaises(ValueError):
                self.record(points=points)
        self.assertEqual(self.ledger.export_attempts(), [])

    def test_daily_vintages_preserve_previous_predictions(self):
        self.record()
        next_issue_at = self.issued + timedelta(days=1)
        event = deepcopy(self.event)
        event["observations"].append(self.observation(5, next_issue_at, 70))
        next_issue = build_issue(event, next_issue_at)
        self.record(issue=next_issue, points=self.make_points(next_issue), executed_at=next_issue_at)
        points = self.ledger.export_points(101)
        self.assertEqual(len(points), 3)
        self.assertEqual(len({point["issued_as_of_at"] for point in points}), 2)
        same_target = [point for point in points if point["target_at"] == self.points[1]["target_at"]]
        self.assertEqual(len(same_target), 2)
        self.assertNotEqual(same_target[0]["predicted_available_total"], same_target[1]["predicted_available_total"])

    def test_scoring_is_matched_temporal_and_immutable(self):
        self.record()
        target = self.issued + timedelta(days=1)
        event = deepcopy(self.event)
        event["observations"].extend([
            self.observation(10, target - timedelta(hours=1), 80),
            self.observation(11, target + timedelta(seconds=1), 1),
        ])
        early = self.ledger.score([event], target - timedelta(seconds=1))
        self.assertEqual(early["scored_count"], 0)
        result = self.ledger.score([event], target + timedelta(minutes=1))
        self.assertEqual(result["scored_count"], 1)
        scored = self.ledger.export_points()[0]["score"]
        self.assertEqual(scored["target_snapshot_id"], 10)
        self.assertEqual(scored["target_available_total"], 80)
        self.assertEqual(scored["candidate_abs_error"], abs(self.points[0]["predicted_available_total"] - 80))
        # A later imported/revised target observation must not rewrite a score.
        event["observations"].append(self.observation(12, target, 2))
        retry = self.ledger.score([event], target + timedelta(hours=1))
        self.assertEqual(retry["already_scored_count"], 1)
        self.assertEqual(self.ledger.export_points()[0]["score"]["target_snapshot_id"], 10)

    def test_missing_stale_or_changed_measurement_not_scored(self):
        self.record()
        target = self.issued + timedelta(days=1)
        for observation in (
            self.observation(10, target - timedelta(hours=6, seconds=1), 80),
            self.observation(10, target, 80, key="different-source"),
        ):
            event = deepcopy(self.event)
            event["observations"].append(observation)
            result = self.ledger.score([event], target)
            self.assertEqual(result["scored_count"], 0)
        self.assertIsNone(self.ledger.export_points()[0]["score"])

    def test_exact_six_hour_target_tolerance_and_literal_zero_valid(self):
        self.record()
        target = self.issued + timedelta(days=1)
        event = deepcopy(self.event)
        event["observations"].append(self.observation(10, target - timedelta(hours=6), 0))
        result = self.ledger.score([event], target)
        self.assertEqual(result["scored_count"], 1)
        self.assertEqual(self.ledger.export_points()[0]["score"]["target_available_total"], 0)

    def test_sql_update_and_delete_blocked(self):
        self.record()
        for sql in ("UPDATE daily_path_points SET lead_days=7", "DELETE FROM daily_path_points",
                    "UPDATE daily_path_attempts SET executed_at='forged'"):
            with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable"):
                self.ledger._conn.execute(sql)
            self.ledger._conn.rollback()
        self.assertEqual(len(self.ledger.export_points()), 2)


if __name__ == "__main__":
    unittest.main()
