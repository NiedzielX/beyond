"""Trajectory Lane B v2: residual-ratio target diagnostic.

V2 intentionally reuses Lane B v1's architecture, preprocessing, optimization,
seeds and fold semantics. The only material modelling change is target/output
scaling from raw seat residual to residual ratio.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .trajectory_lane_b_v1 import (
    GRAD_CLIP,
    LEARNING_RATE,
    MAX_EPOCHS,
    SEEDS,
    WEIGHT_DECAY,
    _SmallGRUResidualV1,
    _capacity_from_example,
    _event_mean_errors,
    _pad_sequences,
    _seed_everything,
    _torch_modules,
    fit_global_preprocessor_v1,
    transform_global_v1,
    transform_sequence_v1,
)
from .trajectory_shared_dataset_v1 import TrajectoryDevelopmentExampleV1
from .trajectory_validation_folds_v1 import TrajectoryForwardFoldV1

PRECOMMIT_ID = "trajectory-lane-b-small-gru-residual-ratio-v2"


@dataclass(frozen=True)
class LaneBV2Prediction:
    fold_id: str
    ticket_event_id: int
    days_to_event: int
    incumbent_p50: float
    predicted_residual_ratio: float
    predicted_seat_residual: float
    challenger_p50: float
    actual_attendance: int
    incumbent_abs_error: float
    challenger_abs_error: float
    seed_ratio_predictions: tuple[float, ...]


@dataclass(frozen=True)
class LaneBV2Score:
    precommit_id: str
    seeds: tuple[int, ...]
    independent_test_events: int
    test_rows: int
    incumbent_event_balanced_mae: float
    challenger_event_balanced_mae: float
    delta_mae_vs_incumbent: float
    lane_b_v1_event_balanced_mae: float
    delta_mae_vs_lane_b_v1: float
    lane_a_event_balanced_mae: float
    delta_mae_vs_lane_a: float
    event_improvement_rate: float
    worst_event_degradation: float
    median_seed_ratio_spread: float
    max_seed_ratio_spread: float
    predictions: tuple[LaneBV2Prediction, ...]


def evaluate_lane_b_v2_forward(
    examples: Iterable[TrajectoryDevelopmentExampleV1],
    folds: Iterable[TrajectoryForwardFoldV1],
    *,
    lane_b_v1_event_balanced_mae: float,
    lane_a_event_balanced_mae: float,
) -> LaneBV2Score:
    """Run the frozen v2 diagnostic on exposed strict-forward folds."""
    torch, nn = _torch_modules()
    rows = tuple(examples)
    by_event: dict[int, list[TrajectoryDevelopmentExampleV1]] = {}
    for row in rows:
        if row.incumbent_p50 <= 0:
            raise ValueError("Lane B v2 requires structural incumbent P50 > 0")
        by_event.setdefault(row.ticket_event_id, []).append(row)

    predictions: list[LaneBV2Prediction] = []

    for fold in folds:
        train = [row for event_id in fold.train_event_ids for row in by_event.get(event_id, ())]
        test = [row for event_id in fold.test_event_ids for row in by_event.get(event_id, ())]
        if not train or not test:
            continue
        if set(fold.train_event_ids) & set(fold.test_event_ids):
            raise ValueError("train/test event overlap")

        global_pre = fit_global_preprocessor_v1(train)
        xg_train = transform_global_v1(train, global_pre)
        xg_test = transform_global_v1(test, global_pre)
        seq_train = [transform_sequence_v1(row) for row in train]
        seq_test = [transform_sequence_v1(row) for row in test]
        y_train = np.asarray(
            [row.residual_target / row.incumbent_p50 for row in train],
            dtype=np.float32,
        )
        weights = np.asarray([row.event_row_weight for row in train], dtype=np.float32)

        per_seed_predictions: list[np.ndarray] = []
        for seed in SEEDS:
            _seed_everything(seed, torch)
            model = _SmallGRUResidualV1(nn=nn, torch=torch, global_dim=xg_train.shape[1])
            optimizer = torch.optim.AdamW(
                model.parameters(),
                lr=LEARNING_RATE,
                weight_decay=WEIGHT_DECAY,
            )

            seq_tensor, lengths = _pad_sequences(seq_train, torch)
            global_tensor = torch.tensor(xg_train, dtype=torch.float32)
            target_tensor = torch.tensor(y_train, dtype=torch.float32)
            weight_tensor = torch.tensor(weights, dtype=torch.float32)

            model.train()
            for _ in range(MAX_EPOCHS):
                optimizer.zero_grad(set_to_none=True)
                pred = model(seq_tensor, lengths, global_tensor)
                loss = (torch.abs(pred - target_tensor) * weight_tensor).sum() / weight_tensor.sum()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
                optimizer.step()

            model.eval()
            with torch.no_grad():
                seq_test_tensor, test_lengths = _pad_sequences(seq_test, torch)
                global_test_tensor = torch.tensor(xg_test, dtype=torch.float32)
                seed_pred = model(seq_test_tensor, test_lengths, global_test_tensor).cpu().numpy()
            per_seed_predictions.append(seed_pred.astype(float))

        stacked = np.vstack(per_seed_predictions)
        median_ratios = np.median(stacked, axis=0)
        for idx, row in enumerate(test):
            seed_values = tuple(float(stacked[j, idx]) for j in range(stacked.shape[0]))
            ratio = float(median_ratios[idx])
            seat_residual = ratio * row.incumbent_p50
            challenger = max(0.0, row.incumbent_p50 + seat_residual)
            capacity = _capacity_from_example(row)
            if capacity is not None:
                challenger = min(challenger, capacity)
            actual = float(row.actual_attendance)
            predictions.append(
                LaneBV2Prediction(
                    fold_id=fold.fold_id,
                    ticket_event_id=row.ticket_event_id,
                    days_to_event=row.days_to_event,
                    incumbent_p50=row.incumbent_p50,
                    predicted_residual_ratio=ratio,
                    predicted_seat_residual=seat_residual,
                    challenger_p50=challenger,
                    actual_attendance=row.actual_attendance,
                    incumbent_abs_error=abs(row.incumbent_p50 - actual),
                    challenger_abs_error=abs(challenger - actual),
                    seed_ratio_predictions=seed_values,
                )
            )

    if not predictions:
        raise ValueError("no evaluable Lane B v2 forward predictions")

    incumbent_by_event = _event_mean_errors(predictions, challenger=False)
    challenger_by_event = _event_mean_errors(predictions, challenger=True)
    common = sorted(set(incumbent_by_event) & set(challenger_by_event))
    incumbent_mae = float(np.mean([incumbent_by_event[e] for e in common]))
    challenger_mae = float(np.mean([challenger_by_event[e] for e in common]))
    degradations = [challenger_by_event[e] - incumbent_by_event[e] for e in common]
    improvement_rate = float(np.mean([challenger_by_event[e] < incumbent_by_event[e] for e in common]))
    seed_spreads = [
        max(row.seed_ratio_predictions) - min(row.seed_ratio_predictions)
        for row in predictions
    ]

    return LaneBV2Score(
        precommit_id=PRECOMMIT_ID,
        seeds=SEEDS,
        independent_test_events=len(common),
        test_rows=len(predictions),
        incumbent_event_balanced_mae=incumbent_mae,
        challenger_event_balanced_mae=challenger_mae,
        delta_mae_vs_incumbent=challenger_mae - incumbent_mae,
        lane_b_v1_event_balanced_mae=lane_b_v1_event_balanced_mae,
        delta_mae_vs_lane_b_v1=challenger_mae - lane_b_v1_event_balanced_mae,
        lane_a_event_balanced_mae=lane_a_event_balanced_mae,
        delta_mae_vs_lane_a=challenger_mae - lane_a_event_balanced_mae,
        event_improvement_rate=improvement_rate,
        worst_event_degradation=max(degradations),
        median_seed_ratio_spread=float(np.median(seed_spreads)),
        max_seed_ratio_spread=max(seed_spreads),
        predictions=tuple(predictions),
    )
