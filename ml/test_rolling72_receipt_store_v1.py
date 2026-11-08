"""Actual knowledge bounds and immutable feature-store transaction tests."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.demand_engine.test_rolling72_features_v1 import ISSUE, row
from ml.rolling72_receipt_store_v1 import prepare_receipt, persist_batch


def export_payload(rows=None, retrieve_delay_minutes=1):
    event = {"ticket_event_id": 1, "club_slug": "club",
             "kickoff_at": (ISSUE + timedelta(days=50)).isoformat(),
             "observations": [row()] if rows is None else rows}
    data = {"version": "daily-inventory-public-export-v1", "exported_at": ISSUE.isoformat(),
            "retrieved_at": (ISSUE + timedelta(minutes=retrieve_delay_minutes)).isoformat(),
            "events": [event]}
    data["export_sha256"] = _hash(data)
    return json.dumps(data).encode()


def rehash(batch):
    batch["batch_sha256"] = _hash({k: v for k, v in batch.items() if k != "batch_sha256"})
    return batch


class ReceiptStoreTests(unittest.TestCase):
    def setUp(self):
        self.issued = ISSUE + timedelta(minutes=2)

    def test_original_receipt_is_a_conservative_bound_not_capture_time(self):
        batch = prepare_receipt(export_payload([row(age=72), row(2)]), self.issued)
        issue = batch["records"][0]["issue"]
        self.assertEqual(issue["status"], "READY")
        self.assertTrue(all(r["known_at"] == batch["receipt"]["retrieved_at"] for r in issue["observed_prefix"]))
        self.assertEqual(issue["event"]["known_at"], batch["receipt"]["retrieved_at"])
        self.assertFalse(batch["receipt"]["historical_ingestion_known_at_proven"])
        self.assertEqual(batch["receipt"]["intervention_status"], "UNKNOWN")
        self.assertEqual(batch["forecast_count"], 0)

    def test_no_historical_issue_before_read_receipt(self):
        with self.assertRaisesRegex(ValueError, "before the original receipt"):
            prepare_receipt(export_payload(), ISSUE)

    def test_old_source_stays_stale_instead_of_becoming_fresh(self):
        batch = prepare_receipt(export_payload([row(age=7)]), self.issued)
        self.assertEqual(batch["records"][0]["issue"]["status"], "STALE_INPUT")
        self.assertEqual(batch["records"][0]["horizons"][0]["features"], {})

    def test_single_point_zero_is_preserved_without_invented_source_flags(self):
        issue = prepare_receipt(export_payload([row(value=0)]), self.issued)["records"][0]["issue"]
        self.assertEqual(issue["status"], "READY")
        self.assertEqual(issue["last_available_total"], 0)
        self.assertIsNone(issue["observed_prefix"][0]["source_active"])

    def test_source_hash_and_invalid_receipt_clocks_fail(self):
        data = json.loads(export_payload())
        data["events"][0]["observations"][0]["available_total"] = 0
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            prepare_receipt(json.dumps(data).encode(), self.issued)
        with self.assertRaisesRegex(ValueError, "follows retrieval"):
            prepare_receipt(export_payload(retrieve_delay_minutes=-1), self.issued)

    def test_snapshot_after_cutoff_cannot_be_smuggled_into_receipt(self):
        with self.assertRaisesRegex(ValueError, "exceeds"):
            prepare_receipt(export_payload([row(age=-.01)]), self.issued)

    def test_idempotent_append_and_three_horizon_feature_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "features.sqlite"
            batch = prepare_receipt(export_payload(), self.issued)
            self.assertEqual(persist_batch(path, batch)["inserted_issue_count"], 1)
            self.assertEqual(persist_batch(path, batch)["inserted_issue_count"], 0)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("select count(*) from receipts").fetchone()[0], 1)
                self.assertEqual(db.execute("select count(*) from feature_rows").fetchone()[0], 3)
                self.assertEqual({r[0] for r in db.execute("select name from sqlite_master where type='table'")},
                                 {"receipts", "issues", "feature_rows"})

    def test_immutable_issue_conflict_does_not_overwrite_or_add_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "features.sqlite"
            batch = prepare_receipt(export_payload(), self.issued)
            persist_batch(path, batch)
            with sqlite3.connect(path) as db:
                original = db.execute("select payload_json from issues").fetchone()[0]
            changed = prepare_receipt(export_payload([row(value=999)]), self.issued)
            with self.assertRaisesRegex(ValueError, "Immutable issue conflict"):
                persist_batch(path, changed)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("select payload_json from issues").fetchone()[0], original)
                self.assertEqual(db.execute("select count(*) from receipts").fetchone()[0], 1)

    def test_transaction_rolls_back_new_rows_before_later_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "features.sqlite"
            persist_batch(path, prepare_receipt(export_payload(), self.issued))
            data = json.loads(export_payload([row(value=999)]))
            # New event is inserted first; second event conflicts with existing issue.
            new = deepcopy(data["events"][0]); new["ticket_event_id"] = 2
            data["events"].insert(0, new)
            data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
            batch = prepare_receipt(json.dumps(data).encode(), self.issued)
            batch["records"].reverse()
            rehash(batch)
            with self.assertRaisesRegex(ValueError, "Immutable issue conflict"):
                persist_batch(path, batch)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("select count(*) from issues").fetchone()[0], 1)
                self.assertEqual(db.execute("select count(*) from feature_rows").fetchone()[0], 3)

    def test_new_vintage_never_rewrites_old_features(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "features.sqlite"
            payload = export_payload()
            first = prepare_receipt(payload, self.issued)
            second = prepare_receipt(payload, self.issued + timedelta(hours=1))
            persist_batch(path, first)
            persist_batch(path, second)
            with sqlite3.connect(path) as db:
                rows = db.execute("select payload_json from issues order by issued_at").fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(json.loads(rows[0][0]), first["records"][0]["issue"])

    def test_existing_foreign_ledger_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "old.sqlite"
            with sqlite3.connect(path) as db:
                db.execute("create table old_predictions(value text)")
            with self.assertRaisesRegex(ValueError, "foreign/frozen"):
                persist_batch(path, prepare_receipt(export_payload(), self.issued))
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("pragma application_id").fetchone()[0], 0)
                self.assertEqual(db.execute("select name from sqlite_master where type='table'").fetchall(), [("old_predictions",)])

    def test_tampering_detected_even_when_batch_hash_is_recomputed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "features.sqlite"
            batch = prepare_receipt(export_payload(), self.issued)
            batch["records"][0]["horizons"][0]["features"]["last_available_total"] = 0
            with self.assertRaisesRegex(ValueError, "canonical issue"):
                persist_batch(path, rehash(batch))
            self.assertFalse(path.exists())

    def test_receipt_bound_cannot_be_backdated_in_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = prepare_receipt(export_payload(), self.issued)
            batch["receipt"]["retrieved_at"] = (self.issued + timedelta(days=1)).isoformat()
            with self.assertRaisesRegex(ValueError, "knowledge bound"):
                persist_batch(Path(directory) / "features.sqlite", rehash(batch))


if __name__ == "__main__":
    unittest.main()
