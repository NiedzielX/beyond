"""Composable Beyond Demand Engine v1.

No unvalidated live correction is embedded here. Production promotion requires a
correction implementation to pass the benchmark gate; until then the safe
reference implementation is a no-op / shadow correction.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from .contracts import (
    EngineForecast,
    ForecastRequest,
    LiveCorrection,
    LiveFeatures,
    QuantileForecast,
)

ENGINE_VERSION = "beyond-demand-engine-v1"


class HistoricalForecaster(Protocol):
    def forecast(self, request: ForecastRequest) -> QuantileForecast: ...


class LiveFeatureProvider(Protocol):
    def features(self, request: ForecastRequest) -> LiveFeatures: ...


class LiveCorrector(Protocol):
    def correct(
        self,
        request: ForecastRequest,
        historical: QuantileForecast,
        live_features: LiveFeatures,
    ) -> LiveCorrection: ...


class NoOpLiveCorrector:
    """Safe reference correction used until a live rule/model is validated."""

    correction_version = "live-correction-noop-v1"

    def correct(
        self,
        request: ForecastRequest,
        historical: QuantileForecast,
        live_features: LiveFeatures,
    ) -> LiveCorrection:
        status = "shadow" if live_features.signal_readiness != "not_ready" else "not_applied"
        return LiveCorrection(
            adjustment=0.0,
            correction_version=self.correction_version,
            status=status,
            reason="No validated live correction promoted; historical forecast preserved.",
        )


class DemandEngine:
    def __init__(
        self,
        historical_forecaster: HistoricalForecaster,
        live_feature_provider: LiveFeatureProvider,
        live_corrector: LiveCorrector | None = None,
        engine_version: str = ENGINE_VERSION,
    ) -> None:
        self.historical_forecaster = historical_forecaster
        self.live_feature_provider = live_feature_provider
        self.live_corrector = live_corrector or NoOpLiveCorrector()
        self.engine_version = engine_version

    def forecast(self, request: ForecastRequest) -> EngineForecast:
        historical = self.historical_forecaster.forecast(request)
        historical.validate()
        live_features = self.live_feature_provider.features(request)
        correction = self.live_corrector.correct(request, historical, live_features)

        # v1 applies a point shift consistently to all quantiles. A future
        # probabilistic corrector may return quantile-specific deltas, but that
        # change must be benchmarked and versioned explicitly.
        capacity = request.stadium_capacity
        final = [
            historical.p10 + correction.adjustment,
            historical.p50 + correction.adjustment,
            historical.p90 + correction.adjustment,
        ]
        final = [max(0.0, value) for value in final]
        if capacity is not None:
            final = [min(float(capacity), value) for value in final]

        output = EngineForecast(
            engine_version=self.engine_version,
            request=request,
            historical=historical,
            live_features=live_features,
            correction=correction,
            final_p10=final[0],
            final_p50=final[1],
            final_p90=final[2],
        )
        output.validate()
        return output
