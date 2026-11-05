"""Protect genuine P9 windows by dispatching the existing main heartbeat only."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from ml.c1_live_matched_audit_v1 import ROOT
from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.frozen_window_guardian_v1 import GuardianAPI, GITHUB_BASE

P9 = 'p9-booking-curve-prospective-v1.yml'
HEARTBEAT = 'p9-prospective-heartbeat-v1.yml'
VERSION = 'p9-heartbeat-window-guardian-v1'
UTC = timezone.utc


def open_windows(summary, now):
    if (summary.get('production_change') is not False or summary.get('live_adjustment') != 0
            or not now-timedelta(minutes=2) <= parse_timestamp(summary['checked_at']) <= now+timedelta(minutes=1)):
        raise ValueError('Stale or invalid decision summary')
    preflight = summary['operational_state']['p9_preflight']
    if (preflight.get('version') != 'p9-prospective-preflight-v1'
            or preflight.get('production_change') is not False or preflight.get('target_values_used') is not False
            or parse_timestamp(preflight['checked_at']) != parse_timestamp(summary['checked_at'])
            or abs((now-parse_timestamp(preflight['checked_at'])).total_seconds()) > 120):
        raise ValueError('Invalid P9 preflight contract')
    due, seen = [], set()
    for event in preflight['events']:
        event_id = event['ticket_event_id']
        if isinstance(event_id, bool) or not isinstance(event_id, int) or event_id <= 0 or event_id in seen:
            raise ValueError('Duplicate or invalid event identity')
        seen.add(event_id)
        kickoff = parse_timestamp(event['kickoff_at'])
        for hours in (48, 24):
            field = f't{hours}'
            cutoff = parse_timestamp(event[field+'_at'])
            if cutoff != kickoff-timedelta(hours=hours):
                raise ValueError('P9 cutoff coordinate drift')
            prediction = event['prediction_'+field+'_exists']
            if not isinstance(prediction, bool):
                raise ValueError('Malformed prediction flag')
            if event['attempt_'+field+'_status'] is not None or prediction:
                continue
            if cutoff <= now <= cutoff+timedelta(minutes=90):
                due.append({'ticket_event_id': event_id, 'cutoff_hours': hours,
                    'cutoff_at': cutoff.isoformat(), 'source_status': event[field+'_status']})
    return sorted(due, key=lambda p: (p['cutoff_at'], p['ticket_event_id']))


class P9API(GuardianAPI):
    def active_p9_runs(self):
        active = []
        for workflow in (P9, HEARTBEAT):
            value = self.request(GITHUB_BASE+f'/actions/workflows/{workflow}/runs?branch=main&per_page=100', self.github_headers)
            runs = value.get('workflow_runs')
            if not isinstance(runs, list):
                raise ValueError('Malformed P9 workflow list')
            active.extend(r['id'] for r in runs if r.get('head_branch') == 'main'
                          and r.get('status') in {'queued', 'in_progress', 'requested', 'waiting', 'pending'})
        return active

    def dispatch_heartbeat(self):
        self.request(GITHUB_BASE+f'/actions/workflows/{HEARTBEAT}/dispatches', self.github_headers, {'ref': 'main'})


def cycle(api, state, clock=lambda: datetime.now(UTC), deadline=None, persist_state=lambda state: None):
    summary = api.decision()
    now = clock()
    due = open_windows(summary, now)
    result = {'version': VERSION, 'checked_at': now.isoformat(), 'open_windows': due,
        'dispatched': False, 'hosted_workflow_chain_done': False,
        'production_change': False, 'live_adjustment': 0}
    if not due:
        return {**result, 'status': 'NO_LEGAL_UNRECORDED_WINDOW'}
    previous = state.get('last_dispatch_at')
    if previous is not None and now-parse_timestamp(previous) < timedelta(minutes=10):
        return {**result, 'status': 'DISPATCH_COOLDOWN'}
    counts = state.get('window_dispatch_counts', {})
    key = lambda p: f"{p['ticket_event_id']}/{p['cutoff_hours']}/{p['cutoff_at']}"
    eligible = [p for p in due if counts.get(key(p), 0) < 3]
    if not eligible:
        return {**result, 'status': 'WINDOW_DISPATCH_LIMIT_REACHED'}
    active = api.active_p9_runs()
    if active:
        return {**result, 'status': 'EXISTING_MAIN_P9_OR_HEARTBEAT_ACTIVE', 'active_run_ids': active}
    # Re-check actual time and source freshness after potentially slow network reads.
    issued = clock()
    if deadline is not None and issued >= deadline:
        return {**result, 'status': 'GUARDIAN_DEADLINE_REACHED'}
    legal = {key(p) for p in open_windows(summary, issued)}
    eligible = [p for p in eligible if key(p) in legal]
    if not eligible:
        return {**result, 'status': 'WINDOW_CLOSED_BEFORE_DISPATCH'}
    # Persist the dispatch intent first: a timeout can follow an accepted remote request.
    # Ambiguous attempts still consume cooldown/retry budget, preventing request storms.
    state['last_dispatch_at'] = issued.isoformat()
    state['window_dispatch_counts'] = {**counts, **{key(p): counts.get(key(p), 0)+1 for p in eligible}}
    persist_state(state)
    api.dispatch_heartbeat()
    return {**result, 'status': 'HEARTBEAT_DISPATCH_ACCEPTED_AWAITING_CHILD_AND_DB',
        'dispatched': True, 'dispatch_requested_at': issued.isoformat(), 'dispatched_for': eligible}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--until', required=True)
    p.add_argument('--interval', type=int, default=60)
    a = p.parse_args(); now = datetime.now(UTC); until = parse_timestamp(a.until)
    if not now < until <= now+timedelta(hours=24) or a.interval < 30 or a.runtime.resolve().is_relative_to(ROOT):
        p.error('Require private runtime, deadline within24hours and interval at least30seconds')
    a.runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    names = ['ml/p9_heartbeat_window_guardian_v1.py', 'ml/frozen_window_guardian_v1.py']
    digests = lambda: {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
    expected = {'version': VERSION, 'source_sha256': digests()}
    with (a.runtime/'guardian.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        contract = a.runtime/'source-contract.json'
        if contract.exists():
            if json.loads(contract.read_text()) != expected:
                raise ValueError('Guardian source changed; preserve old runtime')
        else:
            if any(v.name != 'guardian.lock' for v in a.runtime.iterdir()):
                raise ValueError('Refuse a nonempty unmarked runtime')
            with contract.open('x') as f: json.dump(expected, f, indent=2)
        (a.runtime/'guardian-launch.json').write_text(json.dumps({'pid': os.getpid(), 'started_at': now.isoformat(),
            'until': until.isoformat(), 'interval_seconds': a.interval, 'host_dependent': True,
            'production_change': False, 'live_adjustment': 0}, indent=2))
        path = a.runtime/'guardian-state.json'; state = json.loads(path.read_text()) if path.exists() else {}
        api = P9API()
        while datetime.now(UTC) < until:
            if digests() != expected['source_sha256']:
                raise ValueError('Published guardian implementation changed')
            try: result = cycle(api, state, deadline=until,
                                persist_state=lambda value: path.write_text(json.dumps(value, indent=2)))
            except Exception as exc:
                result = {'status': 'FAILED_CLOSED', 'checked_at': datetime.now(UTC).isoformat(),
                    'error_type': type(exc).__name__, 'production_change': False, 'live_adjustment': 0}
            path.write_text(json.dumps(state, indent=2))
            (a.runtime/'guardian-latest.json').write_text(json.dumps(result, indent=2))
            with (a.runtime/'guardian-audit.jsonl').open('a') as f: f.write(json.dumps(result)+'\n')
            print(json.dumps(result), flush=True)
            time.sleep(min(a.interval, max(0., (until-datetime.now(UTC)).total_seconds())))


if __name__ == '__main__':
    main()
