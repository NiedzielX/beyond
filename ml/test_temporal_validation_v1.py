#!/usr/bin/env python3
"""Regression checks for reusable temporal validation contract v1."""
from __future__ import annotations

import math

import pandas as pd

from ml.temporal_validation_v1 import (
    build_expanding_group_folds,
    build_forward_event_folds,
    event_balanced_mae,
    fold_manifest,
    forecast_metrics,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame({
        "match_key": ["a", "b", "c", "d", "e", "f"],
        "season": ["2021/2022", "2021/2022", "2022/2023", "2022/2023", "2023/2024", "2023/2024"],
        "kickoff_at": pd.to_datetime([
            "2021-08-01T16:00:00Z",
            "2021-09-01T16:00:00Z",
            "2022-08-01T16:00:00Z",
            "2022-09-01T16:00:00Z",
            "2023-08-01T16:00:00Z",
            "2023-09-01T16:00:00Z",
        ], utc=True),
    })


def test_forward_event_is_strictly_past_only() -> None:
    frame = _frame()
    folds = build_forward_event_folds(
        frame,
        entity_col="match_key",
        time_col="kickoff_at",
        min_train_entities=2,
    )
    assert [fold.test_entities for fold in folds] == [("c",), ("d",), ("e",), ("f",)]
    for fold in folds:
        assert pd.Timestamp(fold.train_end_at) < pd.Timestamp(fold.test_start_at)
        assert set(fold.train_entities).isdisjoint(fold.test_entities)


def test_same_timestamp_is_not_training_history() -> None:
    frame = pd.DataFrame({
        "event_id": [1, 2, 3],
        "kickoff_at": pd.to_datetime([
            "2026-01-01T12:00:00Z",
            "2026-01-02T12:00:00Z",
            "2026-01-02T12:00:00Z",
        ], utc=True),
    })
    folds = build_forward_event_folds(
        frame,
        entity_col="event_id",
        time_col="kickoff_at",
        min_train_entities=1,
    )
    assert len(folds) == 2
    for fold in folds:
        assert fold.train_entities == ("1",)


def test_expanding_season_fold_order() -> None:
    frame = _frame()
    folds = build_expanding_group_folds(
        frame,
        entity_col="match_key",
        time_col="kickoff_at",
        group_col="season",
        min_train_groups=2,
    )
    assert len(folds) == 1
    fold = folds[0]
    assert fold.train_groups == ("2021/2022", "2022/2023")
    assert fold.test_groups == ("2023/2024",)
    assert set(fold.train_entities) == {"a", "b", "c", "d"}
    assert set(fold.test_entities) == {"e", "f"}


def test_overlapping_groups_fail_closed() -> None:
    frame = pd.DataFrame({
        "match_key": ["a", "b", "c", "d"],
        "season": ["s1", "s1", "s2", "s2"],
        "kickoff_at": pd.to_datetime([
            "2025-01-01T12:00:00Z",
            "2025-03-01T12:00:00Z",
            "2025-02-01T12:00:00Z",
            "2025-04-01T12:00:00Z",
        ], utc=True),
    })
    try:
        build_expanding_group_folds(
            frame,
            entity_col="match_key",
            time_col="kickoff_at",
            group_col="season",
            min_train_groups=1,
        )
    except RuntimeError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("overlapping temporal groups must fail closed")


def test_metrics_include_mae_tail_and_bias() -> None:
    scored = forecast_metrics([100, 100, 100, 100], [90, 100, 110, 130])
    assert scored["n"] == 4
    assert math.isclose(float(scored["mae"]), 12.5)
    assert math.isclose(float(scored["median_ae"]), 10.0)
    assert float(scored["p90_ae"]) > float(scored["median_ae"])
    assert math.isclose(float(scored["bias"]), 7.5)


def test_event_balanced_mae_does_not_overweight_dense_events() -> None:
    frame = pd.DataFrame({
        "event_id": [1, 1, 1, 2],
        "actual": [100, 100, 100, 100],
        "pred": [110, 110, 110, 140],
    })
    # Per-event MAE = 10 and 40, therefore event-balanced = 25.
    assert math.isclose(
        event_balanced_mae(
            frame,
            event_col="event_id",
            actual_col="actual",
            prediction_col="pred",
        ),
        25.0,
    )


def test_fold_manifest_is_deterministic() -> None:
    folds = build_forward_event_folds(
        _frame(),
        entity_col="match_key",
        time_col="kickoff_at",
        min_train_entities=2,
    )
    first = fold_manifest(folds, protocol_id="unit-forward")
    second = fold_manifest(folds, protocol_id="unit-forward")
    assert first["folds_sha256"] == second["folds_sha256"]
    assert first["strict_temporal_order"] is True
    assert first["random_split_allowed"] is False


def main() -> None:
    test_forward_event_is_strictly_past_only()
    test_same_timestamp_is_not_training_history()
    test_expanding_season_fold_order()
    test_overlapping_groups_fail_closed()
    test_metrics_include_mae_tail_and_bias()
    test_event_balanced_mae_does_not_overweight_dense_events()
    test_fold_manifest_is_deterministic()
    print("temporal validation v1 checks passed")


if __name__ == "__main__":
    main()
