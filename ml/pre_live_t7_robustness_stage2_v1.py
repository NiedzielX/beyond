#!/usr/bin/env python3
"""T-7 Pre-Live robustness / trust-region blend experiment.

Stage-2 objective:
- preserve the MAE uplift of the stage-1 T-7 Hist31 challenger;
- reduce severe single-event regressions versus the frozen incumbent;
- select the robustness policy using development-era rolling folds only;
- score the frozen selection unchanged on exposed 2024/25 and 2025/26 references;
- never change production automatically.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor

from ml.demand_engine.freeze_structural_prior_artifacts import (
    EXPECTED_DEVELOPMENT_MAE,
    EXPECTED_HOLDOUT_ATOL,
    EXPECTED_HOLDOUT_MAE,
)
from ml.demand_engine.structural_prior_runtime import (
    CAT,
    CURRENT_EARLY_RUNTIME_SPECS,
    _preprocessor,
    feature_columns,
    fit_structural_prior_runtime,
)
from ml.pre_live_baseline_optimization_v1 import (
    comparison_scorecard,
    eligible_rows,
    load_feature_store,
    metrics,
    sha256_file,
)

EXPERIMENT = "pre-live-t7-robustness-stage2-v1"
WORKSTREAM = "a2 — Historical / Structural Prior optimization"
HORIZON = "T-7"
RANDOM_SEED = 42

DEVELOPMENT_FOLDS = [
    ("2022/2023", ["2021/2022"]),
    ("2023/2024", ["2021/2022", "2022/2023"]),
]
REFERENCE_HOLDOUTS = [
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]

ALPHAS = (0.25, 0.50, 0.75, 1.00)
CAP_FRACTIONS: tuple[float | None, ...] = (0.05, 0.10, None)
ROBUST_GAIN_RETENTION = 0.80
SELECTION_ATOL = 1e-9

HIST31_CONFIG = {
    "loss": "absolute_error",
    "learning_rate": 0.04,
    "max_iter": 300,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 10,
    "l2_regularization": 1.0,
    "random_state": RANDOM_SEED,
}

# Canonical Stage-1 T-7 Hist31 values. Stage 2 must reproduce these exactly
# before any blend/cap evidence is accepted. This catches fit-contract drift
# such as omitting the explicit uniform sample_weight used in Stage 1.
EXPECTED_STAGE1_HIST31_MAE = {
    "2023/2024": 2379.4562743080337,
    "2024/2025": 1672.1378964152464,
    "2025/2026": 1770.2165629066017,
}
EXPECTED_STAGE1_HIST31_ATOL = 1e-9


@dataclass(frozen=True)
class RobustCandidate:
    id: str
    alpha: float
    cap_fraction: float | None


@dataclass
class FittedHist31:
    preprocessor: Any
    estimator: HistGradientBoostingRegressor
    numeric_features: list[str]
    baseline_column: str
    training_rows: int
    training_seasons: list[str]

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        matrix = self.preprocessor.transform(rows[CAT + self.numeric_features])
        residual = self.estimator.predict(matrix)
        capacity = rows["capacity"].astype(float).to_numpy()
        baseline = rows[self.baseline_column].astype(float).to_numpy()
        return np.clip(baseline + residual * capacity, 0.0, capacity)


def robust_candidates() -> list[RobustCandidate]:
    candidates = [RobustCandidate(id="incumbent", alpha=0.0, cap_fraction=None)]
    for alpha in ALPHAS:
        for cap_fraction in CAP_FRACTIONS:
            cap_label = "uncapped" if cap_fraction is None else f"cap{int(round(cap_fraction * 100)):02d}"
            candidates.append(
                RobustCandidate(
                    id=f"hist31-a{int(round(alpha * 100)):03d}-{cap_label}",
                    alpha=float(alpha),
                    cap_fraction=cap_fraction,
                )
            )
    return candidates


def fit_hist31(store: pd.DataFrame, training_seasons: list[str]) -> FittedHist31:
    spec = CURRENT_EARLY_RUNTIME_SPECS[HORIZON]
    rows = store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(training_seasons)
        & store[spec.baseline_column].notna()
    ].copy()
    if rows.empty:
        raise RuntimeError(f"no eligible T-7 training rows for {training_seasons}")

    numeric = feature_columns(store, spec.feature_mode)
    preprocessor = _preprocessor(numeric)
    x_train = preprocessor.fit_transform(rows[CAT + numeric])
    capacity = rows["capacity"].astype(float).to_numpy()
    target = (
        rows["target_attendance"].astype(float).to_numpy() / capacity
        - rows[spec.baseline_column].astype(float).to_numpy() / capacity
    )

    estimator = HistGradientBoostingRegressor(**HIST31_CONFIG)
    # Exact Stage-1 contract: even uniform weights are passed explicitly.
    sample_weight = np.ones(len(rows), dtype=float)
    estimator.fit(x_train, target, sample_weight=sample_weight)
    return FittedHist31(
        preprocessor=preprocessor,
        estimator=estimator,
        numeric_features=numeric,
        baseline_column=spec.baseline_column,
        training_rows=int(len(rows)),
        training_seasons=list(training_seasons),
    )


def apply_robust_policy(
    incumbent_prediction: np.ndarray,
    hist31_prediction: np.ndarray,
    capacity: np.ndarray,
    candidate: RobustCandidate,
) -> np.ndarray:
    incumbent_prediction = np.asarray(incumbent_prediction, dtype=float)
    hist31_prediction = np.asarray(hist31_prediction, dtype=float)
    capacity = np.asarray(capacity, dtype=float)

    if candidate.alpha == 0.0:
        return incumbent_prediction.copy()

    delta = candidate.alpha * (hist31_prediction - incumbent_prediction)
    if candidate.cap_fraction is not None:
        bound = candidate.cap_fraction * capacity
        delta = np.clip(delta, -bound, bound)
    return np.clip(incumbent_prediction + delta, 0.0, capacity)


def _verify_known_incumbent(season: str, mae: float) -> None:
    if season == "2023/2024":
        expected = EXPECTED_DEVELOPMENT_MAE[HORIZON]
        if not np.isclose(mae, expected, rtol=0.0, atol=1e-9):
            raise RuntimeError(
                f"T-7 incumbent benchmark mismatch {season}: actual={mae} expected={expected}"
            )
    elif season in EXPECTED_HOLDOUT_MAE[HORIZON]:
        expected = EXPECTED_HOLDOUT_MAE[HORIZON][season]
        atol = EXPECTED_HOLDOUT_ATOL[HORIZON]
        if not np.isclose(mae, expected, rtol=0.0, atol=atol):
            raise RuntimeError(
                f"T-7 incumbent benchmark mismatch {season}: actual={mae} expected={expected}"
            )


def _verify_stage1_hist31(season: str, mae: float) -> None:
    expected = EXPECTED_STAGE1_HIST31_MAE.get(season)
    if expected is None:
        return
    if not np.isclose(mae, expected, rtol=0.0, atol=EXPECTED_STAGE1_HIST31_ATOL):
        raise RuntimeError(
            f"T-7 Stage-1 Hist31 reproduction mismatch {season}: "
            f"actual={mae} expected={expected}"
        )


def score_fold(
    store: pd.DataFrame,
    test_season: str,
    training_seasons: list[str],
    candidates: list[RobustCandidate],
) -> dict[str, Any]:
    spec = CURRENT_EARLY_RUNTIME_SPECS[HORIZON]
    test = eligible_rows(store, HORIZON, test_season, spec.baseline_column)
    if test.empty:
        raise RuntimeError(f"empty T-7 fold for {test_season}")

    incumbent_runtime = fit_structural_prior_runtime(store, HORIZON, training_seasons)
    incumbent_prediction = incumbent_runtime.predict(test)
    actual = test["target_attendance"].astype(float).to_numpy()
    incumbent_metrics = metrics(actual, incumbent_prediction)
    _verify_known_incumbent(test_season, float(incumbent_metrics["mae"]))

    hist31_runtime = fit_hist31(store, training_seasons)
    hist31_prediction = hist31_runtime.predict(test)
    hist31_metrics = metrics(actual, hist31_prediction)
    _verify_stage1_hist31(test_season, float(hist31_metrics["mae"]))
    capacity = test["capacity"].astype(float).to_numpy()

    scored: dict[str, Any] = {}
    for candidate in candidates:
        prediction = apply_robust_policy(
            incumbent_prediction,
            hist31_prediction,
            capacity,
            candidate,
        )
        scored[candidate.id] = {
            "candidate": asdict(candidate),
            "scorecard": comparison_scorecard(test, prediction, incumbent_prediction),
        }

    pure_hist31 = next(
        c for c in candidates if c.alpha == 1.0 and c.cap_fraction is None
    )
    return {
        "test_season": test_season,
        "training_seasons": list(training_seasons),
        "test_rows": int(len(test)),
        "incumbent_training_rows": int(incumbent_runtime.training_rows),
        "hist31_training_rows": int(hist31_runtime.training_rows),
        "numeric_feature_count": int(len(hist31_runtime.numeric_features)),
        "incumbent_model_spec_id": spec.model_spec_id,
        "hist31_config": HIST31_CONFIG,
        "incumbent_mae": float(incumbent_metrics["mae"]),
        "hist31_mae": float(hist31_metrics["mae"]),
        "pure_hist31_candidate_id": pure_hist31.id,
        "candidates": scored,
    }


def aggregate_development(
    folds: list[dict[str, Any]],
    candidates: list[RobustCandidate],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        improvements = []
        candidate_maes = []
        incumbent_maes = []
        p90_deltas = []
        worst_degradations = []
        med_deltas = []
        for fold in folds:
            score = fold["candidates"][candidate.id]["scorecard"]
            improvements.append(float(score["mae_improvement"]))
            candidate_maes.append(float(score["candidate"]["mae"]))
            incumbent_maes.append(float(score["incumbent"]["mae"]))
            p90_deltas.append(
                float(score["candidate"]["p90_ae"] - score["incumbent"]["p90_ae"])
            )
            med_deltas.append(
                float(score["candidate"]["median_ae"] - score["incumbent"]["median_ae"])
            )
            worst_degradations.append(float(score["worst_event_degradation"]))
        rows.append({
            "candidate": asdict(candidate),
            "mean_candidate_mae": float(np.mean(candidate_maes)),
            "mean_incumbent_mae": float(np.mean(incumbent_maes)),
            "mean_mae_improvement": float(np.mean(improvements)),
            "fold_mae_improvements": improvements,
            "all_folds_improve": bool(all(value > 0.0 for value in improvements)),
            "mean_p90_delta": float(np.mean(p90_deltas)),
            "mean_median_ae_delta": float(np.mean(med_deltas)),
            "max_worst_event_degradation": float(np.max(worst_degradations)),
        })
    return rows


def select_robust_candidate(
    development_rows: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    non_incumbent = [
        row for row in development_rows
        if row["candidate"]["id"] != "incumbent"
        and row["all_folds_improve"]
        and row["mean_mae_improvement"] > 0.0
    ]
    if not non_incumbent:
        incumbent = next(
            row for row in development_rows if row["candidate"]["id"] == "incumbent"
        )
        return "incumbent", {
            "reason": "NO_NON_INCUMBENT_IMPROVES_ALL_DEVELOPMENT_FOLDS",
            "best_mean_improvement": 0.0,
            "required_retained_improvement": 0.0,
            "eligible_candidate_ids": [],
            "selected_row": incumbent,
        }

    best_gain = max(float(row["mean_mae_improvement"]) for row in non_incumbent)
    required_gain = ROBUST_GAIN_RETENTION * best_gain
    robust_pool = [
        row for row in non_incumbent
        if float(row["mean_mae_improvement"]) + SELECTION_ATOL >= required_gain
    ]

    def selection_key(row: dict[str, Any]) -> tuple[float, float, float, float, str]:
        candidate = row["candidate"]
        cap = candidate["cap_fraction"]
        cap_sort = 1.0 if cap is None else float(cap)
        return (
            float(row["max_worst_event_degradation"]),
            float(row["mean_p90_delta"]),
            float(candidate["alpha"]),
            cap_sort,
            str(candidate["id"]),
        )

    selected = min(robust_pool, key=selection_key)
    return str(selected["candidate"]["id"]), {
        "reason": "PRESERVE_80_PERCENT_OF_BEST_DEV_MAE_GAIN_THEN_MINIMIZE_TAIL",
        "best_mean_improvement": float(best_gain),
        "required_retained_improvement": float(required_gain),
        "eligible_candidate_ids": [str(row["candidate"]["id"]) for row in robust_pool],
        "selected_row": selected,
    }


def summarize_selected_holdouts(
    folds: list[dict[str, Any]],
    selected_id: str,
    pure_hist31_id: str,
) -> list[dict[str, Any]]:
    result = []
    for fold in folds:
        selected = fold["candidates"][selected_id]["scorecard"]
        pure = fold["candidates"][pure_hist31_id]["scorecard"]
        result.append({
            "season": fold["test_season"],
            "incumbent_mae": float(selected["incumbent"]["mae"]),
            "selected_mae": float(selected["candidate"]["mae"]),
            "selected_mae_improvement": float(selected["mae_improvement"]),
            "selected_median_ae": float(selected["candidate"]["median_ae"]),
            "incumbent_median_ae": float(selected["incumbent"]["median_ae"]),
            "selected_p90_ae": float(selected["candidate"]["p90_ae"]),
            "incumbent_p90_ae": float(selected["incumbent"]["p90_ae"]),
            "selected_bias": float(selected["candidate"]["bias"]),
            "incumbent_bias": float(selected["incumbent"]["bias"]),
            "selected_worst_event_degradation": float(selected["worst_event_degradation"]),
            "selected_worst_event": selected["worst_event"],
            "selected_event_improvement_rate": float(selected["event_improvement_rate"]),
            "pure_hist31_mae": float(pure["candidate"]["mae"]),
            "pure_hist31_mae_improvement": float(pure["mae_improvement"]),
            "pure_hist31_worst_event_degradation": float(pure["worst_event_degradation"]),
            "pure_hist31_worst_event": pure["worst_event"],
        })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    expected_input_hash = manifest["historical_runtime"]["sha256"]
    actual_input_hash = sha256_file(args.historical_runtime)
    if actual_input_hash != expected_input_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_input_hash} expected={expected_input_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    candidates = robust_candidates()

    development_folds = [
        score_fold(store, season, train, candidates)
        for season, train in DEVELOPMENT_FOLDS
    ]
    development_rows = aggregate_development(development_folds, candidates)
    selected_id, selection = select_robust_candidate(development_rows)

    selected_candidate = next(c for c in candidates if c.id == selected_id)
    pure_hist31 = next(c for c in candidates if c.alpha == 1.0 and c.cap_fraction is None)
    incumbent_candidate = next(c for c in candidates if c.id == "incumbent")

    if selected_id not in {"incumbent", pure_hist31.id}:
        reference_candidates = [incumbent_candidate, pure_hist31, selected_candidate]
    else:
        reference_candidates = [incumbent_candidate, pure_hist31]

    reference_folds = [
        score_fold(store, season, train, reference_candidates)
        for season, train in REFERENCE_HOLDOUTS
    ]

    holdout_summary = summarize_selected_holdouts(
        reference_folds,
        selected_id,
        pure_hist31.id,
    )

    selected_mean_improvement = float(
        np.mean([row["selected_mae_improvement"] for row in holdout_summary])
    )
    pure_mean_improvement = float(
        np.mean([row["pure_hist31_mae_improvement"] for row in holdout_summary])
    )
    selected_max_tail = float(
        np.max([row["selected_worst_event_degradation"] for row in holdout_summary])
    )
    pure_max_tail = float(
        np.max([row["pure_hist31_worst_event_degradation"] for row in holdout_summary])
    )

    if selected_id == "incumbent":
        signal = "INCUMBENT_RETAINED_ON_DEVELOPMENT"
    elif selected_mean_improvement > 0 and all(
        row["selected_mae_improvement"] > 0 for row in holdout_summary
    ) and selected_max_tail < pure_max_tail:
        signal = "ROBUST_BLEND_IMPROVES_BOTH_REFERENCES_AND_REDUCES_TAIL"
    elif selected_mean_improvement > 0 and selected_max_tail < pure_max_tail:
        signal = "POSITIVE_MEAN_AND_REDUCED_TAIL_BUT_MIXED_REFERENCE_SEASONS"
    else:
        signal = "ROBUSTNESS_POLICY_NOT_PROVEN"

    result = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_HISTORICAL_ROBUSTNESS_EVIDENCE",
        "evidence_class": "EXPOSED_HISTORICAL_REFERENCE_SEASONS",
        "promotion_allowed": False,
        "production_change": False,
        "horizon": HORIZON,
        "stage1_source": {
            "result_document": "ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md",
            "selected_challenger": "model-hist_absolute_31",
            "hist31_config": HIST31_CONFIG,
            "expected_hist31_mae": EXPECTED_STAGE1_HIST31_MAE,
            "reproduction_atol": EXPECTED_STAGE1_HIST31_ATOL,
        },
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_input_hash,
            "manifest_path": str(args.manifest),
            "artifact_version": manifest.get("artifact_version"),
            "feature_contract": manifest.get("feature_contract"),
            "historical_dataset_versions": manifest.get("historical_dataset_versions"),
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
        "candidate_contract": {
            "alphas": list(ALPHAS),
            "cap_fractions": list(CAP_FRACTIONS),
            "candidate_count_including_incumbent": len(candidates),
            "formula": "incumbent + clip(alpha * (hist31 - incumbent), +/- cap_fraction * capacity)",
            "uncapped_formula": "incumbent + alpha * (hist31 - incumbent)",
        },
        "selection_contract": {
            "development_folds": [
                {"test_season": season, "training_seasons": train}
                for season, train in DEVELOPMENT_FOLDS
            ],
            "reference_holdouts": [
                {"test_season": season, "training_seasons": train}
                for season, train in REFERENCE_HOLDOUTS
            ],
            "all_development_folds_must_improve_mae": True,
            "robust_gain_retention": ROBUST_GAIN_RETENTION,
            "selection_rule": (
                "among candidates improving every development fold, retain those with >=80% "
                "of the best mean development MAE gain; select minimum max worst-event "
                "degradation, then minimum mean p90 delta, then lower alpha, then tighter cap"
            ),
            "holdouts_used_for_selection": False,
        },
        "development_folds": development_folds,
        "development_aggregate": development_rows,
        "selection": selection,
        "selected_candidate_id": selected_id,
        "selected_candidate": asdict(selected_candidate),
        "pure_hist31_candidate_id": pure_hist31.id,
        "reference_folds": reference_folds,
        "reference_summary": holdout_summary,
        "mean_reference_mae_improvement_selected": selected_mean_improvement,
        "mean_reference_mae_improvement_pure_hist31": pure_mean_improvement,
        "max_reference_worst_event_degradation_selected": selected_max_tail,
        "max_reference_worst_event_degradation_pure_hist31": pure_max_tail,
        "signal": signal,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "selected_candidate_id": selected_id,
        "selected_candidate": asdict(selected_candidate),
        "selection_reason": selection["reason"],
        "signal": signal,
        "mean_reference_mae_improvement_selected": selected_mean_improvement,
        "mean_reference_mae_improvement_pure_hist31": pure_mean_improvement,
        "max_reference_worst_event_degradation_selected": selected_max_tail,
        "max_reference_worst_event_degradation_pure_hist31": pure_max_tail,
        "promotion_allowed": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
