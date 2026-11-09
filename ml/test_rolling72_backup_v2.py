"""Synthetic-only private v2 recovery and hostile/corrupt bundle checks."""
import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zlib

from threadpoolctl import threadpool_limits

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_backup_v2 import (
    BUCKET, MAX_INFLATED_BYTES, MAX_SOURCE_FILES, PREFIX, VERSION,
    Rolling72Storage, _digest, _encode, backup, make_bundle, restore,
)
from ml.rolling72_offline_challenger_v2 import fit_once
from ml.rolling72_paired_shadow_v2 import capture, create_freeze
from ml.test_rolling72_offline_challenger_v2 import synthetic_dataset


def unpack(raw):
    return json.loads(zlib.decompress(base64.b64decode(json.loads(raw)["payload"])))


def repack(bundle):
    bundle["bundle_sha256"] = _hash({k: v for k, v in bundle.items() if k != "bundle_sha256"})
    body = _encode(bundle)
    return _encode({"version": VERSION, "encoding": "zlib+base64", "payload_sha256": _digest(body),
                    "payload_bytes": len(body), "payload": base64.b64encode(zlib.compress(body)).decode()})


def replace_file(bundle, name, value):
    entry = next(p for p in bundle["files"] if p["name"] == name)
    entry.update({"base64": base64.b64encode(value).decode(), "sha256": _digest(value), "bytes": len(value)})


class MemoryStorage:
    def __init__(self, corrupt_second_read=False):
        self.objects, self.reads, self.privacy_checks = {}, 0, 0
        self.corrupt_second_read = corrupt_second_read

    def ensure_private_bucket(self):
        self.privacy_checks += 1

    def read(self, key):
        Rolling72Storage._key(key)
        self.reads += 1
        raw = self.objects[key]
        return raw + b"bad" if self.corrupt_second_read and self.reads >= 2 else raw

    def put_verified(self, key, raw, content_type):
        Rolling72Storage._key(key)
        if content_type != "application/json" or (key in self.objects and self.objects[key] != raw):
            raise ValueError("Immutable fake storage conflict")
        self.objects.setdefault(key, raw)
        if self.read(key) != raw:
            raise ValueError("Fake upload read-back mismatch")
        return {"key": key, "sha256": _digest(raw), "bytes": len(raw)}


