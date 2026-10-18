#!/usr/bin/env python3
"""Persistent cross-season club residual calibration v1.

This is an a2 hypothesis, not b2 current-season regime modeling.
Calibration state for a target season is built exclusively from out-of-season
residuals generated on strictly earlier completed seasons.

The correction is a fixed empirical-Bayes club residual estimate with no
holdout-tuned shrinkage hyperparameter:
- residual is capacity-normalized;
- historical residual observations are clipped to +/-25pp capacity for robust
  variance estimation;
- between/within-club variance determines shrinkage toward zero;
- final calibration correction is safety-capped at +/-5pp capacity.

No production artifacts are changed automatically.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor

from ml.demand_engine.freeze_structural_prior_artifacts import (
    EXPECTED_DEVELOPMENT_MAE,
    EXPECTED_HOLDOUT_ATOL,
    EXPECTED_HOLDOUT_MAE,
)
from ml.demand_engine.structural_prior_runtime import (
    CAT,
    CURRENT_EARLY_RUNTIME_SPECS,
    _preprocessor,
    feature_columns,
    fit_structural_prior_runtime,
)
from ml.pre_live_baseline_optimization_v1 import (
    comparison_scorecard,
    eligible_rows,
    load_feature_store,
    metrics,
    sha256_file,
)

EXPERIMENT = "persistent-club-calibration-v1"
WORKSTREAM = "a2 — Historical / Structural Prior optimization"
HORIZONS = ["T-30", "T-14", "T-7", "T-3", "T-1"]
SEASONS = ["2021/2022", "2022/2023", "2023/2024", "2024/2025", "2025/2026"]
TARGET_SEASONS = ["2023/2024", "2024/2025", "2025/2026"]
DEVELOPMENT_SEASON = "2023/2024"
REFERENCE_SEASONS = ["2024/2025", "2025/2026"]
RANDOM_SEED = 42
RESIDUAL_INPUT_CLIP = 0.25
CORRECTION_CAP = 0.05
MIN_CLUB_BREAKDOWN_N = 5

T7_CONFIG = {
    "loss": "absolute_error",
    "learning_rate": 0.04,
    "max_iter": 300,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
    "random_state": RANDOM_SEED,
}
EXPECTED_T7_BASE_MAE = {
    "2023/2024": 2317.3395349341,
    "2024/2025": 1650.9668467459,
    "2025/2026": 1773.7952605858,
}


@dataclass
class T7HistoricalCandidate:
    preprocessor: Any
    estimator: HistGradientBoostingRegressor
    numeric_features: list[str]
    baseline_column: str
    training_rows: int
    training_seasons: list[str]

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        matrix = self.preprocessor.transform(rows[CAT + self.numeric_features])
        residual = self.estimator.predict(matrix)
        capacity = rows["capacity"].astype(float).to_numpy()
        baseline = rows[self.baseline_column].astype(float).to_numpy()
        return np.clip(baseline + residual * capacity, 0.0, capacity)


def fit_t7_historical_candidate(
    store: pd.DataFrame,
    training_seasons: list[str],
) -> T7HistoricalCandidate:
    spec = CURRENT_EARLY_RUNTIME_SPECS["T-7"]
    rows = store[
        (store["horizon"].astype(str) == "T-7")
        & store["training_eligible"].astype(bool)
        & store["season"].isin(training_seasons)
        & store[spec.baseline_column].notna()
    ].copy()
    if rows.empty:
        raise RuntimeError(f"no T-7 training rows for {training_seasons}")

    numeric = feature_columns(store, spec.feature_mode)
    preprocessor = _preprocessor(numeric)
    matrix = preprocessor.fit_transform(rows[CAT + numeric])
    capacity = rows["capacity"].astype(float).to_numpy()
    target = (
        rows["target_attendance"].astype(float).to_numpy() / capacity
        - rows[spec.baseline_column].astype(float).to_numpy() / capacity
    )
    estimator = HistGradientBoostingRegressor(**T7_CONFIG)
    # Exact Stage-3 contract: do not pass uniform sample_weight here.
    estimator.fit(matrix, target)
    return T7HistoricalCandidate(
        preprocessor=preprocessor,
        estimator=estimator,
        numeric_features=numeric,
        baseline_column=spec.baseline_column,
        training_rows=int(len(rows)),
        training_seasons=list(training_seasons),
    )


def fit_base_model(store: pd.DataFrame, horizon: str, training_seasons: list[str]):
    if horizon == "T-7":
        return fit_t7_historical_candidate(store, training_seasons)
    return fit_structural_prior_runtime(store, horizon, training_seasons)


def assert_base_mae(horizon: str, season: str, value: float) -> None:
    if horizon == "T-7" and season in EXPECTED_T7_BASE_MAE:
        expected = EXPECTED_T7_BASE_MAE[season]
        if not np.isclose(value, expected, rtol=0.0, atol=1e-8):
            raise RuntimeError(
                f"T-7 frozen historical base mismatch {season}: actual={value} expected={expected}"
            )
        return

    if season in REFERENCE_SEASONS:
        expected = EXPECTED_HOLDOUT_MAE[horizon][season]
        atol = EXPECTED_HOLDOUT_ATOL[horizon]
        if not np.isclose(value, expected, rtol=0.0, atol=atol):
            raise RuntimeError(
                f"base benchmark mismatch {horizon}/{season}: actual={value} expected={expected}"
            )
        return

    if season == DEVELOPMENT_SEASON and horizon in EXPECTED_DEVELOPMENT_MAE:
        expected = EXPECTED_DEVELOPMENT_MAE[horizon]
        if not np.isclose(value, expected, rtol=0.0, atol=1e-9):
            raise RuntimeError(
                f"base development mismatch {horizon}/{season}: actual={value} expected={expected}"
            )


def rolling_oos_residual_archive(store: pd.DataFrame, horizon: str) -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    for index in range(1, len(SEASONS)):
        test_season = SEASONS[index]
        training_seasons = SEASONS[:index]
        spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
        test = eligible_rows(store, horizon, test_season, spec.baseline_column)
        if test.empty:
            continue
        model = fit_base_model(store, horizon, training_seasons)
        prediction = model.predict(test)
        actual = test["target_attendance"].astype(float).to_numpy()
        capacity = test["capacity"].astype(float).to_numpy()
        frame = pd.DataFrame({
            "horizon": horizon,
            "season": test_season,
            "match_key": test["match_key"].astype(str).to_numpy(),
            "home_club_key": test["home_club_key"].astype(str).to_numpy(),
            "capacity": capacity,
            "actual": actual,
            "base_prediction": prediction,
            "residual_fraction_raw": (actual - prediction) / capacity,
        })
        frame["residual_fraction_clipped"] = np.clip(
            frame["residual_fraction_raw"].astype(float),
            -RESIDUAL_INPUT_CLIP,
            RESIDUAL_INPUT_CLIP,
        )
        records.append(frame)
    if not records:
        raise RuntimeError(f"could not build residual archive for {horizon}")
    return pd.concat(records, ignore_index=True)


def empirical_bayes_state(
    prior_residuals: pd.DataFrame,
    target_season: str,
) -> dict[str, Any]:
    target_index = SEASONS.index(target_season)
    allowed = set(SEASONS[:target_index])
    present = set(prior_residuals["season"].astype(str).unique())
    if not present.issubset(allowed):
        raise RuntimeError(
            f"future/same-season residual leakage for {target_season}: {sorted(present - allowed)}"
        )

    values = prior_residuals["residual_fraction_clipped"].astype(float)
    grouped = prior_residuals.groupby("home_club_key", sort=True)

    within_ss = 0.0
    within_df = 0
    club_stats: dict[str, dict[str, float | int]] = {}
    club_mean_sq_adjusted: list[float] = []

    for club, group in grouped:
        residual = group["residual_fraction_clipped"].astype(float).to_numpy()
        n = int(len(residual))
        mean = float(np.mean(residual))
        if n >= 2:
            within_ss += float(np.sum((residual - mean) ** 2))
            within_df += n - 1
        club_stats[str(club)] = {"n": n, "mean_residual_fraction": mean}

    if within_df > 0:
        within_variance = float(within_ss / within_df)
    else:
        within_variance = float(np.var(values.to_numpy(), ddof=1)) if len(values) > 1 else 0.0

    for stats in club_stats.values():
        n = int(stats["n"])
        mean = float(stats["mean_residual_fraction"])
        club_mean_sq_adjusted.append(mean * mean - within_variance / max(n, 1))

    between_variance = float(max(np.mean(club_mean_sq_adjusted), 0.0)) if club_mean_sq_adjusted else 0.0

    correction_by_club: dict[str, float] = {}
    reliability_by_club: dict[str, float] = {}
    for club, stats in club_stats.items():
        n = int(stats["n"])
        mean = float(stats["mean_residual_fraction"])
        denominator = between_variance + within_variance / max(n, 1)
        reliability = float(between_variance / denominator) if denominator > 0 else 0.0
        correction = float(np.clip(reliability * mean, -CORRECTION_CAP, CORRECTION_CAP))
        reliability_by_club[club] = reliability
        correction_by_club[club] = correction

    return {
        "source_seasons": sorted(present, key=SEASONS.index),
        "residual_rows": int(len(prior_residuals)),
        "clubs": int(len(club_stats)),
        "within_variance": within_variance,
        "between_variance": between_variance,
        "input_residual_clip": RESIDUAL_INPUT_CLIP,
        "correction_cap": CORRECTION_CAP,
        "club_stats": club_stats,
        "reliability_by_club": reliability_by_club,
        "correction_fraction_by_club": correction_by_club,
    }


def score_target_season(
    store: pd.DataFrame,
    archive: pd.DataFrame,
    horizon: str,
    target_season: str,
) -> dict[str, Any]:
    target_index = SEASONS.index(target_season)
    training_seasons = SEASONS[:target_index]
    prior_seasons = set(training_seasons)
    # 2021/22 has no PIT OOS residual because there is no earlier training season.
    prior_archive = archive[
        archive["season"].astype(str).isin(prior_seasons - {"2021/2022"})
    ].copy()
    if prior_archive.empty:
        raise RuntimeError(f"no identifiable prior residual archive for {horizon}/{target_season}")

    state = empirical_bayes_state(prior_archive, target_season)
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    test = eligible_rows(store, horizon, target_season, spec.baseline_column)
    base_model = fit_base_model(store, horizon, training_seasons)
    base_prediction = base_model.predict(test)
    actual = test["target_attendance"].astype(float).to_numpy()
    base_metrics = metrics(actual, base_prediction)
    assert_base_mae(horizon, target_season, float(base_metrics["mae"]))

    capacity = test["capacity"].astype(float).to_numpy()
    clubs = test["home_club_key"].astype(str).to_numpy()
    correction_fraction = np.asarray(
        [state["correction_fraction_by_club"].get(club, 0.0) for club in clubs],
        dtype=float,
    )
    calibrated_prediction = np.clip(
        base_prediction + correction_fraction * capacity,
        0.0,
        capacity,
    )
    score = comparison_scorecard(test, calibrated_prediction, base_prediction)

    known_club = np.asarray([club in state["correction_fraction_by_club"] for club in clubs], dtype=bool)
    nonzero = np.abs(correction_fraction) > 1e-12

    return {
        "horizon": horizon,
        "target_season": target_season,
        "training_seasons": training_seasons,
        "evidence_role": "development" if target_season == DEVELOPMENT_SEASON else "exposed_reference",
        "base_model": (
            "hist31-leaf20-l2-1" if horizon == "T-7" else CURRENT_EARLY_RUNTIME_SPECS[horizon].model_spec_id
        ),
        "test_rows": int(len(test)),
        "base_mae": float(base_metrics["mae"]),
        "state": state,
        "coverage": {
            "rows_with_prior_club_state": int(np.sum(known_club)),
            "share_rows_with_prior_club_state": float(np.mean(known_club)),
            "rows_with_nonzero_correction": int(np.sum(nonzero)),
            "share_rows_with_nonzero_correction": float(np.mean(nonzero)),
            "mean_abs_correction_seats": float(np.mean(np.abs(correction_fraction * capacity))),
            "max_abs_correction_seats": float(np.max(np.abs(correction_fraction * capacity))),
        },
        "scorecard": score,
    }


def horizon_experiment(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    archive = rolling_oos_residual_archive(store, horizon)
    scored = [score_target_season(store, archive, horizon, season) for season in TARGET_SEASONS]
    development = next(row for row in scored if row["target_season"] == DEVELOPMENT_SEASON)
    references = [row for row in scored if row["target_season"] in REFERENCE_SEASONS]

    dev_improvement = float(development["scorecard"]["mae_improvement"])
    ref_improvements = [float(row["scorecard"]["mae_improvement"]) for row in references]
    mean_ref_improvement = float(np.mean(ref_improvements))

    if dev_improvement <= 0:
        signal = "REJECTED_ON_DEVELOPMENT_REFERENCES_CANNOT_RESCUE"
    elif all(value > 0 for value in ref_improvements):
        signal = "POSITIVE_DEVELOPMENT_AND_BOTH_REFERENCES"
    elif mean_ref_improvement > 0:
        signal = "POSITIVE_DEVELOPMENT_POSITIVE_MEAN_MIXED_REFERENCES"
    else:
        signal = "POSITIVE_DEVELOPMENT_NOT_PROVEN_ON_REFERENCES"

    return {
        "horizon": horizon,
        "base_model": development["base_model"],
        "residual_archive_rows": int(len(archive)),
        "residual_archive_seasons": sorted(archive["season"].astype(str).unique(), key=SEASONS.index),
        "development": development,
        "references": references,
        "development_mae_improvement": dev_improvement,
        "reference_mae_improvements": ref_improvements,
        "mean_reference_mae_improvement": mean_ref_improvement,
        "both_references_improve": bool(all(value > 0 for value in ref_improvements)),
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
        "status": "COMPLETED_HISTORICAL_FIXED_CALIBRATION_EVIDENCE",
        "evidence_class": "EXPOSED_HISTORICAL_REFERENCE_SEASONS",
        "promotion_allowed": False,
        "production_change": False,
        "hypothesis_contract": {
            "type": "persistent_cross_season_club_residual_calibration",
            "same_season_residuals_allowed": False,
            "residual_target": "(actual - base_prediction) / verified_capacity",
            "residual_input_clip": RESIDUAL_INPUT_CLIP,
            "shrinkage": "empirical_bayes_between_vs_within_club_variance_toward_zero",
            "correction_cap_fraction_capacity": CORRECTION_CAP,
            "tuned_on_reference_holdouts": False,
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
                "base_model": row["base_model"],
                "development_mae_improvement": row["development_mae_improvement"],
                "mean_reference_mae_improvement": row["mean_reference_mae_improvement"],
                "both_references_improve": row["both_references_improve"],
                "signal": row["signal"],
            }
            for row in results
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
