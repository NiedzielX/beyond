"""Run the precommitted Lane B v2 residual-ratio diagnostic.

The cohort is already exposed research evidence. This runner intentionally
reuses Lane B v1's frozen export materialization and fold identities.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import numpy as np

from ml.demand_engine.trajectory_lane_b_v2 import evaluate_lane_b_v2_forward
from ml.run_trajectory_lane_b_v1 import (
    EXPECTED_COHORT_VERSION,
    EXPECTED_EXPORT_VERSION,
    _build_folds,
    _load_json,
    _materialize_examples,
)


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


def _distribution(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "min": float(np.min(array)),
        "median": float(np.median(array)),
        "max": float(np.max(array)),
        "median_abs": float(np.median(np.abs(array))),
        "max_abs": float(np.max(np.abs(array))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--cohort", required=True, type=Path)
    parser.add_argument("--lane-a-result", required=True, type=Path)
    parser.add_argument("--lane-b-v1-result", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    export = _load_json(args.input)
    cohort = _load_json(args.cohort)
    lane_a = _load_json(args.lane_a_result)
    lane_b_v1 = _load_json(args.lane_b_v1_result)

    if export.get("ok") is not True or export.get("version") != EXPECTED_EXPORT_VERSION:
        raise ValueError("unexpected trajectory development export")
    if cohort.get("version") != EXPECTED_COHORT_VERSION:
        raise ValueError("unexpected frozen cohort version")
    if lane_a.get("decision") != "REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK":
        raise ValueError("Lane A frozen benchmark mismatch")
    if lane_b_v1.get("decision") != "DO_NOT_ADVANCE":
        raise ValueError("Lane B v1 frozen result mismatch")

    examples = _materialize_examples(export, cohort)
    folds = _build_folds(cohort)
    if len(examples) != 19 or len({row.ticket_event_id for row in examples}) != 10:
        raise ValueError("v2 must use the exact frozen 10-event / 19-row cohort")

    score = evaluate_lane_b_v2_forward(
        examples,
        folds,
        lane_b_v1_event_balanced_mae=float(lane_b_v1["lane_b_event_balanced_mae"]),
        lane_a_event_balanced_mae=float(lane_a["challenger_event_balanced_mae"]),
    )

    ratio_values = [row.predicted_residual_ratio for row in score.predictions]
    seat_values = [row.predicted_seat_residual for row in score.predictions]
    result = {
        "version": "trajectory-lane-b-small-gru-residual-ratio-v2-result",
        "precommit_id": score.precommit_id,
        "evidence_class": "historical_exposed_research",
        "cohort_version": cohort["version"],
        "fold_registry_sha256": cohort["fold_registry_sha256"],
        "export_sha": export.get("sha"),
        "independent_cohort_events": 10,
        "independent_test_events": score.independent_test_events,
        "outer_test_rows": score.test_rows,
        "incumbent_event_balanced_mae": score.incumbent_event_balanced_mae,
        "lane_a_event_balanced_mae": score.lane_a_event_balanced_mae,
        "lane_b_v1_event_balanced_mae": score.lane_b_v1_event_balanced_mae,
        "lane_b_v2_event_balanced_mae": score.challenger_event_balanced_mae,
        "delta_mae_vs_incumbent": score.delta_mae_vs_incumbent,
        "delta_mae_vs_lane_b_v1": score.delta_mae_vs_lane_b_v1,
        "delta_mae_vs_lane_a": score.delta_mae_vs_lane_a,
        "event_improvement_rate": score.event_improvement_rate,
        "worst_event_degradation": score.worst_event_degradation,
        "median_seed_ratio_spread": score.median_seed_ratio_spread,
        "max_seed_ratio_spread": score.max_seed_ratio_spread,
        "predicted_residual_ratio_distribution": _distribution(ratio_values),
        "predicted_seat_residual_distribution": _distribution(seat_values),
        "by_horizon": _horizon_metrics(score.predictions),
        "by_event": _event_metrics(score.predictions),
        "predictions": [asdict(row) for row in score.predictions],
        "target_values_used_in_features": False,
        "production_change": False,
        "decision": "DIAGNOSTIC_RESULT_REQUIRES_REVIEW",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "version": result["version"],
        "evidence_class": result["evidence_class"],
        "incumbent_mae": result["incumbent_event_balanced_mae"],
        "lane_b_v1_mae": result["lane_b_v1_event_balanced_mae"],
        "lane_b_v2_mae": result["lane_b_v2_event_balanced_mae"],
        "delta_vs_incumbent": result["delta_mae_vs_incumbent"],
        "delta_vs_v1": result["delta_mae_vs_lane_b_v1"],
        "ratio_distribution": result["predicted_residual_ratio_distribution"],
        "seat_residual_distribution": result["predicted_seat_residual_distribution"],
        "median_seed_ratio_spread": result["median_seed_ratio_spread"],
        "max_seed_ratio_spread": result["max_seed_ratio_spread"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
