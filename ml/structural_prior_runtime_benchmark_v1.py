#!/usr/bin/env python3
"""Reproduce the frozen T-30/T-14 Structural Prior runtime on season holdouts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml.demand_engine.structural_prior_runtime import (
    CURRENT_EARLY_RUNTIME_SPECS,
    fit_structural_prior_runtime,
)

DEV_TRAIN = ["2021/2022", "2022/2023"]
DEV = "2023/2024"
HOLDOUTS = [
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]


def metrics(actual, prediction) -> dict:
    actual = np.asarray(actual, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    ae = np.abs(prediction - actual)
    return {
        "n": int(len(actual)),
        "mae": float(np.mean(ae)),
        "median_ae": float(np.median(ae)),
        "wape": float(np.sum(ae) / np.sum(actual)),
        "bias": float(np.mean(prediction - actual)),
    }


def eligible(frame: pd.DataFrame, horizon: str, seasons: list[str]) -> pd.DataFrame:
    return frame[
        (frame["horizon"].astype(str) == horizon)
        & frame["training_eligible"].astype(bool)
        & frame["season"].isin(seasons)
    ].copy()


def evaluate(frame: pd.DataFrame) -> dict:
    report = {
        "benchmark_version": "structural-prior-runtime-v1",
        "protocol": {
            "development_train": DEV_TRAIN,
            "development_selection": DEV,
            "holdouts": [season for season, _ in HOLDOUTS],
            "target": "verified-capacity occupancy residual",
            "prediction_clip": "[0, verified_capacity]",
            "automatic_promotion": False,
        },
        "horizons": {},
    }
    for horizon in ["T-30", "T-14"]:
        spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
        development_model = fit_structural_prior_runtime(frame, horizon, DEV_TRAIN)
        development = eligible(frame, horizon, [DEV])
        development = development[development[spec.baseline_column].notna()].copy()
        dev_prediction = development_model.predict(development)
        horizon_report = {
            "model_spec_id": spec.model_spec_id,
            "feature_contract": spec.feature_contract,
            "baseline": spec.baseline_column,
            "feature_mode": spec.feature_mode,
            "estimator": spec.estimator_name,
            "development": metrics(development["target_attendance"], dev_prediction),
            "holdouts": {},
        }
        for test_season, train_seasons in HOLDOUTS:
            model = fit_structural_prior_runtime(frame, horizon, train_seasons)
            test = eligible(frame, horizon, [test_season])
            test = test[test[spec.baseline_column].notna()].copy()
            prediction = model.predict(test)
            horizon_report["holdouts"][test_season] = {
                "training_seasons": train_seasons,
                "training_rows": model.training_rows,
                "baseline": metrics(test["target_attendance"], test[spec.baseline_column]),
                "model": metrics(test["target_attendance"], prediction),
            }
        report["horizons"][horizon] = horizon_report
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-store", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    frame = pd.read_csv(args.feature_store)
    report = evaluate(frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
