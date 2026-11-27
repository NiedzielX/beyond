"""Offline three-method bundle for the prospective damped-trend lane.

This composes the validated PERS/drift24 preparation and actual-issue binder
with the fixed damped arithmetic. It does not issue, persist, or label rows.
Its offline parent does not attest database visibility or membership history.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from ml.rolling72_fresh_paired_drift24_v1 import (
    HORIZONS, bind_actual_issue, prepare_values,
)
from ml.rolling72_damped_trend_v1 import PHI, damped_available_total

VERSION = "rolling72-mvp-paired-damped-trend-v1"
METHODS = ("PERS", "DRIFT24", "DAMPED")


def prepare_triplet_values(
    origin: dict[str, Any],
    history: Iterable[dict[str, Any]],
    *,
    projection_reference_at: datetime,
    attempts: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Calculate all supported numeric values before attaching an issue time."""
    prepared = prepare_values(
        origin, history, projection_reference_at=projection_reference_at,
        attempts=attempts,
    )
    provenance = prepared["provenance"]
    triplet_rows = []
    for row in prepared["forecast_values"]:
        triplet_rows.append(row)
        if row["method"] == "DRIFT24":
            value = damped_available_total(
                origin_available_total=origin["available_total"],
                slope24=provenance["slope24"] if row["status"] == "READY" else None,
                projection_age_hours=provenance["age_hours"],
                horizon_hours=row["horizon_hours"],
            )
            triplet_rows.append({**row, "method": "DAMPED", "prediction": value})
    return {**prepared, "forecast_values": triplet_rows}


def bind_triplet_issue(
    prepared: dict[str, Any], *, issued_at: datetime, kickoff_at: datetime,
) -> dict[str, Any]:
    """Bind caller-provided issue coordinates without calculating forecasts."""
    expected = [(h, method) for h in HORIZONS for method in METHODS]
    values = prepared.get("forecast_values", [])
    if prepared.get("bundle_status") == "UNAVAILABLE_SOURCE":
        expected = []
    if [(row["horizon_hours"], row["method"]) for row in values] != expected:
        raise ValueError("prepared triplet coordinates are incomplete or out of order")
    bound = bind_actual_issue(prepared, issued_at=issued_at, kickoff_at=kickoff_at)
    result_rows = []
    for row in bound["forecasts"]:
        result_rows.append(row)
        if row["method"] == "DRIFT24" and row["prediction"] is None:
            # The parent binder synthesizes two null rows for these cases.
            result_rows.append({**row, "method": "DAMPED"})
    provenance = {
        **bound["provenance"], "version": VERSION, "damping_phi": PHI,
        "damped_formula": "max(0, origin + slope24 * 24*(1-phi**((h+age)/24))/(1-phi))",
    }
    # The parent has already put rows in horizon order and every numeric
    # triplet was prepared in the canonical PERS, DRIFT24, DAMPED order.
    public_coordinates = {
        key: value for key, value in bound.items()
        if key not in {"_origin_captured_at", "forecast_values"}
    }
    return {**public_coordinates, "version": VERSION, "forecasts": result_rows,
            "provenance": provenance}


def prepare_triplet(
    origin: dict[str, Any],
    history: Iterable[dict[str, Any]],
    *,
    projection_reference_at: datetime,
    issued_at: datetime,
    kickoff_at: datetime,
    attempts: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Offline convenience wrapper. Caller clocks are not runtime evidence."""
    prepared = prepare_triplet_values(
        origin, history, projection_reference_at=projection_reference_at,
        attempts=attempts,
    )
    return bind_triplet_issue(prepared, issued_at=issued_at, kickoff_at=kickoff_at)
