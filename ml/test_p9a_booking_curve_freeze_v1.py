#!/usr/bin/env python3
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from ml.p9a_booking_curve_freeze_v1 import freeze_inputs

UTC = timezone.utc


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def snaps(kickoff: datetime, event_id: int, hours: list[float], values: list[int]) -> list[dict]:
    return [
        {
            "snapshot_id": event_id * 1000 + index,
            "captured_at": iso(kickoff - timedelta(hours=hour)),
            "available_total": value,
        }
        for index, (hour, value) in enumerate(zip(hours, values), start=1)
    ]


def reference(event_id: int, kickoff: datetime, club: str) -> dict:
    return {
        "ticket_event_id": event_id,
        "club_slug": club,
        "home_team": f"Home {event_id}",
        "away_team": f"Away {event_id}",
        "kickoff_at": iso(kickoff),
        "snapshots": snaps(
            kickoff,
            event_id,
            [72, 60, 48, 36, 24, 18, 12, 6],
            [1000, 960, 900, 820, 700, 610, 500, 380],
        ),
    }


def payload(*, with_incumbent: bool = False) -> dict:
    kickoff = datetime(2026, 10, 20, 18, tzinfo=UTC)
    target_as_of = kickoff - timedelta(hours=24)
    refs = [
        reference(1, datetime(2026, 10, 1, 18, tzinfo=UTC), "club-a"),
        reference(2, datetime(2026, 10, 5, 18, tzinfo=UTC), "club-b"),
        reference(3, datetime(2026, 10, 10, 18, tzinfo=UTC), "club-c"),
    ]
    incumbents = []
    if with_incumbent:
        incumbents.append({
            "source": "structural_prior_forecasts_v1",
            "row_id": 77,
            "as_of_at": iso(target_as_of - timedelta(hours=1)),
            "persisted_at": iso(target_as_of - timedelta(minutes=30)),
            "p50": 17000.0,
            "model_spec_id": "frozen-prior",
            "point_in_time_validated": True,
        })
    return {
        "version": "p9a-booking-curve-inputs-v1",
        "generated_at": iso(datetime(2026, 10, 24, 12, tzinfo=UTC)),
        "cutoff_hours": 24,
        "canonical_hours": [168, 144, 120, 96, 72, 60, 48, 36, 24, 18, 12, 6],
        "max_interpolation_gap_hours": 12,
        "minimum_overlap_points": 3,
        "inventory_interpretation": "demand_proxy_not_confirmed_sales",
        "independent_unit": "ticket_event",
        "target_values_used": False,
        "post_cutoff_target_snapshots_exported": False,
        "reference_catalog_semantics": "freeze filters strict-prior refs per target",
        "incumbent_rule": "only rows persisted at or before target_as_of_at are exposed",
        "production_change": False,
        "targets": [{
            "ticket_event_id": 99,
            "club_slug": "target-club",
            "home_team": "Target Home",
            "away_team": "Target Away",
            "competition": "PKO BP Ekstraklasa",
            "kickoff_at": iso(kickoff),
            "target_as_of_at": iso(target_as_of),
            "target_snapshots": snaps(
                kickoff,
                99,
                [48, 36, 24],
                [1000, 880, 760],
            ),
            "persisted_incumbents": incumbents,
        }],
        "reference_catalog": refs,
    }


def test_freeze_is_target_free_and_reference_ready() -> None:
    frozen = freeze_inputs(payload())
    row = frozen["targets"][0]
    assert frozen["target_values_opened"] is False
    assert frozen["model_training_performed"] is False
    assert frozen["production_change"] is False
    assert row["representation_ready"] is True
    assert row["reference_ready"] is True
    assert row["freeze_ready"] is True
    assert row["comparator_ready"] is False
    assert row["cutoff_point_available"] is True
    assert row["cutoff_point_source"] == "canonical_point_already_observed"
    assert row["pickup_features"]["target_future_points_used"] is False
    assert row["lineage"]["eligible_reference_event_ids"] == [1, 2, 3]
    assert frozen["summary"]["reference_catalog_event_count"] == 3
    assert frozen["summary"]["learner_status"] == "MODEL_BLOCKED_PENDING_SEPARATE_PRECOMMIT_AND_VALID_COMPARATOR_SAMPLE"


def test_genuine_persisted_incumbent_can_make_comparator_ready() -> None:
    frozen = freeze_inputs(payload(with_incumbent=True))
    row = frozen["targets"][0]
    assert row["comparator_ready"] is True
    assert row["lineage"]["persisted_incumbent_rows"][0]["row_id"] == 77


def test_recent_pre_cutoff_snapshot_is_held_without_future_data() -> None:
    value = payload()
    kickoff = datetime(2026, 10, 20, 18, tzinfo=UTC)
    # No exact T-24 snapshot. T-25.5 is already known at T-24 and is <=6h stale.
    value["targets"][0]["target_snapshots"] = snaps(
        kickoff,
        99,
        [48, 36, 25.5],
        [1000, 880, 770],
    )
    frozen = freeze_inputs(value)
    row = frozen["targets"][0]
    assert row["representation_ready"] is True
    assert row["cutoff_point_available"] is True
    assert row["cutoff_point_source"] == "last_known_pre_cutoff_hold"
    assert abs(row["cutoff_hold_age_hours"] - 1.5) < 1e-9
    assert row["lineage"]["cutoff_source_snapshot_id"] is not None
    assert row["pickup_features"]["target_future_points_used"] is False


