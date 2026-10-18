#!/usr/bin/env python3
import unittest

from ml.pre_live_baseline_optimization_v1 import Candidate
from ml.pre_live_unresolved_multifold_v1 import (
    EXPECTED_STAGE1_DEV_2023_MAE,
    HORIZONS,
    MIN_IDENTIFIABLE_DEVELOPMENT_FOLDS,
    candidate_development_summary,
    is_identifiable,
    select_candidate,
)


class PreLiveUnresolvedMultifoldV1Test(unittest.TestCase):
    def test_scope_excludes_frozen_t7(self) -> None:
        self.assertEqual(HORIZONS, ("T-30", "T-14", "T-3", "T-1"))
        self.assertNotIn("T-7", HORIZONS)
        self.assertEqual(MIN_IDENTIFIABLE_DEVELOPMENT_FOLDS, 2)

    def test_exact_stage1_2023_incumbent_assertions(self) -> None:
        self.assertAlmostEqual(EXPECTED_STAGE1_DEV_2023_MAE["T-30"], 2559.7406941266854)
        self.assertAlmostEqual(EXPECTED_STAGE1_DEV_2023_MAE["T-14"], 2339.9504993283904)
        self.assertAlmostEqual(EXPECTED_STAGE1_DEV_2023_MAE["T-3"], 2311.6246893162593)
        self.assertAlmostEqual(EXPECTED_STAGE1_DEV_2023_MAE["T-1"], 2347.9931110468183)

    def test_recency_is_not_identifiable_with_one_training_season(self) -> None:
        candidate = Candidate(
            id="recency-linear_075",
            family="recency",
            recency_policy="linear_075",
        )
        identifiable, reason = is_identifiable(candidate, ["2021/2022"])
        self.assertFalse(identifiable)
        self.assertEqual(reason, "RECENCY_NOT_IDENTIFIABLE_WITH_ONE_TRAINING_SEASON")
        identifiable2, _ = is_identifiable(candidate, ["2021/2022", "2022/2023"])
        self.assertTrue(identifiable2)

    def test_selection_requires_both_development_folds(self) -> None:
        incumbent = {
            "candidate": {"id": "incumbent"},
            "declared_order": 0,
            "eligibility": "INCUMBENT_FALLBACK",
            "mean_mae_improvement_identifiable_folds": 0.0,
            "max_worst_event_degradation_identifiable_folds": 0.0,
        }
        mixed = {
            "candidate": {"id": "mixed"},
            "declared_order": 1,
            "eligibility": "FAILS_ALL_FOLDS_MAE_IMPROVEMENT_REQUIREMENT",
            "mean_mae_improvement_identifiable_folds": 100.0,
            "max_worst_event_degradation_identifiable_folds": 100.0,
        }
        selected, detail = select_candidate([incumbent, mixed])
        self.assertEqual(selected, "incumbent")
        self.assertEqual(
            detail["reason"],
            "NO_NON_INCUMBENT_IMPROVES_ALL_IDENTIFIABLE_DEVELOPMENT_FOLDS",
        )

    def test_selection_is_mae_first_then_tail(self) -> None:
        rows = [
            {
                "candidate": {"id": "incumbent"},
                "declared_order": 0,
                "eligibility": "INCUMBENT_FALLBACK",
                "mean_mae_improvement_identifiable_folds": 0.0,
                "max_worst_event_degradation_identifiable_folds": 0.0,
            },
            {
                "candidate": {"id": "a"},
                "declared_order": 1,
                "eligibility": "ELIGIBLE",
                "mean_mae_improvement_identifiable_folds": 80.0,
                "max_worst_event_degradation_identifiable_folds": 100.0,
            },
            {
                "candidate": {"id": "b"},
                "declared_order": 2,
                "eligibility": "ELIGIBLE",
                "mean_mae_improvement_identifiable_folds": 90.0,
                "max_worst_event_degradation_identifiable_folds": 1000.0,
            },
        ]
        selected, _ = select_candidate(rows)
        self.assertEqual(selected, "b")


if __name__ == "__main__":
    unittest.main()
