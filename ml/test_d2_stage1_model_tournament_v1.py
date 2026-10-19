#!/usr/bin/env python3
import unittest

import numpy as np
import pandas as pd

from ml.d2_stage1_model_tournament_v1 import (
    CHRONOS2_MODEL_ID,
    CHRONOS_BOLT_MODEL_ID,
    EXPECTED_FREEZE_ID,
    MAX_LIVE_CORRECTION_OCCUPANCY,
    MIN_TSFM_REAL_CONTEXT_POINTS,
    QUANTILE_LEVELS,
    add_tsfm_features,
    causal_inventory_context,
    choose_research_lead,
    governed_forecast,
    normalize_quantile_output,
)
from ml.run_d2_stage1_model_tournament_v1 import CHRONOS_MODEL_REVISIONS


class FakeChronosListPipeline:
    def predict_quantiles(self, contexts, prediction_length, quantile_levels):
        self.contexts = [np.asarray(c, dtype=float).copy() for c in contexts]
        self.prediction_length = int(prediction_length)
        self.quantile_levels = list(quantile_levels)
        outputs = []
        for context in contexts:
            last = float(np.asarray(context)[-1])
            rows = []
            for step in range(prediction_length):
                center = last - 0.01 * (step + 1)
                rows.append([center - 0.02, center, center + 0.02])
            outputs.append(np.asarray(rows, dtype=float)[None, :, :])
        means = [np.asarray(out)[..., 1] for out in outputs]
        return outputs, means


