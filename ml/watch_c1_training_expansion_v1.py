"""Bounded host-dependent collector; inference and private backup, never training."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.parse
import zlib

import pandas as pd

from ml.c1_live_matched_audit_v1 import ROOT
from ml.c1_training_expansion_capture_v1 import load_frozen
from ml.demand_engine.daily_inventory_path_storage_v1 import PrivateResearchStorage, encode, digest


class ExpansionStorage(PrivateResearchStorage):
    @staticmethod
    def _key(key):
        if not re.fullmatch(r'c1-expansion-v1/[0-9a-f]{64}\.json', key):
            raise ValueError('Expansion backup cannot address another experiment namespace')
        return urllib.parse.quote(key, safe='/')


def validate_bounds(until, interval, now):
    duration = (pd.Timestamp(until)-pd.Timestamp(now)).total_seconds()
    if not 0 < duration <= 72*3600 or not 60 <= interval <= 900:
        raise ValueError('Require a future deadline within72hours and60–900second interval')


def lock_source_contract(runtime, hashes):
    path = runtime/'collection-contract.json'
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.exists():
        if json.loads(path.read_text())['source_hashes'] != hashes:
            raise ValueError('Frozen collection/scoring implementation changed; require a new version')
        return
    with path.open('x') as file:
        json.dump({'version': 'c1-training-expansion-collection-contract-v1',
                   'created_at': datetime.now(timezone.utc).isoformat(), 'source_hashes': hashes}, file, indent=2)
        file.write('\n')
    path.chmod(0o440)


def backup(runtime, artifact_dir, storage=None):
    load_frozen(artifact_dir)
    files = (sorted(runtime.glob('evidence/event-*.json')) + sorted(runtime.glob('attempt-*.json'))
             + sorted(runtime.glob('scores/event-*.json')) + sorted(runtime.glob('first-review.json'))
             + sorted(runtime.glob('inputs/input-*.json')) + sorted(runtime.glob('collection-contract.json')))
    if len(files) > 10000: raise ValueError('Bounded evidence source unexpectedly expanded')
    bundle = {'version': 'c1-training-expansion-private-evidence-v1',
              'manifest': json.loads((artifact_dir/'manifest.json').read_text()),
              'files': [{'name': str(p.relative_to(runtime)), 'sha256': digest(p.read_bytes()),
                         'base64': base64.b64encode(p.read_bytes()).decode()} for p in files],
              'production_change': False, 'live_adjustment': 0}
    raw = encode({'version': 'c1-training-expansion-compressed-backup-v1', 'encoding': 'zlib+base64',
                  'payload_sha256': digest(encode(bundle)),
                  'payload': base64.b64encode(zlib.compress(encode(bundle))).decode()})
    storage = storage or ExpansionStorage()
    storage.ensure_private_bucket()
    return storage.put_verified('c1-expansion-v1/'+digest(raw)+'.json', raw, 'application/json')


def cycle(runtime, artifact_dir):
    names = ['ml/watch_c1_training_expansion_v1.py', 'ml/collect_c1_training_expansion_v1.py',
             'ml/score_c1_training_expansion_v1.py']
    lock_source_contract(runtime, {name: digest((ROOT/name).read_bytes()) for name in names})
    result = subprocess.run([sys.executable, '-m', 'ml.collect_c1_training_expansion_v1',
        '--artifact-dir', str(artifact_dir), '--runtime', str(runtime)],
        cwd=ROOT, capture_output=True, text=True, timeout=180)
    if result.returncode: raise ValueError('Current capture subprocess failed; no successful cycle claim')
    capture = json.loads(result.stdout)
    scored = subprocess.run([sys.executable, '-m', 'ml.score_c1_training_expansion_v1',
        '--artifact-dir', str(artifact_dir), '--runtime', str(runtime)],
        cwd=ROOT, capture_output=True, text=True, timeout=180)
    if scored.returncode: raise ValueError('Confirmed-outcome scorer failed; no successful cycle claim')
    scorecard = json.loads(scored.stdout)
    receipt = backup(runtime, artifact_dir)
    return {'status': 'CYCLE_VERIFIED', 'checked_at': datetime.now(timezone.utc).isoformat(),
            'capture': capture, 'scored_events': scorecard['scored_independent_events'],
            'expanded_policy_mae': scorecard['metrics']['expanded_policy']['latest_row_mae'],
            'private_backup': receipt, 'host_dependent': True,
            'production_change': False, 'live_adjustment': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--artifact-dir', type=Path, required=True)
    p.add_argument('--until', required=True)
    p.add_argument('--interval', type=int, default=900)
    a = p.parse_args()
    if a.runtime.resolve().is_relative_to(ROOT): raise ValueError('Private runtime must be outside Git')
    validate_bounds(a.until, a.interval, datetime.now(timezone.utc))
    a.runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (a.runtime/'watcher.lock').open('a') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise ValueError('A collector already holds the lifetime lock') from None
        load_frozen(a.artifact_dir)
        launch = {'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(),
                  'until': a.until, 'interval_seconds': a.interval, 'host_dependent': True,
                  'production_change': False, 'live_adjustment': 0}
        (a.runtime/'watcher-launch.json').write_text(json.dumps(launch, indent=2)+'\n')
        while datetime.now(timezone.utc) < pd.Timestamp(a.until).to_pydatetime():
            try: result = cycle(a.runtime, a.artifact_dir)
            except Exception as exc:
                result = {'status': 'CYCLE_FAILED', 'checked_at': datetime.now(timezone.utc).isoformat(),
                          'error_type': type(exc).__name__, 'production_change': False}
            (a.runtime/'latest-cycle.json').write_text(json.dumps(result, indent=2)+'\n')
            print(json.dumps(result), flush=True)
            remaining = (pd.Timestamp(a.until)-pd.Timestamp.now(tz='UTC')).total_seconds()
            time.sleep(max(0, min(a.interval, remaining)))
        print(json.dumps({'status': 'DEADLINE_REACHED', 'production_change': False}), flush=True)


if __name__ == '__main__': main()
