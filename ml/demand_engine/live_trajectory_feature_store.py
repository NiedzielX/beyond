"""Canonical point-in-time feature builder for Beyond live ticketing trajectories.

The builder is deliberately independent from Supabase. Production adapters may
read the same raw snapshot/sector records from Postgres, while tests and offline
replays can use in-memory records. Every feature is derived only from records
visible at ``as_of``.

Public inventory movement is a demand proxy, not confirmed paid ticket sales.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Literal

from .contracts import SignalReadiness

FEATURE_VERSION = "live-trajectory-v1"
INVENTORY_INTERPRETATION = "demand_proxy_not_confirmed_sales"
DATA_GAP_HOURS = 12.0
MIN_READY_SNAPSHOTS = 4
MIN_READY_OBSERVATION_HOURS = 24.0

# One-sided checkpoint windows: the snapshot must be at or before the business
# checkpoint. This prevents a T-30 feature row from silently using T-29 data.
CHECKPOINTS: tuple[tuple[str, float, float], ...] = (
    ("T-30", 30.0 * 24.0, 3.0 * 24.0),
    ("T-14", 14.0 * 24.0, 2.0 * 24.0),
    ("T-7", 7.0 * 24.0, 1.0 * 24.0),
    ("T-3", 3.0 * 24.0, 18.0),
    ("T-1", 1.0 * 24.0, 12.0),
)

WINDOWS_HOURS: tuple[int, ...] = (6, 24, 72, 168)


@dataclass(frozen=True)
class SnapshotRecord:
    snapshot_id: int
    captured_at: datetime
    available_total: int | None
    sector_count: int | None = None


@dataclass(frozen=True)
class SectorInventoryRecord:
    snapshot_id: int
    sector: str
    available: int


@dataclass(frozen=True)
class WindowMetric:
    window_hours: int
    anchor_snapshot_id: int | None = None
    anchor_captured_at: datetime | None = None
    elapsed_hours: float | None = None
    net_removed: int | None = None
    velocity_per_hour: float | None = None
    velocity_pct_of_first_per_hour: float | None = None
    velocity_pct_of_capacity_per_hour: float | None = None


FeatureQuality = Literal[
    "no_usable_snapshot",
    "single_snapshot_only",
    "raw_total_only",
    "sector_matched_plus_raw",
]


@dataclass(frozen=True)
class LiveTrajectoryFeatures:
    feature_version: str
    signal_readiness: SignalReadiness
    feature_quality: FeatureQuality
    inventory_interpretation: str
    point_in_time_validated: bool

    snapshot_id: int | None = None
    snapshot_captured_at: datetime | None = None
    as_of: datetime | None = None
    kickoff_at: datetime | None = None
    hours_to_kickoff: float | None = None
    days_to_kickoff: float | None = None
    snapshot_age_minutes: float | None = None

    checkpoint_label: str | None = None
    checkpoint_distance_hours: float | None = None
    checkpoint_ready: bool = False

    available_total: int | None = None
    first_available_total: int | None = None
    available_index: float | None = None
    available_share_of_capacity: float | None = None
    public_seat_map_size: int | None = None
    available_pct_of_public_seat_map: float | None = None

    net_removed_since_first: int | None = None
    net_removed_since_previous: int | None = None
    velocity_since_previous: float | None = None

    net_removed_6h: int | None = None
    velocity_6h: float | None = None
    net_removed_24h: int | None = None
    velocity_24h: float | None = None
    net_removed_72h: int | None = None
    velocity_72h: float | None = None
    net_removed_7d: int | None = None
    velocity_7d: float | None = None

    velocity_6h_pct_of_first_per_hour: float | None = None
    velocity_24h_pct_of_first_per_hour: float | None = None
    velocity_72h_pct_of_first_per_hour: float | None = None
    velocity_7d_pct_of_first_per_hour: float | None = None

    velocity_6h_pct_of_capacity_per_hour: float | None = None
    velocity_24h_pct_of_capacity_per_hour: float | None = None
    velocity_72h_pct_of_capacity_per_hour: float | None = None
    velocity_7d_pct_of_capacity_per_hour: float | None = None

    acceleration_6h_vs_24h: float | None = None
    acceleration_24h_vs_72h: float | None = None
    acceleration_72h_vs_7d: float | None = None

    matched_sector_count: int | None = None
    entered_sector_count: int | None = None
    left_sector_count: int | None = None
    matched_absorption: int | None = None
    matched_release: int | None = None
    coverage_inventory_effect: int | None = None
    sector_coverage_change_flag: bool | None = None
    release_activity_flag: bool | None = None
    unexplained_inventory_increase_flag: bool | None = None

    raw_snapshot_count: int = 0
    clean_snapshot_count: int = 0
    excluded_anomaly_count: int = 0
    duplicate_timestamp_count: int = 0
    invalid_snapshot_count: int = 0
    observation_window_hours: float | None = None
    max_visible_gap_hours: float | None = None
    data_gap_detected: bool | None = None


def build_live_trajectory_features(
    snapshots: Iterable[SnapshotRecord],
    sectors: Iterable[SectorInventoryRecord],
    *,
    as_of: datetime,
    kickoff_at: datetime,
    stadium_capacity: int | None = None,
    public_seat_map_size: int | None = None,
) -> LiveTrajectoryFeatures:
    """Build a leakage-safe feature row from snapshot history visible at ``as_of``.

    Invalid negative inventory rows and duplicate timestamps are excluded from
    calculations and counted as anomalies. When multiple rows share a timestamp,
    the highest snapshot id wins deterministically.
    """

    _require_aware("as_of", as_of)
    _require_aware("kickoff_at", kickoff_at)
    if kickoff_at <= as_of:
        raise ValueError("as_of must be before kickoff_at")
    if stadium_capacity is not None and stadium_capacity <= 0:
        raise ValueError("stadium_capacity must be positive")
    if public_seat_map_size is not None and public_seat_map_size <= 0:
        raise ValueError("public_seat_map_size must be positive")

    visible = [s for s in snapshots if s.captured_at <= as_of]
    raw_snapshot_count = len(visible)
    invalid_snapshot_count = sum(
        1 for s in visible if s.available_total is None or int(s.available_total) < 0
    )

    valid = [
        s for s in visible if s.available_total is not None and int(s.available_total) >= 0
    ]
    deduped_by_time: dict[datetime, SnapshotRecord] = {}
    for snapshot in sorted(valid, key=lambda s: (s.captured_at, s.snapshot_id)):
        _require_aware("snapshot.captured_at", snapshot.captured_at)
        deduped_by_time[snapshot.captured_at] = snapshot
    duplicate_timestamp_count = len(valid) - len(deduped_by_time)
    clean = sorted(deduped_by_time.values(), key=lambda s: (s.captured_at, s.snapshot_id))
    excluded_anomaly_count = invalid_snapshot_count + duplicate_timestamp_count

    if not clean:
        hours_to_kickoff = _hours(kickoff_at - as_of)
        checkpoint_label, checkpoint_distance, checkpoint_ready = _checkpoint(hours_to_kickoff)
        return LiveTrajectoryFeatures(
            feature_version=FEATURE_VERSION,
            signal_readiness="not_ready",
            feature_quality="no_usable_snapshot",
            inventory_interpretation=INVENTORY_INTERPRETATION,
            point_in_time_validated=True,
            as_of=as_of,
            kickoff_at=kickoff_at,
            hours_to_kickoff=hours_to_kickoff,
            days_to_kickoff=hours_to_kickoff / 24.0,
            checkpoint_label=checkpoint_label,
            checkpoint_distance_hours=checkpoint_distance,
            checkpoint_ready=checkpoint_ready,
            public_seat_map_size=public_seat_map_size,
            raw_snapshot_count=raw_snapshot_count,
            clean_snapshot_count=0,
            excluded_anomaly_count=excluded_anomaly_count,
            duplicate_timestamp_count=duplicate_timestamp_count,
            invalid_snapshot_count=invalid_snapshot_count,
        )

    first = clean[0]
    current = clean[-1]
    previous = clean[-2] if len(clean) >= 2 else None
    first_available = int(first.available_total or 0)
    current_available = int(current.available_total or 0)

    hours_to_kickoff = _hours(kickoff_at - as_of)
    checkpoint_label, checkpoint_distance, checkpoint_ready = _checkpoint(hours_to_kickoff)
    observation_window_hours = _hours(current.captured_at - first.captured_at)
    snapshot_age_minutes = (as_of - current.captured_at).total_seconds() / 60.0

    max_gap = _max_gap_hours(clean)
    data_gap_detected = bool(
        (max_gap is not None and max_gap > DATA_GAP_HOURS)
        or snapshot_age_minutes > DATA_GAP_HOURS * 60.0
    )

    window_metrics = {
        hours: _window_metric(
            clean,
            current,
            hours,
            first_available_total=first_available,
            stadium_capacity=stadium_capacity,
        )
        for hours in WINDOWS_HOURS
    }

    sector_metrics = _sector_transition_metrics(previous, current, sectors)
    feature_quality: FeatureQuality
    if len(clean) == 1:
        feature_quality = "single_snapshot_only"
    elif sector_metrics["sector_data_available"]:
        feature_quality = "sector_matched_plus_raw"
    else:
        feature_quality = "raw_total_only"

    net_removed_previous: int | None = None
    velocity_previous: float | None = None
    if previous is not None:
        elapsed = _hours(current.captured_at - previous.captured_at)
        if elapsed > 0:
            net_removed_previous = int(previous.available_total or 0) - current_available
            velocity_previous = net_removed_previous / elapsed

    unexplained_increase = None
    if previous is not None:
        increase = current_available - int(previous.available_total or 0)
        material_threshold = max(100, round(first_available * 0.05)) if first_available else 100
        unexplained_increase = bool(
            increase >= material_threshold
            and not sector_metrics["release_activity_flag"]
            and not sector_metrics["sector_coverage_change_flag"]
        )

    readiness = _signal_readiness(
        clean_snapshot_count=len(clean),
        observation_window_hours=observation_window_hours,
        data_gap_detected=data_gap_detected,
        unexplained_inventory_increase_flag=bool(unexplained_increase),
    )

    v6 = window_metrics[6].velocity_per_hour
    v24 = window_metrics[24].velocity_per_hour
    v72 = window_metrics[72].velocity_per_hour
    v7d = window_metrics[168].velocity_per_hour

    return LiveTrajectoryFeatures(
        feature_version=FEATURE_VERSION,
        signal_readiness=readiness,
        feature_quality=feature_quality,
        inventory_interpretation=INVENTORY_INTERPRETATION,
        point_in_time_validated=True,
        snapshot_id=current.snapshot_id,
        snapshot_captured_at=current.captured_at,
        as_of=as_of,
        kickoff_at=kickoff_at,
        hours_to_kickoff=hours_to_kickoff,
        days_to_kickoff=hours_to_kickoff / 24.0,
        snapshot_age_minutes=snapshot_age_minutes,
        checkpoint_label=checkpoint_label,
        checkpoint_distance_hours=checkpoint_distance,
        checkpoint_ready=checkpoint_ready,
        available_total=current_available,
        first_available_total=first_available,
        available_index=_ratio(current_available, first_available),
        available_share_of_capacity=_ratio(current_available, stadium_capacity),
        public_seat_map_size=public_seat_map_size,
        available_pct_of_public_seat_map=(
            _ratio(current_available, public_seat_map_size) * 100.0
            if public_seat_map_size else None
        ),
        net_removed_since_first=first_available - current_available,
        net_removed_since_previous=net_removed_previous,
        velocity_since_previous=velocity_previous,
        net_removed_6h=window_metrics[6].net_removed,
        velocity_6h=v6,
        net_removed_24h=window_metrics[24].net_removed,
        velocity_24h=v24,
        net_removed_72h=window_metrics[72].net_removed,
        velocity_72h=v72,
        net_removed_7d=window_metrics[168].net_removed,
        velocity_7d=v7d,
        velocity_6h_pct_of_first_per_hour=window_metrics[6].velocity_pct_of_first_per_hour,
        velocity_24h_pct_of_first_per_hour=window_metrics[24].velocity_pct_of_first_per_hour,
        velocity_72h_pct_of_first_per_hour=window_metrics[72].velocity_pct_of_first_per_hour,
        velocity_7d_pct_of_first_per_hour=window_metrics[168].velocity_pct_of_first_per_hour,
        velocity_6h_pct_of_capacity_per_hour=window_metrics[6].velocity_pct_of_capacity_per_hour,
        velocity_24h_pct_of_capacity_per_hour=window_metrics[24].velocity_pct_of_capacity_per_hour,
        velocity_72h_pct_of_capacity_per_hour=window_metrics[72].velocity_pct_of_capacity_per_hour,
        velocity_7d_pct_of_capacity_per_hour=window_metrics[168].velocity_pct_of_capacity_per_hour,
        acceleration_6h_vs_24h=_difference(v6, v24),
        acceleration_24h_vs_72h=_difference(v24, v72),
        acceleration_72h_vs_7d=_difference(v72, v7d),
        matched_sector_count=sector_metrics["matched_sector_count"],
        entered_sector_count=sector_metrics["entered_sector_count"],
        left_sector_count=sector_metrics["left_sector_count"],
        matched_absorption=sector_metrics["matched_absorption"],
        matched_release=sector_metrics["matched_release"],
        coverage_inventory_effect=sector_metrics["coverage_inventory_effect"],
        sector_coverage_change_flag=sector_metrics["sector_coverage_change_flag"],
        release_activity_flag=sector_metrics["release_activity_flag"],
        unexplained_inventory_increase_flag=unexplained_increase,
        raw_snapshot_count=raw_snapshot_count,
        clean_snapshot_count=len(clean),
        excluded_anomaly_count=excluded_anomaly_count,
        duplicate_timestamp_count=duplicate_timestamp_count,
        invalid_snapshot_count=invalid_snapshot_count,
        observation_window_hours=observation_window_hours,
        max_visible_gap_hours=max_gap,
        data_gap_detected=data_gap_detected,
    )


def _window_metric(
    clean: list[SnapshotRecord],
    current: SnapshotRecord,
    window_hours: int,
    *,
    first_available_total: int,
    stadium_capacity: int | None,
) -> WindowMetric:
    cutoff = current.captured_at - timedelta(hours=window_hours)
    anchors = [s for s in clean if s.captured_at <= cutoff]
    if not anchors:
        return WindowMetric(window_hours=window_hours)

    anchor = anchors[-1]
    # A stale anchor turns a nominal 6h feature into a 20h feature. Reject it
    # when it lies too far before the requested cutoff.
    anchor_lag_hours = _hours(cutoff - anchor.captured_at)
    tolerance = max(3.0, window_hours * 0.25)
    if anchor_lag_hours > tolerance:
        return WindowMetric(window_hours=window_hours)

    elapsed = _hours(current.captured_at - anchor.captured_at)
    if elapsed <= 0:
        return WindowMetric(window_hours=window_hours)

    net_removed = int(anchor.available_total or 0) - int(current.available_total or 0)
    velocity = net_removed / elapsed
    return WindowMetric(
        window_hours=window_hours,
        anchor_snapshot_id=anchor.snapshot_id,
        anchor_captured_at=anchor.captured_at,
        elapsed_hours=elapsed,
        net_removed=net_removed,
        velocity_per_hour=velocity,
        velocity_pct_of_first_per_hour=(
            velocity / first_available_total * 100.0 if first_available_total > 0 else None
        ),
        velocity_pct_of_capacity_per_hour=(
            velocity / stadium_capacity * 100.0 if stadium_capacity else None
        ),
    )


def _sector_transition_metrics(
    previous: SnapshotRecord | None,
    current: SnapshotRecord,
    sectors: Iterable[SectorInventoryRecord],
) -> dict[str, int | bool | None]:
    if previous is None:
        return _empty_sector_metrics()

    by_snapshot: dict[int, dict[str, int]] = {}
    for row in sectors:
        if row.available < 0:
            continue
        by_snapshot.setdefault(row.snapshot_id, {})[row.sector] = int(row.available)

    prev = by_snapshot.get(previous.snapshot_id)
    cur = by_snapshot.get(current.snapshot_id)
    if not prev or not cur:
        return _empty_sector_metrics()

    prev_keys = set(prev)
    cur_keys = set(cur)
    matched = prev_keys & cur_keys
    entered = cur_keys - prev_keys
    left = prev_keys - cur_keys

    matched_absorption = sum(max(prev[key] - cur[key], 0) for key in matched)
    matched_release = sum(max(cur[key] - prev[key], 0) for key in matched)
    entered_available = sum(cur[key] for key in entered)
    left_available = sum(prev[key] for key in left)
    coverage_effect = entered_available - left_available

    return {
        "sector_data_available": True,
        "matched_sector_count": len(matched),
        "entered_sector_count": len(entered),
        "left_sector_count": len(left),
        "matched_absorption": matched_absorption,
        "matched_release": matched_release,
        "coverage_inventory_effect": coverage_effect,
        "sector_coverage_change_flag": bool(entered or left),
        "release_activity_flag": bool(matched_release > 0 or entered_available > 0),
    }


def _empty_sector_metrics() -> dict[str, int | bool | None]:
    return {
        "sector_data_available": False,
        "matched_sector_count": None,
        "entered_sector_count": None,
        "left_sector_count": None,
        "matched_absorption": None,
        "matched_release": None,
        "coverage_inventory_effect": None,
        "sector_coverage_change_flag": None,
        "release_activity_flag": None,
    }


def _signal_readiness(
    *,
    clean_snapshot_count: int,
    observation_window_hours: float,
    data_gap_detected: bool,
    unexplained_inventory_increase_flag: bool,
) -> SignalReadiness:
    if clean_snapshot_count < 2:
        return "not_ready"
    if (
        clean_snapshot_count < MIN_READY_SNAPSHOTS
        or observation_window_hours < MIN_READY_OBSERVATION_HOURS
        or data_gap_detected
        or unexplained_inventory_increase_flag
    ):
        return "partial"
    return "ready"


def _checkpoint(hours_to_kickoff: float) -> tuple[str | None, float | None, bool]:
    for label, target, tolerance in CHECKPOINTS:
        distance = hours_to_kickoff - target
        if 0.0 <= distance <= tolerance:
            return label, distance, True
    return None, None, False


def _max_gap_hours(clean: list[SnapshotRecord]) -> float | None:
    if len(clean) < 2:
        return None
    return max(_hours(b.captured_at - a.captured_at) for a, b in zip(clean, clean[1:]))


def _difference(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def _ratio(numerator: int, denominator: int | None) -> float | None:
    if not denominator:
        return None
    return numerator / denominator


def _hours(delta: timedelta) -> float:
    return delta.total_seconds() / 3600.0


def _require_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
