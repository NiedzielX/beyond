"""Target-free 24h trajectory representation learning v1.

This module implements the frozen precommit
``trajectory-self-supervised-24h-delta-v1``. It never consumes attendance or
structural-prior values.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math
import random
from typing import Iterable

import numpy as np

PRECOMMIT_ID = "trajectory-self-supervised-24h-delta-v1"
FROZEN_CUTOFF = "2026-10-28T22:09:43.958409Z"
TRAIN_EVENT_IDS: tuple[int, ...] = (3, 1, 4, 9, 14, 15, 18, 11, 19, 5, 20, 10, 16, 23, 21, 22, 443, 446, 6, 444, 445)
VALIDATION_EVENT_IDS: tuple[int, ...] = (447, 449, 450, 451, 452)
MAX_CONTEXT_HOURS = 168.0
MIN_PREFIX_OBSERVATIONS = 4
MIN_PREFIX_SPAN_HOURS = 24.0
FUTURE_MIN_HOURS = 18.0
FUTURE_TARGET_HOURS = 24.0
FUTURE_MAX_HOURS = 30.0
HIDDEN_DIM = 8
HEAD_DIM = 8
DROPOUT = 0.20
LEARNING_RATE = 0.001
WEIGHT_DECAY = 0.01
BATCH_SIZE = 128
EPOCHS = 100
GRAD_CLIP = 1.0
SEED = 17


@dataclass(frozen=True)
class TargetFreeObservationV1:
    snapshot_id: int
    captured_at: datetime
    hours_to_kickoff: float
    available_total: int


@dataclass(frozen=True)
class TargetFreeEventV1:
    ticket_event_id: int
    club_slug: str
    kickoff_at: datetime
    observations: tuple[TargetFreeObservationV1, ...]


@dataclass(frozen=True)
class TargetFreePairV1:
    ticket_event_id: int
    club_slug: str
    source_at: datetime
    future_at: datetime
    elapsed_hours: float
    sequence: np.ndarray
    target_delta_index: float
    event_pair_weight: float


@dataclass(frozen=True)
class TargetFreePredictionV1:
    ticket_event_id: int
    club_slug: str
    source_at: datetime
    target_delta_index: float
    predicted_delta_index: float
    baseline_abs_error: float
    model_abs_error: float


@dataclass(frozen=True)
class SelfSupervisedScoreV1:
    precommit_id: str
    train_events: int
    train_pairs: int
    validation_events: int
    validation_pairs: int
    baseline_event_balanced_mae: float
    model_event_balanced_mae: float
    delta_mae_vs_baseline: float
    pair_mae: float
    signed_bias: float
    improved_validation_events: int
    predictions: tuple[TargetFreePredictionV1, ...]


def build_target_free_pairs_v1(event: TargetFreeEventV1) -> tuple[TargetFreePairV1, ...]:
    """Build frozen ~24h pairs from one genuine hourly-bucket event sequence."""
    observations = tuple(sorted(event.observations, key=lambda row: (row.captured_at, row.snapshot_id)))
    if not observations:
        return ()
    first_available = observations[0].available_total
    if first_available <= 0:
        return ()

    raw_pairs: list[tuple[int, int, tuple[TargetFreeObservationV1, ...], float]] = []
    for source_idx, source in enumerate(observations):
        candidates: list[tuple[float, datetime, int, float]] = []
        for future_idx in range(source_idx + 1, len(observations)):
            future = observations[future_idx]
            elapsed = (future.captured_at - source.captured_at).total_seconds() / 3600.0
            if elapsed < FUTURE_MIN_HOURS:
                continue
            if elapsed > FUTURE_MAX_HOURS:
                break
            candidates.append((abs(elapsed - FUTURE_TARGET_HOURS), future.captured_at, future_idx, elapsed))
        if not candidates:
            continue
        _, _, future_idx, elapsed = min(candidates, key=lambda item: (item[0], item[1], item[2]))

        context_start = source.captured_at - timedelta(hours=MAX_CONTEXT_HOURS)
        context = tuple(
            row for row in observations[: source_idx + 1]
            if row.captured_at >= context_start
        )
        if len(context) < MIN_PREFIX_OBSERVATIONS:
            continue
        span = (context[-1].captured_at - context[0].captured_at).total_seconds() / 3600.0
        if span < MIN_PREFIX_SPAN_HOURS:
            continue
        raw_pairs.append((source_idx, future_idx, context, elapsed))

    if not raw_pairs:
        return ()

    pair_weight = 1.0 / len(raw_pairs)
    pairs: list[TargetFreePairV1] = []
    for source_idx, future_idx, context, elapsed in raw_pairs:
        sequence = _sequence_array(context, first_available)
        source_index = observations[source_idx].available_total / first_available
        future_index = observations[future_idx].available_total / first_available
        pairs.append(
            TargetFreePairV1(
                ticket_event_id=event.ticket_event_id,
                club_slug=event.club_slug,
                source_at=observations[source_idx].captured_at,
                future_at=observations[future_idx].captured_at,
                elapsed_hours=elapsed,
                sequence=sequence,
                target_delta_index=float(future_index - source_index),
                event_pair_weight=pair_weight,
            )
        )
    return tuple(pairs)


def train_and_score_self_supervised_v1(
    train_pairs: Iterable[TargetFreePairV1],
    validation_pairs: Iterable[TargetFreePairV1],
):
    """Train the frozen GRU and score against zero-change on held-out events."""
    torch, nn = _torch_modules()
    train = tuple(train_pairs)
    validation = tuple(validation_pairs)
    if not train or not validation:
        raise ValueError("train and validation pairs are required")
    if set(row.ticket_event_id for row in train) & set(row.ticket_event_id for row in validation):
        raise ValueError("train/validation event overlap")

    _seed_everything(SEED, torch)
    model = _SelfSupervisedGRUV1(nn=nn, torch=torch)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)

    train_seq, train_lengths = _pad_all([row.sequence for row in train])
    train_target = np.asarray([row.target_delta_index for row in train], dtype=np.float32)
    train_weight = np.asarray([row.event_pair_weight for row in train], dtype=np.float32)

    generator = torch.Generator()
    generator.manual_seed(SEED)
    n = len(train)
    model.train()
    for _ in range(EPOCHS):
        order = torch.randperm(n, generator=generator).numpy()
        for start in range(0, n, BATCH_SIZE):
            indices = order[start : start + BATCH_SIZE]
            seq_tensor = torch.tensor(train_seq[indices], dtype=torch.float32)
            length_tensor = torch.tensor(train_lengths[indices], dtype=torch.long)
            target_tensor = torch.tensor(train_target[indices], dtype=torch.float32)
            weight_tensor = torch.tensor(train_weight[indices], dtype=torch.float32)

            optimizer.zero_grad(set_to_none=True)
            prediction = model(seq_tensor, length_tensor)
            loss = (torch.abs(prediction - target_tensor) * weight_tensor).sum() / weight_tensor.sum()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            optimizer.step()

    val_seq, val_lengths = _pad_all([row.sequence for row in validation])
    model.eval()
    with torch.no_grad():
        predictions = model(
            torch.tensor(val_seq, dtype=torch.float32),
            torch.tensor(val_lengths, dtype=torch.long),
        ).cpu().numpy().astype(float)

    rows: list[TargetFreePredictionV1] = []
    for pair, predicted in zip(validation, predictions, strict=True):
        target = pair.target_delta_index
        rows.append(
            TargetFreePredictionV1(
                ticket_event_id=pair.ticket_event_id,
                club_slug=pair.club_slug,
                source_at=pair.source_at,
                target_delta_index=target,
                predicted_delta_index=float(predicted),
                baseline_abs_error=abs(target),
                model_abs_error=abs(float(predicted) - target),
            )
        )

    baseline_by_event = _event_mae(rows, model=False)
    model_by_event = _event_mae(rows, model=True)
    event_ids = sorted(model_by_event)
    baseline_mae = float(np.mean([baseline_by_event[event_id] for event_id in event_ids]))
    model_mae = float(np.mean([model_by_event[event_id] for event_id in event_ids]))
    improved = sum(model_by_event[event_id] < baseline_by_event[event_id] for event_id in event_ids)
    pair_mae = float(np.mean([row.model_abs_error for row in rows]))
    signed_bias = float(np.mean([row.predicted_delta_index - row.target_delta_index for row in rows]))

    score = SelfSupervisedScoreV1(
        precommit_id=PRECOMMIT_ID,
        train_events=len({row.ticket_event_id for row in train}),
        train_pairs=len(train),
        validation_events=len(event_ids),
        validation_pairs=len(validation),
        baseline_event_balanced_mae=baseline_mae,
        model_event_balanced_mae=model_mae,
        delta_mae_vs_baseline=model_mae - baseline_mae,
        pair_mae=pair_mae,
        signed_bias=signed_bias,
        improved_validation_events=improved,
        predictions=tuple(rows),
    )
    return score, model


def _sequence_array(context: tuple[TargetFreeObservationV1, ...], first_available: int) -> np.ndarray:
    rows: list[list[float]] = []
    previous: TargetFreeObservationV1 | None = None
    previous_index: float | None = None
    for observation in context:
        index = observation.available_total / first_available
        delta_hours = 0.0
        delta_index = 0.0
        if previous is not None and previous_index is not None:
            delta_hours = (observation.captured_at - previous.captured_at).total_seconds() / 3600.0
            delta_index = index - previous_index
        rows.append([
            observation.hours_to_kickoff / 1440.0,
            index,
            delta_hours / 24.0,
            delta_index,
        ])
        previous = observation
        previous_index = index
    return np.asarray(rows, dtype=np.float32)


def _pad_all(sequences: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    max_len = max(len(sequence) for sequence in sequences)
    padded = np.zeros((len(sequences), max_len, 4), dtype=np.float32)
    lengths = np.zeros(len(sequences), dtype=np.int64)
    for idx, sequence in enumerate(sequences):
        padded[idx, : len(sequence), :] = sequence
        lengths[idx] = len(sequence)
    return padded, lengths


class _SelfSupervisedGRUV1:
    def __new__(cls, *, nn, torch):
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.gru = nn.GRU(input_size=4, hidden_size=HIDDEN_DIM, num_layers=1, batch_first=True)
                self.head = nn.Sequential(
                    nn.Linear(HIDDEN_DIM, HEAD_DIM),
                    nn.ReLU(),
                    nn.Dropout(DROPOUT),
                    nn.Linear(HEAD_DIM, 1),
                )

            def forward(self, sequences, lengths):
                packed = nn.utils.rnn.pack_padded_sequence(
                    sequences,
                    lengths.cpu(),
                    batch_first=True,
                    enforce_sorted=False,
                )
                _, hidden = self.gru(packed)
                return self.head(hidden[-1]).squeeze(1)

        return Model()


def _event_mae(rows: Iterable[TargetFreePredictionV1], *, model: bool) -> dict[int, float]:
    grouped: dict[int, list[float]] = {}
    for row in rows:
        grouped.setdefault(row.ticket_event_id, []).append(
            row.model_abs_error if model else row.baseline_abs_error
        )
    return {event_id: float(np.mean(errors)) for event_id, errors in grouped.items()}


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


def _torch_modules():
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise RuntimeError("self-supervised trajectory v1 requires PyTorch") from exc
    return torch, nn
