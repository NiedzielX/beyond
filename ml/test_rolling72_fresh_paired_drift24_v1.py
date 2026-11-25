"""Synthetic offline contract tests; no database, source, or issued receipts."""
from datetime import datetime, timedelta, timezone
import math
import unittest

from ml.rolling72_fresh_paired_drift24_v1 import (
    bind_actual_issue, event_grouped_mae, prepare_pair, prepare_values,
)

UTC = timezone.utc
BASE = datetime(2026, 11, 25, 12, tzinfo=UTC)


def snapshot(seal, hours_ago, total, *, known_hours_ago=40, ids=("a", "b"), family="roboticket/roboticket", status="READY"):
    if known_hours_ago == 40:
        known_hours_ago = max(0.0, hours_ago - 1 / 60)
    return {"seal_id": seal, "event_id": "evt-1", "source_family": family or "roboticket/roboticket", "unit": "available_total_seats",
            "captured_at": BASE - timedelta(hours=hours_ago),
            "known_at": BASE - timedelta(hours=known_hours_ago), "available_total": total,
            "sector_ids": list(ids),
            "sector_price_area_ids": [(str(x), f"pa-{x}") for x in ids],
            "source_status": status, "content_hash": f"hash-{seal}"}


def run(history, *, origin=None, **kwargs):
    origin = origin or snapshot("o", 0, 100, known_hours_ago=0)
    defaults = {"projection_reference_at": BASE + timedelta(minutes=2),
                "issued_at": BASE + timedelta(minutes=2, seconds=10),
                "kickoff_at": BASE + timedelta(days=5), "attempts": ()}
    defaults.update(kwargs)
    return prepare_pair(origin, history, **defaults)


def values(result, method):
    return [x for x in result["forecasts"] if x["method"] == method]


