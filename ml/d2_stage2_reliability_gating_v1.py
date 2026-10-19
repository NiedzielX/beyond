#!/usr/bin/env python3
"""d2 Stage 2: reliability/tail-risk governance around frozen Stage-1 Ridge.

Stage 2 does not retune the Stage-1 expert. It reconstructs the exact
out-of-fold `ridge-a10` predictions on the frozen 9-event / 30-row development
lineage and applies a small, predeclared set of causal reliability policies.

The reserved Lech-Korona event 5 is not part of this input and must not be used
for policy selection.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.d2_stage1_model_tournament_v1 import (
    CandidateSpec,
    candidate_scorecard,
    load_stage0_frame,
    loeo_predictions,
)

EXPERIMENT = "d2-stage2-reliability-gating-v1"
STAGE = "d2-stage2-reliability-tail-risk-loeo"
STAGE1_EXPERT_ID = "ridge-a10"
EXPECTED_EVENT_COUNT = 9
EXPECTED_ROW_COUNT = 30
RESERVED_HOLDOUT_EVENT_ID = 5

# Canonical Stage-1 evidence. Tolerances are deliberately tight enough to
# detect lineage/model drift while allowing text/CSV float round trips.
EXPECTED_FROZEN_LATEST_MAE = 4128.01
EXPECTED_RIDGE_LATEST_MAE = 3320.39
EXPECTED_RIDGE_WINDOW_MAE = 3619.19
EXPECTED_RIDGE_WORST_DEGRADATION = 4326.90
CANONICAL_METRIC_ATOL = 0.10

# Stage-2 advancement gates, predeclared before policy evidence is scored.
MIN_RETAINED_LATEST_UPLIFT = 0.50
MIN_RETAINED_WINDOW_UPLIFT = 0.50
MIN_WORST_DEGRADATION_REDUCTION = 0.25


@dataclass(frozen=True)
class PolicySpec:
    id: str
    description: str


POLICIES = (
    PolicySpec("P0-frozen-v2", "No live revision; reliability=0."),
    PolicySpec("P1-raw-ridge", "Frozen Stage-1 Ridge; reliability=1."),
    PolicySpec(
        "P2-observation-maturity",
        "Shrink early/immature trajectories using only observation index and time-to-kickoff.",
    ),
    PolicySpec(
        "P3-correction-magnitude",
        "Shrink larger proposed Ridge corrections with fixed occupancy thresholds.",
    ),
    PolicySpec(
        "P4-data-quality",
        "Shrink when release/coverage/gap/quality diagnostics make inventory interpretation unstable.",
    ),
    PolicySpec(
        "P5-combined-reliability",
        "Conservative minimum of maturity, correction-magnitude and data-quality reliability.",
    ),
)


def _numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> np.ndarray:
    if column not in frame.columns:
        return np.full(len(frame), float(default), dtype=float)
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    return np.where(np.isfinite(values), values, float(default))


def add_causal_reliability_state(frame: pd.DataFrame) -> pd.DataFrame:
    """Add state available at each exact as-of without outcome information."""
    out = frame.copy().sort_values(["ticket_event_id", "as_of_at"]).reset_index(drop=True)
    out["stage2_observation_index"] = (
        out.groupby("ticket_event_id", sort=False).cumcount() + 1
    ).astype(int)
    first_as_of = out.groupby("ticket_event_id", sort=False)["as_of_at"].transform("min")
    out["stage2_observation_span_hours"] = (
        (out["as_of_at"] - first_as_of).dt.total_seconds() / 3600.0
    ).astype(float)
    return out


def maturity_reliability(frame: pd.DataFrame) -> np.ndarray:
    index = _numeric(frame, "stage2_observation_index", default=1.0)
    hours = _numeric(frame, "hours_to_kickoff", default=24.0)

    observation_weight = np.where(index <= 1.0, 0.25, np.where(index <= 2.0, 0.60, 1.0))
    time_weight = np.where(hours > 18.0, 0.75, np.where(hours > 12.0, 0.90, 1.0))
    return np.minimum(observation_weight, time_weight).astype(float)


def magnitude_reliability(ridge_delta_occupancy: np.ndarray) -> np.ndarray:
    magnitude = np.abs(np.asarray(ridge_delta_occupancy, dtype=float))
    return np.where(
        magnitude <= 0.025,
        1.00,
        np.where(magnitude <= 0.050, 0.80, np.where(magnitude <= 0.075, 0.55, 0.35)),
    ).astype(float)


def quality_reliability(frame: pd.DataFrame) -> np.ndarray:
    signal_ready = _numeric(frame, "signal_ready", default=1.0)
    feature_good = _numeric(frame, "feature_quality_good", default=1.0)
    data_gap = _numeric(frame, "data_gap_detected", default=0.0)
    unexplained_increase = _numeric(frame, "unexplained_inventory_increase_flag", default=0.0)
    release = _numeric(frame, "release_activity_flag", default=0.0)
    coverage = _numeric(frame, "sector_coverage_change_flag", default=0.0)
    max_gap = _numeric(frame, "max_visible_gap_hours", default=0.0)

    weight = np.ones(len(frame), dtype=float)
    hard_warning = (
        (signal_ready < 0.5)
        | (feature_good < 0.5)
        | (data_gap > 0.5)
        | (unexplained_increase > 0.5)
    )
    soft_warning = (release > 0.5) | (coverage > 0.5) | (max_gap > 12.0)
    weight[soft_warning] = np.minimum(weight[soft_warning], 0.50)
    weight[hard_warning] = np.minimum(weight[hard_warning], 0.25)
    return weight


def policy_reliability(
    policy_id: str,
    frame: pd.DataFrame,
    ridge_delta_occupancy: np.ndarray,
) -> np.ndarray:
    maturity = maturity_reliability(frame)
    magnitude = magnitude_reliability(ridge_delta_occupancy)
    quality = quality_reliability(frame)

    if policy_id == "P0-frozen-v2":
        weight = np.zeros(len(frame), dtype=float)
    elif policy_id == "P1-raw-ridge":
        weight = np.ones(len(frame), dtype=float)
    elif policy_id == "P2-observation-maturity":
        weight = maturity
    elif policy_id == "P3-correction-magnitude":
        weight = magnitude
    elif policy_id == "P4-data-quality":
        weight = quality
    elif policy_id == "P5-combined-reliability":
        weight = np.minimum(np.minimum(maturity, magnitude), quality)
    else:
        raise ValueError(f"unknown Stage-2 policy {policy_id}")
    return np.clip(weight, 0.0, 1.0)


def raw_ridge_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    spec = CandidateSpec(STAGE1_EXPERT_ID, "ridge")
    predictions = loeo_predictions(frame, spec).copy()
    predictions = predictions.rename(
        columns={
            "raw_predicted_delta_occupancy": "ridge_raw_predicted_delta_occupancy",
            "governed_delta_occupancy": "ridge_governed_delta_occupancy",
            "forecast_p50": "ridge_forecast_p50",
            "absolute_error": "ridge_absolute_error",
        }
    )
    return predictions


def attach_stage0_features(frame: pd.DataFrame, ridge: pd.DataFrame) -> pd.DataFrame:
    keys = ["ticket_event_id", "as_of_at"]
    feature_frame = frame.copy()
    keep = [column for column in feature_frame.columns if column not in {
        "actual_attendance", "stadium_capacity", "frozen_v2_p50"
    }]
    merged = ridge.merge(feature_frame[keep], on=keys, how="left", validate="one_to_one")
    if len(merged) != EXPECTED_ROW_COUNT:
        raise RuntimeError("Stage-2 feature join changed row count")
    if merged["ticket_event_id"].nunique() != EXPECTED_EVENT_COUNT:
        raise RuntimeError("Stage-2 feature join changed event count")
    if RESERVED_HOLDOUT_EVENT_ID in set(merged["ticket_event_id"].astype(int)):
        raise RuntimeError("reserved event 5 leaked into Stage-2 development")
    return add_causal_reliability_state(merged)


def policy_predictions(
    base: pd.DataFrame,
    policy: PolicySpec,
) -> pd.DataFrame:
    out = base.copy()
    ridge_delta = out["ridge_governed_delta_occupancy"].astype(float).to_numpy()
    reliability = policy_reliability(policy.id, out, ridge_delta)
    capacity = out["stadium_capacity"].astype(float).to_numpy()
    anchor = out["frozen_v2_p50"].astype(float).to_numpy()
    applied_delta = reliability * ridge_delta
    forecast = np.clip(anchor + applied_delta * capacity, 0.0, capacity)

    result = out[[
        "ticket_event_id",
        "as_of_at",
        "actual_attendance",
        "stadium_capacity",
        "frozen_v2_p50",
        "anchor_absolute_error",
        "stage2_observation_index",
        "stage2_observation_span_hours",
    ]].copy()
    result["policy_id"] = policy.id
    result["ridge_governed_delta_occupancy"] = ridge_delta
    result["reliability"] = reliability
    result["applied_delta_occupancy"] = applied_delta
    result["forecast_p50"] = forecast
    result["absolute_error"] = np.abs(
        result["actual_attendance"].astype(float) - result["forecast_p50"].astype(float)
    )
    result["maturity_reliability"] = maturity_reliability(out)
    result["magnitude_reliability"] = magnitude_reliability(ridge_delta)
    result["quality_reliability"] = quality_reliability(out)
    return result


def stage2_scorecard(predictions: pd.DataFrame) -> dict[str, Any]:
    # Reuse the exact Stage-1 MAE/tail scorecard contract.
    score = candidate_scorecard(predictions)
    latest = (
        predictions.sort_values("as_of_at")
        .groupby("ticket_event_id", sort=True)
        .tail(1)
        .copy()
    )
    degradation = (
        latest["absolute_error"].astype(float)
        - latest["anchor_absolute_error"].astype(float)
    ).to_numpy(dtype=float)
    harmful = np.maximum(degradation, 0.0)
    score["p90_latest_event_degradation"] = float(np.quantile(harmful, 0.90))
    score["mean_reliability"] = float(predictions["reliability"].astype(float).mean())
    score["full_reliability_share"] = float(np.mean(predictions["reliability"].astype(float) >= 0.999999))
    score["zero_reliability_share"] = float(np.mean(predictions["reliability"].astype(float) <= 1e-12))
    return score


def _assert_close(actual: float, expected: float, label: str) -> None:
    if not np.isclose(float(actual), float(expected), rtol=0.0, atol=CANONICAL_METRIC_ATOL):
        raise RuntimeError(f"{label} drift actual={actual} expected={expected}")


def select_stage2_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["policy_id"]: row for row in rows}
    frozen = by_id["P0-frozen-v2"]["scorecard"]
    raw = by_id["P1-raw-ridge"]["scorecard"]

    raw_latest_uplift = float(raw["latest_mae_improvement"])
    raw_window_uplift = float(raw["window_mae_improvement"])
    raw_worst = float(raw["worst_latest_event_degradation"])

    eligible: list[dict[str, Any]] = []
    for row in rows:
        if row["policy_id"] in {"P0-frozen-v2", "P1-raw-ridge"}:
            continue
        score = row["scorecard"]
        retained_latest = (
            float(score["latest_mae_improvement"]) / raw_latest_uplift
            if raw_latest_uplift > 0 else -np.inf
        )
        retained_window = (
            float(score["window_mae_improvement"]) / raw_window_uplift
            if raw_window_uplift > 0 else -np.inf
        )
        tail_reduction = (
            (raw_worst - float(score["worst_latest_event_degradation"])) / raw_worst
            if raw_worst > 0 else 0.0
        )
        row["retained_latest_uplift_share"] = float(retained_latest)
        row["retained_window_uplift_share"] = float(retained_window)
        row["worst_degradation_reduction_share"] = float(tail_reduction)
        if (
            float(score["latest_row_mae"]) < float(frozen["latest_row_mae"])
            and float(score["event_balanced_window_mae"]) < float(frozen["event_balanced_window_mae"])
            and retained_latest >= MIN_RETAINED_LATEST_UPLIFT
            and retained_window >= MIN_RETAINED_WINDOW_UPLIFT
            and tail_reduction >= MIN_WORST_DEGRADATION_REDUCTION
        ):
            eligible.append(row)

    if not eligible:
        return {
            "decision": "RAW_RIDGE_RETAINED_NO_STAGE2_POLICY_PASSED",
            "selected_policy_id": "P1-raw-ridge",
            "stage2_policy_advanced": False,
            "eligible_policy_ids": [],
        }

    winner = min(
        eligible,
        key=lambda row: (
            row["scorecard"]["latest_row_mae"],
            row["scorecard"]["event_balanced_window_mae"],
            row["scorecard"]["worst_latest_event_degradation"],
            row["policy_id"],
        ),
    )
    return {
        "decision": "STAGE2_RELIABILITY_POLICY_SELECTED",
        "selected_policy_id": winner["policy_id"],
        "stage2_policy_advanced": True,
        "eligible_policy_ids": [row["policy_id"] for row in eligible],
    }


def run_stage2(frame: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    if RESERVED_HOLDOUT_EVENT_ID in set(frame["ticket_event_id"].astype(int)):
        raise RuntimeError("reserved event 5 must not be present in Stage-2 input")

    ridge = raw_ridge_predictions(frame)
    base = attach_stage0_features(frame, ridge)

    policy_rows: list[dict[str, Any]] = []
    prediction_parts: list[pd.DataFrame] = []
    for policy in POLICIES:
        predictions = policy_predictions(base, policy)
        score = stage2_scorecard(predictions)
        policy_rows.append({
            "policy_id": policy.id,
            "description": policy.description,
            "scorecard": score,
        })
        prediction_parts.append(predictions)

    by_id = {row["policy_id"]: row for row in policy_rows}
    frozen_score = by_id["P0-frozen-v2"]["scorecard"]
    ridge_score = by_id["P1-raw-ridge"]["scorecard"]
    _assert_close(frozen_score["latest_row_mae"], EXPECTED_FROZEN_LATEST_MAE, "Frozen-v2 latest MAE")
    _assert_close(ridge_score["latest_row_mae"], EXPECTED_RIDGE_LATEST_MAE, "Ridge latest MAE")
    _assert_close(ridge_score["event_balanced_window_mae"], EXPECTED_RIDGE_WINDOW_MAE, "Ridge window MAE")
    _assert_close(
        ridge_score["worst_latest_event_degradation"],
        EXPECTED_RIDGE_WORST_DEGRADATION,
        "Ridge worst latest-event degradation",
    )

    selection = select_stage2_policy(policy_rows)
    output = {
        "experiment": EXPERIMENT,
        "stage": STAGE,
        "status": "COMPLETED_RELIABILITY_TOURNAMENT",
        "production_change": False,
        "promotion_allowed": False,
        "frozen_c1_v8_changed": False,
        "stage1_expert_id": STAGE1_EXPERT_ID,
        "stage1_expert_retuned": False,
        "development_event_ids": sorted(int(v) for v in frame["ticket_event_id"].unique()),
        "event_count": int(frame["ticket_event_id"].nunique()),
        "row_count": int(len(frame)),
        "validation": "LOEO_STAGE1_RIDGE_THEN_CAUSAL_POLICY",
        "reserved_holdout_event_id": RESERVED_HOLDOUT_EVENT_ID,
        "reserved_holdout_used_for_selection": False,
        "advancement_gates": {
            "min_retained_latest_uplift": MIN_RETAINED_LATEST_UPLIFT,
            "min_retained_window_uplift": MIN_RETAINED_WINDOW_UPLIFT,
            "min_worst_degradation_reduction": MIN_WORST_DEGRADATION_REDUCTION,
        },
        "policies": policy_rows,
        **selection,
        "decision_boundary": (
            "Stage 2 is development-only. Event 5 remains reserved until this policy decision "
            "is persisted/frozen. Production live_adjustment remains 0."
        ),
    }
    return output, pd.concat(prediction_parts, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-predictions-csv", type=Path, required=True)
    args = parser.parse_args()

    frame = load_stage0_frame(args.input_csv)
    result, predictions = run_stage2(frame)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    predictions.to_csv(args.output_predictions_csv, index=False)
    print(json.dumps({
        "decision": result["decision"],
        "selected_policy_id": result["selected_policy_id"],
        "stage2_policy_advanced": result["stage2_policy_advanced"],
        "policies": [
            {
                "policy_id": row["policy_id"],
                "latest_mae": row["scorecard"]["latest_row_mae"],
                "window_mae": row["scorecard"]["event_balanced_window_mae"],
                "latest_uplift": row["scorecard"]["latest_mae_improvement"],
                "window_uplift": row["scorecard"]["window_mae_improvement"],
                "worst_degradation": row["scorecard"]["worst_latest_event_degradation"],
                "mean_reliability": row["scorecard"]["mean_reliability"],
                "retained_latest_uplift_share": row.get("retained_latest_uplift_share"),
                "worst_degradation_reduction_share": row.get("worst_degradation_reduction_share"),
            }
            for row in result["policies"]
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
