#!/usr/bin/env python3
"""C1-alpha T-1 / final-24h tournament v2.

The v1 all-phase tournament mixed sparse T-14/T-7 evidence with much richer
late-stage trajectories. v2 deliberately focuses on the shared late window:
from T-1 cutoff to kickoff. All validation remains Leave-One-Event-Out.

This is an experimental model-selection run. It does not activate production.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.c1_alpha_model_tournament_v1 import (
    BOOLEAN_LIVE_FEATURES,
    NUMERIC_LIVE_FEATURES,
    _event_prior_replay,
    _training_frame,
)

WINDOW_HOURS = 24.0

# Keep v2 deliberately compact. These features are directly interpretable and
# are available point-in-time in the current live feature contract.
COMPACT_NUMERIC = [
    "prior_p50",
    "prior_expected_occupancy",
    "stadium_capacity",
    "hours_to_kickoff",
    "available_total",
    "first_available_total",
    "available_index",
    "available_share_of_capacity",
    "net_removed_since_first",
    "net_removed_since_previous",
    "velocity_since_previous",
    "net_removed_6h",
    "velocity_6h",
    "net_removed_24h",
    "velocity_24h",
    "acceleration_6h_vs_24h",
    "matched_sector_count",
    "matched_absorption",
    "matched_release",
    "coverage_inventory_effect",
    "raw_snapshot_count",
    "clean_snapshot_count",
    "observation_window_hours",
    "max_visible_gap_hours",
    "signal_ready",
    "feature_quality_good",
    "release_activity_flag",
    "sector_coverage_change_flag",
    "unexplained_inventory_increase_flag",
    "data_gap_detected",
]

LEAN_NUMERIC = [
    "prior_expected_occupancy",
    "hours_to_kickoff",
    "available_index",
    "available_share_of_capacity",
    "velocity_6h",
    "velocity_24h",
    "acceleration_6h_vs_24h",
    "matched_absorption",
    "matched_release",
    "release_activity_flag",
    "sector_coverage_change_flag",
    "feature_quality_good",
]


def event_weights(frame: pd.DataFrame) -> np.ndarray:
    counts = frame.groupby("ticket_event_id")["ticket_event_id"].transform("count").astype(float)
    weights = 1.0 / counts.to_numpy()
    return weights / np.mean(weights)


def preprocessor(numeric: list[str], club_aware: bool, scale: bool) -> ColumnTransformer:
    numeric_steps: list[tuple[str, Any]] = [
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
    ]
    if scale:
        numeric_steps.append(("scale", StandardScaler()))
    transformers: list[tuple[str, Any, list[str]]] = [
        ("num", Pipeline(numeric_steps), numeric),
    ]
    if club_aware:
        transformers.append((
            "club",
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ["club_slug"],
        ))
    return ColumnTransformer(transformers, remainder="drop")


def pipeline(numeric: list[str], club_aware: bool, model: Any, scale: bool = False) -> Pipeline:
    return Pipeline([
        ("prep", preprocessor(numeric, club_aware, scale)),
        ("model", model),
    ])


def candidate_specs(frame: pd.DataFrame) -> list[dict[str, Any]]:
    compact = [c for c in COMPACT_NUMERIC if c in frame.columns]
    lean = [c for c in LEAN_NUMERIC if c in frame.columns]
    specs: list[dict[str, Any]] = []

    for features_name, features in (("lean", lean), ("compact", compact)):
        for club_aware in (False, True):
            suffix = "club" if club_aware else "generic"
            for alpha in (10.0, 100.0, 1000.0):
                specs.append({
                    "name": f"ridge_{features_name}_{suffix}_a{alpha:g}",
                    "target_mode": "residual_occupancy",
                    "features": features,
                    "model": pipeline(features, club_aware, Ridge(alpha=alpha), scale=True),
                })
                specs.append({
                    "name": f"ridge_directocc_{features_name}_{suffix}_a{alpha:g}",
                    "target_mode": "direct_occupancy",
                    "features": features,
                    "model": pipeline(features, club_aware, Ridge(alpha=alpha), scale=True),
                })

    # Constrained nonlinear challengers. Small grids only.
    for club_aware in (False, True):
        suffix = "club" if club_aware else "generic"
        specs.extend([
            {
                "name": f"hist_lean_{suffix}",
                "target_mode": "residual_occupancy",
                "features": lean,
                "model": pipeline(
                    lean,
                    club_aware,
                    HistGradientBoostingRegressor(
                        loss="absolute_error",
                        learning_rate=0.05,
                        max_iter=120,
                        max_leaf_nodes=7,
                        min_samples_leaf=6,
                        l2_regularization=5.0,
                        random_state=42,
                    ),
                ),
            },
            {
                "name": f"gbr_huber_lean_{suffix}",
                "target_mode": "residual_occupancy",
                "features": lean,
                "model": pipeline(
                    lean,
                    club_aware,
                    GradientBoostingRegressor(
                        loss="huber",
                        n_estimators=120,
                        learning_rate=0.03,
                        max_depth=2,
                        min_samples_leaf=4,
                        random_state=42,
                    ),
                ),
            },
            {
                "name": f"extra_lean_{suffix}",
                "target_mode": "residual_occupancy",
                "features": lean,
                "model": pipeline(
                    lean,
                    club_aware,
                    ExtraTreesRegressor(
                        n_estimators=400,
                        min_samples_leaf=4,
                        max_features=0.7,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            },
            {
                "name": f"rf_lean_{suffix}",
                "target_mode": "residual_occupancy",
                "features": lean,
                "model": pipeline(
                    lean,
                    club_aware,
                    RandomForestRegressor(
                        n_estimators=400,
                        min_samples_leaf=4,
                        max_features=0.7,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            },
        ])
    return specs


def fit_with_weights(model: Pipeline, x: pd.DataFrame, y: np.ndarray, weights: np.ndarray) -> Pipeline:
    fitted = clone(model)
    try:
        fitted.fit(x, y, model__sample_weight=weights)
    except (TypeError, ValueError):
        fitted.fit(x, y)
    return fitted


def predictions_for_mode(
    spec: dict[str, Any],
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> np.ndarray:
    features = spec["features"] + (["club_slug"] if "_club_" in spec["name"] or spec["name"].endswith("_club") else [])
    # ColumnTransformer expects club_slug separately; duplicate removal keeps the
    # raw dataframe contract simple.
    features = list(dict.fromkeys(features))
    mode = spec["target_mode"]
    if mode == "residual_occupancy":
        target = train["target_residual_occupancy"].astype(float).to_numpy()
    elif mode == "direct_occupancy":
        target = (train["actual_attendance"].astype(float) / train["stadium_capacity"].astype(float)).to_numpy()
    else:
        raise KeyError(mode)
    fitted = fit_with_weights(spec["model"], train[features], target, event_weights(train))
    raw = np.asarray(fitted.predict(test[features]), dtype=float)
    capacity = test["stadium_capacity"].astype(float).to_numpy()
    prior = test["prior_p50"].astype(float).to_numpy()
    if mode == "residual_occupancy":
        pred = prior + raw * capacity
    else:
        pred = raw * capacity
    return np.clip(pred, 0.0, capacity)


def evaluate(frame: pd.DataFrame, spec: dict[str, Any] | None, name: str) -> dict[str, Any]:
    events = sorted(int(x) for x in frame["ticket_event_id"].unique())
    folds: list[dict[str, Any]] = []
    for held_out in events:
        train = frame[frame["ticket_event_id"] != held_out].copy()
        test = frame[frame["ticket_event_id"] == held_out].copy().sort_values("as_of_at")
        actual = test["actual_attendance"].astype(float).to_numpy()
        prior = test["prior_p50"].astype(float).to_numpy()

        if name == "zero_correction":
            live = prior.copy()
        elif name == "bias_median":
            event_residuals = train.groupby("ticket_event_id")["target_residual_occupancy"].mean()
            correction = float(event_residuals.median())
            live = prior + correction * test["stadium_capacity"].astype(float).to_numpy()
        else:
            assert spec is not None
            live = predictions_for_mode(spec, train, test)

        prior_err = np.abs(prior - actual)
        live_err = np.abs(live - actual)
        # first row = earliest available observation inside final-24h window;
        # latest row = freshest pre-kickoff observation.
        folds.append({
            "ticket_event_id": held_out,
            "home_team": str(test["home_team"].iloc[0]),
            "away_team": str(test["away_team"].iloc[0]),
            "rows": int(len(test)),
            "first_hours_to_kickoff": float(test["hours_to_kickoff"].iloc[0]),
            "latest_hours_to_kickoff": float(test["hours_to_kickoff"].iloc[-1]),
            "prior_window_mae": float(np.mean(prior_err)),
            "live_window_mae": float(np.mean(live_err)),
            "prior_first_error": float(prior_err[0]),
            "live_first_error": float(live_err[0]),
            "prior_latest_error": float(prior_err[-1]),
            "live_latest_error": float(live_err[-1]),
            "window_improved": bool(np.mean(live_err) < np.mean(prior_err)),
        })

    prior_window = float(np.mean([f["prior_window_mae"] for f in folds]))
    live_window = float(np.mean([f["live_window_mae"] for f in folds]))
    prior_first = float(np.mean([f["prior_first_error"] for f in folds]))
    live_first = float(np.mean([f["live_first_error"] for f in folds]))
    prior_latest = float(np.mean([f["prior_latest_error"] for f in folds]))
    live_latest = float(np.mean([f["live_latest_error"] for f in folds]))
    return {
        "candidate": name,
        "target_mode": "none" if spec is None else spec["target_mode"],
        "event_count": len(folds),
        "prior_window_mae": prior_window,
        "live_window_mae": live_window,
        "absolute_uplift": prior_window - live_window,
        "relative_improvement": (prior_window - live_window) / prior_window if prior_window else 0.0,
        "event_improvement_rate": float(np.mean([f["window_improved"] for f in folds])),
        "worst_event_degradation": float(max(f["live_window_mae"] - f["prior_window_mae"] for f in folds)),
        "prior_first_row_mae": prior_first,
        "live_first_row_mae": live_first,
        "prior_latest_row_mae": prior_latest,
        "live_latest_row_mae": live_latest,
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
    frame = _training_frame(payload, priors)

    # Shared late-stage evidence window. _training_frame already assigns the
    # latest due Structural Prior; inside <=24h this is T-1 for every row.
    frame = frame[
        (frame["hours_to_kickoff"].astype(float) >= 0.0)
        & (frame["hours_to_kickoff"].astype(float) <= WINDOW_HOURS)
        & (frame["prior_horizon"] == "T-1")
    ].copy()
    if frame["ticket_event_id"].nunique() < 6:
        raise RuntimeError("C1-alpha T-1 tournament requires at least 6 independent completed events")

    results = [
        evaluate(frame, None, "zero_correction"),
        evaluate(frame, None, "bias_median"),
    ]
    for spec in candidate_specs(frame):
        results.append(evaluate(frame, spec, spec["name"]))

    results.sort(key=lambda row: (
        row["live_window_mae"],
        row["worst_event_degradation"],
        row["live_latest_row_mae"],
        row["candidate"],
    ))
    incumbent = next(r for r in results if r["candidate"] == "zero_correction")
    best = results[0]

    report = {
        "experiment": "c1-alpha-t1-tournament-v2",
        "window": "T-1 to kickoff / <=24h",
        "dataset_version": payload.get("version"),
        "event_count": int(frame["ticket_event_id"].nunique()),
        "row_count": int(len(frame)),
        "rows_per_event": {str(k): int(v) for k, v in frame.groupby("ticket_event_id").size().to_dict().items()},
        "validation": "Leave-One-Event-Out; equal event weighting; final-24h only",
        "incumbent": incumbent,
        "best": best,
        "goal": {
            "beat_t1_structural_prior": bool(best["live_window_mae"] < incumbent["live_window_mae"]),
            "under_1900": bool(best["live_window_mae"] < 1900.0),
            "under_1700": bool(best["live_window_mae"] < 1700.0),
            "under_1500_stretch": bool(best["live_window_mae"] < 1500.0),
        },
        "leaderboard": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({
        "experiment": report["experiment"],
        "event_count": report["event_count"],
        "row_count": report["row_count"],
        "incumbent": {k: incumbent[k] for k in ("prior_window_mae", "prior_first_row_mae", "prior_latest_row_mae")},
        "best": {k: best[k] for k in (
            "candidate", "target_mode", "live_window_mae", "absolute_uplift",
            "relative_improvement", "event_improvement_rate", "worst_event_degradation",
            "live_first_row_mae", "live_latest_row_mae"
        )},
        "goal": report["goal"],
        "top_10": [
            {k: row[k] for k in (
                "candidate", "target_mode", "live_window_mae", "absolute_uplift",
                "relative_improvement", "event_improvement_rate", "worst_event_degradation",
                "live_first_row_mae", "live_latest_row_mae"
            )}
            for row in results[:10]
        ],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
