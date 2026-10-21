#!/usr/bin/env python3
"""Materialize genuine pre-outcome Long72 P2 forecasts from frozen package v1.

The input must come from the forward-only gateway and contain no target outcome.
The script:
1. verifies the frozen package manifest;
2. reconstructs the frozen T-3 + b2 current-season anchor using only prior,
   already-completed same-season home matches;
3. applies the frozen inventory-linear-extrapolation Stage 1;
4. applies frozen P2 observation-maturity reliability;
5. emits rows for immutable pre-outcome persistence.

No model fitting or parameter selection occurs here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay
from ml.d2_long72_anchor_contract_v1 import (
    build_replay_events,
    compose_context,
    utc,
)
from ml.d2_long72_stage1_model_tournament_v1 import (
    governed_forecast,
    inventory_linear_delta,
)
from ml.d2_long72_stage2_reliability_gating_v1 import (
    add_causal_reliability_state,
    maturity_reliability,
)

PACKAGE_ID = "d2-long72-stage2-p2-observation-maturity-2026-10-21-v1"
STAGE1_EXPERT_ID = "inventory-linear-extrapolation"
STAGE2_POLICY_ID = "P2-observation-maturity"
EXPECTED_MANIFEST_SHA256 = "2a523ae461a43a9d66e3870c836b56588eb582dd52513cfb9d8f638953f08872"
EXPECTED_FEATURE_CONTRACT = "live-trajectory-v1.1"
FREEZE_CUTOFF = pd.Timestamp("2026-10-21T17:37:07Z")
COMPLETION_BUFFER_HOURS = 3
B2_RESIDUAL_CLIP = 0.25
B2_EWMA_ALPHA = 0.50
B2_SHRINK_K_T3 = 2
B2_MIN_PRIOR_HOME_MATCHES_T3 = 3
B2_CORRECTION_CAP_SHARE = 0.05


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_input(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if payload.get("ok") is False:
        raise RuntimeError(f"forward gateway returned failure: {payload.get('error')}")
    forward = payload.get("forward") if isinstance(payload.get("forward"), dict) else payload
    if forward.get("version") != "d2-long72-forward-inputs-v1":
        raise RuntimeError(f"unexpected forward input version: {forward.get('version')}")
    if forward.get("packageId") != PACKAGE_ID:
        raise RuntimeError("forward input package mismatch")
    if bool(forward.get("outcomeAccessAllowed")):
        raise RuntimeError("forward input illegally allows outcome access")
    requested_at = utc(forward["requestedAt"])
    if requested_at < FREEZE_CUTOFF:
        raise RuntimeError("requested_at predates package freeze")
    return payload


def verify_manifest(path: Path) -> dict[str, Any]:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError(
            f"Long72 package manifest drift actual={actual_sha} expected={EXPECTED_MANIFEST_SHA256}"
        )
    manifest = json.loads(path.read_text())
    if manifest.get("package_id") != PACKAGE_ID:
        raise RuntimeError("Long72 package ID drift")
    if manifest.get("status") != "FROZEN_HISTORICAL_RESEARCH_PACKAGE":
        raise RuntimeError("Long72 package is not frozen")
    if manifest.get("production_change") is not False:
        raise RuntimeError("Long72 manifest unexpectedly changes production")
    if manifest["stage1"]["expert_id"] != STAGE1_EXPERT_ID:
        raise RuntimeError("Stage1 expert drift")
    if float(manifest["stage1"]["correction_cap_occupancy"]) != 0.1:
        raise RuntimeError("Stage1 correction cap drift")
    if manifest["stage2"]["policy_id"] != STAGE2_POLICY_ID:
        raise RuntimeError("Stage2 policy drift")
    return manifest


def support(payload: dict[str, Any], key: str, nested_key: str) -> list[dict[str, Any]]:
    value = payload.get(key) or {}
    rows = value.get(nested_key) if isinstance(value, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError(f"missing support payload {key}.{nested_key}")
    return rows


def _target_event_dict(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket_event_id": int(event["ticket_event_id"]),
        "club_slug": str(event["club_slug"]),
        "home_team": str(event["home_team"]),
        "away_team": str(event["away_team"]),
        "season": str(event["season"]),
        "round_no": int(event["round_no"]),
        "kickoff_at": utc(event["kickoff_at"]).isoformat(),
        "home_club_key": str(event["home_club_key"]),
        "away_club_key": str(event["away_club_key"]),
        "stadium_capacity": int(event["stadium_capacity"]),
    }


def compute_b2_t3_correction(
    residual_fractions: list[float],
    target_capacity: float,
) -> dict[str, Any]:
    """Apply the frozen T-3 b2 policy to chronological clipped residuals."""
    ewma: float | None = None
    for value in residual_fractions:
        clipped = float(np.clip(value, -B2_RESIDUAL_CLIP, B2_RESIDUAL_CLIP))
        ewma = clipped if ewma is None else (
            B2_EWMA_ALPHA * clipped + (1.0 - B2_EWMA_ALPHA) * ewma
        )
    n = len(residual_fractions)
    active = n >= B2_MIN_PRIOR_HOME_MATCHES_T3
    correction = 0.0
    if active:
        assert ewma is not None
        shrink = n / (n + B2_SHRINK_K_T3)
        raw_correction = shrink * ewma * float(target_capacity)
        cap = B2_CORRECTION_CAP_SHARE * float(target_capacity)
        correction = float(np.clip(raw_correction, -cap, cap))
    return {
        "prior_home_matches": n,
        "ewma_residual_fraction": ewma,
        "active": active,
        "correction_seats": correction,
    }


def reconstruct_t3_b2_anchor(
    *,
    event: dict[str, Any],
    attendance_rows: list[dict[str, Any]],
    sporting_rows: list[dict[str, Any]],
    alias_rows: list[dict[str, Any]],
    capacity_rows: list[dict[str, Any]],
    artifact_dir: Path,
) -> dict[str, Any]:
    """Reconstruct frozen T-3+b2 without any target label."""
    target = _target_event_dict(event)
    target_id = int(target["ticket_event_id"])
    target_kickoff = utc(target["kickoff_at"])
    target_as_of = target_kickoff - pd.Timedelta(days=3)
    target_club = str(target["home_club_key"])
    target_season = str(target["season"])

    # Reuse the historical contract's verified attendance->sporting->capacity
    # mapping, but pass no tracked targets so every attendance row is synthetic.
    history_context = compose_context(
        {"events": []},
        {"attendance": attendance_rows},
        {"sportingMatches": sporting_rows},
        {"aliases": alias_rows},
    )
    history_events, actual_by_id, _ = build_replay_events(
        history_context, capacity_rows
    )

    prior_sources = [
        row for row in history_events
        if str(row["home_club_key"]) == target_club
        and str(row["season"]) == target_season
        and utc(row["kickoff_at"]) + pd.Timedelta(hours=COMPLETION_BUFFER_HOURS) < target_as_of
    ]

    replay_payload = dict(history_context)
    replay_payload["events"] = [*prior_sources, target]
    priors = _event_prior_replay(replay_payload, artifact_dir)
    t3 = priors[(priors["horizon"] == "T-3") & priors["prior_p50"].notna()].copy()
    if t3.empty:
        raise RuntimeError(f"no forecastable T-3 priors for target event={target_id}")

    target_rows = t3[t3["ticket_event_id"].astype(int) == target_id]
    if len(target_rows) != 1:
        raise RuntimeError(
            f"expected one target T-3 prior event={target_id}, got {len(target_rows)}"
        )
    structural_t3 = float(target_rows.iloc[0]["prior_p50"])

    source_predictions = {
        int(row["ticket_event_id"]): float(row["prior_p50"])
        for row in t3.to_dict("records")
        if int(row["ticket_event_id"]) != target_id
    }
    source_events = [
        row for row in prior_sources if int(row["ticket_event_id"]) in source_predictions
    ]
    source_events.sort(key=lambda row: utc(row["kickoff_at"]))

    residuals: list[float] = []
    used_sources: list[dict[str, Any]] = []
    for source in source_events:
        source_id = int(source["ticket_event_id"])
        base = float(source_predictions[source_id])
        actual = float(actual_by_id[source_id])
        capacity = float(source["stadium_capacity"])
        residual = float(np.clip((actual - base) / capacity, -B2_RESIDUAL_CLIP, B2_RESIDUAL_CLIP))
        residuals.append(residual)
        used_sources.append({
            "synthetic_event_id": source_id,
            "kickoff_at": utc(source["kickoff_at"]).isoformat(),
            "actual_attendance": actual,
            "structural_t3_p50": base,
            "stadium_capacity": int(capacity),
            "residual_fraction_clipped": residual,
        })

    b2 = compute_b2_t3_correction(
        residuals, float(target["stadium_capacity"])
    )
    n = int(b2["prior_home_matches"])
    ewma = b2["ewma_residual_fraction"]
    active = bool(b2["active"])
    correction = float(b2["correction_seats"])

    anchor = float(np.clip(
        structural_t3 + correction,
        0.0,
        float(target["stadium_capacity"]),
    ))
    return {
        "structural_t3_p50": structural_t3,
        "b2_prior_home_matches": n,
        "b2_ewma_residual_fraction": ewma,
        "b2_active": active,
        "b2_correction_seats": correction,
        "anchor_p50": anchor,
        "source_events": used_sources,
        "target_as_of_at": target_as_of.isoformat(),
    }


def materialize_event(
    *,
    event: dict[str, Any],
    rows: list[dict[str, Any]],
    anchor: dict[str, Any],
    requested_at: pd.Timestamp,
    github_sha: str | None,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame_records: list[dict[str, Any]] = []
    source_by_asof: dict[pd.Timestamp, dict[str, Any]] = {}
    for row in rows:
        features = dict(row.get("features") or {})
        as_of = utc(features.get("as_of_at") or row["requested_as_of_at"])
        if not bool(features.get("point_in_time_validated")):
            raise RuntimeError(f"non-PIT live row event={event['ticket_event_id']}")
        if str(features.get("feature_version")) != EXPECTED_FEATURE_CONTRACT:
            raise RuntimeError(
                f"feature contract drift event={event['ticket_event_id']} "
                f"actual={features.get('feature_version')}"
            )
        hours = float(row["hours_to_kickoff"])
        if not (24.0 < hours <= 72.0):
            raise RuntimeError("live row outside Long72 frozen scope")
        if as_of < FREEZE_CUTOFF or as_of > requested_at:
            raise RuntimeError("live row violates post-freeze/requested_at boundary")

        rec = {
            "ticket_event_id": int(event["ticket_event_id"]),
            "as_of_at": as_of,
            "hours_to_kickoff": hours,
            "stadium_capacity": float(event["stadium_capacity"]),
            "anchor_p50": float(anchor["anchor_p50"]),
            "anchor_expected_occupancy": float(anchor["anchor_p50"]) / float(event["stadium_capacity"]),
            **features,
        }
        frame_records.append(rec)
        source_by_asof[as_of] = row

    frame = pd.DataFrame(frame_records).sort_values("as_of_at").reset_index(drop=True)
    frame = add_causal_reliability_state(frame)
    raw_delta = inventory_linear_delta(frame)
    stage1_forecast, governed_delta = governed_forecast(frame, raw_delta)
    reliability = maturity_reliability(frame)
    capacity = frame["stadium_capacity"].astype(float).to_numpy()
    anchor_values = frame["anchor_p50"].astype(float).to_numpy()
    final = np.clip(
        anchor_values + reliability * governed_delta * capacity,
        0.0,
        capacity,
    )

    output: list[dict[str, Any]] = []
    prior = dict(event["prior"])
    source_prior_p50 = float(prior["p50"])
    if abs(source_prior_p50 - float(anchor["structural_t3_p50"])) > 0.02:
        raise RuntimeError(
            f"artifact/database T-3 mismatch event={event['ticket_event_id']} "
            f"artifact={anchor['structural_t3_p50']} db={source_prior_p50}"
        )
    if utc(prior["target_as_of_at"]) > frame["as_of_at"].min():
        raise RuntimeError("future T-3 checkpoint used")

    for idx, row in frame.iterrows():
        as_of = utc(row["as_of_at"])
        source = source_by_asof[as_of]
        features = dict(source["features"])
        item = {
            "ticket_event_id": int(event["ticket_event_id"]),
            "source_prior_id": int(prior["source_prior_id"]),
            "source_snapshot_id": int(source["requested_snapshot_id"]),
            "as_of_at": as_of.isoformat(),
            "kickoff_at": utc(event["kickoff_at"]).isoformat(),
            "hours_to_kickoff": float(row["hours_to_kickoff"]),
            "bucket_6h": int(source["bucket_6h"]),
            "stadium_capacity": int(event["stadium_capacity"]),
            "structural_t3_p50": source_prior_p50,
            "b2_prior_home_matches": int(anchor["b2_prior_home_matches"]),
            "b2_ewma_residual_fraction": (
                None if anchor["b2_ewma_residual_fraction"] is None
                else float(anchor["b2_ewma_residual_fraction"])
            ),
            "b2_correction_seats": float(anchor["b2_correction_seats"]),
            "anchor_p50": float(anchor["anchor_p50"]),
            "raw_inventory_delta_occupancy": float(raw_delta[idx]),
            "governed_delta_occupancy": float(governed_delta[idx]),
            "stage1_inventory_p50": float(stage1_forecast[idx]),
            "stage2_observation_index": int(row["stage2_observation_index"]),
            "stage2_reliability": float(reliability[idx]),
            "final_p50": float(final[idx]),
            "package_id": PACKAGE_ID,
            "stage1_expert_id": STAGE1_EXPERT_ID,
            "stage2_policy_id": STAGE2_POLICY_ID,
            "package_manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "feature_contract": EXPECTED_FEATURE_CONTRACT,
            "github_sha": github_sha,
            "input_lineage": {
                "requested_snapshot_id": int(source["requested_snapshot_id"]),
                "feature_snapshot_id": int(features["snapshot_id"]),
                "source_snapshot_captured_at": as_of.isoformat(),
                "prior_target_as_of_at": utc(prior["target_as_of_at"]).isoformat(),
                "prior_model_spec_id": prior["model_spec_id"],
                "prior_model_family": prior["model_family"],
                "prior_feature_contract": prior["feature_contract"],
                "capacity_source_name": event.get("capacity_source_name"),
                "capacity_source_url": event.get("capacity_source_url"),
                "capacity_verification_status": event.get("capacity_verification_status"),
            },
            "metadata": {
                "evidence_class": "true_post_freeze_prospective",
                "production_change": False,
                "b2_active": bool(anchor["b2_active"]),
                "b2_source_events": anchor["source_events"],
                "signal_readiness": features.get("signal_readiness"),
                "feature_quality": features.get("feature_quality"),
            },
        }
        output.append(item)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--package-manifest", type=Path, required=True)
    parser.add_argument("--structural-artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--github-sha")
    args = parser.parse_args()

    verify_manifest(args.package_manifest)
    payload = load_input(args.input)
    forward = payload.get("forward") if isinstance(payload.get("forward"), dict) else payload
    requested_at = utc(forward["requestedAt"])

    attendance_rows = support(payload, "attendance", "attendance")
    sporting_rows = support(payload, "sporting", "sportingMatches")
    alias_rows = support(payload, "aliases", "aliases")
    capacity_rows = support(payload, "capacity", "rows")

    events = {
        int(row["ticket_event_id"]): row
        for row in forward.get("events") or []
    }
    live_by_event: dict[int, list[dict[str, Any]]] = {}
    for row in forward.get("liveRows") or []:
        live_by_event.setdefault(int(row["ticket_event_id"]), []).append(row)

    observations: list[dict[str, Any]] = []
    anchor_diagnostics: list[dict[str, Any]] = []
    for event_id, event in sorted(events.items()):
        anchor = reconstruct_t3_b2_anchor(
            event=event,
            attendance_rows=attendance_rows,
            sporting_rows=sporting_rows,
            alias_rows=alias_rows,
            capacity_rows=capacity_rows,
            artifact_dir=args.structural_artifact_dir,
        )
        event_observations = materialize_event(
            event=event,
            rows=live_by_event.get(event_id, []),
            anchor=anchor,
            requested_at=requested_at,
            github_sha=args.github_sha,
        )
        observations.extend(event_observations)
        anchor_diagnostics.append({
            "ticket_event_id": event_id,
            "structural_t3_p50": anchor["structural_t3_p50"],
            "b2_prior_home_matches": anchor["b2_prior_home_matches"],
            "b2_active": anchor["b2_active"],
            "b2_correction_seats": anchor["b2_correction_seats"],
            "anchor_p50": anchor["anchor_p50"],
            "materialized_rows": len(event_observations),
        })

    result = {
        "version": "d2-long72-forward-materialize-v1",
        "status": "READY_FOR_PRE_OUTCOME_PERSISTENCE",
        "package_id": PACKAGE_ID,
        "requested_at": requested_at.isoformat(),
        "outcome_access_allowed": False,
        "model_training_performed": False,
        "production_change": False,
        "event_count": len(events),
        "observation_count": len(observations),
        "anchors": anchor_diagnostics,
        "observations": observations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "version": result["version"],
        "status": result["status"],
        "event_count": result["event_count"],
        "observation_count": result["observation_count"],
        "anchors": anchor_diagnostics,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
