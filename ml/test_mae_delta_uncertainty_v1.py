#!/usr/bin/env python3
"""Regression checks for paired event-block MAE uncertainty v1."""
from __future__ import annotations

import math

import pandas as pd

from ml.mae_delta_uncertainty_v1 import (
    BootstrapConfig,
    bootstrap_delta_mae,
    evaluate_candidate,
    paired_event_errors,
)


def test_event_rows_are_collapsed_before_bootstrap() -> None:
    frame = pd.DataFrame({
        "fold_id": ["f1", "f1", "f1", "f1"],
        "event_id": ["a", "a", "b", "b"],
        "actual": [100, 100, 100, 100],
        "inc": [120, 110, 130, 130],
        "chal": [105, 105, 115, 115],
    })
    errors = paired_event_errors(
        frame,
        event_col="event_id",
        actual_col="actual",
        incumbent_col="inc",
        challenger_col="chal",
        strata_cols=["fold_id"],
    )
    assert len(errors) == 2
    a = errors[errors["event_id"] == "a"].iloc[0]
    assert math.isclose(float(a["incumbent_ae"]), 15.0)
    assert math.isclose(float(a["challenger_ae"]), 5.0)


def test_bootstrap_detects_uniform_improvement() -> None:
    errors = pd.DataFrame({
        "fold_id": ["f1", "f1", "f2", "f2"],
        "event_id": ["a", "b", "c", "d"],
        "incumbent_ae": [20.0, 30.0, 40.0, 50.0],
        "challenger_ae": [10.0, 20.0, 30.0, 40.0],
        "delta_ae": [-10.0, -10.0, -10.0, -10.0],
    })
    result = bootstrap_delta_mae(
        errors,
        strata_cols=["fold_id"],
        config=BootstrapConfig(n_resamples=500, seed=7),
    )
    assert math.isclose(float(result["delta_mae"]), -10.0)
    assert math.isclose(float(result["bootstrap"]["delta_mae_lower"]), -10.0)
    assert math.isclose(float(result["bootstrap"]["delta_mae_upper"]), -10.0)
    assert math.isclose(float(result["bootstrap"]["p_delta_mae_below_zero"]), 1.0)


def test_candidate_pairing_is_one_to_one() -> None:
    predictions = pd.DataFrame({
        "fold_id": ["f1", "f1", "f1", "f1"],
        "match_key": ["a", "b", "a", "b"],
        "candidate_id": ["inc", "inc", "chal", "chal"],
        "actual_attendance": [100, 100, 100, 100],
        "forecast_p50": [120, 120, 105, 105],
    })
    result = evaluate_candidate(
        predictions,
        candidate_id="chal",
        incumbent_id="inc",
        event_col="match_key",
        actual_col="actual_attendance",
        prediction_col="forecast_p50",
        candidate_col="candidate_id",
        strata_cols=["fold_id"],
        config=BootstrapConfig(n_resamples=500, seed=11),
    )
    assert result["independent_event_count"] == 2
    assert math.isclose(float(result["delta_mae"]), -15.0)
    assert result["event_improvement_rate"] == 1.0


def test_mismatched_labels_fail_closed() -> None:
    predictions = pd.DataFrame({
        "fold_id": ["f1", "f1"],
        "match_key": ["a", "a"],
        "candidate_id": ["inc", "chal"],
        "actual_attendance": [100, 101],
        "forecast_p50": [110, 105],
    })
    try:
        evaluate_candidate(
            predictions,
            candidate_id="chal",
            incumbent_id="inc",
            event_col="match_key",
            actual_col="actual_attendance",
            prediction_col="forecast_p50",
            candidate_col="candidate_id",
            strata_cols=["fold_id"],
            config=BootstrapConfig(n_resamples=100, seed=1),
        )
    except RuntimeError as exc:
        assert "actual labels differ" in str(exc)
    else:
        raise AssertionError("mismatched labels must fail closed")


def main() -> None:
    test_event_rows_are_collapsed_before_bootstrap()
    test_bootstrap_detects_uniform_improvement()
    test_candidate_pairing_is_one_to_one()
    test_mismatched_labels_fail_closed()
    print("mae delta uncertainty v1 checks passed")


if __name__ == "__main__":
    main()
