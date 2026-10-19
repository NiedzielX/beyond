#!/usr/bin/env python3
"""Frozen d2 prospective scorer v1.

Scores newly completed ticket events against the already-frozen d2 package.
It never retrains on prospective outcomes and never changes Ridge/P2.

The immutable training set is the original 9-event/30-row Stage-0 frame.
Prospective events are discovered from the append-only exporter and excluded
when they are either frozen-development IDs or already present in the committed
prospective registry.

C1 comparison remains a separate evidence join because only genuine persisted
pre-outcome C1 decisions are allowed; this scorer never reconstructs C1 after
an outcome.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay, _training_frame
from ml.current_season_regime_fixed_temporal_audit_v1 import apply_fixed_policy
from ml.current_season_residual_regime_v1 import add_same_season_residual_state
from ml.d2_live_replay_anchor_v1 import (
    EXPECTED_FREEZE_ID,
    WARSAW_TZ,
    _sporting_index,
    canonical_club_key,
    load_and_verify_freeze_manifest,
    utc_timestamp,
)
from ml.d2_stage1_model_tournament_v1 import (
    CandidateSpec,
    available_base_features,
    fit_predict_learned,
    governed_forecast,
    load_stage0_frame,
)
from ml.d2_stage2_reliability_gating_v1 import (
    add_causal_reliability_state,
    maturity_reliability,
)

EXPERIMENT = "d2-prospective-score-v1"
STAGE = "d2-frozen-prospective-accumulation"
EXPECTED_STAGE2_PACKAGE = "d2-stage2-p2-observation-maturity-2026-10-19-v1"
EXPECTED_STAGE1_EXPERT = "ridge-a10"
EXPECTED_STAGE2_POLICY = "P2-observation-maturity"
EXPECTED_REGISTRY_VERSION = "d2-prospective-registry-v1"
EXPECTED_DEVELOPMENT_EVENT_IDS = (1, 3, 4, 8, 9, 12, 13, 14, 17)
EXPECTED_DEVELOPMENT_ROWS = 30
SYNTHETIC_EVENT_ID_BASE = 9_200_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def combined_payload(
    events_export: dict[str, Any],
    attendance_export: dict[str, Any],
    sporting_export: dict[str, Any],
    aliases_export: dict[str, Any],
    live_export: dict[str, Any],
) -> dict[str, Any]:
    return {
        "events": events_export.get("events") or [],
        "attendance": attendance_export.get("attendance") or [],
        "sportingMatches": sporting_export.get("sportingMatches") or [],
        "aliases": aliases_export.get("aliases") or [],
        "liveRows": live_export.get("liveRows") or [],
        "eventCount": live_export.get("eventCount"),
        "liveRowCount": live_export.get("liveRowCount"),
        "sampling": live_export.get("sampling"),
    }


def verify_stage2_manifest(path: Path) -> dict[str, Any]:
    manifest = load_json(path)
    if manifest.get("artifact_version") != EXPECTED_STAGE2_PACKAGE:
        raise RuntimeError("prospective scorer Stage-2 package drift")
    if manifest.get("status") != "FROZEN_RESEARCH_CANDIDATE":
        raise RuntimeError("Stage-2 package is not frozen")
    if manifest.get("stage1_expert_id") != EXPECTED_STAGE1_EXPERT:
        raise RuntimeError("Stage-1 expert drift")
    if manifest.get("stage2_policy_id") != EXPECTED_STAGE2_POLICY:
        raise RuntimeError("Stage-2 policy drift")
    if manifest.get("stage1_expert_retuned") is not False:
        raise RuntimeError("Stage-1 expert must remain frozen")
    development = manifest.get("development") or {}
    ids = tuple(int(v) for v in development.get("event_ids") or [])
    if ids != EXPECTED_DEVELOPMENT_EVENT_IDS:
        raise RuntimeError("Stage-2 development event IDs drift")
    if int(development.get("row_count") or 0) != EXPECTED_DEVELOPMENT_ROWS:
        raise RuntimeError("Stage-2 development row count drift")
    return manifest


def verify_registry(path: Path) -> tuple[dict[str, Any], set[int]]:
    registry = load_json(path)
    if registry.get("registry_version") != EXPECTED_REGISTRY_VERSION:
        raise RuntimeError("prospective registry version drift")
    if registry.get("frozen_package_id") != EXPECTED_STAGE2_PACKAGE:
        raise RuntimeError("prospective registry frozen-package drift")
    ids = tuple(int(v) for v in registry.get("development_event_ids") or [])
    if ids != EXPECTED_DEVELOPMENT_EVENT_IDS:
        raise RuntimeError("prospective registry development IDs drift")
    scored = {
        int(row["ticket_event_id"])
        for row in registry.get("scored_prospective_events") or []
    }
    if scored & set(EXPECTED_DEVELOPMENT_EVENT_IDS):
        raise RuntimeError("development event leaked into prospective registry")
    return registry, scored


def eligible_events(payload: dict[str, Any], scored_ids: set[int]) -> list[dict[str, Any]]:
    live_count: dict[int, int] = {}
    for row in payload.get("liveRows") or []:
        event_id = int(row["ticket_event_id"])
        live_count[event_id] = live_count.get(event_id, 0) + 1

    development = set(EXPECTED_DEVELOPMENT_EVENT_IDS)
    candidates: list[dict[str, Any]] = []
    for event in payload.get("events") or []:
        event_id = int(event["ticket_event_id"])
        if event_id in development or event_id in scored_ids:
            continue
        actual = event.get("actual_attendance")
        if actual is None or not np.isfinite(float(actual)) or float(actual) <= 0:
            continue
        if live_count.get(event_id, 0) <= 0:
            continue
        candidate = dict(event)
        candidate["prospective_live_row_count"] = int(live_count[event_id])
        candidates.append(candidate)
    return sorted(candidates, key=lambda row: utc_timestamp(row["kickoff_at"]))


def alias_map(payload: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in payload.get("aliases") or []:
        alias = str(row.get("alias") or "").strip()
        club_key = str(row.get("club_key") or "").strip()
        if alias and club_key:
            mapping[alias] = canonical_club_key(club_key)
    return mapping


def build_same_season_home_replay_events(
    payload: dict[str, Any],
    target_event: dict[str, Any],
    capacity_audit: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[int, float]]:
    event_id = int(target_event["ticket_event_id"])
    club_slug = str(target_event["club_slug"])
    home_key = canonical_club_key(club_slug)
    audit_row = (capacity_audit.get("clubs") or {}).get(club_slug)
    if audit_row is None:
        raise RuntimeError(f"capacity audit missing club={club_slug} event={event_id}")
    capacity = int(audit_row["capacity"])
    if int(target_event["stadium_capacity"]) != capacity:
        raise RuntimeError(
            f"event capacity differs from audited capacity event={event_id} "
            f"event_capacity={target_event['stadium_capacity']} audit={capacity}"
        )

    sporting = _sporting_index(payload)
    aliases = alias_map(payload)
    tracked = {
        (canonical_club_key(str(row["club_slug"])), utc_timestamp(row["kickoff_at"])): row
        for row in payload.get("events") or []
    }
    target_kickoff = utc_timestamp(target_event["kickoff_at"])
    target_season = str(target_event["season"]).replace("-", "/")

    replay: list[dict[str, Any]] = []
    actual_by_id: dict[int, float] = {}
    synthetic_counter = 0
    attendance_rows = sorted(
        [
            row for row in payload.get("attendance") or []
            if str(row.get("club_slug")) == club_slug
            and utc_timestamp(row["kickoff_at"]) <= target_kickoff
        ],
        key=lambda row: utc_timestamp(row["kickoff_at"]),
    )

    for attendance in attendance_rows:
        kickoff = utc_timestamp(attendance["kickoff_at"])
        local_date = kickoff.tz_convert(WARSAW_TZ).date().isoformat()
        match = sporting.get((local_date, home_key))
        if match is None:
            raise RuntimeError(
                f"cannot join attendance to sporting state event={event_id} kickoff={kickoff}"
            )
        season = str(match["season"]).replace("-", "/")
        if season != target_season:
            continue
        away_alias = str(match["away_team"])
        away_key = aliases.get(away_alias)
        if away_key is None:
            raise RuntimeError(
                f"missing away-team alias event={event_id} away={away_alias}"
            )
        tracked_event = tracked.get((home_key, kickoff))
        if tracked_event is not None:
            replay_event_id = int(tracked_event["ticket_event_id"])
        else:
            replay_event_id = SYNTHETIC_EVENT_ID_BASE + event_id * 100 + synthetic_counter
            synthetic_counter += 1
        replay_event = {
            "ticket_event_id": replay_event_id,
            "club_slug": club_slug,
            "home_team": str(match["home_team"]),
            "away_team": str(match["away_team"]),
            "season": season,
            "round_no": int(match["round_number"]),
            "kickoff_at": kickoff.isoformat(),
            "home_club_key": home_key,
            "away_club_key": away_key,
            "stadium_capacity": capacity,
            "actual_attendance": float(attendance["actual_attendance"]),
        }
        replay.append(replay_event)
        actual_by_id[replay_event_id] = float(attendance["actual_attendance"])

    replay_ids = [int(row["ticket_event_id"]) for row in replay]
    if event_id not in replay_ids:
        raise RuntimeError(f"target event missing from same-season replay event={event_id}")
    if replay_ids[-1] != event_id:
        raise RuntimeError(f"target event is not final replay event event={event_id}")
    return replay, actual_by_id


def build_frozen_anchor(
    payload: dict[str, Any],
    event: dict[str, Any],
    artifact_dir: Path,
    capacity_audit: dict[str, Any],
) -> dict[str, Any]:
    event_id = int(event["ticket_event_id"])
    replay_events, actual_by_id = build_same_season_home_replay_events(
        payload, event, capacity_audit
    )
    replay_payload = dict(payload)
    replay_payload["events"] = replay_events
    priors = _event_prior_replay(replay_payload, artifact_dir)
    t1 = priors[(priors["horizon"] == "T-1") & priors["prior_p50"].notna()].copy()
    if len(t1) != len(replay_events):
        raise RuntimeError(
            f"not all same-season replay events have T-1 base event={event_id} "
            f"predicted={len(t1)} expected={len(replay_events)}"
        )

    event_meta = {int(row["ticket_event_id"]): row for row in replay_events}
    state_rows: list[dict[str, Any]] = []
    base_predictions: list[float] = []
    for row in t1.sort_values("target_as_of_at").to_dict("records"):
        replay_event_id = int(row["ticket_event_id"])
        replay_event = event_meta[replay_event_id]
        state_rows.append({
            "match_key": f"d2-prospective|{event_id}|{replay_event_id}",
            "ticket_event_id": replay_event_id,
            "season": replay_event["season"],
            "home_club_key": replay_event["home_club_key"],
            "away_club_key": replay_event["away_club_key"],
            "as_of_at": utc_timestamp(row["target_as_of_at"]),
            "kickoff_at": utc_timestamp(replay_event["kickoff_at"]),
            "target_attendance": float(actual_by_id[replay_event_id]),
            "capacity": float(replay_event["stadium_capacity"]),
        })
        base_predictions.append(float(row["prior_p50"]))

    state = pd.DataFrame(state_rows)
    base = np.asarray(base_predictions, dtype=float)
    state = add_same_season_residual_state(state, base)
    frozen, diagnostics = apply_fixed_policy(state, base, "T-1")
    state["base_t1_p50"] = base
    state["frozen_v2_p50"] = frozen
    target = state[state["ticket_event_id"] == event_id]
    if len(target) != 1:
        raise RuntimeError(f"target event state missing/duplicated event={event_id}")
    row = target.iloc[0]
    structural = float(row["base_t1_p50"])
    frozen_p50 = float(row["frozen_v2_p50"])
    actual = float(event["actual_attendance"])
    return {
        "structural_t1_base_p50": structural,
        "frozen_v2_p50": frozen_p50,
        "b2_correction_seats": frozen_p50 - structural,
        "prior_completed_same_season_home_matches": int(row["regime_prior_home_matches"]),
        "regime_ewma_residual_fraction": float(row["regime_ewma_residual_fraction"]),
        "replayed_same_season_home_matches": int(len(state)),
        "structural_absolute_error": abs(actual - structural),
        "frozen_v2_absolute_error": abs(actual - frozen_p50),
        "b2_incremental_error_change": abs(actual - frozen_p50) - abs(actual - structural),
        "b2_diagnostics": diagnostics,
    }


def build_event_frame(
    payload: dict[str, Any],
    event: dict[str, Any],
    artifact_dir: Path,
    frozen_anchor: float,
) -> pd.DataFrame:
    event_id = int(event["ticket_event_id"])
    event_payload = dict(payload)
    event_payload["events"] = [event]
    event_payload["liveRows"] = [
        row for row in payload.get("liveRows") or []
        if int(row["ticket_event_id"]) == event_id
    ]
    priors = _event_prior_replay(event_payload, artifact_dir)
    t1_mask = (priors["ticket_event_id"] == event_id) & (priors["horizon"] == "T-1")
    if int(t1_mask.sum()) != 1:
        raise RuntimeError(f"event requires exactly one T-1 prior event={event_id}")
    priors = priors.copy()
    priors.loc[t1_mask, "prior_p50"] = float(frozen_anchor)
    priors.loc[t1_mask, "prior_model_spec_id"] = EXPECTED_FREEZE_ID
    priors.loc[t1_mask, "artifact_version"] = EXPECTED_FREEZE_ID
    frame = _training_frame(event_payload, priors)
    frame = frame[frame["ticket_event_id"] == event_id].copy()
    if frame.empty:
        raise RuntimeError(f"event produced no live scoring rows event={event_id}")
    if set(frame["prior_horizon"].astype(str)) != {"T-1"}:
        raise RuntimeError(f"prospective final-24h rows are not all T-1 event={event_id}")
    frame["frozen_v2_p50"] = frame["prior_p50"].astype(float)
    frame["frozen_v2_expected_occupancy"] = frame["prior_expected_occupancy"].astype(float)
    frame["pre_live_freeze_id"] = EXPECTED_FREEZE_ID
    frame["anchor_status"] = "FROZEN_V2_EXACT_PROSPECTIVE"
    frame["target_live_delta_attendance"] = (
        frame["actual_attendance"].astype(float) - frame["frozen_v2_p50"].astype(float)
    )
    frame["target_live_delta_occupancy"] = (
        frame["actual_attendance"].astype(float) / frame["stadium_capacity"].astype(float)
        - frame["frozen_v2_expected_occupancy"].astype(float)
    )
    return frame.sort_values("as_of_at").reset_index(drop=True)


def score_series(actual: float, values: np.ndarray) -> dict[str, float]:
    errors = np.abs(np.asarray(values, dtype=float) - float(actual))
    return {
        "latest_error": float(errors[-1]),
        "window_mae": float(np.mean(errors)),
    }


def score_event(
    *,
    development: pd.DataFrame,
    payload: dict[str, Any],
    event: dict[str, Any],
    structural_artifact_dir: Path,
    capacity_audit: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    event_id = int(event["ticket_event_id"])
    anchor = build_frozen_anchor(payload, event, structural_artifact_dir, capacity_audit)
    frame = build_event_frame(
        payload,
        event,
        structural_artifact_dir,
        float(anchor["frozen_v2_p50"]),
    )

    frozen_features = available_base_features(development)
    missing = [column for column in frozen_features if column not in frame.columns]
    if missing:
        raise RuntimeError(f"event missing frozen Ridge features event={event_id}: {missing}")

    spec = CandidateSpec(EXPECTED_STAGE1_EXPERT, "ridge")
    raw_delta = fit_predict_learned(spec, development, frame)
    raw_forecast, governed_delta = governed_forecast(frame, raw_delta)
    state = add_causal_reliability_state(frame)
    reliability = maturity_reliability(state)
    p2_delta = reliability * governed_delta
    capacity = frame["stadium_capacity"].astype(float).to_numpy()
    frozen = frame["frozen_v2_p50"].astype(float).to_numpy()
    p2_forecast = np.clip(frozen + p2_delta * capacity, 0.0, capacity)
    actual = float(event["actual_attendance"])

    frozen_score = score_series(actual, frozen)
    raw_score = score_series(actual, raw_forecast)
    p2_score = score_series(actual, p2_forecast)

    rows = frame[[
        "ticket_event_id",
        "as_of_at",
        "hours_to_kickoff",
        "actual_attendance",
        "stadium_capacity",
        "frozen_v2_p50",
    ]].copy()
    rows["observation_index"] = state["stage2_observation_index"].astype(int).to_numpy()
    rows["raw_ridge_delta_occupancy"] = raw_delta
    rows["raw_ridge_governed_delta_occupancy"] = governed_delta
    rows["raw_ridge_p50"] = raw_forecast
    rows["p2_reliability"] = reliability
    rows["p2_delta_occupancy"] = p2_delta
    rows["p2_p50"] = p2_forecast
    rows["frozen_v2_absolute_error"] = np.abs(actual - frozen)
    rows["raw_ridge_absolute_error"] = np.abs(actual - raw_forecast)
    rows["p2_absolute_error"] = np.abs(actual - p2_forecast)

    return {
        "ticket_event_id": event_id,
        "home_team": event.get("home_team"),
        "away_team": event.get("away_team"),
        "club_slug": event.get("club_slug"),
        "kickoff_at": utc_timestamp(event["kickoff_at"]).isoformat(),
        "actual_attendance": actual,
        "stadium_capacity": float(event["stadium_capacity"]),
        "live_row_count": int(len(frame)),
        "component_diagnostics": anchor,
        "scores": {
            "frozen_v2": frozen_score,
            "raw_ridge": raw_score,
            "p2_governed_ridge": p2_score,
            "raw_ridge_latest_improvement_vs_frozen": (
                frozen_score["latest_error"] - raw_score["latest_error"]
            ),
            "raw_ridge_window_improvement_vs_frozen": (
                frozen_score["window_mae"] - raw_score["window_mae"]
            ),
            "p2_latest_improvement_vs_frozen": (
                frozen_score["latest_error"] - p2_score["latest_error"]
            ),
            "p2_window_improvement_vs_frozen": (
                frozen_score["window_mae"] - p2_score["window_mae"]
            ),
            "p2_latest_improvement_vs_raw_ridge": (
                raw_score["latest_error"] - p2_score["latest_error"]
            ),
            "p2_window_improvement_vs_raw_ridge": (
                raw_score["window_mae"] - p2_score["window_mae"]
            ),
        },
        "c1_v8_comparator": {
            "status": "SEPARATE_PRE_OUTCOME_PERSISTED_EVIDENCE_REQUIRED",
            "reconstruct_after_outcome_allowed": False,
        },
    }, rows


def run_prospective(
    *,
    development_stage0_csv: Path,
    payload: dict[str, Any],
    structural_artifact_dir: Path,
    pre_live_manifest: Path,
    stage2_manifest_path: Path,
    capacity_audit_path: Path,
    registry_path: Path,
) -> tuple[dict[str, Any], pd.DataFrame]:
    load_and_verify_freeze_manifest(pre_live_manifest)
    stage2_manifest = verify_stage2_manifest(stage2_manifest_path)
    registry, scored_ids = verify_registry(registry_path)
    capacity_audit = load_json(capacity_audit_path)

    development = load_stage0_frame(development_stage0_csv)
    development_ids = tuple(sorted(int(v) for v in development["ticket_event_id"].unique()))
    if development_ids != EXPECTED_DEVELOPMENT_EVENT_IDS:
        raise RuntimeError("prospective scorer training event IDs drift")
    if len(development) != EXPECTED_DEVELOPMENT_ROWS:
        raise RuntimeError("prospective scorer training row count drift")

    candidates = eligible_events(payload, scored_ids)
    if not candidates:
        empty = pd.DataFrame(columns=[
            "ticket_event_id", "as_of_at", "hours_to_kickoff", "actual_attendance",
            "stadium_capacity", "frozen_v2_p50", "observation_index",
            "raw_ridge_delta_occupancy", "raw_ridge_governed_delta_occupancy",
            "raw_ridge_p50", "p2_reliability", "p2_delta_occupancy", "p2_p50",
            "frozen_v2_absolute_error", "raw_ridge_absolute_error", "p2_absolute_error",
        ])
        return {
            "experiment": EXPERIMENT,
            "stage": STAGE,
            "status": "NO_NEW_ELIGIBLE_EVENTS",
            "production_change": False,
            "promotion_allowed": False,
            "model_training_on_prospective_outcomes": False,
            "policy_retuning_performed": False,
            "frozen_lineage": {
                "pre_live_freeze_id": EXPECTED_FREEZE_ID,
                "stage1_expert_id": EXPECTED_STAGE1_EXPERT,
                "stage2_package_id": stage2_manifest["artifact_version"],
                "stage2_policy_id": stage2_manifest["stage2_policy_id"],
                "registry_version": registry["registry_version"],
            },
            "development_event_ids": list(development_ids),
            "registered_prospective_event_ids": sorted(scored_ids),
            "new_candidate_event_ids": [],
            "scored_events": [],
            "blocked_events": [],
            "current_export": {
                "event_count_metadata": payload.get("eventCount"),
                "live_row_count_metadata": payload.get("liveRowCount"),
            },
        }, empty

    scored: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    row_parts: list[pd.DataFrame] = []
    for event in candidates:
        event_id = int(event["ticket_event_id"])
        try:
            event_result, event_rows = score_event(
                development=development,
                payload=payload,
                event=event,
                structural_artifact_dir=structural_artifact_dir,
                capacity_audit=capacity_audit,
            )
        except Exception as exc:
            blocked.append({
                "ticket_event_id": event_id,
                "home_team": event.get("home_team"),
                "away_team": event.get("away_team"),
                "kickoff_at": event.get("kickoff_at"),
                "reason": type(exc).__name__,
                "message": str(exc),
            })
            continue
        scored.append(event_result)
        row_parts.append(event_rows)

    rows = pd.concat(row_parts, ignore_index=True) if row_parts else pd.DataFrame()
    status = "COMPLETED_PROSPECTIVE_SCORING" if scored else "NEW_EVENTS_BLOCKED_NO_SCORES"
    return {
        "experiment": EXPERIMENT,
        "stage": STAGE,
        "status": status,
        "production_change": False,
        "promotion_allowed": False,
        "model_training_on_prospective_outcomes": False,
        "policy_retuning_performed": False,
        "frozen_lineage": {
            "pre_live_freeze_id": EXPECTED_FREEZE_ID,
            "stage1_expert_id": EXPECTED_STAGE1_EXPERT,
            "stage2_package_id": stage2_manifest["artifact_version"],
            "stage2_policy_id": stage2_manifest["stage2_policy_id"],
            "registry_version": registry["registry_version"],
            "pre_live_manifest_sha256": sha256_file(pre_live_manifest),
            "stage2_manifest_sha256": sha256_file(stage2_manifest_path),
            "registry_sha256": sha256_file(registry_path),
        },
        "development_event_ids": list(development_ids),
        "registered_prospective_event_ids": sorted(scored_ids),
        "new_candidate_event_ids": [int(row["ticket_event_id"]) for row in candidates],
        "scored_events": scored,
        "blocked_events": blocked,
        "current_export": {
            "event_count_metadata": payload.get("eventCount"),
            "live_row_count_metadata": payload.get("liveRowCount"),
        },
        "decision_boundary": (
            "Prospective scoring only. Do not add scored outcomes to Ridge training or change P2. "
            "Persist evidence/registry in a separate review cycle."
        ),
    }, rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--attendance", type=Path, required=True)
    parser.add_argument("--sporting", type=Path, required=True)
    parser.add_argument("--aliases", type=Path, required=True)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--development-stage0-csv", type=Path, required=True)
    parser.add_argument("--structural-artifact-dir", type=Path, required=True)
    parser.add_argument("--pre-live-manifest", type=Path, required=True)
    parser.add_argument("--stage2-manifest", type=Path, required=True)
    parser.add_argument("--capacity-audit", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    payload = combined_payload(
        load_json(args.events),
        load_json(args.attendance),
        load_json(args.sporting),
        load_json(args.aliases),
        load_json(args.live),
    )
    result, rows = run_prospective(
        development_stage0_csv=args.development_stage0_csv,
        payload=payload,
        structural_artifact_dir=args.structural_artifact_dir,
        pre_live_manifest=args.pre_live_manifest,
        stage2_manifest_path=args.stage2_manifest,
        capacity_audit_path=args.capacity_audit,
        registry_path=args.registry,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    rows.to_csv(args.output_csv, index=False)
    print(json.dumps({
        "status": result["status"],
        "new_candidate_event_ids": result["new_candidate_event_ids"],
        "scored_events": result["scored_events"],
        "blocked_events": result["blocked_events"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
