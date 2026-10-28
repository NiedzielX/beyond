#!/usr/bin/env python3
"""P9 prospective incumbent-family fallback v2.

This is a fallback-only extension of the frozen P9 prospective v1 learner.
It never replaces a v1 prediction. It emits a prediction only when:
- v1 would select a valid D2 Long72 target incumbent,
- the exact frozen five P9a neighbors provide fewer than three usable D2
  residual references, and
- a valid Structural Prior target incumbent exists and the same five neighbors
  provide at least three usable Structural Prior residual references.

No target attendance is accepted or used. Event443 is intentionally not
backfilled; the workflow may persist v2 predictions only inside future genuine
T-48/T-24 immutable windows.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from ml.p9_booking_curve_prospective_v1 import (
    ALLOWED_CUTOFFS,
    MIN_RESIDUAL_NEIGHBORS,
    choose_incumbent,
    parse_dt,
    require,
    scan_forbidden,
    sha,
)

VERSION = "p9-booking-curve-prospective-family-fallback-builder-v2"
PRECOMMIT_ID = "p9-knn-median-residual-k5-family-fallback-v2"
D2_FAMILY = "d2_long72_forward_predictions_v1"
STRUCTURAL_FAMILY = "structural_prior_forecasts_v1"


def family_support(
    *,
    family: str,
    selected_neighbors: list[int],
    event_meta: dict[int, dict[str, Any]],
    catalog_rows: dict[int, list[dict[str, Any]]],
    outcomes: dict[int, dict[str, Any]],
    target_id: int,
    target_as_of: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return usable same-family residual references and fail-closed reasons."""
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
        ref_inc = choose_incumbent(catalog_rows.get(ref_id, []), ref_cutoff, required_source=family)
        if ref_inc is None:
            missing.append({"ticket_event_id": ref_id, "reason": "missing_same_family_pit_incumbent"})
            continue

        outcome = outcomes.get(ref_id)
        if outcome is None:
            missing.append({"ticket_event_id": ref_id, "reason": "missing_genuine_reference_outcome"})
            continue

        confirmed = parse_dt(outcome["confirmed_at"], f"reference[{ref_id}].confirmed_at")
        require(confirmed >= ref_kickoff, f"reference outcome confirmed before kickoff ref={ref_id}")
        if confirmed > target_as_of:
            missing.append({
                "ticket_event_id": ref_id,
                "reason": "reference_outcome_not_known_by_target_cutoff",
                "confirmed_at": confirmed.isoformat(),
                "target_as_of_at": target_as_of.isoformat(),
            })
            continue

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

    return residual_rows, missing


