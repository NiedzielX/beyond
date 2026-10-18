#!/usr/bin/env python3
"""Chronological validation of the fixed C1 v8 Prior-vs-Live policy.

This experiment answers a narrower question than the synthetic augmentation run:
raw Live can generalise poorly in chronological walk-forward, but does the already
frozen v8 policy protect the final prediction by falling back to Structural Prior?

Policy thresholds are imported unchanged from c1_alpha_reliability_policy_v8.
No selector or threshold is fitted in this script.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay, _training_frame
from ml.c1_alpha_reliability_policy_v8 import POLICY_ID, event_policy_rows
from ml.c1_alpha_t1_tournament_v2 import WINDOW_HOURS
from ml.c1_synthetic_trajectory_validation_v1 import (
    MIN_WALK_FORWARD_TRAIN_EVENTS,
    PROFILES,
    SEED,
    _event_kickoff_map,
    fit_predict,
)

EXPERIMENT = "c1-walk-forward-policy-validation-v1"


def _latest_row(rows: pd.DataFrame) -> dict[str, Any]:
    row = rows.sort_values("as_of_at").iloc[-1]
    return {
        "hours_to_kickoff": float(row["hours_to_kickoff"]),
        "prior_p50": float(row["prior_p50"]),
        "live_p50": float(row["live_p50"]),
        "policy_prediction": float(row["policy_prediction"]),
        "prior_error": float(row["prior_error"]),
        "live_error": float(row["live_error"]),
        "policy_error": float(row["policy_error"]),
        "selected_expert": str(row["selected_expert"]),
        "reason_code": str(row["reason_code"]),
        "abs_disagreement_occupancy": float(row["abs_disagreement_occupancy"]),
        "live_observation_count_to_date": int(row["live_observation_count_to_date"]),
        "live_slope_occupancy_per_hour_to_date": (
            None
            if pd.isna(row["live_slope_occupancy_per_hour_to_date"])
            else float(row["live_slope_occupancy_per_hour_to_date"])
        ),
    }


def evaluate_profile(frame: pd.DataFrame, profile: Any) -> dict[str, Any]:
    kickoff = _event_kickoff_map(frame)
    ordered_events = sorted(kickoff, key=lambda event_id: (kickoff[event_id], event_id))
    folds: list[dict[str, Any]] = []

    for position, held_out in enumerate(ordered_events):
        earlier = ordered_events[:position]
        if len(earlier) < MIN_WALK_FORWARD_TRAIN_EVENTS:
            continue

        train = (
            frame[frame["ticket_event_id"].isin(earlier)]
            .copy()
            .reset_index(drop=True)
        )
        test = (
            frame[frame["ticket_event_id"] == held_out]
            .copy()
            .sort_values("as_of_at")
            .reset_index(drop=True)
        )

        live = fit_predict(
            train,
            test,
            profile,
            SEED + int(held_out) * 911 + len(profile.name),
        )
        policy_rows, event = event_policy_rows(test, live)
        latest = _latest_row(policy_rows)

        folds.append({
            "ticket_event_id": int(held_out),
            "home_team": str(event["home_team"]),
            "away_team": str(event["away_team"]),
            "kickoff_at": str(kickoff[held_out]),
            "training_event_count": len(earlier),
            "training_event_ids": [int(value) for value in earlier],
            "row_count": int(event["row_count"]),
            "prior_mae": float(event["prior_mae"]),
            "live_mae": float(event["live_mae"]),
            "policy_mae": float(event["policy_mae"]),
            "policy_delta_vs_prior": float(event["policy_mae"] - event["prior_mae"]),
            "policy_delta_vs_live": float(event["policy_mae"] - event["live_mae"]),
            "live_selected_rows": int(event["live_selected_rows"]),
            "prior_selected_rows": int(event["prior_selected_rows"]),
            "first_selected_expert": str(event["first_selected_expert"]),
            "latest_selected_expert": str(event["latest_selected_expert"]),
            "latest": latest,
        })

    if not folds:
        raise RuntimeError("Chronological policy validation produced no folds")

    prior_mae = float(np.mean([fold["prior_mae"] for fold in folds]))
    live_mae = float(np.mean([fold["live_mae"] for fold in folds]))
    policy_mae = float(np.mean([fold["policy_mae"] for fold in folds]))
    latest_prior_mae = float(np.mean([fold["latest"]["prior_error"] for fold in folds]))
    latest_live_mae = float(np.mean([fold["latest"]["live_error"] for fold in folds]))
    latest_policy_mae = float(np.mean([fold["latest"]["policy_error"] for fold in folds]))
    total_rows = int(sum(fold["row_count"] for fold in folds))
    live_selected_rows = int(sum(fold["live_selected_rows"] for fold in folds))

    return {
        "profile": profile.name,
        "event_count": len(folds),
        "row_count": total_rows,
        "prior_mae": prior_mae,
        "live_mae": live_mae,
        "policy_mae": policy_mae,
        "policy_absolute_uplift_vs_prior": prior_mae - policy_mae,
        "policy_absolute_uplift_vs_live": live_mae - policy_mae,
        "latest_prior_mae": latest_prior_mae,
        "latest_live_mae": latest_live_mae,
        "latest_policy_mae": latest_policy_mae,
        "latest_policy_absolute_uplift_vs_prior": latest_prior_mae - latest_policy_mae,
        "latest_policy_absolute_uplift_vs_live": latest_live_mae - latest_policy_mae,
        "live_selection_row_rate": live_selected_rows / total_rows if total_rows else 0.0,
        "live_selected_rows": live_selected_rows,
        "prior_selected_rows": total_rows - live_selected_rows,
        "event_improvement_rate_vs_prior": float(
            np.mean([fold["policy_mae"] < fold["prior_mae"] for fold in folds])
        ),
        "worst_event_policy_degradation_vs_prior": float(
            max(fold["policy_delta_vs_prior"] for fold in folds)
        ),
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
    frame = frame[
        (frame["hours_to_kickoff"].astype(float) >= 0.0)
        & (frame["hours_to_kickoff"].astype(float) <= WINDOW_HOURS)
        & (frame["prior_horizon"] == "T-1")
    ].copy().reset_index(drop=True)
    frame["as_of_at"] = pd.to_datetime(frame["as_of_at"], utc=True)

    results = [evaluate_profile(frame, profile) for profile in PROFILES]
    real_only = next(row for row in results if row["profile"] == "real_only")

    report = {
        "experiment": EXPERIMENT,
        "policy_id": POLICY_ID,
        "dataset_version": payload.get("version"),
        "independent_event_count_available": int(frame["ticket_event_id"].nunique()),
        "real_row_count": int(len(frame)),
        "walk_forward_min_training_events": MIN_WALK_FORWARD_TRAIN_EVENTS,
        "governance": {
            "policy_thresholds_refit": False,
            "policy_thresholds_changed": False,
            "test_events_real_only": True,
            "future_events_used_for_training": False,
            "production_activation": False,
            "frozen_v8_package_changed": False,
        },
        "profiles": results,
        "decision": {
            "real_only_policy_beats_raw_live": real_only["policy_mae"] < real_only["live_mae"],
            "real_only_policy_beats_prior": real_only["policy_mae"] < real_only["prior_mae"],
            "real_only_policy_safe_vs_prior": real_only["policy_mae"] <= real_only["prior_mae"],
            "promotion_allowed": False,
            "reason": (
                "This is retrospective chronological validation of the already-fixed v8 policy. "
                "It can diagnose protection against a weak live expert but cannot replace prospective evidence."
            ),
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")

    print(json.dumps({
        "experiment": report["experiment"],
        "policy_id": report["policy_id"],
        "profiles": [{
            "profile": row["profile"],
            "event_count": row["event_count"],
            "prior_mae": row["prior_mae"],
            "live_mae": row["live_mae"],
            "policy_mae": row["policy_mae"],
            "latest_prior_mae": row["latest_prior_mae"],
            "latest_live_mae": row["latest_live_mae"],
            "latest_policy_mae": row["latest_policy_mae"],
            "live_selection_row_rate": row["live_selection_row_rate"],
            "worst_event_policy_degradation_vs_prior": row["worst_event_policy_degradation_vs_prior"],
            "folds": row["folds"],
        } for row in results],
        "decision": report["decision"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
