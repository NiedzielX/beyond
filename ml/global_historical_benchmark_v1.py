#!/usr/bin/env python3
"""Beyond Global Historical Benchmark v1.

Question: does pooling point-in-time information across Ekstraklasa clubs beat a
simple club-specific attendance-history baseline?

The benchmark is deliberately prequential:
- features for each target are frozen at its forecast horizon;
- a target can train only on matches completed before that target's `as_of_at`;
- model/config selection uses an autumn development window only;
- the spring window is untouched for selection;
- production is never changed automatically.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

from ml.features.global_feature_store_v2 import build_feature_store, load_ground_truth

DEV_START = pd.Timestamp("2025-10-01T00:00:00Z")
DEV_END = pd.Timestamp("2026-01-01T00:00:00Z")
HOLDOUT_START = pd.Timestamp("2026-01-30T00:00:00Z")
MIN_HOME_HISTORY = 3
MIN_TRAIN_ROWS = 40
MATCH_COMPLETION_BUFFER = pd.Timedelta(hours=3)

CATEGORICAL = ["home_club_key", "away_club_key"]
NUMERIC = [
    "round_no", "season_progress", "month", "weekday", "kickoff_minutes", "is_weekend",
    "month_sin", "month_cos", "doy_sin", "doy_cos", "kickoff_sin", "kickoff_cos",
    "home_history_n", "home_attendance_mean", "home_attendance_last",
    "home_attendance_rolling3", "home_attendance_rolling5", "home_attendance_std",
    "home_attendance_trend3_vs_mean", "days_since_last_home",
    "opponent_draw_n", "opponent_draw_ratio_mean", "opponent_draw_ratio_recent3",
    "opponent_raw_attendance_mean",
    "home_matches_played", "home_points", "home_ppg", "home_goal_diff_per_game",
    "home_form5_points", "home_form5_goal_diff", "home_days_since_last_match",
    "home_matches_last_14d",
    "away_matches_played", "away_points", "away_ppg", "away_goal_diff_per_game",
    "away_form5_points", "away_form5_goal_diff", "away_days_since_last_match",
    "away_matches_last_14d",
    "home_position", "away_position", "position_gap", "ppg_gap",
    "form5_points_gap", "goal_diff_per_game_gap",
]


@dataclass(frozen=True)
class Candidate:
    name: str
    family: str
    factory: Callable[[], Pipeline]


def metrics(actual, prediction) -> dict:
    actual = np.asarray(actual, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    error = prediction - actual
    ae = np.abs(error)
    ape = ae / np.where(actual == 0, np.nan, actual) * 100.0
    return {
        "n": int(len(actual)),
        "mae": round(float(np.nanmean(ae)), 2),
        "median_ae": round(float(np.nanmedian(ae)), 2),
        "rmse": round(float(math.sqrt(np.nanmean(error ** 2))), 2),
        "mape_pct": round(float(np.nanmean(ape)), 2),
        "wape_pct": round(float(np.nansum(ae) / np.nansum(actual) * 100.0), 2),
        "bias": round(float(np.nanmean(error)), 2),
        "within_10_pct": round(float(np.nanmean(ape <= 10.0) * 100.0), 2),
        "within_20_pct": round(float(np.nanmean(ape <= 20.0) * 100.0), 2),
    }


def preprocess(scale: bool) -> ColumnTransformer:
    numeric_steps: list[tuple[str, object]] = [("impute", SimpleImputer(strategy="median", add_indicator=True))]
    if scale:
        numeric_steps.append(("scale", RobustScaler()))
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
        ("num", Pipeline(numeric_steps), NUMERIC),
    ])


def pipe(estimator, *, scale: bool) -> Pipeline:
    return Pipeline([("pre", preprocess(scale)), ("model", estimator)])


def candidates() -> list[Candidate]:
    out = []
    for alpha in [0.1, 1.0, 10.0, 100.0, 1000.0]:
        out.append(Candidate(
            f"ridge_residual_a{str(alpha).replace('.', '_')}", "ridge",
            lambda alpha=alpha: pipe(Ridge(alpha=alpha), scale=True),
        ))
    out.extend([
        Candidate(
            "huber_residual_e1_35", "huber",
            lambda: pipe(HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=2000), scale=True),
        ),
        Candidate(
            "gbr_residual_huber", "gradient_boosting",
            lambda: pipe(GradientBoostingRegressor(
                loss="huber", n_estimators=180, learning_rate=0.03, max_depth=2,
                min_samples_leaf=8, random_state=42,
            ), scale=False),
        ),
        Candidate(
            "hist_gbr_residual", "hist_gradient_boosting",
            lambda: pipe(HistGradientBoostingRegressor(
                loss="absolute_error", learning_rate=0.05, max_iter=220,
                max_leaf_nodes=15, min_samples_leaf=10, l2_regularization=1.0,
                random_state=42,
            ), scale=False),
        ),
        Candidate(
            "extra_trees_residual", "extra_trees",
            lambda: pipe(ExtraTreesRegressor(
                n_estimators=400, min_samples_leaf=5, max_features=0.8,
                random_state=42, n_jobs=1,
            ), scale=False),
        ),
    ])
    return out


def prepare_store() -> pd.DataFrame:
    store = build_feature_store(load_ground_truth())
    store["as_of_at"] = pd.to_datetime(store["as_of_at"], utc=True)
    store["kickoff_at"] = pd.to_datetime(store["kickoff_at"], utc=True)
    store = store[store["home_history_n"] >= MIN_HOME_HISTORY].copy()
    store = store[store["home_attendance_rolling3"].notna()].copy()
    return store.sort_values(["horizon", "as_of_at", "match_key"]).reset_index(drop=True)


def baseline_report(frame: pd.DataFrame) -> dict:
    actual = frame["target_attendance"].astype(float).to_numpy()
    reports = {
        "home_rolling3": metrics(actual, frame["home_attendance_rolling3"].astype(float).to_numpy()),
        "home_rolling5": metrics(actual, frame["home_attendance_rolling5"].astype(float).to_numpy()),
        "home_expanding_mean": metrics(actual, frame["home_attendance_mean"].astype(float).to_numpy()),
    }
    winner = min(reports, key=lambda name: reports[name]["mae"])
    return {"winner": winner, "candidates": reports}


def baseline_column(name: str) -> str:
    return {
        "home_rolling3": "home_attendance_rolling3",
        "home_rolling5": "home_attendance_rolling5",
        "home_expanding_mean": "home_attendance_mean",
    }[name]


def prequential_predictions(
    horizon_frame: pd.DataFrame,
    target_frame: pd.DataFrame,
    candidate: Candidate,
    baseline_name: str,
) -> pd.DataFrame:
    baseline_col = baseline_column(baseline_name)
    predictions = []

    for target in target_frame.sort_values("as_of_at").itertuples(index=False):
        cutoff = target.as_of_at
        training = horizon_frame[
            (horizon_frame["kickoff_at"] + MATCH_COMPLETION_BUFFER < cutoff)
            & horizon_frame[baseline_col].notna()
        ].copy()
        if len(training) < MIN_TRAIN_ROWS:
            continue

        X_train = training[CATEGORICAL + NUMERIC].copy()
        y_train = (
            training["target_attendance"].astype(float)
            - training[baseline_col].astype(float)
        ).to_numpy()
        model = candidate.factory()
        model.fit(X_train, y_train)

        target_row = pd.DataFrame([{column: getattr(target, column) for column in CATEGORICAL + NUMERIC}])
        residual = float(model.predict(target_row)[0])
        baseline = float(getattr(target, baseline_col))
        prediction = max(0.0, baseline + residual)
        predictions.append({
            "match_key": target.match_key,
            "as_of_at": target.as_of_at,
            "kickoff_at": target.kickoff_at,
            "actual": float(target.target_attendance),
            "baseline": baseline,
            "prediction": prediction,
            "train_rows": int(len(training)),
        })

    return pd.DataFrame(predictions)


def score_prediction_frame(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"n": 0, "mae": None}
    return metrics(frame["actual"].to_numpy(), frame["prediction"].to_numpy())


def evaluate_horizon(store: pd.DataFrame, horizon: str) -> dict:
    frame = store[store["horizon"] == horizon].copy()
    dev = frame[(frame["kickoff_at"] >= DEV_START) & (frame["kickoff_at"] < DEV_END)].copy()
    holdout = frame[frame["kickoff_at"] >= HOLDOUT_START].copy()

    # Pick the naive baseline using only the development window.
    dev_baselines = baseline_report(dev)
    baseline_name = dev_baselines["winner"]
    baseline_col = baseline_column(baseline_name)

    candidate_reports = {}
    candidate_frames = {}
    for candidate in candidates():
        pred = prequential_predictions(frame, dev, candidate, baseline_name)
        candidate_frames[candidate.name] = pred
        candidate_reports[candidate.name] = {
            "family": candidate.family,
            "metrics": score_prediction_frame(pred),
        }

    usable = [name for name, result in candidate_reports.items() if result["metrics"].get("n", 0) > 0]
    if not usable:
        raise RuntimeError(f"No candidate had sufficient training rows at {horizon}")
    selected_name = min(
        usable,
        key=lambda name: (
            candidate_reports[name]["metrics"]["mae"],
            candidate_reports[name]["metrics"]["wape_pct"],
            abs(candidate_reports[name]["metrics"]["bias"]),
        ),
    )
    selected = next(candidate for candidate in candidates() if candidate.name == selected_name)

    holdout_pred = prequential_predictions(frame, holdout, selected, baseline_name)
    holdout_model_metrics = score_prediction_frame(holdout_pred)

    holdout_keys = set(holdout_pred["match_key"]) if not holdout_pred.empty else set()
    holdout_comparable = holdout[holdout["match_key"].isin(holdout_keys)].copy()
    baseline_prediction = holdout_comparable[baseline_col].astype(float).to_numpy()
    holdout_baseline_metrics = metrics(
        holdout_comparable["target_attendance"].astype(float).to_numpy(),
        baseline_prediction,
    ) if len(holdout_comparable) else {"n": 0, "mae": None}

    delta = (
        holdout_baseline_metrics["mae"] - holdout_model_metrics["mae"]
        if holdout_baseline_metrics.get("mae") is not None and holdout_model_metrics.get("mae") is not None
        else None
    )
    return {
        "horizon": horizon,
        "eligible_rows": int(len(frame)),
        "development_rows": int(len(dev)),
        "holdout_rows": int(len(holdout)),
        "development_baselines": dev_baselines,
        "selected_baseline": baseline_name,
        "development_candidates": candidate_reports,
        "selected_model": selected_name,
        "holdout_baseline": holdout_baseline_metrics,
        "holdout_model": holdout_model_metrics,
        "holdout_mae_improvement": round(float(delta), 2) if delta is not None else None,
        "holdout_improvement_pct": round(float(delta / holdout_baseline_metrics["mae"] * 100.0), 2)
        if delta is not None and holdout_baseline_metrics["mae"] else None,
        "decision": "GLOBAL_MODEL_BETTER" if delta is not None and delta > 0 else "CLUB_BASELINE_BETTER",
    }


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Global Historical Benchmark v1",
        "",
        "One-season prequential benchmark. Candidate selection uses autumn 2025 only; spring 2026 is untouched for selection.",
        "",
        "| Horizon | Baseline | Selected model | Holdout baseline MAE | Holdout model MAE | Improvement | Decision |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for horizon, result in report["horizons"].items():
        b = result["holdout_baseline"].get("mae")
        m = result["holdout_model"].get("mae")
        delta = result["holdout_mae_improvement"]
        lines.append(
            f"| {horizon} | {result['selected_baseline']} | {result['selected_model']} | "
            f"{b if b is not None else 'n/a'} | {m if m is not None else 'n/a'} | "
            f"{delta if delta is not None else 'n/a'} | {result['decision']} |"
        )
    lines.extend([
        "",
        "This benchmark is an architecture/proof-of-signal stage. One season is not sufficient to promote a global production model.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    store = prepare_store()
    horizon_results = {
        horizon: evaluate_horizon(store, horizon)
        for horizon in sorted(store["horizon"].unique())
    }
    report = {
        "benchmark_version": "global-historical-v1",
        "dataset_version": str(store["dataset_version"].iloc[0]),
        "feature_set_version": str(store["feature_set_version"].iloc[0]),
        "method": "prequential point-in-time evaluation",
        "development_window": [DEV_START.isoformat(), DEV_END.isoformat()],
        "holdout_start": HOLDOUT_START.isoformat(),
        "minimum_home_history": MIN_HOME_HISTORY,
        "minimum_training_rows": MIN_TRAIN_ROWS,
        "automatic_promotion": False,
        "horizons": horizon_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.markdown_output:
        write_markdown(report, args.markdown_output)
    print(json.dumps({
        h: {
            "baseline": r["selected_baseline"],
            "model": r["selected_model"],
            "baseline_mae": r["holdout_baseline"].get("mae"),
            "model_mae": r["holdout_model"].get("mae"),
            "improvement": r["holdout_mae_improvement"],
            "decision": r["decision"],
        }
        for h, r in horizon_results.items()
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
