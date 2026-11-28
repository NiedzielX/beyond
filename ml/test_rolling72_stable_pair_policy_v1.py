"""Tests for full-policy composition at parent issue coordinates."""
from datetime import datetime, timedelta, timezone
import unittest
from zoneinfo import ZoneInfo

from ml.rolling72_stable_pair_candidate_v1 import HORIZONS, VERSION, prepare_stable_pair_candidate
from ml.rolling72_stable_pair_policy_v1 import compose_stable_pair_policy
from ml.test_rolling72_stable_pair_candidate_v1 import REF, interval


def parent(fallback=None, *, kickoff_hours=96, origin=100, issued=None):
    issued = issued or datetime(2026, 11, 27, 16, 12, tzinfo=timezone.utc)
    utc_issued = issued.astimezone(timezone.utc)
    bundle = {
        "id": 14, "ticket_event_id": 5678, "seal_id": 23, "anchor_seal_id": 12,
        "issued_at": issued, "kickoff_at": utc_issued + timedelta(hours=kickoff_hours),
        "projection_reference_at": utc_issued - timedelta(seconds=1),
        "source_captured_at": utc_issued - timedelta(minutes=5),
        "source_known_at": utc_issued - timedelta(minutes=4),
        "origin_available_total": origin, "fallback_reason": fallback,
        "drift_status": "FALLBACK_PERS" if fallback else "READY",
    }
    predictions = []
    for h in HORIZONS:
        target = utc_issued + timedelta(hours=h)
        outside = target >= bundle["kickoff_at"]
        for method in ("PERS", "DRIFT24"):
            drift = method == "DRIFT24"
            predictions.append({
                "bundle_id": bundle["id"], "ticket_event_id": bundle["ticket_event_id"],
                "horizon_hours": h, "issued_at": utc_issued, "target_at": target,
                "method": method,
                "status": "OUTSIDE_KICKOFF" if outside else bundle["drift_status"] if drift else "READY",
                "prediction": None if outside else 50 if drift and fallback is None else origin,
                "fallback_reason": fallback if drift and not outside else None,
            })
    return bundle, predictions


def candidate(bundle, status="SUPPORTED"):
    return {
        "version": VERSION, "eligible_parent_fallback": True,
        "event_id": bundle["ticket_event_id"], "origin_seal_id": bundle["seal_id"],
        "anchor_seal_id": bundle["anchor_seal_id"],
        "origin_available_total": bundle["origin_available_total"],
        "projection_reference_at": bundle["projection_reference_at"],
        "candidate_policy_status": status,
        "support_status": "SUPPORTED" if status == "SUPPORTED" else "INSUFFICIENT_SUPPORT",
        "forecast_values": [
            {"horizon_hours": h, "status": "READY", "prediction": 120 + h} for h in HORIZONS
        ],
    }


