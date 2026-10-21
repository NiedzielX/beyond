#!/usr/bin/env python3
"""Audit additive d2 long-horizon export coverage and PIT integrity.

This is a data-contract/readiness gate, not a model-selection experiment.
The minimum independent-event threshold is inherited from the existing frozen
Stage-1 development set (9 events); it is not tuned from the new coverage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

EXPERIMENT = "d2-long-horizon-coverage-audit-v1"
EXPECTED_VERSION = "d2-long-horizon-168-rows-v1"
EXPECTED_WINDOW_HOURS = 168
EXPECTED_CADENCE_HOURS = 6
MIN_INDEPENDENT_EVENTS_FOR_LEARNED_WINDOW = 9


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    require(bool(payload.get("ok", True)), "export payload not ok")
    require(payload.get("version") == EXPECTED_VERSION, "unexpected export version")
    sampling = payload.get("sampling") or {}
    require(int(sampling.get("window_hours", -1)) == EXPECTED_WINDOW_HOURS, "window drift")
    require(int(sampling.get("cadence_hours", -1)) == EXPECTED_CADENCE_HOURS, "cadence drift")

    rows = list(payload.get("liveRows") or [])
    coverage = list(payload.get("coverage") or [])
    event_count = int(payload.get("eventCount") or 0)
    row_count = int(payload.get("liveRowCount") or 0)
    require(event_count >= 2, "too few events")
    require(row_count == len(rows), "liveRowCount mismatch")
    require(len(coverage) == event_count, "coverage count mismatch")

    normalized: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for row in rows:
        event_id = int(row["ticket_event_id"])
        bucket = int(row["bucket_6h"])
        hours = float(row["hours_to_kickoff"])
        features = row.get("features") or {}
        key = (event_id, bucket)
        require(key not in seen, f"duplicate event/bucket {key}")
        seen.add(key)
        require(0.0 < hours <= EXPECTED_WINDOW_HOURS, f"hours outside window {hours}")
        require(bool(features.get("point_in_time_validated")), f"PIT invalid event={event_id} bucket={bucket}")
        require(features.get("snapshot_id") is not None, f"missing feature snapshot event={event_id} bucket={bucket}")
        normalized.append({
            "ticket_event_id": event_id,
            "bucket_6h": bucket,
            "hours_to_kickoff": hours,
        })

    frame = pd.DataFrame(normalized)
    require(frame["ticket_event_id"].nunique() == event_count, "eventCount mismatch")

    coverage_by_id = {int(row["ticket_event_id"]): row for row in coverage}
    computed: list[dict[str, Any]] = []
    for event_id, group in frame.groupby("ticket_event_id", sort=True):
        c = coverage_by_id.get(int(event_id))
        require(c is not None, f"missing coverage event={event_id}")
        bands = {
            "rows_0_24h": int(((group.hours_to_kickoff >= 0) & (group.hours_to_kickoff <= 24)).sum()),
            "rows_24_48h": int(((group.hours_to_kickoff > 24) & (group.hours_to_kickoff <= 48)).sum()),
            "rows_48_72h": int(((group.hours_to_kickoff > 48) & (group.hours_to_kickoff <= 72)).sum()),
            "rows_72_168h": int(((group.hours_to_kickoff > 72) & (group.hours_to_kickoff <= 168)).sum()),
        }
        require(int(c["valid_row_count"]) == len(group), f"coverage row count mismatch event={event_id}")
        for name, value in bands.items():
            require(int(c[name]) == value, f"coverage band mismatch event={event_id} band={name}")
        computed.append({
            "ticket_event_id": int(event_id),
            "valid_row_count": int(len(group)),
            "earliest_hours_to_kickoff": float(group.hours_to_kickoff.max()),
            **bands,
        })

    events_gt24 = sum(row["rows_24_48h"] > 0 or row["rows_48_72h"] > 0 or row["rows_72_168h"] > 0 for row in computed)
    events_gt48 = sum(row["rows_48_72h"] > 0 or row["rows_72_168h"] > 0 for row in computed)
    events_gt72 = sum(row["rows_72_168h"] > 0 for row in computed)

    # Readiness uses a predeclared independent-event threshold inherited from
    # the existing frozen d2 Stage-1 development set (9 events).
    candidate_windows = [
        {"window_hours": 48, "eligible_events": events_gt24},
        {"window_hours": 72, "eligible_events": events_gt48},
        {"window_hours": 168, "eligible_events": events_gt72},
    ]
    ready = [
        row for row in candidate_windows
        if row["eligible_events"] >= MIN_INDEPENDENT_EVENTS_FOR_LEARNED_WINDOW
    ]
    max_ready_window = max((row["window_hours"] for row in ready), default=24)

    return {
        "experiment": EXPERIMENT,
        "status": "LONG_HORIZON_DATA_CONTRACT_READY",
        "model_training_performed": False,
        "export": {
            "version": EXPECTED_VERSION,
            "event_count": event_count,
            "live_row_count": row_count,
            "window_hours": EXPECTED_WINDOW_HOURS,
            "cadence_hours": EXPECTED_CADENCE_HOURS,
            "pit_rows_validated": True,
            "unique_event_bucket_rows": True,
        },
        "coverage": {
            "events_with_rows_beyond_24h": events_gt24,
            "events_with_rows_beyond_48h": events_gt48,
            "events_with_rows_beyond_72h": events_gt72,
            "events": computed,
        },
        "readiness": {
            "minimum_independent_events": MIN_INDEPENDENT_EVENTS_FOR_LEARNED_WINDOW,
            "threshold_source": "existing frozen d2 Stage-1 development event count",
            "candidate_windows": candidate_windows,
            "max_window_ready_for_learned_model_v1_hours": max_ready_window,
            "final168_early_band_status": (
                "READY_FOR_LEARNED_MODEL" if events_gt72 >= MIN_INDEPENDENT_EVENTS_FOR_LEARNED_WINDOW
                else "DIAGNOSTIC_ONLY_BELOW_EVENT_THRESHOLD"
            ),
        },
        "decision": (
            f"BUILD_FIRST_LONG_HORIZON_MODEL_TO_{max_ready_window}H"
            if max_ready_window > 24
            else "INSUFFICIENT_EARLY_EVENT_COVERAGE"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(json.loads(args.input.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "coverage": {k: v for k, v in result["coverage"].items() if k != "events"},
        "readiness": result["readiness"],
        "decision": result["decision"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
