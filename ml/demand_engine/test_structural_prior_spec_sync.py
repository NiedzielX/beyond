import unittest

from ml.demand_engine.structural_prior import CURRENT_STRUCTURAL_PRIOR_SPECS
from ml.demand_engine.structural_prior_runtime import CURRENT_EARLY_RUNTIME_SPECS


class StructuralPriorSpecSyncTest(unittest.TestCase):
    def test_early_runtime_specs_match_adapter_contract(self) -> None:
        for horizon in ("T-30", "T-14"):
            runtime = CURRENT_EARLY_RUNTIME_SPECS[horizon]
            adapter = CURRENT_STRUCTURAL_PRIOR_SPECS[horizon]
            self.assertEqual(adapter.model_spec_id, runtime.model_spec_id)
            self.assertEqual(adapter.feature_contract, runtime.feature_contract)
            self.assertEqual(adapter.target_days_before, int(horizon.split("-")[1]))

    def test_early_runtime_model_families_match_adapter(self) -> None:
        self.assertEqual(
            CURRENT_STRUCTURAL_PRIOR_SPECS["T-30"].model_family,
            "ExtraTreesRegressor",
        )
        self.assertEqual(
            CURRENT_STRUCTURAL_PRIOR_SPECS["T-14"].model_family,
            "HistGradientBoostingRegressor",
        )


if __name__ == "__main__":
    unittest.main()
