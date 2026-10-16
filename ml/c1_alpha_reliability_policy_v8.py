#!/usr/bin/env python3
"""C1-alpha v8: fixed PIT-safe reliability policy for Structural Prior vs v2 live expert.

This is NOT a model tournament and does not fit a selector.

Policy was predeclared after v7 diagnostic:
- with one live observation: use LIVE only if abs(prior-live disagreement) >= 20 pp capacity;
- with >=2 observations: use LIVE only if current disagreement >= 10 pp capacity
  AND the live prediction slope using observations available up to the current PIT row is > 0;
- otherwise use PRIOR.

The v2 live expert itself is still trained under outer Leave-One-Event-Out.
The hard-switch policy consumes only PIT-observable predictions/features from the
held-out event. Actual attendance is used only for evaluation after decisions are made.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay, _training_frame
from ml.c1_alpha_t1_stacked_v4 import add_event_context, fit_base_live
from ml.c1_alpha_t1_tournament_v2 import WINDOW_HOURS


MULTI_OBS_DISAGREEMENT_THRESHOLD = 0.10
SINGLE_OBS_DISAGREEMENT_THRESHOLD = 0.20
POLICY_ID = "c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single"


def linear_slope(values: np.ndarray, elapsed_hours: np.ndarray) -> float:
    if len(values) < 2 or np.ptp(elapsed_hours) <= 1e-9:
        return float("nan")
    return float(np.polyfit(elapsed_hours, values, 1)[0])


def event_policy_rows(test: pd.DataFrame, live: np.ndarray) -> tuple[pd.DataFrame, dict[str, Any]]:
    test = test.sort_values("as_of_at").copy().reset_index(drop=True)
    live = np.asarray(live, dtype=float)
    if len(test) != len(live):
        raise RuntimeError("v8 test/live length mismatch")

    capacity = float(test["stadium_capacity"].iloc[0])
    prior = float(test["prior_p50"].iloc[0])
    actual = float(test["actual_attendance"].iloc[0])
    prior_occ = prior / capacity
    as_of = pd.to_datetime(test["as_of_at"], utc=True)
    elapsed = (as_of - as_of.iloc[0]).dt.total_seconds().to_numpy() / 3600.0

    records: list[dict[str, Any]] = []
    for i, row in test.iterrows():
        prefix_live = live[: i + 1]
        prefix_elapsed = elapsed[: i + 1]
        live_now = float(live[i])
        live_occ_now = live_now / capacity
        disagreement = abs(live_occ_now - prior_occ)
        slope_occ_per_hour = linear_slope(prefix_live / capacity, prefix_elapsed)
        observation_count = i + 1

        if observation_count == 1:
            use_live = disagreement >= SINGLE_OBS_DISAGREEMENT_THRESHOLD
            reason = (
                "single_obs_material_disagreement"
                if use_live
                else "single_obs_insufficient_disagreement"
            )
        else:
            use_live = (
                disagreement >= MULTI_OBS_DISAGREEMENT_THRESHOLD
                and np.isfinite(slope_occ_per_hour)
                and slope_occ_per_hour > 0.0
            )
            if use_live:
                reason = "material_disagreement_positive_live_slope"
            elif disagreement < MULTI_OBS_DISAGREEMENT_THRESHOLD:
                reason = "insufficient_disagreement"
            else:
                reason = "live_slope_not_positive"

        prediction = live_now if use_live else prior
        records.append({
            "ticket_event_id": int(row["ticket_event_id"]),
            "club_slug": str(row["club_slug"]),
            "home_team": str(row["home_team"]),
            "away_team": str(row["away_team"]),
            "as_of_at": str(row["as_of_at"]),
            "hours_to_kickoff": float(row["hours_to_kickoff"]),
            "stadium_capacity": capacity,
            "prior_p50": prior,
            "live_p50": live_now,
            "actual_attendance": actual,
            "prior_expected_occupancy": prior_occ,
            "live_expected_occupancy": live_occ_now,
            "abs_disagreement_occupancy": disagreement,
            "live_observation_count_to_date": observation_count,
            "live_slope_occupancy_per_hour_to_date": None if not np.isfinite(slope_occ_per_hour) else float(slope_occ_per_hour),
            "selected_expert": "LIVE" if use_live else "PRIOR",
            "reason_code": reason,
            "policy_prediction": prediction,
            "prior_error": abs(prior - actual),
            "live_error": abs(live_now - actual),
            "policy_error": abs(prediction - actual),
        })

    rows = pd.DataFrame(records)
    prior_event_mae = float(rows["prior_error"].mean())
    live_event_mae = float(rows["live_error"].mean())
    policy_event_mae = float(rows["policy_error"].mean())
    event = {
        "ticket_event_id": int(rows["ticket_event_id"].iloc[0]),
        "club_slug": str(rows["club_slug"].iloc[0]),
        "home_team": str(rows["home_team"].iloc[0]),
        "away_team": str(rows["away_team"].iloc[0]),
        "row_count": int(len(rows)),
        "prior_mae": prior_event_mae,
        "live_mae": live_event_mae,
        "policy_mae": policy_event_mae,
        "oracle_prior_or_live_mae": min(prior_event_mae, live_event_mae),
        "policy_improves_prior": bool(policy_event_mae < prior_event_mae),
        "live_selected_rows": int((rows["selected_expert"] == "LIVE").sum()),
        "prior_selected_rows": int((rows["selected_expert"] == "PRIOR").sum()),
        "first_selected_expert": str(rows["selected_expert"].iloc[0]),
        "latest_selected_expert": str(rows["selected_expert"].iloc[-1]),
    }
    return rows, event


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

    event_ids = sorted(int(v) for v in frame["ticket_event_id"].unique())
    row_blocks: list[pd.DataFrame] = []
    event_results: list[dict[str, Any]] = []

    for held_out in event_ids:
        train = frame[frame["ticket_event_id"] != held_out].copy()
        test = (
            frame[frame["ticket_event_id"] == held_out]
            .copy()
            .sort_values("as_of_at")
        )
        live = fit_base_live(train, test)
        rows, event = event_policy_rows(test, live)
        row_blocks.append(rows)
        event_results.append(event)

    all_rows = pd.concat(row_blocks, ignore_index=True)
    events = pd.DataFrame(event_results).sort_values("ticket_event_id").reset_index(drop=True)

    prior_mae = float(events["prior_mae"].mean())
    live_mae = float(events["live_mae"].mean())
    policy_mae = float(events["policy_mae"].mean())
    oracle_mae = float(events["oracle_prior_or_live_mae"].mean())

    # Reproduce the already-published v2 pair before scoring the fixed v8 policy.
    if abs(prior_mae - 3968.7) > 5.0:
        raise RuntimeError(f"v8 failed to reproduce T-1 prior MAE: {prior_mae:.3f}")
    if abs(live_mae - 2929.3) > 5.0:
        raise RuntimeError(f"v8 failed to reproduce v2 live MAE: {live_mae:.3f}")
    if abs(oracle_mae - 1867.9) > 5.0:
        raise RuntimeError(f"v8 failed to reproduce v2 pair oracle MAE: {oracle_mae:.3f}")

    latest = (
        all_rows.sort_values("as_of_at")
        .groupby("ticket_event_id", as_index=False)
        .tail(1)
    )
    report = {
        "experiment": "c1-alpha-reliability-policy-v8",
        "policy_id": POLICY_ID,
        "dataset_version": payload.get("version"),
        "policy": {
            "multi_observation": {
                "abs_disagreement_occupancy_gte": MULTI_OBS_DISAGREEMENT_THRESHOLD,
                "live_slope_occupancy_per_hour_gt": 0.0,
            },
            "single_observation": {
                "abs_disagreement_occupancy_gte": SINGLE_OBS_DISAGREEMENT_THRESHOLD,
            },
            "fallback": "PRIOR",
            "pit_rule": "At each row use only live predictions observed up to that row; no future final-24h observations.",
            "selection_training": "none; fixed after v7 diagnostic",
        },
        "governance": {
            "development_evidence_only": True,
            "reason": "Policy thresholds were designed after inspecting v7 labels on these same 9 events.",
            "promotion_evidence": False,
            "production_activation": False,
        },
        "event_count": int(len(events)),
        "row_count": int(len(all_rows)),
        "metrics": {
            "prior_mae": prior_mae,
            "live_mae": live_mae,
            "policy_mae": policy_mae,
            "oracle_prior_or_live_mae": oracle_mae,
            "policy_absolute_uplift_vs_prior": prior_mae - policy_mae,
            "policy_relative_improvement_vs_prior": (prior_mae - policy_mae) / prior_mae,
            "policy_gap_to_oracle": policy_mae - oracle_mae,
            "event_improvement_rate_vs_prior": float(events["policy_improves_prior"].mean()),
            "live_selection_row_rate": float((all_rows["selected_expert"] == "LIVE").mean()),
            "live_selection_event_rate_latest": float((latest["selected_expert"] == "LIVE").mean()),
            "latest_row_mae": float(latest["policy_error"].mean()),
            "latest_prior_mae": float(latest["prior_error"].mean()),
            "latest_live_mae": float(latest["live_error"].mean()),
            "worst_event_degradation_vs_prior": float((events["policy_mae"] - events["prior_mae"]).max()),
        },
        "events": events.to_dict(orient="records"),
        "rows": all_rows.to_dict(orient="records"),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")

    print(json.dumps({
        "experiment": report["experiment"],
        "policy_id": report["policy_id"],
        "event_count": report["event_count"],
        "row_count": report["row_count"],
        "metrics": report["metrics"],
        "events": report["events"],
        "latest_decisions": [
            {k: row[k] for k in (
                "ticket_event_id", "home_team", "away_team", "hours_to_kickoff",
                "abs_disagreement_occupancy", "live_observation_count_to_date",
                "live_slope_occupancy_per_hour_to_date", "selected_expert",
                "reason_code", "prior_error", "live_error", "policy_error"
            )}
            for row in latest.to_dict(orient="records")
        ],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
