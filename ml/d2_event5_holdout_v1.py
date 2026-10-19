#!/usr/bin/env python3
"""One-pass chronological holdout scoring for d2 event 5.

This evaluator is intentionally non-selective:
- training is frozen to the original 9-event / 30-row d2 development set;
- the Stage-1 expert is exactly `ridge-a10`;
- the Stage-2 policy is exactly `P2-observation-maturity`;
- event 5 is used only as holdout test data;
- no model/policy parameter is tuned from the event-5 outcome.

The C1 v8 comparator, when supplied, must be an already-persisted prospective
score. This script never reconstructs C1 v8 after the outcome.
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
    BASE_FEATURES,
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

EXPERIMENT = "d2-event5-holdout-v1"
STAGE = "d2-first-chronological-holdout"
HOLDOUT_EVENT_ID = 5
EXPECTED_DEVELOPMENT_EVENT_IDS = (1, 3, 4, 8, 9, 12, 13, 14, 17)
EXPECTED_DEVELOPMENT_EVENT_COUNT = 9
EXPECTED_DEVELOPMENT_ROW_COUNT = 30
EXPECTED_HOLDOUT_ROWS = 4
EXPECTED_ACTUAL_ATTENDANCE = 37407.0
EXPECTED_CAPACITY = 43269.0
EXPECTED_KICKOFF = pd.Timestamp("2026-10-18T15:30:00Z")
EXPECTED_STAGE2_PACKAGE = "d2-stage2-p2-observation-maturity-2026-10-19-v1"
EXPECTED_STAGE2_POLICY = "P2-observation-maturity"
EXPECTED_STAGE1_EXPERT = "ridge-a10"
EXPECTED_C1_PACKAGE = "c1-shadow-v8-frozen-2026-10-16-n9"
SYNTHETIC_EVENT_ID_BASE = 9_100_000


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
        "aliases": aliases_export.get("aliases") or {},
        "liveRows": live_export.get("liveRows") or [],
        "eventCount": live_export.get("eventCount"),
        "liveRowCount": live_export.get("liveRowCount"),
        "sampling": live_export.get("sampling"),
    }


def verify_stage2_manifest(path: Path) -> dict[str, Any]:
    manifest = load_json(path)
    if manifest.get("artifact_version") != EXPECTED_STAGE2_PACKAGE:
        raise RuntimeError("Stage-2 frozen package ID drift")
    if manifest.get("status") != "FROZEN_RESEARCH_CANDIDATE":
        raise RuntimeError("Stage-2 manifest is not frozen research candidate")
    if manifest.get("stage1_expert_id") != EXPECTED_STAGE1_EXPERT:
        raise RuntimeError("Stage-1 expert drift in Stage-2 manifest")
    if manifest.get("stage2_policy_id") != EXPECTED_STAGE2_POLICY:
        raise RuntimeError("Stage-2 policy drift")
    if manifest.get("stage1_expert_retuned") is not False:
        raise RuntimeError("Stage-2 manifest indicates Stage-1 expert retuning")
    development = manifest.get("development") or {}
    if tuple(development.get("event_ids") or []) != EXPECTED_DEVELOPMENT_EVENT_IDS:
        raise RuntimeError("Stage-2 frozen development event set drift")
    if int(development.get("row_count") or 0) != EXPECTED_DEVELOPMENT_ROW_COUNT:
        raise RuntimeError("Stage-2 frozen development row count drift")
    if int(development.get("reserved_holdout_event_id") or -1) != HOLDOUT_EVENT_ID:
        raise RuntimeError("Stage-2 reserved holdout ID drift")
    if development.get("reserved_holdout_used_for_selection") is not False:
        raise RuntimeError("Stage-2 manifest says holdout was used for selection")
    return manifest


def verify_c1_comparator(path: Path) -> dict[str, Any]:
    evidence = load_json(path)
    if int(evidence.get("ticket_event_id") or -1) != HOLDOUT_EVENT_ID:
        raise RuntimeError("C1 comparator event ID drift")
    if evidence.get("package_version") != EXPECTED_C1_PACKAGE:
        raise RuntimeError("C1 comparator package drift")
    if float(evidence.get("actual_attendance")) != EXPECTED_ACTUAL_ATTENDANCE:
        raise RuntimeError("C1 comparator outcome drift")
    if evidence.get("reconstructed_after_outcome") is not False:
        raise RuntimeError("C1 comparator must not be reconstructed after outcome")
    governance = evidence.get("governance") or {}
    if governance.get("source_predictions_persisted_pre_outcome") is not True:
        raise RuntimeError("C1 comparator lacks pre-outcome provenance")
    if governance.get("no_backfill") is not True:
        raise RuntimeError("C1 comparator must be no-backfill evidence")
    return evidence


def get_holdout_event(payload: dict[str, Any]) -> dict[str, Any]:
    rows = [
        row for row in payload.get("events") or []
        if int(row["ticket_event_id"]) == HOLDOUT_EVENT_ID
    ]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one holdout event 5, got {len(rows)}")
    event = rows[0]
    if float(event["actual_attendance"]) != EXPECTED_ACTUAL_ATTENDANCE:
        raise RuntimeError("holdout actual attendance drift")
    if float(event["stadium_capacity"]) != EXPECTED_CAPACITY:
        raise RuntimeError("holdout capacity drift")
    if utc_timestamp(event["kickoff_at"]) != EXPECTED_KICKOFF:
        raise RuntimeError("holdout kickoff drift")
    live_rows = [
        row for row in payload.get("liveRows") or []
        if int(row["ticket_event_id"]) == HOLDOUT_EVENT_ID
    ]
    if len(live_rows) != EXPECTED_HOLDOUT_ROWS:
        raise RuntimeError(f"holdout live-row count drift: {len(live_rows)}")
    return event


def build_same_season_home_replay_events(
    payload: dict[str, Any],
    holdout_event: dict[str, Any],
    capacity_audit: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[int, float]]:
    club_slug = str(holdout_event["club_slug"])
    home_key = canonical_club_key(club_slug)
    audit_row = (capacity_audit.get("clubs") or {}).get(club_slug)
    if not audit_row:
        raise RuntimeError(f"holdout club {club_slug} absent from capacity audit")
    if int(audit_row["capacity"]) != int(EXPECTED_CAPACITY):
        raise RuntimeError("holdout club audited capacity drift")
    if int(holdout_event["stadium_capacity"]) != int(audit_row["capacity"]):
        raise RuntimeError("holdout event capacity does not match audited club capacity")

    sporting = _sporting_index(payload)
    tracked = {
        (canonical_club_key(str(row["club_slug"])), utc_timestamp(row["kickoff_at"])): row
        for row in payload.get("events") or []
    }
    holdout_kickoff = utc_timestamp(holdout_event["kickoff_at"])
    target_season = str(holdout_event["season"]).replace("-", "/")

    replay: list[dict[str, Any]] = []
    actual_by_id: dict[int, float] = {}
    synthetic_counter = 0
    attendance_rows = sorted(
        [
            row for row in (payload.get("attendance") or [])
            if str(row.get("club_slug")) == club_slug
            and utc_timestamp(row["kickoff_at"]) <= holdout_kickoff
        ],
        key=lambda row: utc_timestamp(row["kickoff_at"]),
    )

    for attendance in attendance_rows:
        kickoff = utc_timestamp(attendance["kickoff_at"])
        local_date = kickoff.tz_convert(WARSAW_TZ).date().isoformat()
        match = sporting.get((local_date, home_key))
        if match is None:
            raise RuntimeError(
                f"cannot join {club_slug} attendance row to sporting state kickoff={kickoff}"
            )
        season = str(match["season"]).replace("-", "/")
        if season != target_season:
            continue
        away_key = canonical_club_key(
            next(
                str(row["club_key"])
                for row in payload.get("aliases") or []
                if str(row["alias"]) == str(match["away_team"])
            )
        )
        tracked_event = tracked.get((home_key, kickoff))
        if tracked_event is not None:
            event_id = int(tracked_event["ticket_event_id"])
        else:
            event_id = SYNTHETIC_EVENT_ID_BASE + synthetic_counter
            synthetic_counter += 1
        event = {
            "ticket_event_id": event_id,
            "club_slug": club_slug,
            "home_team": str(match["home_team"]),
            "away_team": str(match["away_team"]),
            "season": season,
            "round_no": int(match["round_number"]),
            "kickoff_at": kickoff.isoformat(),
            "home_club_key": home_key,
            "away_club_key": away_key,
            "stadium_capacity": int(EXPECTED_CAPACITY),
            "actual_attendance": float(attendance["actual_attendance"]),
        }
        replay.append(event)
        actual_by_id[event_id] = float(attendance["actual_attendance"])

    ids = [int(row["ticket_event_id"]) for row in replay]
    if HOLDOUT_EVENT_ID not in ids:
        raise RuntimeError("holdout event absent from same-season home replay")
    if ids[-1] != HOLDOUT_EVENT_ID:
        raise RuntimeError("holdout must be the final same-season home replay event")
    return replay, actual_by_id


def build_holdout_frozen_anchor(
    payload: dict[str, Any],
    holdout_event: dict[str, Any],
    artifact_dir: Path,
    capacity_audit: dict[str, Any],
) -> tuple[float, dict[str, Any], pd.DataFrame]:
    replay_events, actual_by_id = build_same_season_home_replay_events(
        payload, holdout_event, capacity_audit
    )
    replay_payload = dict(payload)
    replay_payload["events"] = replay_events
    priors = _event_prior_replay(replay_payload, artifact_dir)
    t1 = priors[(priors["horizon"] == "T-1") & priors["prior_p50"].notna()].copy()
    if len(t1) != len(replay_events):
        raise RuntimeError(
            f"not all replay events received T-1 base prediction: {len(t1)}/{len(replay_events)}"
        )
    event_meta = {int(row["ticket_event_id"]): row for row in replay_events}
    state_rows: list[dict[str, Any]] = []
    base_predictions: list[float] = []
    for row in t1.sort_values("target_as_of_at").to_dict("records"):
        event_id = int(row["ticket_event_id"])
        event = event_meta[event_id]
        state_rows.append({
            "match_key": f"d2-holdout|{event_id}",
            "ticket_event_id": event_id,
            "season": event["season"],
            "home_club_key": event["home_club_key"],
            "away_club_key": event["away_club_key"],
            "as_of_at": utc_timestamp(row["target_as_of_at"]),
            "kickoff_at": utc_timestamp(event["kickoff_at"]),
            "target_attendance": float(actual_by_id[event_id]),
            "capacity": float(event["stadium_capacity"]),
        })
        base_predictions.append(float(row["prior_p50"]))
    state = pd.DataFrame(state_rows)
    base = np.asarray(base_predictions, dtype=float)
    state = add_same_season_residual_state(state, base)
    frozen, diagnostics = apply_fixed_policy(state, base, "T-1")
    state["base_t1_p50"] = base
    state["frozen_v2_p50"] = frozen
    target = state[state["ticket_event_id"] == HOLDOUT_EVENT_ID]
    if len(target) != 1:
        raise RuntimeError("holdout state row missing or duplicated")
    target_row = target.iloc[0]
    prior_count = int(target_row["regime_prior_home_matches"])
    if prior_count < 3:
        raise RuntimeError(
            f"unexpected holdout b2 maturity state; prior home matches={prior_count}"
        )
    anchor = float(target_row["frozen_v2_p50"])
    return anchor, {
        "base_t1_p50": float(target_row["base_t1_p50"]),
        "frozen_v2_p50": anchor,
        "b2_correction_seats": anchor - float(target_row["base_t1_p50"]),
        "prior_completed_same_season_home_matches": prior_count,
        "regime_ewma_residual_fraction": float(target_row["regime_ewma_residual_fraction"]),
        "replayed_same_season_home_matches": int(len(state)),
        "b2_diagnostics": diagnostics,
    }, state


def build_holdout_frame(
    payload: dict[str, Any],
    holdout_event: dict[str, Any],
    artifact_dir: Path,
    frozen_anchor: float,
) -> pd.DataFrame:
    event_payload = dict(payload)
    event_payload["events"] = [holdout_event]
    event_payload["liveRows"] = [
        row for row in payload.get("liveRows") or []
        if int(row["ticket_event_id"]) == HOLDOUT_EVENT_ID
    ]
    priors = _event_prior_replay(event_payload, artifact_dir)
    t1_mask = (priors["ticket_event_id"] == HOLDOUT_EVENT_ID) & (priors["horizon"] == "T-1")
    if int(t1_mask.sum()) != 1:
        raise RuntimeError("holdout event must have exactly one T-1 prior")
    priors = priors.copy()
    priors.loc[t1_mask, "prior_p50"] = float(frozen_anchor)
    priors.loc[t1_mask, "prior_model_spec_id"] = EXPECTED_FREEZE_ID
    priors.loc[t1_mask, "artifact_version"] = EXPECTED_FREEZE_ID
    frame = _training_frame(event_payload, priors)
    frame = frame[frame["ticket_event_id"] == HOLDOUT_EVENT_ID].copy()
    if len(frame) != EXPECTED_HOLDOUT_ROWS:
        raise RuntimeError(f"holdout training-frame row count drift: {len(frame)}")
    if set(frame["prior_horizon"].astype(str)) != {"T-1"}:
        raise RuntimeError("holdout final-24h rows are not all anchored to T-1")
    if frame["prior_p50"].nunique() != 1:
        raise RuntimeError("holdout frozen anchor varies across live rows")
    if not np.isclose(float(frame["prior_p50"].iloc[0]), frozen_anchor, rtol=0.0, atol=1e-9):
        raise RuntimeError("holdout training frame did not use Frozen-v2 anchor")

    frame["frozen_v2_p50"] = frame["prior_p50"].astype(float)
    frame["frozen_v2_expected_occupancy"] = frame["prior_expected_occupancy"].astype(float)
    frame["pre_live_freeze_id"] = EXPECTED_FREEZE_ID
    frame["anchor_status"] = "FROZEN_V2_EXACT_HOLDOUT"
    frame["target_live_delta_attendance"] = (
        frame["actual_attendance"].astype(float) - frame["frozen_v2_p50"].astype(float)
    )
    frame["target_live_delta_occupancy"] = (
        frame["actual_attendance"].astype(float) / frame["stadium_capacity"].astype(float)
        - frame["frozen_v2_expected_occupancy"].astype(float)
    )
    return frame.sort_values("as_of_at").reset_index(drop=True)


def score_forecast(actual: float, values: np.ndarray) -> dict[str, float]:
    errors = np.abs(np.asarray(values, dtype=float) - float(actual))
    return {
        "latest_error": float(errors[-1]),
        "window_mae": float(np.mean(errors)),
    }


def run_holdout(
    *,
    development_stage0_csv: Path,
    payload: dict[str, Any],
    structural_artifact_dir: Path,
    pre_live_manifest: Path,
    stage2_manifest_path: Path,
    capacity_audit_path: Path,
    c1_comparator_path: Path,
) -> tuple[dict[str, Any], pd.DataFrame]:
    load_and_verify_freeze_manifest(pre_live_manifest)
    stage2_manifest = verify_stage2_manifest(stage2_manifest_path)
    c1_comparator = verify_c1_comparator(c1_comparator_path)
    capacity_audit = load_json(capacity_audit_path)

    development = load_stage0_frame(development_stage0_csv)
    development_ids = tuple(sorted(int(v) for v in development["ticket_event_id"].unique()))
    if development_ids != EXPECTED_DEVELOPMENT_EVENT_IDS:
        raise RuntimeError("holdout training event IDs drift")
    if HOLDOUT_EVENT_ID in development_ids:
        raise RuntimeError("holdout event leaked into training")

    holdout_event = get_holdout_event(payload)
    frozen_anchor, anchor_diag, _ = build_holdout_frozen_anchor(
        payload,
        holdout_event,
        structural_artifact_dir,
        capacity_audit,
    )
    holdout = build_holdout_frame(
        payload,
        holdout_event,
        structural_artifact_dir,
        frozen_anchor,
    )

    frozen_feature_contract = available_base_features(development)
    missing_holdout_features = [
        column for column in frozen_feature_contract if column not in holdout.columns
    ]
    if missing_holdout_features:
        raise RuntimeError(
            f"holdout missing frozen Stage-1 features: {missing_holdout_features}"
        )
    unexpected_development_features = [
        column for column in BASE_FEATURES
        if column in development.columns and column not in frozen_feature_contract
    ]
    if unexpected_development_features:
        raise RuntimeError("internal frozen feature-contract inconsistency")

    spec = CandidateSpec(EXPECTED_STAGE1_EXPERT, "ridge")
    raw_delta = fit_predict_learned(spec, development, holdout)
    raw_forecast, governed_delta = governed_forecast(holdout, raw_delta)

    state = add_causal_reliability_state(holdout)
    reliability = maturity_reliability(state)
    p2_delta = reliability * governed_delta
    capacity = holdout["stadium_capacity"].astype(float).to_numpy()
    anchor = holdout["frozen_v2_p50"].astype(float).to_numpy()
    p2_forecast = np.clip(anchor + p2_delta * capacity, 0.0, capacity)

    actual = EXPECTED_ACTUAL_ATTENDANCE
    frozen_score = score_forecast(actual, anchor)
    raw_score = score_forecast(actual, raw_forecast)
    p2_score = score_forecast(actual, p2_forecast)

    rows = holdout[[
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
    rows["frozen_v2_absolute_error"] = np.abs(actual - anchor)
    rows["raw_ridge_absolute_error"] = np.abs(actual - raw_forecast)
    rows["p2_absolute_error"] = np.abs(actual - p2_forecast)

    result = {
        "experiment": EXPERIMENT,
        "stage": STAGE,
        "status": "COMPLETED_ONE_PASS_HOLDOUT",
        "production_change": False,
        "promotion_allowed": False,
        "holdout_event_id": HOLDOUT_EVENT_ID,
        "holdout_used_for_training": False,
        "holdout_used_for_model_selection": False,
        "holdout_used_for_policy_selection": False,
        "post_holdout_retuning_allowed": False,
        "development": {
            "event_ids": list(development_ids),
            "event_count": int(development["ticket_event_id"].nunique()),
            "row_count": int(len(development)),
            "feature_contract": frozen_feature_contract,
        },
        "frozen_lineage": {
            "pre_live_freeze_id": EXPECTED_FREEZE_ID,
            "stage1_expert_id": EXPECTED_STAGE1_EXPERT,
            "stage2_package_id": stage2_manifest["artifact_version"],
            "stage2_policy_id": stage2_manifest["stage2_policy_id"],
            "pre_live_manifest_sha256": sha256_file(pre_live_manifest),
            "stage2_manifest_sha256": sha256_file(stage2_manifest_path),
            "c1_comparator_sha256": sha256_file(c1_comparator_path),
        },
        "holdout": {
            "home_team": holdout_event["home_team"],
            "away_team": holdout_event["away_team"],
            "kickoff_at": utc_timestamp(holdout_event["kickoff_at"]).isoformat(),
            "actual_attendance": actual,
            "stadium_capacity": EXPECTED_CAPACITY,
            "live_row_count": int(len(holdout)),
            "anchor_diagnostics": anchor_diag,
        },
        "scores": {
            "frozen_v2": frozen_score,
            "raw_ridge": raw_score,
            "p2_governed_ridge": p2_score,
            "raw_ridge_latest_improvement_vs_frozen": (
                frozen_score["latest_error"] - raw_score["latest_error"]
            ),
            "p2_latest_improvement_vs_frozen": (
                frozen_score["latest_error"] - p2_score["latest_error"]
            ),
            "p2_latest_improvement_vs_raw_ridge": (
                raw_score["latest_error"] - p2_score["latest_error"]
            ),
            "raw_ridge_window_improvement_vs_frozen": (
                frozen_score["window_mae"] - raw_score["window_mae"]
            ),
            "p2_window_improvement_vs_frozen": (
                frozen_score["window_mae"] - p2_score["window_mae"]
            ),
        },
        "c1_v8_prospective_comparator": {
            "status": "AVAILABLE_PRE_OUTCOME_PERSISTED",
            "package_version": c1_comparator["package_version"],
            "latest_selected_expert": c1_comparator["latest_selected_expert"],
            "latest_reason_code": c1_comparator["latest_reason_code"],
            "latest_prior_error": float(c1_comparator["latest_prior_error"]),
            "latest_live_error": float(c1_comparator["latest_live_error"]),
            "latest_policy_error": float(c1_comparator["latest_policy_error"]),
            "window_prior_mae": float(c1_comparator["window_prior_mae"]),
            "window_live_mae": float(c1_comparator["window_live_mae"]),
            "window_policy_mae": float(c1_comparator["window_policy_mae"]),
            "prediction_row_count": int(c1_comparator["prediction_row_count"]),
            "representative_bucket_count": int(c1_comparator["representative_bucket_count"]),
            "reconstructed_after_outcome": False,
        },
        "decision_boundary": (
            "One-pass holdout scoring only. Persist result regardless of outcome. "
            "Do not retune Ridge, P2, Pre-Live v2, or C1 v8 using event 5."
        ),
    }
    return result, rows


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
    parser.add_argument("--c1-comparator", type=Path, required=True)
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
    result, rows = run_holdout(
        development_stage0_csv=args.development_stage0_csv,
        payload=payload,
        structural_artifact_dir=args.structural_artifact_dir,
        pre_live_manifest=args.pre_live_manifest,
        stage2_manifest_path=args.stage2_manifest,
        capacity_audit_path=args.capacity_audit,
        c1_comparator_path=args.c1_comparator,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    rows.to_csv(args.output_csv, index=False)
    print(json.dumps({
        "status": result["status"],
        "holdout": result["holdout"],
        "scores": result["scores"],
        "c1_v8_prospective_comparator": result["c1_v8_prospective_comparator"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
