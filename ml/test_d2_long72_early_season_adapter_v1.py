#!/usr/bin/env python3
"""Regression checks for the audited d2 early-season sporting-state adapter."""
from __future__ import annotations

import pandas as pd

import ml.c1_alpha_model_tournament_v1 as c1
from ml.run_d2_live_replay_anchor_v1 import complete_sporting_state


def test_zero_match_clubs_exist_before_first_round() -> None:
    aliases = {
        "Pogoń Szczecin": "pogonszczecin",
        "Jagiellonia Białystok": "jagiellonia",
        "Lech Poznań": "lech",
        "Cracovia": "cracovia",
    }
    matches = [
        {
            "season": "2026-2027",
            "event_date": "2026-07-24",
            "home_team": "Pogoń Szczecin",
            "away_team": "Cracovia",
            "home_score": 2,
            "away_score": 1,
            "completed": True,
        },
        {
            "season": "2026-2027",
            "event_date": "2026-07-25",
            "home_team": "Jagiellonia Białystok",
            "away_team": "Lech Poznań",
            "home_score": 1,
            "away_score": 1,
            "completed": True,
        },
    ]
    state = complete_sporting_state(
        matches,
        aliases,
        as_of_at=pd.Timestamp("2026-07-21T18:00:00Z"),
        source_season="2026/2027",
    )
    assert set(state["club_key"]) == {
        "pogonszczecin",
        "jagiellonia",
        "lech",
        "cracovia",
    }
    assert (state["matches_played"] == 0).all()
    assert (state["points"] == 0.0).all()
    assert state["ppg"].isna().all()
    assert state["gdpg"].isna().all()
    assert state["last_kickoff_at"].isna().all()


def test_long72_runner_patches_c1_namespace() -> None:
    import ml.run_d2_long72_anchor_contract_v1  # noqa: F401

    assert c1.build_sporting_state is complete_sporting_state


def main() -> None:
    test_zero_match_clubs_exist_before_first_round()
    test_long72_runner_patches_c1_namespace()
    print("d2 long72 early-season adapter checks: PASS")


if __name__ == "__main__":
    main()
