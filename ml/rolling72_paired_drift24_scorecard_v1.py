#!/usr/bin/env python3
"""Fixed, pure-stdlib scorecard for accepted shared PERS/drift24 labels.

Input rows are outcome facts only. This module does not read runtime status,
infer coverage, query a database, or create forecasts or labels.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any


HORIZONS = (24, 48, 72)
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 42
MIN_EVENTS = 30
MIN_CLUBS = 8
MIN_IMPROVEMENT = 0.10


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _identifier(value: Any, name: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{name} must be a non-empty string or positive integer")
    if isinstance(value, int):
        if value <= 0:
            raise ValueError(f"{name} must be a non-empty string or positive integer")
        return str(value)
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be a non-empty string or positive integer")
    return normalized


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite non-negative number")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return result


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return math.fsum(items) / len(items) if items else 0.0


def _linear_quantile(values: list[float], probability: float) -> float:
    """Linear interpolation at p*(n-1), for the fixed percentile bootstrap CI."""
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def _horizon_metrics(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    events: dict[int, list[dict[str, Any]]] = defaultdict(list)
    clubs: set[str] = set()
    for row in rows:
        events[row["ticket_event_id"]].append(row)
        clubs.add(row["club_id"])

    event_mae: dict[int, dict[str, float]] = {}
    for event_id, facts in events.items():
        event_mae[event_id] = {
            "pers": _mean(abs(row["pers_prediction"] - row["actual"]) for row in facts),
            "drift24": _mean(abs(row["drift24_prediction"] - row["actual"]) for row in facts),
            "pers_bias": _mean(row["pers_prediction"] - row["actual"] for row in facts),
            "drift24_bias": _mean(row["drift24_prediction"] - row["actual"] for row in facts),
        }

    event_ids = sorted(event_mae)
    pers_mae = [event_mae[event]["pers"] for event in event_ids]
    drift_mae = [event_mae[event]["drift24"] for event in event_ids]
    pers_bias = [event_mae[event]["pers_bias"] for event in event_ids]
    drift_bias = [event_mae[event]["drift24_bias"] for event in event_ids]
    delta = [event_mae[event]["drift24"] - event_mae[event]["pers"] for event in event_ids]
    worst_event_id = max(event_ids, key=lambda event: (event_mae[event]["drift24"], -event))
    return {
        "accepted_shared_labels": len(rows),
        "event_count": len(event_ids),
        "club_count": len(clubs),
        "pers": {
            "event_balanced_mae": _mean(pers_mae),
            "event_balanced_bias": _mean(pers_bias),
            "event_mae_p90": _linear_quantile(pers_mae, 0.90),
            "event_mae_p90_quantile_method": "linear",
            "worst_event_mae": max(pers_mae),
        },
        "drift24": {
            "event_balanced_mae": _mean(drift_mae),
            "event_balanced_bias": _mean(drift_bias),
            "event_mae_p90": _linear_quantile(drift_mae, 0.90),
            "event_mae_p90_quantile_method": "linear",
            "worst_event_mae": max(drift_mae),
            "worst_event_id": worst_event_id,
        },
        "delta_drift24_minus_pers": {
            "event_balanced_mae": _mean(delta),
            "event_mae_p90": _linear_quantile(delta, 0.90),
            "event_mae_p90_quantile_method": "linear",
            "worst_event_mae": max(delta),
        },
        "paired_event_deltas": [
            {"ticket_event_id": event, "delta_mae": event_mae[event]["drift24"] - event_mae[event]["pers"]}
            for event in event_ids
        ],
    }


def _bootstrap_ci(deltas: list[float]) -> dict[str, Any] | None:
    if not deltas:
        return None
    rng = random.Random(BOOTSTRAP_SEED)
    count = len(deltas)
    means = [
        math.fsum(deltas[rng.randrange(count)] for _ in range(count)) / count
        for _ in range(BOOTSTRAP_DRAWS)
    ]
    return {
        "method": "paired_event_percentile_bootstrap",
        "resampling_unit": "ticket_event_id",
        "draws": BOOTSTRAP_DRAWS,
        "seed": BOOTSTRAP_SEED,
        "confidence_level": 0.95,
        "lower": _linear_quantile(means, 0.025),
        "upper": _linear_quantile(means, 0.975),
    }


def analyze(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate accepted shared-label facts and calculate the fixed scorecard."""
    if isinstance(rows, (str, bytes, Mapping)):
        raise ValueError("rows must be an iterable of row objects")
    try:
        input_rows = list(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of row objects") from exc

    normalized: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    event_club: dict[int, str] = {}
    bundle_event: dict[int, int] = {}
    required = {"bundle_id", "ticket_event_id", "club_id", "horizon_hours", "actual", "pers_prediction", "drift24_prediction"}
    for index, row in enumerate(input_rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"rows[{index}] must be an object")
        missing = required - row.keys()
        if missing:
            raise ValueError(f"rows[{index}] missing fields: {', '.join(sorted(missing))}")
        bundle = _positive_int(row["bundle_id"], f"rows[{index}].bundle_id")
        event = _positive_int(row["ticket_event_id"], f"rows[{index}].ticket_event_id")
        club = _identifier(row["club_id"], f"rows[{index}].club_id")
        horizon = row["horizon_hours"]
        if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon not in HORIZONS:
            raise ValueError(f"rows[{index}].horizon_hours must be one of 24, 48, 72")
        key = (bundle, horizon)
        if key in seen:
            raise ValueError(f"duplicate bundle_id/horizon pair: {bundle}/{horizon}")
        seen.add(key)
        if event in event_club and event_club[event] != club:
            raise ValueError(f"ticket_event_id {event} maps to more than one club_id")
        event_club[event] = club
        if bundle in bundle_event and bundle_event[bundle] != event:
            raise ValueError(f"bundle_id {bundle} maps to more than one ticket_event_id")
        bundle_event[bundle] = event
        normalized.append({
            "bundle_id": bundle,
            "ticket_event_id": event,
            "club_id": club,
            "horizon_hours": horizon,
            "actual": _number(row["actual"], f"rows[{index}].actual"),
            "pers_prediction": _number(row["pers_prediction"], f"rows[{index}].pers_prediction"),
            "drift24_prediction": _number(row["drift24_prediction"], f"rows[{index}].drift24_prediction"),
        })

    by_horizon = {horizon: [row for row in normalized if row["horizon_hours"] == horizon] for horizon in HORIZONS}
    summaries = {str(horizon): _horizon_metrics(by_horizon[horizon]) for horizon in HORIZONS}
    primary_summary = summaries["72"]
    primary_events = primary_summary["paired_event_deltas"] if primary_summary else []
    event_deltas = [item["delta_mae"] for item in primary_events]
    bootstrap = _bootstrap_ci(event_deltas)

    missing_horizons = [horizon for horizon in HORIZONS if not by_horizon[horizon]]
    support_events = primary_summary["event_count"] if primary_summary else 0
    support_clubs = primary_summary["club_count"] if primary_summary else 0
    has_support = support_events >= MIN_EVENTS and support_clubs >= MIN_CLUBS
    guardrails_available = not missing_horizons
    guardrails_pass: bool | None = None
    if guardrails_available:
        guardrails_pass = all(
            summaries[str(h)]["drift24"]["event_balanced_mae"] <= summaries[str(h)]["pers"]["event_balanced_mae"]
            for h in (24, 48)
        )

    primary_delta = primary_summary["delta_drift24_minus_pers"]["event_balanced_mae"] if primary_summary else None
    pers72 = primary_summary["pers"]["event_balanced_mae"] if primary_summary else None
    reduction = ((pers72 - primary_summary["drift24"]["event_balanced_mae"]) / pers72) if pers72 else None
    primary_rule_pass = bool(
        has_support and primary_summary and pers72 is not None and pers72 > 0
        and reduction is not None and reduction >= MIN_IMPROVEMENT
        and bootstrap is not None and bootstrap["upper"] < 0
    )

    if not normalized or missing_horizons:
        decision = "UNKNOWN"
    elif not has_support:
        decision = "PARTIAL"
    elif primary_rule_pass and guardrails_pass:
        decision = "SUPPORTED"
    else:
        decision = "NOT_SUPPORTED"

    return {
        "schema_version": "rolling72-paired-drift24-scorecard-v1",
        "decision": decision,
        "coverage": {
            "status": "UNKNOWN",
            "forecast_coverage": None,
            "scoring_coverage": None,
            "source": "runtime status required; accepted shared-label facts do not establish coverage",
        },
        "support": {
            "primary_horizon_hours": 72,
            "accepted_event_count": support_events,
            "club_count": support_clubs,
            "minimum_events": MIN_EVENTS,
            "minimum_clubs": MIN_CLUBS,
            "floor_met": has_support,
        },
        "horizons": summaries,
        "primary_72h": {
            "pers_event_balanced_mae": pers72,
            "drift24_event_balanced_mae": primary_summary["drift24"]["event_balanced_mae"] if primary_summary else None,
            "delta_drift24_minus_pers": primary_delta,
            "relative_reduction": reduction,
            "bootstrap_95_percentile_interval": bootstrap,
            "required_relative_reduction": MIN_IMPROVEMENT,
            "upper_interval_strictly_below_zero": bootstrap is not None and bootstrap["upper"] < 0,
            "guardrails_available": guardrails_available,
            "guardrails_pass": guardrails_pass,
            "missing_horizons": missing_horizons,
        },
    }


def _load_cli_input(text: str) -> list[Mapping[str, Any]]:
    payload = json.loads(text)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, Mapping) and isinstance(payload.get("rows"), list):
        return payload["rows"]
    raise ValueError("input JSON must be an array of rows or an object with a rows array")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="JSON file, or - for stdin (default)")
    parser.add_argument("--output", default="-", help="output JSON file, or - for stdout (default)")
    args = parser.parse_args(argv)
    try:
        source = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
        result = analyze(_load_cli_input(source))
        rendered = json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n"
        if args.output == "-":
            sys.stdout.write(rendered)
        else:
            with open(args.output, "w", encoding="utf-8") as output:
                output.write(rendered)
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"scorecard input error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
