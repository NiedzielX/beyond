#!/usr/bin/env python3
"""Pre-Live v3 historical-anchor + current-season regime revalidation.

This is a new Track-B challenger cycle. It does not mutate Frozen Pre-Live v2.

Protocol:
- use exact robust T-30/T-7/T-1 historical ensemble contracts from the
  completed a2 fixed-temporal audit;
- retain current a2 historical base at T-14/T-3;
- rebuild same-season residual state relative to the new historical anchor;
- repeat the canonical two-stage b2 development-only selection:
    A) signal/shrinkage among 15 variants;
    B) maturity min1/min2/min3 for the selected signal;
- score the old frozen b2 formulation on the new anchor as a fixed comparator;
- reproduce Frozen Pre-Live v2 exactly on every rolling fold;
- open 2024/25 and 2025/26 only after v3 regime selection is frozen;
- no prospective/delayed-label d2 event is used for selection.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.a2_external_ensemble_closure_v1 import current_a2_prediction
from ml.a2_external_ensemble_fixed_temporal_v1 import (
    FIXED_CONTRACTS as ROBUST_HISTORICAL_CONTRACTS,
    fixed_candidate_prediction,
)
from ml.current_season_regime_fixed_temporal_audit_v1 import (
    FIXED_VARIANTS as FROZEN_B2_VARIANTS,
    MIN_PRIOR_HOME_MATCHES as FROZEN_B2_MIN_PRIOR,
    apply_fixed_policy,
)
from ml.current_season_regime_maturity_stage2_v1 import (
    ACTIVATION_MIN_PRIOR_HOME_MATCHES,
    apply_activation_threshold,
    score_candidate as score_maturity_candidate,
)
from ml.current_season_residual_regime_v1 import (
    DEVELOPMENT_FOLDS,
    REFERENCE_HOLDOUTS,
    VARIANTS,
    RegimeVariant,
    add_same_season_residual_state,
    aggregate_development as aggregate_signal_development,
    base_predictions_for_season,
    no_adjustment_score,
    score_variant,
    select_candidate as select_signal_candidate,
)
from ml.demand_engine.structural_prior_runtime import CURRENT_EARLY_RUNTIME_SPECS
from ml.pre_live_baseline_optimization_v1 import (
    comparison_scorecard,
    eligible_rows,
    load_feature_store,
    metrics,
    sha256_file,
)
from ml.pre_live_v2_historical_freeze_v1 import EXPECTED_FINAL_MAE as FROZEN_V2_EXPECTED_MAE

EXPERIMENT = "pre-live-v3-regime-revalidation-v1"
WORKSTREAM = "Pre-Live v3 — robust historical anchors + b2 revalidation"
HORIZONS = ("T-30", "T-14", "T-7", "T-3", "T-1")
RANDOM_SEED = 42
EXPECTED_ATOL = 1e-9

# Preserve the original maturity-selection discipline.
MIN_MEAN_RELATIVE_MAE_IMPROVEMENT = 0.005
MATURITY_NEAR_BEST_GAIN_RETENTION = 0.95
SELECTION_ATOL = 1e-12


@dataclass
class V3HistoricalBase:
    rows: pd.DataFrame
    prediction: np.ndarray
    model_id: str


def v3_historical_model_id(horizon: str) -> str:
    if horizon == "T-30":
        return "v3-hist-t30-ensemble-current075-xgbd3-025"
    if horizon == "T-7":
        return "v3-hist-t7-ensemble-hgb025-catd4-025-lgbm15-050"
    if horizon == "T-1":
        return "v3-hist-t1-ensemble-hgb025-catd4-050-lgbm15-025"
    return f"v3-hist-retain-current-a2-{horizon.lower().replace('-', '')}"


def v3_historical_base_for_season(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
) -> V3HistoricalBase:
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = eligible_rows(store, horizon, season, spec.baseline_column).reset_index(drop=True)
    if rows.empty:
        raise RuntimeError(f"no eligible rows for {horizon}/{season}")

    if horizon in ROBUST_HISTORICAL_CONTRACTS:
        prediction = fixed_candidate_prediction(
            store, horizon, training_seasons, rows
        )
    else:
        prediction = current_a2_prediction(
            store, horizon, training_seasons, rows
        )

    return V3HistoricalBase(
        rows=rows,
        prediction=np.asarray(prediction, dtype=float),
        model_id=v3_historical_model_id(horizon),
    )


def _row_identity(rows: pd.DataFrame) -> list[tuple[str, str]]:
    return [
        (str(row.match_key), pd.Timestamp(row.as_of_at).isoformat())
        for row in rows[["match_key", "as_of_at"]].itertuples(index=False)
    ]


def assert_same_rows(left: pd.DataFrame, right: pd.DataFrame, label: str) -> None:
    if _row_identity(left) != _row_identity(right):
        raise RuntimeError(f"row identity mismatch: {label}")


def frozen_v2_for_season(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    expected_rows: pd.DataFrame,
) -> tuple[np.ndarray, dict[str, Any]]:
    old_base = base_predictions_for_season(
        store, horizon, season, training_seasons
    )
    assert_same_rows(expected_rows, old_base.rows, f"v3-vs-v2 {horizon}/{season}")

    if horizon in FROZEN_B2_VARIANTS:
        old_state = add_same_season_residual_state(
            old_base.rows, old_base.prediction
        )
        prediction, diagnostics = apply_fixed_policy(
            old_state, old_base.prediction, horizon
        )
        policy_id = (
            f"{FROZEN_B2_VARIANTS[horizon].id}-min{FROZEN_B2_MIN_PRIOR}"
        )
    else:
        prediction = np.asarray(old_base.prediction, dtype=float)
        diagnostics = {
            "active_rows": 0,
            "active_share": 0.0,
            "mean_abs_correction_seats": 0.0,
        }
        policy_id = "NO_ADJUSTMENT"

    value = float(metrics(expected_rows["target_attendance"], prediction)["mae"])
    expected = float(FROZEN_V2_EXPECTED_MAE[horizon][season])
    if not np.isclose(value, expected, rtol=0.0, atol=EXPECTED_ATOL):
        raise RuntimeError(
            f"Frozen-v2 reproduction mismatch {horizon}/{season}: "
            f"actual={value} expected={expected}"
        )
    return np.asarray(prediction, dtype=float), {
        "policy_id": policy_id,
        "mae": value,
        "diagnostics": diagnostics,
    }


def score_signal_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
) -> dict[str, Any]:
    base = v3_historical_base_for_season(
        store, horizon, season, training_seasons
    )
    rows = add_same_season_residual_state(base.rows, base.prediction)
    scored: dict[str, Any] = {
        "NO_ADJUSTMENT": no_adjustment_score(rows, base.prediction)
    }
    for variant in VARIANTS:
        scored[variant.id] = score_variant(rows, base.prediction, variant)
    return {
        "horizon": horizon,
        "season": season,
        "training_seasons": list(training_seasons),
        "base_model_id": base.model_id,
        "base_mae": float(metrics(rows["target_attendance"], base.prediction)["mae"]),
        "test_rows": int(len(rows)),
        "candidates": scored,
    }


def score_maturity_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    variant: RegimeVariant,
) -> dict[str, Any]:
    base = v3_historical_base_for_season(
        store, horizon, season, training_seasons
    )
    rows = add_same_season_residual_state(base.rows, base.prediction)
    candidates: dict[str, Any] = {
        "NO_ADJUSTMENT": {
            "candidate_id": "NO_ADJUSTMENT",
            "min_prior_home_matches": None,
            "fixed_stage1_variant": None,
            "diagnostics": {
                "active_rows_after_activation_gate": 0,
                "active_share_after_activation_gate": 0.0,
                "mean_abs_correction_seats": 0.0,
                "max_abs_correction_seats": 0.0,
            },
            "scorecard": comparison_scorecard(
                rows, base.prediction, base.prediction
            ),
        }
    }
    for min_prior in ACTIVATION_MIN_PRIOR_HOME_MATCHES:
        item = score_maturity_candidate(
            rows, base.prediction, variant, min_prior
        )
        candidates[item["candidate_id"]] = item
    return {
        "horizon": horizon,
        "season": season,
        "training_seasons": list(training_seasons),
        "base_model_id": base.model_id,
        "test_rows": int(len(rows)),
        "selected_signal_variant": asdict(variant),
        "candidates": candidates,
    }


def aggregate_maturity_development(
    folds: list[dict[str, Any]],
    variant: RegimeVariant,
) -> list[dict[str, Any]]:
    candidate_ids = [
        "NO_ADJUSTMENT",
        *[
            f"{variant.id}-min{min_prior}"
            for min_prior in ACTIVATION_MIN_PRIOR_HOME_MATCHES
        ],
    ]
    result: list[dict[str, Any]] = []
    for candidate_id in candidate_ids:
        fold_rows: list[dict[str, Any]] = []
        for fold in folds:
            score = fold["candidates"][candidate_id]["scorecard"]
            incumbent_mae = float(score["incumbent"]["mae"])
            candidate_mae = float(score["candidate"]["mae"])
            improvement = float(score["mae_improvement"])
            fold_rows.append({
                "season": fold["season"],
                "incumbent_mae": incumbent_mae,
                "candidate_mae": candidate_mae,
                "mae_improvement": improvement,
                "relative_mae_improvement": improvement / incumbent_mae,
                "median_ae_delta": float(
                    score["candidate"]["median_ae"]
                    - score["incumbent"]["median_ae"]
                ),
                "p90_ae_delta": float(
                    score["candidate"]["p90_ae"]
                    - score["incumbent"]["p90_ae"]
                ),
                "worst_event_degradation": float(
                    score["worst_event_degradation"]
                ),
                "event_improvement_rate": float(
                    score["event_improvement_rate"]
                ),
            })
        mean_inc = float(np.mean([row["incumbent_mae"] for row in fold_rows]))
        mean_cand = float(np.mean([row["candidate_mae"] for row in fold_rows]))
        improvement = mean_inc - mean_cand
        min_prior = None
        if candidate_id != "NO_ADJUSTMENT":
            min_prior = int(candidate_id.rsplit("min", 1)[1])
        result.append({
            "candidate_id": candidate_id,
            "min_prior_home_matches": min_prior,
            "folds": fold_rows,
            "all_development_folds_improve": bool(
                all(row["mae_improvement"] > 0 for row in fold_rows)
            ),
            "mean_incumbent_mae": mean_inc,
            "mean_candidate_mae": mean_cand,
            "mean_mae_improvement": improvement,
            "mean_relative_mae_improvement": improvement / mean_inc,
            "mean_median_ae_delta": float(
                np.mean([row["median_ae_delta"] for row in fold_rows])
            ),
            "mean_p90_ae_delta": float(
                np.mean([row["p90_ae_delta"] for row in fold_rows])
            ),
            "max_worst_event_degradation": float(
                np.max([row["worst_event_degradation"] for row in fold_rows])
            ),
            "mean_event_improvement_rate": float(
                np.mean([row["event_improvement_rate"] for row in fold_rows])
            ),
        })
    return result


def select_maturity(
    development: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    incumbent = next(
        row for row in development if row["candidate_id"] == "NO_ADJUSTMENT"
    )
    eligible = [
        row
        for row in development
        if row["candidate_id"] != "NO_ADJUSTMENT"
        and row["all_development_folds_improve"]
        and row["mean_relative_mae_improvement"] + SELECTION_ATOL
        >= MIN_MEAN_RELATIVE_MAE_IMPROVEMENT
    ]
    if not eligible:
        return "NO_ADJUSTMENT", {
            "reason": "NO_ACTIVATION_THRESHOLD_MEETS_TWO_FOLD_GATE_ON_V3_ANCHOR",
            "eligible_candidate_ids": [],
            "selected_row": incumbent,
        }

    best_gain = max(float(row["mean_mae_improvement"]) for row in eligible)
    near_best = [
        row
        for row in eligible
        if float(row["mean_mae_improvement"]) + SELECTION_ATOL
        >= MATURITY_NEAR_BEST_GAIN_RETENTION * best_gain
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
        "best_mean_mae_improvement": best_gain,
        "near_best_required_improvement": (
            MATURITY_NEAR_BEST_GAIN_RETENTION * best_gain
        ),
        "eligible_candidate_ids": [
            str(row["candidate_id"]) for row in eligible
        ],
        "near_best_candidate_ids": [
            str(row["candidate_id"]) for row in near_best
        ],
        "selected_row": selected,
    }


def old_b2_on_v3_anchor(
    rows: pd.DataFrame,
    base_prediction: np.ndarray,
    horizon: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    if horizon not in FROZEN_B2_VARIANTS:
        return np.asarray(base_prediction, dtype=float), {
            "policy_id": "NO_ADJUSTMENT",
            "active_rows": 0,
            "active_share": 0.0,
            "mean_abs_correction_seats": 0.0,
        }
    prediction, diagnostics = apply_fixed_policy(
        rows, base_prediction, horizon
    )
    return prediction, {
        "policy_id": (
            f"{FROZEN_B2_VARIANTS[horizon].id}-min{FROZEN_B2_MIN_PRIOR}"
        ),
        **diagnostics,
    }


def selected_v3_regime_prediction(
    rows: pd.DataFrame,
    base_prediction: np.ndarray,
    variant: RegimeVariant | None,
    min_prior: int | None,
) -> tuple[np.ndarray, dict[str, Any]]:
    if variant is None or min_prior is None:
        return np.asarray(base_prediction, dtype=float), {
            "policy_id": "NO_ADJUSTMENT",
            "active_rows_after_activation_gate": 0,
            "active_share_after_activation_gate": 0.0,
            "mean_abs_correction_seats": 0.0,
        }
    prediction, diagnostics = apply_activation_threshold(
        rows, base_prediction, variant, int(min_prior)
    )
    return prediction, {
        "policy_id": f"{variant.id}-min{int(min_prior)}",
        **diagnostics,
    }


def compact_metrics(rows: pd.DataFrame, prediction: np.ndarray) -> dict[str, float]:
    result = metrics(rows["target_attendance"], prediction)
    return {
        "mae": float(result["mae"]),
        "median_ae": float(result["median_ae"]),
        "p90_ae": float(result["p90_ae"]),
        "bias": float(result["bias"]),
    }


def evaluate_final_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    selected_variant: RegimeVariant | None,
    selected_min_prior: int | None,
) -> dict[str, Any]:
    base = v3_historical_base_for_season(
        store, horizon, season, training_seasons
    )
    rows = add_same_season_residual_state(base.rows, base.prediction)

    frozen_v2, frozen_diag = frozen_v2_for_season(
        store, horizon, season, training_seasons, rows
    )
    old_b2_prediction, old_b2_diag = old_b2_on_v3_anchor(
        rows, base.prediction, horizon
    )
    selected_prediction, selected_diag = selected_v3_regime_prediction(
        rows, base.prediction, selected_variant, selected_min_prior
    )

    return {
        "season": season,
        "training_seasons": list(training_seasons),
        "rows": int(len(rows)),
        "v3_historical_model_id": base.model_id,
        "layers": {
            "frozen_v2": {
                "metrics": compact_metrics(rows, frozen_v2),
                "diagnostics": frozen_diag,
            },
            "v3_historical_only": {
                "metrics": compact_metrics(rows, base.prediction),
                "vs_frozen_v2": comparison_scorecard(
                    rows, base.prediction, frozen_v2
                ),
            },
            "old_b2_on_v3_anchor": {
                "metrics": compact_metrics(rows, old_b2_prediction),
                "diagnostics": old_b2_diag,
                "vs_v3_historical": comparison_scorecard(
                    rows, old_b2_prediction, base.prediction
                ),
                "vs_frozen_v2": comparison_scorecard(
                    rows, old_b2_prediction, frozen_v2
                ),
            },
            "selected_v3_regime": {
                "metrics": compact_metrics(rows, selected_prediction),
                "diagnostics": selected_diag,
                "vs_v3_historical": comparison_scorecard(
                    rows, selected_prediction, base.prediction
                ),
                "vs_frozen_v2": comparison_scorecard(
                    rows, selected_prediction, frozen_v2
                ),
            },
        },
    }


def horizon_experiment(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    # Stage A — signal/shrinkage selection on development only.
    signal_folds = [
        score_signal_fold(store, horizon, season, train)
        for season, train in DEVELOPMENT_FOLDS
    ]
    signal_aggregate = aggregate_signal_development(signal_folds)
    selected_signal_id, signal_selection = select_signal_candidate(
        signal_aggregate
    )
    selected_variant = None
    if selected_signal_id != "NO_ADJUSTMENT":
        selected_variant = next(
            variant for variant in VARIANTS if variant.id == selected_signal_id
        )

    # Stage B — maturity selection for the Stage-A signal.
    if selected_variant is None:
        maturity_folds: list[dict[str, Any]] = []
        maturity_aggregate: list[dict[str, Any]] = []
        selected_policy_id = "NO_ADJUSTMENT"
        selected_min_prior = None
        maturity_selection = {
            "reason": "NO_SIGNAL_ADVANCED_FROM_STAGE_A",
            "selected_row": {
                "candidate_id": "NO_ADJUSTMENT",
                "min_prior_home_matches": None,
            },
        }
    else:
        maturity_folds = [
            score_maturity_fold(
                store, horizon, season, train, selected_variant
            )
            for season, train in DEVELOPMENT_FOLDS
        ]
        maturity_aggregate = aggregate_maturity_development(
            maturity_folds, selected_variant
        )
        selected_policy_id, maturity_selection = select_maturity(
            maturity_aggregate
        )
        selected_min_prior = maturity_selection["selected_row"][
            "min_prior_home_matches"
        ]
        if selected_policy_id == "NO_ADJUSTMENT":
            selected_variant = None
            selected_min_prior = None

    references = [
        evaluate_final_fold(
            store,
            horizon,
            season,
            train,
            selected_variant,
            selected_min_prior,
        )
        for season, train in REFERENCE_HOLDOUTS
    ]

    v3_vs_v2_gains = [
        float(
            fold["layers"]["selected_v3_regime"]["vs_frozen_v2"][
                "mae_improvement"
            ]
        )
        for fold in references
    ]
    regime_vs_hist_gains = [
        float(
            fold["layers"]["selected_v3_regime"]["vs_v3_historical"][
                "mae_improvement"
            ]
        )
        for fold in references
    ]
    old_b2_vs_hist_gains = [
        float(
            fold["layers"]["old_b2_on_v3_anchor"]["vs_v3_historical"][
                "mae_improvement"
            ]
        )
        for fold in references
    ]

    beats_v2_both = bool(all(value > 0 for value in v3_vs_v2_gains))
    if beats_v2_both:
        decision = "ADVANCE_V3_HORIZON_TO_FIXED_TEMPORAL_PACKAGE_AUDIT"
    else:
        decision = "RETAIN_FROZEN_V2_HORIZON"

    return {
        "horizon": horizon,
        "v3_historical_model_id": v3_historical_model_id(horizon),
        "stage_a_signal": {
            "development_folds": signal_folds,
            "development_aggregate": signal_aggregate,
            "selected_signal_id": selected_signal_id,
            "selection": signal_selection,
        },
        "stage_b_maturity": {
            "development_folds": maturity_folds,
            "development_aggregate": maturity_aggregate,
            "selected_policy_id": (
                "NO_ADJUSTMENT"
                if selected_variant is None
                else f"{selected_variant.id}-min{int(selected_min_prior)}"
            ),
            "selected_variant": (
                None if selected_variant is None else asdict(selected_variant)
            ),
            "selected_min_prior_home_matches": selected_min_prior,
            "selection": maturity_selection,
        },
        "references": references,
        "reference_summary": {
            "v3_final_mae_improvement_vs_frozen_v2": v3_vs_v2_gains,
            "v3_regime_incremental_mae_improvement_vs_v3_historical": (
                regime_vs_hist_gains
            ),
            "old_b2_on_v3_anchor_incremental_mae_improvement": (
                old_b2_vs_hist_gains
            ),
            "beats_frozen_v2_both_references": beats_v2_both,
            "mean_v3_final_gain_vs_frozen_v2": float(
                np.mean(v3_vs_v2_gains)
            ),
            "mean_v3_regime_incremental_gain": float(
                np.mean(regime_vs_hist_gains)
            ),
            "mean_old_b2_on_new_anchor_incremental_gain": float(
                np.mean(old_b2_vs_hist_gains)
            ),
        },
        "decision": decision,
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
            f"historical runtime hash mismatch actual={actual_hash} "
            f"expected={expected_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    results = [horizon_experiment(store, horizon) for horizon in HORIZONS]
    advancing = [
        row["horizon"]
        for row in results
        if row["decision"]
        == "ADVANCE_V3_HORIZON_TO_FIXED_TEMPORAL_PACKAGE_AUDIT"
    ]

    payload = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_PRE_LIVE_V3_REGIME_REVALIDATION",
        "evidence_class": "HISTORICAL_DEVELOPMENT_PLUS_EXPOSED_REFERENCES",
        "promotion_allowed": False,
        "production_change": False,
        "frozen_v2_mutation": False,
        "prospective_events_used_for_selection": False,
        "protocol": {
            "development_folds": [
                {"test_season": season, "training_seasons": train}
                for season, train in DEVELOPMENT_FOLDS
            ],
            "reference_holdouts": [
                {"test_season": season, "training_seasons": train}
                for season, train in REFERENCE_HOLDOUTS
            ],
            "signal_candidate_count": len(VARIANTS),
            "maturity_thresholds": list(ACTIVATION_MIN_PRIOR_HOME_MATCHES),
            "frozen_v2_reproduction_atol": EXPECTED_ATOL,
            "references_used_for_selection": False,
            "event5_or_later_d2_evidence_used": False,
        },
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_hash,
            "manifest_sha256": sha256_file(args.manifest),
            "artifact_version": manifest.get("artifact_version"),
            "feature_contract": manifest.get("feature_contract"),
            "matches": int(store["match_key"].nunique()),
            "feature_rows": int(len(store)),
        },
        "runtime": {
            "random_seed": RANDOM_SEED,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "historical_anchor_contract": {
            horizon: {
                "model_id": v3_historical_model_id(horizon),
                "robust_ensemble": horizon in ROBUST_HISTORICAL_CONTRACTS,
                "members": (
                    list(ROBUST_HISTORICAL_CONTRACTS[horizon].member_ids)
                    if horizon in ROBUST_HISTORICAL_CONTRACTS
                    else None
                ),
                "weights": (
                    list(ROBUST_HISTORICAL_CONTRACTS[horizon].weights)
                    if horizon in ROBUST_HISTORICAL_CONTRACTS
                    else None
                ),
            }
            for horizon in HORIZONS
        },
        "horizons": results,
        "summary": {
            "advancing_horizons": advancing,
            "advancing_count": len(advancing),
            "retained_frozen_v2_horizons": [
                horizon for horizon in HORIZONS if horizon not in advancing
            ],
            "frozen_v2_changed": False,
            "production_changed": False,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "experiment": EXPERIMENT,
        "summary": payload["summary"],
        "horizons": [
            {
                "horizon": row["horizon"],
                "selected_signal": row["stage_a_signal"]["selected_signal_id"],
                "selected_policy": row["stage_b_maturity"]["selected_policy_id"],
                "reference_v3_vs_v2_gains": row["reference_summary"][
                    "v3_final_mae_improvement_vs_frozen_v2"
                ],
                "reference_regime_incremental_gains": row["reference_summary"][
                    "v3_regime_incremental_mae_improvement_vs_v3_historical"
                ],
                "old_b2_on_new_anchor_gains": row["reference_summary"][
                    "old_b2_on_v3_anchor_incremental_mae_improvement"
                ],
                "decision": row["decision"],
            }
            for row in results
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
