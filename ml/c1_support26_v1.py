"""One precommitted support-only median fit and its separate future evidence stream."""
from __future__ import annotations

import argparse
import base64
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import io
import json
import os
from pathlib import Path
import re
import time
import zlib

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline

from ml.c1_alpha_t1_tournament_v2 import event_weights
from ml.c1_live_matched_audit_v1 import ROOT, frozen_hashes
from ml.capture_c1_seat_median_v1 import load_models as load_median20
from ml.c1_training_expansion_capture_v1 import validate_current, immutable_save
from ml.collect_c1_training_expansion_v1 import enrich_anchor
from ml.demand_engine.c1_seat_median_runtime_v1 import C1SeatMedianRuntimeV1, FEATURE_CONTRACT
from ml.demand_engine.current_structural_prior_features import DEFAULT_KEY_ALIASES
from ml.demand_engine.daily_inventory_path_storage_v1 import PrivateResearchStorage, encode, digest
from ml.demand_engine.run_c1_shadow_v8 import EXPECTED_PACKAGE, run_candidate, sha256_file
from ml.export_c1_matched_audit_inputs_v1 import Reader
from ml.prepare_c1_training_data26_v1 import BASE_IDS, NEW_IDS, fixture_units, validate_row
from ml.score_c1_training_expansion_v1 import persist_score
from ml.watch_c1_training_expansion_v1 import validate_bounds

PACKAGE = 'c1-live-seat-median-support26-v1-frozen-2026-11-05-n26'
MODEL_ID = 'c1-live-linear-seat-median-q50-a01-n26'
TRAIN_IDS = tuple(sorted(BASE_IDS+NEW_IDS))
PRECOMMIT = ROOT/'ml/C1_SUPPORT26_PRECOMMIT_V1.md'
ARTIFACT_DIR = ROOT/'ml/artifacts/c1_support26_v1'
MEDIAN20_MANIFEST = '8c59720f0f34f39e3590d35eb002d2050d05383b22d87676a4c680df388d4367'
MEDIAN20_ARTIFACT = '96e3b1a86eafd1922eb09f2f0493c054b7eac4e8e017b4b0a9c1e193cdf08c4a'
DATA_HASHES = {
    'training.csv': '0b8eb22c767d16e07b84b59eaa73aeff5ca55b11a220f4939dbb2ae2aaa9d778',
    'manifest.json': '426bcceedb871adf1044160c13cfc956e83008bb6f201f3e80c2c75519cc7ae4',
    'sources.json': '29f878368408f1852cbfe2fb25173461184a9fac83fc7cda371813fe9f0c822b',
    'canonical-fixtures.json': 'a02bb607a074d566e18247fe8d4be6010f3b518d2e4ed58c256948022ae509db',
    'final-validation-receipt.json': '63238c38aa64f47c5a15de32e2a82e7813b687872f6376d06fcdb1e783da953f',
}
BASE_CSV_SHA = 'be9aab4721e69661b8f14d3e1e8938abde569dabd6f7878e0986868fc0756549'
LABEL_CUTOFF = '2026-11-04T18:45:48.637107+00:00'
LIBRARIES = {'numpy': '2.3.5', 'pandas': '2.2.3', 'scikit_learn': '1.8.0', 'joblib': '1.5.3', 'scipy': '1.17.0'}
PARAMS = {'quantile': .5, 'alpha': .1, 'solver': 'highs', 'fit_intercept': True}
MODELS = ('median26', 'median20', 'ridge20', 'original9')
PREDICTIONS = tuple(name+'_'+kind for name in MODELS for kind in ('raw', 'policy'))+('prior',)
EVIDENCE_VERSION = 'c1-support26-paired-evidence-v1'


def stamp(value):
    result = pd.Timestamp(value)
    if pd.isna(result) or result.tzinfo is None:
        raise ValueError('Explicit timezone-aware timestamp required')
    return result


def write_json(path, payload, exclusive=False):
    with path.open('x' if exclusive else 'w') as file:
        json.dump(payload, file, indent=2, sort_keys=True, allow_nan=False); file.write('\n')
    if exclusive: path.chmod(0o440)


def reject_target_fields(value):
    if isinstance(value, dict):
        if any(str(k).lower() in {'actual_attendance', 'target_attendance', 'attendance_label', 'target_outcome'} for k in value):
            raise ValueError('Target attendance cannot enter prospective inference inputs')
        for child in value.values(): reject_target_fields(child)
    elif isinstance(value, list):
        for child in value: reject_target_fields(child)


def store_candidate(runtime, candidate):
    raw = encode(candidate); identity = digest(raw)
    folder = runtime/'inputs'; folder.mkdir(mode=0o700, exist_ok=True)
    path = folder/f'candidate-{identity}.json'
    if path.exists():
        if path.read_bytes() != raw: raise ValueError('Stored input checksum conflict')
    else:
        with path.open('xb') as file:
            file.write(raw); file.flush(); os.fsync(file.fileno())
        path.chmod(0o440)
    return identity


def benchmark_bundle():
    folder = ROOT/'ml/artifacts/c1_seat_median_v1'
    if sha256_file(folder/'manifest.json') != MEDIAN20_MANIFEST:
        raise ValueError('Declared median20 benchmark manifest changed')
    manifest, models, hashes = load_median20(folder)
    if hashes['seat_median'] != MEDIAN20_ARTIFACT:
        raise ValueError('Declared median20 estimator changed')
    return manifest, {'median20': models['seat_median'], 'ridge20': models['ridge20'], 'original9': models['original9']}, {
        'median20': hashes['seat_median'], 'ridge20': hashes['ridge20'], 'original9': hashes['original9']}


