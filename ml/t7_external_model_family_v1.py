#!/usr/bin/env python3
"""T-7 external model-family stage 4.

Compare materially different tabular boosting families while keeping the T-7
baseline, feature contract, preprocessing, target and evaluation protocol fixed.

Selection is 2023/24 development MAE only. After one candidate is frozen, only
that candidate and the production incumbent are scored on exposed 2024/25 and
2025/26 references. No production activation occurs in this experiment.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import catboost
import joblib
import lightgbm
import numpy as np
import pandas as pd
import sklearn
import xgboost
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from xgboost import XGBRegressor

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

EXPERIMENT = "t7-external-model-family-v1"
WORKSTREAM = "a2 — Historical / Structural Prior optimization — T-7 external model family stage 4"
HORIZON = "T-7"
RANDOM_SEED = 42
DEVELOPMENT_TIE_ATOL = 1e-9

STAGE3_RESULT_JSON_SHA256 = "83da3d85daa7c7bc844b8cb6b63cdf47070068cdabb774d0f4c01e5a3e0258fe"
STAGE3_REFERENCE = {
    "2024/2025": {
        "mae": 1650.965008260134,
        "worst_degradation": 4094.161934230611,
    },
    "2025/2026": {
        "mae": 1773.797066783137,
        "worst_degradation": 3700.561222383304,
    },
}

Family = Literal["hist", "catboost", "lightgbm", "xgboost"]


@dataclass(frozen=True)
class CandidateSpec:
    id: str
    family: Family
    variant: str


CANDIDATES: tuple[CandidateSpec, ...] = (
    CandidateSpec("hist31-leaf20-l2-1", "hist", "internal_stage3"),
    CandidateSpec("catboost-mae-depth4-l2-5", "catboost", "depth4"),
    CandidateSpec("catboost-mae-depth6-l2-5", "catboost", "depth6"),
    CandidateSpec("lightgbm-l1-leaves15-l2-5", "lightgbm", "leaves15"),
    CandidateSpec("lightgbm-l1-leaves31-l2-5", "lightgbm", "leaves31"),
    CandidateSpec("xgboost-l1-depth2-l2-5", "xgboost", "depth2"),
    CandidateSpec("xgboost-l1-depth3-l2-5", "xgboost", "depth3"),
)


@dataclass
class FittedCandidate:
    spec: CandidateSpec
    baseline_column: str
    preprocessor: Any
    estimator: Any
    numeric_features: list[str]
    training_seasons: list[str]
    training_rows: int

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        matrix = self.preprocessor.transform(rows[CAT + self.numeric_features])
        residual = np.asarray(self.estimator.predict(matrix), dtype=float)
        capacity = rows["capacity"].astype(float).to_numpy()
        baseline = rows[self.baseline_column].astype(float).to_numpy()
        return np.clip(baseline + residual * capacity, 0.0, capacity)


def estimator_for(spec: CandidateSpec):
    if spec.family == "hist":
        return HistGradientBoostingRegressor(
            loss="absolute_error",
            learning_rate=0.04,
            max_iter=300,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            l2_regularization=1.0,
            random_state=RANDOM_SEED,
        )

    if spec.family == "catboost":
        depth = 4 if spec.variant == "depth4" else 6
        return CatBoostRegressor(
            loss_function="MAE",
            iterations=400,
            learning_rate=0.03,
            depth=depth,
            l2_leaf_reg=5.0,
            random_seed=RANDOM_SEED,
            random_strength=0.0,
            bootstrap_type="No",
            allow_writing_files=False,
            verbose=False,
            thread_count=1,
        )

    if spec.family == "lightgbm":
        num_leaves = 15 if spec.variant == "leaves15" else 31
        return LGBMRegressor(
            objective="regression_l1",
            n_estimators=400,
            learning_rate=0.03,
            num_leaves=num_leaves,
            min_child_samples=20,
            reg_lambda=5.0,
            reg_alpha=0.0,
            subsample=1.0,
            colsample_bytree=1.0,
            deterministic=True,
            force_col_wise=True,
            random_state=RANDOM_SEED,
            n_jobs=1,
            verbosity=-1,
        )

    if spec.family == "xgboost":
        max_depth = 2 if spec.variant == "depth2" else 3
        return XGBRegressor(
            objective="reg:absoluteerror",
            eval_metric="mae",
            n_estimators=400,
            learning_rate=0.03,
            max_depth=max_depth,
            min_child_weight=5.0,
            reg_lambda=5.0,
            reg_alpha=0.0,
            gamma=0.0,
            subsample=1.0,
            colsample_bytree=1.0,
            tree_method="hist",
            random_state=RANDOM_SEED,
            n_jobs=1,
            verbosity=0,
        )

    raise KeyError(spec.family)


def fit_candidate(
    store: pd.DataFrame,
    training_seasons: list[str],
    candidate: CandidateSpec,
) -> FittedCandidate:
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

    return FittedCandidate(
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
    actual = rows["target_attendance"].astype(float).to_numpy()
    incumbent_mae = float(np.mean(np.abs(incumbent_prediction - actual)))
    verify_incumbent(HORIZON, DEV_SEASON, incumbent_mae, "development")

    scored: list[dict[str, Any]] = []
    for declared_order, candidate in enumerate(CANDIDATES):
        fitted = fit_candidate(store, DEV_TRAIN, candidate)
        prediction = fitted.predict(rows)
        score = score_candidate(rows, prediction, incumbent_prediction)
        scored.append({
            "declared_order": declared_order,
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
                "family": item["candidate"]["family"],
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
    selected: CandidateSpec,
) -> dict[str, Any]:
    runtime_spec = CURRENT_EARLY_RUNTIME_SPECS[HORIZON]
    rows = eligible_rows(store, HORIZON, season, runtime_spec.baseline_column)
    incumbent = fit_structural_prior_runtime(store, HORIZON, training_seasons)
    incumbent_prediction = incumbent.predict(rows)
    actual = rows["target_attendance"].astype(float).to_numpy()
    incumbent_mae = float(np.mean(np.abs(incumbent_prediction - actual)))
    verify_incumbent(HORIZON, season, incumbent_mae, "holdout")

    fitted = fit_candidate(store, training_seasons, selected)
    prediction = fitted.predict(rows)
    score = score_candidate(rows, prediction, incumbent_prediction)
    stage3 = STAGE3_REFERENCE[season]
    return {
        "season": season,
        "training_seasons": training_seasons,
        "rows": int(len(rows)),
        "selected_candidate": asdict(selected),
        "scorecard": score,
        "comparison_to_frozen_stage3": {
            "stage3_mae": stage3["mae"],
            "selected_mae": float(score["candidate"]["mae"]),
            "mae_delta_selected_minus_stage3": float(score["candidate"]["mae"] - stage3["mae"]),
            "stage3_worst_degradation": stage3["worst_degradation"],
            "selected_worst_degradation": float(score["worst_event_degradation"]),
            "worst_degradation_delta_selected_minus_stage3": float(
                score["worst_event_degradation"] - stage3["worst_degradation"]
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
    selected_id = development["selected_candidate"]["id"]
    selected = next(candidate for candidate in CANDIDATES if candidate.id == selected_id)

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
    mean_stage3 = float(np.mean([STAGE3_REFERENCE[item["season"]]["mae"] for item in holdouts]))
    mean_improvement = mean_incumbent - mean_selected
    improves_both = all(float(item["scorecard"]["mae_improvement"]) > 0 for item in holdouts)
    beats_stage3_both = all(
        float(item["comparison_to_frozen_stage3"]["mae_delta_selected_minus_stage3"]) < 0
        for item in holdouts
    )
    tail_better_than_stage3_both = all(
        float(item["comparison_to_frozen_stage3"]["worst_degradation_delta_selected_minus_stage3"]) < 0
        for item in holdouts
    )

    if selected.family == "hist":
        signal = "INTERNAL_STAGE3_HGB_REMAINS_DEVELOPMENT_WINNER"
    elif beats_stage3_both and tail_better_than_stage3_both:
        signal = "EXTERNAL_WINNER_BEATS_STAGE3_MAE_AND_TAIL_BOTH_REFERENCES"
    elif mean_selected < mean_stage3 and improves_both:
        signal = "EXTERNAL_WINNER_LOWER_MEAN_THAN_STAGE3_TAIL_MIXED"
    elif improves_both:
        signal = "EXTERNAL_WINNER_IMPROVES_INCUMBENT_BOTH_NOT_STAGE3"
    else:
        signal = "EXTERNAL_WINNER_NOT_PROVEN_ROBUST"

    result = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_HISTORICAL_CHALLENGER_EVIDENCE",
        "evidence_class": "EXPOSED_HISTORICAL_REFERENCE_SEASONS",
        "promotion_allowed": False,
        "horizon": HORIZON,
        "dependencies": {
            "stage3_result_json_sha256": STAGE3_RESULT_JSON_SHA256,
            "stage3_reference": STAGE3_REFERENCE,
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
            "changed_dimension": "estimator family only",
            "baseline_fixed": CURRENT_EARLY_RUNTIME_SPECS[HORIZON].baseline_column,
            "feature_mode_fixed": CURRENT_EARLY_RUNTIME_SPECS[HORIZON].feature_mode,
            "preprocessing_fixed": "incumbent one-hot + median imputation + missing indicators",
            "native_categorical_features_used": False,
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
            "catboost": catboost.__version__,
            "lightgbm": lightgbm.__version__,
            "xgboost": xgboost.__version__,
        },
        "development": development,
        "selected_candidate": asdict(selected),
        "holdouts": holdouts,
        "summary": {
            "mean_reference_incumbent_mae": mean_incumbent,
            "mean_reference_selected_mae": mean_selected,
            "mean_reference_stage3_mae": mean_stage3,
            "mean_reference_mae_improvement_vs_incumbent": mean_improvement,
            "mean_reference_mae_delta_selected_minus_stage3": mean_selected - mean_stage3,
            "selected_improves_both_reference_seasons": improves_both,
            "selected_beats_stage3_mae_both_reference_seasons": beats_stage3_both,
            "selected_beats_stage3_tail_both_reference_seasons": tail_better_than_stage3_both,
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
                "comparison_to_frozen_stage3": item["comparison_to_frozen_stage3"],
            }
            for item in holdouts
        ],
        "promotion_allowed": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
