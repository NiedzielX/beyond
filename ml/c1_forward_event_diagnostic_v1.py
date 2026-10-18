#!/usr/bin/env python3
"""Retrospective diagnostic for the four chronological C1 forward folds.

This experiment does NOT retune or modify frozen C1 v8. It explains why the raw
Live expert can lose to Structural Prior by inspecting row paths, train/test
feature drift, and leave-one-feature-group-out sensitivity on exactly the same
chronological folds used by c1_walk_forward_policy_validation_v1.

Ablations are diagnostic sensitivity tests, not causal attribution and not model
selection evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import Ridge

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay, _training_frame
from ml.c1_alpha_reliability_policy_v8 import POLICY_ID, event_policy_rows
from ml.c1_alpha_t1_tournament_v2 import COMPACT_NUMERIC, WINDOW_HOURS, pipeline
from ml.c1_synthetic_trajectory_validation_v1 import (
    MIN_WALK_FORWARD_TRAIN_EVENTS,
    PROFILES,
    SEED,
    _event_kickoff_map,
    augment_training,
    training_weights,
)

EXPERIMENT = "c1-forward-event-diagnostic-v1"
REAL_ONLY = next(profile for profile in PROFILES if profile.name == "real_only")

FEATURE_GROUPS: dict[str, list[str]] = {
    "baseline_prior": [
        "prior_p50",
        "prior_expected_occupancy",
        "stadium_capacity",
        "hours_to_kickoff",
    ],
    "inventory_level": [
        "available_total",
        "first_available_total",
        "available_index",
        "available_share_of_capacity",
        "net_removed_since_first",
    ],
    "motion_velocity": [
        "net_removed_since_previous",
        "velocity_since_previous",
        "net_removed_6h",
        "velocity_6h",
        "net_removed_24h",
        "velocity_24h",
        "acceleration_6h_vs_24h",
        "matched_absorption",
    ],
    "release_coverage": [
        "matched_sector_count",
        "matched_release",
        "coverage_inventory_effect",
        "release_activity_flag",
        "sector_coverage_change_flag",
        "unexplained_inventory_increase_flag",
    ],
    "data_quality": [
        "raw_snapshot_count",
        "clean_snapshot_count",
        "observation_window_hours",
        "max_visible_gap_hours",
        "signal_ready",
        "feature_quality_good",
        "data_gap_detected",
    ],
}


def _fit_predict_features(
    train: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    seed: int,
) -> np.ndarray:
    """Replicate the real-only v2 Ridge expert with an explicit feature subset."""
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)
    selected = [column for column in features if column in train.columns and column in test.columns]
    if not selected:
        raise RuntimeError("Diagnostic feature subset is empty")

    augmented = augment_training(train, REAL_ONLY, seed)
    model = pipeline(selected, club_aware=False, model=Ridge(alpha=10.0), scale=True)
    fitted = clone(model)
    target = (
        augmented["actual_attendance"].astype(float)
        / augmented["stadium_capacity"].astype(float)
    ).to_numpy()
    fitted.fit(
        augmented[selected],
        target,
        model__sample_weight=training_weights(augmented, REAL_ONLY.synthetic_weight_share),
    )
    occupancy = np.asarray(fitted.predict(test[selected]), dtype=float)
    capacity = test["stadium_capacity"].astype(float).to_numpy()
    return np.clip(occupancy * capacity, 0.0, capacity)


def _errors(test: pd.DataFrame, pred: np.ndarray) -> tuple[float, float]:
    ordered = test.sort_values("as_of_at").reset_index(drop=True)
    actual = ordered["actual_attendance"].astype(float).to_numpy()
    pred = np.asarray(pred, dtype=float)
    absolute = np.abs(pred - actual)
    return float(np.mean(absolute)), float(absolute[-1])


def _feature_drift(train: pd.DataFrame, test: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feature in COMPACT_NUMERIC:
        if feature not in train.columns or feature not in test.columns:
            continue
        train_s = pd.to_numeric(train[feature], errors="coerce")
        test_s = pd.to_numeric(test[feature], errors="coerce")
        train_valid = train_s.dropna()
        test_valid = test_s.dropna()
        if train_valid.empty or test_valid.empty:
            robust_shift = None
            train_median = None if train_valid.empty else float(train_valid.median())
            test_median = None if test_valid.empty else float(test_valid.median())
            scale = None
        else:
            train_median = float(train_valid.median())
            test_median = float(test_valid.median())
            q25 = float(train_valid.quantile(0.25))
            q75 = float(train_valid.quantile(0.75))
            iqr = q75 - q25
            std = float(train_valid.std(ddof=0))
            scale = iqr if iqr > 1e-9 else std
            robust_shift = None if scale <= 1e-9 else (test_median - train_median) / scale
        rows.append({
            "feature": feature,
            "group": next((name for name, values in FEATURE_GROUPS.items() if feature in values), "other"),
            "train_median": train_median,
            "test_median": test_median,
            "train_scale_iqr_or_std": scale,
            "robust_median_shift": robust_shift,
            "train_missing_rate": float(train_s.isna().mean()),
            "test_missing_rate": float(test_s.isna().mean()),
            "missing_rate_delta": float(test_s.isna().mean() - train_s.isna().mean()),
        })
    rows.sort(
        key=lambda row: max(
            abs(row["robust_median_shift"] or 0.0),
            abs(row["missing_rate_delta"]) * 4.0,
        ),
        reverse=True,
    )
    return rows


def _path_rows(test: pd.DataFrame, live: np.ndarray) -> list[dict[str, Any]]:
    policy_rows, _ = event_policy_rows(test, live)
    policy_rows = policy_rows.sort_values("as_of_at").reset_index(drop=True)
    out: list[dict[str, Any]] = []
    signal_fields = [
        "available_share_of_capacity",
        "available_index",
        "net_removed_since_first",
        "velocity_since_previous",
        "velocity_6h",
        "velocity_24h",
        "matched_absorption",
        "matched_release",
        "coverage_inventory_effect",
        "feature_quality_good",
        "release_activity_flag",
        "sector_coverage_change_flag",
        "data_gap_detected",
    ]
    for _, row in policy_rows.iterrows():
        actual = float(row["actual_attendance"])
        prior = float(row["prior_p50"])
        raw_live = float(row["live_p50"])
        record: dict[str, Any] = {
            "as_of_at": str(row["as_of_at"]),
            "hours_to_kickoff": float(row["hours_to_kickoff"]),
            "actual_attendance": actual,
            "prior_p50": prior,
            "raw_live_p50": raw_live,
            "prior_signed_error": prior - actual,
            "raw_live_signed_error": raw_live - actual,
            "prior_abs_error": abs(prior - actual),
            "raw_live_abs_error": abs(raw_live - actual),
            "selected_expert": str(row["selected_expert"]),
            "policy_prediction": float(row["policy_prediction"]),
            "policy_reason": str(row["reason_code"]),
            "abs_disagreement_occupancy": float(row["abs_disagreement_occupancy"]),
            "live_observation_count_to_date": int(row["live_observation_count_to_date"]),
            "live_slope_occupancy_per_hour_to_date": (
                None
                if pd.isna(row["live_slope_occupancy_per_hour_to_date"])
                else float(row["live_slope_occupancy_per_hour_to_date"])
            ),
        }
        for field in signal_fields:
            if field not in row.index:
                continue
            value = row[field]
            record[field] = None if pd.isna(value) else float(value)
        out.append(record)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    priors = _event_prior_replay(payload, args.artifact_dir)
    frame = _training_frame(payload, priors)
    frame = frame[
        (frame["hours_to_kickoff"].astype(float) >= 0.0)
        & (frame["hours_to_kickoff"].astype(float) <= WINDOW_HOURS)
        & (frame["prior_horizon"] == "T-1")
    ].copy().reset_index(drop=True)
    frame["as_of_at"] = pd.to_datetime(frame["as_of_at"], utc=True)

    kickoff = _event_kickoff_map(frame)
    ordered_events = sorted(kickoff, key=lambda event_id: (kickoff[event_id], event_id))
    folds: list[dict[str, Any]] = []

    full_features = [feature for feature in COMPACT_NUMERIC if feature in frame.columns]

    for position, held_out in enumerate(ordered_events):
        earlier = ordered_events[:position]
        if len(earlier) < MIN_WALK_FORWARD_TRAIN_EVENTS:
            continue
        train = frame[frame["ticket_event_id"].isin(earlier)].copy().reset_index(drop=True)
        test = (
            frame[frame["ticket_event_id"] == held_out]
            .copy()
            .sort_values("as_of_at")
            .reset_index(drop=True)
        )
        seed = SEED + int(held_out) * 911 + len(REAL_ONLY.name)
        full_pred = _fit_predict_features(train, test, full_features, seed)
        full_window_mae, full_latest_mae = _errors(test, full_pred)
        prior_window_mae, prior_latest_mae = _errors(test, test["prior_p50"].astype(float).to_numpy())

        ablations: dict[str, Any] = {}
        for group_name, group_features in FEATURE_GROUPS.items():
            retained = [feature for feature in full_features if feature not in set(group_features)]
            pred = _fit_predict_features(train, test, retained, seed)
            window_mae, latest_mae = _errors(test, pred)
            ablations[group_name] = {
                "removed_features": [feature for feature in group_features if feature in full_features],
                "retained_feature_count": len(retained),
                "window_mae": window_mae,
                "latest_mae": latest_mae,
                "window_mae_delta_vs_full": window_mae - full_window_mae,
                "latest_mae_delta_vs_full": latest_mae - full_latest_mae,
                "dropping_group_improves_window": window_mae < full_window_mae,
                "dropping_group_improves_latest": latest_mae < full_latest_mae,
            }

        folds.append({
            "ticket_event_id": int(held_out),
            "home_team": str(test["home_team"].iloc[0]),
            "away_team": str(test["away_team"].iloc[0]),
            "kickoff_at": str(kickoff[held_out]),
            "training_event_count": len(earlier),
            "training_event_ids": [int(value) for value in earlier],
            "row_count": int(len(test)),
            "actual_attendance": float(test["actual_attendance"].iloc[-1]),
            "prior_window_mae": prior_window_mae,
            "prior_latest_mae": prior_latest_mae,
            "raw_live_window_mae": full_window_mae,
            "raw_live_latest_mae": full_latest_mae,
            "latest_prior_signed_error": float(test["prior_p50"].iloc[-1] - test["actual_attendance"].iloc[-1]),
            "latest_raw_live_signed_error": float(full_pred[-1] - test["actual_attendance"].iloc[-1]),
            "path": _path_rows(test, full_pred),
            "top_feature_drift": _feature_drift(train, test)[:15],
            "ablations": ablations,
        })

    if not folds:
        raise RuntimeError("No chronological diagnostic folds were produced")

    full_window_mae = float(np.mean([fold["raw_live_window_mae"] for fold in folds]))
    prior_window_mae = float(np.mean([fold["prior_window_mae"] for fold in folds]))
    full_latest_mae = float(np.mean([fold["raw_live_latest_mae"] for fold in folds]))
    prior_latest_mae = float(np.mean([fold["prior_latest_mae"] for fold in folds]))

    ablation_summary: list[dict[str, Any]] = []
    for group_name in FEATURE_GROUPS:
        window_values = [fold["ablations"][group_name]["window_mae"] for fold in folds]
        latest_values = [fold["ablations"][group_name]["latest_mae"] for fold in folds]
        improved_window = sum(
            bool(fold["ablations"][group_name]["dropping_group_improves_window"])
            for fold in folds
        )
        improved_latest = sum(
            bool(fold["ablations"][group_name]["dropping_group_improves_latest"])
            for fold in folds
        )
        mean_window = float(np.mean(window_values))
        mean_latest = float(np.mean(latest_values))
        ablation_summary.append({
            "removed_group": group_name,
            "window_mae": mean_window,
            "window_mae_delta_vs_full": mean_window - full_window_mae,
            "latest_mae": mean_latest,
            "latest_mae_delta_vs_full": mean_latest - full_latest_mae,
            "events_improved_window": int(improved_window),
            "events_improved_latest": int(improved_latest),
            "event_count": len(folds),
        })
    ablation_summary.sort(key=lambda row: row["window_mae"])

    latest_signed = [float(fold["latest_raw_live_signed_error"]) for fold in folds]
    report = {
        "experiment": EXPERIMENT,
        "policy_id": POLICY_ID,
        "dataset_version": payload.get("version"),
        "governance": {
            "retrospective_only": True,
            "frozen_v8_changed": False,
            "policy_thresholds_changed": False,
            "production_activation": False,
            "ablation_is_causal_attribution": False,
            "ablation_used_for_model_selection": False,
        },
        "event_count": len(folds),
        "row_count": int(sum(fold["row_count"] for fold in folds)),
        "prior_window_mae": prior_window_mae,
        "raw_live_window_mae": full_window_mae,
        "prior_latest_mae": prior_latest_mae,
        "raw_live_latest_mae": full_latest_mae,
        "latest_live_error_direction": {
            "underprediction_events": int(sum(value < 0 for value in latest_signed)),
            "overprediction_events": int(sum(value > 0 for value in latest_signed)),
            "exact_events": int(sum(value == 0 for value in latest_signed)),
        },
        "feature_groups": FEATURE_GROUPS,
        "ablation_summary": ablation_summary,
        "folds": folds,
        "interpretation_guard": (
            "A group whose removal improves MAE is a diagnostic suspect only. Correlated features, "
            "small event count, and model refitting mean this experiment cannot prove causality."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "event_count": report["event_count"],
        "prior_window_mae": prior_window_mae,
        "raw_live_window_mae": full_window_mae,
        "prior_latest_mae": prior_latest_mae,
        "raw_live_latest_mae": full_latest_mae,
        "latest_live_error_direction": report["latest_live_error_direction"],
        "ablation_summary": ablation_summary,
        "events": [{
            "ticket_event_id": fold["ticket_event_id"],
            "match": f"{fold['home_team']} - {fold['away_team']}",
            "prior_window_mae": fold["prior_window_mae"],
            "raw_live_window_mae": fold["raw_live_window_mae"],
            "latest_raw_live_signed_error": fold["latest_raw_live_signed_error"],
        } for fold in folds],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
