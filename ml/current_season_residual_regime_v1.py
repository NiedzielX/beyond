#!/usr/bin/env python3
"""b2 current-season residual regime v1.

This experiment asks a materially different question from
`current_season_adjustment_v1`:

    Is the club running above/below what our own current Pre-Live base model
    expected earlier in THIS season?

For each target-season event, the correction state may use only completed
same-season home matches for that club whose `kickoff_at + 3h <= as_of_at`.
This matters especially for early horizons: a nominally earlier fixture is not
usable if it had not completed when the current T-30/T-14/... forecast was
made.

Candidate selection uses 2022/23 and 2023/24 development-era folds only.
2024/25 and 2025/26 are exposed reference seasons scored only after a candidate
is frozen. No production activation occurs automatically.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.demand_engine.freeze_structural_prior_artifacts import (
    EXPECTED_DEVELOPMENT_MAE,
    EXPECTED_HOLDOUT_ATOL,
    EXPECTED_HOLDOUT_MAE,
)
from ml.demand_engine.structural_prior_runtime import (
    CURRENT_EARLY_RUNTIME_SPECS,
    fit_structural_prior_runtime,
)
from ml.pre_live_baseline_optimization_v1 import (
    comparison_scorecard,
    eligible_rows,
    load_feature_store,
    metrics,
    sha256_file,
)
from ml.t7_robust_estimator_v1 import CANDIDATES as T7_CANDIDATES, fit_estimator

EXPERIMENT = "current-season-residual-regime-v1"
WORKSTREAM = "b2 — Current-season residual regime"
HORIZONS = ["T-30", "T-14", "T-7", "T-3", "T-1"]
SEASONS = ["2021/2022", "2022/2023", "2023/2024", "2024/2025", "2025/2026"]
DEVELOPMENT_FOLDS = [
    ("2022/2023", ["2021/2022"]),
    ("2023/2024", ["2021/2022", "2022/2023"]),
]
REFERENCE_HOLDOUTS = [
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]
RANDOM_SEED = 42
COMPLETION_BUFFER_HOURS = 3
RESIDUAL_FRACTION_CLIP = 0.25
DEMAND_RATIO_CLIP = 0.50
CORRECTION_CAP_SHARE_OF_CAPACITY = 0.05
EWMA_ALPHA = 0.50
MIN_MEAN_RELATIVE_MAE_IMPROVEMENT = 0.005
NEAR_BEST_GAIN_RETENTION = 0.90
SELECTION_ATOL = 1e-12

FIXED_T7_ID = "hist31-leaf20-l2-1"
FIXED_T7_SPEC = next(candidate for candidate in T7_CANDIDATES if candidate.id == FIXED_T7_ID)
EXPECTED_T7_BASE_MAE = {
    "2023/2024": 2317.3395349341495,
    "2024/2025": 1650.9668467458935,
    "2025/2026": 1773.7952605857984,
}

SignalSource = Literal["mean_residual_fraction", "ewma_residual_fraction", "mean_demand_ratio"]


@dataclass(frozen=True)
class RegimeVariant:
    source: SignalSource
    shrink_k: int

    @property
    def id(self) -> str:
        source = {
            "mean_residual_fraction": "mean-resid",
            "ewma_residual_fraction": "ewma50-resid",
            "mean_demand_ratio": "mean-ratio",
        }[self.source]
        return f"{source}-k{self.shrink_k}-cap05"


VARIANTS: tuple[RegimeVariant, ...] = tuple(
    RegimeVariant(source=source, shrink_k=shrink_k)
    for source in (
        "mean_residual_fraction",
        "ewma_residual_fraction",
        "mean_demand_ratio",
    )
    for shrink_k in (2, 4, 6)
)


@dataclass
class BasePredictions:
    rows: pd.DataFrame
    prediction: np.ndarray
    model_id: str
    training_rows: int


def fit_base_model(store: pd.DataFrame, horizon: str, training_seasons: list[str]):
    if horizon == "T-7":
        return fit_estimator(store, training_seasons, FIXED_T7_SPEC)
    return fit_structural_prior_runtime(store, horizon, training_seasons)


def base_model_id(horizon: str) -> str:
    if horizon == "T-7":
        return FIXED_T7_ID
    return CURRENT_EARLY_RUNTIME_SPECS[horizon].model_spec_id


def assert_base_mae(horizon: str, season: str, value: float) -> None:
    if horizon == "T-7" and season in EXPECTED_T7_BASE_MAE:
        expected = EXPECTED_T7_BASE_MAE[season]
        if not np.isclose(value, expected, rtol=0.0, atol=1e-9):
            raise RuntimeError(
                f"T-7 frozen historical base mismatch {season}: actual={value} expected={expected}"
            )
        return

    if season in {test for test, _ in REFERENCE_HOLDOUTS}:
        expected = float(EXPECTED_HOLDOUT_MAE[horizon][season])
        atol = float(EXPECTED_HOLDOUT_ATOL[horizon])
        if not np.isclose(value, expected, rtol=0.0, atol=atol):
            raise RuntimeError(
                f"base holdout mismatch {horizon}/{season}: actual={value} expected={expected}"
            )
        return

    if season == "2023/2024" and horizon in EXPECTED_DEVELOPMENT_MAE:
        expected = float(EXPECTED_DEVELOPMENT_MAE[horizon])
        if not np.isclose(value, expected, rtol=0.0, atol=1e-9):
            raise RuntimeError(
                f"base development mismatch {horizon}/{season}: actual={value} expected={expected}"
            )


def base_predictions_for_season(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
) -> BasePredictions:
    runtime_spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = eligible_rows(store, horizon, season, runtime_spec.baseline_column)
    if rows.empty:
        raise RuntimeError(f"no eligible rows for {horizon}/{season}")
    model = fit_base_model(store, horizon, training_seasons)
    prediction = np.asarray(model.predict(rows), dtype=float)
    base_mae = float(metrics(rows["target_attendance"], prediction)["mae"])
    assert_base_mae(horizon, season, base_mae)
    return BasePredictions(
        rows=rows,
        prediction=prediction,
        model_id=base_model_id(horizon),
        training_rows=int(model.training_rows),
    )


def add_same_season_residual_state(
    rows: pd.DataFrame,
    base_prediction: np.ndarray,
) -> pd.DataFrame:
    """Build PIT-safe same-season regime state for every target row.

    Residual state updates only on a completion event at kickoff + 3 hours.
    Snapshot events are ordered before completion events at the same timestamp,
    matching the canonical feature-store convention.
    """
    out = rows.copy().reset_index(drop=True)
    prediction = np.asarray(base_prediction, dtype=float)
    if len(out) != len(prediction):
        raise ValueError("rows and base_prediction length mismatch")

    for column in ("as_of_at", "kickoff_at"):
        if column not in out.columns:
            raise RuntimeError(f"missing required PIT column {column}")
        out[column] = pd.to_datetime(out[column], utc=True)

    actual = out["target_attendance"].astype(float).to_numpy()
    capacity = out["capacity"].astype(float).to_numpy()
    residual_fraction = np.clip(
        (actual - prediction) / capacity,
        -RESIDUAL_FRACTION_CLIP,
        RESIDUAL_FRACTION_CLIP,
    )
    demand_ratio = np.zeros(len(out), dtype=float)
    valid_base = prediction > 0.0
    demand_ratio[valid_base] = np.clip(
        actual[valid_base] / prediction[valid_base] - 1.0,
        -DEMAND_RATIO_CLIP,
        DEMAND_RATIO_CLIP,
    )

    events: list[tuple[pd.Timestamp, int, str, int]] = []
    for index, row in out.iterrows():
        events.append((row["as_of_at"], 0, "snapshot", int(index)))
        completed_at = row["kickoff_at"] + pd.Timedelta(hours=COMPLETION_BUFFER_HOURS)
        events.append((completed_at, 1, "complete", int(index)))
    events.sort(key=lambda item: (item[0], item[1], item[3]))

    state: dict[str, dict[str, Any]] = {}
    regime_n = np.zeros(len(out), dtype=int)
    regime_mean_residual = np.zeros(len(out), dtype=float)
    regime_ewma_residual = np.zeros(len(out), dtype=float)
    regime_mean_ratio = np.zeros(len(out), dtype=float)
    latest_completion = np.full(len(out), np.datetime64("NaT"), dtype="datetime64[ns]")

    for timestamp, _, event_type, index in events:
        club = str(out.at[index, "home_club_key"])
        club_state = state.setdefault(
            club,
            {
                "n": 0,
                "sum_residual": 0.0,
                "sum_ratio": 0.0,
                "ewma_residual": 0.0,
                "latest_completed_at": None,
            },
        )
        if event_type == "complete":
            n_before = int(club_state["n"])
            value = float(residual_fraction[index])
            club_state["n"] = n_before + 1
            club_state["sum_residual"] = float(club_state["sum_residual"]) + value
            club_state["sum_ratio"] = float(club_state["sum_ratio"]) + float(demand_ratio[index])
            club_state["ewma_residual"] = (
                value
                if n_before == 0
                else EWMA_ALPHA * value
                + (1.0 - EWMA_ALPHA) * float(club_state["ewma_residual"])
            )
            club_state["latest_completed_at"] = timestamp
            continue

        n = int(club_state["n"])
        regime_n[index] = n
        if n > 0:
            regime_mean_residual[index] = float(club_state["sum_residual"]) / n
            regime_ewma_residual[index] = float(club_state["ewma_residual"])
            regime_mean_ratio[index] = float(club_state["sum_ratio"]) / n
            latest = club_state["latest_completed_at"]
            if latest is not None:
                latest_completion[index] = latest.tz_convert("UTC").tz_localize(None).to_datetime64()

    out["regime_prior_home_matches"] = regime_n
    out["regime_mean_residual_fraction"] = regime_mean_residual
    out["regime_ewma_residual_fraction"] = regime_ewma_residual
    out["regime_mean_demand_ratio"] = regime_mean_ratio
    out["regime_latest_completed_at"] = pd.to_datetime(latest_completion, utc=True)

    leaked = out[
        out["regime_latest_completed_at"].notna()
        & (out["regime_latest_completed_at"] > out["as_of_at"])
    ]
    if not leaked.empty:
        raise RuntimeError("same-season residual state contains future completion leakage")

    return out


def variant_signal(rows: pd.DataFrame, variant: RegimeVariant) -> np.ndarray:
    if variant.source == "mean_residual_fraction":
        return rows["regime_mean_residual_fraction"].astype(float).to_numpy()
    if variant.source == "ewma_residual_fraction":
        return rows["regime_ewma_residual_fraction"].astype(float).to_numpy()
    if variant.source == "mean_demand_ratio":
        return rows["regime_mean_demand_ratio"].astype(float).to_numpy()
    raise KeyError(variant.source)


def apply_variant(
    rows: pd.DataFrame,
    base_prediction: np.ndarray,
    variant: RegimeVariant,
) -> tuple[np.ndarray, dict[str, Any]]:
    base = np.asarray(base_prediction, dtype=float)
    capacity = rows["capacity"].astype(float).to_numpy()
    n = rows["regime_prior_home_matches"].astype(float).to_numpy()
    signal = variant_signal(rows, variant)
    shrink = np.where(n > 0.0, n / (n + float(variant.shrink_k)), 0.0)

    if variant.source == "mean_demand_ratio":
        raw_delta = shrink * signal * base
    else:
        raw_delta = shrink * signal * capacity

    cap = CORRECTION_CAP_SHARE_OF_CAPACITY * capacity
    delta = np.clip(raw_delta, -cap, cap)
    adjusted = np.clip(base + delta, 0.0, capacity)
    active = np.abs(delta) > 1e-12

    return adjusted, {
        "rows": int(len(rows)),
        "rows_with_prior_home_match": int(np.sum(n > 0)),
        "share_with_prior_home_match": float(np.mean(n > 0)) if len(n) else 0.0,
        "active_correction_rows": int(np.sum(active)),
        "active_correction_share": float(np.mean(active)) if len(active) else 0.0,
        "mean_abs_correction_seats": float(np.mean(np.abs(delta))) if len(delta) else 0.0,
        "median_abs_correction_seats": float(np.median(np.abs(delta))) if len(delta) else 0.0,
        "max_abs_correction_seats": float(np.max(np.abs(delta))) if len(delta) else 0.0,
        "mean_abs_correction_share_capacity": float(np.mean(np.abs(delta) / capacity)) if len(delta) else 0.0,
    }


def prior_count_bucket(n: int) -> str:
    if n <= 0:
        return "0"
    if n == 1:
        return "1"
    if n == 2:
        return "2"
    return "3+"


def conditional_scorecard(
    rows: pd.DataFrame,
    candidate_prediction: np.ndarray,
    base_prediction: np.ndarray,
) -> dict[str, Any]:
    actual = rows["target_attendance"].astype(float).to_numpy()
    candidate = np.asarray(candidate_prediction, dtype=float)
    base = np.asarray(base_prediction, dtype=float)
    buckets = rows["regime_prior_home_matches"].astype(int).map(prior_count_bucket)
    result: dict[str, Any] = {}
    for bucket in ("0", "1", "2", "3+"):
        mask = buckets.eq(bucket).to_numpy()
        if not np.any(mask):
            result[bucket] = {"n": 0}
            continue
        incumbent_metrics = metrics(actual[mask], base[mask])
        candidate_metrics = metrics(actual[mask], candidate[mask])
        result[bucket] = {
            "n": int(np.sum(mask)),
            "base_mae": float(incumbent_metrics["mae"]),
            "candidate_mae": float(candidate_metrics["mae"]),
            "mae_improvement": float(incumbent_metrics["mae"] - candidate_metrics["mae"]),
            "base_bias": float(incumbent_metrics["bias"]),
            "candidate_bias": float(candidate_metrics["bias"]),
        }
    return result


def score_variant(
    rows: pd.DataFrame,
    base_prediction: np.ndarray,
    variant: RegimeVariant,
) -> dict[str, Any]:
    adjusted, diagnostics = apply_variant(rows, base_prediction, variant)
    score = comparison_scorecard(rows, adjusted, base_prediction)
    return {
        "variant": asdict(variant),
        "variant_id": variant.id,
        "diagnostics": diagnostics,
        "scorecard": score,
        "conditional_by_prior_home_matches": conditional_scorecard(rows, adjusted, base_prediction),
    }


def no_adjustment_score(rows: pd.DataFrame, base_prediction: np.ndarray) -> dict[str, Any]:
    score = comparison_scorecard(rows, base_prediction, base_prediction)
    return {
        "variant": None,
        "variant_id": "NO_ADJUSTMENT",
        "diagnostics": {
            "rows": int(len(rows)),
            "rows_with_prior_home_match": int(np.sum(rows["regime_prior_home_matches"].astype(int) > 0)),
            "active_correction_rows": 0,
            "active_correction_share": 0.0,
            "mean_abs_correction_seats": 0.0,
            "median_abs_correction_seats": 0.0,
            "max_abs_correction_seats": 0.0,
            "mean_abs_correction_share_capacity": 0.0,
        },
        "scorecard": score,
        "conditional_by_prior_home_matches": conditional_scorecard(rows, base_prediction, base_prediction),
    }


def score_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    variants: list[RegimeVariant] | tuple[RegimeVariant, ...],
) -> dict[str, Any]:
    base = base_predictions_for_season(store, horizon, season, training_seasons)
    rows = add_same_season_residual_state(base.rows, base.prediction)
    scored = {"NO_ADJUSTMENT": no_adjustment_score(rows, base.prediction)}
    for variant in variants:
        scored[variant.id] = score_variant(rows, base.prediction, variant)
    return {
        "horizon": horizon,
        "season": season,
        "training_seasons": list(training_seasons),
        "base_model_id": base.model_id,
        "base_training_rows": base.training_rows,
        "test_rows": int(len(rows)),
        "base_mae": float(scored["NO_ADJUSTMENT"]["scorecard"]["incumbent"]["mae"]),
        "regime_availability": {
            "rows_prior_0": int(np.sum(rows["regime_prior_home_matches"].astype(int) == 0)),
            "rows_prior_1": int(np.sum(rows["regime_prior_home_matches"].astype(int) == 1)),
            "rows_prior_2": int(np.sum(rows["regime_prior_home_matches"].astype(int) == 2)),
            "rows_prior_3_plus": int(np.sum(rows["regime_prior_home_matches"].astype(int) >= 3)),
        },
        "candidates": scored,
    }


def aggregate_development(
    folds: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidate_ids = ["NO_ADJUSTMENT", *[variant.id for variant in VARIANTS]]
    result = []
    for candidate_id in candidate_ids:
        fold_rows = []
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
                    score["candidate"]["median_ae"] - score["incumbent"]["median_ae"]
                ),
                "p90_ae_delta": float(
                    score["candidate"]["p90_ae"] - score["incumbent"]["p90_ae"]
                ),
                "worst_event_degradation": float(score["worst_event_degradation"]),
                "event_improvement_rate": float(score["event_improvement_rate"]),
            })
        mean_inc = float(np.mean([row["incumbent_mae"] for row in fold_rows]))
        mean_cand = float(np.mean([row["candidate_mae"] for row in fold_rows]))
        improvement = mean_inc - mean_cand
        result.append({
            "candidate_id": candidate_id,
            "variant": None if candidate_id == "NO_ADJUSTMENT" else asdict(
                next(variant for variant in VARIANTS if variant.id == candidate_id)
            ),
            "folds": fold_rows,
            "all_development_folds_improve": bool(all(row["mae_improvement"] > 0 for row in fold_rows)),
            "mean_incumbent_mae": mean_inc,
            "mean_candidate_mae": mean_cand,
            "mean_mae_improvement": float(improvement),
            "mean_relative_mae_improvement": float(improvement / mean_inc),
            "mean_median_ae_delta": float(np.mean([row["median_ae_delta"] for row in fold_rows])),
            "mean_p90_ae_delta": float(np.mean([row["p90_ae_delta"] for row in fold_rows])),
            "max_worst_event_degradation": float(np.max([row["worst_event_degradation"] for row in fold_rows])),
            "mean_event_improvement_rate": float(np.mean([row["event_improvement_rate"] for row in fold_rows])),
        })
    return result


def select_candidate(development: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    incumbent = next(row for row in development if row["candidate_id"] == "NO_ADJUSTMENT")
    eligible = [
        row for row in development
        if row["candidate_id"] != "NO_ADJUSTMENT"
        and row["all_development_folds_improve"]
        and row["mean_relative_mae_improvement"] + SELECTION_ATOL >= MIN_MEAN_RELATIVE_MAE_IMPROVEMENT
    ]
    if not eligible:
        return "NO_ADJUSTMENT", {
            "reason": "NO_REGIME_VARIANT_MEETS_TWO_FOLD_STABILITY_GATE",
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
            -float(row["mean_event_improvement_rate"]),
            str(row["candidate_id"]),
        ),
    )
    return str(selected["candidate_id"]), {
        "reason": "TWO_FOLD_0P5PCT_GATE_THEN_90PCT_GAIN_RETENTION_AND_TAIL_MINIMIZATION",
        "best_mean_mae_improvement": float(best_gain),
        "near_best_required_improvement": float(NEAR_BEST_GAIN_RETENTION * best_gain),
        "eligible_candidate_ids": [str(row["candidate_id"]) for row in eligible],
        "near_best_candidate_ids": [str(row["candidate_id"]) for row in near_best],
        "selected_row": selected,
    }


def horizon_experiment(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    development_folds = [
        score_fold(store, horizon, season, train, VARIANTS)
        for season, train in DEVELOPMENT_FOLDS
    ]
    aggregate = aggregate_development(development_folds)
    selected_id, selection = select_candidate(aggregate)

    selected_variant = None
    if selected_id != "NO_ADJUSTMENT":
        selected_variant = next(variant for variant in VARIANTS if variant.id == selected_id)
    reference_variants: list[RegimeVariant] = [] if selected_variant is None else [selected_variant]

    references = [
        score_fold(store, horizon, season, train, reference_variants)
        for season, train in REFERENCE_HOLDOUTS
    ]
    reference_rows = []
    for fold in references:
        score = fold["candidates"][selected_id]["scorecard"]
        reference_rows.append({
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
            "conditional_by_prior_home_matches": fold["candidates"][selected_id]["conditional_by_prior_home_matches"],
            "diagnostics": fold["candidates"][selected_id]["diagnostics"],
            "regime_availability": fold["regime_availability"],
        })

    mean_base = float(np.mean([row["base_mae"] for row in reference_rows]))
    mean_selected = float(np.mean([row["selected_mae"] for row in reference_rows]))
    mean_improvement = mean_base - mean_selected
    both_positive = bool(all(row["mae_improvement"] > 0 for row in reference_rows))

    if selected_id == "NO_ADJUSTMENT":
        signal = "NO_STABLE_CURRENT_SEASON_REGIME_ON_DEVELOPMENT"
    elif both_positive and mean_improvement > 0:
        signal = "STABLE_DEV_REGIME_POSITIVE_BOTH_REFERENCES"
    elif mean_improvement > 0:
        signal = "STABLE_DEV_REGIME_POSITIVE_MEAN_MIXED_REFERENCES"
    else:
        signal = "STABLE_DEV_REGIME_NOT_PROVEN_ON_REFERENCES"

    return {
        "horizon": horizon,
        "base_model_id": base_model_id(horizon),
        "candidate_count_nonzero": len(VARIANTS),
        "development_folds": development_folds,
        "development_aggregate": aggregate,
        "selection": selection,
        "selected_candidate_id": selected_id,
        "selected_variant": None if selected_variant is None else asdict(selected_variant),
        "references": references,
        "reference_summary": reference_rows,
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
    parser.add_argument("--horizons", default=",".join(HORIZONS))
    args = parser.parse_args()

    requested = [item.strip() for item in args.horizons.split(",") if item.strip()]
    invalid = sorted(set(requested) - set(HORIZONS))
    if invalid:
        raise ValueError(f"unsupported horizons: {invalid}")

    manifest = json.loads(args.manifest.read_text())
    expected_hash = manifest["historical_runtime"]["sha256"]
    actual_hash = sha256_file(args.historical_runtime)
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    results = [horizon_experiment(store, horizon) for horizon in requested]

    payload = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_HISTORICAL_CURRENT_SEASON_REGIME_EVIDENCE",
        "evidence_class": "EXPOSED_HISTORICAL_REFERENCE_SEASONS",
        "promotion_allowed": False,
        "production_change": False,
        "hypothesis_contract": {
            "question": "does same-season completed-match model error reveal a current demand regime shift?",
            "completion_rule": "prior match may enter state only at kickoff_at + 3h <= current as_of_at",
            "sources": [
                "mean_residual_fraction",
                "ewma50_residual_fraction",
                "mean_demand_ratio",
            ],
            "shrink_k": [2, 4, 6],
            "residual_fraction_clip": RESIDUAL_FRACTION_CLIP,
            "demand_ratio_clip": DEMAND_RATIO_CLIP,
            "correction_cap_share_capacity": CORRECTION_CAP_SHARE_OF_CAPACITY,
            "ewma_alpha": EWMA_ALPHA,
            "minimum_prior_home_matches": 1,
            "minimum_mean_relative_dev_mae_improvement": MIN_MEAN_RELATIVE_MAE_IMPROVEMENT,
            "near_best_gain_retention": NEAR_BEST_GAIN_RETENTION,
            "holdouts_used_for_selection": False,
        },
        "protocol": {
            "development_folds": [
                {"test_season": season, "training_seasons": train}
                for season, train in DEVELOPMENT_FOLDS
            ],
            "reference_holdouts": [
                {"test_season": season, "training_seasons": train}
                for season, train in REFERENCE_HOLDOUTS
            ],
            "event_is_independent_unit": True,
            "target_season_residual_state_is_chronological": True,
            "future_or_uncompleted_match_outcomes_allowed": False,
            "same_season_completed_match_outcomes_allowed": True,
        },
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_hash,
            "manifest_path": str(args.manifest),
            "artifact_version": manifest.get("artifact_version"),
            "feature_contract": manifest.get("feature_contract"),
            "historical_dataset_versions": manifest.get("historical_dataset_versions"),
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
                "base_model_id": row["base_model_id"],
                "selected_candidate_id": row["selected_candidate_id"],
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