def dependency_hashes():
    names = ['ml/c1_support26_v1.py', 'ml/capture_c1_seat_median_v1.py', 'ml/freeze_c1_seat_median_v1.py',
        'ml/demand_engine/c1_seat_median_runtime_v1.py', 'ml/c1_training_expansion_capture_v1.py',
        'ml/collect_c1_training_expansion_v1.py', 'ml/prepare_c1_training_data26_v1.py',
        'ml/c1_alpha_t1_tournament_v2.py', 'ml/score_c1_training_expansion_v1.py',
        'ml/watch_c1_training_expansion_v1.py', 'ml/export_c1_matched_audit_inputs_v1.py',
        'ml/run_daily_inventory_path_v1.py', 'ml/demand_engine/daily_inventory_path_storage_v1.py',
        'ml/demand_engine/run_c1_shadow_v8.py', 'ml/demand_engine/current_structural_prior_features.py']
    files = {ROOT/name for name in names}
    for folder in ('c1_seat_median_v1', 'c1_training_expansion_v1'):
        files.update(p for p in (ROOT/'ml/artifacts'/folder).iterdir() if p.is_file())
    return {**frozen_hashes(), **{str(p.relative_to(ROOT)): sha256_file(p) for p in sorted(files)}}


def numerical_environment():
    return {'numpy': np.__version__, 'pandas': pd.__version__, 'scikit_learn': sklearn.__version__,
            'joblib': joblib.__version__, 'scipy': scipy.__version__}


def validate_training_frame(frame, features, fixtures, metadata):
    if (len(frame) != 80 or tuple(sorted(frame.ticket_event_id.unique())) != TRAIN_IDS
            or frame.duplicated(['ticket_event_id', 'as_of_at']).any()
            or list(frame.columns) != ['ticket_event_id', 'as_of_at', 'actual_attendance', *features]
            or len(features) != 30 or list(metadata['features']) != list(features)
            or metadata.get('all_events_training_exposed') is not True or metadata.get('fresh_validation_events') != 0
            or metadata.get('label_knowledge_cutoff') != LABEL_CUTOFF
            or metadata.get('base_prefix_byte_identical') is not True):
        raise ValueError('Exact exposed support/schema/data contract changed')
    units = fixture_units(fixtures)
    if units != {'independent_fixtures': 26, 'training_clubs': 12}:
        raise ValueError('Canonical training fixtures/clubs changed')
    by_id = {r['id']: r for r in fixtures}
    counts = frame.groupby('ticket_event_id').size()
    if sum(counts.loc[list(BASE_IDS)]) != 74 or any(counts.loc[list(NEW_IDS)] != 1):
        raise ValueError('Declared base-prefix/new-row sampling changed')
    y, cap = frame.actual_attendance.to_numpy(float), frame.stadium_capacity.to_numpy(float)
    if (not np.isfinite(y).all() or not np.isfinite(cap).all() or (cap <= 0).any()
            or (y <= 0).any() or (y > cap).any() or np.isinf(frame[list(features)].to_numpy(float)).any()):
        raise ValueError('Invalid training target/capacity/features')
    for row in frame.itertuples():
        source = stamp(row.as_of_at); kickoff = stamp(by_id[row.ticket_event_id]['kickoff_at'])
        if not kickoff-pd.Timedelta(hours=24) < source < kickoff < stamp(LABEL_CUTOFF):
            raise ValueError('Training source is outside its actual pre-kickoff window')
    return units


def read_training(folder, benchmark_models):
    if folder.resolve().is_relative_to(ROOT):
        raise ValueError('Training data must remain private outside Git')
    for name, expected in DATA_HASHES.items():
        if sha256_file(folder/name) != expected:
            raise ValueError('Immutable training data/lineage checksum changed')
    raw = (folder/'training.csv').read_bytes()
    if digest(raw[:18554]) != BASE_CSV_SHA:
        raise ValueError('Original74row CSV prefix changed')
    metadata = json.loads((folder/'manifest.json').read_text())
    frame = pd.read_csv(io.BytesIO(raw))  # Same parser as frozen median20.
    features = tuple(benchmark_models['median20'].features)
    units = validate_training_frame(frame, features, json.loads((folder/'canonical-fixtures.json').read_text()), metadata)
    sources = json.loads((folder/'sources.json').read_text())
    if len(sources) != 6 or sorted(r['event']['ticket_event_id'] for r in sources) != list(NEW_IDS):
        raise ValueError('Six exact newly confirmed source identities required')
    for src in sources:
        row, _ = validate_row(src['event'], src['truth'], src['prior'], src['feature'], src['snapshot'],
                              LABEL_CUTOFF, benchmark_models['original9'])
        stored = frame[frame.ticket_event_id == row['ticket_event_id']].iloc[0]
        if stamp(stored.as_of_at) != stamp(row['as_of_at']) or stored.actual_attendance != row['actual_attendance']:
            raise ValueError('Added row differs from its actual forecast/label source')
        if not np.allclose(stored[list(features)].to_numpy(float), np.asarray([row[n] for n in features], dtype=float),
                           rtol=0, atol=1e-7, equal_nan=True):
            raise ValueError('Added features differ from the verified reconstruction')
    return frame, features, units


