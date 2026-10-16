#!/usr/bin/env python3
"""T-30 v3 development experiment: PIT-safe home-demand baseline smoothing.

Governance:
- candidate family is pre-registered in ml/T30_RND_GOVERNANCE_V2.md;
- scoring uses only rolling-origin Fold A (2022/23) and Fold B (2023/24);
- 2024/25 and 2025/26 are not scored or used for candidate selection;
- production runtime/artifacts are never mutated by this script.
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

from ml.demand_engine.structural_prior_runtime import (
    CAT,
    feature_columns,
    fit_structural_prior_runtime,
)
from ml.features.structural_prior_feature_store_v1 import (
    WARSAW_TZ,
    build_feature_store,
)

HORIZON = "T-30"
CURRENT_BASELINE = "baseline_season"
PRE_VALIDATION_SEASONS = {"2021/2022", "2022/2023", "2023/2024"}
VALIDATION_SEASONS = {"2024/2025", "2025/2026"}
MATERIAL_GATE = 0.03


@dataclass(frozen=True)
class Fold:
    name: str
    train_seasons: tuple[str, ...]
    eval_season: str


FOLDS = (
    Fold("A", ("2021/2022",), "2022/2023"),
    Fold("B", ("2021/2022", "2022/2023"), "2023/2024"),
)

# Frozen candidate family. No values may be added after looking at validation seasons.
CANDIDATES = tuple(
    [("prev", k) for k in (1.0, 2.0, 3.0, 5.0, 8.0)]
    + [("long", k) for k in (1.0, 2.0, 3.0, 5.0, 8.0)]
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
    frame["training_eligible"] = frame["attendance"].astype(int) != 0
    frame["round"] = frame["round"].astype(int)
    return frame.sort_values(["kickoff_at", "home_club_key"]).reset_index(drop=True)


def _finite(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan)


def candidate_baseline(frame: pd.DataFrame, anchor_mode: str, k: float) -> np.ndarray:
    season_n = _finite(frame["season_home_n"]).fillna(0.0).clip(lower=0.0)
    season_mean = _finite(frame["season_home_mean"])
    long_mean = _finite(frame["home_attendance_mean"])
    previous_mean = _finite(frame["prev_season_home_mean"])
    fallback = _finite(frame[CURRENT_BASELINE])

    if anchor_mode == "prev":
        anchor = previous_mean.fillna(long_mean).fillna(fallback)
    elif anchor_mode == "long":
        anchor = long_mean.fillna(previous_mean).fillna(fallback)
    else:
        raise KeyError(anchor_mode)

    current = season_mean.fillna(anchor).fillna(fallback)
    anchor = anchor.fillna(current).fillna(fallback)

    # If current-season history is absent, use the PIT anchor directly.
    denominator = season_n + float(k)
    smoothed = (season_n * current + float(k) * anchor) / denominator
    smoothed = smoothed.where(season_n > 0, anchor)
    smoothed = smoothed.fillna(fallback)

    if smoothed.isna().any():
        raise RuntimeError("candidate baseline contains nulls")
    return smoothed.astype(float).to_numpy()


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


def fit_candidate(
    store: pd.DataFrame,
    train_seasons: tuple[str, ...],
    anchor_mode: str,
    k: float,
):
    train = store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(train_seasons)
        & store[CURRENT_BASELINE].notna()
    ].copy()
    numeric = feature_columns(store, "full")
    prep = preprocessor(numeric)
    x_train = prep.fit_transform(train[CAT + numeric])
    baseline = candidate_baseline(train, anchor_mode, k)
    capacity = train["capacity"].astype(float).to_numpy()
    target = train["target_attendance"].astype(float).to_numpy()
    residual = target / capacity - baseline / capacity

    # Keep the production estimator fixed. v3 tests the baseline hypothesis only.
    model = ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=3,
        max_features=0.8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, residual)
    return prep, model, numeric, int(len(train))


def predict_candidate(
    frame: pd.DataFrame,
    prep: ColumnTransformer,
    model: ExtraTreesRegressor,
    numeric: list[str],
    anchor_mode: str,
    k: float,
) -> np.ndarray:
    baseline = candidate_baseline(frame, anchor_mode, k)
    capacity = frame["capacity"].astype(float).to_numpy()
    residual = np.asarray(model.predict(prep.transform(frame[CAT + numeric])), dtype=float)
    return np.clip(baseline + residual * capacity, 0.0, capacity)


def fold_rows(store: pd.DataFrame, season: str) -> pd.DataFrame:
    if season in VALIDATION_SEASONS:
        raise RuntimeError("Historical validation season requested by development-only experiment")
    return store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & (store["season"] == season)
        & store[CURRENT_BASELINE].notna()
    ].copy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-runtime",
        type=Path,
        default=Path("ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz"),
    )
    parser.add_argument("--output", type=Path, default=Path("/tmp/t30-baseline-smoothing-v3.json"))
    args = parser.parse_args()

    matches = canonical_matches(args.historical_runtime)
    store = build_feature_store(matches)

    # Defensive contract: evaluation code below only accepts the pre-validation seasons.
    if not all(set(f.train_seasons).issubset(PRE_VALIDATION_SEASONS) and f.eval_season in PRE_VALIDATION_SEASONS for f in FOLDS):
        raise RuntimeError("Invalid development fold definition")

    controls: dict[str, dict] = {}
    control_predictions: dict[str, np.ndarray] = {}
    fold_actual: dict[str, np.ndarray] = {}

    for fold in FOLDS:
        eval_rows = fold_rows(store, fold.eval_season)
        current = fit_structural_prior_runtime(store, HORIZON, list(fold.train_seasons))
        pred = current.predict(eval_rows)
        actual = eval_rows["target_attendance"].astype(float).to_numpy()
        controls[fold.name] = metrics(actual, pred)
        control_predictions[fold.name] = pred
        fold_actual[fold.name] = actual

    candidates = []
    for anchor_mode, k in CANDIDATES:
        fold_results = {}
        combined_actual = []
        combined_prediction = []
        combined_control = []

        for fold in FOLDS:
            eval_rows = fold_rows(store, fold.eval_season)
            prep, model, numeric, train_rows = fit_candidate(
                store, fold.train_seasons, anchor_mode, k
            )
            prediction = predict_candidate(
                eval_rows, prep, model, numeric, anchor_mode, k
            )
            actual = fold_actual[fold.name]
            current_mae = controls[fold.name]["mae"]
            result = metrics(actual, prediction)
            fold_results[fold.name] = {
                "train_seasons": list(fold.train_seasons),
                "eval_season": fold.eval_season,
                "training_rows": train_rows,
                "control": controls[fold.name],
                "candidate": result,
                "delta_mae_vs_control": result["mae"] - current_mae,
                "relative_improvement_vs_control": (current_mae - result["mae"]) / current_mae,
            }
            combined_actual.extend(actual.tolist())
            combined_prediction.extend(prediction.tolist())
            combined_control.extend(control_predictions[fold.name].tolist())

        combined_candidate = metrics(combined_actual, combined_prediction)
        combined_current = metrics(combined_actual, combined_control)
        relative = (
            combined_current["mae"] - combined_candidate["mae"]
        ) / combined_current["mae"]
        improves_both = all(
            item["candidate"]["mae"] < item["control"]["mae"]
            for item in fold_results.values()
        )
        gate = improves_both and relative >= MATERIAL_GATE

        candidates.append({
            "candidate": f"baseline_{anchor_mode}_shrink_k{k:g}",
            "anchor_mode": anchor_mode,
            "k": k,
            "folds": fold_results,
            "combined": {
                "control": combined_current,
                "candidate": combined_candidate,
                "delta_mae_vs_control": combined_candidate["mae"] - combined_current["mae"],
                "relative_improvement_vs_control": relative,
            },
            "pre_validation_gate_passed": gate,
        })

    candidates.sort(key=lambda item: (item["combined"]["candidate"]["mae"], item["candidate"]))
    passing = [item for item in candidates if item["pre_validation_gate_passed"]]

    report = {
        "experiment": "t30-baseline-smoothing-v3",
        "hypothesis": "shrink noisy current-season home attendance toward a PIT historical anchor",
        "governance": {
            "policy": "ml/T30_RND_GOVERNANCE_V2.md",
            "folds": [
                {"name": f.name, "train": list(f.train_seasons), "evaluate": f.eval_season}
                for f in FOLDS
            ],
            "historical_validation_seasons_scored": False,
            "material_combined_mae_gate": MATERIAL_GATE,
            "must_improve_every_fold": True,
            "automatic_promotion": False,
        },
        "control": controls,
        "best": candidates[0],
        "passing_candidate_count": len(passing),
        "best_passing_candidate": passing[0] if passing else None,
        "all_candidates": candidates,
        "decision": (
            "ELIGIBLE_TO_FREEZE_FOR_VALIDATION"
            if passing
            else "STOP_PRE_VALIDATION_GATE_NOT_MET"
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
