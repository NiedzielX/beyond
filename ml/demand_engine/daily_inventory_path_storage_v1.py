"""Immutable private Storage backups of the daily-path local evidence ledger.

Storage objects are recovery copies, not relational forecast rows or a deployed
scheduler. Credentials stay in environment bindings; no signed URLs are used.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from .daily_inventory_path_model_v1 import load_model

BUCKET = "beyond-daily-path-research-v1"
MANIFEST_VERSION = "daily-inventory-path-storage-backup-v1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sqlite_snapshot(path: str | Path) -> bytes:
    source = Path(path).resolve()
    if not source.is_file():
        raise ValueError("Ledger does not exist")
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as connection:
        meta = connection.execute("SELECT version FROM daily_path_meta WHERE singleton=1").fetchone()
        if not meta or meta[0] != "daily-inventory-path-local-ledger-v1":
            raise ValueError("Unexpected ledger schema")
        with tempfile.TemporaryDirectory() as folder:
            copy = Path(folder) / "snapshot.sqlite"
            with sqlite3.connect(copy) as destination:
                connection.backup(destination)
                if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Ledger integrity check failed")
            return copy.read_bytes()


class PrivateResearchStorage:
    def __init__(self) -> None:
        base = os.environ.get("SUPABASE_URL", "").rstrip("/")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if urllib.parse.urlparse(base).scheme != "https" or not key:
            raise ValueError("HTTPS Supabase URL and service-role binding required")
        self.base = base + "/storage/v1"
        self.headers = {"apikey": key}
        if not key.startswith("sb_"):
            self.headers["Authorization"] = "Bearer " + key

    def _request(self, method: str, path: str, data: bytes | None = None,
                 content_type: str = "application/json") -> tuple[int, bytes]:
        request = urllib.request.Request(self.base + path, data=data,
            headers={**self.headers, "Content-Type": content_type}, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            # Only status is exposed, never a credential-bearing request/body.
            return exc.code, b""

    def ensure_private_bucket(self) -> None:
        status, raw = self._request("GET", "/bucket")
        if status != 200:
            raise ValueError(f"Storage bucket listing returned HTTP {status}")
        buckets = json.loads(raw)
        existing = next((item for item in buckets if item.get("id") == BUCKET), None)
        if existing is None:
            status, _ = self._request("POST", "/bucket", encode({
                "id": BUCKET, "name": BUCKET, "public": False,
                "file_size_limit": 10 * 1024 * 1024,
                "allowed_mime_types": ["application/octet-stream", "application/json"],
            }))
            if status not in (200, 201, 409):
                raise ValueError(f"Private bucket creation returned HTTP {status}")
            status, raw = self._request("GET", "/bucket")
            if status != 200:
                raise ValueError("Cannot verify bucket privacy after creation")
            existing = next((item for item in json.loads(raw) if item.get("id") == BUCKET), None)
        if not existing or existing.get("public") is not False:
            raise ValueError("Research backup bucket must be private")

    @staticmethod
    def _key(key: str) -> str:
        # Opaque content-addressed objects only; no arbitrary paths or overwrite.
        import re
        if not re.fullmatch(r"(ledgers|models|manifests)/[0-9a-f]{64}\.(sqlite|json)", key):
            raise ValueError("Unexpected backup object key")
        return urllib.parse.quote(key, safe="/")

    def read(self, key: str) -> bytes:
        status, raw = self._request("GET", f"/object/authenticated/{BUCKET}/{self._key(key)}")
        if status != 200:
            raise ValueError(f"Storage read-back returned HTTP {status}")
        return raw

    def latest_manifest(self) -> str:
        self.ensure_private_bucket()
        status, raw = self._request("POST", f"/object/list/{BUCKET}", encode({
            "prefix": "manifests", "limit": 1, "offset": 0,
            "sortBy": {"column": "created_at", "order": "desc"},
        }))
        if status != 200:
            raise ValueError(f"Backup manifest listing returned HTTP {status}")
        rows = json.loads(raw)
        if not isinstance(rows, list) or not rows:
            raise ValueError("No private ledger backup manifest found")
        key = "manifests/" + rows[0]["name"]
        self._key(key)
        return key

    def put_verified(self, key: str, data: bytes, content_type: str) -> dict:
        status, _ = self._request("POST", f"/object/{BUCKET}/{self._key(key)}", data, content_type)
        # Some Storage versions return400 for existing objects. Always verify
        # an actual readable byte-for-byte identical object before accepting it.
        if status not in (200, 201, 400, 409):
            raise ValueError(f"Immutable Storage upload returned HTTP {status}")
        if self.read(key) != data:
            raise ValueError("Storage read-back differs from the uploaded backup")
        return {"key": key, "sha256": digest(data), "bytes": len(data), "read_back_verified": True}


def backup_ledger(ledger_path: str | Path, model_path: str | Path,
                  storage: PrivateResearchStorage | None = None) -> dict:
    storage = storage or PrivateResearchStorage()
    model = load_model(model_path)
    ledger_bytes = sqlite_snapshot(ledger_path)
    model_bytes = Path(model_path).read_bytes()
    storage.ensure_private_bucket()
    ledger = storage.put_verified(f"ledgers/{digest(ledger_bytes)}.sqlite", ledger_bytes, "application/octet-stream")
    artifact = storage.put_verified(f"models/{digest(model_bytes)}.json", model_bytes, "application/json")
    manifest = {
        "version": MANIFEST_VERSION, "created_at": datetime.now(timezone.utc).isoformat(),
        "bucket": BUCKET, "private": True, "ledger": ledger, "model": artifact,
        "model_version": model["model_version"], "model_sha256": model["model_sha256"],
        "production_change": False, "live_adjustment": 0,
        "evidence_kind": "private_backup_of_local_post_freeze_ledger",
    }
    data = encode(manifest)
    uploaded = storage.put_verified(f"manifests/{digest(data)}.json", data, "application/json")
    return {**manifest, "manifest_object": uploaded}


def restore_ledger(manifest_key: str, output: str | Path,
                   storage: PrivateResearchStorage | None = None) -> dict:
    storage = storage or PrivateResearchStorage()
    storage.ensure_private_bucket()
    if manifest_key == "latest":
        manifest_key = storage.latest_manifest()
    raw = storage.read(manifest_key)
    if manifest_key != f"manifests/{digest(raw)}.json":
        raise ValueError("Backup manifest content hash mismatch")
    manifest = json.loads(raw)
    if (manifest.get("version") != MANIFEST_VERSION or manifest.get("private") is not True
            or manifest.get("bucket") != BUCKET or manifest.get("production_change") is not False):
        raise ValueError("Unexpected backup manifest contract")
    record = manifest["ledger"]
    data = storage.read(record["key"])
    if digest(data) != record["sha256"] or record["key"] != f"ledgers/{digest(data)}.sqlite":
        raise ValueError("Ledger backup content hash mismatch")
    destination = Path(output)
    if destination.exists():
        raise ValueError("Refusing to overwrite an existing ledger")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Validate before committing the restored file to its requested location.
    with tempfile.TemporaryDirectory(dir=destination.parent) as folder:
        candidate = Path(folder) / "candidate.sqlite"
        candidate.write_bytes(data)
        sqlite_snapshot(candidate)
        with destination.open("xb") as stream:
            stream.write(data)
    return {"restored_path": str(destination), "sha256": digest(data), "production_change": False}