class StablePairFullPolicyTests(unittest.TestCase):
    def test_ready_drift_is_preserved(self):
        rows = compose_stable_pair_policy(*parent())
        self.assertEqual([row["status"] for row in rows], ["INHERITED_DRIFT24"] * 3)
        self.assertEqual([row["prediction"] for row in rows], [50, 50, 50])

    def test_supported_scope_override_preserves_clocks_and_kickoff(self):
        bundle, parents = parent("SCOPE_MISMATCH", kickoff_hours=72)
        rows = compose_stable_pair_policy(bundle, parents, candidate(bundle))
        self.assertEqual([row["status"] for row in rows], [
            "STABLE_PAIR_OVERRIDE", "STABLE_PAIR_OVERRIDE", "OUTSIDE_KICKOFF",
        ])
        self.assertEqual([row["prediction"] for row in rows], [144, 168, None])
        self.assertEqual([row["stable_pair_support_reason"] for row in rows], ["SUPPORTED", "SUPPORTED", None])
        self.assertEqual([row["target_at"] for row in rows], [
            bundle["issued_at"] + timedelta(hours=h) for h in HORIZONS
        ])

    def test_candidate_arithmetic_and_full_policy_use_same_endpoint(self):
        seals = interval(extra_origin=15)
        anchor, _, origin = seals
        bundle, parents = parent(
            "SCOPE_MISMATCH", origin=origin["available_total"], issued=REF + timedelta(seconds=1),
        )
        for seal in seals:
            seal["event_id"] = bundle["ticket_event_id"]
        bundle["seal_id"] = origin["seal_id"]
        bundle["anchor_seal_id"] = anchor["seal_id"]
        bundle["source_captured_at"] = origin["captured_at"]
        bundle["source_known_at"] = origin["known_at"]
        result = prepare_stable_pair_candidate(
            origin, seals, anchor_seal_id=anchor["seal_id"],
            parent_fallback_reason="SCOPE_MISMATCH", projection_reference_at=REF,
        )
        rows = compose_stable_pair_policy(bundle, parents, result)
        self.assertEqual([row["status"] for row in rows], ["STABLE_PAIR_OVERRIDE"] * 3)
        self.assertEqual([row["prediction"] for row in rows],
                         [row["prediction"] for row in result["forecast_values"]])

    def test_scope_failure_inherits_pers_and_reports_reason(self):
        bundle, parents = parent("SCOPE_MISMATCH", origin=0)
        rows = compose_stable_pair_policy(bundle, parents, candidate(bundle, "FALLBACK_PERS"))
        self.assertEqual([row["status"] for row in rows], ["INHERITED_PERS"] * 3)
        self.assertEqual([row["prediction"] for row in rows], [0, 0, 0])
        self.assertEqual(rows[0]["stable_pair_support_reason"], "INSUFFICIENT_SUPPORT")
        self.assertEqual(compose_stable_pair_policy(bundle, parents)[0]["stable_pair_support_reason"],
                         "MISSING_CANDIDATE_INPUT")

    def test_other_parent_fallback_cannot_be_replaced(self):
        bundle, parents = parent("SOURCE_BREAK")
        rows = compose_stable_pair_policy(bundle, parents)
        self.assertEqual([row["fallback_reason"] for row in rows], ["SOURCE_BREAK"] * 3)
        with self.assertRaisesRegex(ValueError, "does not bind"):
            compose_stable_pair_policy(bundle, parents, candidate(bundle))

    def test_bad_candidate_or_parent_coordinates_are_rejected(self):
        bundle, predictions = parent("SCOPE_MISMATCH")
        replacement = candidate(bundle)
        replacement["event_id"] = 123
        with self.assertRaisesRegex(ValueError, "does not bind"):
            compose_stable_pair_policy(bundle, predictions, replacement)
        replacement = candidate(bundle)
        replacement["forecast_values"][0]["prediction"] = float("nan")
        with self.assertRaisesRegex(ValueError, "complete numeric forecasts"):
            compose_stable_pair_policy(bundle, predictions, replacement)
        replacement = candidate(bundle)
        replacement["support_status"] = "INSUFFICIENT_SUPPORT"
        with self.assertRaisesRegex(ValueError, "support status disagrees"):
            compose_stable_pair_policy(bundle, predictions, replacement)
        predictions[0]["target_at"] += timedelta(seconds=1)
        with self.assertRaisesRegex(ValueError, "clocks disagree"):
            compose_stable_pair_policy(bundle, predictions, candidate(bundle))

    def test_elapsed_time_on_daylight_saving_boundary(self):
        issued = datetime(2026, 3, 28, 15, 30, tzinfo=ZoneInfo("Europe/Warsaw"))
        bundle, parents = parent(issued=issued)
        rows = compose_stable_pair_policy(bundle, parents)
        self.assertEqual(rows[0]["target_at"].astimezone(issued.tzinfo).hour, 16)

    def test_issue_latency_and_source_age_limits_are_inclusive(self):
        bundle, parents = parent()
        bundle["projection_reference_at"] = bundle["issued_at"] - timedelta(seconds=90)
        bundle["source_captured_at"] = bundle["issued_at"] - timedelta(hours=1)
        self.assertEqual(len(compose_stable_pair_policy(bundle, parents)), 3)
        for field in ("projection_reference_at", "source_captured_at"):
            late = {**bundle, field: bundle[field] - timedelta(microseconds=1)}
            with self.assertRaisesRegex(ValueError, "exceeds its limit"):
                compose_stable_pair_policy(late, parents)
        unordered = {**bundle, "source_known_at": bundle["projection_reference_at"] + timedelta(seconds=1)}
        with self.assertRaisesRegex(ValueError, "clocks are out of order"):
            compose_stable_pair_policy(unordered, parents)


if __name__ == "__main__":
    unittest.main()
