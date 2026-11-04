"""Bounded operational guardian for already-deployed frozen-encoder workflow."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.run_daily_inventory_path_v1 import PublicInventoryReader

UTC = timezone.utc
WORKFLOW = "trajectory-frozen-encoder-shadow-v1.yml"
GITHUB_BASE = "https://api.github.com/repos/NiedzielX/beyond"


def open_checkpoints(summary: dict, now: datetime) -> list[dict]:
    if summary.get("production_change") is not False or summary.get("live_adjustment") != 0:
        raise ValueError("Unexpected production flags in decision summary")
    checked = parse_timestamp(summary["checked_at"])
    if not now-timedelta(minutes=2) <= checked <= now+timedelta(minutes=1):
        raise ValueError("Stale decision summary")
    preflight = summary["operational_state"]["trajectory_preflight"]
    if (preflight.get("model_version") != "trajectory-frozen-encoder-ridge-ratio-head-v1"
            or preflight.get("target_values_used") is not False or preflight.get("production_change") is not False):
        raise ValueError("Unexpected frozen preflight contract")
    checkpoints = preflight["checkpoints"]
    if not isinstance(checkpoints, list):
        raise ValueError("Malformed checkpoint response")
    result, identities = [], set()
    for point in checkpoints:
        event, days = point["ticket_event_id"], point["days_to_event"]
        cutoff = parse_timestamp(point["cutoff_at"])
        identity = (event, days, cutoff)
        if identity in identities:
            raise ValueError("Duplicate frozen checkpoint")
        identities.add(identity)
        if days not in (1, 3, 7) or not isinstance(event, int) or isinstance(event, bool) or event <= 0:
            raise ValueError("Invalid frozen checkpoint identity")
        if cutoff != parse_timestamp(point["kickoff_at"])-timedelta(days=days):
            raise ValueError("Inconsistent frozen cutoff coordinate")
        if point.get("attempted_at") is not None or point.get("prediction_id") is not None or point.get("attempt_status") is not None:
            continue
        if point.get("status") not in {"WINDOW_OPEN_READY", "WINDOW_OPEN_NO_INCUMBENT", "WINDOW_OPEN_INPUT_INSUFFICIENT"}:
            continue
        if cutoff <= now <= cutoff+timedelta(minutes=90):
            result.append({"ticket_event_id": event, "days_to_event": days, "cutoff_at": cutoff.isoformat(),
                           "source_status": point.get("status"), "input_ready": point.get("input_ready")})
    return sorted(result, key=lambda row: (row["cutoff_at"], row["ticket_event_id"]))


class GuardianAPI:
    def __init__(self):
        reader = PublicInventoryReader()
        self.supabase_base, self.supabase_headers = reader.base, reader.headers
        token = os.environ.get("GH_TOKEN", "")
        if not token:
            raise ValueError("GitHub credential binding missing")
        self.github_headers = {"Authorization": "Bearer "+token, "Accept": "application/vnd.github+json",
                               "Content-Type": "application/json"}

    def request(self, url, headers, payload=None):
        encoded = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(url, data=encoded, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
                return json.loads(data) if data else None
        except urllib.error.HTTPError as exc:
            raise ValueError(f"Guardian request failed with HTTP{exc.code}") from None
        except urllib.error.URLError:
            raise ValueError("Guardian request failed at network boundary") from None

    def decision(self):
        return self.request(self.supabase_base+"/rest/v1/rpc/prospective_decision_summary_v1",
                            {**self.supabase_headers, "Content-Type": "application/json"}, {"p_horizon_days": 10})

    def active_main_runs(self):
        data = self.request(GITHUB_BASE+f"/actions/workflows/{WORKFLOW}/runs?per_page=10", self.github_headers)
        runs = data.get("workflow_runs")
        if not isinstance(runs, list):
            raise ValueError("Malformed workflow-run response")
        return [run["id"] for run in runs if run.get("head_branch") == "main"
                and run.get("status") in {"queued", "in_progress", "requested", "waiting", "pending"}]

    def dispatch(self):
        self.request(GITHUB_BASE+f"/actions/workflows/{WORKFLOW}/dispatches", self.github_headers, {"ref": "main"})


def cycle(api: GuardianAPI, state: dict, now: datetime) -> dict:
    summary = api.decision()
    due = open_checkpoints(summary, now)
    result = {"checked_at": now.isoformat(), "open_checkpoints": due, "dispatched": False,
              "workflow": WORKFLOW, "production_change": False, "live_adjustment": 0}
    if not due:
        return {**result, "status": "NO_LEGAL_UNRECORDED_CHECKPOINT"}
    active = api.active_main_runs()
    if active:
        return {**result, "status": "EXISTING_MAIN_RUN_ACTIVE", "active_run_ids": active}
    previous = state.get("last_dispatch_at")
    if previous is not None and now-parse_timestamp(previous) < timedelta(minutes=10):
        return {**result, "status": "DISPATCH_COOLDOWN"}
    api.dispatch()
    state["last_dispatch_at"] = now.isoformat()
    return {**result, "status": "DISPATCHED_AWAITING_RUN_AND_DB_EVIDENCE", "dispatched": True}


@contextmanager
def guardian_lock(runtime: Path):
    runtime.mkdir(parents=True, exist_ok=True)
    with (runtime/"guardian.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another frozen-window guardian is active") from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--watch-until", required=True)
    parser.add_argument("--interval-seconds", type=int, default=60)
    args = parser.parse_args()
    stop = parse_timestamp(args.watch_until)
    if not datetime.now(UTC) < stop <= datetime.now(UTC)+timedelta(hours=24) or args.interval_seconds < 60:
        parser.error("Guardian must stop within24hours; interval must be at least60seconds")
    api = GuardianAPI()
    with guardian_lock(args.runtime):
        (args.runtime/"guardian.pid").write_text(str(os.getpid())+"\n")
        state_file = args.runtime/"guardian-state.json"
        state = json.loads(state_file.read_text()) if state_file.exists() else {}
        failures = 0
        while datetime.now(UTC) < stop:
            try:
                result = cycle(api, state, datetime.now(UTC))
                failures = 0
            except (ValueError, OSError, KeyError, TypeError) as exc:
                failures += 1
                result = {"status": "FAILED_CLOSED", "checked_at": datetime.now(UTC).isoformat(),
                          "consecutive_failures": failures, "production_change": False}
                result["error_type"] = type(exc).__name__
            state_file.write_text(json.dumps(state, indent=2)+"\n")
            (args.runtime/"guardian-latest.json").write_text(json.dumps(result, indent=2)+"\n")
            with (args.runtime/"guardian-audit.jsonl").open("a") as stream:
                stream.write(json.dumps(result)+"\n")
            print(json.dumps(result), flush=True)
            if failures >= 3:
                return 2
            deadline = time.monotonic()+args.interval_seconds
            while datetime.now(UTC) < stop and time.monotonic() < deadline:
                time.sleep(min(10, max(0, (stop-datetime.now(UTC)).total_seconds()), max(0, deadline-time.monotonic())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
