"""One bounded actual-time rolling72 source/score/forecast recovery cycle.

Local due checks never poll Supabase. A due cycle reads only the tracked event
metadata and at most499 incremental snapshots per event, preserving genuine
prefix rows and their gaps. Nothing reconstructs missed prospective issues.
The deadline and runner/freeze/registry hashes are locked for this runtime.
The original frozen predictor, label matcher and v1 ledger remain untouched.
This v2 wrapper binds its private fitted artifact and separate paired ledger.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from ml.demand_engine.rolling72_features_v1 import _hash, _id, _time
from ml.rolling72_backup_v1 import MAX_FILE_BYTES
from ml.rolling72_backup_v2 import backup
from ml.rolling72_cycle_v1 import BoundedReader, _refresh
from ml.rolling72_paired_shadow_v2 import APPLICATION_ID, _load_freeze, capture, score, report


VERSION = "rolling72-bounded-cycle-v2"
ROOT = Path(__file__).resolve().parents[1]
MIN_RETRY_SECONDS = 900
DUE_GRACE = timedelta(minutes=10)


def _now():
    return datetime.now(timezone.utc)


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _atomic(path, value):
    raw = _json(value)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _immutable(path, raw):
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("Immutable runtime file differs")
        return
    with path.open("xb") as stream:
        stream.write(raw)
    path.chmod(0o440)


def _audit(runtime, result):
    with (runtime / "audit.jsonl").open("ab") as audit:
        audit.write(_json(result) + b"\n")


def _readonly(database):
    db = sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True)
    if db.execute("pragma application_id").fetchone()[0] != APPLICATION_ID:
        db.close()
        raise ValueError("Bounded cycle requires its own rolling72 ledger")
    return db


def _checkpoint(database):
    with _readonly(database) as db:
        return {name: db.execute("select count(*) from " + name).fetchone()[0]
                for name in ("issues", "predictions", "sources", "target_matches", "scores")}


def due_status(database, now) -> dict:
    """Pure local schedule: target+10m or last successful issue+24h+10m."""
    current = _time(now)
    with _readonly(database) as db:
        captures, targets, next_times = [], [], []
        for event_id, issued, serialized in db.execute("""select i.event_id,max(i.issued_at),i.issue_json
            from issues i join predictions p using(event_id,issued_at)
            where p.prediction is not null group by i.event_id"""):
            # Read the exact latest successful issue instead of relying on an aggregate's arbitrary row.
            serialized = db.execute("select issue_json from issues where event_id=? and issued_at=?", (event_id, issued)).fetchone()[0]
            kickoff = _time(json.loads(serialized)["event"]["kickoff_at"])
            if kickoff <= current + timedelta(hours=24):
                continue
            at = _time(issued) + timedelta(hours=24) + DUE_GRACE
            next_times.append(at)
            if current >= at:
                captures.append(event_id)
        for event_id, issued, horizon, target in db.execute("""select distinct p.event_id,p.issued_at,p.horizon,p.target_at
            from predictions p left join target_matches t using(event_id,issued_at,horizon)
            where p.prediction is not null and t.event_id is null"""):
            at = _time(target) + DUE_GRACE
            next_times.append(at)
            if current >= at:
                targets.append({"event_id": event_id, "issued_at": issued, "horizon_hours": horizon})
    return {"capture_event_ids": sorted(set(captures)), "mature_unmatched_targets": targets,
            "due": bool(captures or targets),
            "next_due_at": min(next_times).isoformat() if next_times else None}


def _source_paths(database, source_path, runtime, state):
    with _readonly(database) as db:
        wanted = {row[0] for row in db.execute("select sha from sources")}
    candidates = [Path(value) for value in state.get("source_paths", [])] + [Path(source_path)]
    for folder in {Path(source_path).parent, Path(database).parent, runtime / "sources"}:
        if folder.is_dir():
            candidates.extend(folder.glob("*.json"))
    found = {}
    for path in dict.fromkeys(candidates):
        if path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_FILE_BYTES:
            digest = _digest(path.read_bytes())
            if digest in wanted:
                found[digest] = path.resolve()
    if set(found) != wanted:
        raise ValueError("Original source files required by ledger are missing")
    return [found[key] for key in sorted(found)]


def _finish(database, source_path, artifactdir, registry_path, freeze_path, runtime, state, storage, operation, *, synthetic_test=False):
    paths = _source_paths(database, source_path, runtime, state)
    summary = report(database)
    recovery = backup(database, paths, artifactdir, freeze_path, registry_path, {
        "runner_version": VERSION, "operation": operation, "until": state["until"],
        "cycle_at": _now().isoformat(), "source_file_count": len(paths),
    }, storage=storage, allow_synthetic_test=synthetic_test)
    state.update({"checkpoint": _checkpoint(database), "source_paths": list(map(str, paths)),
                  "last_backup": recovery, "last_completed_at": _now().isoformat(),
                  "last_status": "SUCCESS"})
    state.pop("failure_stage", None)
    state.pop("error_type", None)
    _atomic(runtime / "current-report.json", summary)
    _atomic(runtime / "state.json", state)
    return recovery


@contextmanager
def _locked_runtime(runtime, contract):
    if runtime.resolve().is_relative_to(ROOT):
        raise ValueError("Private cycle runtime must be outside the repository")
    runtime.mkdir(parents=True, exist_ok=True)
    with (runtime / "cycle.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another rolling72 cycle holds this runtime") from None
        try:
            path = runtime / "source-contract.json"
            if path.exists():
                if json.loads(path.read_text()) != contract:
                    raise ValueError("Bounded cycle contract changed")
            elif any(path.name != "cycle.lock" for path in runtime.iterdir()):
                raise ValueError("An empty private runtime is required")
            else:
                _immutable(path, _json(contract))
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def cycle(database, source_path, artifactdir, identity_registry_path, freeze_path, runtime, until, *,
          capture_now=False, reader=None, storage=None, synthetic_test=False) -> dict:
    """Run one guarded cycle; callers may check locally without network each minute."""
    started, end = _now(), _time(until)
    if end - started > timedelta(hours=96):
        raise ValueError("Cycle deadline must be within96hours")
    if end <= started:
        result = {"version": VERSION, "status": "DEADLINE_EXPIRED", "network_reads": 0,
                  "checked_at": started.isoformat(), "production_change": False, "live_adjustment": 0}
        existing = Path(runtime)
        marker = existing / "source-contract.json"
        if marker.is_file() and not existing.resolve().is_relative_to(ROOT):
            contract = json.loads(marker.read_text())
            if contract.get("version") == VERSION and contract.get("until") == end.isoformat():
                _audit(existing, result)
        return result
    if not isinstance(capture_now, bool):
        raise ValueError("capture_now must be an explicit boolean")
    database, source_path, artifactdir, identity_registry_path, freeze_path, runtime = map(Path, (
        database, source_path, artifactdir, identity_registry_path, freeze_path, runtime))
    registry_payload = identity_registry_path.read_bytes()
    freeze, loaded, _, _, _ = _load_freeze(freeze_path, artifactdir, registry_payload, started, synthetic_test)
    contract = {"version": VERSION, "runner_sha256": _digest(Path(__file__).read_bytes()),
                "database": str(database.resolve()), "until": end.isoformat(),
                "identity_registry_sha256": _digest(registry_payload),
                "initial_source_sha256": _digest(source_path.read_bytes()),
                "model_manifest_sha256": loaded["manifest"]["manifest_sha256"],
                "model_file_sha256": loaded["manifest"]["model_file_sha256"],
                "artifactdir": str(artifactdir.resolve()), "synthetic_test": synthetic_test,
                "dependency_sha256": {name: _digest((ROOT / name).read_bytes()) for name in (
                    "ml/rolling72_cycle_v1.py", "ml/rolling72_backup_v2.py")},
                "freeze_file_sha256": _digest(freeze_path.read_bytes())}
    with _locked_runtime(runtime, contract):
        state_path = runtime / "state.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {
            "version": VERSION, "until": end.isoformat(), "source_paths": [str(source_path.resolve())]}
        if state.get("version") != VERSION or state.get("until") != end.isoformat():
            raise ValueError("Invalid bounded cycle state")
        due = due_status(database, started)
        checkpoint = _checkpoint(database)
        result = {"version": VERSION, "status": "NOT_DUE", "checked_at": started.isoformat(),
                  "until": end.isoformat(), "due": due, "network_reads": 0,
                  "production_change": False, "live_adjustment": 0}
        if "checkpoint" in state and state["checkpoint"] != checkpoint:
            try:
                result["backup"] = _finish(database, source_path, artifactdir, identity_registry_path, freeze_path, runtime, state, storage, "recover_committed_ledger", synthetic_test=synthetic_test)
                result["status"] = "RECOVERED_COMMITTED_LEDGER"
            except Exception as exc:
                state.update(last_status="FAILED_CLOSED", failure_stage="recover_committed_ledger", error_type=type(exc).__name__)
                _atomic(state_path, state)
                result.update(status="FAILED_CLOSED", failure_stage="recover_committed_ledger", error_type=type(exc).__name__)
            _audit(runtime, result)
            return result
        if not capture_now and not due["due"]:
            state.update({"checkpoint": checkpoint, "last_checked_at": started.isoformat(), "last_status": "NOT_DUE"})
            _atomic(state_path, state)
            _audit(runtime, result)
            return result
        previous_attempt = state.get("last_network_attempt_at")
        if previous_attempt and started - _time(previous_attempt) < timedelta(seconds=MIN_RETRY_SECONDS):
            result["status"] = "RETRY_INTERVAL_NOT_DUE"
            _audit(runtime, result)
            return result
        state.update({"checkpoint": checkpoint, "last_network_attempt_at": started.isoformat(),
                      "last_checked_at": started.isoformat(), "last_status": "IN_PROGRESS"})
        _atomic(state_path, state)
        stage = "source_read"
        try:
            current_source = Path(state.get("current_source_path", source_path))
            selected_reader = reader if reader is not None else BoundedReader()

            class CountedReader:
                def rows(self, table, parameters):
                    result["network_reads"] += 1
                    return selected_reader.rows(table, parameters)

            payload, new_rows = _refresh(current_source.read_bytes(), identity_registry_path.read_bytes(), CountedReader())
            if _now() >= end:
                raise ValueError("Deadline expired during source read")
            sources = runtime / "sources"
            sources.mkdir(exist_ok=True)
            path = sources / ("source-" + _digest(payload) + ".json")
            _immutable(path, payload)
            state["current_source_path"] = str(path.resolve())
            _atomic(state_path, state)
            stage = "score"
            result["scoring"] = score(database, payload, artifactdir, freeze_path, registry_payload, synthetic_test=synthetic_test)
            capture_ids = set(due["capture_event_ids"])
            data = json.loads(payload)
            if capture_now:
                capture_ids = {event["ticket_event_id"] for event in data["events"]}
            if capture_ids:
                stage = "capture"
                if _now() >= end:
                    raise ValueError("Deadline expired before actual new capture")
                selected = [event for event in data["events"] if event["ticket_event_id"] in capture_ids]
                if selected:
                    capture_source = payload
                    if len(selected) != len(data["events"]):
                        data.update(events=selected, capture_subset_of_sha256=_digest(payload))
                        data.pop("export_sha256", None)
                        data["export_sha256"] = _hash(data)
                        capture_source = _json(data)
                        _immutable(sources / ("source-" + _digest(capture_source) + ".json"), capture_source)
                    result["capture"] = capture(database, capture_source, artifactdir, freeze_path, registry_payload, synthetic_test=synthetic_test)
            stage = "private_backup"
            state["current_source_path"] = str(path.resolve())
            result["backup"] = _finish(database, source_path, artifactdir, identity_registry_path, freeze_path, runtime, state, storage, "source_score_capture", synthetic_test=synthetic_test)
            result.update(status="SUCCESS", incremental_snapshot_count=new_rows,
                          source_sha256=_digest(payload), completed_at=_now().isoformat())
        except Exception as exc:
            state.update(last_status="FAILED_CLOSED", failure_stage=stage, error_type=type(exc).__name__)
            _atomic(state_path, state)
            result.update(status="FAILED_CLOSED", failure_stage=stage, error_type=type(exc).__name__)
        _audit(runtime, result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("database", "source", "artifactdir", "identity-registry", "freeze", "runtime"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--until", required=True)
    parser.add_argument("--capture-now", action="store_true")
    args = parser.parse_args()
    result = cycle(args.database, args.source, args.artifactdir, args.identity_registry, args.freeze,
                   args.runtime, args.until, capture_now=args.capture_now)
    print(json.dumps(result, sort_keys=True))
    if result["status"] == "FAILED_CLOSED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