def fit_once(data_dir, output=ARTIFACT_DIR):
    if output.resolve() != ARTIFACT_DIR or output.exists():
        raise ValueError('Require the single fresh canonical support26 artifact directory')
    installed = numerical_environment()
    if installed != LIBRARIES:
        raise ValueError('Pinned numerical environment differs')
    baseline, benchmarks, hashes = benchmark_bundle()
    frame, features, units = read_training(data_dir, benchmarks)
    before = dependency_hashes()
    prep = deepcopy(benchmarks['median20'].estimator.named_steps['prep'])
    prep_hash = joblib.hash(prep)
    if prep_hash != baseline['preprocessor_joblib_hash']:
        raise ValueError('Frozen preprocessing identity differs')
    transformed = prep.transform(frame[list(features)])
    output.mkdir(parents=True)
    write_json(output/'FIT_STARTED.json', {'package_version': PACKAGE, 'started_at': datetime.now(timezone.utc).isoformat()}, True)
    learner = QuantileRegressor(**PARAMS)
    learner.fit(transformed, frame.actual_attendance.to_numpy(float), sample_weight=event_weights(frame))
    if joblib.hash(prep) != prep_hash or before != dependency_hashes():
        raise ValueError('A frozen source/representation changed during fitting')
    runtime = C1SeatMedianRuntimeV1(Pipeline([('prep', prep), ('model', learner)]), features, TRAIN_IDS, 80,
                                   package_version=PACKAGE, live_model_id=MODEL_ID)
    path = output/'c1_support26_v1.joblib'; joblib.dump(runtime, path, compress=3)
    loaded = joblib.load(path); checked = loaded.predict_live_p50(frame[list(features)])
    if checked.shape != (80,) or not np.isfinite(checked).all():
        raise ValueError('Support26 finite load-back failed')
    manifest = {'package_version': PACKAGE, 'live_model_id': MODEL_ID, 'feature_contract': FEATURE_CONTRACT,
        'status': 'EXPERIMENTAL_SHADOW', 'production_change': False, 'production_activation': False, 'live_adjustment': 0,
        'frozen_at': datetime.now(timezone.utc).isoformat(), 'training_cutoff': LABEL_CUTOFF,
        'precommit_sha256': sha256_file(PRECOMMIT), 'source_data_hashes': DATA_HASHES,
        'benchmark_manifest_sha256': MEDIAN20_MANIFEST, 'benchmark_artifacts': hashes,
        'benchmark_packages': {name: model.package_version for name, model in benchmarks.items()},
        'training': {'event_ids': list(TRAIN_IDS), 'events': 26, 'rows': 80, 'clubs': units['training_clubs'],
            'all_training_exposed': True, 'target': 'direct_attendance_persons', 'equal_event_weights': True},
        'features': list(features), 'preprocessor_joblib_hash': prep_hash, 'preprocessor_reused_without_fit': True,
        'estimator': {'family': 'QuantileRegressor', **PARAMS, 'fit_count': 1,
            'nonzero_coefficients': int(np.count_nonzero(learner.coef_))},
        'output': {'units': 'persons', 'multiply_by_capacity': False, 'clipping': '[0,stadium_capacity]'},
        'artifact': {'filename': path.name, 'sha256': sha256_file(path)}, 'dependency_sha256': before,
        'libraries': installed, 'attendance_mae': None, 'training_mae_computed': False,
        'prospective_validation_required': True}
    write_json(output/'manifest.json', manifest, True)
    write_json(output/'freeze_receipt.json', {'package_version': PACKAGE,
        'manifest_sha256': sha256_file(output/'manifest.json')}, True)
    return manifest


def load_models(folder=ARTIFACT_DIR):
    receipt = json.loads((folder/'freeze_receipt.json').read_text())
    m = json.loads((folder/'manifest.json').read_text())
    if (receipt['package_version'] != PACKAGE or receipt['manifest_sha256'] != sha256_file(folder/'manifest.json')
            or m['package_version'] != PACKAGE or m['live_model_id'] != MODEL_ID
            or m['precommit_sha256'] != sha256_file(PRECOMMIT) or m['source_data_hashes'] != DATA_HASHES
            or m['training']['event_ids'] != list(TRAIN_IDS) or m['training']['rows'] != 80
            or m['training']['events'] != 26 or m['training']['clubs'] != 12
            or m['training']['all_training_exposed'] is not True or m['training_cutoff'] != LABEL_CUTOFF
            or m['output']['multiply_by_capacity'] is not False or m['output']['units'] != 'persons'
            or m['output']['clipping'] != '[0,stadium_capacity]' or m['preprocessor_reused_without_fit'] is not True
            or m['libraries'] != LIBRARIES or numerical_environment() != LIBRARIES
            or m['estimator']['family'] != 'QuantileRegressor' or m['estimator']['fit_count'] != 1
            or any(m['estimator'][key] != value for key, value in PARAMS.items())
            or m.get('production_change') is not False or m.get('production_activation') is not False
            or m.get('live_adjustment') != 0 or m['dependency_sha256'] != dependency_hashes()):
        raise ValueError('Frozen support26 identity/data/source/governance changed')
    baseline, models, hashes = benchmark_bundle()
    if (m['benchmark_artifacts'] != hashes or m['benchmark_manifest_sha256'] != MEDIAN20_MANIFEST
            or m['benchmark_packages'] != {name: model.package_version for name, model in models.items()}):
        raise ValueError('Frozen paired benchmark changed')
    path = folder/m['artifact']['filename']
    if m['artifact']['filename'] != 'c1_support26_v1.joblib' or sha256_file(path) != m['artifact']['sha256']:
        raise ValueError('Frozen support26 estimator checksum changed')
    model = joblib.load(path)
    if (model.package_version != PACKAGE or model.live_model_id != MODEL_ID
            or model.feature_contract != FEATURE_CONTRACT or model.policy_id != models['median20'].policy_id
            or model.training_event_ids != TRAIN_IDS or model.training_rows != 80
            or tuple(model.features) != tuple(models['median20'].features) or list(model.features) != m['features']
            or joblib.hash(model.estimator.named_steps['prep']) != baseline['preprocessor_joblib_hash']
            or m['preprocessor_joblib_hash'] != baseline['preprocessor_joblib_hash']
            or any(model.estimator.named_steps['model'].get_params()[key] != value for key, value in PARAMS.items())):
        raise ValueError('Frozen learner/preprocessor/runtime differs from the declared support-only comparison')
    m['_verified_manifest_sha256'] = receipt['manifest_sha256']
    return m, {'median26': model, **models}, {'median26': m['artifact']['sha256'], **hashes}


