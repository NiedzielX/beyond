#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from ml.d2_event5_holdout_v1 import (
    EXPECTED_C1_PACKAGE,
    EXPECTED_DEVELOPMENT_EVENT_IDS,
    EXPECTED_STAGE2_PACKAGE,
    HOLDOUT_EVENT_ID,
    get_holdout_event,
    verify_c1_comparator,
    verify_stage2_manifest,
)
from ml.d2_stage1_model_tournament_v1 import CandidateSpec, fit_predict_learned, governed_forecast
from ml.d2_stage2_reliability_gating_v1 import add_causal_reliability_state, maturity_reliability


class D2Event5HoldoutV1Test(unittest.TestCase):
    def test_holdout_is_not_in_frozen_development_ids(self) -> None:
        self.assertEqual(HOLDOUT_EVENT_ID, 5)
        self.assertNotIn(HOLDOUT_EVENT_ID, EXPECTED_DEVELOPMENT_EVENT_IDS)

    def test_p2_reliability_contract_is_exact_on_four_observations(self) -> None:
        frame = pd.DataFrame({
            "ticket_event_id": [5, 5, 5, 5],
            "as_of_at": pd.to_datetime([
                "2026-10-17T16:00:00Z",
                "2026-10-17T22:00:00Z",
                "2026-10-18T04:00:00Z",
                "2026-10-18T10:00:00Z",
            ], utc=True),
            "hours_to_kickoff": [23.5, 17.5, 11.5, 5.5],
        })
        state = add_causal_reliability_state(frame)
        weights = maturity_reliability(state)
        np.testing.assert_allclose(weights, np.array([0.25, 0.60, 1.0, 1.0]))

    def test_frozen_ridge_prediction_does_not_depend_on_holdout_labels(self) -> None:
        train = pd.DataFrame({
            "ticket_event_id": [1, 1, 3, 3],
            "frozen_v2_p50": [10000.0, 10000.0, 12000.0, 12000.0],
            "frozen_v2_expected_occupancy": [0.50, 0.50, 0.60, 0.60],
            "stadium_capacity": [20000.0] * 4,
            "hours_to_kickoff": [18.0, 6.0, 18.0, 6.0],
            "available_share_of_capacity": [0.40, 0.30, 0.35, 0.25],
            "target_live_delta_occupancy": [0.05, 0.08, -0.02, 0.01],
        })
        test = pd.DataFrame({
            "ticket_event_id": [5, 5],
            "frozen_v2_p50": [11000.0, 11000.0],
            "frozen_v2_expected_occupancy": [0.55, 0.55],
            "stadium_capacity": [20000.0, 20000.0],
            "hours_to_kickoff": [18.0, 6.0],
            "available_share_of_capacity": [0.28, 0.20],
            "actual_attendance": [15000.0, 15000.0],
            "target_live_delta_occupancy": [0.20, 0.20],
        })
        changed = test.copy()
        changed["actual_attendance"] = [1.0, 99999.0]
        changed["target_live_delta_occupancy"] = [-0.9, 0.9]
        spec = CandidateSpec("ridge-a10", "ridge")
        first = fit_predict_learned(spec, train, test)
        second = fit_predict_learned(spec, train, changed)
        np.testing.assert_allclose(first, second)
        first_forecast, first_delta = governed_forecast(test, first)
        second_forecast, second_delta = governed_forecast(changed, second)
        np.testing.assert_allclose(first_delta, second_delta)
        np.testing.assert_allclose(first_forecast, second_forecast)

    def test_stage2_manifest_must_match_frozen_package_and_holdout_boundary(self) -> None:
        payload = {
            "artifact_version": EXPECTED_STAGE2_PACKAGE,
            "status": "FROZEN_RESEARCH_CANDIDATE",
            "stage1_expert_id": "ridge-a10",
            "stage2_policy_id": "P2-observation-maturity",
            "stage1_expert_retuned": False,
            "development": {
                "event_ids": list(EXPECTED_DEVELOPMENT_EVENT_IDS),
                "row_count": 30,
                "reserved_holdout_event_id": 5,
                "reserved_holdout_used_for_selection": False,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(payload))
            loaded = verify_stage2_manifest(path)
        self.assertEqual(loaded["stage2_policy_id"], "P2-observation-maturity")

    def test_c1_comparator_requires_real_pre_outcome_evidence(self) -> None:
        payload = {
            "ticket_event_id": 5,
            "package_version": EXPECTED_C1_PACKAGE,
            "actual_attendance": 37407,
            "reconstructed_after_outcome": False,
            "governance": {
                "source_predictions_persisted_pre_outcome": True,
                "no_backfill": True,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "c1.json"
            path.write_text(json.dumps(payload))
            loaded = verify_c1_comparator(path)
            self.assertFalse(loaded["reconstructed_after_outcome"])
            payload["reconstructed_after_outcome"] = True
            path.write_text(json.dumps(payload))
            with self.assertRaises(RuntimeError):
                verify_c1_comparator(path)

    def test_holdout_metadata_and_four_rows_are_hard_asserted(self) -> None:
        payload = {
            "events": [{
                "ticket_event_id": 5,
                "kickoff_at": "2026-10-18T15:30:00Z",
                "actual_attendance": 37407,
                "stadium_capacity": 43269,
            }],
            "liveRows": [
                {"ticket_event_id": 5},
                {"ticket_event_id": 5},
                {"ticket_event_id": 5},
                {"ticket_event_id": 5},
            ],
        }
        event = get_holdout_event(payload)
        self.assertEqual(event["ticket_event_id"], 5)


if __name__ == "__main__":
    unittest.main()
