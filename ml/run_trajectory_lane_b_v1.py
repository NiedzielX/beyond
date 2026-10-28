"""Run the frozen Trajectory Lane B v1 experiment from an OIDC export payload.

This runner deliberately filters the export through
``ml/artifacts/trajectory_development_cohort_v1.json`` so Lane B is evaluated on
exactly the same persisted checkpoint identities as frozen Lane A v1.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from ml.demand_engine.trajectory_feature_contract_v1 import LaneBSequenceV1, SequenceStepV1
from ml.demand_engine.trajectory_lane_b_v1 import evaluate_lane_b_forward_v1
from ml.demand_engine.trajectory_shared_dataset_v1 import TrajectoryDevelopmentExampleV1
from ml.demand_engine.trajectory_validation_folds_v1 import TrajectoryForwardFoldV1

EXPECTED_EXPORT_VERSION = "trajectory-development-export-v1"
EXPECTED_COHORT_VERSION = "trajectory-development-cohort-v1"
HORIZON_TO_DAYS = {"T-30": 30, "T-14": 14, "T-7": 7, "T-3": 3, "T-1": 1}


def _dt(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    result = datetime.fromisoformat(normalized)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"timezone-aware timestamp required: {value}")
    return result


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"JSON object expected: {path}")
    return value


def _build_sequence(row: dict[str, Any]) -> LaneBSequenceV1:
    pairs = row.get("sequence_pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError(f"empty sequence for event={row.get('ticket_event_id')} horizon={row.get('horizon')}")

    first_available = int(pairs[0][1])
    if first_available <= 0:
        raise ValueError("first genuine sequence inventory must be positive")

    capacity = row.get("stadium_capacity")
    capacity_value = int(capacity) if capacity is not None and int(capacity) > 0 else None
    steps: list[SequenceStepV1] = []
    previous_hours: float | None = None
    previous_index: float | None = None

    # Export pairs are already chronological (earliest -> latest), so
    # hours_to_kickoff must monotonically decrease.
    for index, pair in enumerate(pairs):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("invalid sequence pair")
        hours = float(pair[0])
        available = int(pair[1])
        available_index = available / first_available
        if previous_hours is not None and hours >= previous_hours:
            raise ValueError("sequence is not strictly chronological by hours_to_kickoff")
        delta_hours = None if previous_hours is None else previous_hours - hours
        delta_index = None if previous_index is None else available_index - previous_index
        steps.append(
            SequenceStepV1(
                snapshot_id=index + 1,
                captured_at=_dt(row["kickoff_at"]),  # lineage placeholder; not a model input
                hours_to_kickoff=hours,
                available_index=available_index,
                # Persisted v1 checkpoint feature rows did not carry this channel;
                # keep it missing so Lane B does not receive new capacity-normalized
                # inventory information after Lane A outer results are known.
                available_share_of_capacity=None,
                delta_hours_since_previous=delta_hours,
                delta_available_index=delta_index,
            )
        )
        previous_hours = hours
        previous_index = available_index

    return LaneBSequenceV1(
        contract_id="trajectory-feature-contract-v1",
        as_of_at=_dt(row["as_of_at"]),
        kickoff_at=_dt(row["kickoff_at"]),
        steps=tuple(steps),
        first_available_total=first_available,
        verified_capacity=capacity_value,
    )


def _global_features(row: dict[str, Any], sequence: LaneBSequenceV1) -> dict[str, float | int | bool | None]:
    features = row.get("features") or {}
    capacity = row.get("stadium_capacity")
    capacity_value = float(capacity) if capacity is not None and float(capacity) > 0 else None
    p50 = float(row["structural_p50"])
    days = HORIZON_TO_DAYS[row["horizon"]]
    return {
        "days_to_event": days,
        "snapshot_age_minutes": _float_or_none(features.get("snapshot_age_minutes")),
        "clean_snapshot_count": int(features.get("clean_snapshot_count") or 0),
        "observation_window_hours": _float_or_none(features.get("observation_window_hours")),
        "max_visible_gap_hours": _float_or_none(features.get("max_visible_gap_hours")),
        "structural_incumbent_p50": p50,
        "structural_incumbent_p50_share_of_capacity": (
            p50 / capacity_value if capacity_value is not None else None
        ),
        "verified_capacity_available": capacity_value is not None,
        "sequence_length": sequence.sequence_length,
    }


def _float_or_none(value: Any) -> float | None:
    return None if value is None else float(value)


def _expected_identities(cohort: dict[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    identities: dict[tuple[int, str], dict[str, Any]] = {}
    for event in cohort["events"]:
        event_id = int(event["ticket_event_id"])
        for horizon in event["eligible_horizons"]:
            key = (event_id, str(horizon))
            if key in identities:
                raise ValueError(f"duplicate frozen identity: {key}")
            identities[key] = event
    return identities


def _materialize_examples(export: dict[str, Any], cohort: dict[str, Any]) -> tuple[TrajectoryDevelopmentExampleV1, ...]:
    expected = _expected_identities(cohort)
    selected: dict[tuple[int, str], dict[str, Any]] = {}

    for row in export.get("rows", []):
        key = (int(row["ticket_event_id"]), str(row["horizon"]))
        if key not in expected:
            continue
        if key in selected:
            raise ValueError(f"duplicate exported identity: {key}")
        if row.get("target_values_used_in_features") is not False:
            raise ValueError(f"target-values guard failed: {key}")
        if row.get("production_change") is not False:
            raise ValueError(f"production guard failed: {key}")
        selected[key] = row

    missing = sorted(set(expected) - set(selected))
    extra = sorted(set(selected) - set(expected))
    if missing or extra:
        raise ValueError(f"frozen cohort identity mismatch missing={missing} extra={extra}")

    rows_per_event: dict[int, int] = defaultdict(int)
    for event_id, _ in expected:
        rows_per_event[event_id] += 1

    examples: list[TrajectoryDevelopmentExampleV1] = []
    for key in sorted(selected, key=lambda item: (_dt(selected[item]["kickoff_at"]), item[0], HORIZON_TO_DAYS[item[1]], item[1])):
        row = selected[key]
        event_id, horizon = key
        sequence = _build_sequence(row)
        p50 = float(row["structural_p50"])
        actual = int(row["actual_attendance"])
        examples.append(
            TrajectoryDevelopmentExampleV1(
                dataset_contract_id="trajectory-shared-development-dataset-v1",
                feature_contract_id="trajectory-feature-contract-v1",
                ticket_event_id=event_id,
                club_slug=str(row["club_slug"]),
                kickoff_at=_dt(row["kickoff_at"]),
                days_to_event=HORIZON_TO_DAYS[horizon],
                as_of_at=_dt(row["as_of_at"]),
                incumbent_p50=p50,
                actual_attendance=actual,
                residual_target=float(actual) - p50,
                lane_a_features={},
                lane_b_sequence=sequence,
                lane_b_global_features=_global_features(row, sequence),
                event_row_weight=1.0 / rows_per_event[event_id],
                target_values_used_in_features=False,
                production_change=False,
            )
        )
    return tuple(examples)


def _build_folds(cohort: dict[str, Any]) -> tuple[TrajectoryForwardFoldV1, ...]:
    event_by_id = {int(row["ticket_event_id"]): row for row in cohort["events"]}
    folds: list[TrajectoryForwardFoldV1] = []
    for raw in cohort["folds"]:
        test_ids = tuple(int(value) for value in raw["test_event_ids"])
        if not test_ids:
            raise ValueError("test fold must not be empty")
        test_kickoff = _dt(event_by_id[test_ids[0]]["kickoff_at"])
        folds.append(
            TrajectoryForwardFoldV1(
                contract_id="trajectory-validation-fold-contract-v1",
                fold_id=str(raw["fold_id"]),
                test_kickoff_at=test_kickoff,
                train_event_ids=tuple(int(value) for value in raw["train_event_ids"]),
                test_event_ids=test_ids,
                train_clubs=tuple(str(value) for value in raw["train_clubs"]),
            )
        )
    return tuple(folds)


def _event_metrics(predictions) -> dict[str, dict[str, float]]:
    grouped: dict[int, list[Any]] = defaultdict(list)
    for row in predictions:
        grouped[row.ticket_event_id].append(row)
    result: dict[str, dict[str, float]] = {}
    for event_id, rows in grouped.items():
        incumbent = float(np.mean([row.incumbent_abs_error for row in rows]))
        challenger = float(np.mean([row.challenger_abs_error for row in rows]))
        result[str(event_id)] = {
            "incumbent_event_mae": incumbent,
            "challenger_event_mae": challenger,
            "delta_mae": challenger - incumbent,
        }
    return result


def _horizon_metrics(predictions) -> dict[str, dict[str, float | int]]:
    grouped: dict[int, list[Any]] = defaultdict(list)
    for row in predictions:
        grouped[row.days_to_event].append(row)
    result: dict[str, dict[str, float | int]] = {}
    for days, rows in sorted(grouped.items(), reverse=True):
        incumbent = float(np.mean([row.incumbent_abs_error for row in rows]))
        challenger = float(np.mean([row.challenger_abs_error for row in rows]))
        result[f"T-{days}"] = {
            "events": len({row.ticket_event_id for row in rows}),
            "rows": len(rows),
            "incumbent_mae": incumbent,
            "challenger_mae": challenger,
            "delta_mae": challenger - incumbent,
        }
    return result


def _identity_sha(examples: tuple[TrajectoryDevelopmentExampleV1, ...]) -> str:
    payload = [
        {
            "ticket_event_id": row.ticket_event_id,
            "days_to_event": row.days_to_event,
            "as_of_at": row.as_of_at.isoformat(),
        }
        for row in examples
    ]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--cohort", required=True, type=Path)
    parser.add_argument("--lane-a-result", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    export = _load_json(args.input)
    cohort = _load_json(args.cohort)
    lane_a_result = _load_json(args.lane_a_result)

    if export.get("ok") is not True:
        raise ValueError("trajectory export gateway did not return ok=true")
    if export.get("version") != EXPECTED_EXPORT_VERSION:
        raise ValueError(f"unexpected export version: {export.get('version')}")
    if cohort.get("version") != EXPECTED_COHORT_VERSION:
        raise ValueError(f"unexpected cohort version: {cohort.get('version')}")
    if lane_a_result.get("decision") != "REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK":
        raise ValueError("Lane A benchmark result/decision is not frozen as expected")

    examples = _materialize_examples(export, cohort)
    folds = _build_folds(cohort)
    if len({row.ticket_event_id for row in examples}) != 10 or len(examples) != 19:
        raise ValueError("frozen cohort must materialize exactly 10 events / 19 rows")

    score = evaluate_lane_b_forward_v1(
        examples,
        folds,
        lane_a_event_balanced_mae=float(lane_a_result["challenger_event_balanced_mae"]),
    )

    result = {
        "version": "trajectory-lane-b-small-gru-residual-v1-result",
        "precommit_id": score.precommit_id,
        "feature_contract_id": "trajectory-feature-contract-v1",
        "validation_contract_id": "trajectory-validation-fold-contract-v1",
        "cohort_version": cohort["version"],
        "fold_registry_sha256": cohort["fold_registry_sha256"],
        "export_sha": export.get("sha"),
        "dataset_identity_sha256": _identity_sha(examples),
        "evidence_class": "historical_exposed_research",
        "independent_cohort_events": len({row.ticket_event_id for row in examples}),
        "independent_test_events": score.independent_test_events,
        "outer_test_rows": score.test_rows,
        "incumbent_event_balanced_mae": score.incumbent_event_balanced_mae,
        "lane_a_event_balanced_mae": score.lane_a_event_balanced_mae,
        "lane_b_event_balanced_mae": score.challenger_event_balanced_mae,
        "delta_mae_vs_incumbent": score.delta_mae_vs_incumbent,
        "delta_mae_vs_lane_a": score.delta_mae_vs_lane_a,
        "event_improvement_rate": score.event_improvement_rate,
        "worst_event_degradation": score.worst_event_degradation,
        "median_seed_spread": score.median_seed_spread,
        "max_seed_spread": score.max_seed_spread,
        "seeds": list(score.seeds),
        "by_horizon": _horizon_metrics(score.predictions),
        "by_event": _event_metrics(score.predictions),
        "predictions": [asdict(row) for row in score.predictions],
        "target_values_used_in_features": False,
        "production_change": False,
    }
    result["decision"] = (
        "ADVANCE_TO_CANDIDATE_REVIEW"
        if result["delta_mae_vs_incumbent"] < 0 and result["delta_mae_vs_lane_a"] < 0
        else "DO_NOT_ADVANCE"
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "version": result["version"],
        "decision": result["decision"],
        "independent_test_events": result["independent_test_events"],
        "incumbent_mae": result["incumbent_event_balanced_mae"],
        "lane_a_mae": result["lane_a_event_balanced_mae"],
        "lane_b_mae": result["lane_b_event_balanced_mae"],
        "delta_vs_incumbent": result["delta_mae_vs_incumbent"],
        "delta_vs_lane_a": result["delta_mae_vs_lane_a"],
        "median_seed_spread": result["median_seed_spread"],
        "max_seed_spread": result["max_seed_spread"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
