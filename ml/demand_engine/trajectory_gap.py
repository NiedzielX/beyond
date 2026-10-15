"""Leakage-safe descriptive expected-trajectory / trajectory-gap contract.

The initial implementation deliberately stays in normalized public-inventory
space. Public seat-map inventory is a demand proxy, not paid sales, and is not
converted 1:1 into final attendance. A genuine Structural Prior is required as
the final-demand anchor, but the descriptive reference curve comes from other
point-in-time-valid live trajectories at the same canonical horizon.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Iterable, Literal

import numpy as np

from .live_trajectory_feature_store import LiveTrajectoryFeatures

TRAJECTORY_GAP_VERSION = "trajectory-gap-v1"
REFERENCE_MODE = "empirical_inventory_progress_by_horizon_v1"
PRIOR_MAPPING_MODE = "anchor_only_no_inventory_to_attendance_conversion"
MIN_REFERENCE_EVENTS = 3
MIN_REFERENCE_CLUBS = 2

TrajectoryStatus = Literal[
    "UNDERPERFORMING",
    "ON_TRACK",
    "OUTPERFORMING",
    "INSUFFICIENT_SIGNAL",
]
Confidence = Literal["LOW", "MEDIUM", "HIGH", "NONE"]


@dataclass(frozen=True)
class StructuralPriorAnchor:
    status: str
    source_prior_id: int | None
    horizon: str | None
    p50: float | None
    stadium_capacity: int | None
    expected_occupancy: float | None
    point_in_time_validated: bool | None


@dataclass(frozen=True)
class TrajectoryReferenceRow:
    ticket_event_id: int
    club_slug: str
    horizon: str
    as_of_at: datetime
    feature_version: str
    training_eligible: bool
    point_in_time_validated: bool
    signal_readiness: str
    available_index: float | None
    velocity_24h_pct_of_first_per_hour: float | None = None
    velocity_6h_pct_of_first_per_hour: float | None = None


@dataclass(frozen=True)
class TrajectoryGapResult:
    version: str
    reference_mode: str
    prior_mapping_mode: str
    ticket_event_id: int
    as_of_at: datetime
    structural_prior_id: int | None
    structural_prior_horizon: str | None
    structural_prior_p50: float | None
    reference_horizon: str | None
    reference_event_count: int
    reference_club_count: int
    observed_progress: float | None
    expected_progress: float | None
    expected_progress_q25: float | None
    expected_progress_q75: float | None
    level_gap: float | None
    observed_velocity_24h: float | None
    expected_velocity_24h: float | None
    velocity_gap: float | None
    observed_acceleration_6h_vs_24h: float | None
    expected_acceleration_6h_vs_24h: float | None
    acceleration_gap: float | None
    status: TrajectoryStatus
    confidence: Confidence
    reason_code: str
    signal_readiness: str
    feature_quality: str
    point_in_time_validated: bool


def evaluate_trajectory_gap(
    *,
    ticket_event_id: int,
    club_slug: str,
    live: LiveTrajectoryFeatures,
    prior: StructuralPriorAnchor,
    references: Iterable[TrajectoryReferenceRow],
    min_reference_events: int = MIN_REFERENCE_EVENTS,
    min_reference_clubs: int = MIN_REFERENCE_CLUBS,
) -> TrajectoryGapResult:
    """Compare current normalized inventory progress with a PIT reference band."""
    if live.as_of is None:
        raise ValueError("live.as_of is required")

    common = dict(
        version=TRAJECTORY_GAP_VERSION,
        reference_mode=REFERENCE_MODE,
        prior_mapping_mode=PRIOR_MAPPING_MODE,
        ticket_event_id=int(ticket_event_id),
        as_of_at=live.as_of,
        structural_prior_id=prior.source_prior_id,
        structural_prior_horizon=prior.horizon,
        structural_prior_p50=prior.p50,
        signal_readiness=live.signal_readiness,
        feature_quality=live.feature_quality,
    )

    observed_progress = (
        1.0 - float(live.available_index)
        if live.available_index is not None
        else None
    )
    observed_v24 = live.velocity_24h_pct_of_first_per_hour
    observed_acc = _difference(
        live.velocity_6h_pct_of_first_per_hour,
        live.velocity_24h_pct_of_first_per_hour,
    )

    if prior.status != "ready" or not prior.point_in_time_validated or prior.p50 is None:
        return _insufficient(
            common,
            observed_progress=observed_progress,
            observed_v24=observed_v24,
            observed_acc=observed_acc,
            reason="structural_prior_not_ready",
            point_in_time_validated=bool(live.point_in_time_validated),
        )
    if not live.point_in_time_validated:
        return _insufficient(
            common,
            observed_progress=observed_progress,
            observed_v24=observed_v24,
            observed_acc=observed_acc,
            reason="live_feature_not_pit_validated",
            point_in_time_validated=False,
        )
    if live.signal_readiness != "ready":
        return _insufficient(
            common,
            observed_progress=observed_progress,
            observed_v24=observed_v24,
            observed_acc=observed_acc,
            reason=f"live_signal_{live.signal_readiness}",
            point_in_time_validated=True,
        )
    if not live.checkpoint_ready or live.checkpoint_label is None:
        return _insufficient(
            common,
            observed_progress=observed_progress,
            observed_v24=observed_v24,
            observed_acc=observed_acc,
            reason="outside_reference_checkpoint_window",
            point_in_time_validated=True,
        )
    if live.available_index is None:
        return _insufficient(
            common,
            observed_progress=None,
            observed_v24=observed_v24,
            observed_acc=observed_acc,
            reason="missing_available_index",
            point_in_time_validated=True,
        )

    horizon = live.checkpoint_label
    eligible = [
        row
        for row in references
        if row.ticket_event_id != ticket_event_id
        and row.horizon == horizon
        and row.feature_version == live.feature_version
        and row.training_eligible
        and row.point_in_time_validated
        and row.signal_readiness == "ready"
        and row.available_index is not None
        and row.as_of_at <= live.as_of
    ]
    event_count = len({row.ticket_event_id for row in eligible})
    club_count = len({row.club_slug for row in eligible})
    if event_count < min_reference_events or club_count < min_reference_clubs:
        return _insufficient(
            common,
            observed_progress=observed_progress,
            observed_v24=observed_v24,
            observed_acc=observed_acc,
            reason="insufficient_reference_pool",
            point_in_time_validated=True,
            reference_horizon=horizon,
            reference_event_count=event_count,
            reference_club_count=club_count,
        )

    progress = np.asarray([1.0 - float(row.available_index) for row in eligible], dtype=float)
    expected = float(np.median(progress))
    q25 = float(np.quantile(progress, 0.25))
    q75 = float(np.quantile(progress, 0.75))
    level_gap = float(observed_progress - expected)

    reference_v24 = [
        float(row.velocity_24h_pct_of_first_per_hour)
        for row in eligible
        if row.velocity_24h_pct_of_first_per_hour is not None
    ]
    expected_v24 = float(median(reference_v24)) if reference_v24 else None
    velocity_gap = _difference(observed_v24, expected_v24)

    reference_acc = [
        acc
        for row in eligible
        if (acc := _difference(
            row.velocity_6h_pct_of_first_per_hour,
            row.velocity_24h_pct_of_first_per_hour,
        )) is not None
    ]
    expected_acc = float(median(reference_acc)) if reference_acc else None
    acceleration_gap = _difference(observed_acc, expected_acc)

    if observed_progress < q25:
        status: TrajectoryStatus = "UNDERPERFORMING"
        reason = "progress_below_reference_iqr"
    elif observed_progress > q75:
        status = "OUTPERFORMING"
        reason = "progress_above_reference_iqr"
    else:
        status = "ON_TRACK"
        reason = "progress_within_reference_iqr"

    confidence: Confidence
    if event_count >= 10 and club_count >= 5:
        confidence = "HIGH"
    elif event_count >= 5 and club_count >= 3:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return TrajectoryGapResult(
        **common,
        reference_horizon=horizon,
        reference_event_count=event_count,
        reference_club_count=club_count,
        observed_progress=observed_progress,
        expected_progress=expected,
        expected_progress_q25=q25,
        expected_progress_q75=q75,
        level_gap=level_gap,
        observed_velocity_24h=observed_v24,
        expected_velocity_24h=expected_v24,
        velocity_gap=velocity_gap,
        observed_acceleration_6h_vs_24h=observed_acc,
        expected_acceleration_6h_vs_24h=expected_acc,
        acceleration_gap=acceleration_gap,
        status=status,
        confidence=confidence,
        reason_code=reason,
        point_in_time_validated=True,
    )


def _insufficient(
    common: dict,
    *,
    observed_progress: float | None,
    observed_v24: float | None,
    observed_acc: float | None,
    reason: str,
    point_in_time_validated: bool,
    reference_horizon: str | None = None,
    reference_event_count: int = 0,
    reference_club_count: int = 0,
) -> TrajectoryGapResult:
    return TrajectoryGapResult(
        **common,
        reference_horizon=reference_horizon,
        reference_event_count=reference_event_count,
        reference_club_count=reference_club_count,
        observed_progress=observed_progress,
        expected_progress=None,
        expected_progress_q25=None,
        expected_progress_q75=None,
        level_gap=None,
        observed_velocity_24h=observed_v24,
        expected_velocity_24h=None,
        velocity_gap=None,
        observed_acceleration_6h_vs_24h=observed_acc,
        expected_acceleration_6h_vs_24h=None,
        acceleration_gap=None,
        status="INSUFFICIENT_SIGNAL",
        confidence="NONE",
        reason_code=reason,
        point_in_time_validated=point_in_time_validated,
    )


def _difference(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)
