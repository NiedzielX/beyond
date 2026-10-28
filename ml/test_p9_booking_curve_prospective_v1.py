#!/usr/bin/env python3
from __future__ import annotations

from ml.p9_booking_curve_prospective_v1 import build_predictions


def p9a(cutoff: int, neighbors: list[int] | None = None) -> dict:
    refs = neighbors or [1, 2, 3]
    return {
        "version": "p9a-booking-curve-freeze-v1",
        "cutoff_hours": cutoff,
        "manifest_sha256": "a" * 64,
        "target_values_opened": False,
        "model_training_performed": False,
        "production_change": False,
        "targets": [
            {
                "ticket_event_id": 10,
                "target_as_of_at": f"2026-11-01T{12-cutoff//24:02d}:00:00+00:00" if False else (
                    "2026-10-30T12:00:00+00:00" if cutoff == 48 else "2026-10-31T12:00:00+00:00"
                ),
                "lineage_sha256": "b" * 64,
                "lineage": {
                    "selected_neighbor_event_ids": refs,
                    "persisted_incumbent_rows": [
                        {"source": "structural_prior_forecasts_v1", "row_id": 100}
                    ],
                },
            }
        ],
    }


def catalog(cutoff: int, include_all_refs: bool = True) -> dict:
    cutoff_at = "2026-10-30T12:00:00+00:00" if cutoff == 48 else "2026-10-31T12:00:00+00:00"
    ref_cutoff = "2026-10-10T12:00:00+00:00"
    events = [
        {
            "ticket_event_id": 10,
            "club_slug": "target",
            "home_team": "Target FC",
            "away_team": "Away FC",
            "kickoff_at": "2026-11-01T12:00:00+00:00",
            "analogous_cutoff_at": cutoff_at,
            "is_target": True,
        },
    ]
    for ref_id in [1, 2, 3]:
        events.append({
            "ticket_event_id": ref_id,
            "club_slug": f"ref-{ref_id}",
            "home_team": f"Ref {ref_id}",
            "away_team": "Other",
            "kickoff_at": "2026-10-12T12:00:00+00:00",
            "analogous_cutoff_at": ref_cutoff,
            "is_target": False,
        })

    incumbents = [
        {
            "source": "structural_prior_forecasts_v1",
            "row_id": 100,
            "ticket_event_id": 10,
            "as_of_at": cutoff_at,
            "persisted_at": cutoff_at,
            "p50": 100.0,
            "stadium_capacity": 200,
            "model_spec_id": "structural-v1",
            "point_in_time_validated": True,
        }
    ]
    ref_ids = [1, 2, 3] if include_all_refs else [1, 2]
    for ref_id in ref_ids:
        incumbents.append({
            "source": "structural_prior_forecasts_v1",
            "row_id": 100 + ref_id,
            "ticket_event_id": ref_id,
            "as_of_at": ref_cutoff,
            "persisted_at": ref_cutoff,
            "p50": 50.0,
            "stadium_capacity": 200,
            "model_spec_id": "structural-v1",
            "point_in_time_validated": True,
        })

    return {
        "version": "p9-prospective-incumbent-catalog-v1",
        "cutoff_hours": cutoff,
        "target_event_ids": [10],
        "events": events,
        "incumbents": incumbents,
        "attendance_values_included": False,
        "target_values_used": False,
        "production_change": False,
    }


def reference_outcomes(include_target: bool = False) -> dict:
    rows = [
        {"ticket_event_id": 1, "actual_attendance": 60, "confirmed_at": "2026-10-12T15:00:00+00:00", "attendance_definition": "reported_match_attendance", "source_name": "s1", "source_url": "https://example.com/1"},
        {"ticket_event_id": 2, "actual_attendance": 70, "confirmed_at": "2026-10-12T15:00:00+00:00", "attendance_definition": "reported_match_attendance", "source_name": "s2", "source_url": "https://example.com/2"},
        {"ticket_event_id": 3, "actual_attendance": 80, "confirmed_at": "2026-10-12T15:00:00+00:00", "attendance_definition": "reported_match_attendance", "source_name": "s3", "source_url": "https://example.com/3"},
    ]
    if include_target:
        rows.append({"ticket_event_id": 10, "actual_attendance": 130, "confirmed_at": "2026-11-01T15:00:00+00:00"})
    return {
        "version": "p9-prospective-reference-outcomes-v1",
        "attendance": rows,
        "target_attendance_included": False,
        "production_change": False,
    }


