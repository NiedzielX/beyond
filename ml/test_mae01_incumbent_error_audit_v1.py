import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ml.mae01_incumbent_error_audit_v1 import (
    add_segments, decompose, sha256, validate_rows, verify_sources,
)


def row(event="A", horizon="T-7", actual=100, predicted=110, **extra):
    kickoff = pd.Timestamp("2025-07-19T16:00Z")
    return {"match_key": event, "horizon": horizon, "target_attendance": actual,
            "prediction": predicted, "baseline": 120, "capacity": 200,
            "season": "2025/2026", "home_club_key": "home_"+event, "away_club_key": "away",
            "kickoff_at": kickoff, "as_of_at": kickoff-pd.Timedelta(days=int(horizon[2:])),
            "season_progress": .5, "home_history_n": 20, "opponent_draw_ratio_mean": None,
            "opponent_draw_n": 0, "away_position": None, **extra}


class ErrorAuditTests(unittest.TestCase):
    def test_equal_event_weight_despite_different_horizon_counts(self):
        frame = pd.DataFrame([row(), row(horizon="T-1", predicted=130), row("B", predicted=200)])
        report = decompose(frame)
        self.assertEqual(report["available_cohort"]["event_count"], 2)
        self.assertEqual(report["available_cohort"]["event_balanced_mae"], 60)
        self.assertEqual(report["available_cohort"]["row_count"], 3)
        self.assertEqual(report["common_five_horizon_cohort"]["event_count"], 0)
        for table in report["segments"].values():
            self.assertAlmostEqual(sum(x["contribution_to_overall_mae"] for x in table), 60)
            self.assertAlmostEqual(sum(x["effective_event_weight"] for x in table), 2)
            self.assertAlmostEqual(sum(x["error_share"] for x in table), 1)
        clubs = {item["value"]: item for item in report["segments"]["home_club_key"]}
        self.assertEqual(clubs["home_A"]["contribution_to_overall_mae"], 10)
        self.assertEqual(clubs["home_B"]["contribution_to_overall_mae"], 50)

    def test_common_cohort_requires_all_five_horizons(self):
        rows = [row(horizon=h) for h in ("T-30", "T-14", "T-7", "T-3", "T-1")]
        report = decompose(pd.DataFrame(rows+[row("B", predicted=200)]))
        self.assertEqual(report["common_five_horizon_cohort"]["event_count"], 1)
        self.assertEqual(report["common_five_horizon_cohort"]["event_balanced_mae"], 10)
        for result in report["common_cohort_per_horizon"].values():
            self.assertEqual(result["event_count"], 1)

    def test_duplicate_horizon_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            decompose(pd.DataFrame([row(), row()]))

    def test_target_and_club_consistency_rejected(self):
        for change in ({"actual": 101}, {"home_club_key": "other"}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "Inconsistent"):
                decompose(pd.DataFrame([row(), row(horizon="T-1", **change)]))

    def test_invalid_cutoff_rejected(self):
        with self.assertRaisesRegex(ValueError, "PIT"):
            validate_rows(pd.DataFrame([row(as_of_at="2025-07-19T16:00Z")]))

    def test_nonfinite_prediction_and_nonpositive_capacity_rejected(self):
        for change in ({"predicted": float("nan")}, {"capacity": 0}, {"predicted": -1}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "Invalid"):
                validate_rows(pd.DataFrame([row(**change)]))

    def test_true_zero_target_is_valid_and_bias_signed(self):
        report = decompose(pd.DataFrame([row(actual=0, predicted=0)]))
        self.assertEqual(report["available_cohort"]["event_balanced_mae"], 0)
        self.assertEqual(report["available_cohort"]["signed_bias"], 0)
        self.assertEqual(report["segments"]["error_direction"][0]["value"], "exact")

    def test_unknown_context_is_not_low_demand_or_bottom_club(self):
        segments = add_segments(pd.DataFrame([row()]))
        self.assertEqual(segments.iloc[0].opponent_draw_bucket, "unknown")
        self.assertEqual(segments.iloc[0].opponent_position_bucket, "unknown")

    def test_fill_boundary_and_overcapacity_are_explicit(self):
        rows = [row("A", actual=190), row("B", actual=200), row("C", actual=201)]
        segments = add_segments(pd.DataFrame(rows))
        self.assertEqual(segments.actual_fill_bucket.tolist(),
                         ["sellout-prone:95-100%", "sellout-prone:95-100%", "above-capacity"])
        report = decompose(pd.DataFrame(rows))
        event = next(x for x in report["worst_events"] if x["match_key"] == "C")
        self.assertIn("actual_above_capacity_map_requires_review", event["associations_only"])
        self.assertIn("event_specific_shock", event["unassessed"])

    def test_frozen_source_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/"history.csv").write_text("original\n")
            manifest = {"historical_runtime": {"filename": "history.csv", "sha256": sha256(path/"history.csv")},
                        "artifacts": {}}
            (path/"manifest.json").write_text(json.dumps(manifest))
            verify_sources(path)
            (path/"history.csv").write_text("changed\n")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verify_sources(path)


if __name__ == "__main__":
    unittest.main()