class Rolling72V2RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory()
        cls.base_model = Path(cls.shared.name) / "model"
        with threadpool_limits(limits=1):
            fit_once(cls.base_model, synthetic_dataset(), synthetic_test=True)
        cls.base = datetime.now(timezone.utc) + timedelta(minutes=10)

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.artifact = self.root / "model"
        shutil.copytree(self.base_model, self.artifact)
        self.ledger, self.freeze = self.root / "ledger.sqlite", self.root / "freeze.json"
        self.source, self.registry = self.root / "source.json", self.root / "registry.json"
        self.registry.write_text(json.dumps([{"id": 999, "provider": "roboticket", "club_slug": "club",
                                             "source_domain": "club.test", "external_event_id": "fixture999"}]))
        rows = [{"snapshot_id": i, "captured_at": (self.base - timedelta(hours=h)).isoformat(),
                 "available_total": v, "measurement_key": "roboticket/roboticket"}
                for i, h, v in ((90001, 48, 1480), (90002, 25, 1250), (90003, 12, 1120), (90004, 0, 1000))]
        data = {"version": "daily-inventory-public-export-v1", "exported_at": self.base.isoformat(),
                "retrieved_at": (self.base + timedelta(minutes=1)).isoformat(),
                "events": [{"ticket_event_id": 999, "club_slug": "club", "provider": "roboticket",
                            "kickoff_at": (self.base + timedelta(days=50)).isoformat(), "observations": rows}]}
        data["export_sha256"] = _hash(data)
        self.source.write_text(json.dumps(data))
        with patch("ml.rolling72_paired_shadow_v2._now", return_value=self.base + timedelta(minutes=2)):
            create_freeze(self.freeze, self.artifact, self.registry.read_bytes(), synthetic_test=True)
        at = self.base + timedelta(minutes=3)
        with patch("ml.rolling72_paired_shadow_v2._now", return_value=at), patch("ml.rolling72_offline_challenger_v2._now", return_value=at), threadpool_limits(limits=1):
            self.capture_result = capture(self.ledger, self.source.read_bytes(), self.artifact, self.freeze,
                                          self.registry.read_bytes(), synthetic_test=True)

    def tearDown(self):
        self.folder.cleanup()

    def bundle(self, **changes):
        args = {"ledger_path": self.ledger, "source_paths": [self.source], "artifactdir": self.artifact,
                "freeze_path": self.freeze, "registry_path": self.registry, "metadata": {"purpose": "synthetic_only"},
                "allow_synthetic_test": True, **changes}
        with patch("ml.rolling72_backup_v2._now", return_value=self.base + timedelta(minutes=10)):
            return make_bundle(**args)

    def test_full_restore_keeps_model_and_original_sources_without_deserializing(self):
        original = self.ledger.read_bytes()
        raw = self.bundle()
        with patch("joblib.load", side_effect=AssertionError("restore must not execute model pickle")):
            result = restore(raw, self.root / "restored", allow_synthetic_test=True)
        self.assertEqual(result["issues"], 1)
        self.assertEqual(result["numeric_forecasts"], self.capture_result["numeric_forecast_count"])
        self.assertEqual(result["scores"], 0)
        self.assertEqual(result["file_count"], 9)
        self.assertTrue(result["model_bytes_verified_without_loading"])
        self.assertEqual(self.ledger.read_bytes(), original)
        for name in ("model.joblib", "manifest.json", "fit-marker.json"):
            self.assertEqual(Path(result["paths"][name]).read_bytes(), (self.artifact / name).read_bytes())
        self.assertEqual(Path(result["paths"]["registry.json"]).read_bytes(), self.registry.read_bytes())

    def test_private_upload_independent_readback_and_restore(self):
        storage = MemoryStorage()
        with patch("ml.rolling72_backup_v2._now", return_value=self.base + timedelta(minutes=10)):
            result = backup(self.ledger, [self.source], self.artifact, self.freeze, self.registry,
                            {"purpose": "synthetic_only"}, storage, allow_synthetic_test=True)
        self.assertEqual(storage.privacy_checks, 1)
        self.assertEqual(storage.reads, 2)
        self.assertTrue(result["independent_restore_verified"])
        self.assertEqual(result["key"], PREFIX + "/" + _digest(storage.objects[result["key"]]) + ".json")
        self.assertTrue(result["private"])

    def test_remote_readback_corruption_rejected(self):
        with patch("ml.rolling72_backup_v2._now", return_value=self.base + timedelta(minutes=10)):
            with self.assertRaisesRegex(ValueError, "read-back differs"):
                backup(self.ledger, [self.source], self.artifact, self.freeze, self.registry, {},
                       MemoryStorage(True), allow_synthetic_test=True)

    def test_synthetic_not_accepted_by_default_or_as_real(self):
        with self.assertRaisesRegex(ValueError, "Synthetic model"):
            self.bundle(allow_synthetic_test=False)
        with self.assertRaisesRegex(ValueError, "Synthetic model"):
            restore(self.bundle(), self.root / "mustnotexist")
        self.assertFalse((self.root / "mustnotexist").exists())

    def test_namespace_rejects_v1_latest_and_traversal(self):
        self.assertEqual(Rolling72Storage._key(PREFIX + "/" + "a" * 64 + ".json"), PREFIX + "/" + "a" * 64 + ".json")
        for name in ("rolling72-shadow-v1/" + "a" * 64 + ".json", PREFIX + "/latest.json", "../escape", "models/" + "a" * 64 + ".json"):
            with self.assertRaises(ValueError):
                Rolling72Storage._key(name)
        with self.assertRaisesRegex(ValueError, "no mutable latest"):
            Rolling72Storage.__new__(Rolling72Storage).latest_manifest()

    def test_only_existing_private_bucket_allowed_without_creation(self):
        obj = Rolling72Storage.__new__(Rolling72Storage)
        for rows in ([], [{"id": BUCKET, "public": True}]):
            with patch.object(obj, "_request", return_value=(200, json.dumps(rows).encode())) as request:
                with self.assertRaises(ValueError):
                    obj.ensure_private_bucket()
                self.assertEqual(request.call_args.args, ("GET", "/bucket"))
                self.assertEqual(request.call_count, 1)
        with patch.object(obj, "_request", return_value=(200, json.dumps([{"id": BUCKET, "public": False}]).encode())):
            obj.ensure_private_bucket()

    def test_existing_restore_and_repository_destination_rejected(self):
        old = self.root / "old"
        old.mkdir()
        (old / "sentinel").write_text("keep")
        with self.assertRaisesRegex(ValueError, "New private restore"):
            restore(self.bundle(), old, allow_synthetic_test=True)
        self.assertEqual((old / "sentinel").read_text(), "keep")
        with self.assertRaisesRegex(ValueError, "outside Git"):
            restore(self.bundle(), Path(__file__).parent / "forbidden-recovery-test", allow_synthetic_test=True)

    def test_foreign_and_unexpected_schema_rejected(self):
        foreign = self.root / "foreign.sqlite"
        with sqlite3.connect(foreign) as db:
            db.execute("create table unrelated(value integer)")
        with self.assertRaisesRegex(ValueError, "Foreign ledger"):
            self.bundle(ledger_path=foreign)
        with sqlite3.connect(self.ledger) as db:
            db.execute("create view unexpected as select * from issues")
        with self.assertRaisesRegex(ValueError, "Unexpected paired"):
            self.bundle()

    def test_missing_original_sources_and_count_bound_rejected(self):
        with self.assertRaisesRegex(ValueError, "At least one"):
            self.bundle(source_paths=[])
        other = self.root / "other.json"
        other.write_bytes(self.source.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "Original source bytes missing"):
            self.bundle(source_paths=[other])
        with self.assertRaisesRegex(ValueError, "Too many"):
            self.bundle(source_paths=[self.source] * (MAX_SOURCE_FILES + 1))

    def test_model_bytes_and_completed_marker_are_bound(self):
        (self.artifact / "model.joblib").write_bytes(b"corruption")
        with self.assertRaisesRegex(ValueError, "Model bytes"):
            self.bundle()
        shutil.copy(self.base_model / "model.joblib", self.artifact / "model.joblib")
        marker = json.loads((self.artifact / "fit-marker.json").read_text())
        marker["status"] = "FAILED_NO_REFIT"
        (self.artifact / "fit-marker.json").write_text(json.dumps(marker))
        with self.assertRaisesRegex(ValueError, "completed fit marker"):
            self.bundle()

    def test_changed_registry_or_rehashed_other_lane_freeze_rejected(self):
        self.registry.write_bytes(self.registry.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "freeze contract"):
            self.bundle()
        self.registry.write_bytes(self.registry.read_bytes()[:-1])
        freeze = json.loads(self.freeze.read_text())
        freeze["frozen_at"] = (self.base + timedelta(minutes=2, seconds=1)).isoformat()
        freeze["freeze_sha256"] = _hash({k: v for k, v in freeze.items() if k != "freeze_sha256"})
        self.freeze.write_text(json.dumps(freeze))
        with self.assertRaisesRegex(ValueError, "another immutable"):
            self.bundle()

    def test_actual_issue_clock_and_foreign_keys_checked(self):
        with sqlite3.connect(self.ledger) as db:
            db.execute("update issues set written_at=?", ((self.base + timedelta(hours=1)).isoformat(),))
        with self.assertRaisesRegex(ValueError, "clocks exceed"):
            self.bundle()

    def test_envelope_file_checksum_and_rehashed_model_corruption_rejected(self):
        raw = self.bundle()
        envelope = json.loads(raw)
        envelope["payload_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "payload checksum"):
            restore(_encode(envelope), self.root / "bad1", allow_synthetic_test=True)
        body = unpack(raw)
        body["files"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "file checksum"):
            restore(repack(body), self.root / "bad2", allow_synthetic_test=True)
        body = unpack(raw)
        replace_file(body, "model.joblib", b"malicious pickle not loaded")
        with self.assertRaisesRegex(ValueError, "Model bytes"):
            restore(repack(body), self.root / "bad3", allow_synthetic_test=True)

    def test_rehashed_unsafe_duplicate_and_missing_filenames_rejected(self):
        raw = self.bundle()
        body = unpack(raw)
        body["files"][0]["name"] = "../escape"
        with self.assertRaisesRegex(ValueError, "Unsafe or duplicate"):
            restore(repack(body), self.root / "bad1", allow_synthetic_test=True)
        body = unpack(raw)
        body["files"].append(deepcopy(body["files"][0]))
        with self.assertRaisesRegex(ValueError, "Unsafe or duplicate"):
            restore(repack(body), self.root / "bad2", allow_synthetic_test=True)
        body = unpack(raw)
        next(p for p in body["files"] if p["name"] == "registry.json")["name"] = "source-" + "1" * 64 + ".json"
        with self.assertRaisesRegex(ValueError, "Source filename"):
            restore(repack(body), self.root / "bad3", allow_synthetic_test=True)

    def test_inflation_bounds_truncation_and_concatenation_rejected(self):
        raw = self.bundle()
        envelope = json.loads(raw)
        envelope["payload_bytes"] = MAX_INFLATED_BYTES + 1
        with self.assertRaisesRegex(ValueError, "inflation size"):
            restore(_encode(envelope), self.root / "bad1", allow_synthetic_test=True)
        for change in (lambda b: b[:-2], lambda b: b + zlib.compress(b"second")):
            envelope = json.loads(raw)
            envelope["payload"] = base64.b64encode(change(base64.b64decode(envelope["payload"]))).decode()
            with self.assertRaisesRegex(ValueError, "compression"):
                restore(_encode(envelope), self.root / "bad2", allow_synthetic_test=True)


if __name__ == "__main__":
    unittest.main()
