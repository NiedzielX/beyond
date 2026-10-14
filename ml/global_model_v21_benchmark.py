#!/usr/bin/env python3
"""Beyond Global Model v2.1 benchmark.

This script consumes a canonical point-in-time feature-store CSV and evaluates
Beyond's historical attendance forecasting architecture under a strict
season-blocked protocol.

Protocol
--------
* candidate selection: train 2021/22 + 2022/23, validate 2023/24;
* first untouched historical holdout: train through 2023/24, test 2024/25;
* second untouched historical holdout: train through 2024/25, test 2025/26;
* selected model family is chosen independently per horizon;
* models learn a residual correction over a fixed point-in-time club-history
  baseline;
* no automatic production promotion is performed.

Expected feature-store contract
-------------------------------
Required metadata columns:
  match_key, season, horizon, as_of_at, kickoff_at,
  home_club_key, away_club_key, target_attendance,
  training_eligible, baseline_fixed

All remaining numeric columns are treated as point-in-time model features.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

CAT = ["home_club_key", "away_club_key"]
META = {
    "match_key",
    "season",
    "horizon",
    "as_of_at",
    "kickoff_at",
    "home_club_key",
    "away_club_key",
    "target_attendance",
    "training_eligible",
    "baseline_fixed",
}

DEV_TRAIN_SEASONS = ["2021/2022", "2022/2023"]
DEV_SEASON = "2023/2024"
HOLDOUTS = [
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]


def metrics(actual: pd.Series | np.ndarray, prediction: pd.Series | np.ndarray) -> dict:
    actual = np.asarray(actual, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    error = prediction - actual
    absolute = np.abs(error)
    return {
        "n": int(len(actual)),
        "mae": round(float(np.mean(absolute)), 4),
        "median_ae": round(float(np.median(absolute)), 4),
        "rmse": round(float(np.sqrt(np.mean(error ** 2))), 4),
        "wape_pct": round(float(np.sum(absolute) / np.sum(actual) * 100.0), 4),
        "bias": round(float(np.mean(error)), 4),
        "within_10_pct": round(float(np.mean(absolute / actual <= 0.10) * 100.0), 4),
        "within_20_pct": round(float(np.mean(absolute / actual <= 0.20) * 100.0), 4),
    }


def numeric_features(frame: pd.DataFrame) -> list[str]:
    return [
        column
        for column in frame.columns
        if column not in META and pd.api.types.is_numeric_dtype(frame[column])
    ]


def preprocessor(numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CAT,
            ),
            (
                "num",
                SimpleImputer(strategy="median", add_indicator=True),
                numeric,
            ),
        ]
    )


def hist_gradient_boosting(numeric: list[str]) -> Pipeline:
    return Pipeline(
        [
            ("pre", preprocessor(numeric)),
            (
                "model",
                HistGradientBoostingRegressor(
                    loss="absolute_error",
                    learning_rate=0.05,
                    max_iter=250,
                    max_leaf_nodes=15,
                    min_samples_leaf=10,
                    l2_regularization=1.0,
                    random_state=42,
                ),
            ),
        ]
    )


def xgboost(numeric: list[str]) -> Pipeline:
    return Pipeline(
        [
            ("pre", preprocessor(numeric)),
            (
                "model",
                XGBRegressor(
                    n_estimators=350,
                    max_depth=3,
                    learning_rate=0.03,
                    subsample=0.85,
                    colsample_bytree=0.85,
                    min_child_weight=5,
                    reg_lambda=10,
                    objective="reg:absoluteerror",
                    n_jobs=4,
                    random_state=42,
                ),
            ),
        ]
    )


def factories(numeric: list[str]):
    return {
        "HistGradientBoosting": lambda: hist_gradient_boosting(numeric),
        "XGBoost": lambda: xgboost(numeric),
    }


def clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = META
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"Feature store missing required columns: {missing}")

    out = frame.copy()
    out["training_eligible"] = out["training_eligible"].astype(str).str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    ).fillna(out["training_eligible"].astype(bool))
    out["target_attendance"] = pd.to_numeric(out["target_attendance"], errors="raise")
    out["baseline_fixed"] = pd.to_numeric(out["baseline_fixed"], errors="coerce")
    out = out[out["training_eligible"] & out["baseline_fixed"].notna()].copy()
    return out


def fit_residual(model: Pipeline, train: pd.DataFrame, numeric: list[str]) -> Pipeline:
    target = train["target_attendance"].astype(float) - train["baseline_fixed"].astype(float)
    model.fit(train[CAT + numeric], target)
    return model


def predict_attendance(model: Pipeline, frame: pd.DataFrame, numeric: list[str]) -> np.ndarray:
    residual = model.predict(frame[CAT + numeric])
    return np.maximum(0.0, frame["baseline_fixed"].astype(float).to_numpy() + residual)


def evaluate_horizon(frame: pd.DataFrame, horizon: str, numeric: list[str]) -> dict:
    data = frame[frame["horizon"] == horizon].copy()
    dev_train = data[data["season"].isin(DEV_TRAIN_SEASONS)]
    dev = data[data["season"] == DEV_SEASON]
    if dev_train.empty or dev.empty:
        raise RuntimeError(f"{horizon}: missing development train/validation rows")

    development = {}
    model_factories = factories(numeric)
    for name, factory in model_factories.items():
        model = fit_residual(factory(), dev_train, numeric)
        prediction = predict_attendance(model, dev, numeric)
        development[name] = metrics(dev["target_attendance"], prediction)

    selected = min(
        development,
        key=lambda name: (
            development[name]["mae"],
            development[name]["wape_pct"],
            abs(development[name]["bias"]),
        ),
    )

    holdouts = {}
    for test_season, train_seasons in HOLDOUTS:
        train = data[data["season"].isin(train_seasons)]
        test = data[data["season"] == test_season]
        if train.empty or test.empty:
            raise RuntimeError(f"{horizon}: missing rows for holdout {test_season}")

        model = fit_residual(model_factories[selected](), train, numeric)
        prediction = predict_attendance(model, test, numeric)
        model_metrics = metrics(test["target_attendance"], prediction)
        baseline_metrics = metrics(test["target_attendance"], test["baseline_fixed"])
        delta = baseline_metrics["mae"] - model_metrics["mae"]

        holdouts[test_season] = {
            "training_seasons": train_seasons,
            "rows": int(len(test)),
            "baseline": baseline_metrics,
            "model": model_metrics,
            "mae_improvement": round(float(delta), 4),
            "mae_improvement_pct": round(float(delta / baseline_metrics["mae"] * 100.0), 4),
        }

    return {
        "horizon": horizon,
        "selected_model": selected,
        "development": development,
        "holdouts": holdouts,
    }


def write_markdown(report: dict, output: Path) -> None:
    lines = [
        "# Beyond Global Model v2.1 benchmark",
        "",
        f"Feature rows: **{report['feature_rows']:,}**  ",
        f"Matches: **{report['matches']:,}**  ",
        f"Seasons: **{', '.join(report['seasons'])}**",
        "",
        "| Horizon | Selected model | 2024/25 baseline | 2024/25 model | Improvement | 2025/26 baseline | 2025/26 model | Improvement |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for horizon in ["T-30d", "T-14d", "T-7d", "T-3d", "T-1d"]:
        result = report["horizons"][horizon]
        a = result["holdouts"]["2024/2025"]
        b = result["holdouts"]["2025/2026"]
        lines.append(
            f"| {horizon} | {result['selected_model']} | "
            f"{a['baseline']['mae']:.1f} | **{a['model']['mae']:.1f}** | **{a['mae_improvement_pct']:.1f}%** | "
            f"{b['baseline']['mae']:.1f} | **{b['model']['mae']:.1f}** | **{b['mae_improvement_pct']:.1f}%** |"
        )
    lines.extend(
        [
            "",
            "Model selection uses 2023/24 only. 2024/25 and 2025/26 are not used for family selection.",
            "No production promotion is performed by this benchmark.",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-store", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    raw = pd.read_csv(args.feature_store)
    frame = clean_frame(raw)
    numeric = numeric_features(frame)
    horizons = sorted(frame["horizon"].dropna().unique())
    expected = {"T-30d", "T-14d", "T-7d", "T-3d", "T-1d"}
    if set(horizons) != expected:
        raise RuntimeError(f"Unexpected horizons: {horizons}")

    result = {
        "benchmark_version": "global-model-v2.1",
        "protocol": {
            "development_train_seasons": DEV_TRAIN_SEASONS,
            "development_selection_season": DEV_SEASON,
            "holdouts": [season for season, _ in HOLDOUTS],
            "architecture": "fixed point-in-time baseline + learned residual correction",
            "automatic_promotion": False,
        },
        "feature_rows": int(len(raw)),
        "eligible_feature_rows": int(len(frame)),
        "matches": int(raw["match_key"].nunique()),
        "seasons": sorted(raw["season"].dropna().unique()),
        "numeric_feature_count": len(numeric),
        "horizons": {
            horizon: evaluate_horizon(frame, horizon, numeric)
            for horizon in ["T-30d", "T-14d", "T-7d", "T-3d", "T-1d"]
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if args.markdown_output:
        write_markdown(result, args.markdown_output)

    print(json.dumps({
        horizon: {
            "selected_model": value["selected_model"],
            "holdouts": {
                season: {
                    "baseline_mae": metrics_["baseline"]["mae"],
                    "model_mae": metrics_["model"]["mae"],
                    "improvement_pct": metrics_["mae_improvement_pct"],
                }
                for season, metrics_ in value["holdouts"].items()
            },
        }
        for horizon, value in result["horizons"].items()
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
