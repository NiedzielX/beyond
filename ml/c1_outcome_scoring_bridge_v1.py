"""Local outcome hint -> unchanged frozen scorers; no periodic source RPCs."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'c1-history-support-residual-v1-frozen-2026-11-05-n26'
SOURCES = ('ml/c1_outcome_scoring_bridge_v1.py', 'ml/score_c1_training_expansion_v1.py',
           'ml/score_c1_seat_median_v1.py', 'ml/watch_c1_training_expansion_v1.py',
           'ml/watch_c1_seat_median_v1.py')
LANES = (
    ('ridge20', 'ml.score_c1_training_expansion_v1', '2026-11-04-c1-training-expansion', 'c1_training_expansion_v1'),
    ('median20', 'ml.score_c1_seat_median_v1', '2026-11-04-c1-seat-median', 'c1_seat_median_v1'),
)


def save(path, value):
    temp = path.with_suffix('.tmp')
    with temp.open('w') as file:
        json.dump(value, file, indent=2, sort_keys=True, allow_nan=False)
        file.write('\n'); file.flush(); os.fsync(file.fileno())
    os.replace(temp, path)


def tick(report, state, now, execute, persist):
    if (report.get('package_version') != PACKAGE or report.get('production_change') is not False
            or type(report.get('live_adjustment')) is not int or report['live_adjustment'] != 0):
        raise ValueError('Unexpected real outcome hint contract')
    count = report.get('scored_events')
    if type(count) is not int or not 0 <= count <= 10000:
        raise ValueError('Invalid independent scored-event count')
    last = state.get('last_successful_count', 0)
    if type(last) is not int or not 0 <= last <= count:
        raise ValueError('Scoring frontier cannot reset or regress')
    base = {'checked_at': now.isoformat(), 'hint_scored_events': count,
            'production_change': False, 'live_adjustment': 0, 'source_rpc_polled': False}
    if count == last:
        return {**base, 'status': 'NO_NEW_GENUINE_SCORED_EVENT'}
    attempts = state.setdefault('attempts', {})
    if any(type(n) is not int or not 0 <= n <= 3 for n in attempts.values()):
        raise ValueError('Invalid durable attempt accounting')
    if attempts.get(str(count), 0) >= 3:
        return {**base, 'status': 'ATTEMPT_LIMIT_REQUIRES_REVIEW'}
    previous = state.get('last_attempt_at')
    if previous and now - datetime.fromisoformat(previous) < timedelta(minutes=10):
        return {**base, 'status': 'RETRY_COOLDOWN'}
    attempts[str(count)] = attempts.get(str(count), 0) + 1
    state['last_attempt_at'] = now.isoformat()
    persist(state)  # Intent survives a scorer, backup or process failure.
    results = execute()
    state['last_successful_count'] = count
    persist(state)
    return {**base, 'status': 'UNCHANGED_OLD_SCORERS_AND_RECOVERY_VERIFIED', 'lanes': results}


def run_scorers():
    from ml.watch_c1_training_expansion_v1 import backup as ridge_backup
    from ml.watch_c1_seat_median_v1 import backup as median_backup
    results = {}
    for name, module, folder, artifact in LANES:
        runtime = Path('/workspace/ops-runtime') / folder
        artifact_dir = ROOT / 'ml/artifacts' / artifact
        with (runtime / 'watcher.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError('Original capture worker is active; do not race its runtime') from None
            result = subprocess.run([sys.executable, '-m', module, '--runtime', str(runtime),
                '--artifact-dir', str(artifact_dir)], cwd=ROOT, capture_output=True, text=True, timeout=180)
            if result.returncode:
                raise ValueError('Frozen scorer failed closed; original evidence preserved')
            scorecard = json.loads(result.stdout)
            if scorecard.get('production_change') is not False or scorecard.get('live_adjustment') != 0:
                raise ValueError('Unexpected scorer production state')
            receipt = (ridge_backup if name == 'ridge20' else median_backup)(runtime, artifact_dir)
            if receipt.get('read_back_verified') is not True:
                raise ValueError('Frozen evidence recovery not verified')
            results[name] = {'scored_events': scorecard['scored_independent_events'], 'backup': receipt}
    return results


def source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--until', required=True)
    args = parser.parse_args()
    now = datetime.now(timezone.utc); until = datetime.fromisoformat(args.until.replace('Z', '+00:00'))
    if until.tzinfo is None or not now < until <= now + timedelta(hours=72):
        raise ValueError('Explicit bounded deadline within72hours required')
    if args.runtime.resolve().is_relative_to(ROOT) or args.report.resolve().is_relative_to(ROOT):
        raise ValueError('Private runtime/report required')
    args.runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    contract = {'version': 'c1-outcome-scoring-bridge-v1', 'source_hashes': source_hashes()}
    contract_path = args.runtime / 'source-contract.json'
    if contract_path.exists():
        if json.loads(contract_path.read_text()) != contract:
            raise ValueError('Bridge implementation changed')
    else:
        save(contract_path, contract)
    with (args.runtime / 'bridge.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        save(args.runtime / 'launch.json', {'pid': os.getpid(), 'started_at': now.isoformat(),
            'until': until.isoformat(), 'local_poll_seconds': 60, 'host_dependent': True,
            'production_change': False, 'live_adjustment': 0})
        state_path = args.runtime / 'state.json'
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        while datetime.now(timezone.utc) < until:
            checked = datetime.now(timezone.utc)
            try:
                if source_hashes() != contract['source_hashes']:
                    raise ValueError('Bridge source contract changed')
                age = checked.timestamp() - args.report.stat().st_mtime
                if not 0 <= age <= 30 * 60:
                    raise ValueError('Local genuine outcome report is stale')
                report = json.loads(args.report.read_text())
                result = tick(report, state, checked, run_scorers, lambda value: save(state_path, value))
            except Exception as exc:
                result = {'checked_at': checked.isoformat(), 'status': 'FAILED_CLOSED',
                    'error_type': type(exc).__name__, 'production_change': False, 'live_adjustment': 0}
            save(args.runtime / 'latest-cycle.json', result)
            with (args.runtime / 'audit.jsonl').open('a') as file:
                file.write(json.dumps(result, sort_keys=True) + '\n')
            print(json.dumps(result), flush=True)
            time.sleep(min(60, max(0, (until - datetime.now(timezone.utc)).total_seconds())))


if __name__ == '__main__':
    main()
