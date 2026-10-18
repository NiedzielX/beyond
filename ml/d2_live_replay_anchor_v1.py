#!/usr/bin/env python3
"""d2 Stage 0: rebuild the existing C1 live replay on the frozen Pre-Live v2 anchor.

No learned d2 model is fitted here.

The script intentionally reuses the existing C1 v7 split payload and its
30-row final-24h training contract. It replaces only the prior layer:

    legacy Structural Prior T-1
        -> frozen Pre-Live v2 T-1
           = same T-1 historical base + frozen b2 current-season regime.

The frozen b2 policy is replayed from point-in-time-safe same-season home-match
residuals. For the existing nine-event C1 training set, capacity stability is
sealed by a committed audit snapshot. Future/uncovered event capacity lineage
must not be silently inferred from this audit.
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
    _aliases,
    _event_prior_replay,
    _training_frame,
)
from ml.current_season_regime_fixed_temporal_audit_v1 import apply_fixed_policy
from ml.current_season_residual_regime_v1 import add_same_season_residual_state
from ml.demand_engine.current_structural_prior_features import DEFAULT_KEY_ALIASES

EXPERIMENT = "d2-live-replay-anchor-v1"
STAGE = "d2-stage0-frozen-v2-anchor-compatibility"
EXPECTED_FREEZE_ID = "pre-live-v2-historical-candidate-2026-10-18-v1"
EXPECTED_FREEZE_MANIFEST_SHA256 = (
    "44c911d1ac8b1bf6870ed31e1a636b9b8374d8c8da2d57ba3b4fb5b4aaba4d3c"
)
EXPECTED_C1_EVENT_IDS = (1, 3, 4, 8, 9, 12, 13, 14, 17)
EXPECTED_C1_EVENT_COUNT = 9
EXPECTED_C1_LIVE_ROWS = 30
EXPECTED_C1_PACKAGE = "c1-shadow-v8-frozen-2026-10-16-n9"
EXPECTED_C1_CONTRACT_VERSION = "c1-shadow-v8-training-contract-v1"
BASE_REPRO_ATOL = 1e-9
WARSAW_TZ = "Europe/Warsaw"
SYNTHETIC_EVENT_ID_BASE = 9_000_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_timestamp(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def canonical_club_key(slug: str) -> str:
    return str(DEFAULT_KEY_ALIASES.get(str(slug), str(slug)))


def load_and_verify_freeze_manifest(path: Path) -> dict[str, Any]:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_FREEZE_MANIFEST_SHA256:
        raise RuntimeError(
            f"frozen Pre-Live v2 manifest SHA mismatch actual={actual_sha} "
            f"expected={EXPECTED_FREEZE_MANIFEST_SHA256}"
        )
    manifest = json.loads(path.read_text())
    if manifest.get("freeze_id") != EXPECTED_FREEZE_ID:
        raise RuntimeError(
            f"unexpected freeze_id {manifest.get('freeze_id')} != {EXPECTED_FREEZE_ID}"
        )
    t1 = next(row for row in manifest["horizons"] if row["horizon"] == "T-1")
    expected_b2 = "ewma50-resid-k6-cap05-min3"
    if t1["contract"]["current_season_regime"] != expected_b2:
        raise RuntimeError("frozen T-1 b2 contract changed")
    if t1["contract"]["historical_context_extension"] != "NO_CONTEXT":
        raise RuntimeError("d2 Stage 0 expects no frozen historical c2 extension at T-1")
    return manifest


def load_capacity_audit(path: Path) -> dict[str, Any]:
    audit = json.loads(path.read_text())
    if audit.get("audit_version") != "d2-stage0-capacity-stability-audit-2026-10-18-v1":
        raise RuntimeError("unexpected d2 capacity audit version")
    if audit.get("season") != "2026/2027":
        raise RuntimeError("capacity audit season changed")
    for slug, row in audit.get("clubs", {}).items():
        if int(row["distinct_capacities"]) != 1 or int(row["missing_capacity_rows"]) != 0:
            raise RuntimeError(f"capacity audit is not stable for {slug}: {row}")
        if int(row["capacity"]) <= 0:
            raise RuntimeError(f"invalid audited capacity for {slug}")
    return audit


def verify_c1_contract(payload: dict[str, Any], contract_path: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text())
    if contract.get("contract_version") != EXPECTED_C1_CONTRACT_VERSION:
        raise RuntimeError("unexpected C1 training contract version")
    if contract.get("package_version") != EXPECTED_C1_PACKAGE:
        raise RuntimeError("unexpected C1 package version")

    rows = contract.get("rows") or []
    if len(rows) != EXPECTED_C1_LIVE_ROWS:
        raise RuntimeError(f"C1 committed rows changed: {len(rows)}")
    event_ids = tuple(sorted({int(row["ticket_event_id"]) for row in rows}))
    if event_ids != EXPECTED_C1_EVENT_IDS:
        raise RuntimeError(f"C1 committed event set changed: {event_ids}")

    live_rows = payload.get("liveRows") or []
    actual_keys = {
        (
            int(row["ticket_event_id"]),
            utc_timestamp(
                (row.get("features") or {}).get("as_of_at")
                or row.get("requested_as_of_at")
            ).isoformat(),
        )
        for row in live_rows
    }
    expected_keys = {
        (int(row["ticket_event_id"]), utc_timestamp(row["as_of_at"]).isoformat())
        for row in rows
    }
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        raise RuntimeError(
            f"live-row identity drift vs frozen C1 contract missing={missing} extra={extra}"
        )
    if len(live_rows) != EXPECTED_C1_LIVE_ROWS:
        raise RuntimeError(f"C1 payload live rows changed: {len(live_rows)}")

    events = {int(row["ticket_event_id"]): row for row in payload.get("events") or []}
    if tuple(sorted(events)) != EXPECTED_C1_EVENT_IDS:
        raise RuntimeError(f"C1 payload event set changed: {tuple(sorted(events))}")

    contract_actual: dict[int, float] = {}
    for row in rows:
        event_id = int(row["ticket_event_id"])
        actual = float(row["actual_attendance"])
        previous = contract_actual.setdefault(event_id, actual)
        if not np.isclose(previous, actual, rtol=0.0, atol=0.0):
            raise RuntimeError(f"C1 contract actual attendance varies within event {event_id}")
    for event_id, actual in contract_actual.items():
        payload_actual = float(events[event_id]["actual_attendance"])
        if not np.isclose(actual, payload_actual, rtol=0.0, atol=0.0):
            raise RuntimeError(
                f"C1 event outcome drift event={event_id} contract={actual} payload={payload_actual}"
            )
    return contract


def _sporting_index(payload: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    aliases = _aliases(payload)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in payload.get("sportingMatches") or []:
        home_key = aliases.get(str(row.get("home_team")))
        away_key = aliases.get(str(row.get("away_team")))
        event_date = str(row.get("event_date"))
        if home_key is None or away_key is None or not event_date:
            continue
        grouped.setdefault((event_date, home_key), []).append(row)

    result: dict[tuple[str, str], dict[str, Any]] = {}
    for key, rows in grouped.items():
        def sort_key(row: dict[str, Any]) -> str:
            return str(row.get("fetched_at") or "")
        ordered = sorted(rows, key=sort_key)
        latest = ordered[-1]
        semantic = {
            (
                str(row.get("season")),
                int(row.get("round_number")),
                aliases.get(str(row.get("away_team"))),
            )
            for row in rows
        }
        if len(semantic) != 1:
            raise RuntimeError(f"conflicting sporting shadow rows for {key}: {semantic}")
        result[key] = latest
    return result


def build_replay_events(
    payload: dict[str, Any],
    capacity_audit: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[int, float]]:
    aliases = _aliases(payload)
    sporting = _sporting_index(payload)
    tracked = {
        (
            canonical_club_key(str(row["club_slug"])),
            utc_timestamp(row["kickoff_at"]),
        ): row
        for row in payload.get("events") or []
    }

    attendance_rows = sorted(
        payload.get("attendance") or [],
        key=lambda row: utc_timestamp(row["kickoff_at"]),
    )
    by_slug_count: dict[str, int] = {}
    for row in attendance_rows:
        slug = str(row["club_slug"])
        if slug in capacity_audit["clubs"]:
            by_slug_count[slug] = by_slug_count.get(slug, 0) + 1
    for slug, audit in capacity_audit["clubs"].items():
        if by_slug_count.get(slug, 0) != int(audit["attendance_rows"]):
            raise RuntimeError(
                f"attendance-row count drift for {slug}: "
                f"payload={by_slug_count.get(slug, 0)} audit={audit['attendance_rows']}"
            )

    replay_events: list[dict[str, Any]] = []
    actual_by_id: dict[int, float] = {}
    synthetic_counter = 0
    for attendance in attendance_rows:
        slug = str(attendance["club_slug"])
        if slug not in capacity_audit["clubs"]:
            continue
        home_key = canonical_club_key(slug)
        audit = capacity_audit["clubs"][slug]
        if str(audit["club_key"]) != home_key:
            raise RuntimeError(f"capacity audit club key mismatch for {slug}")
        kickoff = utc_timestamp(attendance["kickoff_at"])
        local_date = kickoff.tz_convert(WARSAW_TZ).date().isoformat()
        match = sporting.get((local_date, home_key))
        if match is None:
            raise RuntimeError(
                f"could not join attendance to sporting row slug={slug} kickoff={kickoff}"
            )
        away_key = aliases.get(str(match["away_team"]))
        if away_key is None:
            raise RuntimeError(f"missing away alias for {match['away_team']}")

        tracked_event = tracked.get((home_key, kickoff))
        if tracked_event is not None:
            event_id = int(tracked_event["ticket_event_id"])
            target_capacity = int(tracked_event["stadium_capacity"])
            if target_capacity != int(audit["capacity"]):
                raise RuntimeError(
                    f"tracked-event capacity != audited capacity event={event_id} "
                    f"target={target_capacity} audit={audit['capacity']}"
                )
        else:
            event_id = SYNTHETIC_EVENT_ID_BASE + synthetic_counter
            synthetic_counter += 1

        season = str(match["season"]).replace("-", "/")
        event = {
            "ticket_event_id": event_id,
            "club_slug": slug,
            "home_team": str(match["home_team"]),
            "away_team": str(match["away_team"]),
            "season": season,
            "round_no": int(match["round_number"]),
            "kickoff_at": kickoff.isoformat(),
            "home_club_key": home_key,
            "away_club_key": away_key,
            "stadium_capacity": int(audit["capacity"]),
            "actual_attendance": float(attendance["actual_attendance"]),
            "capacity_lineage": "d2-stage0-capacity-stability-audit-2026-10-18-v1",
        }
        replay_events.append(event)
        actual_by_id[event_id] = float(attendance["actual_attendance"])

    tracked_ids_in_replay = tuple(
        sorted(
            int(row["ticket_event_id"])
            for row in replay_events
            if int(row["ticket_event_id"]) in EXPECTED_C1_EVENT_IDS
        )
    )
    if tracked_ids_in_replay != EXPECTED_C1_EVENT_IDS:
        raise RuntimeError(
            f"not all frozen C1 events mapped to attendance history: {tracked_ids_in_replay}"
        )
    return replay_events, actual_by_id


def build_frozen_v2_event_anchors(
    payload: dict[str, Any],
    artifact_dir: Path,
    capacity_audit: dict[str, Any],
    freeze_manifest: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    legacy_priors = _event_prior_replay(payload, artifact_dir)
    replay_events, actual_by_id = build_replay_events(payload, capacity_audit)
    replay_payload = dict(payload)
    replay_payload["events"] = replay_events
    replay_priors = _event_prior_replay(replay_payload, artifact_dir)

    t1_replay = replay_priors[
        (replay_priors["horizon"] == "T-1")
        & replay_priors["prior_p50"].notna()
    ].copy()
    if len(t1_replay) != len(replay_events):
        bad = replay_priors[
            (replay_priors["horizon"] == "T-1")
            & replay_priors["prior_p50"].isna()
        ][["ticket_event_id", "prior_error"]].to_dict("records")
        raise RuntimeError(
            f"not all current-season home matches received a T-1 base prediction "
            f"predicted={len(t1_replay)} events={len(replay_events)} errors={bad}"
        )

    event_meta = {int(row["ticket_event_id"]): row for row in replay_events}
    t1_replay = t1_replay.sort_values("ticket_event_id").reset_index(drop=True)
    state_rows: list[dict[str, Any]] = []
    base_prediction: list[float] = []
    for row in t1_replay.to_dict("records"):
        event_id = int(row["ticket_event_id"])
        event = event_meta[event_id]
        state_rows.append({
            "match_key": f"d2-stage0|{event_id}",
            "ticket_event_id": event_id,
            "season": event["season"],
            "home_club_key": event["home_club_key"],
            "away_club_key": event["away_club_key"],
            "as_of_at": utc_timestamp(row["target_as_of_at"]),
            "kickoff_at": utc_timestamp(event["kickoff_at"]),
            "target_attendance": float(actual_by_id[event_id]),
            "capacity": float(event["stadium_capacity"]),
        })
        base_prediction.append(float(row["prior_p50"]))

    state = pd.DataFrame(state_rows)
    base_array = np.asarray(base_prediction, dtype=float)
    state = add_same_season_residual_state(state, base_array)
    frozen_prediction, b2_diag = apply_fixed_policy(state, base_array, "T-1")
    state["base_t1_p50"] = base_array
    state["frozen_v2_p50"] = frozen_prediction
    state["b2_correction_seats"] = frozen_prediction - base_array
    state["pre_live_freeze_id"] = EXPECTED_FREEZE_ID

    target_state = state[state["ticket_event_id"].isin(EXPECTED_C1_EVENT_IDS)].copy()
    if tuple(sorted(target_state["ticket_event_id"].astype(int))) != EXPECTED_C1_EVENT_IDS:
        raise RuntimeError("target frozen-v2 state is incomplete")

    frozen_t1_contract = next(
        row for row in freeze_manifest["horizons"] if row["horizon"] == "T-1"
    )["contract"]
    expected_base_id = frozen_t1_contract["historical_base"]

    legacy_t1 = legacy_priors[
        (legacy_priors["horizon"] == "T-1")
        & legacy_priors["ticket_event_id"].isin(EXPECTED_C1_EVENT_IDS)
    ].copy()
    if len(legacy_t1) != EXPECTED_C1_EVENT_COUNT:
        raise RuntimeError(f"legacy C1 T-1 prior count changed: {len(legacy_t1)}")

    legacy_by_id = {
        int(row["ticket_event_id"]): row
        for row in legacy_t1.to_dict("records")
    }
    target_by_id = {
        int(row["ticket_event_id"]): row
        for row in target_state.to_dict("records")
    }
    event_audit = []
    for event_id in EXPECTED_C1_EVENT_IDS:
        legacy = legacy_by_id[event_id]
        state_row = target_by_id[event_id]
        if legacy.get("prior_error") is not None:
            raise RuntimeError(f"legacy C1 prior error event={event_id}: {legacy['prior_error']}")
        if str(legacy.get("prior_model_spec_id")) != expected_base_id:
            raise RuntimeError(
                f"legacy T-1 base model id drift event={event_id}: "
                f"{legacy.get('prior_model_spec_id')} != {expected_base_id}"
            )
        legacy_p50 = float(legacy["prior_p50"])
        replay_base = float(state_row["base_t1_p50"])
        if not np.isclose(legacy_p50, replay_base, rtol=0.0, atol=BASE_REPRO_ATOL):
            raise RuntimeError(
                f"target base replay mismatch event={event_id}: "
                f"legacy={legacy_p50} replay={replay_base}"
            )
        n = int(state_row["regime_prior_home_matches"])
        correction = float(state_row["b2_correction_seats"])
        if n < 3 and not np.isclose(correction, 0.0, rtol=0.0, atol=1e-12):
            raise RuntimeError(
                f"b2 maturity gate violated event={event_id} n={n} correction={correction}"
            )
        event_audit.append({
            "ticket_event_id": event_id,
            "home_club_key": str(state_row["home_club_key"]),
            "legacy_t1_base_p50": legacy_p50,
            "frozen_v2_p50": float(state_row["frozen_v2_p50"]),
            "anchor_delta_seats": correction,
            "prior_completed_same_season_home_matches": n,
            "regime_ewma_residual_fraction": float(
                state_row["regime_ewma_residual_fraction"]
            ),
            "anchor_status": "FROZEN_V2_EXACT",
        })

    frozen_priors = legacy_priors.copy()
    for audit in event_audit:
        mask = (
            (frozen_priors["ticket_event_id"] == audit["ticket_event_id"])
            & (frozen_priors["horizon"] == "T-1")
        )
        frozen_priors.loc[mask, "prior_p50"] = audit["frozen_v2_p50"]
        frozen_priors.loc[mask, "prior_model_spec_id"] = EXPECTED_FREEZE_ID
        frozen_priors.loc[mask, "artifact_version"] = EXPECTED_FREEZE_ID

    return legacy_priors, frozen_priors, {
        "events": event_audit,
        "b2_state_diagnostics": b2_diag,
        "replayed_current_season_home_matches": int(len(state)),
    }


def build_d2_frame(
    payload: dict[str, Any],
    legacy_priors: pd.DataFrame,
    frozen_priors: pd.DataFrame,
    event_audit: dict[str, Any],
) -> pd.DataFrame:
    legacy = _training_frame(payload, legacy_priors).copy()
    frozen = _training_frame(payload, frozen_priors).copy()

    key_cols = ["ticket_event_id", "as_of_at"]
    legacy_keys = [
        (int(row.ticket_event_id), utc_timestamp(row.as_of_at).isoformat())
        for row in legacy[key_cols].itertuples(index=False)
    ]
    frozen_keys = [
        (int(row.ticket_event_id), utc_timestamp(row.as_of_at).isoformat())
        for row in frozen[key_cols].itertuples(index=False)
    ]
    if legacy_keys != frozen_keys:
        raise RuntimeError("frozen-v2 replay changed C1 row identity/order")
    if len(frozen) != EXPECTED_C1_LIVE_ROWS:
        raise RuntimeError(f"d2 Stage 0 row count changed: {len(frozen)}")

    legacy_by_key = {
        (int(row.ticket_event_id), utc_timestamp(row.as_of_at).isoformat()): float(row.prior_p50)
        for row in legacy[["ticket_event_id", "as_of_at", "prior_p50"]].itertuples(index=False)
    }
    audit_by_event = {
        int(row["ticket_event_id"]): row for row in event_audit["events"]
    }

    frozen = frozen.copy()
    frozen["legacy_prior_p50"] = [
        legacy_by_key[(int(row.ticket_event_id), utc_timestamp(row.as_of_at).isoformat())]
        for row in frozen[["ticket_event_id", "as_of_at"]].itertuples(index=False)
    ]
    frozen["frozen_v2_p50"] = frozen["prior_p50"].astype(float)
    frozen["frozen_v2_expected_occupancy"] = (
        frozen["frozen_v2_p50"].astype(float)
        / frozen["stadium_capacity"].astype(float)
    )
    frozen["anchor_delta_seats"] = (
        frozen["frozen_v2_p50"].astype(float)
        - frozen["legacy_prior_p50"].astype(float)
    )
    frozen["pre_live_freeze_id"] = EXPECTED_FREEZE_ID
    frozen["pre_live_manifest_sha256"] = EXPECTED_FREEZE_MANIFEST_SHA256
    frozen["anchor_status"] = "FROZEN_V2_EXACT"
    frozen["prior_completed_same_season_home_matches"] = frozen["ticket_event_id"].map(
        lambda event_id: int(audit_by_event[int(event_id)]["prior_completed_same_season_home_matches"])
    )
    frozen["regime_ewma_residual_fraction"] = frozen["ticket_event_id"].map(
        lambda event_id: float(audit_by_event[int(event_id)]["regime_ewma_residual_fraction"])
    )
    frozen["target_live_delta_attendance"] = (
        frozen["actual_attendance"].astype(float)
        - frozen["frozen_v2_p50"].astype(float)
    )
    frozen["target_live_delta_occupancy"] = (
        frozen["actual_attendance"].astype(float)
        / frozen["stadium_capacity"].astype(float)
        - frozen["frozen_v2_expected_occupancy"].astype(float)
    )

    if frozen["ticket_event_id"].nunique() != EXPECTED_C1_EVENT_COUNT:
        raise RuntimeError("d2 Stage 0 lost C1 events")
    if set(frozen["anchor_status"].unique()) != {"FROZEN_V2_EXACT"}:
        raise RuntimeError("primary d2 Stage 0 contains non-exact anchor rows")
    anchor_nunique = frozen.groupby("ticket_event_id")["frozen_v2_p50"].nunique()
    if int(anchor_nunique.max()) != 1:
        raise RuntimeError("frozen-v2 anchor varies across live rows within an event")
    return frozen


def summary_payload(
    frame: pd.DataFrame,
    event_audit: dict[str, Any],
    freeze_manifest_path: Path,
    c1_contract_path: Path,
    capacity_audit_path: Path,
) -> dict[str, Any]:
    events = []
    for event_id, group in frame.groupby("ticket_event_id", sort=True):
        first = group.iloc[0]
        events.append({
            "ticket_event_id": int(event_id),
            "home_team": str(first["home_team"]),
            "away_team": str(first["away_team"]),
            "rows": int(len(group)),
            "actual_attendance": float(first["actual_attendance"]),
            "stadium_capacity": float(first["stadium_capacity"]),
            "legacy_prior_p50": float(first["legacy_prior_p50"]),
            "frozen_v2_p50": float(first["frozen_v2_p50"]),
            "anchor_delta_seats": float(first["anchor_delta_seats"]),
            "prior_completed_same_season_home_matches": int(
                first["prior_completed_same_season_home_matches"]
            ),
            "target_live_delta_attendance": float(first["target_live_delta_attendance"]),
            "anchor_status": str(first["anchor_status"]),
        })

    changed = [row for row in events if abs(row["anchor_delta_seats"]) > 1e-12]
    legacy_event_mae = float(
        np.mean([abs(row["actual_attendance"] - row["legacy_prior_p50"]) for row in events])
    )
    frozen_event_mae = float(
        np.mean([abs(row["actual_attendance"] - row["frozen_v2_p50"]) for row in events])
    )
    return {
        "experiment": EXPERIMENT,
        "stage": STAGE,
        "status": "FROZEN_V2_EXACT_COMPATIBILITY_READY",
        "production_change": False,
        "model_training_performed": False,
        "source_live_contract": EXPECTED_C1_CONTRACT_VERSION,
        "source_c1_package": EXPECTED_C1_PACKAGE,
        "pre_live_freeze_id": EXPECTED_FREEZE_ID,
        "pre_live_manifest_sha256": EXPECTED_FREEZE_MANIFEST_SHA256,
        "lineage": {
            "freeze_manifest_sha256": sha256_file(freeze_manifest_path),
            "c1_training_contract_sha256": sha256_file(c1_contract_path),
            "capacity_audit_sha256": sha256_file(capacity_audit_path),
        },
        "dataset": {
            "event_count": int(frame["ticket_event_id"].nunique()),
            "row_count": int(len(frame)),
            "event_ids": sorted(int(v) for v in frame["ticket_event_id"].unique()),
            "all_rows_exact_frozen_v2_anchor": True,
            "events_with_nonzero_b2_anchor_delta": int(len(changed)),
            "events_without_b2_due_to_maturity_gate_or_zero_signal": int(len(events) - len(changed)),
        },
        "anchor_comparison": {
            "legacy_structural_prior_event_mae": legacy_event_mae,
            "frozen_v2_event_mae": frozen_event_mae,
            "mae_improvement_from_anchor_change": legacy_event_mae - frozen_event_mae,
            "mean_abs_anchor_delta_seats": float(
                np.mean([abs(row["anchor_delta_seats"]) for row in events])
            ),
            "max_abs_anchor_delta_seats": float(
                np.max([abs(row["anchor_delta_seats"]) for row in events])
            ),
        },
        "events": events,
        "b2_state_diagnostics": event_audit["b2_state_diagnostics"],
        "replayed_current_season_home_matches": event_audit[
            "replayed_current_season_home_matches"
        ],
        "decision": (
            "Use this 9-event/30-row exact frozen-v2 replay as the primary d2 Stage-1 "
            "training/evaluation lineage. Do not train d2 against the legacy C1 Structural "
            "Prior anchor under the frozen-v2 label."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--structural-artifact-dir", type=Path, required=True)
    parser.add_argument("--freeze-manifest", type=Path, required=True)
    parser.add_argument("--c1-training-contract", type=Path, required=True)
    parser.add_argument("--capacity-audit", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    freeze_manifest = load_and_verify_freeze_manifest(args.freeze_manifest)
    capacity_audit = load_capacity_audit(args.capacity_audit)
    verify_c1_contract(payload, args.c1_training_contract)

    legacy_priors, frozen_priors, event_audit = build_frozen_v2_event_anchors(
        payload,
        args.structural_artifact_dir,
        capacity_audit,
        freeze_manifest,
    )
    frame = build_d2_frame(payload, legacy_priors, frozen_priors, event_audit)
    summary = summary_payload(
        frame,
        event_audit,
        args.freeze_manifest,
        args.c1_training_contract,
        args.capacity_audit,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    frame.to_csv(args.output_csv, index=False)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
