#!/usr/bin/env python3
"""T-30 v4 development experiment: occupancy-normalized historical anchoring.

Hypothesis:
Raw previous-season attendance is not comparable across venue/capacity regimes.
Use the previous season's PIT-safe mean home occupancy and map it onto the
current verified capacity before shrinking the current-season home mean.

Governance:
- rolling-origin Fold A: train 2021/22 -> evaluate 2022/23;
- rolling-origin Fold B: train 2021/22+2022/23 -> evaluate 2023/24;
- 2024/25 and 2025/26 are not scored by this script;
- production estimator and feature matrix remain fixed;
- only the baseline family is evaluated;
- no production mutation or auto-promotion.
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
from ml.features.structural_prior_feature_store_v1 import (
    SEASONS,
    WARSAW_TZ,
    build_feature_store,
    capacity_for,
)

HORIZON = "T-30"
BASELINE = "baseline_season"
PRE_VALIDATION = {"2021/2022", "2022/2023", "2023/2024"}
EXPOSED_REGRESSION = {"2024/2025", "2025/2026"}
MATERIAL_GATE = 0.03
K_VALUES = (1.0, 2.0, 3.0, 5.0, 8.0)


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
    frame["date"] = pd.to_datetime(frame["date"])
    local = pd.to_datetime(
        frame["date"].dt.strftime("%Y-%m-%d") + " " + frame["kickoff_time_local"].astype(str),
        format="mixed",
    )
    frame["kickoff_at"] = local.dt.tz_localize(
        WARSAW_TZ, ambiguous="raise", nonexistent="raise"
    ).dt.tz_convert("UTC")
    frame["completed_at"] = frame["kickoff_at"] + pd.Timedelta(hours=3)
    frame["training_eligible"] = frame["attendance"].astype(int) != 0
    frame["round"] = frame["round"].astype(int)
    frame["verified_capacity"] = frame.apply(
        lambda row: capacity_for(row.to_dict()), axis=1
    )
    if frame["verified_capacity"].isna().any():
        raise RuntimeError("Historical occupancy experiment requires complete verified capacity")
    frame["home_occupancy"] = (
        frame["attendance"].astype(float) / frame["verified_capacity"].astype(float)
    )
    return frame.sort_values(["kickoff_at", "home_club_key"]).reset_index(drop=True)


def previous_season_occupancy_map(matches: pd.DataFrame) -> dict[tuple[str, str], float]:
    """Map (current season, club) -> prior-season mean home occupancy.

    The prior season is fully completed before the current season begins, so the
    aggregate is point-in-time safe for every current-season T-30 checkpoint.
    Closed-door zero attendance is excluded consistently with demand training.
    """
    valid = matches[matches["attendance"].astype(float) > 0].copy()
    means = (
        valid.groupby(["season", "home_club_key"])["home_occupancy"]
        .mean()
        .to_dict()
    )
    result: dict[tuple[str, str], float] = {}
    previous = {SEASONS[i]: (SEASONS[i - 1] if i > 0 else None) for i in range(len(SEASONS))}
    for season in SEASONS:
        prev = previous[season]
        if prev is None:
            continue
        clubs = valid.loc[valid["season"] == season, "home_club_key"].unique().tolist()
        for club in clubs:
            value = means.get((prev, club))
            if value is not None and np.isfinite(value):
                result[(season, str(club))] = float(value)
    return result


def add_anchor(store: pd.DataFrame, occ_map: dict[tuple[str, str], float]) -> pd.DataFrame:
    out = store.copy()
    out["prev_season_home_occupancy"] = [
        occ_map.get((str(season), str(club)), np.nan)
        for season, club in zip(out["season"], out["home_club_key"])
    ]
    out["prev_occ_current_capacity_anchor"] = (
        out["prev_season_home_occupancy"].astype(float) * out["capacity"].astype(float)
    )
    return out


def candidate_baseline(frame: pd.DataFrame, k: float) -> np.ndarray:
    n = pd.to_numeric(frame["season_home_n"], errors="coerce").fillna(0.0).clip(lower=0.0)
    current = pd.to_numeric(frame["season_home_mean"], errors="coerce")
    anchor = pd.to_numeric(frame["prev_occ_current_capacity_anchor"], errors="coerce")
    fallback = pd.to_numeric(frame[BASELINE], errors="coerce")

    # For clubs without a same-club previous season (promotion/re-entry), do not
    # invent an occupancy anchor; preserve the production baseline instead.
    anchor = anchor.fillna(fallback)
    current = current.fillna(anchor).fillna(fallback)
    anchor = anchor.fillna(current).fillna(fallback)

    smoothed = (n * current + float(k) * anchor) / (n + float(k))
    smoothed = smoothed.where(n > 0, anchor).fillna(fallback)
    if smoothed.isna().any():
        raise RuntimeError("v4 baseline contains nulls")
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


def fit_candidate(store: pd.DataFrame, train_seasons: tuple[str, ...], k: float):
    train = store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(train_seasons)
        & store[BASELINE].notna()
    ].copy()

    # The new anchor is used only in the baseline/target residual. It is not fed
    # into the estimator, isolating the hypothesis from feature-set expansion.
    numeric = feature_columns(store.drop(columns=["prev_season_home_occupancy", "prev_occ_current_capacity_anchor"]), "full")
    prep = preprocessor(numeric)
    x_train = prep.fit_transform(train[CAT + numeric])
    baseline = candidate_baseline(train, k)
    capacity = train["capacity"].astype(float).to_numpy()
    target = train["target_attendance"].astype(float).to_numpy()
    residual = target / capacity - baseline / capacity

    model = ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=3,
        max_features=0.8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, residual)
    return prep, model, numeric, int(len(train))


def predict_candidate(frame: pd.DataFrame, prep, model, numeric: list[str], k: float) -> np.ndarray:
    baseline = candidate_baseline(frame, k)
    capacity = frame["capacity"].astype(float).to_numpy()
    residual = np.asarray(model.predict(prep.transform(frame[CAT + numeric])), dtype=float)
    return np.clip(baseline + residual * capacity, 0.0, capacity)


def eval_rows(store: pd.DataFrame, season: str) -> pd.DataFrame:
    if season in EXPOSED_REGRESSION:
        raise RuntimeError("Development-only v4 attempted to score exposed regression season")
    return store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & (store["season"] == season)
        & store[BASELINE].notna()
    ].copy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-runtime",
        type=Path,
        default=Path("ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz"),
    )
    parser.add_argument("--output", type=Path, default=Path("/tmp/t30-occupancy-anchor-v4.json"))
    args = parser.parse_args()

    matches = canonical_matches(args.historical_runtime)
    base_store = build_feature_store(matches)
    store = add_anchor(base_store, previous_season_occupancy_map(matches))

    if not all(set(f.train_seasons).issubset(PRE_VALIDATION) and f.eval_season in PRE_VALIDATION for f in FOLDS):
        raise RuntimeError("Invalid v4 rolling-origin fold definition")

    controls = {}
    actual_by_fold = {}
    control_pred_by_fold = {}
    for fold in FOLDS:
        test = eval_rows(store, fold.eval_season)
        current = fit_structural_prior_runtime(base_store, HORIZON, list(fold.train_seasons))
        prediction = current.predict(test[base_store.columns])
        actual = test["target_attendance"].astype(float).to_numpy()
        controls[fold.name] = metrics(actual, prediction)
        actual_by_fold[fold.name] = actual
        control_pred_by_fold[fold.name] = np.asarray(prediction)

    candidates = []
    for k in K_VALUES:
        fold_results = {}
        all_actual = []
        all_current = []
        all_candidate = []
        for fold in FOLDS:
            test = eval_rows(store, fold.eval_season)
            prep, model, numeric, train_rows = fit_candidate(store, fold.train_seasons, k)
            prediction = predict_candidate(test, prep, model, numeric, k)
            actual = actual_by_fold[fold.name]
            current = controls[fold.name]
            cand = metrics(actual, prediction)
            fold_results[fold.name] = {
                "train_seasons": list(fold.train_seasons),
                "eval_season": fold.eval_season,
                "training_rows": train_rows,
                "control": current,
                "candidate": cand,
                "delta_mae": cand["mae"] - current["mae"],
                "relative_improvement": (current["mae"] - cand["mae"]) / current["mae"],
            }
            all_actual.extend(actual.tolist())
            all_current.extend(control_pred_by_fold[fold.name].tolist())
            all_candidate.extend(prediction.tolist())

        combined_current = metrics(all_actual, all_current)
        combined_candidate = metrics(all_actual, all_candidate)
        relative = (
            combined_current["mae"] - combined_candidate["mae"]
        ) / combined_current["mae"]
        improves_both = all(
            item["candidate"]["mae"] < item["control"]["mae"]
            for item in fold_results.values()
        )
        gate = improves_both and relative >= MATERIAL_GATE
        candidates.append({
            "candidate": f"occupancy_anchor_shrink_k{k:g}",
            "k": k,
            "folds": fold_results,
            "combined": {
                "control": combined_current,
                "candidate": combined_candidate,
                "delta_mae": combined_candidate["mae"] - combined_current["mae"],
                "relative_improvement": relative,
            },
            "pre_validation_gate_passed": gate,
        })

    candidates.sort(key=lambda item: (item["combined"]["candidate"]["mae"], item["candidate"]))
    passing = [item for item in candidates if item["pre_validation_gate_passed"]]
    coverage = (
        store.loc[store["horizon"].astype(str) == HORIZON, "prev_season_home_occupancy"]
        .notna()
        .groupby(store.loc[store["horizon"].astype(str) == HORIZON, "season"])
        .mean()
        .to_dict()
    )

    report = {
        "experiment": "t30-occupancy-anchor-v4",
        "hypothesis": "map previous-season mean occupancy into current verified capacity before early-season shrinkage",
        "governance": {
            "policy": "ml/T30_RND_GOVERNANCE_V2.md",
            "folds": [
                {"name": f.name, "train": list(f.train_seasons), "evaluate": f.eval_season}
                for f in FOLDS
            ],
            "exposed_regression_seasons_scored": False,
            "must_improve_every_fold": True,
            "material_combined_mae_gate": MATERIAL_GATE,
            "automatic_promotion": False,
        },
        "anchor_coverage_by_season": {str(k): float(v) for k, v in coverage.items()},
        "control": controls,
        "best": candidates[0],
        "passing_candidate_count": len(passing),
        "best_passing_candidate": passing[0] if passing else None,
        "all_candidates": candidates,
        "decision": "ELIGIBLE_TO_FREEZE_FOR_REGRESSION" if passing else "STOP_PRE_VALIDATION_GATE_NOT_MET",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
