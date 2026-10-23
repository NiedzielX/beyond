#!/usr/bin/env python3
"""P9 booking-curve / trajectory-shape primitives v1.

This module intentionally does not fit an attendance model. It creates a
point-in-time-safe normalized representation of the public-inventory path and a
simple auditable historical-similarity/pickup estimate.

Public inventory is a demand proxy, not confirmed paid sales.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import numpy as np

VERSION = "p9-booking-curve-v1"
INVENTORY_INTERPRETATION = "demand_proxy_not_confirmed_sales"
CANONICAL_HOURS = (168.0, 144.0, 120.0, 96.0, 72.0, 60.0, 48.0, 36.0, 24.0, 18.0, 12.0, 6.0)
MIN_OVERLAP_POINTS = 3
DEFAULT_NEIGHBORS = 5
# Reuse the canonical live-trajectory quality ceiling. We do not interpolate a
# canonical curve point between raw observations separated by a larger gap.
MAX_INTERPOLATION_GAP_HOURS = 12.0


@dataclass(frozen=True)
class CurveObservation:
    snapshot_id: int
    captured_at: datetime
    available_total: int


@dataclass(frozen=True)
class NormalizedCurve:
    version: str
    ticket_event_id: int
    as_of_at: datetime
    kickoff_at: datetime
    first_visible_available: int
    inventory_interpretation: str
    point_in_time_validated: bool
    points: tuple[tuple[float, float | None], ...]

    def as_dict(self) -> dict[float, float | None]:
        return dict(self.points)


@dataclass(frozen=True)
class HistoricalCurveReference:
    ticket_event_id: int
    club_slug: str
    completed_at: datetime
    curve: NormalizedCurve


@dataclass(frozen=True)
class CurveNeighbor:
    ticket_event_id: int
    club_slug: str
    distance: float
    overlap_points: int
    remaining_pickup_share: float


@dataclass(frozen=True)
class PickupEstimate:
    version: str
    ticket_event_id: int
    as_of_at: datetime
    observed_hours_to_kickoff: float
    reference_event_count: int
    reference_club_count: int
    neighbor_count: int
    median_distance: float | None
    median_remaining_pickup_share: float | None
    pickup_q25: float | None
    pickup_q75: float | None
    neighbors: tuple[CurveNeighbor, ...]
    point_in_time_validated: bool
    target_future_points_used: bool


def build_normalized_curve(
    observations: Iterable[CurveObservation],
    *,
    ticket_event_id: int,
    as_of_at: datetime,
    kickoff_at: datetime,
    canonical_hours: tuple[float, ...] = CANONICAL_HOURS,
) -> NormalizedCurve:
    """Build a curve using only snapshots visible at ``as_of_at``.

    Canonical points later than the current cutoff remain missing. Linear
    interpolation is allowed only between two already-visible snapshots whose
    bracket gap is within the canonical 12h trajectory quality ceiling.
    """
    _require_aware(as_of_at, "as_of_at")
    _require_aware(kickoff_at, "kickoff_at")
    if not as_of_at < kickoff_at:
        raise ValueError("as_of_at must be before kickoff_at")

    visible = []
    for obs in observations:
        _require_aware(obs.captured_at, "observation.captured_at")
        if obs.available_total < 0:
            raise ValueError("available_total must be non-negative")
        if obs.captured_at <= as_of_at:
            hours = (kickoff_at - obs.captured_at).total_seconds() / 3600.0
            if hours > 0:
                visible.append((hours, int(obs.snapshot_id), int(obs.available_total)))
    if not visible:
        raise ValueError("no visible pre-kickoff observations")

    by_hours: dict[float, tuple[int, int]] = {}
    for hours, snapshot_id, available in visible:
        existing = by_hours.get(hours)
        if existing is None or snapshot_id > existing[0]:
            by_hours[hours] = (snapshot_id, available)
    clean = sorted(
        [(hours, sid, available) for hours, (sid, available) in by_hours.items()],
        key=lambda row: -row[0],
    )
    first_available = clean[0][2]
    if first_available <= 0:
        raise ValueError("first visible inventory must be positive for normalization")

    current_h = (kickoff_at - as_of_at).total_seconds() / 3600.0
    points: list[tuple[float, float | None]] = []
    for canonical_h in canonical_hours:
        if canonical_h < current_h - 1e-9:
            points.append((float(canonical_h), None))
            continue
        value = _interpolate_visible(clean, float(canonical_h))
        points.append((float(canonical_h), None if value is None else float(value / first_available)))

    return NormalizedCurve(
        version=VERSION,
        ticket_event_id=int(ticket_event_id),
        as_of_at=as_of_at,
        kickoff_at=kickoff_at,
        first_visible_available=first_available,
        inventory_interpretation=INVENTORY_INTERPRETATION,
        point_in_time_validated=True,
        points=tuple(points),
    )


def curve_distance(
    target: NormalizedCurve,
    reference: NormalizedCurve,
    *,
    min_overlap_points: int = MIN_OVERLAP_POINTS,
) -> tuple[float, int] | None:
    """Weighted L1 distance on target-observed canonical points only."""
    target_map = target.as_dict()
    ref_map = reference.as_dict()
    shared = [
        h for h, target_value in target_map.items()
        if target_value is not None and ref_map.get(h) is not None
    ]
    if len(shared) < min_overlap_points:
        return None
    raw_weights = np.asarray([1.0 / max(h, 6.0) for h in shared], dtype=float)
    weights = raw_weights / raw_weights.sum()
    diffs = np.asarray([
        abs(float(target_map[h]) - float(ref_map[h])) for h in shared
    ], dtype=float)
    return float(np.sum(weights * diffs)), len(shared)


def estimate_historical_pickup(
    target: NormalizedCurve,
    references: Iterable[HistoricalCurveReference],
    *,
    neighbors: int = DEFAULT_NEIGHBORS,
    min_overlap_points: int = MIN_OVERLAP_POINTS,
) -> PickupEstimate:
    """Estimate remaining normalized inventory pickup from completed prior curves.

    Reference events must have completed by target ``as_of_at``. The target's
    future path is never read. Historical reference future points may be used to
    calculate their realized remaining pickup because they are already completed
    prior events.
    """
    if neighbors < 1:
        raise ValueError("neighbors must be >=1")
    current_h = (target.kickoff_at - target.as_of_at).total_seconds() / 3600.0
    candidates: list[CurveNeighbor] = []
    target_map = target.as_dict()
    target_observed = [h for h, value in target_map.items() if value is not None]
    if not target_observed:
        raise ValueError("target has no observed canonical points")
    cutoff_h = min(target_observed)

    for reference in references:
        if reference.ticket_event_id == target.ticket_event_id:
            continue
        _require_aware(reference.completed_at, "reference.completed_at")
        if reference.completed_at > target.as_of_at:
            continue
        distance_result = curve_distance(target, reference.curve, min_overlap_points=min_overlap_points)
        if distance_result is None:
            continue
        distance, overlap = distance_result
        pickup = _reference_remaining_pickup(reference.curve, cutoff_h)
        if pickup is None:
            continue
        candidates.append(CurveNeighbor(
            ticket_event_id=int(reference.ticket_event_id),
            club_slug=str(reference.club_slug),
            distance=distance,
            overlap_points=overlap,
            remaining_pickup_share=pickup,
        ))

    selected = sorted(candidates, key=lambda row: (row.distance, row.ticket_event_id))[:neighbors]
    pickup_values = np.asarray([row.remaining_pickup_share for row in selected], dtype=float)
    distances = np.asarray([row.distance for row in selected], dtype=float)
    return PickupEstimate(
        version=VERSION,
        ticket_event_id=target.ticket_event_id,
        as_of_at=target.as_of_at,
        observed_hours_to_kickoff=float(current_h),
        reference_event_count=len({row.ticket_event_id for row in candidates}),
        reference_club_count=len({row.club_slug for row in candidates}),
        neighbor_count=len(selected),
        median_distance=(float(np.median(distances)) if len(distances) else None),
        median_remaining_pickup_share=(float(np.median(pickup_values)) if len(pickup_values) else None),
        pickup_q25=(float(np.quantile(pickup_values, 0.25)) if len(pickup_values) else None),
        pickup_q75=(float(np.quantile(pickup_values, 0.75)) if len(pickup_values) else None),
        neighbors=tuple(selected),
        point_in_time_validated=True,
        target_future_points_used=False,
    )


def _interpolate_visible(clean: list[tuple[float, int, int]], target_h: float) -> float | None:
    exact = [available for hours, _, available in clean if abs(hours - target_h) < 1e-9]
    if exact:
        return float(exact[-1])
    hours_values = [row[0] for row in clean]
    if target_h < min(hours_values) or target_h > max(hours_values):
        return None
    older = [row for row in clean if row[0] > target_h]
    newer = [row for row in clean if row[0] < target_h]
    if not older or not newer:
        return None
    left = min(older, key=lambda row: row[0] - target_h)
    right = min(newer, key=lambda row: target_h - row[0])
    h1, _, v1 = left
    h2, _, v2 = right
    if h1 - h2 > MAX_INTERPOLATION_GAP_HOURS:
        return None
    weight = (h1 - target_h) / (h1 - h2)
    return float(v1 + weight * (v2 - v1))


def _reference_remaining_pickup(reference: NormalizedCurve, cutoff_h: float) -> float | None:
    values = reference.as_dict()
    at_cutoff = values.get(cutoff_h)
    if at_cutoff is None:
        return None
    later_points = [
        (h, value) for h, value in values.items()
        if h < cutoff_h and value is not None
    ]
    if not later_points:
        return None
    _, final_index = min(later_points, key=lambda item: item[0])
    return float(at_cutoff - float(final_index))


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
