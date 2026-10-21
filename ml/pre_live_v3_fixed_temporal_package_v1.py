#!/usr/bin/env python3
"""Fixed-temporal audit for the exact mixed-horizon Pre-Live v3 package.

No tuning occurs here. T-30 and T-7 use the exact contracts selected by
pre-live-v3-regime-revalidation-v1. T-14/T-3/T-1 reproduce Frozen Pre-Live v2.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.a2_external_ensemble_fixed_temporal_v1 import (
    LARGE_DEGRADATION_THRESHOLDS,
    paired_bootstrap_improvement,
)
from ml.current_season_regime_maturity_stage2_v1 import apply_activation_threshold
from ml.current_season_residual_regime_v1 import RegimeVariant, add_same_season_residual_state
from ml.pre_live_baseline_optimization_v1 import comparison_scorecard, load_feature_store, metrics, sha256_file
from ml.pre_live_v2_historical_freeze_v1 import EXPECTED_FINAL_MAE as FROZEN_V2_EXPECTED_MAE
from ml.pre_live_v3_regime_revalidation_v1 import (
    HORIZONS,
    frozen_v2_for_season,
    v3_historical_base_for_season,
)

EXPERIMENT = "pre-live-v3-fixed-temporal-package-v1"
WORKSTREAM = "Pre-Live v3 — fixed-temporal mixed-horizon package audit"
RANDOM_SEED = 42
BOOTSTRAP_SAMPLES = 10_000
EXPECTED_ATOL = 1e-9

FOLDS = [
    ("2022/2023", ["2021/2022"]),
    ("2023/2024", ["2021/2022", "2022/2023"]),
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]

CHANGED_HORIZONS = ("T-30", "T-7")
UNCHANGED_HORIZONS = ("T-14", "T-3", "T-1")
T7_VARIANT = RegimeVariant(source="ewma50_residual_fraction", shrink_k=4)
T7_MIN_PRIOR = 2

EXPECTED_PARENT_REFERENCE_MAE = {
    "T-30": {
        "2024/2025": 1834.434818303733,
        "2025/2026": 1816.5413180631813,
    },
    "T-7": {
        "2024/2025": 1630.112559463305,
        "2025/2026": 1711.095982768726,
    },
}


def candidate_prediction(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
) -> tuple[pd.DataFrame, np.ndarray, dict[str, Any]]:
    base = v3_historical_base_for_season(store, horizon, season, training_seasons)
    rows = add_same_season_residual_state(base.rows, base.prediction)

    if horizon == "T-30":
        return rows, np.asarray(base.prediction, dtype=float), {
            "historical_model_id": base.model_id,
            "current_season_regime": "NO_ADJUSTMENT",
        }
    if horizon == "T-7":
        prediction, diagnostics = apply_activation_threshold(
            rows,
            base.prediction,
            T7_VARIANT,
            T7_MIN_PRIOR,
        )
        return rows, np.asarray(prediction, dtype=float), {
            "historical_model_id": base.model_id,
            "current_season_regime": "ewma50-resid-k4-cap05-min2",
            "regime_diagnostics": diagnostics,
        }
    raise KeyError(horizon)


def assert_parent_reference_reproduction(
    horizon: str,
    season: str,
    candidate_mae: float,
) -> None:
    expected = EXPECTED_PARENT_REFERENCE_MAE.get(horizon, {}).get(season)
    if expected is None:
        return
    if not np.isclose(candidate_mae, expected, rtol=0.0, atol=EXPECTED_ATOL):
        raise RuntimeError(
            f"parent v3 reference reproduction mismatch {horizon}/{season}: "
            f"actual={candidate_mae} expected={expected}"
        )


def diagnostics(
    rows: pd.DataFrame,
    frozen_prediction: np.ndarray,
    candidate_prediction_: np.ndarray,
    seed: int,
) -> dict[str, Any]:
    actual = rows["target_attendance"].astype(float).to_numpy()
    frozen_ae = np.abs(np.asarray(frozen_prediction, dtype=float) - actual)
    candidate_ae = np.abs(np.asarray(candidate_prediction_, dtype=float) - actual)
    degradation = candidate_ae - frozen_ae
    return {
        "paired_bootstrap": paired_bootstrap_improvement(
            frozen_ae,
            candidate_ae,
            seed=seed,
            samples=BOOTSTRAP_SAMPLES,
        ),
        "harmful_regressions": {
            str(int(threshold)): {
                "count": int(np.sum(degradation > threshold)),
                "rate": float(np.mean(degradation > threshold)),
            }
            for threshold in LARGE_DEGRADATION_THRESHOLDS
        },
        "degradation_quantiles": {
            "p50": float(np.quantile(degradation, 0.50)),
            "p90": float(np.quantile(degradation, 0.90)),
            "p95": float(np.quantile(degradation, 0.95)),
            "max": float(np.max(degradation)),
        },
    }


def score_changed_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    seed: int,
) -> dict[str, Any]:
    rows, candidate, contract = candidate_prediction(
        store, horizon, season, training_seasons
    )
    frozen, frozen_diag = frozen_v2_for_season(
        store, horizon, season, training_seasons, rows
    )
    candidate_mae = float(metrics(rows["target_attendance"], candidate)["mae"])
    assert_parent_reference_reproduction(horizon, season, candidate_mae)
    score = comparison_scorecard(rows, candidate, frozen)
    return {
        "horizon": horizon,
        "season": season,
        "training_seasons": list(training_seasons),
        "rows": int(len(rows)),
        "contract": contract,
        "frozen_v2": frozen_diag,
        "scorecard": score,
        "diagnostics": diagnostics(rows, frozen, candidate, seed),
    }


def score_unchanged_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
) -> dict[str, Any]:
    base = v3_historical_base_for_season(store, horizon, season, training_seasons)
    frozen, frozen_diag = frozen_v2_for_season(
        store, horizon, season, training_seasons, base.rows
    )
    value = float(metrics(base.rows["target_attendance"], frozen)["mae"])
    expected = float(FROZEN_V2_EXPECTED_MAE[horizon][season])
    if not np.isclose(value, expected, rtol=0.0, atol=EXPECTED_ATOL):
        raise RuntimeError(f"unchanged horizon reproduction mismatch {horizon}/{season}")
    return {
        "horizon": horizon,
        "season": season,
        "training_seasons": list(training_seasons),
        "rows": int(len(base.rows)),
        "contract": "EXACT_FROZEN_V2_HORIZON",
        "frozen_v2": frozen_diag,
        "scorecard": comparison_scorecard(base.rows, frozen, frozen),
        "diagnostics": {
            "paired_bootstrap": {
                "samples": BOOTSTRAP_SAMPLES,
                "observed_mean_improvement": 0.0,
                "ci95_low": 0.0,
                "ci95_high": 0.0,
                "probability_improvement_gt_0": 0.0,
            },
            "harmful_regressions": {
                str(int(threshold)): {"count": 0, "rate": 0.0}
                for threshold in LARGE_DEGRADATION_THRESHOLDS
            },
            "degradation_quantiles": {"p50": 0.0, "p90": 0.0, "p95": 0.0, "max": 0.0},
        },
    }


def summarize_horizon(folds: list[dict[str, Any]], changed: bool) -> dict[str, Any]:
    gains = [float(fold["scorecard"]["mae_improvement"]) for fold in folds]
    frozen_maes = [float(fold["scorecard"]["incumbent"]["mae"]) for fold in folds]
    candidate_maes = [float(fold["scorecard"]["candidate"]["mae"]) for fold in folds]
    if changed:
        decision = (
            "V3_HORIZON_FIXED_TEMPORAL_PASS"
            if all(gain > 0.0 for gain in gains)
            else "V3_HORIZON_FIXED_TEMPORAL_REJECT"
        )
    else:
        decision = (
            "UNCHANGED_FROZEN_V2_REPRODUCED"
            if all(np.isclose(gain, 0.0, atol=EXPECTED_ATOL, rtol=0.0) for gain in gains)
            else "UNCHANGED_HORIZON_REPRODUCTION_FAILURE"
        )
    return {
        "decision": decision,
        "fold_gains": gains,
        "all_four_positive": bool(changed and all(gain > 0 for gain in gains)),
        "mean_frozen_v2_mae": float(np.mean(frozen_maes)),
        "mean_candidate_mae": float(np.mean(candidate_maes)),
        "mean_mae_improvement": float(np.mean(gains)),
        "relative_mean_mae_improvement": float(
            (np.mean(frozen_maes) - np.mean(candidate_maes)) / np.mean(frozen_maes)
        ),
        "worst_event_degradation_across_folds": float(
            max(fold["scorecard"]["worst_event_degradation"] for fold in folds)
        ),
        "minimum_bootstrap_probability_improvement_gt_0": (
            float(min(
                fold["diagnostics"]["paired_bootstrap"]["probability_improvement_gt_0"]
                for fold in folds
            ))
            if changed else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    actual_hash = sha256_file(args.historical_runtime)
    expected_hash = manifest["historical_runtime"]["sha256"]
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    horizons: dict[str, Any] = {}
    all_cells: list[dict[str, Any]] = []

    for h_idx, horizon in enumerate(HORIZONS):
        folds: list[dict[str, Any]] = []
        for f_idx, (season, train) in enumerate(FOLDS):
            if horizon in CHANGED_HORIZONS:
                fold = score_changed_fold(
                    store, horizon, season, train, RANDOM_SEED + h_idx * 10 + f_idx
                )
            else:
                fold = score_unchanged_fold(store, horizon, season, train)
            folds.append(fold)
            all_cells.append({
                "horizon": horizon,
                "season": season,
                "frozen_v2_mae": float(fold["scorecard"]["incumbent"]["mae"]),
                "candidate_mae": float(fold["scorecard"]["candidate"]["mae"]),
                "mae_improvement": float(fold["scorecard"]["mae_improvement"]),
            })
        horizons[horizon] = {
            "changed": horizon in CHANGED_HORIZONS,
            "folds": folds,
            "summary": summarize_horizon(folds, horizon in CHANGED_HORIZONS),
        }

    changed_pass = all(
        horizons[horizon]["summary"]["decision"] == "V3_HORIZON_FIXED_TEMPORAL_PASS"
        for horizon in CHANGED_HORIZONS
    )
    unchanged_pass = all(
        horizons[horizon]["summary"]["decision"] == "UNCHANGED_FROZEN_V2_REPRODUCED"
        for horizon in UNCHANGED_HORIZONS
    )
    frozen_mean = float(np.mean([cell["frozen_v2_mae"] for cell in all_cells]))
    candidate_mean = float(np.mean([cell["candidate_mae"] for cell in all_cells]))
    package_gain = frozen_mean - candidate_mean
    package_pass = bool(changed_pass and unchanged_pass and package_gain > 0)

    payload = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_FIXED_TEMPORAL_PACKAGE_AUDIT",
        "promotion_allowed": False,
        "production_change": False,
        "frozen_v2_mutation": False,
        "tuning_or_selection_in_this_audit": False,
        "protocol": {
            "folds": [
                {"test_season": season, "training_seasons": train}
                for season, train in FOLDS
            ],
            "changed_horizons": list(CHANGED_HORIZONS),
            "unchanged_horizons": list(UNCHANGED_HORIZONS),
            "t7_policy": "ewma50-resid-k4-cap05-min2",
            "bootstrap_samples_per_changed_fold": BOOTSTRAP_SAMPLES,
            "decision_gate": "T30/T7 positive in all four folds + unchanged horizons exact + full 20-cell mean gain positive",
        },
        "input": {
            "historical_runtime_sha256": actual_hash,
            "manifest_sha256": sha256_file(args.manifest),
            "matches": int(store["match_key"].nunique()),
            "feature_rows": int(len(store)),
        },
        "runtime": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
            "random_seed": RANDOM_SEED,
        },
        "horizons": horizons,
        "cells": all_cells,
        "package_summary": {
            "decision": "V3_FIXED_PACKAGE_PASS" if package_pass else "V3_FIXED_PACKAGE_REJECT",
            "changed_horizons_pass": changed_pass,
            "unchanged_horizons_reproduced": unchanged_pass,
            "frozen_v2_20cell_mean_mae": frozen_mean,
            "v3_20cell_mean_mae": candidate_mean,
            "mean_mae_improvement": package_gain,
            "relative_mean_mae_improvement": package_gain / frozen_mean,
            "frozen_v2_changed": False,
            "production_changed": False,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "package_summary": payload["package_summary"],
        "horizons": {
            h: horizons[h]["summary"] for h in HORIZONS
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
