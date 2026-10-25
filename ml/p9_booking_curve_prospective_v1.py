#!/usr/bin/env python3
"""P9 Booking Curve prospective prediction builder v1.

Uses the exact learner frozen before the ninth historical full-window label:
`p9-knn-median-residual-k5-v1`.

No target attendance is accepted. The builder consumes:
- a target-free P9a freeze for future targets at T-48/T-24;
- a target-free incumbent catalog;
- genuine outcomes only for already-completed reference events.

If fewer than three selected curve neighbors carry a valid same-family PIT
incumbent + genuine reference outcome, the target fails closed and no
prediction is emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

VERSION = "p9-booking-curve-prospective-builder-v1"
PRECOMMIT_ID = "p9-knn-median-residual-k5-v1"
ALLOWED_CUTOFFS = {24, 48}
MIN_RESIDUAL_NEIGHBORS = 3
MAX_LONG72_STALENESS_HOURS = 6.0
FORBIDDEN_TARGET_KEYS = {"actual_attendance", "target_attendance", "target_outcome"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def parse_dt(value: Any, name: str) -> datetime:
    require(isinstance(value, str) and value, f"{name} must be timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None, f"{name} must be timezone aware")
    return parsed


def scan_forbidden(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_TARGET_KEYS:
                raise RuntimeError(f"target label key forbidden: {path}.{key}")
            scan_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            scan_forbidden(child, f"{path}[{i}]")


def incumbent_identity(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": str(row["source"]),
        "row_id": int(row["row_id"]),
        "ticket_event_id": int(row["ticket_event_id"]),
        "as_of_at": parse_dt(row["as_of_at"], "incumbent.as_of_at").isoformat(),
        "persisted_at": parse_dt(row["persisted_at"], "incumbent.persisted_at").isoformat(),
        "p50": float(row["p50"]),
        "stadium_capacity": int(row["stadium_capacity"]),
        "model_spec_id": None if row.get("model_spec_id") is None else str(row.get("model_spec_id")),
    }


def choose_incumbent(rows: list[dict[str, Any]], cutoff_at: datetime, required_source: str | None = None) -> dict[str, Any] | None:
    eligible: list[dict[str, Any]] = []
    for row in rows:
        source = str(row.get("source"))
        if required_source is not None and source != required_source:
            continue
        if not bool(row.get("point_in_time_validated", False)):
            continue
        as_of = parse_dt(row["as_of_at"], "incumbent.as_of_at")
        persisted = parse_dt(row["persisted_at"], "incumbent.persisted_at")
        if as_of > cutoff_at or persisted > cutoff_at:
            continue
        if source == "d2_long72_forward_predictions_v1" and cutoff_at - as_of > timedelta(hours=MAX_LONG72_STALENESS_HOURS):
            continue
        eligible.append(row)
    if not eligible:
        return None
    if required_source is None:
        live = [r for r in eligible if str(r.get("source")) == "d2_long72_forward_predictions_v1"]
        pool = live if live else [r for r in eligible if str(r.get("source")) == "structural_prior_forecasts_v1"]
    else:
        pool = eligible
    if not pool:
        return None
    selected = max(pool, key=lambda r: (
        parse_dt(r["as_of_at"], "incumbent.as_of_at"),
        parse_dt(r["persisted_at"], "incumbent.persisted_at"),
        int(r["row_id"]),
    ))
    return incumbent_identity(selected)


def build_predictions(p9a: dict[str, Any], catalog: dict[str, Any], reference_outcomes: dict[str, Any]) -> dict[str, Any]:
    scan_forbidden(p9a)
    scan_forbidden(catalog)
    require(p9a.get("version") == "p9a-booking-curve-freeze-v1", "unexpected P9a freeze version")
    require(catalog.get("version") == "p9-prospective-incumbent-catalog-v1", "unexpected incumbent catalog version")
    require(reference_outcomes.get("version") == "p9-prospective-reference-outcomes-v1", "unexpected reference outcome version")
    require(p9a.get("target_values_opened") is False, "P9a opened target labels")
    require(p9a.get("model_training_performed") is False, "P9a trained a model")
    require(p9a.get("production_change") is False, "P9a production change")
    require(catalog.get("attendance_values_included") is False, "catalog contains attendance")
    require(catalog.get("target_values_used") is False, "catalog used target values")
    require(catalog.get("production_change") is False, "catalog production change")
    require(reference_outcomes.get("target_attendance_included") is False, "reference payload contains target attendance")
    require(reference_outcomes.get("production_change") is False, "reference payload production change")

    cutoff = int(p9a["cutoff_hours"])
    require(cutoff in ALLOWED_CUTOFFS, "unsupported cutoff")
    require(int(catalog["cutoff_hours"]) == cutoff, "cutoff mismatch")

    event_meta = {int(row["ticket_event_id"]): row for row in catalog.get("events") or []}
    catalog_rows: dict[int, list[dict[str, Any]]] = {}
    by_identity: dict[tuple[str, int], dict[str, Any]] = {}
    for row in catalog.get("incumbents") or []:
        event_id = int(row["ticket_event_id"])
        catalog_rows.setdefault(event_id, []).append(row)
        by_identity[(str(row["source"]), int(row["row_id"]))] = row

    outcomes = {int(row["ticket_event_id"]): row for row in reference_outcomes.get("attendance") or []}
    outcomes_sha = sha(reference_outcomes)

    predictions: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for target in p9a.get("targets") or []:
        target_id = int(target["ticket_event_id"])
        meta = event_meta.get(target_id)
        if meta is None or not bool(meta.get("is_target")):
            continue
        require(target_id not in outcomes, f"future target leaked into reference outcomes event={target_id}")
        target_as_of = parse_dt(target["target_as_of_at"], f"target[{target_id}].target_as_of_at")
        kickoff = parse_dt(meta["kickoff_at"], f"target[{target_id}].kickoff_at")
        require(target_as_of == kickoff - timedelta(hours=cutoff), f"target cutoff drift event={target_id}")

        lineage_rows = target.get("lineage", {}).get("persisted_incumbent_rows") or []
        frozen_target_candidates: list[dict[str, Any]] = []
        for row in lineage_rows:
            full = by_identity.get((str(row["source"]), int(row["row_id"])))
            if full is not None and int(full["ticket_event_id"]) == target_id:
                frozen_target_candidates.append(full)
        target_inc = choose_incumbent(frozen_target_candidates, target_as_of)
        if target_inc is None:
            diagnostics.append({"ticket_event_id": target_id, "cutoff_hours": cutoff, "status": "NO_TARGET_INCUMBENT"})
            continue

        source_family = str(target_inc["source"])
        selected_neighbors = [int(v) for v in target.get("lineage", {}).get("selected_neighbor_event_ids") or []]
        residual_rows: list[dict[str, Any]] = []
        missing: list[dict[str, Any]] = []
        for ref_id in selected_neighbors:
            ref_meta = event_meta.get(ref_id)
            if ref_meta is None:
                missing.append({"ticket_event_id": ref_id, "reason": "missing_reference_metadata"})
                continue
            ref_kickoff = parse_dt(ref_meta["kickoff_at"], f"reference[{ref_id}].kickoff_at")
            require(ref_kickoff < target_as_of, f"reference chronology violation target={target_id} ref={ref_id}")
            ref_cutoff = parse_dt(ref_meta["analogous_cutoff_at"], f"reference[{ref_id}].analogous_cutoff_at")
            ref_inc = choose_incumbent(catalog_rows.get(ref_id, []), ref_cutoff, required_source=source_family)
            if ref_inc is None:
                missing.append({"ticket_event_id": ref_id, "reason": "missing_same_family_pit_incumbent"})
                continue
            outcome = outcomes.get(ref_id)
            if outcome is None:
                missing.append({"ticket_event_id": ref_id, "reason": "missing_genuine_reference_outcome"})
                continue
            confirmed = parse_dt(outcome["confirmed_at"], f"reference[{ref_id}].confirmed_at")
            require(confirmed >= ref_kickoff, f"reference outcome confirmed before kickoff ref={ref_id}")
            actual = int(outcome["actual_attendance"])
            residual_rows.append({
                "ticket_event_id": ref_id,
                "incumbent": ref_inc,
                "actual_attendance": actual,
                "attendance_confirmed_at": confirmed.isoformat(),
                "attendance_definition": outcome.get("attendance_definition"),
                "attendance_source_name": outcome.get("source_name"),
                "attendance_source_url": outcome.get("source_url"),
                "residual": float(actual) - float(ref_inc["p50"]),
            })

        support_core = {
            "version": "p9-prospective-support-freeze-v1",
            "precommit_id": PRECOMMIT_ID,
            "ticket_event_id": target_id,
            "cutoff_hours": cutoff,
            "target_as_of_at": target_as_of.isoformat(),
            "p9a_manifest_sha256": str(p9a["manifest_sha256"]),
            "p9a_target_lineage_sha256": str(target["lineage_sha256"]),
            "target_incumbent": target_inc,
            "target_incumbent_source_family": source_family,
            "selected_neighbor_event_ids": selected_neighbors,
            "residual_reference_rows": residual_rows,
            "missing_reference_rows": missing,
            "residual_reference_count": len(residual_rows),
            "minimum_residual_neighbors": MIN_RESIDUAL_NEIGHBORS,
            "target_values_used": False,
            "production_change": False,
        }
        support_sha = sha(support_core)

        if len(residual_rows) < MIN_RESIDUAL_NEIGHBORS:
            diagnostics.append({
                "ticket_event_id": target_id,
                "cutoff_hours": cutoff,
                "status": "PIT_SUPPORT_INSUFFICIENT",
                "target_incumbent_source_family": source_family,
                "selected_neighbor_event_ids": selected_neighbors,
                "residual_reference_count": len(residual_rows),
                "missing_reference_rows": missing,
                "support_manifest_sha256": support_sha,
            })
            continue

        residuals = np.asarray([float(row["residual"]) for row in residual_rows], dtype=float)
        correction = float(np.median(residuals))
        capacity = int(target_inc["stadium_capacity"])
        anchor = float(target_inc["p50"])
        challenger = float(np.clip(anchor + correction, 0.0, float(capacity)))
        prediction_identity_core = {
            "precommit_id": PRECOMMIT_ID,
            "ticket_event_id": target_id,
            "cutoff_hours": cutoff,
            "target_as_of_at": target_as_of.isoformat(),
            "target_incumbent_source": source_family,
            "target_incumbent_row_id": int(target_inc["row_id"]),
            "p9a_manifest_sha256": str(p9a["manifest_sha256"]),
            "support_manifest_sha256": support_sha,
            "reference_outcomes_sha256": outcomes_sha,
        }
        predictions.append({
            "ticket_event_id": target_id,
            "cutoff_hours": cutoff,
            "target_as_of_at": target_as_of.isoformat(),
            "target_at": kickoff.isoformat(),
            "stadium_capacity": capacity,
            "incumbent_source": source_family,
            "incumbent_row_id": int(target_inc["row_id"]),
            "incumbent_p50": anchor,
            "trajectory_residual": correction,
            "challenger_p50": challenger,
            "selected_neighbor_event_ids": selected_neighbors,
            "residual_reference_event_ids": [int(row["ticket_event_id"]) for row in residual_rows],
            "reference_incumbent_row_ids": [int(row["incumbent"]["row_id"]) for row in residual_rows],
            "p9a_manifest_sha256": str(p9a["manifest_sha256"]),
            "support_manifest_sha256": support_sha,
            "reference_outcomes_sha256": outcomes_sha,
            "prediction_identity_sha256": sha(prediction_identity_core),
            "source_version": VERSION,
        })
        diagnostics.append({
            "ticket_event_id": target_id,
            "cutoff_hours": cutoff,
            "status": "PREDICTION_READY",
            "target_incumbent_source_family": source_family,
            "residual_reference_count": len(residual_rows),
            "support_manifest_sha256": support_sha,
        })

    return {
        "version": VERSION,
        "precommit_id": PRECOMMIT_ID,
        "cutoff_hours": cutoff,
        "p9a_manifest_sha256": str(p9a["manifest_sha256"]),
        "reference_outcomes_sha256": outcomes_sha,
        "predictions": predictions,
        "diagnostics": diagnostics,
        "target_values_used": False,
        "production_activation_allowed": False,
        "live_adjustment": 0,
        "production_change": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p9a-freeze", type=Path, required=True)
    parser.add_argument("--incumbent-catalog", type=Path, required=True)
    parser.add_argument("--reference-outcomes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_predictions(
        json.loads(args.p9a_freeze.read_text()),
        json.loads(args.incumbent_catalog.read_text()),
        json.loads(args.reference_outcomes.read_text()),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "version": result["version"],
        "cutoff_hours": result["cutoff_hours"],
        "prediction_count": len(result["predictions"]),
        "diagnostics": result["diagnostics"],
        "target_values_used": result["target_values_used"],
        "production_change": result["production_change"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
