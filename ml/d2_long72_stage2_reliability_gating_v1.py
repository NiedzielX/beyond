#!/usr/bin/env python3
"""d2 Long72 Stage 2 — reliability and tail-risk governance.

This experiment keeps the frozen Stage-1 expert fixed:

    inventory-linear-extrapolation

It consumes the exact frozen long72 dataset and exact Stage-1 OOF predictions,
then applies only a small predeclared set of causal reliability policies.
All evidence is exposed historical R&D evidence. No production activation.
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
STAGE = "d2-long72-stage2-reliability-tail-risk"
STAGE1_EXPERT_ID = "inventory-linear-extrapolation"

EXPECTED_DATASET_SHA256 = (
    "2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c"
)
EXPECTED_STAGE1_PREDICTIONS_SHA256 = (
    "33de331d2c3bf1e385f513c7fa7e28aa8b454a4d49cfe00d48163e6c083a6df5"
)
EXPECTED_EVENT_COUNT = 13
EXPECTED_ROW_COUNT = 80
EXPECTED_48_72_EVENT_COUNT = 10

# Canonical Stage-1 inventory evidence. Stage 2 hard-fails on drift before any
# policy is eligible for selection.
EXPECTED_RAW_OVERALL_MAE = 3254.6809517243155
EXPECTED_RAW_OVERALL_UPLIFT = 452.4572219222955
EXPECTED_RAW_24_48_UPLIFT = 675.3308228020314
EXPECTED_RAW_48_72_UPLIFT = 675.6771220422229
EXPECTED_RAW_WORST_DEGRADATION = 3100.5999999999985
EXPECTED_RAW_48_72_WORST_DEGRADATION = 3741.7941628246845
EXPECTED_RAW_ABS_BIAS = 1458.934971360056
METRIC_ATOL = 1e-6
ROW_REPRO_ATOL = 1e-9

# Fixed Stage-2 advancement gates, declared before policy results are opened.
MIN_RETAINED_UPLIFT_SHARE = 0.50
MIN_WORST_DEGRADATION_REDUCTION = 0.25
MIN_ABS_BIAS_REDUCTION = 0.25

# Only these causal columns may be joined from the frozen dataset. Outcome and
# residual target columns never enter reliability policy logic.
CAUSAL_RELIABILITY_FEATURES = (
    "signal_ready",
    "feature_quality_good",
    "data_gap_detected",
    "unexplained_inventory_increase_flag",
    "release_activity_flag",
    "sector_coverage_change_flag",
    "max_visible_gap_hours",
)

FORBIDDEN_RELIABILITY_FEATURE_NAMES = frozenset(
    {
        "actual_attendance",
        "target_live_delta_attendance",
        "target_live_delta_occupancy",
        "absolute_error",
        "anchor_absolute_error",
        "signed_error",
    }
)


@dataclass(frozen=True)
class PolicySpec:
    id: str
    description: str


POLICIES = (
    PolicySpec("P0-anchor", "No early-live correction; reliability=0."),
    PolicySpec(
        "P1-raw-inventory",
        "Exact frozen Stage-1 inventory correction; reliability=1.",
    ),
    PolicySpec(
        "P2-observation-maturity",
        "Shrink early/immature observations using fixed observation-index and time bands.",
    ),
    PolicySpec(
        "P3-correction-magnitude",
        "Shrink larger proposed occupancy corrections using fixed magnitude bands.",
    ),
    PolicySpec(
        "P4-data-quality",
        "Shrink when causal PIT inventory quality/release/coverage/gap diagnostics are unstable.",
    ),
    PolicySpec(
        "P5-combined-reliability",
        "Conservative minimum of maturity, correction-magnitude and data-quality reliability.",
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


def _assert_close(actual: float, expected: float, label: str) -> None:
    if not np.isclose(float(actual), float(expected), rtol=0.0, atol=METRIC_ATOL):
        raise RuntimeError(f"{label} drift actual={actual} expected={expected}")


def load_inputs(dataset_path: Path, predictions_path: Path) -> pd.DataFrame:
    """Load exact pinned inputs and join only causal reliability features."""
    dataset_sha = sha256_file(dataset_path)
    if dataset_sha != EXPECTED_DATASET_SHA256:
        raise RuntimeError(
            f"frozen long72 dataset hash drift actual={dataset_sha} "
            f"expected={EXPECTED_DATASET_SHA256}"
        )
    predictions_sha = sha256_file(predictions_path)
    if predictions_sha != EXPECTED_STAGE1_PREDICTIONS_SHA256:
        raise RuntimeError(
            f"Stage-1 predictions hash drift actual={predictions_sha} "
            f"expected={EXPECTED_STAGE1_PREDICTIONS_SHA256}"
        )

    full = pd.read_csv(dataset_path)
    full["as_of_at"] = pd.to_datetime(full["as_of_at"], utc=True)
    early = full[
        (pd.to_numeric(full["hours_to_kickoff"], errors="raise") > 24.0)
        & (pd.to_numeric(full["hours_to_kickoff"], errors="raise") <= 72.0)
    ].copy()

    if len(early) != EXPECTED_ROW_COUNT:
        raise RuntimeError(f"expected {EXPECTED_ROW_COUNT} early rows, got {len(early)}")
    if early["ticket_event_id"].nunique() != EXPECTED_EVENT_COUNT:
        raise RuntimeError("long72 early event count drift")
    if early.loc[early["hours_to_kickoff"] > 48.0, "ticket_event_id"].nunique() != EXPECTED_48_72_EVENT_COUNT:
        raise RuntimeError("long72 48-72h event count drift")

    missing_causal = sorted(
        set(CAUSAL_RELIABILITY_FEATURES) - set(early.columns)
    )
    if missing_causal:
        raise RuntimeError(f"frozen dataset missing reliability features: {missing_causal}")
    if FORBIDDEN_RELIABILITY_FEATURE_NAMES.intersection(CAUSAL_RELIABILITY_FEATURES):
        raise RuntimeError("forbidden label leaked into reliability feature contract")

    predictions = pd.read_csv(predictions_path)
    predictions = predictions[
        predictions["candidate_id"].astype(str) == STAGE1_EXPERT_ID
    ].copy()
    predictions["as_of_at"] = pd.to_datetime(predictions["as_of_at"], utc=True)

    if len(predictions) != EXPECTED_ROW_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_ROW_COUNT} Stage-1 inventory rows, got {len(predictions)}"
        )
    if predictions["ticket_event_id"].nunique() != EXPECTED_EVENT_COUNT:
        raise RuntimeError("Stage-1 inventory event count drift")

    keys = ["ticket_event_id", "as_of_at"]
    if predictions.duplicated(keys).any():
        raise RuntimeError("duplicate Stage-1 prediction key")
    if early.duplicated(keys).any():
        raise RuntimeError("duplicate frozen long72 dataset key")

    prediction_keys = set(
        zip(
            predictions["ticket_event_id"].astype(int),
            predictions["as_of_at"].map(pd.Timestamp),
        )
    )
    early_keys = set(
        zip(
            early["ticket_event_id"].astype(int),
            early["as_of_at"].map(pd.Timestamp),
        )
    )
    if prediction_keys != early_keys:
        raise RuntimeError("Stage-1 prediction identities differ from frozen long72 early rows")

    feature_frame = early[
        ["ticket_event_id", "as_of_at", *CAUSAL_RELIABILITY_FEATURES]
    ].copy()
    merged = predictions.merge(
        feature_frame,
        on=keys,
        how="left",
        validate="one_to_one",
    )
    if len(merged) != EXPECTED_ROW_COUNT:
        raise RuntimeError("Stage-2 causal feature join changed row count")
    if merged[list(CAUSAL_RELIABILITY_FEATURES)].isna().all(axis=1).any():
        raise RuntimeError("Stage-2 causal feature join produced an unmatched row")

    return add_causal_reliability_state(merged)


def add_causal_reliability_state(frame: pd.DataFrame) -> pd.DataFrame:
    """Create row state available at the exact as-of timestamp."""
    out = frame.copy().sort_values(
        ["ticket_event_id", "as_of_at"]
    ).reset_index(drop=True)
    out["stage2_observation_index"] = (
        out.groupby("ticket_event_id", sort=False).cumcount() + 1
    ).astype(int)
    first_as_of = out.groupby("ticket_event_id", sort=False)["as_of_at"].transform("min")
    out["stage2_observation_span_hours"] = (
        (out["as_of_at"] - first_as_of).dt.total_seconds() / 3600.0
    ).astype(float)
    return out


def maturity_reliability(frame: pd.DataFrame) -> np.ndarray:
    """Fixed final24-P2 shape scaled to the 24-72h research window."""
    index = _numeric(frame, "stage2_observation_index", default=1.0)
    hours = _numeric(frame, "hours_to_kickoff", default=72.0)

    observation_weight = np.where(
        index <= 1.0,
        0.25,
        np.where(index <= 2.0, 0.60, 1.0),
    )
    time_weight = np.where(
        hours > 60.0,
        0.75,
        np.where(hours > 48.0, 0.90, 1.0),
    )
    return np.minimum(observation_weight, time_weight).astype(float)


def magnitude_reliability(raw_delta_occupancy: np.ndarray) -> np.ndarray:
    magnitude = np.abs(np.asarray(raw_delta_occupancy, dtype=float))
    return np.where(
        magnitude <= 0.025,
        1.00,
        np.where(
            magnitude <= 0.050,
            0.80,
            np.where(magnitude <= 0.075, 0.55, 0.35),
        ),
    ).astype(float)


def quality_reliability(frame: pd.DataFrame) -> np.ndarray:
    signal_ready = _numeric(frame, "signal_ready", default=1.0)
    feature_good = _numeric(frame, "feature_quality_good", default=1.0)
    data_gap = _numeric(frame, "data_gap_detected", default=0.0)
    unexplained_increase = _numeric(
        frame, "unexplained_inventory_increase_flag", default=0.0
    )
    release = _numeric(frame, "release_activity_flag", default=0.0)
    coverage = _numeric(frame, "sector_coverage_change_flag", default=0.0)
    max_gap = _numeric(frame, "max_visible_gap_hours", default=0.0)

    weight = np.ones(len(frame), dtype=float)
    soft_warning = (
        (release > 0.5)
        | (coverage > 0.5)
        | (max_gap > 12.0)
    )
    hard_warning = (
        (signal_ready < 0.5)
        | (feature_good < 0.5)
        | (data_gap > 0.5)
        | (unexplained_increase > 0.5)
    )
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
        raise ValueError(f"unknown Stage-2 policy {policy_id}")
    return np.clip(weight, 0.0, 1.0)


def policy_predictions(base: pd.DataFrame, policy: PolicySpec) -> pd.DataFrame:
    raw_delta = base["governed_delta_occupancy"].astype(float).to_numpy()
    reliability = policy_reliability(policy.id, base, raw_delta)
    capacity = base["stadium_capacity"].astype(float).to_numpy()
    anchor = base["anchor_p50"].astype(float).to_numpy()
    applied_delta = reliability * raw_delta
    forecast = np.clip(anchor + applied_delta * capacity, 0.0, capacity)

    result = base[
        [
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
        ]
    ].copy()
    result["policy_id"] = policy.id
    result["raw_inventory_delta_occupancy"] = raw_delta
    result["reliability"] = reliability
    result["applied_delta_occupancy"] = applied_delta
    result["forecast_p50"] = forecast
    result["absolute_error"] = np.abs(
        result["actual_attendance"].astype(float)
        - result["forecast_p50"].astype(float)
    )
    result["signed_error"] = (
        result["forecast_p50"].astype(float)
        - result["actual_attendance"].astype(float)
    )
    result["revision_seats"] = (
        result["forecast_p50"].astype(float)
        - result["anchor_p50"].astype(float)
    )
    result["maturity_reliability"] = maturity_reliability(base)
    result["magnitude_reliability"] = magnitude_reliability(raw_delta)
    result["quality_reliability"] = quality_reliability(base)
    return result


def score_policy(predictions: pd.DataFrame) -> dict[str, Any]:
    return {
        "overall_24_72h": band_score(predictions, 24.0, 72.0),
        "band_24_48h": band_score(predictions, 24.0, 48.0),
        "band_48_72h": band_score(predictions, 48.0, 72.0),
        "original_stage1_exposed_subset": subgroup_score(
            predictions, ORIGINAL_STAGE1_EVENT_IDS
        ),
        "later_exposed_subset": subgroup_score(
            predictions, LATER_EXPOSED_EVENT_IDS
        ),
        "mean_reliability": float(
            predictions["reliability"].astype(float).mean()
        ),
        "full_reliability_share": float(
            np.mean(
                predictions["reliability"].astype(float) >= 0.999999
            )
        ),
        "zero_reliability_share": float(
            np.mean(
                predictions["reliability"].astype(float) <= 1e-12
            )
        ),
    }


def assert_stage1_lineage(
    raw_predictions: pd.DataFrame,
    raw_score: dict[str, Any],
) -> None:
    """Prove Stage 2 reconstructed the exact frozen Stage-1 expert."""
    if not np.allclose(
        raw_predictions["forecast_p50"].astype(float).to_numpy(),
        raw_predictions["stage1_forecast_p50"].astype(float).to_numpy(),
        rtol=0.0,
        atol=ROW_REPRO_ATOL,
    ):
        max_delta = float(
            np.max(
                np.abs(
                    raw_predictions["forecast_p50"].astype(float).to_numpy()
                    - raw_predictions["stage1_forecast_p50"].astype(float).to_numpy()
                )
            )
        )
        raise RuntimeError(
            f"P1 row-level forecast does not reproduce Stage-1 expert max_delta={max_delta}"
        )

    overall = raw_score["overall_24_72h"]
    b24 = raw_score["band_24_48h"]
    b48 = raw_score["band_48_72h"]
    _assert_close(
        overall["event_balanced_mae"],
        EXPECTED_RAW_OVERALL_MAE,
        "raw overall MAE",
    )
    _assert_close(
        overall["mae_improvement"],
        EXPECTED_RAW_OVERALL_UPLIFT,
        "raw overall uplift",
    )
    _assert_close(
        b24["mae_improvement"],
        EXPECTED_RAW_24_48_UPLIFT,
        "raw 24-48 uplift",
    )
    _assert_close(
        b48["mae_improvement"],
        EXPECTED_RAW_48_72_UPLIFT,
        "raw 48-72 uplift",
    )
    _assert_close(
        overall["worst_event_degradation"],
        EXPECTED_RAW_WORST_DEGRADATION,
        "raw overall worst degradation",
    )
    _assert_close(
        b48["worst_event_degradation"],
        EXPECTED_RAW_48_72_WORST_DEGRADATION,
        "raw 48-72 worst degradation",
    )
    _assert_close(
        abs(overall["event_balanced_bias"]),
        EXPECTED_RAW_ABS_BIAS,
        "raw absolute bias",
    )


def _retained(value: float, raw_value: float) -> float:
    return float(value / raw_value) if raw_value > 0.0 else float("-inf")


def enrich_policy_row(
    row: dict[str, Any],
    raw_score: dict[str, Any],
) -> dict[str, Any]:
    score = row["scorecard"]
    overall = score["overall_24_72h"]
    band24 = score["band_24_48h"]
    band48 = score["band_48_72h"]
    raw_overall = raw_score["overall_24_72h"]
    raw_band24 = raw_score["band_24_48h"]
    raw_band48 = raw_score["band_48_72h"]

    row["retained_overall_uplift_share"] = _retained(
        overall["mae_improvement"], raw_overall["mae_improvement"]
    )
    row["retained_24_48_uplift_share"] = _retained(
        band24["mae_improvement"], raw_band24["mae_improvement"]
    )
    row["retained_48_72_uplift_share"] = _retained(
        band48["mae_improvement"], raw_band48["mae_improvement"]
    )
    row["overall_worst_degradation_reduction_share"] = float(
        (
            raw_overall["worst_event_degradation"]
            - overall["worst_event_degradation"]
        )
        / raw_overall["worst_event_degradation"]
    )
    row["band_48_72_worst_degradation_reduction_share"] = float(
        (
            raw_band48["worst_event_degradation"]
            - band48["worst_event_degradation"]
        )
        / raw_band48["worst_event_degradation"]
    )
    row["absolute_bias_reduction_share"] = float(
        (
            abs(raw_overall["event_balanced_bias"])
            - abs(overall["event_balanced_bias"])
        )
        / abs(raw_overall["event_balanced_bias"])
    )

    original_uplift = score["original_stage1_exposed_subset"].get(
        "mae_improvement", float("-inf")
    )
    later_uplift = score["later_exposed_subset"].get(
        "mae_improvement", float("-inf")
    )

    row["selector_eligible"] = bool(
        overall["mae_improvement"] > 0.0
        and band24["mae_improvement"] > 0.0
        and band48["mae_improvement"] > 0.0
        and row["retained_overall_uplift_share"] >= MIN_RETAINED_UPLIFT_SHARE
        and row["retained_24_48_uplift_share"] >= MIN_RETAINED_UPLIFT_SHARE
        and row["retained_48_72_uplift_share"] >= MIN_RETAINED_UPLIFT_SHARE
        and row["overall_worst_degradation_reduction_share"]
        >= MIN_WORST_DEGRADATION_REDUCTION
        and row["band_48_72_worst_degradation_reduction_share"]
        >= MIN_WORST_DEGRADATION_REDUCTION
        and row["absolute_bias_reduction_share"] >= MIN_ABS_BIAS_REDUCTION
        and float(original_uplift) > 0.0
        and float(later_uplift) > 0.0
    )
    return row


def select_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [
        row
        for row in rows
        if row["policy_id"] not in {"P0-anchor", "P1-raw-inventory"}
        and bool(row.get("selector_eligible", False))
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
    prediction_parts: list[pd.DataFrame] = []

    for policy in POLICIES:
        predictions = policy_predictions(base, policy)
        if policy.id == "P1-raw-inventory":
            predictions["stage1_forecast_p50"] = base[
                "forecast_p50"
            ].astype(float).to_numpy()
        score = score_policy(predictions)
        policy_rows.append(
            {
                "policy_id": policy.id,
                "description": policy.description,
                "scorecard": score,
            }
        )
        prediction_parts.append(predictions)

    raw_row = next(
        row for row in policy_rows if row["policy_id"] == "P1-raw-inventory"
    )
    raw_predictions = next(
        frame
        for frame in prediction_parts
        if set(frame["policy_id"].astype(str)) == {"P1-raw-inventory"}
    )
    assert_stage1_lineage(raw_predictions, raw_row["scorecard"])
    raw_score = raw_row["scorecard"]

    for row in policy_rows:
        if row["policy_id"] in {"P0-anchor", "P1-raw-inventory"}:
            row["selector_eligible"] = False
        else:
            enrich_policy_row(row, raw_score)

    selection = select_policy(policy_rows)
    predictions = pd.concat(prediction_parts, ignore_index=True)

    return {
        "experiment": EXPERIMENT,
        "stage": STAGE,
        "status": "COMPLETED_STAGE2_RELIABILITY_GATING",
        "production_change": False,
        "promotion_allowed": False,
        "stage1_expert_id": STAGE1_EXPERT_ID,
        "independent_evaluation_unit": "event",
        "evidence_scope": "EXPOSED_HISTORICAL_R_AND_D_24_72H",
        "event_count": int(base["ticket_event_id"].nunique()),
        "row_count": int(len(base)),
        "policy_count": len(policy_rows),
        "pinned_inputs": {
            "dataset_sha256": EXPECTED_DATASET_SHA256,
            "stage1_predictions_sha256": EXPECTED_STAGE1_PREDICTIONS_SHA256,
        },
        "policies": policy_rows,
        "selection": selection,
        "advancement_gates": {
            "minimum_retained_uplift_share_each_view": MIN_RETAINED_UPLIFT_SHARE,
            "minimum_overall_worst_degradation_reduction_share": MIN_WORST_DEGRADATION_REDUCTION,
            "minimum_48_72_worst_degradation_reduction_share": MIN_WORST_DEGRADATION_REDUCTION,
            "minimum_absolute_bias_reduction_share": MIN_ABS_BIAS_REDUCTION,
            "positive_uplift_required_overall_and_both_time_bands": True,
            "positive_uplift_required_in_both_exposed_temporal_subsets": True,
        },
        "limitations": [
            "All Stage-2 events are exposed historical research evidence.",
            "Policy selection is not production-promotion evidence.",
            "The final24 frozen Ridge/P2 Track-A package is unchanged.",
            "The 72-168h learned band remains below the inherited independent-event threshold.",
        ],
    }, predictions


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
    args.output_json.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    predictions.to_csv(args.output_predictions_csv, index=False)

    print(
        json.dumps(
            {
                "selection": result["selection"],
                "policies": [
                    {
                        "policy_id": row["policy_id"],
                        "eligible": row.get("selector_eligible", False),
                        "overall_mae": row["scorecard"]["overall_24_72h"]["event_balanced_mae"],
                        "overall_uplift": row["scorecard"]["overall_24_72h"]["mae_improvement"],
                        "uplift_24_48": row["scorecard"]["band_24_48h"]["mae_improvement"],
                        "uplift_48_72": row["scorecard"]["band_48_72h"]["mae_improvement"],
                        "worst_event_degradation": row["scorecard"]["overall_24_72h"]["worst_event_degradation"],
                        "bias": row["scorecard"]["overall_24_72h"]["event_balanced_bias"],
                        "original_subset_uplift": row["scorecard"]["original_stage1_exposed_subset"].get("mae_improvement"),
                        "later_subset_uplift": row["scorecard"]["later_exposed_subset"].get("mae_improvement"),
                    }
                    for row in result["policies"]
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
