#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from ml.d2_prospective_score_v1 import (
    EXPECTED_DEVELOPMENT_EVENT_IDS,
    EXPECTED_REGISTRY_VERSION,
    EXPECTED_STAGE2_PACKAGE,
    eligible_events,
    verify_registry,
)
from ml.d2_stage1_model_tournament_v1 import CandidateSpec, fit_predict_learned
from ml.d2_stage2_reliability_gating_v1 import add_causal_reliability_state, maturity_reliability


class D2ProspectiveScoreV1Test(unittest.TestCase):
    def test_registry_keeps_event5_out_of_future_unseen_set(self) -> None:
        payload = {
            "registry_version": EXPECTED_REGISTRY_VERSION,
            "frozen_package_id": EXPECTED_STAGE2_PACKAGE,
            "development_event_ids": list(EXPECTED_DEVELOPMENT_EVENT_IDS),
            "scored_prospective_events": [{"ticket_event_id": 5}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(payload))
            _, scored = verify_registry(path)
        self.assertEqual(scored, {5})

    def test_candidate_discovery_excludes_development_and_registered_events(self) -> None:
        payload = {
            "events": [
                {"ticket_event_id": 1, "actual_attendance": 10000, "kickoff_at": "2026-10-01T10:00:00Z"},
                {"ticket_event_id": 5, "actual_attendance": 11000, "kickoff_at": "2026-10-02T10:00:00Z"},
                {"ticket_event_id": 21, "actual_attendance": 12000, "kickoff_at": "2026-10-03T10:00:00Z"},
                {"ticket_event_id": 22, "actual_attendance": None, "kickoff_at": "2026-10-04T10:00:00Z"},
                {"ticket_event_id": 23, "actual_attendance": 13000, "kickoff_at": "2026-10-05T10:00:00Z"},
            ],
            "liveRows": [
                {"ticket_event_id": 1},
                {"ticket_event_id": 5},
                {"ticket_event_id": 21},
                {"ticket_event_id": 21},
                {"ticket_event_id": 22},
            ],
        }
        candidates = eligible_events(payload, {5})
        self.assertEqual([row["ticket_event_id"] for row in candidates], [21])
        self.assertEqual(candidates[0]["prospective_live_row_count"], 2)

    def test_future_prospective_label_does_not_change_frozen_ridge_inference(self) -> None:
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
            "ticket_event_id": [21, 21],
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
        np.testing.assert_allclose(
            fit_predict_learned(spec, train, test),
            fit_predict_learned(spec, train, changed),
        )

    def test_p2_is_reused_without_refitting(self) -> None:
        frame = pd.DataFrame({
            "ticket_event_id": [21, 21, 21, 21],
            "as_of_at": pd.to_datetime([
                "2026-10-20T00:00:00Z",
                "2026-10-20T06:00:00Z",
                "2026-10-20T12:00:00Z",
                "2026-10-20T18:00:00Z",
            ], utc=True),
            "hours_to_kickoff": [24.0, 18.0, 12.0, 6.0],
        })
        weights = maturity_reliability(add_causal_reliability_state(frame))
        np.testing.assert_allclose(weights, np.array([0.25, 0.60, 1.0, 1.0]))

    def test_development_set_remains_exactly_frozen_nine(self) -> None:
        self.assertEqual(
            EXPECTED_DEVELOPMENT_EVENT_IDS,
            (1, 3, 4, 8, 9, 12, 13, 14, 17),
        )


if __name__ == "__main__":
    unittest.main()
