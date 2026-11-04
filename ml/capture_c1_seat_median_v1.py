"""Current-only paired inference for the separate direct-person median lane."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import joblib
import pandas as pd

from ml.c1_live_matched_audit_v1 import ROOT
from ml.c1_training_expansion_capture_v1 import load_frozen, validate_current, immutable_save
from ml.c1_training_expansion_v1 import EVENT_IDS, digest_json
from ml.collect_c1_training_expansion_v1 import enrich_anchor
from ml.demand_engine.c1_seat_median_runtime_v1 import PACKAGE, MODEL_ID, FEATURE_CONTRACT
from ml.demand_engine.run_c1_shadow_v8 import EXPECTED_PACKAGE, run_candidate, sha256_file
from ml.export_c1_matched_audit_inputs_v1 import Reader

PRECOMMIT = ROOT/'ml/C1_SEAT_MEDIAN_PRECOMMIT_V1.md'


def load_models(folder):
    receipt = json.loads((folder/'freeze_receipt.json').read_text())
    manifest = json.loads((folder/'manifest.json').read_text())
    if (receipt['package_version'] != PACKAGE or receipt['manifest_sha256'] != sha256_file(folder/'manifest.json')
            or manifest['package_version'] != PACKAGE or manifest['live_model_id'] != MODEL_ID
            or manifest.get('production_change') is not False or manifest.get('production_activation') is not False
            or manifest.get('live_adjustment') != 0 or manifest['precommit_sha256'] != sha256_file(PRECOMMIT)
            or manifest['training']['event_ids'] != list(EVENT_IDS) or manifest['training']['rows'] != 74
            or manifest['output']['units'] != 'persons' or manifest['output']['multiply_by_capacity'] is not False):
        raise ValueError('Median freeze identity/governance mismatch')
    for name, digest in {**manifest['old_frozen_hashes'], **manifest['source_code_sha256']}.items():
        if sha256_file(ROOT/name) != digest: raise ValueError('Frozen median source/dependency changed')
    path = folder/manifest['artifact']['filename']
    if sha256_file(path) != manifest['artifact']['sha256']: raise ValueError('Median estimator hash mismatch')
    baseline, original_manifest, ridge, original = load_frozen(ROOT/'ml/artifacts/c1_training_expansion_v1')
    median = joblib.load(path)
    if (manifest['baseline_manifest_sha256'] != baseline['_verified_manifest_sha256']
            or manifest['baseline_ridge_artifact_sha256'] != baseline['artifact']['sha256']
            or median.package_version != PACKAGE or median.live_model_id != MODEL_ID
            or median.feature_contract != FEATURE_CONTRACT or median.training_event_ids != EVENT_IDS
            or median.training_rows != 74 or tuple(median.features) != tuple(ridge.features)
            or median.policy_id != ridge.policy_id
            or joblib.hash(median.estimator.named_steps['prep']) != manifest['preprocessor_joblib_hash']
            or joblib.hash(ridge.estimator.named_steps['prep']) != manifest['preprocessor_joblib_hash']):
        raise ValueError('Frozen median representation/benchmark identity differs')
    params = median.estimator.named_steps['model'].get_params()
    if any(params[key] != value for key, value in {'quantile': .5, 'alpha': .1, 'solver': 'highs', 'fit_intercept': True}.items()):
        raise ValueError('Frozen median estimator parameters differ')
    manifest['_verified_manifest_sha256'] = receipt['manifest_sha256']
    models = {'seat_median': median, 'ridge20': ridge, 'original9': original}
    hashes = {'seat_median': manifest['artifact']['sha256'], 'ridge20': baseline['artifact']['sha256'],
              'original9': original_manifest['artifact']['sha256']}
    return manifest, models, hashes


def ensure_runtime(runtime, manifest):
    if runtime.resolve().is_relative_to(ROOT): raise ValueError('Private median evidence must remain outside Git')
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    marker = runtime/'experiment.json'
    expected = {'package_version': PACKAGE, 'manifest_sha256': manifest['_verified_manifest_sha256']}
    if marker.exists():
        if json.loads(marker.read_text()) != expected: raise ValueError('Another experiment owns this runtime')
    else:
        if any(runtime.iterdir()): raise ValueError('Refuse to open a nonempty unmarked/old-lane runtime')
        with marker.open('x') as file: json.dump(expected, file, sort_keys=True); file.write('\n')
        marker.chmod(0o440)


def capture(payload, manifest, models, hashes, *, runtime, labelled_ids, now):
    ensure_runtime(runtime, manifest)
    if (payload.get('version') != 'c1-shadow-v8-inputs-v1' or payload.get('package_version') != EXPECTED_PACKAGE
            or abs((pd.Timestamp(now)-pd.Timestamp(payload['requested_at'])).total_seconds()) > 900):
        raise ValueError('Require genuine current C1collector inputs')
    candidates = payload.get('candidates') or []
    if payload.get('candidate_count') != len(candidates) or len({c['ticket_event_id'] for c in candidates}) != len(candidates):
        raise ValueError('Collector cohort mismatch')
    results = []
    for c in candidates:
        try:
            latest = validate_current(c, payload['requested_at'], now, manifest['frozen_at'], labelled_ids)
            decisions = {name: run_candidate(c, model, hashes[name], pd.Timestamp(payload['requested_at']))
                         for name, model in models.items()}
            forecasts = {'prior': decisions['seat_median']['structural_prior_p50']}
            for name, decision in decisions.items():
                if (decision['structural_prior_p50'] != forecasts['prior']
                        or pd.Timestamp(decision['as_of_at']) != latest
                        or decision['source_snapshot_id'] != decisions['seat_median']['source_snapshot_id']):
                    raise ValueError('Paired experts do not share the same actual observation/anchor')
                forecasts[name+'_raw'] = decision['v2_live_p50']
                forecasts[name+'_policy'] = decision['policy_prediction']
            evidence = {'version': 'c1-seat-median-paired-evidence-v1', 'package_version': PACKAGE,
                'issued_at': pd.Timestamp(now).isoformat(), 'input_requested_at': payload['requested_at'],
                'ticket_event_id': c['ticket_event_id'], 'kickoff_at': c['kickoff_at'], 'as_of_at': latest.isoformat(),
                'source_snapshot_id': decisions['seat_median']['source_snapshot_id'], 'candidate_input_sha256': digest_json(c),
                'manifest_sha256': manifest['_verified_manifest_sha256'], 'precommit_sha256': manifest['precommit_sha256'],
                'model_hashes': hashes, 'frozen_at': manifest['frozen_at'], 'forecasts': forecasts, 'decisions': decisions,
                'known_outcome_at_capture': False, 'production_change': False, 'live_adjustment': 0}
            receipt = immutable_save(runtime/'evidence', evidence)
            results.append({'ticket_event_id': c['ticket_event_id'], **receipt})
        except (ValueError, KeyError, RuntimeError) as exc:
            results.append({'ticket_event_id': c['ticket_event_id'], 'status': 'FAILED_CLOSED', 'reason': str(exc)[:200]})
    return {'status': 'CURRENT_INPUTS_CHECKED', 'package_version': PACKAGE, 'issued_at': pd.Timestamp(now).isoformat(),
            'candidate_count': len(candidates), 'new_predictions': sum(r['status'] == 'CAPTURED_IMMUTABLE' for r in results),
            'events': results, 'production_change': False, 'live_adjustment': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True); p.add_argument('--artifact-dir', type=Path, required=True)
    a = p.parse_args(); manifest, models, hashes = load_models(a.artifact_dir); ensure_runtime(a.runtime, manifest)
    reader = Reader(); requested = datetime.now(timezone.utc).isoformat()
    original = reader.request('rpc/get_c1_shadow_v8_inputs_v1', {'p_requested_at': requested})
    payload = {**original, 'candidates': []}; failures, resolutions = [], []
    for c in original.get('candidates') or []:
        try:
            latest = max(pd.Timestamp(r['requested_as_of_at']) for r in c['representatives'])
            resolved = reader.request('rpc/get_structural_prior_v1', {'p_ticket_event_id': c['ticket_event_id'],
                                       'p_requested_as_of_at': latest.isoformat()})
            payload['candidates'].append(enrich_anchor(c, resolved))
            resolutions.append({'ticket_event_id': c['ticket_event_id'], 'prior': resolved})
        except (ValueError, KeyError):
            failures.append({'ticket_event_id': c['ticket_event_id'], 'status': 'FAILED_CLOSED', 'reason': 'EXACT_ANCHOR_RESOLUTION_FAILED'})
    payload['candidate_count'] = len(payload['candidates'])
    outcomes = reader.request('ticket_event_outcomes?select=ticket_event_id&limit=1001')
    if len(outcomes) >= 1000: raise ValueError('Unpaginated outcome source expanded')
    result = capture(payload, manifest, models, hashes, runtime=a.runtime,
                     labelled_ids={r['ticket_event_id'] for r in outcomes}, now=datetime.now(timezone.utc))
    result['events'].extend(failures); result['candidate_count'] += len(failures)
    if result['candidate_count'] != original['candidate_count']: raise ValueError('Enrichment dropped collector coverage')
    if original['candidate_count']:
        source = {'original': original, 'resolutions': resolutions, 'enriched': payload}
        directory = a.runtime/'inputs'; directory.mkdir(mode=0o700, exist_ok=True)
        path = directory/('input-'+digest_json(source)+'.json')
        if not path.exists():
            with path.open('x') as file: json.dump(source, file, indent=2, sort_keys=True, allow_nan=False); file.write('\n')
            path.chmod(0o440)
        result['private_input_file'] = str(path.relative_to(a.runtime))
    with (a.runtime/('attempt-'+requested.replace(':', '-')+'.json')).open('x') as file:
        json.dump(result, file, indent=2, allow_nan=False); file.write('\n')
    print(json.dumps(result))


if __name__ == '__main__': main()
