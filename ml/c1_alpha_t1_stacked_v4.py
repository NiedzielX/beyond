#!/usr/bin/env python3
"""C1-alpha T-1 stacked/meta-gate tournament v4.

v3 proved that disagreement gating can protect good Structural Priors, while the
v2 live model contains enough complementary signal for an oracle event switch to
reach ~1.87k MAE. v4 learns the combination rather than hand-tuning a threshold.

For each outer LOEO fold:
1. create base-live OOF predictions inside the outer-training events;
2. train a small strongly regularized meta model using only those OOF estimates;
3. refit the base live model on all outer-training events;
4. generate prior + base-live inputs for the untouched outer event;
5. apply the meta model to the untouched event.

No outer-event outcome enters base or meta training.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay, _training_frame
from ml.c1_alpha_t1_tournament_v2 import (
    COMPACT_NUMERIC,
    WINDOW_HOURS,
    event_weights,
    fit_with_weights,
    pipeline as base_pipeline,
)


META_BASE_FEATURES = [
    "prior_expected_occupancy",
    "base_live_occupancy",
    "signed_disagreement_occupancy",
    "abs_disagreement_occupancy",
    "available_share_of_capacity",
    "available_index",
    "velocity_6h",
    "velocity_24h",
    "acceleration_6h_vs_24h",
    "observation_window_hours",
    "raw_snapshot_count",
    "clean_snapshot_count",
    "matched_absorption",
    "matched_release",
    "signal_ready",
    "feature_quality_good",
    "release_activity_flag",
    "sector_coverage_change_flag",
    "season_home_evidence_n",
    "round_no",
]

META_MINIMAL_FEATURES = [
    "prior_expected_occupancy",
    "base_live_occupancy",
    "signed_disagreement_occupancy",
    "abs_disagreement_occupancy",
    "available_share_of_capacity",
    "available_index",
    "season_home_evidence_n",
    "round_no",
]


@dataclass(frozen=True)
class MetaSpec:
    name: str
    mode: str
    features: tuple[str, ...]
    model: Any
    club_aware: bool = False


def add_event_context(frame: pd.DataFrame, payload: dict) -> pd.DataFrame:
    out = frame.copy()
    events = {int(row["ticket_event_id"]): row for row in payload.get("events") or []}
    attendance = pd.DataFrame(payload.get("attendance") or [])
    if not attendance.empty:
        attendance["kickoff_at"] = pd.to_datetime(attendance["kickoff_at"], utc=True)

    rounds = []
    season_evidence = []
    for row in out.itertuples(index=False):
        event = events[int(row.ticket_event_id)]
        rounds.append(pd.to_numeric(event.get("round_no"), errors="coerce"))
        if attendance.empty:
            season_evidence.append(0.0)
            continue
        as_of = pd.Timestamp(row.as_of_at)
        if as_of.tzinfo is None:
            as_of = as_of.tz_localize("UTC")
        else:
            as_of = as_of.tz_convert("UTC")
        event_season = str(event.get("season"))
        club_slug = str(event.get("club_slug"))
        mask = (
            (attendance["club_slug"].astype(str) == club_slug)
            & (attendance["season"].astype(str) == event_season)
            & (attendance["kickoff_at"] < as_of)
        )
        season_evidence.append(float(mask.sum()))
    out["round_no"] = rounds
    out["season_home_evidence_n"] = season_evidence
    return out


def base_features(frame: pd.DataFrame) -> list[str]:
    return [column for column in COMPACT_NUMERIC if column in frame.columns]


def fit_base_live(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Exact v2 winner: generic compact Ridge alpha=10, direct occupancy."""
    features = base_features(train)
    model = base_pipeline(features, False, Ridge(alpha=10.0), scale=True)
    target = (
        train["actual_attendance"].astype(float)
        / train["stadium_capacity"].astype(float)
    ).to_numpy()
    fitted = fit_with_weights(
        model,
        train[features],
        target,
        event_weights(train),
    )
    occupancy = np.asarray(fitted.predict(test[features]), dtype=float)
    capacity = test["stadium_capacity"].astype(float).to_numpy()
    return np.clip(occupancy * capacity, 0.0, capacity)


