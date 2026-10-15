import unittest

import pandas as pd

from ml.demand_engine.structural_prior_runtime import (
    CURRENT_EARLY_RUNTIME_SPECS,
    IMPORTANCE,
    feature_columns,
)


class StructuralPriorRuntimeContractTest(unittest.TestCase):
    def test_current_early_specs_are_explicit_and_horizon_specific(self) -> None:
        t30 = CURRENT_EARLY_RUNTIME_SPECS["T-30"]
        t14 = CURRENT_EARLY_RUNTIME_SPECS["T-14"]
        self.assertEqual(t30.model_spec_id, "structural-prior-runtime-v1-t30-extra-full")
        self.assertEqual(t30.baseline_column, "baseline_season")
        self.assertEqual(t30.feature_mode, "full")
        self.assertEqual(t30.estimator_name, "extra_leaf3")
        self.assertEqual(t14.model_spec_id, "structural-prior-runtime-v1-t14-hist-base")
        self.assertEqual(t14.baseline_column, "baseline_r3")
        self.assertEqual(t14.feature_mode, "base")
        self.assertEqual(t14.estimator_name, "hist15")

    def test_base_feature_contract_excludes_importance_interactions(self) -> None:
        frame = pd.DataFrame({
            "home_club_key": ["a"],
            "away_club_key": ["b"],
            "capacity": [10000.0],
            "baseline_r3": [5000.0],
            "combined_ppg": [3.0],
            "top4_any": [1],
            "target_attendance": [6000.0],
            "training_eligible": [True],
        })
        base = feature_columns(frame, "base")
        full = feature_columns(frame, "full")
        self.assertIn("capacity", base)
        self.assertNotIn("combined_ppg", base)
        self.assertNotIn("top4_any", base)
        self.assertIn("combined_ppg", full)
        self.assertTrue({"combined_ppg", "top4_any"}.issubset(IMPORTANCE))


if __name__ == "__main__":
    unittest.main()
