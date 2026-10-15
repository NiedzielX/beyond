"""P50-only shadow forecast contract built on the genuine Structural Prior.

P10/P90 remain absent until the probabilistic layer is calibrated. Live
trajectory evidence and trajectory-gap state are persisted for observation, but
no live correction is applied before its promotion gate passes.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .live_trajectory_feature_store import LiveTrajectoryFeatures
from .trajectory_gap import TrajectoryGapResult

ENGINE_VERSION = "beyond-demand-engine-v1-structural-prior-shadow"
CORRECTION_VERSION = "live-correction-noop-v2-trajectory-gap-observed"
INTERVAL_STATUS = "not_yet_calibrated"


class StructuralPriorShadowError(RuntimeError):
    pass


@dataclass(frozen=True)
class StructuralPriorSnapshot:
    status: str
    source_prior_id: int | None
    horizon: str | None
    model_spec_id: str | None
    model_family: str | None
    feature_contract: str | None
    p50: float | None
    stadium_capacity: int | None
    expected_occupancy: float | None
    point_in_time_validated: bool | None


@dataclass(frozen=True)
class P50ShadowForecast:
    ticket_event_id: int
    club_slug: str
    home_team: str
    away_team: str
    competition: str
    kickoff_at: datetime
    forecast_generated_at: datetime
    source_snapshot_id: int
    source_snapshot_captured_at: datetime
    prior: StructuralPriorSnapshot
    live: LiveTrajectoryFeatures
    trajectory_gap: TrajectoryGapResult
    engine_version: str = ENGINE_VERSION

    @property
    def hours_to_kickoff(self) -> float:
        return (self.kickoff_at - self.forecast_generated_at).total_seconds() / 3600.0

    @property
    def days_to_match(self) -> float:
        return self.hours_to_kickoff / 24.0

    @property
    def final_p50(self) -> float:
        if self.prior.p50 is None:
            raise StructuralPriorShadowError("Structural Prior P50 is missing")
        return float(self.prior.p50)

    def validate(self) -> None:
        if self.prior.status != "ready":
            raise StructuralPriorShadowError("Structural Prior must be ready")
        if self.prior.source_prior_id is None:
            raise StructuralPriorShadowError("source_prior_id is required")
        if not self.prior.point_in_time_validated:
            raise StructuralPriorShadowError("Structural Prior is not PIT validated")
        if self.prior.p50 is None or self.prior.p50 < 0:
            raise StructuralPriorShadowError("Valid Structural Prior P50 is required")
        if not self.prior.horizon or not self.prior.model_spec_id or not self.prior.feature_contract:
            raise StructuralPriorShadowError("Structural Prior lineage is incomplete")
        if not self.live.point_in_time_validated:
            raise StructuralPriorShadowError("Live features are not PIT validated")
        if self.live.snapshot_id != self.source_snapshot_id:
            raise StructuralPriorShadowError("Live snapshot does not match source_snapshot_id")
        if self.live.snapshot_captured_at != self.source_snapshot_captured_at:
            raise StructuralPriorShadowError("Live snapshot timestamp does not match source lineage")
        if self.live.as_of != self.forecast_generated_at:
            raise StructuralPriorShadowError("Live as_of must equal forecast_generated_at")
        if self.forecast_generated_at >= self.kickoff_at:
            raise StructuralPriorShadowError("forecast_generated_at must be before kickoff")
        if self.trajectory_gap.ticket_event_id != self.ticket_event_id:
            raise StructuralPriorShadowError("Trajectory gap event mismatch")
        if self.trajectory_gap.structural_prior_id != self.prior.source_prior_id:
            raise StructuralPriorShadowError("Trajectory gap prior mismatch")
        if self.trajectory_gap.as_of_at != self.forecast_generated_at:
            raise StructuralPriorShadowError("Trajectory gap as_of mismatch")
        if self.prior.stadium_capacity is not None and self.final_p50 > self.prior.stadium_capacity:
            raise StructuralPriorShadowError("P50 exceeds stadium capacity")


def to_forecast_observation(forecast: P50ShadowForecast) -> dict[str, Any]:
    """Serialize a P50-only shadow revision for forecast_observations."""
    forecast.validate()
    live = forecast.live
    gap = forecast.trajectory_gap
    prior = forecast.prior

    row: dict[str, Any] = {
        "ticket_event_id": forecast.ticket_event_id,
        "source_snapshot_id": forecast.source_snapshot_id,
        "forecast_generated_at": forecast.forecast_generated_at.isoformat(),
        "source_snapshot_captured_at": forecast.source_snapshot_captured_at.isoformat(),
        "hours_to_kickoff": forecast.hours_to_kickoff,
        "days_to_match": forecast.days_to_match,
        # This is the source Structural Prior checkpoint being carried forward,
        # not a legacy nearest-checkpoint label for the current live timestamp.
        "horizon": prior.horizon,
        "model_version": forecast.engine_version,
        "historical_model": prior.model_spec_id,
        "historical_p50": int(round(forecast.final_p50)),
        "live_adjustment": 0,
        "final_p50": int(round(forecast.final_p50)),
        "forecast_status": "shadow",
        "correction_status": "shadow",
        "signal_readiness": live.signal_readiness,
        "live_available_total": live.available_total,
        "live_first_available_total": live.first_available_total,
        "live_available_index": live.available_index,
        "live_net_removed_since_first": live.net_removed_since_first,
        "live_net_removed_since_previous": live.net_removed_since_previous,
        "live_velocity_since_previous": live.velocity_since_previous,
        "live_net_removed_6h": live.net_removed_6h,
        "live_velocity_6h": live.velocity_6h,
        "live_net_removed_24h": live.net_removed_24h,
        "live_velocity_24h": live.velocity_24h,
        "live_acceleration_6h_vs_24h": live.acceleration_6h_vs_24h,
        "live_raw_snapshot_count": live.raw_snapshot_count,
        "live_clean_snapshot_count": live.clean_snapshot_count,
        "live_excluded_anomaly_count": live.excluded_anomaly_count,
        "payload": {
            "engine": {
                "engine_version": forecast.engine_version,
                "mode": "shadow",
                "source_prior_id": prior.source_prior_id,
                "structural_prior_horizon": prior.horizon,
                "historical_model_name": prior.model_spec_id,
                "historical_model_version": prior.model_spec_id,
                "historical_feature_set_version": prior.feature_contract,
                "historical_interval_method": INTERVAL_STATUS,
                "historical_calibration_version": None,
                "live_feature_version": live.feature_version,
                "correction_version": CORRECTION_VERSION,
                "correction_reason": (
                    "No validated live correction promoted; genuine Structural Prior P50 preserved."
                ),
            },
            "structural_prior": {
                "source_prior_id": prior.source_prior_id,
                "horizon": prior.horizon,
                "model_spec_id": prior.model_spec_id,
                "model_family": prior.model_family,
                "feature_contract": prior.feature_contract,
                "p50": prior.p50,
                "stadium_capacity": prior.stadium_capacity,
                "expected_occupancy": prior.expected_occupancy,
                "point_in_time_validated": prior.point_in_time_validated,
            },
            "trajectory_gap": {
                "version": gap.version,
                "reference_mode": gap.reference_mode,
                "prior_mapping_mode": gap.prior_mapping_mode,
                "reference_horizon": gap.reference_horizon,
                "reference_event_count": gap.reference_event_count,
                "reference_club_count": gap.reference_club_count,
                "observed_progress": gap.observed_progress,
                "expected_progress": gap.expected_progress,
                "expected_progress_q25": gap.expected_progress_q25,
                "expected_progress_q75": gap.expected_progress_q75,
                "level_gap": gap.level_gap,
                "observed_velocity_24h": gap.observed_velocity_24h,
                "expected_velocity_24h": gap.expected_velocity_24h,
                "velocity_gap": gap.velocity_gap,
                "observed_acceleration_6h_vs_24h": gap.observed_acceleration_6h_vs_24h,
                "expected_acceleration_6h_vs_24h": gap.expected_acceleration_6h_vs_24h,
                "acceleration_gap": gap.acceleration_gap,
                "status": gap.status,
                "confidence": gap.confidence,
                "reason_code": gap.reason_code,
                "point_in_time_validated": gap.point_in_time_validated,
            },
            "live": {
                "inventory_interpretation": live.inventory_interpretation,
                "feature_quality": live.feature_quality,
                "point_in_time_validated": live.point_in_time_validated,
                "checkpoint_label": live.checkpoint_label,
                "checkpoint_distance_hours": live.checkpoint_distance_hours,
                "checkpoint_ready": live.checkpoint_ready,
                "feature_hours_to_kickoff": live.hours_to_kickoff,
                "snapshot_age_minutes": live.snapshot_age_minutes,
                "available_share_of_capacity": live.available_share_of_capacity,
                "velocity_6h_pct_of_first_per_hour": live.velocity_6h_pct_of_first_per_hour,
                "velocity_24h_pct_of_first_per_hour": live.velocity_24h_pct_of_first_per_hour,
                "velocity_72h_pct_of_first_per_hour": live.velocity_72h_pct_of_first_per_hour,
                "velocity_7d_pct_of_first_per_hour": live.velocity_7d_pct_of_first_per_hour,
                "matched_sector_count": live.matched_sector_count,
                "entered_sector_count": live.entered_sector_count,
                "left_sector_count": live.left_sector_count,
                "release_activity_flag": live.release_activity_flag,
                "sector_coverage_change_flag": live.sector_coverage_change_flag,
                "unexplained_inventory_increase_flag": live.unexplained_inventory_increase_flag,
                "observation_window_hours": live.observation_window_hours,
                "max_visible_gap_hours": live.max_visible_gap_hours,
                "data_gap_detected": live.data_gap_detected,
            },
        },
    }
    # P10/P90 are intentionally omitted until calibration exists.
    return {key: value for key, value in row.items() if value is not None}


class SupabaseP50ShadowStore:
    """Persist P50-only Structural Prior shadow revisions through the existing RPC."""

    rpc_name = "insert_demand_engine_shadow_forecast_v1"

    def __init__(self, supabase_url: str | None = None, service_role_key: str | None = None) -> None:
        self.supabase_url = (supabase_url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.service_role_key = service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is required")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")

    def insert(self, forecast: P50ShadowForecast) -> dict[str, Any]:
        observation = to_forecast_observation(forecast)
        endpoint = f"{self.supabase_url}/rest/v1/rpc/{self.rpc_name}"
        payload = json.dumps({"p_observation": observation}).encode("utf-8")
        request = Request(
            endpoint,
            data=payload,
            method="POST",
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise StructuralPriorShadowError(
                f"{self.rpc_name} failed with HTTP {exc.code}: {body}"
            ) from exc
        observation_id = int(result)
        return {
            "id": observation_id,
            "ticket_event_id": forecast.ticket_event_id,
            "model_version": forecast.engine_version,
            "forecast_status": "shadow",
        }