def add_meta_features(frame: pd.DataFrame, base_live: np.ndarray) -> pd.DataFrame:
    out = frame.copy()
    capacity = out["stadium_capacity"].astype(float).to_numpy()
    prior = out["prior_p50"].astype(float).to_numpy()
    base_live = np.asarray(base_live, dtype=float)
    out["base_live_prediction"] = base_live
    out["base_live_occupancy"] = base_live / capacity
    out["signed_disagreement_occupancy"] = (base_live - prior) / capacity
    out["abs_disagreement_occupancy"] = np.abs(base_live - prior) / capacity
    out["oracle_live_better"] = (
        np.abs(base_live - out["actual_attendance"].astype(float).to_numpy())
        < np.abs(prior - out["actual_attendance"].astype(float).to_numpy())
    ).astype(int)
    return out


def inner_oof_meta_frame(outer_train: pd.DataFrame) -> pd.DataFrame:
    blocks = []
    event_ids = sorted(int(value) for value in outer_train["ticket_event_id"].unique())
    for inner_held_out in event_ids:
        inner_train = outer_train[outer_train["ticket_event_id"] != inner_held_out].copy()
        inner_test = (
            outer_train[outer_train["ticket_event_id"] == inner_held_out]
            .copy()
            .sort_values("as_of_at")
        )
        if inner_train["ticket_event_id"].nunique() < 2:
            continue
        live = fit_base_live(inner_train, inner_test)
        blocks.append(add_meta_features(inner_test, live))
    if not blocks:
        raise RuntimeError("No inner OOF rows for stacked C1 meta model")
    return pd.concat(blocks, ignore_index=True)


def meta_preprocessor(features: list[str], club_aware: bool, scale: bool = True) -> ColumnTransformer:
    numeric_steps: list[tuple[str, Any]] = [
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
    ]
    if scale:
        numeric_steps.append(("scale", StandardScaler()))
    transformers: list[tuple[str, Any, list[str]]] = [
        ("num", Pipeline(numeric_steps), features),
    ]
    if club_aware:
        transformers.append((
            "club",
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ["club_slug"],
        ))
    return ColumnTransformer(transformers, remainder="drop")


def meta_pipeline(features: list[str], club_aware: bool, model: Any, scale: bool = True) -> Pipeline:
    return Pipeline([
        ("prep", meta_preprocessor(features, club_aware, scale)),
        ("model", model),
    ])


def meta_specs(frame: pd.DataFrame) -> list[MetaSpec]:
    base = tuple(column for column in META_BASE_FEATURES if column in frame.columns)
    minimal = tuple(column for column in META_MINIMAL_FEATURES if column in frame.columns)
    specs: list[MetaSpec] = []

    for feature_name, features in (("minimal", minimal), ("base", base)):
        for club_aware in (False, True):
            suffix = "club" if club_aware else "generic"
            for alpha in (1.0, 10.0, 100.0, 1000.0):
                specs.append(MetaSpec(
                    name=f"stack_ridge_{feature_name}_{suffix}_a{alpha:g}",
                    mode="direct_occupancy",
                    features=features,
                    model=meta_pipeline(list(features), club_aware, Ridge(alpha=alpha), scale=True),
                    club_aware=club_aware,
                ))
            for epsilon, alpha in ((1.35, 0.001), (1.5, 0.001), (1.5, 0.01)):
                specs.append(MetaSpec(
                    name=f"stack_huber_{feature_name}_{suffix}_e{epsilon:g}_a{alpha:g}",
                    mode="direct_occupancy",
                    features=features,
                    model=meta_pipeline(
                        list(features), club_aware,
                        HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=1000),
                        scale=True,
                    ),
                    club_aware=club_aware,
                ))
            for c in (0.01, 0.1, 1.0):
                specs.append(MetaSpec(
                    name=f"softgate_logit_{feature_name}_{suffix}_c{c:g}",
                    mode="soft_gate",
                    features=features,
                    model=meta_pipeline(
                        list(features), club_aware,
                        LogisticRegression(C=c, max_iter=1000, random_state=42),
                        scale=True,
                    ),
                    club_aware=club_aware,
                ))
                specs.append(MetaSpec(
                    name=f"hardgate_logit_{feature_name}_{suffix}_c{c:g}",
                    mode="hard_gate",
                    features=features,
                    model=meta_pipeline(
                        list(features), club_aware,
                        LogisticRegression(C=c, max_iter=1000, random_state=42),
                        scale=True,
                    ),
                    club_aware=club_aware,
                ))

    # Interpretable nonlinear gate/stacker with severe depth constraints.
    for depth in (1, 2):
        specs.append(MetaSpec(
            name=f"softgate_tree_d{depth}",
            mode="soft_gate",
            features=minimal,
            model=meta_pipeline(
                list(minimal), False,
                DecisionTreeClassifier(max_depth=depth, min_samples_leaf=4, random_state=42),
                scale=False,
            ),
            club_aware=False,
        ))
        specs.append(MetaSpec(
            name=f"stack_tree_d{depth}",
            mode="direct_occupancy",
            features=minimal,
            model=meta_pipeline(
                list(minimal), False,
                DecisionTreeRegressor(max_depth=depth, min_samples_leaf=4, random_state=42),
                scale=False,
            ),
            club_aware=False,
        ))
    return specs