def ensure_runtime(runtime, manifest):
    if runtime.resolve().is_relative_to(ROOT):
        raise ValueError('Private support26 evidence must remain outside Git')
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = runtime/'experiment.json'
    expected = {'package_version': PACKAGE, 'manifest_sha256': manifest['_verified_manifest_sha256']}
    if path.exists():
        if json.loads(path.read_text()) != expected:
            raise ValueError('Another model/version owns this runtime')
    else:
        if any(runtime.iterdir()):
            raise ValueError('Refuse a nonempty unmarked or old-lane runtime')
        write_json(path, expected, True); path.chmod(0o440)


def validate_payload(payload, now):
    requested = stamp(payload['requested_at'])
    if (payload.get('version') != 'c1-shadow-v8-inputs-v1' or payload.get('package_version') != EXPECTED_PACKAGE
            or abs((stamp(now)-requested).total_seconds()) > 900):
        raise ValueError('Require the exact current input contract')
    candidates = payload.get('candidates') or []
    if (not isinstance(candidates, list) or len(candidates) > 100
            or isinstance(payload.get('candidate_count'), bool) or payload.get('candidate_count') != len(candidates)
            or len({r['ticket_event_id'] for r in candidates}) != len(candidates)):
        raise ValueError('Current collector coverage accounting differs')
    return requested, candidates


def capture(payload, manifest, models, hashes, *, runtime, labelled_ids, now, clock=None):
    ensure_runtime(runtime, manifest)
    now = stamp(now); requested, candidates = validate_payload(payload, now)
    if set(models) != set(MODELS) or set(hashes) != set(MODELS):
        raise ValueError('Require the exact current input and four-expert contract')
    results = []
    for candidate in candidates:
        event = candidate['ticket_event_id']
        try:
            reject_target_fields(candidate)
            if isinstance(event, bool) or not isinstance(event, int) or event <= 0 or event in TRAIN_IDS:
                raise ValueError('All26training events are excluded from prospective evaluation')
            for value in [candidate['kickoff_at'], candidate['prior']['generated_at'], candidate['prior']['target_as_of_at']]:
                stamp(value)
            for rep in candidate.get('representatives') or []:
                stamp(rep['requested_as_of_at']); stamp(rep['features']['as_of_at'])
                snapshot = rep['requested_snapshot_id']
                if isinstance(snapshot, bool) or not isinstance(snapshot, int) or snapshot <= 0:
                    raise ValueError('Invalid genuine source snapshot identity')
            latest = validate_current(candidate, requested, now, manifest['frozen_at'], labelled_ids)
            input_sha = store_candidate(runtime, candidate)  # Durable input precedes its immutable forecast.
            decisions = {name: run_candidate(candidate, models[name], hashes[name], requested) for name in MODELS}
            prior = decisions['median26']['structural_prior_p50']; anchor = decisions['median26']['source_snapshot_id']
            forecasts = {'prior': prior}
            for name, decision in decisions.items():
                if (decision['structural_prior_p50'] != prior or stamp(decision['as_of_at']) != latest
                        or decision['source_snapshot_id'] != anchor
                        or decision['artifact_sha256'] != hashes[name]):
                    raise ValueError('Paired experts do not share the same actual source/anchor')
                forecasts[name+'_raw'] = decision['v2_live_p50']; forecasts[name+'_policy'] = decision['policy_prediction']
            issued = stamp(clock()) if clock is not None else now
            validate_current(candidate, requested, issued, manifest['frozen_at'], labelled_ids)
            evidence = {'version': EVIDENCE_VERSION, 'package_version': PACKAGE, 'issued_at': issued.isoformat(),
                'input_requested_at': payload['requested_at'], 'ticket_event_id': event, 'kickoff_at': candidate['kickoff_at'],
                'as_of_at': latest.isoformat(), 'source_snapshot_id': anchor, 'candidate_input_sha256': input_sha,
                'manifest_sha256': manifest['_verified_manifest_sha256'], 'precommit_sha256': manifest['precommit_sha256'],
                'model_hashes': hashes, 'frozen_at': manifest['frozen_at'], 'forecasts': forecasts, 'decisions': decisions,
                'known_outcome_at_capture': False, 'production_change': False, 'live_adjustment': 0}
            results.append({'ticket_event_id': event, **immutable_save(runtime/'evidence', evidence)})
        except (ValueError, KeyError, RuntimeError, TypeError) as exc:
            results.append({'ticket_event_id': event, 'status': 'FAILED_CLOSED', 'reason': str(exc)[:200]})
    return {'status': 'CURRENT_INPUTS_CHECKED', 'package_version': PACKAGE, 'issued_at': now.isoformat(),
        'candidate_count': len(candidates), 'new_predictions': sum(r['status'] == 'CAPTURED_IMMUTABLE' for r in results),
        'events': results, 'production_change': False, 'live_adjustment': 0}


