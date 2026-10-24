#!/usr/bin/env python3
"""Deterministic target-free freeze harness for P9a T-24/T-48.

The harness freezes representation/reference identities only. It does not open
attendance labels and does not train or select a learner.

Fail-closed guarantees:
- target snapshots must be <= target as_of_at;
- target as_of must equal the declared fixed cutoff from kickoff;
- reference kickoff must be strictly before target as_of_at;
- target event cannot reference itself;
- exact cutoff curve point must be observable;
- at least three canonical target points are required;
- reference-pool identities and raw snapshot identities are persisted in the
  deterministic manifest SHA;
- only incumbent rows genuinely persisted before the target cutoff are exposed
  by the SQL contract and audited here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ml.p9_booking_curve_v1 import (
    DEFAULT_NEIGHBORS,
    MIN_OVERLAP_POINTS,
    CurveObservation,
    HistoricalCurveReference,
    build_normalized_curve,
    estimate_historical_pickup,
)

VERSION = "p9a-booking-curve-freeze-v1"
ALLOWED_CUTOFFS = {24, 48}
MIN_REFERENCE_EVENTS = 3
FORBIDDEN_INPUT_KEYS = {
    "actual_attendance",
    "attendance_label",
    "target_attendance",
    "outcome_attendance",
}


def _parse_dt(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty ISO timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return parsed


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _scan_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_INPUT_KEYS:
                raise ValueError(f"target/label field forbidden in P9a input export: {path}.{key}")
            _scan_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden_keys(child, f"{path}[{index}]")


def _observation(row: dict[str, Any], *, max_at: datetime, name: str) -> CurveObservation:
    snapshot_id = int(row["snapshot_id"])
    captured_at = _parse_dt(row["captured_at"], f"{name}.captured_at")
    if captured_at > max_at:
        raise ValueError(f"{name} snapshot {snapshot_id} is after allowed cutoff")
    available_total = int(row["available_total"])
    if available_total < 0:
        raise ValueError(f"{name} snapshot {snapshot_id} has negative inventory")
    return CurveObservation(snapshot_id, captured_at, available_total)


def _curve_points(curve: Any) -> list[dict[str, float | None]]:
    return [
        {"hours_before_kickoff": float(hours), "available_index": None if value is None else float(value)}
        for hours, value in curve.points
    ]


def _incumbent_audit(rows: list[dict[str, Any]], target_as_of: datetime) -> list[dict[str, Any]]:
    audited: list[dict[str, Any]] = []
    for row in rows:
        persisted_at = _parse_dt(row["persisted_at"], "persisted_incumbent.persisted_at")
        as_of_at = _parse_dt(row["as_of_at"], "persisted_incumbent.as_of_at")
        if persisted_at > target_as_of:
            raise ValueError("persisted incumbent was created after target cutoff")
        if as_of_at > target_as_of:
            raise ValueError("persisted incumbent as_of is after target cutoff")
        audited.append({
            "source": str(row["source"]),
            "row_id": int(row["row_id"]),
            "as_of_at": as_of_at.isoformat(),
            "persisted_at": persisted_at.isoformat(),
            "p50": float(row["p50"]),
            "model_spec_id": None if row.get("model_spec_id") is None else str(row.get("model_spec_id")),
            "point_in_time_validated": bool(row.get("point_in_time_validated", False)),
        })
    return sorted(audited, key=lambda item: (item["persisted_at"], item["source"], item["row_id"]))


def freeze_inputs(payload: dict[str, Any]) -> dict[str, Any]:
    _scan_forbidden_keys(payload)
    if payload.get("version") != "p9a-booking-curve-inputs-v1":
        raise ValueError("unexpected P9a input contract version")
    if payload.get("target_values_used") is not False:
        raise ValueError("P9a input export must be target-free")
    if payload.get("post_cutoff_target_snapshots_exported") is not False:
        raise ValueError("P9a export does not prove post-cutoff target exclusion")
    if payload.get("production_change") is not False:
        raise ValueError("P9a freeze must not change production")

    cutoff_hours = int(payload.get("cutoff_hours"))
    if cutoff_hours not in ALLOWED_CUTOFFS:
        raise ValueError("P9a cutoff must be 24 or 48 hours")

    targets = payload.get("targets")
    if not isinstance(targets, list):
        raise ValueError("targets must be an array")

    frozen_targets: list[dict[str, Any]] = []
    seen_target_ids: set[int] = set()

    for target_row in sorted(targets, key=lambda row: (row["kickoff_at"], int(row["ticket_event_id"]))):
        event_id = int(target_row["ticket_event_id"])
        if event_id in seen_target_ids:
            raise ValueError(f"duplicate target event {event_id}")
        seen_target_ids.add(event_id)

        kickoff_at = _parse_dt(target_row["kickoff_at"], f"target[{event_id}].kickoff_at")
        target_as_of = _parse_dt(target_row["target_as_of_at"], f"target[{event_id}].target_as_of_at")
        expected_as_of = kickoff_at - timedelta(hours=cutoff_hours)
        if abs((target_as_of - expected_as_of).total_seconds()) > 1e-6:
            raise ValueError(f"target {event_id} as_of does not equal fixed T-{cutoff_hours}")

        raw_target_snapshots = target_row.get("target_snapshots", [])
        if not isinstance(raw_target_snapshots, list):
            raise ValueError(f"target {event_id} snapshots must be an array")
        target_observations = [
            _observation(row, max_at=target_as_of, name=f"target[{event_id}]")
            for row in raw_target_snapshots
        ]
        target_snapshot_ids = [obs.snapshot_id for obs in target_observations]
        if len(target_snapshot_ids) != len(set(target_snapshot_ids)):
            raise ValueError(f"target {event_id} contains duplicate snapshot ids")

        representation_error: str | None = None
        target_curve = None
        try:
            target_curve = build_normalized_curve(
                target_observations,
                ticket_event_id=event_id,
                as_of_at=target_as_of,
                kickoff_at=kickoff_at,
            )
        except ValueError as exc:
            representation_error = str(exc)

        target_points: list[dict[str, float | None]] = []
        observed_point_count = 0
        exact_cutoff_available = False
        if target_curve is not None:
            target_points = _curve_points(target_curve)
            point_map = target_curve.as_dict()
            observed_point_count = sum(value is not None for value in point_map.values())
            exact_cutoff_available = point_map.get(float(cutoff_hours)) is not None

        representation_ready = bool(
            target_curve is not None
            and observed_point_count >= MIN_OVERLAP_POINTS
            and exact_cutoff_available
        )

        reference_objects: list[HistoricalCurveReference] = []
        reference_snapshot_ids: dict[int, list[int]] = {}
        reference_errors: list[dict[str, Any]] = []
        raw_refs = target_row.get("reference_events", [])
        if not isinstance(raw_refs, list):
            raise ValueError(f"target {event_id} reference_events must be an array")
        seen_refs: set[int] = set()

        for ref_row in sorted(raw_refs, key=lambda row: (row["kickoff_at"], int(row["ticket_event_id"]))):
            ref_id = int(ref_row["ticket_event_id"])
            if ref_id == event_id:
                raise ValueError(f"target {event_id} references itself")
            if ref_id in seen_refs:
                raise ValueError(f"target {event_id} contains duplicate reference event {ref_id}")
            seen_refs.add(ref_id)
            ref_kickoff = _parse_dt(ref_row["kickoff_at"], f"reference[{ref_id}].kickoff_at")
            if not ref_kickoff < target_as_of:
                raise ValueError(f"reference event {ref_id} is not completed before target {event_id} cutoff")
            raw_ref_snapshots = ref_row.get("snapshots", [])
            if not isinstance(raw_ref_snapshots, list):
                raise ValueError(f"reference {ref_id} snapshots must be an array")
            # Reference booking path may use all snapshots genuinely captured before
            # its own kickoff because the entire reference event precedes target as_of.
            ref_obs = [
                _observation(row, max_at=ref_kickoff, name=f"reference[{ref_id}]")
                for row in raw_ref_snapshots
            ]
            ids = [obs.snapshot_id for obs in ref_obs]
            if len(ids) != len(set(ids)):
                raise ValueError(f"reference {ref_id} contains duplicate snapshot ids")
            reference_snapshot_ids[ref_id] = sorted(ids)
            try:
                ref_curve = build_normalized_curve(
                    ref_obs,
                    ticket_event_id=ref_id,
                    as_of_at=ref_kickoff - timedelta(microseconds=1),
                    kickoff_at=ref_kickoff,
                )
            except ValueError as exc:
                reference_errors.append({"ticket_event_id": ref_id, "reason": str(exc)})
                continue
            reference_objects.append(HistoricalCurveReference(
                ticket_event_id=ref_id,
                club_slug=str(ref_row.get("club_slug") or ""),
                completed_at=ref_kickoff,
                curve=ref_curve,
            ))

        eligible_reference_ids: list[int] = []
        selected_neighbor_ids: list[int] = []
        pickup_features: dict[str, Any] | None = None
        if representation_ready and target_curve is not None:
            # Large k exposes the full set that genuinely satisfies both curve
            # overlap and remaining-pickup requirements. Fixed k=5 is then frozen.
            full_pool = estimate_historical_pickup(
                target_curve,
                reference_objects,
                neighbors=max(1, len(reference_objects)),
                min_overlap_points=MIN_OVERLAP_POINTS,
            )
            eligible_reference_ids = sorted(neighbor.ticket_event_id for neighbor in full_pool.neighbors)
            fixed = estimate_historical_pickup(
                target_curve,
                reference_objects,
                neighbors=DEFAULT_NEIGHBORS,
                min_overlap_points=MIN_OVERLAP_POINTS,
            )
            selected_neighbor_ids = [neighbor.ticket_event_id for neighbor in fixed.neighbors]
            pickup_features = {
                "reference_event_count": full_pool.reference_event_count,
                "reference_club_count": full_pool.reference_club_count,
                "neighbor_count": fixed.neighbor_count,
                "selected_neighbor_ids": selected_neighbor_ids,
                "median_distance": fixed.median_distance,
                "median_remaining_pickup_share": fixed.median_remaining_pickup_share,
                "pickup_q25": fixed.pickup_q25,
                "pickup_q75": fixed.pickup_q75,
                "target_future_points_used": fixed.target_future_points_used,
            }

        incumbent_rows = _incumbent_audit(
            target_row.get("persisted_incumbents", []),
            target_as_of,
        )
        reference_ready = len(eligible_reference_ids) >= MIN_REFERENCE_EVENTS
        freeze_ready = bool(representation_ready and reference_ready)
        comparator_ready = bool(freeze_ready and len(incumbent_rows) > 0)

        lineage = {
            "target_snapshot_ids": sorted(target_snapshot_ids),
            "eligible_reference_event_ids": eligible_reference_ids,
            "selected_neighbor_event_ids": selected_neighbor_ids,
            "eligible_reference_snapshot_ids": {
                str(ref_id): reference_snapshot_ids.get(ref_id, [])
                for ref_id in eligible_reference_ids
            },
            "persisted_incumbent_rows": incumbent_rows,
        }
        lineage_sha = _sha256(lineage)

        frozen_targets.append({
            "ticket_event_id": event_id,
            "club_slug": str(target_row.get("club_slug") or ""),
            "home_team": str(target_row.get("home_team") or ""),
            "away_team": str(target_row.get("away_team") or ""),
            "kickoff_at": kickoff_at.isoformat(),
            "target_as_of_at": target_as_of.isoformat(),
            "cutoff_hours": cutoff_hours,
            "representation_ready": representation_ready,
            "reference_ready": reference_ready,
            "freeze_ready": freeze_ready,
            "comparator_ready": comparator_ready,
            "representation_error": representation_error,
            "observed_canonical_point_count": observed_point_count,
            "exact_cutoff_point_available": exact_cutoff_available,
            "target_curve": target_points,
            "pickup_features": pickup_features,
            "reference_errors": reference_errors,
            "lineage": lineage,
            "lineage_sha256": lineage_sha,
        })

    manifest_core = {
        "version": VERSION,
        "input_contract_version": payload.get("version"),
        "cutoff_hours": cutoff_hours,
        "canonical_hours": payload.get("canonical_hours"),
        "max_interpolation_gap_hours": payload.get("max_interpolation_gap_hours"),
        "minimum_overlap_points": MIN_OVERLAP_POINTS,
        "minimum_reference_events": MIN_REFERENCE_EVENTS,
        "fixed_neighbor_k": DEFAULT_NEIGHBORS,
        "independent_unit": "ticket_event",
        "inventory_interpretation": "demand_proxy_not_confirmed_sales",
        "evidence_class": "historical_exposed_research_representation_freeze",
        "target_values_opened": False,
        "model_training_performed": False,
        "production_change": False,
        "targets": frozen_targets,
    }
    manifest_sha = _sha256(manifest_core)
    summary = {
        "input_target_count": len(frozen_targets),
        "representation_ready_count": sum(row["representation_ready"] for row in frozen_targets),
        "reference_ready_count": sum(row["reference_ready"] for row in frozen_targets),
        "freeze_ready_count": sum(row["freeze_ready"] for row in frozen_targets),
        "comparator_ready_count": sum(row["comparator_ready"] for row in frozen_targets),
        "freeze_ready_event_ids": [row["ticket_event_id"] for row in frozen_targets if row["freeze_ready"]],
        "comparator_ready_event_ids": [row["ticket_event_id"] for row in frozen_targets if row["comparator_ready"]],
        "learner_status": "MODEL_BLOCKED_PENDING_SEPARATE_PRECOMMIT_AND_VALID_COMPARATOR_SAMPLE",
    }
    return {
        **manifest_core,
        "manifest_sha256": manifest_sha,
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.inputs.read_text())
    frozen = freeze_inputs(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "version": frozen["version"],
        "manifest_sha256": frozen["manifest_sha256"],
        "summary": frozen["summary"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
