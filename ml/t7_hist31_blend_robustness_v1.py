#!/usr/bin/env python3
"""T-7 Hist31 robustness stage 2.

This experiment follows PRE_LIVE_BASELINE_OPTIMIZATION_V1.
It tests whether a fixed blend of the frozen T-7 incumbent and the stage-1
HistGradientBoosting challenger can preserve MAE improvement while reducing
harmful event-level degradation.

Selection is development-only (2023/24). Reference holdouts are scored only
after one alpha is frozen. No production promotion occurs here.
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
import sklearn

from ml.demand_engine.structural_prior_runtime import fit_structural_prior_runtime
from ml.pre_live_baseline_optimization_v1 import (
    DEV_SEASON,
    DEV_TRAIN,
    HOLDOUTS,
    Candidate,
    comparison_scorecard,
    eligible_rows,
    fit_candidate,
    load_feature_store,
    resolved_feature_groups,
    sha256_file,
    verify_incumbent,
)

EXPERIMENT = "t7-hist31-blend-robustness-v1"
WORKSTREAM = "a2 — Historical / Structural Prior optimization — T-7 robustness stage 2"
HORIZON = "T-7"
RANDOM_SEED = 42
ALPHAS = (0.0, 0.25, 0.50, 0.75, 1.0)
SELECTION_TIE_ATOL = 1e-9
STAGE1_RESULT_JSON_SHA256 = "55ea6ee19309771b54e0b0336ecaa2871de19d95d2bf4360400ff76e4c2ddc79"
STAGE1_FULL_HIST31_WORST_DEGRADATION = {
    "2024/2025": 3685.7443205687923,
    "2025/2026": 4233.1079323212325,
}


def metrics(actual: np.ndarray, prediction: np.ndarray) -> dict[str, float | int]:
    actual = np.asarray(actual, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    ae = np.abs(prediction - actual)
    denom = float(np.sum(actual))
    return {
        "n": int(len(actual)),
        "mae": float(np.mean(ae)),
        "median_ae": float(np.median(ae)),
        "bias": float(np.mean(prediction - actual)),
        "wape": float(np.sum(ae) / denom) if denom > 0 else float("nan"),
        "p90_ae": float(np.quantile(ae, 0.90)),
    }


def blend_predictions(
    incumbent_prediction: np.ndarray,
    hist31_prediction: np.ndarray,
    alpha: float,
) -> np.ndarray:
    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"alpha must be in [0, 1], got {alpha}")
    incumbent = np.asarray(incumbent_prediction, dtype=float)
    hist31 = np.asarray(hist31_prediction, dtype=float)
    if incumbent.shape != hist31.shape:
        raise ValueError("incumbent and Hist31 predictions must have identical shape")
    return (1.0 - alpha) * incumbent + alpha * hist31


def robustness_scorecard(
    rows: pd.DataFrame,
    candidate_prediction: np.ndarray,
    incumbent_prediction: np.ndarray,
    hist31_prediction: np.ndarray,
) -> dict[str, Any]:
    base = comparison_scorecard(rows, candidate_prediction, incumbent_prediction)
    candidate = np.asarray(candidate_prediction, dtype=float)
    incumbent = np.asarray(incumbent_prediction, dtype=float)
    hist31 = np.asarray(hist31_prediction, dtype=float)
    capacity = rows["capacity"].astype(float).to_numpy()
    actual = rows["target_attendance"].astype(float).to_numpy()

    candidate_ae = np.abs(candidate - actual)
    incumbent_ae = np.abs(incumbent - actual)
    degradation = candidate_ae - incumbent_ae
    worst_index = int(np.argmax(degradation))

    hist31_ae = np.abs(hist31 - actual)
    hist31_degradation = hist31_ae - incumbent_ae

    base.update({
        "mean_abs_revision_vs_incumbent": float(np.mean(np.abs(candidate - incumbent))),
        "p90_abs_revision_vs_incumbent": float(np.quantile(np.abs(candidate - incumbent), 0.90)),
        "max_abs_revision_vs_incumbent": float(np.max(np.abs(candidate - incumbent))),
        "worst_event_degradation_share_of_capacity": float(
            degradation[worst_index] / capacity[worst_index]
        ),
        "hist31_full": {
            "metrics": metrics(actual, hist31),
            "mae_improvement_vs_incumbent": float(
                base["incumbent"]["mae"] - metrics(actual, hist31)["mae"]
            ),
            "worst_event_degradation_vs_incumbent": float(np.max(hist31_degradation)),
        },
    })
    return base


def fit_pair(
    store: pd.DataFrame,
    training_seasons: list[str],
):
    groups, _ = resolved_feature_groups(store, HORIZON)
    incumbent = fit_structural_prior_runtime(store, HORIZON, training_seasons)
    hist31_candidate = Candidate(
        id="model-hist_absolute_31",
        family="model_family",
        model_policy="hist_absolute_31",
    )
    hist31 = fit_candidate(
        store,
        HORIZON,
        training_seasons,
        hist31_candidate,
        groups,
    )
    return incumbent, hist31


def score_development(store: pd.DataFrame) -> dict[str, Any]:
    incumbent, hist31 = fit_pair(store, DEV_TRAIN)
    rows = eligible_rows(store, HORIZON, DEV_SEASON, incumbent.spec.baseline_column)
    incumbent_prediction = incumbent.predict(rows)
    hist31_prediction = hist31.predict(rows)
    incumbent_mae = metrics(
        rows["target_attendance"].astype(float).to_numpy(), incumbent_prediction
    )["mae"]
    verify_incumbent(HORIZON, DEV_SEASON, float(incumbent_mae), "development")

    candidates: list[dict[str, Any]] = []
    for alpha in ALPHAS:
        prediction = blend_predictions(incumbent_prediction, hist31_prediction, alpha)
        score = robustness_scorecard(rows, prediction, incumbent_prediction, hist31_prediction)
        candidates.append({
            "alpha": alpha,
            "id": f"blend-a{int(round(alpha * 100)):03d}",
            "scorecard": score,
        })

    best_mae = min(float(item["scorecard"]["candidate"]["mae"]) for item in candidates)
    tied = [
        item for item in candidates
        if np.isclose(
            float(item["scorecard"]["candidate"]["mae"]),
            best_mae,
            rtol=0.0,
            atol=SELECTION_TIE_ATOL,
        )
    ]
    # ALPHAS are declared in ascending order: on an exact tie prefer more incumbent.
    selected = min(tied, key=lambda item: float(item["alpha"]))
    ranking = sorted(
        [
            {
                "id": item["id"],
                "alpha": float(item["alpha"]),
                "mae": float(item["scorecard"]["candidate"]["mae"]),
                "mae_improvement_vs_incumbent": float(item["scorecard"]["mae_improvement"]),
                "worst_event_degradation": float(item["scorecard"]["worst_event_degradation"]),
                "p90_ae": float(item["scorecard"]["candidate"]["p90_ae"]),
                "median_ae": float(item["scorecard"]["candidate"]["median_ae"]),
            }
            for item in candidates
        ],
        key=lambda item: (item["mae"], item["alpha"]),
    )

    return {
        "training_seasons": DEV_TRAIN,
        "test_season": DEV_SEASON,
        "rows": int(len(rows)),
        "candidates": candidates,
        "ranking": ranking,
        "best_mae": best_mae,
        "tie_ids": [item["id"] for item in tied],
        "tie_break_rule": "within 1e-9 MAE choose lower alpha (more incumbent)",
        "selected_id": selected["id"],
        "selected_alpha": float(selected["alpha"]),
    }


def score_holdout(
    store: pd.DataFrame,
    season: str,
    training_seasons: list[str],
    alpha: float,
) -> dict[str, Any]:
    incumbent, hist31 = fit_pair(store, training_seasons)
    rows = eligible_rows(store, HORIZON, season, incumbent.spec.baseline_column)
    incumbent_prediction = incumbent.predict(rows)
    hist31_prediction = hist31.predict(rows)
    incumbent_mae = metrics(
        rows["target_attendance"].astype(float).to_numpy(), incumbent_prediction
    )["mae"]
    verify_incumbent(HORIZON, season, float(incumbent_mae), "holdout")

    selected_prediction = blend_predictions(incumbent_prediction, hist31_prediction, alpha)
    score = robustness_scorecard(
        rows, selected_prediction, incumbent_prediction, hist31_prediction
    )

    stage1_worst = STAGE1_FULL_HIST31_WORST_DEGRADATION[season]
    selected_worst = float(score["worst_event_degradation"])
    return {
        "season": season,
        "training_seasons": training_seasons,
        "rows": int(len(rows)),
        "selected_alpha": alpha,
        "scorecard": score,
        "tail_vs_stage1_full_hist31": {
            "stage1_full_hist31_worst_degradation": stage1_worst,
            "selected_blend_worst_degradation": selected_worst,
            "worst_degradation_reduction": stage1_worst - selected_worst,
            "worst_degradation_reduction_rate": (
                (stage1_worst - selected_worst) / stage1_worst
                if stage1_worst > 0 else float("nan")
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    expected_hash = manifest["historical_runtime"]["sha256"]
    actual_hash = sha256_file(args.historical_runtime)
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    development = score_development(store)
    selected_alpha = float(development["selected_alpha"])

    holdouts = [
        score_holdout(store, season, train, selected_alpha)
        for season, train in HOLDOUTS
    ]

    mean_incumbent = float(np.mean([
        item["scorecard"]["incumbent"]["mae"] for item in holdouts
    ]))
    mean_selected = float(np.mean([
        item["scorecard"]["candidate"]["mae"] for item in holdouts
    ]))
    mean_hist31 = float(np.mean([
        item["scorecard"]["hist31_full"]["metrics"]["mae"] for item in holdouts
    ]))
    mean_improvement = mean_incumbent - mean_selected

    selected_both_positive = all(
        float(item["scorecard"]["mae_improvement"]) > 0.0 for item in holdouts
    )
    tail_reduced_both = all(
        float(item["tail_vs_stage1_full_hist31"]["worst_degradation_reduction"]) > 0.0
        for item in holdouts
    )

    if selected_alpha == 0.0:
        signal = "INCUMBENT_SELECTED_ON_DEVELOPMENT"
    elif selected_alpha == 1.0:
        signal = "FULL_HIST31_SELECTED_NO_BLEND_ROBUSTNESS_GAIN"
    elif selected_both_positive and tail_reduced_both:
        signal = "BLEND_RETAINS_REFERENCE_UPLIFT_AND_REDUCES_TAIL"
    elif mean_improvement > 0.0 and tail_reduced_both:
        signal = "BLEND_POSITIVE_MEAN_AND_REDUCES_TAIL"
    else:
        signal = "BLEND_NOT_PROVEN_ROBUST"

    result = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_HISTORICAL_CHALLENGER_EVIDENCE",
        "evidence_class": "EXPOSED_HISTORICAL_REFERENCE_SEASONS",
        "promotion_allowed": False,
        "horizon": HORIZON,
        "stage1_dependency": {
            "result_json_sha256": STAGE1_RESULT_JSON_SHA256,
            "candidate": "model-hist_absolute_31",
            "stage1_mean_reference_mae_improvement": 68.80692578319918,
            "stage1_worst_degradation_by_season": STAGE1_FULL_HIST31_WORST_DEGRADATION,
        },
        "protocol": {
            "alphas": list(ALPHAS),
            "selection_metric": "MAE",
            "selection_training_seasons": DEV_TRAIN,
            "selection_development_season": DEV_SEASON,
            "selection_tie_rule": "within 1e-9 MAE choose lower alpha",
            "holdouts": [
                {"season": season, "training_seasons": train}
                for season, train in HOLDOUTS
            ],
            "holdout_selection_allowed": False,
            "event_is_independent_unit": True,
            "random_snapshot_split": False,
            "future_leakage_allowed": False,
            "production_activation": False,
        },
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_hash,
            "artifact_version": manifest.get("artifact_version"),
            "feature_contract": manifest.get("feature_contract"),
            "matches": int(store["match_key"].nunique()),
            "feature_rows": int(len(store)),
        },
        "runtime": {
            "random_seed": RANDOM_SEED,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "development": development,
        "selected_alpha": selected_alpha,
        "holdouts": holdouts,
        "summary": {
            "mean_reference_incumbent_mae": mean_incumbent,
            "mean_reference_selected_mae": mean_selected,
            "mean_reference_full_hist31_mae": mean_hist31,
            "mean_reference_mae_improvement_vs_incumbent": mean_improvement,
            "selected_improves_both_reference_seasons": selected_both_positive,
            "selected_reduces_worst_degradation_vs_full_hist31_both_seasons": tail_reduced_both,
            "signal": signal,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "experiment": EXPERIMENT,
        "selected_alpha": selected_alpha,
        "development_ranking": development["ranking"],
        "summary": result["summary"],
        "holdouts": [
            {
                "season": item["season"],
                "incumbent_mae": item["scorecard"]["incumbent"]["mae"],
                "selected_mae": item["scorecard"]["candidate"]["mae"],
                "mae_improvement": item["scorecard"]["mae_improvement"],
                "worst_event_degradation": item["scorecard"]["worst_event_degradation"],
                "worst_event": item["scorecard"]["worst_event"],
                "tail_reduction_vs_full_hist31": item["tail_vs_stage1_full_hist31"],
            }
            for item in holdouts
        ],
        "promotion_allowed": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