def score_rows(evidence, outcomes, metadata, manifest, hashes, now, *, models, source_inputs):
    now = stamp(now)
    truth = {r['ticket_event_id']: r for r in outcomes}; catalog = {r['id']: r for r in metadata}
    if len(truth) != len(outcomes) or len(catalog) != len(metadata):
        raise ValueError('Duplicate canonical label/fixture identity')
    scores, missing, identities, fixture_ids = [], set(), set(), {}
    packages = {'median26': PACKAGE, **manifest['benchmark_packages']}
    for row in evidence:
        event = row['ticket_event_id']; as_of, issued, kickoff = map(stamp, [row['as_of_at'], row['issued_at'], row['kickoff_at']])
        identity = (event, as_of)
        if identity in identities: raise ValueError('Duplicate captured source/event identity')
        identities.add(identity)
        if (row.get('version') != EVIDENCE_VERSION or row.get('package_version') != PACKAGE
                or row.get('manifest_sha256') != manifest['_verified_manifest_sha256']
                or row.get('precommit_sha256') != manifest['precommit_sha256'] or row.get('model_hashes') != hashes
                or row.get('frozen_at') != manifest['frozen_at'] or row.get('known_outcome_at_capture') is not False
                or row.get('production_change') is not False or row.get('live_adjustment') != 0
                or isinstance(event, bool) or not isinstance(event, int) or event <= 0 or event in TRAIN_IDS
                or not stamp(manifest['frozen_at']) <= as_of <= issued < kickoff or issued > now
                or issued-as_of > pd.Timedelta(hours=2) or set(row['decisions']) != set(MODELS)
                or set(row['forecasts']) != set(PREDICTIONS)):
            raise ValueError('Invalid frozen/prospective evidence identity or timing')
        source = source_inputs.get(row['candidate_input_sha256'])
        if source is None or digest(encode(source)) != row['candidate_input_sha256'] or source['ticket_event_id'] != event:
            raise ValueError('Missing or changed immutable source input')
        reject_target_fields(source)
        latest = validate_current(source, row['input_requested_at'], issued, manifest['frozen_at'], set())
        if latest != as_of or stamp(source['kickoff_at']) != kickoff:
            raise ValueError('Stored source cutoff/kickoff differs')
        expected = {name: run_candidate(source, models[name], hashes[name], stamp(row['input_requested_at'])) for name in MODELS}
        if digest(encode(expected)) != digest(encode(row['decisions'])):
            raise ValueError('Stored decisions do not reproduce from the exact frozen models and original input')
        forecasts = row['forecasts']; capacity = float(expected['median26']['stadium_capacity'])
        for name in MODELS:
            decision = row['decisions'][name]
            if (decision['package_version'] != packages[name] or decision['artifact_sha256'] != hashes[name]
                    or stamp(decision['as_of_at']) != as_of or decision['source_snapshot_id'] != row['source_snapshot_id']
                    or float(decision['stadium_capacity']) != capacity or decision['structural_prior_p50'] != forecasts['prior']
                    or decision['v2_live_p50'] != forecasts[name+'_raw'] or decision['policy_prediction'] != forecasts[name+'_policy']):
                raise ValueError('Paired decision fields differ')
        if (not np.isfinite(capacity) or capacity <= 0 or any(isinstance(v, bool) or not np.isfinite(float(v))
                or not 0 <= float(v) <= capacity for v in forecasts.values())):
            raise ValueError('Invalid paired forecast/capacity')
        meta = catalog[event]
        if not meta.get('club_slug') or stamp(meta['kickoff_at']) != kickoff:
            raise ValueError('Canonical club/kickoff changed or missing')
        club = DEFAULT_KEY_ALIASES.get(meta['club_slug'], meta['club_slug'])
        fixture = (club, kickoff.tz_convert('Europe/Warsaw').date())
        if fixture in fixture_ids and fixture_ids[fixture] != event:
            raise ValueError('Different ticket IDs refer to one independent fixture')
        fixture_ids[fixture] = event
        label = truth.get(event)
        if label is None: missing.add(event); continue
        actual, confirmed = float(label['actual_attendance']), stamp(label['confirmed_at'])
        if (isinstance(label['actual_attendance'], bool) or not np.isfinite(actual) or not 0 < actual <= capacity
                or not issued < confirmed <= now or confirmed < kickoff
                or not label.get('source_name') or not str(label.get('source_url', '')).startswith('https://')):
            raise ValueError('Invalid, already known or future attendance outcome/provenance')
        scores.append({'ticket_event_id': event, 'source_snapshot_id': row['source_snapshot_id'], 'as_of_at': row['as_of_at'],
            'issued_at': row['issued_at'], 'kickoff_at': row['kickoff_at'], 'club_slug': club,
            'capture_sha256': digest(encode(row)), 'actual_attendance': actual, 'confirmed_at': label['confirmed_at'],
            'source_name': label['source_name'], 'source_url': label['source_url'], 'forecasts': forecasts,
            'absolute_errors': {k: abs(float(v)-actual) for k, v in forecasts.items()},
            'signed_errors': {k: float(v)-actual for k, v in forecasts.items()}})
    return scores, sorted(missing), len({r['ticket_event_id'] for r in evidence})


