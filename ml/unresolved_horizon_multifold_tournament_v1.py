#!/usr/bin/env python3
"""a2 unresolved-horizon multi-fold tournament v1.

Purpose:
- revisit T-30 / T-14 / T-3 / T-1 with a stronger selection protocol;
- require stability across 2022/23 and 2023/24 development-era rolling folds;
- freeze the development-selected candidate before exposed 2024/25 and 2025/26 scoring;
- preserve exact incumbent benchmark assertions;
- emit full MAE/tail/club evidence;
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

from ml.demand_engine.structural_prior_runtime import (
    CAT,
    CURRENT_EARLY_RUNTIME_SPECS,
    _preprocessor,
    feature_columns,
    fit_structural_prior_runtime,
)
from ml.pre_live_baseline_optimization_v1 import (
    Candidate,
    candidate_set,
    comparison_scorecard,
    eligible_rows,
    fit_candidate,
    load_feature_store,
    metrics,
    sha256_file,
    verify_incumbent,
)

EXPERIMENT = "unresolved-horizon-multifold-tournament-v1"
WORKSTREAM = "a2 — Historical / Structural Prior optimization"
HORIZONS = ["T-30", "T-14", "T-3", "T-1"]
RANDOM_SEED = 42

DEVELOPMENT_FOLDS = [
    ("2022/2023", ["2021/2022"]),
    ("2023/2024", ["2021/2022", "2022/2023"]),
]
REFERENCE_HOLDOUTS = [
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]

MIN_MEAN_RELATIVE_MAE_IMPROVEMENT = 0.01
NEAR_BEST_GAIN_RETENTION = 0.95
SELECTION_ATOL = 1e-12
TRANSFER_CANDIDATE_ID = "model-hist-absolute-leaf20"

TRANSFER_HGB_CONFIG = {
    "loss": "absolute_error",
    "learning_rate": 0.04,
    "max_iter": 300,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
    "random_state": RANDOM_SEED,
}


@dataclass(frozen=True)
class TournamentCandidate:
    id: str
    source: str
    base_candidate: Candidate | None = None


@dataclass
class FittedTransferHGB:
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


def tournament_candidates(
    store: pd.DataFrame,
    horizon: str,
) -> tuple[list[TournamentCandidate], dict[str, list[str]], list[str]]:
    base_candidates, groups, protected = candidate_set(store, horizon)
    result = [
        TournamentCandidate(id=c.id, source="stage1", base_candidate=c)
        for c in base_candidates
    ]
    result.append(TournamentCandidate(id=TRANSFER_CANDIDATE_ID, source="t7_transfer"))
    if len({candidate.id for candidate in result}) != len(result):
        raise RuntimeError(f"duplicate candidate id in {horizon}")
    return result, groups, protected


def fit_transfer_hgb(
    store: pd.DataFrame,
    horizon: str,
    training_seasons: list[str],
) -> FittedTransferHGB:
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = store[
        (store["horizon"].astype(str) == horizon)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(training_seasons)
        & store[spec.baseline_column].notna()
    ].copy()
    if rows.empty:
        raise RuntimeError(f"no eligible training rows for {horizon}/{training_seasons}")

    numeric = feature_columns(store, spec.feature_mode)
    preprocessor = _preprocessor(numeric)
    matrix = preprocessor.fit_transform(rows[CAT + numeric])
    capacity = rows["capacity"].astype(float).to_numpy()
    target = (
        rows["target_attendance"].astype(float).to_numpy() / capacity
        - rows[spec.baseline_column].astype(float).to_numpy() / capacity
    )
    model = HistGradientBoostingRegressor(**TRANSFER_HGB_CONFIG)
    model.fit(matrix, target, sample_weight=np.ones(len(rows), dtype=float))
    return FittedTransferHGB(
        preprocessor=preprocessor,
        estimator=model,
        numeric_features=numeric,
        baseline_column=spec.baseline_column,
        training_rows=int(len(rows)),
        training_seasons=list(training_seasons),
    )


def score_fold(
    store: pd.DataFrame,
    horizon: str,
    test_season: str,
    training_seasons: list[str],
    candidates: list[TournamentCandidate],
    groups: dict[str, list[str]],
    split_kind: str,
) -> dict[str, Any]:
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    test = eligible_rows(store, horizon, test_season, spec.baseline_column)
    if test.empty:
        raise RuntimeError(f"empty test rows for {horizon}/{test_season}")

    incumbent_runtime = fit_structural_prior_runtime(store, horizon, training_seasons)
    incumbent_prediction = incumbent_runtime.predict(test)
    actual = test["target_attendance"].astype(float).to_numpy()
    incumbent_metrics = metrics(actual, incumbent_prediction)
    verify_incumbent(horizon, test_season, float(incumbent_metrics["mae"]), split_kind)

    scored: dict[str, Any] = {}
    transfer_fit: FittedTransferHGB | None = None
    for candidate in candidates:
        if candidate.id == "incumbent":
            prediction = incumbent_prediction
            training_rows = int(incumbent_runtime.training_rows)
            numeric_feature_count = int(len(incumbent_runtime.numeric_features))
            detail = {"source": candidate.source}
        elif candidate.id == TRANSFER_CANDIDATE_ID:
            if transfer_fit is None:
                transfer_fit = fit_transfer_hgb(store, horizon, training_seasons)
            prediction = transfer_fit.predict(test)
            training_rows = int(transfer_fit.training_rows)
            numeric_feature_count = int(len(transfer_fit.numeric_features))
            detail = {
                "source": candidate.source,
                "estimator": "HistGradientBoostingRegressor",
                "config": TRANSFER_HGB_CONFIG,
            }
        else:
            if candidate.base_candidate is None:
                raise RuntimeError(f"missing base candidate for {candidate.id}")
            fitted = fit_candidate(
                store,
                horizon,
                training_seasons,
                candidate.base_candidate,
                groups,
            )
            prediction = fitted.predict(test)
            training_rows = int(fitted.training_rows)
            numeric_feature_count = int(len(fitted.numeric_features))
            detail = {
                "source": candidate.source,
                "base_candidate": asdict(candidate.base_candidate),
                "sample_weight_by_season": fitted.sample_weight_by_season,
            }

        scored[candidate.id] = {
            "candidate_id": candidate.id,
            "detail": detail,
            "training_rows": training_rows,
            "numeric_feature_count": numeric_feature_count,
            "scorecard": comparison_scorecard(test, prediction, incumbent_prediction),
        }

    return {
        "horizon": horizon,
        "split_kind": split_kind,
        "test_season": test_season,
        "training_seasons": list(training_seasons),
        "test_rows": int(len(test)),
        "incumbent_model_spec_id": spec.model_spec_id,
        "incumbent_baseline_column": spec.baseline_column,
        "incumbent_feature_mode": spec.feature_mode,
        "incumbent_mae": float(incumbent_metrics["mae"]),
        "candidates": scored,
    }


def aggregate_development(
    folds: list[dict[str, Any]],
    candidates: list[TournamentCandidate],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for candidate in candidates:
        fold_rows = []
        for fold in folds:
            score = fold["candidates"][candidate.id]["scorecard"]
            incumbent_mae = float(score["incumbent"]["mae"])
            candidate_mae = float(score["candidate"]["mae"])
            improvement = float(score["mae_improvement"])
            fold_rows.append({
                "season": fold["test_season"],
                "incumbent_mae": incumbent_mae,
                "candidate_mae": candidate_mae,
                "mae_improvement": improvement,
                "relative_mae_improvement": improvement / incumbent_mae,
                "median_ae_delta": float(
                    score["candidate"]["median_ae"] - score["incumbent"]["median_ae"]
                ),
                "p90_ae_delta": float(
                    score["candidate"]["p90_ae"] - score["incumbent"]["p90_ae"]
                ),
                "bias_abs_delta": float(
                    abs(float(score["candidate"]["bias"]))
                    - abs(float(score["incumbent"]["bias"]))
                ),
                "worst_event_degradation": float(score["worst_event_degradation"]),
                "event_improvement_rate": float(score["event_improvement_rate"]),
            })

        mean_incumbent_mae = float(np.mean([row["incumbent_mae"] for row in fold_rows]))
        mean_candidate_mae = float(np.mean([row["candidate_mae"] for row in fold_rows]))
        mean_improvement = mean_incumbent_mae - mean_candidate_mae
        result.append({
            "candidate_id": candidate.id,
            "source": candidate.source,
            "folds": fold_rows,
            "all_folds_improve_mae": bool(all(row["mae_improvement"] > 0 for row in fold_rows)),
            "mean_incumbent_mae": mean_incumbent_mae,
            "mean_candidate_mae": mean_candidate_mae,
            "mean_mae_improvement": float(mean_improvement),
            "mean_relative_mae_improvement": float(mean_improvement / mean_incumbent_mae),
            "mean_median_ae_delta": float(np.mean([row["median_ae_delta"] for row in fold_rows])),
            "mean_p90_ae_delta": float(np.mean([row["p90_ae_delta"] for row in fold_rows])),
            "mean_bias_abs_delta": float(np.mean([row["bias_abs_delta"] for row in fold_rows])),
            "max_worst_event_degradation": float(
                np.max([row["worst_event_degradation"] for row in fold_rows])
            ),
            "mean_event_improvement_rate": float(
                np.mean([row["event_improvement_rate"] for row in fold_rows])
            ),
        })
    return result


def select_candidate(
    development: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    incumbent = next(row for row in development if row["candidate_id"] == "incumbent")
    eligible = [
        row
        for row in development
        if row["candidate_id"] != "incumbent"
        and row["all_folds_improve_mae"]
        and row["mean_relative_mae_improvement"] + SELECTION_ATOL
        >= MIN_MEAN_RELATIVE_MAE_IMPROVEMENT
    ]
    if not eligible:
        return "incumbent", {
            "reason": "NO_CANDIDATE_MEETS_MULTIFOLD_STABILITY_GATE",
            "eligible_candidate_ids": [],
            "selected_row": incumbent,
        }

    best_gain = max(float(row["mean_mae_improvement"]) for row in eligible)
    near_best = [
        row
        for row in eligible
        if float(row["mean_mae_improvement"]) + SELECTION_ATOL
        >= NEAR_BEST_GAIN_RETENTION * best_gain
    ]

    selected = min(
        near_best,
        key=lambda row: (
            float(row["max_worst_event_degradation"]),
            float(row["mean_p90_ae_delta"]),
            float(row["mean_bias_abs_delta"]),
            str(row["candidate_id"]),
        ),
    )
    return str(selected["candidate_id"]), {
        "reason": "MULTIFOLD_1PCT_GATE_THEN_95PCT_GAIN_RETENTION_AND_TAIL_MINIMIZATION",
        "best_mean_mae_improvement": float(best_gain),
        "near_best_required_improvement": float(NEAR_BEST_GAIN_RETENTION * best_gain),
        "eligible_candidate_ids": [str(row["candidate_id"]) for row in eligible],
        "near_best_candidate_ids": [str(row["candidate_id"]) for row in near_best],
        "selected_row": selected,
    }


def reference_summary(
    folds: list[dict[str, Any]],
    selected_id: str,
) -> list[dict[str, Any]]:
    result = []
    for fold in folds:
        score = fold["candidates"][selected_id]["scorecard"]
        result.append({
            "season": fold["test_season"],
            "incumbent_mae": float(score["incumbent"]["mae"]),
            "selected_mae": float(score["candidate"]["mae"]),
            "mae_improvement": float(score["mae_improvement"]),
            "median_ae_delta": float(
                score["candidate"]["median_ae"] - score["incumbent"]["median_ae"]
            ),
            "p90_ae_delta": float(
                score["candidate"]["p90_ae"] - score["incumbent"]["p90_ae"]
            ),
            "bias_abs_delta": float(
                abs(float(score["candidate"]["bias"]))
                - abs(float(score["incumbent"]["bias"]))
            ),
            "worst_event_degradation": float(score["worst_event_degradation"]),
            "worst_event": score["worst_event"],
            "event_improvement_rate": float(score["event_improvement_rate"]),
            "club_breakdown_min_n_5": score["club_breakdown_min_n_5"],
        })
    return result


def horizon_experiment(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    candidates, groups, protected = tournament_candidates(store, horizon)

    development_folds = [
        score_fold(
            store,
            horizon,
            test_season,
            training_seasons,
            candidates,
            groups,
            "development",
        )
        for test_season, training_seasons in DEVELOPMENT_FOLDS
    ]
    development = aggregate_development(development_folds, candidates)
    selected_id, selection = select_candidate(development)
    selected = next(candidate for candidate in candidates if candidate.id == selected_id)
    incumbent = next(candidate for candidate in candidates if candidate.id == "incumbent")

    reference_candidates = [incumbent] if selected_id == "incumbent" else [incumbent, selected]
    reference_folds = [
        score_fold(
            store,
            horizon,
            test_season,
            training_seasons,
            reference_candidates,
            groups,
            "holdout",
        )
        for test_season, training_seasons in REFERENCE_HOLDOUTS
    ]
    references = reference_summary(reference_folds, selected_id)

    mean_incumbent = float(np.mean([row["incumbent_mae"] for row in references]))
    mean_selected = float(np.mean([row["selected_mae"] for row in references]))
    mean_improvement = mean_incumbent - mean_selected
    both_reference_positive = bool(all(row["mae_improvement"] > 0 for row in references))

    if selected_id == "incumbent":
        signal = "NO_STABLE_DEVELOPMENT_CHALLENGER"
    elif both_reference_positive and mean_improvement > 0:
        signal = "STABLE_DEV_CHALLENGER_POSITIVE_BOTH_REFERENCES"
    elif mean_improvement > 0:
        signal = "STABLE_DEV_CHALLENGER_POSITIVE_MEAN_MIXED_REFERENCES"
    else:
        signal = "STABLE_DEV_CHALLENGER_NOT_PROVEN_ON_REFERENCES"

    return {
        "horizon": horizon,
        "candidate_count": len(candidates),
        "protected_direct_baseline_feature": protected,
        "feature_groups_resolved": groups,
        "development_folds": development_folds,
        "development_aggregate": development,
        "selection": selection,
        "selected_candidate_id": selected_id,
        "selected_candidate_source": selected.source,
        "reference_folds": reference_folds,
        "reference_summary": references,
        "mean_reference_incumbent_mae": mean_incumbent,
        "mean_reference_selected_mae": mean_selected,
        "mean_reference_mae_improvement": float(mean_improvement),
        "both_reference_seasons_improve": both_reference_positive,
        "signal": signal,
        "promotion_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--horizons", default=",".join(HORIZONS))
    args = parser.parse_args()

    requested = [item.strip() for item in args.horizons.split(",") if item.strip()]
    invalid = sorted(set(requested) - set(HORIZONS))
    if invalid:
        raise ValueError(f"unsupported horizons: {invalid}")

    manifest = json.loads(args.manifest.read_text())
    expected_hash = manifest["historical_runtime"]["sha256"]
    actual_hash = sha256_file(args.historical_runtime)
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    horizon_results = [horizon_experiment(store, horizon) for horizon in requested]

    result = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_HISTORICAL_MULTIFOLD_CHALLENGER_EVIDENCE",
        "evidence_class": "EXPOSED_HISTORICAL_REFERENCE_SEASONS",
        "promotion_allowed": False,
        "production_change": False,
        "protocol": {
            "development_folds": [
                {"test_season": season, "training_seasons": train}
                for season, train in DEVELOPMENT_FOLDS
            ],
            "reference_holdouts": [
                {"test_season": season, "training_seasons": train}
                for season, train in REFERENCE_HOLDOUTS
            ],
            "minimum_mean_relative_mae_improvement": MIN_MEAN_RELATIVE_MAE_IMPROVEMENT,
            "near_best_gain_retention": NEAR_BEST_GAIN_RETENTION,
            "selection": (
                "candidate must improve both development folds and >=1% mean MAE; "
                "among candidates within 95% of best mean gain choose minimum max tail, "
                "then p90 delta, absolute-bias delta, deterministic id"
            ),
            "reference_holdouts_used_for_selection": False,
            "event_is_independent_unit": True,
            "random_snapshot_split": False,
            "future_leakage_allowed": False,
        },
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_hash,
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
        "transfer_candidate": {
            "id": TRANSFER_CANDIDATE_ID,
            "origin": "T-7 frozen historical candidate family",
            "config": TRANSFER_HGB_CONFIG,
        },
        "horizons": horizon_results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "promotion_allowed": False,
        "horizons": [
            {
                "horizon": item["horizon"],
                "selected_candidate_id": item["selected_candidate_id"],
                "signal": item["signal"],
                "mean_reference_incumbent_mae": item["mean_reference_incumbent_mae"],
                "mean_reference_selected_mae": item["mean_reference_selected_mae"],
                "mean_reference_mae_improvement": item["mean_reference_mae_improvement"],
            }
            for item in horizon_results
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
