#!/usr/bin/env python3
"""b2 current-season residual regime maturity / activation Stage 2.

Stage 1 selected a fixed signal formulation per advancing horizon. This stage
changes only activation maturity: how many earlier completed same-season home
matches must exist before the fixed Stage-1 correction may be applied.

Selection remains development-only on 2022/23 and 2023/24. Exposed references
2024/25 and 2025/26 are scored only after the activation threshold is frozen.
No production promotion occurs automatically.
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
    DEVELOPMENT_FOLDS,
    REFERENCE_HOLDOUTS,
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

EXPERIMENT = "current-season-regime-maturity-stage2-v1"
WORKSTREAM = "b2 — Current-season residual regime — signal maturity Stage 2"
HORIZONS = ["T-7", "T-3", "T-1"]
ACTIVATION_MIN_PRIOR_HOME_MATCHES = (1, 2, 3)
MIN_MEAN_RELATIVE_MAE_IMPROVEMENT = 0.005
NEAR_BEST_GAIN_RETENTION = 0.95
SELECTION_ATOL = 1e-12

STAGE1_VARIANTS: dict[str, RegimeVariant] = {
    "T-7": RegimeVariant(source="ewma_residual_fraction", shrink_k=6),
    "T-3": RegimeVariant(source="ewma_residual_fraction", shrink_k=2),
    "T-1": RegimeVariant(source="ewma_residual_fraction", shrink_k=6),
}

# Hard reproduction gates for Stage-1 min_prior=1 behavior. Stage 2 cannot
# proceed if the exact Stage-1 selected candidate is not reproduced.
EXPECTED_STAGE1_CANDIDATE_MAE = {
    "T-7": {
        "2022/2023": 1904.7800328241033,
        "2023/2024": 2242.004630262366,
        "2024/2025": 1654.856159968983,
        "2025/2026": 1740.1068803034543,
    },
    "T-3": {
        "2022/2023": 1850.723585403322,
        "2023/2024": 2190.711335362965,
        "2024/2025": 1630.2588518240318,
        "2025/2026": 1742.2048615326544,
    },
    "T-1": {
        "2022/2023": 1807.0890994179251,
        "2023/2024": 2266.773185039798,
        "2024/2025": 1632.937487550164,
        "2025/2026": 1691.322952623548,
    },
}
EXPECTED_ATOL = 1e-9


def apply_activation_threshold(
    rows: pd.DataFrame,
    base_prediction: np.ndarray,
    fixed_variant: RegimeVariant,
    min_prior_home_matches: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    candidate_prediction, base_diagnostics = apply_variant(rows, base_prediction, fixed_variant)
    base = np.asarray(base_prediction, dtype=float)
    n = rows["regime_prior_home_matches"].astype(int).to_numpy()
    active = n >= int(min_prior_home_matches)
    prediction = np.where(active, candidate_prediction, base)
    delta = prediction - base
    capacity = rows["capacity"].astype(float).to_numpy()
    return prediction, {
        "min_prior_home_matches": int(min_prior_home_matches),
        "eligible_rows_before_activation_gate": int(base_diagnostics["active_correction_rows"]),
        "active_rows_after_activation_gate": int(np.sum(np.abs(delta) > 1e-12)),
        "active_share_after_activation_gate": float(np.mean(np.abs(delta) > 1e-12)),
        "rows_meeting_maturity_threshold": int(np.sum(active)),
        "share_meeting_maturity_threshold": float(np.mean(active)),
        "mean_abs_correction_seats": float(np.mean(np.abs(delta))),
        "median_abs_correction_seats": float(np.median(np.abs(delta))),
        "max_abs_correction_seats": float(np.max(np.abs(delta))),
        "mean_abs_correction_share_capacity": float(np.mean(np.abs(delta) / capacity)),
    }


def score_candidate(
    rows: pd.DataFrame,
    base_prediction: np.ndarray,
    fixed_variant: RegimeVariant,
    min_prior_home_matches: int,
) -> dict[str, Any]:
    prediction, diagnostics = apply_activation_threshold(
        rows,
        base_prediction,
        fixed_variant,
        min_prior_home_matches,
    )
    return {
        "candidate_id": f"{fixed_variant.id}-min{min_prior_home_matches}",
        "min_prior_home_matches": int(min_prior_home_matches),
        "fixed_stage1_variant": asdict(fixed_variant),
        "diagnostics": diagnostics,
        "scorecard": comparison_scorecard(rows, prediction, base_prediction),
        "conditional_by_prior_home_matches": conditional_scorecard(rows, prediction, base_prediction),
    }


def no_adjustment(rows: pd.DataFrame, base_prediction: np.ndarray) -> dict[str, Any]:
    return {
        "candidate_id": "NO_ADJUSTMENT",
        "min_prior_home_matches": None,
        "fixed_stage1_variant": None,
        "diagnostics": {
            "active_rows_after_activation_gate": 0,
            "active_share_after_activation_gate": 0.0,
            "mean_abs_correction_seats": 0.0,
            "max_abs_correction_seats": 0.0,
        },
        "scorecard": comparison_scorecard(rows, base_prediction, base_prediction),
        "conditional_by_prior_home_matches": conditional_scorecard(rows, base_prediction, base_prediction),
    }


def verify_stage1_reproduction(
    horizon: str,
    season: str,
    stage1_candidate_mae: float,
) -> None:
    expected = EXPECTED_STAGE1_CANDIDATE_MAE[horizon][season]
    if not np.isclose(stage1_candidate_mae, expected, rtol=0.0, atol=EXPECTED_ATOL):
        raise RuntimeError(
            f"Stage-1 b2 reproduction mismatch {horizon}/{season}: "
            f"actual={stage1_candidate_mae} expected={expected}"
        )


def score_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
) -> dict[str, Any]:
    base = base_predictions_for_season(store, horizon, season, training_seasons)
    rows = add_same_season_residual_state(base.rows, base.prediction)
    fixed_variant = STAGE1_VARIANTS[horizon]

    candidates = {"NO_ADJUSTMENT": no_adjustment(rows, base.prediction)}
    for min_prior in ACTIVATION_MIN_PRIOR_HOME_MATCHES:
        scored = score_candidate(rows, base.prediction, fixed_variant, min_prior)
        candidates[scored["candidate_id"]] = scored

    stage1_id = f"{fixed_variant.id}-min1"
    stage1_mae = float(candidates[stage1_id]["scorecard"]["candidate"]["mae"])
    verify_stage1_reproduction(horizon, season, stage1_mae)

    return {
        "horizon": horizon,
        "season": season,
        "training_seasons": list(training_seasons),
        "base_model_id": base.model_id,
        "base_training_rows": int(base.training_rows),
        "test_rows": int(len(rows)),
        "fixed_stage1_variant": asdict(fixed_variant),
        "stage1_reproduction_candidate_id": stage1_id,
        "stage1_reproduction_mae": stage1_mae,
        "candidates": candidates,
    }


def aggregate_development(folds: list[dict[str, Any]], horizon: str) -> list[dict[str, Any]]:
    fixed_variant = STAGE1_VARIANTS[horizon]
    candidate_ids = [
        "NO_ADJUSTMENT",
        *[
            f"{fixed_variant.id}-min{min_prior}"
            for min_prior in ACTIVATION_MIN_PRIOR_HOME_MATCHES
        ],
    ]
    result = []
    for candidate_id in candidate_ids:
        rows = []
        for fold in folds:
            score = fold["candidates"][candidate_id]["scorecard"]
            incumbent_mae = float(score["incumbent"]["mae"])
            candidate_mae = float(score["candidate"]["mae"])
            improvement = float(score["mae_improvement"])
            rows.append({
                "season": fold["season"],
                "incumbent_mae": incumbent_mae,
                "candidate_mae": candidate_mae,
                "mae_improvement": improvement,
                "relative_mae_improvement": improvement / incumbent_mae,
                "median_ae_delta": float(
                    score["candidate"]["median_ae"] - score["incumbent"]["median_ae"]
                ),
                "p90_ae_delta": float(
                    score["candidate"]["p90_ae"] - score["incumbent"]["p90_ae"]
                ),
                "worst_event_degradation": float(score["worst_event_degradation"]),
                "event_improvement_rate": float(score["event_improvement_rate"]),
            })
        mean_inc = float(np.mean([row["incumbent_mae"] for row in rows]))
        mean_cand = float(np.mean([row["candidate_mae"] for row in rows]))
        improvement = mean_inc - mean_cand
        min_prior = None
        if candidate_id != "NO_ADJUSTMENT":
            min_prior = int(candidate_id.rsplit("min", 1)[1])
        result.append({
            "candidate_id": candidate_id,
            "min_prior_home_matches": min_prior,
            "folds": rows,
            "all_development_folds_improve": bool(all(row["mae_improvement"] > 0 for row in rows)),
            "mean_incumbent_mae": mean_inc,
            "mean_candidate_mae": mean_cand,
            "mean_mae_improvement": float(improvement),
            "mean_relative_mae_improvement": float(improvement / mean_inc),
            "mean_median_ae_delta": float(np.mean([row["median_ae_delta"] for row in rows])),
            "mean_p90_ae_delta": float(np.mean([row["p90_ae_delta"] for row in rows])),
            "max_worst_event_degradation": float(np.max([row["worst_event_degradation"] for row in rows])),
            "mean_event_improvement_rate": float(np.mean([row["event_improvement_rate"] for row in rows])),
        })
    return result


def select_activation(development: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    incumbent = next(row for row in development if row["candidate_id"] == "NO_ADJUSTMENT")
    eligible = [
        row for row in development
        if row["candidate_id"] != "NO_ADJUSTMENT"
        and row["all_development_folds_improve"]
        and row["mean_relative_mae_improvement"] + SELECTION_ATOL
        >= MIN_MEAN_RELATIVE_MAE_IMPROVEMENT
    ]
    if not eligible:
        return "NO_ADJUSTMENT", {
            "reason": "NO_ACTIVATION_THRESHOLD_MEETS_TWO_FOLD_GATE",
            "eligible_candidate_ids": [],
            "selected_row": incumbent,
        }

    best_gain = max(float(row["mean_mae_improvement"]) for row in eligible)
    near_best = [
        row for row in eligible
        if float(row["mean_mae_improvement"]) + SELECTION_ATOL
        >= NEAR_BEST_GAIN_RETENTION * best_gain
    ]
    selected = min(
        near_best,
        key=lambda row: (
            float(row["max_worst_event_degradation"]),
            float(row["mean_p90_ae_delta"]),
            -int(row["min_prior_home_matches"] or 0),
            str(row["candidate_id"]),
        ),
    )
    return str(selected["candidate_id"]), {
        "reason": "TWO_FOLD_GATE_THEN_95PCT_GAIN_RETENTION_AND_TAIL_MINIMIZATION",
        "best_mean_mae_improvement": float(best_gain),
        "near_best_required_improvement": float(NEAR_BEST_GAIN_RETENTION * best_gain),
        "eligible_candidate_ids": [str(row["candidate_id"]) for row in eligible],
        "near_best_candidate_ids": [str(row["candidate_id"]) for row in near_best],
        "selected_row": selected,
    }


def horizon_experiment(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    development_folds = [
        score_fold(store, horizon, season, training_seasons)
        for season, training_seasons in DEVELOPMENT_FOLDS
    ]
    aggregate = aggregate_development(development_folds, horizon)
    selected_id, selection = select_activation(aggregate)

    reference_folds = [
        score_fold(store, horizon, season, training_seasons)
        for season, training_seasons in REFERENCE_HOLDOUTS
    ]
    references = []
    for fold in reference_folds:
        score = fold["candidates"][selected_id]["scorecard"]
        references.append({
            "season": fold["season"],
            "base_mae": float(score["incumbent"]["mae"]),
            "selected_mae": float(score["candidate"]["mae"]),
            "mae_improvement": float(score["mae_improvement"]),
            "median_ae_delta": float(score["candidate"]["median_ae"] - score["incumbent"]["median_ae"]),
            "p90_ae_delta": float(score["candidate"]["p90_ae"] - score["incumbent"]["p90_ae"]),
            "bias_delta": float(score["candidate"]["bias"] - score["incumbent"]["bias"]),
            "worst_event_degradation": float(score["worst_event_degradation"]),
            "worst_event": score["worst_event"],
            "event_improvement_rate": float(score["event_improvement_rate"]),
            "diagnostics": fold["candidates"][selected_id]["diagnostics"],
            "conditional_by_prior_home_matches": fold["candidates"][selected_id]["conditional_by_prior_home_matches"],
        })

    mean_base = float(np.mean([row["base_mae"] for row in references]))
    mean_selected = float(np.mean([row["selected_mae"] for row in references]))
    mean_improvement = mean_base - mean_selected
    both_positive = bool(all(row["mae_improvement"] > 0 for row in references))

    if selected_id == "NO_ADJUSTMENT":
        signal = "NO_STABLE_MATURITY_THRESHOLD"
    elif both_positive and mean_improvement > 0:
        signal = "MATURITY_GATED_REGIME_POSITIVE_BOTH_REFERENCES"
    elif mean_improvement > 0:
        signal = "MATURITY_GATED_REGIME_POSITIVE_MEAN_MIXED_REFERENCES"
    else:
        signal = "MATURITY_GATED_REGIME_NOT_PROVEN_ON_REFERENCES"

    return {
        "horizon": horizon,
        "base_model_id": base_model_id(horizon),
        "fixed_stage1_variant": asdict(STAGE1_VARIANTS[horizon]),
        "development_folds": development_folds,
        "development_aggregate": aggregate,
        "selection": selection,
        "selected_candidate_id": selected_id,
        "selected_min_prior_home_matches": selection["selected_row"]["min_prior_home_matches"],
        "reference_folds": reference_folds,
        "reference_summary": references,
        "mean_reference_base_mae": mean_base,
        "mean_reference_selected_mae": mean_selected,
        "mean_reference_mae_improvement": float(mean_improvement),
        "both_reference_seasons_improve": both_positive,
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
    results = [horizon_experiment(store, horizon) for horizon in HORIZONS]

    payload = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_HISTORICAL_SIGNAL_MATURITY_EVIDENCE",
        "evidence_class": "EXPOSED_HISTORICAL_REFERENCE_SEASONS",
        "promotion_allowed": False,
        "production_change": False,
        "contract": {
            "stage1_signal_source_and_shrinkage_frozen": True,
            "activation_candidates_min_prior_home_matches": list(ACTIVATION_MIN_PRIOR_HOME_MATCHES),
            "development_selection_only": True,
            "minimum_mean_relative_mae_improvement": MIN_MEAN_RELATIVE_MAE_IMPROVEMENT,
            "near_best_gain_retention": NEAR_BEST_GAIN_RETENTION,
            "references_used_for_selection": False,
        },
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_hash,
            "manifest_path": str(args.manifest),
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
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "promotion_allowed": False,
        "horizons": [
            {
                "horizon": row["horizon"],
                "selected_candidate_id": row["selected_candidate_id"],
                "selected_min_prior_home_matches": row["selected_min_prior_home_matches"],
                "signal": row["signal"],
                "mean_reference_base_mae": row["mean_reference_base_mae"],
                "mean_reference_selected_mae": row["mean_reference_selected_mae"],
                "mean_reference_mae_improvement": row["mean_reference_mae_improvement"],
            }
            for row in results
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
