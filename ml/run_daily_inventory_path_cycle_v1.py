"""One repeatable research cycle, optionally watched in this cloud machine.

No retraining, no production updates, no SQL deployment. A running watcher is
dependent on its host/session; it is not an always-on coding agent.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import json
from pathlib import Path
import time

from ml.run_daily_inventory_path_v1 import (
    PublicInventoryReader, _dump, export_public, ledger_preview, ledger_metrics, shadow,
)
from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger
from ml.demand_engine.daily_inventory_path_model_v1 import load_model
from ml.demand_engine.daily_inventory_path_storage_v1 import backup_ledger

UTC = timezone.utc


@contextmanager
def exclusive_cycle(runtime: Path):
    runtime.mkdir(parents=True, exist_ok=True)
    with (runtime / "cycle.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another daily-path cycle is already running") from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def run_cycle(runtime: str | Path, artifact: str | Path, panel_feed: str | Path | None = None) -> dict:
    runtime = Path(runtime)
    with exclusive_cycle(runtime):
        model = load_model(artifact)
        now = datetime.now(UTC)
        label = now.strftime("%Y%m%dT%H%M%S.%fZ")
        summary = {"started_at": now.isoformat(), "model_sha256": model["model_sha256"],
                   "production_change": False, "live_adjustment": 0, "status": "STARTED"}
        ledger_path = runtime / "shadow-v1.sqlite"
        # Create an empty valid ledger so even a partial first cycle can be backed up.
        with DailyInventoryPathLedger(ledger_path):
            pass
        failure = None
        try:
            data = export_public(PublicInventoryReader(), now)
            _dump(runtime / f"public-export-{label}.json", data, exclusive=True)
            summary["export_sha256"] = data["export_sha256"]
            summary["shadow"] = shadow(data, model, ledger_path)
            with DailyInventoryPathLedger(ledger_path) as ledger:
                summary["scores"] = ledger.score(data["events"], data["exported_at"])
            summary["evaluation"] = ledger_metrics(ledger_path, data["exported_at"])
            summary["status"] = "CAPTURED_AND_SCORED"
        except (ValueError, OSError, KeyError, TypeError) as exc:
            # Retain the successfully written prefix of a cycle, without weakening
            # a failed input/window check or pretending the rest succeeded.
            failure = exc
            summary["status"] = "FAILED_CLOSED"
            summary["error_type"] = type(exc).__name__
        finally:
            # Always preserve existing local evidence, even if a later event/read failed.
            try:
                backup = backup_ledger(ledger_path, artifact)
                summary["backup"] = {"bucket": backup["bucket"],
                                     "manifest_key": backup["manifest_object"]["key"],
                                     "read_back_verified": True}
                _dump(runtime / f"storage-backup-{label}.json", backup, exclusive=True)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                summary["backup_error_type"] = type(exc).__name__
                summary["status"] = "FAILED_CLOSED"
                failure = failure or exc
            if panel_feed is not None:
                _dump(panel_feed, ledger_preview(ledger_path))
            summary["finished_at"] = datetime.now(UTC).isoformat()
            _dump(runtime / f"cycle-{label}.json", summary, exclusive=True)
            _dump(runtime / "latest-cycle.json", summary)
        if failure is not None:
            raise ValueError("Daily-path cycle failed closed; inspect latest-cycle.json") from failure
        return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--artifact", default="ml/artifacts/daily_inventory_path_v1.json")
    parser.add_argument("--panel-feed")
    parser.add_argument("--watch-until", help="UTC/offset timestamp; bounded host-dependent watcher")
    parser.add_argument("--interval-seconds", type=int, default=900)
    args = parser.parse_args(argv)
    if args.interval_seconds < 60:
        parser.error("Interval must be at least 60 seconds")
    stop = parse_timestamp(args.watch_until) if args.watch_until else None
    if stop is not None and stop > datetime.now(UTC) + timedelta(hours=24):
        parser.error("A local watcher is bounded to at most 24 hours")
    failures = 0
    while stop is None or datetime.now(UTC) < stop:
        started = time.monotonic()
        try:
            result = run_cycle(args.runtime, args.artifact, args.panel_feed)
            print(json.dumps(result), flush=True)
            failures = 0
        except (ValueError, OSError) as exc:
            failures += 1
            print(json.dumps({"status": "FAILED_CLOSED", "error_type": type(exc).__name__,
                              "consecutive_failures": failures}), flush=True)
        if stop is None:
            return int(failures > 0)
        if failures >= 3:
            return 2
        deadline = started + args.interval_seconds
        # Short waits keep termination responsive; do not perform a single long sleep.
        while time.monotonic() < deadline and datetime.now(UTC) < stop:
            time.sleep(min(10.0, deadline - time.monotonic(), max(0.0, (stop - datetime.now(UTC)).total_seconds())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
