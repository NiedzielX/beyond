#!/usr/bin/env python3
import unittest

from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from xgboost import XGBRegressor

from ml.t7_external_model_family_v1 import CANDIDATES, estimator_for


class T7ExternalModelFamilyV1Test(unittest.TestCase):
    def test_candidate_ids_are_unique_and_small_predeclared_set(self) -> None:
        ids = [candidate.id for candidate in CANDIDATES]
        self.assertEqual(len(ids), 7)
        self.assertEqual(len(ids), len(set(ids)))

    def test_internal_stage3_benchmark_is_first(self) -> None:
        candidate = CANDIDATES[0]
        self.assertEqual(candidate.id, "hist31-leaf20-l2-1")
        estimator = estimator_for(candidate)
        self.assertIsInstance(estimator, HistGradientBoostingRegressor)
        self.assertEqual(estimator.min_samples_leaf, 20)
        self.assertEqual(estimator.max_leaf_nodes, 31)
        self.assertEqual(estimator.l2_regularization, 1.0)

    def test_two_candidates_per_external_family(self) -> None:
        for family in ("catboost", "lightgbm", "xgboost"):
            self.assertEqual(sum(c.family == family for c in CANDIDATES), 2)

    def test_catboost_contract(self) -> None:
        candidate = next(c for c in CANDIDATES if c.id == "catboost-mae-depth4-l2-5")
        estimator = estimator_for(candidate)
        self.assertIsInstance(estimator, CatBoostRegressor)
        params = estimator.get_params()
        self.assertEqual(params["loss_function"], "MAE")
        self.assertEqual(params["depth"], 4)
        self.assertEqual(params["thread_count"], 1)

    def test_lightgbm_contract(self) -> None:
        candidate = next(c for c in CANDIDATES if c.id == "lightgbm-l1-leaves15-l2-5")
        estimator = estimator_for(candidate)
        self.assertIsInstance(estimator, LGBMRegressor)
        params = estimator.get_params()
        self.assertEqual(params["objective"], "regression_l1")
        self.assertEqual(params["num_leaves"], 15)
        self.assertEqual(params["n_jobs"], 1)

    def test_xgboost_contract(self) -> None:
        candidate = next(c for c in CANDIDATES if c.id == "xgboost-l1-depth2-l2-5")
        estimator = estimator_for(candidate)
        self.assertIsInstance(estimator, XGBRegressor)
        params = estimator.get_params()
        self.assertEqual(params["objective"], "reg:absoluteerror")
        self.assertEqual(params["max_depth"], 2)
        self.assertEqual(params["n_jobs"], 1)


if __name__ == "__main__":
    unittest.main()
