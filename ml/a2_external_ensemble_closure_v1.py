#!/usr/bin/env python3
"""a2 all-horizon external model + heterogeneous ensemble closure audit.

This audit closes a specific gap left by the earlier a2 work:
CatBoost/LightGBM/XGBoost were tested under the canonical contract only at T-7.

Protocol:
- fixed committed historical runtime input;
- development selection only on 2023/24 after training on 2021/22+2022/23;
- current frozen a2 historical base is the benchmark for each horizon;
- single-family candidates plus two predeclared heterogeneous ensembles;
- ensemble component variants and weights are selected on development only;
- unchanged selected contract is then refit on expanding history and scored on
  exposed 2024/25 and 2025/26 references;
- no b2/c2/live layer, no production write, no freeze mutation.

A positive result advances only to a separately versioned fixed-temporal
robustness audit. A failed challenger closes this challenger, not model R&D.
"""
from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import catboost
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
    _estimator,
    _preprocessor,
    feature_columns,
    fit_structural_prior_runtime,
)
from ml.pre_live_baseline_optimization_v1 import (
    DEV_SEASON,
    DEV_TRAIN,
    HOLDOUTS,
    HORIZONS,
    comparison_scorecard,
    eligible_rows,
    load_feature_store,
    sha256_file,
    verify_incumbent,
)

EXPERIMENT = "a2-external-ensemble-closure-v1"
WORKSTREAM = "a2 — External model + heterogeneous ensemble closure audit"
RANDOM_SEED = 42
WEIGHT_GRID_STEP = 0.25
MIN_NONZERO_ENSEMBLE_MEMBERS = 2

Family = Literal["current_a2", "hist", "catboost", "lightgbm", "xgboost"]


@dataclass(frozen=True)
class CandidateSpec:
    id: str
    family: Family
    variant: str


@dataclass
class FittedCandidate:
    horizon: str
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


def candidate_specs(horizon: str) -> tuple[CandidateSpec, ...]:
    specs: list[CandidateSpec] = [
        CandidateSpec("current-a2-base", "current_a2", "frozen_current_a2"),
    ]
    if horizon != "T-7":
        specs.append(CandidateSpec("hist31-leaf20-l2-1", "hist", "hist31"))
    specs.extend([
        CandidateSpec("catboost-mae-depth4-l2-5", "catboost", "depth4"),
        CandidateSpec("catboost-mae-depth6-l2-5", "catboost", "depth6"),
        CandidateSpec("lightgbm-l1-leaves15-l2-5", "lightgbm", "leaves15"),
        CandidateSpec("lightgbm-l1-leaves31-l2-5", "lightgbm", "leaves31"),
        CandidateSpec("xgboost-l1-depth2-l2-5", "xgboost", "depth2"),
        CandidateSpec("xgboost-l1-depth3-l2-5", "xgboost", "depth3"),
    ])
    ids = [item.id for item in specs]
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"duplicate candidate IDs for {horizon}")
    return tuple(specs)


def estimator_for(horizon: str, spec: CandidateSpec):
    runtime = CURRENT_EARLY_RUNTIME_SPECS[horizon]

    if spec.family == "current_a2":
        if horizon == "T-7":
            return HistGradientBoostingRegressor(
                loss="absolute_error",
                learning_rate=0.04,
                max_iter=300,
                max_leaf_nodes=31,
                min_samples_leaf=20,
                l2_regularization=1.0,
                random_state=RANDOM_SEED,
            )
        return _estimator(runtime.estimator_name)

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
    horizon: str,
    training_seasons: list[str],
    spec: CandidateSpec,
) -> FittedCandidate:
    runtime = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = store[
        (store["horizon"].astype(str) == horizon)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(training_seasons)
        & store[runtime.baseline_column].notna()
    ].copy()
    if rows.empty:
        raise RuntimeError(f"no training rows for {horizon}")

    numeric = feature_columns(store, runtime.feature_mode)
    preprocessor = _preprocessor(numeric)
    matrix = preprocessor.fit_transform(rows[CAT + numeric])
    capacity = rows["capacity"].astype(float).to_numpy()
    target = (
        rows["target_attendance"].astype(float).to_numpy() / capacity
        - rows[runtime.baseline_column].astype(float).to_numpy() / capacity
    )
    estimator = estimator_for(horizon, spec)
    estimator.fit(matrix, target)

    return FittedCandidate(
        horizon=horizon,
        spec=spec,
        baseline_column=runtime.baseline_column,
        preprocessor=preprocessor,
        estimator=estimator,
        numeric_features=numeric,
        training_seasons=list(training_seasons),
        training_rows=int(len(rows)),
    )


