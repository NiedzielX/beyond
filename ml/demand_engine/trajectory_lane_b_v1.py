"""Precommitted Lane B small-GRU residual model v1.

Implements ``trajectory-lane-b-small-gru-residual-v1``. This module requires
PyTorch at runtime but remains research-only and performs no architecture or
hyperparameter search.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from statistics import median
from typing import Iterable

import numpy as np

from .trajectory_shared_dataset_v1 import TrajectoryDevelopmentExampleV1
from .trajectory_validation_folds_v1 import TrajectoryForwardFoldV1

PRECOMMIT_ID = "trajectory-lane-b-small-gru-residual-v1"
SEEDS: tuple[int, ...] = (17, 29, 41)
HIDDEN_DIM = 8
HEAD_DIM = 8
DROPOUT = 0.20
LEARNING_RATE = 0.001
WEIGHT_DECAY = 0.01
MAX_EPOCHS = 200
GRAD_CLIP = 1.0

_GLOBAL_NUMERIC_FIELDS: tuple[str, ...] = (
    "days_to_event",
    "snapshot_age_minutes",
    "clean_snapshot_count",
    "observation_window_hours",
    "max_visible_gap_hours",
    "structural_incumbent_p50",
    "structural_incumbent_p50_share_of_capacity",
    "sequence_length",
)
_GLOBAL_BOOLEAN_FIELDS: tuple[str, ...] = ("verified_capacity_available",)


@dataclass(frozen=True)
class LaneBGlobalPreprocessorV1:
    medians: tuple[float, ...]
    means: tuple[float, ...]
    stds: tuple[float, ...]


@dataclass(frozen=True)
class LaneBPredictionV1:
    fold_id: str
    ticket_event_id: int
    days_to_event: int
    incumbent_p50: float
    predicted_residual: float
    challenger_p50: float
    actual_attendance: int
    incumbent_abs_error: float
    challenger_abs_error: float
    seed_predictions: tuple[float, ...]


@dataclass(frozen=True)
class LaneBScoreV1:
    precommit_id: str
    seeds: tuple[int, ...]
    independent_test_events: int
    test_rows: int
    incumbent_event_balanced_mae: float
    challenger_event_balanced_mae: float
    delta_mae_vs_incumbent: float
    lane_a_event_balanced_mae: float | None
    delta_mae_vs_lane_a: float | None
    event_improvement_rate: float
    worst_event_degradation: float
    median_seed_spread: float
    max_seed_spread: float
    predictions: tuple[LaneBPredictionV1, ...]


def fit_global_preprocessor_v1(
    examples: Iterable[TrajectoryDevelopmentExampleV1],
) -> LaneBGlobalPreprocessorV1:
    rows = tuple(examples)
    if not rows:
        raise ValueError("training examples required")
    medians: list[float] = []
    means: list[float] = []
    stds: list[float] = []
    for name in _GLOBAL_NUMERIC_FIELDS:
        observed = [
            float(value)
            for row in rows
            if _finite(value := row.lane_b_global_features.get(name))
        ]
        med = float(median(observed)) if observed else 0.0
        vals = [
            float(row.lane_b_global_features.get(name))
            if _finite(row.lane_b_global_features.get(name))
            else med
            for row in rows
        ]
        mean = float(np.mean(vals))
        std = float(np.std(vals))
        if not math.isfinite(std) or std <= 1e-12:
            std = 1.0
        medians.append(med)
        means.append(mean)
        stds.append(std)
    return LaneBGlobalPreprocessorV1(tuple(medians), tuple(means), tuple(stds))


def transform_global_v1(
    examples: Iterable[TrajectoryDevelopmentExampleV1],
    pre: LaneBGlobalPreprocessorV1,
) -> np.ndarray:
    rows = tuple(examples)
    out: list[list[float]] = []
    for row in rows:
        vector: list[float] = []
        for idx, name in enumerate(_GLOBAL_NUMERIC_FIELDS):
            raw = row.lane_b_global_features.get(name)
            missing = not _finite(raw)
            value = pre.medians[idx] if missing else float(raw)
            vector.append((value - pre.means[idx]) / pre.stds[idx])
            vector.append(1.0 if missing else 0.0)
        for name in _GLOBAL_BOOLEAN_FIELDS:
            raw = row.lane_b_global_features.get(name)
            vector.append(1.0 if bool(raw) else 0.0)
        out.append(vector)
    return np.asarray(out, dtype=np.float32)


def transform_sequence_v1(example: TrajectoryDevelopmentExampleV1) -> np.ndarray:
    """Apply only the deterministic v1 sequence transforms."""
    rows: list[list[float]] = []
    for step in example.lane_b_sequence.steps:
        rows.append(
            [
                float(step.hours_to_kickoff) / 1440.0,
                float(step.available_index),
                float(step.available_share_of_capacity) if step.available_share_of_capacity is not None else 0.0,
                float(step.delta_hours_since_previous) / 24.0 if step.delta_hours_since_previous is not None else 0.0,
                float(step.delta_available_index) if step.delta_available_index is not None else 0.0,
            ]
        )
    if not rows:
        raise ValueError("Lane B sequence must contain at least one genuine step")
    return np.asarray(rows, dtype=np.float32)


def evaluate_lane_b_forward_v1(
    examples: Iterable[TrajectoryDevelopmentExampleV1],
    folds: Iterable[TrajectoryForwardFoldV1],
    *,
    lane_a_event_balanced_mae: float | None = None,
) -> LaneBScoreV1:
    torch, nn = _torch_modules()
    rows = tuple(examples)
    by_event: dict[int, list[TrajectoryDevelopmentExampleV1]] = {}
    for row in rows:
        by_event.setdefault(row.ticket_event_id, []).append(row)

    predictions: list[LaneBPredictionV1] = []

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
        y_train = np.asarray([row.residual_target for row in train], dtype=np.float32)
        weights = np.asarray([row.event_row_weight for row in train], dtype=np.float32)

        per_seed_predictions: list[np.ndarray] = []
        for seed in SEEDS:
            _seed_everything(seed, torch)
            model = _SmallGRUResidualV1(
                nn=nn,
                torch=torch,
                global_dim=xg_train.shape[1],
            )
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
        median_residuals = np.median(stacked, axis=0)
        for idx, row in enumerate(test):
            seed_values = tuple(float(stacked[j, idx]) for j in range(stacked.shape[0]))
            residual = float(median_residuals[idx])
            challenger = max(0.0, row.incumbent_p50 + residual)
            capacity = _capacity_from_example(row)
            if capacity is not None:
                challenger = min(challenger, capacity)
            actual = float(row.actual_attendance)
            predictions.append(
                LaneBPredictionV1(
                    fold_id=fold.fold_id,
                    ticket_event_id=row.ticket_event_id,
                    days_to_event=row.days_to_event,
                    incumbent_p50=row.incumbent_p50,
                    predicted_residual=residual,
                    challenger_p50=challenger,
                    actual_attendance=row.actual_attendance,
                    incumbent_abs_error=abs(row.incumbent_p50 - actual),
                    challenger_abs_error=abs(challenger - actual),
                    seed_predictions=seed_values,
                )
            )

    if not predictions:
        raise ValueError("no evaluable Lane B forward predictions")

    incumbent_by_event = _event_mean_errors(predictions, challenger=False)
    challenger_by_event = _event_mean_errors(predictions, challenger=True)
    common = sorted(set(incumbent_by_event) & set(challenger_by_event))
    incumbent_mae = float(np.mean([incumbent_by_event[e] for e in common]))
    challenger_mae = float(np.mean([challenger_by_event[e] for e in common]))
    degradations = [challenger_by_event[e] - incumbent_by_event[e] for e in common]
    improvement_rate = float(np.mean([challenger_by_event[e] < incumbent_by_event[e] for e in common]))
    seed_spreads = [max(row.seed_predictions) - min(row.seed_predictions) for row in predictions]

    return LaneBScoreV1(
        precommit_id=PRECOMMIT_ID,
        seeds=SEEDS,
        independent_test_events=len(common),
        test_rows=len(predictions),
        incumbent_event_balanced_mae=incumbent_mae,
        challenger_event_balanced_mae=challenger_mae,
        delta_mae_vs_incumbent=challenger_mae - incumbent_mae,
        lane_a_event_balanced_mae=lane_a_event_balanced_mae,
        delta_mae_vs_lane_a=(
            challenger_mae - lane_a_event_balanced_mae
            if lane_a_event_balanced_mae is not None
            else None
        ),
        event_improvement_rate=improvement_rate,
        worst_event_degradation=max(degradations),
        median_seed_spread=float(np.median(seed_spreads)),
        max_seed_spread=max(seed_spreads),
        predictions=tuple(predictions),
    )


class _SmallGRUResidualV1:
    """Tiny wrapper that behaves like an nn.Module without importing torch globally."""

    def __new__(cls, *, nn, torch, global_dim: int):
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.gru = nn.GRU(input_size=5, hidden_size=HIDDEN_DIM, num_layers=1, batch_first=True)
                self.head = nn.Sequential(
                    nn.Linear(HIDDEN_DIM + global_dim, HEAD_DIM),
                    nn.ReLU(),
                    nn.Dropout(DROPOUT),
                    nn.Linear(HEAD_DIM, 1),
                )

            def forward(self, sequences, lengths, global_features):
                packed = nn.utils.rnn.pack_padded_sequence(
                    sequences,
                    lengths.cpu(),
                    batch_first=True,
                    enforce_sorted=False,
                )
                _, hidden = self.gru(packed)
                encoded = hidden[-1]
                return self.head(torch.cat([encoded, global_features], dim=1)).squeeze(1)

        return Model()


def _pad_sequences(sequences: list[np.ndarray], torch):
    lengths = torch.tensor([len(seq) for seq in sequences], dtype=torch.long)
    max_len = int(max(len(seq) for seq in sequences))
    padded = np.zeros((len(sequences), max_len, 5), dtype=np.float32)
    for idx, seq in enumerate(sequences):
        padded[idx, : len(seq), :] = seq
    return torch.tensor(padded, dtype=torch.float32), lengths


def _seed_everything(seed: int, torch) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if hasattr(torch, "cuda") and torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass


def _event_mean_errors(predictions: Iterable[LaneBPredictionV1], *, challenger: bool) -> dict[int, float]:
    grouped: dict[int, list[float]] = {}
    for row in predictions:
        grouped.setdefault(row.ticket_event_id, []).append(
            row.challenger_abs_error if challenger else row.incumbent_abs_error
        )
    return {event_id: float(np.mean(values)) for event_id, values in grouped.items()}


def _capacity_from_example(row: TrajectoryDevelopmentExampleV1) -> float | None:
    p50 = row.lane_b_global_features.get("structural_incumbent_p50")
    share = row.lane_b_global_features.get("structural_incumbent_p50_share_of_capacity")
    if not _finite(p50) or not _finite(share) or float(share) <= 0:
        return None
    return float(p50) / float(share)


def _finite(value: object) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _torch_modules():
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise RuntimeError("trajectory Lane B v1 requires PyTorch") from exc
    return torch, nn
