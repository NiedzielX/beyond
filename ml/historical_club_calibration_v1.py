#!/usr/bin/env python3
"""Fixed cross-season home-club residual calibration audit.

This is the final major a2 historical hypothesis before b2.

The policy is deliberately fixed before evidence:
- generate out-of-season residuals from rolling per-horizon historical models;
- use ONLY prior completed seasons as calibration history;
- estimate a robust home-club normalized residual median;
- shrink toward zero with n/(n+10);
- require >=5 historical residual observations;
- cap correction at +/-5% verified capacity;
- never use residuals from the target season itself.

T-7 keeps the exact frozen historical candidate estimator. Other horizons keep
current production incumbents. Calibration is a separate layer, not estimator
retuning. No automatic production promotion occurs.
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
from ml.t7_robust_estimator_v1 import CANDIDATES, fit_estimator

EXPERIMENT = "historical-club-calibration-v1"
WORKSTREAM = "a2 — Historical / Structural Prior optimization — fixed cross-season club calibration"
RANDOM_SEED = 42
HORIZONS = ("T-30", "T-14", "T-7", "T-3", "T-1")

ROLLING_SEASONS = (
    ("2022/2023", ["2021/2022"], "warmup_residual_source"),
    ("2023/2024", ["2021/2022", "2022/2023"], "development_evaluation"),
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"], "exposed_reference"),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"], "exposed_reference"),
)
EVALUATION_SEASONS = ("2023/2024", "2024/2025", "2025/2026")

CALIBRATION_ID = "club-median-residual-ratio-k10-cap05-min5"
SHRINKAGE_K = 10.0
CAP_FRACTION = 0.05
MIN_HISTORY_OBSERVATIONS = 5

T7_CANDIDATE_ID = "hist31-leaf20-l2-1"
T7_CANDIDATE = next(candidate for candidate in CANDIDATES if candidate.id == T7_CANDIDATE_ID)

# Exact already-canonical base-model reproduction gates.
EXPECTED_BASE_MAE: dict[str, dict[str, float]] = {
    "T-30": {
        "2023/2024": 2559.7406941266854,
        "2024/2025": 1889.3672272292858,
        "2025/2026": 1846.2792557036205,
    },
    "T-14": {
        "2023/2024": 2339.9504993283904,
        "2024/2025": 1748.4970512511325,
        "2025/2026": 1870.393553818474,
    },
    "T-7": {
        "2022/2023": 1984.99095713069,
        "2023/2024": 2317.3395349341495,
        "2024/2025": 1650.9668467458935,
        "2025/2026": 1773.7952605857984,
    },
    "T-3": {
        "2023/2024": 2311.6246893162593,
        "2024/2025": 1661.715966441126,
        "2025/2026": 1775.069078799718,
    },
    "T-1": {
        "2023/2024": 2347.9931110468183,
        "2024/2025": 1651.733625020056,
        "2025/2026": 1742.835142803119,
    },
}
EXPECTED_ATOL = 1e-9


def fit_base_model(store: pd.DataFrame, horizon: str, training_seasons: list[str]):
    if horizon == "T-7":
        return fit_estimator(store, training_seasons, T7_CANDIDATE)
    return fit_structural_prior_runtime(store, horizon, training_seasons)


def verify_base_mae(horizon: str, season: str, mae: float) -> None:
    expected = EXPECTED_BASE_MAE.get(horizon, {}).get(season)
    if expected is None:
        return
    if not np.isclose(mae, expected, rtol=0.0, atol=EXPECTED_ATOL):
        raise RuntimeError(
            f"base-model reproduction mismatch {horizon}/{season}: actual={mae} expected={expected}"
        )


def score_rolling_base(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    evidence_role: str,
) -> pd.DataFrame:
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = eligible_rows(store, horizon, season, spec.baseline_column)
    if rows.empty:
        raise RuntimeError(f"empty base scoring split {horizon}/{season}")
    model = fit_base_model(store, horizon, training_seasons)
    prediction = model.predict(rows)
    actual = rows["target_attendance"].astype(float).to_numpy()
    base_metrics = metrics(actual, prediction)
    verify_base_mae(horizon, season, float(base_metrics["mae"]))

    frame = pd.DataFrame({
        "horizon": horizon,
        "season": season,
        "evidence_role": evidence_role,
        "match_key": rows["match_key"].astype(str).to_numpy(),
        "home_club_key": rows["home_club_key"].astype(str).to_numpy(),
        "away_club_key": rows["away_club_key"].astype(str).to_numpy(),
        "kickoff_at": pd.to_datetime(rows["kickoff_at"], utc=True).to_numpy(),
        "capacity": rows["capacity"].astype(float).to_numpy(),
        "actual": actual,
        "base_prediction": np.asarray(prediction, dtype=float),
    })
    frame["base_residual"] = frame["actual"] - frame["base_prediction"]
    frame["base_residual_ratio"] = frame["base_residual"] / frame["capacity"]
    return frame


def calibration_state(history: pd.DataFrame) -> dict[str, dict[str, float | int]]:
    state: dict[str, dict[str, float | int]] = {}
    if history.empty:
        return state
    for club, group in history.groupby("home_club_key", sort=True):
        ratios = group["base_residual_ratio"].astype(float).to_numpy()
        n = int(len(ratios))
        median_ratio = float(np.median(ratios))
        shrinkage = float(n / (n + SHRINKAGE_K))
        shrunk = median_ratio * shrinkage
        bounded = float(np.clip(shrunk, -CAP_FRACTION, CAP_FRACTION))
        state[str(club)] = {
            "n": n,
            "median_residual_ratio": median_ratio,
            "shrinkage": shrinkage,
            "shrunk_residual_ratio": shrunk,
            "bounded_correction_ratio": bounded,
            "active": bool(n >= MIN_HISTORY_OBSERVATIONS),
        }
    return state


def apply_calibration(rows: pd.DataFrame, state: dict[str, dict[str, float | int]]) -> tuple[np.ndarray, pd.DataFrame]:
    corrections = []
    active = []
    history_n = []
    for club, capacity in zip(rows["home_club_key"].astype(str), rows["capacity"].astype(float), strict=True):
        item = state.get(club)
        if item is None or not bool(item["active"]):
            ratio = 0.0
            n = 0 if item is None else int(item["n"])
            flag = False
        else:
            ratio = float(item["bounded_correction_ratio"])
            n = int(item["n"])
            flag = True
        corrections.append(ratio * capacity)
        active.append(flag)
        history_n.append(n)

    correction = np.asarray(corrections, dtype=float)
    base = rows["base_prediction"].astype(float).to_numpy()
    capacity = rows["capacity"].astype(float).to_numpy()
    prediction = np.clip(base + correction, 0.0, capacity)
    detail = pd.DataFrame({
        "match_key": rows["match_key"].astype(str).to_numpy(),
        "home_club_key": rows["home_club_key"].astype(str).to_numpy(),
        "correction_seats": correction,
        "correction_abs_share_capacity": np.abs(correction) / capacity,
        "active": active,
        "history_n": history_n,
    })
    return prediction, detail


def season_score(
    season_rows: pd.DataFrame,
    history_rows: pd.DataFrame,
) -> dict[str, Any]:
    state = calibration_state(history_rows)
    calibrated_prediction, detail = apply_calibration(season_rows, state)
    base_prediction = season_rows["base_prediction"].astype(float).to_numpy()
    actual = season_rows["actual"].astype(float).to_numpy()

    score_rows = pd.DataFrame({
        "target_attendance": actual,
        "home_club_key": season_rows["home_club_key"].astype(str).to_numpy(),
        "away_club_key": season_rows["away_club_key"].astype(str).to_numpy(),
        "match_key": season_rows["match_key"].astype(str).to_numpy(),
    })
    score = comparison_scorecard(score_rows, calibrated_prediction, base_prediction)

    active = detail[detail["active"]].copy()
    club_state = {
        club: value
        for club, value in state.items()
        if int(value["n"]) >= MIN_HISTORY_OBSERVATIONS
    }

    club_rows = []
    for club, group in score_rows.assign(
        base_prediction=base_prediction,
        calibrated_prediction=calibrated_prediction,
    ).groupby("home_club_key", sort=True):
        y = group["target_attendance"].astype(float).to_numpy()
        bp = group["base_prediction"].astype(float).to_numpy()
        cp = group["calibrated_prediction"].astype(float).to_numpy()
        base_mae = float(np.mean(np.abs(bp - y)))
        cal_mae = float(np.mean(np.abs(cp - y)))
        club_rows.append({
            "club": str(club),
            "n": int(len(group)),
            "base_mae": base_mae,
            "calibrated_mae": cal_mae,
            "mae_improvement": base_mae - cal_mae,
            "calibration_state": club_state.get(str(club)),
        })

    return {
        "scorecard": score,
        "history_rows": int(len(history_rows)),
        "history_seasons": sorted(history_rows["season"].astype(str).unique().tolist()) if not history_rows.empty else [],
        "clubs_with_state": int(len(state)),
        "clubs_with_active_calibration": int(len(club_state)),
        "event_active_calibration_rate": float(detail["active"].mean()),
        "correction": {
            "mean_abs_seats": float(active["correction_seats"].abs().mean()) if not active.empty else 0.0,
            "median_abs_seats": float(active["correction_seats"].abs().median()) if not active.empty else 0.0,
            "p90_abs_seats": float(active["correction_seats"].abs().quantile(0.90)) if not active.empty else 0.0,
            "max_abs_seats": float(active["correction_seats"].abs().max()) if not active.empty else 0.0,
            "mean_abs_share_capacity": float(active["correction_abs_share_capacity"].mean()) if not active.empty else 0.0,
            "max_abs_share_capacity": float(active["correction_abs_share_capacity"].max()) if not active.empty else 0.0,
        },
        "club_breakdown": club_rows,
    }


def horizon_experiment(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    rolling_frames: list[pd.DataFrame] = []
    rolling_meta: list[dict[str, Any]] = []

    for season, training_seasons, role in ROLLING_SEASONS:
        frame = score_rolling_base(store, horizon, season, training_seasons, role)
        rolling_frames.append(frame)
        rolling_meta.append({
            "season": season,
            "training_seasons": list(training_seasons),
            "evidence_role": role,
            "rows": int(len(frame)),
            "base_mae": float(np.mean(np.abs(frame["base_prediction"] - frame["actual"]))),
        })

    by_season = {frame["season"].iloc[0]: frame for frame in rolling_frames}
    evaluations: dict[str, Any] = {}
    for season in EVALUATION_SEASONS:
        prior = pd.concat(
            [frame for frame in rolling_frames if str(frame["season"].iloc[0]) < season],
            ignore_index=True,
        )
        # The lexical season labels are chronological in YYYY/YYYY form here.
        target = by_season[season]
        evaluations[season] = season_score(target, prior)

    improvements = [
        float(evaluations[season]["scorecard"]["mae_improvement"])
        for season in EVALUATION_SEASONS
    ]
    mean_improvement = float(np.mean(improvements))
    all_improve = bool(all(value > 0.0 for value in improvements))

    if all_improve and mean_improvement > 0.0:
        signal = "FIXED_CLUB_CALIBRATION_IMPROVES_ALL_EVALUATION_SEASONS"
    elif mean_improvement > 0.0:
        signal = "FIXED_CLUB_CALIBRATION_POSITIVE_MEAN_MIXED_SEASONS"
    else:
        signal = "FIXED_CLUB_CALIBRATION_NOT_PROVEN"

    return {
        "horizon": horizon,
        "base_model": (
            T7_CANDIDATE_ID if horizon == "T-7"
            else CURRENT_EARLY_RUNTIME_SPECS[horizon].model_spec_id
        ),
        "rolling_base_scoring": rolling_meta,
        "evaluations": evaluations,
        "evaluation_mae_improvements": improvements,
        "mean_evaluation_mae_improvement": mean_improvement,
        "all_evaluation_seasons_improve": all_improve,
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
    actual_hash = sha256_file(args.historical_runtime)
    expected_hash = manifest["historical_runtime"]["sha256"]
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    horizons = [horizon_experiment(store, horizon) for horizon in HORIZONS]

    result = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_FIXED_HISTORICAL_CLUB_CALIBRATION_EVIDENCE",
        "evidence_class": "FIXED_POLICY_DEVELOPMENT_PLUS_EXPOSED_REFERENCES",
        "promotion_allowed": False,
        "production_change": False,
        "policy": {
            "id": CALIBRATION_ID,
            "source": "prior completed seasons only",
            "residual": "(actual - rolling_base_prediction) / verified_capacity",
            "club_statistic": "median residual ratio",
            "shrinkage": "n / (n + 10)",
            "shrinkage_k": SHRINKAGE_K,
            "minimum_history_observations": MIN_HISTORY_OBSERVATIONS,
            "cap_fraction_capacity": CAP_FRACTION,
            "target_season_residuals_allowed": False,
            "league_fallback": 0.0,
            "hyperparameter_selection_in_this_experiment": False,
        },
        "protocol": {
            "rolling_seasons": [
                {"season": season, "training_seasons": train, "role": role}
                for season, train, role in ROLLING_SEASONS
            ],
            "evaluation_seasons": list(EVALUATION_SEASONS),
            "2022_23_role": "warm-up residual source only; no prior-season calibration history exists",
            "references_already_exposed": True,
            "future_leakage_allowed": False,
            "same_target_season_residuals_used": False,
            "t7_estimator_retuned": False,
        },
        "input": {
            "historical_runtime_sha256": actual_hash,
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
        "expected_base_mae_assertions": EXPECTED_BASE_MAE,
        "horizons": horizons,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "policy": CALIBRATION_ID,
        "promotion_allowed": False,
        "horizons": [
            {
                "horizon": item["horizon"],
                "base_model": item["base_model"],
                "signal": item["signal"],
                "improvements": item["evaluation_mae_improvements"],
                "mean_improvement": item["mean_evaluation_mae_improvement"],
            }
            for item in horizons
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
