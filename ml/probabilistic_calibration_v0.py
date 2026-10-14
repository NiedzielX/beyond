#!/usr/bin/env python3
"""Leakage-safe empirical P10/P90 calibration for Global Model v2.1.

The script consumes the canonical point-in-time Feature Store CSV used by
`global_model_v21_benchmark.py`. It keeps the P50 architecture unchanged and
calibrates an empirical signed-residual interval using only earlier
out-of-sample seasons.

This is a probabilistic baseline, not the final conditional quantile model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml.global_model_v21_benchmark import (
    CAT,
    DEV_SEASON,
    DEV_TRAIN_SEASONS,
    clean_frame,
    factories,
    fit_residual,
    metrics,
    numeric_features,
    predict_attendance,
)

HORIZONS = ["T-30d", "T-14d", "T-7d", "T-3d", "T-1d"]


def select_family(data: pd.DataFrame, numeric: list[str]) -> tuple[str, dict]:
    train = data[data["season"].isin(DEV_TRAIN_SEASONS)]
    dev = data[data["season"] == DEV_SEASON]
    results = {}
    model_factories = factories(numeric)
    for name, factory in model_factories.items():
        model = fit_residual(factory(), train, numeric)
        prediction = predict_attendance(model, dev, numeric)
        results[name] = metrics(dev["target_attendance"], prediction)
    winner = min(
        results,
        key=lambda name: (
            results[name]["mae"],
            results[name]["wape_pct"],
            abs(results[name]["bias"]),
        ),
    )
    return winner, results


def oos_predictions(
    data: pd.DataFrame,
    numeric: list[str],
    family: str,
    train_seasons: list[str],
    test_season: str,
) -> pd.DataFrame:
    factory = factories(numeric)[family]
    train = data[data["season"].isin(train_seasons)]
    test = data[data["season"] == test_season].copy()
    model = fit_residual(factory(), train, numeric)
    prediction = predict_attendance(model, test, numeric)
    out = test[["match_key", "target_attendance"]].copy()
    out["p50"] = prediction
    out["residual"] = out["target_attendance"].astype(float) - out["p50"]
    return out


def interval_metrics(frame: pd.DataFrame) -> dict:
    actual = frame["target_attendance"].astype(float).to_numpy()
    p10 = frame["p10"].astype(float).to_numpy()
    p50 = frame["p50"].astype(float).to_numpy()
    p90 = frame["p90"].astype(float).to_numpy()
    covered = (actual >= p10) & (actual <= p90)
    below = actual < p10
    above = actual > p90
    return {
        "n": int(len(frame)),
        "coverage_pct": round(float(np.mean(covered) * 100.0), 4),
        "lower_miss_pct": round(float(np.mean(below) * 100.0), 4),
        "upper_miss_pct": round(float(np.mean(above) * 100.0), 4),
        "avg_interval_width": round(float(np.mean(p90 - p10)), 4),
        "median_interval_width": round(float(np.median(p90 - p10)), 4),
        "p50": metrics(actual, p50),
    }


def apply_interval(pred: pd.DataFrame, q10: float, q90: float) -> pd.DataFrame:
    out = pred.copy()
    out["p10"] = np.maximum(0.0, out["p50"].astype(float) + q10)
    out["p90"] = np.maximum(out["p10"], out["p50"].astype(float) + q90)
    return out


def evaluate_horizon(frame: pd.DataFrame, horizon: str, numeric: list[str]) -> dict:
    data = frame[frame["horizon"] == horizon].copy()
    family, development = select_family(data, numeric)

    # Calibration residuals for 2024/25 come solely from 2023/24 OOS predictions.
    dev_oos = oos_predictions(
        data,
        numeric,
        family,
        DEV_TRAIN_SEASONS,
        "2023/2024",
    )
    q10_2024 = float(dev_oos["residual"].quantile(0.10))
    q90_2024 = float(dev_oos["residual"].quantile(0.90))

    pred_2024 = oos_predictions(
        data,
        numeric,
        family,
        ["2021/2022", "2022/2023", "2023/2024"],
        "2024/2025",
    )
    interval_2024 = apply_interval(pred_2024, q10_2024, q90_2024)

    # 2025/26 calibration may use prior OOS residuals from 2023/24 + 2024/25,
    # but never any 2025/26 outcome.
    calibration_2025 = pd.concat(
        [dev_oos[["residual"]], pred_2024[["residual"]]], ignore_index=True
    )
    q10_2025 = float(calibration_2025["residual"].quantile(0.10))
    q90_2025 = float(calibration_2025["residual"].quantile(0.90))

    pred_2025 = oos_predictions(
        data,
        numeric,
        family,
        ["2021/2022", "2022/2023", "2023/2024", "2024/2025"],
        "2025/2026",
    )
    interval_2025 = apply_interval(pred_2025, q10_2025, q90_2025)

    return {
        "selected_model": family,
        "development_models": development,
        "2024/2025": {
            "calibration_source": ["2023/2024"],
            "residual_q10": round(q10_2024, 4),
            "residual_q90": round(q90_2024, 4),
            **interval_metrics(interval_2024),
        },
        "2025/2026": {
            "calibration_source": ["2023/2024", "2024/2025"],
            "residual_q10": round(q10_2025, 4),
            "residual_q90": round(q90_2025, 4),
            **interval_metrics(interval_2025),
        },
    }


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Probabilistic Calibration v0",
        "",
        "Nominal P10-P90 target coverage: **80%**.",
        "",
        "| Horizon | Model | 2024/25 coverage | 2024/25 width | 2025/26 coverage | 2025/26 width |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for horizon in HORIZONS:
        result = report["horizons"][horizon]
        a = result["2024/2025"]
        b = result["2025/2026"]
        lines.append(
            f"| {horizon} | {result['selected_model']} | {a['coverage_pct']:.1f}% | "
            f"{a['avg_interval_width']:.0f} | {b['coverage_pct']:.1f}% | "
            f"{b['avg_interval_width']:.0f} |"
        )
    lines += [
        "",
        "Intervals are calibrated from signed residuals of earlier OOS seasons only.",
        "No target-season outcome is used to calibrate its own interval.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    raw = pd.read_csv(args.feature_store)
    frame = clean_frame(raw)
    numeric = numeric_features(frame)
    report = {
        "calibration_version": "probabilistic-calibration-v0",
        "point_model": "Global Model v2.1",
        "nominal_coverage_pct": 80.0,
        "method": "empirical signed OOS residual q10/q90",
        "automatic_promotion": False,
        "horizons": {
            horizon: evaluate_horizon(frame, horizon, numeric)
            for horizon in HORIZONS
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.markdown_output:
        write_markdown(report, args.markdown_output)
    print(json.dumps({
        horizon: {
            season: {
                "coverage_pct": result[season]["coverage_pct"],
                "avg_interval_width": result[season]["avg_interval_width"],
                "lower_miss_pct": result[season]["lower_miss_pct"],
                "upper_miss_pct": result[season]["upper_miss_pct"],
            }
            for season in ["2024/2025", "2025/2026"]
        }
        for horizon, result in report["horizons"].items()
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
