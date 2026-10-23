#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from ml.p10_pooled_horizon_global_v1 import clean_frame, evaluate, match_balanced_weights

UTC = timezone.utc
SEASONS = ["2021/2022", "2022/2023", "2023/2024", "2024/2025", "2025/2026"]
HORIZONS = [("T-30", 30), ("T-14", 14), ("T-7", 7), ("T-3", 3), ("T-1", 1)]


def synthetic_frame(matches_per_season: int = 8) -> pd.DataFrame:
    rows = []
    match_number = 0
    for season_index, season in enumerate(SEASONS):
        season_start = datetime(2021 + season_index, 8, 1, 16, tzinfo=UTC)
        for local_match in range(matches_per_season):
            match_number += 1
            kickoff = season_start + timedelta(days=7 * local_match)
            capacity = 28000.0 + (local_match % 4) * 1500.0
            base_demand = 12000.0 + season_index * 350.0 + local_match * 180.0
            target = base_demand + (local_match % 3) * 450.0 + ((match_number * 137) % 401) - 200.0
            for horizon, days in HORIZONS:
                # The PIT features get progressively more informative closer to kickoff.
                horizon_signal = target - days * 16.0
                rows.append({
                    "match_key": f"m-{match_number:03d}",
                    "season": season,
                    "horizon": horizon,
                    "as_of_at": kickoff - timedelta(days=days),
                    "kickoff_at": kickoff,
                    "home_club_key": f"home-{local_match % 4}",
                    "away_club_key": f"away-{(local_match + 1) % 5}",
                    "target_attendance": float(target),
                    "target_eligible": True,
                    "training_eligible": True,
                    "capacity": capacity,
                    "season_progress": local_match / matches_per_season,
                    "home_ppg": 1.0 + 0.1 * (local_match % 4),
                    "away_ppg": 1.2 + 0.08 * (local_match % 5),
                    "home_attendance_r5": base_demand - 250.0,
                    "baseline_r5": horizon_signal,
                })
    return pd.DataFrame(rows)


def test_match_balanced_weights_sum_to_one_per_match() -> None:
    frame = clean_frame(synthetic_frame(3))
    frame["weight"] = match_balanced_weights(frame)
    totals = frame.groupby("match_key")["weight"].sum().to_numpy()
    assert np.allclose(totals, 1.0)


def test_match_balanced_weights_handle_missing_horizon_rows() -> None:
    raw = synthetic_frame(3)
    raw.loc[(raw["match_key"] == "m-001") & (raw["horizon"] == "T-30"), "training_eligible"] = False
    frame = clean_frame(raw)
    frame["weight"] = match_balanced_weights(frame)
    totals = frame.groupby("match_key")["weight"].sum().to_numpy()
    assert np.allclose(totals, 1.0)


def test_duplicate_match_horizon_fails_closed() -> None:
    raw = synthetic_frame(3)
    duplicated = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
    try:
        clean_frame(duplicated)
    except RuntimeError as exc:
        assert "one PIT row per match/horizon" in str(exc)
    else:
        raise AssertionError("expected duplicate match/horizon failure")


def test_p10_runs_with_match_blocked_expanding_folds() -> None:
    result, predictions, manifest = evaluate(synthetic_frame(8))
    assert result["version"] == "p10-pooled-horizon-global-v1"
    assert result["match_blocking"] is True
    assert result["fold_count"] == 3
    assert manifest["fold_count"] == 3
    assert result["matches"] == 40
    assert len(predictions) == 24 * 5
    assert result["local_match_balanced_mae"] > 0
    assert "horizon_days" in result["numeric_features"]
    for fold in manifest["folds"]:
        assert not set(fold["train_entities"]) & set(fold["test_entities"])
    assert result["governance_v2"]["decision"] in {
        "NO_RESEARCH_GAIN", "POINT_GAIN_UNCERTAINTY_LIMITED"
    }
    # No business threshold is supplied, so robust advancement is impossible.
    assert result["governance_v2"]["robust_advance_allowed"] is False


if __name__ == "__main__":
    test_match_balanced_weights_sum_to_one_per_match()
    test_match_balanced_weights_handle_missing_horizon_rows()
    test_duplicate_match_horizon_fails_closed()
    test_p10_runs_with_match_blocked_expanding_folds()
    print("p10_pooled_horizon_global_v1 tests passed")
