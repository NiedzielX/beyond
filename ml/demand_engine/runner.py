"""One-run orchestration for Beyond Demand Engine v1."""
from __future__ import annotations

from typing import Protocol

from .contracts import EngineForecast, ForecastRequest
from .engine import DemandEngine


class ForecastStore(Protocol):
    def insert(self, forecast: EngineForecast) -> dict: ...


class ForecastRunner:
    def __init__(self, engine: DemandEngine, store: ForecastStore) -> None:
        self.engine = engine
        self.store = store

    def run(self, request: ForecastRequest) -> tuple[EngineForecast, dict]:
        forecast = self.engine.forecast(request)
        persisted = self.store.insert(forecast)
        return forecast, persisted