def summary(scores, missing, captured_events):
    by_event = {}
    for row in scores: by_event.setdefault(row['ticket_event_id'], []).append(row)
    latest = sorted([max(rows, key=lambda r: stamp(r['as_of_at'])) for rows in by_event.values()], key=lambda r: r['ticket_event_id'])
    clubs = sorted({r['club_slug'] for r in latest}); ready = len(latest) >= 30 and len(clubs) >= 8
    mean = lambda values: float(np.mean(values)) if len(values) else None
    metrics = {}
    for name in PREDICTIONS:
        errors = [r['absolute_errors'][name] for r in latest]
        metrics[name] = {'latest_row_mae': mean(errors),
            'event_balanced_window_mae': mean([mean([r['absolute_errors'][name] for r in rows]) for rows in by_event.values()]),
            'signed_bias': mean([r['signed_errors'][name] for r in latest]),
            'p90_absolute_error': float(np.quantile(errors, .9)) if errors else None,
            'worst_absolute_error': max(errors) if errors else None}
    def pair(candidate, benchmark):
        delta = np.asarray([r['absolute_errors'][candidate]-r['absolute_errors'][benchmark] for r in latest])
        ci = None
        if ready:
            rng = np.random.default_rng(42)
            draws = np.concatenate([rng.choice(delta, size=(250, len(delta)), replace=True).mean(axis=1) for _ in range(40)])
            ci = [float(v) for v in np.quantile(draws, [.025, .975])]
        avg = mean(delta)
        return {'candidate': candidate, 'benchmark': benchmark, 'paired_delta_mae': avg,
            'median_event_delta_ae': float(np.median(delta)) if len(delta) else None,
            'event_improvement_rate': mean((delta < 0).astype(float)),
            'worst_event_degradation': max(0., float(delta.max())) if len(delta) else None,
            'paired_event_bootstrap_95_interval': ci, 'evidence_gate_met': bool(ready and avg < 0 and ci[1] < 0)}
    support = pair('median26_raw', 'median20_raw')
    product = {name: pair('median26_policy', name) for name in ['median20_policy', 'ridge20_policy', 'original9_policy', 'prior']}
    def grouped(items, key):
        groups = {}
        for row in items: groups.setdefault(key(row), {}).setdefault(row['ticket_event_id'], []).append(row)
        return {label: {'independent_events': len(events), 'event_balanced_mae': {
            name: mean([mean([r['absolute_errors'][name] for r in rows]) for rows in events.values()]) for name in PREDICTIONS}}
            for label, events in sorted(groups.items())}
    def horizon(row):
        hours = (stamp(row['kickoff_at'])-stamp(row['as_of_at'])).total_seconds()/3600
        return '0_to_1_hours' if hours <= 1 else '1_to_6_hours' if hours <= 6 else '6_to_24_hours'
    return {'version': 'c1-support26-scorecard-v1', 'package_version': PACKAGE,
        'captured_independent_events': captured_events, 'scored_independent_events': len(latest), 'scored_rows': len(scores),
        'clubs': clubs, 'missing_outcome_event_ids': missing, 'metrics': metrics,
        'first_review_ready': ready, 'support_comparison': support, 'governed_comparisons': product,
        'support_gate_met': support['evidence_gate_met'],
        'product_gate_met': bool(ready and all(v['evidence_gate_met'] for v in product.values())),
        'by_club_latest_descriptive': grouped(latest, lambda r: r['club_slug']),
        'by_horizon_window_descriptive': grouped(scores, horizon), 'early_scores_descriptive_only': not ready,
        'production_change': False, 'production_activation_allowed': False, 'live_adjustment': 0}


class SupportStorage(PrivateResearchStorage):
    @staticmethod
    def _key(key):
        if not re.fullmatch(r'c1-support26-v1/[0-9a-f]{64}\.json', key):
            raise ValueError('Support26 cannot access another recovery namespace')
        return key


