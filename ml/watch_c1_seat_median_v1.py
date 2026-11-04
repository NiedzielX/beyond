"""Bounded median-lane inference/scoring and byte-exact private recovery."""
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
from ml.capture_c1_seat_median_v1 import load_models, ensure_runtime
from ml.demand_engine.c1_seat_median_runtime_v1 import PACKAGE
from ml.demand_engine.daily_inventory_path_storage_v1 import PrivateResearchStorage, encode, digest
from ml.watch_c1_training_expansion_v1 import validate_bounds


class MedianStorage(PrivateResearchStorage):
    @staticmethod
    def _key(key):
        if not re.fullmatch(r'c1-seat-median-v1/[0-9a-f]{64}\.json', key):
            raise ValueError('Median storage cannot access another experiment namespace')
        return urllib.parse.quote(key, safe='/')


def source_lock(runtime, hashes):
    path = runtime/'collection-contract.json'
    expected = {'package_version': PACKAGE, 'source_hashes': hashes}
    if path.exists():
        saved = json.loads(path.read_text())
        if any(saved[k] != v for k,v in expected.items()): raise ValueError('Frozen median collection/scoring source changed')
    else:
        with path.open('x') as file: json.dump({**expected, 'created_at': datetime.now(timezone.utc).isoformat()}, file, indent=2); file.write('\n')
        path.chmod(0o440)


def backup(runtime, artifact_dir, storage=None):
    manifest, _, _ = load_models(artifact_dir); ensure_runtime(runtime, manifest)
    files = (list(runtime.glob('experiment.json')) + list(runtime.glob('collection-contract.json'))
             + list(runtime.glob('attempt-*.json')) + list(runtime.glob('evidence/event-*.json'))
             + list(runtime.glob('inputs/input-*.json')) + list(runtime.glob('scores/event-*.json'))
             + list(runtime.glob('first-review.json')))
    if len(files) > 10000: raise ValueError('Bounded median backup source expanded')
    payload = encode({'version': 'c1-seat-median-private-evidence-v1', 'package_version': PACKAGE,
        'manifest': manifest, 'files': [{'name': str(p.relative_to(runtime)), 'sha256': digest(p.read_bytes()),
            'base64': base64.b64encode(p.read_bytes()).decode()} for p in sorted(files)],
        'production_change': False, 'live_adjustment': 0})
    raw = encode({'version': 'c1-seat-median-compressed-backup-v1', 'encoding': 'zlib+base64',
        'payload_sha256': digest(payload), 'payload': base64.b64encode(zlib.compress(payload)).decode()})
    storage = storage or MedianStorage(); storage.ensure_private_bucket()
    return storage.put_verified('c1-seat-median-v1/'+digest(raw)+'.json', raw, 'application/json')


def cycle(runtime, artifact_dir):
    manifest, _, _ = load_models(artifact_dir); ensure_runtime(runtime, manifest)
    names = ['ml/watch_c1_seat_median_v1.py', 'ml/score_c1_seat_median_v1.py']
    source_lock(runtime, {name: digest((ROOT/name).read_bytes()) for name in names})
    results = []
    for module in ['ml.capture_c1_seat_median_v1', 'ml.score_c1_seat_median_v1']:
        result = subprocess.run([sys.executable, '-m', module, '--runtime', str(runtime), '--artifact-dir', str(artifact_dir)],
            cwd=ROOT, capture_output=True, text=True, timeout=180)
        if result.returncode: raise ValueError('Median capture/scoring subprocess failed; no verified cycle claim')
        results.append(json.loads(result.stdout))
    capture, score = results
    receipt = backup(runtime, artifact_dir)
    return {'status': 'CYCLE_VERIFIED', 'checked_at': datetime.now(timezone.utc).isoformat(), 'capture': capture,
        'scored_events': score['scored_independent_events'], 'median_policy_mae': score['metrics']['seat_median_policy']['latest_row_mae'],
        'private_backup': receipt, 'host_dependent': True, 'production_change': False, 'live_adjustment': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True); p.add_argument('--artifact-dir', type=Path, required=True)
    p.add_argument('--until', required=True); p.add_argument('--interval', type=int, default=900)
    a = p.parse_args(); validate_bounds(a.until, a.interval, datetime.now(timezone.utc))
    manifest, _, _ = load_models(a.artifact_dir); ensure_runtime(a.runtime, manifest)
    with (a.runtime/'watcher.lock').open('a') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise ValueError('Median collector already holds the lifetime lock') from None
        (a.runtime/'watcher-launch.json').write_text(json.dumps({'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(),
            'until': a.until, 'interval_seconds': a.interval, 'host_dependent': True, 'production_change': False}, indent=2)+'\n')
        while pd.Timestamp.now(tz='UTC') < pd.Timestamp(a.until):
            try: result = cycle(a.runtime, a.artifact_dir)
            except Exception as exc:
                result = {'status': 'CYCLE_FAILED', 'checked_at': datetime.now(timezone.utc).isoformat(), 'error_type': type(exc).__name__}
            (a.runtime/'latest-cycle.json').write_text(json.dumps(result, indent=2)+'\n'); print(json.dumps(result), flush=True)
            time.sleep(max(0, min(a.interval, (pd.Timestamp(a.until)-pd.Timestamp.now(tz='UTC')).total_seconds())))
        print(json.dumps({'status': 'DEADLINE_REACHED', 'production_change': False}), flush=True)


if __name__ == '__main__': main()
