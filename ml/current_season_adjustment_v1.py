#!/usr/bin/env python3
"""Evaluate an explicit current-season adjustment on top of Structural Prior.

Goal: strengthen b) Aktualny sezon without changing the frozen production model.

The frozen Structural Prior is fitted and scored on the canonical feature store
*before* challenger-only current-season columns are added. This prevents the
challenger experiment from silently changing the incumbent feature contract.

Selection protocol:
- choose one fixed adjustment variant per horizon on 2023/24 development only;
- choose NO_ADJUSTMENT when no non-zero variant beats the incumbent on development;
- freeze that choice;
- evaluate unchanged on 2024/25 and 2025/26 rolling holdouts;
- hard-fail if incumbent holdout MAE does not reproduce the frozen benchmark;
- no automatic promotion.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from ml.demand_engine.freeze_structural_prior_artifacts import (
    EXPECTED_HOLDOUT_MAE,
    _canonical_matches,
)
from ml.demand_engine.structural_prior_runtime import fit_structural_prior_runtime
from ml.features.structural_prior_feature_store_v1 import build_feature_store, quality_report

DEV_TRAIN = ["2021/2022", "2022/2023"]
DEV_SEASON = "2023/2024"
HOLDOUTS = [
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]
HORIZONS = ["T-30", "T-14", "T-7", "T-3", "T-1"]
MIN_CURRENT_SEASON_HOME_MATCHES = 2
MAX_ADJUSTMENT_SHARE_OF_CAPACITY = 0.20
BENCHMARK_ATOL = 1e-6


@dataclass(frozen=True)
class AdjustmentVariant:
    source: Literal["season_mean", "season_r3"]
    shrink_k: int
    alpha: float

    @property
    def id(self) -> str:
        return f"{self.source}-k{self.shrink_k}-a{int(round(self.alpha * 100)):02d}"


VARIANTS = [
    AdjustmentVariant(source=source, shrink_k=shrink_k, alpha=alpha)
    for source in ("season_mean", "season_r3")
    for shrink_k in (2, 4, 6)
    for alpha in (0.25, 0.50, 0.75)
]


def _historical_rows(path: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(path)
    rows: list[dict[str, Any]] = []
    for row in frame.to_dict("records"):
        rows.append({
            "dataset_version": "committed-frozen-runtime-input",
            "season": row["season"],
            "round_no": int(row["round"]),
            "match_date": row["date"],
            "kickoff_time_local": row["kickoff_time_local"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "home_club_key": row["home_club_key"],
            "away_club_key": row["away_club_key"],
            "home_goals": int(row["home_goals"]),
            "away_goals": int(row["away_goals"]),
            "attendance": int(row["attendance"]),
            "default_demand_training_eligible": int(row["attendance"]) != 0,
            "match_key": row["match_key"],
        })
    return rows


def load_feature_store(path: Path) -> pd.DataFrame:
    matches = _canonical_matches(_historical_rows(path))
    store = build_feature_store(matches)
    report = quality_report(store)
    if report["status"] != "PASS":
        raise RuntimeError(f"feature store quality failed: {report}")
    return store


def add_current_season_signals(frame: pd.DataFrame) -> pd.DataFrame:
    """Add challenger-only signals after incumbent prediction is already fixed."""
    out = frame.copy().reset_index(drop=True)
    history_n = out["home_history_n"].astype(float)
    season_n = out["season_home_n"].fillna(0).astype(float)
    history_mean = out["home_attendance_mean"].astype(float)
    season_mean = out["season_home_mean"].astype(float)

    prior_n = history_n - season_n
    prior_sum = history_mean * history_n - season_mean.fillna(0.0) * season_n
    prior_mean = pd.Series(np.nan, index=out.index, dtype=float)
    valid = prior_n > 0
    prior_mean.loc[valid] = prior_sum.loc[valid] / prior_n.loc[valid]

    prior_mean = prior_mean.fillna(out["prev_season_home_mean"].astype(float))
    prior_mean = prior_mean.fillna(history_mean)

    out["current_season_prior_home_mean"] = prior_mean
    out["current_season_prior_home_n"] = prior_n.clip(lower=0.0)
    out["current_season_mean_delta"] = season_mean - prior_mean
    out["current_season_mean_ratio"] = season_mean / prior_mean.replace(0.0, np.nan)
    out["current_season_r3_delta"] = out["season_home_r3"].astype(float) - prior_mean
    out["current_season_r3_ratio"] = (
        out["season_home_r3"].astype(float) / prior_mean.replace(0.0, np.nan)
    )
    return out


def metrics(actual: pd.Series | np.ndarray, prediction: np.ndarray) -> dict[str, float | int]:
    actual_values = np.asarray(actual, dtype=float)
    prediction_values = np.asarray(prediction, dtype=float)
    ae = np.abs(prediction_values - actual_values)
    return {
        "n": int(len(actual_values)),
        "mae": float(np.mean(ae)),
        "median_ae": float(np.median(ae)),
        "wape": float(np.sum(ae) / np.sum(actual_values)),
        "bias": float(np.mean(prediction_values - actual_values)),
    }


def eligible(frame: pd.DataFrame, horizon: str, season: str) -> pd.DataFrame:
    return frame[
        (frame["horizon"].astype(str) == horizon)
        & frame["training_eligible"].astype(bool)
        & (frame["season"] == season)
    ].copy().reset_index(drop=True)


def current_level(rows: pd.DataFrame, variant: AdjustmentVariant) -> np.ndarray:
    if variant.source == "season_mean":
        return rows["season_home_mean"].astype(float).to_numpy()
    return rows["season_home_r3"].astype(float).to_numpy()


def adjustment_signal(rows: pd.DataFrame, variant: AdjustmentVariant) -> tuple[np.ndarray, np.ndarray]:
    season_n = rows["season_home_n"].fillna(0).astype(float).to_numpy()
    prior = rows["current_season_prior_home_mean"].astype(float).to_numpy()
    current = current_level(rows, variant)

    reliable = (
        (season_n >= MIN_CURRENT_SEASON_HOME_MATCHES)
        & np.isfinite(prior)
        & np.isfinite(current)
    )
    shrink = np.where(reliable, season_n / (season_n + float(variant.shrink_k)), 0.0)
    raw_delta = np.where(reliable, shrink * (current - prior), 0.0)
    cap = rows["capacity"].astype(float).to_numpy() * MAX_ADJUSTMENT_SHARE_OF_CAPACITY
    bounded = np.clip(raw_delta, -cap, cap)
    return variant.alpha * bounded, reliable


def apply_adjustment(
    rows: pd.DataFrame,
    incumbent_prediction: np.ndarray,
    variant: AdjustmentVariant,
) -> tuple[np.ndarray, dict[str, Any]]:
    delta, reliable = adjustment_signal(rows, variant)
    capacity = rows["capacity"].astype(float).to_numpy()
    adjusted = np.clip(np.asarray(incumbent_prediction, dtype=float) + delta, 0.0, capacity)
    return adjusted, {
        "eligible_adjustment_rows": int(np.sum(reliable)),
        "eligible_adjustment_share": float(np.mean(reliable)) if len(reliable) else 0.0,
        "mean_abs_applied_adjustment": float(np.mean(np.abs(delta))) if len(delta) else 0.0,
        "median_abs_applied_adjustment": float(np.median(np.abs(delta))) if len(delta) else 0.0,
        "max_abs_applied_adjustment": float(np.max(np.abs(delta))) if len(delta) else 0.0,
    }


def no_adjustment_result(
    rows: pd.DataFrame,
    incumbent_prediction: np.ndarray,
    incumbent_metrics: dict[str, float | int],
) -> dict[str, Any]:
    return {
        "variant": "NO_ADJUSTMENT",
        "config": None,
        "metrics": incumbent_metrics,
        "diagnostics": {
            "eligible_adjustment_rows": 0,
            "eligible_adjustment_share": 0.0,
            "mean_abs_applied_adjustment": 0.0,
            "median_abs_applied_adjustment": 0.0,
            "max_abs_applied_adjustment": 0.0,
        },
        "prediction": np.asarray(incumbent_prediction, dtype=float),
    }


def score_variant(
    rows: pd.DataFrame,
    incumbent_prediction: np.ndarray,
    variant: AdjustmentVariant,
) -> dict[str, Any]:
    adjusted, diagnostics = apply_adjustment(rows, incumbent_prediction, variant)
    return {
        "variant": variant.id,
        "config": asdict(variant),
        "metrics": metrics(rows["target_attendance"], adjusted),
        "diagnostics": diagnostics,
        "prediction": adjusted,
    }


def public_result(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "prediction"}


def verify_frozen_incumbent(horizon: str, season: str, value: float) -> None:
    expected = float(EXPECTED_HOLDOUT_MAE[horizon][season])
    if not np.isclose(value, expected, rtol=0.0, atol=BENCHMARK_ATOL):
        raise RuntimeError(
            f"incumbent benchmark mismatch {horizon}/{season}: actual={value} expected={expected}"
        )


def evaluate_horizon(frame: pd.DataFrame, horizon: str) -> dict[str, Any]:
    # Fit incumbent on the untouched canonical store. Challenger-only columns are
    # intentionally absent here so the incumbent feature contract cannot change.
    development_model = fit_structural_prior_runtime(frame, horizon, DEV_TRAIN)
    development_base = eligible(frame, horizon, DEV_SEASON)
    development_base = development_base[
        development_base[development_model.spec.baseline_column].notna()
    ].copy().reset_index(drop=True)
    dev_incumbent = development_model.predict(development_base)
    dev_incumbent_metrics = metrics(development_base["target_attendance"], dev_incumbent)
    development = add_current_season_signals(development_base)

    nonzero_candidates = [
        score_variant(development, dev_incumbent, variant) for variant in VARIANTS
    ]
    best_nonzero = min(
        nonzero_candidates,
        key=lambda row: (row["metrics"]["mae"], row["variant"]),
    )
    no_adjustment = no_adjustment_result(development, dev_incumbent, dev_incumbent_metrics)
    selected = min(
        [no_adjustment, *nonzero_candidates],
        key=lambda row: (row["metrics"]["mae"], row["variant"]),
    )
    selected_variant = None
    if selected["variant"] != "NO_ADJUSTMENT":
        selected_variant = next(
            variant for variant in VARIANTS if variant.id == selected["variant"]
        )

    holdout_results: dict[str, Any] = {}
    for test_season, train_seasons in HOLDOUTS:
        model = fit_structural_prior_runtime(frame, horizon, train_seasons)
        test_base = eligible(frame, horizon, test_season)
        test_base = test_base[test_base[model.spec.baseline_column].notna()].copy().reset_index(drop=True)
        incumbent_prediction = model.predict(test_base)
        incumbent_metrics = metrics(test_base["target_attendance"], incumbent_prediction)
        verify_frozen_incumbent(horizon, test_season, float(incumbent_metrics["mae"]))
        test = add_current_season_signals(test_base)

        if selected_variant is None:
            adjusted_prediction = incumbent_prediction
            diagnostics = no_adjustment_result(
                test, incumbent_prediction, incumbent_metrics
            )["diagnostics"]
        else:
            adjusted_prediction, diagnostics = apply_adjustment(
                test, incumbent_prediction, selected_variant
            )
        adjusted_metrics = metrics(test["target_attendance"], adjusted_prediction)
        holdout_results[test_season] = {
            "training_seasons": train_seasons,
            "incumbent": incumbent_metrics,
            "adjusted": adjusted_metrics,
            "mae_delta_vs_incumbent": incumbent_metrics["mae"] - adjusted_metrics["mae"],
            "diagnostics": diagnostics,
        }

    holdout_deltas = [row["mae_delta_vs_incumbent"] for row in holdout_results.values()]
    incumbent_mean = float(np.mean([row["incumbent"]["mae"] for row in holdout_results.values()]))
    adjusted_mean = float(np.mean([row["adjusted"]["mae"] for row in holdout_results.values()]))

    if selected_variant is None:
        signal = "NO_ADJUSTMENT_SELECTED"
    elif all(delta > 0 for delta in holdout_deltas):
        signal = "PROMISING_CONSISTENT_HOLDOUT_IMPROVEMENT"
    elif adjusted_mean < incumbent_mean:
        signal = "MIXED_BUT_POSITIVE_MEAN"
    else:
        signal = "NOT_PROVEN"

    return {
        "horizon": horizon,
        "incumbent_model_spec_id": development_model.spec.model_spec_id,
        "development": {
            "season": DEV_SEASON,
            "training_seasons": DEV_TRAIN,
            "incumbent": dev_incumbent_metrics,
            "selected_variant": public_result(selected),
            "best_nonzero_variant": public_result(best_nonzero),
            "candidate_count": len(VARIANTS),
            "top_nonzero_candidates": [
                public_result(row)
                for row in sorted(
                    nonzero_candidates,
                    key=lambda row: row["metrics"]["mae"],
                )[:5]
            ],
        },
        "holdouts": holdout_results,
        "mean_holdout_incumbent_mae": incumbent_mean,
        "mean_holdout_adjusted_mae": adjusted_mean,
        "mean_holdout_mae_delta": incumbent_mean - adjusted_mean,
        "signal": signal,
        "automatic_promotion": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frame = load_feature_store(args.historical_runtime)
    results = [evaluate_horizon(frame, horizon) for horizon in HORIZONS]

    consistent = [
        row for row in results
        if row["signal"] == "PROMISING_CONSISTENT_HOLDOUT_IMPROVEMENT"
    ]
    positive_mean = [
        row for row in results
        if row["mean_holdout_mae_delta"] > BENCHMARK_ATOL
    ]

    report = {
        "experiment": "current-season-adjustment-v1",
        "workstream": "b) Aktualny sezon — wzmocnić",
        "dataset": "committed-frozen-runtime-input / five Ekstraklasa seasons",
        "protocol": {
            "development_train": DEV_TRAIN,
            "development_selection": DEV_SEASON,
            "holdouts": [season for season, _ in HOLDOUTS],
            "minimum_current_season_home_matches": MIN_CURRENT_SEASON_HOME_MATCHES,
            "max_adjustment_share_of_capacity": MAX_ADJUSTMENT_SHARE_OF_CAPACITY,
            "candidate_variants": len(VARIANTS),
            "no_adjustment_candidate": True,
            "frozen_incumbent_benchmark_asserted": True,
            "point_in_time_safe": True,
            "automatic_promotion": False,
            "production_changed": False,
        },
        "horizons": results,
        "summary": {
            "consistent_holdout_improvement_horizons": [row["horizon"] for row in consistent],
            "positive_mean_holdout_improvement_horizons": [row["horizon"] for row in positive_mean],
            "no_adjustment_selected_horizons": [
                row["horizon"] for row in results
                if row["signal"] == "NO_ADJUSTMENT_SELECTED"
            ],
            "all_horizons_consistent": len(consistent) == len(HORIZONS),
            "promotion_allowed": False,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
