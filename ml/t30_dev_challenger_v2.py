#!/usr/bin/env python3
"""Development-only T-30 challenger search.

Governance:
- train only on 2021/22 + 2022/23;
- select only on 2023/24;
- never read/evaluate 2024/25 or 2025/26 in this script;
- reuse the frozen Structural Prior PIT feature contract;
- do not mutate production runtime/artifacts.

The output is candidate ranking only. A selected candidate must be frozen before
any untouched-holdout verification is performed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

from ml.demand_engine.structural_prior_runtime import CAT, feature_columns
from ml.features.structural_prior_feature_store_v1 import build_feature_store, WARSAW_TZ

TRAIN_SEASONS = ["2021/2022", "2022/2023"]
DEV_SEASON = "2023/2024"
HORIZON = "T-30"
BASELINE = "baseline_season"
FORBIDDEN_SEASONS = {"2024/2025", "2025/2026"}


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


def mae(actual, predicted) -> float:
    return float(np.mean(np.abs(np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float))))


def score_prediction(dev: pd.DataFrame, residual_prediction: np.ndarray) -> np.ndarray:
    pred = (
        dev[BASELINE].astype(float).to_numpy()
        + residual_prediction * dev["capacity"].astype(float).to_numpy()
    )
    return np.clip(pred, 0.0, dev["capacity"].astype(float).to_numpy())


def model_candidates():
    # Current champion is included exactly as a control.
    yield (
        "current_extra_leaf3_f08",
        ExtraTreesRegressor(
            n_estimators=500,
            min_samples_leaf=3,
            max_features=0.8,
            random_state=42,
            n_jobs=-1,
        ),
    )

    for leaf in (1, 2, 4, 5, 7):
        for max_features in (0.55, 0.70, 0.90, 1.0):
            yield (
                f"extra_leaf{leaf}_f{max_features:.2f}",
                ExtraTreesRegressor(
                    n_estimators=700,
                    min_samples_leaf=leaf,
                    max_features=max_features,
                    random_state=42,
                    n_jobs=-1,
                ),
            )

    for leaf in (2, 4, 7):
        for max_features in (0.6, 0.8, 1.0):
            yield (
                f"rf_leaf{leaf}_f{max_features:.1f}",
                RandomForestRegressor(
                    n_estimators=600,
                    min_samples_leaf=leaf,
                    max_features=max_features,
                    random_state=42,
                    n_jobs=-1,
                ),
            )

    for leaf_nodes, min_leaf in ((7, 8), (15, 8), (15, 15), (31, 10), (31, 20)):
        for lr in (0.03, 0.06):
            yield (
                f"hist_nodes{leaf_nodes}_leaf{min_leaf}_lr{lr:.2f}",
                HistGradientBoostingRegressor(
                    loss="absolute_error",
                    learning_rate=lr,
                    max_iter=300,
                    max_leaf_nodes=leaf_nodes,
                    min_samples_leaf=min_leaf,
                    l2_regularization=1.0,
                    random_state=42,
                ),
            )

    for loss in ("huber", "absolute_error"):
        for depth in (1, 2, 3):
            yield (
                f"gbr_{loss}_d{depth}",
                GradientBoostingRegressor(
                    loss=loss,
                    n_estimators=250,
                    learning_rate=0.03,
                    max_depth=depth,
                    min_samples_leaf=8,
                    random_state=42,
                ),
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-runtime",
        type=Path,
        default=Path("ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz"),
    )
    parser.add_argument("--output", type=Path, default=Path("/tmp/t30-dev-challenger-v2.json"))
    args = parser.parse_args()

    matches = canonical_matches(args.historical_runtime)
    if FORBIDDEN_SEASONS.intersection(TRAIN_SEASONS + [DEV_SEASON]):
        raise RuntimeError("Holdout season leaked into development protocol")

    store = build_feature_store(matches)
    rows = store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(TRAIN_SEASONS + [DEV_SEASON])
    ].copy()
    train = rows[rows["season"].isin(TRAIN_SEASONS) & rows[BASELINE].notna()].copy()
    dev = rows[(rows["season"] == DEV_SEASON) & rows[BASELINE].notna()].copy()

    numeric = feature_columns(store, "full")
    prep = preprocessor(numeric)
    x_train = prep.fit_transform(train[CAT + numeric])
    x_dev = prep.transform(dev[CAT + numeric])
    y_train = (
        train["target_attendance"].astype(float).to_numpy() / train["capacity"].astype(float).to_numpy()
        - train[BASELINE].astype(float).to_numpy() / train["capacity"].astype(float).to_numpy()
    )
    actual = dev["target_attendance"].astype(float).to_numpy()
    baseline_prediction = dev[BASELINE].astype(float).to_numpy()

    results: list[dict] = []
    current_prediction = None
    prediction_cache: dict[str, np.ndarray] = {}

    for name, model in model_candidates():
        model.fit(x_train, y_train)
        residual = np.asarray(model.predict(x_dev), dtype=float)
        prediction = score_prediction(dev, residual)
        prediction_cache[name] = prediction
        value = mae(actual, prediction)
        results.append({
            "candidate": name,
            "mae": value,
            "uplift_vs_baseline": mae(actual, baseline_prediction) - value,
        })
        if name == "current_extra_leaf3_f08":
            current_prediction = prediction

    if current_prediction is None:
        raise RuntimeError("Current T-30 control prediction missing")

    current_mae = mae(actual, current_prediction)

    # Predefined residual-shrinkage challengers around the current frozen model.
    current_delta = current_prediction - baseline_prediction
    for alpha in (0.45, 0.60, 0.75, 0.90, 1.10):
        pred = np.clip(
            baseline_prediction + alpha * current_delta,
            0.0,
            dev["capacity"].astype(float).to_numpy(),
        )
        results.append({
            "candidate": f"current_extra_residual_shrink_{alpha:.2f}",
            "mae": mae(actual, pred),
            "uplift_vs_baseline": mae(actual, baseline_prediction) - mae(actual, pred),
        })
        prediction_cache[f"current_extra_residual_shrink_{alpha:.2f}"] = pred

    # Small, predeclared model blends. Inputs are fixed before development scores
    # are read; holdouts are still never loaded by this script.
    blend_pairs = [
        ("current_extra_leaf3_f08", "hist_nodes15_leaf8_lr0.03"),
        ("current_extra_leaf3_f08", "gbr_huber_d2"),
        ("current_extra_leaf3_f08", "rf_leaf4_f0.8"),
    ]
    for left, right in blend_pairs:
        if left not in prediction_cache or right not in prediction_cache:
            continue
        for weight in (0.25, 0.50, 0.75):
            pred = weight * prediction_cache[left] + (1.0 - weight) * prediction_cache[right]
            results.append({
                "candidate": f"blend_{left}__{right}__w{weight:.2f}",
                "mae": mae(actual, pred),
                "uplift_vs_baseline": mae(actual, baseline_prediction) - mae(actual, pred),
            })

    results.sort(key=lambda item: (item["mae"], item["candidate"]))
    baseline_mae = mae(actual, baseline_prediction)
    best = results[0]

    report = {
        "experiment": "t30-dev-challenger-v2",
        "governance": {
            "train_seasons": TRAIN_SEASONS,
            "selection_season": DEV_SEASON,
            "holdouts_opened": False,
            "automatic_promotion": False,
            "feature_contract": "structural-prior-pit-v1+verified-capacity-v1",
            "target": "verified-capacity occupancy residual",
        },
        "rows": {"train": int(len(train)), "development": int(len(dev))},
        "numeric_feature_count": len(numeric),
        "baseline_mae": baseline_mae,
        "current_champion_dev_mae": current_mae,
        "best": {
            **best,
            "delta_vs_current": best["mae"] - current_mae,
            "relative_improvement_vs_current": (current_mae - best["mae"]) / current_mae,
        },
        "top_15": [
            {
                **item,
                "delta_vs_current": item["mae"] - current_mae,
            }
            for item in results[:15]
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
