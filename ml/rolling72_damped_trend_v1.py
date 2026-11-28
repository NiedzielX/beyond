"""Offline arithmetic for the proposed Rolling72 damped trend.

The issuer must supply the same validated slope and projection age used by
the undamped control. This module has no clock, cohort, or label authority.
"""

from __future__ import annotations

import math

PHI = 0.80
HORIZONS = (24, 48, 72)


def _finite(value: int | float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{field} must be finite")
    try:
        result = float(value)
    except OverflowError:
        raise ValueError(f"{field} must be finite") from None
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def damped_available_total(
    *,
    origin_available_total: int | float,
    slope24: int | float | None,
    projection_age_hours: int | float,
    horizon_hours: int,
) -> float:
    """Return the prospective policy value for an already validated origin.

    A missing slope means that the shared drift eligibility policy selected
    fallback. Its status and reason are owned by the caller's issue record.
    """
    if type(horizon_hours) is not int or horizon_hours not in HORIZONS:
        raise ValueError("horizon_hours must be 24, 48 or 72")
    origin = _finite(origin_available_total, "origin_available_total")
    age = _finite(projection_age_hours, "projection_age_hours")
    if origin < 0 or not 0 <= age <= 1:
        raise ValueError("origin or projection age is outside the supported range")
    if slope24 is None:
        return origin
    slope = _finite(slope24, "slope24")
    elapsed_days = (horizon_hours + age) / 24
    effective_hours = 24 * -math.expm1(elapsed_days * math.log(PHI)) / (1 - PHI)
    value = origin + slope * effective_hours
    if not math.isfinite(value):
        raise ValueError("damped prediction must be finite")
    return max(0.0, value)
