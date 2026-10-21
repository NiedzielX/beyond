#!/usr/bin/env python3
"""Unit checks for the Pre-Live v3 historical research freeze seal."""
from __future__ import annotations

import numpy as np

from ml.pre_live_v3_historical_freeze_v1 import (
    CONTRACT,
    EXPECTED_FINAL_MAE,
    FREEZE_ID,
    HORIZONS,
)


def test_freeze_identity_and_scope() -> None:
    assert FREEZE_ID == "pre-live-v3-historical-candidate-2026-10-21-v1"
    assert HORIZONS == ["T-30", "T-14", "T-7", "T-3", "T-1"]
    assert set(CONTRACT) == set(HORIZONS)


def test_exact_changed_horizon_contracts() -> None:
    assert CONTRACT["T-30"]["current_season_regime"] == "NO_ADJUSTMENT"
    assert "xgboost" in CONTRACT["T-30"]["historical_base"]

    assert CONTRACT["T-7"]["current_season_regime"] == "ewma50-resid-k4-cap05-min2"
    assert "catboost" in CONTRACT["T-7"]["historical_base"]
    assert "lightgbm" in CONTRACT["T-7"]["historical_base"]


def test_unchanged_horizons_match_v2_contract_shape() -> None:
    assert CONTRACT["T-14"]["current_season_regime"] == "NO_ADJUSTMENT"
    assert CONTRACT["T-3"]["current_season_regime"] == "ewma50-resid-k2-cap05-min3"
    assert CONTRACT["T-1"]["current_season_regime"] == "ewma50-resid-k6-cap05-min3"


def test_expected_mae_matrix_is_complete() -> None:
    seasons = {"2022/2023", "2023/2024", "2024/2025", "2025/2026"}
    assert set(EXPECTED_FINAL_MAE) == set(HORIZONS)
    for horizon in HORIZONS:
        assert set(EXPECTED_FINAL_MAE[horizon]) == seasons
        assert all(np.isfinite(value) and value > 0 for value in EXPECTED_FINAL_MAE[horizon].values())


def main() -> None:
    test_freeze_identity_and_scope()
    test_exact_changed_horizon_contracts()
    test_unchanged_horizons_match_v2_contract_shape()
    test_expected_mae_matrix_is_complete()
    print("Pre-Live v3 historical freeze unit checks: PASS")


if __name__ == "__main__":
    main()
