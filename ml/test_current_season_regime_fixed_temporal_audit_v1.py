#!/usr/bin/env python3
import unittest

import numpy as np
import pandas as pd

from ml.current_season_regime_fixed_temporal_audit_v1 import (
    EXPECTED_FIXED_MAE,
    FIXED_VARIANTS,
    MIN_PRIOR_HOME_MATCHES,
    apply_fixed_policy,
    verify_fixed_mae,
)


class CurrentSeasonRegimeFixedTemporalAuditV1Test(unittest.TestCase):
    def test_fixed_contract_is_exact(self) -> None:
        self.assertEqual(MIN_PRIOR_HOME_MATCHES, 3)
        self.assertEqual(FIXED_VARIANTS["T-7"].id, "ewma50-resid-k6-cap05")
        self.assertEqual(FIXED_VARIANTS["T-3"].id, "ewma50-resid-k2-cap05")
        self.assertEqual(FIXED_VARIANTS["T-1"].id, "ewma50-resid-k6-cap05")
        self.assertEqual(set(EXPECTED_FIXED_MAE), {"T-7", "T-3", "T-1"})

    def test_maturity_gate_keeps_first_two_prior_states_at_base(self) -> None:
        rows = pd.DataFrame({
            "capacity": [20000.0, 20000.0, 20000.0],
            "regime_prior_home_matches": [1, 2, 3],
            "regime_mean_residual_fraction": [0.20, 0.20, 0.20],
            "regime_median_residual_fraction": [0.20, 0.20, 0.20],
            "regime_ewma_residual_fraction": [0.20, 0.20, 0.20],
            "regime_last3_mean_residual_fraction": [0.20, 0.20, 0.20],
            "regime_mean_demand_ratio": [0.20, 0.20, 0.20],
        })
        prediction, _ = apply_fixed_policy(
            rows,
            np.array([10000.0, 10000.0, 10000.0]),
            "T-3",
        )
        self.assertAlmostEqual(float(prediction[0]), 10000.0)
        self.assertAlmostEqual(float(prediction[1]), 10000.0)
        self.assertGreater(float(prediction[2]), 10000.0)

    def test_reproduction_assertion_rejects_drift(self) -> None:
        expected = EXPECTED_FIXED_MAE["T-1"]["2025/2026"]
        verify_fixed_mae("T-1", "2025/2026", expected)
        with self.assertRaises(RuntimeError):
            verify_fixed_mae("T-1", "2025/2026", expected + 0.01)


if __name__ == "__main__":
    unittest.main()
