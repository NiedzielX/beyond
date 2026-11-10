"""Independent bounded private recovery for the separate paired rolling72 v2.

Checksums bind copies within our trusted local pipeline, not arbitrary uploaded
pickle authenticity. Neither backup nor restore deserializes model bytes.
Nothing modifies v1, source services, forecasts or existing Storage objects.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import zlib

from ml.demand_engine.daily_inventory_path_storage_v1 import BUCKET
from ml.demand_engine.rolling72_features_v1 import _hash, _time
from ml.rolling72_backup_v1 import (
    MAX_COMPRESSED_BYTES, MAX_ENVELOPE_BYTES, MAX_FILE_BYTES,
    MAX_INFLATED_BYTES, MAX_SOURCE_FILES, Rolling72Storage as _V1Storage,
    _digest, _encode, _read_bounded, _validate_source,
)
from ml.rolling72_offline_challenger_v2 import (
    PRECOMMIT_SHA256, VERSION as MODEL_VERSION, FEATURE_NAMES,
)

VERSION = "rolling72-shadow-private-backup-v2"
BUNDLE_VERSION = "rolling72-shadow-private-files-v2"
PREFIX = "rolling72-shadow-v2"
ROOT = Path(__file__).resolve().parents[1]
FIXED_FILES = {"ledger.sqlite", "freeze.json", "metadata.json", "registry.json",
               "precommit.json", "model.joblib", "manifest.json", "fit-marker.json"}


def _now():
    return datetime.now(timezone.utc)


class Rolling72Storage(_V1Storage):
    """Same already-private bucket, exclusively a new immutable namespace."""
    @staticmethod
    def _key(key):
        if not isinstance(key, str) or re.fullmatch(r"rolling72-shadow-v2/[a-f0-9]{64}\.json", key) is None:
            raise ValueError("V2 recovery cannot access another namespace")
        return key

    def latest_manifest(self):
        raise ValueError("Rolling72 v2 recovery has no mutable latest manifest")


def _checksum_object(value, field, name):
    if not isinstance(value, dict) or value.get(field) != _hash({k: v for k, v in value.items() if k != field}):
        raise ValueError(f"{name} checksum mismatch")
    return value


def _model(files, created, *, allow_synthetic_test=False):
    """Verify trusted model bytes/manifest/marker without executable loading."""
    if not isinstance(allow_synthetic_test, bool):
        raise ValueError("Explicit boolean synthetic recovery mode required")
    recipe = _checksum_object(json.loads(files["precommit.json"]), "precommit_sha256", "Precommit")
    if recipe["precommit_sha256"] != PRECOMMIT_SHA256:
        raise ValueError("Exact published v2 precommit required")
    manifest = _checksum_object(json.loads(files["manifest.json"]), "manifest_sha256", "Private model manifest")
    marker = json.loads(files["fit-marker.json"])
    if (manifest.get("version") != MODEL_VERSION or manifest.get("precommit_sha256") != PRECOMMIT_SHA256
            or manifest.get("parameters") != recipe["candidate"]["parameters"]
            or manifest.get("feature_names") != list(FEATURE_NAMES)
            or manifest.get("sklearn_version") != recipe["candidate"]["sklearn_version"]
            or manifest.get("training_data_cutoff_at") != recipe["training_data_cutoff_at"]
            or manifest.get("historical_knowledge_unproven") is not True
            or manifest.get("historical_validation_accuracy_claim_allowed") is not False
            or manifest.get("private_artifact_trusted_local_only") is not True
            or manifest.get("mae_computed") is not False
            or manifest.get("production_change") is not False or manifest.get("live_adjustment") != 0
            or not isinstance(manifest.get("synthetic_test"), bool)):
        raise ValueError("Private model differs from the v2 recipe/evidence contract")
    if manifest["synthetic_test"] and not allow_synthetic_test:
        raise ValueError("Synthetic model recovery needs explicit synthetic mode")
    if (not isinstance(marker, dict) or marker.get("status") != "FIT_COMPLETE"
            or marker.get("manifest_sha256") != manifest["manifest_sha256"]
            or marker.get("dataset_sha256") != manifest.get("dataset_sha256")
            or marker.get("precommit_sha256") != PRECOMMIT_SHA256
            or marker.get("synthetic_test") != manifest["synthetic_test"]
            or marker.get("fit_started_at") != manifest.get("fit_started_at")
            or marker.get("frozen_at") != manifest.get("frozen_at")
            or _digest(files["model.joblib"]) != manifest.get("model_file_sha256")):
        raise ValueError("Model bytes or completed fit marker mismatch")
    if not _time(recipe["created_at"]) <= _time(manifest["fit_started_at"]) <= _time(manifest["frozen_at"]) <= created:
        raise ValueError("Actual model clocks exceed recovery boundary")
    bindings = manifest.get("source_bindings")
    if not isinstance(bindings, dict) or any(
            not isinstance(bindings.get(kind), dict)
            or any(bindings[kind].get(k) != v for k, v in expected.items())
            or bindings[kind].get("verified_file_sha256") != expected["file_sha256"]
            for kind, expected in recipe["source_bindings"].items()):
        raise ValueError("Model source bindings differ from exact precommit")
    code = manifest.get("source_code_sha256")
    if not isinstance(code, dict) or not code or any(
            not isinstance(key, str) or not isinstance(sha, str) or re.fullmatch("[a-f0-9]{64}", sha) is None
            for key, sha in code.items()):
        raise ValueError("Model source code bindings required")
    return recipe, manifest


def _contracts(files, created, *, allow_synthetic_test=False):
    from ml.rolling72_paired_shadow_v2 import VERSION as LEDGER_VERSION, CODE_PATHS, COHORT
    recipe, manifest = _model(files, created, allow_synthetic_test=allow_synthetic_test)
    freeze = _checksum_object(json.loads(files["freeze.json"]), "freeze_sha256", "Lane freeze")
    if (freeze.get("version") != LEDGER_VERSION or freeze.get("precommit_sha256") != PRECOMMIT_SHA256
            or freeze.get("production_change") is not False or freeze.get("live_adjustment") != 0
            or freeze.get("synthetic_test") is not manifest["synthetic_test"]
            or freeze.get("cohort") != COHORT
            or freeze.get("model_manifest_sha256") != manifest["manifest_sha256"]
            or freeze.get("model_file_sha256") != manifest["model_file_sha256"]
            or freeze.get("identity_registry_sha256") != _digest(files["registry.json"])):
        raise ValueError("Invalid v2 lane freeze contract")
    if (not _time(manifest["frozen_at"]) <= _time(freeze["frozen_at"]) <= created
            or (not manifest["synthetic_test"] and _digest(files["registry.json"])
                != recipe["source_bindings"]["identity_registry"]["file_sha256"])):
        raise ValueError("Lane freeze/model/registry clocks or bindings mismatch")
    code = freeze.get("code_sha256")
    if (not isinstance(code, dict) or set(code) != set(CODE_PATHS)
            or any(not isinstance(sha, str) or re.fullmatch("[a-f0-9]{64}", sha) is None
                   for sha in code.values())
            or any(code.get(name) != sha for name, sha in manifest["source_code_sha256"].items())):
        raise ValueError("Lane code differs from the frozen model pipeline")
    from ml.rolling72_receipt_dataset_v1 import _registry
    groups, _, _ = _registry(files["registry.json"])
    if not groups:
        raise ValueError("Original nonempty registry required")
    return recipe, manifest, freeze


def _inspect_ledger(path, freeze, sources, created):
    from ml.rolling72_paired_shadow_v2 import APPLICATION_ID, TABLES
    with sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True) as db:
        if db.execute("pragma application_id").fetchone()[0] != APPLICATION_ID:
            raise ValueError("Foreign ledger is not paired v2")
        objects = db.execute("select name,type from sqlite_master where type in ('table','view','trigger')").fetchall()
        if {name for name, kind in objects if kind == "table"} != TABLES or any(kind != "table" for _, kind in objects):
            raise ValueError("Unexpected paired v2 ledger schema")
        if db.execute("pragma integrity_check").fetchall() != [("ok",)] or db.execute("pragma foreign_key_check").fetchall():
            raise ValueError("Paired v2 ledger integrity/foreign keys failed")
        lane = db.execute("select singleton,freeze_json from lane").fetchall()
        if len(lane) != 1 or lane[0][0] != 1 or json.loads(lane[0][1]) != freeze:
            raise ValueError("Ledger belongs to another immutable lane freeze")
        for sha, payload in db.execute("select sha,receipt_json from sources"):
            if sha not in sources or _digest(sources[sha]) != sha:
                raise ValueError("Original source bytes missing from v2 recovery")
            if _validate_source(sources[sha], created) != json.loads(payload):
                raise ValueError("Original source bytes disagree with v2 ledger receipt")
        for issued, written in db.execute("select issued_at,written_at from issues"):
            if (not _time(freeze["frozen_at"]) < _time(issued) <= _time(written) <= created
                    or (_time(written) - _time(issued)).total_seconds() > 90):
                raise ValueError("Actual issue/write clocks exceed recovery boundary")
        for (matched,) in db.execute("select matched_at from target_matches"):
            if _time(matched) > created:
                raise ValueError("Score clock exceeds recovery boundary")
        return {"issues": db.execute("select count(*) from issues").fetchone()[0],
                "numeric_forecasts": db.execute("select count(*) from predictions where prediction is not null").fetchone()[0],
                "scores": db.execute("select count(*) from scores").fetchone()[0]}


def _snapshot(path):
    from ml.rolling72_paired_shadow_v2 import APPLICATION_ID
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("Existing regular v2 ledger required")
    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as db:
        if db.execute("pragma application_id").fetchone()[0] != APPLICATION_ID:
            raise ValueError("Foreign ledger cannot be backed up as v2")
        if db.execute("pragma page_count").fetchone()[0] * db.execute("pragma page_size").fetchone()[0] > MAX_FILE_BYTES:
            raise ValueError("V2 ledger exceeds recovery size bound")
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "snapshot.sqlite"
            with sqlite3.connect(destination) as target:
                db.backup(target)
            return _read_bounded(destination)


def _pack(files, created):
    bundle = {"version": BUNDLE_VERSION, "created_at": created.isoformat(),
              "production_change": False, "live_adjustment": 0,
              "evidence_kind": "private_recovery_of_local_v2_shadow_not_hosted_serving",
              "files": [{"name": name, "sha256": _digest(raw), "bytes": len(raw),
                         "base64": base64.b64encode(raw).decode("ascii")}
                        for name, raw in sorted(files.items())]}
    bundle["bundle_sha256"] = _hash(bundle)
    body = _encode(bundle)
    if len(body) > MAX_INFLATED_BYTES:
        raise ValueError("Recovery bundle exceeds inflation bound")
    packed = zlib.compress(body)
    if len(packed) > MAX_COMPRESSED_BYTES:
        raise ValueError("Recovery bundle exceeds compression bound")
    raw = _encode({"version": VERSION, "encoding": "zlib+base64", "payload_sha256": _digest(body),
                   "payload_bytes": len(body), "payload": base64.b64encode(packed).decode("ascii")})
    if len(raw) > MAX_ENVELOPE_BYTES:
        raise ValueError("Recovery envelope exceeds bucket size bound")
    return raw


def _decode(raw, *, allow_synthetic_test=False):
    if not isinstance(raw, bytes) or len(raw) > MAX_ENVELOPE_BYTES:
        raise ValueError("Bounded v2 recovery bytes required")
    envelope = json.loads(raw)
    if (not isinstance(envelope, dict) or envelope.get("version") != VERSION
            or envelope.get("encoding") != "zlib+base64"):
        raise ValueError("Invalid v2 recovery envelope")
    declared = envelope.get("payload_bytes")
    if isinstance(declared, bool) or not isinstance(declared, int) or not 0 < declared <= MAX_INFLATED_BYTES:
        raise ValueError("Invalid recovery inflation size")
    packed = base64.b64decode(envelope["payload"], validate=True)
    if len(packed) > MAX_COMPRESSED_BYTES:
        raise ValueError("Recovery compression exceeds bound")
    inflater = zlib.decompressobj()
    body = inflater.decompress(packed, MAX_INFLATED_BYTES + 1)
    if (len(body) > MAX_INFLATED_BYTES or inflater.unconsumed_tail or not inflater.eof
            or inflater.unused_data or len(body) != declared):
        raise ValueError("Oversized, truncated or concatenated recovery compression")
    if _digest(body) != envelope.get("payload_sha256"):
        raise ValueError("Recovery payload checksum mismatch")
    bundle = _checksum_object(json.loads(body), "bundle_sha256", "Recovery bundle")
    if (bundle.get("version") != BUNDLE_VERSION or bundle.get("production_change") is not False
            or bundle.get("live_adjustment") != 0):
        raise ValueError("Invalid v2 recovery bundle contract")
    created = _time(bundle["created_at"])
    parts = bundle.get("files")
    if not isinstance(parts, list) or not len(FIXED_FILES) + 1 <= len(parts) <= len(FIXED_FILES) + MAX_SOURCE_FILES:
        raise ValueError("Invalid bounded recovery file list")
    files = {}
    for part in parts:
        if not isinstance(part, dict):
            raise ValueError("Recovery file entry must be an object")
        name = part.get("name")
        if (not isinstance(name, str) or name in files
                or (name not in FIXED_FILES and re.fullmatch(r"source-[a-f0-9]{64}\.json", name) is None)):
            raise ValueError("Unsafe or duplicate recovery filename")
        count = part.get("bytes")
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= MAX_FILE_BYTES:
            raise ValueError("Invalid bounded recovery file size")
        value = base64.b64decode(part["base64"], validate=True)
        if len(value) != count or _digest(value) != part.get("sha256"):
            raise ValueError("Recovery file checksum mismatch")
        if name.startswith("source-") and name != "source-" + _digest(value) + ".json":
            raise ValueError("Source filename differs from original byte hash")
        files[name] = value
    if not FIXED_FILES <= set(files):
        raise ValueError("Required v2 recovery files missing")
    if len(files["metadata.json"]) > 64 * 1024 or not isinstance(json.loads(files["metadata.json"]), dict):
        raise ValueError("Bounded recovery metadata object required")
    recipe, manifest, freeze = _contracts(files, created, allow_synthetic_test=allow_synthetic_test)
    sources = {name[7:-5]: value for name, value in files.items() if name.startswith("source-")}
    for value in sources.values():
        _validate_source(value, created)
    return bundle, files, freeze, sources, created


def make_bundle(ledger_path, source_paths, artifactdir, freeze_path, registry_path, metadata, *, allow_synthetic_test=False):
    """Read-only consistent snapshot; no model loading, fits or network calls."""
    if not isinstance(metadata, dict) or len(_encode(metadata)) > 64 * 1024:
        raise ValueError("Bounded explicit recovery metadata object required")
    sources = {}
    for index, path in enumerate(source_paths):
        if index >= MAX_SOURCE_FILES:
            raise ValueError("Too many original source inputs")
        raw = _read_bounded(path)
        sources[_digest(raw)] = raw
    if not sources:
        raise ValueError("At least one original source receipt required")
    artifact = Path(artifactdir)
    if artifact.is_symlink() or artifact.resolve().is_relative_to(ROOT):
        raise ValueError("Trusted private artifact outside Git required")
    files = {name: _read_bounded(artifact / name) for name in ("model.joblib", "manifest.json", "fit-marker.json")}
    files.update({"ledger.sqlite": _snapshot(ledger_path), "freeze.json": _read_bounded(freeze_path),
                  "registry.json": _read_bounded(registry_path), "metadata.json": _encode(metadata),
                  "precommit.json": _read_bounded(ROOT / "ml/artifacts/rolling72_v2/precommit.json")})
    files.update({"source-" + sha + ".json": raw for sha, raw in sources.items()})
    created = _now()
    raw = _pack(files, created)
    _, checked_files, freeze, checked_sources, boundary = _decode(raw, allow_synthetic_test=allow_synthetic_test)
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "ledger.sqlite"
        path.write_bytes(checked_files["ledger.sqlite"])
        _inspect_ledger(path, freeze, checked_sources, boundary)
    return raw


def restore(rawbytes, outdir, *, allow_synthetic_test=False):
    """Independently validate and restore flat private files, never overwrite."""
    destination = Path(outdir)
    if destination.exists() or destination.is_symlink() or destination.resolve().is_relative_to(ROOT):
        raise ValueError("New private restore directory outside Git required")
    bundle, files, freeze, sources, created = _decode(rawbytes, allow_synthetic_test=allow_synthetic_test)
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "ledger.sqlite"
        path.write_bytes(files["ledger.sqlite"])
        info = _inspect_ledger(path, freeze, sources, created)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(mode=0o700)
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
            "file_sha256": {name: _digest(value) for name, value in files.items()},
            "file_count": len(files), "integrity_and_foreign_keys_verified": True,
            "original_sources_verified": True, "model_bytes_verified_without_loading": True,
            **info, "production_change": False, "live_adjustment": 0}


def backup(ledger_path, source_paths, artifactdir, freeze_path, registry_path, metadata, storage=None, *, allow_synthetic_test=False):
    """Immutable private upload, independent remote read and full local restore."""
    raw = make_bundle(ledger_path, source_paths, artifactdir, freeze_path, registry_path, metadata,
                      allow_synthetic_test=allow_synthetic_test)
    storage = storage or Rolling72Storage()
    storage.ensure_private_bucket()
    key = Rolling72Storage._key(PREFIX + "/" + _digest(raw) + ".json")
    uploaded = storage.put_verified(key, raw, "application/json")
    remote = storage.read(key)
    if remote != raw or key != PREFIX + "/" + _digest(remote) + ".json":
        raise ValueError("Independent private backup read-back differs")
    with tempfile.TemporaryDirectory() as folder:
        restored = restore(remote, Path(folder) / "independent-restore", allow_synthetic_test=allow_synthetic_test)
    return {**uploaded, "version": VERSION, "key": key, "sha256": _digest(raw),
            "bytes": len(raw), "bucket": BUCKET, "private": True,
            "read_back_verified": True, "independent_restore_verified": True,
            "bundle_sha256": restored["bundle_sha256"], "file_count": restored["file_count"],
            "file_sha256": restored["file_sha256"], "issues": restored["issues"],
            "numeric_forecasts": restored["numeric_forecasts"], "scores": restored["scores"],
            "model_bytes_verified_without_loading": True,
            "production_change": False, "live_adjustment": 0}
