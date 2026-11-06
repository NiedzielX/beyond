"""Run unchanged inventory collectors only at genuine daily cutoff windows."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import math
from pathlib import Path
import os
import sqlite3
import time

from ml.c1_outcome_scoring_bridge_v1 import save
from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.export_structural_known_at_inputs_v1 import validate_envelope

ROOT = Path(__file__).resolve().parents[1]
DAILY = Path('/workspace/ops-runtime/2026-11-03-daily-path')
DRIFT = Path('/workspace/ops-runtime/2026-11-04-drift-comparator')
ARCHIVE = Path('/workspace/ops-runtime/2026-11-04-known-at-source-archive')
SOURCES = ('ml/daily_path_window_runner_v1.py', 'ml/run_daily_inventory_path_cycle_v1.py',
           'ml/run_daily_inventory_path_v1.py', 'ml/run_daily_inventory_drift_v1.py',
           'ml/artifacts/daily_inventory_path_v1.json', 'ml/artifacts/daily_inventory_drift_comparator_v1.json')


def windows(events, pending, now, training_ids=()):
    if not isinstance(events, list) or len(events) >= 1000:
        raise ValueError('Bounded canonical event metadata required')
    seen, slots = set(), set()
    for event in events:
        identity = event['id']
        if type(identity) is not int or identity <= 0 or identity in seen:
            raise ValueError('Duplicate or invalid canonical event identity')
        seen.add(identity); kickoff = parse_timestamp(event['kickoff_at'])
        if kickoff <= now or identity in training_ids:
            continue
        days = math.ceil((kickoff - now).total_seconds() / 86400)
        if 1 <= days <= 60:
            cutoff = kickoff - timedelta(days=days)
            if cutoff + timedelta(minutes=10) <= now <= cutoff + timedelta(minutes=90):
                slots.add(f'issue/{identity}/{cutoff.isoformat()}')
    for event, value in pending:
        target = parse_timestamp(value)
        if target + timedelta(minutes=10) <= now <= target + timedelta(minutes=90):
            slots.add(f'target/{event}/{target.isoformat()}')
    return sorted(slots)


def tick(events, pending, state, now, training_ids, execute, persist):
    due = [key for key in windows(events, pending, now, training_ids)
           if key not in state.get('completed_slots', [])]
    result = {'checked_at': now.isoformat(), 'due_slots': due,
              'full_export_executed': False, 'production_change': False, 'live_adjustment': 0}
    if not due:
        return {**result, 'status': 'NO_NEW_LEGAL_SLOT_LOCAL_CHECK_ONLY'}
    counts = state.setdefault('slot_attempts', {})
    if any(type(n) is not int or not 0 <= n <= 3 for n in counts.values()):
        raise ValueError('Invalid durable slot attempt budget')
    if any(counts.get(key, 0) >= 3 for key in due):
        return {**result, 'status': 'SLOT_ATTEMPT_LIMIT_REQUIRES_REVIEW'}
    previous = state.get('last_attempt_at')
    if previous and now - parse_timestamp(previous) < timedelta(minutes=10):
        return {**result, 'status': 'RETRY_COOLDOWN_LOCAL_CHECK_ONLY'}
    for key in due:
        counts[key] = counts.get(key, 0) + 1
    state['last_attempt_at'] = now.isoformat(); persist(state)
    execution = execute()
    state['completed_slots'] = sorted(set(state.get('completed_slots', [])) | set(due)); persist(state)
    return {**result, 'status': 'UNCHANGED_DAILY_AND_DRIFT_CYCLES_VERIFIED',
            'full_export_executed': True, 'execution': execution}


def local_inputs(now):
    receipt = json.loads((ARCHIVE / 'latest-cycle.json').read_text())
    if receipt.get('status') != 'SOURCE_ARCHIVED_AND_RESTORED' or receipt.get('restore_verified') is not True:
        raise ValueError('Actual restored source archive required')
    path = Path(receipt['private_input_path'])
    if not path.resolve().is_relative_to(ARCHIVE.resolve()):
        raise ValueError('Wrong private archive path')
    source = validate_envelope(json.loads(path.read_text()))
    if (source['export_sha256'] != receipt['source_export_sha256']
            or not timedelta(0) <= now - parse_timestamp(source['completed_at']) <= timedelta(minutes=45)):
        raise ValueError('Stale or changed source archive')
    ledger = DAILY / 'shadow-v1.sqlite'
    with sqlite3.connect(ledger.resolve().as_uri() + '?mode=ro', uri=True) as connection:
        if connection.execute('select version from daily_path_meta where singleton=1').fetchone() != ('daily-inventory-path-local-ledger-v1',):
            raise ValueError('Wrong original daily ledger')
        pending = connection.execute('''select distinct a.ticket_event_id,p.target_at
            from daily_path_points p join daily_path_attempts a on a.id=p.attempt_id
            left join daily_path_scores s on s.point_id=p.id where s.point_id is null''').fetchall()
    model = json.loads((ROOT / 'ml/artifacts/daily_inventory_path_v1.json').read_text())
    return source['parts']['ticket_events'], pending, model['training_event_ids']


def execute_cycles():
    from ml.run_daily_inventory_path_cycle_v1 import run_cycle as daily_cycle
    from ml.run_daily_inventory_drift_v1 import run_cycle as drift_cycle
    from ml.daily_path_paired_comparison_v1 import compare
    from ml.daily_path_prefix_diagnostics_v1 import read_ledger
    daily = daily_cycle(DAILY, ROOT / 'ml/artifacts/daily_inventory_path_v1.json')
    if daily['status'] != 'CAPTURED_AND_SCORED':
        raise ValueError('Daily collection/backup failed closed')
    drift = drift_cycle(DAILY / 'shadow-v1.sqlite', DRIFT)
    d = read_ledger(DRIFT / 'drift-v1.sqlite'); p = read_ledger(DAILY / 'shadow-v1.sqlite')
    comparison = compare(*p, *d, datetime.now(timezone.utc).isoformat())
    return {'daily_finished_at': daily['finished_at'], 'daily_scores': daily['scores'],
            'daily_metrics': daily['evaluation'], 'drift_checked_at': drift['checked_at'],
            'drift_scores': drift['scores'], 'drift_missed_uncaptured': drift['missed_uncaptured'],
            'paired_report': comparison, 'backup_verified': True}


def source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True); parser.add_argument('--until', required=True)
    args = parser.parse_args(); now = datetime.now(timezone.utc); until = parse_timestamp(args.until)
    if not now < until <= now + timedelta(hours=24) or args.runtime.resolve().is_relative_to(ROOT):
        raise ValueError('Private runtime and explicit deadline within24hours required')
    args.runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    expected = {'version': 'daily-path-cutoff-window-runner-v1', 'source_hashes': source_hashes()}
    contract = args.runtime / 'source-contract.json'
    if contract.exists():
        if json.loads(contract.read_text()) != expected:
            raise ValueError('Window runner source changed')
    else:
        save(contract, expected)
    with (args.runtime / 'watcher.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        save(args.runtime / 'launch.json', {'pid': os.getpid(), 'started_at': now.isoformat(),
            'until': until.isoformat(), 'local_poll_seconds': 60, 'host_dependent': True,
            'production_change': False, 'live_adjustment': 0})
        state_path = args.runtime / 'state.json'; state = json.loads(state_path.read_text()) if state_path.exists() else {}
        while datetime.now(timezone.utc) < until:
            now = datetime.now(timezone.utc)
            try:
                if source_hashes() != expected['source_hashes']:
                    raise ValueError('Window runner/frozen source changed')
                events, pending, training = local_inputs(now)
                result = tick(events, pending, state, now, training, execute_cycles, lambda s: save(state_path, s))
            except Exception as exc:
                result = {'status': 'FAILED_CLOSED', 'checked_at': now.isoformat(),
                    'error_type': type(exc).__name__, 'production_change': False, 'live_adjustment': 0}
            save(args.runtime / 'latest-cycle.json', result)
            with (args.runtime / 'audit.jsonl').open('a') as file:
                file.write(json.dumps(result, sort_keys=True) + '\n')
            print(json.dumps({k: result[k] for k in ['status', 'checked_at', 'production_change']}), flush=True)
            time.sleep(min(60, max(0, (until - datetime.now(timezone.utc)).total_seconds())))


if __name__ == '__main__':
    main()
