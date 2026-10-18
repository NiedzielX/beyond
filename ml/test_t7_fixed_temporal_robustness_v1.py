#!/usr/bin/env python3
import unittest

import numpy as np

from ml.t7_fixed_temporal_robustness_v1 import (
    BOOTSTRAP_SAMPLES,
    EXPECTED_FIXED_MAE,
    FIXED_CANDIDATE_ID,
    FOLDS,
    LARGE_DEGRADATION_THRESHOLDS,
    paired_bootstrap_improvement,
)


class T7FixedTemporalRobustnessV1Test(unittest.TestCase):
    def test_fixed_contract(self) -> None:
        self.assertEqual(FIXED_CANDIDATE_ID, "hist31-leaf20-l2-1")
        self.assertEqual(len(FOLDS), 4)
        self.assertEqual(BOOTSTRAP_SAMPLES, 10_000)
        self.assertEqual(LARGE_DEGRADATION_THRESHOLDS, (500.0, 1000.0, 2000.0, 3000.0))

    def test_exact_stage3_assertions_exist(self) -> None:
        self.assertEqual(
            set(EXPECTED_FIXED_MAE),
            {"2023/2024", "2024/2025", "2025/2026"},
        )
        self.assertAlmostEqual(EXPECTED_FIXED_MAE["2023/2024"], 2317.3395349341495)

    def test_bootstrap_is_deterministic(self) -> None:
        incumbent = np.array([10.0, 20.0, 30.0, 40.0])
        candidate = np.array([8.0, 19.0, 29.0, 35.0])
        a = paired_bootstrap_improvement(incumbent, candidate, seed=42, samples=500)
        b = paired_bootstrap_improvement(incumbent, candidate, seed=42, samples=500)
        self.assertEqual(a, b)
        self.assertGreater(float(a["probability_improvement_gt_0"]), 0.9)

    def test_bootstrap_detects_worse_candidate(self) -> None:
        incumbent = np.array([10.0, 20.0, 30.0, 40.0])
        candidate = np.array([15.0, 25.0, 35.0, 45.0])
        result = paired_bootstrap_improvement(incumbent, candidate, seed=7, samples=500)
        self.assertLess(float(result["observed_mean_improvement"]), 0.0)
        self.assertEqual(float(result["probability_improvement_gt_0"]), 0.0)


if __name__ == "__main__":
    unittest.main()
