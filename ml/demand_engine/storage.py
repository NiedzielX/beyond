"""Storage mapping for the existing Supabase forecast_observations contract."""
from __future__ import annotations

from typing import Any

from .contracts import EngineForecast


def to_forecast_observation(forecast: EngineForecast) -> dict[str, Any]:
    """Serialize one engine run without requiring a new database table.

    Engine/correction/feature lineage that has no dedicated column is retained
    inside payload.engine. The dashboard does not need payload access.
    """
    request = forecast.request
    live = forecast.live_features
    correction = forecast.correction

    return {
        "ticket_event_id": request.ticket_event_id,
        "source_snapshot_id": request.source_snapshot_id,
        "forecast_generated_at": request.forecast_generated_at.isoformat(),
        "source_snapshot_captured_at": (
            request.source_snapshot_captured_at.isoformat()
            if request.source_snapshot_captured_at
            else None
        ),
        "hours_to_kickoff": request.hours_to_kickoff,
        "days_to_match": request.days_to_match,
        "horizon": _canonical_horizon(request.hours_to_kickoff),
        "model_version": forecast.engine_version,
        "historical_model": (
            f"{forecast.historical.model_name}:{forecast.historical.model_version}"
        ),
        "historical_p10": round(forecast.historical.p10),
        "historical_p50": round(forecast.historical.p50),
        "historical_p90": round(forecast.historical.p90),
        "live_adjustment": round(correction.adjustment),
        "final_p10": round(forecast.final_p10),
        "final_p50": round(forecast.final_p50),
        "final_p90": round(forecast.final_p90),
        "forecast_status": "forecast_ready",
        "correction_status": correction.status,
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
                "historical_model_name": forecast.historical.model_name,
                "historical_model_version": forecast.historical.model_version,
                "historical_feature_set_version": forecast.historical.feature_set_version,
                "historical_interval_method": forecast.historical.interval_method,
                "historical_calibration_version": forecast.historical.calibration_version,
                "live_feature_version": live.feature_version,
                "correction_version": correction.correction_version,
                "correction_reason": correction.reason,
            },
            "live": {
                "inventory_interpretation": "demand_proxy_not_confirmed_sales",
                "data_gap_detected": live.data_gap_detected,
            },
        },
    }


def _canonical_horizon(hours: float) -> str:
    targets = [
        (720.0, "T-30"),
        (336.0, "T-14"),
        (168.0, "T-7"),
        (72.0, "T-3"),
        (24.0, "T-24h"),
    ]
    target, label = min(targets, key=lambda item: abs(hours - item[0]))
    return label if abs(hours - target) <= max(12.0, target * 0.33) else "continuous"
