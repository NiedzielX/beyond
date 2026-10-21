#!/usr/bin/env python3
"""Unit checks for Pre-Live v3 regime revalidation."""
from __future__ import annotations

import numpy as np

from ml.pre_live_v3_regime_revalidation_v1 import (
    HORIZONS,
    ROBUST_HISTORICAL_CONTRACTS,
    aggregate_maturity_development,
    select_maturity,
    v3_historical_model_id,
)
from ml.current_season_residual_regime_v1 import RegimeVariant


def test_v3_historical_contract_scope() -> None:
    assert set(HORIZONS) == {"T-30", "T-14", "T-7", "T-3", "T-1"}
    assert set(ROBUST_HISTORICAL_CONTRACTS) == {"T-30", "T-7", "T-1"}
    assert "ensemble" in v3_historical_model_id("T-30")
    assert "ensemble" in v3_historical_model_id("T-7")
    assert "ensemble" in v3_historical_model_id("T-1")
    assert "retain-current-a2" in v3_historical_model_id("T-14")
    assert "retain-current-a2" in v3_historical_model_id("T-3")


def _scorecard(improvement: float, incumbent_mae: float = 100.0) -> dict:
    candidate_mae = incumbent_mae - improvement
    return {
        "incumbent": {"mae": incumbent_mae, "median_ae": 90.0, "p90_ae": 180.0},
        "candidate": {
            "mae": candidate_mae,
            "median_ae": 89.0,
            "p90_ae": 179.0,
        },
        "mae_improvement": improvement,
        "worst_event_degradation": 25.0,
        "event_improvement_rate": 0.6,
    }


def _fold(variant: RegimeVariant, gains: dict[int | None, float]) -> dict:
    candidates = {
        "NO_ADJUSTMENT": {
            "scorecard": _scorecard(0.0),
        }
    }
    for min_prior in (1, 2, 3):
        candidates[f"{variant.id}-min{min_prior}"] = {
            "scorecard": _scorecard(gains[min_prior]),
        }
    return {"season": "toy", "candidates": candidates}


def test_maturity_selection_requires_two_fold_gain() -> None:
    variant = RegimeVariant(source="ewma50_residual_fraction", shrink_k=6)
    folds = [
        _fold(variant, {1: 1.0, 2: 0.8, 3: 0.6}),
        _fold(variant, {1: 1.0, 2: 0.8, 3: 0.6}),
    ]
    aggregate = aggregate_maturity_development(folds, variant)
    selected, info = select_maturity(aggregate)
    assert selected != "NO_ADJUSTMENT"
    assert info["selected_row"]["mean_relative_mae_improvement"] >= 0.005

    bad_folds = [
        _fold(variant, {1: 1.0, 2: 0.8, 3: 0.6}),
        _fold(variant, {1: -0.1, 2: -0.1, 3: -0.1}),
    ]
    bad_aggregate = aggregate_maturity_development(bad_folds, variant)
    bad_selected, _ = select_maturity(bad_aggregate)
    assert bad_selected == "NO_ADJUSTMENT"


def test_robust_weights_are_fixed_and_non_degenerate() -> None:
    expected = {
        "T-30": (0.75, 0.0, 0.0, 0.0, 0.25),
        "T-7": (0.25, 0.25, 0.50, 0.0),
        "T-1": (0.0, 0.25, 0.50, 0.25, 0.0),
    }
    for horizon, weights in expected.items():
        contract = ROBUST_HISTORICAL_CONTRACTS[horizon]
        assert contract.weights == weights
        assert np.isclose(sum(weights), 1.0)
        assert sum(weight > 0 for weight in weights) >= 2


def main() -> None:
    test_v3_historical_contract_scope()
    test_maturity_selection_requires_two_fold_gain()
    test_robust_weights_are_fixed_and_non_degenerate()
    print("Pre-Live v3 regime revalidation unit checks: PASS")


if __name__ == "__main__":
    main()
