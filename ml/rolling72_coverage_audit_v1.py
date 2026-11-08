"""Read-only coverage of cached public inventory; never fit or issue forecasts.

Rows describe retrospective capture-time label support, not historical knowledge
or prospective evidence. Source identity is weaker than a verified constant pool.
The six-hour match window is an explicit diagnostic copied from daily v1.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import timedelta
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ml.demand_engine.daily_inventory_path_dataset_v1 import canonical_hash, parse_timestamp

VERSION = "rolling72-cached-coverage-audit-v1"
HORIZONS_HOURS = (24, 48, 72)
TARGET_MAX_STALENESS_HOURS = 6
MATURITY_INTERVALS = (
    (50, float("inf"), "P50plus"), (30, 50, "P30_to_P50"),
    (15, 30, "P15_to_P30"), (7, 15, "P7_to_P15"),
    (3, 7, "P3_to_P7"), (0, 3, "P0_to_P3"),
)


def maturity_bucket(days: float) -> str:
    for lower, upper, label in MATURITY_INTERVALS:
        if lower <= days < upper:
            return label
    raise ValueError("Only pre-kickoff observations have a maturity bucket")


def _valid(row: dict) -> bool:
    value = row.get("available_total")
    return (
        not isinstance(value, bool) and isinstance(value, (int, float))
        and math.isfinite(value) and value >= 0
        and isinstance(row.get("measurement_key"), str)
        and bool(row["measurement_key"].strip())
        and all(row.get(flag) is None or isinstance(row[flag], bool)
                for flag in ("source_active", "source_visible"))
    )


def _hidden(row: dict) -> bool:
    return row.get("source_active") is False or row.get("source_visible") is False


def _box() -> dict:
    return {**dict.fromkeys(("issues", "mature", "matched", "pending", "past_kickoff",
                            "source_changed_prefix", "invalid_prefix", "hidden_prefix"), 0),
            "events": set(), "clubs": set()}


def _finish(box: dict) -> dict:
    return {key: len(value) if isinstance(value, set) else value for key, value in box.items()}


def _age_bucket(hours: float) -> str:
    return ("first_or_under1h" if hours < 1 else "1_to_24h" if hours < 24
            else "24_to_72h" if hours < 72 else "72hplus")


def audit_export(data: dict) -> dict:
    """Return aggregate support, preserving missingness and first observations.

    Sample the actual first pre-kickoff point plus the latest actual point in
    each UTC hour. Every selected point is a diagnostic issue coordinate, not a
    claim that a forecast was historically issued there. Reject an observed
    prefix after any invalid value, explicit hidden/inactive state or source
    identity change. Unknown flags remain unknown. A target is the latest
    actual reading no later than the nominal horizon, at most six hours old,
    strictly after its anchor and strictly before kickoff, with the same key.
    No target interpolation, clipping to kickoff, or historical writes occur.
    """
    if data.get("version") != "daily-inventory-public-export-v1":
        raise ValueError("Expected a daily-inventory-public-export-v1 cache")
    expected = canonical_hash({key: value for key, value in data.items() if key != "export_sha256"})
    if data.get("export_sha256") != expected:
        raise ValueError("Public export manifest hash mismatch")
    as_of = parse_timestamp(data["exported_at"])
    if parse_timestamp(data["retrieved_at"]) < as_of:
        raise ValueError("Retrieval receipt precedes export cutoff")
    events = data.get("events")
    if not isinstance(events, list):
        raise ValueError("Expected an events list")
    ids = [event["ticket_event_id"] for event in events]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate event identity")
    matrix, ages, first_support = defaultdict(_box), defaultdict(_box), defaultdict(_box)
    sources, flags, sector_counts = Counter(), Counter(), Counter()
    first_days, source_change_events = [], 0
    invalid_rows = zero_rows = snapshot_rows = sector_payload_rows = 0
    for event in events:
        kickoff = parse_timestamp(event["kickoff_at"])
        obs = sorted(event["observations"], key=lambda row: (
            parse_timestamp(row["captured_at"]), int(row["snapshot_id"])))
        snapshot_ids = [row["snapshot_id"] for row in obs]
        if len(set(snapshot_ids)) != len(snapshot_ids):
            raise ValueError("Duplicate snapshot identity in cached export")
        if any(parse_timestamp(row["captured_at"]) > as_of for row in obs):
            raise ValueError("Observation exceeds the declared export cutoff")
        snapshot_rows += len(obs)
        for row in obs:
            sources[str(row.get("source"))] += 1
            sector_counts[str(row.get("sector_count"))] += 1
            invalid_rows += not _valid(row)
            zero_rows += _valid(row) and row["available_total"] == 0
            sector_payload_rows += any(key in row for key in ("sectors", "sector_id", "sector_values"))
            for flag in ("source_active", "source_visible"):
                flags[flag + "/" + str(row.get(flag))] += 1
        pre = [row for row in obs if parse_timestamp(row["captured_at"]) < kickoff]
        if not pre:
            continue
        first = parse_timestamp(pre[0]["captured_at"])
        first_days.append((kickoff - first).total_seconds() / 86400)
        source_change_events += len({row.get("measurement_key") for row in pre}) > 1
        hourly = {}
        for row in pre:
            hourly[parse_timestamp(row["captured_at"]).replace(minute=0, second=0, microsecond=0)] = row
        selected = {int(pre[0]["snapshot_id"]): pre[0]}
        selected.update({int(row["snapshot_id"]): row for row in hourly.values()})
        times = [parse_timestamp(row["captured_at"]) for row in obs]
        cursor, keys, bad, hidden = 0, set(), False, False
        for anchor in sorted(selected.values(), key=lambda row: (
                parse_timestamp(row["captured_at"]), int(row["snapshot_id"]))):
            issued = parse_timestamp(anchor["captured_at"])
            while cursor < len(pre) and parse_timestamp(pre[cursor]["captured_at"]) <= issued:
                row = pre[cursor]
                keys.add(row.get("measurement_key"))
                bad |= not _valid(row)
                hidden |= _hidden(row)
                cursor += 1
            maturity = maturity_bucket((kickoff - issued).total_seconds() / 86400)
            age = _age_bucket((issued - first).total_seconds() / 3600)
            for horizon in HORIZONS_HOURS:
                target = issued + timedelta(hours=horizon)
                boxes = [matrix[(maturity, horizon)], ages[(age, horizon)]]
                if anchor["snapshot_id"] == pre[0]["snapshot_id"]:
                    boxes.append(first_support[horizon])
                for box in boxes:
                    box["issues"] += 1
                    if len(keys) != 1:
                        box["source_changed_prefix"] += 1
                        continue
                    if bad:
                        box["invalid_prefix"] += 1
                        continue
                    if hidden:
                        box["hidden_prefix"] += 1
                        continue
                    if target >= kickoff:
                        box["past_kickoff"] += 1
                        continue
                    if target > as_of:
                        box["pending"] += 1
                        continue
                    box["mature"] += 1
                    index = bisect_right(times, target) - 1
                    if index < 0:
                        continue
                    label, captured = obs[index], times[index]
                    if (captured <= issued or target - captured > timedelta(hours=TARGET_MAX_STALENESS_HOURS)
                            or not _valid(label) or _hidden(label)
                            or label["measurement_key"] != anchor.get("measurement_key")):
                        continue
                    box["matched"] += 1
                    box["events"].add(event["ticket_event_id"])
                    box["clubs"].add(event["club_slug"])
    totals = {}
    for horizon in HORIZONS_HOURS:
        boxes = [box for (_, lead), box in matrix.items() if lead == horizon]
        totals[str(horizon)] = {
            "matched": sum(box["matched"] for box in boxes),
            "events": len(set().union(*(box["events"] for box in boxes))),
            "clubs": len(set().union(*(box["clubs"] for box in boxes))),
        }
    return {
        "version": VERSION, "exported_at": data["exported_at"],
        "retrieved_at": data.get("retrieved_at"), "source_manifest_sha256": expected,
        "event_count": len(events), "club_count": len({event["club_slug"] for event in events}),
        "snapshot_rows": snapshot_rows, "invalid_rows": invalid_rows, "literal_zero_rows": zero_rows,
        "source_counts": dict(sources), "source_flag_counts": dict(flags),
        "events_with_measurement_changes": source_change_events,
        "sector_count_distribution": dict(sector_counts),
        "rows_with_sector_payload_fields": sector_payload_rows,
        "first_observation_statistics": {
            "events_with_pre_kickoff_observations": len(first_days),
            "events_first_seen_at_least_P50": sum(days >= 50 for days in first_days),
            "events_first_seen_at_least_P30": sum(days >= 30 for days in first_days),
            "earliest_tracking_days_before_kickoff": max(first_days, default=None),
        },
        "maturity_intervals_days": {label: [lower, upper if math.isfinite(upper) else None]
                                    for lower, upper, label in MATURITY_INTERVALS},
        "maturity_horizon_matrix": {f"{stage}/+{horizon}h": _finish(box)
                                    for (stage, horizon), box in sorted(matrix.items())},
        "prefix_age_horizon_matrix": {f"{age}/+{horizon}h": _finish(box)
                                      for (age, horizon), box in sorted(ages.items())},
        "first_observation_target_support": {str(horizon): _finish(first_support[horizon])
                                             for horizon in HORIZONS_HOURS},
        "per_horizon_support": totals,
        "evidence_kind": "historical_diagnostic_not_prospective",
        "target_max_staleness_hours": TARGET_MAX_STALENESS_HOURS,
        "sampling": "first genuine point plus latest genuine point per UTC hour",
        "historical_ingestion_known_at_proven": False,
        "stable_released_pool_verified": False, "sales_open_timestamp_proven": False,
        "production_change": False, "live_adjustment": 0,
        "limitations": [
            "Captured time is not historical ingestion-known-at; these are capture-time label matches.",
            "Current event kickoff metadata is not a historical revision ledger.",
            "A stable provider/source key does not verify constant released pool or paid sales/attendance.",
            "Unknown source flags remain unknown; sector_count is not a per-sector trajectory.",
            "A same-key target does not prove unchanged pool/source during the unobserved intervening interval.",
            "No sales-opening date is inferred from the first tracked observation.",
            "Exposed historical matches are not untouched holdouts or future issued forecasts.",
        ],
    }


def audit_cache(path: str | Path) -> dict:
    source = Path(path)
    payload = source.read_bytes()
    result = audit_export(json.loads(payload))
    result["source_path"] = str(source)
    result["source_file_sha256"] = hashlib.sha256(payload).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Existing private daily inventory export")
    parser.add_argument("--output", required=True, help="New aggregate diagnostic JSON (outside Git)")
    args = parser.parse_args()
    result = audit_cache(args.input)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": "DIAGNOSTIC_ONLY", "event_count": result["event_count"],
                      "snapshot_rows": result["snapshot_rows"], "production_change": False}))


if __name__ == "__main__":
    main()
