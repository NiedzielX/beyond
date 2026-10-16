#!/usr/bin/env python3
"""Run frozen C1 v2+v8 shadow inference from a forward-only input payload.

Inference only: this module loads the committed artifact and never fits a model.
It emits prospective evidence rows for a privileged gateway to persist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ml.demand_engine.c1_shadow_runtime_v8 import (
    C1ShadowRuntimeV8,
    FEATURE_CONTRACT,
    LIVE_MODEL_ID,
    POLICY_ID,
    apply_v8_policy,
)


EXPECTED_PACKAGE = "c1-shadow-v8-frozen-2026-10-16-n9"
BOOLEAN_FEATURES = {
    "release_activity_flag",
    "sector_coverage_change_flag",
    "unexplained_inventory_increase_flag",
    "data_gap_detected",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def numeric(value: Any) -> float:
    parsed = pd.to_numeric(value, errors="coerce")
    return float(parsed) if pd.notna(parsed) else float("nan")


def feature_record(candidate: dict, representative: dict, runtime: C1ShadowRuntimeV8) -> dict[str, Any]:
    prior = candidate["prior"]
    f = representative.get("features") or {}
    capacity = float(prior["stadium_capacity"])
    prior_p50 = float(prior["p50"])
    rec: dict[str, Any] = {
        "prior_p50": prior_p50,
        "prior_expected_occupancy": prior_p50 / capacity,
        "stadium_capacity": capacity,
        "signal_ready": 1.0 if str(f.get("signal_readiness")) == "ready" else 0.0,
        "feature_quality_good": 1.0 if str(f.get("feature_quality")) in {"sector_matched_plus_raw", "raw_only"} else 0.0,
    }
    for feature in runtime.features:
        if feature in rec:
            continue
        value = f.get(feature)
        if feature in BOOLEAN_FEATURES:
            rec[feature] = np.nan if value is None else float(bool(value))
        else:
            rec[feature] = numeric(value)
    return rec


def run_candidate(candidate: dict, runtime: C1ShadowRuntimeV8, artifact_sha256: str, requested_at: pd.Timestamp) -> dict[str, Any]:
    representatives = sorted(
        candidate.get("representatives") or [],
        key=lambda row: pd.Timestamp(row["requested_as_of_at"]),
    )
    if not representatives:
        raise RuntimeError(f"event {candidate.get('ticket_event_id')} has no final-24h representatives")
    if len(representatives) > 4:
        raise RuntimeError(f"event {candidate.get('ticket_event_id')} exceeds frozen 4-bucket contract")

    records = [feature_record(candidate, rep, runtime) for rep in representatives]
    frame = pd.DataFrame(records)
    live_predictions = runtime.predict_live_p50(frame)

    as_of = pd.to_datetime([rep["requested_as_of_at"] for rep in representatives], utc=True)
    if as_of[-1] > requested_at:
        raise RuntimeError(f"event {candidate.get('ticket_event_id')} contains future representative")
    elapsed_hours = (as_of - as_of[0]).total_seconds() / 3600.0

    prior = candidate["prior"]
    capacity = float(prior["stadium_capacity"])
    prior_p50 = float(prior["p50"])
    decision = apply_v8_policy(
        prior_p50=prior_p50,
        stadium_capacity=capacity,
        live_history_p50=live_predictions,
        elapsed_hours=elapsed_hours,
    )

    latest_rep = representatives[-1]
    latest_features = latest_rep.get("features") or {}
    latest_as_of = pd.Timestamp(latest_rep["requested_as_of_at"])
    if latest_as_of.tzinfo is None:
        latest_as_of = latest_as_of.tz_localize("UTC")
    else:
        latest_as_of = latest_as_of.tz_convert("UTC")

    if str(prior.get("horizon")) != "T-1" or not bool(prior.get("point_in_time_validated")):
        raise RuntimeError(f"event {candidate.get('ticket_event_id')} is not anchored to PIT-valid T-1 prior")
    if not all(bool((rep.get("features") or {}).get("point_in_time_validated")) for rep in representatives):
        raise RuntimeError(f"event {candidate.get('ticket_event_id')} contains non-PIT live feature")

    return {
        "ticket_event_id": int(candidate["ticket_event_id"]),
        "source_prior_id": int(prior["source_prior_id"]),
        "source_snapshot_id": int(latest_rep["requested_snapshot_id"]),
        "as_of_at": latest_as_of.isoformat(),
        "hours_to_kickoff": numeric(latest_features.get("hours_to_kickoff")),
        "stadium_capacity": int(capacity),
        "structural_prior_p50": prior_p50,
        "v2_live_p50": float(decision["live_p50"]),
        "abs_disagreement_occupancy": float(decision["abs_disagreement_occupancy"]),
        "live_observation_count_to_date": int(decision["live_observation_count_to_date"]),
        "live_slope_occupancy_per_hour_to_date": decision["live_slope_occupancy_per_hour_to_date"],
        "selected_expert": decision["selected_expert"],
        "policy_prediction": float(decision["policy_prediction"]),
        "reason_code": decision["reason_code"],
        "package_version": runtime.package_version,
        "live_model_id": runtime.live_model_id,
        "policy_id": runtime.policy_id,
        "artifact_sha256": artifact_sha256,
        "feature_contract": runtime.feature_contract,
        "metadata": {
            "status": "EXPERIMENTAL_SHADOW",
            "production_activation": False,
            "structural_prior_model_spec_id": prior.get("model_spec_id"),
            "structural_prior_artifact_version": prior.get("artifact_version"),
            "representative_bucket_6h": [int(rep["bucket_6h"]) for rep in representatives],
            "representative_snapshot_ids": [int(rep["requested_snapshot_id"]) for rep in representatives],
            "representative_as_of_at": [pd.Timestamp(rep["requested_as_of_at"]).isoformat() for rep in representatives],
            "live_history_p50": [float(value) for value in live_predictions],
            "input_feature_version": latest_features.get("feature_version"),
            "input_signal_readiness": latest_features.get("signal_readiness"),
            "input_feature_quality": latest_features.get("feature_quality"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    if payload.get("version") != "c1-shadow-v8-inputs-v1":
        raise RuntimeError(f"unexpected C1 shadow input version: {payload.get('version')}")
    if payload.get("package_version") != EXPECTED_PACKAGE:
        raise RuntimeError(f"unexpected C1 shadow package in input: {payload.get('package_version')}")

    manifest = json.loads((args.artifact_dir / "manifest.json").read_text())
    if manifest.get("package_version") != EXPECTED_PACKAGE:
        raise RuntimeError("frozen C1 shadow manifest package mismatch")
    if manifest.get("status") != "EXPERIMENTAL_SHADOW" or manifest.get("production_activation") is not False:
        raise RuntimeError("C1 shadow artifact is not explicitly shadow-only")
    if manifest.get("live_model_id") != LIVE_MODEL_ID or manifest.get("policy_id") != POLICY_ID:
        raise RuntimeError("C1 shadow model/policy manifest mismatch")
    if manifest.get("feature_contract") != FEATURE_CONTRACT:
        raise RuntimeError("C1 shadow feature contract mismatch")

    artifact_path = args.artifact_dir / manifest["artifact"]["filename"]
    artifact_sha = sha256_file(artifact_path)
    if artifact_sha != manifest["artifact"]["sha256"]:
        raise RuntimeError("C1 shadow artifact hash mismatch")
    runtime: C1ShadowRuntimeV8 = joblib.load(artifact_path)
    if runtime.package_version != EXPECTED_PACKAGE:
        raise RuntimeError("loaded C1 shadow runtime package mismatch")

    requested_at = pd.Timestamp(payload["requested_at"])
    if requested_at.tzinfo is None:
        requested_at = requested_at.tz_localize("UTC")
    else:
        requested_at = requested_at.tz_convert("UTC")

    predictions = [
        run_candidate(candidate, runtime, artifact_sha, requested_at)
        for candidate in payload.get("candidates") or []
    ]
    result = {
        "version": "c1-shadow-v8-predictions-v1",
        "status": "EXPERIMENTAL_SHADOW",
        "production_activation": False,
        "requested_at": requested_at.isoformat(),
        "package_version": runtime.package_version,
        "artifact_sha256": artifact_sha,
        "candidate_count": int(payload.get("candidate_count") or 0),
        "prediction_count": len(predictions),
        "predictions": predictions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({
        "version": result["version"],
        "requested_at": result["requested_at"],
        "package_version": result["package_version"],
        "candidate_count": result["candidate_count"],
        "prediction_count": result["prediction_count"],
        "decisions": [
            {
                "ticket_event_id": row["ticket_event_id"],
                "as_of_at": row["as_of_at"],
                "selected_expert": row["selected_expert"],
                "policy_prediction": row["policy_prediction"],
                "reason_code": row["reason_code"],
            }
            for row in predictions
        ],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
