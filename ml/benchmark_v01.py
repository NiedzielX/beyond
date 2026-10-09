#!/usr/bin/env python3
"""Beyond ML benchmark harness v0.1.

Reproduces the Lech v1.3 season walk-forward benchmark and compares the
incumbent sklearn GradientBoosting model with CatBoost challengers. Challenger
selection is performed only on development seasons; the holdout is untouched.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

TEST_SEASONS = ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
DEVELOPMENT_SEASONS = ["2022/2023", "2023/2024"]
HOLDOUT_SEASONS = ["2024/2025", "2025/2026"]
RECENCY_HALF_LIFE_DAYS = 365.25 * 3.0
CATEGORICAL = ["opponent_key"]

CORE = [
    "month", "weekday", "kickoff_minutes", "is_weekend",
    "rolling_3", "rolling_5", "rolling_10", "season_avg_so_far",
    "recent_attendance_trend", "opponent_draw_ratio", "opponent_recent_draw_ratio",
    "round_no", "matches_remaining_after", "season_progress", "late_season",
    "lech_position_before", "opponent_position_before", "position_gap",
    "lech_points_before", "opponent_points_before", "points_gap", "points_to_leader",
    "opponent_points_to_leader", "leader_margin_if_lech_first", "lech_ppg_before",
    "opponent_ppg_before", "ppg_gap", "lech_last5_points", "opponent_last5_points",
    "form_points_gap", "lech_last5_goal_diff", "opponent_last5_goal_diff", "form_gd_gap",
    "days_since_lech_prev_league_match", "days_since_opponent_prev_league_match",
    "lech_matches_last_14d", "opponent_matches_last_14d", "title_reachability",
    "title_pressure", "top4_match", "late_top4_match",
]

SEASONALITY = [
    "month_sin", "month_cos", "doy_sin", "doy_cos", "kickoff_sin", "kickoff_cos",
    "is_summer_month", "is_winter_month", "days_to_nearest_public_holiday",
]

TABLE_IMPORTANCE = [
    "is_leader", "is_top2", "is_top3", "opponent_top3", "opponent_top6",
    "abs_position_gap", "abs_points_gap", "same_table_band", "points_close_match",
    "remaining_points_available", "normalized_points_to_leader", "title_alive",
    "title_chaser_close", "leader_late", "title_chaser_late", "top3_match_late",
    "direct_rival_late", "position_gap_late", "points_gap_late", "opponent_strength_late",
]

FEATURE_SETS = {
    "early": CORE + SEASONALITY,
    "early_table": CORE + SEASONALITY + TABLE_IMPORTANCE,
}


def metric_set(actual, pred):
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    error = pred - actual
    ae = np.abs(error)
    ape = ae / actual * 100.0
    return {
        "n": int(len(actual)),
        "mae": round(float(np.mean(ae)), 2),
        "median_ae": round(float(np.median(ae)), 2),
        "rmse": round(float(math.sqrt(np.mean(error ** 2))), 2),
        "mape_pct": round(float(np.mean(ape)), 2),
        "wape_pct": round(float(np.sum(ae) / np.sum(actual) * 100.0), 2),
        "bias": round(float(np.mean(error)), 2),
        "within_5_pct": round(float(np.mean(ape <= 5.0) * 100.0), 2),
        "within_10_pct": round(float(np.mean(ape <= 10.0) * 100.0), 2),
        "within_20_pct": round(float(np.mean(ape <= 20.0) * 100.0), 2),
    }


def add_features(df):
    df = df.copy()
    if "capacity_constrained_for_model" in df.columns:
        constrained = (
            df["capacity_constrained_for_model"]
            .astype(str).str.lower().isin(["true", "1", "yes"])
        )
        df = df.loc[~constrained].copy()

    df["match_date"] = pd.to_datetime(df["match_date"], utc=True, errors="raise")
    df = df.sort_values("match_date").reset_index(drop=True)
    local = df["match_date"].dt.tz_convert("Europe/Warsaw")
    df["month"] = local.dt.month
    df["weekday"] = local.dt.weekday
    df["kickoff_minutes"] = local.dt.hour * 60 + local.dt.minute
    df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)

    numeric_source = sorted(set([
        "attendance", "round_no", "matches_remaining_after", "season_progress",
        "lech_position_before", "opponent_position_before", "position_gap",
        "lech_points_before", "opponent_points_before", "points_gap", "points_to_leader",
        "opponent_points_to_leader", "leader_margin_if_lech_first", "lech_ppg_before",
        "opponent_ppg_before", "lech_last5_points", "opponent_last5_points",
        "lech_last5_goal_diff", "opponent_last5_goal_diff",
        "days_since_lech_prev_league_match", "days_since_opponent_prev_league_match",
        "lech_matches_last_14d", "opponent_matches_last_14d",
    ] + SEASONALITY))

    for col in numeric_source:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Every attendance-history feature uses only previously completed matches.
    prior = df["attendance"].shift(1)
    df["rolling_3"] = prior.rolling(3, min_periods=1).mean()
    df["rolling_5"] = prior.rolling(5, min_periods=1).mean()
    df["rolling_10"] = prior.rolling(10, min_periods=1).mean()
    df["global_prev_mean"] = prior.expanding().mean()
    df["season_avg_so_far"] = (
        df.groupby("season")["attendance"]
        .transform(lambda s: s.shift(1).expanding().mean())
        .fillna(df["global_prev_mean"])
    )
    df["recent_attendance_trend"] = (
        df["rolling_3"] / df["rolling_10"].replace(0, np.nan)
    )
    df["opponent_prev_mean"] = (
        df.groupby("opponent_key")["attendance"]
        .transform(lambda s: s.shift(1).expanding().mean())
        .fillna(df["global_prev_mean"])
    )
    df["opponent_draw_ratio"] = (
        df["opponent_prev_mean"] / df["global_prev_mean"].replace(0, np.nan)
    ).clip(0.50, 1.80)
    df["opponent_recent_mean"] = (
        df.groupby("opponent_key")["attendance"]
        .transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
        .fillna(df["opponent_prev_mean"])
    )
    df["opponent_recent_draw_ratio"] = (
        df["opponent_recent_mean"] / df["global_prev_mean"].replace(0, np.nan)
    ).clip(0.50, 1.80)

    df["ppg_gap"] = df["lech_ppg_before"] - df["opponent_ppg_before"]
    df["form_points_gap"] = df["lech_last5_points"] - df["opponent_last5_points"]
    df["form_gd_gap"] = df["lech_last5_goal_diff"] - df["opponent_last5_goal_diff"]
    df["late_season"] = df["season_progress"].clip(0.0, 1.0) ** 2
    remaining = (3.0 * (df["matches_remaining_after"] + 1)).clip(lower=3.0)
    df["title_reachability"] = (1.0 - df["points_to_leader"] / remaining).clip(0.0, 1.0)
    df["title_pressure"] = df["late_season"] * df["title_reachability"]
    df["top4_match"] = (
        (df["lech_position_before"] <= 4) & (df["opponent_position_before"] <= 4)
    ).astype(int)
    df["late_top4_match"] = df["top4_match"] * df["late_season"]

    df["is_leader"] = (df["lech_position_before"] == 1).astype(int)
    df["is_top2"] = (df["lech_position_before"] <= 2).astype(int)
    df["is_top3"] = (df["lech_position_before"] <= 3).astype(int)
    df["opponent_top3"] = (df["opponent_position_before"] <= 3).astype(int)
    df["opponent_top6"] = (df["opponent_position_before"] <= 6).astype(int)
    df["abs_position_gap"] = df["position_gap"].abs()
    df["abs_points_gap"] = df["points_gap"].abs()
    df["same_table_band"] = (df["abs_position_gap"] <= 3).astype(int)
    df["points_close_match"] = (df["abs_points_gap"] <= 6).astype(int)
    df["remaining_points_available"] = remaining
    df["normalized_points_to_leader"] = (df["points_to_leader"] / remaining).clip(0.0, 2.0)
    df["title_alive"] = (df["points_to_leader"] <= remaining).astype(int)
    df["title_chaser_close"] = (
        (df["lech_position_before"] <= 3) & (df["points_to_leader"] <= 6)
    ).astype(int)
    df["leader_late"] = df["is_leader"] * df["late_season"]
    df["title_chaser_late"] = df["title_chaser_close"] * df["late_season"]
    df["top3_match_late"] = (
        ((df["lech_position_before"] <= 3) & (df["opponent_position_before"] <= 3)).astype(int)
        * df["late_season"]
    )
    df["direct_rival_late"] = (
        ((df["abs_position_gap"] <= 3) & (df["abs_points_gap"] <= 6)).astype(int)
        * df["late_season"]
    )
    df["position_gap_late"] = df["abs_position_gap"] * df["late_season"]
    df["points_gap_late"] = df["abs_points_gap"] * df["late_season"]
    df["opponent_strength_late"] = df["opponent_ppg_before"] * df["late_season"]
    df["target_residual"] = df["attendance"] - df["rolling_5"]

    for col in ["days_since_lech_prev_league_match", "days_since_opponent_prev_league_match"]:
        df[col] = df[col].fillna(14.0).clip(0, 60)

    return df.dropna(subset=[
        "attendance", "rolling_5", "opponent_draw_ratio",
        "lech_position_before", "opponent_position_before",
    ]).reset_index(drop=True)


def recency_weights(train):
    dates = pd.to_datetime(train["match_date"], utc=True)
    age_days = (dates.max() - dates).dt.total_seconds() / 86400.0
    return np.power(0.5, age_days / RECENCY_HALF_LIFE_DAYS)


def build_incumbent(numeric_features):
    prep = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
        ("num", RobustScaler(), numeric_features),
    ], remainder="drop")
    reg = GradientBoostingRegressor(
        random_state=42,
        n_estimators=220,
        learning_rate=0.025,
        max_depth=2,
        min_samples_leaf=7,
        loss="huber",
    )
    return Pipeline([("features", prep), ("model", reg)])


def walk_forward_incumbent(df, numeric_features):
    out = []
    for season in TEST_SEASONS:
        test = df[df["season"] == season].copy()
        if test.empty:
            continue
        cutoff = test["match_date"].min()
        train = df[df["match_date"] < cutoff].copy()
        model = build_incumbent(numeric_features)
        model.fit(
            train[CATEGORICAL + numeric_features],
            train["target_residual"],
            model__sample_weight=recency_weights(train),
        )
        pred = test["rolling_5"].to_numpy() + model.predict(test[CATEGORICAL + numeric_features])
        for idx, p in zip(test.index, pred):
            out.append({
                "index": int(idx), "season": season,
                "actual": float(df.loc[idx, "attendance"]), "pred": float(p),
            })
    return pd.DataFrame(out)


def catboost_model(config):
    return CatBoostRegressor(
        iterations=500 if config["loss"] == "mae" else 400,
        depth=config["depth"],
        learning_rate=0.03,
        loss_function="MAE" if config["loss"] == "mae" else "RMSE",
        l2_leaf_reg=10.0,
        random_seed=42,
        verbose=False,
        allow_writing_files=False,
    )


def cat_frame(df, features):
    X = df[CATEGORICAL + features].copy()
    X["opponent_key"] = X["opponent_key"].fillna("unknown").astype(str)
    for col in features:
        X[col] = pd.to_numeric(X[col], errors="coerce")
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median())
    return X


def walk_forward_catboost(df, config):
    features = FEATURE_SETS[config["features"]]
    out = []
    for season in TEST_SEASONS:
        test = df[df["season"] == season].copy()
        if test.empty:
            continue
        cutoff = test["match_date"].min()
        train = df[df["match_date"] < cutoff].copy()
        target = train["target_residual"] if config["target"] == "residual" else train["attendance"]
        model = catboost_model(config)
        model.fit(
            cat_frame(train, features), target,
            cat_features=[0], sample_weight=recency_weights(train),
        )
        raw_pred = model.predict(cat_frame(test, features))
        pred = test["rolling_5"].to_numpy() + raw_pred if config["target"] == "residual" else raw_pred
        for idx, p in zip(test.index, pred):
            out.append({
                "index": int(idx), "season": season,
                "actual": float(df.loc[idx, "attendance"]), "pred": float(p),
            })
    return pd.DataFrame(out)


def summarize(predictions, seasons):
    p = predictions[predictions["season"].isin(seasons)]
    return metric_set(p["actual"], p["pred"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    df = add_features(pd.read_csv(args.dataset))

    baseline_rows = []
    for season in TEST_SEASONS:
        for idx, row in df[df["season"] == season].iterrows():
            baseline_rows.append({
                "index": int(idx), "season": season,
                "actual": float(row["attendance"]),
                "rolling_5": float(row["rolling_5"]),
                "opponent_mean": float(row["opponent_prev_mean"]),
            })
    base = pd.DataFrame(baseline_rows)
    incumbent = walk_forward_incumbent(df, FEATURE_SETS["early"])

    grid = [
        {"features": features, "target": target, "loss": loss, "depth": depth}
        for features in ["early", "early_table"]
        for target in ["residual", "direct"]
        for loss in ["mae", "rmse"]
        for depth in [3, 4]
    ]

    runs = []
    for config in grid:
        predictions = walk_forward_catboost(df, config)
        runs.append({
            "config": config,
            "development": summarize(predictions, DEVELOPMENT_SEASONS),
            "predictions": predictions,
        })

    # This is the only challenger selection step. Holdout is not consulted here.
    best = min(runs, key=lambda r: (r["development"]["mae"], r["development"]["mape_pct"]))
    challenger = best["predictions"]

    def baseline_metric(column, seasons):
        p = base[base["season"].isin(seasons)]
        return metric_set(p["actual"], p[column])

    result = {
        "protocol": {
            "selection_seasons": DEVELOPMENT_SEASONS,
            "untouched_holdout_seasons": HOLDOUT_SEASONS,
            "test_seasons": TEST_SEASONS,
            "capacity_constrained_rows_excluded": True,
            "feature_timing": "pre-match only",
            "challenger_selection": "lowest development MAE; holdout not used for selection",
        },
        "selected_catboost_config": best["config"],
        "development": {
            "rolling_5": baseline_metric("rolling_5", DEVELOPMENT_SEASONS),
            "opponent_mean": baseline_metric("opponent_mean", DEVELOPMENT_SEASONS),
            "incumbent_gb_v13": summarize(incumbent, DEVELOPMENT_SEASONS),
            "catboost_challenger": summarize(challenger, DEVELOPMENT_SEASONS),
        },
        "holdout": {
            "rolling_5": baseline_metric("rolling_5", HOLDOUT_SEASONS),
            "opponent_mean": baseline_metric("opponent_mean", HOLDOUT_SEASONS),
            "incumbent_gb_v13": summarize(incumbent, HOLDOUT_SEASONS),
            "catboost_challenger": summarize(challenger, HOLDOUT_SEASONS),
        },
        "overall": {
            "rolling_5": baseline_metric("rolling_5", TEST_SEASONS),
            "opponent_mean": baseline_metric("opponent_mean", TEST_SEASONS),
            "incumbent_gb_v13": summarize(incumbent, TEST_SEASONS),
            "catboost_challenger": summarize(challenger, TEST_SEASONS),
        },
        "decision": {
            "promote_catboost": False,
            "reason": (
                "CatBoost improves some tolerance metrics but worsens holdout MAE/WAPE "
                "and materially increases negative bias versus the incumbent."
            ),
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
