#!/usr/bin/env python3
"""Fixed-config temporal robustness audit for frozen b2 historical candidates.

No parameter selection occurs here. The exact Stage-2 maturity-gated policies
are replayed across the four rolling seasons 2022/23..2025/26 using the same
PIT completion rule and base-model contracts. The audit hard-asserts exact
Stage-2 MAE values and summarizes temporal stability, tail, club heterogeneity,
and correction coverage.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.current_season_residual_regime_v1 import (
    RegimeVariant,
    add_same_season_residual_state,
    apply_variant,
    base_model_id,
    base_predictions_for_season,
    conditional_scorecard,
)
from ml.pre_live_baseline_optimization_v1 import (
    comparison_scorecard,
    load_feature_store,
    sha256_file,
)

EXPERIMENT = "current-season-regime-fixed-temporal-audit-v1"
WORKSTREAM = "b2 — Current-season residual regime — fixed temporal audit"
HORIZONS = ["T-7", "T-3", "T-1"]
FOLDS = [
    ("2022/2023", ["2021/2022"]),
    ("2023/2024", ["2021/2022", "2022/2023"]),
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]
MIN_PRIOR_HOME_MATCHES = 3
EXPECTED_ATOL = 1e-9

FIXED_VARIANTS = {
    "T-7": RegimeVariant(source="ewma50_residual_fraction", shrink_k=6),
    "T-3": RegimeVariant(source="ewma50_residual_fraction", shrink_k=2),
    "T-1": RegimeVariant(source="ewma50_residual_fraction", shrink_k=6),
}

EXPECTED_FIXED_MAE = {
    "T-7": {
        "2022/2023": 1891.8569676571947,
        "2023/2024": 2246.567509322297,
        "2024/2025": 1643.8199399385203,
        "2025/2026": 1738.980778795042,
    },
    "T-3": {
        "2022/2023": 1826.9503009277796,
        "2023/2024": 2190.79000146779,
        "2024/2025": 1611.374341513805,
        "2025/2026": 1753.8914942230822,
    },
    "T-1": {
        "2022/2023": 1794.2577798538857,
        "2023/2024": 2261.110393081583,
        "2024/2025": 1627.0746389116598,
        "2025/2026": 1695.9606369653366,
    },
}


def apply_fixed_policy(
    rows: pd.DataFrame,
    base_prediction: np.ndarray,
    horizon: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    variant = FIXED_VARIANTS[horizon]
    candidate, v1_diag = apply_variant(rows, base_prediction, variant)
    n = rows["regime_prior_home_matches"].astype(int).to_numpy()
    active = n >= MIN_PRIOR_HOME_MATCHES
    base = np.asarray(base_prediction, dtype=float)
    prediction = np.where(active, candidate, base)
    delta = prediction - base
    capacity = rows["capacity"].astype(float).to_numpy()
    return prediction, {
        "fixed_variant": asdict(variant),
        "min_prior_home_matches": MIN_PRIOR_HOME_MATCHES,
        "eligible_rows_before_maturity_gate": int(v1_diag["active_correction_rows"]),
        "rows_meeting_maturity_gate": int(np.sum(active)),
        "share_meeting_maturity_gate": float(np.mean(active)),
        "active_rows": int(np.sum(np.abs(delta) > 1e-12)),
        "active_share": float(np.mean(np.abs(delta) > 1e-12)),
        "mean_abs_correction_seats": float(np.mean(np.abs(delta))),
        "median_abs_correction_seats": float(np.median(np.abs(delta))),
        "max_abs_correction_seats": float(np.max(np.abs(delta))),
        "mean_abs_correction_share_capacity": float(np.mean(np.abs(delta) / capacity)),
    }


def verify_fixed_mae(horizon: str, season: str, mae: float) -> None:
    expected = EXPECTED_FIXED_MAE[horizon][season]
    if not np.isclose(mae, expected, rtol=0.0, atol=EXPECTED_ATOL):
        raise RuntimeError(
            f"fixed b2 candidate reproduction mismatch {horizon}/{season}: "
            f"actual={mae} expected={expected}"
        )


def score_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
) -> dict[str, Any]:
    base = base_predictions_for_season(store, horizon, season, training_seasons)
    rows = add_same_season_residual_state(base.rows, base.prediction)
    prediction, diagnostics = apply_fixed_policy(rows, base.prediction, horizon)
    score = comparison_scorecard(rows, prediction, base.prediction)
    candidate_mae = float(score["candidate"]["mae"])
    verify_fixed_mae(horizon, season, candidate_mae)

    club_cells = []
    for club, metrics in score["club_breakdown_min_n_5"].items():
        club_cells.append({
            "club": club,
            "n": int(metrics["n"]),
            "base_mae": float(metrics["incumbent_mae"]),
            "candidate_mae": float(metrics["candidate_mae"]),
            "mae_improvement": float(metrics["mae_improvement"]),
        })

    return {
        "season": season,
        "training_seasons": list(training_seasons),
        "base_model_id": base.model_id,
        "fixed_candidate_id": (
            f"{FIXED_VARIANTS[horizon].id}-min{MIN_PRIOR_HOME_MATCHES}"
        ),
        "test_rows": int(len(rows)),
        "base_mae": float(score["incumbent"]["mae"]),
        "candidate_mae": candidate_mae,
        "mae_improvement": float(score["mae_improvement"]),
        "relative_mae_improvement": float(
            score["mae_improvement"] / score["incumbent"]["mae"]
        ),
        "base_median_ae": float(score["incumbent"]["median_ae"]),
        "candidate_median_ae": float(score["candidate"]["median_ae"]),
        "median_ae_delta": float(
            score["candidate"]["median_ae"] - score["incumbent"]["median_ae"]
        ),
        "base_p90_ae": float(score["incumbent"]["p90_ae"]),
        "candidate_p90_ae": float(score["candidate"]["p90_ae"]),
        "p90_ae_delta": float(
            score["candidate"]["p90_ae"] - score["incumbent"]["p90_ae"]
        ),
        "base_bias": float(score["incumbent"]["bias"]),
        "candidate_bias": float(score["candidate"]["bias"]),
        "event_improvement_rate": float(score["event_improvement_rate"]),
        "worst_event_degradation": float(score["worst_event_degradation"]),
        "worst_event": score["worst_event"],
        "best_event_improvement": float(score["best_event_improvement"]),
        "best_event": score["best_event"],
        "diagnostics": diagnostics,
        "conditional_by_prior_home_matches": conditional_scorecard(
            rows, prediction, base.prediction
        ),
        "club_cells_n5": club_cells,
    }


def horizon_audit(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    folds = [
        score_fold(store, horizon, season, training_seasons)
        for season, training_seasons in FOLDS
    ]
    improvements = [float(fold["mae_improvement"]) for fold in folds]
    club_cells = [cell | {"season": fold["season"]} for fold in folds for cell in fold["club_cells_n5"]]
    improved_club_cells = [cell for cell in club_cells if cell["mae_improvement"] > 0]
    worse_club_cells = [cell for cell in club_cells if cell["mae_improvement"] < 0]
    worst_club_cell = min(club_cells, key=lambda x: x["mae_improvement"]) if club_cells else None
    best_club_cell = max(club_cells, key=lambda x: x["mae_improvement"]) if club_cells else None

    all_positive = bool(all(value > 0 for value in improvements))
    signal = "FIXED_CONFIG_POSITIVE_ALL_FOUR_FOLDS" if all_positive else "FIXED_CONFIG_NOT_STABLE_ALL_FOUR_FOLDS"
    return {
        "horizon": horizon,
        "base_model_id": base_model_id(horizon),
        "fixed_variant": asdict(FIXED_VARIANTS[horizon]),
        "min_prior_home_matches": MIN_PRIOR_HOME_MATCHES,
        "fixed_candidate_id": f"{FIXED_VARIANTS[horizon].id}-min3",
        "folds": folds,
        "fold_mae_improvements": improvements,
        "all_four_folds_improve": all_positive,
        "mean_base_mae": float(np.mean([fold["base_mae"] for fold in folds])),
        "mean_candidate_mae": float(np.mean([fold["candidate_mae"] for fold in folds])),
        "mean_mae_improvement": float(np.mean(improvements)),
        "minimum_fold_mae_improvement": float(np.min(improvements)),
        "maximum_fold_mae_improvement": float(np.max(improvements)),
        "max_worst_event_degradation": float(np.max([fold["worst_event_degradation"] for fold in folds])),
        "mean_event_improvement_rate": float(np.mean([fold["event_improvement_rate"] for fold in folds])),
        "mean_active_share": float(np.mean([fold["diagnostics"]["active_share"] for fold in folds])),
        "club_stability": {
            "club_season_cells_n5": int(len(club_cells)),
            "improved_cells": int(len(improved_club_cells)),
            "worse_cells": int(len(worse_club_cells)),
            "improved_share": float(len(improved_club_cells) / len(club_cells)) if club_cells else 0.0,
            "worst_club_season_cell": worst_club_cell,
            "best_club_season_cell": best_club_cell,
        },
        "signal": signal,
        "promotion_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    expected_hash = manifest["historical_runtime"]["sha256"]
    actual_hash = sha256_file(args.historical_runtime)
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    results = [horizon_audit(store, horizon) for horizon in HORIZONS]
    overall_pass = bool(all(row["all_four_folds_improve"] for row in results))

    payload = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "PASS" if overall_pass else "FAIL",
        "evidence_class": "FIXED_CONFIG_HISTORICAL_TEMPORAL_ROBUSTNESS",
        "promotion_allowed": False,
        "production_change": False,
        "selection_performed": False,
        "contract": {
            "fixed_from_stage2": True,
            "horizons": HORIZONS,
            "min_prior_home_matches": MIN_PRIOR_HOME_MATCHES,
            "four_rolling_folds": [
                {"season": season, "training_seasons": train}
                for season, train in FOLDS
            ],
            "hard_expected_candidate_mae_assertions": EXPECTED_FIXED_MAE,
            "no_parameter_tuning": True,
        },
        "input": {
            "historical_runtime_sha256": actual_hash,
            "artifact_version": manifest.get("artifact_version"),
            "feature_contract": manifest.get("feature_contract"),
        },
        "runtime": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "horizons": results,
        "overall_pass": overall_pass,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "status": payload["status"],
        "overall_pass": overall_pass,
        "promotion_allowed": False,
        "horizons": [
            {
                "horizon": row["horizon"],
                "fixed_candidate_id": row["fixed_candidate_id"],
                "all_four_folds_improve": row["all_four_folds_improve"],
                "mean_mae_improvement": row["mean_mae_improvement"],
                "minimum_fold_mae_improvement": row["minimum_fold_mae_improvement"],
                "max_worst_event_degradation": row["max_worst_event_degradation"],
                "mean_active_share": row["mean_active_share"],
                "signal": row["signal"],
            }
            for row in results
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
