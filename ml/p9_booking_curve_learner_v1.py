#!/usr/bin/env python3
"""Fixed P9 booking-curve analogue residual evaluator v1.

Scientific contract: ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md

This script performs no model selection and fits no coefficients. It consumes
already-registered target-free support freezes plus label/support payloads that
can only be exported after the 9/9 gate. For each target/cutoff it applies the
single precommitted learner:

  target incumbent + median residual of valid curve-neighbour references

The independent unit is ticket_event. The primary score is the event-balanced
mean AE across the fixed T-48/T-24 cutoff lanes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

VERSION = "p9-booking-curve-learner-v1"
PRECOMMIT_ID = "p9-knn-median-residual-k5-v1"
ALLOWED_CUTOFFS = (48, 24)
MIN_RESIDUAL_NEIGHBORS = 3
BOOTSTRAP_SEED = 42
BOOTSTRAP_REPS = 20_000


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def validate_pair(support: dict[str, Any], labels: dict[str, Any]) -> int:
    require(support.get("version") == "p9-learner-support-freeze-v1", "unexpected support freeze version")
    require(labels.get("version") == "p9-learner-label-support-v2", "unexpected label payload version")
    require(support.get("precommit_id") == PRECOMMIT_ID, "support precommit mismatch")
    require(labels.get("precommit_id") == PRECOMMIT_ID, "label precommit mismatch")
    cutoff = int(support["cutoff_hours"])
    require(cutoff in ALLOWED_CUTOFFS, "unsupported cutoff")
    require(int(labels["cutoff_hours"]) == cutoff, "cutoff mismatch")
    require(labels.get("registered_p9a_manifest_sha256") == support.get("p9a_manifest_sha256"), "P9a manifest mismatch")
    require(labels.get("registered_support_manifest_sha256") == support.get("manifest_sha256"), "support manifest mismatch")
    require(support.get("attendance_values_opened") is False, "support freeze opened attendance")
    require(support.get("target_values_used") is False, "support freeze used targets")
    require(support.get("model_training_performed") is False, "support freeze trained model")
    require(support.get("production_change") is False, "support freeze production change")
    require(labels.get("target_free_support_freeze_registered") is True, "label payload lacks registered support freeze")
    require(labels.get("production_change") is False, "label payload production change")
    require(int(labels.get("readiness_168_events", 0)) >= 9, "9/9 gate not open")
    require(int(labels.get("readiness_168_clubs", 0)) >= 3, "club gate not open")
    return cutoff


def build_maps(labels: dict[str, Any]) -> tuple[dict[int, dict[str, Any]], dict[int, int]]:
    events = {int(row["ticket_event_id"]): row for row in labels.get("events") or []}
    attendance: dict[int, int] = {}
    for row in labels.get("attendance") or []:
        event_id = int(row["ticket_event_id"])
        require(event_id in events, f"attendance event missing metadata {event_id}")
        kickoff = np.datetime64(str(events[event_id]["kickoff_at"]))
        confirmed = np.datetime64(str(row["confirmed_at"]))
        require(confirmed >= kickoff, f"attendance confirmed before kickoff event={event_id}")
        value = int(row["actual_attendance"])
        require(value >= 0, f"negative attendance event={event_id}")
        attendance[event_id] = value
    return events, attendance


def evaluate_cutoff(support: dict[str, Any], labels: dict[str, Any]) -> list[dict[str, Any]]:
    cutoff = validate_pair(support, labels)
    events, attendance = build_maps(labels)
    rows: list[dict[str, Any]] = []

    for target in support.get("targets") or []:
        if not bool(target.get("support_ready")):
            continue
        target_id = int(target["ticket_event_id"])
        if target_id not in attendance:
            continue
        target_inc = target["target_incumbent"]
        capacity = int(target_inc["stadium_capacity"])
        require(capacity > 0, f"invalid capacity target={target_id}")
        anchor = float(target_inc["p50"])
        require(0 <= anchor <= capacity, f"anchor outside capacity target={target_id}")

        residuals: list[float] = []
        reference_rows: list[dict[str, Any]] = []
        for ref_inc in target.get("reference_incumbents") or []:
            ref_id = int(ref_inc["ticket_event_id"])
            if ref_id not in attendance:
                continue
            residual = float(attendance[ref_id]) - float(ref_inc["p50"])
            residuals.append(residual)
            reference_rows.append({
                "ticket_event_id": ref_id,
                "incumbent_source": str(ref_inc["source"]),
                "incumbent_row_id": int(ref_inc["row_id"]),
                "incumbent_p50": float(ref_inc["p50"]),
                "actual_attendance": int(attendance[ref_id]),
                "residual": residual,
            })

        if len(residuals) < MIN_RESIDUAL_NEIGHBORS:
            continue

        correction = float(np.median(np.asarray(residuals, dtype=float)))
        challenger = float(np.clip(anchor + correction, 0.0, float(capacity)))
        actual = int(attendance[target_id])
        anchor_error = anchor - actual
        challenger_error = challenger - actual
        rows.append({
            "ticket_event_id": target_id,
            "cutoff_hours": cutoff,
            "actual_attendance": actual,
            "stadium_capacity": capacity,
            "incumbent_source": str(target_inc["source"]),
            "incumbent_row_id": int(target_inc["row_id"]),
            "incumbent_p50": anchor,
            "trajectory_residual": correction,
            "challenger_p50": challenger,
            "anchor_error": anchor_error,
            "challenger_error": challenger_error,
            "anchor_abs_error": abs(anchor_error),
            "challenger_abs_error": abs(challenger_error),
            "delta_abs_error": abs(challenger_error) - abs(anchor_error),
            "improved": abs(challenger_error) < abs(anchor_error),
            "residual_neighbor_count": len(residuals),
            "selected_neighbor_event_ids": [int(v) for v in target.get("selected_neighbor_event_ids") or []],
            "residual_reference_rows": reference_rows,
            "target_support_lineage_sha256": str(target["support_lineage_sha256"]),
            "support_manifest_sha256": str(support["manifest_sha256"]),
            "p9a_manifest_sha256": str(support["p9a_manifest_sha256"]),
        })
    return rows


def event_balanced(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, float | int | None]]:
    by_event: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_event.setdefault(int(row["ticket_event_id"]), []).append(row)

    event_rows: list[dict[str, Any]] = []
    for event_id, values in sorted(by_event.items()):
        anchor_ae = float(np.mean([float(v["anchor_abs_error"]) for v in values]))
        challenger_ae = float(np.mean([float(v["challenger_abs_error"]) for v in values]))
        anchor_bias = float(np.mean([float(v["anchor_error"]) for v in values]))
        challenger_bias = float(np.mean([float(v["challenger_error"]) for v in values]))
        event_rows.append({
            "ticket_event_id": event_id,
            "cutoff_count": len(values),
            "cutoffs": sorted(int(v["cutoff_hours"]) for v in values),
            "anchor_mean_abs_error": anchor_ae,
            "challenger_mean_abs_error": challenger_ae,
            "delta_mean_abs_error": challenger_ae - anchor_ae,
            "anchor_mean_bias": anchor_bias,
            "challenger_mean_bias": challenger_bias,
            "improved": challenger_ae < anchor_ae,
        })

    if not event_rows:
        return [], {
            "event_count": 0,
            "anchor_event_balanced_mae": None,
            "challenger_event_balanced_mae": None,
            "delta_event_balanced_mae": None,
        }

    anchor = np.asarray([r["anchor_mean_abs_error"] for r in event_rows], dtype=float)
    challenger = np.asarray([r["challenger_mean_abs_error"] for r in event_rows], dtype=float)
    delta = challenger - anchor
    summary: dict[str, float | int | None] = {
        "event_count": len(event_rows),
        "anchor_event_balanced_mae": float(np.mean(anchor)),
        "challenger_event_balanced_mae": float(np.mean(challenger)),
        "delta_event_balanced_mae": float(np.mean(delta)),
        "relative_point_improvement": float((np.mean(anchor) - np.mean(challenger)) / np.mean(anchor)) if np.mean(anchor) > 0 else None,
        "event_improvement_rate": float(np.mean(delta < 0)),
        "anchor_event_balanced_bias": float(np.mean([r["anchor_mean_bias"] for r in event_rows])),
        "challenger_event_balanced_bias": float(np.mean([r["challenger_mean_bias"] for r in event_rows])),
        "challenger_event_median_ae": float(np.median(challenger)),
        "challenger_event_p90_ae": float(np.quantile(challenger, 0.9)),
        "worst_event_degradation": float(np.max(delta)),
    }
    return event_rows, summary


def cutoff_summary(rows: list[dict[str, Any]], cutoff: int) -> dict[str, Any]:
    subset = [r for r in rows if int(r["cutoff_hours"]) == cutoff]
    if not subset:
        return {"cutoff_hours": cutoff, "event_count": 0}
    anchor = np.asarray([r["anchor_abs_error"] for r in subset], dtype=float)
    challenger = np.asarray([r["challenger_abs_error"] for r in subset], dtype=float)
    return {
        "cutoff_hours": cutoff,
        "event_count": len(subset),
        "anchor_mae": float(np.mean(anchor)),
        "challenger_mae": float(np.mean(challenger)),
        "delta_mae": float(np.mean(challenger - anchor)),
        "event_improvement_rate": float(np.mean(challenger < anchor)),
        "challenger_bias": float(np.mean([r["challenger_error"] for r in subset])),
    }


def bootstrap_delta(event_rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(event_rows)
    if n == 0:
        return {"event_count": 0, "reps": 0, "ci95": [None, None], "p_delta_lt_zero": None}
    delta = np.asarray([r["delta_mean_abs_error"] for r in event_rows], dtype=float)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    idx = rng.integers(0, n, size=(BOOTSTRAP_REPS, n))
    means = delta[idx].mean(axis=1)
    return {
        "event_count": n,
        "reps": BOOTSTRAP_REPS,
        "seed": BOOTSTRAP_SEED,
        "ci95": [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))],
        "p_delta_lt_zero": float(np.mean(means < 0.0)),
    }


def run(support_48: dict[str, Any], labels_48: dict[str, Any], support_24: dict[str, Any], labels_24: dict[str, Any]) -> dict[str, Any]:
    rows = evaluate_cutoff(support_48, labels_48) + evaluate_cutoff(support_24, labels_24)
    require(rows, "no learner-evaluable P9 rows")
    event_rows, primary = event_balanced(rows)
    uncertainty = bootstrap_delta(event_rows)

    delta = primary.get("delta_event_balanced_mae")
    if delta is None or float(delta) >= 0:
        evidence = "NO_RESEARCH_GAIN"
    else:
        # Governance business minimum meaningful delta is not approved yet, so
        # this lane cannot self-declare ROBUST_RESEARCH_ADVANCE.
        evidence = "POINT_GAIN_UNCERTAINTY_LIMITED"

    core = {
        "version": VERSION,
        "precommit_id": PRECOMMIT_ID,
        "cutoffs": [48, 24],
        "independent_unit": "ticket_event",
        "learner": {
            "type": "fixed_nonparametric_analogue_residual",
            "neighbor_k": 5,
            "minimum_residual_neighbors": MIN_RESIDUAL_NEIGHBORS,
            "aggregation": "median_reference_residual",
            "fitted_coefficients": False,
            "candidate_search": False,
        },
        "row_count": len(rows),
        "independent_event_count": len(event_rows),
        "rows": rows,
        "event_rows": event_rows,
        "primary": primary,
        "cutoff_metrics": [cutoff_summary(rows, 48), cutoff_summary(rows, 24)],
        "uncertainty": uncertainty,
        "evidence_status": evidence,
        "business_minimum_meaningful_delta_approved": False,
        "production_activation_allowed": False,
        "live_adjustment": 0,
        "production_change": False,
    }
    return {**core, "result_sha256": sha(core)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--support-48", type=Path, required=True)
    parser.add_argument("--labels-48", type=Path, required=True)
    parser.add_argument("--support-24", type=Path, required=True)
    parser.add_argument("--labels-24", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = run(
        json.loads(args.support_48.read_text()),
        json.loads(args.labels_48.read_text()),
        json.loads(args.support_24.read_text()),
        json.loads(args.labels_24.read_text()),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "version": result["version"],
        "result_sha256": result["result_sha256"],
        "primary": result["primary"],
        "cutoff_metrics": result["cutoff_metrics"],
        "uncertainty": result["uncertainty"],
        "evidence_status": result["evidence_status"],
        "production_change": result["production_change"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
