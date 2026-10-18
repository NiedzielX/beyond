#!/usr/bin/env python3
import unittest

import numpy as np
import pandas as pd

from ml.persistent_club_calibration_v1 import (
    CORRECTION_CAP,
    RESIDUAL_INPUT_CLIP,
    empirical_bayes_state,
)


class PersistentClubCalibrationV1Test(unittest.TestCase):
    def test_contract_caps_are_frozen(self) -> None:
        self.assertEqual(RESIDUAL_INPUT_CLIP, 0.25)
        self.assertEqual(CORRECTION_CAP, 0.05)

    def test_same_season_residual_is_rejected(self) -> None:
        frame = pd.DataFrame({
            "season": ["2022/2023", "2023/2024"],
            "home_club_key": ["club-a", "club-a"],
            "residual_fraction_clipped": [0.03, 0.04],
        })
        with self.assertRaises(RuntimeError):
            empirical_bayes_state(frame, "2023/2024")

    def test_future_residual_is_rejected(self) -> None:
        frame = pd.DataFrame({
            "season": ["2024/2025"],
            "home_club_key": ["club-a"],
            "residual_fraction_clipped": [0.03],
        })
        with self.assertRaises(RuntimeError):
            empirical_bayes_state(frame, "2023/2024")

    def test_correction_is_shrunk_and_safety_capped(self) -> None:
        rows = []
        for value in [0.20, 0.20, 0.20, 0.20, 0.20]:
            rows.append({
                "season": "2022/2023",
                "home_club_key": "club-a",
                "residual_fraction_clipped": value,
            })
        for value in [-0.02, 0.00, 0.01, -0.01, 0.02]:
            rows.append({
                "season": "2022/2023",
                "home_club_key": "club-b",
                "residual_fraction_clipped": value,
            })
        state = empirical_bayes_state(pd.DataFrame(rows), "2023/2024")
        correction = state["correction_fraction_by_club"]["club-a"]
        self.assertLessEqual(abs(correction), CORRECTION_CAP)
        self.assertGreater(correction, 0.0)

    def test_low_between_variance_shrinks_toward_zero(self) -> None:
        rows = []
        for club in ["a", "b", "c"]:
            for value in [-0.01, 0.01, -0.01, 0.01]:
                rows.append({
                    "season": "2022/2023",
                    "home_club_key": club,
                    "residual_fraction_clipped": value,
                })
        state = empirical_bayes_state(pd.DataFrame(rows), "2023/2024")
        for correction in state["correction_fraction_by_club"].values():
            self.assertTrue(np.isclose(correction, 0.0, atol=1e-12))


if __name__ == "__main__":
    unittest.main()
