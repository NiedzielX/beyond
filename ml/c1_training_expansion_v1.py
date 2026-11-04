"""One intentional build-time fit on new labels; never called by inference."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge

from ml.c1_live_matched_audit_v1 import ROOT, check_training_features, frozen_hashes
from ml.c1_alpha_t1_tournament_v2 import COMPACT_NUMERIC, event_weights, fit_with_weights, pipeline
from ml.demand_engine.c1_shadow_runtime_v8 import C1ShadowRuntimeV8
from ml.demand_engine.run_c1_shadow_v8 import sha256_file

PACKAGE = 'c1-training-expansion-v1-frozen-2026-11-04-n20'
MODEL_ID = 'c1-training-expansion-ridge-directocc-compact-generic-a10-n20'
EVENT_IDS = (1, 3, 4, 5, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23)
CUTOFF = pd.Timestamp('2026-11-04T12:17:04.736622Z')
PRECOMMIT = ROOT/'ml/C1_TRAINING_EXPANSION_PRECOMMIT_V1.md'


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_training(frame, payload, outcomes, old_contract):
    ids = tuple(sorted(int(i) for i in frame.ticket_event_id.unique()))
    if ids != EVENT_IDS or len(frame) != 74 or frame.club_slug.nunique() != 11:
        raise ValueError('Fixed twenty-event/74-row/11-club training cohort changed')
    if tuple(COMPACT_NUMERIC) != tuple(old_contract['features']):
        raise ValueError('Original thirty-feature order changed')
    if frame.duplicated(['ticket_event_id', 'as_of_at']).any():
        raise ValueError('Duplicate training identity')
    truths = {r['ticket_event_id']: r for r in outcomes}
    events = {r['ticket_event_id']: r for r in payload['events']}
    rows = {(r['ticket_event_id'], pd.Timestamp(r['requested_as_of_at'])): r for r in payload['liveRows']}
    if len(rows) != 74:
        raise ValueError('Raw feature identities changed')
    for r in frame.itertuples():
        event, truth = events[r.ticket_event_id], truths[r.ticket_event_id]
        as_of, kickoff = pd.Timestamp(r.as_of_at), pd.Timestamp(event['kickoff_at'])
        source = rows[(r.ticket_event_id, as_of)]
        f = source['features']
        actual, capacity = float(r.actual_attendance), float(r.stadium_capacity)
        if (not np.isfinite(actual) or not np.isfinite(capacity) or actual <= 0 or capacity <= 0 or actual > capacity
                or truth['actual_attendance'] != actual or event['actual_attendance'] != actual
                or pd.Timestamp(truth['confirmed_at']) > CUTOFF
                or kickoff >= CUTOFF or not kickoff-pd.Timedelta(hours=24) < as_of < kickoff
                or r.prior_horizon != 'T-1' or f.get('point_in_time_validated') is not True
                or pd.Timestamp(f['as_of_at']) != as_of or f['snapshot_id'] != source['requested_snapshot_id']):
            raise ValueError('Training label, cutoff, capacity or feature identity is invalid')
    by_key = {(int(r.ticket_event_id), pd.Timestamp(r.as_of_at)): r for r in frame.itertuples()}
    for old in old_contract['rows']:
        r = by_key[(old['ticket_event_id'], pd.Timestamp(old['as_of_at']))]
        if r.actual_attendance != old['actual_attendance'] or r.stadium_capacity != old['stadium_capacity']:
            raise ValueError('Original training targets/capacities changed')


def fit_once(input_dir: Path, output_dir: Path, private_dir: Path):
    if output_dir.resolve() != ROOT/'ml/artifacts/c1_training_expansion_v1':
        raise ValueError('This version has one fixed freeze destination')
    if private_dir.resolve().is_relative_to(ROOT):
        raise ValueError('Raw training lineage must remain outside Git')
    # Refuse an existing destination BEFORE fitting: a new name cannot rerun v1.
    if output_dir.exists() or private_dir.exists():
        raise ValueError('Freeze destinations must be new; never refit/overwrite this version')
    known = json.loads((ROOT/'ml/artifacts/c1_live_matched_audit_v1/summary.json').read_text())['source_hashes']
    source_hashes = {}
    def read(name):
        path = input_dir/(name+'.json'); digest = sha256_file(path)
        if digest != known[path.name]:
            raise ValueError('Inputs differ from precommitted captured evidence')
        source_hashes[path.name] = digest
        return json.loads(path.read_text())
    events, attendance, sporting, aliases, live, outcomes, exported = [read(n) for n in
        ['events', 'attendance', 'sporting', 'aliases', 'final24', 'outcomes', 'export-manifest']]
    if pd.Timestamp(exported['retrieved_at']) != CUTOFF:
        raise ValueError('Training capture cutoff changed')
    before = frozen_hashes()
    old_manifest = json.loads((ROOT/'ml/artifacts/c1_shadow_v8/manifest.json').read_text())
    installed = {'numpy': np.__version__, 'pandas': pd.__version__, 'scikit_learn': sklearn.__version__, 'joblib': joblib.__version__}
    if any(installed[k] != old_manifest['libraries'][k] for k in installed):
        raise ValueError('Pinned original numerical environment differs')
    old_path = ROOT/'ml/artifacts/c1_shadow_v8'/old_manifest['artifact']['filename']
    if sha256_file(old_path) != old_manifest['artifact']['sha256']:
        raise ValueError('Original C1 artifact changed')
    old = joblib.load(old_path)
    contract = json.loads((ROOT/'ml/artifacts/c1_shadow_v8/training_contract_v1.json').read_text())
    # Compatibility is local to this research process; production modules unchanged.
    from ml.run_d2_live_replay_anchor_v1 import c1
    payload = {'events': events['events'], 'attendance': attendance['attendance'],
               'sportingMatches': sporting['sportingMatches'], 'aliases': aliases['aliases'], 'liveRows': live['liveRows']}
    priors = c1._event_prior_replay(payload, ROOT/'ml/artifacts/structural_prior_runtime_v1')
    frame = c1._training_frame(payload, priors)
    validate_training(frame, payload, outcomes, contract)
    frame['legacy_prior_p50'] = frame['prior_p50']
    cells = check_training_features(frame, payload, contract, old)
    if cells != 900 or before != frozen_hashes():
        raise ValueError('Original training or dependency hash changed')
    private_dir.mkdir(mode=0o700, parents=True)
    output_dir.mkdir(parents=True)
    # A durable marker prevents accidental repeat after a partially failed fit.
    (output_dir/'FIT_STARTED.json').write_text(json.dumps({'package_version': PACKAGE, 'at': datetime.now(timezone.utc).isoformat()})+'\n')
    features = list(old.features)
    estimator = pipeline(features, False, Ridge(alpha=10.0), scale=True)
    fitted = fit_with_weights(estimator, frame[features],
        (frame.actual_attendance/frame.stadium_capacity).to_numpy(), event_weights(frame))
    runtime = C1ShadowRuntimeV8(fitted, tuple(features), PACKAGE, EVENT_IDS, 74, live_model_id=MODEL_ID)
    artifact_path = output_dir/'c1_training_expansion_v1.joblib'
    joblib.dump(runtime, artifact_path, compress=3)
    loaded = joblib.load(artifact_path)
    predictions = loaded.predict_live_p50(frame)
    if len(predictions) != 74 or not np.isfinite(predictions).all():
        raise ValueError('Frozen load-back predictions invalid')
    # Never calculate or select by an in-sample error metric.
    private_rows = frame[['ticket_event_id', 'as_of_at', 'actual_attendance', *features]].copy()
    private_rows.to_csv(private_dir/'training.csv', index=False)
    priors.to_json(private_dir/'replayed-priors.json', orient='records', date_format='iso')
    manifest = {'package_version': PACKAGE, 'live_model_id': MODEL_ID,
        'status': 'EXPERIMENTAL_SHADOW', 'production_activation': False, 'production_change': False, 'live_adjustment': 0,
        'frozen_at': datetime.now(timezone.utc).isoformat(), 'training_cutoff': CUTOFF.isoformat(),
        'precommit_sha256': sha256_file(PRECOMMIT), 'precommit_published_commit': '79ab4b00a9bf795deed8b3e494e124d91ebb993d',
        'features': features, 'policy_id': old.policy_id, 'feature_contract': old.feature_contract,
        'training': {'event_ids': list(EVENT_IDS), 'event_count': 20, 'row_count': 74, 'club_count': 11,
                     'original_training_cells_verified': cells, 'target': 'direct_occupancy',
                     'equal_event_weights': True, 'all_events_exposed_training': True,
                     'private_frame_sha256': sha256_file(private_dir/'training.csv')},
        'model': {'family': 'Ridge', 'alpha': 10.0, 'club_aware': False, 'scaled': True, 'fit_count': 1},
        'artifact': {'filename': artifact_path.name, 'sha256': sha256_file(artifact_path)},
        'source_hashes': source_hashes, 'old_frozen_hashes': before,
        'source_code_sha256': {name: sha256_file(ROOT/name) for name in
            ['ml/c1_training_expansion_v1.py', 'ml/c1_training_expansion_capture_v1.py']},
        'libraries': {'numpy': np.__version__, 'pandas': pd.__version__, 'scikit_learn': sklearn.__version__, 'joblib': joblib.__version__},
        'attendance_accuracy_evidence': None, 'historical_publication_times_independently_verified': False,
        'scheduled_inference_must_not_fit': True}
    if before != frozen_hashes():
        raise ValueError('Old frozen dependencies changed')
    (output_dir/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: manifest[k] for k in ['package_version', 'frozen_at', 'artifact', 'attendance_accuracy_evidence']}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--private-dir', type=Path, required=True)
    a = p.parse_args(); fit_once(a.input_dir, a.output_dir, a.private_dir)


if __name__ == '__main__': main()
