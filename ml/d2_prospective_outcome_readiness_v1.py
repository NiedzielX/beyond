#!/usr/bin/env python3
"""Read-only readiness classifier for frozen d2 prospective evidence.

The model-scoring exports intentionally contain only outcome-eligible events.
Readiness is therefore driven by a separate additive feed that exposes all
tracked Ekstraklasa ticket events with:

- verified attendance outcome when available;
- audited capacity when available;
- raw final-24h snapshot count.

This module never estimates attendance from inventory and never mutates model,
policy, registry or production state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.d2_prospective_score_v1 import (
    EXPECTED_DEVELOPMENT_EVENT_IDS,
    EXPECTED_STAGE2_PACKAGE,
    load_json,
    verify_registry,
)
from ml.d2_live_replay_anchor_v1 import utc_timestamp

EXPERIMENT = "d2-prospective-outcome-readiness-v1"
EXPECTED_READINESS_EXPORT_VERSION = "d2-prospective-readiness-v1"
POST_MATCH_GRACE_HOURS = 3.0

STATUS_READY = "READY_FOR_PROSPECTIVE_SCORE"
STATUS_MISSING_OUTCOME = "BLOCKED_MISSING_OUTCOME"
STATUS_MISSING_LIVE = "BLOCKED_NO_FINAL24_LIVE_ROWS"
STATUS_MISSING_CAPACITY = "BLOCKED_MISSING_CAPACITY"
STATUS_GRACE = "WAITING_POST_MATCH_GRACE"
STATUS_FUTURE = "FUTURE_NOT_DUE"


def _valid_positive_number(value: Any) -> bool:
    if value is None:
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return bool(np.isfinite(number) and number > 0.0)


def verify_readiness_export(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("version") != EXPECTED_READINESS_EXPORT_VERSION:
        raise RuntimeError(
            f"readiness export version drift actual={payload.get('version')} "
            f"expected={EXPECTED_READINESS_EXPORT_VERSION}"
        )
    events = payload.get("events")
    if not isinstance(events, list):
        raise RuntimeError("readiness export events must be a list")
    metadata_count = int(payload.get("eventCount") or 0)
    if metadata_count != len(events):
        raise RuntimeError(
            f"readiness export event count mismatch metadata={metadata_count} rows={len(events)}"
        )
    return events


def classify_events(
    *,
    events: list[dict[str, Any]],
    scored_ids: set[int],
    as_of_at: pd.Timestamp,
) -> list[dict[str, Any]]:
    """Classify every unregistered non-development event without model scoring."""
    as_of = utc_timestamp(as_of_at)
    development = set(EXPECTED_DEVELOPMENT_EVENT_IDS)

    output: list[dict[str, Any]] = []
    for event in events:
        event_id = int(event["ticket_event_id"])
        if event_id in development or event_id in scored_ids:
            continue

        kickoff = utc_timestamp(event["kickoff_at"])
        hours_since_kickoff = float((as_of - kickoff).total_seconds() / 3600.0)
        rows = int(event.get("final24_snapshot_count") or 0)
        has_outcome = _valid_positive_number(event.get("actual_attendance"))
        has_capacity = _valid_positive_number(event.get("stadium_capacity"))

        if hours_since_kickoff < 0.0:
            status = STATUS_FUTURE
        elif hours_since_kickoff < POST_MATCH_GRACE_HOURS:
            status = STATUS_GRACE
        elif not has_outcome:
            status = STATUS_MISSING_OUTCOME
        elif rows <= 0:
            status = STATUS_MISSING_LIVE
        elif not has_capacity:
            status = STATUS_MISSING_CAPACITY
        else:
            status = STATUS_READY

        output.append({
            "ticket_event_id": event_id,
            "club_slug": event.get("club_slug"),
            "home_team": event.get("home_team"),
            "away_team": event.get("away_team"),
            "kickoff_at": kickoff.isoformat(),
            "hours_since_kickoff": hours_since_kickoff,
            "final24_snapshot_count": rows,
            "actual_attendance_present": has_outcome,
            "stadium_capacity_present": has_capacity,
            "outcome_source_name": event.get("outcome_source_name"),
            "outcome_confirmed_at": event.get("outcome_confirmed_at"),
            "capacity_verification_status": event.get("capacity_verification_status"),
            "readiness_status": status,
        })

    return sorted(output, key=lambda row: (row["kickoff_at"], row["ticket_event_id"]))


def build_readiness_report(
    *,
    readiness_export: dict[str, Any],
    registry_path: Path,
    as_of_at: pd.Timestamp,
) -> dict[str, Any]:
    registry, scored_ids = verify_registry(registry_path)
    events = verify_readiness_export(readiness_export)
    rows = classify_events(
        events=events,
        scored_ids=scored_ids,
        as_of_at=as_of_at,
    )

    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row["readiness_status"])
        status_counts[status] = status_counts.get(status, 0) + 1

    completed_attention = [
        row for row in rows
        if row["readiness_status"] in {
            STATUS_READY,
            STATUS_MISSING_OUTCOME,
            STATUS_MISSING_LIVE,
            STATUS_MISSING_CAPACITY,
        }
    ]
    blockers = [
        row for row in completed_attention
        if row["readiness_status"] != STATUS_READY
    ]
    ready = [
        row for row in completed_attention
        if row["readiness_status"] == STATUS_READY
    ]

    return {
        "experiment": EXPERIMENT,
        "status": "READINESS_EVALUATED",
        "as_of_at": utc_timestamp(as_of_at).isoformat(),
        "production_change": False,
        "model_change": False,
        "policy_change": False,
        "attendance_estimation_performed": False,
        "readiness_export_version": EXPECTED_READINESS_EXPORT_VERSION,
        "readiness_export_event_count": int(readiness_export.get("eventCount") or 0),
        "frozen_package_id": EXPECTED_STAGE2_PACKAGE,
        "registry_version": registry["registry_version"],
        "development_event_ids": list(EXPECTED_DEVELOPMENT_EVENT_IDS),
        "registered_prospective_event_ids": sorted(scored_ids),
        "status_counts": status_counts,
        "ready_event_ids": [int(row["ticket_event_id"]) for row in ready],
        "blocked_completed_event_ids": [int(row["ticket_event_id"]) for row in blockers],
        "events": rows,
        "decision_boundary": (
            "Read-only readiness only. Never derive actual attendance from seat-map inventory. "
            "A BLOCKED_MISSING_OUTCOME event becomes scoreable only after a verified outcome "
            "enters the trusted outcome pipeline."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readiness-export", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--as-of-at", type=str, default=None)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    if args.as_of_at:
        as_of = utc_timestamp(args.as_of_at)
    else:
        as_of = pd.Timestamp.now(tz="UTC")

    report = build_readiness_report(
        readiness_export=load_json(args.readiness_export),
        registry_path=args.registry,
        as_of_at=as_of,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "as_of_at": report["as_of_at"],
        "readiness_export_event_count": report["readiness_export_event_count"],
        "ready_event_ids": report["ready_event_ids"],
        "blocked_completed_event_ids": report["blocked_completed_event_ids"],
        "status_counts": report["status_counts"],
        "events": report["events"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
