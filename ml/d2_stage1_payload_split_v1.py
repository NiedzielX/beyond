#!/usr/bin/env python3
"""Freeze d2 Stage-1 development rows while preserving newer events as holdouts.

The C1 export is intentionally append-only/dynamic. The frozen C1 v8 training
contract is not. This utility rebuilds the exact committed 9-event / 30-row
Stage-1 development payload by identity (event + as-of timestamp) and keeps any
new completed events outside development for later chronological/prospective
scoring.

It does not alter, downsample, or relabel the committed training rows.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

EXPECTED_FROZEN_EVENT_COUNT = 9
EXPECTED_FROZEN_ROW_COUNT = 30


def utc_timestamp(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def live_row_key(row: dict[str, Any]) -> tuple[int, str]:
    features = row.get("features") or {}
    value = features.get("as_of_at") or row.get("requested_as_of_at")
    if value is None:
        raise RuntimeError("live row missing as-of timestamp")
    return int(row["ticket_event_id"]), utc_timestamp(value).isoformat()


def contract_row_key(row: dict[str, Any]) -> tuple[int, str]:
    return int(row["ticket_event_id"]), utc_timestamp(row["as_of_at"]).isoformat()


def split_payload(
    *,
    events_export: dict[str, Any],
    attendance_export: dict[str, Any],
    sporting_export: dict[str, Any],
    aliases_export: dict[str, Any],
    live_export: dict[str, Any],
    training_contract: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    contract_rows = training_contract.get("rows") or []
    if len(contract_rows) != EXPECTED_FROZEN_ROW_COUNT:
        raise RuntimeError(
            f"unexpected committed C1 row count {len(contract_rows)}"
        )
    expected_keys = [contract_row_key(row) for row in contract_rows]
    if len(set(expected_keys)) != EXPECTED_FROZEN_ROW_COUNT:
        raise RuntimeError("duplicate keys in committed C1 training contract")
    frozen_event_ids = sorted({event_id for event_id, _ in expected_keys})
    if len(frozen_event_ids) != EXPECTED_FROZEN_EVENT_COUNT:
        raise RuntimeError(
            f"unexpected committed C1 event count {len(frozen_event_ids)}"
        )

    current_live_rows = live_export.get("liveRows") or []
    by_key: dict[tuple[int, str], dict[str, Any]] = {}
    duplicate_current_keys: list[tuple[int, str]] = []
    for row in current_live_rows:
        key = live_row_key(row)
        if key in by_key:
            duplicate_current_keys.append(key)
        by_key[key] = row
    if duplicate_current_keys:
        raise RuntimeError(
            f"duplicate current live-row keys: {duplicate_current_keys[:5]}"
        )

    missing = sorted(set(expected_keys) - set(by_key))
    if missing:
        raise RuntimeError(
            f"current exporter no longer contains frozen C1 rows missing={missing[:10]}"
        )
    frozen_live_rows = [by_key[key] for key in expected_keys]
    extra_live_rows = [
        row for key, row in by_key.items() if key not in set(expected_keys)
    ]

    events = events_export.get("events") or []
    events_by_id = {int(row["ticket_event_id"]): row for row in events}
    missing_events = sorted(set(frozen_event_ids) - set(events_by_id))
    if missing_events:
        raise RuntimeError(f"current exporter missing frozen events {missing_events}")
    frozen_events = [events_by_id[event_id] for event_id in frozen_event_ids]

    max_frozen_kickoff = max(
        utc_timestamp(row["kickoff_at"])
        for row in frozen_events
    )
    # The committed Stage-0 capacity audit was created before later completed
    # events were appended. Rows after the final frozen event cannot affect any
    # frozen event's PIT state and are excluded explicitly to preserve the
    # audited attendance-row counts.
    frozen_attendance = [
        row
        for row in (attendance_export.get("attendance") or [])
        if utc_timestamp(row["kickoff_at"]) <= max_frozen_kickoff
    ]

    extra_event_ids = sorted({int(row["ticket_event_id"]) for row in extra_live_rows})
    extra_rows_by_event = {
        event_id: sum(
            1 for row in extra_live_rows if int(row["ticket_event_id"]) == event_id
        )
        for event_id in extra_event_ids
    }
    holdout_events = [events_by_id[event_id] for event_id in extra_event_ids if event_id in events_by_id]

    frozen_payload = {
        "version": "d2-stage1-frozen-c1-development-payload-v1",
        "eventCount": len(frozen_events),
        "events": frozen_events,
        "attendance": frozen_attendance,
        "sportingMatches": sporting_export.get("sportingMatches") or [],
        "aliases": aliases_export.get("aliases") or {},
        "liveRows": frozen_live_rows,
        "liveRowCount": len(frozen_live_rows),
        "sampling": live_export.get("sampling"),
    }
    if frozen_payload["eventCount"] != EXPECTED_FROZEN_EVENT_COUNT:
        raise RuntimeError("frozen development event count changed")
    if frozen_payload["liveRowCount"] != EXPECTED_FROZEN_ROW_COUNT:
        raise RuntimeError("frozen development live-row count changed")

    split_manifest = {
        "split_version": "d2-stage1-frozen-development-plus-new-holdouts-v1",
        "frozen_development": {
            "event_ids": frozen_event_ids,
            "event_count": len(frozen_event_ids),
            "live_row_count": len(frozen_live_rows),
            "max_kickoff_at": max_frozen_kickoff.isoformat(),
        },
        "current_export": {
            "event_count_metadata": live_export.get("eventCount"),
            "live_row_count_metadata": live_export.get("liveRowCount"),
            "actual_live_rows": len(current_live_rows),
        },
        "new_holdout_candidates": {
            "event_ids": extra_event_ids,
            "event_count": len(extra_event_ids),
            "live_rows_by_event": extra_rows_by_event,
            "events": [
                {
                    "ticket_event_id": int(row["ticket_event_id"]),
                    "club_slug": row.get("club_slug"),
                    "home_team": row.get("home_team"),
                    "away_team": row.get("away_team"),
                    "kickoff_at": row.get("kickoff_at"),
                    "actual_attendance": row.get("actual_attendance"),
                    "stadium_capacity": row.get("stadium_capacity"),
                }
                for row in holdout_events
            ],
        },
        "rules": {
            "new_holdouts_used_for_stage1_selection": False,
            "frozen_rows_selected_by_exact_contract_identity": True,
            "future_attendance_rows_removed_from_frozen_stage0_replay": True,
        },
    }
    return frozen_payload, split_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--attendance", type=Path, required=True)
    parser.add_argument("--sporting", type=Path, required=True)
    parser.add_argument("--aliases", type=Path, required=True)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--training-contract", type=Path, required=True)
    parser.add_argument("--output-frozen", type=Path, required=True)
    parser.add_argument("--output-split-manifest", type=Path, required=True)
    args = parser.parse_args()

    def load(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text())

    frozen, manifest = split_payload(
        events_export=load(args.events),
        attendance_export=load(args.attendance),
        sporting_export=load(args.sporting),
        aliases_export=load(args.aliases),
        live_export=load(args.live),
        training_contract=load(args.training_contract),
    )
    args.output_frozen.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
    args.output_split_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
