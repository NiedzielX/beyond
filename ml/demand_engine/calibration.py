"""Probabilistic interval calibration for Beyond Demand Engine v1.

This module turns a point forecast (P50) into an empirically calibrated 80%
prediction interval using split-conformal absolute residuals. The stored lower
and upper bounds map to the existing P10/P90 fields, but lineage explicitly
records that they are conformal interval bounds rather than independently
trained 0.10/0.90 quantile models.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable, Mapping

import numpy as np

DEFAULT_COVERAGE = 0.80


@dataclass(frozen=True)
class CalibrationBand:
    calibration_version: str
    coverage_target: float
    global_radius: float
    horizon_radius: Mapping[str, float]
    min_horizon_rows: int
    calibration_rows: int

    def radius_for(self, horizon: str | None) -> tuple[float, str]:
        if horizon and horizon in self.horizon_radius:
            return float(self.horizon_radius[horizon]), f"horizon:{horizon}"
        return float(self.global_radius), "global_fallback"

    def interval(
        self,
        p50: float,
        horizon: str | None = None,
        capacity: float | None = None,
    ) -> tuple[float, float, str]:
        radius, source = self.radius_for(horizon)
        lower = max(0.0, float(p50) - radius)
        upper = float(p50) + radius
        if capacity is not None:
            upper = min(float(capacity), upper)
        return lower, upper, source


def conformal_radius(
    absolute_errors: Iterable[float],
    coverage: float = DEFAULT_COVERAGE,
) -> float:
    """Finite-sample split-conformal radius.

    Uses the ceil((n + 1) * coverage)-th ordered absolute residual, capped at n.
    This is the standard conservative finite-sample conformal quantile for a
    symmetric interval around a point forecast.
    """
    values = np.asarray(list(absolute_errors), dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        raise ValueError("Calibration requires at least one finite absolute error")
    if not 0.0 < coverage < 1.0:
        raise ValueError("coverage must be between 0 and 1")

    ordered = np.sort(values)
    rank = min(len(ordered), ceil((len(ordered) + 1) * coverage))
    return float(ordered[rank - 1])


def fit_calibration_band(
    rows: Iterable[dict],
    *,
    calibration_version: str,
    coverage: float = DEFAULT_COVERAGE,
    min_horizon_rows: int = 20,
) -> CalibrationBand:
    """Fit global + optional horizon-specific conformal radii.

    Each row must contain `actual`, `p50` and optionally `horizon`.
    Horizon-specific radii are only emitted when enough independent calibration
    observations exist; otherwise inference falls back to the global radius.
    """
    materialized = list(rows)
    errors = [
        abs(float(row["actual"]) - float(row["p50"]))
        for row in materialized
        if row.get("actual") is not None and row.get("p50") is not None
    ]
    global_radius = conformal_radius(errors, coverage)

    by_horizon: dict[str, list[float]] = {}
    for row in materialized:
        if row.get("actual") is None or row.get("p50") is None:
            continue
        horizon = row.get("horizon")
        if not horizon:
            continue
        by_horizon.setdefault(str(horizon), []).append(
            abs(float(row["actual"]) - float(row["p50"]))
        )

    horizon_radius = {
        horizon: conformal_radius(values, coverage)
        for horizon, values in by_horizon.items()
        if len(values) >= min_horizon_rows
    }

    return CalibrationBand(
        calibration_version=calibration_version,
        coverage_target=coverage,
        global_radius=global_radius,
        horizon_radius=horizon_radius,
        min_horizon_rows=min_horizon_rows,
        calibration_rows=len(errors),
    )
