#!/usr/bin/env python3
"""P7 Long168 precommit/freeze harness.

This module deliberately does *not* fit a model. Its job is to make the
72-168h experiment impossible to start until the predeclared data gate is met,
then freeze the exact event/as-of/snapshot identities and the modelling
contract before any Long168 model comparison is opened.

The independent unit is an event. N=9 is a research-start threshold only; it
is not evidence for production promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

VERSION = "p7-long168-harness-v1"
EXPECTED_EXPORT_VERSION = "d2-long-horizon-168-rows-v1"
WINDOW_LOWER_EXCLUSIVE_HOURS = 72.0
WINDOW_UPPER_INCLUSIVE_HOURS = 168.0
EXPECTED_CADENCE_HOURS = 6
MIN_INDEPENDENT_EVENTS = 9
MIN_FORWARD_TRAIN_EVENTS = 5

PROHIBITED_TARGET_KEYS = {
    "actual_attendance",
    "attendance_actual",
    "target",
    "target_attendance",
    "label",
    "outcome",
    "outcome_confirmed_at",
}

# Features are frozen before labels/model results. The list is intentionally
# small, interpretable and already present in the current PIT trajectory
# contract. No context feature added later may silently enter P7 v1.
FEATURE_ALLOWLIST = (
    "hours_to_kickoff",
    "available_index",
    "available_total",
    "available_share_of_capacity",
    "first_available_total",
    "net_removed_since_first",
    "net_removed_since_previous",
    "velocity_since_previous",
    "velocity_7d",
    "velocity_72h",
    "velocity_7d_pct_of_capacity_per_hour",
    "velocity_72h_pct_of_capacity_per_hour",
    "acceleration_72h_vs_7d",
    "observation_window_hours",
    "snapshot_age_minutes",
    "max_visible_gap_hours",
    "raw_snapshot_count",
    "clean_snapshot_count",
    "data_gap_detected",
    "release_activity_flag",
    "unexplained_inventory_increase_flag",
)

CANDIDATES = (
    {
        "candidate_id": "anchor-only-t7",
        "role": "incumbent_control",
        "prediction": "PIT-safe Structural Prior T-7 forecast; zero live correction",
        "fit": False,
    },
    {
        "candidate_id": "q50-linear-residual-a002",
        "role": "mae_native_challenger",
        "prediction": "T-7 anchor + learned residual",
        "estimator": "QuantileRegressor",
        "fixed_parameters": {
            "quantile": 0.5,
            "alpha": 0.002,
            "solver": "highs",
        },
        "preprocessing": "training-fold median imputation + RobustScaler",
        "event_weighting": "each training event contributes total weight 1",
        "fit": True,
    },
    {
        "candidate_id": "gbr-l1-depth2-n50-lr003",
        "role": "nonlinear_mae_challenger",
        "prediction": "T-7 anchor + learned residual",
        "estimator": "GradientBoostingRegressor",
        "fixed_parameters": {
            "loss": "absolute_error",
            "n_estimators": 50,
            "learning_rate": 0.03,
            "max_depth": 2,
            "min_samples_leaf": 4,
            "random_state": 42,
        },
        "preprocessing": "training-fold median imputation",
        "event_weighting": "each training event contributes total weight 1",
        "fit": True,
    },
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _parse_ts(value: Any) -> datetime:
    require(value is not None, "missing timestamp")
    text = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    require(parsed.tzinfo is not None, f"timestamp must be timezone-aware: {value}")
    return parsed


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def experiment_contract() -> dict[str, Any]:
    return {
        "version": VERSION,
        "research_question": (
            "Does PIT live ticket trajectory between 72h and 168h before kickoff "
            "reduce event-balanced MAE beyond the Structural Prior T-7 anchor?"
        ),
        "evidence_class": "historical_forward_fold_exposed_research",
        "independent_unit": "ticket_event",
        "research_start_gate": {
            "minimum_independent_events_with_rows_gt_72h": MIN_INDEPENDENT_EVENTS,
            "meaning": "research may start; this is not a production adequacy threshold",
        },
        "window": {
            "hours_to_kickoff": ">72 and <=168",
            "sampling": "latest snapshot in each event x 6h bucket",
            "cadence_hours": EXPECTED_CADENCE_HOURS,
        },
        "anchor": {
            "id": "structural-prior-t7",
            "rule": (
                "Use only the PIT-safe Structural Prior T-7 forecast available at or before "
                "the live row as_of. Do not interpolate from T-3/T-1 and do not extrapolate "
                "Long72 P2 backward beyond 72h."
            ),
        },
        "target": {
            "name": "actual_attendance",
            "join_timing": "only after this identity manifest is frozen",
            "must_not_exist_in_freeze_payload": True,
        },
        "feature_allowlist": list(FEATURE_ALLOWLIST),
        "candidate_family": list(CANDIDATES),
        "training": {
            "target": "actual_attendance - structural_prior_t7",
            "row_weight": "1 / rows_for_training_event",
            "hyperparameter_search": "none in v1; challenger parameters are fixed pre-result",
            "random_seed": 42,
        },
        "validation": {
            "utility": "ml/temporal_validation_v1.py::build_forward_event_folds",
            "type": "strict_forward_event",
            "min_train_events": MIN_FORWARD_TRAIN_EVENTS,
            "rule": "train_end < test_start; tied kickoffs cannot train each other",
            "random_snapshot_split_allowed": False,
        },
        "primary_metric": {
            "name": "event_balanced_mae",
            "aggregation": "mean of per-event mean absolute error across held-out rows",
        },
        "secondary_metrics": [
            "median_absolute_error",
            "signed_bias",
            "p90_absolute_error",
            "worst_event_degradation",
            "event_improvement_rate",
            "forward_fold_mae_delta",
            "horizon_band_mae_72_96_96_120_120_144_144_168",
        ],
        "uncertainty": {
            "utility": "ml/mae_delta_uncertainty_v1.py",
            "method": "paired_event_block_percentile_bootstrap",
            "n_resamples": 5000,
            "seed": 42,
            "interpretation": {
                "delta_mae_ge_0": "NO_MAE_GAIN",
                "delta_mae_lt_0_and_ci_crosses_0": "POINT_GAIN_UNCERTAINTY_LIMITED",
                "ci_upper_lt_0": "SUPPORTED_HISTORICAL_FORWARD_GAIN",
            },
        },
        "research_advancement_rule": {
            "required": [
                "challenger event-balanced forward MAE < T-7 anchor MAE",
                "challenger improves a majority of independently held-out events",
                "challenger improves a majority of usable forward folds",
                "PIT/lineage/reproducibility checks pass",
            ],
            "note": (
                "Bootstrap CI is mandatory evidence. At N=9 a CI crossing zero is expected to "
                "remain uncertainty-limited and cannot imply production readiness."
            ),
        },
        "production": {
            "promotion_allowed_from_p7_v1": False,
            "live_adjustment": 0,
        },
    }


def _validate_payload_header(payload: dict[str, Any]) -> None:
    require(payload.get("version") == EXPECTED_EXPORT_VERSION, "unexpected Long168 export version")
    sampling = payload.get("sampling") or {}
    require(int(sampling.get("window_hours", -1)) == 168, "Long168 export window drift")
    require(int(sampling.get("cadence_hours", -1)) == EXPECTED_CADENCE_HOURS, "Long168 cadence drift")
    prohibited = sorted(set(_walk_keys(payload)) & PROHIBITED_TARGET_KEYS)
    require(not prohibited, f"target/outcome leakage in freeze payload keys: {prohibited}")


def _eligible_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    _validate_payload_header(payload)
    rows = list(payload.get("liveRows") or [])
    normalized: list[dict[str, Any]] = []
    seen_event_bucket: set[tuple[int, int]] = set()
    seen_identity: set[tuple[int, str, int]] = set()

    for row in rows:
        event_id = int(row["ticket_event_id"])
        bucket = int(row["bucket_6h"])
        hours = float(row["hours_to_kickoff"])
        if not (WINDOW_LOWER_EXCLUSIVE_HOURS < hours <= WINDOW_UPPER_INCLUSIVE_HOURS):
            continue

        features = dict(row.get("features") or {})
        require(bool(features.get("point_in_time_validated")), f"PIT invalid event={event_id} bucket={bucket}")
        requested_snapshot_id = int(row["requested_snapshot_id"])
        feature_snapshot_id = int(features["snapshot_id"])
        require(requested_snapshot_id == feature_snapshot_id, f"snapshot identity drift event={event_id} bucket={bucket}")

        requested_as_of = _parse_ts(row["requested_as_of_at"])
        feature_as_of = _parse_ts(features["as_of_at"])
        require(requested_as_of == feature_as_of, f"as_of identity drift event={event_id} bucket={bucket}")
        kickoff = _parse_ts(features["kickoff_at"])
        require(requested_as_of < kickoff, f"as_of must precede kickoff event={event_id} bucket={bucket}")

        computed_hours = (kickoff - requested_as_of).total_seconds() / 3600.0
        require(abs(computed_hours - hours) <= 0.02, f"hours_to_kickoff drift event={event_id} bucket={bucket}")

        event_bucket = (event_id, bucket)
        require(event_bucket not in seen_event_bucket, f"duplicate event/bucket {event_bucket}")
        seen_event_bucket.add(event_bucket)
        identity = (event_id, requested_as_of.isoformat(), requested_snapshot_id)
        require(identity not in seen_identity, f"duplicate Long168 identity {identity}")
        seen_identity.add(identity)

        normalized.append({
            "ticket_event_id": event_id,
            "bucket_6h": bucket,
            "hours_to_kickoff": round(hours, 9),
            "requested_as_of_at": requested_as_of.isoformat(),
            "requested_snapshot_id": requested_snapshot_id,
            "kickoff_at": kickoff.isoformat(),
            "feature_version": features.get("feature_version"),
            "feature_quality": features.get("feature_quality"),
        })

    normalized.sort(key=lambda x: (x["kickoff_at"], x["ticket_event_id"], x["requested_as_of_at"], x["bucket_6h"]))
    return normalized


def readiness(payload: dict[str, Any]) -> dict[str, Any]:
    rows = _eligible_rows(payload)
    event_counts = Counter(row["ticket_event_id"] for row in rows)
    event_count = len(event_counts)
    return {
        "version": VERSION,
        "status": "READY_TO_FREEZE" if event_count >= MIN_INDEPENDENT_EVENTS else "P7_NOT_READY",
        "independent_events_gt_72h": event_count,
        "rows_gt_72h": len(rows),
        "research_start_threshold": MIN_INDEPENDENT_EVENTS,
        "threshold_met": event_count >= MIN_INDEPENDENT_EVENTS,
        "rows_per_event": {str(key): event_counts[key] for key in sorted(event_counts)},
        "model_training_performed": False,
        "production_change": False,
    }


def freeze_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    rows = _eligible_rows(payload)
    by_event: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_event[row["ticket_event_id"]].append(row)

    event_ids = sorted(by_event)
    require(
        len(event_ids) >= MIN_INDEPENDENT_EVENTS,
        f"P7_NOT_READY: independent_events_gt_72h={len(event_ids)} threshold={MIN_INDEPENDENT_EVENTS}",
    )

    event_summary = []
    for event_id in event_ids:
        event_rows = by_event[event_id]
        event_summary.append({
            "ticket_event_id": event_id,
            "row_count": len(event_rows),
            "max_hours_to_kickoff": max(row["hours_to_kickoff"] for row in event_rows),
            "min_hours_to_kickoff": min(row["hours_to_kickoff"] for row in event_rows),
            "kickoff_at": event_rows[0]["kickoff_at"],
        })

    contract = experiment_contract()
    freeze_core = {
        "version": VERSION,
        "status": "P7_LONG168_IDENTITIES_FROZEN",
        "source_export_version": EXPECTED_EXPORT_VERSION,
        "independent_event_count": len(event_ids),
        "row_count": len(rows),
        "event_ids": event_ids,
        "event_summary": event_summary,
        "identities": rows,
        "experiment_contract": contract,
        "target_values_present": False,
        "model_training_performed": False,
        "model_results_opened": False,
        "production_change": False,
    }
    return {
        **freeze_core,
        "manifest_sha256": _sha(freeze_core),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--mode", choices=("contract", "readiness", "freeze"), default="freeze")
    args = parser.parse_args()

    if args.mode == "contract":
        result = experiment_contract()
    else:
        require(args.input_json is not None, "--input-json is required for readiness/freeze")
        payload = json.loads(args.input_json.read_text())
        result = readiness(payload) if args.mode == "readiness" else freeze_manifest(payload)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
