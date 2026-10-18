#!/usr/bin/env python3
import unittest

from ml.unresolved_horizon_multifold_tournament_v1 import (
    MIN_MEAN_RELATIVE_MAE_IMPROVEMENT,
    NEAR_BEST_GAIN_RETENTION,
    TRANSFER_CANDIDATE_ID,
    select_candidate,
)


class UnresolvedHorizonMultifoldTournamentV1Test(unittest.TestCase):
    def test_selection_thresholds_are_frozen(self) -> None:
        self.assertEqual(MIN_MEAN_RELATIVE_MAE_IMPROVEMENT, 0.01)
        self.assertEqual(NEAR_BEST_GAIN_RETENTION, 0.95)
        self.assertEqual(TRANSFER_CANDIDATE_ID, "model-hist-absolute-leaf20")

    def test_no_stable_candidate_falls_back_to_incumbent(self) -> None:
        rows = [
            {
                "candidate_id": "incumbent",
                "all_folds_improve_mae": False,
                "mean_relative_mae_improvement": 0.0,
                "mean_mae_improvement": 0.0,
                "max_worst_event_degradation": 0.0,
                "mean_p90_ae_delta": 0.0,
                "mean_bias_abs_delta": 0.0,
            },
            {
                "candidate_id": "mixed",
                "all_folds_improve_mae": False,
                "mean_relative_mae_improvement": 0.03,
                "mean_mae_improvement": 70.0,
                "max_worst_event_degradation": 500.0,
                "mean_p90_ae_delta": -50.0,
                "mean_bias_abs_delta": -20.0,
            },
        ]
        selected, detail = select_candidate(rows)
        self.assertEqual(selected, "incumbent")
        self.assertEqual(detail["reason"], "NO_CANDIDATE_MEETS_MULTIFOLD_STABILITY_GATE")

    def test_sub_one_percent_candidate_does_not_advance(self) -> None:
        rows = [
            {
                "candidate_id": "incumbent",
                "all_folds_improve_mae": False,
                "mean_relative_mae_improvement": 0.0,
                "mean_mae_improvement": 0.0,
                "max_worst_event_degradation": 0.0,
                "mean_p90_ae_delta": 0.0,
                "mean_bias_abs_delta": 0.0,
            },
            {
                "candidate_id": "tiny",
                "all_folds_improve_mae": True,
                "mean_relative_mae_improvement": 0.0099,
                "mean_mae_improvement": 20.0,
                "max_worst_event_degradation": 200.0,
                "mean_p90_ae_delta": -10.0,
                "mean_bias_abs_delta": -5.0,
            },
        ]
        selected, _ = select_candidate(rows)
        self.assertEqual(selected, "incumbent")

    def test_near_best_pool_uses_tail_as_tiebreak(self) -> None:
        rows = [
            {
                "candidate_id": "incumbent",
                "all_folds_improve_mae": False,
                "mean_relative_mae_improvement": 0.0,
                "mean_mae_improvement": 0.0,
                "max_worst_event_degradation": 0.0,
                "mean_p90_ae_delta": 0.0,
                "mean_bias_abs_delta": 0.0,
            },
            {
                "candidate_id": "best-gain-bad-tail",
                "all_folds_improve_mae": True,
                "mean_relative_mae_improvement": 0.04,
                "mean_mae_improvement": 100.0,
                "max_worst_event_degradation": 4000.0,
                "mean_p90_ae_delta": -100.0,
                "mean_bias_abs_delta": -50.0,
            },
            {
                "candidate_id": "near-best-robust",
                "all_folds_improve_mae": True,
                "mean_relative_mae_improvement": 0.038,
                "mean_mae_improvement": 96.0,
                "max_worst_event_degradation": 1200.0,
                "mean_p90_ae_delta": -80.0,
                "mean_bias_abs_delta": -40.0,
            },
            {
                "candidate_id": "below-95pct",
                "all_folds_improve_mae": True,
                "mean_relative_mae_improvement": 0.03,
                "mean_mae_improvement": 94.0,
                "max_worst_event_degradation": 100.0,
                "mean_p90_ae_delta": -70.0,
                "mean_bias_abs_delta": -30.0,
            },
        ]
        selected, detail = select_candidate(rows)
        self.assertEqual(selected, "near-best-robust")
        self.assertEqual(
            set(detail["near_best_candidate_ids"]),
            {"best-gain-bad-tail", "near-best-robust"},
        )


if __name__ == "__main__":
    unittest.main()