def test_prediction_uses_fixed_median_residual() -> None:
    result = build_predictions(p9a(48), catalog(48), reference_outcomes())
    assert result["precommit_id"] == "p9-knn-median-residual-k5-v1"
    assert result["target_values_used"] is False
    assert result["production_change"] is False
    assert len(result["predictions"]) == 1
    row = result["predictions"][0]
    assert row["ticket_event_id"] == 10
    assert row["cutoff_hours"] == 48
    # residuals: 10, 20, 30 -> median 20
    assert row["trajectory_residual"] == 20.0
    assert row["incumbent_p50"] == 100.0
    assert row["challenger_p50"] == 120.0
    assert row["residual_reference_event_ids"] == [1, 2, 3]
    assert row["reference_incumbent_row_ids"] == [101, 102, 103]


def test_insufficient_support_emits_no_prediction() -> None:
    result = build_predictions(p9a(48), catalog(48, include_all_refs=False), reference_outcomes())
    assert result["predictions"] == []
    assert result["diagnostics"][0]["status"] == "PIT_SUPPORT_INSUFFICIENT"
    assert result["diagnostics"][0]["residual_reference_count"] == 2


def test_target_attendance_leak_fails_closed() -> None:
    try:
        build_predictions(p9a(48), catalog(48), reference_outcomes(include_target=True))
    except RuntimeError as exc:
        assert "future target leaked into reference outcomes" in str(exc)
    else:
        raise AssertionError("target attendance leak did not fail closed")


def test_same_family_required() -> None:
    c = catalog(48)
    for row in c["incumbents"]:
        if row["ticket_event_id"] in (1, 2, 3):
            row["source"] = "d2_long72_forward_predictions_v1"
    result = build_predictions(p9a(48), c, reference_outcomes())
    assert result["predictions"] == []
    assert result["diagnostics"][0]["status"] == "PIT_SUPPORT_INSUFFICIENT"


def test_reference_outcome_must_be_known_by_target_cutoff() -> None:
    outcomes = reference_outcomes()
    # T-48 target cutoff is 2026-10-30 12:00 UTC. The reference event is
    # historical, but this attendance value is intentionally confirmed one
    # minute after the target cutoff and must therefore be unavailable to P9.
    outcomes["attendance"][2]["confirmed_at"] = "2026-10-30T12:01:00+00:00"

    result = build_predictions(p9a(48), catalog(48), outcomes)
    assert result["predictions"] == []
    diag = result["diagnostics"][0]
    assert diag["status"] == "PIT_SUPPORT_INSUFFICIENT"
    assert diag["residual_reference_count"] == 2
    late = [row for row in diag["missing_reference_rows"] if row["ticket_event_id"] == 3]
    assert len(late) == 1
    assert late[0]["reason"] == "reference_outcome_not_known_by_target_cutoff"
    assert late[0]["confirmed_at"] == "2026-10-30T12:01:00+00:00"
    assert late[0]["target_as_of_at"] == "2026-10-30T12:00:00+00:00"


def main() -> None:
    test_prediction_uses_fixed_median_residual()
    test_insufficient_support_emits_no_prediction()
    test_target_attendance_leak_fails_closed()
    test_same_family_required()
    test_reference_outcome_must_be_known_by_target_cutoff()
    print("P9 prospective builder v1 tests: OK")


if __name__ == "__main__":
    main()
