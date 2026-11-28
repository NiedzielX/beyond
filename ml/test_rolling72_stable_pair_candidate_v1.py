"""Synthetic contract tests for offline stable-pair scope candidate arithmetic."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from ml.rolling72_stable_pair_candidate_v1 import (
    HORIZONS, MAX_INTERVAL_SEALS, MIN_ORIGIN_COVERAGE,
    prepare_stable_pair_candidate,
)

UTC = timezone.utc
REF = datetime(2026, 11, 27, 12, 2, tzinfo=UTC)
BASE = REF - timedelta(minutes=2)
EVENT = "synthetic-event"


def pair(sector, area, available, name=None):
    return {"sector_source_id": sector, "price_area_id": area,
            "sector": name or f"sector-{sector}", "available": available}


def seal(seal_id, snapshot_id, hours_before, pairs, *, prior=None,
         known_delay_minutes=1, transition="COMPLETE", gap_count=0,
         event=EVENT, total=None, **changes):
    rows = deepcopy(pairs)
    payload = {
        "seal_id": seal_id, "snapshot_id": snapshot_id, "event_id": event,
        "source_family": "roboticket/roboticket", "unit": "available_total_seats",
        "captured_at": BASE - timedelta(hours=hours_before),
        "known_at": BASE - timedelta(hours=hours_before) + timedelta(minutes=known_delay_minutes),
        "available_total": sum(r["available"] for r in rows) if total is None else total,
        "sector_price_area_rows": rows, "source_status": "READY", "committed": True,
        "source_content_sha256": f"{seal_id:064x}", "transition_status": transition,
        "gap_count": gap_count, "prior_seal_id": prior,
    }
    payload.update(changes)
    return payload


def interval(*, extra_origin=0, origin_hours=0, middle_hours=12.25,
             anchor_hours=24.5, stable_availability=(30, 25, 20),
             middle_rows=None, origin_rows=None, anchor_rows=None):
    if anchor_rows is None:
        anchor_rows = [pair(i, 1, stable_availability[0]) for i in range(1, 4)]
    if middle_rows is None:
        middle_rows = [pair(i, 1, stable_availability[1]) for i in range(1, 4)]
    if origin_rows is None:
        origin_rows = [pair(i, 1, stable_availability[2]) for i in range(1, 4)]
        if extra_origin:
            origin_rows.append(pair(4, 7, extra_origin))
    a = seal(1, 101, anchor_hours, anchor_rows, prior=0, transition="NO_PRIOR", gap_count=0)
    m = seal(2, 102, middle_hours, middle_rows, prior=1)
    o = seal(3, 103, origin_hours, origin_rows, prior=2)
    return a, m, o


def run(rows=None, *, anchor_id=1, fallback="SCOPE_MISMATCH", ref=REF, **kw):
    selected = rows or interval(**kw)
    o = next((row for row in selected if row.get("seal_id") == 3), selected[-1])
    return prepare_stable_pair_candidate(
        o, selected, anchor_seal_id=anchor_id,
        parent_fallback_reason=fallback, projection_reference_at=ref,
    )


class StablePairCandidateTests(unittest.TestCase):
    def test_supported_scope_candidate_projects_only_stable_pairs(self):
        a, m, o = interval(extra_origin=15)  # exactly 80% stable origin coverage
        out = run(rows=(a, m, o))
        self.assertEqual(out["support_status"], "SUPPORTED")
        self.assertEqual(out["metrics"]["stable_pair_count"], 3)
        self.assertEqual(out["metrics"]["stable_sector_count"], 3)
        self.assertEqual(out["metrics"]["origin_coverage"], MIN_ORIGIN_COVERAGE)
        self.assertEqual(out["metrics"]["uncovered_origin_available"], 15)
        self.assertEqual([r["horizon_hours"] for r in out["forecast_values"]], list(HORIZONS))
        self.assertTrue(all(r["status"] == "READY" for r in out["forecast_values"]))
        self.assertTrue(all(r["prediction"] >= 15 for r in out["forecast_values"]))
        self.assertFalse(out["claims"]["clock_attested"])
        self.assertFalse(out["claims"]["runtime_or_persistence"])

    def test_disappearing_then_reappearing_pair_is_not_continuous(self):
        a, m, o = interval(extra_origin=15)
        a["sector_price_area_rows"].append(pair(1, 9, 15))
        a["available_total"] += 15
        o["sector_price_area_rows"].append(pair(1, 9, 15))
        o["available_total"] += 15
        # The endpoint pair is absent in the interior. It is excluded from stable support.
        out = run(rows=(a, m, o))
        self.assertEqual(out["support_status"], "INSUFFICIENT_SUPPORT")
        self.assertEqual(out["metrics"]["stable_pair_count"], 3)
        self.assertEqual(out["metrics"]["stable_origin_available"], 60)

    def test_changed_price_area_with_same_sector_does_not_claim_continuity(self):
        a, m, o = interval(extra_origin=15)
        m["sector_price_area_rows"][2]["price_area_id"] = 2
        m["available_total"] = sum(x["available"] for x in m["sector_price_area_rows"])
        o["sector_price_area_rows"][2]["price_area_id"] = 2
        o["available_total"] = sum(x["available"] for x in o["sector_price_area_rows"])
        out = run(rows=(a, m, o))
        self.assertEqual(out["support_status"], "INSUFFICIENT_SUPPORT")
        self.assertEqual(out["metrics"]["stable_sector_count"], 2)

    def test_origin_coverage_below_fixed_floor_falls_back(self):
        a, m, o = interval(extra_origin=16)
        out = run(rows=(a, m, o))
        self.assertEqual(out["support_status"], "INSUFFICIENT_SUPPORT")
        self.assertEqual(out["candidate_policy_status"], "FALLBACK_PERS")
        self.assertTrue(all(r["prediction"] == o["available_total"] for r in out["forecast_values"]))

    def test_non_scope_fallback_is_not_replaced(self):
        out = run(fallback="NO_24H_ANCHOR")
        self.assertEqual(out["support_status"], "NOT_SCOPE_MISMATCH")
        self.assertEqual(out["candidate_policy_status"], "NOT_APPLICABLE")
        self.assertTrue(all(r["status"] == "NOT_APPLICABLE" for r in out["forecast_values"]))

    def test_no_anchor_is_distinct_from_no_usable_pairs(self):
        out = run(anchor_id=None)
        self.assertEqual(out["support_status"], "NO_ANCHOR")
        self.assertEqual(out["candidate_policy_status"], "FALLBACK_PERS")
        self.assertEqual(out["forecast_values"][0]["fallback_reason"], "NO_ANCHOR")

        a, m, o = interval(extra_origin=15)
        m["sector_price_area_rows"] = [pair(9, 8, 75)]
        m["available_total"] = 75
        out = run(rows=(a, m, o))
        self.assertEqual(out["support_status"], "NO_USABLE_STABLE_PAIRS")
        self.assertEqual(out["metrics"]["stable_pair_count"], 0)
        self.assertEqual(out["candidate_policy_status"], "FALLBACK_PERS")

    def test_interior_gap_or_broken_prior_link_fails_closed(self):
        a, m, o = interval(extra_origin=15)
        m["gap_count"] = 1
        out = run(rows=(a, m, o))
        self.assertEqual(out["support_status"], "GAPPED_INTERVAL")
        self.assertTrue(all(r["prediction"] == o["available_total"] for r in out["forecast_values"]))
        m["gap_count"] = 0
        o["prior_seal_id"] = 1
        out = run(rows=(a, m, o))
        self.assertEqual(out["support_status"], "GAPPED_INTERVAL")

    def test_endpoints_and_an_interior_observation_are_required(self):
        a, m, o = interval()
        self.assertEqual(run(rows=(a, o))["support_status"], "NO_INTERIOR_SEAL")
        self.assertEqual(run(rows=(m, o))["support_status"], "MISSING_ENDPOINT")
        stale_origin = {**o, "source_content_sha256": "a" * 64}
        out = prepare_stable_pair_candidate(
            stale_origin, [a, m, o], anchor_seal_id=a["seal_id"],
            parent_fallback_reason="SCOPE_MISMATCH", projection_reference_at=REF,
        )
        self.assertEqual(out["support_status"], "ORIGIN_ENDPOINT_MISMATCH")
        after_origin = seal(4, 104, -0.01, o["sector_price_area_rows"], prior=o["seal_id"])
        self.assertEqual(run(rows=(a, m, o, after_origin))["support_status"], "INVALID_INTERVAL_ORDER")

    def test_observation_known_exactly_at_projection_is_visible(self):
        a, m, o = interval()
        o["known_at"] = REF
        self.assertEqual(run(rows=(a, m, o))["support_status"], "SUPPORTED")

    def test_late_known_seal_and_invalid_or_mismatched_seals_fail_closed(self):
        a, m, o = interval(extra_origin=15)
        m["known_at"] = REF + timedelta(seconds=1)
        self.assertEqual(run(rows=(a, m, o))["support_status"], "INVALID_OR_INCOMPLETE_SEAL")
        a, m, o = interval(extra_origin=15)
        m["committed"] = False
        self.assertEqual(run(rows=(a, m, o))["support_status"], "INVALID_OR_INCOMPLETE_SEAL")
        a, m, o = interval(extra_origin=15)
        m["event_id"] = "other-event"
        self.assertEqual(run(rows=(a, m, o))["support_status"], "INVALID_OR_INCOMPLETE_SEAL")

    def test_invalid_totals_and_duplicate_pairs_fail_closed(self):
        a, m, o = interval(extra_origin=15)
        m["available_total"] += 1
        self.assertEqual(run(rows=(a, m, o))["support_status"], "INVALID_OR_INCOMPLETE_SEAL")
        a, m, o = interval(extra_origin=15)
        m["sector_price_area_rows"].append(deepcopy(m["sector_price_area_rows"][0]))
        m["available_total"] += m["sector_price_area_rows"][-1]["available"]
        self.assertEqual(run(rows=(a, m, o))["support_status"], "INVALID_OR_INCOMPLETE_SEAL")

    def test_invalid_pair_identity_and_gap_type_fail_closed(self):
        a, m, o = interval()
        m["sector_price_area_rows"][0]["price_area_id"] = "changed"
        self.assertEqual(run(rows=(a, m, o))["support_status"], "INVALID_OR_INCOMPLETE_SEAL")
        a, m, o = interval()
        m["gap_count"] = False
        self.assertEqual(run(rows=(a, m, o))["support_status"], "GAPPED_INTERVAL")

    def test_capture_ties_use_snapshot_id_order_and_inclusive_endpoints(self):
        a, _, o = interval(extra_origin=15)
        middle = seal(2, 102, 24.5, [pair(i, 1, 25) for i in range(1, 4)],
                      prior=1, transition="COMPLETE")
        # Same capture time as anchor sorts after snapshot 101; with origin as third row,
        # its parent edge is valid and all interval endpoints remain inclusive.
        middle["captured_at"] = a["captured_at"]
        out = run(rows=(a, middle, o))
        self.assertEqual(out["support_status"], "SUPPORTED")
        self.assertEqual(out["metrics"]["elapsed_capture_hours"], 24.5)
        # Equal order keys are ambiguous and fail closed.
        duplicate_order = deepcopy(middle)
        duplicate_order["snapshot_id"] = a["snapshot_id"]
        self.assertEqual(run(rows=(a, duplicate_order, o))["support_status"], "INVALID_OR_INCOMPLETE_SEAL")

    def test_more_than_130_seals_refuses_partial_interval(self):
        a, m, o = interval(extra_origin=15)
        extras = [deepcopy(m) for _ in range(MAX_INTERVAL_SEALS - 2)]
        # The selector refuses the full supplied interval before parsing/truncating it.
        out = run(rows=(a, m, o, *extras))
        self.assertEqual(out["support_status"], "OVER_130_SEALS")
        self.assertTrue(all(r["prediction"] == o["available_total"] for r in out["forecast_values"]))

    def test_stream_is_not_read_past_the_overflow_sentinel(self):
        a, m, o = interval()

        def rows():
            yield a
            yield from (m for _ in range(MAX_INTERVAL_SEALS - 1))
            yield o
            self.fail("candidate consumed rows after the overflow sentinel")

        out = prepare_stable_pair_candidate(
            o, rows(), anchor_seal_id=a["seal_id"],
            parent_fallback_reason="SCOPE_MISMATCH", projection_reference_at=REF,
        )
        self.assertEqual(out["support_status"], "OVER_130_SEALS")

    def test_exactly_130_continuous_seals_are_accepted(self):
        rows = [
            seal(index, 100 + index, 24.5 * (MAX_INTERVAL_SEALS - index) / (MAX_INTERVAL_SEALS - 1),
                 [pair(i, 1, 20) for i in range(1, 4)], prior=index - 1)
            for index in range(1, MAX_INTERVAL_SEALS + 1)
        ]
        out = prepare_stable_pair_candidate(
            rows[-1], iter(rows), anchor_seal_id=rows[0]["seal_id"],
            parent_fallback_reason="SCOPE_MISMATCH", projection_reference_at=REF,
        )
        self.assertEqual(out["support_status"], "SUPPORTED")

    def test_zero_origin_and_true_zero_are_preserved(self):
        zero_rows = [pair(i, 1, 0) for i in range(1, 4)]
        a = seal(1, 101, 24.5, zero_rows, prior=0, transition="NO_PRIOR")
        m = seal(2, 102, 12.25, zero_rows, prior=1)
        o = seal(3, 103, 0, zero_rows, prior=2)
        out = run(rows=(a, m, o))
        self.assertEqual(out["support_status"], "ZERO_ORIGIN")
        self.assertEqual(out["candidate_policy_status"], "ZERO_ORIGIN")
        self.assertTrue(all(r["prediction"] == 0 for r in out["forecast_values"]))

    def test_fractional_age_slope_projection_and_lower_clip(self):
        a, m, o = interval(extra_origin=15)
        out = run(rows=(a, m, o))
        slope = out["metrics"]["stable_pair_slope_per_hour"]
        age = out["metrics"]["origin_age_hours"]
        uncovered = out["metrics"]["uncovered_origin_available"]
        stable_origin = out["metrics"]["stable_origin_available"]
        self.assertAlmostEqual(age, 2 / 60)
        expected = [uncovered + max(0, stable_origin + slope * (h + age)) for h in HORIZONS]
        self.assertEqual([r["prediction"] for r in out["forecast_values"]], expected)
        # A sufficiently steep decline clips the stable component, not uncovered inventory.
        self.assertEqual(out["forecast_values"][-1]["prediction"], uncovered)
        # Increasing inventory projects upward using the same fixed arithmetic.
        a, m, o = interval(extra_origin=15, stable_availability=(10, 15, 20))
        out = run(rows=(a, m, o))
        self.assertEqual(out["support_status"], "SUPPORTED")
        self.assertGreater(out["forecast_values"][-1]["prediction"], o["available_total"])


if __name__ == "__main__":
    unittest.main()
