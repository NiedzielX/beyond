#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from ml.d2_long72_stage2_reliability_gating_v1 import (
    CAUSAL_RELIABILITY_FEATURES,
    FORBIDDEN_RELIABILITY_FEATURE_NAMES,
    PolicySpec,
    enrich_policy_row,
    magnitude_reliability,
    maturity_reliability,
    policy_predictions,
    quality_reliability,
    select_policy,
)


def test_reliability_feature_contract_has_no_labels() -> None:
    assert not FORBIDDEN_RELIABILITY_FEATURE_NAMES.intersection(
        CAUSAL_RELIABILITY_FEATURES
    )


def test_maturity_reliability_fixed_bands() -> None:
    frame = pd.DataFrame(
        {
            "stage2_observation_index": [1, 2, 3, 3, 4],
            "hours_to_kickoff": [66.0, 54.0, 54.0, 42.0, 61.0],
        }
    )
    actual = maturity_reliability(frame)
    expected = np.array([0.25, 0.60, 0.90, 1.00, 0.75])
    assert np.allclose(actual, expected)


def test_magnitude_reliability_fixed_bands() -> None:
    actual = magnitude_reliability(
        np.array([0.0, 0.025, 0.03, 0.05, 0.06, 0.075, 0.09])
    )
    expected = np.array([1.0, 1.0, 0.8, 0.8, 0.55, 0.55, 0.35])
    assert np.allclose(actual, expected)


def test_quality_reliability_soft_and_hard_warnings() -> None:
    frame = pd.DataFrame(
        {
            "signal_ready": [1, 1, 0, 1],
            "feature_quality_good": [1, 1, 1, 1],
            "data_gap_detected": [0, 0, 0, 1],
            "unexplained_inventory_increase_flag": [0, 0, 0, 0],
            "release_activity_flag": [0, 1, 0, 1],
            "sector_coverage_change_flag": [0, 0, 0, 0],
            "max_visible_gap_hours": [6, 6, 6, 20],
        }
    )
    actual = quality_reliability(frame)
    assert np.allclose(actual, np.array([1.0, 0.5, 0.25, 0.25]))


def _base_policy_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticket_event_id": [1, 1],
            "club_slug": ["x", "x"],
            "home_team": ["X", "X"],
            "away_team": ["Y", "Y"],
            "kickoff_at": ["2026-01-03T00:00:00Z", "2026-01-03T00:00:00Z"],
            "as_of_at": pd.to_datetime(
                ["2026-01-01T00:00:00Z", "2026-01-01T06:00:00Z"], utc=True
            ),
            "hours_to_kickoff": [48.0, 42.0],
            "actual_attendance": [9000.0, 9000.0],
            "stadium_capacity": [10000.0, 10000.0],
            "anchor_p50": [8000.0, 8000.0],
            "anchor_absolute_error": [1000.0, 1000.0],
            "governed_delta_occupancy": [0.10, 0.10],
            "stage2_observation_index": [1, 2],
            "stage2_observation_span_hours": [0.0, 6.0],
            "signal_ready": [1, 1],
            "feature_quality_good": [1, 1],
            "data_gap_detected": [0, 0],
            "unexplained_inventory_increase_flag": [0, 0],
            "release_activity_flag": [0, 0],
            "sector_coverage_change_flag": [0, 0],
            "max_visible_gap_hours": [6.0, 6.0],
        }
    )


def test_anchor_and_raw_policy_prediction_identity() -> None:
    base = _base_policy_frame()
    anchor = policy_predictions(base, PolicySpec("P0-anchor", ""))
    raw = policy_predictions(base, PolicySpec("P1-raw-inventory", ""))
    assert np.allclose(anchor["forecast_p50"], [8000.0, 8000.0])
    assert np.allclose(raw["forecast_p50"], [9000.0, 9000.0])
    assert np.allclose(anchor["reliability"], [0.0, 0.0])
    assert np.allclose(raw["reliability"], [1.0, 1.0])


def _band(
    mae: float,
    improvement: float,
    worst: float,
    bias: float = 0.0,
) -> dict:
    return {
        "event_balanced_mae": mae,
        "mae_improvement": improvement,
        "worst_event_degradation": worst,
        "event_balanced_bias": bias,
    }


def _score(
    overall_imp: float,
    b24_imp: float,
    b48_imp: float,
    worst: float,
    worst48: float,
    bias: float,
    original_imp: float,
    later_imp: float,
) -> dict:
    return {
        "overall_24_72h": _band(3000.0, overall_imp, worst, bias),
        "band_24_48h": _band(2800.0, b24_imp, worst, bias),
        "band_48_72h": _band(3500.0, b48_imp, worst48, bias),
        "original_stage1_exposed_subset": {"mae_improvement": original_imp},
        "later_exposed_subset": {"mae_improvement": later_imp},
    }


def test_stage2_gate_requires_retention_tail_bias_and_both_subsets() -> None:
    raw_score = _score(
        overall_imp=400.0,
        b24_imp=600.0,
        b48_imp=600.0,
        worst=3000.0,
        worst48=3600.0,
        bias=1400.0,
        original_imp=-400.0,
        later_imp=1900.0,
    )
    good = {
        "policy_id": "P2-observation-maturity",
        "scorecard": _score(
            overall_imp=250.0,
            b24_imp=350.0,
            b48_imp=350.0,
            worst=2000.0,
            worst48=2500.0,
            bias=900.0,
            original_imp=50.0,
            later_imp=900.0,
        ),
    }
    bad_subset = {
        "policy_id": "P3-correction-magnitude",
        "scorecard": _score(
            overall_imp=260.0,
            b24_imp=360.0,
            b48_imp=360.0,
            worst=1900.0,
            worst48=2400.0,
            bias=850.0,
            original_imp=-1.0,
            later_imp=1000.0,
        ),
    }
    enrich_policy_row(good, raw_score)
    enrich_policy_row(bad_subset, raw_score)
    assert good["selector_eligible"] is True
    assert bad_subset["selector_eligible"] is False

    rows = [
        {"policy_id": "P0-anchor", "selector_eligible": False},
        {"policy_id": "P1-raw-inventory", "selector_eligible": False},
        good,
        bad_subset,
    ]
    selected = select_policy(rows)
    assert selected["selected_policy_id"] == "P2-observation-maturity"
    assert selected["stage2_policy_advanced"] is True


def test_selector_retains_raw_when_nobody_passes() -> None:
    rows = [
        {"policy_id": "P0-anchor", "selector_eligible": False},
        {"policy_id": "P1-raw-inventory", "selector_eligible": False},
        {"policy_id": "P2-observation-maturity", "selector_eligible": False},
    ]
    selected = select_policy(rows)
    assert selected["decision"] == "RAW_INVENTORY_RETAINED_NO_STAGE2_POLICY_PASSED"
    assert selected["selected_policy_id"] == "P1-raw-inventory"
    assert selected["stage2_policy_advanced"] is False


def main() -> None:
    test_reliability_feature_contract_has_no_labels()
    test_maturity_reliability_fixed_bands()
    test_magnitude_reliability_fixed_bands()
    test_quality_reliability_soft_and_hard_warnings()
    test_anchor_and_raw_policy_prediction_identity()
    test_stage2_gate_requires_retention_tail_bias_and_both_subsets()
    test_selector_retains_raw_when_nobody_passes()
    print("d2 long72 Stage2 reliability unit checks: PASS")


if __name__ == "__main__":
    main()
