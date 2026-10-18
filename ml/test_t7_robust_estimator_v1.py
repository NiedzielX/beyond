#!/usr/bin/env python3
import unittest

from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor

from ml.t7_robust_estimator_v1 import CANDIDATES, estimator_for


class T7RobustEstimatorV1Test(unittest.TestCase):
    def test_candidate_ids_are_unique(self) -> None:
        ids = [candidate.id for candidate in CANDIDATES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_exact_stage1_hist31_is_first_candidate(self) -> None:
        candidate = CANDIDATES[0]
        self.assertEqual(candidate.id, "hist31-leaf10-l2-1")
        self.assertEqual(candidate.family, "hist")
        self.assertEqual(candidate.learning_rate, 0.04)
        self.assertEqual(candidate.max_iter_or_estimators, 300)
        self.assertEqual(candidate.max_leaf_nodes, 31)
        self.assertEqual(candidate.min_samples_leaf, 10)
        self.assertEqual(candidate.l2_regularization, 1.0)

    def test_regularized_hist_candidates_are_materially_distinct(self) -> None:
        signatures = {
            (
                c.family,
                c.learning_rate,
                c.max_iter_or_estimators,
                c.max_leaf_nodes,
                c.min_samples_leaf,
                c.l2_regularization,
                c.max_depth,
            )
            for c in CANDIDATES
        }
        self.assertEqual(len(signatures), len(CANDIDATES))

    def test_hist_estimator_contract(self) -> None:
        estimator = estimator_for(CANDIDATES[0])
        self.assertIsInstance(estimator, HistGradientBoostingRegressor)
        self.assertEqual(estimator.loss, "absolute_error")
        self.assertEqual(estimator.max_leaf_nodes, 31)
        self.assertEqual(estimator.min_samples_leaf, 10)
        self.assertEqual(estimator.l2_regularization, 1.0)

    def test_absolute_gbr_contract(self) -> None:
        candidate = next(c for c in CANDIDATES if c.id == "gbr-absolute-depth2-leaf8")
        estimator = estimator_for(candidate)
        self.assertIsInstance(estimator, GradientBoostingRegressor)
        self.assertEqual(estimator.loss, "absolute_error")
        self.assertEqual(estimator.max_depth, 2)
        self.assertEqual(estimator.min_samples_leaf, 8)

    def test_grid_contains_stronger_regularization_dimensions(self) -> None:
        self.assertTrue(any(c.max_leaf_nodes == 15 for c in CANDIDATES if c.family == "hist"))
        self.assertTrue(any(c.min_samples_leaf >= 20 for c in CANDIDATES if c.family == "hist"))
        self.assertTrue(any(c.l2_regularization >= 5.0 for c in CANDIDATES if c.family == "hist"))


if __name__ == "__main__":
    unittest.main()