def spec_input_columns(spec: MetaSpec) -> list[str]:
    cols = list(spec.features)
    if spec.club_aware:
        cols.append("club_slug")
    return cols


def fit_meta_predict(spec: MetaSpec, meta_train: pd.DataFrame, outer_test_meta: pd.DataFrame) -> np.ndarray:
    xcols = spec_input_columns(spec)
    weights = event_weights(meta_train)
    model = clone(spec.model)

    if spec.mode == "direct_occupancy":
        target = (
            meta_train["actual_attendance"].astype(float)
            / meta_train["stadium_capacity"].astype(float)
        ).to_numpy()
        try:
            model.fit(meta_train[xcols], target, model__sample_weight=weights)
        except (TypeError, ValueError):
            model.fit(meta_train[xcols], target)
        occupancy = np.asarray(model.predict(outer_test_meta[xcols]), dtype=float)
        capacity = outer_test_meta["stadium_capacity"].astype(float).to_numpy()
        return np.clip(occupancy, 0.0, 1.0) * capacity

    target = meta_train["oracle_live_better"].astype(int).to_numpy()
    if np.unique(target).size < 2:
        # Degenerate inner data: conservatively keep Structural Prior.
        return outer_test_meta["prior_p50"].astype(float).to_numpy()
    try:
        model.fit(meta_train[xcols], target, model__sample_weight=weights)
    except (TypeError, ValueError):
        model.fit(meta_train[xcols], target)
    probability = np.asarray(model.predict_proba(outer_test_meta[xcols])[:, 1], dtype=float)
    if spec.mode == "hard_gate":
        probability = (probability >= 0.5).astype(float)
    prior = outer_test_meta["prior_p50"].astype(float).to_numpy()
    live = outer_test_meta["base_live_prediction"].astype(float).to_numpy()
    prediction = prior + probability * (live - prior)
    capacity = outer_test_meta["stadium_capacity"].astype(float).to_numpy()
    return np.clip(prediction, 0.0, capacity)


def fold_metrics(test: pd.DataFrame, prediction: np.ndarray) -> dict[str, float]:
    actual = test["actual_attendance"].astype(float).to_numpy()
    prior = test["prior_p50"].astype(float).to_numpy()
    prediction = np.asarray(prediction, dtype=float)
    prior_error = np.abs(prior - actual)
    live_error = np.abs(prediction - actual)
    return {
        "prior_window_mae": float(np.mean(prior_error)),
        "live_window_mae": float(np.mean(live_error)),
        "prior_first_error": float(prior_error[0]),
        "live_first_error": float(live_error[0]),
        "prior_latest_error": float(prior_error[-1]),
        "live_latest_error": float(live_error[-1]),
        "degradation": float(np.mean(live_error) - np.mean(prior_error)),
    }


def evaluate_spec(frame: pd.DataFrame, spec: MetaSpec) -> dict[str, Any]:
    folds = []
    event_ids = sorted(int(value) for value in frame["ticket_event_id"].unique())
    for held_out in event_ids:
        outer_train = frame[frame["ticket_event_id"] != held_out].copy()
        outer_test = (
            frame[frame["ticket_event_id"] == held_out]
            .copy()
            .sort_values("as_of_at")
        )
        meta_train = inner_oof_meta_frame(outer_train)
        outer_base = fit_base_live(outer_train, outer_test)
        outer_meta = add_meta_features(outer_test, outer_base)
        prediction = fit_meta_predict(spec, meta_train, outer_meta)
        m = fold_metrics(outer_test, prediction)
        folds.append({
            "ticket_event_id": held_out,
            "home_team": str(outer_test["home_team"].iloc[0]),
            "away_team": str(outer_test["away_team"].iloc[0]),
            "rows": int(len(outer_test)),
            **m,
            "improved": bool(m["live_window_mae"] < m["prior_window_mae"]),
        })

    prior_mae = float(np.mean([f["prior_window_mae"] for f in folds]))
    live_mae = float(np.mean([f["live_window_mae"] for f in folds]))
    return {
        "candidate": spec.name,
        "mode": spec.mode,
        "event_count": len(folds),
        "prior_window_mae": prior_mae,
        "live_window_mae": live_mae,
        "absolute_uplift": prior_mae - live_mae,
        "relative_improvement": (prior_mae - live_mae) / prior_mae if prior_mae else 0.0,
        "event_improvement_rate": float(np.mean([f["improved"] for f in folds])),
        "worst_event_degradation": float(max(f["degradation"] for f in folds)),
        "prior_first_row_mae": float(np.mean([f["prior_first_error"] for f in folds])),
        "live_first_row_mae": float(np.mean([f["live_first_error"] for f in folds])),
        "prior_latest_row_mae": float(np.mean([f["prior_latest_error"] for f in folds])),
        "live_latest_row_mae": float(np.mean([f["live_latest_error"] for f in folds])),
        "folds": folds,
    }


