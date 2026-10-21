#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from ml.d2_long72_stage2_reliability_gating_v1 import (
    maturity_reliability,
    magnitude_reliability,
    policy_reliability,
    quality_reliability,
    select_policy,
)


def test_maturity_reliability_scaled_to_24_72h() -> None:
    frame = pd.DataFrame({
        "stage2_observation_index": [1, 2, 3, 3],
        "hours_to_kickoff": [66.0, 54.0, 54.0, 42.0],
    })
    actual = maturity_reliability(frame)
    expected = np.asarray([0.25, 0.60, 0.90, 1.00])
    assert np.allclose(actual, expected, rtol=0.0, atol=0.0)


def test_magnitude_reliability_fixed_bands() -> None:
    delta = np.asarray([0.01, 0.04, 0.06, 0.09, -0.09])
    actual = magnitude_reliability(delta)
    expected = np.asarray([1.00, 0.80, 0.55, 0.35, 0.35])
    assert np.allclose(actual, expected, rtol=0.0, atol=0.0)


def test_quality_reliability_warning_levels() -> None:
    frame = pd.DataFrame({
        "signal_ready": [1.0, 1.0, 0.0],
        "feature_quality_good": [1.0, 1.0, 1.0],
        "data_gap_detected": [0.0, 0.0, 0.0],
        "unexplained_inventory_increase_flag": [0.0, 0.0, 0.0],
        "release_activity_flag": [0.0, 1.0, 0.0],
        "sector_coverage_change_flag": [0.0, 0.0, 0.0],
        "max_visible_gap_hours": [2.0, 2.0, 2.0],
    })
    actual = quality_reliability(frame)
    expected = np.asarray([1.00, 0.50, 0.25])
    assert np.allclose(actual, expected, rtol=0.0, atol=0.0)


def test_combined_policy_uses_conservative_minimum() -> None:
    frame = pd.DataFrame({
        "stage2_observation_index": [1, 3],
        "hours_to_kickoff": [66.0, 42.0],
        "signal_ready": [1.0, 1.0],
        "feature_quality_good": [1.0, 1.0],
        "data_gap_detected": [0.0, 0.0],
        "unexplained_inventory_increase_flag": [0.0, 0.0],
        "release_activity_flag": [0.0, 1.0],
        "sector_coverage_change_flag": [0.0, 0.0],
        "max_visible_gap_hours": [2.0, 2.0],
    })
    delta = np.asarray([0.09, 0.01])
    actual = policy_reliability("P5-combined-reliability", frame, delta)
    expected = np.asarray([0.25, 0.50])
    assert np.allclose(actual, expected, rtol=0.0, atol=0.0)


def _policy_row(
    policy_id: str,
    *,
    eligible: bool,
    overall_mae: float,
    band_mae: float,
    worst: float,
) -> dict:
    return {
        "policy_id": policy_id,
        "selector_eligible": eligible,
        "scorecard": {
            "overall_24_72h": {
                "event_balanced_mae": overall_mae,
                "worst_event_degradation": worst,
            },
            "band_48_72h": {"event_balanced_mae": band_mae},
        },
    }


def test_selector_chooses_best_eligible_policy_only() -> None:
    rows = [
        _policy_row(
            "P0-anchor", eligible=False, overall_mae=3700.0, band_mae=4500.0, worst=0.0
        ),
        _policy_row(
            "P1-raw-inventory", eligible=False, overall_mae=3250.0, band_mae=3900.0, worst=3100.0
        ),
        _policy_row(
            "P2-observation-maturity", eligible=True, overall_mae=3010.0, band_mae=3920.0, worst=1500.0
        ),
        _policy_row(
            "P4-data-quality", eligible=True, overall_mae=3070.0, band_mae=3770.0, worst=800.0
        ),
    ]
    selection = select_policy(rows)
    assert selection["stage2_policy_advanced"] is True
    assert selection["selected_policy_id"] == "P2-observation-maturity"
    assert set(selection["eligible_policy_ids"]) == {
        "P2-observation-maturity",
        "P4-data-quality",
    }


def test_selector_retains_raw_when_no_policy_is_eligible() -> None:
    rows = [
        _policy_row(
            "P0-anchor", eligible=False, overall_mae=3700.0, band_mae=4500.0, worst=0.0
        ),
        _policy_row(
            "P1-raw-inventory", eligible=False, overall_mae=3250.0, band_mae=3900.0, worst=3100.0
        ),
        _policy_row(
            "P2-observation-maturity", eligible=False, overall_mae=3000.0, band_mae=3900.0, worst=1400.0
        ),
    ]
    selection = select_policy(rows)
    assert selection["stage2_policy_advanced"] is False
    assert selection["selected_policy_id"] == "P1-raw-inventory"


def main() -> None:
    test_maturity_reliability_scaled_to_24_72h()
    test_magnitude_reliability_fixed_bands()
    test_quality_reliability_warning_levels()
    test_combined_policy_uses_conservative_minimum()
    test_selector_chooses_best_eligible_policy_only()
    test_selector_retains_raw_when_no_policy_is_eligible()
    print("d2 long72 Stage2 reliability unit checks: PASS")


if __name__ == "__main__":
    main()
