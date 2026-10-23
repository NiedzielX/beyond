#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from ml.p10b_pooled_vs_prelive_v3_v1 import (
    HORIZONS,
    canonical_folds,
    evaluate,
    prepare_frame,
)

UTC = timezone.utc
SEASONS = ["2021/2022", "2022/2023", "2023/2024", "2024/2025", "2025/2026"]


def synthetic_store(matches_per_season: int = 12) -> pd.DataFrame:
    rows = []
    match_no = 0
    horizon_days = {"T-30": 30, "T-14": 14, "T-7": 7, "T-3": 3, "T-1": 1}
    for season_idx, season in enumerate(SEASONS):
        start = datetime(2021 + season_idx, 8, 1, 16, tzinfo=UTC)
        for local_idx in range(matches_per_season):
            match_no += 1
            kickoff = start + timedelta(days=7 * local_idx)
            target = 12000.0 + 300 * season_idx + 175 * local_idx + ((match_no * 97) % 401)
            baseline = target + ((match_no * 53) % 501) - 250.0
            for horizon in HORIZONS:
                days = horizon_days[horizon]
                rows.append({
                    "match_key": f"m-{match_no:04d}",
                    "season": season,
                    "horizon": horizon,
                    "as_of_at": kickoff - timedelta(days=days),
                    "kickoff_at": kickoff,
                    "home_club_key": f"home-{local_idx % 6}",
                    "away_club_key": f"away-{(local_idx + 2) % 7}",
                    "target_attendance": target,
                    "training_eligible": True,
                    "target_eligible": True,
                    "baseline_season": baseline,
                    "capacity": 30000.0,
                    "home_ppg": 1.0 + 0.1 * (local_idx % 5),
                    "away_ppg": 1.2 + 0.08 * (local_idx % 4),
                    "season_progress": local_idx / matches_per_season,
                })
    return pd.DataFrame(rows)


def fake_champion(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
):
    del training_seasons
    rows = store[
        (store["season"] == season)
        & (store["horizon"] == horizon)
        & (store["training_eligible"])
    ].copy()
    # Stable synthetic incumbent. The unit test validates protocol mechanics,
    # not whether the real challenger wins.
    prediction = rows["baseline_season"].astype(float).to_numpy()
    return rows, prediction


def test_four_folds_match_frozen_prelive_v3_protocol() -> None:
    frame = prepare_frame(synthetic_store())
    folds = canonical_folds(frame)
    assert len(folds) == 4
    assert [fold.test_groups[0] for fold in folds] == SEASONS[1:]
    for fold in folds:
        assert not set(fold.train_entities) & set(fold.test_entities)


def test_p10b_runs_without_match_leakage_and_cannot_robust_advance_without_business_threshold() -> None:
    result, predictions, manifest = evaluate(
        synthetic_store(),
        champion_provider=fake_champion,
        minimum_meaningful_mae_improvement=None,
    )
    assert result["version"] == "p10b-pooled-vs-prelive-v3-v1"
    assert result["incumbent_id"] == "pre-live-v3-historical-candidate-2026-10-21-v1"
    assert result["match_blocking"] is True
    assert len(result["fold_scores"]) == 4
    assert manifest["fold_count"] == 4
    assert result["production_change"] is False
    assert result["live_adjustment"] == 0
    assert result["governance_v2"]["robust_advance_allowed"] is False
    assert "business_meaningful_mae_threshold_not_defined" in result["governance_v2"]["reason_codes"]
    assert predictions["match_key"].nunique() == 4 * 12
    assert len(predictions) == 4 * 12 * 5


def test_ineligible_match_horizon_does_not_change_total_match_blocking() -> None:
    store = synthetic_store()
    mask = (store["match_key"] == "m-0001") & (store["horizon"] == "T-30")
    store.loc[mask, "training_eligible"] = False
    frame = prepare_frame(store)
    assert len(frame[frame["match_key"] == "m-0001"]) == 4
    folds = canonical_folds(frame)
    assert len(folds) == 4


if __name__ == "__main__":
    test_four_folds_match_frozen_prelive_v3_protocol()
    test_p10b_runs_without_match_leakage_and_cannot_robust_advance_without_business_threshold()
    test_ineligible_match_horizon_does_not_change_total_match_blocking()
    print("p10b_pooled_vs_prelive_v3_v1 tests passed")
