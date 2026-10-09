#!/usr/bin/env python3
"""Benchmark Beyond probabilistic calibration v1.

Expected input columns:
- season
- actual
- pred  (point forecast / P50)
Optional:
- horizon
- stadium_capacity

Protocol:
- fit calibration only on development seasons;
- evaluate untouched holdout seasons;
- report empirical coverage, width, pinball and Winkler-style interval score;
- never tune on holdout.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml.demand_engine.calibration import fit_calibration_band

DEVELOPMENT_SEASONS = ["2022/2023", "2023/2024"]
HOLDOUT_SEASONS = ["2024/2025", "2025/2026"]
TARGET_COVERAGE = 0.80
ALPHA = 1.0 - TARGET_COVERAGE


def pinball(actual: np.ndarray, pred: np.ndarray, q: float) -> float:
    error = actual - pred
    return float(np.mean(np.maximum(q * error, (q - 1.0) * error)))


def interval_score(actual: np.ndarray, lower: np.ndarray, upper: np.ndarray, alpha: float) -> float:
    width = upper - lower
    below = np.maximum(lower - actual, 0.0)
    above = np.maximum(actual - upper, 0.0)
    return float(np.mean(width + (2.0 / alpha) * below + (2.0 / alpha) * above))


def evaluate(frame: pd.DataFrame, lower: np.ndarray, upper: np.ndarray) -> dict:
    actual = frame["actual"].astype(float).to_numpy()
    p50 = frame["pred"].astype(float).to_numpy()
    covered = (actual >= lower) & (actual <= upper)
    width = upper - lower
    return {
        "n": int(len(frame)),
        "coverage_pct": round(float(np.mean(covered) * 100.0), 2),
        "coverage_gap_pp": round(float((np.mean(covered) - TARGET_COVERAGE) * 100.0), 2),
        "mean_width": round(float(np.mean(width)), 2),
        "median_width": round(float(np.median(width)), 2),
        "pinball_p10": round(pinball(actual, lower, 0.10), 2),
        "pinball_p50": round(pinball(actual, p50, 0.50), 2),
        "pinball_p90": round(pinball(actual, upper, 0.90), 2),
        "interval_score_80": round(interval_score(actual, lower, upper, ALPHA), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--min-horizon-rows", type=int, default=20)
    args = parser.parse_args()

    frame = pd.read_csv(args.predictions)
    required = {"season", "actual", "pred"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"Missing prediction columns: {missing}")

    frame = frame.dropna(subset=["season", "actual", "pred"]).copy()
    dev = frame[frame["season"].isin(DEVELOPMENT_SEASONS)].copy()
    holdout = frame[frame["season"].isin(HOLDOUT_SEASONS)].copy()
    if dev.empty:
        raise RuntimeError("No development-season rows available for calibration")
    if holdout.empty:
        raise RuntimeError("No holdout-season rows available for evaluation")

    rows = [
        {
            "actual": row.actual,
            "p50": row.pred,
            "horizon": getattr(row, "horizon", None),
        }
        for row in dev.itertuples(index=False)
    ]
    band = fit_calibration_band(
        rows,
        calibration_version="split-conformal-80-v1",
        coverage=TARGET_COVERAGE,
        min_horizon_rows=args.min_horizon_rows,
    )

    lowers = []
    uppers = []
    sources = []
    for row in holdout.itertuples(index=False):
        capacity = getattr(row, "stadium_capacity", None)
        if pd.isna(capacity):
            capacity = None
        horizon = getattr(row, "horizon", None)
        if pd.isna(horizon):
            horizon = None
        lower, upper, source = band.interval(
            float(row.pred),
            horizon=str(horizon) if horizon else None,
            capacity=float(capacity) if capacity is not None else None,
        )
        lowers.append(lower)
        uppers.append(upper)
        sources.append(source)

    lower_arr = np.asarray(lowers, dtype=float)
    upper_arr = np.asarray(uppers, dtype=float)

    report = {
        "benchmark_version": "calibration-v1",
        "method": "split_conformal_absolute_residual_80",
        "calibration_seasons": DEVELOPMENT_SEASONS,
        "holdout_seasons": HOLDOUT_SEASONS,
        "target_coverage_pct": 80.0,
        "calibration_rows": band.calibration_rows,
        "global_radius": round(band.global_radius, 2),
        "horizon_radius": {k: round(v, 2) for k, v in band.horizon_radius.items()},
        "min_horizon_rows": band.min_horizon_rows,
        "holdout": evaluate(holdout, lower_arr, upper_arr),
        "source_usage": dict(pd.Series(sources).value_counts()),
        "by_season": {},
    }

    for season in HOLDOUT_SEASONS:
        mask = holdout["season"].to_numpy() == season
        if np.any(mask):
            report["by_season"][season] = evaluate(
                holdout.loc[mask], lower_arr[mask], upper_arr[mask]
            )

    if "horizon" in holdout.columns:
        report["by_horizon"] = {}
        for horizon in sorted(holdout["horizon"].dropna().astype(str).unique()):
            mask = holdout["horizon"].astype(str).to_numpy() == horizon
            report["by_horizon"][horizon] = evaluate(
                holdout.loc[mask], lower_arr[mask], upper_arr[mask]
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
