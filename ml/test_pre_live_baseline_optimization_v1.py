#!/usr/bin/env python3
import unittest

import numpy as np
import pandas as pd

from ml.pre_live_baseline_optimization_v1 import (
    FEATURE_GROUPS,
    comparison_scorecard,
    metrics,
    season_weight_map,
)


class PreLiveBaselineOptimizationV1Test(unittest.TestCase):
    def test_feature_groups_are_unique_and_complete_for_declared_contract(self) -> None:
        flattened = [column for columns in FEATURE_GROUPS.values() for column in columns]
        self.assertEqual(len(flattened), 80)
        self.assertEqual(len(flattened), len(set(flattened)))

    def test_recency_weights_are_explicit_and_latest_is_one(self) -> None:
        seasons = ["s1", "s2", "s3", "s4"]
        self.assertEqual(season_weight_map(seasons, "uniform"), {
            "s1": 1.0, "s2": 1.0, "s3": 1.0, "s4": 1.0,
        })
        linear = season_weight_map(seasons, "linear_075")
        self.assertAlmostEqual(linear["s1"], 0.75)
        self.assertAlmostEqual(linear["s4"], 1.0)
        exp = season_weight_map(seasons, "exp_050")
        self.assertEqual(exp, {"s1": 0.125, "s2": 0.25, "s3": 0.5, "s4": 1.0})

    def test_metrics_and_comparison_direction(self) -> None:
        actual = np.array([100.0, 200.0, 300.0])
        incumbent = np.array([90.0, 220.0, 330.0])
        candidate = np.array([95.0, 205.0, 295.0])
        m = metrics(actual, candidate)
        self.assertAlmostEqual(float(m["mae"]), 5.0)

        rows = pd.DataFrame({
            "target_attendance": actual,
            "home_club_key": ["club", "club", "club"],
        })
        score = comparison_scorecard(rows, candidate, incumbent)
        self.assertGreater(float(score["mae_improvement"]), 0.0)
        self.assertEqual(float(score["event_improvement_rate"]), 1.0)

    def test_unknown_recency_policy_fails(self) -> None:
        with self.assertRaises(KeyError):
            season_weight_map(["s1", "s2"], "unknown")


if __name__ == "__main__":
    unittest.main()
