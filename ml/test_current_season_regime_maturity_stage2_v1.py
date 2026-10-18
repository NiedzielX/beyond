#!/usr/bin/env python3
import unittest

import numpy as np
import pandas as pd

from ml.current_season_regime_maturity_stage2_v1 import (
    ACTIVATION_MIN_PRIOR_HOME_MATCHES,
    RegimeVariant,
    apply_activation_threshold,
    select_activation,
)


class RegimeMaturityStage2V1Test(unittest.TestCase):
    def test_activation_grid_is_fixed(self) -> None:
        self.assertEqual(ACTIVATION_MIN_PRIOR_HOME_MATCHES, (1, 2, 3))

    def test_activation_gate_keeps_immature_rows_at_base(self) -> None:
        rows = pd.DataFrame({
            "capacity": [20000.0, 20000.0, 20000.0],
            "regime_prior_home_matches": [1, 2, 3],
            "regime_mean_residual_fraction": [0.20, 0.20, 0.20],
            "regime_ewma_residual_fraction": [0.20, 0.20, 0.20],
            "regime_mean_demand_ratio": [0.20, 0.20, 0.20],
        })
        variant = RegimeVariant(source="ewma_residual_fraction", shrink_k=2)
        prediction, _ = apply_activation_threshold(
            rows,
            np.array([10000.0, 10000.0, 10000.0]),
            variant,
            min_prior_home_matches=3,
        )
        self.assertAlmostEqual(float(prediction[0]), 10000.0)
        self.assertAlmostEqual(float(prediction[1]), 10000.0)
        self.assertGreater(float(prediction[2]), 10000.0)

    def test_selection_falls_back_when_folds_disagree(self) -> None:
        rows = [
            {"candidate_id":"NO_ADJUSTMENT","all_development_folds_improve":False,"mean_relative_mae_improvement":0.0,"mean_mae_improvement":0.0,"max_worst_event_degradation":0.0,"mean_p90_ae_delta":0.0,"min_prior_home_matches":None},
            {"candidate_id":"x-min3","all_development_folds_improve":False,"mean_relative_mae_improvement":0.03,"mean_mae_improvement":80.0,"max_worst_event_degradation":500.0,"mean_p90_ae_delta":-50.0,"min_prior_home_matches":3},
        ]
        selected, detail = select_activation(rows)
        self.assertEqual(selected, "NO_ADJUSTMENT")
        self.assertEqual(detail["reason"], "NO_ACTIVATION_THRESHOLD_MEETS_TWO_FOLD_GATE")

    def test_near_best_selection_prefers_lower_tail(self) -> None:
        rows = [
            {"candidate_id":"NO_ADJUSTMENT","all_development_folds_improve":False,"mean_relative_mae_improvement":0.0,"mean_mae_improvement":0.0,"max_worst_event_degradation":0.0,"mean_p90_ae_delta":0.0,"min_prior_home_matches":None},
            {"candidate_id":"x-min2","all_development_folds_improve":True,"mean_relative_mae_improvement":0.04,"mean_mae_improvement":100.0,"max_worst_event_degradation":3000.0,"mean_p90_ae_delta":-100.0,"min_prior_home_matches":2},
            {"candidate_id":"x-min3","all_development_folds_improve":True,"mean_relative_mae_improvement":0.038,"mean_mae_improvement":96.0,"max_worst_event_degradation":1000.0,"mean_p90_ae_delta":-80.0,"min_prior_home_matches":3},
        ]
        selected, _ = select_activation(rows)
        self.assertEqual(selected, "x-min3")


if __name__ == "__main__":
    unittest.main()
