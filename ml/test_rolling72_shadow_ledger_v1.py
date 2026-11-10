"""Actual-time issuance, source freeze and immutable later target matching."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
import unittest

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_shadow_ledger_v1 import capture, create_freeze, report, score


BASE = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)


def source(rows=None, exported=None, retrieved=None):
    if rows is None:
        rows = [{"snapshot_id": i, "captured_at": (BASE - timedelta(hours=age)).isoformat(),
                 "available_total": value, "measurement_key": "roboticket/roboticket"}
                for i, age, value in ((1, 48, 1480), (2, 25, 1250), (3, 12, 1120), (4, 0, 1000))]
    data = {"version": "daily-inventory-public-export-v1", "exported_at": (exported or BASE).isoformat(),
            "retrieved_at": (retrieved or BASE + timedelta(minutes=1)).isoformat(),
            "events": [{"ticket_event_id": 1, "club_slug": "club", "kickoff_at": (BASE + timedelta(days=50)).isoformat(),
                        "observations": rows}]}
    data["export_sha256"] = _hash(data)
    return json.dumps(data).encode()


class ShadowLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.freeze = self.root / "freeze.json"
        self.db = self.root / "new-shadow.sqlite"
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=BASE + timedelta(minutes=2)):
            create_freeze(self.freeze)
        self.issued = BASE + timedelta(minutes=3)

    def tearDown(self):
        self.tmp.cleanup()

    def capture(self, payload=None, at=None):
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=at or self.issued):
            return capture(self.db, payload or source(), self.freeze)

    def later_source(self, target, value=800, later=False):
        data = json.loads(source())
        data["events"][0]["observations"].append({
            "snapshot_id": 6 if later else 5,
            "captured_at": (target if later else target - timedelta(minutes=1)).isoformat(),
            "available_total": value, "measurement_key": "roboticket/roboticket"})
        data["exported_at"] = (target + timedelta(minutes=1 if not later else 4)).isoformat()
        data["retrieved_at"] = (target + timedelta(minutes=2 if not later else 5)).isoformat()
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        return json.dumps(data).encode()

    def test_real_issue_clock_future_targets_and_exact_prediction_count(self):
        result = self.capture()
        self.assertEqual(result["numeric_forecast_count"], 6)
        self.assertEqual(result["prediction_status_rows"], 9)
        self.assertEqual(result["issued_at"], self.issued.isoformat())
        with sqlite3.connect(self.db) as db:
            targets = db.execute("select distinct horizon,target_at from predictions order by horizon").fetchall()
            for h, at in targets:
                self.assertEqual(at, (self.issued + timedelta(hours=h)).isoformat())
            self.assertEqual(db.execute("pragma foreign_key_check").fetchall(), [])

    def test_first_point_keeps_persistence_without_fake_drift_or_pickup(self):
        payload = source([json.loads(source())["events"][0]["observations"][-1]])
        result = self.capture(payload)
        self.assertEqual(result["numeric_forecast_count"], 3)
        self.assertEqual(result["prediction_status_rows"], 9)

    def test_same_issue_is_never_replaced_and_next_issue_keeps_old_bytes(self):
        self.capture()
        with sqlite3.connect(self.db) as db:
            original = db.execute("select * from predictions order by horizon,model").fetchall()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.capture()
        self.capture(at=self.issued + timedelta(hours=1))
        with sqlite3.connect(self.db) as db:
            old = db.execute("select * from predictions where issued_at=? order by horizon,model", (self.issued.isoformat(),)).fetchall()
        self.assertEqual(original, old)

    def test_source_received_after_issue_and_future_freeze_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "before the original receipt"):
            self.capture(source(retrieved=self.issued + timedelta(seconds=1)))
        with self.assertRaisesRegex(ValueError, "later than execution"):
            self.capture(at=BASE)
        self.assertFalse(self.db.exists())

    def test_foreign_ledger_not_touched(self):
        with sqlite3.connect(self.db) as db:
            db.execute("create table old_forecasts(value text)")
        with self.assertRaisesRegex(ValueError, "foreign/frozen"):
            self.capture()
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select name from sqlite_master where type='table'").fetchall(), [("old_forecasts",)])

    def test_freeze_hash_and_code_changed_before_capture_are_rejected(self):
        data = json.loads(self.freeze.read_text())
        data["code_sha256"]["ml/demand_engine/rolling72_features_v1.py"] = "0" * 64
        data["freeze_sha256"] = _hash({k: v for k, v in data.items() if k != "freeze_sha256"})
        self.freeze.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "code changed"):
            self.capture()
        self.assertFalse(self.db.exists())

    def test_pending_targets_do_not_produce_zero_scores(self):
        self.capture()
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=self.issued + timedelta(hours=1)):
            result = score(self.db, source(), self.freeze)
            summary = report(self.db)
        self.assertEqual(result["accepted_targets"], 0)
        self.assertEqual(summary["scores"], 0)
        self.assertEqual(summary["pending_targets"], 3)
        self.assertEqual(summary["metrics"], {})

    def test_first_genuine_label_is_frozen_even_when_later_read_is_closer(self):
        self.capture()
        target = self.issued + timedelta(hours=24)
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=target + timedelta(minutes=3)):
            result = score(self.db, self.later_source(target), self.freeze)
        self.assertEqual(result["accepted_targets"], 1)
        self.assertEqual(result["added_scores"], 2)
        with sqlite3.connect(self.db) as db:
            before = db.execute("select * from scores order by model").fetchall()
            label = json.loads(db.execute("select label_json from target_matches").fetchone()[0])
        self.assertEqual(label["label"]["available_total"], 800)
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=target + timedelta(minutes=6)):
            retry = score(self.db, self.later_source(target, 900, later=True), self.freeze)
            summary = report(self.db)
        self.assertEqual(retry["accepted_targets"], 0)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(before, db.execute("select * from scores order by model").fetchall())
        self.assertEqual(summary["metrics"]["+24h/persistence"]["event_balanced_mae"], 200)

    def test_invalid_latest_future_value_cannot_fallback_to_old_label(self):
        self.capture()
        target = self.issued + timedelta(hours=24)
        data = json.loads(self.later_source(target))
        data["events"][0]["observations"][-1]["available_total"] = None
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=target + timedelta(minutes=3)):
            result = score(self.db, json.dumps(data).encode(), self.freeze)
            summary = report(self.db)
        self.assertEqual(result["accepted_targets"], 0)
        self.assertEqual(summary["mature_unmatched_targets"], 1)

    def test_one_immutable_freeze_per_ledger(self):
        self.capture()
        other = self.root / "other-freeze.json"
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=self.issued + timedelta(seconds=1)):
            create_freeze(other)
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=self.issued + timedelta(minutes=1)):
            with self.assertRaisesRegex(ValueError, "different immutable freeze"):
                capture(self.db, source(), other)

    def test_changed_old_prefix_payload_rejects_score_and_rolls_back_receipt(self):
        self.capture()
        target = self.issued + timedelta(hours=24)
        data = json.loads(self.later_source(target))
        data["events"][0]["observations"][3]["available_total"] = 9999
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=target + timedelta(minutes=3)):
            with self.assertRaisesRegex(ValueError, "snapshot payload conflict"):
                score(self.db, json.dumps(data).encode(), self.freeze)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select count(*) from sources").fetchone()[0], 1)
            self.assertEqual(db.execute("select count(*) from target_matches").fetchone()[0], 0)
            self.assertEqual(db.execute("select count(*) from scores").fetchone()[0], 0)

    def test_future_observation_seen_while_pending_cannot_be_revised_later(self):
        self.capture()
        target = self.issued + timedelta(hours=24)
        data = json.loads(source())
        data["events"][0]["observations"].append({"snapshot_id": 5,
            "captured_at": (target - timedelta(hours=1)).isoformat(), "available_total": 800,
            "measurement_key": "roboticket/roboticket"})
        data["exported_at"] = (target - timedelta(minutes=50)).isoformat()
        data["retrieved_at"] = (target - timedelta(minutes=49)).isoformat()
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=target - timedelta(minutes=48)):
            self.assertEqual(score(self.db, json.dumps(data).encode(), self.freeze)["accepted_targets"], 0)
        data["events"][0]["observations"][-1]["available_total"] = 900
        data["exported_at"] = (target + timedelta(minutes=1)).isoformat()
        data["retrieved_at"] = (target + timedelta(minutes=2)).isoformat()
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=target + timedelta(minutes=3)):
            with self.assertRaisesRegex(ValueError, "snapshot payload conflict"):
                score(self.db, json.dumps(data).encode(), self.freeze)

    def test_equivalent_numeric_encoding_and_new_receipt_bound_are_compatible(self):
        self.capture()
        data = json.loads(source())
        for row in data["events"][0]["observations"]:
            row["available_total"] = float(row["available_total"])
        data["retrieved_at"] = self.issued.isoformat()
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        later = self.capture(json.dumps(data).encode(), at=self.issued + timedelta(minutes=1))
        self.assertEqual(later["numeric_forecast_count"], 6)


if __name__ == "__main__":
    unittest.main()
