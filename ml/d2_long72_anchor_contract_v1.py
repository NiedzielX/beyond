#!/usr/bin/env python3
"""Build the fixed 0-72h live dataset with PIT Pre-Live checkpoint anchors.

No learned live model is fitted here. The script reconstructs all 2026/27
same-season home matches needed for the current-season residual state, resolves
capacity from the versioned registry at each kickoff date, replays T-3/T-1
Structural Prior + frozen b2, and then anchors each long-horizon live row to the
latest checkpoint available at its as-of timestamp:

    24h < h <= 72h -> T-3
     0h < h <= 24h -> T-1

Sealed Pre-Live v3 uses the exact v2 T-3/T-1 contracts, so this dataset is valid
for both v2 and v3 in the 0-72h window. The changed v3 T-7 contract is not used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.c1_alpha_model_tournament_v1 import (
    BOOLEAN_LIVE_FEATURES,
    NUMERIC_LIVE_FEATURES,
    _aliases,
    _event_prior_replay,
)
from ml.current_season_regime_fixed_temporal_audit_v1 import apply_fixed_policy
from ml.current_season_residual_regime_v1 import add_same_season_residual_state
from ml.d2_live_replay_anchor_v1 import _sporting_index
from ml.demand_engine.current_structural_prior_features import DEFAULT_KEY_ALIASES

EXPERIMENT = "d2-long72-anchor-contract-v1"
WINDOW_HOURS = 72.0
WARSAW_TZ = "Europe/Warsaw"
SYNTHETIC_EVENT_ID_BASE = 8_000_000
EXPECTED_LONG_EXPORT = "d2-long-horizon-168-rows-v1"
EXPECTED_CAPACITY_EXPORT = "d2-capacity-registry-v1"
EXPECTED_EVENT_EXPORT = "c1-alpha-v7-events-v1"
EXPECTED_ATTENDANCE_EXPORT = "c1-alpha-v7-attendance-v1"
EXPECTED_SPORTING_EXPORT = "c1-alpha-v7-sporting-v1"
EXPECTED_ALIAS_EXPORT = "c1-alpha-v7-aliases-v1"
EXPECTED_V2_FREEZE = "pre-live-v2-historical-candidate-2026-10-18-v1"
EXPECTED_V3_FREEZE = "pre-live-v3-historical-candidate-2026-10-21-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def canonical_club_key(value: str) -> str:
    raw = str(value)
    return str(DEFAULT_KEY_ALIASES.get(raw, raw))


def load_export(path: Path, expected_version: str) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if payload.get("ok") is False:
        raise RuntimeError(f"export not ok: {path}")
    if payload.get("version") != expected_version:
        raise RuntimeError(
            f"export version mismatch {path}: {payload.get('version')} != {expected_version}"
        )
    return payload


def resolve_capacity(
    capacity_rows: list[dict[str, Any]], club_key: str, kickoff: pd.Timestamp
) -> dict[str, Any]:
    local_date = kickoff.tz_convert(WARSAW_TZ).date()
    eligible: list[dict[str, Any]] = []
    for row in capacity_rows:
        if str(row["club_key"]) != club_key:
            continue
        valid_from = pd.Timestamp(row["valid_from"]).date()
        valid_to = pd.Timestamp(row["valid_to"]).date() if row.get("valid_to") else None
        if local_date < valid_from:
            continue
        if valid_to is not None and local_date > valid_to:
            continue
        eligible.append(row)
    if not eligible:
        raise RuntimeError(f"no capacity registry row club={club_key} kickoff={kickoff}")
    eligible.sort(key=lambda row: (str(row["valid_from"]), int(row["id"])))
    selected = eligible[-1]
    if int(selected["stadium_capacity"]) <= 0:
        raise RuntimeError(f"invalid capacity {selected}")
    return selected


def compose_context(
    events: dict[str, Any],
    attendance: dict[str, Any],
    sporting: dict[str, Any],
    aliases: dict[str, Any],
) -> dict[str, Any]:
    return {
        "events": list(events.get("events") or []),
        "attendance": list(attendance.get("attendance") or []),
        "sportingMatches": list(sporting.get("sportingMatches") or []),
        "aliases": list(aliases.get("aliases") or []),
    }


def build_replay_events(
    payload: dict[str, Any], capacity_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[int, float], dict[int, dict[str, Any]]]:
    aliases = _aliases(payload)
    sporting = _sporting_index(payload)
    tracked = {
        (str(row["home_club_key"]), utc(row["kickoff_at"])): row
        for row in payload.get("events") or []
    }

    replay_events: list[dict[str, Any]] = []
    actual_by_id: dict[int, float] = {}
    capacity_lineage: dict[int, dict[str, Any]] = {}
    synthetic_counter = 0

    attendance_rows = sorted(
        payload.get("attendance") or [], key=lambda row: utc(row["kickoff_at"])
    )
    for attendance in attendance_rows:
        slug = str(attendance["club_slug"])
        home_key = canonical_club_key(slug)
        kickoff = utc(attendance["kickoff_at"])
        cap = resolve_capacity(capacity_rows, home_key, kickoff)
        local_date = kickoff.tz_convert(WARSAW_TZ).date().isoformat()
        sporting_row = sporting.get((local_date, home_key))
        if sporting_row is None:
            raise RuntimeError(
                f"could not join attendance to sporting club={home_key} kickoff={kickoff}"
            )
        away_key = aliases.get(str(sporting_row["away_team"]))
        if away_key is None:
            raise RuntimeError(f"missing away alias {sporting_row['away_team']}")

        target = tracked.get((home_key, kickoff))
        if target is not None:
            event_id = int(target["ticket_event_id"])
            if int(target["stadium_capacity"]) != int(cap["stadium_capacity"]):
                raise RuntimeError(
                    f"target/registry capacity mismatch event={event_id} "
                    f"target={target['stadium_capacity']} registry={cap['stadium_capacity']}"
                )
        else:
            event_id = SYNTHETIC_EVENT_ID_BASE + synthetic_counter
            synthetic_counter += 1

        event = {
            "ticket_event_id": event_id,
            "club_slug": slug,
            "home_team": str(sporting_row["home_team"]),
            "away_team": str(sporting_row["away_team"]),
            "season": str(sporting_row["season"]).replace("-", "/"),
            "round_no": int(sporting_row["round_number"]),
            "kickoff_at": kickoff.isoformat(),
            "home_club_key": home_key,
            "away_club_key": str(away_key),
            "stadium_capacity": int(cap["stadium_capacity"]),
            "actual_attendance": float(attendance["actual_attendance"]),
        }
        replay_events.append(event)
        actual_by_id[event_id] = float(attendance["actual_attendance"])
        capacity_lineage[event_id] = {
            "club_key": home_key,
            "stadium_capacity": int(cap["stadium_capacity"]),
            "valid_from": cap["valid_from"],
            "valid_to": cap.get("valid_to"),
            "source_name": cap.get("source_name"),
            "source_url": cap.get("source_url"),
            "verification_status": cap.get("verification_status"),
        }

    tracked_ids = {int(row["ticket_event_id"]) for row in payload.get("events") or []}
    replay_tracked = {int(row["ticket_event_id"]) for row in replay_events if int(row["ticket_event_id"]) in tracked_ids}
    if replay_tracked != tracked_ids:
        raise RuntimeError(
            f"not all target events mapped into attendance history missing={sorted(tracked_ids-replay_tracked)}"
        )
    return replay_events, actual_by_id, capacity_lineage


def build_checkpoint_anchors(
    context: dict[str, Any],
    artifact_dir: Path,
    capacity_rows: list[dict[str, Any]],
) -> tuple[dict[tuple[int, str], dict[str, Any]], dict[str, Any]]:
    replay_events, actual_by_id, capacity_lineage = build_replay_events(
        context, capacity_rows
    )
    replay_payload = dict(context)
    replay_payload["events"] = replay_events
    priors = _event_prior_replay(replay_payload, artifact_dir)
    event_meta = {int(row["ticket_event_id"]): row for row in replay_events}
    anchor_map: dict[tuple[int, str], dict[str, Any]] = {}
    horizon_diag: dict[str, Any] = {}

    for horizon in ("T-3", "T-1"):
        subset = priors[(priors["horizon"] == horizon) & priors["prior_p50"].notna()].copy()
        if len(subset) != len(replay_events):
            missing = priors[(priors["horizon"] == horizon) & priors["prior_p50"].isna()][
                ["ticket_event_id", "prior_error"]
            ].to_dict("records")
            raise RuntimeError(
                f"not all replay events received {horizon} base prior "
                f"predicted={len(subset)} events={len(replay_events)} missing={missing}"
            )
        subset = subset.sort_values("ticket_event_id").reset_index(drop=True)
        rows: list[dict[str, Any]] = []
        base: list[float] = []
        for prior in subset.to_dict("records"):
            event_id = int(prior["ticket_event_id"])
            event = event_meta[event_id]
            rows.append({
                "match_key": f"d2-long72|{event_id}|{horizon}",
                "ticket_event_id": event_id,
                "season": event["season"],
                "home_club_key": event["home_club_key"],
                "away_club_key": event["away_club_key"],
                "as_of_at": utc(prior["target_as_of_at"]),
                "kickoff_at": utc(event["kickoff_at"]),
                "target_attendance": float(actual_by_id[event_id]),
                "capacity": float(event["stadium_capacity"]),
            })
            base.append(float(prior["prior_p50"]))
        state = pd.DataFrame(rows)
        base_arr = np.asarray(base, dtype=float)
        state = add_same_season_residual_state(state, base_arr)
        final, diag = apply_fixed_policy(state, base_arr, horizon)
        state["base_p50"] = base_arr
        state["anchor_p50"] = final
        state["b2_correction_seats"] = final - base_arr
        for row in state.to_dict("records"):
            event_id = int(row["ticket_event_id"])
            anchor_map[(event_id, horizon)] = {
                "anchor_p50": float(row["anchor_p50"]),
                "base_p50": float(row["base_p50"]),
                "b2_correction_seats": float(row["b2_correction_seats"]),
                "checkpoint_as_of_at": utc(row["as_of_at"]),
                "capacity_lineage": capacity_lineage[event_id],
            }
        horizon_diag[horizon] = diag
    return anchor_map, {
        "replay_event_count": len(replay_events),
        "target_event_count": len(context.get("events") or []),
        "attendance_row_count": len(context.get("attendance") or []),
        "horizon_diagnostics": horizon_diag,
    }


def build_long72_frame(
    context: dict[str, Any],
    long_export: dict[str, Any],
    anchor_map: dict[tuple[int, str], dict[str, Any]],
) -> pd.DataFrame:
    events = {int(row["ticket_event_id"]): row for row in context.get("events") or []}
    records: list[dict[str, Any]] = []
    for row in long_export.get("liveRows") or []:
        h = float(row["hours_to_kickoff"])
        if not (0.0 < h <= WINDOW_HOURS):
            continue
        event_id = int(row["ticket_event_id"])
        if event_id not in events:
            raise RuntimeError(f"long live row references unknown event {event_id}")
        event = events[event_id]
        f = dict(row.get("features") or {})
        if not bool(f.get("point_in_time_validated")) or f.get("snapshot_id") is None:
            raise RuntimeError(f"invalid PIT live row event={event_id}")
        as_of = utc(f.get("as_of_at") or row["requested_as_of_at"])
        horizon = "T-1" if h <= 24.0 else "T-3"
        anchor = anchor_map.get((event_id, horizon))
        if anchor is None:
            raise RuntimeError(f"missing {horizon} anchor event={event_id}")
        if anchor["checkpoint_as_of_at"] > as_of:
            raise RuntimeError(
                f"future checkpoint used event={event_id} h={h} "
                f"checkpoint={anchor['checkpoint_as_of_at']} row={as_of}"
            )
        capacity = float(event["stadium_capacity"])
        actual = float(event["actual_attendance"])
        if int(anchor["capacity_lineage"]["stadium_capacity"]) != int(capacity):
            raise RuntimeError(f"anchor/live capacity mismatch event={event_id}")
        anchor_p50 = float(anchor["anchor_p50"])
        rec: dict[str, Any] = {
            "ticket_event_id": event_id,
            "club_slug": event["club_slug"],
            "home_team": event["home_team"],
            "away_team": event["away_team"],
            "kickoff_at": utc(event["kickoff_at"]),
            "as_of_at": as_of,
            "hours_to_kickoff": h,
            "bucket_6h": int(row["bucket_6h"]),
            "requested_snapshot_id": int(row["requested_snapshot_id"]),
            "feature_snapshot_id": int(f["snapshot_id"]),
            "anchor_horizon": horizon,
            "anchor_checkpoint_as_of_at": anchor["checkpoint_as_of_at"],
            "anchor_p50": anchor_p50,
            "anchor_base_p50": float(anchor["base_p50"]),
            "anchor_b2_correction_seats": float(anchor["b2_correction_seats"]),
            "stadium_capacity": capacity,
            "actual_attendance": actual,
            "target_live_delta_attendance": actual - anchor_p50,
            "target_live_delta_occupancy": actual / capacity - anchor_p50 / capacity,
            "anchor_expected_occupancy": anchor_p50 / capacity,
            "signal_ready": 1.0 if str(f.get("signal_readiness")) == "ready" else 0.0,
            "feature_quality_good": 1.0 if str(f.get("feature_quality")) in {"sector_matched_plus_raw", "raw_only"} else 0.0,
        }
        for key in NUMERIC_LIVE_FEATURES:
            rec[key] = pd.to_numeric(f.get(key), errors="coerce")
        for key in BOOLEAN_LIVE_FEATURES:
            value = f.get(key)
            rec[key] = np.nan if value is None else float(bool(value))
        records.append(rec)
    frame = pd.DataFrame(records)
    if frame.empty:
        raise RuntimeError("long72 frame is empty")
    frame = frame.sort_values(["ticket_event_id", "as_of_at"]).reset_index(drop=True)
    if frame.duplicated(["ticket_event_id", "bucket_6h"]).any():
        raise RuntimeError("duplicate event/bucket in long72 frame")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--attendance", type=Path, required=True)
    parser.add_argument("--sporting", type=Path, required=True)
    parser.add_argument("--aliases", type=Path, required=True)
    parser.add_argument("--capacity", type=Path, required=True)
    parser.add_argument("--long168", type=Path, required=True)
    parser.add_argument("--structural-artifact-dir", type=Path, required=True)
    parser.add_argument("--v2-manifest", type=Path, required=True)
    parser.add_argument("--v3-manifest", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    events = load_export(args.events, EXPECTED_EVENT_EXPORT)
    attendance = load_export(args.attendance, EXPECTED_ATTENDANCE_EXPORT)
    sporting = load_export(args.sporting, EXPECTED_SPORTING_EXPORT)
    aliases = load_export(args.aliases, EXPECTED_ALIAS_EXPORT)
    capacity = load_export(args.capacity, EXPECTED_CAPACITY_EXPORT)
    long168 = load_export(args.long168, EXPECTED_LONG_EXPORT)
    v2 = json.loads(args.v2_manifest.read_text())
    v3 = json.loads(args.v3_manifest.read_text())
    if v2.get("freeze_id") != EXPECTED_V2_FREEZE or v3.get("freeze_id") != EXPECTED_V3_FREEZE:
        raise RuntimeError("unexpected pre-live freeze lineage")
    for horizon in ("T-3", "T-1"):
        v2row = next(row for row in v2["horizons"] if row["horizon"] == horizon)
        v3row = next(row for row in v3["horizons"] if row["horizon"] == horizon)
        if v2row["contract"] != v3row["contract"]:
            raise RuntimeError(f"v2/v3 {horizon} contracts are not identical")

    context = compose_context(events, attendance, sporting, aliases)
    anchors, replay_diag = build_checkpoint_anchors(
        context, args.structural_artifact_dir, list(capacity.get("rows") or [])
    )
    frame = build_long72_frame(context, long168, anchors)

    event_count = int(frame["ticket_event_id"].nunique())
    rows_by_band = {
        "0_24h": int((frame["hours_to_kickoff"] <= 24).sum()),
        "24_48h": int(((frame["hours_to_kickoff"] > 24) & (frame["hours_to_kickoff"] <= 48)).sum()),
        "48_72h": int(((frame["hours_to_kickoff"] > 48) & (frame["hours_to_kickoff"] <= 72)).sum()),
    }
    events_by_band = {
        "0_24h": int(frame.loc[frame["hours_to_kickoff"] <= 24, "ticket_event_id"].nunique()),
        "24_48h": int(frame.loc[(frame["hours_to_kickoff"] > 24) & (frame["hours_to_kickoff"] <= 48), "ticket_event_id"].nunique()),
        "48_72h": int(frame.loc[(frame["hours_to_kickoff"] > 48) & (frame["hours_to_kickoff"] <= 72), "ticket_event_id"].nunique()),
    }
    if event_count != int(events["eventCount"]):
        raise RuntimeError(f"long72 event coverage drift {event_count} != {events['eventCount']}")
    if rows_by_band != {"0_24h": 50, "24_48h": 45, "48_72h": 35}:
        raise RuntimeError(f"unexpected long72 band row counts {rows_by_band}")
    if events_by_band["48_72h"] < 9:
        raise RuntimeError(f"48-72h independent event threshold failed {events_by_band}")

    result = {
        "experiment": EXPERIMENT,
        "status": "FROZEN_LONG72_DATA_AND_ANCHOR_CONTRACT",
        "model_training_performed": False,
        "production_change": False,
        "window_hours": 72,
        "anchor_rule": {
            "0_24h": "T-1 frozen Pre-Live checkpoint hold",
            "24_72h": "T-3 frozen Pre-Live checkpoint hold",
            "future_checkpoint_use_allowed": False,
            "v2_v3_equivalent_in_window": True,
        },
        "dataset": {
            "event_count": event_count,
            "row_count": int(len(frame)),
            "event_ids": sorted(int(v) for v in frame["ticket_event_id"].unique()),
            "rows_by_band": rows_by_band,
            "events_by_band": events_by_band,
            "min_hours_to_kickoff": float(frame["hours_to_kickoff"].min()),
            "max_hours_to_kickoff": float(frame["hours_to_kickoff"].max()),
        },
        "replay": replay_diag,
        "lineage": {
            "events_sha256": sha256_file(args.events),
            "attendance_sha256": sha256_file(args.attendance),
            "sporting_sha256": sha256_file(args.sporting),
            "aliases_sha256": sha256_file(args.aliases),
            "capacity_sha256": sha256_file(args.capacity),
            "long168_sha256": sha256_file(args.long168),
            "v2_manifest_sha256": sha256_file(args.v2_manifest),
            "v3_manifest_sha256": sha256_file(args.v3_manifest),
        },
        "next": "d2-long72-stage1-model-tournament-v1",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    frame.to_csv(args.output_csv, index=False)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
