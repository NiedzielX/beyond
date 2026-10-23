#!/usr/bin/env python3
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone

from ml.p4_fixture_context_harness_v1 import (
    CHALLENGER_ID,
    MIN_DISTINCT_VALUES,
    MIN_LABELED_EVENTS,
    PRIMARY_FEATURE,
    contract,
    evaluate,
    freeze_manifest,
    labeled_frame,
)

UTC = timezone.utc


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def inputs(n: int = 9, distinct: int = 4) -> dict:
    rows = []
    spacing_values = [10.0 + 5.0 * (idx % distinct) for idx in range(n)]
    for idx in range(n):
        event_id = idx + 1
        kickoff = datetime(2026, 11, 1, 18, tzinfo=UTC) + timedelta(days=idx * 3)
        rows.append({
            "ticket_event_id": event_id,
            "context_id": 100 + event_id,
            "forward_prediction_id": 200 + event_id,
            "source_prior_id": 300 + event_id,
            "forecast_as_of_at": iso(kickoff - timedelta(days=3)),
            "kickoff_at": iso(kickoff),
            "schedule_batch_id": 400 + event_id,
            "stadium_capacity": 40_000,
            "structural_t3_p50": 17_500.0,
            "b2_prior_home_matches": 4,
            "b2_ewma_residual_fraction": 0.01,
            "b2_correction_seats": 400.0,
            "anchor_p50": 17_900.0,
            "home_team_canonical": f"home-{event_id}",
            "away_team_canonical": f"away-{event_id}",
            PRIMARY_FEATURE: spacing_values[idx],
            "previous_home_opponent_canonical": "prior",
            "next_home_match_days": None,
            "next_home_opponent_canonical": None,
            "team_fixture_density_next_7d": 1,
            "team_fixture_density_next_14d": 1,
            "team_fixture_density_next_30d": 1,
            "home_fixture_density_next_7d": 0,
            "home_fixture_density_next_14d": 0,
            "home_fixture_density_next_30d": 0,
        })
    return {
        "version": "p4-fixture-context-inputs-v1",
        "independentUnit": "ticket_event",
        "selectionRule": "first READY fixture-context row per reproducible Long72 event",
        "anchorDefinition": "frozen Long72 pre-live T3 Structural Prior plus frozen B2 current-season correction",
        "primaryFeature": PRIMARY_FEATURE,
        "inactiveFeatures": ["next_home_match_days"],
        "targetFieldsIncluded": False,
        "labelsIncluded": False,
        "eventCount": len(rows),
        "events": rows,
    }


def labels(n: int = 9) -> dict:
    rows = []
    for idx in range(n):
        event_id = idx + 1
        spacing = 10.0 + 5.0 * (idx % 4)
        actual = int(17_900 + 80 * (spacing - 15.0))
        kickoff = datetime(2026, 11, 1, 18, tzinfo=UTC) + timedelta(days=idx * 3)
        rows.append({
            "ticket_event_id": event_id,
            "actual_attendance": actual,
            "outcome_confirmed_at": iso(kickoff + timedelta(hours=3)),
            "outcome_version_at": iso(kickoff + timedelta(hours=3)),
            "scored_at": iso(kickoff + timedelta(hours=4)),
            "package_id": "d2-long72-stage2-p2-observation-maturity-2026-10-21-v1",
        })
    return {
        "version": "p4-fixture-context-labels-v1",
        "independentUnit": "ticket_event",
        "eventCount": len(rows),
        "labels": rows,
    }


def expect_runtime_error(fn, contains: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert contains in str(exc), str(exc)
    else:
        raise AssertionError(f"expected RuntimeError containing {contains!r}")


def test_contract_is_fixed() -> None:
    value = contract()
    assert value["research_start_gate"]["minimum_labeled_events"] == MIN_LABELED_EVENTS == 9
    assert value["research_start_gate"]["minimum_distinct_primary_feature_values"] == MIN_DISTINCT_VALUES == 3
    assert value["candidate_family"][1]["candidate_id"] == CHALLENGER_ID
    assert value["production"]["live_adjustment"] == 0


def test_freeze_is_deterministic_and_target_free() -> None:
    payload = inputs(9, 4)
    a = freeze_manifest(payload)
    b = freeze_manifest(copy.deepcopy(payload))
    assert a["manifest_sha256"] == b["manifest_sha256"]
    assert a["event_count"] == 9
    assert a["target_values_opened"] is False


def test_target_leakage_rejected() -> None:
    payload = inputs(9, 4)
    payload["events"][0]["actual_attendance"] = 20_000
    expect_runtime_error(lambda: freeze_manifest(payload), "P4A_TARGET_LEAKAGE")


def test_below_nine_labels_fails_closed() -> None:
    payload = inputs(9, 4)
    frozen = freeze_manifest(payload)
    expect_runtime_error(
        lambda: labeled_frame(payload, frozen, labels(8)),
        "P4A_NOT_READY: labeled_events=8",
    )


def test_insufficient_feature_variance_fails_closed() -> None:
    payload = inputs(9, 2)
    frozen = freeze_manifest(payload)
    expect_runtime_error(
        lambda: labeled_frame(payload, frozen, labels(9)),
        f"P4A_NOT_READY: distinct_{PRIMARY_FEATURE}=2",
    )


def test_freeze_drift_fails_before_labels() -> None:
    payload = inputs(9, 4)
    frozen = freeze_manifest(payload)
    frozen["identities"][0][PRIMARY_FEATURE] += 1.0
    expect_runtime_error(
        lambda: labeled_frame(payload, frozen, labels(9)),
        "P4A_IDENTITY_DRIFT",
    )


def test_fixed_tournament_runs_at_gate() -> None:
    payload = inputs(9, 4)
    frozen = freeze_manifest(payload)
    scorecard, predictions, manifest = evaluate(payload, frozen, labels(9))
    assert scorecard["status"] == "P4A_FIXTURE_CONTEXT_EVALUATION_COMPLETE"
    assert scorecard["labeled_event_count"] == 9
    assert scorecard["distinct_primary_feature_values"] >= 3
    assert scorecard["fold_count"] == 4
    assert scorecard["forward_test_event_count"] == 4
    assert scorecard["production_activation_allowed"] is False
    assert scorecard["live_adjustment"] == 0
    assert len(predictions) == 4
    assert manifest["folds_sha256"] == scorecard["fold_manifest_sha256"]


if __name__ == "__main__":
    test_contract_is_fixed()
    test_freeze_is_deterministic_and_target_free()
    test_target_leakage_rejected()
    test_below_nine_labels_fails_closed()
    test_insufficient_feature_variance_fails_closed()
    test_freeze_drift_fails_before_labels()
    test_fixed_tournament_runs_at_gate()
    print("p4_fixture_context_harness_v1 tests passed")
