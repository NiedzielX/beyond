#!/usr/bin/env python3
"""T-30 v5 development experiment: cold-start-only historical anchoring.

v3/v4 showed that historical anchoring can help early rolling-origin folds but
applying it through the full season is not robust. v5 isolates the cold-start
hypothesis: use a capacity-aware previous-season occupancy anchor only while
current-season home evidence is sparse, then revert exactly to production
`baseline_season`.

Selection protocol:
- Fold A: train 2021/22 -> evaluate 2022/23;
- Fold B: train 2021/22+2022/23 -> evaluate 2023/24;
- 2024/25 and 2025/26 are NEVER scored by this script;
- production estimator and feature matrix remain fixed;
- candidate family is predeclared below;
- no automatic promotion.
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
MATERIAL_GATE = 0.03
PRE_VALIDATION = {"2021/2022", "2022/2023", "2023/2024"}
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

# Fixed candidate family defined before any new validation read.
# `k` is the virtual prior-match strength; `max_n` is the last current-season
# home-match count for which the prior is allowed to influence the baseline.
CANDIDATES = tuple(
    (float(k), int(max_n))
    for k in (1, 2, 3)
    for max_n in (1, 2, 3)
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
    frame["verified_capacity"] = frame.apply(lambda row: capacity_for(row.to_dict()), axis=1)
    if frame["verified_capacity"].isna().any():
        raise RuntimeError("Verified historical capacity is required")
    frame["home_occupancy"] = frame["attendance"].astype(float) / frame["verified_capacity"].astype(float)
    return frame.sort_values(["kickoff_at", "home_club_key"]).reset_index(drop=True)


def previous_occupancy_map(matches: pd.DataFrame) -> dict[tuple[str, str], float]:
    valid = matches[matches["attendance"].astype(float) > 0]
    means = valid.groupby(["season", "home_club_key"])["home_occupancy"].mean().to_dict()
    previous = {SEASONS[i]: (SEASONS[i - 1] if i else None) for i in range(len(SEASONS))}
    result: dict[tuple[str, str], float] = {}
    for season in SEASONS:
        prev = previous[season]
        if prev is None:
            continue
        clubs = valid.loc[valid["season"] == season, "home_club_key"].unique()
        for club in clubs:
            value = means.get((prev, club))
            if value is not None and np.isfinite(value):
                result[(season, str(club))] = float(value)
    return result


def enrich(store: pd.DataFrame, occ_map: dict[tuple[str, str], float]) -> pd.DataFrame:
    out = store.copy()
    out["prev_home_occupancy"] = [
        occ_map.get((str(season), str(club)), np.nan)
        for season, club in zip(out["season"], out["home_club_key"])
    ]
    out["prev_occ_anchor"] = out["prev_home_occupancy"] * out["capacity"].astype(float)
    return out


def cold_start_baseline(frame: pd.DataFrame, k: float, max_n: int) -> np.ndarray:
    production = pd.to_numeric(frame[BASELINE], errors="coerce")
    n = pd.to_numeric(frame["season_home_n"], errors="coerce").fillna(0.0).clip(lower=0.0)
    current = pd.to_numeric(frame["season_home_mean"], errors="coerce")
    anchor = pd.to_numeric(frame["prev_occ_anchor"], errors="coerce")

    # Default is the exact production baseline. Historical support may alter it
    # only for cold-start rows with a valid previous-season same-club anchor.
    result = production.copy()
    eligible = anchor.notna() & (n <= float(max_n))

    current_safe = current.fillna(anchor).fillna(production)
    anchor_safe = anchor.fillna(production)
    smoothed = (n * current_safe + float(k) * anchor_safe) / (n + float(k))
    smoothed = smoothed.where(n > 0, anchor_safe)
    result = result.where(~eligible, smoothed)
    result = result.fillna(production)
    if result.isna().any():
        raise RuntimeError("v5 baseline contains nulls")
    return result.astype(float).to_numpy()


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


def fit_candidate(store: pd.DataFrame, train_seasons: tuple[str, ...], k: float, max_n: int):
    train = store[
        (store["horizon"].astype(str) == HORIZON)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(train_seasons)
        & store[BASELINE].notna()
    ].copy()
    clean_store = store.drop(columns=["prev_home_occupancy", "prev_occ_anchor"])
    numeric = feature_columns(clean_store, "full")
    prep = preprocessor(numeric)
    x_train = prep.fit_transform(train[CAT + numeric])
    baseline = cold_start_baseline(train, k, max_n)
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


def predict_candidate(frame: pd.DataFrame, prep, model, numeric: list[str], k: float, max_n: int) -> np.ndarray:
    baseline = cold_start_baseline(frame, k, max_n)
    capacity = frame["capacity"].astype(float).to_numpy()
    residual = np.asarray(model.predict(prep.transform(frame[CAT + numeric])), dtype=float)
    return np.clip(baseline + residual * capacity, 0.0, capacity)


def evaluation_rows(store: pd.DataFrame, season: str) -> pd.DataFrame:
    if season in FORBIDDEN:
        raise RuntimeError("v5 attempted to read a forbidden historical regression season")
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
    parser.add_argument("--output", type=Path, default=Path("/tmp/t30-cold-start-v5.json"))
    args = parser.parse_args()

    matches = canonical_matches(args.historical_runtime)
    base_store = build_feature_store(matches)
    store = enrich(base_store, previous_occupancy_map(matches))

    if not all(set(f.train_seasons).issubset(PRE_VALIDATION) and f.eval_season in PRE_VALIDATION for f in FOLDS):
        raise RuntimeError("Invalid v5 fold definition")

    controls = {}
    actual_by_fold = {}
    control_pred_by_fold = {}
    for fold in FOLDS:
        test = evaluation_rows(store, fold.eval_season)
        runtime = fit_structural_prior_runtime(base_store, HORIZON, list(fold.train_seasons))
        prediction = runtime.predict(test)
        actual = test["target_attendance"].astype(float).to_numpy()
        controls[fold.name] = metrics(actual, prediction)
        actual_by_fold[fold.name] = actual
        control_pred_by_fold[fold.name] = np.asarray(prediction)

    candidates = []
    for k, max_n in CANDIDATES:
        fold_results = {}
        all_actual = []
        all_current = []
        all_candidate = []
        affected_rows = 0
        total_rows = 0

        for fold in FOLDS:
            test = evaluation_rows(store, fold.eval_season)
            prep, model, numeric, train_rows = fit_candidate(store, fold.train_seasons, k, max_n)
            prediction = predict_candidate(test, prep, model, numeric, k, max_n)
            actual = actual_by_fold[fold.name]
            current = controls[fold.name]
            cand = metrics(actual, prediction)
            eligible = test["prev_occ_anchor"].notna() & (
                pd.to_numeric(test["season_home_n"], errors="coerce").fillna(0.0) <= max_n
            )
            affected_rows += int(eligible.sum())
            total_rows += int(len(test))
            fold_results[fold.name] = {
                "train_seasons": list(fold.train_seasons),
                "eval_season": fold.eval_season,
                "training_rows": train_rows,
                "affected_eval_rows": int(eligible.sum()),
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
            row["candidate"]["mae"] < row["control"]["mae"]
            for row in fold_results.values()
        )
        gate = improves_both and relative >= MATERIAL_GATE
        candidates.append({
            "candidate": f"cold_start_occ_k{k:g}_maxn{max_n}",
            "k": k,
            "max_n": max_n,
            "affected_eval_rows": affected_rows,
            "affected_eval_share": affected_rows / total_rows if total_rows else 0.0,
            "folds": fold_results,
            "combined": {
                "control": combined_current,
                "candidate": combined_candidate,
                "delta_mae": combined_candidate["mae"] - combined_current["mae"],
                "relative_improvement": relative,
            },
            "pre_validation_gate_passed": gate,
        })

    candidates.sort(key=lambda row: (row["combined"]["candidate"]["mae"], row["candidate"]))
    passing = [row for row in candidates if row["pre_validation_gate_passed"]]

    report = {
        "experiment": "t30-cold-start-v5",
        "hypothesis": "historical occupancy anchor is useful only during sparse current-season home evidence",
        "governance": {
            "policy": "ml/T30_RND_GOVERNANCE_V2.md",
            "folds": [
                {"name": f.name, "train": list(f.train_seasons), "evaluate": f.eval_season}
                for f in FOLDS
            ],
            "historical_regression_seasons_scored": False,
            "next_validation_if_passed": "prospective_2026_27_shadow",
            "must_improve_every_fold": True,
            "material_combined_mae_gate": MATERIAL_GATE,
            "automatic_promotion": False,
        },
        "control": controls,
        "best": candidates[0],
        "passing_candidate_count": len(passing),
        "best_passing_candidate": passing[0] if passing else None,
        "all_candidates": candidates,
        "decision": "ELIGIBLE_FOR_PROSPECTIVE_SHADOW" if passing else "STOP_PRE_VALIDATION_GATE_NOT_MET",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
