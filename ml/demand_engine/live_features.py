"""Adapters for Demand Engine live inventory features."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .contracts import ForecastRequest, LiveFeatures, SignalReadiness

LIVE_FEATURE_VERSION = "live-trajectory-v1"


class RowLiveFeatureProvider:
    """Maps a latest-feature row into the engine contract.

    The row retrieval itself is dependency-injected so production may use
    Supabase/Postgres while tests/replays can use CSV or in-memory data.

    This provider never upgrades an unspecified readiness state to `ready`.
    Freshly computed/legacy rows default to `partial` until the quality/readiness
    policy is explicitly present in the row.
    """

    def __init__(
        self,
        fetch_latest: Callable[[int], Mapping[str, Any] | None],
        feature_version: str = LIVE_FEATURE_VERSION,
    ) -> None:
        self.fetch_latest = fetch_latest
        self.feature_version = feature_version

    def features(self, request: ForecastRequest) -> LiveFeatures:
        row = self.fetch_latest(request.ticket_event_id)
        if not row:
            return LiveFeatures(
                feature_version=self.feature_version,
                signal_readiness="not_ready",
            )

        readiness = _readiness(row.get("signal_readiness"))
        if readiness is None:
            readiness = "partial"

        available_total = _int(row.get("available_total"))
        capacity_share = _float(row.get("available_share_of_capacity"))
        if capacity_share is None and available_total is not None and request.stadium_capacity:
            capacity_share = available_total / request.stadium_capacity

        return LiveFeatures(
            feature_version=str(_first(row.get("feature_version"), self.feature_version)),
            signal_readiness=readiness,
            feature_quality=_str(row.get("feature_quality")),
            point_in_time_validated=_bool(row.get("point_in_time_validated")),
            hours_to_kickoff=_float(row.get("hours_to_kickoff")),
            days_to_kickoff=_float(row.get("days_to_kickoff")),
            snapshot_age_minutes=_float(row.get("snapshot_age_minutes")),
            checkpoint_label=_str(_first(row.get("checkpoint_label"), row.get("horizon"))),
            checkpoint_distance_hours=_float(row.get("checkpoint_distance_hours")),
            checkpoint_ready=_bool(row.get("checkpoint_ready")),
            available_total=available_total,
            first_available_total=_int(
                _first(row.get("first_available_total"), row.get("first_observed_available_total"))
            ),
            available_index=_float(row.get("available_index")),
            available_share_of_capacity=capacity_share,
            public_seat_map_size=_int(row.get("public_seat_map_size")),
            available_pct_of_public_seat_map=_float(
                row.get("available_pct_of_public_seat_map")
            ),
            net_removed_since_first=_int(
                _first(row.get("net_removed_since_first"), row.get("raw_net_removed_since_first"))
            ),
            net_removed_since_previous=_int(
                _first(
                    row.get("net_removed_since_previous"),
                    row.get("raw_net_removed_since_previous"),
                )
            ),
            velocity_since_previous=_float(
                _first(row.get("velocity_since_previous"), row.get("raw_velocity_since_previous"))
            ),
            net_removed_6h=_int(_first(row.get("net_removed_6h"), row.get("raw_net_removed_6h"))),
            velocity_6h=_float(_first(row.get("velocity_6h"), row.get("raw_velocity_6h"))),
            net_removed_24h=_int(
                _first(row.get("net_removed_24h"), row.get("raw_net_removed_24h"))
            ),
            velocity_24h=_float(_first(row.get("velocity_24h"), row.get("raw_velocity_24h"))),
            net_removed_72h=_int(row.get("net_removed_72h")),
            velocity_72h=_float(row.get("velocity_72h")),
            net_removed_7d=_int(row.get("net_removed_7d")),
            velocity_7d=_float(row.get("velocity_7d")),
            velocity_6h_pct_of_first_per_hour=_float(
                _first(
                    row.get("velocity_6h_pct_of_first_per_hour"),
                    row.get("raw_velocity_6h_pct_of_first_per_hour"),
                )
            ),
            velocity_24h_pct_of_first_per_hour=_float(
                _first(
                    row.get("velocity_24h_pct_of_first_per_hour"),
                    row.get("raw_velocity_24h_pct_of_first_per_hour"),
                )
            ),
            velocity_72h_pct_of_first_per_hour=_float(
                row.get("velocity_72h_pct_of_first_per_hour")
            ),
            velocity_7d_pct_of_first_per_hour=_float(
                row.get("velocity_7d_pct_of_first_per_hour")
            ),
            velocity_6h_pct_of_capacity_per_hour=_float(
                row.get("velocity_6h_pct_of_capacity_per_hour")
            ),
            velocity_24h_pct_of_capacity_per_hour=_float(
                row.get("velocity_24h_pct_of_capacity_per_hour")
            ),
            velocity_72h_pct_of_capacity_per_hour=_float(
                row.get("velocity_72h_pct_of_capacity_per_hour")
            ),
            velocity_7d_pct_of_capacity_per_hour=_float(
                row.get("velocity_7d_pct_of_capacity_per_hour")
            ),
            acceleration_6h_vs_24h=_float(
                _first(
                    row.get("acceleration_6h_vs_24h"),
                    row.get("raw_acceleration_6h_vs_24h"),
                )
            ),
            acceleration_24h_vs_72h=_float(row.get("acceleration_24h_vs_72h")),
            acceleration_72h_vs_7d=_float(row.get("acceleration_72h_vs_7d")),
            matched_sector_count=_int(row.get("matched_sector_count")),
            entered_sector_count=_int(row.get("entered_sector_count")),
            left_sector_count=_int(row.get("left_sector_count")),
            matched_absorption=_int(row.get("matched_absorption")),
            matched_release=_int(row.get("matched_release")),
            coverage_inventory_effect=_int(row.get("coverage_inventory_effect")),
            sector_coverage_change_flag=_bool(row.get("sector_coverage_change_flag")),
            release_activity_flag=_bool(row.get("release_activity_flag")),
            unexplained_inventory_increase_flag=_bool(
                row.get("unexplained_inventory_increase_flag")
            ),
            raw_snapshot_count=_int(
                _first(row.get("raw_snapshot_count"), row.get("snapshots_visible"))
            ),
            clean_snapshot_count=_int(row.get("clean_snapshot_count")),
            excluded_anomaly_count=_int(row.get("excluded_anomaly_count")),
            duplicate_timestamp_count=_int(row.get("duplicate_timestamp_count")),
            invalid_snapshot_count=_int(row.get("invalid_snapshot_count")),
            observation_window_hours=_float(row.get("observation_window_hours")),
            max_visible_gap_hours=_float(row.get("max_visible_gap_hours")),
            data_gap_detected=_bool(row.get("data_gap_detected")),
        )


def _first(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _readiness(value: Any) -> SignalReadiness | None:
    if value in {"not_ready", "partial", "ready"}:
        return value
    return None


def _float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "t", "1", "yes"}:
            return True
        if lowered in {"false", "f", "0", "no"}:
            return False
    return bool(value)
