#!/usr/bin/env python3
import unittest

import numpy as np

from ml.pre_live_t7_robustness_stage2_v1 import (
    ALPHAS,
    CAP_FRACTIONS,
    ROBUST_GAIN_RETENTION,
    RobustCandidate,
    apply_robust_policy,
    robust_candidates,
    select_robust_candidate,
)


class T7RobustnessStage2V1Test(unittest.TestCase):
    def test_candidate_contract_is_fixed(self) -> None:
        candidates = robust_candidates()
        self.assertEqual(ALPHAS, (0.25, 0.50, 0.75, 1.00))
        self.assertEqual(CAP_FRACTIONS, (0.05, 0.10, None))
        self.assertEqual(ROBUST_GAIN_RETENTION, 0.80)
        self.assertEqual(len(candidates), 13)
        self.assertEqual(candidates[0].id, "incumbent")
        self.assertEqual(len({candidate.id for candidate in candidates}), len(candidates))

    def test_trust_region_caps_shift_by_capacity(self) -> None:
        incumbent = np.array([100.0, 200.0])
        hist31 = np.array([180.0, 80.0])
        capacity = np.array([1000.0, 1000.0])
        candidate = RobustCandidate("x", alpha=1.0, cap_fraction=0.05)
        prediction = apply_robust_policy(incumbent, hist31, capacity, candidate)
        np.testing.assert_allclose(prediction, np.array([150.0, 150.0]))

    def test_alpha_blend_without_cap(self) -> None:
        incumbent = np.array([100.0])
        hist31 = np.array([300.0])
        capacity = np.array([1000.0])
        candidate = RobustCandidate("x", alpha=0.25, cap_fraction=None)
        prediction = apply_robust_policy(incumbent, hist31, capacity, candidate)
        np.testing.assert_allclose(prediction, np.array([150.0]))

    def test_selection_preserves_gain_then_minimizes_tail(self) -> None:
        rows = [
            {
                "candidate": {"id": "incumbent", "alpha": 0.0, "cap_fraction": None},
                "all_folds_improve": False,
                "mean_mae_improvement": 0.0,
                "max_worst_event_degradation": 0.0,
                "mean_p90_delta": 0.0,
            },
            {
                "candidate": {"id": "best-mae", "alpha": 1.0, "cap_fraction": None},
                "all_folds_improve": True,
                "mean_mae_improvement": 100.0,
                "max_worst_event_degradation": 4000.0,
                "mean_p90_delta": -100.0,
            },
            {
                "candidate": {"id": "robust", "alpha": 0.75, "cap_fraction": 0.05},
                "all_folds_improve": True,
                "mean_mae_improvement": 85.0,
                "max_worst_event_degradation": 1200.0,
                "mean_p90_delta": -80.0,
            },
            {
                "candidate": {"id": "too-little-gain", "alpha": 0.25, "cap_fraction": 0.05},
                "all_folds_improve": True,
                "mean_mae_improvement": 70.0,
                "max_worst_event_degradation": 200.0,
                "mean_p90_delta": -50.0,
            },
        ]
        selected, detail = select_robust_candidate(rows)
        self.assertEqual(selected, "robust")
        self.assertAlmostEqual(detail["required_retained_improvement"], 80.0)
        self.assertEqual(set(detail["eligible_candidate_ids"]), {"best-mae", "robust"})

    def test_selection_falls_back_to_incumbent_when_folds_disagree(self) -> None:
        rows = [
            {
                "candidate": {"id": "incumbent", "alpha": 0.0, "cap_fraction": None},
                "all_folds_improve": False,
                "mean_mae_improvement": 0.0,
                "max_worst_event_degradation": 0.0,
                "mean_p90_delta": 0.0,
            },
            {
                "candidate": {"id": "mixed", "alpha": 0.75, "cap_fraction": None},
                "all_folds_improve": False,
                "mean_mae_improvement": 50.0,
                "max_worst_event_degradation": 1000.0,
                "mean_p90_delta": -50.0,
            },
        ]
        selected, detail = select_robust_candidate(rows)
        self.assertEqual(selected, "incumbent")
        self.assertEqual(detail["reason"], "NO_NON_INCUMBENT_IMPROVES_ALL_DEVELOPMENT_FOLDS")


if __name__ == "__main__":
    unittest.main()
