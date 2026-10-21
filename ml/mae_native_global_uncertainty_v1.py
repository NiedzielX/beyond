#!/usr/bin/env python3
"""Paired forward-fold uncertainty for the MAE-native global tournament v1.

This diagnostic replays only the two historically interesting horizons from the
already-completed predeclared tournament:

* T-3: quantile-linear-a002 passed the selector with a tiny mean MAE gain.
* T-7: the same challenger had a larger aggregate gain but failed the 2/3 fold
  consistency gate and is included only as a diagnostic.

No candidate selection, retuning or production change occurs here. The exact
canonical history and tournament code are reused, then paired fixture-block
bootstrap uncertainty is computed within temporal folds.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ml.mae_delta_uncertainty_v1 import BootstrapConfig, evaluate_candidate
from ml.mae_native_global_tournament_v1 import (
    EVIDENCE_CLASS,
    EXPECTED_HISTORY_SHA256,
    build_store,
    load_canonical_history,
    run_horizon,
)

EXPERIMENT = "mae-native-global-uncertainty-v1"
CANDIDATE_ID = "quantile-linear-a002"
INCUMBENT_ID = "incumbent-runtime"
TARGET_HORIZONS = ("T-3", "T-7")
PARENT_TOURNAMENT_RUN_ID = 39668550104
PARENT_TOURNAMENT_ARTIFACT_ID = 12378567266
PARENT_TOURNAMENT_ARTIFACT_SHA256 = (
    "5b9bd145124c8ee98b5fddf4849e37a2337ef66a475339a5a00b57fe76528ab1"
)


def decision_for(horizon: str, diagnostic: dict[str, Any]) -> str:
    bootstrap = diagnostic["bootstrap"]
    lower = float(bootstrap["delta_mae_lower"])
    upper = float(bootstrap["delta_mae_upper"])
    probability = float(bootstrap["p_delta_mae_below_zero"])
    point = float(diagnostic["delta_mae"])

    if horizon == "T-7":
        # T-7 failed the already-frozen 2/3 temporal-fold consistency selector.
        # Uncertainty cannot retroactively make it eligible.
        return "RETAIN_INCUMBENT_TEMPORAL_CONSISTENCY_FAILED"

    if point >= 0:
        return "RETAIN_INCUMBENT_NO_POINT_IMPROVEMENT"
    if upper < 0 and probability >= 0.975:
        return "RETAIN_AS_HISTORICAL_RESEARCH_LEAD_UNCERTAINTY_SUPPORTIVE"
    if lower > 0:
        return "REJECT_CHALLENGER_UNCERTAINTY_FAVORS_INCUMBENT"
    return "RETAIN_INCUMBENT_EFFECT_NOT_DISTINGUISHABLE_FROM_ZERO"


def run_diagnostic(history_path: Path, n_resamples: int, seed: int) -> dict[str, Any]:
    history = load_canonical_history(history_path)
    store = build_store(history)
    config = BootstrapConfig(n_resamples=n_resamples, seed=seed)

    horizon_results: list[dict[str, Any]] = []
    for horizon in TARGET_HORIZONS:
        tournament_result, predictions = run_horizon(store, horizon)
        diagnostic = evaluate_candidate(
            predictions,
            candidate_id=CANDIDATE_ID,
            incumbent_id=INCUMBENT_ID,
            event_col="match_key",
            actual_col="actual_attendance",
            prediction_col="forecast_p50",
            candidate_col="candidate_id",
            strata_cols=["fold_id"],
            config=config,
        )
        diagnostic["horizon"] = horizon
        diagnostic["tournament_selector_eligible"] = bool(
            next(
                row["selector_eligible"]
                for row in tournament_result["candidates"]
                if row["candidate_id"] == CANDIDATE_ID
            )
        )
        diagnostic["tournament_fold_wins_vs_incumbent"] = int(
            next(
                row["fold_wins_vs_incumbent"]
                for row in tournament_result["candidates"]
                if row["candidate_id"] == CANDIDATE_ID
            )
        )
        diagnostic["tournament_mean_fold_delta_mae"] = float(
            next(
                row["mae_delta_vs_incumbent"]
                for row in tournament_result["candidates"]
                if row["candidate_id"] == CANDIDATE_ID
            )
        )
        diagnostic["decision"] = decision_for(horizon, diagnostic)
        horizon_results.append(diagnostic)

    return {
        "experiment": EXPERIMENT,
        "status": "COMPLETED_HISTORICAL_FORWARD_UNCERTAINTY_DIAGNOSTIC",
        "evidence_class": EVIDENCE_CLASS,
        "production_change": False,
        "promotion_allowed": False,
        "candidate_id": CANDIDATE_ID,
        "incumbent_id": INCUMBENT_ID,
        "historical_runtime_sha256": EXPECTED_HISTORY_SHA256,
        "match_count": int(history["match_key"].nunique()),
        "feature_row_count": int(len(store)),
        "resampling_unit": "fixture",
        "stratification": ["fold_id"],
        "bootstrap_config": {
            "n_resamples": n_resamples,
            "seed": seed,
            "method": "paired_event_block_percentile",
        },
        "parent_tournament": {
            "run_id": PARENT_TOURNAMENT_RUN_ID,
            "artifact_id": PARENT_TOURNAMENT_ARTIFACT_ID,
            "artifact_sha256": PARENT_TOURNAMENT_ARTIFACT_SHA256,
        },
        "horizons": horizon_results,
        "interpretation_rule": {
            "supportive": "95% bootstrap interval entirely below zero and P(delta<0)>=0.975",
            "otherwise": "retain incumbent / treat historical point improvement as uncertain",
            "t7_override": "T-7 remains ineligible because it failed the predeclared 2/3 temporal-fold gate",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--n-resamples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    result = run_diagnostic(args.history, args.n_resamples, args.seed)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": result["experiment"],
        "status": result["status"],
        "horizons": [
            {
                "horizon": row["horizon"],
                "delta_mae": row["delta_mae"],
                "delta_mae_lower": row["bootstrap"]["delta_mae_lower"],
                "delta_mae_upper": row["bootstrap"]["delta_mae_upper"],
                "p_delta_mae_below_zero": row["bootstrap"]["p_delta_mae_below_zero"],
                "event_improvement_rate": row["event_improvement_rate"],
                "tournament_fold_wins": row["tournament_fold_wins_vs_incumbent"],
                "decision": row["decision"],
            }
            for row in result["horizons"]
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
