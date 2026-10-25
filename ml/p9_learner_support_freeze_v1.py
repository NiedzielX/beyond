#!/usr/bin/env python3
"""P9 learner target-free incumbent identity freeze v1.

Consumes:
- a P9a target-free representation freeze for one fixed cutoff;
- a target-free incumbent catalog for the same cutoff.

Produces an immutable deterministic support manifest selecting the exact target
incumbent and same-family reference incumbent identities before attendance
labels are exported. This module never accepts attendance values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

VERSION = "p9-learner-support-freeze-v1"
PRECOMMIT_ID = "p9-knn-median-residual-k5-v1"
ALLOWED_CUTOFFS = {24, 48}
MAX_LONG72_STALENESS_HOURS = 6.0
MIN_RESIDUAL_NEIGHBORS = 3
FORBIDDEN_KEYS = {
    "actual_attendance",
    "attendance_actual",
    "attendance_label",
    "target_attendance",
    "outcome_attendance",
    "actual",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def parse_dt(value: Any, name: str) -> datetime:
    require(isinstance(value, str) and bool(value), f"{name} must be ISO timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None, f"{name} must be timezone aware")
    return parsed


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def scan_forbidden(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise RuntimeError(f"attendance/target key forbidden in target-free P9 support: {path}.{key}")
            scan_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            scan_forbidden(child, f"{path}[{i}]")


def row_identity(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": str(row["source"]),
        "row_id": int(row["row_id"]),
        "ticket_event_id": int(row["ticket_event_id"]),
        "as_of_at": parse_dt(row["as_of_at"], "incumbent.as_of_at").isoformat(),
        "persisted_at": parse_dt(row["persisted_at"], "incumbent.persisted_at").isoformat(),
        "p50": float(row["p50"]),
        "stadium_capacity": int(row["stadium_capacity"]),
        "model_spec_id": None if row.get("model_spec_id") is None else str(row.get("model_spec_id")),
        "point_in_time_validated": bool(row.get("point_in_time_validated", False)),
    }


def choose_incumbent(rows: list[dict[str, Any]], cutoff: datetime, *, required_source: str | None = None) -> dict[str, Any] | None:
    eligible: list[dict[str, Any]] = []
    for row in rows:
        if required_source is not None and str(row.get("source")) != required_source:
            continue
        if not bool(row.get("point_in_time_validated", False)):
            continue
        as_of = parse_dt(row["as_of_at"], "incumbent.as_of_at")
        persisted = parse_dt(row["persisted_at"], "incumbent.persisted_at")
        if as_of > cutoff or persisted > cutoff:
            continue
        if str(row.get("source")) == "d2_long72_forward_predictions_v1" and cutoff - as_of > timedelta(hours=MAX_LONG72_STALENESS_HOURS):
            continue
        eligible.append(row)

    if not eligible:
        return None

    if required_source is None:
        live = [row for row in eligible if str(row.get("source")) == "d2_long72_forward_predictions_v1"]
        pool = live if live else [row for row in eligible if str(row.get("source")) == "structural_prior_forecasts_v1"]
    else:
        pool = eligible
    if not pool:
        return None

    selected = max(
        pool,
        key=lambda row: (
            parse_dt(row["as_of_at"], "incumbent.as_of_at"),
            parse_dt(row["persisted_at"], "incumbent.persisted_at"),
            int(row["row_id"]),
        ),
    )
    return row_identity(selected)


def build_support_freeze(p9a: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    scan_forbidden(p9a)
    scan_forbidden(catalog)
    require(p9a.get("version") == "p9a-booking-curve-freeze-v1", "unexpected P9a freeze version")
    require(catalog.get("version") == "p9-learner-incumbent-catalog-v1", "unexpected incumbent catalog version")
    require(p9a.get("target_values_opened") is False, "P9a target values already opened")
    require(p9a.get("model_training_performed") is False, "P9a model training already performed")
    require(p9a.get("production_change") is False, "P9a production change flag must be false")
    require(catalog.get("attendance_values_included") is False, "incumbent catalog contains attendance")
    require(catalog.get("target_values_used") is False, "incumbent catalog target values used")
    require(catalog.get("production_change") is False, "incumbent catalog production change")

    cutoff_hours = int(p9a["cutoff_hours"])
    require(cutoff_hours in ALLOWED_CUTOFFS, "unsupported cutoff")
    require(int(catalog["cutoff_hours"]) == cutoff_hours, "cutoff mismatch")
    require(int(catalog.get("readiness_168_events", 0)) >= 9, "full-window gate not open")
    require(int(catalog.get("readiness_168_clubs", 0)) >= 3, "full-window club gate not open")

    event_meta = {int(row["ticket_event_id"]): row for row in catalog.get("events") or []}
    catalog_rows: dict[int, list[dict[str, Any]]] = {}
    by_identity: dict[tuple[str, int], dict[str, Any]] = {}
    for row in catalog.get("incumbents") or []:
        event_id = int(row["ticket_event_id"])
        catalog_rows.setdefault(event_id, []).append(row)
        by_identity[(str(row["source"]), int(row["row_id"]))] = row

    frozen_targets: list[dict[str, Any]] = []
    for target in p9a.get("targets") or []:
        if not bool(target.get("comparator_ready")):
            continue
        target_id = int(target["ticket_event_id"])
        target_cutoff = parse_dt(target["target_as_of_at"], f"target[{target_id}].target_as_of_at")
        lineage_rows = target.get("lineage", {}).get("persisted_incumbent_rows") or []

        # Resolve frozen target incumbent only from row identities already present
        # in the P9a target-free lineage, then enrich with capacity from catalog.
        frozen_candidates: list[dict[str, Any]] = []
        for row in lineage_rows:
            identity = (str(row["source"]), int(row["row_id"]))
            full = by_identity.get(identity)
            if full is not None and int(full["ticket_event_id"]) == target_id:
                frozen_candidates.append(full)
        target_incumbent = choose_incumbent(frozen_candidates, target_cutoff)
        if target_incumbent is None:
            continue

        source_family = str(target_incumbent["source"])
        selected_neighbors = [int(v) for v in target.get("lineage", {}).get("selected_neighbor_event_ids") or []]
        reference_incumbents: list[dict[str, Any]] = []
        missing_reference_incumbents: list[int] = []
        for ref_id in selected_neighbors:
            meta = event_meta.get(ref_id)
            if meta is None:
                missing_reference_incumbents.append(ref_id)
                continue
            analogous_cutoff = parse_dt(meta["analogous_cutoff_at"], f"reference[{ref_id}].analogous_cutoff_at")
            selected = choose_incumbent(catalog_rows.get(ref_id, []), analogous_cutoff, required_source=source_family)
            if selected is None:
                missing_reference_incumbents.append(ref_id)
                continue
            reference_incumbents.append(selected)

        support_ready = len(reference_incumbents) >= MIN_RESIDUAL_NEIGHBORS
        target_core = {
            "ticket_event_id": target_id,
            "cutoff_hours": cutoff_hours,
            "target_as_of_at": target_cutoff.isoformat(),
            "p9a_lineage_sha256": str(target["lineage_sha256"]),
            "selected_neighbor_event_ids": selected_neighbors,
            "target_incumbent": target_incumbent,
            "target_incumbent_source_family": source_family,
            "reference_incumbents": sorted(reference_incumbents, key=lambda row: row["ticket_event_id"]),
            "missing_reference_incumbent_event_ids": sorted(missing_reference_incumbents),
            "reference_incumbent_count": len(reference_incumbents),
            "minimum_residual_neighbors": MIN_RESIDUAL_NEIGHBORS,
            "support_ready": support_ready,
        }
        frozen_targets.append({**target_core, "support_lineage_sha256": sha(target_core)})

    core = {
        "version": VERSION,
        "precommit_id": PRECOMMIT_ID,
        "p9a_manifest_sha256": str(p9a["manifest_sha256"]),
        "cutoff_hours": cutoff_hours,
        "fixed_neighbor_k": 5,
        "minimum_residual_neighbors": MIN_RESIDUAL_NEIGHBORS,
        "long72_max_staleness_hours": MAX_LONG72_STALENESS_HOURS,
        "attendance_values_opened": False,
        "target_values_used": False,
        "model_training_performed": False,
        "production_activation_allowed": False,
        "live_adjustment": 0,
        "production_change": False,
        "targets": frozen_targets,
        "summary": {
            "comparator_targets_from_p9a": len([t for t in p9a.get("targets") or [] if bool(t.get("comparator_ready"))]),
            "support_frozen_targets": len(frozen_targets),
            "support_ready_targets": sum(bool(t["support_ready"]) for t in frozen_targets),
            "support_ready_event_ids": [int(t["ticket_event_id"]) for t in frozen_targets if bool(t["support_ready"])],
        },
    }
    return {**core, "manifest_sha256": sha(core)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p9a-freeze", type=Path, required=True)
    parser.add_argument("--incumbent-catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    p9a = json.loads(args.p9a_freeze.read_text())
    catalog = json.loads(args.incumbent_catalog.read_text())
    frozen = build_support_freeze(p9a, catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "version": frozen["version"],
        "manifest_sha256": frozen["manifest_sha256"],
        "summary": frozen["summary"],
        "attendance_values_opened": frozen["attendance_values_opened"],
        "production_change": frozen["production_change"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
