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
        self.assertEqual(len(VARIANTS), 15)
        self.assertEqual(len({variant.id for variant in VARIANTS}), 15)
        self.assertEqual(CORRECTION_CAP_SHARE_OF_CAPACITY, 0.05)
        self.assertEqual(MIN_MEAN_RELATIVE_MAE_IMPROVEMENT, 0.005)
        sources = {variant.source for variant in VARIANTS}
        self.assertEqual(sources, {
            "mean_residual_fraction",
            "median_residual_fraction",
            "ewma50_residual_fraction",
            "last3_mean_residual_fraction",
            "mean_demand_ratio",
        })

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
        self.assertEqual(int(state.loc[1, "regime_prior_home_matches"]), 0)
        self.assertEqual(int(state.loc[2, "regime_prior_home_matches"]), 1)
        self.assertAlmostEqual(float(state.loc[2, "regime_mean_residual_fraction"]), 0.10)

    def test_equal_completion_timestamp_is_still_unavailable(self) -> None:
        rows = pd.DataFrame({
            "match_key": ["source", "equal", "after"],
            "home_club_key": ["club", "club", "club"],
            "as_of_at": pd.to_datetime([
                "2026-01-01T10:00:00Z",
                "2026-01-10T15:00:00Z",
                "2026-01-10T15:00:01Z",
            ]),
            "kickoff_at": pd.to_datetime([
                "2026-01-10T12:00:00Z",
                "2026-02-01T12:00:00Z",
                "2026-03-01T12:00:00Z",
            ]),
            "target_attendance": [12000.0, 11000.0, 10000.0],
            "capacity": [20000.0, 20000.0, 20000.0],
        })
        state = add_same_season_residual_state(rows, np.array([10000.0, 10000.0, 10000.0]))
        self.assertEqual(int(state.loc[1, "regime_prior_home_matches"]), 0)
        self.assertEqual(int(state.loc[2, "regime_prior_home_matches"]), 1)

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

    def test_median_and_last3_state_are_computed_from_completed_history(self) -> None:
        rows = pd.DataFrame({
            "match_key": ["m1", "m2", "m3", "m4", "target"],
            "home_club_key": ["club"] * 5,
            "as_of_at": pd.to_datetime([
                "2026-01-01T00:00:00Z",
                "2026-01-02T00:00:00Z",
                "2026-01-03T00:00:00Z",
                "2026-01-04T00:00:00Z",
                "2026-02-01T00:00:00Z",
            ]),
            "kickoff_at": pd.to_datetime([
                "2026-01-01T01:00:00Z",
                "2026-01-02T01:00:00Z",
                "2026-01-03T01:00:00Z",
                "2026-01-04T01:00:00Z",
                "2026-03-01T01:00:00Z",
            ]),
            "target_attendance": [11000.0, 12000.0, 13000.0, 14000.0, 10000.0],
            "capacity": [20000.0] * 5,
        })
        base = np.array([10000.0] * 5)
        state = add_same_season_residual_state(rows, base)
        self.assertEqual(int(state.loc[4, "regime_prior_home_matches"]), 4)
        values = np.array([0.05, 0.10, 0.15, 0.20])
        self.assertAlmostEqual(float(state.loc[4, "regime_median_residual_fraction"]), float(np.median(values)))
        self.assertAlmostEqual(float(state.loc[4, "regime_last3_mean_residual_fraction"]), float(np.mean(values[-3:])))

    def test_correction_is_capped_to_five_percent_capacity(self) -> None:
        rows = pd.DataFrame({
            "capacity": [20000.0],
            "regime_prior_home_matches": [10],
            "regime_mean_residual_fraction": [0.25],
            "regime_median_residual_fraction": [0.25],
            "regime_ewma_residual_fraction": [0.25],
            "regime_last3_mean_residual_fraction": [0.25],
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