def encode_bundle(runtime, artifact_dir, training_dir=None):
    manifest = json.loads((artifact_dir/'manifest.json').read_text())
    marker = json.loads((runtime/'experiment.json').read_text())
    if (manifest.get('package_version') != PACKAGE or marker != {'package_version': PACKAGE,
            'manifest_sha256': sha256_file(artifact_dir/'manifest.json')}):
        raise ValueError('Backup requires the matching support26 artifact/runtime identity')
    files = [p for pattern in ['experiment.json', 'attempt-*.json', 'evidence/event-*.json',
        'inputs/*.json', 'scores/event-*.json', 'first-review.json'] for p in runtime.glob(pattern)]
    files += list(artifact_dir.glob('*'))
    if len(files) > 10000 or any(not p.is_file() or p.is_symlink() for p in files):
        raise ValueError('Unexpected evidence bundle source')
    parts = [{'name': ('artifact/' if p.parent == artifact_dir else 'runtime/')+
        str(p.relative_to(artifact_dir if p.parent == artifact_dir else runtime)),
        'sha256': digest(p.read_bytes()), 'base64': base64.b64encode(p.read_bytes()).decode()} for p in sorted(files)]
    if training_dir is not None:
        if training_dir.resolve().is_relative_to(ROOT): raise ValueError('Training lineage must remain private')
        for name, expected in DATA_HASHES.items():
            path = training_dir/name
            if path.is_symlink() or sha256_file(path) != expected: raise ValueError('Training recovery checksum changed')
            parts.append({'name': 'training/'+name, 'sha256': expected, 'base64': base64.b64encode(path.read_bytes()).decode()})
    payload = encode({'version': 'c1-support26-private-evidence-v1', 'package_version': PACKAGE,
                      'files': parts, 'production_change': False, 'live_adjustment': 0})
    return encode({'version': 'c1-support26-compressed-backup-v1', 'encoding': 'zlib+base64',
                   'payload_sha256': digest(payload), 'payload': base64.b64encode(zlib.compress(payload)).decode()})


def restore_bundle(raw, destination):
    if destination.exists() or destination.resolve().is_relative_to(ROOT):
        raise ValueError('Fresh private restore directory required')
    envelope = json.loads(raw)
    if envelope.get('version') != 'c1-support26-compressed-backup-v1' or envelope.get('encoding') != 'zlib+base64':
        raise ValueError('Wrong recovery envelope')
    compressed = base64.b64decode(envelope['payload'], validate=True)
    decoder = zlib.decompressobj(); payload = decoder.decompress(compressed, 32*1024*1024+1)
    if len(payload) > 32*1024*1024 or not decoder.eof or decoder.unused_data:
        raise ValueError('Oversized or incomplete recovery payload')
    if digest(payload) != envelope['payload_sha256']:
        raise ValueError('Recovery payload checksum differs')
    bundle = json.loads(payload)
    if bundle.get('version') != 'c1-support26-private-evidence-v1' or bundle.get('package_version') != PACKAGE:
        raise ValueError('Wrong private recovery experiment')
    decoded, names = [], set()
    for part in bundle['files']:
        name = Path(part['name'])
        if (not name.parts or str(name) != part['name'] or name.is_absolute() or '..' in name.parts or name.parts[0] not in ['runtime', 'artifact', 'training']
                or len(name.parts) < 2 or part['name'] in names):
            raise ValueError('Unsafe or duplicate recovery path')
        names.add(part['name']); value = base64.b64decode(part['base64'], validate=True)
        if digest(value) != part['sha256']: raise ValueError('Recovery file checksum differs')
        decoded.append((name, value))
    destination.mkdir(mode=0o700, parents=True)
    for name, value in decoded:
        path = destination/name; path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open('xb') as file: file.write(value)
        path.chmod(0o440)
    return {'files': len(decoded), 'decompression_and_file_hashes_verified': True}


def backup(runtime, artifact_dir, storage=None, training_dir=None):
    raw = encode_bundle(runtime, artifact_dir, training_dir)
    storage = storage or SupportStorage(); storage.ensure_private_bucket()
    receipt = storage.put_verified('c1-support26-v1/'+digest(raw)+'.json', raw, 'application/json')
    # Independently validate recoverability after verified remote byte read-back.
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        restored = restore_bundle(raw, Path(temp)/'restored')
    return {**receipt, **restored}


def small_read(reader, path):
    value = reader.request(path)
    if not isinstance(value, list) or len(value) >= 1000:
        raise ValueError('Unpaginated source changed or expanded')
    return value


