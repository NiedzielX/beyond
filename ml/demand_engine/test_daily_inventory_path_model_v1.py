from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from ml.demand_engine.daily_inventory_path_model_v1 import (
    FEATURE_COUNT, MODEL_VERSION, artifact_sha256, evaluate_points,
    fit_model, load_model, make_features, predict_path, save_model,
)


UTC = timezone.utc


def issue(event_id=99, *, kickoff=None, days=40, last=1000.0):
    kickoff = kickoff or datetime(2027, 2, 20, 18, tzinfo=UTC)
    issued = kickoff - timedelta(days=days)
    offsets = [timedelta(days=10), timedelta(days=5), timedelta(days=1), timedelta(hours=1)]
    observations = [{
        "snapshot_id": event_id * 100 + index + 1,
        "captured_at": (issued - offset).isoformat(),
        "available_total": last + (3 - index) * 20,
        "measurement_key": "public-inventory-v1",
    } for index, offset in enumerate(offsets)]
    return {
        "status": "READY", "ticket_event_id": event_id,
        "club_slug": f"club-{event_id % 3}", "kickoff_at": kickoff.isoformat(),
        "issued_as_of_at": issued.isoformat(), "days_to_event": days,
        "measurement_key": "public-inventory-v1", "observed_prefix": observations,
        "latest_captured_at": observations[-1]["captured_at"],
        "last_available_total": float(last),
        "prefix_sha256": "a" * 64, "input_manifest_sha256": "b" * 64,
    }


def label(current_issue, lead, actual):
    target = datetime.fromisoformat(current_issue["issued_as_of_at"]) + timedelta(days=lead)
    return {
        "issue": current_issue, "lead_days": lead, "target_at": target.isoformat(),
        "target_available_total": float(actual),
        "target_snapshot_id": current_issue["ticket_event_id"] * 10000 + lead,
        "target_captured_at": target.isoformat(), "measurement_key": "public-inventory-v1",
    }


def training_rows():
    rows = []
    for event_id in range(1, 7):
        current_issue = issue(event_id, kickoff=datetime(2026, 10, 1 + event_id, 18, tzinfo=UTC))
        for lead in (1, 10, 20, 30, 39):
            rows.append(label(current_issue, lead, 1000 + 25 * lead))
    return rows


class DailyInventoryPathFeaturesTest(unittest.TestCase):
    def test_full_prefix_and_missing_masks_are_retained(self):
        current_issue = issue()
        features = make_features(current_issue, 7)
        self.assertEqual(features.shape, (FEATURE_COUNT,))
        self.assertEqual(features[5 + 10], 60 / 1060)
        self.assertEqual(features[5 + 60 + 10], 1)
        self.assertEqual(features[5 + 8], 0)
        self.assertEqual(features[5 + 60 + 8], 0)
        self.assertEqual(features[0], 1.0)
        self.assertEqual(features[125 + 5 + 60 + 10], 1)
        np.testing.assert_array_equal(features[:125], features[125:])
        # Removing a >168h observation changes features, not just lineage.
        shorter = deepcopy(current_issue)
        shorter["observed_prefix"][0]["captured_at"] = (
            datetime.fromisoformat(current_issue["issued_as_of_at"]) - timedelta(days=6)
        ).isoformat()
        self.assertFalse(np.array_equal(features, make_features(shorter, 7)))

    def test_genuine_zero_has_observed_mask(self):
        current_issue = issue(last=0)
        features = make_features(current_issue, 7)
        self.assertEqual(features[5], 0)
        self.assertEqual(features[5 + 60], 1)
        self.assertTrue(np.isfinite(features).all())

    def test_future_hidden_and_changed_measurements_fail_closed(self):
        for mutation in ("future", "hidden", "measurement", "nan"):
            with self.subTest(mutation=mutation):
                current_issue = issue()
                if mutation == "future":
                    current_issue["observed_prefix"][-1]["captured_at"] = (
                        datetime.fromisoformat(current_issue["issued_as_of_at"]) + timedelta(seconds=1)
                    ).isoformat()
                elif mutation == "hidden":
                    current_issue["observed_prefix"][-1]["source_visible"] = False
                elif mutation == "measurement":
                    current_issue["observed_prefix"][0]["measurement_key"] = "other"
                else:
                    current_issue["observed_prefix"][0]["available_total"] = float("nan")
                with self.assertRaises(ValueError):
                    make_features(current_issue, 1)

    def test_invalid_leads_and_naive_timestamps_are_rejected(self):
        for lead in (0, 40, True, 1.0):
            with self.subTest(lead=lead), self.assertRaises(ValueError):
                make_features(issue(), lead)
        current_issue = issue()
        current_issue["issued_as_of_at"] = current_issue["issued_as_of_at"][:19]
        with self.assertRaises(ValueError):
            make_features(current_issue, 1)


class DailyInventoryPathModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Only synthetic examples are fitted in this test suite.
        cls.artifact = fit_model(training_rows(), "2026-11-01T00:00:00+00:00")

    def test_learned_direct_predictions_cover_each_remaining_day(self):
        current_issue = issue()
        points = predict_path(current_issue, self.artifact)
        self.assertEqual(len(points), 39)
        self.assertEqual([point["lead_days"] for point in points], list(range(1, 40)))
        self.assertLess(points[0]["predicted_available_total"], points[-1]["predicted_available_total"])
        self.assertGreater(points[-1]["predicted_available_total"], points[-1]["baseline_available_total"])
        self.assertEqual(points[-1]["target_at"], (
            datetime.fromisoformat(current_issue["kickoff_at"]) - timedelta(days=1)
        ).isoformat())
        self.assertTrue(all(point["evidence_kind"] == "research_preview_not_prospective" for point in points))
        self.assertTrue(all(point["production_change"] is False for point in points))

    def test_event_overlap_and_training_after_issue_are_rejected(self):
        with self.assertRaises(ValueError):
            predict_path(issue(1), self.artifact)
        historical = issue(100, kickoff=datetime(2026, 10, 20, 18, tzinfo=UTC))
        with self.assertRaises(ValueError):
            predict_path(historical, self.artifact)

    def test_lead_interactions_allow_prefix_conditioned_slopes_and_curvature(self):
        # Construct coefficients to test the model's representation capacity,
        # without selecting or comparing any fitted candidate on outcomes.
        artifact = deepcopy(self.artifact)
        artifact["coefficients"] = [0.0] * FEATURE_COUNT
        artifact["coefficients"][5 + 10] = .5
        artifact["coefficients"][125 + 5 + 10] = .25
        artifact["model_sha256"] = artifact_sha256(artifact)
        first = issue()
        second = deepcopy(first)
        second["observed_prefix"][0]["available_total"] += 240
        path_a, path_b = predict_path(first, artifact), predict_path(second, artifact)
        slope_a = path_a[1]["predicted_available_total"] - path_a[0]["predicted_available_total"]
        slope_b = path_b[1]["predicted_available_total"] - path_b[0]["predicted_available_total"]
        self.assertNotAlmostEqual(slope_a, slope_b)
        next_slope_a = path_a[2]["predicted_available_total"] - path_a[1]["predicted_available_total"]
        self.assertNotAlmostEqual(slope_a, next_slope_a)

    def test_zero_intercept_is_enforced_even_with_rehashed_artifact(self):
        artifact = deepcopy(self.artifact)
        artifact["intercept"] = 1.0
        artifact["model_sha256"] = artifact_sha256(artifact)
        with self.assertRaises(ValueError):
            predict_path(issue(), artifact)

    def test_training_cutoff_and_label_timestamp_prevent_future_leakage(self):
        rows = training_rows()
        with self.assertRaises(ValueError):
            fit_model(rows, "2026-09-01T00:00:00+00:00")
        rows[0]["target_captured_at"] = (
            datetime.fromisoformat(rows[0]["target_at"]) + timedelta(seconds=1)
        ).isoformat()
        with self.assertRaises(ValueError):
            fit_model(rows, "2026-11-01T00:00:00+00:00")

    def test_minimum_independent_events_and_duplicate_identities(self):
        rows = training_rows()
        with self.assertRaises(ValueError):
            fit_model([row for row in rows if row["issue"]["ticket_event_id"] < 5], "2026-11-01T00:00:00+00:00")
        with self.assertRaises(ValueError):
            fit_model(rows + [rows[0]], "2026-11-01T00:00:00+00:00")

    def test_future_label_cannot_reuse_an_input_snapshot_identity(self):
        rows = training_rows()
        rows[0]["target_snapshot_id"] = rows[0]["issue"]["observed_prefix"][-1]["snapshot_id"]
        with self.assertRaises(ValueError):
            fit_model(rows, "2026-11-01T00:00:00+00:00")

    def test_artifact_roundtrip_hash_and_no_overwrite(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            save_model(self.artifact, path)
            save_model(self.artifact, path)  # Identical retry is idempotent.
            restored = load_model(path)
            self.assertEqual(restored["model_sha256"], self.artifact["model_sha256"])
            self.assertEqual(predict_path(issue(), restored), predict_path(issue(), self.artifact))
            tampered = json.loads(path.read_text())
            tampered["intercept"] += 1
            path.write_text(json.dumps(tampered))
            with self.assertRaises(ValueError):
                load_model(path)
            with self.assertRaises(ValueError):
                predict_path(issue(), tampered)
            tampered["model_sha256"] = artifact_sha256(tampered)
            path.write_text(json.dumps(self.artifact))
            with self.assertRaises(ValueError):
                save_model(tampered, path)

    def test_later_issue_creates_new_vintage_without_mutating_old_points(self):
        first = issue()
        old_points = predict_path(first, self.artifact)
        original = deepcopy(old_points)
        next_issue = issue(days=39, last=1300)
        new_points = predict_path(next_issue, self.artifact)
        self.assertEqual(old_points, original)
        self.assertEqual(len(new_points), len(old_points) - 1)
        self.assertNotEqual(old_points[1]["issued_as_of_at"], new_points[0]["issued_as_of_at"])
        self.assertEqual(old_points[1]["target_at"], new_points[0]["target_at"])


class DailyInventoryPathMetricsTest(unittest.TestCase):
    def _paired(self):
        rows, points = [], []
        for event_id, count, latest, prediction in ((90, 10, 120, 110), (91, 1, 300, 200)):
            current_issue = issue(event_id, days=40, last=latest)
            for lead in range(1, count + 1):
                row = label(current_issue, lead, 100)
                rows.append(row)
                points.append({
                    "ticket_event_id": event_id, "issued_as_of_at": current_issue["issued_as_of_at"],
                    "target_at": row["target_at"], "lead_days": lead,
                    "predicted_available_total": prediction, "baseline_available_total": latest,
                    "measurement_key": current_issue["measurement_key"], "model_version": MODEL_VERSION,
                })
        return rows, points

    def test_equal_event_mae_does_not_reward_many_correlated_points(self):
        rows, points = self._paired()
        metrics = evaluate_points(points, rows)
        self.assertEqual(metrics["scored_event_count"], 2)
        self.assertEqual(metrics["point_count"], 11)
        self.assertEqual(metrics["challenger_event_balanced_mae"], 55)
        self.assertEqual(metrics["baseline_event_balanced_mae"], 110)
        self.assertEqual(metrics["delta_mae"], -55)
        self.assertEqual(metrics["challenger_signed_bias"], 55)
        self.assertEqual(metrics["per_lead"]["1"]["scored_event_count"], 2)
        self.assertEqual(metrics["per_lead"]["3"]["scored_event_count"], 1)
        self.assertEqual(metrics["per_lead"]["7"]["scored_event_count"], 1)

    def test_coverage_reports_unmatched_predictions_without_filling_labels(self):
        rows, points = self._paired()
        metrics = evaluate_points(points, rows[:-1])
        self.assertEqual(metrics["unmatched_prediction_count"], 1)
        self.assertEqual(metrics["prediction_label_coverage"], 10 / 11)
        self.assertEqual(metrics["scored_event_count"], 1)
        empty = evaluate_points([], [])
        self.assertIsNone(empty["challenger_event_balanced_mae"])
        self.assertEqual(set(empty["per_lead"]), {"1", "3", "7"})

    def test_duplicate_predictions_and_mixed_lanes_are_rejected(self):
        rows, points = self._paired()
        with self.assertRaises(ValueError):
            evaluate_points(points + [points[0]], rows)
        points[-1]["model_version"] = "another-model"
        with self.assertRaises(ValueError):
            evaluate_points(points, rows)


if __name__ == "__main__":
    unittest.main()
