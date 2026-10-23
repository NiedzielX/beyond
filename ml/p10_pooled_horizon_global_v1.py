#!/usr/bin/env python3
"""P10 pooled-horizon global challenger v1.

Controlled question:
    Does pooling T-30/T-14/T-7/T-3/T-1 rows reduce match-balanced OOS MAE
    versus the same fixed residual model trained separately per horizon?

All rows of one match remain in the same temporal fold. The experiment uses a
small fixed candidate family and does not relabel historical folds as unseen.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.mae_delta_uncertainty_v1 import BootstrapConfig, bootstrap_delta_mae, paired_event_errors
from ml.research_advance_governance_v2 import ResearchAdvanceInput, decide_research_advance
from ml.temporal_validation_v1 import build_expanding_group_folds, event_balanced_mae, fold_manifest, forecast_metrics

VERSION = "p10-pooled-horizon-global-v1"
POOLED_ID = "pooled-hgb-absolute-error-v1"
LOCAL_ID = "local-horizon-hgb-absolute-error-v1"
CAT = ["home_club_key", "away_club_key"]
HORIZON_DAYS = {
    "T-30": 30.0, "T-30d": 30.0,
    "T-14": 14.0, "T-14d": 14.0,
    "T-7": 7.0, "T-7d": 7.0,
    "T-3": 3.0, "T-3d": 3.0,
    "T-1": 1.0, "T-1d": 1.0,
}
META = {
    "match_key", "season", "horizon", "as_of_at", "kickoff_at",
    "home_club_key", "away_club_key", "target_attendance",
    "training_eligible", "baseline_fixed", "target_eligible",
}


def clean_frame(raw: pd.DataFrame) -> pd.DataFrame:
    required = {
        "match_key", "season", "horizon", "kickoff_at", "home_club_key",
        "away_club_key", "target_attendance", "training_eligible", "baseline_fixed",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise RuntimeError(f"P10 feature store missing columns: {missing}")
    frame = raw.copy()
    frame["training_eligible"] = frame["training_eligible"].astype(str).str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    ).fillna(frame["training_eligible"].astype(bool))
    frame = frame[frame["training_eligible"]].copy()
    frame["target_attendance"] = pd.to_numeric(frame["target_attendance"], errors="raise")
    frame["baseline_fixed"] = pd.to_numeric(frame["baseline_fixed"], errors="raise")
    frame["kickoff_at"] = pd.to_datetime(frame["kickoff_at"], utc=True, errors="raise")
    normalized_horizon = frame["horizon"].astype(str)
    unknown = sorted(set(normalized_horizon) - set(HORIZON_DAYS))
    if unknown:
        raise RuntimeError(f"P10 unknown horizons: {unknown}")
    frame["horizon_days"] = normalized_horizon.map(HORIZON_DAYS).astype(float)
    duplicate = frame.duplicated(["match_key", "horizon"], keep=False)
    if duplicate.any():
        raise RuntimeError("P10 requires exactly one PIT row per match/horizon")
    per_match_kickoff = frame.groupby("match_key")["kickoff_at"].nunique()
    if (per_match_kickoff != 1).any():
        raise RuntimeError("P10 match rows disagree on kickoff_at")
    return frame.reset_index(drop=True)


def numeric_features(frame: pd.DataFrame) -> list[str]:
    features = [
        column for column in frame.columns
        if column not in META and pd.api.types.is_numeric_dtype(frame[column])
    ]
    # Explicitly guarantee horizon representation is present exactly once.
    if "horizon_days" not in features:
        features.append("horizon_days")
    return sorted(set(features))


def model(numeric: list[str]) -> Pipeline:
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
        ("num", SimpleImputer(strategy="median", add_indicator=True), numeric),
    ])
    return Pipeline([
        ("pre", pre),
        ("model", HistGradientBoostingRegressor(
            loss="absolute_error",
            learning_rate=0.05,
            max_iter=250,
            max_leaf_nodes=15,
            min_samples_leaf=10,
            l2_regularization=1.0,
            random_state=42,
        )),
    ])


def match_balanced_weights(frame: pd.DataFrame) -> np.ndarray:
    counts = frame.groupby("match_key")["match_key"].transform("size").astype(float)
    return (1.0 / counts).to_numpy(dtype=float)


def fit_residual(train: pd.DataFrame, numeric: list[str]) -> Pipeline:
    estimator = model(numeric)
    residual = train["target_attendance"].astype(float) - train["baseline_fixed"].astype(float)
    estimator.fit(
        train[CAT + numeric],
        residual,
        model__sample_weight=match_balanced_weights(train),
    )
    return estimator


def predict(estimator: Pipeline, frame: pd.DataFrame, numeric: list[str]) -> np.ndarray:
    residual = np.asarray(estimator.predict(frame[CAT + numeric]), dtype=float)
    return np.maximum(0.0, frame["baseline_fixed"].to_numpy(dtype=float) + residual)


def evaluate(
    raw: pd.DataFrame,
    *,
    minimum_meaningful_mae_improvement: float | None = None,
) -> tuple[dict[str, Any], pd.DataFrame, dict[str, Any]]:
    frame = clean_frame(raw)
    numeric = numeric_features(frame)
    folds = build_expanding_group_folds(
        frame,
        entity_col="match_key",
        time_col="kickoff_at",
        group_col="season",
        min_train_groups=2,
    )
    if not folds:
        raise RuntimeError("P10 requires at least one expanding-season fold")
    manifest = fold_manifest(folds, protocol_id="p10-match-blocked-expanding-season-v1")

    outputs: list[pd.DataFrame] = []
    fold_scores: list[dict[str, Any]] = []
    for fold in folds:
        train_ids = set(fold.train_entities)
        test_ids = set(fold.test_entities)
        train = frame[frame["match_key"].astype(str).isin(train_ids)].copy()
        test = frame[frame["match_key"].astype(str).isin(test_ids)].copy()
        if set(train["match_key"].astype(str)) & set(test["match_key"].astype(str)):
            raise RuntimeError("P10 match leakage across fold")

        pooled_model = fit_residual(train, numeric)
        pooled_pred = predict(pooled_model, test, numeric)

        local_pred = np.full(len(test), np.nan, dtype=float)
        for horizon in sorted(test["horizon"].astype(str).unique()):
            train_h = train[train["horizon"].astype(str) == horizon]
            test_mask = test["horizon"].astype(str) == horizon
            if train_h.empty:
                raise RuntimeError(f"P10 no local training rows for {horizon}")
            local_model = fit_residual(train_h, numeric)
            local_pred[np.flatnonzero(test_mask.to_numpy())] = predict(local_model, test[test_mask], numeric)
        if np.isnan(local_pred).any():
            raise RuntimeError("P10 local comparator produced missing predictions")

        out = test[["match_key", "season", "horizon", "kickoff_at", "home_club_key", "target_attendance"]].copy()
        out["local_prediction"] = local_pred
        out["pooled_prediction"] = pooled_pred
        out["fold_id"] = fold.fold_id
        outputs.append(out)

        local_mae = event_balanced_mae(out, event_col="match_key", actual_col="target_attendance", prediction_col="local_prediction")
        pooled_mae = event_balanced_mae(out, event_col="match_key", actual_col="target_attendance", prediction_col="pooled_prediction")
        fold_scores.append({
            "fold_id": fold.fold_id,
            "test_season": fold.test_groups[0],
            "test_match_count": len(test_ids),
            "local_match_balanced_mae": local_mae,
            "pooled_match_balanced_mae": pooled_mae,
            "delta_mae": pooled_mae - local_mae,
            "pooled_improved": pooled_mae < local_mae,
        })

    predictions = pd.concat(outputs, ignore_index=True).sort_values(["kickoff_at", "match_key", "horizon"]).reset_index(drop=True)
    local_mae = event_balanced_mae(predictions, event_col="match_key", actual_col="target_attendance", prediction_col="local_prediction")
    pooled_mae = event_balanced_mae(predictions, event_col="match_key", actual_col="target_attendance", prediction_col="pooled_prediction")

    paired = paired_event_errors(
        predictions,
        event_col="match_key",
        actual_col="target_attendance",
        incumbent_col="local_prediction",
        challenger_col="pooled_prediction",
        strata_cols=("fold_id",),
    )
    uncertainty = bootstrap_delta_mae(
        paired,
        strata_cols=("fold_id",),
        config=BootstrapConfig(n_resamples=5000, seed=42),
    )
    fold_improvement_rate = float(np.mean([row["pooled_improved"] for row in fold_scores]))
    governance = decide_research_advance(ResearchAdvanceInput(
        incumbent_mae=local_mae,
        challenger_mae=pooled_mae,
        event_improvement_rate=float(uncertainty["event_improvement_rate"]),
        fold_improvement_rate=fold_improvement_rate,
        delta_mae_ci_lower=float(uncertainty["bootstrap"]["delta_mae_lower"]),
        delta_mae_ci_upper=float(uncertainty["bootstrap"]["delta_mae_upper"]),
        minimum_meaningful_mae_improvement=minimum_meaningful_mae_improvement,
    ))

    per_horizon = {}
    for horizon, group in predictions.groupby("horizon", sort=True):
        per_horizon[str(horizon)] = {
            "rows": int(len(group)),
            "matches": int(group["match_key"].nunique()),
            "local": forecast_metrics(group["target_attendance"], group["local_prediction"]),
            "pooled": forecast_metrics(group["target_attendance"], group["pooled_prediction"]),
        }

    result = {
        "version": VERSION,
        "evidence_class": "historical_exposed_research",
        "production_change": False,
        "live_adjustment": 0,
        "question": "Does pooled cross-horizon learning beat the same fixed horizon-local residual model?",
        "independent_unit": "match_key",
        "match_blocking": True,
        "training_weight": "equal total weight per match",
        "candidate_id": POOLED_ID,
        "incumbent_id": LOCAL_ID,
        "eligible_rows": int(len(frame)),
        "matches": int(frame["match_key"].nunique()),
        "fold_count": len(folds),
        "fold_manifest_sha256": manifest["folds_sha256"],
        "local_match_balanced_mae": local_mae,
        "pooled_match_balanced_mae": pooled_mae,
        "delta_mae": pooled_mae - local_mae,
        "fold_improvement_rate": fold_improvement_rate,
        "fold_scores": fold_scores,
        "per_horizon": per_horizon,
        "uncertainty": uncertainty,
        "governance_v2": governance.to_dict(),
    }
    return result, predictions, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-store", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--fold-manifest", type=Path, required=True)
    parser.add_argument("--minimum-meaningful-mae-improvement", type=float)
    args = parser.parse_args()

    raw = pd.read_csv(args.feature_store)
    result, predictions, manifest = evaluate(
        raw,
        minimum_meaningful_mae_improvement=args.minimum_meaningful_mae_improvement,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(args.predictions_csv, index=False)
    args.fold_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.fold_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
