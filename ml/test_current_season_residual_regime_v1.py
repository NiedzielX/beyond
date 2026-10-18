#!/usr/bin/env python3
import unittest

import numpy as np
import pandas as pd

from ml.current_season_residual_regime_v1 import (
    CORRECTION_CAP_SHARE_OF_CAPACITY,
    MIN_MEAN_RELATIVE_MAE_IMPROVEMENT,
    RegimeVariant,
    VARIANTS,
    add_same_season_residual_state,
    apply_variant,
    select_candidate,
)


class CurrentSeasonResidualRegimeV1Test(unittest.TestCase):
    def test_candidate_contract_is_fixed(self) -> None:
        self.assertEqual(len(VARIANTS), 9)
        self.assertEqual(len({variant.id for variant in VARIANTS}), 9)
        self.assertEqual(CORRECTION_CAP_SHARE_OF_CAPACITY, 0.05)
        self.assertEqual(MIN_MEAN_RELATIVE_MAE_IMPROVEMENT, 0.005)

    def test_prior_match_enters_state_only_after_completion_buffer(self) -> None:
        rows = pd.DataFrame({
            "match_key": ["m1", "m2", "m3"],
            "home_club_key": ["club", "club", "club"],
            "as_of_at": pd.to_datetime([
                "2026-01-01T10:00:00Z",
                "2026-01-10T14:00:00Z",
                "2026-01-10T16:00:00Z",
            ]),
            "kickoff_at": pd.to_datetime([
                "2026-01-10T12:00:00Z",
                "2026-02-01T12:00:00Z",
                "2026-03-01T12:00:00Z",
            ]),
            "target_attendance": [12000.0, 11000.0, 10000.0],
            "capacity": [20000.0, 20000.0, 20000.0],
        })
        state = add_same_season_residual_state(
            rows,
            np.array([10000.0, 10000.0, 10000.0]),
        )
        self.assertEqual(int(state.loc[0, "regime_prior_home_matches"]), 0)
        # m1 completes at 15:00, therefore the 14:00 snapshot cannot use it.
        self.assertEqual(int(state.loc[1, "regime_prior_home_matches"]), 0)
        # The 16:00 snapshot can use m1.
        self.assertEqual(int(state.loc[2, "regime_prior_home_matches"]), 1)
        self.assertAlmostEqual(float(state.loc[2, "regime_mean_residual_fraction"]), 0.10)

    def test_same_match_never_enters_its_own_snapshot(self) -> None:
        rows = pd.DataFrame({
            "match_key": ["m1"],
            "home_club_key": ["club"],
            "as_of_at": pd.to_datetime(["2026-01-09T12:00:00Z"]),
            "kickoff_at": pd.to_datetime(["2026-01-10T12:00:00Z"]),
            "target_attendance": [15000.0],
            "capacity": [20000.0],
        })
        state = add_same_season_residual_state(rows, np.array([10000.0]))
        self.assertEqual(int(state.loc[0, "regime_prior_home_matches"]), 0)

    def test_correction_is_capped_to_five_percent_capacity(self) -> None:
        rows = pd.DataFrame({
            "capacity": [20000.0],
            "regime_prior_home_matches": [10],
            "regime_mean_residual_fraction": [0.25],
            "regime_ewma_residual_fraction": [0.25],
            "regime_mean_demand_ratio": [0.50],
        })
        variant = RegimeVariant(source="mean_residual_fraction", shrink_k=2)
        adjusted, diagnostics = apply_variant(rows, np.array([10000.0]), variant)
        self.assertAlmostEqual(float(adjusted[0]), 11000.0)
        self.assertAlmostEqual(float(diagnostics["max_abs_correction_seats"]), 1000.0)

    def test_selection_requires_both_development_folds_and_half_percent_mean(self) -> None:
        rows = [
            {
                "candidate_id": "NO_ADJUSTMENT",
                "all_development_folds_improve": False,
                "mean_relative_mae_improvement": 0.0,
                "mean_mae_improvement": 0.0,
                "max_worst_event_degradation": 0.0,
                "mean_p90_ae_delta": 0.0,
                "mean_event_improvement_rate": 0.0,
            },
            {
                "candidate_id": "mixed",
                "all_development_folds_improve": False,
                "mean_relative_mae_improvement": 0.02,
                "mean_mae_improvement": 50.0,
                "max_worst_event_degradation": 100.0,
                "mean_p90_ae_delta": -10.0,
                "mean_event_improvement_rate": 0.6,
            },
            {
                "candidate_id": "tiny",
                "all_development_folds_improve": True,
                "mean_relative_mae_improvement": 0.004,
                "mean_mae_improvement": 10.0,
                "max_worst_event_degradation": 50.0,
                "mean_p90_ae_delta": -5.0,
                "mean_event_improvement_rate": 0.6,
            },
        ]
        selected, detail = select_candidate(rows)
        self.assertEqual(selected, "NO_ADJUSTMENT")
        self.assertEqual(detail["reason"], "NO_REGIME_VARIANT_MEETS_TWO_FOLD_STABILITY_GATE")

    def test_near_best_selection_prefers_lower_tail(self) -> None:
        rows = [
            {
                "candidate_id": "NO_ADJUSTMENT",
                "all_development_folds_improve": False,
                "mean_relative_mae_improvement": 0.0,
                "mean_mae_improvement": 0.0,
                "max_worst_event_degradation": 0.0,
                "mean_p90_ae_delta": 0.0,
                "mean_event_improvement_rate": 0.0,
            },
            {
                "candidate_id": "best",
                "all_development_folds_improve": True,
                "mean_relative_mae_improvement": 0.03,
                "mean_mae_improvement": 100.0,
                "max_worst_event_degradation": 3000.0,
                "mean_p90_ae_delta": -100.0,
                "mean_event_improvement_rate": 0.55,
            },
            {
                "candidate_id": "robust",
                "all_development_folds_improve": True,
                "mean_relative_mae_improvement": 0.028,
                "mean_mae_improvement": 92.0,
                "max_worst_event_degradation": 900.0,
                "mean_p90_ae_delta": -70.0,
                "mean_event_improvement_rate": 0.54,
            },
        ]
        selected, detail = select_candidate(rows)
        self.assertEqual(selected, "robust")
        self.assertEqual(set(detail["near_best_candidate_ids"]), {"best", "robust"})


if __name__ == "__main__":
    unittest.main()
