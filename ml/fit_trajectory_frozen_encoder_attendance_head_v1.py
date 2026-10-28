"""Fit the single precommitted frozen-encoder attendance head v1.

This runner intentionally does NOT compute historical attendance MAE. The exposed
10-event cohort is used only to fit one fixed Ridge head for future prospective
shadow evaluation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from ml.demand_engine.trajectory_frozen_encoder_attendance_head_v1 import (
    PRECOMMIT_ID,
    build_encoder_sequence_from_pairs_v1,
    encode_sequence_v1,
    fit_attendance_head_v1,
    head_to_json_dict,
    load_frozen_encoder_v1,
)

EXPECTED_EXPORT_VERSION = "trajectory-development-export-v1"
EXPECTED_COHORT_VERSION = "trajectory-development-cohort-v1"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--cohort", required=True, type=Path)
    parser.add_argument("--encoder", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    export = _load(args.input)
    cohort = _load(args.cohort)

    if export.get("ok") is not True or export.get("version") != EXPECTED_EXPORT_VERSION:
        raise ValueError("unexpected historical development export")
    if cohort.get("version") != EXPECTED_COHORT_VERSION:
        raise ValueError("unexpected frozen cohort")
    if int(export.get("event_count", 0)) != 10 or int(export.get("row_count", 0)) != 19:
        raise ValueError("attendance head v1 requires exact 10-event / 19-row export")

    expected = {
        (int(event["ticket_event_id"]), str(horizon))
        for event in cohort["events"]
        for horizon in event["eligible_horizons"]
    }
    rows: dict[tuple[int, str], dict[str, Any]] = {}
    for row in export.get("rows", []):
        key = (int(row["ticket_event_id"]), str(row["horizon"]))
        if key not in expected:
            continue
        if key in rows:
            raise ValueError(f"duplicate historical fit identity: {key}")
        if row.get("target_values_used_in_features") is not False:
            raise ValueError(f"target-values feature guard failed: {key}")
        if row.get("production_change") is not False:
            raise ValueError(f"production guard failed: {key}")
        rows[key] = row

    if set(rows) != expected or len(rows) != 19:
        raise ValueError(f"historical fit identity mismatch missing={sorted(expected-set(rows))} extra={sorted(set(rows)-expected)}")

    encoder, encoder_payload, encoder_artifact_sha256 = load_frozen_encoder_v1(args.encoder)

    embeddings: list[np.ndarray] = []
    structural: list[float] = []
    actual: list[float] = []
    event_ids: list[int] = []
    identities: list[dict[str, Any]] = []

    ordered = sorted(rows.items(), key=lambda item: (item[0][0], item[0][1]))
    for (event_id, horizon), row in ordered:
        sequence = build_encoder_sequence_from_pairs_v1(
            row["sequence_pairs"],
            horizon=horizon,
        )
        embedding = encode_sequence_v1(encoder, sequence)
        p50 = float(row["structural_p50"])
        attendance = float(row["actual_attendance"])
        if p50 <= 0:
            raise ValueError(f"structural P50 must be positive: {(event_id, horizon)}")
        embeddings.append(embedding)
        structural.append(p50)
        actual.append(attendance)
        event_ids.append(event_id)
        identities.append({
            "ticket_event_id": event_id,
            "horizon": horizon,
            "as_of_at": row["as_of_at"],
            "structural_prior_id": row["structural_prior_id"],
        })

    head = fit_attendance_head_v1(
        embeddings=np.vstack(embeddings),
        structural_p50=np.asarray(structural, dtype=float),
        actual_attendance=np.asarray(actual, dtype=float),
        event_ids=np.asarray(event_ids, dtype=int),
        fit_identities=identities,
        encoder_artifact_sha256=encoder_artifact_sha256,
        encoder_source_pt_sha256=str(encoder_payload["source_pt_sha256"]),
    )
    payload = head_to_json_dict(head)
    payload.update({
        "fit_cohort_version": cohort["version"],
        "fit_fold_registry_sha256": cohort["fold_registry_sha256"],
        "fit_export_sha": export.get("sha"),
        "fit_only_no_historical_mae_selection": True,
        "evidence_status": "FITTED_PROSPECTIVE_CANDIDATE_NOT_HISTORICALLY_VALIDATED",
    })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "version": payload["version"],
        "precommit_id": PRECOMMIT_ID,
        "encoder_artifact_sha256": payload["encoder_artifact_sha256"],
        "fit_manifest_sha256": payload["fit_manifest_sha256"],
        "fit_event_count": len(payload["fit_event_ids"]),
        "fit_row_count": payload["fit_row_count"],
        "alpha": payload["alpha"],
        "correction_ratio_cap": payload["correction_ratio_cap"],
        "historical_selection_performed": payload["historical_selection_performed"],
        "production_change": payload["production_change"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
