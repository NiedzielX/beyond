"""Deterministic event-grouped validation folds for trajectory research v1."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Iterable

FOLD_CONTRACT_ID = "trajectory-validation-fold-contract-v1"
MIN_TRAIN_EVENTS = 5
MIN_TRAIN_CLUBS = 4


@dataclass(frozen=True)
class TrajectoryEventIdentityV1:
    ticket_event_id: int
    club_slug: str
    kickoff_at: datetime


@dataclass(frozen=True)
class TrajectoryForwardFoldV1:
    contract_id: str
    fold_id: str
    test_kickoff_at: datetime
    train_event_ids: tuple[int, ...]
    test_event_ids: tuple[int, ...]
    train_clubs: tuple[str, ...]

    @property
    def train_event_count(self) -> int:
        return len(self.train_event_ids)

    @property
    def test_event_count(self) -> int:
        return len(self.test_event_ids)

    @property
    def train_club_count(self) -> int:
        return len(self.train_clubs)


@dataclass(frozen=True)
class TrajectoryFoldRegistryV1:
    contract_id: str
    event_ids: tuple[int, ...]
    folds: tuple[TrajectoryForwardFoldV1, ...]
    manifest_sha256: str


def build_trajectory_forward_folds_v1(
    events: Iterable[TrajectoryEventIdentityV1],
    *,
    min_train_events: int = MIN_TRAIN_EVENTS,
    min_train_clubs: int = MIN_TRAIN_CLUBS,
) -> TrajectoryFoldRegistryV1:
    """Build strict expanding folds with same-kickoff events held out together."""
    if min_train_events < 1:
        raise ValueError("min_train_events must be >= 1")
    if min_train_clubs < 1:
        raise ValueError("min_train_clubs must be >= 1")

    by_id: dict[int, TrajectoryEventIdentityV1] = {}
    for event in events:
        _validate_event(event)
        existing = by_id.get(event.ticket_event_id)
        if existing is not None and existing != event:
            raise ValueError(f"conflicting event identity: {event.ticket_event_id}")
        by_id[event.ticket_event_id] = event

    ordered = sorted(by_id.values(), key=lambda row: (row.kickoff_at, row.ticket_event_id))
    by_kickoff: dict[datetime, list[TrajectoryEventIdentityV1]] = {}
    for event in ordered:
        by_kickoff.setdefault(event.kickoff_at, []).append(event)

    folds: list[TrajectoryForwardFoldV1] = []
    prior_events: list[TrajectoryEventIdentityV1] = []
    for kickoff in sorted(by_kickoff):
        test_group = sorted(by_kickoff[kickoff], key=lambda row: row.ticket_event_id)
        train_ids = tuple(row.ticket_event_id for row in prior_events)
        train_clubs = tuple(sorted({row.club_slug for row in prior_events}))
        if len(train_ids) >= min_train_events and len(train_clubs) >= min_train_clubs:
            folds.append(
                TrajectoryForwardFoldV1(
                    contract_id=FOLD_CONTRACT_ID,
                    fold_id=f"forward-{kickoff.isoformat()}",
                    test_kickoff_at=kickoff,
                    train_event_ids=train_ids,
                    test_event_ids=tuple(row.ticket_event_id for row in test_group),
                    train_clubs=train_clubs,
                )
            )
        prior_events.extend(test_group)

    registry_payload = {
        "contract_id": FOLD_CONTRACT_ID,
        "event_ids": [row.ticket_event_id for row in ordered],
        "folds": [
            {
                "fold_id": fold.fold_id,
                "test_kickoff_at": fold.test_kickoff_at.isoformat(),
                "train_event_ids": list(fold.train_event_ids),
                "test_event_ids": list(fold.test_event_ids),
                "train_clubs": list(fold.train_clubs),
            }
            for fold in folds
        ],
    }
    manifest_sha256 = hashlib.sha256(
        json.dumps(registry_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return TrajectoryFoldRegistryV1(
        contract_id=FOLD_CONTRACT_ID,
        event_ids=tuple(row.ticket_event_id for row in ordered),
        folds=tuple(folds),
        manifest_sha256=manifest_sha256,
    )


def _validate_event(event: TrajectoryEventIdentityV1) -> None:
    if event.ticket_event_id <= 0:
        raise ValueError("ticket_event_id must be positive")
    if not event.club_slug.strip():
        raise ValueError("club_slug must not be empty")
    if event.kickoff_at.tzinfo is None or event.kickoff_at.utcoffset() is None:
        raise ValueError("kickoff_at must be timezone-aware")
