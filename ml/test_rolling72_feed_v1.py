"""Semantic/read-only feed tests using explicitly synthetic local ledgers."""
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_feed_v1 import build_feed
from ml.rolling72_shadow_ledger_v1 import capture, create_freeze, score
from ml.test_rolling72_shadow_ledger_v1 import BASE, source


class Rolling72FeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "synthetic-shadow.sqlite"
        self.freeze = self.root / "freeze.json"
        self.issued = BASE + timedelta(minutes=3)
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=BASE + timedelta(minutes=2)):
            create_freeze(self.freeze)

    def tearDown(self):
        self.tmp.cleanup()

    def capture(self, payload=None, at=None):
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=at or self.issued):
            return capture(self.db, payload or source(), self.freeze)

    def feed(self, at=None):
        return build_feed(self.db, generated_at=at or self.issued + timedelta(minutes=1))

    def scored(self):
        self.capture()
        target = self.issued + timedelta(hours=24)
        data = json.loads(source())
        data["events"][0]["observations"].append({"snapshot_id": 5,
            "captured_at": (target - timedelta(minutes=1)).isoformat(),
            "available_total": 800, "measurement_key": "roboticket/roboticket"})
        data["exported_at"] = (target + timedelta(minutes=1)).isoformat()
        data["retrieved_at"] = (target + timedelta(minutes=2)).isoformat()
        data["export_sha256"] = _hash({key: value for key, value in data.items() if key != "export_sha256"})
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=target + timedelta(minutes=3)):
            score(self.db, json.dumps(data).encode(), self.freeze)
        return target + timedelta(minutes=4)

    def test_first_point_arbitrary_issue_has_three_actual_future_coordinates(self):
        payload = source([json.loads(source())["events"][0]["observations"][-1]])
        self.capture(payload)
        vintage = self.feed()["vintages"][0]
        self.assertEqual(len(vintage["observations"]), 1)
        self.assertEqual(vintage["observations"][0]["captured_at"], BASE.isoformat())
        self.assertNotEqual(vintage["observations"][0]["captured_at"], vintage["issued_at"])
        for point in vintage["points"]:
            self.assertEqual(point["target_at"], (self.issued + timedelta(hours=point["horizon_hours"])).isoformat())
            self.assertEqual(point["models"]["persistence"]["predicted_available_total"], 1000)
            self.assertIsNone(point["models"]["drift"]["predicted_available_total"])

    def test_zero_and_unavailable_are_different_and_no_source_secrets_exported(self):
        data = json.loads(source([json.loads(source())["events"][0]["observations"][-1]]))
        data["events"][0]["observations"][0]["available_total"] = 0
        data["secret"] = "private-secret-must-never-enter-feed"
        data["source_api_url"] = "https://private.invalid/secret"
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        self.capture(json.dumps(data).encode())
        feed = self.feed()
        self.assertNotIn("private-secret", json.dumps(feed))
        self.assertNotIn("private.invalid", json.dumps(feed))
        models = feed["vintages"][0]["points"][0]["models"]
        self.assertEqual(models["persistence"]["predicted_available_total"], 0)
        self.assertIsNone(models["pickup"]["predicted_available_total"])

    def test_export_is_read_only_and_preserves_vintages(self):
        self.capture()
        original = self.feed()["vintages"][0]
        self.capture(at=self.issued + timedelta(minutes=2))
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        feed = self.feed(self.issued + timedelta(minutes=3))
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(), before)
        self.assertEqual(len(feed["vintages"]), 2)
        self.assertEqual(feed["vintages"][0], original)

    def test_declared_stale_failure_preserves_real_prefix_and_null_coordinates(self):
        self.capture(at=self.issued + timedelta(hours=7))
        vintage = self.feed(self.issued + timedelta(hours=7, minutes=1))["vintages"][0]
        self.assertEqual(vintage["status"], "STALE_INPUT")
        self.assertGreater(len(vintage["observations"]), 0)
        self.assertTrue(all(p["target_at"] is None for p in vintage["points"]))
        self.assertTrue(all(m["predicted_available_total"] is None for p in vintage["points"] for m in p["models"].values()))

    def test_genuine_later_target_is_shared_without_entering_original_prefix(self):
        feed = self.feed(self.scored())
        vintage = feed["vintages"][0]
        persistence = vintage["points"][0]["models"]["persistence"]["score"]
        drift = vintage["points"][0]["models"]["drift"]["score"]
        self.assertEqual(persistence["target_available_total"], 800)
        self.assertEqual(persistence["absolute_error"], 200)
        self.assertEqual(persistence["target_snapshot_id"], drift["target_snapshot_id"])
        self.assertEqual(len(vintage["observations"]), 4)
        self.assertTrue(all(row["captured_at"] <= vintage["issued_at"] for row in vintage["observations"]))

    def test_incomplete_coordinates_and_numeric_null_mismatch_fail_closed(self):
        self.capture()
        with sqlite3.connect(self.db) as db:
            db.execute("delete from predictions where horizon=48 and model='pickup'")
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            self.feed()

    def test_changed_prediction_arithmetic_is_rejected(self):
        self.capture()
        with sqlite3.connect(self.db) as db:
            serialized = db.execute("select payload_json from predictions where horizon=24 and model='persistence'").fetchone()[0]
            data = json.loads(serialized); data["predicted_delta"] = 1
            db.execute("update predictions set payload_json=? where horizon=24 and model='persistence'", (json.dumps(data),))
        with self.assertRaisesRegex(ValueError, "Numeric forecast"):
            self.feed()

    def test_changed_input_hash_or_freeze_is_rejected(self):
        self.capture()
        with sqlite3.connect(self.db) as db:
            data = json.loads(db.execute("select issue_json from issues").fetchone()[0])
            data["observed_prefix"][-1]["available_total"] = 0
            db.execute("update issues set issue_json=?", (json.dumps(data),))
        with self.assertRaisesRegex(ValueError, "issue lineage"):
            self.feed()

    def test_accepted_target_requires_every_numeric_model_score(self):
        at = self.scored()
        with sqlite3.connect(self.db) as db:
            db.execute("delete from scores where model='drift'")
        with self.assertRaisesRegex(ValueError, "lacks"):
            self.feed(at)

    def test_score_arithmetic_and_source_flags_are_validated(self):
        at = self.scored()
        with sqlite3.connect(self.db) as db:
            db.execute("update scores set absolute_error=0 where model='persistence'")
        with self.assertRaisesRegex(ValueError, "arithmetic"):
            self.feed(at)

    def test_rehashed_but_malformed_target_source_flag_is_rejected(self):
        at = self.scored()
        with sqlite3.connect(self.db) as db:
            matched = json.loads(db.execute("select label_json from target_matches").fetchone()[0])
            matched["label"]["source_visible"] = "false"
            matched["label_sha256"] = _hash(matched["label"])
            db.execute("update target_matches set label_json=?", (json.dumps(matched),))
        with self.assertRaisesRegex(ValueError, "clocks/measurement"):
            self.feed(at)

    def test_score_cannot_be_exported_before_actual_acceptance(self):
        self.scored()
        with self.assertRaisesRegex(ValueError, "clocks"):
            self.feed(self.issued + timedelta(hours=24, minutes=2))

    def test_foreign_sqlite_is_refused_without_modification(self):
        with sqlite3.connect(self.db) as db:
            db.execute("create table old_private_data(value text)")
        before = self.db.read_bytes()
        with self.assertRaisesRegex(ValueError, "Not a rolling72"):
            self.feed()
        self.assertEqual(self.db.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