def build_fallback_predictions(
    p9a: dict[str, Any],
    catalog: dict[str, Any],
    reference_outcomes: dict[str, Any],
) -> dict[str, Any]:
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

        # Reproduce the exact v1 target-family decision first. v2 may only act
        # when that frozen path would fail support.
        v1_target_inc = choose_incumbent(frozen_target_candidates, target_as_of)
        selected_neighbors = [int(v) for v in target.get("lineage", {}).get("selected_neighbor_event_ids") or []]
        require(len(selected_neighbors) == 5, f"unexpected frozen neighbor count event={target_id}")

        if v1_target_inc is None:
            diagnostics.append({
                "ticket_event_id": target_id,
                "cutoff_hours": cutoff,
                "status": "NO_TARGET_INCUMBENT",
                "selected_neighbor_event_ids": selected_neighbors,
            })
            continue

        v1_family = str(v1_target_inc["source"])
        v1_residuals, v1_missing = family_support(
            family=v1_family,
            selected_neighbors=selected_neighbors,
            event_meta=event_meta,
            catalog_rows=catalog_rows,
            outcomes=outcomes,
            target_id=target_id,
            target_as_of=target_as_of,
        )

        if len(v1_residuals) >= MIN_RESIDUAL_NEIGHBORS:
            diagnostics.append({
                "ticket_event_id": target_id,
                "cutoff_hours": cutoff,
                "status": "V1_COVERED",
                "v1_target_incumbent_source_family": v1_family,
                "v1_residual_reference_count": len(v1_residuals),
                "selected_neighbor_event_ids": selected_neighbors,
            })
            continue

        # The only allowed fallback path is D2 -> Structural. If v1 already
        # selected Structural, no alternate family is permitted.
        if v1_family != D2_FAMILY:
            diagnostics.append({
                "ticket_event_id": target_id,
                "cutoff_hours": cutoff,
                "status": "FALLBACK_NOT_ALLOWED_FOR_V1_FAMILY",
                "v1_target_incumbent_source_family": v1_family,
                "v1_residual_reference_count": len(v1_residuals),
                "v1_missing_reference_rows": v1_missing,
                "selected_neighbor_event_ids": selected_neighbors,
            })
            continue

        structural_target_inc = choose_incumbent(
            frozen_target_candidates,
            target_as_of,
            required_source=STRUCTURAL_FAMILY,
        )
        if structural_target_inc is None:
            diagnostics.append({
                "ticket_event_id": target_id,
                "cutoff_hours": cutoff,
                "status": "FALLBACK_NO_STRUCTURAL_TARGET_INCUMBENT",
                "v1_target_incumbent_source_family": v1_family,
                "v1_residual_reference_count": len(v1_residuals),
                "v1_missing_reference_rows": v1_missing,
                "selected_neighbor_event_ids": selected_neighbors,
            })
            continue

        structural_residuals, structural_missing = family_support(
            family=STRUCTURAL_FAMILY,
            selected_neighbors=selected_neighbors,
            event_meta=event_meta,
            catalog_rows=catalog_rows,
            outcomes=outcomes,
            target_id=target_id,
            target_as_of=target_as_of,
        )

        support_core = {
            "version": "p9-prospective-family-fallback-support-freeze-v2",
            "precommit_id": PRECOMMIT_ID,
            "ticket_event_id": target_id,
            "cutoff_hours": cutoff,
            "target_as_of_at": target_as_of.isoformat(),
            "p9a_manifest_sha256": str(p9a["manifest_sha256"]),
            "p9a_target_lineage_sha256": str(target["lineage_sha256"]),
            "v1_target_incumbent": v1_target_inc,
            "v1_residual_reference_count": len(v1_residuals),
            "fallback_target_incumbent": structural_target_inc,
            "fallback_target_incumbent_source_family": STRUCTURAL_FAMILY,
            "selected_neighbor_event_ids": selected_neighbors,
            "fallback_residual_reference_rows": structural_residuals,
            "fallback_missing_reference_rows": structural_missing,
            "fallback_residual_reference_count": len(structural_residuals),
            "minimum_residual_neighbors": MIN_RESIDUAL_NEIGHBORS,
            "target_values_used": False,
            "production_change": False,
        }
        support_sha = sha(support_core)

        if len(structural_residuals) < MIN_RESIDUAL_NEIGHBORS:
            diagnostics.append({
                "ticket_event_id": target_id,
                "cutoff_hours": cutoff,
                "status": "FALLBACK_SUPPORT_INSUFFICIENT",
                "v1_target_incumbent_source_family": v1_family,
                "v1_residual_reference_count": len(v1_residuals),
                "fallback_target_incumbent_source_family": STRUCTURAL_FAMILY,
                "fallback_residual_reference_count": len(structural_residuals),
                "selected_neighbor_event_ids": selected_neighbors,
                "fallback_missing_reference_rows": structural_missing,
                "support_manifest_sha256": support_sha,
            })
            continue

        residuals = np.asarray([float(row["residual"]) for row in structural_residuals], dtype=float)
        correction = float(np.median(residuals))
        capacity = int(structural_target_inc["stadium_capacity"])
        anchor = float(structural_target_inc["p50"])
        challenger = float(np.clip(anchor + correction, 0.0, float(capacity)))
        prediction_identity_core = {
            "precommit_id": PRECOMMIT_ID,
            "ticket_event_id": target_id,
            "cutoff_hours": cutoff,
            "target_as_of_at": target_as_of.isoformat(),
            "fallback_from_family": D2_FAMILY,
            "target_incumbent_source": STRUCTURAL_FAMILY,
            "target_incumbent_row_id": int(structural_target_inc["row_id"]),
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
            "fallback_from_family": D2_FAMILY,
            "v1_residual_reference_count": len(v1_residuals),
            "incumbent_source": STRUCTURAL_FAMILY,
            "incumbent_row_id": int(structural_target_inc["row_id"]),
            "incumbent_p50": anchor,
            "trajectory_residual": correction,
            "challenger_p50": challenger,
            "selected_neighbor_event_ids": selected_neighbors,
            "residual_reference_event_ids": [int(row["ticket_event_id"]) for row in structural_residuals],
            "reference_incumbent_row_ids": [int(row["incumbent"]["row_id"]) for row in structural_residuals],
            "p9a_manifest_sha256": str(p9a["manifest_sha256"]),
            "support_manifest_sha256": support_sha,
            "reference_outcomes_sha256": outcomes_sha,
            "prediction_identity_sha256": sha(prediction_identity_core),
            "source_version": VERSION,
        })
        diagnostics.append({
            "ticket_event_id": target_id,
            "cutoff_hours": cutoff,
            "status": "FALLBACK_PREDICTION_READY",
            "v1_target_incumbent_source_family": v1_family,
            "v1_residual_reference_count": len(v1_residuals),
            "fallback_target_incumbent_source_family": STRUCTURAL_FAMILY,
            "fallback_residual_reference_count": len(structural_residuals),
            "selected_neighbor_event_ids": selected_neighbors,
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

    result = build_fallback_predictions(
        json.loads(args.p9a_freeze.read_text()),
        json.loads(args.incumbent_catalog.read_text()),
        json.loads(args.reference_outcomes.read_text()),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "version": result["version"],
        "cutoff_hours": result["cutoff_hours"],
        "fallback_prediction_count": len(result["predictions"]),
        "diagnostics": result["diagnostics"],
        "target_values_used": result["target_values_used"],
        "production_change": result["production_change"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
