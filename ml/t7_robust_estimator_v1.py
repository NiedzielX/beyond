#!/usr/bin/env python3
"""T-7 robust-estimator stage 3.

Stage 1 found a material HistGradientBoosting MAE lead, while stage 2 showed
that unconditional blending only trades MAE for smaller revisions and that
MAE-only development selection prefers full Hist31.

This experiment keeps the T-7 baseline, feature contract, splits and target
fixed, and changes only estimator regularization / robust model shape.
One candidate is selected on 2023/24 development only. Reference seasons are
scored only after that choice is frozen. No production activation occurs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor

from ml.demand_engine.structural_prior_runtime import (
    CAT,
    CURRENT_EARLY_RUNTIME_SPECS,
    _preprocessor,
    feature_columns,
    fit_structural_prior_runtime,
)
from ml.pre_live_baseline_optimization_v1 import (
    DEV_SEASON,
    DEV_TRAIN,
    HOLDOUTS,
    comparison_scorecard,
    eligible_rows,
    load_feature_store,
    sha256_file,
    verify_incumbent,
)

EXPERIMENT = "t7-robust-estimator-v1"
WORKSTREAM = "a2 — Historical / Structural Prior optimization — T-7 robust estimator stage 3"
HORIZON = "T-7"
RANDOM_SEED = 42
DEVELOPMENT_TIE_ATOL = 1e-9
STAGE1_RESULT_JSON_SHA256 = "55ea6ee19309771b54e0b0336ecaa2871de19d95d2bf4360400ff76e4c2ddc79"
STAGE2_RESULT_JSON_SHA256 = "170cf7bc10437ca4f0b5bb724e7db7ffab0941600932b7c53544c150007b7703"
STAGE1_FULL_HIST31_WORST_DEGRADATION = {
    "2024/2025": 3685.7443205687923,
    "2025/2026": 4233.1079323212325,
}

EstimatorFamily = Literal["hist", "gbr_absolute"]


@dataclass(frozen=True)
class EstimatorSpec:
    id: str
    family: EstimatorFamily
    learning_rate: float
    max_iter_or_estimators: int
    max_leaf_nodes: int | None = None
    min_samples_leaf: int = 10
    l2_regularization: float = 0.0
    max_depth: int | None = None


# Predeclared before reference scoring. The first Hist31 spec is the exact
# stage-1 lead; remaining configs strengthen structural regularization or use
# a simpler absolute-error GradientBoosting shape.
CANDIDATES: tuple[EstimatorSpec, ...] = (
    EstimatorSpec(
        id="hist31-leaf10-l2-1",
        family="hist",
        learning_rate=0.04,
        max_iter_or_estimators=300,
        max_leaf_nodes=31,
        min_samples_leaf=10,
        l2_regularization=1.0,
    ),
    EstimatorSpec(
        id="hist15-leaf10-l2-1",
        family="hist",
        learning_rate=0.04,
        max_iter_or_estimators=300,
        max_leaf_nodes=15,
        min_samples_leaf=10,
        l2_regularization=1.0,
    ),
    EstimatorSpec(
        id="hist15-leaf20-l2-1",
        family="hist",
        learning_rate=0.04,
        max_iter_or_estimators=300,
        max_leaf_nodes=15,
        min_samples_leaf=20,
        l2_regularization=1.0,
    ),
    EstimatorSpec(
        id="hist15-leaf20-l2-5",
        family="hist",
        learning_rate=0.04,
        max_iter_or_estimators=300,
        max_leaf_nodes=15,
        min_samples_leaf=20,
        l2_regularization=5.0,
    ),
    EstimatorSpec(
        id="hist31-leaf20-l2-1",
        family="hist",
        learning_rate=0.04,
        max_iter_or_estimators=300,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=1.0,
    ),
    EstimatorSpec(
        id="hist31-leaf20-l2-5",
        family="hist",
        learning_rate=0.04,
        max_iter_or_estimators=300,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=5.0,
    ),
    EstimatorSpec(
        id="hist31-leaf20-l2-10",
        family="hist",
        learning_rate=0.04,
        max_iter_or_estimators=300,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=10.0,
    ),
    EstimatorSpec(
        id="hist31-leaf30-l2-5",
        family="hist",
        learning_rate=0.04,
        max_iter_or_estimators=300,
        max_leaf_nodes=31,
        min_samples_leaf=30,
        l2_regularization=5.0,
    ),
    EstimatorSpec(
        id="gbr-absolute-depth2-leaf8",
        family="gbr_absolute",
        learning_rate=0.03,
        max_iter_or_estimators=180,
        max_depth=2,
        min_samples_leaf=8,
    ),
    EstimatorSpec(
        id="gbr-absolute-depth1-leaf12",
        family="gbr_absolute",
        learning_rate=0.03,
        max_iter_or_estimators=250,
        max_depth=1,
        min_samples_leaf=12,
    ),
)


@dataclass
class FittedEstimator:
    spec: EstimatorSpec
    baseline_column: str
    preprocessor: Any
    estimator: Any
    numeric_features: list[str]
    training_seasons: list[str]
    training_rows: int

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        matrix = self.preprocessor.transform(rows[CAT + self.numeric_features])
        residual = self.estimator.predict(matrix)
        capacity = rows["capacity"].astype(float).to_numpy()
        baseline = rows[self.baseline_column].astype(float).to_numpy()
        return np.clip(baseline + residual * capacity, 0.0, capacity)


def estimator_for(spec: EstimatorSpec):
    if spec.family == "hist":
        return HistGradientBoostingRegressor(
            loss="absolute_error",
            learning_rate=spec.learning_rate,
            max_iter=spec.max_iter_or_estimators,
            max_leaf_nodes=spec.max_leaf_nodes,
            min_samples_leaf=spec.min_samples_leaf,
            l2_regularization=spec.l2_regularization,
            random_state=RANDOM_SEED,
        )
    if spec.family == "gbr_absolute":
        return GradientBoostingRegressor(
            loss="absolute_error",
            n_estimators=spec.max_iter_or_estimators,
            learning_rate=spec.learning_rate,
            max_depth=spec.max_depth,
            min_samples_leaf=spec.min_samples_leaf,
            random_state=RANDOM_SEED,
        )
    raise KeyError(spec.family)


def fit_estimator(
    store: pd.DataFrame,
    training_seasons: list[str],
    candidate: EstimatorSpec,
) -> FittedEstimator:
    runtime_spec = CURRENT_EARLY_RUNTIME_SPECS[HORIZON]
    rows = store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(training_seasons)
        & store[runtime_spec.baseline_column].notna()
    ].copy()
    if rows.empty:
        raise RuntimeError("no T-7 training rows")

    numeric = feature_columns(store, runtime_spec.feature_mode)
    preprocessor = _preprocessor(numeric)
    matrix = preprocessor.fit_transform(rows[CAT + numeric])
    capacity = rows["capacity"].astype(float).to_numpy()
    target = (
        rows["target_attendance"].astype(float).to_numpy() / capacity
        - rows[runtime_spec.baseline_column].astype(float).to_numpy() / capacity
    )
    estimator = estimator_for(candidate)
    estimator.fit(matrix, target)
    return FittedEstimator(
        spec=candidate,
        baseline_column=runtime_spec.baseline_column,
        preprocessor=preprocessor,
        estimator=estimator,
        numeric_features=numeric,
        training_seasons=list(training_seasons),
        training_rows=int(len(rows)),
    )


def score_candidate(
    rows: pd.DataFrame,
    candidate_prediction: np.ndarray,
    incumbent_prediction: np.ndarray,
) -> dict[str, Any]:
    score = comparison_scorecard(rows, candidate_prediction, incumbent_prediction)
    candidate = np.asarray(candidate_prediction, dtype=float)
    incumbent = np.asarray(incumbent_prediction, dtype=float)
    capacity = rows["capacity"].astype(float).to_numpy()
    actual = rows["target_attendance"].astype(float).to_numpy()
    degradation = np.abs(candidate - actual) - np.abs(incumbent - actual)
    worst_index = int(np.argmax(degradation))
    score.update({
        "mean_abs_revision_vs_incumbent": float(np.mean(np.abs(candidate - incumbent))),
        "p90_abs_revision_vs_incumbent": float(np.quantile(np.abs(candidate - incumbent), 0.90)),
        "max_abs_revision_vs_incumbent": float(np.max(np.abs(candidate - incumbent))),
        "worst_event_degradation_share_of_capacity": float(
            degradation[worst_index] / capacity[worst_index]
        ),
    })
    return score


def score_development(store: pd.DataFrame) -> dict[str, Any]:
    runtime_spec = CURRENT_EARLY_RUNTIME_SPECS[HORIZON]
    rows = eligible_rows(store, HORIZON, DEV_SEASON, runtime_spec.baseline_column)
    incumbent = fit_structural_prior_runtime(store, HORIZON, DEV_TRAIN)
    incumbent_prediction = incumbent.predict(rows)
    incumbent_mae = float(
        np.mean(np.abs(incumbent_prediction - rows["target_attendance"].astype(float).to_numpy()))
    )
    verify_incumbent(HORIZON, DEV_SEASON, incumbent_mae, "development")

    scored: list[dict[str, Any]] = []
    for index, candidate in enumerate(CANDIDATES):
        fitted = fit_estimator(store, DEV_TRAIN, candidate)
        prediction = fitted.predict(rows)
        score = score_candidate(rows, prediction, incumbent_prediction)
        scored.append({
            "declared_order": index,
            "candidate": asdict(candidate),
            "training_rows": fitted.training_rows,
            "numeric_feature_count": len(fitted.numeric_features),
            "scorecard": score,
        })

    best_mae = min(float(item["scorecard"]["candidate"]["mae"]) for item in scored)
    tied = [
        item for item in scored
        if np.isclose(
            float(item["scorecard"]["candidate"]["mae"]),
            best_mae,
            rtol=0.0,
            atol=DEVELOPMENT_TIE_ATOL,
        )
    ]
    selected = min(tied, key=lambda item: int(item["declared_order"]))
    ranking = sorted(
        [
            {
                "id": item["candidate"]["id"],
                "declared_order": item["declared_order"],
                "mae": float(item["scorecard"]["candidate"]["mae"]),
                "mae_improvement_vs_incumbent": float(item["scorecard"]["mae_improvement"]),
                "median_ae": float(item["scorecard"]["candidate"]["median_ae"]),
                "p90_ae": float(item["scorecard"]["candidate"]["p90_ae"]),
                "bias": float(item["scorecard"]["candidate"]["bias"]),
                "worst_event_degradation": float(item["scorecard"]["worst_event_degradation"]),
            }
            for item in scored
        ],
        key=lambda item: (item["mae"], item["declared_order"]),
    )
    return {
        "training_seasons": DEV_TRAIN,
        "test_season": DEV_SEASON,
        "rows": int(len(rows)),
        "incumbent_mae": incumbent_mae,
        "candidates": scored,
        "ranking": ranking,
        "best_mae": best_mae,
        "tie_ids": [item["candidate"]["id"] for item in tied],
        "tie_break_rule": "within 1e-9 MAE choose earlier predeclared candidate order",
        "selected_candidate": selected["candidate"],
    }


def score_holdout(
    store: pd.DataFrame,
    season: str,
    training_seasons: list[str],
    selected_spec: EstimatorSpec,
) -> dict[str, Any]:
    runtime_spec = CURRENT_EARLY_RUNTIME_SPECS[HORIZON]
    rows = eligible_rows(store, HORIZON, season, runtime_spec.baseline_column)
    incumbent = fit_structural_prior_runtime(store, HORIZON, training_seasons)
    incumbent_prediction = incumbent.predict(rows)
    incumbent_mae = float(
        np.mean(np.abs(incumbent_prediction - rows["target_attendance"].astype(float).to_numpy()))
    )
    verify_incumbent(HORIZON, season, incumbent_mae, "holdout")

    fitted = fit_estimator(store, training_seasons, selected_spec)
    prediction = fitted.predict(rows)
    score = score_candidate(rows, prediction, incumbent_prediction)
    stage1_worst = STAGE1_FULL_HIST31_WORST_DEGRADATION[season]
    selected_worst = float(score["worst_event_degradation"])
    return {
        "season": season,
        "training_seasons": training_seasons,
        "rows": int(len(rows)),
        "selected_candidate": asdict(selected_spec),
        "scorecard": score,
        "tail_vs_stage1_hist31": {
            "stage1_hist31_worst_degradation": stage1_worst,
            "selected_worst_degradation": selected_worst,
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
    actual_hash = sha256_file(args.historical_runtime)
    expected_hash = manifest["historical_runtime"]["sha256"]
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    ids = [candidate.id for candidate in CANDIDATES]
    if len(ids) != len(set(ids)):
        raise RuntimeError("candidate IDs must be unique")

    store = load_feature_store(args.historical_runtime)
    development = score_development(store)
    selected_dict = development["selected_candidate"]
    selected = next(candidate for candidate in CANDIDATES if candidate.id == selected_dict["id"])

    holdouts = [
        score_holdout(store, season, train, selected)
        for season, train in HOLDOUTS
    ]

    mean_incumbent = float(np.mean([
        item["scorecard"]["incumbent"]["mae"] for item in holdouts
    ]))
    mean_selected = float(np.mean([
        item["scorecard"]["candidate"]["mae"] for item in holdouts
    ]))
    mean_improvement = mean_incumbent - mean_selected
    improves_both = all(float(item["scorecard"]["mae_improvement"]) > 0 for item in holdouts)
    tail_reduced_both = all(
        float(item["tail_vs_stage1_hist31"]["worst_degradation_reduction"]) > 0
        for item in holdouts
    )

    if selected.id == "hist31-leaf10-l2-1":
        signal = "STAGE1_HIST31_REMAINS_DEVELOPMENT_WINNER"
    elif improves_both and tail_reduced_both:
        signal = "REGULARIZED_WINNER_IMPROVES_BOTH_AND_REDUCES_TAIL"
    elif mean_improvement > 0 and tail_reduced_both:
        signal = "REGULARIZED_WINNER_POSITIVE_MEAN_AND_REDUCES_TAIL"
    elif mean_improvement > 0:
        signal = "REGULARIZED_WINNER_POSITIVE_MEAN_TAIL_NOT_SOLVED"
    else:
        signal = "REGULARIZED_WINNER_NOT_PROVEN_ON_REFERENCES"

    result = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_HISTORICAL_CHALLENGER_EVIDENCE",
        "evidence_class": "EXPOSED_HISTORICAL_REFERENCE_SEASONS",
        "promotion_allowed": False,
        "horizon": HORIZON,
        "dependencies": {
            "stage1_result_json_sha256": STAGE1_RESULT_JSON_SHA256,
            "stage2_result_json_sha256": STAGE2_RESULT_JSON_SHA256,
            "stage1_hist31_worst_degradation": STAGE1_FULL_HIST31_WORST_DEGRADATION,
        },
        "protocol": {
            "selection_training_seasons": DEV_TRAIN,
            "selection_development_season": DEV_SEASON,
            "selection_metric": "MAE",
            "selection_tie_rule": "within 1e-9 MAE choose earlier predeclared candidate order",
            "holdouts": [
                {"season": season, "training_seasons": train}
                for season, train in HOLDOUTS
            ],
            "holdout_selection_allowed": False,
            "one_dimension_changed": "estimator family / regularization only",
            "baseline_fixed": CURRENT_EARLY_RUNTIME_SPECS[HORIZON].baseline_column,
            "feature_mode_fixed": CURRENT_EARLY_RUNTIME_SPECS[HORIZON].feature_mode,
            "season_weights": "uniform",
            "event_is_independent_unit": True,
            "random_snapshot_split": False,
            "future_leakage_allowed": False,
            "production_activation": False,
        },
        "candidate_contract": [asdict(candidate) for candidate in CANDIDATES],
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
        "selected_candidate": asdict(selected),
        "holdouts": holdouts,
        "summary": {
            "mean_reference_incumbent_mae": mean_incumbent,
            "mean_reference_selected_mae": mean_selected,
            "mean_reference_mae_improvement_vs_incumbent": mean_improvement,
            "selected_improves_both_reference_seasons": improves_both,
            "selected_reduces_stage1_hist31_tail_both_seasons": tail_reduced_both,
            "signal": signal,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "development_ranking": development["ranking"],
        "selected_candidate": asdict(selected),
        "summary": result["summary"],
        "holdouts": [
            {
                "season": item["season"],
                "incumbent_mae": item["scorecard"]["incumbent"]["mae"],
                "selected_mae": item["scorecard"]["candidate"]["mae"],
                "mae_improvement": item["scorecard"]["mae_improvement"],
                "median_ae": item["scorecard"]["candidate"]["median_ae"],
                "p90_ae": item["scorecard"]["candidate"]["p90_ae"],
                "bias": item["scorecard"]["candidate"]["bias"],
                "worst_event_degradation": item["scorecard"]["worst_event_degradation"],
                "worst_event": item["scorecard"]["worst_event"],
                "tail_vs_stage1_hist31": item["tail_vs_stage1_hist31"],
            }
            for item in holdouts
        ],
        "promotion_allowed": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
