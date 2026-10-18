#!/usr/bin/env python3
import unittest

import numpy as np

from ml.current_season_regime_maturity_v1 import (
    BOOTSTRAP_SAMPLES,
    BUCKETS,
    EXPECTED_VARIANT_IDS,
    FIXED_VARIANTS,
    LARGE_DEGRADATION_THRESHOLDS,
    bucket_label,
    paired_bootstrap_improvement,
)


class CurrentSeasonRegimeMaturityV1Test(unittest.TestCase):
    def test_fixed_winner_contract(self) -> None:
        self.assertEqual(set(FIXED_VARIANTS), {"T-7", "T-3", "T-1"})
        for horizon, variant in FIXED_VARIANTS.items():
            self.assertEqual(variant.id, EXPECTED_VARIANT_IDS[horizon])
        self.assertEqual(EXPECTED_VARIANT_IDS["T-7"], "ewma50-resid-k6-cap05")
        self.assertEqual(EXPECTED_VARIANT_IDS["T-3"], "ewma50-resid-k2-cap05")
        self.assertEqual(EXPECTED_VARIANT_IDS["T-1"], "ewma50-resid-k6-cap05")

    def test_maturity_bucket_contract(self) -> None:
        self.assertEqual(BUCKETS, ("0", "1", "2", "3+"))
        self.assertEqual(bucket_label(0), "0")
        self.assertEqual(bucket_label(1), "1")
        self.assertEqual(bucket_label(2), "2")
        self.assertEqual(bucket_label(3), "3+")
        self.assertEqual(bucket_label(20), "3+")

    def test_tail_and_bootstrap_contract(self) -> None:
        self.assertEqual(BOOTSTRAP_SAMPLES, 10_000)
        self.assertEqual(LARGE_DEGRADATION_THRESHOLDS, (500.0, 1000.0, 2000.0, 3000.0))

    def test_bootstrap_is_deterministic(self) -> None:
        incumbent = np.array([100.0, 200.0, 300.0, 400.0])
        candidate = np.array([90.0, 190.0, 280.0, 390.0])
        a = paired_bootstrap_improvement(incumbent, candidate, seed=42, samples=500)
        b = paired_bootstrap_improvement(incumbent, candidate, seed=42, samples=500)
        self.assertEqual(a, b)
        self.assertGreater(float(a["observed_mean_improvement"]), 0.0)

    def test_bootstrap_detects_harm(self) -> None:
        incumbent = np.array([10.0, 20.0, 30.0, 40.0])
        candidate = np.array([20.0, 30.0, 40.0, 50.0])
        result = paired_bootstrap_improvement(incumbent, candidate, seed=7, samples=500)
        self.assertLess(float(result["observed_mean_improvement"]), 0.0)
        self.assertEqual(float(result["probability_improvement_gt_0"]), 0.0)


if __name__ == "__main__":
    unittest.main()
