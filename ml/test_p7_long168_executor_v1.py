#!/usr/bin/env python3
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone

import numpy as np

from ml.p7_long168_anchor_replay_v1 import (
    ANCHOR_EVIDENCE_CLASS,
    VERSION as ANCHOR_VERSION,
    _support_payload,
)
from ml.p7_long168_harness_v1 import freeze_manifest
from ml.p7_long168_tournament_v1 import (
    ANCHOR_ID,
    CANDIDATES,
    GBR_ID,
    QLIN_ID,
    run_tournament,
)

UTC = timezone.utc


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def synthetic_long168(n_events: int = 9) -> dict:
    rows = []
    for event_id in range(1, n_events + 1):
        kickoff = datetime(2026, 9, 1, 18, tzinfo=UTC) + timedelta(days=event_id * 3)
        for idx, hours in enumerate((150.0, 120.0, 90.0)):
            as_of = kickoff - timedelta(hours=hours)
            snapshot_id = 10_000 + event_id * 10 + idx
            available = 16_000.0 - event_id * 700.0 - idx * 500.0
            rows.append({
                "ticket_event_id": event_id,
                "requested_snapshot_id": snapshot_id,
                "requested_as_of_at": iso(as_of),
                "hours_to_kickoff": hours,
                "bucket_6h": int(hours // 6),
                "features": {
                    "point_in_time_validated": True,
                    "snapshot_id": snapshot_id,
                    "as_of_at": iso(as_of),
                    "kickoff_at": iso(kickoff),
                    "feature_version": "live-trajectory-v1.1",
                    "feature_quality": "OK",
                    "available_index": available,
                    "available_total": available,
                    "available_share_of_capacity": available / 40_000.0,
                    "first_available_total": 18_000.0,
                    "net_removed_since_first": 18_000.0 - available,
                    "net_removed_since_previous": 500.0 if idx else 0.0,
                    "velocity_since_previous": 40.0 + event_id,
                    "velocity_7d": 30.0 + event_id,
                    "velocity_72h": 45.0 + event_id,
                    "velocity_7d_pct_of_capacity_per_hour": (30.0 + event_id) / 40_000.0,
                    "velocity_72h_pct_of_capacity_per_hour": (45.0 + event_id) / 40_000.0,
                    "acceleration_72h_vs_7d": 15.0,
                    "observation_window_hours": 168.0 - hours,
                    "snapshot_age_minutes": 0.0,
                    "max_visible_gap_hours": 6.0,
                    "raw_snapshot_count": idx + 1,
                    "clean_snapshot_count": idx + 1,
                    "data_gap_detected": False,
                    "release_activity_flag": False,
                    "unexplained_inventory_increase_flag": False,
                },
            })
    return {
        "version": "d2-long-horizon-168-rows-v1",
        "eventCount": n_events,
        "liveRowCount": len(rows),
        "sampling": {"window_hours": 168, "cadence_hours": 6},
        "coverage": [],
        "liveRows": rows,
    }


def synthetic_events(n_events: int = 9) -> dict:
    events = []
    for event_id in range(1, n_events + 1):
        kickoff = datetime(2026, 9, 1, 18, tzinfo=UTC) + timedelta(days=event_id * 3)
        # Construct a residual signal that is learnable from event progression.
        actual = 10_000.0 + event_id * 550.0
        events.append({
            "ticket_event_id": event_id,
            "kickoff_at": iso(kickoff),
            "stadium_capacity": 40_000,
            "actual_attendance": actual,
        })
    return {
        "version": "c1-alpha-v7-events-v1",
        "eventCount": n_events,
        "events": events,
    }


def synthetic_anchor(long168: dict) -> dict:
    freeze = freeze_manifest(long168)
    anchors = []
    for summary in freeze["event_summary"]:
        event_id = int(summary["ticket_event_id"])
        kickoff = datetime.fromisoformat(summary["kickoff_at"])
        anchors.append({
            "ticket_event_id": event_id,
            "kickoff_at": iso(kickoff),
            "target_as_of_at": iso(kickoff - timedelta(days=7)),
            "p50": 10_000.0,
            "stadium_capacity": 40_000,
            "prior_model_spec_id": "structural-prior-runtime-v1-t7-gbr-base",
            "artifact_version": "synthetic-test",
            "anchor_evidence_class": ANCHOR_EVIDENCE_CLASS,
            "persisted_forecast": False,
            "historical_replay": True,
        })
    return {
        "version": ANCHOR_VERSION,
        "status": "P7_T7_ANCHOR_REPLAY_READY",
        "anchor_evidence_class": ANCHOR_EVIDENCE_CLASS,
        "persisted_forecast": False,
        "model_training_performed": False,
        "event_ids": freeze["event_ids"],
        "anchor_count": len(anchors),
        "anchors": anchors,
        "target_attendance_invariance": {"status": "PASS"},
        "package_sha256": "synthetic-anchor-sha",
    }


def expect_runtime_error(fn, contains: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert contains in str(exc), str(exc)
    else:
        raise AssertionError(f"expected RuntimeError containing {contains!r}")


def test_support_payload_strips_target_label_metadata() -> None:
    events = {
        "version": "c1-alpha-v7-events-v1",
        "events": [{
            "ticket_event_id": 1,
            "actual_attendance": 12345,
            "kickoff_at": "2026-09-10T18:00:00+00:00",
        }],
    }
    support = _support_payload(
        target_event_ids=[1],
        events_payload=events,
        attendance_payload={"version": "c1-alpha-v7-attendance-v1", "attendance": []},
        sporting_payload={"version": "c1-alpha-v7-sporting-v1", "sportingMatches": []},
        aliases_payload={"version": "c1-alpha-v7-aliases-v1", "aliases": []},
    )
    assert "actual_attendance" not in support["events"][0]


def test_tournament_is_deterministic_and_uses_fixed_candidates() -> None:
    long168 = synthetic_long168()
    freeze = freeze_manifest(long168)
    anchor = synthetic_anchor(long168)
    events = synthetic_events()
    first, first_predictions, first_manifest = run_tournament(
        long168=long168,
        freeze=freeze,
        anchor=anchor,
        events_payload=events,
    )
    second, second_predictions, second_manifest = run_tournament(
        long168=copy.deepcopy(long168),
        freeze=copy.deepcopy(freeze),
        anchor=copy.deepcopy(anchor),
        events_payload=copy.deepcopy(events),
    )
    assert first["candidate_ids"] == list(CANDIDATES)
    assert first["candidate_ids"] == [ANCHOR_ID, QLIN_ID, GBR_ID]
    assert first["fold_count"] == 4
    assert first["forward_test_event_count"] == 4
    assert first["scorecard_sha256"] == second["scorecard_sha256"]
    assert first_manifest["folds_sha256"] == second_manifest["folds_sha256"]
    assert first_predictions.equals(second_predictions)
    assert first["production_activation_allowed"] is False
    assert first["live_adjustment"] == 0
    assert np.isfinite(first["anchor"]["summary"]["event_balanced_mae"])


def test_identity_drift_fails_before_tournament() -> None:
    long168 = synthetic_long168()
    freeze = freeze_manifest(long168)
    anchor = synthetic_anchor(long168)
    events = synthetic_events()
    freeze["identities"][0]["requested_snapshot_id"] += 1
    expect_runtime_error(
        lambda: run_tournament(long168=long168, freeze=freeze, anchor=anchor, events_payload=events),
        "frozen identity drift",
    )


def test_future_anchor_fails_closed() -> None:
    long168 = synthetic_long168()
    freeze = freeze_manifest(long168)
    anchor = synthetic_anchor(long168)
    events = synthetic_events()
    event_id = int(freeze["event_ids"][0])
    target = next(row for row in anchor["anchors"] if int(row["ticket_event_id"]) == event_id)
    kickoff = datetime.fromisoformat(target["kickoff_at"])
    # 2 days before kickoff is later than all P7 live observations (90-150h).
    target["target_as_of_at"] = iso(kickoff - timedelta(days=2))
    expect_runtime_error(
        lambda: run_tournament(long168=long168, freeze=freeze, anchor=anchor, events_payload=events),
        "future anchor leakage",
    )


def test_anchor_event_set_must_equal_freeze() -> None:
    long168 = synthetic_long168()
    freeze = freeze_manifest(long168)
    anchor = synthetic_anchor(long168)
    events = synthetic_events()
    anchor["anchors"] = anchor["anchors"][:-1]
    anchor["anchor_count"] -= 1
    expect_runtime_error(
        lambda: run_tournament(long168=long168, freeze=freeze, anchor=anchor, events_payload=events),
        "missing/extra P7 anchors",
    )


if __name__ == "__main__":
    test_support_payload_strips_target_label_metadata()
    test_tournament_is_deterministic_and_uses_fixed_candidates()
    test_identity_drift_fails_before_tournament()
    test_future_anchor_fails_closed()
    test_anchor_event_set_must_equal_freeze()
    print("p7_long168_executor_v1 tests passed")
