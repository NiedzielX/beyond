"""Adapters for Demand Engine live inventory features."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .contracts import ForecastRequest, LiveFeatures, SignalReadiness

LIVE_FEATURE_VERSION = "live-features-v1"


class RowLiveFeatureProvider:
    """Maps a latest-feature row into the engine contract.

    The row retrieval itself is dependency-injected so production may use
    Supabase/Postgres while tests/replays can use CSV or in-memory data.

    This provider never upgrades an unspecified readiness state to `ready`.
    Freshly computed rows default to `partial` until the quality/readiness policy
    is explicitly validated and versioned.
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

        return LiveFeatures(
            feature_version=self.feature_version,
            signal_readiness=readiness,
            available_total=_int(row.get("available_total")),
            first_available_total=_int(row.get("first_available_total")),
            available_index=_float(row.get("available_index")),
            net_removed_since_first=_int(row.get("net_removed_since_first")),
            net_removed_since_previous=_int(row.get("net_removed_since_previous")),
            velocity_since_previous=_float(row.get("velocity_since_previous")),
            net_removed_6h=_int(row.get("net_removed_6h")),
            velocity_6h=_float(row.get("velocity_6h")),
            net_removed_24h=_int(row.get("net_removed_24h")),
            velocity_24h=_float(row.get("velocity_24h")),
            acceleration_6h_vs_24h=_float(row.get("acceleration_6h_vs_24h")),
            raw_snapshot_count=_int(row.get("raw_snapshot_count")),
            clean_snapshot_count=_int(row.get("clean_snapshot_count")),
            excluded_anomaly_count=_int(row.get("excluded_anomaly_count")),
            data_gap_detected=_bool(row.get("data_gap_detected")),
        )


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
