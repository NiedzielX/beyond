"""Bounded cloud worker: local due checks, no catch-up forecasts or global polls.

The independent cycle owns source/score/capture/backup transactions. This wrapper
only keeps checking while the cloud host exists, with an explicit <=96h expiry.
It does not keep an AI coding session alive after account/session limits.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import threading

from ml.demand_engine.rolling72_features_v1 import _hash, _time
from ml.rolling72_cycle_v2 import cycle


VERSION = "rolling72-bounded-worker-v2"
ROOT = Path(__file__).resolve().parent.parent


def _now():
    return datetime.now(timezone.utc)


def _atomic(path, payload):
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    temporary.replace(path)


def run_worker(database, source_path, artifactdir, identity_registry_path, freeze_path, runtime, until,
               *, interval_seconds=60, stop_event=None, clock=None, wait=None, cycle_fn=None):
    """Run actual-time cycles. Clock/wait/cycle injection is for unit tests only."""
    clock, cycle_fn = clock or _now, cycle_fn or cycle
    stop_event = stop_event or threading.Event()
    wait = wait or stop_event.wait
    if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, int) or not 15 <= interval_seconds <= 60:
        raise ValueError("Local check interval must be15..60seconds")
    started, end = _time(clock()), _time(until)
    if not timedelta(0) < end - started <= timedelta(hours=96):
        raise ValueError("Worker requires a future deadline within96hours")
    runtime = Path(runtime).resolve()
    if runtime.is_relative_to(ROOT):
        raise ValueError("Private worker state must remain outside Git")
    paths = [Path(value).resolve() for value in (database, source_path, artifactdir, identity_registry_path, freeze_path)]
    model_files = [paths[2] / name for name in ("manifest.json", "fit-marker.json", "model.joblib")]
    regular = [paths[i] for i in (0, 1, 3, 4)] + model_files
    if any(not path.is_file() or path.is_symlink() for path in regular):
        raise ValueError("Existing original ledger/source/identity/freeze files required")
    runtime.mkdir(parents=True, exist_ok=True)
    lock = (runtime / "worker.lock").open("a")
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another worker owns this runtime") from None
        contract = {"version": VERSION, "until": end.isoformat(),
                    "interval_seconds": interval_seconds, "database": str(paths[0]),
                    "source": str(paths[1]), "artifactdir": str(paths[2]),
                    "identity_registry": str(paths[3]), "freeze": str(paths[4]),
                    "initial_source_sha256": hashlib.sha256(paths[1].read_bytes()).hexdigest(),
                    "model_file_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in model_files},
                    "worker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    "cycle_sha256": hashlib.sha256((ROOT / "ml/rolling72_cycle_v2.py").read_bytes()).hexdigest(),
                    "registry_sha256": hashlib.sha256(paths[3].read_bytes()).hexdigest(),
                    "freeze_sha256": hashlib.sha256(paths[4].read_bytes()).hexdigest()}
        marker = runtime / "worker-contract.json"
        if marker.exists():
            if json.loads(marker.read_text()) != contract:
                raise ValueError("Worker contract changed; preserve old runtime and use a new activation")
        else:
            if any(p.name != "worker.lock" for p in runtime.iterdir()):
                raise ValueError("First activation requires its own empty worker runtime")
            with marker.open("x") as stream:
                json.dump(contract, stream, indent=2, sort_keys=True)
        state = {"version": VERSION, "pid": os.getpid(), "started_at": started.isoformat(),
                 "until": end.isoformat(), "status": "STARTING", "cycle_count": 0,
                 "error_count": 0, "network_reads": 0,
                 "worker_contract_sha256": _hash(contract),
                 "host_dependent": True, "production_change": False, "live_adjustment": 0}
        _atomic(runtime / "worker-state.json", state)
        while not stop_event.is_set() and _time(clock()) < end:
            try:
                result = cycle_fn(*paths, runtime / "cycle", end.isoformat())
                failed_closed = result.get("status") == "FAILED_CLOSED"
                state.update({"last_cycle": result,
                              "status": "RUNNING_WITH_FAILED_CYCLE" if failed_closed else "RUNNING",
                              "error_count": state["error_count"] + int(failed_closed),
                              "cycle_count": state["cycle_count"] + 1,
                              "last_checked_at": _time(clock()).isoformat(),
                              "network_reads": state["network_reads"] + result.get("network_reads", 0)})
                with (runtime / "worker-audit.jsonl").open("a") as audit:
                    audit.write(json.dumps({"at": state["last_checked_at"], "status": result.get("status"),
                                            "network_reads": result.get("network_reads", 0)}) + "\n")
            except Exception as exc:
                state.update({"status": "RUNNING_WITH_FAILED_CYCLE", "error_count": state["error_count"] + 1,
                              "last_error_type": type(exc).__name__, "last_checked_at": _time(clock()).isoformat()})
                # Preserve only the exception type: requests may contain private context.
                with (runtime / "worker-audit.jsonl").open("a") as audit:
                    audit.write(json.dumps({"at": state["last_checked_at"], "status": "FAILED_CLOSED",
                                            "error_type": type(exc).__name__}) + "\n")
            _atomic(runtime / "worker-state.json", state)
            remaining = (end - _time(clock())).total_seconds()
            if remaining <= 0:
                break
            wait(min(interval_seconds, remaining))
        state.update({"status": "STOPPED" if stop_event.is_set() else "DEADLINE_EXPIRED",
                      "stopped_at": _time(clock()).isoformat()})
        _atomic(runtime / "worker-state.json", state)
        return state
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("database", "source", "artifactdir", "identity-registry", "freeze", "runtime"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--until", required=True)
    parser.add_argument("--interval", type=int, default=60)
    args = parser.parse_args()
    stopped = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda signum, frame: stopped.set())
    result = run_worker(args.database, args.source, args.artifactdir, args.identity_registry, args.freeze,
                        args.runtime, args.until, interval_seconds=args.interval, stop_event=stopped)
    print(json.dumps({key: result[key] for key in ("version", "status", "cycle_count", "error_count", "network_reads", "until")}))


if __name__ == "__main__":
    main()
