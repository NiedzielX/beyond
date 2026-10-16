#!/usr/bin/env python3
"""C1-alpha live-correction model tournament.

Uses completed Ekstraklasa events with full PIT live trajectories and reconstructs
current-compatible Structural Prior checkpoints from the frozen Runtime v1
artifacts. Validation is Leave-One-Event-Out only; random snapshot splits are
forbidden.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.demand_engine.current_structural_prior_features import (
    CurrentStructuralPriorEvent,
    build_current_structural_prior_row,
)
from ml.demand_engine.materialize_structural_priors import build_sporting_state

HORIZON_DAYS = {"T-30": 30, "T-14": 14, "T-7": 7, "T-3": 3, "T-1": 1}
HORIZON_ORDER = ["T-30", "T-14", "T-7", "T-3", "T-1"]

NUMERIC_LIVE_FEATURES = [
    "hours_to_kickoff",
    "days_to_kickoff",
    "snapshot_age_minutes",
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
    "net_removed_72h",
    "velocity_72h",
    "net_removed_7d",
    "velocity_7d",
    "velocity_6h_pct_of_first_per_hour",
    "velocity_24h_pct_of_first_per_hour",
    "velocity_72h_pct_of_first_per_hour",
    "velocity_7d_pct_of_first_per_hour",
    "velocity_6h_pct_of_capacity_per_hour",
    "velocity_24h_pct_of_capacity_per_hour",
    "velocity_72h_pct_of_capacity_per_hour",
    "velocity_7d_pct_of_capacity_per_hour",
    "acceleration_6h_vs_24h",
    "acceleration_24h_vs_72h",
    "acceleration_72h_vs_7d",
    "matched_sector_count",
    "entered_sector_count",
    "left_sector_count",
    "matched_absorption",
    "matched_release",
    "coverage_inventory_effect",
    "raw_snapshot_count",
    "clean_snapshot_count",
    "excluded_anomaly_count",
    "duplicate_timestamp_count",
    "invalid_snapshot_count",
    "observation_window_hours",
    "max_visible_gap_hours",
]

BOOLEAN_LIVE_FEATURES = [
    "checkpoint_ready",
    "sector_coverage_change_flag",
    "release_activity_flag",
    "unexplained_inventory_increase_flag",
    "data_gap_detected",
]


def _artifact_bundle(artifact_dir: Path):
    manifest = json.loads((artifact_dir / "manifest.json").read_text())
    models: dict[str, Any] = {}
    for horizon in HORIZON_ORDER:
        spec = manifest["artifacts"].get(horizon)
        if spec:
            models[horizon] = joblib.load(artifact_dir / spec["filename"])
    historical = pd.read_csv(artifact_dir / manifest["historical_runtime"]["filename"])
    return manifest, models, historical


def _aliases(payload: dict) -> dict[str, str]:
    return {str(row["alias"]): str(row["club_key"]) for row in payload.get("aliases", [])}


def _event_prior_replay(payload: dict, artifact_dir: Path) -> pd.DataFrame:
    manifest, models, historical = _artifact_bundle(artifact_dir)
    aliases = _aliases(payload)
    attendance = pd.DataFrame(payload.get("attendance") or [])
    sporting_matches = payload.get("sportingMatches") or []
    rows: list[dict[str, Any]] = []

    for event in payload.get("events") or []:
        kickoff = pd.Timestamp(event["kickoff_at"])
        if kickoff.tzinfo is None:
            kickoff = kickoff.tz_localize("UTC")
        else:
            kickoff = kickoff.tz_convert("UTC")
        current_event = CurrentStructuralPriorEvent(
            ticket_event_id=int(event["ticket_event_id"]),
            season=str(event["season"]),
            round_no=int(event["round_no"]),
            kickoff_at=kickoff,
            home_club_key=str(event["home_club_key"]),
            away_club_key=str(event["away_club_key"]),
            stadium_capacity=int(event["stadium_capacity"]),
        )

        for horizon in HORIZON_ORDER:
            runtime = models.get(horizon)
            if runtime is None:
                continue
            as_of_at = kickoff - pd.Timedelta(days=HORIZON_DAYS[horizon])
            sporting_state = build_sporting_state(
                sporting_matches,
                aliases,
                as_of_at=as_of_at,
                source_season=str(event["season"]),
            )
            try:
                frame = build_current_structural_prior_row(
                    historical_matches=historical,
                    current_attendance=attendance,
                    sporting_state=sporting_state,
                    event=current_event,
                    horizon=horizon,
                )
                p50 = float(runtime.predict(frame)[0])
            except Exception as exc:  # fail per checkpoint, not entire tournament
                rows.append({
                    "ticket_event_id": int(event["ticket_event_id"]),
                    "horizon": horizon,
                    "target_as_of_at": as_of_at,
                    "prior_p50": np.nan,
                    "prior_error": str(exc),
                })
                continue
            rows.append({
                "ticket_event_id": int(event["ticket_event_id"]),
                "horizon": horizon,
                "target_as_of_at": as_of_at,
                "prior_p50": p50,
                "prior_model_spec_id": runtime.spec.model_spec_id,
                "artifact_version": manifest["artifact_version"],
                "prior_error": None,
            })
    return pd.DataFrame(rows)


def _choose_prior(priors: pd.DataFrame, event_id: int, as_of_at: pd.Timestamp) -> dict | None:
    event_priors = priors[
        (priors["ticket_event_id"] == event_id)
        & priors["prior_p50"].notna()
        & (pd.to_datetime(priors["target_as_of_at"], utc=True) <= as_of_at)
    ].copy()
    if event_priors.empty:
        return None
    event_priors["target_as_of_at"] = pd.to_datetime(event_priors["target_as_of_at"], utc=True)
    row = event_priors.sort_values("target_as_of_at").iloc[-1]
    return row.to_dict()


def _training_frame(payload: dict, priors: pd.DataFrame) -> pd.DataFrame:
    events = {int(row["ticket_event_id"]): row for row in payload.get("events") or []}
    records: list[dict[str, Any]] = []
    for row in payload.get("liveRows") or []:
        event_id = int(row["ticket_event_id"])
        event = events[event_id]
        f = dict(row.get("features") or {})
        as_of = pd.Timestamp(f.get("as_of_at") or row["requested_as_of_at"])
        if as_of.tzinfo is None:
            as_of = as_of.tz_localize("UTC")
        else:
            as_of = as_of.tz_convert("UTC")
        prior = _choose_prior(priors, event_id, as_of)
        if prior is None:
            continue

        capacity = float(event["stadium_capacity"])
        actual = float(event["actual_attendance"])
        prior_p50 = float(prior["prior_p50"])
        rec: dict[str, Any] = {
            "ticket_event_id": event_id,
            "club_slug": event["club_slug"],
            "home_team": event["home_team"],
            "away_team": event["away_team"],
            "actual_attendance": actual,
            "stadium_capacity": capacity,
            "as_of_at": as_of,
            "prior_horizon": prior["horizon"],
            "prior_p50": prior_p50,
            "prior_expected_occupancy": prior_p50 / capacity,
            "target_residual_attendance": actual - prior_p50,
            "target_residual_occupancy": actual / capacity - prior_p50 / capacity,
            "signal_ready": 1.0 if str(f.get("signal_readiness")) == "ready" else 0.0,
            "feature_quality_good": 1.0 if str(f.get("feature_quality")) in {"sector_matched_plus_raw", "raw_only"} else 0.0,
        }
        for key in NUMERIC_LIVE_FEATURES:
            rec[key] = pd.to_numeric(f.get(key), errors="coerce")
        for key in BOOLEAN_LIVE_FEATURES:
            value = f.get(key)
            rec[key] = np.nan if value is None else float(bool(value))
        records.append(rec)

    frame = pd.DataFrame(records)
    if frame.empty:
        raise RuntimeError("C1 training frame is empty after Structural Prior replay")
    frame = frame.sort_values(["ticket_event_id", "as_of_at"]).reset_index(drop=True)
    return frame


def _feature_columns(frame: pd.DataFrame) -> list[str]:
    columns = [
        "prior_p50",
        "prior_expected_occupancy",
        "stadium_capacity",
        "signal_ready",
        "feature_quality_good",
        *NUMERIC_LIVE_FEATURES,
        *BOOLEAN_LIVE_FEATURES,
    ]
    return [column for column in columns if column in frame.columns]


def _event_weights(frame: pd.DataFrame) -> np.ndarray:
    counts = frame.groupby("ticket_event_id")["ticket_event_id"].transform("count").astype(float)
    weights = 1.0 / counts.to_numpy()
    return weights / np.mean(weights)


def _linear_pipeline(model) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
        ("model", model),
    ])


def _tree_pipeline(model) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("model", model),
    ])


def _candidates() -> list[tuple[str, Any]]:
    candidates: list[tuple[str, Any]] = []
    for alpha in (1.0, 10.0, 30.0, 100.0):
        candidates.append((f"ridge_a{alpha:g}", _linear_pipeline(Ridge(alpha=alpha))))
    for alpha in (0.001, 0.01, 0.1):
        for l1_ratio in (0.1, 0.5, 0.9):
            candidates.append((
                f"elastic_a{alpha:g}_l1{l1_ratio:g}",
                _linear_pipeline(ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=10000, random_state=42)),
            ))
    for epsilon in (1.35, 1.5):
        for alpha in (0.0001, 0.001):
            candidates.append((
                f"huber_e{epsilon:g}_a{alpha:g}",
                _linear_pipeline(HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=1000)),
            ))
    for leaves, min_leaf, l2 in ((7, 8, 1.0), (15, 8, 1.0), (15, 12, 5.0), (31, 12, 10.0)):
        candidates.append((
            f"hist_l{leaves}_min{min_leaf}_l2{l2:g}",
            _tree_pipeline(HistGradientBoostingRegressor(
                loss="absolute_error",
                learning_rate=0.05,
                max_iter=160,
                max_leaf_nodes=leaves,
                min_samples_leaf=min_leaf,
                l2_regularization=l2,
                random_state=42,
            )),
        ))
    for leaf in (3, 5, 8):
        candidates.append((
            f"extra_leaf{leaf}",
            _tree_pipeline(ExtraTreesRegressor(
                n_estimators=400,
                min_samples_leaf=leaf,
                max_features=0.7,
                random_state=42,
                n_jobs=-1,
            )),
        ))
        candidates.append((
            f"rf_leaf{leaf}",
            _tree_pipeline(RandomForestRegressor(
                n_estimators=400,
                min_samples_leaf=leaf,
                max_features=0.7,
                random_state=42,
                n_jobs=-1,
            )),
        ))

    try:
        from xgboost import XGBRegressor
        for depth, min_child in ((2, 5), (3, 8)):
            candidates.append((
                f"xgb_d{depth}_child{min_child}",
                _tree_pipeline(XGBRegressor(
                    n_estimators=250,
                    max_depth=depth,
                    learning_rate=0.03,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    min_child_weight=min_child,
                    reg_alpha=1.0,
                    reg_lambda=10.0,
                    objective="reg:absoluteerror",
                    random_state=42,
                    n_jobs=2,
                )),
            ))
    except ImportError:
        pass

    try:
        from lightgbm import LGBMRegressor
        for leaves, min_child in ((7, 10), (15, 15)):
            candidates.append((
                f"lgbm_l{leaves}_min{min_child}",
                _tree_pipeline(LGBMRegressor(
                    objective="regression_l1",
                    n_estimators=250,
                    learning_rate=0.03,
                    num_leaves=leaves,
                    min_child_samples=min_child,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=1.0,
                    reg_lambda=10.0,
                    random_state=42,
                    verbosity=-1,
                    n_jobs=2,
                )),
            ))
    except ImportError:
        pass
    return candidates


def _fit_with_weights(model: Any, x: pd.DataFrame, y: np.ndarray, weights: np.ndarray):
    fitted = clone(model)
    try:
        fitted.fit(x, y, model__sample_weight=weights)
    except (TypeError, ValueError):
        fitted.fit(x, y)
    return fitted


def _evaluate_candidate(
    frame: pd.DataFrame,
    features: list[str],
    name: str,
    model: Any | None,
    target_mode: str,
) -> dict[str, Any]:
    event_ids = sorted(int(value) for value in frame["ticket_event_id"].unique())
    folds: list[dict[str, Any]] = []

    for held_out in event_ids:
        train = frame[frame["ticket_event_id"] != held_out].copy()
        test = frame[frame["ticket_event_id"] == held_out].copy()
        actual = test["actual_attendance"].astype(float).to_numpy()
        prior = test["prior_p50"].astype(float).to_numpy()
        capacity = test["stadium_capacity"].astype(float).to_numpy()

        if name == "zero_correction":
            live = prior.copy()
        elif name == "bias_mean":
            if target_mode == "attendance":
                correction = train.groupby("ticket_event_id")["target_residual_attendance"].mean().mean()
                live = prior + float(correction)
            else:
                correction = train.groupby("ticket_event_id")["target_residual_occupancy"].mean().mean()
                live = prior + float(correction) * capacity
        elif name == "bias_median":
            if target_mode == "attendance":
                correction = train.groupby("ticket_event_id")["target_residual_attendance"].mean().median()
                live = prior + float(correction)
            else:
                correction = train.groupby("ticket_event_id")["target_residual_occupancy"].mean().median()
                live = prior + float(correction) * capacity
        else:
            target_column = (
                "target_residual_attendance" if target_mode == "attendance" else "target_residual_occupancy"
            )
            weights = _event_weights(train)
            fitted = _fit_with_weights(
                model,
                train[features],
                train[target_column].astype(float).to_numpy(),
                weights,
            )
            correction = np.asarray(fitted.predict(test[features]), dtype=float)
            live = prior + correction if target_mode == "attendance" else prior + correction * capacity

        live = np.clip(live, 0.0, capacity)
        prior_ae = np.abs(prior - actual)
        live_ae = np.abs(live - actual)
        folds.append({
            "ticket_event_id": held_out,
            "home_team": str(test["home_team"].iloc[0]),
            "away_team": str(test["away_team"].iloc[0]),
            "rows": int(len(test)),
            "prior_mae": float(np.mean(prior_ae)),
            "live_mae": float(np.mean(live_ae)),
            "uplift": float(np.mean(prior_ae) - np.mean(live_ae)),
            "prior_latest_error": float(prior_ae[-1]),
            "live_latest_error": float(live_ae[-1]),
            "improved": bool(np.mean(live_ae) < np.mean(prior_ae)),
        })

    prior_mae = float(np.mean([fold["prior_mae"] for fold in folds]))
    live_mae = float(np.mean([fold["live_mae"] for fold in folds]))
    prior_latest = float(np.mean([fold["prior_latest_error"] for fold in folds]))
    live_latest = float(np.mean([fold["live_latest_error"] for fold in folds]))
    return {
        "candidate": name,
        "target_mode": target_mode,
        "event_count": len(folds),
        "prior_mae": prior_mae,
        "live_mae": live_mae,
        "absolute_uplift": prior_mae - live_mae,
        "relative_improvement": (prior_mae - live_mae) / prior_mae if prior_mae else 0.0,
        "event_improvement_rate": float(np.mean([fold["improved"] for fold in folds])),
        "worst_event_degradation": float(max(fold["live_mae"] - fold["prior_mae"] for fold in folds)),
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
    if not payload.get("ok", True):
        raise RuntimeError(f"C1 export failed: {payload}")
    priors = _event_prior_replay(payload, args.artifact_dir)
    frame = _training_frame(payload, priors)
    features = _feature_columns(frame)

    event_counts = frame.groupby("ticket_event_id").size().to_dict()
    results: list[dict[str, Any]] = []
    for target_mode in ("attendance", "occupancy"):
        results.append(_evaluate_candidate(frame, features, "zero_correction", None, target_mode))
        results.append(_evaluate_candidate(frame, features, "bias_mean", None, target_mode))
        results.append(_evaluate_candidate(frame, features, "bias_median", None, target_mode))
        for name, model in _candidates():
            results.append(_evaluate_candidate(frame, features, name, model, target_mode))

    results.sort(key=lambda row: (row["live_mae"], row["worst_event_degradation"], row["candidate"]))
    incumbent = next(row for row in results if row["candidate"] == "zero_correction" and row["target_mode"] == "attendance")
    best = results[0]
    report = {
        "experiment": "c1-alpha-model-tournament-v1",
        "dataset_version": payload.get("version"),
        "sampling": payload.get("sampling"),
        "artifact_version": json.loads((args.artifact_dir / "manifest.json").read_text())["artifact_version"],
        "event_count": int(frame["ticket_event_id"].nunique()),
        "row_count": int(len(frame)),
        "rows_per_event": {str(k): int(v) for k, v in event_counts.items()},
        "feature_count": len(features),
        "features": features,
        "validation": "leave-one-event-out; equal event weighting in training and metrics",
        "incumbent": incumbent,
        "best": best,
        "goal": {
            "beat_structural_prior": bool(best["live_mae"] < incumbent["live_mae"]),
            "under_1700": bool(best["live_mae"] < 1700.0),
            "under_1500_stretch": bool(best["live_mae"] < 1500.0),
        },
        "leaderboard": results,
        "prior_replay": priors.to_dict(orient="records"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({
        "experiment": report["experiment"],
        "event_count": report["event_count"],
        "row_count": report["row_count"],
        "incumbent": {k: incumbent[k] for k in ("prior_mae", "live_mae")},
        "best": {k: best[k] for k in ("candidate", "target_mode", "live_mae", "absolute_uplift", "relative_improvement", "event_improvement_rate", "worst_event_degradation")},
        "goal": report["goal"],
        "top_10": [
            {k: row[k] for k in ("candidate", "target_mode", "live_mae", "absolute_uplift", "relative_improvement", "event_improvement_rate", "worst_event_degradation")}
            for row in results[:10]
        ],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
