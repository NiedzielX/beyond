#!/usr/bin/env python3
"""Beyond Demand Engine v1 residual-correction benchmark.

Input is a CSV exported from get_demand_engine_v1_residual_training_set().
Rows are snapshot-level observations, but validation is ALWAYS grouped by match
(`group_ticket_event_id`) so snapshots from one match cannot leak across folds.

This script is an evaluation harness only. It never promotes or persists a model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [
    "hours_to_kickoff",
    "days_to_match",
    "historical_p50",
    "live_available_total",
    "live_first_available_total",
    "live_available_index",
    "live_net_removed_since_first",
    "live_net_removed_since_previous",
    "live_velocity_since_previous",
    "live_net_removed_6h",
    "live_velocity_6h",
    "live_net_removed_24h",
    "live_velocity_24h",
    "live_acceleration_6h_vs_24h",
    "live_raw_snapshot_count",
    "sector_coverage_change_flag",
    "release_activity_flag",
    "entered_sector_count",
    "left_sector_count",
    "coverage_inventory_effect",
]


def metric_set(actual: np.ndarray, prediction: np.ndarray) -> dict:
    error = prediction - actual
    absolute = np.abs(error)
    ape = absolute / np.where(actual == 0, np.nan, actual) * 100.0
    return {
        "n": int(len(actual)),
        "mae": round(float(np.nanmean(absolute)), 2),
        "mape_pct": round(float(np.nanmean(ape)), 2),
        "wape_pct": round(float(np.nansum(absolute) / np.nansum(actual) * 100.0), 2),
        "bias": round(float(np.nanmean(error)), 2),
        "within_5_pct": round(float(np.nanmean(ape <= 5.0) * 100.0), 2),
        "within_10_pct": round(float(np.nanmean(ape <= 10.0) * 100.0), 2),
    }


def make_ridge() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=10.0)),
        ]
    )


def make_gb() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            (
                "model",
                GradientBoostingRegressor(
                    loss="huber",
                    n_estimators=120,
                    learning_rate=0.03,
                    max_depth=2,
                    min_samples_leaf=5,
                    random_state=42,
                ),
            ),
        ]
    )


def evaluate_model(frame: pd.DataFrame, model_factory) -> dict:
    groups = frame["group_ticket_event_id"].astype(str).to_numpy()
    unique_groups = np.unique(groups)
    n_splits = min(5, len(unique_groups))
    splitter = GroupKFold(n_splits=n_splits)

    X = frame[FEATURES].copy()
    for column in ["sector_coverage_change_flag", "release_activity_flag"]:
        X[column] = X[column].fillna(False).astype(int)
    y = frame["target_residual"].astype(float).to_numpy()
    actual = frame["actual_attendance"].astype(float).to_numpy()
    historical = frame["historical_p50"].astype(float).to_numpy()

    residual_pred = np.full(len(frame), np.nan, dtype=float)
    fold_reports = []

    for fold_no, (train_idx, test_idx) in enumerate(splitter.split(X, y, groups), start=1):
        model = model_factory()
        model.fit(X.iloc[train_idx], y[train_idx])
        residual_pred[test_idx] = model.predict(X.iloc[test_idx])

        fold_final = historical[test_idx] + residual_pred[test_idx]
        fold_reports.append(
            {
                "fold": fold_no,
                "test_matches": int(len(np.unique(groups[test_idx]))),
                "metrics": metric_set(actual[test_idx], fold_final),
            }
        )

    final_prediction = historical + residual_pred
    return {
        "metrics": metric_set(actual, final_prediction),
        "residual_mae": round(float(np.nanmean(np.abs(residual_pred - y))), 2),
        "folds": fold_reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--min-matches",
        type=int,
        default=20,
        help="Refuse candidate benchmarking below this many unique matches.",
    )
    args = parser.parse_args()

    frame = pd.read_csv(args.data)
    required = set(FEATURES + [
        "group_ticket_event_id",
        "historical_p50",
        "actual_attendance",
        "target_residual",
    ])
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"Residual dataset missing columns: {missing}")

    frame = frame.dropna(
        subset=["group_ticket_event_id", "historical_p50", "actual_attendance", "target_residual"]
    ).copy()
    unique_matches = int(frame["group_ticket_event_id"].nunique())

    baseline_actual = frame["actual_attendance"].astype(float).to_numpy()
    baseline_historical = frame["historical_p50"].astype(float).to_numpy()
    baseline = metric_set(baseline_actual, baseline_historical)

    report = {
        "benchmark_version": "residual-v1",
        "split_protocol": "GroupKFold by group_ticket_event_id",
        "rows": int(len(frame)),
        "unique_matches": unique_matches,
        "minimum_matches_required": args.min_matches,
        "baseline_no_live_correction": baseline,
        "candidates": {},
        "status": "insufficient_matches",
    }

    if unique_matches >= args.min_matches:
        report["candidates"] = {
            "ridge_residual_v1": evaluate_model(frame, make_ridge),
            "gradient_boosting_residual_v1": evaluate_model(frame, make_gb),
        }
        report["status"] = "benchmarked_not_promoted"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if unique_matches < args.min_matches:
        raise SystemExit(
            f"Not enough independent matches to benchmark residual models: "
            f"{unique_matches} < {args.min_matches}. Baseline report was saved."
        )


if __name__ == "__main__":
    main()