def current_a2_prediction(
    store: pd.DataFrame,
    horizon: str,
    training_seasons: list[str],
    rows: pd.DataFrame,
) -> np.ndarray:
    spec = next(item for item in candidate_specs(horizon) if item.family == "current_a2")
    return fit_candidate(store, horizon, training_seasons, spec).predict(rows)


def structural_incumbent_prediction(
    store: pd.DataFrame,
    horizon: str,
    training_seasons: list[str],
    rows: pd.DataFrame,
    season: str,
    split_name: str,
) -> np.ndarray:
    incumbent = fit_structural_prior_runtime(store, horizon, training_seasons)
    prediction = incumbent.predict(rows)
    actual = rows["target_attendance"].astype(float).to_numpy()
    incumbent_mae = float(np.mean(np.abs(prediction - actual)))
    verify_incumbent(horizon, season, incumbent_mae, split_name)
    return prediction


def mae(actual: np.ndarray, prediction: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(prediction, dtype=float) - np.asarray(actual, dtype=float))))


def simplex_weight_vectors(
    member_count: int,
    step: float = WEIGHT_GRID_STEP,
    min_nonzero: int = MIN_NONZERO_ENSEMBLE_MEMBERS,
) -> list[tuple[float, ...]]:
    units = int(round(1.0 / step))
    if not np.isclose(units * step, 1.0):
        raise ValueError("weight step must divide 1.0 exactly")
    vectors: list[tuple[float, ...]] = []
    for cuts in itertools.product(range(units + 1), repeat=member_count):
        if sum(cuts) != units:
            continue
        if sum(value > 0 for value in cuts) < min_nonzero:
            continue
        vectors.append(tuple(value / units for value in cuts))
    return vectors


def weighted_prediction(predictions: list[np.ndarray], weights: tuple[float, ...]) -> np.ndarray:
    if len(predictions) != len(weights):
        raise ValueError("prediction/weight length mismatch")
    matrix = np.vstack([np.asarray(item, dtype=float) for item in predictions])
    return np.average(matrix, axis=0, weights=np.asarray(weights, dtype=float))


def median_prediction(predictions: list[np.ndarray]) -> np.ndarray:
    matrix = np.vstack([np.asarray(item, dtype=float) for item in predictions])
    return np.median(matrix, axis=0)


