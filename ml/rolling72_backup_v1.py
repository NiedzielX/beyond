"""Bounded private recovery bundles for the separate rolling72 shadow ledger.

The original ledger is opened read-only and snapshotted through SQLite backup.
Objects use a new content-addressed namespace in the existing private research
bucket. No latest manifest, old ledger, source service or model is modified.
Recovery proves a local ledger can be restored, not hosted forecast execution.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import zlib

from ml.demand_engine.daily_inventory_path_storage_v1 import BUCKET, PrivateResearchStorage
from ml.demand_engine.rolling72_features_v1 import _hash, _time
from ml.rolling72_receipt_store_v1 import prepare_receipt
from ml.rolling72_shadow_ledger_v1 import APPLICATION_ID, CODE_PATHS, VERSION as LEDGER_VERSION


VERSION = "rolling72-shadow-private-backup-v1"
BUNDLE_VERSION = "rolling72-shadow-private-files-v1"
PREFIX = "rolling72-shadow-v1"
MAX_ENVELOPE_BYTES = 10 * 1024 * 1024
MAX_COMPRESSED_BYTES = 8 * 1024 * 1024
MAX_INFLATED_BYTES = 32 * 1024 * 1024
MAX_FILE_BYTES = 24 * 1024 * 1024
MAX_SOURCE_FILES = 128
REPO_ROOT = Path(__file__).resolve().parents[1]
TABLES = {"lane", "sources", "source_observations", "issues", "predictions",
          "target_matches", "scores", "scoring_attempts"}


def _now():
    return datetime.now(timezone.utc)


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


class Rolling72Storage(PrivateResearchStorage):
    """Only this recovery namespace; the bucket must already exist and be private."""
    @staticmethod
    def _key(key):
        if not isinstance(key, str) or re.fullmatch(r"rolling72-shadow-v1/[a-f0-9]{64}\.json", key) is None:
            raise ValueError("Rolling72 backup cannot access another recovery namespace")
        return key

    def ensure_private_bucket(self):
        status, raw = self._request("GET", "/bucket")
        if status != 200:
            raise ValueError("Cannot verify existing private research bucket")
        buckets = json.loads(raw)
        if not isinstance(buckets, list):
            raise ValueError("Unexpected private bucket listing")
        existing = next((item for item in buckets if item.get("id") == BUCKET), None)
        if not existing or existing.get("public") is not False:
            raise ValueError("Existing rolling72 research bucket must be private")

    def latest_manifest(self):
        raise ValueError("Rolling72 recovery has no mutable latest manifest")


def _read_bounded(path):
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("Recovery input must be an original regular file")
    if source.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Recovery input exceeds file size bound")
    with source.open("rb") as stream:
        raw = stream.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError("Recovery input grew beyond file size bound")
    return raw


def _freeze(raw):
    value = json.loads(raw)
    if (not isinstance(value, dict) or value.get("version") != LEDGER_VERSION
            or value.get("freeze_sha256") != _hash({k: v for k, v in value.items() if k != "freeze_sha256"})
            or value.get("production_change") is not False or value.get("live_adjustment") != 0
            or value.get("model_fit_performed") is not False):
        raise ValueError("Invalid rolling72 freeze checksum/contract")
    _time(value["frozen_at"])
    if (not isinstance(value.get("precommit_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", value["precommit_sha256"]) is None
            or set(value.get("code_sha256", {})) != set(CODE_PATHS)
            or any(not isinstance(sha, str) or re.fullmatch(r"[a-f0-9]{64}", sha) is None
                   for sha in value["code_sha256"].values())):
        raise ValueError("Invalid frozen recipe/code hashes")
    return value


def _validate_source(raw, created_at):
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Recovery source must be an original export object")
    received = _time(parsed["retrieved_at"])
    if received > created_at:
        raise ValueError("Source receipt is later than backup creation")
    return prepare_receipt(raw, received)["receipt"]


def _inspect_ledger(path, freeze, sources, created_at):
    with sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True) as db:
        if db.execute("pragma application_id").fetchone()[0] != APPLICATION_ID:
            raise ValueError("Foreign/frozen ledger is not a rolling72 shadow ledger")
        objects = db.execute("select name,type from sqlite_master where type in ('table','view','trigger')").fetchall()
        if {name for name, kind in objects if kind == "table"} != TABLES or any(kind != "table" for _, kind in objects):
            raise ValueError("Unexpected rolling72 ledger schema")
        if db.execute("pragma integrity_check").fetchall() != [("ok",)] or db.execute("pragma foreign_key_check").fetchall():
            raise ValueError("Rolling72 ledger integrity/foreign-key check failed")
        lane = db.execute("select singleton,freeze_json from lane").fetchall()
        if len(lane) != 1 or lane[0][0] != 1 or json.loads(lane[0][1]) != freeze:
            raise ValueError("Ledger belongs to another immutable freeze")
        referenced = {}
        for sha, payload in db.execute("select sha,receipt_json from sources"):
            if sha not in sources or _digest(sources[sha]) != sha:
                raise ValueError("Original source bytes missing from recovery bundle")
            receipt = _validate_source(sources[sha], created_at)
            if receipt != json.loads(payload):
                raise ValueError("Original source bytes disagree with ledger receipt")
            referenced[sha] = receipt
        for issued, written in db.execute("select issued_at,written_at from issues"):
            if not _time(freeze["frozen_at"]) <= _time(issued) <= _time(written) <= created_at:
                raise ValueError("Ledger issue/write clocks exceed backup boundary")
        for (matched,) in db.execute("select matched_at from target_matches"):
            if _time(matched) > created_at:
                raise ValueError("Ledger score is later than backup boundary")
        return {"source_receipts": referenced,
                "issues": db.execute("select count(*) from issues").fetchone()[0],
                "numeric_forecasts": db.execute("select count(*) from predictions where prediction is not null").fetchone()[0],
                "scores": db.execute("select count(*) from scores").fetchone()[0]}


def _snapshot(path):
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("Rolling72 ledger must already exist as a regular file")
    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as db:
        if db.execute("pragma application_id").fetchone()[0] != APPLICATION_ID:
            raise ValueError("Foreign/frozen ledger cannot be backed up as rolling72")
        pages = db.execute("pragma page_count").fetchone()[0]
        size = db.execute("pragma page_size").fetchone()[0]
        if pages * size > MAX_FILE_BYTES:
            raise ValueError("Ledger exceeds recovery file size bound")
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "snapshot.sqlite"
            with sqlite3.connect(destination) as target:
                db.backup(target)
            return _read_bounded(destination)


def make_bundle(ledger_path, source_paths, freeze_path, metadata: dict) -> bytes:
    """Make one bounded bundle locally; no network, source writes or forecasts."""
    if not isinstance(metadata, dict):
        raise ValueError("Recovery metadata must be an explicit JSON object without credentials")
    metadata_raw = _encode(metadata)
    if len(metadata_raw) > 64 * 1024:
        raise ValueError("Recovery metadata exceeds size bound")
    sources = {}
    for index, path in enumerate(source_paths):
        if index >= MAX_SOURCE_FILES:
            raise ValueError("Too many source receipt inputs for one bounded recovery bundle")
        raw = _read_bounded(path)
        sources[_digest(raw)] = raw
        if len(sources) > MAX_SOURCE_FILES:
            raise ValueError("Too many source receipts for one bounded recovery bundle")
    if not sources:
        raise ValueError("At least one original source receipt is required")
    freeze_raw = _read_bounded(freeze_path)
    freeze = _freeze(freeze_raw)
    created = _now()
    if _time(freeze["frozen_at"]) > created:
        raise ValueError("Cannot back up a future freeze")
    ledger_raw = _snapshot(ledger_path)
    with tempfile.TemporaryDirectory() as folder:
        candidate = Path(folder) / "ledger.sqlite"
        candidate.write_bytes(ledger_raw)
        _inspect_ledger(candidate, freeze, sources, created)
    files = {"ledger.sqlite": ledger_raw, "freeze.json": freeze_raw, "metadata.json": metadata_raw}
    files.update({"source-" + sha + ".json": raw for sha, raw in sources.items()})
    for raw in sources.values():
        _validate_source(raw, created)
    bundle = {"version": BUNDLE_VERSION, "created_at": created.isoformat(),
              "production_change": False, "live_adjustment": 0,
              "evidence_kind": "private_recovery_of_local_shadow_not_hosted_execution",
              "files": [{"name": name, "sha256": _digest(raw), "bytes": len(raw),
                         "base64": base64.b64encode(raw).decode("ascii")}
                        for name, raw in sorted(files.items())]}
    bundle["bundle_sha256"] = _hash(bundle)
    body = _encode(bundle)
    if len(body) > MAX_INFLATED_BYTES:
        raise ValueError("Recovery bundle exceeds bounded inflated size")
    packed = zlib.compress(body)
    if len(packed) > MAX_COMPRESSED_BYTES:
        raise ValueError("Recovery bundle exceeds compressed size bound")
    raw = _encode({"version": VERSION, "encoding": "zlib+base64", "payload_sha256": _digest(body),
                   "payload_bytes": len(body), "payload": base64.b64encode(packed).decode("ascii")})
    if len(raw) > MAX_ENVELOPE_BYTES:
        raise ValueError("Recovery envelope exceeds private bucket size bound")
    return raw


def _decode(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_ENVELOPE_BYTES:
        raise ValueError("Recovery envelope is not bounded bytes")
    envelope = json.loads(raw)
    if (not isinstance(envelope, dict) or envelope.get("version") != VERSION
            or envelope.get("encoding") != "zlib+base64"):
        raise ValueError("Invalid rolling72 recovery envelope")
    declared = envelope.get("payload_bytes")
    if isinstance(declared, bool) or not isinstance(declared, int) or not 0 < declared <= MAX_INFLATED_BYTES:
        raise ValueError("Invalid declared recovery inflation size")
    packed = base64.b64decode(envelope["payload"], validate=True)
    if len(packed) > MAX_COMPRESSED_BYTES:
        raise ValueError("Compressed recovery data exceeds bound")
    inflater = zlib.decompressobj()
    body = inflater.decompress(packed, MAX_INFLATED_BYTES + 1)
    if (len(body) > MAX_INFLATED_BYTES or inflater.unconsumed_tail or not inflater.eof
            or inflater.unused_data or len(body) != declared):
        raise ValueError("Oversized, incomplete or concatenated recovery compression")
    if _digest(body) != envelope.get("payload_sha256"):
        raise ValueError("Recovery payload checksum mismatch")
    bundle = json.loads(body)
    if (not isinstance(bundle, dict) or bundle.get("version") != BUNDLE_VERSION
            or bundle.get("bundle_sha256") != _hash({k: v for k, v in bundle.items() if k != "bundle_sha256"})
            or bundle.get("production_change") is not False or bundle.get("live_adjustment") != 0):
        raise ValueError("Invalid recovery bundle checksum/contract")
    created = _time(bundle["created_at"])
    parts = bundle.get("files")
    if not isinstance(parts, list) or not 4 <= len(parts) <= MAX_SOURCE_FILES + 3:
        raise ValueError("Invalid bounded recovery file list")
    files = {}
    for part in parts:
        if not isinstance(part, dict):
            raise ValueError("Recovery file entry must be an object")
        name = part.get("name")
        if (not isinstance(name, str) or re.fullmatch(r"(?:ledger\.sqlite|freeze\.json|metadata\.json|source-[a-f0-9]{64}\.json)", name) is None
                or name in files):
            raise ValueError("Unsafe or duplicate recovery filename")
        count = part.get("bytes")
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= MAX_FILE_BYTES:
            raise ValueError("Invalid recovery file size bound")
        value = base64.b64decode(part["base64"], validate=True)
        if len(value) != count or _digest(value) != part.get("sha256"):
            raise ValueError("Recovery file checksum mismatch")
        if name.startswith("source-") and name != "source-" + _digest(value) + ".json":
            raise ValueError("Recovery source filename does not bind original bytes")
        files[name] = value
    if not {"ledger.sqlite", "freeze.json", "metadata.json"} <= set(files):
        raise ValueError("Required rolling72 recovery files missing")
    freeze = _freeze(files["freeze.json"])
    if _time(freeze["frozen_at"]) > created or not isinstance(json.loads(files["metadata.json"]), dict):
        raise ValueError("Recovery metadata/freeze is incompatible")
    sources = {name[len("source-"):-len(".json")]: value
               for name, value in files.items() if name.startswith("source-")}
    for value in sources.values():
        _validate_source(value, created)
    return bundle, files, freeze, sources, created


def restore(rawbytes: bytes, outdir) -> dict:
    """Validate independently, then restore fixed private files without overwrite."""
    destination = Path(outdir)
    if destination.exists() or destination.is_symlink() or destination.resolve().is_relative_to(REPO_ROOT):
        raise ValueError("A new private restore directory outside the repository is required")
    bundle, files, freeze, sources, created = _decode(rawbytes)
    with tempfile.TemporaryDirectory() as folder:
        candidate = Path(folder) / "ledger.sqlite"
        candidate.write_bytes(files["ledger.sqlite"])
        info = _inspect_ledger(candidate, freeze, sources, created)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(mode=0o700)  # Exclusive directory creation; never replace an existing path.
    written = []
    try:
        for name, raw in files.items():
            path = destination / name
            with path.open("xb") as stream:
                written.append(path)
                stream.write(raw)
            path.chmod(0o440)
    except BaseException:
        for path in written:
            path.unlink()
        destination.rmdir()
        raise
    return {"version": VERSION, "bundle_sha256": bundle["bundle_sha256"],
            "paths": {name: str((destination / name).resolve()) for name in files},
            "file_sha256": {name: _digest(raw) for name, raw in files.items()},
            "file_count": len(files), "integrity_and_foreign_keys_verified": True,
            "original_sources_verified": True, "issues": info["issues"],
            "numeric_forecasts": info["numeric_forecasts"], "scores": info["scores"],
            "production_change": False, "live_adjustment": 0}


def backup(ledger_path, source_paths, freeze_path, metadata, storage=None) -> dict:
    """Upload one immutable private object, read it back, independently restore."""
    raw = make_bundle(ledger_path, source_paths, freeze_path, metadata)
    storage = storage or Rolling72Storage()
    storage.ensure_private_bucket()
    key = Rolling72Storage._key(PREFIX + "/" + _digest(raw) + ".json")
    uploaded = storage.put_verified(key, raw, "application/json")
    remote = storage.read(key)
    if remote != raw or key != PREFIX + "/" + _digest(remote) + ".json":
        raise ValueError("Independent private backup read-back differs")
    with tempfile.TemporaryDirectory() as folder:
        restored = restore(remote, Path(folder) / "independent-restore")
    return {**uploaded, "version": VERSION, "key": key, "sha256": _digest(raw),
            "bytes": len(raw), "bucket": BUCKET, "private": True,
            "read_back_verified": True, "independent_restore_verified": True,
            "bundle_sha256": restored["bundle_sha256"], "file_count": restored["file_count"],
            "file_sha256": restored["file_sha256"], "issues": restored["issues"],
            "numeric_forecasts": restored["numeric_forecasts"], "scores": restored["scores"],
            "production_change": False, "live_adjustment": 0}
