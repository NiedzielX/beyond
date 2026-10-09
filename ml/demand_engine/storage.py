"""Persistence contract for Python Beyond Demand Engine shadow forecasts."""
from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .contracts import EngineForecast


class ForecastPersistenceError(RuntimeError):
    pass


def _rounded(value: float | None) -> int | None:
    return None if value is None else int(round(float(value)))


def canonical_horizon(hours_to_kickoff: float) -> str:
    # Same one-sided canonical windows used by live_benchmark_v03: a forecast
    # cannot use information from after the target checkpoint.
    windows = (
        ("T-30", 720.0, 240.0),
        ("T-14", 336.0, 96.0),
        ("T-7", 168.0, 48.0),
        ("T-3", 72.0, 24.0),
        ("T-24h", 24.0, 12.0),
    )
    for label, target, tolerance in windows:
        if target <= hours_to_kickoff <= target + tolerance:
            return label
    # A six-hour scheduler can first execute the exact T-7 shadow model shortly
    # after the canonical instant. Keep its lineage explicit rather than calling
    # it a generic continuous forecast.
    if 162.0 <= hours_to_kickoff < 168.0:
        return "T-7"
    return "continuous"


def engine_forecast_to_shadow_observation(forecast: EngineForecast) -> dict[str, Any]:
    forecast.validate()
    request = forecast.request
    if request.source_snapshot_id is None:
        raise ForecastPersistenceError("source_snapshot_id is required for persisted shadow forecasts")
    if request.source_snapshot_captured_at is None:
        raise ForecastPersistenceError(
            "source_snapshot_captured_at is required for persisted shadow forecasts"
        )

    historical_state_keys = (
        "season",
        "opponent_key",
        "target_round_no",
        "target_season_progress",
        "target_matches_remaining",
        "lech_position_at_t7",
        "opponent_position_at_t7",
        "lech_matches_played_at_t7",
        "opponent_matches_played_at_t7",
        "league_team_count",
        "t7_state_cutoff_local_date",
        "t7_visible_league_results",
    )
    historical_state = {
        key: request.static_features[key]
        for key in historical_state_keys
        if key in request.static_features
    }

    live = forecast.live_features
    row: dict[str, Any] = {
        "ticket_event_id": request.ticket_event_id,
        "source_snapshot_id": request.source_snapshot_id,
        "forecast_generated_at": request.forecast_generated_at.isoformat(),
        "source_snapshot_captured_at": request.source_snapshot_captured_at.isoformat(),
        "hours_to_kickoff": request.hours_to_kickoff,
        "days_to_match": request.days_to_match,
        "horizon": canonical_horizon(request.hours_to_kickoff),
        "model_version": forecast.engine_version,
        "historical_model": forecast.historical.model_version,
        "historical_p10": _rounded(forecast.historical.p10),
        "historical_p50": _rounded(forecast.historical.p50),
        "historical_p90": _rounded(forecast.historical.p90),
        "live_adjustment": _rounded(forecast.correction.adjustment) or 0,
        "final_p10": _rounded(forecast.final_p10),
        "final_p50": _rounded(forecast.final_p50),
        "final_p90": _rounded(forecast.final_p90),
        "forecast_status": "shadow",
        "correction_status": forecast.correction.status,
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
                "historical_model_name": forecast.historical.model_name,
                "historical_model_version": forecast.historical.model_version,
                "historical_feature_set_version": forecast.historical.feature_set_version,
                "historical_interval_method": forecast.historical.interval_method,
                "historical_calibration_version": forecast.historical.calibration_version,
                "live_feature_version": live.feature_version,
                "correction_version": forecast.correction.correction_version,
                "correction_reason": forecast.correction.reason,
            },
            "historical_state": historical_state,
            "live": {
                "inventory_interpretation": "demand_proxy_not_confirmed_sales",
                "data_gap_detected": live.data_gap_detected,
            },
        },
    }
    return {key: value for key, value in row.items() if value is not None}


# Backward-compatible name used by earlier harness code.
to_forecast_observation = engine_forecast_to_shadow_observation


class SupabaseForecastStore:
    rpc_name = "insert_demand_engine_shadow_forecast_v1"

    def __init__(
        self,
        supabase_url: str | None = None,
        service_role_key: str | None = None,
    ) -> None:
        self.supabase_url = (supabase_url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.service_role_key = service_role_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY", ""
        )
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is required")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")

    def insert(self, forecast: EngineForecast) -> dict[str, Any]:
        observation = engine_forecast_to_shadow_observation(forecast)
        result = self._post(observation)
        if isinstance(result, int):
            observation_id = result
        elif isinstance(result, str) and result.isdigit():
            observation_id = int(result)
        else:
            raise ForecastPersistenceError(
                f"Unexpected {self.rpc_name} response: {result!r}"
            )
        return {
            "id": observation_id,
            "ticket_event_id": forecast.request.ticket_event_id,
            "model_version": forecast.engine_version,
            "forecast_status": "shadow",
        }

    def _post(self, observation: dict[str, Any]) -> Any:
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
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ForecastPersistenceError(
                f"{self.rpc_name} failed with HTTP {exc.code}: {body}"
            ) from exc
