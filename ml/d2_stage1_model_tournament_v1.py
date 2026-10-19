#!/usr/bin/env python3
"""d2 Stage 1: small LOEO live-residual tournament with TSFM challengers.

The independent evaluation unit is the event. All rows from one event remain in
one held-out fold. The target is the attendance residual relative to the sealed
Frozen Pre-Live v2 anchor.

Chronos-2 / Chronos-Bolt are NOT given final attendance as a time-series value.
They forecast only the causal public inventory proxy trajectory
`available_share_of_capacity`. Their zero-shot terminal forecasts are then used
as additional features by a separately LOEO-trained residual model.

No candidate changes production and no C1 v8 artifact is retrained.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

EXPERIMENT = "d2-stage1-model-tournament-v1"
STAGE = "d2-stage1-live-residual-loeo"
EXPECTED_FREEZE_ID = "pre-live-v2-historical-candidate-2026-10-18-v1"
EXPECTED_EVENT_COUNT = 9
EXPECTED_ROW_COUNT = 30
RANDOM_SEED = 42
GRID_HOURS = 6.0
MIN_TSFM_REAL_CONTEXT_POINTS = 2
MAX_LIVE_CORRECTION_OCCUPANCY = 0.10
QUANTILE_LEVELS = (0.1, 0.5, 0.9)

CHRONOS_PACKAGE_VERSION = "2.3.2"
CHRONOS2_MODEL_ID = "amazon/chronos-2"
CHRONOS_BOLT_MODEL_ID = "amazon/chronos-bolt-small"

BASE_FEATURES = [
    "frozen_v2_p50",
    "frozen_v2_expected_occupancy",
    "stadium_capacity",
    "signal_ready",
    "feature_quality_good",
    "hours_to_kickoff",
    "available_total",
    "first_available_total",
    "available_index",
    "available_share_of_capacity",
    "net_removed_since_first",
    "net_removed_since_previous",
    "velocity_since_previous",
    "net_removed_6h",
    "velocity_6h",
    "net_removed_24h",
    "velocity_24h",
    "acceleration_6h_vs_24h",
    "matched_sector_count",
    "matched_absorption",
    "matched_release",
    "coverage_inventory_effect",
    "raw_snapshot_count",
    "clean_snapshot_count",
    "observation_window_hours",
    "max_visible_gap_hours",
    "release_activity_flag",
    "sector_coverage_change_flag",
    "unexplained_inventory_increase_flag",
    "data_gap_detected",
]


@dataclass(frozen=True)
class CandidateSpec:
    id: str
    family: str
    tsfm_prefix: str | None = None


CANDIDATES = (
    CandidateSpec("frozen-v2-zero-correction", "zero"),
    CandidateSpec("train-fold-bias", "bias"),
    CandidateSpec("inventory-linear-extrapolation", "inventory_rule"),
    CandidateSpec("ridge-a10", "ridge"),
    CandidateSpec("huber-a001", "huber"),
    CandidateSpec("histgbr-abs-l7-leaf5-l2-10", "histgbr"),
    CandidateSpec("ridge-a10-plus-chronos2", "ridge", "chronos2"),
    CandidateSpec("ridge-a10-plus-bolt-small", "ridge", "bolt"),
)


def load_stage0_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if len(frame) != EXPECTED_ROW_COUNT:
        raise RuntimeError(f"d2 Stage 1 expects {EXPECTED_ROW_COUNT} rows, got {len(frame)}")
    if frame["ticket_event_id"].nunique() != EXPECTED_EVENT_COUNT:
        raise RuntimeError(
            f"d2 Stage 1 expects {EXPECTED_EVENT_COUNT} events, "
            f"got {frame['ticket_event_id'].nunique()}"
        )
    if set(frame["anchor_status"].astype(str).unique()) != {"FROZEN_V2_EXACT"}:
        raise RuntimeError("d2 Stage 1 requires exact frozen-v2 anchor lineage")
    if set(frame["pre_live_freeze_id"].astype(str).unique()) != {EXPECTED_FREEZE_ID}:
        raise RuntimeError("d2 Stage 1 freeze ID drift")
    frame["as_of_at"] = pd.to_datetime(frame["as_of_at"], utc=True)
    frame = frame.sort_values(["ticket_event_id", "as_of_at"]).reset_index(drop=True)
    if frame["target_live_delta_occupancy"].isna().any():
        raise RuntimeError("missing d2 target_live_delta_occupancy")
    return frame


def event_balanced_weights(frame: pd.DataFrame) -> np.ndarray:
    counts = frame.groupby("ticket_event_id")["ticket_event_id"].transform("count").astype(float)
    weights = 1.0 / counts.to_numpy()
    return weights / float(np.mean(weights))


def _bucket_remaining(hours_to_kickoff: float) -> int:
    if not np.isfinite(hours_to_kickoff):
        raise ValueError("hours_to_kickoff must be finite for TSFM trajectory")
    return max(1, int(math.ceil(max(0.0, hours_to_kickoff) / GRID_HOURS)))


def causal_inventory_context(
    event_rows: pd.DataFrame,
    current_as_of: pd.Timestamp,
) -> dict[str, Any]:
    """Create a causal regularized 6h context from Stage-0 bucket observations.

    Missing historical buckets are forward-filled only from an older observed
    value. No later/future observation is ever used to fill an earlier context.
    """
    history = event_rows[event_rows["as_of_at"] <= current_as_of].copy()
    history = history[history["available_share_of_capacity"].notna()].copy()
    if history.empty:
        return {"ready": False, "reason": "NO_INVENTORY_CONTEXT"}

    history["bucket_remaining"] = history["hours_to_kickoff"].astype(float).map(
        _bucket_remaining
    )
    history = history.sort_values("as_of_at")
    # If a contract ever emits two rows in one 6h bucket, use only the latest
    # row available in that bucket. This remains causal for the current as-of.
    latest_by_bucket = (
        history.sort_values("as_of_at")
        .groupby("bucket_remaining", sort=False)
        .tail(1)
        .set_index("bucket_remaining")
    )
    current_row = history.iloc[-1]
    current_bucket = _bucket_remaining(float(current_row["hours_to_kickoff"]))
    oldest_bucket = int(max(latest_by_bucket.index))

    values: list[float] = []
    real_points = 0
    last_value: float | None = None
    # Chronological order: oldest bucket -> current bucket.
    for bucket in range(oldest_bucket, current_bucket - 1, -1):
        if bucket in latest_by_bucket.index:
            value = float(latest_by_bucket.loc[bucket, "available_share_of_capacity"])
            last_value = value
            real_points += 1
        if last_value is not None:
            values.append(float(last_value))

    if not values:
        return {"ready": False, "reason": "EMPTY_REGULARIZED_CONTEXT"}
    return {
        "ready": real_points >= MIN_TSFM_REAL_CONTEXT_POINTS,
        "reason": None if real_points >= MIN_TSFM_REAL_CONTEXT_POINTS else "INSUFFICIENT_REAL_CONTEXT",
        "context": np.asarray(values, dtype=np.float32),
        "real_context_points": int(real_points),
        "regularized_context_points": int(len(values)),
        "prediction_steps": int(current_bucket),
        "current_available_share": float(current_row["available_share_of_capacity"]),
    }


def _to_numpy(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    return np.asarray(value, dtype=float)


def normalize_quantile_output(
    quantiles: Any,
    prediction_length: int,
    batch_size: int,
) -> list[np.ndarray]:
    """Normalize Chronos-2 list output and Chronos-Bolt tensor output.

    Each returned item has shape (prediction_length, 3) for p10/p50/p90.
    """
    if isinstance(quantiles, list):
        items = [_to_numpy(item) for item in quantiles]
    else:
        arr = _to_numpy(quantiles)
        if arr.ndim < 2:
            raise RuntimeError(f"unexpected Chronos quantile rank {arr.shape}")
        if arr.shape[0] != batch_size:
            raise RuntimeError(
                f"unexpected Chronos batch axis shape={arr.shape} expected={batch_size}"
            )
        items = [arr[index] for index in range(batch_size)]

    normalized: list[np.ndarray] = []
    for item in items:
        arr = np.squeeze(item)
        if arr.ndim != 2:
            raise RuntimeError(f"unexpected per-series Chronos quantile shape {arr.shape}")
        if arr.shape == (prediction_length, len(QUANTILE_LEVELS)):
            pass
        elif arr.shape == (len(QUANTILE_LEVELS), prediction_length):
            arr = arr.T
        else:
            raise RuntimeError(
                f"cannot normalize Chronos quantiles shape={arr.shape} "
                f"prediction_length={prediction_length}"
            )
        normalized.append(arr.astype(float))
    if len(normalized) != batch_size:
        raise RuntimeError("Chronos result batch size changed")
    return normalized


def load_chronos_pipeline(model_id: str):
    try:
        import torch
        from chronos import BaseChronosPipeline
    except ImportError as exc:  # pragma: no cover - tested via injected pipelines
        raise RuntimeError(
            "Chronos runtime missing. Install ml/requirements-d2-tsfm-v1.txt"
        ) from exc
    return BaseChronosPipeline.from_pretrained(
        model_id,
        device_map="cpu",
        torch_dtype=torch.float32,
    )


def add_tsfm_features(
    frame: pd.DataFrame,
    pipeline: Any,
    prefix: str,
) -> pd.DataFrame:
    """Add zero-shot terminal inventory-trajectory forecasts to each row.

    The TSFM sees only current/past public inventory proxy values. Final
    attendance and d2 residual labels never enter the TSFM context.
    """
    result = frame.copy()
    output = {
        f"{prefix}_ready": np.zeros(len(result), dtype=float),
        f"{prefix}_context_real_points": np.zeros(len(result), dtype=float),
        f"{prefix}_context_grid_points": np.zeros(len(result), dtype=float),
        f"{prefix}_prediction_steps": np.zeros(len(result), dtype=float),
        f"{prefix}_terminal_available_share_p10": np.full(len(result), np.nan),
        f"{prefix}_terminal_available_share_p50": np.full(len(result), np.nan),
        f"{prefix}_terminal_available_share_p90": np.full(len(result), np.nan),
        f"{prefix}_terminal_available_share_p50_clipped": np.full(len(result), np.nan),
        f"{prefix}_projected_removed_share_p50": np.full(len(result), np.nan),
        f"{prefix}_uncertainty_width": np.full(len(result), np.nan),
        f"{prefix}_out_of_range_flag": np.zeros(len(result), dtype=float),
    }

    tasks_by_horizon: dict[int, list[tuple[int, dict[str, Any]]]] = {}
    for event_id, event_rows in result.groupby("ticket_event_id", sort=False):
        event_rows = event_rows.sort_values("as_of_at")
        for index, row in event_rows.iterrows():
            context = causal_inventory_context(event_rows, pd.Timestamp(row["as_of_at"]))
            output[f"{prefix}_context_real_points"][index] = float(
                context.get("real_context_points", 0)
            )
            output[f"{prefix}_context_grid_points"][index] = float(
                context.get("regularized_context_points", 0)
            )
            output[f"{prefix}_prediction_steps"][index] = float(
                context.get("prediction_steps", 0)
            )
            if not context.get("ready"):
                continue
            tasks_by_horizon.setdefault(int(context["prediction_steps"]), []).append(
                (int(index), context)
            )

    for prediction_length, tasks in sorted(tasks_by_horizon.items()):
        contexts = [task[1]["context"] for task in tasks]
        quantiles, _ = pipeline.predict_quantiles(
            contexts,
            prediction_length=prediction_length,
            quantile_levels=list(QUANTILE_LEVELS),
        )
        normalized = normalize_quantile_output(
            quantiles,
            prediction_length=prediction_length,
            batch_size=len(tasks),
        )
        for (index, context), forecast in zip(tasks, normalized):
            terminal = forecast[-1]
            p10, p50, p90 = map(float, terminal)
            clipped = float(np.clip(p50, 0.0, 1.0))
            output[f"{prefix}_ready"][index] = 1.0
            output[f"{prefix}_terminal_available_share_p10"][index] = p10
            output[f"{prefix}_terminal_available_share_p50"][index] = p50
            output[f"{prefix}_terminal_available_share_p90"][index] = p90
            output[f"{prefix}_terminal_available_share_p50_clipped"][index] = clipped
            output[f"{prefix}_projected_removed_share_p50"][index] = float(
                context["current_available_share"] - clipped
            )
            output[f"{prefix}_uncertainty_width"][index] = float(max(0.0, p90 - p10))
            output[f"{prefix}_out_of_range_flag"][index] = float(p50 < 0.0 or p50 > 1.0)

    for column, values in output.items():
        result[column] = values
    return result


def tsfm_feature_columns(prefix: str) -> list[str]:
    return [
        f"{prefix}_ready",
        f"{prefix}_context_real_points",
        f"{prefix}_prediction_steps",
        f"{prefix}_terminal_available_share_p50_clipped",
        f"{prefix}_projected_removed_share_p50",
        f"{prefix}_uncertainty_width",
        f"{prefix}_out_of_range_flag",
    ]


def available_base_features(frame: pd.DataFrame) -> list[str]:
    return [column for column in BASE_FEATURES if column in frame.columns]


def _linear_pipeline(model: Any, columns: list[str]) -> Pipeline:
    prep = ColumnTransformer(
        [("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
        ]), columns)],
        remainder="drop",
    )
    return Pipeline([("prep", prep), ("model", model)])


def _tree_pipeline(model: Any, columns: list[str]) -> Pipeline:
    prep = ColumnTransformer(
        [("numeric", SimpleImputer(strategy="median", add_indicator=True), columns)],
        remainder="drop",
    )
    return Pipeline([("prep", prep), ("model", model)])


def fit_predict_learned(
    spec: CandidateSpec,
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> np.ndarray:
    columns = available_base_features(train)
    if spec.tsfm_prefix:
        columns = [*columns, *tsfm_feature_columns(spec.tsfm_prefix)]
    columns = [column for column in columns if column in train.columns and column in test.columns]
    y = train["target_live_delta_occupancy"].astype(float).to_numpy()
    weights = event_balanced_weights(train)

    if spec.family == "ridge":
        model = _linear_pipeline(Ridge(alpha=10.0), columns)
    elif spec.family == "huber":
        model = _linear_pipeline(
            HuberRegressor(epsilon=1.35, alpha=0.01, max_iter=1000), columns
        )
    elif spec.family == "histgbr":
        model = _tree_pipeline(
            HistGradientBoostingRegressor(
                loss="absolute_error",
                learning_rate=0.05,
                max_iter=100,
                max_leaf_nodes=7,
                min_samples_leaf=5,
                l2_regularization=10.0,
                random_state=RANDOM_SEED,
            ),
            columns,
        )
    else:
        raise KeyError(spec.family)

    model.fit(train[columns], y, model__sample_weight=weights)
    return np.asarray(model.predict(test[columns]), dtype=float)


def train_fold_bias(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    weights = event_balanced_weights(train)
    y = train["target_live_delta_occupancy"].astype(float).to_numpy()
    bias = float(np.average(y, weights=weights))
    return np.full(len(test), bias, dtype=float)


def inventory_linear_delta(test: pd.DataFrame) -> np.ndarray:
    capacity = test["stadium_capacity"].astype(float).to_numpy()
    available = test["available_total"].astype(float).to_numpy()
    hours = test["hours_to_kickoff"].astype(float).to_numpy()
    velocity_6h = pd.to_numeric(test.get("velocity_6h"), errors="coerce").to_numpy(dtype=float)
    velocity_24h = pd.to_numeric(test.get("velocity_24h"), errors="coerce").to_numpy(dtype=float)
    velocity_prev = pd.to_numeric(test.get("velocity_since_previous"), errors="coerce").to_numpy(dtype=float)
    velocity = np.where(
        np.isfinite(velocity_6h),
        velocity_6h,
        np.where(np.isfinite(velocity_24h), velocity_24h, velocity_prev),
    )
    velocity = np.where(np.isfinite(velocity), velocity, 0.0)
    projected_available = np.clip(available - velocity * np.maximum(hours, 0.0), 0.0, capacity)
    projected_occupancy = 1.0 - projected_available / capacity
    frozen_occ = test["frozen_v2_expected_occupancy"].astype(float).to_numpy()
    return projected_occupancy - frozen_occ


def governed_forecast(
    frame: pd.DataFrame,
    predicted_delta_occupancy: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    delta = np.clip(
        np.asarray(predicted_delta_occupancy, dtype=float),
        -MAX_LIVE_CORRECTION_OCCUPANCY,
        MAX_LIVE_CORRECTION_OCCUPANCY,
    )
    capacity = frame["stadium_capacity"].astype(float).to_numpy()
    anchor = frame["frozen_v2_p50"].astype(float).to_numpy()
    forecast = np.clip(anchor + delta * capacity, 0.0, capacity)
    return forecast, delta


def loeo_predictions(frame: pd.DataFrame, spec: CandidateSpec) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for held_out in sorted(frame["ticket_event_id"].astype(int).unique()):
        train = frame[frame["ticket_event_id"].astype(int) != int(held_out)].copy()
        test = frame[frame["ticket_event_id"].astype(int) == int(held_out)].copy()
        if spec.family == "zero":
            raw_delta = np.zeros(len(test), dtype=float)
        elif spec.family == "bias":
            raw_delta = train_fold_bias(train, test)
        elif spec.family == "inventory_rule":
            raw_delta = inventory_linear_delta(test)
        else:
            raw_delta = fit_predict_learned(spec, train, test)
        forecast, governed_delta = governed_forecast(test, raw_delta)
        out = test[[
            "ticket_event_id",
            "as_of_at",
            "actual_attendance",
            "stadium_capacity",
            "frozen_v2_p50",
        ]].copy()
        out["candidate_id"] = spec.id
        out["raw_predicted_delta_occupancy"] = raw_delta
        out["governed_delta_occupancy"] = governed_delta
        out["forecast_p50"] = forecast
        out["absolute_error"] = np.abs(
            out["actual_attendance"].astype(float) - out["forecast_p50"].astype(float)
        )
        out["anchor_absolute_error"] = np.abs(
            out["actual_attendance"].astype(float) - out["frozen_v2_p50"].astype(float)
        )
        parts.append(out)
    return pd.concat(parts, ignore_index=True).sort_values(
        ["ticket_event_id", "as_of_at"]
    ).reset_index(drop=True)


def candidate_scorecard(predictions: pd.DataFrame) -> dict[str, Any]:
    per_event_window = (
        predictions.groupby("ticket_event_id", sort=True)
        .agg(
            window_mae=("absolute_error", "mean"),
            anchor_window_mae=("anchor_absolute_error", "mean"),
            rows=("ticket_event_id", "size"),
        )
        .reset_index()
    )
    latest = (
        predictions.sort_values("as_of_at")
        .groupby("ticket_event_id", sort=True)
        .tail(1)
        .copy()
    )
    window_mae = float(per_event_window["window_mae"].mean())
    anchor_window_mae = float(per_event_window["anchor_window_mae"].mean())
    latest_mae = float(latest["absolute_error"].mean())
    anchor_latest_mae = float(latest["anchor_absolute_error"].mean())
    latest_degradation = (
        latest["absolute_error"].astype(float) - latest["anchor_absolute_error"].astype(float)
    )
    latest_improvement = -latest_degradation
    correction_seats = (
        predictions["forecast_p50"].astype(float)
        - predictions["frozen_v2_p50"].astype(float)
    )
    signed_error = (
        predictions["forecast_p50"].astype(float)
        - predictions["actual_attendance"].astype(float)
    )
    event_latest = []
    for row in latest.sort_values("ticket_event_id").to_dict("records"):
        event_latest.append({
            "ticket_event_id": int(row["ticket_event_id"]),
            "actual_attendance": float(row["actual_attendance"]),
            "frozen_v2_p50": float(row["frozen_v2_p50"]),
            "forecast_p50": float(row["forecast_p50"]),
            "anchor_absolute_error": float(row["anchor_absolute_error"]),
            "candidate_absolute_error": float(row["absolute_error"]),
            "mae_improvement": float(row["anchor_absolute_error"] - row["absolute_error"]),
        })
    return {
        "event_count": int(predictions["ticket_event_id"].nunique()),
        "row_count": int(len(predictions)),
        "event_balanced_window_mae": window_mae,
        "anchor_event_balanced_window_mae": anchor_window_mae,
        "window_mae_improvement": anchor_window_mae - window_mae,
        "latest_row_mae": latest_mae,
        "anchor_latest_row_mae": anchor_latest_mae,
        "latest_mae_improvement": anchor_latest_mae - latest_mae,
        "latest_event_improvement_rate": float(np.mean(latest_improvement > 0.0)),
        "worst_latest_event_degradation": float(max(0.0, latest_degradation.max())),
        "best_latest_event_improvement": float(max(0.0, latest_improvement.max())),
        "row_bias": float(signed_error.mean()),
        "nonzero_revision_share": float(np.mean(np.abs(correction_seats) > 1e-9)),
        "mean_abs_revision_seats": float(np.mean(np.abs(correction_seats))),
        "max_abs_revision_seats": float(np.max(np.abs(correction_seats))),
        "events_latest": event_latest,
    }


def choose_research_lead(scorecards: list[dict[str, Any]]) -> str:
    """Rank only; this is not a production-promotion selector.

    Require positive window and latest MAE improvements. Among eligible models,
    rank by latest-row MAE, then event-balanced window MAE, then tail.
    """
    eligible = [
        row for row in scorecards
        if row["candidate_id"] != "frozen-v2-zero-correction"
        and row["scorecard"]["latest_mae_improvement"] > 0.0
        and row["scorecard"]["window_mae_improvement"] > 0.0
    ]
    if not eligible:
        return "frozen-v2-zero-correction"
    return min(
        eligible,
        key=lambda row: (
            row["scorecard"]["latest_row_mae"],
            row["scorecard"]["event_balanced_window_mae"],
            row["scorecard"]["worst_latest_event_degradation"],
            row["candidate_id"],
        ),
    )["candidate_id"]


def run_tournament(
    frame: pd.DataFrame,
    include_tsfm: bool,
    chronos2_pipeline: Any | None = None,
    bolt_pipeline: Any | None = None,
) -> tuple[dict[str, Any], pd.DataFrame]:
    working = frame.copy()
    tsfm_status: dict[str, Any] = {
        "enabled": bool(include_tsfm),
        "target_series": "available_share_of_capacity",
        "grid_hours": GRID_HOURS,
        "min_real_context_points": MIN_TSFM_REAL_CONTEXT_POINTS,
        "label_leakage_allowed": False,
        "chronos2_model_id": CHRONOS2_MODEL_ID,
        "chronos_bolt_model_id": CHRONOS_BOLT_MODEL_ID,
    }
    if include_tsfm:
        chronos2_pipeline = chronos2_pipeline or load_chronos_pipeline(CHRONOS2_MODEL_ID)
        bolt_pipeline = bolt_pipeline or load_chronos_pipeline(CHRONOS_BOLT_MODEL_ID)
        working = add_tsfm_features(working, chronos2_pipeline, "chronos2")
        working = add_tsfm_features(working, bolt_pipeline, "bolt")
        tsfm_status["chronos2_ready_rows"] = int(working["chronos2_ready"].sum())
        tsfm_status["bolt_ready_rows"] = int(working["bolt_ready"].sum())
    else:
        tsfm_status["status"] = "NOT_RUN"

    specs = [
        spec for spec in CANDIDATES
        if include_tsfm or spec.tsfm_prefix is None
    ]
    all_predictions: list[pd.DataFrame] = []
    scorecards: list[dict[str, Any]] = []
    for spec in specs:
        predictions = loeo_predictions(working, spec)
        score = candidate_scorecard(predictions)
        all_predictions.append(predictions)
        scorecards.append({"candidate_id": spec.id, "spec": asdict(spec), "scorecard": score})

    lead = choose_research_lead(scorecards)
    output = {
        "experiment": EXPERIMENT,
        "stage": STAGE,
        "status": "COMPLETED_RESEARCH_TOURNAMENT",
        "production_change": False,
        "promotion_allowed": False,
        "frozen_c1_v8_changed": False,
        "pre_live_freeze_id": EXPECTED_FREEZE_ID,
        "independent_evaluation_unit": "event",
        "validation": "LOEO_ALL_ROWS_HELD_OUT_BY_EVENT",
        "event_balanced_training_weights": True,
        "max_live_correction_occupancy": MAX_LIVE_CORRECTION_OCCUPANCY,
        "event_count": int(working["ticket_event_id"].nunique()),
        "row_count": int(len(working)),
        "tsfm": tsfm_status,
        "candidates": scorecards,
        "research_lead_candidate_id": lead,
        "decision_boundary": (
            "Research ranking only. N=9 independent completed events is not sufficient "
            "for production promotion. Continue prospective evidence collection."
        ),
        "runtime": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
    }
    return output, pd.concat(all_predictions, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-predictions-csv", type=Path, required=True)
    parser.add_argument("--with-tsfm", action="store_true")
    args = parser.parse_args()

    frame = load_stage0_frame(args.input_csv)
    result, predictions = run_tournament(frame, include_tsfm=bool(args.with_tsfm))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    predictions.to_csv(args.output_predictions_csv, index=False)
    print(json.dumps({
        "experiment": result["experiment"],
        "research_lead_candidate_id": result["research_lead_candidate_id"],
        "event_count": result["event_count"],
        "row_count": result["row_count"],
        "tsfm": result["tsfm"],
        "candidates": [
            {
                "candidate_id": row["candidate_id"],
                "latest_row_mae": row["scorecard"]["latest_row_mae"],
                "latest_mae_improvement": row["scorecard"]["latest_mae_improvement"],
                "window_mae_improvement": row["scorecard"]["window_mae_improvement"],
                "worst_latest_event_degradation": row["scorecard"]["worst_latest_event_degradation"],
            }
            for row in result["candidates"]
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
