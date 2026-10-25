#!/usr/bin/env python3
from __future__ import annotations

from ml.p9_booking_curve_learner_v1 import run


def support(cutoff: int) -> dict:
    return {
        "version": "p9-learner-support-freeze-v1",
        "precommit_id": "p9-knn-median-residual-k5-v1",
        "p9a_manifest_sha256": "a" * 64,
        "manifest_sha256": ("b" if cutoff == 48 else "c") * 64,
        "cutoff_hours": cutoff,
        "attendance_values_opened": False,
        "target_values_used": False,
        "model_training_performed": False,
        "production_change": False,
        "targets": [
            {
                "ticket_event_id": 10,
                "support_ready": True,
                "support_lineage_sha256": "d" * 64,
                "selected_neighbor_event_ids": [1, 2, 3],
                "target_incumbent": {
                    "source": "structural_prior_forecasts_v1",
                    "row_id": 1000 + cutoff,
                    "ticket_event_id": 10,
                    "p50": 100.0,
                    "stadium_capacity": 200,
                },
                "reference_incumbents": [
                    {"source": "structural_prior_forecasts_v1", "row_id": 101, "ticket_event_id": 1, "p50": 50.0, "stadium_capacity": 200},
                    {"source": "structural_prior_forecasts_v1", "row_id": 102, "ticket_event_id": 2, "p50": 50.0, "stadium_capacity": 200},
                    {"source": "structural_prior_forecasts_v1", "row_id": 103, "ticket_event_id": 3, "p50": 50.0, "stadium_capacity": 200},
                ],
            }
        ],
    }


def labels(cutoff: int) -> dict:
    support_sha = ("b" if cutoff == 48 else "c") * 64
    events = [
        {"ticket_event_id": 1, "kickoff_at": "2026-01-01T12:00:00+00:00"},
        {"ticket_event_id": 2, "kickoff_at": "2026-01-02T12:00:00+00:00"},
        {"ticket_event_id": 3, "kickoff_at": "2026-01-03T12:00:00+00:00"},
        {"ticket_event_id": 10, "kickoff_at": "2026-01-10T12:00:00+00:00"},
    ]
    attendance = [
        {"ticket_event_id": 1, "actual_attendance": 60, "confirmed_at": "2026-01-01T15:00:00+00:00"},
        {"ticket_event_id": 2, "actual_attendance": 70, "confirmed_at": "2026-01-02T15:00:00+00:00"},
        {"ticket_event_id": 3, "actual_attendance": 80, "confirmed_at": "2026-01-03T15:00:00+00:00"},
        {"ticket_event_id": 10, "actual_attendance": 130, "confirmed_at": "2026-01-10T15:00:00+00:00"},
    ]
    return {
        "version": "p9-learner-label-support-v2",
        "precommit_id": "p9-knn-median-residual-k5-v1",
        "cutoff_hours": cutoff,
        "registered_p9a_manifest_sha256": "a" * 64,
        "registered_support_manifest_sha256": support_sha,
        "readiness_168_events": 9,
        "readiness_168_clubs": 5,
        "target_free_support_freeze_registered": True,
        "production_change": False,
        "events": events,
        "attendance": attendance,
    }


def test_fixed_median_residual() -> None:
    result = run(support(48), labels(48), support(24), labels(24))
    assert result["precommit_id"] == "p9-knn-median-residual-k5-v1"
    assert result["learner"]["candidate_search"] is False
    assert result["learner"]["fitted_coefficients"] is False
    assert result["independent_event_count"] == 1
    assert len(result["rows"]) == 2
    for row in result["rows"]:
        # reference residuals = 10, 20, 30 -> frozen median = 20
        assert row["trajectory_residual"] == 20.0
        assert row["incumbent_p50"] == 100.0
        assert row["challenger_p50"] == 120.0
        assert row["actual_attendance"] == 130
        assert row["anchor_abs_error"] == 30.0
        assert row["challenger_abs_error"] == 10.0
    assert result["primary"]["anchor_event_balanced_mae"] == 30.0
    assert result["primary"]["challenger_event_balanced_mae"] == 10.0
    assert result["primary"]["delta_event_balanced_mae"] == -20.0
    assert result["evidence_status"] == "POINT_GAIN_UNCERTAINTY_LIMITED"
    assert result["production_activation_allowed"] is False
    assert result["live_adjustment"] == 0
    assert result["production_change"] is False


def test_manifest_mismatch_fails_closed() -> None:
    bad = labels(48)
    bad["registered_support_manifest_sha256"] = "e" * 64
    try:
        run(support(48), bad, support(24), labels(24))
    except RuntimeError as exc:
        assert "support manifest mismatch" in str(exc)
    else:
        raise AssertionError("manifest mismatch did not fail closed")


def main() -> None:
    test_fixed_median_residual()
    test_manifest_mismatch_fails_closed()
    print("P9 learner v1 tests: OK")


if __name__ == "__main__":
    main()
