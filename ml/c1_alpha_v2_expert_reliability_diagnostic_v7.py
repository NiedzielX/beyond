#!/usr/bin/env python3
"""C1-alpha v7: event-level reliability diagnostic for the v2 expert pair.

This is deliberately NOT another model tournament.

For each outer LOEO event it recreates the frozen v2 live expert from the
remaining events, predicts the full final-24h trajectory, and summarizes one
PIT feature profile for the held-out event. Actual attendance / oracle winner
are stored only as evaluation labels.
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


DIAGNOSTIC_NUMERIC = [
    "prior_expected_occupancy",
    "round_no",
    "season_home_evidence_n",
    "earliest_hours_to_kickoff",
    "latest_hours_to_kickoff",
    "live_earliest_occupancy",
    "live_latest_occupancy",
    "earliest_signed_disagreement_occ",
    "latest_signed_disagreement_occ",
    "earliest_abs_disagreement_occ",
    "latest_abs_disagreement_occ",
    "live_prediction_range_pct_capacity",
    "live_prediction_std_pct_capacity",
    "live_prediction_slope_pct_capacity_per_hour",
    "live_row_count",
    "live_elapsed_hours",
    "earliest_available_share_of_capacity",
    "latest_available_share_of_capacity",
    "earliest_available_index",
    "latest_available_index",
    "earliest_velocity_6h_pct_capacity_per_hour",
    "latest_velocity_6h_pct_capacity_per_hour",
    "earliest_velocity_24h_pct_capacity_per_hour",
    "latest_velocity_24h_pct_capacity_per_hour",
    "earliest_observation_window_hours",
    "latest_observation_window_hours",
    "earliest_raw_snapshot_count",
    "latest_raw_snapshot_count",
    "earliest_clean_snapshot_count",
    "latest_clean_snapshot_count",
    "latest_matched_sector_count",
    "release_row_share",
    "coverage_change_row_share",
    "data_gap_row_share",
    "signal_ready_row_share",
    "feature_quality_good_row_share",
    "hybrid_v6",
    "hybrid_missing",
]


def num(value: Any) -> float:
    return float(pd.to_numeric(value, errors="coerce")) if pd.notna(pd.to_numeric(value, errors="coerce")) else float("nan")


def bshare(series: pd.Series) -> float:
    vals = pd.to_numeric(series, errors="coerce")
    return float(vals.mean()) if vals.notna().any() else float("nan")


def linear_slope(values: np.ndarray, elapsed_hours: np.ndarray) -> float:
    if len(values) < 2 or np.ptp(elapsed_hours) <= 1e-9:
        return 0.0
    return float(np.polyfit(elapsed_hours, values, 1)[0])


def enrich_hybrid(frame: pd.DataFrame, payload: dict) -> pd.DataFrame:
    out = frame.copy()
    hybrid = {
        int(row["ticket_event_id"]): row
        for row in payload.get("ticketingChallengerRows") or []
    }
    vals, sources = [], []
    for event_id in out["ticket_event_id"].astype(int):
        row = hybrid.get(event_id)
        vals.append(np.nan if row is None else pd.to_numeric(row.get("hybrid_v6"), errors="coerce"))
        sources.append("missing" if row is None else str(row.get("hybrid_v6_source") or "missing"))
    out["hybrid_v6"] = vals
    out["hybrid_missing"] = out["hybrid_v6"].isna().astype(float)
    out["hybrid_v6_source"] = sources
    return out


def event_profile(test: pd.DataFrame, live: np.ndarray) -> dict[str, Any]:
    test = test.sort_values("as_of_at").copy()
    live = np.asarray(live, dtype=float)
    capacity = float(test["stadium_capacity"].iloc[0])
    actual = float(test["actual_attendance"].iloc[0])
    prior = float(test["prior_p50"].iloc[0])

    as_of = pd.to_datetime(test["as_of_at"], utc=True)
    elapsed = (as_of - as_of.iloc[0]).dt.total_seconds().to_numpy() / 3600.0
    live_occ = live / capacity
    prior_occ = prior / capacity

    prior_errors = np.abs(prior - actual) * np.ones(len(test))
    live_errors = np.abs(live - actual)
    prior_window_mae = float(np.mean(prior_errors))
    live_window_mae = float(np.mean(live_errors))

    earliest = test.iloc[0]
    latest = test.iloc[-1]

    def row_bool(name: str) -> pd.Series:
        if name not in test.columns:
            return pd.Series([np.nan] * len(test), index=test.index)
        return pd.to_numeric(test[name], errors="coerce")

    profile = {
        "ticket_event_id": int(test["ticket_event_id"].iloc[0]),
        "club_slug": str(test["club_slug"].iloc[0]),
        "home_team": str(test["home_team"].iloc[0]),
        "away_team": str(test["away_team"].iloc[0]),
        "prior_p50": prior,
        "prior_expected_occupancy": prior_occ,
        "round_no": num(earliest.get("round_no")),
        "season_home_evidence_n": num(earliest.get("season_home_evidence_n")),
        "earliest_hours_to_kickoff": num(earliest.get("hours_to_kickoff")),
        "latest_hours_to_kickoff": num(latest.get("hours_to_kickoff")),
        "live_earliest_p50": float(live[0]),
        "live_latest_p50": float(live[-1]),
        "live_earliest_occupancy": float(live_occ[0]),
        "live_latest_occupancy": float(live_occ[-1]),
        "earliest_signed_disagreement_occ": float(live_occ[0] - prior_occ),
        "latest_signed_disagreement_occ": float(live_occ[-1] - prior_occ),
        "earliest_abs_disagreement_occ": float(abs(live_occ[0] - prior_occ)),
        "latest_abs_disagreement_occ": float(abs(live_occ[-1] - prior_occ)),
        "live_prediction_range_pct_capacity": float(np.ptp(live) / capacity),
        "live_prediction_std_pct_capacity": float(np.std(live) / capacity),
        "live_prediction_slope_pct_capacity_per_hour": float(linear_slope(live, elapsed) / capacity),
        "live_row_count": int(len(test)),
        "live_elapsed_hours": float(elapsed[-1] if len(elapsed) else 0.0),
        "earliest_available_share_of_capacity": num(earliest.get("available_share_of_capacity")),
        "latest_available_share_of_capacity": num(latest.get("available_share_of_capacity")),
        "earliest_available_index": num(earliest.get("available_index")),
        "latest_available_index": num(latest.get("available_index")),
        "earliest_velocity_6h_pct_capacity_per_hour": num(earliest.get("velocity_6h_pct_of_capacity_per_hour")),
        "latest_velocity_6h_pct_capacity_per_hour": num(latest.get("velocity_6h_pct_of_capacity_per_hour")),
        "earliest_velocity_24h_pct_capacity_per_hour": num(earliest.get("velocity_24h_pct_of_capacity_per_hour")),
        "latest_velocity_24h_pct_capacity_per_hour": num(latest.get("velocity_24h_pct_of_capacity_per_hour")),
        "earliest_observation_window_hours": num(earliest.get("observation_window_hours")),
        "latest_observation_window_hours": num(latest.get("observation_window_hours")),
        "earliest_raw_snapshot_count": num(earliest.get("raw_snapshot_count")),
        "latest_raw_snapshot_count": num(latest.get("raw_snapshot_count")),
        "earliest_clean_snapshot_count": num(earliest.get("clean_snapshot_count")),
        "latest_clean_snapshot_count": num(latest.get("clean_snapshot_count")),
        "latest_matched_sector_count": num(latest.get("matched_sector_count")),
        "release_row_share": bshare(row_bool("release_activity_flag")),
        "coverage_change_row_share": bshare(row_bool("sector_coverage_change_flag")),
        "data_gap_row_share": bshare(row_bool("data_gap_detected")),
        "signal_ready_row_share": bshare(test["signal_ready"]) if "signal_ready" in test else float("nan"),
        "feature_quality_good_row_share": bshare(test["feature_quality_good"]) if "feature_quality_good" in test else float("nan"),
        "hybrid_v6": num(earliest.get("hybrid_v6")),
        "hybrid_missing": num(earliest.get("hybrid_missing")),
        "hybrid_v6_source": str(earliest.get("hybrid_v6_source", "missing")),
        # Evaluation labels below. Never use them as model/policy predictors.
        "actual_attendance": actual,
        "prior_error": float(abs(prior - actual)),
        "live_window_mae": live_window_mae,
        "live_latest_error": float(live_errors[-1]),
        "oracle_expert_window": "LIVE" if live_window_mae < prior_window_mae else "PRIOR",
        "oracle_uplift_if_live": float(prior_window_mae - live_window_mae),
    }
    return profile


def feature_contrasts(events: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for feature in DIAGNOSTIC_NUMERIC:
        if feature not in events.columns:
            continue
        prior = pd.to_numeric(events.loc[events.oracle_expert_window == "PRIOR", feature], errors="coerce").dropna()
        live = pd.to_numeric(events.loc[events.oracle_expert_window == "LIVE", feature], errors="coerce").dropna()
        if prior.empty or live.empty:
            continue
        combined = pd.concat([prior, live])
        scale = float(combined.std(ddof=0))
        rows.append({
            "feature": feature,
            "prior_winner_median": float(prior.median()),
            "live_winner_median": float(live.median()),
            "median_difference_live_minus_prior": float(live.median() - prior.median()),
            "standardized_median_gap": 0.0 if scale <= 1e-12 else float((live.median() - prior.median()) / scale),
            "prior_n": int(len(prior)),
            "live_n": int(len(live)),
        })
    rows.sort(key=lambda row: abs(row["standardized_median_gap"]), reverse=True)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    priors = _event_prior_replay(payload, args.artifact_dir)
    frame = add_event_context(_training_frame(payload, priors), payload)
    frame = enrich_hybrid(frame, payload)
    frame = frame[
        (frame["hours_to_kickoff"].astype(float) >= 0.0)
        & (frame["hours_to_kickoff"].astype(float) <= WINDOW_HOURS)
        & (frame["prior_horizon"] == "T-1")
    ].copy()

    event_ids = sorted(int(v) for v in frame["ticket_event_id"].unique())
    profiles: list[dict[str, Any]] = []
    for held_out in event_ids:
        train = frame[frame["ticket_event_id"] != held_out].copy()
        test = frame[frame["ticket_event_id"] == held_out].copy().sort_values("as_of_at")
        live = fit_base_live(train, test)
        profiles.append(event_profile(test, live))

    events = pd.DataFrame(profiles).sort_values("ticket_event_id").reset_index(drop=True)
    prior_mae = float(events["prior_error"].mean())
    live_mae = float(events["live_window_mae"].mean())
    oracle_mae = float(np.mean(np.minimum(events["prior_error"], events["live_window_mae"])))

    # Guard that this is genuinely reproducing the already-published v2 result,
    # not silently creating a different expert.
    if abs(live_mae - 2929.3) > 5.0:
        raise RuntimeError(f"v7 failed to reproduce v2 live MAE: {live_mae:.3f}")
    if abs(prior_mae - 3968.7) > 5.0:
        raise RuntimeError(f"v7 failed to reproduce T-1 prior MAE: {prior_mae:.3f}")

    winner_counts = events["oracle_expert_window"].value_counts().to_dict()
    report = {
        "experiment": "c1-alpha-v2-expert-reliability-diagnostic-v7",
        "dataset_version": payload.get("version"),
        "unit": "one held-out event profile derived from v2 outer-LOEO predictions",
        "event_count": int(len(events)),
        "v2_reproduction": {
            "prior_mae": prior_mae,
            "live_mae": live_mae,
            "absolute_uplift": prior_mae - live_mae,
            "relative_improvement": (prior_mae - live_mae) / prior_mae,
            "oracle_prior_or_live_mae": oracle_mae,
            "oracle_winner_counts": winner_counts,
        },
        "label_semantics": {
            "oracle_expert_window": "evaluation only; LIVE iff held-out v2 window MAE < Structural Prior error",
            "outcome_features_allowed": False,
        },
        "events": events.to_dict(orient="records"),
        "feature_contrasts_diagnostic_only": feature_contrasts(events),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")

    print(json.dumps({
        "experiment": report["experiment"],
        "event_count": report["event_count"],
        "v2_reproduction": report["v2_reproduction"],
        "events": [
            {k: row[k] for k in (
                "ticket_event_id", "home_team", "away_team", "prior_error",
                "live_window_mae", "oracle_expert_window", "round_no",
                "season_home_evidence_n", "earliest_abs_disagreement_occ",
                "latest_abs_disagreement_occ", "live_prediction_range_pct_capacity",
                "live_prediction_std_pct_capacity", "live_row_count",
                "latest_observation_window_hours", "hybrid_v6_source"
            )}
            for row in report["events"]
        ],
        "top_feature_contrasts_diagnostic_only": report["feature_contrasts_diagnostic_only"][:12],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
