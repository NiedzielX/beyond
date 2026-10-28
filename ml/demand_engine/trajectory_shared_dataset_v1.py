"""Shared development dataset materializer for trajectory Lane A and Lane B v1.

The module deliberately creates both model representations from the same
canonical daily rows. It accepts raw event records in memory and does not query
Supabase itself, which keeps PIT/evidence semantics testable and deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Iterable

from .daily_trajectory_dataset import build_daily_trajectory_dataset
from .live_trajectory_feature_store import SectorInventoryRecord, SnapshotRecord
from .structural_prior import StructuralPrior
from .trajectory_feature_contract_v1 import (
    CONTRACT_ID as FEATURE_CONTRACT_ID,
    LaneBSequenceV1,
    build_lane_b_sequence_v1,
    lane_a_features_v1,
    lane_b_global_features_v1,
    shared_eligibility_v1,
)

DATASET_CONTRACT_ID = "trajectory-shared-development-dataset-v1"


@dataclass(frozen=True)
class TrajectoryOutcomeV1:
    actual_attendance: int
    confirmed_at: datetime
    attendance_definition: str
    source_name: str


@dataclass(frozen=True)
class TrajectoryEventBundleV1:
    ticket_event_id: int
    club_slug: str
    kickoff_at: datetime
    snapshots: tuple[SnapshotRecord, ...]
    sectors: tuple[SectorInventoryRecord, ...]
    structural_priors: tuple[StructuralPrior, ...]
    outcome: TrajectoryOutcomeV1
    stadium_capacity: int | None = None
    public_seat_map_size: int | None = None


@dataclass(frozen=True)
class TrajectoryDevelopmentExampleV1:
    dataset_contract_id: str
    feature_contract_id: str
    ticket_event_id: int
    club_slug: str
    kickoff_at: datetime
    days_to_event: int
    as_of_at: datetime
    incumbent_p50: float
    actual_attendance: int
    residual_target: float
    lane_a_features: dict[str, float | int | bool | str | None]
    lane_b_sequence: LaneBSequenceV1
    lane_b_global_features: dict[str, float | int | bool | None]
    event_row_weight: float
    target_values_used_in_features: bool = False
    production_change: bool = False


@dataclass(frozen=True)
class TrajectoryDevelopmentDatasetV1:
    contract_id: str
    feature_contract_id: str
    examples: tuple[TrajectoryDevelopmentExampleV1, ...]
    event_ids: tuple[int, ...]
    identity_manifest_sha256: str


def materialize_event_examples_v1(
    bundle: TrajectoryEventBundleV1,
    *,
    start_days: int = 60,
    end_days: int = 1,
) -> tuple[TrajectoryDevelopmentExampleV1, ...]:
    """Create all shared eligible daily examples for one completed event.

    Feature representations are built first from PIT-only source records. The
    exposed historical attendance label is attached only after eligibility and
    both model representations have been constructed.
    """
    _validate_bundle(bundle)

    daily_rows = build_daily_trajectory_dataset(
        ticket_event_id=bundle.ticket_event_id,
        club_slug=bundle.club_slug,
        kickoff_at=bundle.kickoff_at,
        snapshots=bundle.snapshots,
        sectors=bundle.sectors,
        structural_priors=bundle.structural_priors,
        stadium_capacity=bundle.stadium_capacity,
        public_seat_map_size=bundle.public_seat_map_size,
        start_days=start_days,
        end_days=end_days,
    )

    staged: list[tuple] = []
    for row in daily_rows:
        eligibility = shared_eligibility_v1(row)
        if not eligibility.eligible:
            continue
        if row.structural_prior is None:
            raise AssertionError("eligible row unexpectedly lacks structural prior")

        lane_a = lane_a_features_v1(row)
        sequence = build_lane_b_sequence_v1(
            bundle.snapshots,
            as_of_at=row.as_of_at,
            kickoff_at=bundle.kickoff_at,
            stadium_capacity=bundle.stadium_capacity,
        )
        lane_b_global = lane_b_global_features_v1(row, sequence)
        staged.append((row, lane_a, sequence, lane_b_global))

    if not staged:
        return ()

    row_weight = 1.0 / len(staged)
    examples: list[TrajectoryDevelopmentExampleV1] = []
    for row, lane_a, sequence, lane_b_global in staged:
        incumbent_p50 = float(row.structural_prior.p50)
        actual = bundle.outcome.actual_attendance
        examples.append(
            TrajectoryDevelopmentExampleV1(
                dataset_contract_id=DATASET_CONTRACT_ID,
                feature_contract_id=FEATURE_CONTRACT_ID,
                ticket_event_id=bundle.ticket_event_id,
                club_slug=bundle.club_slug,
                kickoff_at=bundle.kickoff_at,
                days_to_event=row.days_to_event,
                as_of_at=row.as_of_at,
                incumbent_p50=incumbent_p50,
                actual_attendance=actual,
                residual_target=float(actual) - incumbent_p50,
                lane_a_features=lane_a,
                lane_b_sequence=sequence,
                lane_b_global_features=lane_b_global,
                event_row_weight=row_weight,
            )
        )
    return tuple(examples)


def materialize_shared_dataset_v1(
    bundles: Iterable[TrajectoryEventBundleV1],
    *,
    start_days: int = 60,
    end_days: int = 1,
) -> TrajectoryDevelopmentDatasetV1:
    """Materialize one shared identity-preserving dataset across events."""
    examples: list[TrajectoryDevelopmentExampleV1] = []
    seen_events: set[int] = set()

    for bundle in bundles:
        if bundle.ticket_event_id in seen_events:
            raise ValueError(f"duplicate event bundle: {bundle.ticket_event_id}")
        seen_events.add(bundle.ticket_event_id)
        examples.extend(
            materialize_event_examples_v1(
                bundle,
                start_days=start_days,
                end_days=end_days,
            )
        )

    ordered = sorted(
        examples,
        key=lambda row: (row.kickoff_at, row.ticket_event_id, -row.days_to_event),
    )
    event_ids = tuple(sorted({row.ticket_event_id for row in ordered}))
    identity_payload = {
        "contract_id": DATASET_CONTRACT_ID,
        "feature_contract_id": FEATURE_CONTRACT_ID,
        "rows": [
            {
                "ticket_event_id": row.ticket_event_id,
                "days_to_event": row.days_to_event,
                "as_of_at": row.as_of_at.isoformat(),
                "kickoff_at": row.kickoff_at.isoformat(),
            }
            for row in ordered
        ],
    }
    identity_sha = hashlib.sha256(
        json.dumps(identity_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return TrajectoryDevelopmentDatasetV1(
        contract_id=DATASET_CONTRACT_ID,
        feature_contract_id=FEATURE_CONTRACT_ID,
        examples=tuple(ordered),
        event_ids=event_ids,
        identity_manifest_sha256=identity_sha,
    )


def _validate_bundle(bundle: TrajectoryEventBundleV1) -> None:
    if bundle.ticket_event_id <= 0:
        raise ValueError("ticket_event_id must be positive")
    if not bundle.club_slug.strip():
        raise ValueError("club_slug must not be empty")
    _require_aware("kickoff_at", bundle.kickoff_at)
    _require_aware("outcome.confirmed_at", bundle.outcome.confirmed_at)
    if bundle.outcome.actual_attendance < 0:
        raise ValueError("actual_attendance must be non-negative")
    if bundle.outcome.confirmed_at <= bundle.kickoff_at:
        raise ValueError("outcome must be confirmed after kickoff for historical research")
    if not bundle.outcome.attendance_definition.strip():
        raise ValueError("attendance_definition must not be empty")
    if not bundle.outcome.source_name.strip():
        raise ValueError("outcome source_name must not be empty")


def _require_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