def incumbent_result(frame: pd.DataFrame) -> dict[str, Any]:
    folds = []
    for event_id, test in frame.groupby("ticket_event_id", sort=True):
        test = test.sort_values("as_of_at")
        prior = test["prior_p50"].astype(float).to_numpy()
        m = fold_metrics(test, prior)
        folds.append({
            "ticket_event_id": int(event_id),
            **m,
            "improved": False,
        })
    prior_mae = float(np.mean([f["prior_window_mae"] for f in folds]))
    return {
        "candidate": "structural_prior_zero_correction",
        "mode": "incumbent",
        "event_count": len(folds),
        "prior_window_mae": prior_mae,
        "live_window_mae": prior_mae,
        "absolute_uplift": 0.0,
        "relative_improvement": 0.0,
        "event_improvement_rate": 0.0,
        "worst_event_degradation": 0.0,
        "prior_first_row_mae": float(np.mean([f["prior_first_error"] for f in folds])),
        "live_first_row_mae": float(np.mean([f["prior_first_error"] for f in folds])),
        "prior_latest_row_mae": float(np.mean([f["prior_latest_error"] for f in folds])),
        "live_latest_row_mae": float(np.mean([f["prior_latest_error"] for f in folds])),
        "folds": folds,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    priors = _event_prior_replay(payload, args.artifact_dir)
    frame = add_event_context(_training_frame(payload, priors), payload)
    frame = frame[
        (frame["hours_to_kickoff"].astype(float) >= 0.0)
        & (frame["hours_to_kickoff"].astype(float) <= WINDOW_HOURS)
        & (frame["prior_horizon"] == "T-1")
    ].copy()
    if frame["ticket_event_id"].nunique() < 6:
        raise RuntimeError("Stacked C1 v4 requires at least 6 independent events")

    incumbent = incumbent_result(frame)
    specs = meta_specs(frame)
    leaderboard = [evaluate_spec(frame, spec) for spec in specs]
    leaderboard.sort(key=lambda row: (
        row["live_window_mae"],
        row["worst_event_degradation"],
        -row["event_improvement_rate"],
        row["candidate"],
    ))
    best = leaderboard[0]

    report = {
        "experiment": "c1-alpha-t1-stacked-v4",
        "window": "T-1 to kickoff / <=24h",
        "base_live_model": "ridge_directocc_compact_generic_a10",
        "dataset_version": payload.get("version"),
        "event_count": int(frame["ticket_event_id"].nunique()),
        "row_count": int(len(frame)),
        "validation": "outer LOEO; base predictions for meta training are inner-LOEO OOF",
        "meta_candidate_count": len(specs),
        "incumbent": incumbent,
        "best": best,
        "goal": {
            "beat_structural_prior": bool(best["live_window_mae"] < incumbent["live_window_mae"]),
            "under_1900": bool(best["live_window_mae"] < 1900.0),
            "under_1700": bool(best["live_window_mae"] < 1700.0),
            "under_1500_stretch": bool(best["live_window_mae"] < 1500.0),
        },
        "leaderboard": leaderboard,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({
        "experiment": report["experiment"],
        "event_count": report["event_count"],
        "row_count": report["row_count"],
        "incumbent_mae": incumbent["live_window_mae"],
        "best": {key: best[key] for key in (
            "candidate", "mode", "live_window_mae", "absolute_uplift",
            "relative_improvement", "event_improvement_rate", "worst_event_degradation",
            "live_first_row_mae", "live_latest_row_mae"
        )},
        "goal": report["goal"],
        "top_10": [
            {key: row[key] for key in (
                "candidate", "mode", "live_window_mae", "absolute_uplift",
                "relative_improvement", "event_improvement_rate", "worst_event_degradation",
                "live_first_row_mae", "live_latest_row_mae"
            )}
            for row in leaderboard[:10]
        ],
        "best_folds": best["folds"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
