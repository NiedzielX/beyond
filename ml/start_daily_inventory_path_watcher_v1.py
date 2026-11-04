"""Launch one detached, time-bounded inference worker; inspect actual cycle health."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.run_daily_inventory_path_cycle_v1 import exclusive_cycle

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = ROOT/"ml/artifacts/daily_inventory_path_v1.json"
UTC = timezone.utc


def process_alive(pid: int) -> bool:
    if pid <= 1:
        raise ValueError("Invalid worker PID; inspect runtime state before launching")
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


@contextmanager
def launch_lock(runtime: Path):
    runtime.mkdir(parents=True, exist_ok=True)
    with (runtime/"watcher-launch.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another worker launcher is active") from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def start_worker(runtime: Path, stop_at: str, panel_feed: Path | None = None, interval: int = 900) -> dict:
    runtime = runtime.resolve()
    now = datetime.now(UTC)
    stop = parse_timestamp(stop_at)
    if not now < stop <= now+timedelta(hours=24) or not isinstance(interval, int) or interval < 60:
        raise ValueError("Worker must stop within24hours; interval must be at least60seconds")
    with launch_lock(runtime):
        pidfile = runtime/"watcher.pid"
        if pidfile.exists():
            try:
                pid = int(pidfile.read_text().strip())
            except ValueError:
                raise ValueError("Malformed worker PID; inspect state before launching") from None
            if process_alive(pid):
                return {"status": "ALREADY_RUNNING", "pid": pid, "new_worker_started": False,
                        "requested_watch_until": stop.isoformat(), "host_dependent": True}
        # Release the cycle lock before the new subprocess can try to acquire it.
        with exclusive_cycle(runtime):
            pass
        label = now.strftime("%Y%m%dT%H%M%SZ")
        logfile = runtime/f"watcher-{label}.log"
        command = [sys.executable, "-u", "-m", "ml.run_daily_inventory_path_cycle_v1",
                   "--runtime", str(runtime), "--artifact", str(ARTIFACT),
                   "--watch-until", stop.isoformat(), "--interval-seconds", str(interval)]
        if panel_feed is not None:
            command += ["--panel-feed", str(panel_feed.resolve())]
        with os.fdopen(os.open(logfile, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600), "ab", buffering=0) as log:
            child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
        state = {"pid": child.pid, "started_at": now.isoformat(), "watch_until": stop.isoformat(),
                 "interval_seconds": interval, "detached": True, "host_dependent": True,
                 "logfile": str(logfile), "production_change": False}
        try:
            (runtime/"watcher-launch.json").write_text(json.dumps(state, indent=2)+"\n")
            pidfile.write_text(str(child.pid)+"\n")
        except OSError:
            child.terminate()  # Only the new child owned by this exact launcher.
            raise
        return {"status": "LAUNCHED_NOT_YET_CYCLE_VERIFIED", "new_worker_started": True, **state}


def worker_status(runtime: Path) -> dict:
    runtime = runtime.resolve()
    result = {"status": "STOPPED", "worker_alive": False, "recent_cycle_verified": False,
              "host_dependent": True, "production_change": False}
    if not (runtime/"watcher.pid").exists():
        return result
    pid = int((runtime/"watcher.pid").read_text().strip())
    alive = process_alive(pid)
    result.update(pid=pid, worker_alive=alive)
    if not alive:
        return result
    result["status"] = "RUNNING_AWAITING_VERIFIED_CYCLE"
    launch = json.loads((runtime/"watcher-launch.json").read_text())
    result["watch_until"] = launch["watch_until"]
    if not (runtime/"latest-cycle.json").exists():
        return result
    cycle = json.loads((runtime/"latest-cycle.json").read_text())
    finished = parse_timestamp(cycle["finished_at"])
    age = (datetime.now(UTC)-finished).total_seconds()
    expected_hash = json.loads(ARTIFACT.read_text())["model_sha256"]
    valid = (cycle.get("status") == "CAPTURED_AND_SCORED"
             and cycle.get("backup", {}).get("read_back_verified") is True
             and cycle.get("model_sha256") == expected_hash
             and finished >= parse_timestamp(launch["started_at"])
             and datetime.now(UTC) < parse_timestamp(launch["watch_until"])
             and 0 <= age <= 2*launch.get("interval_seconds", 900))
    result.update(status="HEALTHY" if valid else "RUNNING_WITHOUT_RECENT_VERIFIED_CYCLE",
                  recent_cycle_verified=valid, last_cycle_at=finished.isoformat(),
                  pending_points=cycle.get("evaluation", {}).get("pending_prediction_count"),
                  scored_points=cycle.get("evaluation", {}).get("labeled_target_count"))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--watch-until")
    parser.add_argument("--interval-seconds", type=int, default=900)
    parser.add_argument("--panel-feed", type=Path)
    args = parser.parse_args()
    if args.status:
        result = worker_status(args.runtime)
    else:
        stop = args.watch_until or (datetime.now(UTC)+timedelta(hours=23)).isoformat()
        result = start_worker(args.runtime, stop, args.panel_feed, args.interval_seconds)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
