#!/usr/bin/env python3
import copy
import unittest

import numpy as np
import pandas as pd

from ml.d2_stage2_reliability_gating_v1 import (
    MIN_RETAINED_LATEST_UPLIFT,
    MIN_RETAINED_WINDOW_UPLIFT,
    MIN_WORST_DEGRADATION_REDUCTION,
    POLICIES,
    RESERVED_HOLDOUT_EVENT_ID,
    add_causal_reliability_state,
    magnitude_reliability,
    maturity_reliability,
    policy_reliability,
    quality_reliability,
    select_stage2_policy,
)


class D2Stage2ReliabilityGatingV1Test(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        return pd.DataFrame({
            "ticket_event_id": [1, 1, 1, 3],
            "as_of_at": pd.to_datetime([
                "2026-10-01T00:00:00Z",
                "2026-10-01T06:00:00Z",
                "2026-10-01T12:00:00Z",
                "2026-10-02T00:00:00Z",
            ], utc=True),
            "hours_to_kickoff": [24.0, 18.0, 12.0, 6.0],
            "signal_ready": [1, 1, 1, 1],
            "feature_quality_good": [1, 1, 1, 1],
            "data_gap_detected": [0, 0, 0, 0],
            "unexplained_inventory_increase_flag": [0, 0, 0, 0],
            "release_activity_flag": [0, 0, 1, 0],
            "sector_coverage_change_flag": [0, 0, 0, 0],
            "max_visible_gap_hours": [2.0, 2.0, 2.0, 2.0],
            "actual_attendance": [10000, 10000, 10000, 12000],
        })

    def test_policy_family_is_frozen_p0_to_p5(self) -> None:
        self.assertEqual(
            [policy.id for policy in POLICIES],
            [
                "P0-frozen-v2",
                "P1-raw-ridge",
                "P2-observation-maturity",
                "P3-correction-magnitude",
                "P4-data-quality",
                "P5-combined-reliability",
            ],
        )

    def test_reserved_holdout_id_is_explicit(self) -> None:
        self.assertEqual(RESERVED_HOLDOUT_EVENT_ID, 5)

    def test_causal_observation_state_uses_only_row_order_within_event(self) -> None:
        frame = add_causal_reliability_state(self._frame())
        event1 = frame[frame["ticket_event_id"] == 1]
        self.assertEqual(event1["stage2_observation_index"].tolist(), [1, 2, 3])
        np.testing.assert_allclose(
            event1["stage2_observation_span_hours"].to_numpy(),
            np.array([0.0, 6.0, 12.0]),
        )

    def test_maturity_reliability_increases_with_evidence(self) -> None:
        frame = add_causal_reliability_state(self._frame())
        weights = maturity_reliability(frame)
        event1 = weights[:3]
        self.assertLess(event1[0], event1[1])
        self.assertLess(event1[1], event1[2])
        self.assertGreaterEqual(event1.min(), 0.0)
        self.assertLessEqual(event1.max(), 1.0)

    def test_magnitude_reliability_is_monotone_nonincreasing(self) -> None:
        delta = np.array([0.01, 0.03, 0.06, 0.09])
        weights = magnitude_reliability(delta)
        self.assertEqual(weights.tolist(), [1.0, 0.8, 0.55, 0.35])

    def test_quality_warnings_only_shrink_reliability(self) -> None:
        frame = self._frame()
        baseline = quality_reliability(frame)
        self.assertEqual(baseline.tolist(), [1.0, 1.0, 0.5, 1.0])
        bad = frame.copy()
        bad.loc[1, "data_gap_detected"] = 1
        warned = quality_reliability(bad)
        self.assertEqual(float(warned[1]), 0.25)
        self.assertTrue(np.all(warned <= 1.0))

    def test_reliability_does_not_depend_on_attendance_label(self) -> None:
        first = add_causal_reliability_state(self._frame())
        second = first.copy()
        second["actual_attendance"] = 999999
        ridge_delta = np.array([0.02, 0.04, -0.08, 0.01])
        for policy in POLICIES:
            np.testing.assert_allclose(
                policy_reliability(policy.id, first, ridge_delta),
                policy_reliability(policy.id, second, ridge_delta),
            )

    def test_combined_policy_never_exceeds_component_reliability(self) -> None:
        frame = add_causal_reliability_state(self._frame())
        ridge_delta = np.array([0.02, 0.04, 0.08, 0.01])
        combined = policy_reliability("P5-combined-reliability", frame, ridge_delta)
        maturity = policy_reliability("P2-observation-maturity", frame, ridge_delta)
        magnitude = policy_reliability("P3-correction-magnitude", frame, ridge_delta)
        quality = policy_reliability("P4-data-quality", frame, ridge_delta)
        self.assertTrue(np.all(combined <= maturity + 1e-12))
        self.assertTrue(np.all(combined <= magnitude + 1e-12))
        self.assertTrue(np.all(combined <= quality + 1e-12))

    def _selection_rows(self):
        frozen = {
            "policy_id": "P0-frozen-v2",
            "scorecard": {
                "latest_row_mae": 4000.0,
                "event_balanced_window_mae": 4000.0,
                "latest_mae_improvement": 0.0,
                "window_mae_improvement": 0.0,
                "worst_latest_event_degradation": 0.0,
            },
        }
        ridge = {
            "policy_id": "P1-raw-ridge",
            "scorecard": {
                "latest_row_mae": 3200.0,
                "event_balanced_window_mae": 3500.0,
                "latest_mae_improvement": 800.0,
                "window_mae_improvement": 500.0,
                "worst_latest_event_degradation": 4000.0,
            },
        }
        good = {
            "policy_id": "P3-correction-magnitude",
            "scorecard": {
                "latest_row_mae": 3400.0,
                "event_balanced_window_mae": 3650.0,
                "latest_mae_improvement": 600.0,
                "window_mae_improvement": 350.0,
                "worst_latest_event_degradation": 2500.0,
            },
        }
        weak_tail = {
            "policy_id": "P2-observation-maturity",
            "scorecard": {
                "latest_row_mae": 3300.0,
                "event_balanced_window_mae": 3600.0,
                "latest_mae_improvement": 700.0,
                "window_mae_improvement": 400.0,
                "worst_latest_event_degradation": 3500.0,
            },
        }
        return [frozen, ridge, good, weak_tail]

    def test_selector_requires_uplift_retention_and_material_tail_reduction(self) -> None:
        rows = self._selection_rows()
        result = select_stage2_policy(rows)
        self.assertTrue(result["stage2_policy_advanced"])
        self.assertEqual(result["selected_policy_id"], "P3-correction-magnitude")
        self.assertEqual(result["eligible_policy_ids"], ["P3-correction-magnitude"])
        self.assertEqual(MIN_RETAINED_LATEST_UPLIFT, 0.50)
        self.assertEqual(MIN_RETAINED_WINDOW_UPLIFT, 0.50)
        self.assertEqual(MIN_WORST_DEGRADATION_REDUCTION, 0.25)

    def test_selector_retains_raw_ridge_if_no_policy_passes(self) -> None:
        rows = self._selection_rows()
        rows = copy.deepcopy(rows)
        rows[2]["scorecard"]["worst_latest_event_degradation"] = 3900.0
        result = select_stage2_policy(rows)
        self.assertFalse(result["stage2_policy_advanced"])
        self.assertEqual(result["selected_policy_id"], "P1-raw-ridge")


if __name__ == "__main__":
    unittest.main()
