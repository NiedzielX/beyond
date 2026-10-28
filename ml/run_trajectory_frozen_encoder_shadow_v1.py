"""Run immutable prospective shadow inference for the frozen encoder/head v1.

The runner talks only to the OIDC-protected shadow gateway. It never receives or
uses attendance outcomes for prediction construction.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import numpy as np

from ml.demand_engine.trajectory_frozen_encoder_attendance_head_v1 import (
    CORRECTION_RATIO_CAP,
    PRECOMMIT_ID,
    build_encoder_sequence_from_pairs_v1,
    encode_sequence_v1,
    load_attendance_head_v1,
    load_frozen_encoder_v1,
)

MODEL_VERSION = PRECOMMIT_ID
DATASET_VERSION = "trajectory-frozen-encoder-shadow-input-v1"
GATEWAY_URL = "https://adchzwqboeekhokapxqi.supabase.co/functions/v1/trajectory_frozen_encoder_shadow_v1"
SUPPORTED_DAYS = (7, 3, 1)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _iso(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timezone-aware timestamp required: {value}")
    return parsed.isoformat()


def _post(token: str, body: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        GATEWAY_URL,
        data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("ok") is not True:
        raise RuntimeError(f"shadow gateway error: {payload}")
    return payload


def _raw_ratio(head, embedding: np.ndarray) -> float:
    mean = np.asarray(head.scaler_mean, dtype=float)
    std = np.asarray(head.scaler_std, dtype=float)
    coef = np.asarray(head.ridge_coef, dtype=float)
    standardized = (embedding.astype(float) - mean) / std
    return float(np.dot(coef, standardized) + head.ridge_intercept)


def _candidate_manifest_sha(head_bytes: bytes, encoder_bytes: bytes) -> str:
    payload = {
        "model_version": MODEL_VERSION,
        "dataset_version": DATASET_VERSION,
        "head_sha256": _sha256_bytes(head_bytes),
        "encoder_sha256": _sha256_bytes(encoder_bytes),
        "supported_days": list(SUPPORTED_DAYS),
        "correction_ratio_cap": CORRECTION_RATIO_CAP,
    }
    return _sha256_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _prediction_identity_sha(*, target: dict[str, Any], candidate_manifest_sha: str, snapshot_ids: list[int]) -> str:
    payload = {
        "ticket_event_id": int(target["ticket_event_id"]),
        "days_to_event": int(target["days_to_event"]),
        "target_as_of_at": _iso(str(target["target_as_of_at"])),
        "model_version": MODEL_VERSION,
        "candidate_manifest_sha256": candidate_manifest_sha,
        "snapshot_ids": snapshot_ids,
        "structural_prior_id": target.get("structural_prior_id"),
    }
    return _sha256_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _base_attempt_payload(*, target: dict[str, Any], candidate_manifest_sha: str, status: str, status_reason: str | None, observations: list[dict[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "version": "daily-trajectory-attempt-v1",
        "ticket_event_id": int(target["ticket_event_id"]),
        "days_to_event": int(target["days_to_event"]),
        "target_as_of_at": _iso(str(target["target_as_of_at"])),
        "model_version": MODEL_VERSION,
        "precommit_id": PRECOMMIT_ID,
        "dataset_version": DATASET_VERSION,
        "dataset_manifest_sha256": candidate_manifest_sha,
        "status": status,
        "status_reason": status_reason,
        "target_values_used": False,
        "production_change": False,
        "live_adjustment": 0,
        "input_payload": {
            "candidate_manifest_sha256": candidate_manifest_sha,
            "trajectory_observation_count": len(observations),
            "structural_model_spec_id": target.get("structural_model_spec_id"),
            "production_change": False,
        },
    }
    if observations:
        payload["source_snapshot_id"] = int(observations[-1]["snapshot_id"])
        payload["source_snapshot_captured_at"] = _iso(str(observations[-1]["captured_at"]))
    if target.get("structural_prior_id") is not None:
        payload["incumbent_source"] = "structural_prior_forecasts_v1"
        payload["incumbent_row_id"] = int(target["structural_prior_id"])
        payload["incumbent_p50"] = float(target["structural_p50"])
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--encoder", required=True, type=Path)
    parser.add_argument("--head", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    args = parser.parse_args()

    token = os.environ.get("TRAJECTORY_SHADOW_OIDC_TOKEN", "")
    if not token:
        raise RuntimeError("TRAJECTORY_SHADOW_OIDC_TOKEN is required")

    encoder_bytes = args.encoder.read_bytes()
    head_bytes = args.head.read_bytes()
    encoder, _, encoder_artifact_sha = load_frozen_encoder_v1(args.encoder)
    head = load_attendance_head_v1(args.head)
    if head.encoder_artifact_sha256 != encoder_artifact_sha:
        raise ValueError("head/encoder artifact SHA mismatch")

    candidate_manifest_sha = _candidate_manifest_sha(head_bytes, encoder_bytes)
    due = _post(token, {"action": "due"})
    if due.get("model_version") != MODEL_VERSION:
        raise ValueError("due-target model version mismatch")
    if due.get("target_values_used") is not False or due.get("production_change") is not False:
        raise ValueError("due-target evidence guard failed")

    summary: dict[str, Any] = {
        "version": "trajectory-frozen-encoder-shadow-run-v1",
        "candidate_manifest_sha256": candidate_manifest_sha,
        "due_target_count": int(due.get("target_count", 0)),
        "attempts": [],
        "predictions": [],
        "production_change": False,
    }

    for target in due.get("targets", []):
        days = int(target["days_to_event"])
        if days not in SUPPORTED_DAYS:
            raise ValueError(f"unexpected due horizon: {days}")
        observations = list(target.get("observations") or [])

        if target.get("structural_prior_id") is None or target.get("structural_p50") is None:
            attempt_payload = _base_attempt_payload(
                target=target,
                candidate_manifest_sha=candidate_manifest_sha,
                status="NO_INCUMBENT",
                status_reason="No PIT-valid structural prior existed by target cutoff.",
                observations=observations,
            )
            result = _post(token, {"action": "attempt", "payload": attempt_payload})
            summary["attempts"].append({"ticket_event_id": target["ticket_event_id"], "days_to_event": days, "status": "NO_INCUMBENT", "result": result.get("result")})
            continue

        p50 = float(target["structural_p50"])
        if p50 <= 0:
            attempt_payload = _base_attempt_payload(
                target=target,
                candidate_manifest_sha=candidate_manifest_sha,
                status="NO_INCUMBENT",
                status_reason="Structural P50 was not positive.",
                observations=observations,
            )
            result = _post(token, {"action": "attempt", "payload": attempt_payload})
            summary["attempts"].append({"ticket_event_id": target["ticket_event_id"], "days_to_event": days, "status": "NO_INCUMBENT", "result": result.get("result")})
            continue

        try:
            pairs = [[float(row["hours_to_kickoff"]), int(row["available_total"])] for row in observations]
            sequence = build_encoder_sequence_from_pairs_v1(pairs, horizon=f"T-{days}")
            embedding = encode_sequence_v1(encoder, sequence)
        except Exception as exc:
            attempt_payload = _base_attempt_payload(
                target=target,
                candidate_manifest_sha=candidate_manifest_sha,
                status="MODEL_INPUT_INSUFFICIENT",
                status_reason=f"Frozen encoder input gate failed: {type(exc).__name__}: {exc}",
                observations=observations,
            )
            result = _post(token, {"action": "attempt", "payload": attempt_payload})
            summary["attempts"].append({"ticket_event_id": target["ticket_event_id"], "days_to_event": days, "status": "MODEL_INPUT_INSUFFICIENT", "result": result.get("result")})
            continue

        source_hours = days * 24.0
        context_obs = [
            row for row in observations
            if float(row["hours_to_kickoff"]) <= source_hours + 168.0 + 1e-9
        ]
        if not context_obs:
            raise AssertionError("encoder sequence built without context observations")

        raw_ratio = _raw_ratio(head, embedding)
        clipped_ratio = float(np.clip(raw_ratio, -head.correction_ratio_cap, head.correction_ratio_cap))
        challenger = max(0.0, p50 * (1.0 + clipped_ratio))
        capacity = target.get("stadium_capacity")
        if capacity is not None and int(capacity) > 0:
            challenger = min(challenger, float(capacity))

        attempt_payload = _base_attempt_payload(
            target=target,
            candidate_manifest_sha=candidate_manifest_sha,
            status="PREDICTION_READY",
            status_reason=None,
            observations=observations,
        )
        attempt_payload["observed_prefix_start_at"] = _iso(str(context_obs[0]["captured_at"]))
        attempt_payload["observed_prefix_end_at"] = _iso(str(context_obs[-1]["captured_at"]))
        attempt_payload["input_payload"].update({
            "encoder_embedding": [float(x) for x in embedding],
            "encoder_sequence_length": int(sequence.shape[0]),
            "head_raw_ratio": raw_ratio,
            "head_clipped_ratio": clipped_ratio,
            "head_cap_hit": abs(raw_ratio) > head.correction_ratio_cap,
            "encoder_artifact_sha256": encoder_artifact_sha,
            "head_fit_manifest_sha256": head.fit_manifest_sha256,
        })
        attempt_result = _post(token, {"action": "attempt", "payload": attempt_payload})
        registry = attempt_result.get("result") or {}
        attempt_id = registry.get("attempt_id")
        inserted = registry.get("inserted") is True
        summary["attempts"].append({"ticket_event_id": target["ticket_event_id"], "days_to_event": days, "status": "PREDICTION_READY", "result": registry})
        if not inserted or attempt_id is None:
            continue

        snapshot_ids = [int(row["snapshot_id"]) for row in context_obs]
        identity_sha = _prediction_identity_sha(
            target=target,
            candidate_manifest_sha=candidate_manifest_sha,
            snapshot_ids=snapshot_ids,
        )
        prediction_payload: dict[str, Any] = {
            "version": "daily-trajectory-prediction-v1",
            "attempt_id": int(attempt_id),
            "model_version": MODEL_VERSION,
            "precommit_id": PRECOMMIT_ID,
            "dataset_version": DATASET_VERSION,
            "dataset_manifest_sha256": candidate_manifest_sha,
            "prediction_identity_sha256": identity_sha,
            "challenger_p50": challenger,
            "trajectory_residual": challenger - p50,
            "target_values_used": False,
            "production_change": False,
            "prediction_payload": {
                "raw_ratio": raw_ratio,
                "clipped_ratio": clipped_ratio,
                "cap_hit": abs(raw_ratio) > head.correction_ratio_cap,
                "encoder_artifact_sha256": encoder_artifact_sha,
                "head_fit_manifest_sha256": head.fit_manifest_sha256,
                "source_snapshot_ids": snapshot_ids,
                "production_change": False,
            },
        }
        if capacity is not None and int(capacity) > 0:
            prediction_payload["stadium_capacity"] = int(capacity)

        prediction_result = _post(token, {"action": "prediction", "payload": prediction_payload})
        summary["predictions"].append({
            "ticket_event_id": target["ticket_event_id"],
            "days_to_event": days,
            "incumbent_p50": p50,
            "raw_ratio": raw_ratio,
            "clipped_ratio": clipped_ratio,
            "challenger_p50": challenger,
            "result": prediction_result.get("result"),
        })

    score_result = _post(token, {"action": "score"})
    summary["score_result"] = score_result.get("result")
    summary["attempt_count"] = len(summary["attempts"])
    summary["prediction_count"] = len(summary["predictions"])

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "version": summary["version"],
        "due_target_count": summary["due_target_count"],
        "attempt_count": summary["attempt_count"],
        "prediction_count": summary["prediction_count"],
        "score_result": summary["score_result"],
        "production_change": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
