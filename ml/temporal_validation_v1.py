#!/usr/bin/env python3
"""Reusable time-respecting validation contract for Beyond ML challengers.

The module intentionally does not know about a particular model family. It
creates auditable fold identities and common MAE diagnostics for both:

* expanding group folds (e.g. seasons), and
* forward-event folds (e.g. live ticket events ordered by kickoff).

Every fold is strict: all training observations must occur before the earliest
evaluation observation. Random row/snapshot splitting is outside this contract.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TemporalFold:
    fold_id: str
    protocol: str
    train_entities: tuple[str, ...]
    test_entities: tuple[str, ...]
    train_groups: tuple[str, ...]
    test_groups: tuple[str, ...]
    train_row_count: int
    test_row_count: int
    train_end_at: str
    test_start_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_series(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, utc=True, errors="raise")
    if parsed.isna().any():
        raise RuntimeError("temporal key contains null timestamps")
    return parsed


def _entity_time_map(frame: pd.DataFrame, entity_col: str, time_col: str) -> pd.DataFrame:
    if frame.empty:
        raise RuntimeError("cannot build temporal folds from an empty frame")
    if entity_col not in frame or time_col not in frame:
        raise RuntimeError(f"missing temporal columns: {entity_col}, {time_col}")

    work = frame[[entity_col, time_col]].copy()
    work[entity_col] = work[entity_col].astype(str)
    work[time_col] = _utc_series(work[time_col])
    counts = work.groupby(entity_col, sort=False)[time_col].nunique()
    bad = counts[counts != 1]
    if not bad.empty:
        raise RuntimeError(
            "each independent entity must have exactly one event time; "
            f"violations={bad.index.tolist()}"
        )
    return (
        work.drop_duplicates(entity_col)
        .sort_values([time_col, entity_col])
        .reset_index(drop=True)
    )


def _strict_temporal_assertion(
    frame: pd.DataFrame,
    *,
    entity_col: str,
    time_col: str,
    train_entities: Sequence[str],
    test_entities: Sequence[str],
) -> tuple[pd.Timestamp, pd.Timestamp]:
    train_set = {str(x) for x in train_entities}
    test_set = {str(x) for x in test_entities}
    if not train_set or not test_set:
        raise RuntimeError("temporal fold requires non-empty train and test entities")
    overlap = train_set & test_set
    if overlap:
        raise RuntimeError(f"train/test entity leakage: {sorted(overlap)}")

    work = frame.copy()
    work[entity_col] = work[entity_col].astype(str)
    work[time_col] = _utc_series(work[time_col])
    train = work[work[entity_col].isin(train_set)]
    test = work[work[entity_col].isin(test_set)]
    if train.empty or test.empty:
        raise RuntimeError("fold entities do not resolve to rows")
    train_end = train[time_col].max()
    test_start = test[time_col].min()
    if not train_end < test_start:
        raise RuntimeError(
            f"temporal leakage: train_end={train_end.isoformat()} "
            f"must be strictly before test_start={test_start.isoformat()}"
        )
    return train_end, test_start


def build_forward_event_folds(
    frame: pd.DataFrame,
    *,
    entity_col: str,
    time_col: str,
    min_train_entities: int,
) -> list[TemporalFold]:
    """Hold out each event once enough strictly earlier events exist."""
    if min_train_entities < 1:
        raise ValueError("min_train_entities must be >= 1")
    entities = _entity_time_map(frame, entity_col, time_col)
    folds: list[TemporalFold] = []

    for test_row in entities.to_dict("records"):
        test_entity = str(test_row[entity_col])
        test_time = pd.Timestamp(test_row[time_col])
        earlier = entities[entities[time_col] < test_time]
        if len(earlier) < min_train_entities:
            continue
        train_entities = tuple(earlier[entity_col].astype(str).tolist())
        test_entities = (test_entity,)
        train_end, test_start = _strict_temporal_assertion(
            frame,
            entity_col=entity_col,
            time_col=time_col,
            train_entities=train_entities,
            test_entities=test_entities,
        )
        work_entity = frame[entity_col].astype(str)
        folds.append(TemporalFold(
            fold_id=f"forward-event-{len(folds)+1:03d}-{test_entity}",
            protocol="forward_event_expanding",
            train_entities=train_entities,
            test_entities=test_entities,
            train_groups=(),
            test_groups=(),
            train_row_count=int(work_entity.isin(train_entities).sum()),
            test_row_count=int(work_entity.isin(test_entities).sum()),
            train_end_at=train_end.isoformat(),
            test_start_at=test_start.isoformat(),
        ))
    return folds


def _group_order(
    frame: pd.DataFrame,
    *,
    group_col: str,
    time_col: str,
) -> list[str]:
    if group_col not in frame:
        raise RuntimeError(f"missing group column: {group_col}")
    work = frame[[group_col, time_col]].copy()
    work[group_col] = work[group_col].astype(str)
    work[time_col] = _utc_series(work[time_col])
    starts = work.groupby(group_col, sort=False)[time_col].min().reset_index()
    ends = work.groupby(group_col, sort=False)[time_col].max().reset_index(name="end_at")
    spans = starts.merge(ends, on=group_col).sort_values([time_col, group_col]).reset_index(drop=True)
    for previous, current in zip(spans.to_dict("records"), spans.to_dict("records")[1:]):
        if pd.Timestamp(previous["end_at"]) >= pd.Timestamp(current[time_col]):
            raise RuntimeError(
                f"temporal groups overlap: {previous[group_col]} and {current[group_col]}"
            )
    return spans[group_col].astype(str).tolist()


def build_expanding_group_folds(
    frame: pd.DataFrame,
    *,
    entity_col: str,
    time_col: str,
    group_col: str,
    min_train_groups: int,
) -> list[TemporalFold]:
    """Create expanding-origin folds such as train prior seasons -> next season."""
    if min_train_groups < 1:
        raise ValueError("min_train_groups must be >= 1")
    _entity_time_map(frame, entity_col, time_col)
    ordered_groups = _group_order(frame, group_col=group_col, time_col=time_col)
    folds: list[TemporalFold] = []
    work_group = frame[group_col].astype(str)
    work_entity = frame[entity_col].astype(str)

    for index in range(min_train_groups, len(ordered_groups)):
        train_groups = tuple(ordered_groups[:index])
        test_groups = (ordered_groups[index],)
        train_mask = work_group.isin(train_groups)
        test_mask = work_group.isin(test_groups)
        train_entities = tuple(sorted(work_entity[train_mask].unique().tolist()))
        test_entities = tuple(sorted(work_entity[test_mask].unique().tolist()))
        train_end, test_start = _strict_temporal_assertion(
            frame,
            entity_col=entity_col,
            time_col=time_col,
            train_entities=train_entities,
            test_entities=test_entities,
        )
        folds.append(TemporalFold(
            fold_id=f"expanding-group-{len(folds)+1:03d}-{test_groups[0]}",
            protocol="expanding_group",
            train_entities=train_entities,
            test_entities=test_entities,
            train_groups=train_groups,
            test_groups=test_groups,
            train_row_count=int(train_mask.sum()),
            test_row_count=int(test_mask.sum()),
            train_end_at=train_end.isoformat(),
            test_start_at=test_start.isoformat(),
        ))
    return folds


def forecast_metrics(
    actual: Iterable[float],
    prediction: Iterable[float],
) -> dict[str, float | int]:
    actual_arr = np.asarray(list(actual), dtype=float)
    pred_arr = np.asarray(list(prediction), dtype=float)
    if actual_arr.shape != pred_arr.shape or actual_arr.ndim != 1:
        raise RuntimeError("actual and prediction must be equal-length 1D arrays")
    if len(actual_arr) == 0:
        raise RuntimeError("cannot score empty predictions")
    if not np.isfinite(actual_arr).all() or not np.isfinite(pred_arr).all():
        raise RuntimeError("non-finite values in scoring input")
    error = pred_arr - actual_arr
    absolute = np.abs(error)
    return {
        "n": int(len(actual_arr)),
        "mae": float(np.mean(absolute)),
        "median_ae": float(np.median(absolute)),
        "p90_ae": float(np.quantile(absolute, 0.90)),
        "bias": float(np.mean(error)),
        "rmse": float(np.sqrt(np.mean(error ** 2))),
    }


def event_balanced_mae(
    frame: pd.DataFrame,
    *,
    event_col: str,
    actual_col: str,
    prediction_col: str,
) -> float:
    work = frame[[event_col, actual_col, prediction_col]].copy()
    work["absolute_error"] = (
        pd.to_numeric(work[prediction_col], errors="raise")
        - pd.to_numeric(work[actual_col], errors="raise")
    ).abs()
    per_event = work.groupby(event_col, sort=True)["absolute_error"].mean()
    if per_event.empty:
        raise RuntimeError("cannot score empty event set")
    return float(per_event.mean())


def fold_manifest(
    folds: Sequence[TemporalFold],
    *,
    protocol_id: str,
    source_id: str | None = None,
) -> dict[str, Any]:
    rows = [fold.to_dict() for fold in folds]
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return {
        "version": "temporal-validation-v1",
        "protocol_id": protocol_id,
        "source_id": source_id,
        "fold_count": len(rows),
        "folds_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "folds": rows,
        "strict_temporal_order": True,
        "random_split_allowed": False,
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
