"""Synthetic-only private recovery contract tests; no network or live writes."""
import base64
from copy import deepcopy
from datetime import timedelta
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zlib

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_backup_v1 import (
    BUCKET, MAX_COMPRESSED_BYTES, MAX_ENVELOPE_BYTES, MAX_INFLATED_BYTES,
    MAX_SOURCE_FILES, PREFIX, Rolling72Storage, _encode, backup, make_bundle,
    restore,
)
from ml.rolling72_shadow_ledger_v1 import capture, create_freeze
from ml.test_rolling72_shadow_ledger_v1 import BASE, source


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unpack(raw):
    return json.loads(zlib.decompress(base64.b64decode(json.loads(raw)["payload"])))


def repack(bundle):
    bundle["bundle_sha256"] = _hash({key: value for key, value in bundle.items()
                                      if key != "bundle_sha256"})
    body = _encode(bundle)
    return _encode({"version": "rolling72-shadow-private-backup-v1", "encoding": "zlib+base64",
                    "payload_sha256": digest(body), "payload_bytes": len(body),
                    "payload": base64.b64encode(zlib.compress(body)).decode()})


class MemoryStorage:
    """Private immutable fake; both uploader and backup independently read back."""
    def __init__(self, corrupt_second_read=False):
        self.objects = {}
        self.privacy_checks = 0
        self.reads = 0
        self.corrupt_second_read = corrupt_second_read

    def ensure_private_bucket(self):
        self.privacy_checks += 1

    def read(self, key):
        Rolling72Storage._key(key)
        self.reads += 1
        value = self.objects[key]
        return value + b"bad" if self.corrupt_second_read and self.reads >= 2 else value

    def put_verified(self, key, raw, content_type):
        Rolling72Storage._key(key)
        assert content_type == "application/json"
        if key in self.objects and self.objects[key] != raw:
            raise ValueError("Fake immutable object conflict")
        self.objects.setdefault(key, raw)
        if self.read(key) != raw:
            raise ValueError("Fake upload read-back mismatch")
        return {"key": key, "sha256": digest(raw), "bytes": len(raw), "read_back_verified": True}


