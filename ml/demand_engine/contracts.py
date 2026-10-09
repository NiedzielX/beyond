"""Typed contracts for Beyond Demand Engine v1.

The contracts intentionally separate historical forecasting from proprietary live
inventory correction. This lets incumbents and challengers run in shadow mode
without changing the storage contract or product layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Mapping

SignalReadiness = Literal["not_ready", "partial", "ready"]
CorrectionStatus = Literal["not_applied", "shadow", "applied", "blocked_quality"]


@dataclass(frozen=True)
class ForecastRequest:
    ticket_event_id: int
    club_slug: str
    home_team: str
    away_team: str
    competition: str
    kickoff_at: datetime
    forecast_generated_at: datetime
    source_snapshot_id: int | None = None
    source_snapshot_captured_at: datetime | None = None
    stadium_capacity: int | None = None
    static_features: Mapping[str, Any] = field(default_factory=dict)

    @property
    def hours_to_kickoff(self) -> float:
        return (self.kickoff_at - self.forecast_generated_at).total_seconds() / 3600.0

    @property
    def days_to_match(self) -> float:
        return self.hours_to_kickoff / 24.0


@dataclass(frozen=True)
class QuantileForecast:
    p10: float
    p50: float
    p90: float
    model_name: str
    model_version: str
    feature_set_version: str

    def validate(self) -> None:
        if not self.p10 <= self.p50 <= self.p90:
            raise ValueError(f"Invalid quantile order: {self.p10}, {self.p50}, {self.p90}")
        if self.p10 < 0:
            raise ValueError("Attendance forecast cannot be negative")


@dataclass(frozen=True)
class LiveFeatures:
    feature_version: str
    signal_readiness: SignalReadiness
    available_total: int | None = None
    first_available_total: int | None = None
    available_index: float | None = None
    net_removed_since_first: int | None = None
    net_removed_since_previous: int | None = None
    velocity_since_previous: float | None = None
    net_removed_6h: int | None = None
    velocity_6h: float | None = None
    net_removed_24h: int | None = None
    velocity_24h: float | None = None
    acceleration_6h_vs_24h: float | None = None
    raw_snapshot_count: int | None = None
    clean_snapshot_count: int | None = None
    excluded_anomaly_count: int | None = None
    data_gap_detected: bool | None = None


@dataclass(frozen=True)
class LiveCorrection:
    adjustment: float
    correction_version: str
    status: CorrectionStatus
    reason: str


@dataclass(frozen=True)
class EngineForecast:
    engine_version: str
    request: ForecastRequest
    historical: QuantileForecast
    live_features: LiveFeatures
    correction: LiveCorrection
    final_p10: float
    final_p50: float
    final_p90: float

    def validate(self) -> None:
        self.historical.validate()
        if not self.final_p10 <= self.final_p50 <= self.final_p90:
            raise ValueError(
                f"Invalid final quantile order: {self.final_p10}, {self.final_p50}, {self.final_p90}"
            )
        if self.final_p10 < 0:
            raise ValueError("Final attendance forecast cannot be negative")
        if self.request.stadium_capacity is not None and self.final_p90 > self.request.stadium_capacity:
            raise ValueError("Final P90 exceeds configured stadium capacity")
