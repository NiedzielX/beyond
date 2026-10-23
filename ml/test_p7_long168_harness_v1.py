#!/usr/bin/env python3
from __future__ import annotations

import copy

from ml.p7_long168_harness_v1 import (
    FEATURE_ALLOWLIST,
    MIN_INDEPENDENT_EVENTS,
    experiment_contract,
    freeze_manifest,
    readiness,
)


def row(event_id: int, bucket: int = 20) -> dict:
    kickoff_hour = event_id % 20
    kickoff = f"2026-11-{10 + event_id:02d}T{kickoff_hour:02d}:00:00+00:00"
    # Exactly 120h before kickoff, safely inside 72-168h.
    day = 5 + event_id
    as_of = f"2026-11-{day:02d}T{kickoff_hour:02d}:00:00+00:00"
    snapshot_id = 1000 + event_id
    return {
        "ticket_event_id": event_id,
        "bucket_6h": bucket,
        "hours_to_kickoff": 120.0,
        "requested_as_of_at": as_of,
        "requested_snapshot_id": snapshot_id,
        "features": {
            "point_in_time_validated": True,
            "snapshot_id": snapshot_id,
            "as_of_at": as_of,
            "kickoff_at": kickoff,
            "feature_version": "live-trajectory-v1.1",
            "feature_quality": "OK",
            "hours_to_kickoff": 120.0,
        },
    }


def payload(n_events: int) -> dict:
    rows = [row(event_id) for event_id in range(1, n_events + 1)]
    return {
        "version": "d2-long-horizon-168-rows-v1",
        "eventCount": n_events,
        "liveRowCount": len(rows),
        "sampling": {
            "window_hours": 168,
            "cadence_hours": 6,
            "rule": "latest snapshot in each event x 6h bucket inside final 168h",
        },
        "coverage": [],
        "liveRows": rows,
    }


def expect_runtime_error(fn, contains: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert contains in str(exc), str(exc)
    else:
        raise AssertionError(f"expected RuntimeError containing {contains!r}")


def test_readiness_fails_closed_at_eight_events() -> None:
    result = readiness(payload(MIN_INDEPENDENT_EVENTS - 1))
    assert result["status"] == "P7_NOT_READY"
    assert result["independent_events_gt_72h"] == 8
    assert result["threshold_met"] is False
    expect_runtime_error(
        lambda: freeze_manifest(payload(MIN_INDEPENDENT_EVENTS - 1)),
        "P7_NOT_READY",
    )


def test_nine_events_freeze_exact_identities_deterministically() -> None:
    source = payload(MIN_INDEPENDENT_EVENTS)
    first = freeze_manifest(source)
    second = freeze_manifest(copy.deepcopy(source))
    assert first["status"] == "P7_LONG168_IDENTITIES_FROZEN"
    assert first["independent_event_count"] == MIN_INDEPENDENT_EVENTS
    assert first["row_count"] == MIN_INDEPENDENT_EVENTS
    assert first["event_ids"] == list(range(1, 10))
    assert first["manifest_sha256"] == second["manifest_sha256"]
    assert first["target_values_present"] is False
    assert first["model_training_performed"] is False
    assert first["model_results_opened"] is False


def test_target_leakage_is_rejected_before_freeze() -> None:
    source = payload(MIN_INDEPENDENT_EVENTS)
    source["liveRows"][0]["actual_attendance"] = 12345
    expect_runtime_error(
        lambda: freeze_manifest(source),
        "target/outcome leakage",
    )


def test_pit_identity_drift_is_rejected() -> None:
    source = payload(MIN_INDEPENDENT_EVENTS)
    source["liveRows"][0]["features"]["snapshot_id"] += 1
    expect_runtime_error(
        lambda: freeze_manifest(source),
        "snapshot identity drift",
    )


def test_contract_is_fixed_and_production_blocked() -> None:
    contract = experiment_contract()
    candidate_ids = [row["candidate_id"] for row in contract["candidate_family"]]
    assert candidate_ids == [
        "anchor-only-t7",
        "q50-linear-residual-a002",
        "gbr-l1-depth2-n50-lr003",
    ]
    assert contract["validation"]["min_train_events"] == 5
    assert contract["primary_metric"]["name"] == "event_balanced_mae"
    assert contract["uncertainty"]["n_resamples"] == 5000
    assert contract["production"]["promotion_allowed_from_p7_v1"] is False
    assert contract["production"]["live_adjustment"] == 0
    assert "hours_to_kickoff" in FEATURE_ALLOWLIST


if __name__ == "__main__":
    test_readiness_fails_closed_at_eight_events()
    test_nine_events_freeze_exact_identities_deterministically()
    test_target_leakage_is_rejected_before_freeze()
    test_pit_identity_drift_is_rejected()
    test_contract_is_fixed_and_production_blocked()
    print("p7_long168_harness_v1 tests passed")
