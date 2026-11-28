"""Synthetic database-shaped binding tests for the stable-pair adapter."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from ml.rolling72_stable_pair_verified_adapter_v1 import (
    VerifiedRecordMismatch, prepare_from_verified_records,
)

UTC = timezone.utc
EVENT_ID = 27049
SOURCE_LANE = "rolling72-december-source-v1"
REF = datetime(2026, 11, 27, 12, 2, tzinfo=UTC)
BASE = REF - timedelta(minutes=2)


def row(sector, area, available):
    return {"sector_source_id": sector, "price_area_id": area,
            "sector": f"sector-{sector}", "available": available}


def membership(rows):
    sectors = sorted({str(x["sector_source_id"]) for x in rows})
    pairs = sorted([[str(x["sector_source_id"]), str(x["price_area_id"])] for x in rows])
    return {"sector_ids": sectors, "pairs": pairs}


def seal(seal_id, snapshot_id, hours_before, pair_rows, *, prior=None,
         transition="COMPLETE", gap_count=0, status="READY", known_delay=1):
    captured = BASE - timedelta(hours=hours_before)
    known = captured + timedelta(minutes=known_delay)
    total = sum(x["available"] for x in pair_rows)
    source_hash = f"{seal_id:064x}"
    snapshot_hash = f"{snapshot_id:064x}"
    payload = {
        "lane_id": SOURCE_LANE,
        "source_family": "roboticket/roboticket", "unit": "available_total_seats",
        "binding": {"ticket_event_id": EVENT_ID, "club_slug": "synthetic"},
        "snapshot": {"id": snapshot_id, "ticket_event_id": EVENT_ID,
                     "captured_at": captured.isoformat(), "available_total": total,
                     "sector_count": len({x["sector_source_id"] for x in pair_rows})},
        "sector_price_area_rows": deepcopy(pair_rows),
    }
    attempt = {
        "id": seal_id + 1000, "ticket_event_id": EVENT_ID, "snapshot_id": snapshot_id,
        "run_id": f"run-{seal_id}",
        "captured_at": captured.isoformat(), "known_at": known.isoformat(),
        "read_started_at": (captured + timedelta(seconds=2)).isoformat(),
        "read_completed_at": (known - timedelta(seconds=1)).isoformat(),
        "source_content_sha256": source_hash, "snapshot_sha256": snapshot_hash,
        "attempt_binding_sha256": "c" * 64,
        "status": status, "raw_source": deepcopy(payload),
    }
    attempt["binding_payload"] = {
        "attempt_id": attempt["id"], "run_id": attempt["run_id"], "lane_id": SOURCE_LANE,
        "ticket_event_id": EVENT_ID, "snapshot_id": snapshot_id,
        "source_content_sha256": source_hash,
        "read_started_at": attempt["read_started_at"],
        "read_completed_at": attempt["read_completed_at"],
        "known_at": attempt["known_at"], "status": status, "reason": None,
    }
    source_seal = {
        "id": seal_id, "ticket_event_id": EVENT_ID, "snapshot_id": snapshot_id,
        "attempt_id": attempt["id"], "captured_at": captured.isoformat(),
        "known_at": known.isoformat(), "read_started_at": attempt["read_started_at"],
        "read_completed_at": attempt["read_completed_at"], "available_total": total,
        "source_content_sha256": source_hash, "snapshot_sha256": snapshot_hash,
        "source_payload": deepcopy(payload), "phase": "ISSUE_WINDOW",
        "prior_seal_id": prior, "transition_status": transition,
        "gap_count": gap_count,
    }
    return source_seal, attempt


def fixture():
    a, aa = seal(1, 101, 24.5, [row(i, 1, 30) for i in range(1, 4)],
                 prior=None, transition="NO_PRIOR")
    m, ma = seal(2, 102, 12.25, [row(i, 1, 25) for i in range(1, 4)], prior=1)
    o, oa = seal(3, 103, 0, [row(i, 1, 20) for i in range(1, 4)] + [row(4, 7, 15)], prior=2)
    bundle = {
        "id": 9001, "ticket_event_id": EVENT_ID, "seal_id": 3,
        "source_known_at": o["known_at"], "source_captured_at": o["captured_at"],
        "projection_reference_at": REF, "calculation_completed_at": REF + timedelta(seconds=1),
        "issued_at": REF + timedelta(seconds=5), "fallback_reason": "SCOPE_MISMATCH",
        "source_content_sha256": o["source_content_sha256"],
        "origin_available_total": o["available_total"], "origin_membership": membership(o["source_payload"]["sector_price_area_rows"]),
        "origin_membership_sha256": "a" * 64,
        "anchor_seal_id": 1, "anchor_captured_at": a["captured_at"],
        "anchor_known_at": a["known_at"], "anchor_available_total": a["available_total"],
        "anchor_membership": membership(a["source_payload"]["sector_price_area_rows"]),
        "anchor_membership_sha256": "b" * 64,
    }
    return bundle, [a, m, o], [aa, ma, oa]


def run(bundle=None, seals=None, attempts=None, *, verified_attempt_ids=None,
        expected_source_lane_id=SOURCE_LANE, **changes):
    b, ss, aa = fixture()
    b = bundle or b
    ss = seals or ss
    aa = attempts or aa
    b = deepcopy(b)
    b.update(changes.pop("bundle_changes", {}))
    return prepare_from_verified_records(
        b, ss, aa,
        verified_bundle_ids={9001}, verified_seal_ids={1, 2, 3},
        verified_attempt_ids=(verified_attempt_ids if verified_attempt_ids is not None
                              else {1001, 1002, 1003}), **changes,
        expected_source_lane_id=expected_source_lane_id,
    )


class VerifiedBundleAdapterTests(unittest.TestCase):
    def test_adapts_exact_bundle_boundary_to_internal_event_and_candidate(self):
        result = run()
        self.assertEqual(result["event_id"], EVENT_ID)
        self.assertEqual(result["support_status"], "SUPPORTED")
        self.assertEqual(result["provenance"]["bundle_id"], 9001)
        self.assertEqual(result["provenance"]["ticket_event_id"], EVENT_ID)
        self.assertEqual(result["provenance"]["interval_seal_ids"], [1, 2, 3])
        self.assertEqual(result["provenance"]["anchor"]["source_content_sha256"], f"{1:064x}")
        self.assertEqual(result["provenance"]["origin"]["source_content_sha256"], f"{3:064x}")
        self.assertEqual(result["provenance"]["projection_reference_at"], REF)

    def test_internal_event_binding_is_not_replaced_by_external_fixture_id(self):
        bundle, seals, attempts = fixture()
        seals[1]["source_payload"]["binding"]["ticket_event_id"] = 777
        attempts[1]["raw_source"] = deepcopy(seals[1]["source_payload"])
        with self.assertRaisesRegex(VerifiedRecordMismatch, "binding ticket_event_id"):
            run(bundle=bundle, seals=seals, attempts=attempts)

    def test_bundle_origin_digest_and_timestamp_are_exact_boundaries(self):
        bundle, seals, attempts = fixture()
        bundle["source_content_sha256"] = "f" * 64
        with self.assertRaisesRegex(VerifiedRecordMismatch, "origin seal does not match"):
            run(bundle=bundle, seals=seals, attempts=attempts)
        bundle, seals, attempts = fixture()
        bundle["source_captured_at"] = (BASE + timedelta(seconds=1)).isoformat()
        with self.assertRaisesRegex(VerifiedRecordMismatch, "origin seal does not match"):
            run(bundle=bundle, seals=seals, attempts=attempts)

    def test_anchor_membership_and_boundary_identity_are_checked(self):
        bundle, seals, attempts = fixture()
        bundle["anchor_membership"] = {"sector_ids": ["wrong"], "pairs": [["wrong", "1"]]}
        with self.assertRaisesRegex(VerifiedRecordMismatch, "anchor membership"):
            run(bundle=bundle, seals=seals, attempts=attempts)
        bundle, seals, attempts = fixture()
        bundle["anchor_seal_id"] = 2
        with self.assertRaisesRegex(VerifiedRecordMismatch, "anchor seal does not match"):
            run(bundle=bundle, seals=seals, attempts=attempts)

    def test_linked_attempt_id_hash_clock_and_raw_payload_are_verified(self):
        bundle, seals, attempts = fixture()
        attempts[1]["source_content_sha256"] = "f" * 64
        with self.assertRaisesRegex(VerifiedRecordMismatch, "source digest mismatch"):
            run(bundle=bundle, seals=seals, attempts=attempts)
        bundle, seals, attempts = fixture()
        seals[1]["attempt_id"] = 777
        with self.assertRaisesRegex(VerifiedRecordMismatch, "lacks caller verification"):
            run(bundle=bundle, seals=seals, attempts=attempts)
        bundle, seals, attempts = fixture()
        attempts[1]["known_at"] = (BASE + timedelta(hours=1)).isoformat()
        with self.assertRaisesRegex(VerifiedRecordMismatch, "known_at mismatch"):
            run(bundle=bundle, seals=seals, attempts=attempts)
        bundle, seals, attempts = fixture()
        attempts[1]["raw_source"]["unit"] = "other"
        with self.assertRaisesRegex(VerifiedRecordMismatch, "payload differs"):
            run(bundle=bundle, seals=seals, attempts=attempts)

    def test_endpoint_attempt_must_be_ready(self):
        bundle, seals, attempts = fixture()
        attempts[1]["status"] = "INVALID_SOURCE"
        with self.assertRaisesRegex(VerifiedRecordMismatch, "not READY"):
            run(bundle=bundle, seals=seals, attempts=attempts)

    def test_source_lane_attempt_binding_and_read_clock_are_explicit(self):
        bundle, seals, attempts = fixture()
        with self.assertRaisesRegex(VerifiedRecordMismatch, "unexpected source lane"):
            run(bundle=bundle, seals=seals, attempts=attempts,
                expected_source_lane_id="rolling72-mvp-research-v1")
        bundle, seals, attempts = fixture()
        attempts[1]["binding_payload"]["ticket_event_id"] = 999
        with self.assertRaisesRegex(VerifiedRecordMismatch, "attempt binding payload"):
            run(bundle=bundle, seals=seals, attempts=attempts)
        bundle, seals, attempts = fixture()
        attempts[1]["attempt_binding_sha256"] = "bad"
        with self.assertRaisesRegex(VerifiedRecordMismatch, "attempt binding hash"):
            run(bundle=bundle, seals=seals, attempts=attempts)
        bundle, seals, attempts = fixture()
        late = (datetime.fromisoformat(attempts[1]["known_at"]) + timedelta(seconds=1)).isoformat()
        attempts[1]["read_completed_at"] = late
        seals[1]["read_completed_at"] = late
        with self.assertRaisesRegex(VerifiedRecordMismatch, "read clocks are out of order"):
            run(bundle=bundle, seals=seals, attempts=attempts)

    def test_late_known_interval_seal_and_unverified_seal_fail_closed(self):
        bundle, seals, attempts = fixture()
        seals[1]["known_at"] = (REF + timedelta(seconds=1)).isoformat()
        attempts[1]["known_at"] = seals[1]["known_at"]
        attempts[1]["binding_payload"]["known_at"] = seals[1]["known_at"]
        with self.assertRaisesRegex(VerifiedRecordMismatch, "not known by the projection reference"):
            run(bundle=bundle, seals=seals, attempts=attempts)
        bundle, seals, attempts = fixture()
        with self.assertRaisesRegex(VerifiedRecordMismatch, "lacks caller verification"):
            prepare_from_verified_records(
                bundle, seals, attempts, verified_bundle_ids={9001},
                verified_seal_ids={1, 3}, verified_attempt_ids={1001, 1002, 1003},
                expected_source_lane_id=SOURCE_LANE,
            )

    def test_known_adverse_attempt_vetoes_candidate_and_uses_explicit_pers(self):
        bundle, seals, attempts = fixture()
        bad = {
            "id": 2000, "ticket_event_id": EVENT_ID, "snapshot_id": None,
            "captured_at": None, "known_at": (BASE - timedelta(hours=5)).isoformat(),
            "status": "INVALID_SOURCE",
        }
        result = run(bundle=bundle, seals=seals, attempts=attempts + [bad],
                     verified_attempt_ids={1001, 1002, 1003, 2000})
        self.assertEqual(result["support_status"], "KNOWN_FAILED_SOURCE_ATTEMPT")
        self.assertEqual(result["candidate_policy_status"], "FALLBACK_PERS")
        self.assertEqual(result["provenance"]["verified_adverse_attempt_ids"], [2000])
        self.assertTrue(all(row["prediction"] == bundle["origin_available_total"]
                            for row in result["forecast_values"]))

    def test_future_adverse_attempt_is_not_used_before_known_at(self):
        bundle, seals, attempts = fixture()
        future = {
            "id": 2001, "ticket_event_id": EVENT_ID, "snapshot_id": None,
            "captured_at": None, "known_at": (REF + timedelta(seconds=1)).isoformat(),
            "status": "INVALID_SOURCE",
        }
        result = run(bundle=bundle, seals=seals, attempts=attempts + [future])
        self.assertEqual(result["support_status"], "SUPPORTED")
        self.assertEqual(result["provenance"]["verified_adverse_attempt_ids"], [])

    def test_wrong_bundle_and_seal_cap_are_rejected(self):
        bundle, seals, attempts = fixture()
        bundle["fallback_reason"] = "NO_24H_ANCHOR"
        with self.assertRaisesRegex(VerifiedRecordMismatch, "only accepts SCOPE_MISMATCH"):
            run(bundle=bundle, seals=seals, attempts=attempts)
        bundle, seals, attempts = fixture()
        with self.assertRaisesRegex(VerifiedRecordMismatch, "cap exceeded"):
            run(bundle=bundle, seals=seals + [deepcopy(seals[1]) for _ in range(128)], attempts=attempts)
        bundle, seals, attempts = fixture()
        with self.assertRaisesRegex(VerifiedRecordMismatch, "attempt cap exceeded"):
            run(bundle=bundle, seals=seals, attempts=attempts + [deepcopy(attempts[0]) for _ in range(510)])


if __name__ == "__main__":
    unittest.main()
