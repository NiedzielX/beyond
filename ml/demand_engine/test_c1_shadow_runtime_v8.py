from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ml.demand_engine.c1_shadow_runtime_v8 import (
    C1ShadowRuntimeV8,
    POLICY_ID,
    apply_v8_policy,
)


class _DummyEstimator:
    def __init__(self, occupancy: float):
        self.occupancy = occupancy

    def predict(self, frame: pd.DataFrame):
        return np.full(len(frame), self.occupancy, dtype=float)


class C1ShadowRuntimeV8Tests(unittest.TestCase):
    def test_single_observation_below_20pp_keeps_prior(self):
        result = apply_v8_policy(
            prior_p50=7000.0,
            stadium_capacity=10000.0,
            live_history_p50=[5900.0],
            elapsed_hours=[0.0],
        )
        self.assertEqual(result["selected_expert"], "PRIOR")
        self.assertEqual(result["reason_code"], "single_obs_insufficient_disagreement")
        self.assertAlmostEqual(result["policy_prediction"], 7000.0)

    def test_single_observation_at_least_20pp_uses_live(self):
        result = apply_v8_policy(
            prior_p50=5500.0,
            stadium_capacity=10000.0,
            live_history_p50=[8350.0],
            elapsed_hours=[0.0],
        )
        self.assertEqual(result["selected_expert"], "LIVE")
        self.assertEqual(result["reason_code"], "single_obs_material_disagreement")
        self.assertAlmostEqual(result["policy_prediction"], 8350.0)

    def test_multi_observation_material_disagreement_positive_slope_uses_live(self):
        result = apply_v8_policy(
            prior_p50=7000.0,
            stadium_capacity=10000.0,
            live_history_p50=[5500.0, 5700.0, 5900.0],
            elapsed_hours=[0.0, 6.0, 12.0],
        )
        self.assertEqual(result["selected_expert"], "LIVE")
        self.assertEqual(result["reason_code"], "material_disagreement_positive_live_slope")
        self.assertGreater(result["live_slope_occupancy_per_hour_to_date"], 0.0)

    def test_multi_observation_material_disagreement_negative_slope_keeps_prior(self):
        result = apply_v8_policy(
            prior_p50=8500.0,
            stadium_capacity=10000.0,
            live_history_p50=[7600.0, 7400.0, 7200.0],
            elapsed_hours=[0.0, 6.0, 12.0],
        )
        self.assertEqual(result["selected_expert"], "PRIOR")
        self.assertEqual(result["reason_code"], "live_slope_not_positive")

    def test_multi_observation_small_disagreement_keeps_prior(self):
        result = apply_v8_policy(
            prior_p50=8000.0,
            stadium_capacity=10000.0,
            live_history_p50=[7600.0, 7700.0, 7800.0],
            elapsed_hours=[0.0, 6.0, 12.0],
        )
        self.assertEqual(result["selected_expert"], "PRIOR")
        self.assertEqual(result["reason_code"], "insufficient_disagreement")

    def test_runtime_predicts_and_clips_attendance(self):
        runtime = C1ShadowRuntimeV8(
            estimator=_DummyEstimator(occupancy=1.2),
            features=("feature_a",),
            package_version="test-package",
            training_event_ids=(1, 2),
            training_rows=2,
        )
        frame = pd.DataFrame({
            "feature_a": [1.0, 2.0],
            "stadium_capacity": [10000.0, 15000.0],
        })
        predicted = runtime.predict_live_p50(frame)
        np.testing.assert_allclose(predicted, [10000.0, 15000.0])
        self.assertEqual(runtime.policy_id, POLICY_ID)

    def test_policy_rejects_misaligned_history(self):
        with self.assertRaises(ValueError):
            apply_v8_policy(
                prior_p50=7000.0,
                stadium_capacity=10000.0,
                live_history_p50=[6000.0, 6100.0],
                elapsed_hours=[0.0],
            )


if __name__ == "__main__":
    unittest.main()