class FreshPairedDrift24Tests(unittest.TestCase):
 def test_first_point_falls_back_and_preserves_zero(self):
    origin = snapshot("o", 0, 0, known_hours_ago=0)
    result = prepare_pair(origin, [], projection_reference_at=BASE + timedelta(minutes=2),
                          issued_at=BASE + timedelta(minutes=2, seconds=5),
                          kickoff_at=BASE + timedelta(days=5))
    self.assertEqual([x["prediction"] for x in values(result, "PERS")], [0, 0, 0])
    self.assertEqual([x["status"] for x in values(result, "DRIFT24")], ["FALLBACK_PERS"] * 3)
    self.assertEqual([x["fallback_reason"] for x in values(result, "DRIFT24")], ["NO_24H_ANCHOR"] * 3)


 def test_anchor_bounds_inclusive_and_latest_tie_break_by_seal_id(self):
    a = snapshot("z-seal", 24, 76)
    b = snapshot("a-seal", 30, 70)
    c = snapshot("zz-seal", 24, 80)
    out = run([a, b, c])
    self.assertEqual(out["provenance"]["anchor_seal_id"], "zz-seal")
    self.assertTrue(math.isclose(out["provenance"]["slope24"], 20 / 24))
    actual = [x["prediction"] for x in values(out, "DRIFT24")]
    expected = [100 + (20 / 24) * (h + 2 / 60) for h in (24, 48, 72)]
    self.assertTrue(all(math.isclose(a, e) for a, e in zip(actual, expected)))

 def test_anchor_at_outer_30_hour_boundary_is_eligible(self):
    out = run([snapshot("outer", 30, 70)])
    self.assertEqual(out["provenance"]["anchor_seal_id"], "outer")
    self.assertIsNone(values(out, "DRIFT24")[0]["fallback_reason"])


 def test_known_after_read_is_excluded_and_only_known_anchor_does_not_exist(self):
    future_known = snapshot("a", 25, 80, known_hours_ago=-1)
    out = run([future_known])
    self.assertEqual(values(out, "DRIFT24")[0]["fallback_reason"], "NO_24H_ANCHOR")


 def test_intervening_source_and_membership_breaks_are_explicit(self):
    anchor = snapshot("a", 26, 90)
    changed_source = snapshot("b", 3, 95, known_hours_ago=2, family="other")
    changed_scope = snapshot("c", 3, 95, known_hours_ago=2, ids=("a", "c"))
    changed_price_area = {**snapshot("d", 3, 95, known_hours_ago=2),
                          "sector_price_area_ids": [("a", "pa-new"), ("b", "pa-b")]}
    self.assertEqual(values(run([anchor, changed_source]), "DRIFT24")[0]["fallback_reason"], "SOURCE_BREAK")
    self.assertEqual(values(run([anchor, changed_scope]), "DRIFT24")[0]["fallback_reason"], "SCOPE_MISMATCH")
    self.assertEqual(values(run([anchor, changed_price_area]), "DRIFT24")[0]["fallback_reason"], "SCOPE_MISMATCH")


 def test_known_failed_attempt_breaks_support(self):
    anchor = snapshot("a", 26, 90)
    attempt = {"status": "INVALID_SOURCE", "known_at": BASE - timedelta(hours=2),
               "captured_at": BASE - timedelta(hours=2)}
    out = run([anchor], attempts=[attempt])
    self.assertEqual(values(out, "DRIFT24")[0]["fallback_reason"], "SOURCE_BREAK")


 def test_zero_clamp_source_age_and_no_rounding(self):
    falling = snapshot("a", 24, 200)
    out = run([falling])
    self.assertEqual(values(out, "DRIFT24")[2]["prediction"], 0.0)
    rising = run([snapshot("r", 24, 99.9)])
    self.assertNotEqual(values(rising, "DRIFT24")[0]["prediction"], round(values(rising, "DRIFT24")[0]["prediction"]))
    with self.assertRaisesRegex(ValueError, "source age"):
        run([falling], projection_reference_at=BASE + timedelta(hours=1, seconds=1),
            issued_at=BASE + timedelta(hours=1, seconds=2))


 def test_caller_clock_order_latency_and_common_coordinates(self):
    ref = BASE + timedelta(minutes=1)
    issued = ref + timedelta(seconds=90)
    result = run([snapshot("a", 25, 90)], projection_reference_at=ref, issued_at=issued)
    self.assertTrue(result["provenance"]["projection_reference_clock_claim"].startswith("caller_provided"))
    for h in (24, 48, 72):
        pair = [r for r in result["forecasts"] if r["horizon_hours"] == h]
        self.assertEqual(len(pair), 2)
        self.assertEqual(pair[0]["target_at"], pair[1]["target_at"])
        self.assertEqual(datetime.fromisoformat(pair[0]["target_at"]), issued + timedelta(hours=h))
    with self.assertRaisesRegex(ValueError, "90 seconds"):
        run([], projection_reference_at=ref, issued_at=issued + timedelta(microseconds=1))
    with self.assertRaisesRegex(ValueError, "follow projection"):
        run([], projection_reference_at=ref, issued_at=ref - timedelta(seconds=1))


 def test_target_crossing_kickoff_is_outside_for_both_methods(self):
    issued = BASE + timedelta(minutes=2)
    out = run([snapshot("a", 25, 90)], issued_at=issued,
              kickoff_at=issued + timedelta(hours=48))
    self.assertEqual([x["status"] for x in out["forecasts"] if x["horizon_hours"] == 48],
                     ["OUTSIDE_KICKOFF", "OUTSIDE_KICKOFF"])
    self.assertEqual([x["prediction"] for x in out["forecasts"] if x["horizon_hours"] == 48], [None, None])


 def test_invalid_current_source_is_unavailable_not_fallback(self):
    origin = snapshot("o", 0, 10, known_hours_ago=0, status="INVALID_SOURCE")
    out = prepare_pair(origin, [], projection_reference_at=BASE + timedelta(minutes=1),
                       issued_at=BASE + timedelta(minutes=1, seconds=1), kickoff_at=BASE + timedelta(days=4))
    self.assertEqual(out["bundle_status"], "UNAVAILABLE_SOURCE")
    self.assertTrue(all(x["prediction"] is None and x["status"] == "UNAVAILABLE_SOURCE" for x in out["forecasts"]))

 def test_rejects_negative_missing_ready_bad_clocks_and_duplicate_ids(self):
    for broken in (
        snapshot("n", 0, -1, known_hours_ago=0),
        {**snapshot("c", 0, 1, known_hours_ago=0), "captured_at": BASE + timedelta(seconds=1)},
        snapshot("d", 0, 1, known_hours_ago=0, ids=("a", "a")),
        {**snapshot("bool-id", 0, 1, known_hours_ago=0),
         "sector_price_area_ids": [("a", "pa-a"), (True, "pa-true")]},
    ):
        with self.assertRaises(ValueError):
            run([], origin=broken)
    missing_status = {k: v for k, v in snapshot("m", 0, 1, known_hours_ago=0).items() if k != "source_status"}
    unavailable = run([], origin=missing_status)
    self.assertEqual(unavailable["bundle_status"], "UNAVAILABLE_SOURCE")
    self.assertTrue(all(x["prediction"] is None for x in unavailable["forecasts"]))
    with self.assertRaisesRegex(ValueError, "roboticket/roboticket"):
        run([], origin=snapshot("wrong-family", 0, 1, known_hours_ago=0, family="roboticket"))

 def test_source_can_be_fresh_at_read_but_stale_at_issue_is_refused(self):
    origin = snapshot("late", 59 / 60, 100, known_hours_ago=0)
    ref = BASE + timedelta(minutes=1)
    prepared = prepare_values(origin, [], projection_reference_at=ref)
    with self.assertRaisesRegex(ValueError, "actual issued_at"):
        bind_actual_issue(prepared, issued_at=ref + timedelta(seconds=90),
                          kickoff_at=BASE + timedelta(days=3))


 def test_event_grouped_metric_weights_events_equally_and_requires_paired_rows(self):
    rows = [
        {"event_id": "a", "horizon_hours": 24, "pers": 0, "drift24": 0, "target": 0},
        {"event_id": "b", "horizon_hours": 24, "pers": 0, "drift24": 10, "target": 10},
        {"event_id": "b", "horizon_hours": 24, "pers": 0, "drift24": 10, "target": 10},
        {"event_id": "c", "horizon_hours": 24, "pers": None, "drift24": 1, "target": 0},
    ]
    result = event_grouped_mae(rows, horizon_hours=24)
    self.assertEqual(result["horizon_hours"], 24)
    self.assertEqual((result["events"], result["points"]), (2, 3))
    self.assertEqual(result["pers_event_balanced_mae"], 5)
    self.assertEqual(result["drift24_event_balanced_mae"], 0)
    self.assertEqual(result["delta_event_balanced_mae"], -5)
    with self.assertRaisesRegex(ValueError, "match"):
        event_grouped_mae(rows + [{"event_id": "a", "horizon_hours": 48, "pers": 0,
                                   "drift24": 0, "target": 0}], horizon_hours=24)


if __name__ == "__main__":
    unittest.main()