class D2Stage1TournamentV1Test(unittest.TestCase):
    def test_chronos_models_and_revisions_are_frozen(self) -> None:
        self.assertEqual(CHRONOS2_MODEL_ID, "amazon/chronos-2")
        self.assertEqual(CHRONOS_BOLT_MODEL_ID, "amazon/chronos-bolt-small")
        self.assertEqual(
            CHRONOS_MODEL_REVISIONS[CHRONOS2_MODEL_ID],
            "95a9710e2596287d08352589f42634fa5abdf0a7",
        )
        self.assertEqual(
            CHRONOS_MODEL_REVISIONS[CHRONOS_BOLT_MODEL_ID],
            "0e96a1377adca89eebae3bbde4f859dc3b9f4b46",
        )
        self.assertEqual(QUANTILE_LEVELS, (0.1, 0.5, 0.9))
        self.assertEqual(MIN_TSFM_REAL_CONTEXT_POINTS, 2)

    def test_causal_context_never_uses_future_row(self) -> None:
        rows = pd.DataFrame({
            "as_of_at": pd.to_datetime([
                "2026-10-01T00:00:00Z",
                "2026-10-01T06:00:00Z",
                "2026-10-01T12:00:00Z",
            ], utc=True),
            "hours_to_kickoff": [18.0, 12.0, 6.0],
            "available_share_of_capacity": [0.30, 0.25, 0.01],
        })
        context = causal_inventory_context(rows, pd.Timestamp("2026-10-01T06:00:00Z"))
        self.assertTrue(context["ready"])
        np.testing.assert_allclose(context["context"], np.array([0.30, 0.25], dtype=np.float32))
        # The very distinctive future value must not appear in the context.
        self.assertFalse(np.any(np.isclose(context["context"], 0.01)))

    def test_missing_historical_bucket_is_forward_filled_causally(self) -> None:
        rows = pd.DataFrame({
            "as_of_at": pd.to_datetime([
                "2026-10-01T00:00:00Z",
                "2026-10-01T12:00:00Z",
            ], utc=True),
            "hours_to_kickoff": [24.0, 12.0],
            "available_share_of_capacity": [0.40, 0.20],
        })
        context = causal_inventory_context(rows, pd.Timestamp("2026-10-01T12:00:00Z"))
        self.assertTrue(context["ready"])
        # buckets 4,3,2 -> bucket 3 can only inherit the older bucket-4 value
        np.testing.assert_allclose(
            context["context"],
            np.array([0.40, 0.40, 0.20], dtype=np.float32),
        )

    def test_one_real_context_point_is_not_tsfm_ready(self) -> None:
        rows = pd.DataFrame({
            "as_of_at": pd.to_datetime(["2026-10-01T00:00:00Z"], utc=True),
            "hours_to_kickoff": [18.0],
            "available_share_of_capacity": [0.30],
        })
        context = causal_inventory_context(rows, rows.loc[0, "as_of_at"])
        self.assertFalse(context["ready"])
        self.assertEqual(context["reason"], "INSUFFICIENT_REAL_CONTEXT")

    def test_chronos_features_do_not_depend_on_final_attendance_label(self) -> None:
        base = pd.DataFrame({
            "ticket_event_id": [1, 1, 1],
            "as_of_at": pd.to_datetime([
                "2026-10-01T00:00:00Z",
                "2026-10-01T06:00:00Z",
                "2026-10-01T12:00:00Z",
            ], utc=True),
            "hours_to_kickoff": [18.0, 12.0, 6.0],
            "available_share_of_capacity": [0.30, 0.25, 0.20],
            "actual_attendance": [10000.0, 10000.0, 10000.0],
            "target_live_delta_occupancy": [0.1, 0.1, 0.1],
        })
        changed_labels = base.copy()
        changed_labels["actual_attendance"] = 99999.0
        changed_labels["target_live_delta_occupancy"] = -0.5
        first = add_tsfm_features(base, FakeChronosListPipeline(), "chronos2")
        second = add_tsfm_features(changed_labels, FakeChronosListPipeline(), "chronos2")
        columns = [column for column in first.columns if column.startswith("chronos2_")]
        pd.testing.assert_frame_equal(first[columns], second[columns])

    def test_list_quantile_shape_is_normalized(self) -> None:
        item = np.array([[[0.1, 0.2, 0.3], [0.2, 0.3, 0.4]]], dtype=float)
        normalized = normalize_quantile_output([item], prediction_length=2, batch_size=1)
        self.assertEqual(normalized[0].shape, (2, 3))
        self.assertAlmostEqual(float(normalized[0][-1, 1]), 0.3)

    def test_governed_revision_is_capped_at_ten_percent_capacity(self) -> None:
        frame = pd.DataFrame({
            "stadium_capacity": [20000.0, 20000.0],
            "frozen_v2_p50": [10000.0, 10000.0],
        })
        forecast, delta = governed_forecast(frame, np.array([0.50, -0.50]))
        np.testing.assert_allclose(delta, np.array([0.10, -0.10]))
        np.testing.assert_allclose(forecast, np.array([12000.0, 8000.0]))
        self.assertEqual(MAX_LIVE_CORRECTION_OCCUPANCY, 0.10)

    def test_research_lead_requires_both_window_and_latest_improvement(self) -> None:
        rows = [
            {
                "candidate_id": "frozen-v2-zero-correction",
                "scorecard": {
                    "latest_mae_improvement": 0.0,
                    "window_mae_improvement": 0.0,
                    "latest_row_mae": 100.0,
                    "event_balanced_window_mae": 100.0,
                    "worst_latest_event_degradation": 0.0,
                },
            },
            {
                "candidate_id": "latest-only",
                "scorecard": {
                    "latest_mae_improvement": 10.0,
                    "window_mae_improvement": -5.0,
                    "latest_row_mae": 90.0,
                    "event_balanced_window_mae": 105.0,
                    "worst_latest_event_degradation": 20.0,
                },
            },
            {
                "candidate_id": "both",
                "scorecard": {
                    "latest_mae_improvement": 8.0,
                    "window_mae_improvement": 4.0,
                    "latest_row_mae": 92.0,
                    "event_balanced_window_mae": 96.0,
                    "worst_latest_event_degradation": 10.0,
                },
            },
        ]
        self.assertEqual(choose_research_lead(rows), "both")

    def test_freeze_id_is_explicit(self) -> None:
        self.assertEqual(
            EXPECTED_FREEZE_ID,
            "pre-live-v2-historical-candidate-2026-10-18-v1",
        )


if __name__ == "__main__":
    unittest.main()
