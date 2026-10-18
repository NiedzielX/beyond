#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from ml.current_season_regime_fixed_temporal_audit_v1 import apply_fixed_policy
from ml.current_season_residual_regime_v1 import add_same_season_residual_state
from ml.d2_live_replay_anchor_v1 import (
    EXPECTED_C1_CONTRACT_VERSION,
    EXPECTED_C1_EVENT_COUNT,
    EXPECTED_C1_EVENT_IDS,
    EXPECTED_C1_LIVE_ROWS,
    EXPECTED_FREEZE_ID,
    canonical_club_key,
    load_capacity_audit,
)
from ml.run_d2_live_replay_anchor_v1 import (
    FREEZE_SEMANTIC_SHA256,
    complete_sporting_state,
    load_and_verify_freeze_manifest_semantic,
    semantic_json_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
FREEZE_MANIFEST = ROOT / "ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json"
C1_CONTRACT = ROOT / "ml/artifacts/c1_shadow_v8/training_contract_v1.json"
CAPACITY_AUDIT = ROOT / "ml/artifacts/d2_stage0_capacity_audit_v1.json"


class D2LiveReplayAnchorV1Test(unittest.TestCase):
    def test_frozen_pre_live_manifest_is_semantically_pinned(self) -> None:
        manifest = load_and_verify_freeze_manifest_semantic(FREEZE_MANIFEST)
        self.assertEqual(manifest["freeze_id"], EXPECTED_FREEZE_ID)
        self.assertEqual(semantic_json_sha256(manifest), FREEZE_SEMANTIC_SHA256)
        self.assertEqual(int(manifest["manifest_float_decimals"]), 9)
        t1 = next(row for row in manifest["horizons"] if row["horizon"] == "T-1")
        self.assertEqual(
            t1["contract"]["current_season_regime"],
            "ewma50-resid-k6-cap05-min3",
        )

    def test_c1_training_contract_is_still_nine_events_thirty_rows(self) -> None:
        contract = json.loads(C1_CONTRACT.read_text())
        self.assertEqual(contract["contract_version"], EXPECTED_C1_CONTRACT_VERSION)
        self.assertEqual(len(contract["rows"]), EXPECTED_C1_LIVE_ROWS)
        event_ids = tuple(sorted({int(row["ticket_event_id"]) for row in contract["rows"]}))
        self.assertEqual(event_ids, EXPECTED_C1_EVENT_IDS)
        self.assertEqual(len(event_ids), EXPECTED_C1_EVENT_COUNT)

    def test_capacity_audit_covers_all_existing_c1_home_clubs(self) -> None:
        audit = load_capacity_audit(CAPACITY_AUDIT)
        self.assertEqual(
            set(audit["clubs"]),
            {
                "lech",
                "jagiellonia",
                "pogonszczecin",
                "cracovia",
                "slaskwroclaw",
                "gkskatowice",
                "legia",
            },
        )
        for row in audit["clubs"].values():
            self.assertEqual(int(row["distinct_capacities"]), 1)
            self.assertEqual(int(row["missing_capacity_rows"]), 0)
            self.assertGreater(int(row["capacity"]), 0)

    def test_slug_normalization_matches_structural_prior_contract(self) -> None:
        self.assertEqual(canonical_club_key("lech"), "lech")
        self.assertEqual(canonical_club_key("slaskwroclaw"), "slask_wroclaw")
        self.assertEqual(canonical_club_key("pogonszczecin"), "pogonszczecin")

    def test_early_season_sporting_state_includes_zero_match_clubs(self) -> None:
        aliases = {
            "Alpha FC": "alpha",
            "Beta FC": "beta",
            "Gamma FC": "gamma",
            "Delta FC": "delta",
        }
        matches = [
            {
                "season": "2026-2027",
                "event_date": "2026-07-20",
                "home_team": "Alpha FC",
                "away_team": "Beta FC",
                "home_score": None,
                "away_score": None,
                "completed": False,
            },
            {
                "season": "2026-2027",
                "event_date": "2026-07-21",
                "home_team": "Gamma FC",
                "away_team": "Delta FC",
                "home_score": None,
                "away_score": None,
                "completed": False,
            },
        ]
        state = complete_sporting_state(
            matches,
            aliases,
            as_of_at=pd.Timestamp("2026-07-19T12:00:00Z"),
            source_season="2026/2027",
        )
        self.assertEqual(set(state["club_key"]), {"alpha", "beta", "gamma", "delta"})
        self.assertTrue((state["matches_played"] == 0).all())
        self.assertTrue(state["ppg"].isna().all())
        self.assertTrue(state["last_kickoff_at"].isna().all())
        positions = dict(zip(state["club_key"], state["position"]))
        self.assertEqual(positions, {"alpha": 1, "beta": 2, "delta": 3, "gamma": 4})

    def test_sporting_zero_state_updates_after_completed_fixture(self) -> None:
        aliases = {
            "Alpha FC": "alpha",
            "Beta FC": "beta",
            "Gamma FC": "gamma",
            "Delta FC": "delta",
        }
        matches = [
            {
                "season": "2026-2027",
                "event_date": "2026-07-10",
                "home_team": "Alpha FC",
                "away_team": "Beta FC",
                "home_score": 2,
                "away_score": 0,
                "completed": True,
            },
            {
                "season": "2026-2027",
                "event_date": "2026-07-20",
                "home_team": "Gamma FC",
                "away_team": "Delta FC",
                "home_score": None,
                "away_score": None,
                "completed": False,
            },
        ]
        state = complete_sporting_state(
            matches,
            aliases,
            as_of_at=pd.Timestamp("2026-07-19T12:00:00Z"),
            source_season="2026/2027",
        ).set_index("club_key")
        self.assertEqual(int(state.loc["alpha", "matches_played"]), 1)
        self.assertEqual(float(state.loc["alpha", "points"]), 3.0)
        self.assertEqual(int(state.loc["alpha", "position"]), 1)
        self.assertEqual(int(state.loc["beta", "matches_played"]), 1)
        self.assertEqual(int(state.loc["gamma", "matches_played"]), 0)
        self.assertEqual(int(state.loc["delta", "matches_played"]), 0)

    def test_frozen_t1_b2_activates_only_at_three_prior_home_matches(self) -> None:
        rows = pd.DataFrame({
            "match_key": ["m1", "m2", "m3", "m4"],
            "ticket_event_id": [1, 2, 3, 4],
            "season": ["2026/2027"] * 4,
            "home_club_key": ["club"] * 4,
            "away_club_key": ["a", "b", "c", "d"],
            "as_of_at": pd.to_datetime([
                "2026-07-09T12:00:00Z",
                "2026-07-19T12:00:00Z",
                "2026-07-29T12:00:00Z",
                "2026-08-08T12:00:00Z",
            ]),
            "kickoff_at": pd.to_datetime([
                "2026-07-10T12:00:00Z",
                "2026-07-20T12:00:00Z",
                "2026-07-30T12:00:00Z",
                "2026-08-09T12:00:00Z",
            ]),
            "target_attendance": [16000.0, 16000.0, 16000.0, 16000.0],
            "capacity": [20000.0] * 4,
        })
        base = np.asarray([10000.0, 10000.0, 10000.0, 10000.0])
        state = add_same_season_residual_state(rows, base)
        prediction, _ = apply_fixed_policy(state, base, "T-1")
        self.assertEqual(state["regime_prior_home_matches"].astype(int).tolist(), [0, 1, 2, 3])
        np.testing.assert_allclose(prediction[:3], base[:3], rtol=0.0, atol=0.0)
        self.assertGreater(float(prediction[3]), float(base[3]))
        self.assertLessEqual(abs(float(prediction[3] - base[3])), 1000.0 + 1e-12)


if __name__ == "__main__":
    unittest.main()
