#!/usr/bin/env python3
"""Fixed historical regression validation for frozen T-30 baseline smoothing v3.

Candidate frozen first in commit:
d37647ace1947eec2227be80c38b3c66db108aea

2024/25 and 2025/26 are treated as exposed fixed historical regression sets,
not pristine untouched holdouts. This script performs no candidate search.
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
from ml.features.structural_prior_feature_store_v1 import WARSAW_TZ, build_feature_store

HORIZON = "T-30"
FROZEN_SPEC_COMMIT = "d37647ace1947eec2227be80c38b3c66db108aea"
MODEL_ID = "structural-prior-t30-v3-prev-shrink-k2"
K = 2.0
REGRESSION_SETS = (
    ("2024/2025", ("2021/2022", "2022/2023", "2023/2024")),
    ("2025/2026", ("2021/2022", "2022/2023", "2023/2024", "2024/2025")),
)


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


def _finite(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan)


def frozen_baseline(frame: pd.DataFrame) -> np.ndarray:
    n = _finite(frame["season_home_n"]).fillna(0.0).clip(lower=0.0)
    current = _finite(frame["season_home_mean"])
    previous = _finite(frame["prev_season_home_mean"])
    long_mean = _finite(frame["home_attendance_mean"])
    fallback = _finite(frame["baseline_season"])

    anchor = previous.fillna(long_mean).fillna(fallback)
    current = current.fillna(anchor).fillna(fallback)
    anchor = anchor.fillna(current).fillna(fallback)
    smoothed = (n * current + K * anchor) / (n + K)
    smoothed = smoothed.where(n > 0, anchor).fillna(fallback)
    if smoothed.isna().any():
        raise RuntimeError("Frozen v3 baseline contains nulls")
    return smoothed.astype(float).to_numpy()


def preprocessor(numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
        ("num", SimpleImputer(strategy="median", add_indicator=True), numeric),
    ])


def fit_frozen(store: pd.DataFrame, train_seasons: tuple[str, ...]):
    train = store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(train_seasons)
        & store["baseline_season"].notna()
    ].copy()
    numeric = feature_columns(store, "full")
    prep = preprocessor(numeric)
    x_train = prep.fit_transform(train[CAT + numeric])
    baseline = frozen_baseline(train)
    capacity = train["capacity"].astype(float).to_numpy()
    target = train["target_attendance"].astype(float).to_numpy()
    residual = target / capacity - baseline / capacity
    model = ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=3,
        max_features=0.8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, residual)
    return prep, model, numeric, int(len(train))


def predict_frozen(frame: pd.DataFrame, prep, model, numeric: list[str]) -> np.ndarray:
    baseline = frozen_baseline(frame)
    capacity = frame["capacity"].astype(float).to_numpy()
    residual = np.asarray(model.predict(prep.transform(frame[CAT + numeric])), dtype=float)
    return np.clip(baseline + residual * capacity, 0.0, capacity)


def metrics(actual, prediction) -> dict:
    actual = np.asarray(actual, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    error = prediction - actual
    ae = np.abs(error)
    return {
        "n": int(len(actual)),
        "mae": float(np.mean(ae)),
        "median_ae": float(np.median(ae)),
        "wape": float(np.sum(ae) / np.sum(actual)),
        "bias": float(np.mean(error)),
    }


def club_metrics(frame: pd.DataFrame, current_pred: np.ndarray, candidate_pred: np.ndarray) -> dict:
    work = frame[["home_club_key", "target_attendance"]].copy().reset_index(drop=True)
    work["current"] = current_pred
    work["candidate"] = candidate_pred
    result = {}
    for club, group in work.groupby("home_club_key"):
        actual = group["target_attendance"].astype(float).to_numpy()
        current = metrics(actual, group["current"].to_numpy())
        candidate = metrics(actual, group["candidate"].to_numpy())
        result[str(club)] = {
            "n": int(len(group)),
            "current_mae": current["mae"],
            "candidate_mae": candidate["mae"],
            "delta_mae": candidate["mae"] - current["mae"],
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-runtime",
        type=Path,
        default=Path("ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz"),
    )
    parser.add_argument("--output", type=Path, default=Path("/tmp/t30-baseline-smoothing-v3-validation.json"))
    args = parser.parse_args()

    store = build_feature_store(canonical_matches(args.historical_runtime))
    report = {
        "experiment": "t30-baseline-smoothing-v3-fixed-regression-validation",
        "model_id": MODEL_ID,
        "frozen_spec_commit": FROZEN_SPEC_COMMIT,
        "search_performed": False,
        "validation_status": "EXPOSED_FIXED_HISTORICAL_REGRESSION_SET",
        "automatic_promotion": False,
        "seasons": {},
    }

    all_actual = []
    all_current = []
    all_candidate = []

    for season, train_seasons in REGRESSION_SETS:
        test = store[
            (store["horizon"].astype(str) == HORIZON)
            & store["training_eligible"].astype(bool)
            & (store["season"] == season)
            & store["baseline_season"].notna()
        ].copy()
        actual = test["target_attendance"].astype(float).to_numpy()

        current_runtime = fit_structural_prior_runtime(store, HORIZON, list(train_seasons))
        current_prediction = current_runtime.predict(test)

        prep, model, numeric, train_rows = fit_frozen(store, train_seasons)
        candidate_prediction = predict_frozen(test, prep, model, numeric)

        current = metrics(actual, current_prediction)
        candidate = metrics(actual, candidate_prediction)
        report["seasons"][season] = {
            "train_seasons": list(train_seasons),
            "training_rows": train_rows,
            "current": current,
            "candidate": candidate,
            "delta_mae": candidate["mae"] - current["mae"],
            "relative_improvement": (current["mae"] - candidate["mae"]) / current["mae"],
            "clubs": club_metrics(test, current_prediction, candidate_prediction),
        }
        all_actual.extend(actual.tolist())
        all_current.extend(np.asarray(current_prediction).tolist())
        all_candidate.extend(np.asarray(candidate_prediction).tolist())

    current_combined = metrics(all_actual, all_current)
    candidate_combined = metrics(all_actual, all_candidate)
    report["combined"] = {
        "current": current_combined,
        "candidate": candidate_combined,
        "delta_mae": candidate_combined["mae"] - current_combined["mae"],
        "relative_improvement": (
            current_combined["mae"] - candidate_combined["mae"]
        ) / current_combined["mae"],
    }
    improves_each = all(
        row["candidate"]["mae"] < row["current"]["mae"]
        for row in report["seasons"].values()
    )
    report["decision"] = {
        "improves_each_historical_regression_season": improves_each,
        "improves_combined": candidate_combined["mae"] < current_combined["mae"],
        "under_1700_combined": candidate_combined["mae"] < 1700.0,
        "production_promotion": "NO_AUTO_PROMOTION_PROSPECTIVE_EVIDENCE_REQUIRED",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
