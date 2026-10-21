#!/usr/bin/env python3
"""d2 long72 Stage 1: early-live residual tournament for 24-72h.

This experiment deliberately excludes the final 24h from model selection. The
existing frozen Ridge/P2 package already covers that problem. Here we ask only
whether PIT ticket trajectory adds value before the final day.

Independent unit: event. Validation: Leave-One-Event-Out. Target: occupancy
residual relative to the frozen T-3 checkpoint-hold anchor. Corrections are
capped at +/-10 percentage points occupancy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

EXPERIMENT = "d2-long72-stage1-model-tournament-v1"
STAGE = "d2-long72-stage1-early-live-loeo"
EXPECTED_FULL_DATASET_SHA256 = "2af62094eec57aba3c3e8c96ed33d06cf611f9cd60b690d72e2deedbdf63ce17"
EXPECTED_FULL_EVENT_COUNT = 14
EXPECTED_FULL_ROW_COUNT = 130
EXPECTED_EARLY_ROW_COUNT = 80
EXPECTED_EARLY_EVENT_COUNT = 13
EXPECTED_48_72_EVENT_COUNT = 10
EARLY_MIN_HOURS = 24.0
EARLY_MAX_HOURS = 72.0
MAX_LIVE_CORRECTION_OCCUPANCY = 0.10
RANDOM_SEED = 42

ORIGINAL_STAGE1_EVENT_IDS = frozenset({1, 3, 4, 8, 9, 12, 13, 14, 17})
LATER_EXPOSED_EVENT_IDS = frozenset({5, 11, 15, 18, 19})

BASE_FEATURES = [
    "anchor_p50",
    "anchor_expected_occupancy",
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
    "net_removed_72h",
    "velocity_72h",
    "net_removed_7d",
    "velocity_7d",
    "velocity_6h_pct_of_first_per_hour",
    "velocity_24h_pct_of_first_per_hour",
    "velocity_72h_pct_of_first_per_hour",
    "velocity_7d_pct_of_first_per_hour",
    "velocity_6h_pct_of_capacity_per_hour",
    "velocity_24h_pct_of_capacity_per_hour",
    "velocity_72h_pct_of_capacity_per_hour",
    "velocity_7d_pct_of_capacity_per_hour",
    "acceleration_6h_vs_24h",
    "acceleration_24h_vs_72h",
    "acceleration_72h_vs_7d",
    "matched_sector_count",
    "entered_sector_count",
    "left_sector_count",
    "matched_absorption",
    "matched_release",
    "coverage_inventory_effect",
    "raw_snapshot_count",
    "clean_snapshot_count",
    "excluded_anomaly_count",
    "duplicate_timestamp_count",
    "invalid_snapshot_count",
    "observation_window_hours",
    "max_visible_gap_hours",
    "checkpoint_ready",
    "sector_coverage_change_flag",
    "release_activity_flag",
    "unexplained_inventory_increase_flag",
    "data_gap_detected",
]


@dataclass(frozen=True)
class CandidateSpec:
    id: str
    family: str
    alpha: float | None = None


CANDIDATES = (
    CandidateSpec("anchor-zero-correction", "zero"),
    CandidateSpec("train-fold-bias", "bias"),
    CandidateSpec("inventory-linear-extrapolation", "inventory_rule"),
    CandidateSpec("ridge-a10", "ridge", 10.0),
    CandidateSpec("ridge-a30", "ridge", 30.0),
    CandidateSpec("huber-a001", "huber", 0.01),
    CandidateSpec("histgbr-abs-l7-leaf5-l2-10", "histgbr"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_long72(path: Path) -> pd.DataFrame:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_FULL_DATASET_SHA256:
        raise RuntimeError(
            f"long72 frozen dataset hash drift actual={actual_sha} "
            f"expected={EXPECTED_FULL_DATASET_SHA256}"
        )
    frame = pd.read_csv(path)
    if len(frame) != EXPECTED_FULL_ROW_COUNT:
        raise RuntimeError(f"expected {EXPECTED_FULL_ROW_COUNT} full rows, got {len(frame)}")
    if frame["ticket_event_id"].nunique() != EXPECTED_FULL_EVENT_COUNT:
        raise RuntimeError("full long72 event count drift")
    frame["as_of_at"] = pd.to_datetime(frame["as_of_at"], utc=True)
    frame["kickoff_at"] = pd.to_datetime(frame["kickoff_at"], utc=True)
    frame["anchor_checkpoint_as_of_at"] = pd.to_datetime(
        frame["anchor_checkpoint_as_of_at"], utc=True
    )
    if (frame["anchor_checkpoint_as_of_at"] > frame["as_of_at"]).any():
        raise RuntimeError("future checkpoint found in frozen long72 dataset")
    if frame["target_live_delta_occupancy"].isna().any():
        raise RuntimeError("missing long72 occupancy target")
    return frame.sort_values(["ticket_event_id", "as_of_at"]).reset_index(drop=True)


def early_frame(full: pd.DataFrame) -> pd.DataFrame:
    frame = full[
        (full["hours_to_kickoff"].astype(float) > EARLY_MIN_HOURS)
        & (full["hours_to_kickoff"].astype(float) <= EARLY_MAX_HOURS)
    ].copy()
    if len(frame) != EXPECTED_EARLY_ROW_COUNT:
        raise RuntimeError(f"expected {EXPECTED_EARLY_ROW_COUNT} early rows, got {len(frame)}")
    if frame["ticket_event_id"].nunique() != EXPECTED_EARLY_EVENT_COUNT:
        raise RuntimeError("24-72h event count drift")
    if frame.loc[frame["hours_to_kickoff"] > 48, "ticket_event_id"].nunique() != EXPECTED_48_72_EVENT_COUNT:
        raise RuntimeError("48-72h event count drift")
    if set(frame["anchor_horizon"].astype(str)) != {"T-3"}:
        raise RuntimeError("24-72h rows must use T-3 checkpoint hold")
    return frame.reset_index(drop=True)


def event_balanced_weights(frame: pd.DataFrame) -> np.ndarray:
    counts = frame.groupby("ticket_event_id")["ticket_event_id"].transform("count").astype(float)
    weights = 1.0 / counts.to_numpy()
    return weights / float(np.mean(weights))


def available_features(frame: pd.DataFrame) -> list[str]:
    columns = [column for column in BASE_FEATURES if column in frame.columns]
    if "anchor_p50" not in columns or "hours_to_kickoff" not in columns:
        raise RuntimeError("required long72 features missing")
    return columns


def _linear_pipeline(model: Any, columns: list[str]) -> Pipeline:
    prep = ColumnTransformer(
        [(
            "numeric",
            Pipeline([
                ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                ("scale", StandardScaler()),
            ]),
            columns,
        )],
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
    columns = available_features(train)
    y = train["target_live_delta_occupancy"].astype(float).to_numpy()
    weights = event_balanced_weights(train)

    if spec.family == "ridge":
        model = _linear_pipeline(Ridge(alpha=float(spec.alpha)), columns)
    elif spec.family == "huber":
        model = _linear_pipeline(
            HuberRegressor(epsilon=1.35, alpha=float(spec.alpha), max_iter=2000),
            columns,
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

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always", ConvergenceWarning)
        model.fit(train[columns], y, model__sample_weight=weights)
    return np.asarray(model.predict(test[columns]), dtype=float)


def train_fold_bias(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    y = train["target_live_delta_occupancy"].astype(float).to_numpy()
    bias = float(np.average(y, weights=event_balanced_weights(train)))
    return np.full(len(test), bias, dtype=float)


def inventory_linear_delta(test: pd.DataFrame) -> np.ndarray:
    capacity = test["stadium_capacity"].astype(float).to_numpy()
    available = test["available_total"].astype(float).to_numpy()
    hours = test["hours_to_kickoff"].astype(float).to_numpy()
    velocity_6h = pd.to_numeric(test["velocity_6h"], errors="coerce").to_numpy(dtype=float)
    velocity_24h = pd.to_numeric(test["velocity_24h"], errors="coerce").to_numpy(dtype=float)
    velocity_previous = pd.to_numeric(
        test["velocity_since_previous"], errors="coerce"
    ).to_numpy(dtype=float)
    velocity = np.where(
        np.isfinite(velocity_6h), velocity_6h,
        np.where(np.isfinite(velocity_24h), velocity_24h, velocity_previous),
    )
    velocity = np.where(np.isfinite(velocity), velocity, 0.0)
    projected_available = np.clip(
        available - velocity * np.maximum(hours, 0.0), 0.0, capacity
    )
    projected_occupancy = 1.0 - projected_available / capacity
    return projected_occupancy - test["anchor_expected_occupancy"].astype(float).to_numpy()


def governed_forecast(
    frame: pd.DataFrame,
    raw_delta_occupancy: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    delta = np.clip(
        np.asarray(raw_delta_occupancy, dtype=float),
        -MAX_LIVE_CORRECTION_OCCUPANCY,
        MAX_LIVE_CORRECTION_OCCUPANCY,
    )
    capacity = frame["stadium_capacity"].astype(float).to_numpy()
    anchor = frame["anchor_p50"].astype(float).to_numpy()
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
            "ticket_event_id", "club_slug", "home_team", "away_team",
            "kickoff_at", "as_of_at", "hours_to_kickoff", "actual_attendance",
            "stadium_capacity", "anchor_p50",
        ]].copy()
        out["candidate_id"] = spec.id
        out["raw_predicted_delta_occupancy"] = raw_delta
        out["governed_delta_occupancy"] = governed_delta
        out["forecast_p50"] = forecast
        out["absolute_error"] = np.abs(
            out["actual_attendance"].astype(float) - out["forecast_p50"].astype(float)
        )
        out["anchor_absolute_error"] = np.abs(
            out["actual_attendance"].astype(float) - out["anchor_p50"].astype(float)
        )
        out["signed_error"] = (
            out["forecast_p50"].astype(float) - out["actual_attendance"].astype(float)
        )
        out["revision_seats"] = (
            out["forecast_p50"].astype(float) - out["anchor_p50"].astype(float)
        )
        parts.append(out)
    return pd.concat(parts, ignore_index=True).sort_values(
        ["ticket_event_id", "as_of_at"]
    ).reset_index(drop=True)


def _band(frame: pd.DataFrame, lower: float, upper: float) -> pd.DataFrame:
    return frame[
        (frame["hours_to_kickoff"].astype(float) > lower)
        & (frame["hours_to_kickoff"].astype(float) <= upper)
    ].copy()


def band_score(predictions: pd.DataFrame, lower: float, upper: float) -> dict[str, Any]:
    rows = _band(predictions, lower, upper)
    if rows.empty:
        raise RuntimeError(f"empty score band {lower}-{upper}h")
    per_event = (
        rows.groupby("ticket_event_id", sort=True)
        .agg(
            candidate_mae=("absolute_error", "mean"),
            anchor_mae=("anchor_absolute_error", "mean"),
            bias=("signed_error", "mean"),
            mean_abs_revision=("revision_seats", lambda x: float(np.mean(np.abs(x)))),
            rows=("ticket_event_id", "size"),
        )
        .reset_index()
    )
    degradation = per_event["candidate_mae"] - per_event["anchor_mae"]
    improvement = -degradation
    candidate_mae = float(per_event["candidate_mae"].mean())
    anchor_mae = float(per_event["anchor_mae"].mean())
    return {
        "lower_exclusive_hours": lower,
        "upper_inclusive_hours": upper,
        "event_count": int(rows["ticket_event_id"].nunique()),
        "row_count": int(len(rows)),
        "event_balanced_mae": candidate_mae,
        "anchor_event_balanced_mae": anchor_mae,
        "mae_improvement": anchor_mae - candidate_mae,
        "relative_mae_improvement": ((anchor_mae - candidate_mae) / anchor_mae if anchor_mae > 0 else 0.0),
        "event_improvement_rate": float(np.mean(improvement > 0.0)),
        "worst_event_degradation": float(max(0.0, degradation.max())),
        "best_event_improvement": float(max(0.0, improvement.max())),
        "event_balanced_bias": float(per_event["bias"].mean()),
        "event_balanced_mean_abs_revision_seats": float(per_event["mean_abs_revision"].mean()),
        "row_median_absolute_error": float(rows["absolute_error"].median()),
        "row_p90_absolute_error": float(rows["absolute_error"].quantile(0.90)),
    }


def subgroup_score(predictions: pd.DataFrame, event_ids: frozenset[int]) -> dict[str, Any]:
    rows = predictions[predictions["ticket_event_id"].astype(int).isin(event_ids)].copy()
    if rows.empty:
        return {"event_count": 0, "row_count": 0}
    per_event = rows.groupby("ticket_event_id").agg(
        candidate_mae=("absolute_error", "mean"),
        anchor_mae=("anchor_absolute_error", "mean"),
    )
    candidate = float(per_event["candidate_mae"].mean())
    anchor = float(per_event["anchor_mae"].mean())
    return {
        "event_count": int(len(per_event)),
        "row_count": int(len(rows)),
        "event_balanced_mae": candidate,
        "anchor_event_balanced_mae": anchor,
        "mae_improvement": anchor - candidate,
    }


def candidate_scorecard(predictions: pd.DataFrame) -> dict[str, Any]:
    overall = band_score(predictions, 24.0, 72.0)
    band_24_48 = band_score(predictions, 24.0, 48.0)
    band_48_72 = band_score(predictions, 48.0, 72.0)
    return {
        "overall_24_72h": overall,
        "band_24_48h": band_24_48,
        "band_48_72h": band_48_72,
        "original_stage1_exposed_subset": subgroup_score(predictions, ORIGINAL_STAGE1_EVENT_IDS),
        "later_exposed_subset": subgroup_score(predictions, LATER_EXPOSED_EVENT_IDS),
    }


def is_selector_eligible(row: dict[str, Any]) -> bool:
    if row["candidate_id"] == "anchor-zero-correction":
        return False
    score = row["scorecard"]
    return (
        score["overall_24_72h"]["mae_improvement"] > 0.0
        and score["band_24_48h"]["mae_improvement"] > 0.0
        and score["band_48_72h"]["mae_improvement"] > 0.0
    )


def choose_research_lead(scorecards: list[dict[str, Any]]) -> str:
    eligible = [row for row in scorecards if is_selector_eligible(row)]
    if not eligible:
        return "anchor-zero-correction"
    return min(
        eligible,
        key=lambda row: (
            row["scorecard"]["overall_24_72h"]["event_balanced_mae"],
            row["scorecard"]["band_48_72h"]["event_balanced_mae"],
            row["scorecard"]["overall_24_72h"]["worst_event_degradation"],
            row["candidate_id"],
        ),
    )["candidate_id"]


def run_tournament(frame: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    all_predictions: list[pd.DataFrame] = []
    scorecards: list[dict[str, Any]] = []
    for spec in CANDIDATES:
        predictions = loeo_predictions(frame, spec)
        score = candidate_scorecard(predictions)
        all_predictions.append(predictions)
        scorecards.append({
            "candidate_id": spec.id,
            "spec": asdict(spec),
            "selector_eligible": False,
            "scorecard": score,
        })
    for row in scorecards:
        row["selector_eligible"] = is_selector_eligible(row)
    lead = choose_research_lead(scorecards)
    return {
        "experiment": EXPERIMENT,
        "stage": STAGE,
        "status": "COMPLETED_RESEARCH_TOURNAMENT",
        "production_change": False,
        "promotion_allowed": False,
        "independent_evaluation_unit": "event",
        "validation": "LOEO_ALL_EARLY_ROWS_HELD_OUT_BY_EVENT",
        "training_scope": "24<hours_to_kickoff<=72 only",
        "target": "target_live_delta_occupancy",
        "event_balanced_training_weights": True,
        "max_live_correction_occupancy": MAX_LIVE_CORRECTION_OCCUPANCY,
        "full_frozen_dataset_sha256": EXPECTED_FULL_DATASET_SHA256,
        "event_count": int(frame["ticket_event_id"].nunique()),
        "row_count": int(len(frame)),
        "candidate_count": len(scorecards),
        "candidates": scorecards,
        "research_lead_candidate_id": lead,
        "selector": {
            "requirements": [
                "positive event-balanced MAE improvement on 24-72h overall",
                "positive event-balanced MAE improvement on 24-48h",
                "positive event-balanced MAE improvement on 48-72h",
            ],
            "ranking": [
                "lowest overall 24-72h event-balanced MAE",
                "lowest 48-72h event-balanced MAE",
                "lowest overall worst-event degradation",
                "candidate id",
            ],
            "no_unseen_holdout_claim": True,
        },
        "limitations": [
            "All 14 historical event outcomes are exposed research evidence.",
            "The 24-72h training set has 13 independent events and the 48-72h band has 10.",
            "This experiment does not revalidate or replace the frozen final-24h Ridge/P2 package.",
            "Historical/LOEO success is not production-promotion evidence.",
        ],
        "runtime": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
    }, pd.concat(all_predictions, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-predictions-csv", type=Path, required=True)
    args = parser.parse_args()

    full = load_frozen_long72(args.input_csv)
    frame = early_frame(full)
    result, predictions = run_tournament(frame)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    predictions.to_csv(args.output_predictions_csv, index=False)
    print(json.dumps({
        "experiment": result["experiment"],
        "event_count": result["event_count"],
        "row_count": result["row_count"],
        "research_lead_candidate_id": result["research_lead_candidate_id"],
        "candidates": [
            {
                "candidate_id": row["candidate_id"],
                "eligible": row["selector_eligible"],
                "overall_mae": row["scorecard"]["overall_24_72h"]["event_balanced_mae"],
                "overall_improvement": row["scorecard"]["overall_24_72h"]["mae_improvement"],
                "improvement_24_48h": row["scorecard"]["band_24_48h"]["mae_improvement"],
                "improvement_48_72h": row["scorecard"]["band_48_72h"]["mae_improvement"],
                "worst_event_degradation": row["scorecard"]["overall_24_72h"]["worst_event_degradation"],
            }
            for row in result["candidates"]
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
