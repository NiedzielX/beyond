"""Synthetic offline contract tests for the damped triplet only."""
from datetime import datetime, timedelta, timezone
import unittest

from ml.rolling72_damped_triplet_v1 import (
    METHODS, VERSION, bind_triplet_issue, prepare_triplet, prepare_triplet_values,
)

UTC = timezone.utc
BASE = datetime(2026, 11, 25, 12, tzinfo=UTC)


def snapshot(seal, hours_ago, total, *, known_hours_ago=None, status="READY"):
    if known_hours_ago is None:
        known_hours_ago = max(0, hours_ago - 1 / 60)
    return {
        "seal_id": seal, "event_id": "evt", "source_family": "roboticket/roboticket",
        "unit": "available_total_seats", "captured_at": BASE - timedelta(hours=hours_ago),
        "known_at": BASE - timedelta(hours=known_hours_ago), "available_total": total,
        "sector_price_area_ids": [("s1", "pa1")], "source_status": status,
        "content_hash": f"hash-{seal}",
    }


def run(history=(), *, origin=None, issued=None, kickoff=None):
    ref = BASE + timedelta(minutes=2)
    issued = issued or ref + timedelta(seconds=5)
    kickoff = kickoff or issued + timedelta(days=5)
    origin = origin or snapshot("o", 0, 100, known_hours_ago=0)
    return prepare_triplet(origin, history, projection_reference_at=ref,
                           issued_at=issued, kickoff_at=kickoff)


class DampedTripletTests(unittest.TestCase):
    def test_supported_triplet_has_fixed_shape_and_shared_coordinates(self):
        out = run([snapshot("a", 24, 76)])
        self.assertEqual(out["version"], VERSION)
        self.assertEqual(len(out["forecasts"]), 9)
        for horizon in (24, 48, 72):
            rows = [r for r in out["forecasts"] if r["horizon_hours"] == horizon]
            self.assertEqual([r["method"] for r in rows], list(METHODS))
            self.assertEqual(len({r["target_at"] for r in rows}), 1)
            self.assertEqual(rows[0]["target_at"], (datetime.fromisoformat(out["issued_at"]) + timedelta(hours=horizon)).isoformat())
        vals = {(r["method"], r["horizon_hours"]): r for r in out["forecasts"]}
        age = out["provenance"]["age_hours"]
        eff24 = 24 * (1 - 0.8 ** ((24 + age) / 24)) / (1 - 0.8)
        eff48 = 24 * (1 - 0.8 ** ((48 + age) / 24)) / (1 - 0.8)
        self.assertAlmostEqual(vals[("DAMPED", 24)]["prediction"], 100 + eff24)
        self.assertAlmostEqual(vals[("DAMPED", 48)]["prediction"], 100 + eff48)

    def test_prepare_values_before_issue_then_bind_without_changing_numbers(self):
        ref = BASE + timedelta(minutes=2)
        prepared = prepare_triplet_values(
            snapshot("o", 0, 100), [snapshot("a", 24, 76)],
            projection_reference_at=ref,
        )
        self.assertEqual(len(prepared["forecast_values"]), 9)
        self.assertTrue(all("target_at" not in r for r in prepared["forecast_values"]))
        issued = ref + timedelta(seconds=5)
        bound = bind_triplet_issue(prepared, issued_at=issued, kickoff_at=issued + timedelta(days=5))
        self.assertEqual(
            [row["prediction"] for row in bound["forecasts"]],
            [row["prediction"] for row in prepared["forecast_values"]],
        )
        incomplete = {**prepared, "forecast_values": prepared["forecast_values"][:-1]}
        with self.assertRaisesRegex(ValueError, "incomplete"):
            bind_triplet_issue(incomplete, issued_at=issued, kickoff_at=issued + timedelta(days=5))

    def test_fallback_and_zero_are_preserved(self):
        out = run(origin=snapshot("o", 0, 0, known_hours_ago=0))
        self.assertEqual(len(out["forecasts"]), 9)
        damped = [r for r in out["forecasts"] if r["method"] == "DAMPED"]
        self.assertEqual([r["status"] for r in damped], ["FALLBACK_PERS"] * 3)
        self.assertEqual([r["fallback_reason"] for r in damped], ["NO_24H_ANCHOR"] * 3)
        self.assertEqual([r["prediction"] for r in damped], [0, 0, 0])

    def test_zero_projection_age_preserves_the_first_day_trend(self):
        prepared = prepare_triplet_values(
            snapshot("o", 0, 100), [snapshot("a", 24, 76)],
            projection_reference_at=BASE,
        )
        rows = {r["method"]: r["prediction"] for r in prepared["forecast_values"]
                if r["horizon_hours"] == 24}
        self.assertAlmostEqual(rows["DAMPED"], rows["DRIFT24"])

    def test_kickoff_nulls_are_independent_per_horizon(self):
        issue = BASE + timedelta(minutes=2, seconds=5)
        out = run([snapshot("a", 24, 76)], issued=issue,
                  kickoff=issue + timedelta(hours=48))
        damped = [r for r in out["forecasts"] if r["method"] == "DAMPED"]
        self.assertEqual([r["status"] for r in damped], ["READY", "OUTSIDE_KICKOFF", "OUTSIDE_KICKOFF"])
        self.assertIsNone(damped[1]["prediction"])
        self.assertIsNone(damped[2]["prediction"])

    def test_unavailable_origin_produces_nine_null_rows(self):
        bad = snapshot("o", 0, 10, known_hours_ago=0, status="INVALID_SOURCE")
        out = run(origin=bad)
        damped = [r for r in out["forecasts"] if r["method"] == "DAMPED"]
        self.assertEqual(len(damped), 3)
        self.assertTrue(all(r["prediction"] is None and r["status"] == "UNAVAILABLE_SOURCE" for r in damped))


if __name__ == "__main__":
    unittest.main()
