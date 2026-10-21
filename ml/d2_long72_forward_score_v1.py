#!/usr/bin/env python3
"""Generate pre-outcome forward forecasts for the sealed long72 P2 package.

Package:
    d2-long72-stage2-p2-observation-maturity-2026-10-21-v1

Scope:
    24 < hours_to_kickoff <= 72

Formula:
    T-3 frozen Pre-Live anchor
      + P2 observation-maturity reliability
      * frozen inventory-linear-extrapolation delta

This module never reads target-event outcome labels. Historical attendance is
used only to reconstruct the already-frozen current-season T-3 residual regime.
The database writer independently rejects any target event whose outcome exists
at forecast-generation time.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.c1_alpha_model_tournament_v1 import _aliases, _event_prior_replay
from ml.current_season_regime_fixed_temporal_audit_v1 import apply_fixed_policy
from ml.current_season_residual_regime_v1 import add_same_season_residual_state
from ml.d2_live_replay_anchor_v1 import _sporting_index
from ml.d2_long72_anchor_contract_v1 import canonical_club_key, resolve_capacity
from ml.d2_long72_stage2_reliability_gating_v1 import maturity_reliability
from ml.d2_stage1_model_tournament_v1 import governed_forecast, inventory_linear_delta

PACKAGE_ID = "d2-long72-stage2-p2-observation-maturity-2026-10-21-v1"
PACKAGE_SOURCE_COMMIT = "a4f3bf0bdcfd1bb8897f23efc1a180314f5dfedb"
PACKAGE_MANIFEST_BLOB_SHA = "6dcce985c4467b261359923766c613d1b6278d40"
PACKAGE_FREEZE_CUTOFF = pd.Timestamp("2026-10-21T17:37:07Z")
EXPECTED_FORWARD_VERSION = "d2-long72-forward-rows-v1"
EXPECTED_ATTENDANCE_VERSION = "c1-alpha-v7-attendance-v1"
EXPECTED_SPORTING_VERSION = "c1-alpha-v7-sporting-v1"
EXPECTED_ALIAS_VERSION = "c1-alpha-v7-aliases-v1"
EXPECTED_CAPACITY_VERSION = "d2-capacity-registry-v1"
EXPECTED_V2_FREEZE = "pre-live-v2-historical-candidate-2026-10-18-v1"
EXPECTED_V3_FREEZE = "pre-live-v3-historical-candidate-2026-10-21-v1"
SYNTHETIC_EVENT_ID_BASE = 9_000_000


def utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_export(path: Path, expected_version: str) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("ok") is False:
        raise RuntimeError(f"export not ok: {path}: {payload.get('error')}")
    if payload.get("version") != expected_version:
        raise RuntimeError(
            f"export version mismatch {path}: {payload.get('version')} != {expected_version}"
        )
    return payload


def compose_context(
    forward: dict[str, Any],
    attendance: dict[str, Any],
    sporting: dict[str, Any],
    aliases: dict[str, Any],
) -> dict[str, Any]:
    events = list(forward.get("events") or [])
    event_ids = {int(row["ticket_event_id"]) for row in events}
    attendance_rows = list(attendance.get("attendance") or [])

    # Target-event outcomes are forbidden. If one of the future target IDs has
    # somehow entered historical attendance, fail closed instead of scoring.
    event_key = {
        (
            str(row["club_slug"]),
            utc(row["kickoff_at"]),
        )
        for row in events
    }
    leaked = [
        row
        for row in attendance_rows
        if (str(row.get("club_slug")), utc(row.get("kickoff_at"))) in event_key
    ]
    if leaked:
        raise RuntimeError(
            f"target-event outcome leaked into attendance context: "
            f"{[(row.get('club_slug'), row.get('kickoff_at')) for row in leaked]}"
        )

    return {
        "events": events,
        "attendance": attendance_rows,
        "sportingMatches": list(sporting.get("sportingMatches") or []),
        "aliases": list(aliases.get("aliases") or []),
        "target_event_ids": sorted(event_ids),
    }


def build_historical_replay_events(
    context: dict[str, Any],
    capacity_rows: list[dict[str, Any]],
    *,
    before_kickoff: pd.Timestamp,
) -> tuple[list[dict[str, Any]], dict[int, float]]:
    aliases = _aliases(context)
    sporting = _sporting_index(context)
    replay_events: list[dict[str, Any]] = []
    actual_by_id: dict[int, float] = {}
    counter = 0

    attendance_rows = sorted(
        context.get("attendance") or [], key=lambda row: utc(row["kickoff_at"])
    )
    for attendance in attendance_rows:
        kickoff = utc(attendance["kickoff_at"])
        if kickoff >= before_kickoff:
            continue
        slug = str(attendance["club_slug"])
        home_key = canonical_club_key(slug)
        local_date = kickoff.tz_convert("Europe/Warsaw").date().isoformat()
        sporting_row = sporting.get((local_date, home_key))
        if sporting_row is None:
            raise RuntimeError(
                f"could not join historical attendance to sporting state "
                f"club={home_key} kickoff={kickoff}"
            )
        away_key = aliases.get(str(sporting_row["away_team"]))
        if away_key is None:
            raise RuntimeError(f"missing away alias {sporting_row['away_team']}")
        capacity = resolve_capacity(capacity_rows, home_key, kickoff)
        event_id = SYNTHETIC_EVENT_ID_BASE + counter
        counter += 1
        replay_events.append(
            {
                "ticket_event_id": event_id,
                "club_slug": slug,
                "home_team": str(sporting_row["home_team"]),
                "away_team": str(sporting_row["away_team"]),
                "season": str(sporting_row["season"]).replace("-", "/"),
                "round_no": int(sporting_row["round_number"]),
                "kickoff_at": kickoff.isoformat(),
                "home_club_key": home_key,
                "away_club_key": str(away_key),
                "stadium_capacity": int(capacity["stadium_capacity"]),
            }
        )
        actual_by_id[event_id] = float(attendance["actual_attendance"])
    return replay_events, actual_by_id


def build_t3_anchor(
    context: dict[str, Any],
    target_event: dict[str, Any],
    capacity_rows: list[dict[str, Any]],
    artifact_dir: Path,
) -> dict[str, Any]:
    target_id = int(target_event["ticket_event_id"])
    target_kickoff = utc(target_event["kickoff_at"])
    target_as_of = target_kickoff - pd.Timedelta(days=3)
    if target_as_of < PACKAGE_FREEZE_CUTOFF and target_kickoff <= PACKAGE_FREEZE_CUTOFF:
        raise RuntimeError("target event is not post-package-freeze")

    historical_events, actual_by_id = build_historical_replay_events(
        context,
        capacity_rows,
        before_kickoff=target_kickoff,
    )
    target_replay = {
        "ticket_event_id": target_id,
        "club_slug": str(target_event["club_slug"]),
        "home_team": str(target_event["home_team"]),
        "away_team": str(target_event["away_team"]),
        "season": str(target_event["season"]),
        "round_no": int(target_event["round_no"]),
        "kickoff_at": target_kickoff.isoformat(),
        "home_club_key": str(target_event["home_club_key"]),
        "away_club_key": str(target_event["away_club_key"]),
        "stadium_capacity": int(target_event["stadium_capacity"]),
    }

    replay_payload = dict(context)
    replay_payload["events"] = [*historical_events, target_replay]
    priors = _event_prior_replay(replay_payload, artifact_dir)
    t3 = priors[(priors["horizon"] == "T-3") & priors["prior_p50"].notna()].copy()
    if t3.empty:
        raise RuntimeError(f"no T-3 priors available for target event={target_id}")

    target_prior = t3[t3["ticket_event_id"].astype(int) == target_id]
    if len(target_prior) != 1:
        error = priors[
            (priors["horizon"] == "T-3")
            & (priors["ticket_event_id"].astype(int) == target_id)
        ][["prior_error"]].to_dict("records")
        raise RuntimeError(
            f"target T-3 prior unavailable event={target_id} errors={error}"
        )

    rows: list[dict[str, Any]] = []
    bases: list[float] = []
    event_meta = {
        int(row["ticket_event_id"]): row
        for row in [*historical_events, target_replay]
    }
    for prior in t3.sort_values("ticket_event_id").to_dict("records"):
        event_id = int(prior["ticket_event_id"])
        event = event_meta[event_id]
        base_p50 = float(prior["prior_p50"])
        rows.append(
            {
                "match_key": f"d2-long72-forward|{target_id}|{event_id}|T-3",
                "ticket_event_id": event_id,
                "season": str(event["season"]),
                "home_club_key": str(event["home_club_key"]),
                "away_club_key": str(event["away_club_key"]),
                "as_of_at": utc(prior["target_as_of_at"]),
                "kickoff_at": utc(event["kickoff_at"]),
                # Target label is deliberately synthetic and can never enter its
                # own PIT state because completion is after the target T-3 as-of.
                "target_attendance": (
                    float(actual_by_id[event_id]) if event_id in actual_by_id else base_p50
                ),
                "capacity": float(event["stadium_capacity"]),
            }
        )
        bases.append(base_p50)

    state = pd.DataFrame(rows)
    base_array = np.asarray(bases, dtype=float)
    state = add_same_season_residual_state(state, base_array)
    final, diagnostics = apply_fixed_policy(state, base_array, "T-3")
    state["base_p50"] = base_array
    state["anchor_p50"] = final
    state["b2_correction_seats"] = final - base_array

    target_state = state[state["ticket_event_id"].astype(int) == target_id]
    if len(target_state) != 1:
        raise RuntimeError(f"target T-3 state missing event={target_id}")
    row = target_state.iloc[0]
    if utc(row["as_of_at"]) != target_as_of:
        raise RuntimeError(
            f"target T-3 checkpoint drift event={target_id}: "
            f"{row['as_of_at']} != {target_as_of}"
        )
    return {
        "ticket_event_id": target_id,
        "checkpoint_as_of_at": target_as_of.isoformat(),
        "base_p50": float(row["base_p50"]),
        "anchor_p50": float(row["anchor_p50"]),
        "b2_correction_seats": float(row["b2_correction_seats"]),
        "regime_prior_home_matches": int(row["regime_prior_home_matches"]),
        "regime_ewma_residual_fraction": float(row["regime_ewma_residual_fraction"]),
        "b2_diagnostics": diagnostics,
    }


def build_live_feature_frame(
    event: dict[str, Any],
    live_rows: list[dict[str, Any]],
    anchor: dict[str, Any],
) -> pd.DataFrame:
    capacity = float(event["stadium_capacity"])
    anchor_p50 = float(anchor["anchor_p50"])
    records: list[dict[str, Any]] = []
    for row in live_rows:
        features = dict(row.get("features") or {})
        as_of = utc(features.get("as_of_at") or row["requested_as_of_at"])
        snapshot_id = int(features.get("snapshot_id") or row["requested_snapshot_id"])
        hours = float(row["hours_to_kickoff"])
        if not (24.0 < hours <= 72.0):
            raise RuntimeError(f"live row outside sealed scope event={event['ticket_event_id']} h={hours}")
        if as_of < PACKAGE_FREEZE_CUTOFF:
            raise RuntimeError("live row predates package freeze cutoff")
        if utc(anchor["checkpoint_as_of_at"]) > as_of:
            raise RuntimeError("future T-3 checkpoint would be used")
        if not bool(features.get("point_in_time_validated")):
            raise RuntimeError("live row is not PIT validated")
        records.append(
            {
                "ticket_event_id": int(event["ticket_event_id"]),
                "club_slug": str(event["club_slug"]),
                "home_team": str(event["home_team"]),
                "away_team": str(event["away_team"]),
                "kickoff_at": utc(event["kickoff_at"]),
                "as_of_at": as_of,
                "hours_to_kickoff": hours,
                "bucket_6h": int(row["bucket_6h"]),
                "requested_snapshot_id": int(row["requested_snapshot_id"]),
                "feature_snapshot_id": snapshot_id,
                "stadium_capacity": capacity,
                "anchor_p50": anchor_p50,
                "frozen_v2_expected_occupancy": anchor_p50 / capacity,
                "anchor_expected_occupancy": anchor_p50 / capacity,
                **features,
            }
        )
    frame = pd.DataFrame(records).sort_values("as_of_at").reset_index(drop=True)
    frame["stage2_observation_index"] = np.arange(1, len(frame) + 1, dtype=int)
    return frame


def score_event(
    event: dict[str, Any],
    live_rows: list[dict[str, Any]],
    anchor: dict[str, Any],
    generated_at: pd.Timestamp,
) -> list[dict[str, Any]]:
    frame = build_live_feature_frame(event, live_rows, anchor)
    if frame.empty:
        return []

    raw_delta = inventory_linear_delta(frame)
    stage1_forecast, governed_delta = governed_forecast(frame, raw_delta)
    frame["governed_delta_occupancy"] = governed_delta
    reliability = maturity_reliability(frame)
    capacity = frame["stadium_capacity"].astype(float).to_numpy()
    anchor_p50 = frame["anchor_p50"].astype(float).to_numpy()
    final_p50 = np.clip(anchor_p50 + reliability * governed_delta * capacity, 0.0, capacity)

    observations: list[dict[str, Any]] = []
    for idx, row in frame.iterrows():
        features = row.to_dict()
        as_of = utc(row["as_of_at"])
        kickoff = utc(event["kickoff_at"])
        if generated_at < as_of or generated_at >= kickoff:
            raise RuntimeError(
                f"forecast generation time invalid event={event['ticket_event_id']} "
                f"generated={generated_at} as_of={as_of} kickoff={kickoff}"
            )
        obs_index = int(row["stage2_observation_index"])
        hours = float(row["hours_to_kickoff"])
        observation_weight = 0.25 if obs_index == 1 else 0.60 if obs_index == 2 else 1.0
        time_weight = 0.75 if hours > 60.0 else 0.90 if hours > 48.0 else 1.0
        rel = float(reliability[idx])
        if not np.isclose(rel, min(observation_weight, time_weight), rtol=0.0, atol=1e-12):
            raise RuntimeError("P2 reliability drift")

        def scalar(name: str) -> Any:
            value = features.get(name)
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return None
            if isinstance(value, (np.integer, np.floating)):
                return value.item()
            return value

        observations.append(
            {
                "ticket_event_id": int(event["ticket_event_id"]),
                "source_snapshot_id": int(row["feature_snapshot_id"]),
                "forecast_generated_at": generated_at.isoformat(),
                "source_snapshot_captured_at": as_of.isoformat(),
                "hours_to_kickoff": hours,
                "model_version": PACKAGE_ID,
                "forecast_status": "shadow",
                "correction_status": "frozen_long72_p2_research",
                "signal_readiness": scalar("signal_readiness"),
                "live_available_total": scalar("available_total"),
                "live_first_available_total": scalar("first_available_total"),
                "live_available_index": scalar("available_index"),
                "live_net_removed_since_first": scalar("net_removed_since_first"),
                "live_net_removed_since_previous": scalar("net_removed_since_previous"),
                "live_velocity_since_previous": scalar("velocity_since_previous"),
                "live_net_removed_6h": scalar("net_removed_6h"),
                "live_velocity_6h": scalar("velocity_6h"),
                "live_net_removed_24h": scalar("net_removed_24h"),
                "live_velocity_24h": scalar("velocity_24h"),
                "live_acceleration_6h_vs_24h": scalar("acceleration_6h_vs_24h"),
                "live_raw_snapshot_count": scalar("raw_snapshot_count"),
                "live_clean_snapshot_count": scalar("clean_snapshot_count"),
                "live_excluded_anomaly_count": scalar("excluded_anomaly_count"),
                "payload": {
                    "package_id": PACKAGE_ID,
                    "package_source_commit": PACKAGE_SOURCE_COMMIT,
                    "package_manifest_blob_sha": PACKAGE_MANIFEST_BLOB_SHA,
                    "package_freeze_cutoff_at": PACKAGE_FREEZE_CUTOFF.isoformat(),
                    "evidence_state_at_generation": "TRUE_POST_FREEZE_PROSPECTIVE_PENDING_OUTCOME",
                    "production_change": False,
                    "kickoff_at": kickoff.isoformat(),
                    "stadium_capacity": int(event["stadium_capacity"]),
                    "capacity_verification_status": event.get("capacity_verification_status"),
                    "bucket_6h": int(row["bucket_6h"]),
                    "feature_snapshot_id": int(row["feature_snapshot_id"]),
                    "anchor_horizon": "T-3",
                    "anchor_checkpoint_as_of_at": anchor["checkpoint_as_of_at"],
                    "anchor_base_p50": float(anchor["base_p50"]),
                    "anchor_b2_correction_seats": float(anchor["b2_correction_seats"]),
                    "anchor_p50": float(anchor["anchor_p50"]),
                    "regime_prior_home_matches": int(anchor["regime_prior_home_matches"]),
                    "regime_ewma_residual_fraction": float(anchor["regime_ewma_residual_fraction"]),
                    "raw_inventory_delta_occupancy": float(raw_delta[idx]),
                    "stage1_forecast_p50": float(stage1_forecast[idx]),
                    "governed_delta_occupancy": float(governed_delta[idx]),
                    "stage2_observation_index": obs_index,
                    "p2_observation_weight": observation_weight,
                    "p2_time_weight": time_weight,
                    "reliability": rel,
                    "applied_delta_occupancy": float(rel * governed_delta[idx]),
                    "final_p50": float(final_p50[idx]),
                },
            }
        )
    return observations


def run_forward(
    forward: dict[str, Any],
    attendance: dict[str, Any],
    sporting: dict[str, Any],
    aliases: dict[str, Any],
    capacity: dict[str, Any],
    artifact_dir: Path,
    v2_manifest: dict[str, Any],
    v3_manifest: dict[str, Any],
    generated_at: pd.Timestamp,
) -> dict[str, Any]:
    if forward.get("packageId") != PACKAGE_ID:
        raise RuntimeError("forward export package mismatch")
    if forward.get("outcomeAccessAllowed") is not False:
        raise RuntimeError("forward export is not outcome-free")
    if utc(forward.get("packageFreezeCutoffAt")) != PACKAGE_FREEZE_CUTOFF:
        raise RuntimeError("forward export freeze cutoff drift")
    if v2_manifest.get("freeze_id") != EXPECTED_V2_FREEZE:
        raise RuntimeError("unexpected v2 freeze")
    if v3_manifest.get("freeze_id") != EXPECTED_V3_FREEZE:
        raise RuntimeError("unexpected v3 freeze")
    v2_t3 = next(row for row in v2_manifest["horizons"] if row["horizon"] == "T-3")
    v3_t3 = next(row for row in v3_manifest["horizons"] if row["horizon"] == "T-3")
    if v2_t3["contract"] != v3_t3["contract"]:
        raise RuntimeError("v2/v3 T-3 anchor contract drift")

    context = compose_context(forward, attendance, sporting, aliases)
    events = {int(row["ticket_event_id"]): row for row in forward.get("events") or []}
    live_by_event: dict[int, list[dict[str, Any]]] = {}
    for row in forward.get("liveRows") or []:
        live_by_event.setdefault(int(row["ticket_event_id"]), []).append(row)

    if len(events) != int(forward.get("eventCount") or 0):
        raise RuntimeError("forward eventCount mismatch")
    if sum(len(rows) for rows in live_by_event.values()) != int(forward.get("liveRowCount") or 0):
        raise RuntimeError("forward liveRowCount mismatch")

    observations: list[dict[str, Any]] = []
    anchor_evidence: list[dict[str, Any]] = []
    capacity_rows = list(capacity.get("rows") or [])
    for event_id in sorted(events):
        event = events[event_id]
        rows = live_by_event.get(event_id, [])
        if not rows:
            continue
        anchor = build_t3_anchor(context, event, capacity_rows, artifact_dir)
        anchor_evidence.append(anchor)
        observations.extend(score_event(event, rows, anchor, generated_at))

    return {
        "experiment": "d2-long72-forward-score-v1",
        "status": "FORWARD_ROWS_READY" if observations else "NO_FORWARD_ROWS",
        "package_id": PACKAGE_ID,
        "package_source_commit": PACKAGE_SOURCE_COMMIT,
        "package_manifest_blob_sha": PACKAGE_MANIFEST_BLOB_SHA,
        "package_freeze_cutoff_at": PACKAGE_FREEZE_CUTOFF.isoformat(),
        "generated_at": generated_at.isoformat(),
        "production_change": False,
        "outcome_access_allowed": False,
        "event_count": len({int(row["ticket_event_id"]) for row in observations}),
        "observation_count": len(observations),
        "target_event_ids": sorted({int(row["ticket_event_id"]) for row in observations}),
        "anchors": anchor_evidence,
        "observations": observations,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--attendance", type=Path, required=True)
    parser.add_argument("--sporting", type=Path, required=True)
    parser.add_argument("--aliases", type=Path, required=True)
    parser.add_argument("--capacity", type=Path, required=True)
    parser.add_argument("--structural-artifact-dir", type=Path, required=True)
    parser.add_argument("--v2-manifest", type=Path, required=True)
    parser.add_argument("--v3-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--generated-at", type=str, default=None)
    args = parser.parse_args()

    forward = load_export(args.forward, EXPECTED_FORWARD_VERSION)
    attendance = load_export(args.attendance, EXPECTED_ATTENDANCE_VERSION)
    sporting = load_export(args.sporting, EXPECTED_SPORTING_VERSION)
    aliases = load_export(args.aliases, EXPECTED_ALIAS_VERSION)
    capacity = load_export(args.capacity, EXPECTED_CAPACITY_VERSION)
    generated_at = utc(args.generated_at) if args.generated_at else pd.Timestamp.now(tz="UTC")

    result = run_forward(
        forward,
        attendance,
        sporting,
        aliases,
        capacity,
        args.structural_artifact_dir,
        load_json(args.v2_manifest),
        load_json(args.v3_manifest),
        generated_at,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "event_count": result["event_count"],
                "observation_count": result["observation_count"],
                "target_event_ids": result["target_event_ids"],
                "package_id": result["package_id"],
                "production_change": result["production_change"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
