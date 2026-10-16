#!/usr/bin/env python3
"""T-30 v6: explicit baseline-occupancy state.

Pre-registered hypothesis from the rolling-origin error audit:
The T-30 target is an occupancy residual but the estimator currently receives
`baseline_season` and `capacity` only as separate features. Add the explicit
PIT-safe ratio `baseline_season / verified_capacity` while keeping every other
production choice fixed.

This script scores only rolling-origin 2022/23 and 2023/24 development folds.
It never scores 2024/25 or 2025/26 and never mutates production.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

from ml.demand_engine.structural_prior_runtime import CAT, feature_columns, fit_structural_prior_runtime
from ml.features.structural_prior_feature_store_v1 import WARSAW_TZ, build_feature_store

HORIZON = "T-30"
BASELINE = "baseline_season"
NEW_FEATURE = "baseline_occupancy"
MATERIAL_GATE = 0.03
FORBIDDEN = {"2024/2025", "2025/2026"}


@dataclass(frozen=True)
class Fold:
    name: str
    train_seasons: tuple[str, ...]
    eval_season: str


FOLDS = (
    Fold("A", ("2021/2022",), "2022/2023"),
    Fold("B", ("2021/2022", "2022/2023"), "2023/2024"),
)


def canonical_matches(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    local = pd.to_datetime(
        pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
        + " "
        + frame["kickoff_time_local"].astype(str),
        format="mixed",
    )
    frame["kickoff_at"] = local.dt.tz_localize(
        WARSAW_TZ, ambiguous="raise", nonexistent="raise"
    ).dt.tz_convert("UTC")
    frame["completed_at"] = frame["kickoff_at"] + pd.Timedelta(hours=3)
    frame["training_eligible"] = frame["attendance"].astype(float) != 0
    frame["round"] = frame["round"].astype(int)
    return frame.sort_values(["kickoff_at", "home_club_key"]).reset_index(drop=True)


def add_feature(store: pd.DataFrame) -> pd.DataFrame:
    out = store.copy()
    baseline = pd.to_numeric(out[BASELINE], errors="coerce")
    capacity = pd.to_numeric(out["capacity"], errors="coerce")
    out[NEW_FEATURE] = baseline / capacity
    invalid = out[BASELINE].notna() & (
        out[NEW_FEATURE].isna() | ~np.isfinite(out[NEW_FEATURE]) | (capacity <= 0)
    )
    if invalid.any():
        raise RuntimeError("baseline_occupancy invalid for eligible baseline rows")
    return out


def preprocessor(numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
        ("num", SimpleImputer(strategy="median", add_indicator=True), numeric),
    ])


def metrics(actual, prediction) -> dict:
    actual = np.asarray(actual, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    error = prediction - actual
    ae = np.abs(error)
    return {
        "n": int(len(actual)),
        "mae": float(np.mean(ae)),
        "median_ae": float(np.median(ae)),
        "wape": float(np.sum(ae) / np.sum(actual)),
        "bias": float(np.mean(error)),
    }


def fit_candidate(store: pd.DataFrame, train_seasons: tuple[str, ...]):
    train = store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(train_seasons)
        & store[BASELINE].notna()
    ].copy()

    numeric = feature_columns(store, "full")
    if NEW_FEATURE not in numeric:
        raise RuntimeError("baseline_occupancy missing from candidate numeric feature set")

    prep = preprocessor(numeric)
    x_train = prep.fit_transform(train[CAT + numeric])
    capacity = train["capacity"].astype(float).to_numpy()
    baseline = train[BASELINE].astype(float).to_numpy()
    target = train["target_attendance"].astype(float).to_numpy()
    residual = target / capacity - baseline / capacity

    # Exact production T-30 estimator. v6 changes only one input feature.
    model = ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=3,
        max_features=0.8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, residual)
    return prep, model, numeric, int(len(train))


def predict_candidate(frame: pd.DataFrame, prep, model, numeric: list[str]) -> np.ndarray:
    residual = np.asarray(model.predict(prep.transform(frame[CAT + numeric])), dtype=float)
    capacity = frame["capacity"].astype(float).to_numpy()
    baseline = frame[BASELINE].astype(float).to_numpy()
    return np.clip(baseline + residual * capacity, 0.0, capacity)


def low_occupancy_metrics(frame: pd.DataFrame, prediction: np.ndarray) -> dict:
    mask = frame[NEW_FEATURE].astype(float) <= 0.45
    subset = frame.loc[mask].copy()
    if subset.empty:
        return {"n": 0}
    return metrics(subset["target_attendance"], np.asarray(prediction)[mask.to_numpy()])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-runtime",
        type=Path,
        default=Path("ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz"),
    )
    parser.add_argument("--output", type=Path, default=Path("/tmp/t30-baseline-occupancy-v6.json"))
    args = parser.parse_args()

    base_store = build_feature_store(canonical_matches(args.historical_runtime))
    store = add_feature(base_store)

    fold_results = {}
    combined_actual = []
    combined_control = []
    combined_candidate = []

    for fold in FOLDS:
        if fold.eval_season in FORBIDDEN or FORBIDDEN.intersection(fold.train_seasons):
            raise RuntimeError("Forbidden historical regression season requested")

        test = store[
            (store["horizon"].astype(str) == HORIZON)
            & store["training_eligible"].astype(bool)
            & (store["season"] == fold.eval_season)
            & store[BASELINE].notna()
        ].copy()
        actual = test["target_attendance"].astype(float).to_numpy()

        control_runtime = fit_structural_prior_runtime(
            base_store, HORIZON, list(fold.train_seasons)
        )
        control_prediction = control_runtime.predict(test[base_store.columns])

        prep, model, numeric, train_rows = fit_candidate(store, fold.train_seasons)
        candidate_prediction = predict_candidate(test, prep, model, numeric)

        control = metrics(actual, control_prediction)
        candidate = metrics(actual, candidate_prediction)
        control_low = low_occupancy_metrics(test, control_prediction)
        candidate_low = low_occupancy_metrics(test, candidate_prediction)

        fold_results[fold.name] = {
            "train_seasons": list(fold.train_seasons),
            "eval_season": fold.eval_season,
            "training_rows": train_rows,
            "control": control,
            "candidate": candidate,
            "delta_mae": candidate["mae"] - control["mae"],
            "relative_improvement": (control["mae"] - candidate["mae"]) / control["mae"],
            "low_baseline_occupancy_le_45pct": {
                "control": control_low,
                "candidate": candidate_low,
                "delta_mae": (
                    candidate_low.get("mae", np.nan) - control_low.get("mae", np.nan)
                ),
            },
        }
        combined_actual.extend(actual.tolist())
        combined_control.extend(np.asarray(control_prediction).tolist())
        combined_candidate.extend(np.asarray(candidate_prediction).tolist())

    control_combined = metrics(combined_actual, combined_control)
    candidate_combined = metrics(combined_actual, combined_candidate)
    relative = (
        control_combined["mae"] - candidate_combined["mae"]
    ) / control_combined["mae"]
    improves_both = all(
        row["candidate"]["mae"] < row["control"]["mae"]
        for row in fold_results.values()
    )
    gate = improves_both and relative >= MATERIAL_GATE

    report = {
        "experiment": "t30-baseline-occupancy-v6",
        "hypothesis": "explicit baseline occupancy state helps model occupancy residuals, especially low-occupancy matches",
        "candidate_model_id": "structural-prior-t30-v6-baseline-occupancy",
        "new_feature": "baseline_season / verified_capacity",
        "governance": {
            "policy": "ml/T30_RND_GOVERNANCE_V2.md",
            "evidence": "ml/results/T30_PREVALIDATION_ERROR_AUDIT_V1_2026-10-16.md",
            "historical_regression_seasons_scored": False,
            "next_validation_if_passed": "prospective_2026_27_shadow",
            "must_improve_every_fold": True,
            "material_combined_mae_gate": MATERIAL_GATE,
            "automatic_promotion": False,
        },
        "folds": fold_results,
        "combined": {
            "control": control_combined,
            "candidate": candidate_combined,
            "delta_mae": candidate_combined["mae"] - control_combined["mae"],
            "relative_improvement": relative,
        },
        "decision": {
            "improves_both_folds": improves_both,
            "passes_material_gate": gate,
            "status": "ELIGIBLE_FOR_PROSPECTIVE_SHADOW" if gate else "STOP_PRE_VALIDATION_GATE_NOT_MET",
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
