"""Inference-only, current-cutoff paired capture into a separate private namespace."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

import joblib
import numpy as np
import pandas as pd

from ml.c1_live_matched_audit_v1 import ROOT
from ml.demand_engine.run_c1_shadow_v8 import EXPECTED_PACKAGE, run_candidate, sha256_file
from ml.c1_training_expansion_v1 import PACKAGE, MODEL_ID, PRECOMMIT, EVENT_IDS, digest_json
from ml.export_c1_matched_audit_inputs_v1 import Reader


def load_frozen(artifact_dir):
    receipt = json.loads((artifact_dir/'freeze_receipt.json').read_text())
    manifest_sha = sha256_file(artifact_dir/'manifest.json')
    if receipt.get('package_version') != PACKAGE or receipt.get('manifest_sha256') != manifest_sha:
        raise ValueError('Expansion freeze manifest hash mismatch')
    manifest = json.loads((artifact_dir/'manifest.json').read_text())
    if (manifest['package_version'] != PACKAGE or manifest['live_model_id'] != MODEL_ID
            or manifest.get('production_activation') is not False or manifest.get('production_change') is not False
            or manifest.get('live_adjustment') != 0 or manifest['training']['event_ids'] != list(EVENT_IDS)
            or manifest['precommit_sha256'] != sha256_file(PRECOMMIT)):
        raise ValueError('Expansion package/precommit governance mismatch')
    for name, digest in {**manifest['old_frozen_hashes'], **manifest['source_code_sha256']}.items():
        if sha256_file(ROOT/name) != digest:
            raise ValueError('Frozen source/dependency changed')
    path = artifact_dir/manifest['artifact']['filename']
    if sha256_file(path) != manifest['artifact']['sha256']:
        raise ValueError('Expansion estimator hash mismatch')
    runtime = joblib.load(path)
    old_manifest = json.loads((ROOT/'ml/artifacts/c1_shadow_v8/manifest.json').read_text())
    old_path = ROOT/'ml/artifacts/c1_shadow_v8'/old_manifest['artifact']['filename']
    old = joblib.load(old_path)
    if (runtime.package_version != PACKAGE or runtime.live_model_id != MODEL_ID
            or old.package_version != EXPECTED_PACKAGE or tuple(runtime.features) != tuple(old.features)
            or runtime.training_event_ids != EVENT_IDS or runtime.training_rows != 74
            or runtime.policy_id != old.policy_id):
        raise ValueError('Runtime identities differ from frozen protocol')
    manifest['_verified_manifest_sha256'] = manifest_sha
    return manifest, old_manifest, runtime, old


def validate_current(candidate, requested_at, now, frozen_at, labelled_ids):
    requested_at, now, frozen_at = map(pd.Timestamp, [requested_at, now, frozen_at])
    if abs((now-requested_at).total_seconds()) > 900 or now < frozen_at:
        raise ValueError('Collector timestamp is not current or artifact is not frozen yet')
    event_id = candidate['ticket_event_id']
    if event_id in EVENT_IDS or event_id in labelled_ids:
        raise ValueError('Training/known-outcome event cannot enter prospective evidence')
    kickoff = pd.Timestamp(candidate['kickoff_at'])
    if not now < kickoff <= now+pd.Timedelta(hours=24):
        raise ValueError('Event is outside the genuine current final24 window')
    prior = candidate['prior']
    capacity = float(prior['stadium_capacity'])
    if (not np.isfinite(capacity) or capacity <= 0 or not np.isfinite(float(prior['p50']))
            or not 0 <= float(prior['p50']) <= capacity or prior.get('horizon') != 'T-1'
            or prior.get('point_in_time_validated') is not True
            or pd.Timestamp(prior['target_as_of_at']) != kickoff-pd.Timedelta(hours=24)):
        raise ValueError('Invalid structural anchor')
    reps = candidate.get('representatives') or []
    if not 1 <= len(reps) <= 4:
        raise ValueError('Require one to four genuine final24 representatives')
    times, buckets, ids = [], [], []
    for r in reps:
        as_of = pd.Timestamp(r['requested_as_of_at']); f = r['features']
        bucket = int((kickoff-as_of).total_seconds()//21600)
        if (not kickoff-pd.Timedelta(hours=24) < as_of < kickoff or as_of > min(requested_at, now)
                or pd.Timestamp(prior['generated_at']) > as_of or pd.Timestamp(prior['target_as_of_at']) > as_of
                or pd.Timestamp(f['as_of_at']) != as_of or r['requested_snapshot_id'] != f['snapshot_id']
                or f.get('point_in_time_validated') is not True or r.get('bucket_6h') != bucket
                or bucket not in range(4) or (r.get('ticket_event_id', event_id) != event_id)):
            raise ValueError('Future, mismatched or invalid point-in-time representative')
        times.append(as_of); buckets.append(bucket); ids.append(r['requested_snapshot_id'])
    if len(set(buckets)) != len(reps) or len(set(ids)) != len(reps) or len(set(times)) != len(reps):
        raise ValueError('Duplicate representative/bucket identity')
    latest = max(times)
    if latest < frozen_at or now-latest > pd.Timedelta(hours=2):
        raise ValueError('Latest source is stale or predates freeze; no historical backfill')
    return latest


def immutable_save(directory, evidence):
    if directory.resolve().is_relative_to(ROOT):
        raise ValueError('Prospective evidence must remain private outside Git')
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    name = f"event-{evidence['ticket_event_id']}-snapshot-{evidence['source_snapshot_id']}.json"
    path = directory/name
    raw = (json.dumps(evidence, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    def existing():
        previous = json.loads(path.read_text())
        strip = lambda d: {k:v for k,v in d.items() if k not in ['issued_at', 'input_requested_at']}
        if strip(previous) != strip(evidence):
            raise ValueError('Immutable evidence conflict; never overwrite')
        return {'status': 'EXISTING_IDENTICAL', 'path': name, 'issued_at': previous['issued_at']}
    if path.exists(): return existing()
    fd, temp = tempfile.mkstemp(prefix='.capture-', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(raw); file.flush(); os.fsync(file.fileno())
        os.chmod(temp, 0o440)
        try: os.link(temp, path)
        except FileExistsError: return existing()
    finally:
        os.unlink(temp)
    return {'status': 'CAPTURED_IMMUTABLE', 'path': name, 'issued_at': evidence['issued_at']}


def capture(payload, manifest, old_manifest, runtime, old, *, now, labelled_ids, output_dir):
    if output_dir.resolve().is_relative_to(ROOT):
        raise ValueError('Prospective evidence must remain private outside Git')
    if payload.get('version') != 'c1-shadow-v8-inputs-v1' or payload.get('package_version') != EXPECTED_PACKAGE:
        raise ValueError('Unexpected current collector contract')
    candidates = payload.get('candidates') or []
    if payload.get('candidate_count') != len(candidates) or len({c['ticket_event_id'] for c in candidates}) != len(candidates):
        raise ValueError('Collector cohort accounting mismatch')
    if abs((pd.Timestamp(now)-pd.Timestamp(payload['requested_at'])).total_seconds()) > 900:
        raise ValueError('Collector timestamp is not current')
    records = []
    for c in candidates:
        try:
            latest = validate_current(c, payload['requested_at'], now, manifest['frozen_at'], labelled_ids)
            new = run_candidate(c, runtime, manifest['artifact']['sha256'], pd.Timestamp(payload['requested_at']))
            baseline = run_candidate(c, old, old_manifest['artifact']['sha256'], pd.Timestamp(payload['requested_at']))
            if any(not np.isfinite(float(r[key])) for r in [new, baseline]
                   for key in ['policy_prediction', 'v2_live_p50', 'structural_prior_p50']):
                raise ValueError('Nonfinite paired prediction')
            evidence = {'version': 'c1-training-expansion-paired-evidence-v1', 'package_version': PACKAGE,
                'issued_at': pd.Timestamp(now).isoformat(), 'input_requested_at': payload['requested_at'],
                'frozen_at': manifest['frozen_at'], 'precommit_sha256': manifest['precommit_sha256'],
                'manifest_sha256': manifest['_verified_manifest_sha256'],
                'artifact_sha256': manifest['artifact']['sha256'], 'baseline_artifact_sha256': old_manifest['artifact']['sha256'],
                'ticket_event_id': c['ticket_event_id'], 'kickoff_at': c['kickoff_at'],
                'as_of_at': latest.isoformat(), 'source_snapshot_id': new['source_snapshot_id'],
                'candidate_input_sha256': digest_json(c),
                'shared_prior': new['structural_prior_p50'], 'expanded_raw': new['v2_live_p50'],
                'expanded_policy': new['policy_prediction'], 'original_raw': baseline['v2_live_p50'],
                'original_policy': baseline['policy_prediction'],
                'expanded_decision': new, 'original_decision': baseline,
                'production_change': False, 'live_adjustment': 0, 'known_outcome_at_capture': False}
            receipt = immutable_save(output_dir, evidence)
            records.append({'ticket_event_id': c['ticket_event_id'], **receipt})
        except (ValueError, RuntimeError, KeyError) as exc:
            # Preserve cohort coverage failures separately; no invalid prediction emitted.
            records.append({'ticket_event_id': c['ticket_event_id'], 'status': 'FAILED_CLOSED',
                            'reason': str(exc)[:200]})
    result = {'status': 'CURRENT_INPUTS_CHECKED', 'candidate_count': len(candidates),
              'issued_at': pd.Timestamp(now).isoformat(), 'input_requested_at': payload['requested_at'],
              'new_predictions': sum(r['status'] == 'CAPTURED_IMMUTABLE' for r in records), 'events': records,
              'production_change': False, 'live_adjustment': 0}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args()
    manifest, old_manifest, runtime, old = load_frozen(a.artifact_dir)
    reader = Reader()
    requested = datetime.now(timezone.utc).isoformat()
    payload = reader.request('rpc/get_c1_shadow_v8_inputs_v1', {'p_requested_at': requested})
    labelled = reader.request('ticket_event_outcomes?select=ticket_event_id&limit=1001')
    if len(labelled) >= 1000: raise ValueError('Outcome source expanded beyond bounded source contract')
    result = capture(payload, manifest, old_manifest, runtime, old, now=datetime.now(timezone.utc),
                     labelled_ids={r['ticket_event_id'] for r in labelled}, output_dir=a.output_dir)
    # Save each operational attempt too, including no-candidate and coverage failure.
    a.output_dir.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (a.output_dir.parent/('attempt-'+requested.replace(':', '-')+'.json')).open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__': main()
