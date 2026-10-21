#!/usr/bin/env python3
"""Unit checks for fixed-temporal a2 external/ensemble robustness audit."""
from __future__ import annotations

import numpy as np

from ml.a2_external_ensemble_closure_v1 import candidate_specs
from ml.a2_external_ensemble_fixed_temporal_v1 import (
    FIXED_CONTRACTS,
    summarize_horizon,
    validate_fixed_contracts,
)


def test_exact_fixed_contracts() -> None:
    validate_fixed_contracts()
    assert set(FIXED_CONTRACTS) == {"T-30", "T-7", "T-1"}

    expected = {
        "T-30": (0.75, 0.0, 0.0, 0.0, 0.25),
        "T-7": (0.25, 0.25, 0.50, 0.0),
        "T-1": (0.0, 0.25, 0.50, 0.25, 0.0),
    }
    for horizon, contract in FIXED_CONTRACTS.items():
        assert contract.weights == expected[horizon]
        assert np.isclose(sum(contract.weights), 1.0)
        assert sum(value > 0 for value in contract.weights) >= 2
        available = {item.id for item in candidate_specs(horizon)}
        assert set(contract.member_ids).issubset(available)


def _toy_fold(improvement: float, p: float = 0.7) -> dict:
    return {
        "scorecard": {
            "mae_improvement": improvement,
            "incumbent": {"mae": 100.0},
            "worst_event_degradation": 15.0,
        },
        "diagnostics": {
            "bootstrap": {"probability_improvement_gt_0": p},
            "club_consistency": {"clubs_reported": 2, "clubs_improved": 1},
        },
    }


def test_summary_pass_requires_all_four_positive() -> None:
    passed = summarize_horizon([_toy_fold(1), _toy_fold(2), _toy_fold(3), _toy_fold(4)])
    assert passed["decision"] == "ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE"
    assert passed["folds_with_positive_mae_improvement"] == 4
    assert passed["all_rolling_folds_positive"] is True

    rejected = summarize_horizon([_toy_fold(1), _toy_fold(2), _toy_fold(-0.1), _toy_fold(4)])
    assert rejected["decision"] == "ROBUSTNESS_REJECT_NOT_ALL_ROLLING_FOLDS_POSITIVE"
    assert rejected["folds_with_positive_mae_improvement"] == 3
    assert rejected["all_rolling_folds_positive"] is False


def main() -> None:
    test_exact_fixed_contracts()
    test_summary_pass_requires_all_four_positive()
    print("a2 fixed-temporal ensemble robustness unit checks: PASS")


if __name__ == "__main__":
    main()
