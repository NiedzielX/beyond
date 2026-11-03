from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger
from ml.demand_engine.daily_inventory_path_storage_v1 import (
    BUCKET, PrivateResearchStorage, backup_ledger, digest, encode, restore_ledger,
    sqlite_snapshot,
)


class MemoryStorage:
    def __init__(self):
        self.objects = {}
        self.private_verified = False

    def ensure_private_bucket(self):
        self.private_verified = True

    def put_verified(self, key, data, content_type):
        if key in self.objects and self.objects[key] != data:
            raise ValueError("Immutable conflict")
        self.objects[key] = data
        return {"key": key, "sha256": digest(data), "bytes": len(data), "read_back_verified": True}

    def read(self, key):
        return self.objects[key]


class PrivateStorageBackupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = self.root / "ledger.sqlite"
        with DailyInventoryPathLedger(self.ledger):
            pass
        self.model = Path(__file__).resolve().parents[1] / "artifacts/daily_inventory_path_v1.json"

    def test_backup_and_restore_preserve_sqlite_and_model_bytes(self):
        storage = MemoryStorage()
        backup = backup_ledger(self.ledger, self.model, storage)
        self.assertTrue(storage.private_verified)
        self.assertEqual(backup["private"], True)
        self.assertFalse(backup["production_change"])
        self.assertEqual(storage.read(backup["model"]["key"]), self.model.read_bytes())
        restored = self.root / "restored.sqlite"
        result = restore_ledger(backup["manifest_object"]["key"], restored, storage)
        self.assertEqual(result["sha256"], backup["ledger"]["sha256"])
        with DailyInventoryPathLedger(restored) as ledger:
            self.assertEqual(ledger.export_points(), [])
        self.assertEqual(digest(restored.read_bytes()), backup["ledger"]["sha256"])

    def test_restore_never_overwrites_live_ledger(self):
        storage = MemoryStorage()
        backup = backup_ledger(self.ledger, self.model, storage)
        original = self.ledger.read_bytes()
        with self.assertRaisesRegex(ValueError, "overwrite"):
            restore_ledger(backup["manifest_object"]["key"], self.ledger, storage)
        self.assertEqual(self.ledger.read_bytes(), original)

    def test_tampered_manifest_or_ledger_is_rejected_before_creating_destination(self):
        storage = MemoryStorage()
        backup = backup_ledger(self.ledger, self.model, storage)
        key = backup["manifest_object"]["key"]
        original = storage.objects[key]
        storage.objects[key] = original + b" "
        with self.assertRaisesRegex(ValueError, "manifest content hash"):
            restore_ledger(key, self.root / "bad1.sqlite", storage)
        storage.objects[key] = original
        storage.objects[backup["ledger"]["key"]] = b"tampered"
        with self.assertRaisesRegex(ValueError, "Ledger backup content hash"):
            restore_ledger(key, self.root / "bad2.sqlite", storage)
        self.assertFalse((self.root / "bad2.sqlite").exists())

    def test_missing_or_unrelated_sqlite_file_is_not_backed_up(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            sqlite_snapshot(self.root / "missing.sqlite")
        self.assertFalse((self.root / "missing.sqlite").exists())

    def client(self):
        client = object.__new__(PrivateResearchStorage)
        return client

    def test_public_bucket_is_rejected_without_changing_its_privacy(self):
        client = self.client()
        client._request = Mock(return_value=(200, encode({"unused": 1})))
        client._request.return_value = (200, json.dumps([{"id": BUCKET, "public": True}]).encode())
        with self.assertRaisesRegex(ValueError, "must be private"):
            client.ensure_private_bucket()
        self.assertEqual(client._request.call_count, 1)

    def test_bucket_creation_is_private_and_is_rechecked(self):
        client = self.client()
        client._request = Mock(side_effect=[(200, b"[]"), (201, b"{}"),
            (200, json.dumps([{"id": BUCKET, "public": False}]).encode())])
        client.ensure_private_bucket()
        creation = client._request.call_args_list[1].args
        self.assertEqual(creation[:2], ("POST", "/bucket"))
        self.assertFalse(json.loads(creation[2])["public"])

    def test_upload_requires_identical_readback_even_after_conflict(self):
        client = self.client()
        client._request = Mock(return_value=(409, b""))
        client.read = Mock(return_value=b"original")
        key = f"models/{digest(b'original')}.json"
        self.assertTrue(client.put_verified(key, b"original", "application/json")["read_back_verified"])
        with self.assertRaisesRegex(ValueError, "differs"):
            client.put_verified(key, b"changed", "application/json")
        self.assertEqual(client._request.call_args.args[0], "POST")

    def test_path_traversal_or_arbitrary_object_names_are_rejected(self):
        for key in ["../secret", "models/../../x", "ledgers/latest.sqlite", "manifests/x.json"]:
            with self.assertRaises(ValueError):
                PrivateResearchStorage._key(key)

    def test_latest_manifest_is_ordered_by_server_creation_and_still_validated(self):
        client = self.client()
        client.ensure_private_bucket = Mock()
        name = "a" * 64 + ".json"
        client._request = Mock(return_value=(200, json.dumps([{"name": name}]).encode()))
        self.assertEqual(client.latest_manifest(), "manifests/" + name)
        params = json.loads(client._request.call_args.args[2])
        self.assertEqual(params["sortBy"], {"column": "created_at", "order": "desc"})
        client._request.return_value = (200, json.dumps([{"name": "../../unexpected"}]).encode())
        with self.assertRaises(ValueError):
            client.latest_manifest()


if __name__ == "__main__":
    unittest.main()
