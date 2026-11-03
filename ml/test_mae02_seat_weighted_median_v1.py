import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from ml.demand_engine.structural_prior_runtime import CURRENT_EARLY_RUNTIME_SPECS, FittedStructuralPriorRuntime
from ml.mae02_seat_weighted_median_v1 import capacity_weights, development_gate, fit_weighted_copy, paired_metrics, run


def pairs():
    return pd.DataFrame([
        {"match_key": "A", "horizon": "T-3", "target_attendance": 100, "incumbent": 110, "challenger": 100},
        {"match_key": "A", "horizon": "T-1", "target_attendance": 100, "incumbent": 120, "challenger": 130},
        {"match_key": "B", "horizon": "T-3", "target_attendance": 100, "incumbent": 200, "challenger": 190},
    ])


class WeightedObjectiveTests(unittest.TestCase):
    def test_weights_align_absolute_seat_loss_before_clipping(self):
        capacity = np.array([100., 1000., 200.])
        occupancy_residual_error = np.array([-.5, .1, .25])
        weights = capacity_weights(capacity)
        self.assertAlmostEqual(weights.mean(), 1)
        np.testing.assert_allclose(np.abs(occupancy_residual_error)*weights*capacity.mean(),
                                   np.abs(occupancy_residual_error*capacity))

    def test_invalid_training_weights_rejected(self):
        for values in ([], [0, 10], [-1, 10], [float("nan")], [float("inf")], [[1, 2]]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                capacity_weights(values)

    def test_paired_metrics_balance_events_not_horizon_rows(self):
        result = paired_metrics(pairs())
        self.assertEqual(result["event_count"], 2)
        self.assertEqual(result["incumbent_event_balanced_mae"], 57.5)
        self.assertEqual(result["challenger_event_balanced_mae"], 52.5)
        self.assertEqual(result["delta_mae"], -5)
        self.assertEqual(result["event_improvement_rate"], .5)

    def test_duplicate_pairs_and_invalid_forecasts_rejected(self):
        with self.assertRaises(ValueError):
            paired_metrics(pd.concat([pairs(), pairs().iloc[:1]]))
        for value in (float("nan"), float("inf"), -1):
            bad = pairs().astype({"challenger": float}); bad.loc[0, "challenger"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                paired_metrics(bad)

    def test_same_event_cannot_have_different_outcomes(self):
        bad = pairs(); bad.loc[0, "target_attendance"] = 99
        with self.assertRaisesRegex(ValueError, "Inconsistent"):
            paired_metrics(bad)

    def test_both_horizons_must_improve_mae_without_worse_p90(self):
        supported = {h: {"delta_mae": -1, "delta_p90_event_ae": 0} for h in ("T-3", "T-1")}
        self.assertTrue(development_gate(supported))
        for field, value in (("delta_mae", 0), ("delta_mae", 1), ("delta_p90_event_ae", .1), ("delta_mae", float("nan"))):
            failed = {h: dict(metrics) for h, metrics in supported.items()}
            failed["T-1"][field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(development_gate(failed))
        self.assertFalse(development_gate({"T-3": supported["T-3"]}))

    def make_training_and_incumbent(self):
        frame = pd.DataFrame({"match_key": ["A", "B", "C"], "horizon": ["T-3"]*3,
            "season": ["2022/2023"]*3, "home_club_key": ["home"]*3, "away_club_key": ["away"]*3,
            "target_attendance": [1000., 0., 0.], "capacity": [1000., 100., 100.], "baseline_season": [0.]*3})
        pre = ColumnTransformer([("num", "passthrough", ["capacity"])]).fit(frame)
        estimator = HistGradientBoostingRegressor(loss="absolute_error", max_iter=2, min_samples_leaf=10,
                                                  early_stopping=False, random_state=42)
        with threadpool_limits(limits=1):
            estimator.fit(pre.transform(frame), np.array([1., 0., 0.]))
        runtime = FittedStructuralPriorRuntime(CURRENT_EARLY_RUNTIME_SPECS["T-3"], pre, estimator,
                                               ["capacity"], ("2022/2023",), 3)
        return frame, runtime

    def test_weighted_copy_keeps_incumbent_parameters_and_predictions(self):
        frame, incumbent = self.make_training_and_incumbent()
        with threadpool_limits(limits=1):
            before = incumbent.predict(frame)
            candidate = fit_weighted_copy(incumbent, frame)
            np.testing.assert_array_equal(incumbent.predict(frame), before)
            self.assertFalse(np.array_equal(candidate.predict(frame), before))
        self.assertIsNot(candidate.estimator, incumbent.estimator)
        self.assertEqual(candidate.estimator.get_params(), incumbent.estimator.get_params())
        self.assertEqual(candidate.training_seasons, incumbent.training_seasons)

    def test_test_season_or_duplicate_event_cannot_be_weighted_training(self):
        frame, runtime = self.make_training_and_incumbent()
        for change in ("season", "duplicate"):
            bad = frame.copy()
            if change == "season": bad.loc[0, "season"] = "2024/2025"
            else: bad.loc[0, "match_key"] = "B"
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "same eligible"):
                fit_weighted_copy(runtime, bad)

    def test_failed_development_gate_stops_before_old_holdout_fits(self):
        frame = pairs().assign(season="2023/2024", as_of_at="2023-07-01", kickoff_at="2023-07-04",
                               home_club_key="home", away_club_key="away", capacity=1000)
        summary = {"per_horizon": {h: {"delta_mae": 1, "delta_p90_event_ae": -1} for h in ("T-3", "T-1")}}
        module = "ml.mae02_seat_weighted_median_v1."
        with tempfile.TemporaryDirectory() as directory, \
             patch(module+"verify_sources", return_value={"historical_runtime": {"filename": "history.csv", "sha256": "x"}}), \
             patch(module+"canonical_matches"), patch(module+"build_feature_store"), \
             patch(module+"quality_report", return_value={"status": "PASS"}), \
             patch(module+"evaluate_fold", return_value=(frame, [])) as evaluate, \
             patch(module+"summarize", return_value=summary), patch(module+"sha256", return_value="x"):
            result = run(Path(directory), Path(directory)/"output")
            self.assertEqual(result["status"], "REJECT_FOR_PROSPECTIVE")
            self.assertFalse(result["weighted_holdout_fits_performed"])
            self.assertEqual(result["exposed_holdout_checks"], {})
            evaluate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
