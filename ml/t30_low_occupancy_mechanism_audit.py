#!/usr/bin/env python3
"""Diagnose the stable T-30 low-occupancy underprediction regime.

The merged pre-validation audit identified `baseline_season / capacity <= 45%`
as the strongest repeated high-error regime. This script stays on the same two
rolling-origin development folds and asks a narrower question:

Which PIT-safe features consistently distinguish the most severely
underpredicted low-occupancy rows from the well-predicted low-occupancy rows?

No 2024/25 or 2025/26 rows are scored. No challenger is trained.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ml.demand_engine.structural_prior_runtime import feature_columns, fit_structural_prior_runtime
from ml.features.structural_prior_feature_store_v1 import WARSAW_TZ, build_feature_store

HORIZON = "T-30"
BASELINE = "baseline_season"
LOW_OCCUPANCY_MAX = 0.45
FORBIDDEN = {"2024/2025", "2025/2026"}
MIN_FINITE_PER_GROUP = 8
MIN_ABS_SMD_EACH_FOLD = 0.30


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


def evaluate_fold(store: pd.DataFrame, fold: Fold) -> pd.DataFrame:
    if fold.eval_season in FORBIDDEN or FORBIDDEN.intersection(fold.train_seasons):
        raise RuntimeError("Forbidden historical regression season requested")
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
    rows["baseline_occupancy_audit"] = (
        rows[BASELINE].astype(float) / rows["capacity"].astype(float)
    )
    return rows


def pooled_smd(a: pd.Series, b: pd.Series) -> dict | None:
    a = pd.to_numeric(a, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    b = pd.to_numeric(b, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if len(a) < MIN_FINITE_PER_GROUP or len(b) < MIN_FINITE_PER_GROUP:
        return None
    va = float(a.var(ddof=1)) if len(a) > 1 else 0.0
    vb = float(b.var(ddof=1)) if len(b) > 1 else 0.0
    pooled = np.sqrt((va + vb) / 2.0)
    mean_a = float(a.mean())
    mean_b = float(b.mean())
    if not np.isfinite(pooled) or pooled == 0:
        smd = 0.0 if np.isclose(mean_a, mean_b) else float(np.sign(mean_a - mean_b) * 99.0)
    else:
        smd = float((mean_a - mean_b) / pooled)
    return {
        "severe_n": int(len(a)),
        "well_n": int(len(b)),
        "severe_mean": mean_a,
        "well_mean": mean_b,
        "smd": smd,
    }


def group_definition(low: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    # Severe underprediction = bottom quartile of signed error inside the
    # low-occupancy regime. Well-predicted = lower half of absolute errors.
    q25_error = float(low["error"].quantile(0.25))
    median_abs = float(low["abs_error"].median())
    severe = low[low["error"] <= q25_error].copy()
    well = low[low["abs_error"] <= median_abs].copy()
    # By construction the groups should be largely disjoint. Remove accidental
    # overlap to keep the contrast interpretable.
    overlap = severe.index.intersection(well.index)
    if len(overlap):
        well = well.drop(index=overlap)
    return severe, well, {
        "low_occupancy_rows": int(len(low)),
        "severe_underprediction_error_q25": q25_error,
        "well_predicted_abs_error_median": median_abs,
        "severe_rows": int(len(severe)),
        "well_rows": int(len(well)),
        "overlap_removed": int(len(overlap)),
        "severe_error_mean": float(severe["error"].mean()),
        "well_error_mean": float(well["error"].mean()),
        "severe_abs_error_mean": float(severe["abs_error"].mean()),
        "well_abs_error_mean": float(well["abs_error"].mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-runtime",
        type=Path,
        default=Path("ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz"),
    )
    parser.add_argument("--output", type=Path, default=Path("/tmp/t30-low-occ-mechanism-audit.json"))
    args = parser.parse_args()

    store = build_feature_store(canonical_matches(args.historical_runtime))
    numeric = feature_columns(store, "full")

    fold_groups: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}
    group_meta = {}
    fold_feature_stats: dict[str, dict[str, dict]] = {}

    for fold in FOLDS:
        rows = evaluate_fold(store, fold)
        low = rows[rows["baseline_occupancy_audit"] <= LOW_OCCUPANCY_MAX].copy()
        severe, well, meta = group_definition(low)
        fold_groups[fold.name] = (severe, well)
        group_meta[fold.name] = meta
        stats = {}
        for column in numeric:
            result = pooled_smd(severe[column], well[column])
            if result is not None:
                stats[column] = result
        fold_feature_stats[fold.name] = stats

    common_features = set.intersection(*[set(values) for values in fold_feature_stats.values()])
    stable = []
    for feature in sorted(common_features):
        per_fold = {fold.name: fold_feature_stats[fold.name][feature] for fold in FOLDS}
        smds = [per_fold[fold.name]["smd"] for fold in FOLDS]
        same_direction = all(v > 0 for v in smds) or all(v < 0 for v in smds)
        clears_effect_gate = all(abs(v) >= MIN_ABS_SMD_EACH_FOLD for v in smds)
        if not (same_direction and clears_effect_gate):
            continue
        stable.append({
            "feature": feature,
            "folds": per_fold,
            "direction": "higher_in_severe" if all(v > 0 for v in smds) else "lower_in_severe",
            "min_abs_smd": float(min(abs(v) for v in smds)),
            "mean_abs_smd": float(np.mean([abs(v) for v in smds])),
        })

    stable.sort(key=lambda row: (-row["min_abs_smd"], -row["mean_abs_smd"], row["feature"]))

    # Pairwise mechanism hints for features already represented by meaningful
    # domain variables. These are descriptive only; they do not define a model.
    domain_focus = [
        "home_demand_vs_league_median",
        "opponent_draw_ratio_mean",
        "opponent_draw_ratio_recent3",
        "pair_ratio_mean",
        "home_ppg",
        "away_ppg",
        "combined_ppg",
        "home_position",
        "away_position",
        "combined_table_strength",
        "top4_any",
        "bottom4_any",
        "season_progress",
        "is_weekend",
        "home_attendance_mean",
        "home_attendance_rolling3",
        "season_home_mean",
        "prev_season_home_mean",
        "capacity",
    ]
    focused = [row for row in stable if row["feature"] in domain_focus]

    report = {
        "experiment": "t30-low-occupancy-mechanism-audit-v1",
        "runtime": "structural-prior-runtime-v1-t30-extra-full",
        "scope": "baseline_season / verified_capacity <= 45%",
        "governance": {
            "folds": [
                {"name": f.name, "train": list(f.train_seasons), "evaluate": f.eval_season}
                for f in FOLDS
            ],
            "historical_regression_seasons_scored": False,
            "challenger_trained": False,
            "production_mutation": False,
            "minimum_finite_per_group": MIN_FINITE_PER_GROUP,
            "stable_effect_gate_abs_smd_each_fold": MIN_ABS_SMD_EACH_FOLD,
        },
        "group_definition": group_meta,
        "stable_feature_differences": stable,
        "stable_domain_focus": focused,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": report["experiment"],
        "scope": report["scope"],
        "governance": report["governance"],
        "group_definition": group_meta,
        "stable_domain_focus": focused[:20],
        "top_stable_features": stable[:20],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
