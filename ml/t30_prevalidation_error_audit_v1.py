#!/usr/bin/env python3
"""Pre-validation-only error audit for the current production T-30 runtime.

Purpose: find structural residual patterns that repeat across two rolling-origin
folds before defining another challenger family.

This script never scores 2024/25 or 2025/26 and never mutates production.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ml.demand_engine.structural_prior_runtime import fit_structural_prior_runtime
from ml.features.structural_prior_feature_store_v1 import WARSAW_TZ, build_feature_store

HORIZON = "T-30"
BASELINE = "baseline_season"
FORBIDDEN = {"2024/2025", "2025/2026"}
MIN_BUCKET_N_PER_FOLD = 15


@dataclass(frozen=True)
class Fold:
    name: str
    train_seasons: tuple[str, ...]
    eval_season: str


FOLDS = (
    Fold("A", ("2021/2022",), "2022/2023"),
    Fold("B", ("2021/2022", "2022/2023"), "2023/2024"),
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
    frame["training_eligible"] = frame["attendance"].astype(float) != 0
    frame["round"] = frame["round"].astype(int)
    return frame.sort_values(["kickoff_at", "home_club_key"]).reset_index(drop=True)


def num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def add_audit_buckets(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    season_n = num(out["season_home_n"]).fillna(0)
    history_n = num(out["home_history_n"]).fillna(0)
    opp_n = num(out["opponent_draw_n"]).fillna(0)
    pair_n = num(out["pair_n"]).fillna(0)
    progress = num(out["season_progress"])
    capacity = num(out["capacity"])
    baseline = num(out[BASELINE])
    home_pos = num(out["home_position"])
    away_pos = num(out["away_position"])

    out["bucket_season_home_n"] = pd.cut(
        season_n,
        bins=[-0.1, 0.5, 2.5, 5.5, np.inf],
        labels=["0", "1-2", "3-5", "6+"],
    ).astype(str)
    out["bucket_home_history_n"] = pd.cut(
        history_n,
        bins=[-0.1, 5.5, 10.5, 20.5, np.inf],
        labels=["0-5", "6-10", "11-20", "21+"],
    ).astype(str)
    out["bucket_opponent_draw_n"] = pd.cut(
        opp_n,
        bins=[-0.1, 0.5, 2.5, np.inf],
        labels=["0", "1-2", "3+"],
    ).astype(str)
    out["bucket_pair_n"] = np.where(pair_n > 0, "1+", "0")
    out["bucket_season_phase"] = pd.cut(
        progress,
        bins=[-np.inf, 1 / 3, 2 / 3, np.inf],
        labels=["early", "mid", "late"],
    ).astype(str)
    out["bucket_capacity"] = pd.cut(
        capacity,
        bins=[0, 15000, 25000, 35000, np.inf],
        labels=["<=15k", "15-25k", "25-35k", "35k+"],
        include_lowest=True,
    ).astype(str)
    occupancy = baseline / capacity
    out["bucket_baseline_occupancy"] = pd.cut(
        occupancy,
        bins=[-np.inf, 0.45, 0.65, 0.85, np.inf],
        labels=["<=45%", "45-65%", "65-85%", "85%+"],
    ).astype(str)
    out["bucket_home_position"] = np.select(
        [home_pos <= 4, home_pos >= 15, home_pos.notna()],
        ["top4", "bottom4", "mid"],
        default="unknown",
    )
    out["bucket_away_position"] = np.select(
        [away_pos <= 4, away_pos >= 15, away_pos.notna()],
        ["top4", "bottom4", "mid"],
        default="unknown",
    )
    out["bucket_top4_any"] = np.where(num(out["top4_any"]).fillna(0) > 0, "yes", "no")
    out["bucket_bottom4_any"] = np.where(num(out["bottom4_any"]).fillna(0) > 0, "yes", "no")
    out["bucket_weekend"] = np.where(num(out["is_weekend"]).fillna(0) > 0, "weekend", "weekday")

    if "home_demand_vs_league_median" in out.columns:
        demand = num(out["home_demand_vs_league_median"])
        out["bucket_home_demand"] = pd.cut(
            demand,
            bins=[-np.inf, 0.75, 1.0, 1.35, np.inf],
            labels=["low", "below_med", "above_med", "high"],
        ).astype(str)
    else:
        out["bucket_home_demand"] = "unknown"

    return out


def metrics(group: pd.DataFrame) -> dict:
    error = group["error"].astype(float).to_numpy()
    actual = group["target_attendance"].astype(float).to_numpy()
    ae = np.abs(error)
    return {
        "n": int(len(group)),
        "mae": float(np.mean(ae)),
        "median_ae": float(np.median(ae)),
        "bias": float(np.mean(error)),
        "wape": float(np.sum(ae) / np.sum(actual)),
        "overprediction_rate": float(np.mean(error > 0)),
    }


def evaluate_fold(store: pd.DataFrame, fold: Fold) -> pd.DataFrame:
    if fold.eval_season in FORBIDDEN or FORBIDDEN.intersection(fold.train_seasons):
        raise RuntimeError("Forbidden historical regression season in audit fold")
    rows = store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & (store["season"] == fold.eval_season)
        & store[BASELINE].notna()
    ].copy()
    runtime = fit_structural_prior_runtime(store, HORIZON, list(fold.train_seasons))
    prediction = runtime.predict(rows)
    rows["prediction"] = prediction
    rows["error"] = prediction - rows["target_attendance"].astype(float).to_numpy()
    rows["abs_error"] = np.abs(rows["error"])
    rows["fold"] = fold.name
    return add_audit_buckets(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-runtime",
        type=Path,
        default=Path("ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz"),
    )
    parser.add_argument("--output", type=Path, default=Path("/tmp/t30-prevalidation-error-audit-v1.json"))
    args = parser.parse_args()

    store = build_feature_store(canonical_matches(args.historical_runtime))
    fold_frames = {fold.name: evaluate_fold(store, fold) for fold in FOLDS}
    overall = {name: metrics(frame) for name, frame in fold_frames.items()}

    dimensions = [
        "bucket_season_home_n",
        "bucket_home_history_n",
        "bucket_opponent_draw_n",
        "bucket_pair_n",
        "bucket_season_phase",
        "bucket_capacity",
        "bucket_baseline_occupancy",
        "bucket_home_position",
        "bucket_away_position",
        "bucket_top4_any",
        "bucket_bottom4_any",
        "bucket_weekend",
        "bucket_home_demand",
    ]

    segments = []
    for dimension in dimensions:
        values = sorted(set().union(*[set(frame[dimension].dropna().astype(str)) for frame in fold_frames.values()]))
        for value in values:
            per_fold = {}
            valid = True
            for fold_name, frame in fold_frames.items():
                group = frame[frame[dimension].astype(str) == value]
                if len(group) < MIN_BUCKET_N_PER_FOLD:
                    valid = False
                    break
                m = metrics(group)
                m["mae_ratio_vs_fold"] = m["mae"] / overall[fold_name]["mae"]
                per_fold[fold_name] = m
            if not valid:
                continue

            biases = [per_fold[name]["bias"] for name in sorted(per_fold)]
            mae_ratios = [per_fold[name]["mae_ratio_vs_fold"] for name in sorted(per_fold)]
            stable_bias_sign = all(x > 0 for x in biases) or all(x < 0 for x in biases)
            stable_high_error = all(x >= 1.10 for x in mae_ratios)
            stable_low_error = all(x <= 0.90 for x in mae_ratios)
            min_abs_bias = min(abs(x) for x in biases)
            mean_mae_ratio = float(np.mean(mae_ratios))

            segments.append({
                "dimension": dimension,
                "value": value,
                "folds": per_fold,
                "stable_bias_sign": stable_bias_sign,
                "stable_high_error": stable_high_error,
                "stable_low_error": stable_low_error,
                "min_abs_bias": min_abs_bias,
                "mean_mae_ratio": mean_mae_ratio,
                "priority_score": (
                    max(0.0, mean_mae_ratio - 1.0) * 1000.0
                    + (min_abs_bias if stable_bias_sign else 0.0)
                ),
            })

    stable = [
        item for item in segments
        if item["stable_high_error"] or (item["stable_bias_sign"] and item["min_abs_bias"] >= 350)
    ]
    stable.sort(key=lambda item: (-item["priority_score"], item["dimension"], item["value"]))

    # Also report strongest stable under/over-prediction groups independently of MAE.
    stable_bias = [item for item in segments if item["stable_bias_sign"]]
    stable_bias.sort(key=lambda item: (-item["min_abs_bias"], item["dimension"], item["value"]))

    report = {
        "experiment": "t30-prevalidation-error-audit-v1",
        "runtime": "structural-prior-runtime-v1-t30-extra-full",
        "governance": {
            "folds": [
                {"name": f.name, "train": list(f.train_seasons), "evaluate": f.eval_season}
                for f in FOLDS
            ],
            "historical_regression_seasons_scored": False,
            "minimum_bucket_n_per_fold": MIN_BUCKET_N_PER_FOLD,
            "production_mutation": False,
        },
        "overall": overall,
        "stable_priority_segments": stable[:20],
        "strongest_stable_bias_segments": stable_bias[:20],
        "all_eligible_segments": segments,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": report["experiment"],
        "governance": report["governance"],
        "overall": overall,
        "stable_priority_segments": report["stable_priority_segments"],
        "strongest_stable_bias_segments": report["strongest_stable_bias_segments"][:10],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