def test_stale_pre_cutoff_snapshot_does_not_fill_boundary() -> None:
    value = payload()
    kickoff = datetime(2026, 10, 20, 18, tzinfo=UTC)
    value["targets"][0]["target_snapshots"] = snaps(
        kickoff,
        99,
        [60, 48, 36],
        [1100, 1000, 880],
    )
    frozen = freeze_inputs(value)
    row = frozen["targets"][0]
    assert row["cutoff_point_available"] is False
    assert row["cutoff_point_source"] == "missing_latest_snapshot_too_stale"
    assert row["cutoff_hold_age_hours"] == 12.0
    assert row["representation_ready"] is False
    assert row["freeze_ready"] is False


def test_post_cutoff_target_snapshot_fails_closed() -> None:
    value = payload()
    kickoff = datetime(2026, 10, 20, 18, tzinfo=UTC)
    value["targets"][0]["target_snapshots"].append({
        "snapshot_id": 999999,
        "captured_at": iso(kickoff - timedelta(hours=12)),
        "available_total": 100,
    })
    try:
        freeze_inputs(value)
    except ValueError as exc:
        assert "after allowed cutoff" in str(exc)
    else:
        raise AssertionError("post-cutoff target snapshot must fail closed")


def test_future_reference_is_ignored_and_cannot_change_manifest() -> None:
    base = freeze_inputs(payload())
    value = payload()
    target_kickoff = datetime(2026, 10, 20, 18, tzinfo=UTC)
    value["reference_catalog"].append(reference(
        4,
        target_kickoff - timedelta(hours=12),
        "future-club",
    ))
    with_future = freeze_inputs(value)
    assert with_future["targets"][0]["lineage"]["eligible_reference_event_ids"] == [1, 2, 3]
    assert with_future["targets"][0]["lineage_sha256"] == base["targets"][0]["lineage_sha256"]
    assert with_future["manifest_sha256"] == base["manifest_sha256"]


def test_self_reference_is_ignored() -> None:
    base = freeze_inputs(payload())
    value = payload()
    value["reference_catalog"].append(reference(
        99,
        datetime(2026, 9, 28, 18, tzinfo=UTC),
        "target-club",
    ))
    with_self = freeze_inputs(value)
    assert 99 not in with_self["targets"][0]["lineage"]["eligible_reference_event_ids"]
    assert with_self["targets"][0]["lineage_sha256"] == base["targets"][0]["lineage_sha256"]


def test_attendance_label_in_input_fails_closed() -> None:
    value = payload()
    value["targets"][0]["actual_attendance"] = 12345
    try:
        freeze_inputs(value)
    except ValueError as exc:
        assert "target/label field forbidden" in str(exc)
    else:
        raise AssertionError("attendance target must not be accepted in freeze input")


def test_manifest_sha_is_order_invariant_for_snapshot_and_catalog_arrays() -> None:
    a = payload(with_incumbent=True)
    b = deepcopy(a)
    b["targets"][0]["target_snapshots"].reverse()
    b["reference_catalog"].reverse()
    for ref in b["reference_catalog"]:
        ref["snapshots"].reverse()
    frozen_a = freeze_inputs(a)
    frozen_b = freeze_inputs(b)
    assert frozen_a["manifest_sha256"] == frozen_b["manifest_sha256"]


def test_incumbent_persisted_after_cutoff_fails_closed() -> None:
    value = payload(with_incumbent=True)
    kickoff = datetime(2026, 10, 20, 18, tzinfo=UTC)
    value["targets"][0]["persisted_incumbents"][0]["persisted_at"] = iso(kickoff - timedelta(hours=1))
    try:
        freeze_inputs(value)
    except ValueError as exc:
        assert "created after target cutoff" in str(exc)
    else:
        raise AssertionError("post-cutoff incumbent must fail closed")


def test_reference_snapshot_at_kickoff_fails_closed() -> None:
    value = payload()
    ref = value["reference_catalog"][0]
    kickoff = datetime.fromisoformat(ref["kickoff_at"].replace("Z", "+00:00"))
    ref["snapshots"].append({
        "snapshot_id": 199999,
        "captured_at": iso(kickoff),
        "available_total": 1,
    })
    try:
        freeze_inputs(value)
    except ValueError as exc:
        assert "at/after allowed cutoff" in str(exc)
    else:
        raise AssertionError("reference snapshot at kickoff must fail closed")


if __name__ == "__main__":
    test_freeze_is_target_free_and_reference_ready()
    test_genuine_persisted_incumbent_can_make_comparator_ready()
    test_recent_pre_cutoff_snapshot_is_held_without_future_data()
    test_stale_pre_cutoff_snapshot_does_not_fill_boundary()
    test_post_cutoff_target_snapshot_fails_closed()
    test_future_reference_is_ignored_and_cannot_change_manifest()
    test_self_reference_is_ignored()
    test_attendance_label_in_input_fails_closed()
    test_manifest_sha_is_order_invariant_for_snapshot_and_catalog_arrays()
    test_incumbent_persisted_after_cutoff_fails_closed()
    test_reference_snapshot_at_kickoff_fails_closed()
    print("p9a_booking_curve_freeze_v1 tests passed")
