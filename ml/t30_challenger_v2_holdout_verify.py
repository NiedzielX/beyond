#!/usr/bin/env python3
"""One-time untouched-holdout verification for frozen T-30 Challenger v2.

The candidate specification was frozen first in commit:
2d02f247e151dc191d4af8790b87288fd5aaa68c

This script performs no model search and exposes no tunable CLI parameters.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

from ml.demand_engine.structural_prior_runtime import CAT, feature_columns, fit_structural_prior_runtime
from ml.features.structural_prior_feature_store_v1 import build_feature_store, WARSAW_TZ

HORIZON = "T-30"
BASELINE = "baseline_season"
FROZEN_SPEC_COMMIT = "2d02f247e151dc191d4af8790b87288fd5aaa68c"
FROZEN_MODEL_ID = "structural-prior-t30-challenger-v2-extra-leaf1-full"
HOLDOUTS = [
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]


def canonical_matches(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    local = pd.to_datetime(
        pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
        + " "
        + frame["kickoff_time_local"].astype(str),
        format="mixed",
    )
    frame["kickoff_at"] = local.dt.tz_localize(
        WARSAW_TZ, ambiguous="raise", nonexistent="raise"
    ).dt.tz_convert("UTC")
    frame["completed_at"] = frame["kickoff_at"] + pd.Timedelta(hours=3)
    frame["training_eligible"] = frame["attendance"].astype(int) != 0
    frame["round"] = frame["round"].astype(int)
    return frame.sort_values(["kickoff_at", "home_club_key"]).reset_index(drop=True)


def preprocessor(numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
        ("num", SimpleImputer(strategy="median", add_indicator=True), numeric),
    ])


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


def fit_frozen_challenger(store: pd.DataFrame, train_seasons: list[str]):
    numeric = feature_columns(store, "full")
    train = store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(train_seasons)
        & store[BASELINE].notna()
    ].copy()
    prep = preprocessor(numeric)
    x_train = prep.fit_transform(train[CAT + numeric])
    y_train = (
        train["target_attendance"].astype(float).to_numpy() / train["capacity"].astype(float).to_numpy()
        - train[BASELINE].astype(float).to_numpy() / train["capacity"].astype(float).to_numpy()
    )
    model = ExtraTreesRegressor(
        n_estimators=700,
        min_samples_leaf=1,
        max_features=1.0,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, y_train)
    return prep, model, numeric, int(len(train))


def predict_challenger(prep, model, numeric, test: pd.DataFrame) -> np.ndarray:
    residual = model.predict(prep.transform(test[CAT + numeric]))
    pred = (
        test[BASELINE].astype(float).to_numpy()
        + residual * test["capacity"].astype(float).to_numpy()
    )
    return np.clip(pred, 0.0, test["capacity"].astype(float).to_numpy())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-runtime",
        type=Path,
        default=Path("ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz"),
    )
    parser.add_argument("--output", type=Path, default=Path("/tmp/t30-challenger-v2-holdout.json"))
    args = parser.parse_args()

    matches = canonical_matches(args.historical_runtime)
    store = build_feature_store(matches)

    report = {
        "experiment": "t30-challenger-v2-one-time-holdout-verification",
        "frozen_spec_commit": FROZEN_SPEC_COMMIT,
        "model_id": FROZEN_MODEL_ID,
        "automatic_promotion": False,
        "search_performed": False,
        "holdouts": {},
    }

    combined_actual = []
    combined_current = []
    combined_challenger = []

    for season, train_seasons in HOLDOUTS:
        test = store[
            (store["horizon"].astype(str) == HORIZON)
            & store["training_eligible"].astype(bool)
            & (store["season"] == season)
            & store[BASELINE].notna()
        ].copy()

        current = fit_structural_prior_runtime(store, HORIZON, train_seasons)
        current_prediction = current.predict(test)

        prep, challenger, numeric, train_rows = fit_frozen_challenger(store, train_seasons)
        challenger_prediction = predict_challenger(prep, challenger, numeric, test)

        actual = test["target_attendance"].astype(float).to_numpy()
        current_metrics = metrics(actual, current_prediction)
        challenger_metrics = metrics(actual, challenger_prediction)
        baseline_metrics = metrics(actual, test[BASELINE].astype(float).to_numpy())

        report["holdouts"][season] = {
            "training_seasons": train_seasons,
            "training_rows": train_rows,
            "baseline": baseline_metrics,
            "current_runtime": current_metrics,
            "challenger": challenger_metrics,
            "challenger_delta_mae_vs_current": challenger_metrics["mae"] - current_metrics["mae"],
            "challenger_relative_improvement_vs_current": (
                current_metrics["mae"] - challenger_metrics["mae"]
            ) / current_metrics["mae"],
        }

        combined_actual.extend(actual.tolist())
        combined_current.extend(np.asarray(current_prediction).tolist())
        combined_challenger.extend(np.asarray(challenger_prediction).tolist())

    combined_current_metrics = metrics(combined_actual, combined_current)
    combined_challenger_metrics = metrics(combined_actual, combined_challenger)
    report["combined"] = {
        "current_runtime": combined_current_metrics,
        "challenger": combined_challenger_metrics,
        "challenger_delta_mae_vs_current": (
            combined_challenger_metrics["mae"] - combined_current_metrics["mae"]
        ),
        "challenger_relative_improvement_vs_current": (
            combined_current_metrics["mae"] - combined_challenger_metrics["mae"]
        ) / combined_current_metrics["mae"],
    }

    per_season_improves = all(
        item["challenger"]["mae"] < item["current_runtime"]["mae"]
        for item in report["holdouts"].values()
    )
    report["decision"] = {
        "improves_both_holdouts": per_season_improves,
        "improves_combined_mae": (
            combined_challenger_metrics["mae"] < combined_current_metrics["mae"]
        ),
        "strategic_t30_under_1700_combined": combined_challenger_metrics["mae"] < 1700.0,
        "promotion": "REVIEW_ONLY_NO_AUTO_PROMOTION",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
