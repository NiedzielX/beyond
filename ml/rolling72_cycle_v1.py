"""One bounded actual-time rolling72 source/score/forecast recovery cycle.

Local due checks never poll Supabase. A due cycle reads only the tracked event
metadata and at most499 incremental snapshots per event, preserving genuine
prefix rows and their gaps. Nothing reconstructs missed prospective issues.
The deadline and runner/freeze/registry hashes are locked for this runtime.
The original frozen predictor, label matcher and ledger remain untouched.
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
import urllib.error
import urllib.parse
import urllib.request

from ml.demand_engine.rolling72_features_v1 import _hash, _id, _time
from ml.rolling72_backup_v1 import MAX_FILE_BYTES, backup
from ml.rolling72_feed_v1 import build_feed
from ml.rolling72_receipt_store_v1 import prepare_receipt
from ml.rolling72_shadow_ledger_v1 import APPLICATION_ID, _load_freeze, capture, score


VERSION = "rolling72-bounded-cycle-v1"
ROOT = Path(__file__).resolve().parents[1]
MAX_INCREMENTAL_ROWS = 500
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


class BoundedReader:
    def __init__(self):
        base = os.environ.get("SUPABASE_URL", "").rstrip("/")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if urllib.parse.urlparse(base).scheme != "https" or not key:
            raise ValueError("HTTPS source and service-role binding required")
        self.base = base
        self.headers = {"apikey": key, "Accept": "application/json", "Prefer": "count=exact"}
        if not key.startswith("sb_"):
            self.headers["Authorization"] = "Bearer " + key

    def rows(self, table, parameters):
        if table not in ("ticket_events", "snapshots"):
            raise ValueError("Unapproved bounded source table")
        request = urllib.request.Request(self.base + "/rest/v1/" + table + "?" + urllib.parse.urlencode(parameters), headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.load(response)
                content_range = response.headers.get("Content-Range", "")
        except urllib.error.HTTPError as exc:
            raise ValueError(f"Bounded source returned HTTP {exc.code}") from None
        if not isinstance(result, list) or "/" not in content_range:
            raise ValueError("Bounded source lacks exact count receipt")
        total = content_range.rsplit("/", 1)[1]
        if not total.isdecimal() or int(total) != len(result):
            raise ValueError("Bounded source is truncated or count is unknown")
        if table == "snapshots" and len(result) >= MAX_INCREMENTAL_ROWS:
            raise ValueError("Incremental snapshot cap reached; refusing truncation")
        return result


def _identity(row):
    required = ("provider", "source_domain", "club_slug", "external_event_id")
    if any(row.get(key) is None or not str(row[key]).strip() for key in required):
        raise ValueError("Complete original source identity required")
    return tuple(str(row[key]).strip() for key in required)


def _refresh(source_raw, registry_raw, reader):
    started = _now()
    prepare_receipt(source_raw, started)
    original = json.loads(source_raw)
    registry = json.loads(registry_raw)
    if not isinstance(registry, list):
        raise ValueError("Original identity registry required")
    identities = {}
    for row in registry:
        identifier = _id(row["id"])
        identity = _identity(row)
        if identifier in identities and identities[identifier] != identity:
            raise ValueError("Conflicting original source identities")
        identities[identifier] = identity
    events = original["events"]
    identifiers = [_id(event["ticket_event_id"]) for event in events]
    if not 1 <= len(identifiers) <= 2 or len(set(identifiers)) != len(identifiers):
        raise ValueError("Cycle is limited to one or two explicit fixtures")
    metadata = reader.rows("ticket_events", [
        ("select", "id,provider,source_domain,club_slug,external_event_id,kickoff_at,competition,home_team,away_team"),
        ("id", "in.(" + ",".join(map(str, identifiers)) + ")"), ("limit", str(len(identifiers))),
    ])
    if not isinstance(metadata, list) or len(metadata) != len(identifiers):
        raise ValueError("Bounded fixture metadata is incomplete")
    indexed = {_id(row["id"]): row for row in metadata}
    if set(indexed) != set(identifiers):
        raise ValueError("Bounded fixture metadata identity mismatch")
    for event in events:
        identifier = event["ticket_event_id"]
        actual = indexed[identifier]
        if (identifier not in identities or _identity(actual) != identities[identifier]
                or actual["club_slug"] != event["club_slug"] or actual["provider"] != event.get("provider")):
            raise ValueError("Current source identity differs from original registry")
    refreshed, new_count = [], 0
    for event in events:
        identifier = event["ticket_event_id"]
        known = {_id(row["snapshot_id"]): row for row in event["observations"]}
        if len(known) != len(event["observations"]):
            raise ValueError("Duplicate original snapshot identity")
        after = max(known, default=0)
        rows = reader.rows("snapshots", [
            ("select", "id,ticket_event_id,captured_at,available_total,source,sector_count"),
            ("ticket_event_id", "eq." + str(identifier)), ("id", "gt." + str(after)),
            ("captured_at", "lte." + started.isoformat()), ("order", "id.asc"),
            ("limit", str(MAX_INCREMENTAL_ROWS)),
        ])
        if not isinstance(rows, list) or len(rows) >= MAX_INCREMENTAL_ROWS:
            raise ValueError("Incremental snapshot cap reached or invalid response")
        for row in rows:
            snapshot = _id(row["id"])
            captured = _time(row["captured_at"])
            if snapshot <= after or snapshot in known or row.get("ticket_event_id") != identifier or captured > started:
                raise ValueError("Incremental snapshot violates identity/time bound")
            source = row.get("source")
            known[snapshot] = {"snapshot_id": snapshot, "captured_at": captured.isoformat(),
                               "available_total": row.get("available_total"),
                               "measurement_key": event["provider"] + "/" + source if isinstance(source, str) and source else "",
                               "source": source, "sector_count": row.get("sector_count")}
            new_count += 1
        actual = indexed[identifier]
        refreshed.append({**event, **{key: actual.get(key) for key in (
            "provider", "source_domain", "club_slug", "external_event_id", "competition", "home_team", "away_team")},
            "kickoff_at": _time(actual["kickoff_at"]).isoformat(),
            "observations": sorted(known.values(), key=lambda row: (_time(row["captured_at"]), row["snapshot_id"]))})
    received = _now()
    if received < started:
        raise ValueError("Source clock moved backwards")
    result = {**original, "events": refreshed, "exported_at": started.isoformat(), "retrieved_at": received.isoformat(),
              "collection_mode": "bounded_incremental_original_prefix",
              "history_complete_between_receipts": False,
              "previous_receipt_sha256": _digest(source_raw),
              "identity_registry_sha256": _digest(registry_raw)}
    result.pop("export_sha256", None)
    result["export_sha256"] = _hash(result)
    payload = _json(result)
    prepare_receipt(payload, received)
    return payload, new_count


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


def _finish(database, source_path, freeze_path, runtime, state, storage, operation):
    paths = _source_paths(database, source_path, runtime, state)
    feed = build_feed(database, generated_at=_now())
    feed_raw = _json(feed)
    _immutable(runtime / ("feed-" + _digest(feed_raw) + ".json"), feed_raw)
    recovery = backup(database, paths, freeze_path, {
        "runner_version": VERSION, "operation": operation, "until": state["until"],
        "cycle_at": _now().isoformat(), "source_file_count": len(paths),
    }, storage=storage)
    state.update({"checkpoint": _checkpoint(database), "source_paths": list(map(str, paths)),
                  "last_backup": recovery, "last_completed_at": _now().isoformat(),
                  "last_status": "SUCCESS", "feed_sha256": _digest(feed_raw)})
    state.pop("failure_stage", None)
    state.pop("error_type", None)
    _atomic(runtime / "current-feed.json", feed)
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


def cycle(database, source_path, identity_registry_path, freeze_path, runtime, until, *,
          capture_now=False, reader=None, storage=None) -> dict:
    """Run one guarded cycle; callers may check locally without network each minute."""
    started, end = _now(), _time(until)
    if end - started > timedelta(hours=72):
        raise ValueError("Cycle deadline must be within72hours")
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
    database, source_path, identity_registry_path, freeze_path, runtime = map(Path, (
        database, source_path, identity_registry_path, freeze_path, runtime))
    _load_freeze(freeze_path, started)
    contract = {"version": VERSION, "runner_sha256": _digest(Path(__file__).read_bytes()),
                "database": str(database.resolve()), "until": end.isoformat(),
                "identity_registry_sha256": _digest(identity_registry_path.read_bytes()),
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
                result["backup"] = _finish(database, source_path, freeze_path, runtime, state, storage, "recover_committed_ledger")
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
        if not capture_now and previous_attempt and started - _time(previous_attempt) < timedelta(seconds=MIN_RETRY_SECONDS):
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
            stage = "score"
            result["scoring"] = score(database, payload, freeze_path)
            capture_ids = set(due["capture_event_ids"])
            data = json.loads(payload)
            if capture_now:
                capture_ids = {event["ticket_event_id"] for event in data["events"]}
            if capture_ids:
                stage = "capture"
                selected = [event for event in data["events"] if event["ticket_event_id"] in capture_ids]
                if selected:
                    capture_source = payload
                    if len(selected) != len(data["events"]):
                        data.update(events=selected, capture_subset_of_sha256=_digest(payload))
                        data.pop("export_sha256", None)
                        data["export_sha256"] = _hash(data)
                        capture_source = _json(data)
                        _immutable(sources / ("source-" + _digest(capture_source) + ".json"), capture_source)
                    result["capture"] = capture(database, capture_source, freeze_path)
            stage = "feed_and_private_backup"
            state["current_source_path"] = str(path.resolve())
            result["backup"] = _finish(database, source_path, freeze_path, runtime, state, storage, "source_score_capture")
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
    for name in ("database", "source", "identity-registry", "freeze", "runtime"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--until", required=True)
    parser.add_argument("--capture-now", action="store_true")
    args = parser.parse_args()
    result = cycle(args.database, args.source, args.identity_registry, args.freeze,
                   args.runtime, args.until, capture_now=args.capture_now)
    print(json.dumps(result, sort_keys=True))
    if result["status"] == "FAILED_CLOSED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
