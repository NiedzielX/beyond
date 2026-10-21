#!/usr/bin/env python3
"""d2 long72 Stage 2: reliability/tail governance around frozen Stage-1 inventory lead.

Stage 2 does not change the Stage-1 expert. It consumes the exact frozen
Stage-1 out-of-fold predictions and applies a small predeclared set of causal
reliability weights using only information available at each row's as-of time.

All evidence is historical/exposed development evidence. No production write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.d2_long72_stage1_model_tournament_v1 import (
    LATER_EXPOSED_EVENT_IDS,
    ORIGINAL_STAGE1_EVENT_IDS,
    band_score,
    subgroup_score,
)

EXPERIMENT = "d2-long72-stage2-reliability-gating-v1"
STAGE1_EXPERT_ID = "inventory-linear-extrapolation"
EXPECTED_DATASET_SHA256 = "2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c"
EXPECTED_STAGE1_PREDICTIONS_SHA256 = "33de331d2c3bf1e385f513c7fa7e28aa8b454a4d49cfe00d48163e6c083a6df5"
EXPECTED_EVENT_COUNT = 13
EXPECTED_ROW_COUNT = 80

# Canonical Stage-1 inventory evidence; tight drift checks before Stage-2.
EXPECTED_RAW_OVERALL_MAE = 3254.6809517243155
EXPECTED_RAW_OVERALL_UPLIFT = 452.4572219222955
EXPECTED_RAW_24_48_UPLIFT = 675.3308228020314
EXPECTED_RAW_48_72_UPLIFT = 675.6771220422229
EXPECTED_RAW_WORST_DEGRADATION = 3100.5999999999985
EXPECTED_RAW_48_72_WORST_DEGRADATION = 3741.7941628246845
EXPECTED_RAW_ABS_BIAS = 1458.934971360056
METRIC_ATOL = 1e-6

# Inherited Stage-2 philosophy: retain at least half the raw uplift and reduce
# tail harm materially. Additional subgroup/bias gates address the explicit
# Stage-1 weaknesses discovered before this policy experiment.
MIN_RETAINED_UPLIFT_SHARE = 0.50
MIN_WORST_DEGRADATION_REDUCTION = 0.25
MIN_ABS_BIAS_REDUCTION = 0.25


@dataclass(frozen=True)
class PolicySpec:
    id: str
    description: str


POLICIES = (
    PolicySpec("P0-anchor", "No early-live correction; reliability=0."),
    PolicySpec("P1-raw-inventory", "Frozen Stage-1 inventory correction; reliability=1."),
    PolicySpec(
        "P2-observation-maturity",
        "Scale the existing final24 maturity shape to the 24-72h window using only observation index and time-to-kickoff.",
    ),
    PolicySpec(
        "P3-correction-magnitude",
        "Shrink larger proposed occupancy corrections with fixed Stage-2 magnitude bands.",
    ),
    PolicySpec(
        "P4-data-quality",
        "Shrink when PIT inventory quality/release/coverage/gap diagnostics are unstable.",
    ),
    PolicySpec(
        "P5-combined-reliability",
        "Conservative minimum of maturity, magnitude and data-quality reliability.",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> np.ndarray:
    if column not in frame.columns:
        return np.full(len(frame), float(default), dtype=float)
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    return np.where(np.isfinite(values), values, float(default))


def load_inputs(dataset_path: Path, predictions_path: Path) -> pd.DataFrame:
    if sha256_file(dataset_path) != EXPECTED_DATASET_SHA256:
        raise RuntimeError("frozen long72 dataset hash drift")
    if sha256_file(predictions_path) != EXPECTED_STAGE1_PREDICTIONS_SHA256:
        raise RuntimeError("Stage-1 predictions hash drift")

    full = pd.read_csv(dataset_path)
    full["as_of_at"] = pd.to_datetime(full["as_of_at"], utc=True)
    early = full[
        (full["hours_to_kickoff"].astype(float) > 24.0)
        & (full["hours_to_kickoff"].astype(float) <= 72.0)
    ].copy()

    predictions = pd.read_csv(predictions_path)
    predictions = predictions[
        predictions["candidate_id"].astype(str) == STAGE1_EXPERT_ID
    ].copy()
    predictions["as_of_at"] = pd.to_datetime(predictions["as_of_at"], utc=True)
    if len(predictions) != EXPECTED_ROW_COUNT:
        raise RuntimeError(f"expected {EXPECTED_ROW_COUNT} raw inventory rows")
    if predictions["ticket_event_id"].nunique() != EXPECTED_EVENT_COUNT:
        raise RuntimeError("raw inventory event count drift")

    keep = [
        column for column in early.columns
        if column not in {
            "actual_attendance",
            "stadium_capacity",
            "anchor_p50",
            "club_slug",
            "home_team",
            "away_team",
            "kickoff_at",
            "hours_to_kickoff",
        }
    ]
    merged = predictions.merge(
        early[["ticket_event_id", "as_of_at", *keep]],
        on=["ticket_event_id", "as_of_at"],
        how="left",
        validate="one_to_one",
    )
    if len(merged) != EXPECTED_ROW_COUNT:
        raise RuntimeError("Stage-2 feature join changed row count")
    if merged[keep].isna().all(axis=1).any():
        raise RuntimeError("Stage-2 feature join produced unmatched rows")
    return add_causal_reliability_state(merged)


def add_causal_reliability_state(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().sort_values(["ticket_event_id", "as_of_at"]).reset_index(drop=True)
    out["stage2_observation_index"] = (
        out.groupby("ticket_event_id", sort=False).cumcount() + 1
    ).astype(int)
    first = out.groupby("ticket_event_id", sort=False)["as_of_at"].transform("min")
    out["stage2_observation_span_hours"] = (
        (out["as_of_at"] - first).dt.total_seconds() / 3600.0
    ).astype(float)
    return out


def maturity_reliability(frame: pd.DataFrame) -> np.ndarray:
    """Scaled version of the frozen final24 P2 maturity policy.

    Observation weights are unchanged from final24 P2. Time thresholds are
    moved to the analogous halves/quarter of the earlier 24-72h window.
    """
    index = _numeric(frame, "stage2_observation_index", default=1.0)
    hours = _numeric(frame, "hours_to_kickoff", default=72.0)
    observation_weight = np.where(index <= 1.0, 0.25, np.where(index <= 2.0, 0.60, 1.0))
    time_weight = np.where(hours > 60.0, 0.75, np.where(hours > 48.0, 0.90, 1.0))
    return np.minimum(observation_weight, time_weight).astype(float)


def magnitude_reliability(raw_delta_occupancy: np.ndarray) -> np.ndarray:
    magnitude = np.abs(np.asarray(raw_delta_occupancy, dtype=float))
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
    raw_delta_occupancy: np.ndarray,
) -> np.ndarray:
    maturity = maturity_reliability(frame)
    magnitude = magnitude_reliability(raw_delta_occupancy)
    quality = quality_reliability(frame)
    if policy_id == "P0-anchor":
        weight = np.zeros(len(frame), dtype=float)
    elif policy_id == "P1-raw-inventory":
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
        raise ValueError(f"unknown policy {policy_id}")
    return np.clip(weight, 0.0, 1.0)


def policy_predictions(base: pd.DataFrame, policy: PolicySpec) -> pd.DataFrame:
    out = base.copy()
    raw_delta = out["governed_delta_occupancy"].astype(float).to_numpy()
    reliability = policy_reliability(policy.id, out, raw_delta)
    capacity = out["stadium_capacity"].astype(float).to_numpy()
    anchor = out["anchor_p50"].astype(float).to_numpy()
    applied_delta = reliability * raw_delta
    forecast = np.clip(anchor + applied_delta * capacity, 0.0, capacity)

    result = out[[
        "ticket_event_id",
        "club_slug",
        "home_team",
        "away_team",
        "kickoff_at",
        "as_of_at",
        "hours_to_kickoff",
        "actual_attendance",
        "stadium_capacity",
        "anchor_p50",
        "anchor_absolute_error",
        "stage2_observation_index",
        "stage2_observation_span_hours",
    ]].copy()
    result["policy_id"] = policy.id
    result["raw_inventory_delta_occupancy"] = raw_delta
    result["reliability"] = reliability
    result["applied_delta_occupancy"] = applied_delta
    result["forecast_p50"] = forecast
    result["absolute_error"] = np.abs(
        result["actual_attendance"].astype(float) - result["forecast_p50"].astype(float)
    )
    result["signed_error"] = (
        result["forecast_p50"].astype(float) - result["actual_attendance"].astype(float)
    )
    result["revision_seats"] = (
        result["forecast_p50"].astype(float) - result["anchor_p50"].astype(float)
    )
    result["maturity_reliability"] = maturity_reliability(out)
    result["magnitude_reliability"] = magnitude_reliability(raw_delta)
    result["quality_reliability"] = quality_reliability(out)
    return result


def score_policy(predictions: pd.DataFrame) -> dict[str, Any]:
    return {
        "overall_24_72h": band_score(predictions, 24.0, 72.0),
        "band_24_48h": band_score(predictions, 24.0, 48.0),
        "band_48_72h": band_score(predictions, 48.0, 72.0),
        "original_stage1_exposed_subset": subgroup_score(
            predictions, ORIGINAL_STAGE1_EVENT_IDS
        ),
        "later_exposed_subset": subgroup_score(predictions, LATER_EXPOSED_EVENT_IDS),
        "mean_reliability": float(predictions["reliability"].astype(float).mean()),
        "full_reliability_share": float(
            np.mean(predictions["reliability"].astype(float) >= 0.999999)
        ),
    }


def _assert_close(actual: float, expected: float, label: str) -> None:
    if not np.isclose(actual, expected, rtol=0.0, atol=METRIC_ATOL):
        raise RuntimeError(f"{label} drift actual={actual} expected={expected}")


def assert_stage1_lineage(raw_score: dict[str, Any]) -> None:
    overall = raw_score["overall_24_72h"]
    b1 = raw_score["band_24_48h"]
    b2 = raw_score["band_48_72h"]
    _assert_close(overall["event_balanced_mae"], EXPECTED_RAW_OVERALL_MAE, "raw overall MAE")
    _assert_close(overall["mae_improvement"], EXPECTED_RAW_OVERALL_UPLIFT, "raw overall uplift")
    _assert_close(b1["mae_improvement"], EXPECTED_RAW_24_48_UPLIFT, "raw 24-48 uplift")
    _assert_close(b2["mae_improvement"], EXPECTED_RAW_48_72_UPLIFT, "raw 48-72 uplift")
    _assert_close(overall["worst_event_degradation"], EXPECTED_RAW_WORST_DEGRADATION, "raw worst")
    _assert_close(b2["worst_event_degradation"], EXPECTED_RAW_48_72_WORST_DEGRADATION, "raw 48-72 worst")
    _assert_close(abs(overall["event_balanced_bias"]), EXPECTED_RAW_ABS_BIAS, "raw abs bias")


def enrich_policy_row(
    row: dict[str, Any],
    raw_score: dict[str, Any],
) -> dict[str, Any]:
    score = row["scorecard"]
    raw_overall = raw_score["overall_24_72h"]
    raw_b1 = raw_score["band_24_48h"]
    raw_b2 = raw_score["band_48_72h"]
    overall = score["overall_24_72h"]
    b1 = score["band_24_48h"]
    b2 = score["band_48_72h"]

    def retained(value: float, raw_value: float) -> float:
        return float(value / raw_value) if raw_value > 0 else float("-inf")

    row["retained_overall_uplift_share"] = retained(
        overall["mae_improvement"], raw_overall["mae_improvement"]
    )
    row["retained_24_48_uplift_share"] = retained(
        b1["mae_improvement"], raw_b1["mae_improvement"]
    )
    row["retained_48_72_uplift_share"] = retained(
        b2["mae_improvement"], raw_b2["mae_improvement"]
    )
    row["overall_worst_degradation_reduction_share"] = float(
        (raw_overall["worst_event_degradation"] - overall["worst_event_degradation"])
        / raw_overall["worst_event_degradation"]
    )
    row["band_48_72_worst_degradation_reduction_share"] = float(
        (raw_b2["worst_event_degradation"] - b2["worst_event_degradation"])
        / raw_b2["worst_event_degradation"]
    )
    row["absolute_bias_reduction_share"] = float(
        (abs(raw_overall["event_balanced_bias"]) - abs(overall["event_balanced_bias"]))
        / abs(raw_overall["event_balanced_bias"])
    )
    row["selector_eligible"] = bool(
        overall["mae_improvement"] > 0.0
        and b1["mae_improvement"] > 0.0
        and b2["mae_improvement"] > 0.0
        and row["retained_overall_uplift_share"] >= MIN_RETAINED_UPLIFT_SHARE
        and row["retained_24_48_uplift_share"] >= MIN_RETAINED_UPLIFT_SHARE
        and row["retained_48_72_uplift_share"] >= MIN_RETAINED_UPLIFT_SHARE
        and row["overall_worst_degradation_reduction_share"] >= MIN_WORST_DEGRADATION_REDUCTION
        and row["band_48_72_worst_degradation_reduction_share"] >= MIN_WORST_DEGRADATION_REDUCTION
        and row["absolute_bias_reduction_share"] >= MIN_ABS_BIAS_REDUCTION
        and score["original_stage1_exposed_subset"].get("mae_improvement", -np.inf) > 0.0
        and score["later_exposed_subset"].get("mae_improvement", -np.inf) > 0.0
    )
    return row


def select_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [
        row for row in rows
        if row["policy_id"] not in {"P0-anchor", "P1-raw-inventory"}
        and row.get("selector_eligible")
    ]
    if not eligible:
        return {
            "decision": "RAW_INVENTORY_RETAINED_NO_STAGE2_POLICY_PASSED",
            "selected_policy_id": "P1-raw-inventory",
            "stage2_policy_advanced": False,
            "eligible_policy_ids": [],
        }
    winner = min(
        eligible,
        key=lambda row: (
            row["scorecard"]["overall_24_72h"]["event_balanced_mae"],
            row["scorecard"]["band_48_72h"]["event_balanced_mae"],
            row["scorecard"]["overall_24_72h"]["worst_event_degradation"],
            row["policy_id"],
        ),
    )
    return {
        "decision": "STAGE2_RELIABILITY_POLICY_SELECTED",
        "selected_policy_id": winner["policy_id"],
        "stage2_policy_advanced": True,
        "eligible_policy_ids": [row["policy_id"] for row in eligible],
    }


def run_stage2(base: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    policy_rows: list[dict[str, Any]] = []
    parts: list[pd.DataFrame] = []
    for policy in POLICIES:
        predictions = policy_predictions(base, policy)
        score = score_policy(predictions)
        policy_rows.append({
            "policy_id": policy.id,
            "description": policy.description,
            "scorecard": score,
        })
        parts.append(predictions)

    raw_row = next(row for row in policy_rows if row["policy_id"] == "P1-raw-inventory")
    assert_stage1_lineage(raw_row["scorecard"])
    raw_score = raw_row["scorecard"]
    for row in policy_rows:
        if row["policy_id"] in {"P0-anchor", "P1-raw-inventory"}:
            row["selector_eligible"] = False
        else:
            enrich_policy_row(row, raw_score)
    selection = select_policy(policy_rows)

    return {
        "experiment": EXPERIMENT,
        "status": "COMPLETED_STAGE2_RELIABILITY_GATING",
        "production_change": False,
        "promotion_allowed": False,
        "stage1_expert_id": STAGE1_EXPERT_ID,
        "independent_evaluation_unit": "event",
        "evidence_scope": "historical_exposed_24_72h",
        "policy_count": len(policy_rows),
        "policies": policy_rows,
        "selection": selection,
        "advancement_gates": {
            "minimum_retained_uplift_share_each_view": MIN_RETAINED_UPLIFT_SHARE,
            "minimum_worst_degradation_reduction_share": MIN_WORST_DEGRADATION_REDUCTION,
            "minimum_absolute_bias_reduction_share": MIN_ABS_BIAS_REDUCTION,
            "positive_uplift_required_overall_and_both_time_bands": True,
            "positive_uplift_required_in_both_exposed_temporal_subsets": True,
        },
        "limitations": [
            "All Stage-2 events are exposed historical development evidence.",
            "Reliability policy selection is not production-promotion evidence.",
            "The final24 frozen Ridge/P2 package is a separate Track-A contract and is unchanged.",
        ],
    }, pd.concat(parts, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-csv", type=Path, required=True)
    parser.add_argument("--stage1-predictions-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-predictions-csv", type=Path, required=True)
    args = parser.parse_args()

    base = load_inputs(args.dataset_csv, args.stage1_predictions_csv)
    result, predictions = run_stage2(base)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    predictions.to_csv(args.output_predictions_csv, index=False)
    print(json.dumps({
        "selection": result["selection"],
        "policies": [
            {
                "policy_id": row["policy_id"],
                "eligible": row.get("selector_eligible", False),
                "overall_mae": row["scorecard"]["overall_24_72h"]["event_balanced_mae"],
                "overall_uplift": row["scorecard"]["overall_24_72h"]["mae_improvement"],
                "worst_event_degradation": row["scorecard"]["overall_24_72h"]["worst_event_degradation"],
                "bias": row["scorecard"]["overall_24_72h"]["event_balanced_bias"],
                "original_subset_uplift": row["scorecard"]["original_stage1_exposed_subset"].get("mae_improvement"),
                "later_subset_uplift": row["scorecard"]["later_exposed_subset"].get("mae_improvement"),
            }
            for row in result["policies"]
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