class Rolling72BackupTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.ledger = self.root / "ledger.sqlite"
        self.freeze = self.root / "freeze.json"
        self.source = self.root / "original-source.json"
        self.source.write_bytes(source())
        self.metadata = {"purpose": "synthetic_contract_test", "fitted_model": False}
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=BASE + timedelta(minutes=2)):
            create_freeze(self.freeze)
        with patch("ml.rolling72_shadow_ledger_v1._now", return_value=BASE + timedelta(minutes=3)):
            capture(self.ledger, self.source.read_bytes(), self.freeze)

    def tearDown(self):
        self.folder.cleanup()

    def bundle(self, **changes):
        args = {"ledger_path": self.ledger, "source_paths": [self.source],
                "freeze_path": self.freeze, "metadata": self.metadata, **changes}
        with patch("ml.rolling72_backup_v1._now", return_value=BASE + timedelta(minutes=10)):
            return make_bundle(**args)

    def test_genuine_source_bundle_restores_same_rows_and_bytes(self):
        before = self.ledger.read_bytes()
        raw = self.bundle()
        result = restore(raw, self.root / "restored")
        self.assertEqual(result["issues"], 1)
        self.assertEqual(result["numeric_forecasts"], 6)
        self.assertEqual(result["scores"], 0)
        self.assertEqual(result["file_count"], 4)
        self.assertTrue(result["integrity_and_foreign_keys_verified"])
        self.assertTrue(result["original_sources_verified"])
        self.assertEqual(self.ledger.read_bytes(), before)
        restored_source = Path(result["paths"]["source-" + digest(self.source.read_bytes()) + ".json"])
        self.assertEqual(restored_source.read_bytes(), self.source.read_bytes())
        self.assertEqual(Path(result["paths"]["freeze.json"]).read_bytes(), self.freeze.read_bytes())

    def test_private_upload_independent_read_and_restore_are_verified(self):
        storage = MemoryStorage()
        with patch("ml.rolling72_backup_v1._now", return_value=BASE + timedelta(minutes=10)):
            result = backup(self.ledger, [self.source], self.freeze, self.metadata, storage)
        self.assertEqual(storage.privacy_checks, 1)
        self.assertEqual(storage.reads, 2)
        self.assertTrue(result["independent_restore_verified"])
        self.assertTrue(result["private"])
        self.assertEqual(result["bucket"], BUCKET)
        self.assertEqual(result["key"], PREFIX + "/" + digest(storage.objects[result["key"]]) + ".json")
        self.assertEqual(result["numeric_forecasts"], 6)

    def test_independent_remote_corruption_is_not_accepted(self):
        storage = MemoryStorage(corrupt_second_read=True)
        with patch("ml.rolling72_backup_v1._now", return_value=BASE + timedelta(minutes=10)):
            with self.assertRaisesRegex(ValueError, "read-back differs"):
                backup(self.ledger, [self.source], self.freeze, self.metadata, storage)

    def test_same_bundle_is_immutable_content_addressed(self):
        storage = MemoryStorage()
        with patch("ml.rolling72_backup_v1._now", return_value=BASE + timedelta(minutes=10)):
            first = backup(self.ledger, [self.source], self.freeze, self.metadata, storage)
            second = backup(self.ledger, [self.source], self.freeze, self.metadata, storage)
        self.assertEqual(first["key"], second["key"])
        self.assertEqual(len(storage.objects), 1)

    def test_namespace_rejects_old_manifests_and_traversal(self):
        valid = PREFIX + "/" + "a" * 64 + ".json"
        self.assertEqual(Rolling72Storage._key(valid), valid)
        for key in ("manifests/" + "a" * 64 + ".json", "../outside.json",
                    PREFIX + "/latest.json", PREFIX + "/" + "a" * 64 + ".sqlite"):
            with self.assertRaises(ValueError):
                Rolling72Storage._key(key)
        with self.assertRaisesRegex(ValueError, "no mutable latest"):
            Rolling72Storage.__new__(Rolling72Storage).latest_manifest()

    def test_bucket_must_already_exist_and_be_private_without_mutation(self):
        storage = Rolling72Storage.__new__(Rolling72Storage)
        for listing in ([], [{"id": BUCKET, "public": True}]):
            with patch.object(storage, "_request", return_value=(200, json.dumps(listing).encode())) as request:
                with self.assertRaisesRegex(ValueError, "must be private"):
                    storage.ensure_private_bucket()
                self.assertEqual(request.call_args.args, ("GET", "/bucket"))
                self.assertEqual(request.call_count, 1)
        with patch.object(storage, "_request", return_value=(200, json.dumps([{"id": BUCKET, "public": False}]).encode())):
            storage.ensure_private_bucket()

    def test_no_overwrite_of_existing_restore_directory(self):
        destination = self.root / "existing"
        destination.mkdir()
        sentinel = destination / "keep.txt"
        sentinel.write_text("unchanged")
        with self.assertRaisesRegex(ValueError, "new private restore"):
            restore(self.bundle(), destination)
        self.assertEqual(sentinel.read_text(), "unchanged")

    def test_restore_in_repository_is_refused(self):
        destination = Path(__file__).resolve().parent / "must-not-create-backup-test"
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            restore(self.bundle(), destination)
        self.assertFalse(destination.exists())

    def test_missing_or_modified_original_source_is_rejected(self):
        missing = self.root / "other.json"
        data = json.loads(self.source.read_bytes())
        data["events"][0]["observations"][0]["available_total"] = 7
        data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        missing.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "Original source bytes missing"):
            self.bundle(source_paths=[missing])
        with self.assertRaisesRegex(ValueError, "At least one"):
            self.bundle(source_paths=[])

    def test_freeze_for_another_lane_is_rejected(self):
        data = json.loads(self.freeze.read_text())
        data["frozen_at"] = (BASE + timedelta(minutes=1)).isoformat()
        data["freeze_sha256"] = _hash({k: v for k, v in data.items() if k != "freeze_sha256"})
        self.freeze.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "another immutable freeze"):
            self.bundle()

    def test_foreign_ledger_and_unexpected_schema_are_rejected(self):
        foreign = self.root / "foreign.sqlite"
        with sqlite3.connect(foreign) as db:
            db.execute("create table old_predictions(value integer)")
        with self.assertRaisesRegex(ValueError, "Foreign/frozen"):
            self.bundle(ledger_path=foreign)
        with sqlite3.connect(self.ledger) as db:
            db.execute("create table undeclared(value integer)")
        with self.assertRaisesRegex(ValueError, "Unexpected rolling72 ledger schema"):
            self.bundle()

    def test_issue_clocks_cannot_be_beyond_backup_boundary(self):
        with sqlite3.connect(self.ledger) as db:
            db.execute("update issues set written_at=?", ((BASE + timedelta(hours=1)).isoformat(),))
        with self.assertRaisesRegex(ValueError, "clocks exceed"):
            self.bundle()

    def test_envelope_and_payload_checksums_are_not_interchangeable(self):
        envelope = json.loads(self.bundle())
        envelope["payload_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "payload checksum"):
            restore(_encode(envelope), self.root / "bad")
        body = unpack(self.bundle())
        body["files"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "file checksum"):
            restore(repack(body), self.root / "bad2")
        self.assertFalse((self.root / "bad").exists())

    def test_rehashed_traversal_and_duplicate_names_are_rejected(self):
        body = unpack(self.bundle())
        body["files"][0]["name"] = "../escape.sqlite"
        with self.assertRaisesRegex(ValueError, "Unsafe or duplicate"):
            restore(repack(body), self.root / "bad")
        body = unpack(self.bundle())
        body["files"].append(deepcopy(body["files"][0]))
        with self.assertRaisesRegex(ValueError, "Unsafe or duplicate"):
            restore(repack(body), self.root / "bad2")

    def test_nonobject_file_entry_and_source_filename_forgery_rejected(self):
        body = unpack(self.bundle())
        body["files"][0] = "not-a-file"
        with self.assertRaisesRegex(ValueError, "must be an object"):
            restore(repack(body), self.root / "bad")
        body = unpack(self.bundle())
        part = next(p for p in body["files"] if p["name"].startswith("source-"))
        part["name"] = "source-" + "a" * 64 + ".json"
        with self.assertRaisesRegex(ValueError, "does not bind original bytes"):
            restore(repack(body), self.root / "bad2")

    def test_declared_inflation_limit_and_truncated_or_concatenated_zlib_fail(self):
        envelope = json.loads(self.bundle())
        envelope["payload_bytes"] = MAX_INFLATED_BYTES + 1
        with self.assertRaisesRegex(ValueError, "inflation size"):
            restore(_encode(envelope), self.root / "large")
        for change in (lambda p: p[:-1], lambda p: p + zlib.compress(b"second")):
            envelope = json.loads(self.bundle())
            packed = base64.b64decode(envelope["payload"])
            envelope["payload"] = base64.b64encode(change(packed)).decode()
            with self.assertRaisesRegex(ValueError, "compression"):
                restore(_encode(envelope), self.root / "compressed")

    def test_small_inflation_bound_defeats_compressed_bomb_before_output(self):
        raw = self.bundle()
        envelope = json.loads(raw)
        envelope["payload_bytes"] = 10
        envelope["payload"] = base64.b64encode(zlib.compress(b"x" * 2048)).decode()
        with patch("ml.rolling72_backup_v1.MAX_INFLATED_BYTES", 1024):
            with self.assertRaisesRegex(ValueError, "compression"):
                restore(_encode(envelope), self.root / "bomb")
        self.assertFalse((self.root / "bomb").exists())

    def test_input_and_envelope_bounds_apply_before_unbounded_work(self):
        with patch("ml.rolling72_backup_v1.MAX_FILE_BYTES", 1):
            with self.assertRaisesRegex(ValueError, "file size bound"):
                self.bundle()
        with patch("ml.rolling72_backup_v1.MAX_ENVELOPE_BYTES", 1):
            with self.assertRaisesRegex(ValueError, "bounded bytes"):
                restore(b"{}", self.root / "large")
        with patch("ml.rolling72_backup_v1.MAX_SOURCE_FILES", 2):
            with self.assertRaisesRegex(ValueError, "Too many source receipt inputs"):
                self.bundle(source_paths=[self.source] * 3)

    def test_symlink_source_and_restore_directory_are_refused(self):
        linked = self.root / "linked-source.json"
        linked.symlink_to(self.source)
        with self.assertRaisesRegex(ValueError, "original regular file"):
            self.bundle(source_paths=[linked])
        out = self.root / "linked-restore"
        out.symlink_to(self.root / "nonexistent")
        with self.assertRaisesRegex(ValueError, "new private restore directory"):
            restore(self.bundle(), out)

    def test_partial_write_failure_removes_only_new_restore_files(self):
        raw = self.bundle()
        destination = self.root / "write-failure"
        original_open = Path.open

        @contextmanager
        def broken_open(path, mode="r", *args, **kwargs):
            with original_open(path, mode, *args, **kwargs) as stream:
                if path.parent == destination and mode == "xb":
                    class PartialWriter:
                        def write(self, data):
                            stream.write(data[:2])
                            raise OSError("synthetic disk write failure")
                    yield PartialWriter()
                else:
                    yield stream

        with patch.object(Path, "open", broken_open):
            with self.assertRaisesRegex(OSError, "synthetic disk write failure"):
                restore(raw, destination)
        self.assertFalse(destination.exists())
        self.assertTrue(self.ledger.exists())


if __name__ == "__main__":
    unittest.main()