def best_by_family(scored: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: list[dict[str, Any]] = []
    families = sorted({str(item["spec"]["family"]) for item in scored})
    for family in families:
        family_rows = [item for item in scored if item["spec"]["family"] == family]
        family_rows.sort(key=lambda item: (float(item["mae"]), int(item["declared_order"])))
        best.append(family_rows[0])
    best.sort(key=lambda item: int(item["declared_order"]))
    return best


def select_weighted_ensemble(
    actual: np.ndarray,
    member_ids: list[str],
    member_predictions: list[np.ndarray],
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for order, weights in enumerate(simplex_weight_vectors(len(member_ids))):
        prediction = weighted_prediction(member_predictions, weights)
        candidates.append({
            "declared_order": order,
            "weights": list(weights),
            "mae": mae(actual, prediction),
            "prediction": prediction,
        })
    candidates.sort(key=lambda item: (float(item["mae"]), int(item["declared_order"])))
    selected = candidates[0]
    return {
        "id": "weighted-top-family-grid025",
        "member_ids": list(member_ids),
        "weights": selected["weights"],
        "mae": float(selected["mae"]),
        "prediction": selected["prediction"],
        "grid_step": WEIGHT_GRID_STEP,
        "min_nonzero_members": MIN_NONZERO_ENSEMBLE_MEMBERS,
        "candidate_weight_vectors": len(candidates),
    }


def development_horizon(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    runtime = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = eligible_rows(store, horizon, DEV_SEASON, runtime.baseline_column)
    actual = rows["target_attendance"].astype(float).to_numpy()

    structural = structural_incumbent_prediction(
        store, horizon, DEV_TRAIN, rows, DEV_SEASON, "development"
    )
    current_a2 = current_a2_prediction(store, horizon, DEV_TRAIN, rows)

    scored: list[dict[str, Any]] = []
    prediction_by_id: dict[str, np.ndarray] = {}

    for order, spec in enumerate(candidate_specs(horizon)):
        fitted = fit_candidate(store, horizon, DEV_TRAIN, spec)
        prediction = fitted.predict(rows)
        prediction_by_id[spec.id] = prediction
        score = comparison_scorecard(rows, prediction, current_a2)
        scored.append({
            "declared_order": order,
            "spec": asdict(spec),
            "training_rows": fitted.training_rows,
            "numeric_feature_count": len(fitted.numeric_features),
            "mae": float(score["candidate"]["mae"]),
            "mae_improvement_vs_current_a2": float(score["mae_improvement"]),
            "scorecard_vs_current_a2": score,
        })

    family_winners = best_by_family(scored)
    ensemble_member_ids = [str(item["spec"]["id"]) for item in family_winners]
    ensemble_predictions = [prediction_by_id[item] for item in ensemble_member_ids]

    median_pred = median_prediction(ensemble_predictions)
    median_score = comparison_scorecard(rows, median_pred, current_a2)

    weighted = select_weighted_ensemble(actual, ensemble_member_ids, ensemble_predictions)
    weighted_score = comparison_scorecard(rows, weighted["prediction"], current_a2)

    final_candidates: list[dict[str, Any]] = [
        {
            "kind": "single",
            "id": item["spec"]["id"],
            "family": item["spec"]["family"],
            "variant": item["spec"]["variant"],
            "mae": float(item["mae"]),
            "declared_order": int(item["declared_order"]),
        }
        for item in scored
    ]
    final_candidates.extend([
        {
            "kind": "median_ensemble",
            "id": "median-top-family",
            "member_ids": ensemble_member_ids,
            "mae": float(median_score["candidate"]["mae"]),
            "declared_order": 1000,
        },
        {
            "kind": "weighted_ensemble",
            "id": weighted["id"],
            "member_ids": ensemble_member_ids,
            "weights": weighted["weights"],
            "mae": float(weighted_score["candidate"]["mae"]),
            "declared_order": 1001,
        },
    ])
    final_candidates.sort(key=lambda item: (float(item["mae"]), int(item["declared_order"])))
    selected = final_candidates[0]

    current_a2_mae = mae(actual, current_a2)
    structural_mae = mae(actual, structural)
    ranking = [
        {
            "id": item["id"],
            "kind": item["kind"],
            "mae": float(item["mae"]),
            "improvement_vs_current_a2": float(current_a2_mae - float(item["mae"])),
        }
        for item in final_candidates
    ]

    return {
        "horizon": horizon,
        "training_seasons": DEV_TRAIN,
        "test_season": DEV_SEASON,
        "rows": int(len(rows)),
        "structural_incumbent_mae": structural_mae,
        "current_a2_mae": current_a2_mae,
        "single_candidates": scored,
        "top_family_members": [
            {
                "id": item["spec"]["id"],
                "family": item["spec"]["family"],
                "variant": item["spec"]["variant"],
                "mae": float(item["mae"]),
            }
            for item in family_winners
        ],
        "median_ensemble": {
            "id": "median-top-family",
            "member_ids": ensemble_member_ids,
            "scorecard_vs_current_a2": median_score,
        },
        "weighted_ensemble": {
            key: value for key, value in weighted.items() if key != "prediction"
        }
        | {"scorecard_vs_current_a2": weighted_score},
        "final_ranking": ranking,
        "selected_contract": selected,
    }


def prediction_for_contract(
    store: pd.DataFrame,
    horizon: str,
    training_seasons: list[str],
    rows: pd.DataFrame,
    development: dict[str, Any],
) -> np.ndarray:
    selected = development["selected_contract"]
    kind = selected["kind"]

    if kind == "single":
        candidate_id = str(selected["id"])
        spec = next(item for item in candidate_specs(horizon) if item.id == candidate_id)
        return fit_candidate(store, horizon, training_seasons, spec).predict(rows)

    member_ids = list(selected["member_ids"])
    member_predictions: list[np.ndarray] = []
    for candidate_id in member_ids:
        spec = next(item for item in candidate_specs(horizon) if item.id == candidate_id)
        member_predictions.append(
            fit_candidate(store, horizon, training_seasons, spec).predict(rows)
        )

    if kind == "median_ensemble":
        return median_prediction(member_predictions)
    if kind == "weighted_ensemble":
        return weighted_prediction(member_predictions, tuple(float(x) for x in selected["weights"]))
    raise KeyError(kind)


def holdout_horizon(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    development: dict[str, Any],
) -> dict[str, Any]:
    runtime = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = eligible_rows(store, horizon, season, runtime.baseline_column)
    actual = rows["target_attendance"].astype(float).to_numpy()

    structural = structural_incumbent_prediction(
        store, horizon, training_seasons, rows, season, "holdout"
    )
    current_a2 = current_a2_prediction(store, horizon, training_seasons, rows)
    challenger = prediction_for_contract(
        store, horizon, training_seasons, rows, development
    )

    score = comparison_scorecard(rows, challenger, current_a2)
    return {
        "season": season,
        "training_seasons": list(training_seasons),
        "rows": int(len(rows)),
        "structural_incumbent_mae": mae(actual, structural),
        "current_a2_mae": mae(actual, current_a2),
        "selected_contract": development["selected_contract"],
        "scorecard_vs_current_a2": score,
    }


def horizon_decision(development: dict[str, Any], holdouts: list[dict[str, Any]]) -> dict[str, Any]:
    selected = development["selected_contract"]
    dev_gain = float(
        development["current_a2_mae"] - float(selected["mae"])
    )
    ref_gains = [
        float(item["scorecard_vs_current_a2"]["mae_improvement"])
        for item in holdouts
    ]
    mean_ref_gain = float(np.mean(ref_gains))
    beats_both_refs = all(value > 0 for value in ref_gains)
    selected_is_current = selected["id"] == "current-a2-base"

    if selected_is_current:
        decision = "NO_CHANGE_CURRENT_A2_WINS_DEVELOPMENT"
    elif dev_gain <= 0:
        decision = "NO_CHANGE_NO_DEVELOPMENT_GAIN"
    elif beats_both_refs:
        decision = "ADVANCE_SELECTED_CONTRACT_TO_FIXED_TEMPORAL_ROBUSTNESS_AUDIT"
    elif mean_ref_gain > 0:
        decision = "RETAIN_CURRENT_A2_MIXED_EXPOSED_REFERENCE_SIGNAL"
    else:
        decision = "RETAIN_CURRENT_A2_CHALLENGER_FAILS_EXPOSED_REFERENCES"

    return {
        "decision": decision,
        "selected_contract": selected,
        "development_gain_vs_current_a2": dev_gain,
        "reference_gains_vs_current_a2": ref_gains,
        "mean_reference_gain_vs_current_a2": mean_ref_gain,
        "beats_both_exposed_references": beats_both_refs,
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

    store = load_feature_store(args.historical_runtime)
    development: dict[str, Any] = {}
    holdouts: dict[str, list[dict[str, Any]]] = {}
    decisions: dict[str, Any] = {}

    for horizon in HORIZONS:
        dev = development_horizon(store, horizon)
        development[horizon] = dev
        refs = [
            holdout_horizon(store, horizon, season, train, dev)
            for season, train in HOLDOUTS
        ]
        holdouts[horizon] = refs
        decisions[horizon] = horizon_decision(dev, refs)

    advancing = [
        horizon
        for horizon, item in decisions.items()
        if item["decision"] == "ADVANCE_SELECTED_CONTRACT_TO_FIXED_TEMPORAL_ROBUSTNESS_AUDIT"
    ]

    if advancing:
        overall = "A2_CLOSURE_AUDIT_FOUND_ROBUSTNESS_FOLLOWUP_CANDIDATES"
    else:
        overall = "A2_EXTERNAL_ENSEMBLE_CLOSURE_NO_ADVANCING_CHALLENGER"

    payload = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "HISTORICAL_RND_ONLY_NO_PRODUCTION_WRITE",
        "protocol": {
            "development_train": DEV_TRAIN,
            "development_season": DEV_SEASON,
            "exposed_references": [
                {"season": season, "training_seasons": train}
                for season, train in HOLDOUTS
            ],
            "horizons": HORIZONS,
            "selection_uses_references": False,
            "selection_metric": "development MAE",
            "ensemble_weight_grid_step": WEIGHT_GRID_STEP,
            "ensemble_min_nonzero_members": MIN_NONZERO_ENSEMBLE_MEMBERS,
            "random_seed": RANDOM_SEED,
            "production_write": False,
            "frozen_pre_live_mutation": False,
        },
        "runtime": {
            "python_dependencies": {
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scikit_learn": sklearn.__version__,
                "catboost": catboost.__version__,
                "lightgbm": lightgbm.__version__,
                "xgboost": xgboost.__version__,
            },
            "historical_runtime_sha256": actual_hash,
            "manifest_sha256": sha256_file(args.manifest),
        },
        "development": development,
        "holdouts": holdouts,
        "decisions": decisions,
        "summary": {
            "overall_signal": overall,
            "advancing_horizons": advancing,
            "advancing_count": len(advancing),
            "frozen_current_a2_changed": False,
            "production_changed": False,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
