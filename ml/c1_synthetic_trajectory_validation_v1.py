#!/usr/bin/env python3
"""Validate C1 v2 with train-only synthetic trajectory augmentation.

The held-out/test event is always 100% real. Synthetic rows are generated only
from training events and preserve each training event's real final attendance.
The augmentation perturbs observable trajectory features to test whether modest
observation-space variation improves generalisation.

This experiment does not change the frozen C1 v8 package or production.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import Ridge

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay, _training_frame
from ml.c1_alpha_t1_tournament_v2 import COMPACT_NUMERIC, WINDOW_HOURS, pipeline

MODEL_NAME = "ridge_directocc_compact_generic_a10"
SEED = 20261018
MIN_WALK_FORWARD_TRAIN_EVENTS = 5

MOTION_FEATURES = [
    "net_removed_since_previous",
    "velocity_since_previous",
    "net_removed_6h",
    "velocity_6h",
    "net_removed_24h",
    "velocity_24h",
    "matched_absorption",
]
PCT_MOTION_FEATURES = [
    "velocity_6h_pct_of_first_per_hour",
    "velocity_24h_pct_of_first_per_hour",
    "velocity_6h_pct_of_capacity_per_hour",
    "velocity_24h_pct_of_capacity_per_hour",
]
RELEASE_FEATURES = ["matched_release", "coverage_inventory_effect"]
DROPOUT_FEATURES = [
    "velocity_since_previous",
    "velocity_6h",
    "velocity_24h",
    "acceleration_6h_vs_24h",
    "matched_absorption",
    "matched_release",
]


@dataclass(frozen=True)
class SyntheticProfile:
    name: str
    copies_per_real_row: int
    synthetic_weight_share: float
    motion_sigma: float
    inventory_sigma_capacity: float
    acceleration_sigma: float
    hours_sigma: float
    dropout_probability: float


PROFILES = [
    SyntheticProfile("real_only", 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    SyntheticProfile("conservative_synthetic", 6, 0.35, 0.08, 0.005, 0.08, 0.35, 0.04),
    SyntheticProfile("stress_synthetic", 6, 0.35, 0.20, 0.015, 0.20, 1.0, 0.12),
]


def _finite_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if np.isfinite(out) else None


def _scale_value(value: Any, factor: float) -> Any:
    numeric = _finite_float(value)
    return value if numeric is None else numeric * factor


def _augment_event(
    event_frame: pd.DataFrame,
    profile: SyntheticProfile,
    rng: np.random.Generator,
) -> list[pd.DataFrame]:
    variants: list[pd.DataFrame] = []
    for variant_no in range(profile.copies_per_real_row):
        variant = event_frame.copy()
        motion_factor = float(np.clip(rng.lognormal(0.0, profile.motion_sigma), 0.55, 1.65))
        release_factor = float(np.clip(rng.lognormal(0.0, profile.motion_sigma / 2.0), 0.70, 1.40))
        hours_shift = float(rng.normal(0.0, profile.hours_sigma))

        for idx in variant.index:
            capacity = _finite_float(variant.at[idx, "stadium_capacity"]) or 0.0
            first_available = _finite_float(variant.at[idx, "first_available_total"])
            removed = _finite_float(variant.at[idx, "net_removed_since_first"])

            if first_available is not None and capacity > 0:
                first_noise = float(rng.normal(0.0, profile.inventory_sigma_capacity * capacity / 2.0))
                synthetic_first = float(np.clip(first_available + first_noise, 0.0, capacity))
                variant.at[idx, "first_available_total"] = synthetic_first
            else:
                synthetic_first = first_available

            if synthetic_first is not None and removed is not None and capacity > 0:
                inventory_noise = float(rng.normal(0.0, profile.inventory_sigma_capacity * capacity))
                synthetic_removed = removed * motion_factor
                synthetic_available = float(np.clip(synthetic_first - synthetic_removed + inventory_noise, 0.0, capacity))
                variant.at[idx, "available_total"] = synthetic_available
                if synthetic_first > 0:
                    variant.at[idx, "available_index"] = synthetic_available / synthetic_first
                variant.at[idx, "available_share_of_capacity"] = synthetic_available / capacity
                variant.at[idx, "net_removed_since_first"] = synthetic_first - synthetic_available

            for feature in MOTION_FEATURES:
                if feature in variant.columns:
                    row_factor = motion_factor * float(np.clip(rng.lognormal(0.0, profile.motion_sigma / 3.0), 0.75, 1.35))
                    variant.at[idx, feature] = _scale_value(variant.at[idx, feature], row_factor)

            for feature in PCT_MOTION_FEATURES:
                if feature in variant.columns:
                    variant.at[idx, feature] = _scale_value(variant.at[idx, feature], motion_factor)

            for feature in RELEASE_FEATURES:
                if feature in variant.columns:
                    variant.at[idx, feature] = _scale_value(variant.at[idx, feature], release_factor)

            if "acceleration_6h_vs_24h" in variant.columns:
                accel = _finite_float(variant.at[idx, "acceleration_6h_vs_24h"])
                if accel is not None:
                    variant.at[idx, "acceleration_6h_vs_24h"] = accel + float(
                        rng.normal(0.0, profile.acceleration_sigma * max(abs(accel), 1.0))
                    )

            hours = _finite_float(variant.at[idx, "hours_to_kickoff"])
            if hours is not None:
                variant.at[idx, "hours_to_kickoff"] = float(np.clip(hours + hours_shift, 0.0, WINDOW_HOURS))

            for feature in DROPOUT_FEATURES:
                if feature in variant.columns and rng.random() < profile.dropout_probability:
                    variant.at[idx, feature] = np.nan

        variant["is_synthetic"] = 1.0
        variant["synthetic_profile"] = profile.name
        variant["synthetic_variant_no"] = variant_no + 1
        variants.append(variant)
    return variants


def augment_training(train: pd.DataFrame, profile: SyntheticProfile, seed: int) -> pd.DataFrame:
    base = train.copy()
    base["is_synthetic"] = 0.0
    base["synthetic_profile"] = "real"
    base["synthetic_variant_no"] = 0
    if profile.copies_per_real_row <= 0:
        return base

    rng = np.random.default_rng(seed)
    parts = [base]
    for _, event_frame in train.groupby("ticket_event_id", sort=True):
        parts.extend(_augment_event(event_frame.copy(), profile, rng))
    return pd.concat(parts, ignore_index=True, sort=False)


def training_weights(frame: pd.DataFrame, synthetic_weight_share: float) -> np.ndarray:
    weights = np.zeros(len(frame), dtype=float)
    for _, indices in frame.groupby("ticket_event_id").groups.items():
        idx = np.asarray(list(indices), dtype=int)
        synthetic = frame.loc[idx, "is_synthetic"].astype(float).to_numpy() > 0.5
        real_idx = idx[~synthetic]
        synthetic_idx = idx[synthetic]
        if len(synthetic_idx) == 0 or synthetic_weight_share <= 0.0:
            weights[real_idx] = 1.0 / max(len(real_idx), 1)
            continue
        weights[real_idx] = (1.0 - synthetic_weight_share) / max(len(real_idx), 1)
        weights[synthetic_idx] = synthetic_weight_share / len(synthetic_idx)
    mean = float(np.mean(weights))
    if mean <= 0:
        raise RuntimeError("Invalid zero training weights")
    return weights / mean


def fit_predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    profile: SyntheticProfile,
    seed: int,
) -> np.ndarray:
    features = [column for column in COMPACT_NUMERIC if column in train.columns and column in test.columns]
    augmented = augment_training(train, profile, seed)
    model = pipeline(features, club_aware=False, model=Ridge(alpha=10.0), scale=True)
    fitted = clone(model)
    target = (
        augmented["actual_attendance"].astype(float)
        / augmented["stadium_capacity"].astype(float)
    ).to_numpy()
    fitted.fit(
        augmented[features],
        target,
        model__sample_weight=training_weights(augmented, profile.synthetic_weight_share),
    )
    occupancy = np.asarray(fitted.predict(test[features]), dtype=float)
    capacity = test["stadium_capacity"].astype(float).to_numpy()
    return np.clip(occupancy * capacity, 0.0, capacity)


def _event_metrics(test: pd.DataFrame, pred: np.ndarray) -> dict[str, Any]:
    ordered = test.copy().sort_values("as_of_at")
    actual = ordered["actual_attendance"].astype(float).to_numpy()
    prior = ordered["prior_p50"].astype(float).to_numpy()
    pred = np.asarray(pred, dtype=float)
    prior_error = np.abs(prior - actual)
    model_error = np.abs(pred - actual)
    return {
        "ticket_event_id": int(ordered["ticket_event_id"].iloc[0]),
        "home_team": str(ordered["home_team"].iloc[0]),
        "away_team": str(ordered["away_team"].iloc[0]),
        "rows": int(len(ordered)),
        "actual_attendance": float(actual[-1]),
        "prior_window_mae": float(np.mean(prior_error)),
        "model_window_mae": float(np.mean(model_error)),
        "prior_latest_error": float(prior_error[-1]),
        "model_latest_error": float(model_error[-1]),
        "prior_latest_prediction": float(prior[-1]),
        "model_latest_prediction": float(pred[-1]),
        "window_improved": bool(np.mean(model_error) < np.mean(prior_error)),
        "latest_improved": bool(model_error[-1] < prior_error[-1]),
    }


def _aggregate(folds: list[dict[str, Any]], name: str) -> dict[str, Any]:
    if not folds:
        return {"profile": name, "event_count": 0, "folds": []}
    prior_window = float(np.mean([row["prior_window_mae"] for row in folds]))
    model_window = float(np.mean([row["model_window_mae"] for row in folds]))
    prior_latest = float(np.mean([row["prior_latest_error"] for row in folds]))
    model_latest = float(np.mean([row["model_latest_error"] for row in folds]))
    return {
        "profile": name,
        "event_count": len(folds),
        "prior_window_mae": prior_window,
        "model_window_mae": model_window,
        "window_absolute_uplift": prior_window - model_window,
        "window_relative_improvement": (prior_window - model_window) / prior_window if prior_window else 0.0,
        "prior_latest_mae": prior_latest,
        "model_latest_mae": model_latest,
        "latest_absolute_uplift": prior_latest - model_latest,
        "latest_relative_improvement": (prior_latest - model_latest) / prior_latest if prior_latest else 0.0,
        "window_improvement_rate": float(np.mean([row["window_improved"] for row in folds])),
        "latest_improvement_rate": float(np.mean([row["latest_improved"] for row in folds])),
        "worst_event_degradation": float(max(row["model_window_mae"] - row["prior_window_mae"] for row in folds)),
        "folds": folds,
    }


def evaluate_loeo(frame: pd.DataFrame, profile: SyntheticProfile) -> dict[str, Any]:
    folds: list[dict[str, Any]] = []
    for held_out in sorted(int(value) for value in frame["ticket_event_id"].unique()):
        train = frame[frame["ticket_event_id"] != held_out].copy()
        test = frame[frame["ticket_event_id"] == held_out].copy().sort_values("as_of_at")
        pred = fit_predict(train, test, profile, SEED + held_out * 101 + len(profile.name))
        folds.append(_event_metrics(test, pred))
    result = _aggregate(folds, profile.name)
    result["validation"] = "Leave-One-Event-Out; held-out event never augmented"
    return result


def _event_kickoff_map(frame: pd.DataFrame) -> dict[int, pd.Timestamp]:
    tmp = frame.copy()
    tmp["as_of_at"] = pd.to_datetime(tmp["as_of_at"], utc=True)
    tmp["_kickoff"] = tmp["as_of_at"] + pd.to_timedelta(tmp["hours_to_kickoff"].astype(float), unit="h")
    return {
        int(event_id): pd.Timestamp(group["_kickoff"].median())
        for event_id, group in tmp.groupby("ticket_event_id")
    }


def evaluate_walk_forward(frame: pd.DataFrame, profile: SyntheticProfile) -> dict[str, Any]:
    kickoff = _event_kickoff_map(frame)
    ordered_events = sorted(kickoff, key=lambda event_id: (kickoff[event_id], event_id))
    folds: list[dict[str, Any]] = []
    for position, held_out in enumerate(ordered_events):
        earlier = ordered_events[:position]
        if len(earlier) < MIN_WALK_FORWARD_TRAIN_EVENTS:
            continue
        train = frame[frame["ticket_event_id"].isin(earlier)].copy()
        test = frame[frame["ticket_event_id"] == held_out].copy().sort_values("as_of_at")
        pred = fit_predict(train, test, profile, SEED + held_out * 307 + len(profile.name))
        metrics = _event_metrics(test, pred)
        metrics["training_event_count"] = len(earlier)
        metrics["kickoff_at"] = str(kickoff[held_out])
        folds.append(metrics)
    result = _aggregate(folds, profile.name)
    result["validation"] = (
        f"Chronological walk-forward; minimum {MIN_WALK_FORWARD_TRAIN_EVENTS} earlier events; test event never augmented"
    )
    return result


def _decision(loeo: list[dict[str, Any]], walk: list[dict[str, Any]]) -> dict[str, Any]:
    loeo_by_name = {row["profile"]: row for row in loeo}
    walk_by_name = {row["profile"]: row for row in walk}
    base_loeo = loeo_by_name["real_only"]
    base_walk = walk_by_name["real_only"]
    comparisons = []
    for profile in ("conservative_synthetic", "stress_synthetic"):
        loeo_row = loeo_by_name[profile]
        walk_row = walk_by_name[profile]
        comparisons.append({
            "profile": profile,
            "loeo_window_delta_vs_real": base_loeo["model_window_mae"] - loeo_row["model_window_mae"],
            "loeo_latest_delta_vs_real": base_loeo["model_latest_mae"] - loeo_row["model_latest_mae"],
            "walk_window_delta_vs_real": base_walk["model_window_mae"] - walk_row["model_window_mae"],
            "walk_latest_delta_vs_real": base_walk["model_latest_mae"] - walk_row["model_latest_mae"],
            "beats_real_loeo_window": loeo_row["model_window_mae"] < base_loeo["model_window_mae"],
            "beats_real_loeo_latest": loeo_row["model_latest_mae"] < base_loeo["model_latest_mae"],
            "beats_real_walk_window": walk_row["model_window_mae"] < base_walk["model_window_mae"],
            "beats_real_walk_latest": walk_row["model_latest_mae"] < base_walk["model_latest_mae"],
        })
    conservative = next(row for row in comparisons if row["profile"] == "conservative_synthetic")
    robust_signal = all(
        conservative[key]
        for key in (
            "beats_real_loeo_window",
            "beats_real_loeo_latest",
            "beats_real_walk_window",
            "beats_real_walk_latest",
        )
    )
    return {
        "comparison": comparisons,
        "conservative_augmentation_signal": "PROMISING_FOR_FURTHER_VALIDATION" if robust_signal else "NOT_PROVEN",
        "promotion_allowed": False,
        "reason": (
            "Synthetic augmentation is train-only regularisation. It may become a challenger only if it improves real held-out events; prospective validation is still required."
        ),
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
    frame = frame[
        (frame["hours_to_kickoff"].astype(float) >= 0.0)
        & (frame["hours_to_kickoff"].astype(float) <= WINDOW_HOURS)
        & (frame["prior_horizon"] == "T-1")
    ].copy()
    frame["as_of_at"] = pd.to_datetime(frame["as_of_at"], utc=True)
    if frame["ticket_event_id"].nunique() < 6:
        raise RuntimeError("Synthetic validation requires at least 6 independent completed events")

    loeo = [evaluate_loeo(frame, profile) for profile in PROFILES]
    walk = [evaluate_walk_forward(frame, profile) for profile in PROFILES]
    if any(row["event_count"] == 0 for row in walk):
        raise RuntimeError("Chronological walk-forward produced no evaluation folds")

    report = {
        "experiment": "c1-synthetic-trajectory-validation-v1",
        "model": MODEL_NAME,
        "dataset_version": payload.get("version"),
        "event_count": int(frame["ticket_event_id"].nunique()),
        "real_row_count": int(len(frame)),
        "profiles": [asdict(profile) for profile in PROFILES],
        "synthetic_contract": {
            "test_rows_are_always_real": True,
            "synthetic_rows_train_only": True,
            "real_outcome_preserved_for_training_event": True,
            "synthetic_outcomes_generated": False,
            "synthetic_rows_count_as_new_independent_events": False,
            "purpose": "regularisation / robustness to plausible trajectory observation variation",
        },
        "loeo": loeo,
        "chronological_walk_forward": walk,
        "decision": _decision(loeo, walk),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({
        "experiment": report["experiment"],
        "event_count": report["event_count"],
        "real_row_count": report["real_row_count"],
        "loeo": [{
            "profile": row["profile"],
            "model_window_mae": row["model_window_mae"],
            "model_latest_mae": row["model_latest_mae"],
            "prior_window_mae": row["prior_window_mae"],
            "prior_latest_mae": row["prior_latest_mae"],
            "worst_event_degradation": row["worst_event_degradation"],
        } for row in loeo],
        "walk_forward": [{
            "profile": row["profile"],
            "event_count": row["event_count"],
            "model_window_mae": row["model_window_mae"],
            "model_latest_mae": row["model_latest_mae"],
            "prior_window_mae": row["prior_window_mae"],
            "prior_latest_mae": row["prior_latest_mae"],
        } for row in walk],
        "decision": report["decision"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
