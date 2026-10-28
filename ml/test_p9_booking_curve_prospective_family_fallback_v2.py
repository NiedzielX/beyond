#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from ml.p9_booking_curve_prospective_family_fallback_v2 import (
    D2_FAMILY,
    STRUCTURAL_FAMILY,
    build_fallback_predictions,
)

UTC = timezone.utc
TARGET_ID = 100
REF_IDS = [1, 2, 3, 4, 5]
CUTOFF_HOURS = 48
TARGET_KICKOFF = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
TARGET_AS_OF = TARGET_KICKOFF - timedelta(hours=CUTOFF_HOURS)


def iso(value: datetime) -> str:
    return value.isoformat()


def incumbent(row_id: int, event_id: int, source: str, as_of: datetime, p50: float) -> dict:
    return {
        "row_id": row_id,
        "ticket_event_id": event_id,
        "source": source,
        "as_of_at": iso(as_of),
        "persisted_at": iso(as_of),
        "p50": p50,
        "stadium_capacity": 30000,
        "model_spec_id": f"{source}-test",
        "point_in_time_validated": True,
    }


def payloads(
    d2_refs: set[int],
    structural_refs: set[int],
    *,
    target_d2: bool = True,
    target_structural: bool = True,
) -> tuple[dict, dict, dict]:
    target_lineage_rows: list[dict] = []
    incumbents: list[dict] = []

    if target_structural:
        row = incumbent(1001, TARGET_ID, STRUCTURAL_FAMILY, TARGET_AS_OF - timedelta(hours=12), 12000)
        incumbents.append(row)
        target_lineage_rows.append({"source": STRUCTURAL_FAMILY, "row_id": 1001})
    if target_d2:
        row = incumbent(1002, TARGET_ID, D2_FAMILY, TARGET_AS_OF - timedelta(hours=1), 12500)
        incumbents.append(row)
        target_lineage_rows.append({"source": D2_FAMILY, "row_id": 1002})

    events = [{
        "ticket_event_id": TARGET_ID,
        "kickoff_at": iso(TARGET_KICKOFF),
        "analogous_cutoff_at": iso(TARGET_AS_OF),
        "is_target": True,
    }]
    attendance: list[dict] = []

    for index, ref_id in enumerate(REF_IDS, start=1):
        kickoff = datetime(2026, 10, 18 + index, 12, 0, tzinfo=UTC)
        analogous_cutoff = kickoff - timedelta(hours=CUTOFF_HOURS)
        events.append({
            "ticket_event_id": ref_id,
            "kickoff_at": iso(kickoff),
            "analogous_cutoff_at": iso(analogous_cutoff),
            "is_target": False,
        })
        if ref_id in structural_refs:
            incumbents.append(incumbent(2000 + ref_id, ref_id, STRUCTURAL_FAMILY, analogous_cutoff, 9000 + ref_id * 100))
        if ref_id in d2_refs:
            incumbents.append(incumbent(3000 + ref_id, ref_id, D2_FAMILY, analogous_cutoff, 9200 + ref_id * 100))
        attendance.append({
            "ticket_event_id": ref_id,
            "actual_attendance": 10000 + ref_id * 100,
            "attendance_definition": "test",
            "source_name": "test",
            "source_url": "https://example.invalid",
            "confirmed_at": iso(kickoff + timedelta(hours=3)),
        })

    p9a = {
        "version": "p9a-booking-curve-freeze-v1",
        "cutoff_hours": CUTOFF_HOURS,
        "manifest_sha256": "a" * 64,
        "target_values_opened": False,
        "model_training_performed": False,
        "production_change": False,
        "targets": [{
            "ticket_event_id": TARGET_ID,
            "target_as_of_at": iso(TARGET_AS_OF),
            "lineage_sha256": "b" * 64,
            "lineage": {
                "persisted_incumbent_rows": target_lineage_rows,
                "selected_neighbor_event_ids": REF_IDS,
            },
        }],
    }
    catalog = {
        "version": "p9-prospective-incumbent-catalog-v1",
        "cutoff_hours": CUTOFF_HOURS,
        "events": events,
        "incumbents": incumbents,
        "attendance_values_included": False,
        "target_values_used": False,
        "production_change": False,
    }
    outcomes = {
        "version": "p9-prospective-reference-outcomes-v1",
        "attendance": attendance,
        "target_attendance_included": False,
        "production_change": False,
    }
    return p9a, catalog, outcomes


