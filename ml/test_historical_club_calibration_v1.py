#!/usr/bin/env python3
import unittest

import numpy as np
import pandas as pd

from ml.historical_club_calibration_v1 import (
    CALIBRATION_ID,
    CAP_FRACTION,
    MIN_HISTORY_OBSERVATIONS,
    SHRINKAGE_K,
    T7_CANDIDATE_ID,
    apply_calibration,
    calibration_state,
)


class HistoricalClubCalibrationV1Test(unittest.TestCase):
    def test_fixed_contract(self) -> None:
        self.assertEqual(CALIBRATION_ID, "club-median-residual-ratio-k10-cap05-min5")
        self.assertEqual(SHRINKAGE_K, 10.0)
        self.assertEqual(CAP_FRACTION, 0.05)
        self.assertEqual(MIN_HISTORY_OBSERVATIONS, 5)
        self.assertEqual(T7_CANDIDATE_ID, "hist31-leaf20-l2-1")

    def test_state_uses_median_shrinkage_and_cap(self) -> None:
        history = pd.DataFrame({
            "home_club_key": ["club"] * 10,
            "base_residual_ratio": [0.20] * 10,
        })
        state = calibration_state(history)["club"]
        self.assertEqual(state["n"], 10)
        self.assertAlmostEqual(state["median_residual_ratio"], 0.20)
        self.assertAlmostEqual(state["shrinkage"], 0.5)
        self.assertAlmostEqual(state["shrunk_residual_ratio"], 0.10)
        self.assertAlmostEqual(state["bounded_correction_ratio"], 0.05)
        self.assertTrue(state["active"])

    def test_low_sample_state_is_inactive(self) -> None:
        history = pd.DataFrame({
            "home_club_key": ["club"] * 4,
            "base_residual_ratio": [0.04, 0.03, 0.05, 0.04],
        })
        state = calibration_state(history)["club"]
        self.assertFalse(state["active"])

    def test_apply_calibration_uses_zero_for_unknown_or_inactive_club(self) -> None:
        rows = pd.DataFrame({
            "home_club_key": ["known", "unknown"],
            "capacity": [10000.0, 20000.0],
            "base_prediction": [5000.0, 10000.0],
            "match_key": ["a", "b"],
        })
        state = {
            "known": {
                "n": 10,
                "median_residual_ratio": 0.04,
                "shrinkage": 0.5,
                "shrunk_residual_ratio": 0.02,
                "bounded_correction_ratio": 0.02,
                "active": True,
            }
        }
        prediction, detail = apply_calibration(rows, state)
        np.testing.assert_allclose(prediction, np.array([5200.0, 10000.0]))
        self.assertEqual(detail["active"].tolist(), [True, False])


if __name__ == "__main__":
    unittest.main()
