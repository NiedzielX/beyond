"""Frozen trajectory encoder + single precommitted attendance head v1.

Historical attendance rows are used only to fit one fixed Ridge head. This module
does not score historical MAE for model selection.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.linear_model import Ridge

PRECOMMIT_ID = "trajectory-frozen-encoder-ridge-ratio-head-v1"
ENCODER_PRECOMMIT_ID = "trajectory-self-supervised-24h-delta-v1"
RIDGE_ALPHA = 10.0
CORRECTION_RATIO_CAP = 0.10
MAX_CONTEXT_HOURS = 168.0
MIN_PREFIX_OBSERVATIONS = 4
MIN_PREFIX_SPAN_HOURS = 24.0
HORIZON_TO_DAYS = {"T-7": 7, "T-3": 3, "T-1": 1}


@dataclass(frozen=True)
class FrozenAttendanceHeadV1:
    precommit_id: str
    encoder_artifact_sha256: str
    encoder_source_pt_sha256: str
    fit_manifest_sha256: str
    alpha: float
    correction_ratio_cap: float
    scaler_mean: tuple[float, ...]
    scaler_std: tuple[float, ...]
    ridge_coef: tuple[float, ...]
    ridge_intercept: float
    fit_event_ids: tuple[int, ...]
    fit_row_count: int
    production_change: bool = False

    def predict_ratio(self, embedding: np.ndarray) -> float:
        if embedding.shape != (8,):
            raise ValueError("expected 8-dimensional encoder embedding")
        mean = np.asarray(self.scaler_mean, dtype=float)
        std = np.asarray(self.scaler_std, dtype=float)
        coef = np.asarray(self.ridge_coef, dtype=float)
        standardized = (embedding.astype(float) - mean) / std
        raw = float(np.dot(coef, standardized) + self.ridge_intercept)
        return float(np.clip(raw, -self.correction_ratio_cap, self.correction_ratio_cap))


def load_frozen_encoder_v1(path: Path):
    """Load the frozen target-free GRU weights from the durable JSON artifact."""
    torch, nn = _torch_modules()
    raw_bytes = path.read_bytes()
    payload = json.loads(raw_bytes)
    if payload.get("version") != "trajectory-self-supervised-encoder-v1-json":
        raise ValueError("unexpected encoder artifact version")
    if payload.get("precommit_id") != ENCODER_PRECOMMIT_ID:
        raise ValueError("encoder precommit mismatch")
    if payload.get("decision") != "REPRESENTATION_SUPPORTED":
        raise ValueError("encoder is not frozen as REPRESENTATION_SUPPORTED")
    if int(payload.get("input_dim", -1)) != 4 or int(payload.get("hidden_dim", -1)) != 8:
        raise ValueError("encoder architecture mismatch")
    if int(payload.get("parameter_count", -1)) != 417:
        raise ValueError("encoder parameter-count mismatch")

    class Encoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.gru = nn.GRU(input_size=4, hidden_size=8, num_layers=1, batch_first=True)

        def forward(self, sequence, lengths):
            packed = nn.utils.rnn.pack_padded_sequence(
                sequence,
                lengths.cpu(),
                batch_first=True,
                enforce_sorted=False,
            )
            _, hidden = self.gru(packed)
            return hidden[-1]

    model = Encoder()
    current = model.state_dict()
    source = payload.get("state_dict") or {}
    for key in tuple(current):
        artifact_key = key
        if artifact_key not in source:
            raise ValueError(f"missing frozen encoder parameter: {artifact_key}")
        values = np.asarray(source[artifact_key]["values"], dtype=np.float32).reshape(source[artifact_key]["shape"])
        if tuple(values.shape) != tuple(current[key].shape):
            raise ValueError(f"shape mismatch for {key}")
        current[key] = torch.tensor(values, dtype=current[key].dtype)
    model.load_state_dict(current, strict=True)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    return model, payload, hashlib.sha256(raw_bytes).hexdigest()


def build_encoder_sequence_from_pairs_v1(
    sequence_pairs: Iterable[Iterable[float]],
    *,
    horizon: str,
) -> np.ndarray:
    """Build the exact 4-channel frozen-encoder prefix from exported genuine pairs.

    ``sequence_pairs`` must be chronological earliest->latest and contain
    ``[hours_to_kickoff, available_total]``.
    """
    if horizon not in HORIZON_TO_DAYS:
        raise ValueError(f"unsupported attendance-head horizon: {horizon}")
    all_pairs = [(float(row[0]), int(row[1])) for row in sequence_pairs]
    if not all_pairs:
        raise ValueError("no genuine sequence observations")
    first_available = all_pairs[0][1]
    if first_available <= 0:
        raise ValueError("first genuine available_total must be positive")

    source_hours = HORIZON_TO_DAYS[horizon] * 24.0
    context = [
        (hours, available)
        for hours, available in all_pairs
        if hours <= source_hours + MAX_CONTEXT_HOURS + 1e-9
    ]
    if len(context) < MIN_PREFIX_OBSERVATIONS:
        raise ValueError("insufficient encoder prefix observations")
    span = context[0][0] - context[-1][0]
    if span < MIN_PREFIX_SPAN_HOURS:
        raise ValueError("insufficient encoder prefix span")

    rows: list[list[float]] = []
    previous_hours: float | None = None
    previous_index: float | None = None
    for hours, available in context:
        index = available / first_available
        delta_hours = 0.0 if previous_hours is None else previous_hours - hours
        delta_index = 0.0 if previous_index is None else index - previous_index
        if previous_hours is not None and delta_hours <= 0:
            raise ValueError("sequence pairs must be chronological")
        rows.append([hours / 1440.0, index, delta_hours / 24.0, delta_index])
        previous_hours = hours
        previous_index = index
    return np.asarray(rows, dtype=np.float32)


def encode_sequence_v1(model, sequence: np.ndarray) -> np.ndarray:
    torch, _ = _torch_modules()
    if sequence.ndim != 2 or sequence.shape[1] != 4:
        raise ValueError("encoder sequence must have shape [n,4]")
    with torch.no_grad():
        tensor = torch.tensor(sequence[None, :, :], dtype=torch.float32)
        lengths = torch.tensor([sequence.shape[0]], dtype=torch.long)
        hidden = model(tensor, lengths)[0].cpu().numpy().astype(float)
    if hidden.shape != (8,) or not np.isfinite(hidden).all():
        raise ValueError("invalid frozen encoder embedding")
    return hidden


def fit_attendance_head_v1(
    *,
    embeddings: np.ndarray,
    structural_p50: np.ndarray,
    actual_attendance: np.ndarray,
    event_ids: np.ndarray,
    fit_identities: list[dict[str, Any]],
    encoder_artifact_sha256: str,
    encoder_source_pt_sha256: str,
) -> FrozenAttendanceHeadV1:
    """Fit the single precommitted Ridge head without historical model selection."""
    if embeddings.ndim != 2 or embeddings.shape[1] != 8:
        raise ValueError("embeddings must have shape [n,8]")
    n = embeddings.shape[0]
    if not (len(structural_p50) == len(actual_attendance) == len(event_ids) == n == len(fit_identities)):
        raise ValueError("fit arrays have inconsistent lengths")
    if n != 19 or len(set(int(x) for x in event_ids)) != 10:
        raise ValueError("attendance head v1 requires exact frozen 10-event / 19-row fit cohort")
    if np.any(structural_p50 <= 0):
        raise ValueError("structural P50 must be positive")
    if not np.isfinite(embeddings).all():
        raise ValueError("non-finite embedding")

    mean = embeddings.mean(axis=0)
    std = embeddings.std(axis=0)
    std = np.where(std <= 1e-12, 1.0, std)
    x = (embeddings - mean) / std
    y = (actual_attendance.astype(float) - structural_p50.astype(float)) / structural_p50.astype(float)

    counts: dict[int, int] = {}
    for raw in event_ids:
        event_id = int(raw)
        counts[event_id] = counts.get(event_id, 0) + 1
    weights = np.asarray([1.0 / counts[int(event_id)] for event_id in event_ids], dtype=float)

    model = Ridge(alpha=RIDGE_ALPHA, fit_intercept=True)
    model.fit(x, y, sample_weight=weights)

    manifest = {
        "precommit_id": PRECOMMIT_ID,
        "encoder_artifact_sha256": encoder_artifact_sha256,
        "fit_identities": sorted(fit_identities, key=lambda row: (row["ticket_event_id"], row["horizon"])),
        "event_weight_rule": "1/eligible_row_count_for_event",
        "alpha": RIDGE_ALPHA,
        "correction_ratio_cap": CORRECTION_RATIO_CAP,
        "target": "(actual_attendance-structural_p50)/structural_p50",
    }
    fit_manifest_sha256 = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return FrozenAttendanceHeadV1(
        precommit_id=PRECOMMIT_ID,
        encoder_artifact_sha256=encoder_artifact_sha256,
        encoder_source_pt_sha256=encoder_source_pt_sha256,
        fit_manifest_sha256=fit_manifest_sha256,
        alpha=RIDGE_ALPHA,
        correction_ratio_cap=CORRECTION_RATIO_CAP,
        scaler_mean=tuple(float(x) for x in mean),
        scaler_std=tuple(float(x) for x in std),
        ridge_coef=tuple(float(x) for x in model.coef_),
        ridge_intercept=float(model.intercept_),
        fit_event_ids=tuple(sorted(set(int(x) for x in event_ids))),
        fit_row_count=n,
    )


def head_to_json_dict(head: FrozenAttendanceHeadV1) -> dict[str, Any]:
    return {
        "version": "trajectory-frozen-encoder-attendance-head-v1",
        "precommit_id": head.precommit_id,
        "encoder_artifact_sha256": head.encoder_artifact_sha256,
        "encoder_source_pt_sha256": head.encoder_source_pt_sha256,
        "fit_manifest_sha256": head.fit_manifest_sha256,
        "alpha": head.alpha,
        "correction_ratio_cap": head.correction_ratio_cap,
        "scaler_mean": list(head.scaler_mean),
        "scaler_std": list(head.scaler_std),
        "ridge_coef": list(head.ridge_coef),
        "ridge_intercept": head.ridge_intercept,
        "fit_event_ids": list(head.fit_event_ids),
        "fit_row_count": head.fit_row_count,
        "prospective_horizons_days": [7, 3, 1],
        "historical_selection_performed": False,
        "production_change": False,
    }


def load_attendance_head_v1(path: Path) -> FrozenAttendanceHeadV1:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != "trajectory-frozen-encoder-attendance-head-v1":
        raise ValueError("unexpected attendance-head artifact version")
    if payload.get("precommit_id") != PRECOMMIT_ID:
        raise ValueError("attendance-head precommit mismatch")
    if payload.get("historical_selection_performed") is not False:
        raise ValueError("historical-selection guard failed")
    if payload.get("production_change") is not False:
        raise ValueError("production guard failed")
    if float(payload.get("alpha")) != RIDGE_ALPHA or float(payload.get("correction_ratio_cap")) != CORRECTION_RATIO_CAP:
        raise ValueError("frozen attendance-head protocol mismatch")
    return FrozenAttendanceHeadV1(
        precommit_id=payload["precommit_id"],
        encoder_artifact_sha256=payload["encoder_artifact_sha256"],
        encoder_source_pt_sha256=payload["encoder_source_pt_sha256"],
        fit_manifest_sha256=payload["fit_manifest_sha256"],
        alpha=float(payload["alpha"]),
        correction_ratio_cap=float(payload["correction_ratio_cap"]),
        scaler_mean=tuple(float(x) for x in payload["scaler_mean"]),
        scaler_std=tuple(float(x) for x in payload["scaler_std"]),
        ridge_coef=tuple(float(x) for x in payload["ridge_coef"]),
        ridge_intercept=float(payload["ridge_intercept"]),
        fit_event_ids=tuple(int(x) for x in payload["fit_event_ids"]),
        fit_row_count=int(payload["fit_row_count"]),
        production_change=False,
    )


def _torch_modules():
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise RuntimeError("frozen trajectory encoder requires PyTorch") from exc
    return torch, nn
