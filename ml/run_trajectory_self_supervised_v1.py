"""Run target-free trajectory pretraining v1 from the frozen OIDC export."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from ml.demand_engine.trajectory_self_supervised_v1 import (
    FROZEN_CUTOFF,
    PRECOMMIT_ID,
    TRAIN_EVENT_IDS,
    VALIDATION_EVENT_IDS,
    TargetFreeEventV1,
    TargetFreeObservationV1,
    build_target_free_pairs_v1,
    train_and_score_self_supervised_v1,
)

EXPECTED_EXPORT_VERSION = "trajectory-self-supervised-export-v1"
EXPECTED_SPLIT_VERSION = "trajectory-self-supervised-v1-split"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object expected: {path}")
    return value


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timezone-aware timestamp required: {value}")
    return parsed


def _event_from_export(raw: dict[str, Any]) -> TargetFreeEventV1:
    observations = tuple(
        TargetFreeObservationV1(
            snapshot_id=int(row["snapshot_id"]),
            captured_at=_dt(str(row["captured_at"])),
            hours_to_kickoff=float(row["hours_to_kickoff"]),
            available_total=int(row["available_total"]),
        )
        for row in raw.get("observations", [])
    )
    return TargetFreeEventV1(
        ticket_event_id=int(raw["ticket_event_id"]),
        club_slug=str(raw["club_slug"]),
        kickoff_at=_dt(str(raw["kickoff_at"])),
        observations=observations,
    )


def _distribution(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "min": float(np.min(array)),
        "median": float(np.median(array)),
        "max": float(np.max(array)),
        "median_abs": float(np.median(np.abs(array))),
        "max_abs": float(np.max(np.abs(array))),
    }


def _per_event(predictions) -> dict[str, dict[str, float | int | str]]:
    grouped: dict[int, list[Any]] = defaultdict(list)
    for row in predictions:
        grouped[row.ticket_event_id].append(row)
    result: dict[str, dict[str, float | int | str]] = {}
    for event_id, rows in grouped.items():
        baseline = float(np.mean([row.baseline_abs_error for row in rows]))
        model = float(np.mean([row.model_abs_error for row in rows]))
        result[str(event_id)] = {
            "club_slug": rows[0].club_slug,
            "pairs": len(rows),
            "baseline_mae": baseline,
            "model_mae": model,
            "delta_mae": model - baseline,
        }
    return result


def _export_identity_sha(export: dict[str, Any]) -> str:
    payload = {
        "version": export.get("version"),
        "frozen_data_cutoff": export.get("frozen_data_cutoff"),
        "events": [
            {
                "ticket_event_id": event["ticket_event_id"],
                "observations": [
                    [row["snapshot_id"], row["captured_at"], row["available_total"]]
                    for row in event.get("observations", [])
                ],
            }
            for event in export.get("events", [])
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--split", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--encoder-output", required=True, type=Path)
    args = parser.parse_args()

    export = _load_json(args.input)
    split = _load_json(args.split)

    if export.get("ok") is not True:
        raise ValueError("self-supervised export gateway did not return ok=true")
    if export.get("version") != EXPECTED_EXPORT_VERSION:
        raise ValueError(f"unexpected export version: {export.get('version')}")
    if export.get("precommit_id") != PRECOMMIT_ID:
        raise ValueError("precommit id mismatch")
    if str(export.get("frozen_data_cutoff")).replace("+00:00", "Z") != FROZEN_CUTOFF:
        raise ValueError(f"frozen cutoff mismatch: {export.get('frozen_data_cutoff')}")
    if export.get("attendance_labels_used") is not False:
        raise ValueError("attendance label guard failed")
    if export.get("structural_prior_used") is not False:
        raise ValueError("structural prior guard failed")
    if export.get("production_change") is not False:
        raise ValueError("production guard failed")
    if int(export.get("event_count", 0)) != 26:
        raise ValueError("frozen export must contain exactly 26 events")

    if split.get("version") != EXPECTED_SPLIT_VERSION:
        raise ValueError("split version mismatch")
    if split.get("precommit_id") != PRECOMMIT_ID:
        raise ValueError("split precommit mismatch")
    if tuple(int(x) for x in split["train_event_ids"]) != TRAIN_EVENT_IDS:
        raise ValueError("frozen train event ids mismatch")
    if tuple(int(x) for x in split["validation_event_ids"]) != VALIDATION_EVENT_IDS:
        raise ValueError("frozen validation event ids mismatch")

    event_map: dict[int, TargetFreeEventV1] = {}
    for raw in export.get("events", []):
        event = _event_from_export(raw)
        if event.ticket_event_id in event_map:
            raise ValueError(f"duplicate event export: {event.ticket_event_id}")
        event_map[event.ticket_event_id] = event

    expected_ids = set(TRAIN_EVENT_IDS) | set(VALIDATION_EVENT_IDS)
    if set(event_map) != expected_ids:
        raise ValueError(
            f"self-supervised event identity mismatch missing={sorted(expected_ids-set(event_map))} extra={sorted(set(event_map)-expected_ids)}"
        )

    pairs_by_event = {
        event_id: build_target_free_pairs_v1(event_map[event_id])
        for event_id in sorted(event_map)
    }
    train_pairs = tuple(
        pair
        for event_id in TRAIN_EVENT_IDS
        for pair in pairs_by_event[event_id]
    )
    validation_pairs = tuple(
        pair
        for event_id in VALIDATION_EVENT_IDS
        for pair in pairs_by_event[event_id]
    )

    if len(train_pairs) != 3397:
        raise ValueError(f"frozen train pair count mismatch: {len(train_pairs)}")
    if len(validation_pairs) != 168:
        raise ValueError(f"frozen validation pair count mismatch: {len(validation_pairs)}")
    if len({row.ticket_event_id for row in train_pairs}) != 21:
        raise ValueError("frozen usable train event count must be 21")
    if len({row.ticket_event_id for row in validation_pairs}) != 5:
        raise ValueError("frozen validation event count must be 5")

    score, model = train_and_score_self_supervised_v1(train_pairs, validation_pairs)
    predictions = score.predictions
    target_values = [row.target_delta_index for row in predictions]
    prediction_values = [row.predicted_delta_index for row in predictions]
    improved_events = score.improved_validation_events
    noncollapsed = float(np.median(np.abs(np.asarray(prediction_values, dtype=float)))) > 1e-6
    supported = score.delta_mae_vs_baseline < 0 and improved_events >= 2 and noncollapsed

    result = {
        "version": "trajectory-self-supervised-24h-delta-v1-result",
        "precommit_id": PRECOMMIT_ID,
        "evidence_class": "target_free_temporal_validation",
        "frozen_data_cutoff": FROZEN_CUTOFF,
        "export_sha": export.get("sha"),
        "export_identity_sha256": _export_identity_sha(export),
        "train_events": score.train_events,
        "train_pairs": score.train_pairs,
        "validation_events": score.validation_events,
        "validation_pairs": score.validation_pairs,
        "baseline_event_balanced_mae": score.baseline_event_balanced_mae,
        "model_event_balanced_mae": score.model_event_balanced_mae,
        "delta_mae_vs_baseline": score.delta_mae_vs_baseline,
        "pair_mae": score.pair_mae,
        "signed_bias": score.signed_bias,
        "improved_validation_events": improved_events,
        "target_distribution": _distribution(target_values),
        "prediction_distribution": _distribution(prediction_values),
        "by_event": _per_event(predictions),
        "attendance_labels_used": False,
        "structural_prior_used": False,
        "production_change": False,
        "decision": "REPRESENTATION_SUPPORTED" if supported else "REPRESENTATION_NOT_SUPPORTED",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    import torch

    args.encoder_output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "version": "trajectory-self-supervised-encoder-v1",
            "precommit_id": PRECOMMIT_ID,
            "frozen_data_cutoff": FROZEN_CUTOFF,
            "input_dim": 4,
            "hidden_dim": 8,
            "state_dict": model.state_dict(),
            "decision": result["decision"],
        },
        args.encoder_output,
    )

    print(json.dumps({
        "version": result["version"],
        "decision": result["decision"],
        "train_events": result["train_events"],
        "train_pairs": result["train_pairs"],
        "validation_events": result["validation_events"],
        "validation_pairs": result["validation_pairs"],
        "baseline_event_balanced_mae": result["baseline_event_balanced_mae"],
        "model_event_balanced_mae": result["model_event_balanced_mae"],
        "delta_mae_vs_baseline": result["delta_mae_vs_baseline"],
        "improved_validation_events": result["improved_validation_events"],
        "target_distribution": result["target_distribution"],
        "prediction_distribution": result["prediction_distribution"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
