#!/usr/bin/env python3
"""Beyond live benchmark harness v0.3.

Key protocol correction versus v0.2:
- headline: one latest forecast per event/model version;
- horizon benchmark: exactly ONE forecast per event/model/horizon;
- forecast must be available no later than the target horizon, i.e.
  hours_to_kickoff >= target hours;
- among eligible rows choose the closest observation to the target;
- observations generated after the target horizon are never used as fallback.

This prevents high-frequency events from receiving extra weight and avoids using
information that would not have been available at T-30/T-14/T-7/T-3/T-24h.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

HORIZONS = {
    "T-30": (720.0, 240.0),
    "T-14": (336.0, 96.0),
    "T-7": (168.0, 48.0),
    "T-3": (72.0, 24.0),
    "T-24h": (24.0, 12.0),
}


def pinball(actual: float, predicted: float, quantile: float) -> float:
    error = actual - predicted
    return max(quantile * error, (quantile - 1.0) * error)


def metric_set(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"n": 0, "status": "awaiting_outcomes"}

    actual = frame["actual_attendance"].astype(float)
    p50 = frame["final_p50"].astype(float)
    absolute = (p50 - actual).abs()
    percentage = absolute / actual * 100.0

    result = {
        "n": int(len(frame)),
        "independent_matches": int(frame["ticket_event_id"].nunique()),
        "status": "evaluated",
        "mae": round(float(absolute.mean()), 2),
        "mape_pct": round(float(percentage.mean()), 2),
        "wape_pct": round(float(absolute.sum() / actual.sum() * 100.0), 2),
        "bias": round(float((p50 - actual).mean()), 2),
        "within_5_pct": round(float((percentage <= 5.0).mean() * 100.0), 2),
        "within_10_pct": round(float((percentage <= 10.0).mean() * 100.0), 2),
    }

    probabilistic = frame.dropna(
        subset=["final_p10", "final_p50", "final_p90", "actual_attendance"]
    )
    if not probabilistic.empty:
        coverage = (
            (probabilistic["actual_attendance"] >= probabilistic["final_p10"])
            & (probabilistic["actual_attendance"] <= probabilistic["final_p90"])
        )
        p10_loss = [
            pinball(a, p, 0.10)
            for a, p in zip(probabilistic["actual_attendance"], probabilistic["final_p10"])
        ]
        p50_loss = [
            pinball(a, p, 0.50)
            for a, p in zip(probabilistic["actual_attendance"], probabilistic["final_p50"])
        ]
        p90_loss = [
            pinball(a, p, 0.90)
            for a, p in zip(probabilistic["actual_attendance"], probabilistic["final_p90"])
        ]
        result.update(
            {
                "probabilistic_n": int(len(probabilistic)),
                "interval_coverage_pct": round(float(coverage.mean() * 100.0), 2),
                "pinball_p10": round(float(sum(p10_loss) / len(p10_loss)), 2),
                "pinball_p50": round(float(sum(p50_loss) / len(p50_loss)), 2),
                "pinball_p90": round(float(sum(p90_loss) / len(p90_loss)), 2),
                "pinball_mean": round(
                    float(
                        (sum(p10_loss) + sum(p50_loss) + sum(p90_loss))
                        / (3 * len(p10_loss))
                    ),
                    2,
                ),
            }
        )

    return result


def select_horizon_rows(version: pd.DataFrame, horizon: str) -> pd.DataFrame:
    """Select one strict as-of row per event for a canonical horizon."""
    target, tolerance = HORIZONS[horizon]
    eligible = version[
        version["hours_to_kickoff"].notna()
        & (version["hours_to_kickoff"] >= target)
        & (version["hours_to_kickoff"] <= target + tolerance)
    ].copy()
    if eligible.empty:
        return eligible

    eligible["horizon_distance_hours"] = eligible["hours_to_kickoff"] - target
    return (
        eligible.sort_values(
            [
                "ticket_event_id",
                "horizon_distance_hours",
                "forecast_generated_at",
                "id",
            ],
            ascending=[True, True, False, False],
        )
        .groupby("ticket_event_id", as_index=False)
        .head(1)
        .copy()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forecasts", required=True, type=Path)
    parser.add_argument("--outcomes", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    forecasts = pd.read_csv(args.forecasts)
    outcomes = pd.read_csv(args.outcomes)

    forecasts = forecasts[forecasts["final_p50"].notna()].copy()
    merged = forecasts.merge(
        outcomes[["ticket_event_id", "actual_attendance"]],
        on="ticket_event_id",
        how="left",
    )
    merged["forecast_generated_at"] = pd.to_datetime(
        merged["forecast_generated_at"], utc=True
    )
    merged["hours_to_kickoff"] = pd.to_numeric(
        merged["hours_to_kickoff"], errors="coerce"
    )

    model_versions = sorted(v for v in merged["model_version"].dropna().unique())
    result = {
        "benchmark_version": "0.3",
        "headline_method": "latest_forecast_per_event_and_model_version",
        "horizon_method": "one_closest_pre_target_forecast_per_event_model_horizon",
        "no_post_target_fallback": True,
        "horizon_windows_hours": {
            name: {
                "target": target,
                "eligible_min_hours_to_kickoff": target,
                "eligible_max_hours_to_kickoff": target + tolerance,
            }
            for name, (target, tolerance) in HORIZONS.items()
        },
        "models": {},
    }

    for model_version in model_versions:
        version = merged[merged["model_version"] == model_version].copy()
        latest = (
            version.sort_values(["ticket_event_id", "forecast_generated_at", "id"])
            .groupby("ticket_event_id", as_index=False)
            .tail(1)
        )
        latest_evaluable = latest.dropna(subset=["actual_attendance"])

        horizons = {}
        for horizon in HORIZONS:
            selected = select_horizon_rows(version, horizon)
            evaluable = selected.dropna(subset=["actual_attendance"])
            target = HORIZONS[horizon][0]
            horizon_report = metric_set(evaluable)
            horizon_report.update(
                {
                    "selected_forecasts": int(len(selected)),
                    "selected_events": int(selected["ticket_event_id"].nunique()),
                    "eligible_completed_events": int(
                        evaluable["ticket_event_id"].nunique()
                    ),
                    "mean_hours_before_target": (
                        round(float((evaluable["hours_to_kickoff"] - target).mean()), 2)
                        if not evaluable.empty
                        else None
                    ),
                }
            )
            horizons[horizon] = horizon_report

        result["models"][model_version] = {
            "forecast_events": int(version["ticket_event_id"].nunique()),
            "forecast_observations": int(len(version)),
            "headline": metric_set(latest_evaluable),
            "horizons": horizons,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
