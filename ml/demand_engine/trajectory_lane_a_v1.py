"""Precommitted Lane A Ridge residual benchmark v1.

Implements ``trajectory-lane-a-ridge-residual-v1`` exactly enough for deterministic
historical forward-fold evaluation. No hyperparameter search is performed.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import median
from typing import Iterable

import numpy as np
from sklearn.linear_model import Ridge

from .trajectory_feature_contract_v1 import (
    LANE_A_NUMERIC_FEATURES,
)
from .trajectory_shared_dataset_v1 import TrajectoryDevelopmentExampleV1
from .trajectory_validation_folds_v1 import TrajectoryForwardFoldV1

PRECOMMIT_ID = "trajectory-lane-a-ridge-residual-v1"
RIDGE_ALPHA = 10.0

_BOOLEAN_FEATURES: tuple[str, ...] = (
    "data_gap_detected",
    "release_activity_flag",
    "sector_coverage_change_flag",
    "unexplained_inventory_increase_flag",
)
_CATEGORICAL_FEATURE = "feature_quality"


@dataclass(frozen=True)
class LaneAPreprocessorV1:
    numeric_medians: tuple[float, ...]
    numeric_means: tuple[float, ...]
    numeric_stds: tuple[float, ...]
    feature_quality_categories: tuple[str, ...]


@dataclass(frozen=True)
class LaneAPredictionV1:
    fold_id: str
    ticket_event_id: int
    days_to_event: int
    incumbent_p50: float
    predicted_residual: float
    challenger_p50: float
    actual_attendance: int
    incumbent_abs_error: float
    challenger_abs_error: float


@dataclass(frozen=True)
class LaneAScoreV1:
    precommit_id: str
    alpha: float
    independent_test_events: int
    test_rows: int
    incumbent_event_balanced_mae: float
    challenger_event_balanced_mae: float
    delta_mae: float
    event_improvement_rate: float
    worst_event_degradation: float
    predictions: tuple[LaneAPredictionV1, ...]


def fit_preprocessor_v1(
    examples: Iterable[TrajectoryDevelopmentExampleV1],
) -> LaneAPreprocessorV1:
    rows = tuple(examples)
    if not rows:
        raise ValueError("training examples required")

    medians: list[float] = []
    means: list[float] = []
    stds: list[float] = []
    for name in LANE_A_NUMERIC_FEATURES:
        observed = [
            float(value)
            for row in rows
            if (value := row.lane_a_features.get(name)) is not None
            and _is_finite_number(value)
        ]
        med = float(median(observed)) if observed else 0.0
        imputed = [
            float(row.lane_a_features.get(name))
            if _is_finite_number(row.lane_a_features.get(name))
            else med
            for row in rows
        ]
        mean = float(np.mean(imputed))
        std = float(np.std(imputed))
        if not math.isfinite(std) or std <= 1e-12:
            std = 1.0
        medians.append(med)
        means.append(mean)
        stds.append(std)

    categories = tuple(
        sorted(
            {
                str(row.lane_a_features.get(_CATEGORICAL_FEATURE))
                for row in rows
                if row.lane_a_features.get(_CATEGORICAL_FEATURE) is not None
            }
        )
    )
    return LaneAPreprocessorV1(
        numeric_medians=tuple(medians),
        numeric_means=tuple(means),
        numeric_stds=tuple(stds),
        feature_quality_categories=categories,
    )


def transform_examples_v1(
    examples: Iterable[TrajectoryDevelopmentExampleV1],
    preprocessor: LaneAPreprocessorV1,
) -> np.ndarray:
    rows = tuple(examples)
    matrix: list[list[float]] = []
    for row in rows:
        vector: list[float] = []
        for idx, name in enumerate(LANE_A_NUMERIC_FEATURES):
            raw = row.lane_a_features.get(name)
            missing = not _is_finite_number(raw)
            value = preprocessor.numeric_medians[idx] if missing else float(raw)
            vector.append((value - preprocessor.numeric_means[idx]) / preprocessor.numeric_stds[idx])
            vector.append(1.0 if missing else 0.0)

        for name in _BOOLEAN_FEATURES:
            raw = row.lane_a_features.get(name)
            if raw is None:
                vector.extend((0.0, 1.0))
            else:
                vector.extend((1.0 if bool(raw) else 0.0, 0.0))

        quality = row.lane_a_features.get(_CATEGORICAL_FEATURE)
        for category in preprocessor.feature_quality_categories:
            vector.append(1.0 if quality == category else 0.0)
        matrix.append(vector)

    return np.asarray(matrix, dtype=float)


def evaluate_lane_a_forward_v1(
    examples: Iterable[TrajectoryDevelopmentExampleV1],
    folds: Iterable[TrajectoryForwardFoldV1],
) -> LaneAScoreV1:
    rows = tuple(examples)
    by_event: dict[int, list[TrajectoryDevelopmentExampleV1]] = {}
    for row in rows:
        by_event.setdefault(row.ticket_event_id, []).append(row)

    predictions: list[LaneAPredictionV1] = []
    seen_test_events: set[int] = set()

    for fold in folds:
        train = [row for event_id in fold.train_event_ids for row in by_event.get(event_id, ())]
        test = [row for event_id in fold.test_event_ids for row in by_event.get(event_id, ())]
        if not train or not test:
            continue
        overlap = set(fold.train_event_ids) & set(fold.test_event_ids)
        if overlap:
            raise ValueError(f"train/test event overlap: {sorted(overlap)}")

        pre = fit_preprocessor_v1(train)
        x_train = transform_examples_v1(train, pre)
        x_test = transform_examples_v1(test, pre)
        y_train = np.asarray([row.residual_target for row in train], dtype=float)
        sample_weight = np.asarray([row.event_row_weight for row in train], dtype=float)

        model = Ridge(alpha=RIDGE_ALPHA, fit_intercept=True)
        model.fit(x_train, y_train, sample_weight=sample_weight)
        residuals = model.predict(x_test)

        for row, residual in zip(test, residuals, strict=True):
            seen_test_events.add(row.ticket_event_id)
            challenger = max(0.0, row.incumbent_p50 + float(residual))
            capacity = _capacity_from_lane_a(row)
            if capacity is not None:
                challenger = min(challenger, capacity)
            actual = float(row.actual_attendance)
            predictions.append(
                LaneAPredictionV1(
                    fold_id=fold.fold_id,
                    ticket_event_id=row.ticket_event_id,
                    days_to_event=row.days_to_event,
                    incumbent_p50=row.incumbent_p50,
                    predicted_residual=float(residual),
                    challenger_p50=challenger,
                    actual_attendance=row.actual_attendance,
                    incumbent_abs_error=abs(row.incumbent_p50 - actual),
                    challenger_abs_error=abs(challenger - actual),
                )
            )

    if not predictions:
        raise ValueError("no evaluable Lane A forward predictions")

    incumbent_by_event = _event_mean_errors(predictions, challenger=False)
    challenger_by_event = _event_mean_errors(predictions, challenger=True)
    common = sorted(set(incumbent_by_event) & set(challenger_by_event))
    incumbent_mae = float(np.mean([incumbent_by_event[event_id] for event_id in common]))
    challenger_mae = float(np.mean([challenger_by_event[event_id] for event_id in common]))
    improvements = [
        challenger_by_event[event_id] < incumbent_by_event[event_id]
        for event_id in common
    ]
    degradations = [
        challenger_by_event[event_id] - incumbent_by_event[event_id]
        for event_id in common
    ]

    return LaneAScoreV1(
        precommit_id=PRECOMMIT_ID,
        alpha=RIDGE_ALPHA,
        independent_test_events=len(common),
        test_rows=len(predictions),
        incumbent_event_balanced_mae=incumbent_mae,
        challenger_event_balanced_mae=challenger_mae,
        delta_mae=challenger_mae - incumbent_mae,
        event_improvement_rate=float(np.mean(improvements)),
        worst_event_degradation=max(degradations),
        predictions=tuple(predictions),
    )


def _event_mean_errors(
    predictions: Iterable[LaneAPredictionV1],
    *,
    challenger: bool,
) -> dict[int, float]:
    grouped: dict[int, list[float]] = {}
    for row in predictions:
        grouped.setdefault(row.ticket_event_id, []).append(
            row.challenger_abs_error if challenger else row.incumbent_abs_error
        )
    return {event_id: float(np.mean(values)) for event_id, values in grouped.items()}


def _capacity_from_lane_a(row: TrajectoryDevelopmentExampleV1) -> float | None:
    p50 = row.lane_a_features.get("structural_incumbent_p50")
    share = row.lane_a_features.get("structural_incumbent_p50_share_of_capacity")
    if not _is_finite_number(p50) or not _is_finite_number(share):
        return None
    if float(share) <= 0:
        return None
    return float(p50) / float(share)


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False
