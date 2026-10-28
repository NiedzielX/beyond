"""Executable Trajectory Feature Contract v1.

This module turns the frozen research contract in
``ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`` into deterministic code.

It does not fit a model and does not access attendance outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Iterable

from .daily_trajectory_dataset import DailyTrajectoryRow
from .live_trajectory_feature_store import SnapshotRecord

CONTRACT_ID = "trajectory-feature-contract-v1"
MIN_SHARED_CLEAN_SNAPSHOTS = 4
MIN_SHARED_OBSERVATION_HOURS = 24.0

LANE_A_NUMERIC_FEATURES: tuple[str, ...] = (
    "days_to_event",
    "available_index",
    "available_share_of_capacity",
    "velocity_6h_pct_of_first_per_hour",
    "velocity_24h_pct_of_first_per_hour",
    "velocity_72h_pct_of_first_per_hour",
    "velocity_7d_pct_of_first_per_hour",
    "acceleration_6h_vs_24h",
    "acceleration_24h_vs_72h",
    "acceleration_72h_vs_7d",
    "snapshot_age_minutes",
    "clean_snapshot_count",
    "observation_window_hours",
    "max_visible_gap_hours",
    "structural_incumbent_p50",
    "structural_incumbent_p50_share_of_capacity",
)

LANE_A_QUALITY_FEATURES: tuple[str, ...] = (
    "feature_quality",
    "signal_readiness",
    "data_gap_detected",
    "release_activity_flag",
    "sector_coverage_change_flag",
    "unexplained_inventory_increase_flag",
)

LANE_B_SEQUENCE_FIELDS: tuple[str, ...] = (
    "hours_to_kickoff",
    "available_index",
    "available_share_of_capacity",
    "delta_hours_since_previous",
    "delta_available_index",
)

LANE_B_GLOBAL_FIELDS: tuple[str, ...] = (
    "days_to_event",
    "snapshot_age_minutes",
    "clean_snapshot_count",
    "observation_window_hours",
    "max_visible_gap_hours",
    "structural_incumbent_p50",
    "structural_incumbent_p50_share_of_capacity",
    "verified_capacity_available",
    "sequence_length",
)


@dataclass(frozen=True)
class SharedEligibility:
    eligible: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class SequenceStepV1:
    snapshot_id: int
    captured_at: datetime
    hours_to_kickoff: float
    available_index: float
    available_share_of_capacity: float | None
    delta_hours_since_previous: float | None
    delta_available_index: float | None

    def model_values(self) -> tuple[float | None, ...]:
        return (
            self.hours_to_kickoff,
            self.available_index,
            self.available_share_of_capacity,
            self.delta_hours_since_previous,
            self.delta_available_index,
        )


@dataclass(frozen=True)
class LaneBSequenceV1:
    contract_id: str
    as_of_at: datetime
    kickoff_at: datetime
    steps: tuple[SequenceStepV1, ...]
    first_available_total: int
    verified_capacity: int | None
    point_in_time_validated: bool = True
    target_future_points_used: bool = False

    @property
    def sequence_length(self) -> int:
        return len(self.steps)


class SequenceInputInsufficientError(ValueError):
    """Raised when a genuine sequence cannot be normalized safely."""


def shared_eligibility_v1(row: DailyTrajectoryRow) -> SharedEligibility:
    """Return the frozen shared Lane A/Lane B primary-cohort gate."""
    reasons: list[str] = []
    t = row.trajectory

    if not row.point_in_time_validated or not t.point_in_time_validated:
        reasons.append("PIT_NOT_VALIDATED")
    if row.target_future_points_used:
        reasons.append("TARGET_FUTURE_POINTS_USED")
    if row.days_to_event < 1 or row.days_to_event > 60:
        reasons.append("HORIZON_OUT_OF_RANGE")
    if row.structural_prior is None or not row.structural_prior_available:
        reasons.append("NO_STRUCTURAL_INCUMBENT")
    if t.clean_snapshot_count < MIN_SHARED_CLEAN_SNAPSHOTS:
        reasons.append("INSUFFICIENT_CLEAN_SNAPSHOTS")
    if t.observation_window_hours is None or t.observation_window_hours < MIN_SHARED_OBSERVATION_HOURS:
        reasons.append("INSUFFICIENT_OBSERVATION_WINDOW")
    if t.signal_readiness != "ready":
        reasons.append("SIGNAL_NOT_READY")
    if t.snapshot_captured_at is not None and t.snapshot_captured_at > row.as_of_at:
        reasons.append("FUTURE_SNAPSHOT")

    return SharedEligibility(eligible=not reasons, reasons=tuple(reasons))


def lane_a_features_v1(row: DailyTrajectoryRow) -> dict[str, float | int | bool | str | None]:
    """Build the exact Lane A scalar record from canonical daily features.

    Nullable values deliberately remain ``None``. Fold-local model preprocessing
    owns imputation, missing indicators, encoding and scaling.
    """
    t = row.trajectory
    prior = row.structural_prior
    p50 = float(prior.p50) if prior is not None else None
    capacity = _verified_capacity_from_row(row)

    values: dict[str, float | int | bool | str | None] = {
        "days_to_event": row.days_to_event,
        "available_index": t.available_index,
        "available_share_of_capacity": t.available_share_of_capacity,
        "velocity_6h_pct_of_first_per_hour": t.velocity_6h_pct_of_first_per_hour,
        "velocity_24h_pct_of_first_per_hour": t.velocity_24h_pct_of_first_per_hour,
        "velocity_72h_pct_of_first_per_hour": t.velocity_72h_pct_of_first_per_hour,
        "velocity_7d_pct_of_first_per_hour": t.velocity_7d_pct_of_first_per_hour,
        "acceleration_6h_vs_24h": t.acceleration_6h_vs_24h,
        "acceleration_24h_vs_72h": t.acceleration_24h_vs_72h,
        "acceleration_72h_vs_7d": t.acceleration_72h_vs_7d,
        "snapshot_age_minutes": t.snapshot_age_minutes,
        "clean_snapshot_count": t.clean_snapshot_count,
        "observation_window_hours": t.observation_window_hours,
        "max_visible_gap_hours": t.max_visible_gap_hours,
        "structural_incumbent_p50": p50,
        "structural_incumbent_p50_share_of_capacity": (
            p50 / capacity if p50 is not None and capacity is not None else None
        ),
        "feature_quality": t.feature_quality,
        "signal_readiness": t.signal_readiness,
        "data_gap_detected": t.data_gap_detected,
        "release_activity_flag": t.release_activity_flag,
        "sector_coverage_change_flag": t.sector_coverage_change_flag,
        "unexplained_inventory_increase_flag": t.unexplained_inventory_increase_flag,
    }
    expected = set(LANE_A_NUMERIC_FEATURES) | set(LANE_A_QUALITY_FEATURES)
    if set(values) != expected:
        raise AssertionError("Lane A feature contract drift")
    return values


def lane_b_global_features_v1(
    row: DailyTrajectoryRow,
    sequence: LaneBSequenceV1,
) -> dict[str, float | int | bool | None]:
    """Build the exact small global-context record for Lane B."""
    prior = row.structural_prior
    p50 = float(prior.p50) if prior is not None else None
    capacity = sequence.verified_capacity
    t = row.trajectory
    values: dict[str, float | int | bool | None] = {
        "days_to_event": row.days_to_event,
        "snapshot_age_minutes": t.snapshot_age_minutes,
        "clean_snapshot_count": t.clean_snapshot_count,
        "observation_window_hours": t.observation_window_hours,
        "max_visible_gap_hours": t.max_visible_gap_hours,
        "structural_incumbent_p50": p50,
        "structural_incumbent_p50_share_of_capacity": (
            p50 / capacity if p50 is not None and capacity is not None else None
        ),
        "verified_capacity_available": capacity is not None,
        "sequence_length": sequence.sequence_length,
    }
    if set(values) != set(LANE_B_GLOBAL_FIELDS):
        raise AssertionError("Lane B global feature contract drift")
    return values


def build_lane_b_sequence_v1(
    snapshots: Iterable[SnapshotRecord],
    *,
    as_of_at: datetime,
    kickoff_at: datetime,
    stadium_capacity: int | None = None,
) -> LaneBSequenceV1:
    """Build Lane B's genuine variable-length sequence.

    Rules are frozen by ``TRAJECTORY_FEATURE_CONTRACT_V1.md``:
    - visible and pre-kickoff observations only;
    - non-negative, non-null inventory only;
    - exact timestamp dedupe keeps highest snapshot id;
    - at most one genuine observation per integer hour-to-kickoff bucket, keeping
      the latest observation in that bucket;
    - no interpolation and no forward fill.
    """
    _require_aware("as_of_at", as_of_at)
    _require_aware("kickoff_at", kickoff_at)
    if as_of_at >= kickoff_at:
        raise ValueError("as_of_at must be before kickoff_at")
    if stadium_capacity is not None and stadium_capacity <= 0:
        raise ValueError("stadium_capacity must be positive")

    valid: list[SnapshotRecord] = []
    for snapshot in snapshots:
        _require_aware("snapshot.captured_at", snapshot.captured_at)
        if snapshot.captured_at > as_of_at or snapshot.captured_at >= kickoff_at:
            continue
        if snapshot.available_total is None or int(snapshot.available_total) < 0:
            continue
        valid.append(snapshot)

    by_timestamp: dict[datetime, SnapshotRecord] = {}
    for snapshot in sorted(valid, key=lambda r: (r.captured_at, r.snapshot_id)):
        existing = by_timestamp.get(snapshot.captured_at)
        if existing is None or snapshot.snapshot_id > existing.snapshot_id:
            by_timestamp[snapshot.captured_at] = snapshot

    # Capture cadence differs by source/event. Hourly compression keeps only
    # real observations while reducing the chance that scraper frequency itself
    # becomes a learnable shortcut.
    by_hour_to_kickoff: dict[int, SnapshotRecord] = {}
    for snapshot in sorted(by_timestamp.values(), key=lambda r: (r.captured_at, r.snapshot_id)):
        hours = (kickoff_at - snapshot.captured_at).total_seconds() / 3600.0
        bucket = math.floor(hours)
        existing = by_hour_to_kickoff.get(bucket)
        if existing is None or (snapshot.captured_at, snapshot.snapshot_id) > (
            existing.captured_at,
            existing.snapshot_id,
        ):
            by_hour_to_kickoff[bucket] = snapshot

    clean = sorted(by_hour_to_kickoff.values(), key=lambda r: (r.captured_at, r.snapshot_id))
    if not clean:
        raise SequenceInputInsufficientError("no genuine visible sequence observations")

    first_available = int(clean[0].available_total or 0)
    if first_available <= 0:
        raise SequenceInputInsufficientError("first genuine available_total must be positive")

    steps: list[SequenceStepV1] = []
    previous: SnapshotRecord | None = None
    previous_index: float | None = None
    for snapshot in clean:
        available = int(snapshot.available_total or 0)
        available_index = available / first_available
        hours_to_kickoff = (kickoff_at - snapshot.captured_at).total_seconds() / 3600.0
        capacity_share = available / stadium_capacity if stadium_capacity else None
        delta_hours = None
        delta_index = None
        if previous is not None and previous_index is not None:
            delta_hours = (snapshot.captured_at - previous.captured_at).total_seconds() / 3600.0
            delta_index = available_index - previous_index
        steps.append(
            SequenceStepV1(
                snapshot_id=snapshot.snapshot_id,
                captured_at=snapshot.captured_at,
                hours_to_kickoff=hours_to_kickoff,
                available_index=available_index,
                available_share_of_capacity=capacity_share,
                delta_hours_since_previous=delta_hours,
                delta_available_index=delta_index,
            )
        )
        previous = snapshot
        previous_index = available_index

    return LaneBSequenceV1(
        contract_id=CONTRACT_ID,
        as_of_at=as_of_at,
        kickoff_at=kickoff_at,
        steps=tuple(steps),
        first_available_total=first_available,
        verified_capacity=stadium_capacity,
    )


def _verified_capacity_from_row(row: DailyTrajectoryRow) -> int | None:
    prior = row.structural_prior
    if prior is None or prior.stadium_capacity is None:
        return None
    value = int(prior.stadium_capacity)
    return value if value > 0 else None


def _require_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
