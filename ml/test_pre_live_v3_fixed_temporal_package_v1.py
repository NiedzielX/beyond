#!/usr/bin/env python3
"""Unit checks for Pre-Live v3 fixed-temporal package audit."""
from __future__ import annotations

import numpy as np

from ml.pre_live_v3_fixed_temporal_package_v1 import (
    CHANGED_HORIZONS,
    EXPECTED_PARENT_REFERENCE_MAE,
    HORIZONS,
    T7_MIN_PRIOR,
    T7_VARIANT,
    UNCHANGED_HORIZONS,
    summarize_horizon,
)


def _fold(gain: float, bootstrap_p: float = 0.7) -> dict:
    return {
        "scorecard": {
            "incumbent": {"mae": 100.0},
            "candidate": {"mae": 100.0 - gain},
            "mae_improvement": gain,
            "worst_event_degradation": 10.0,
        },
        "diagnostics": {
            "paired_bootstrap": {
                "probability_improvement_gt_0": bootstrap_p,
            }
        },
    }


def test_package_scope_is_fixed() -> None:
    assert tuple(CHANGED_HORIZONS) == ("T-30", "T-7")
    assert tuple(UNCHANGED_HORIZONS) == ("T-14", "T-3", "T-1")
    assert set(HORIZONS) == set(CHANGED_HORIZONS) | set(UNCHANGED_HORIZONS)
    assert T7_VARIANT.source == "ewma50_residual_fraction"
    assert T7_VARIANT.shrink_k == 4
    assert T7_MIN_PRIOR == 2


def test_parent_reference_values_are_pinned() -> None:
    assert np.isclose(EXPECTED_PARENT_REFERENCE_MAE["T-30"]["2024/2025"], 1834.434818303733)
    assert np.isclose(EXPECTED_PARENT_REFERENCE_MAE["T-7"]["2025/2026"], 1711.095982768726)


def test_changed_horizon_pass_requires_all_four_positive() -> None:
    passed = summarize_horizon([_fold(1), _fold(2), _fold(3), _fold(4)], True)
    assert passed["decision"] == "V3_HORIZON_FIXED_TEMPORAL_PASS"
    assert passed["all_four_positive"] is True

    rejected = summarize_horizon([_fold(1), _fold(2), _fold(-0.1), _fold(4)], True)
    assert rejected["decision"] == "V3_HORIZON_FIXED_TEMPORAL_REJECT"
    assert rejected["all_four_positive"] is False


def test_unchanged_horizon_requires_exact_zero_gain() -> None:
    passed = summarize_horizon([_fold(0), _fold(0), _fold(0), _fold(0)], False)
    assert passed["decision"] == "UNCHANGED_FROZEN_V2_REPRODUCED"

    failed = summarize_horizon([_fold(0), _fold(0), _fold(1e-4), _fold(0)], False)
    assert failed["decision"] == "UNCHANGED_HORIZON_REPRODUCTION_FAILURE"


def main() -> None:
    test_package_scope_is_fixed()
    test_parent_reference_values_are_pinned()
    test_changed_horizon_pass_requires_all_four_positive()
    test_unchanged_horizon_requires_exact_zero_gain()
    print("Pre-Live v3 fixed-temporal package unit checks: PASS")


if __name__ == "__main__":
    main()
