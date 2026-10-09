"""Interval calibration adapters for Beyond Demand Engine v1."""
from __future__ import annotations

from typing import Protocol

from .calibration import CalibrationBand
from .contracts import ForecastRequest, QuantileForecast


class IntervalCalibrator(Protocol):
    def calibrate(
        self,
        request: ForecastRequest,
        forecast: QuantileForecast,
    ) -> QuantileForecast: ...


class NoOpIntervalCalibrator:
    """Preserve the historical interval and its existing lineage."""

    def calibrate(
        self,
        request: ForecastRequest,
        forecast: QuantileForecast,
    ) -> QuantileForecast:
        return forecast


class ConformalIntervalCalibrator:
    """Replace legacy bounds with an empirically calibrated symmetric band.

    This calibrator does not change P50. It may only be activated with a
    CalibrationBand fitted on out-of-sample errors belonging to the SAME point
    forecasting model/protocol as the incoming forecast.
    """

    def __init__(self, band: CalibrationBand) -> None:
        self.band = band

    def calibrate(
        self,
        request: ForecastRequest,
        forecast: QuantileForecast,
    ) -> QuantileForecast:
        horizon = canonical_horizon(request.hours_to_kickoff)
        lower, upper, source = self.band.interval(
            forecast.p50,
            horizon=horizon,
            capacity=request.stadium_capacity,
        )
        return QuantileForecast(
            p10=lower,
            p50=forecast.p50,
            p90=upper,
            model_name=forecast.model_name,
            model_version=forecast.model_version,
            feature_set_version=forecast.feature_set_version,
            interval_method=f"split_conformal_absolute_residual_80:{source}",
            calibration_version=self.band.calibration_version,
        )


def canonical_horizon(hours_to_kickoff: float) -> str | None:
    targets = [
        (720.0, 240.0, "T-30"),
        (336.0, 110.88, "T-14"),
        (168.0, 55.44, "T-7"),
        (72.0, 23.76, "T-3"),
        (24.0, 12.0, "T-24h"),
    ]
    matches = [
        (abs(hours_to_kickoff - target), label)
        for target, tolerance, label in targets
        if abs(hours_to_kickoff - target) <= tolerance
    ]
    if not matches:
        return None
    return min(matches, key=lambda item: item[0])[1]