def test_d2_insufficient_structural_ready_emits_fallback() -> None:
    p9a, catalog, outcomes = payloads({1, 2}, {1, 2, 3})
    result = build_fallback_predictions(p9a, catalog, outcomes)
    assert result["target_values_used"] is False
    assert result["production_change"] is False
    assert len(result["predictions"]) == 1
    prediction = result["predictions"][0]
    assert prediction["fallback_from_family"] == D2_FAMILY
    assert prediction["incumbent_source"] == STRUCTURAL_FAMILY
    assert prediction["v1_residual_reference_count"] == 2
    assert prediction["selected_neighbor_event_ids"] == REF_IDS
    assert prediction["residual_reference_event_ids"] == [1, 2, 3]
    assert result["diagnostics"][0]["status"] == "FALLBACK_PREDICTION_READY"


def test_v1_d2_support_sufficient_does_not_duplicate() -> None:
    p9a, catalog, outcomes = payloads({1, 2, 3}, {1, 2, 3, 4, 5})
    result = build_fallback_predictions(p9a, catalog, outcomes)
    assert result["predictions"] == []
    diagnostic = result["diagnostics"][0]
    assert diagnostic["status"] == "V1_COVERED"
    assert diagnostic["v1_target_incumbent_source_family"] == D2_FAMILY
    assert diagnostic["v1_residual_reference_count"] == 3


def test_v1_structural_support_sufficient_does_not_duplicate() -> None:
    p9a, catalog, outcomes = payloads(set(), {1, 2, 3}, target_d2=False)
    result = build_fallback_predictions(p9a, catalog, outcomes)
    assert result["predictions"] == []
    diagnostic = result["diagnostics"][0]
    assert diagnostic["status"] == "V1_COVERED"
    assert diagnostic["v1_target_incumbent_source_family"] == STRUCTURAL_FAMILY


def test_both_families_insufficient_fail_closed() -> None:
    p9a, catalog, outcomes = payloads({1, 2}, {1, 2})
    result = build_fallback_predictions(p9a, catalog, outcomes)
    assert result["predictions"] == []
    diagnostic = result["diagnostics"][0]
    assert diagnostic["status"] == "FALLBACK_SUPPORT_INSUFFICIENT"
    assert diagnostic["v1_residual_reference_count"] == 2
    assert diagnostic["fallback_residual_reference_count"] == 2


def test_target_outcome_is_rejected() -> None:
    p9a, catalog, outcomes = payloads({1, 2}, {1, 2, 3})
    leaked = deepcopy(outcomes)
    leaked["attendance"].append({
        "ticket_event_id": TARGET_ID,
        "actual_attendance": 12345,
        "confirmed_at": iso(TARGET_KICKOFF + timedelta(hours=2)),
    })
    try:
        build_fallback_predictions(p9a, catalog, leaked)
    except RuntimeError as exc:
        assert "future target leaked" in str(exc)
    else:
        raise AssertionError("target outcome leak must be rejected")


def main() -> None:
    test_d2_insufficient_structural_ready_emits_fallback()
    test_v1_d2_support_sufficient_does_not_duplicate()
    test_v1_structural_support_sufficient_does_not_duplicate()
    test_both_families_insufficient_fail_closed()
    test_target_outcome_is_rejected()
    print("p9 family fallback v2 tests: OK")


if __name__ == "__main__":
    main()
