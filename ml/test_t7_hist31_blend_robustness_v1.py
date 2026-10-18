#!/usr/bin/env python3
import unittest

import numpy as np
import pandas as pd

from ml.t7_hist31_blend_robustness_v1 import (
    ALPHAS,
    STAGE1_FULL_HIST31_WORST_DEGRADATION,
    blend_predictions,
    robustness_scorecard,
)


class T7Hist31BlendRobustnessV1Test(unittest.TestCase):
    def test_alpha_contract_is_fixed_and_ordered(self) -> None:
        self.assertEqual(ALPHAS, (0.0, 0.25, 0.50, 0.75, 1.0))
        self.assertEqual(sorted(ALPHAS), list(ALPHAS))

    def test_blend_endpoints_and_midpoint(self) -> None:
        incumbent = np.array([100.0, 200.0])
        hist31 = np.array([140.0, 160.0])
        np.testing.assert_allclose(blend_predictions(incumbent, hist31, 0.0), incumbent)
        np.testing.assert_allclose(blend_predictions(incumbent, hist31, 1.0), hist31)
        np.testing.assert_allclose(
            blend_predictions(incumbent, hist31, 0.5),
            np.array([120.0, 180.0]),
        )

    def test_invalid_alpha_fails(self) -> None:
        with self.assertRaises(ValueError):
            blend_predictions(np.array([1.0]), np.array([2.0]), -0.1)
        with self.assertRaises(ValueError):
            blend_predictions(np.array([1.0]), np.array([2.0]), 1.1)

    def test_shape_mismatch_fails(self) -> None:
        with self.assertRaises(ValueError):
            blend_predictions(np.array([1.0, 2.0]), np.array([1.0]), 0.5)

    def test_robustness_scorecard_keeps_event_and_revision_details(self) -> None:
        rows = pd.DataFrame({
            "match_key": ["m1", "m2", "m3"],
            "home_club_key": ["a", "a", "b"],
            "away_club_key": ["x", "y", "z"],
            "target_attendance": [100.0, 200.0, 300.0],
            "capacity": [1000.0, 1000.0, 1000.0],
        })
        incumbent = np.array([90.0, 220.0, 330.0])
        hist31 = np.array([130.0, 180.0, 260.0])
        candidate = blend_predictions(incumbent, hist31, 0.5)
        score = robustness_scorecard(rows, candidate, incumbent, hist31)
        self.assertIn("worst_event", score)
        self.assertIn("mean_abs_revision_vs_incumbent", score)
        self.assertIn("worst_event_degradation_share_of_capacity", score)
        self.assertIn("hist31_full", score)

    def test_stage1_tail_reference_is_frozen(self) -> None:
        self.assertAlmostEqual(
            STAGE1_FULL_HIST31_WORST_DEGRADATION["2024/2025"],
            3685.7443205687923,
        )
        self.assertAlmostEqual(
            STAGE1_FULL_HIST31_WORST_DEGRADATION["2025/2026"],
            4233.1079323212325,
        )


if __name__ == "__main__":
    unittest.main()
