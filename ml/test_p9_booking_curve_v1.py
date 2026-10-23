#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone

from ml.p9_booking_curve_v1 import (
    CANONICAL_HOURS,
    CurveObservation,
    HistoricalCurveReference,
    build_normalized_curve,
    curve_distance,
    estimate_historical_pickup,
)

UTC = timezone.utc


def observations(kickoff: datetime, values: list[int]) -> list[CurveObservation]:
    return [
        CurveObservation(
            snapshot_id=index + 1,
            captured_at=kickoff - timedelta(hours=hours),
            available_total=value,
        )
        for index, (hours, value) in enumerate(zip(CANONICAL_HOURS, values))
    ]


def test_future_target_points_are_missing() -> None:
    kickoff = datetime(2026, 11, 10, 18, tzinfo=UTC)
    target = build_normalized_curve(
        observations(kickoff, [1000, 970, 940, 900, 840, 800, 740, 680, 600, 520, 430, 300]),
        ticket_event_id=99,
        as_of_at=kickoff - timedelta(hours=50),
        kickoff_at=kickoff,
    )
    points = target.as_dict()
    assert points[60.0] is not None
    assert points[48.0] is None
    assert points[6.0] is None
    assert target.point_in_time_validated


def test_post_cutoff_snapshot_cannot_change_target_curve() -> None:
    kickoff = datetime(2026, 11, 10, 18, tzinfo=UTC)
    base = observations(kickoff, [1000, 970, 940, 900, 840, 800, 740, 680, 600, 520, 430, 300])
    as_of = kickoff - timedelta(hours=50)
    a = build_normalized_curve(base, ticket_event_id=99, as_of_at=as_of, kickoff_at=kickoff)
    leaked = base + [
        CurveObservation(snapshot_id=999, captured_at=kickoff - timedelta(hours=24), available_total=1)
    ]
    b = build_normalized_curve(leaked, ticket_event_id=99, as_of_at=as_of, kickoff_at=kickoff)
    assert a.points == b.points


def test_interpolation_across_gap_over_12h_is_missing() -> None:
    kickoff = datetime(2026, 11, 10, 18, tzinfo=UTC)
    sparse = [
        CurveObservation(1, kickoff - timedelta(hours=80), 1000),
        CurveObservation(2, kickoff - timedelta(hours=64), 800),
    ]
    curve = build_normalized_curve(
        sparse,
        ticket_event_id=99,
        as_of_at=kickoff - timedelta(hours=60),
        kickoff_at=kickoff,
        canonical_hours=(72.0,),
    )
    assert curve.as_dict()[72.0] is None


def test_similarity_uses_only_observed_target_overlap() -> None:
    target_kickoff = datetime(2026, 11, 10, 18, tzinfo=UTC)
    ref_kickoff = datetime(2026, 10, 10, 18, tzinfo=UTC)
    target = build_normalized_curve(
        observations(target_kickoff, [1000, 970, 940, 900, 840, 800, 740, 680, 600, 520, 430, 300]),
        ticket_event_id=99,
        as_of_at=target_kickoff - timedelta(hours=50),
        kickoff_at=target_kickoff,
    )
    reference = build_normalized_curve(
        observations(ref_kickoff, [1000, 970, 940, 900, 840, 800, 700, 500, 300, 200, 100, 20]),
        ticket_event_id=1,
        as_of_at=ref_kickoff - timedelta(hours=5),
        kickoff_at=ref_kickoff,
    )
    result = curve_distance(target, reference)
    assert result is not None
    distance, overlap = result
    assert overlap == 6
    assert distance == 0.0


def test_pickup_excludes_self_and_future_reference_event() -> None:
    target_kickoff = datetime(2026, 11, 10, 18, tzinfo=UTC)
    target_as_of = target_kickoff - timedelta(hours=50)
    target = build_normalized_curve(
        observations(target_kickoff, [1000, 970, 940, 900, 840, 800, 740, 680, 600, 520, 430, 300]),
        ticket_event_id=99,
        as_of_at=target_as_of,
        kickoff_at=target_kickoff,
    )
    ref1_kickoff = datetime(2026, 10, 1, 18, tzinfo=UTC)
    ref1_curve = build_normalized_curve(
        observations(ref1_kickoff, [1000, 970, 940, 900, 840, 800, 700, 550, 400, 300, 200, 100]),
        ticket_event_id=1,
        as_of_at=ref1_kickoff - timedelta(hours=5),
        kickoff_at=ref1_kickoff,
    )
    self_curve = build_normalized_curve(
        observations(target_kickoff, [1000, 970, 940, 900, 840, 800, 700, 550, 400, 300, 200, 100]),
        ticket_event_id=99,
        as_of_at=target_kickoff - timedelta(hours=5),
        kickoff_at=target_kickoff,
    )
    future_ref_kickoff = datetime(2026, 11, 9, 18, tzinfo=UTC)
    future_curve = build_normalized_curve(
        observations(future_ref_kickoff, [1000] * len(CANONICAL_HOURS)),
        ticket_event_id=2,
        as_of_at=future_ref_kickoff - timedelta(hours=5),
        kickoff_at=future_ref_kickoff,
    )
    estimate = estimate_historical_pickup(target, [
        HistoricalCurveReference(1, "club-a", ref1_kickoff + timedelta(hours=3), ref1_curve),
        HistoricalCurveReference(99, "target-club", target_kickoff - timedelta(days=1), self_curve),
        HistoricalCurveReference(2, "club-b", future_ref_kickoff + timedelta(hours=3), future_curve),
    ])
    assert estimate.reference_event_count == 1
    assert estimate.neighbor_count == 1
    assert estimate.neighbors[0].ticket_event_id == 1
    assert estimate.target_future_points_used is False
    assert estimate.median_remaining_pickup_share is not None
    assert estimate.median_remaining_pickup_share > 0


if __name__ == "__main__":
    test_future_target_points_are_missing()
    test_post_cutoff_snapshot_cannot_change_target_curve()
    test_interpolation_across_gap_over_12h_is_missing()
    test_similarity_uses_only_observed_target_overlap()
    test_pickup_excludes_self_and_future_reference_event()
    print("p9_booking_curve_v1 tests passed")