def run_cycle(runtime, artifact_dir=ARTIFACT_DIR, reader=None, storage=None):
    manifest, models, hashes = load_models(artifact_dir); ensure_runtime(runtime, manifest)
    reader = reader or Reader(); requested = datetime.now(timezone.utc).isoformat()
    original = reader.request('rpc/get_c1_shadow_v8_inputs_v1', {'p_requested_at': requested})
    validate_payload(original, datetime.now(timezone.utc))
    enriched = {**original, 'candidates': []}; failures, resolutions = [], []
    for candidate in original.get('candidates') or []:
        try:
            latest = max(stamp(r['requested_as_of_at']) for r in candidate['representatives'])
            resolved = reader.request('rpc/get_structural_prior_v1', {'p_ticket_event_id': candidate['ticket_event_id'],
                'p_requested_as_of_at': latest.isoformat()})
            enriched['candidates'].append(enrich_anchor(candidate, resolved))
            resolutions.append({'ticket_event_id': candidate['ticket_event_id'], 'prior': resolved})
        except (ValueError, KeyError, TypeError):
            failures.append({'ticket_event_id': candidate['ticket_event_id'], 'status': 'FAILED_CLOSED', 'reason': 'EXACT_ANCHOR_RESOLUTION_FAILED'})
    enriched['candidate_count'] = len(enriched['candidates'])
    outcomes = small_read(reader, 'ticket_event_outcomes?select=*&limit=1001')
    if original['candidate_count']:
        envelope = {'original': original, 'resolutions': resolutions, 'enriched': enriched}
        folder = runtime/'inputs'; folder.mkdir(mode=0o700, exist_ok=True)
        path = folder/('collector-'+digest(encode(envelope))+'.json')
        if not path.exists(): write_json(path, envelope, True); path.chmod(0o440)
    captured = capture(enriched, manifest, models, hashes, runtime=runtime,
        labelled_ids={r['ticket_event_id'] for r in outcomes}, now=datetime.now(timezone.utc),
        clock=lambda: datetime.now(timezone.utc))
    captured['events'].extend(failures); captured['candidate_count'] += len(failures)
    if captured['candidate_count'] != original['candidate_count']:
        raise ValueError('Enrichment dropped original candidate coverage')
    write_json(runtime/('attempt-'+requested.replace(':', '-')+'.json'), captured, True)
    evidence = [json.loads(p.read_text()) for p in sorted((runtime/'evidence').glob('event-*.json'))]
    inputs = {}
    for path in (runtime/'inputs').glob('candidate-*.json'):
        candidate = json.loads(path.read_bytes()); key = path.stem.removeprefix('candidate-')
        if digest(encode(candidate)) != key: raise ValueError('Stored original input checksum differs')
        inputs[key] = candidate
    metadata = small_read(reader, 'ticket_events?select=id,club_slug,kickoff_at&limit=1001')
    scores, missing, count = score_rows(evidence, outcomes, metadata, manifest, hashes, datetime.now(timezone.utc),
                                       models=models, source_inputs=inputs)
    for row in scores:
        persist_score(runtime/'scores'/f"event-{row['ticket_event_id']}-snapshot-{row['source_snapshot_id']}.json", row)
    report = summary(scores, missing, count)
    attempts = [json.loads(p.read_text()) for p in sorted(runtime.glob('attempt-*.json'))]
    failed = [r for a in attempts for r in a['events'] if r['status'] == 'FAILED_CLOSED']
    report['coverage'] = {'operational_attempts': len(attempts), 'candidate_attempts_including_repeats': sum(a['candidate_count'] for a in attempts),
        'failed_candidate_attempts': len(failed), 'failed_event_ids': sorted({r['ticket_event_id'] for r in failed})}
    write_json(runtime/'latest-scorecard.json', report)
    if report['first_review_ready'] and not (runtime/'first-review.json').exists():
        write_json(runtime/'first-review.json', {'checked_at': datetime.now(timezone.utc).isoformat(),
            'scorecard': report, 'event_ids': sorted({r['ticket_event_id'] for r in scores})}, True)
    receipt = backup(runtime, artifact_dir, storage)
    result = {'status': 'CYCLE_VERIFIED', 'package_version': PACKAGE, 'checked_at': datetime.now(timezone.utc).isoformat(),
        'capture': captured, 'scored_events': report['scored_independent_events'],
        'median26_policy_mae': report['metrics']['median26_policy']['latest_row_mae'],
        'private_backup': receipt, 'host_dependent': True, 'production_change': False, 'live_adjustment': 0}
    write_json(runtime/'latest-cycle.json', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command', required=True)
    freeze = sub.add_parser('freeze'); freeze.add_argument('--data-dir', type=Path, required=True)
    for name in ('check', 'cycle', 'watch'):
        command = sub.add_parser(name); command.add_argument('--artifact-dir', type=Path, default=ARTIFACT_DIR)
        if name != 'check': command.add_argument('--runtime', type=Path, required=True)
        if name == 'watch':
            command.add_argument('--until', required=True); command.add_argument('--interval', type=int, default=900)
    a = p.parse_args()
    if a.command == 'freeze':
        manifest = fit_once(a.data_dir)
        print(json.dumps({key: manifest[key] for key in ['package_version', 'frozen_at', 'artifact', 'estimator', 'attendance_mae']})); return
    if a.command == 'check':
        manifest, _, _ = load_models(a.artifact_dir)
        print(json.dumps({'status': 'FROZEN_IDENTITIES_VERIFIED', 'package_version': PACKAGE,
                          'artifact_sha256': manifest['artifact']['sha256']})); return
    manifest, _, _ = load_models(a.artifact_dir); ensure_runtime(a.runtime, manifest)
    if a.command == 'cycle':
        with (a.runtime/'cycle.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            print(json.dumps(run_cycle(a.runtime, a.artifact_dir))); return
    validate_bounds(a.until, a.interval, datetime.now(timezone.utc))
    with (a.runtime/'cycle.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write_json(a.runtime/'watcher-launch.json', {'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(),
            'until': a.until, 'interval_seconds': a.interval, 'host_dependent': True, 'production_change': False})
        while pd.Timestamp.now(tz='UTC') < stamp(a.until):
            try: result = run_cycle(a.runtime, a.artifact_dir)
            except Exception as exc:
                result = {'status': 'CYCLE_FAILED', 'checked_at': datetime.now(timezone.utc).isoformat(), 'error_type': type(exc).__name__}
                write_json(a.runtime/'latest-cycle.json', result)
            print(json.dumps(result), flush=True)
            time.sleep(max(0., min(a.interval, (stamp(a.until)-pd.Timestamp.now(tz='UTC')).total_seconds())))


if __name__ == '__main__':
    main()
