"""One declared median fit on the exact existing20-event frame; no scoring."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline

from ml.c1_live_matched_audit_v1 import ROOT, frozen_hashes
from ml.c1_training_expansion_capture_v1 import load_frozen
from ml.c1_training_expansion_v1 import EVENT_IDS, CUTOFF
from ml.c1_alpha_t1_tournament_v2 import event_weights
from ml.demand_engine.c1_seat_median_runtime_v1 import C1SeatMedianRuntimeV1, PACKAGE, MODEL_ID
from ml.demand_engine.run_c1_shadow_v8 import sha256_file

PRECOMMIT = ROOT/'ml/C1_SEAT_MEDIAN_PRECOMMIT_V1.md'
ARTIFACT_DIR = ROOT/'ml/artifacts/c1_seat_median_v1'
LIBRARIES = {'numpy': '2.3.5', 'pandas': '2.2.3', 'scikit_learn': '1.8.0', 'joblib': '1.5.3', 'scipy': '1.17.0'}


def fit_once(training_csv, output):
    if output.resolve() != ARTIFACT_DIR or output.exists():
        raise ValueError('Require the single fresh canonical median freeze destination')
    installed = {'numpy': np.__version__, 'pandas': pd.__version__, 'scikit_learn': sklearn.__version__,
                 'joblib': joblib.__version__, 'scipy': scipy.__version__}
    if installed != LIBRARIES: raise ValueError('Pinned numerical environment differs')
    baseline, _, ridge, _ = load_frozen(ROOT/'ml/artifacts/c1_training_expansion_v1')
    if sha256_file(training_csv) != baseline['training']['private_frame_sha256']:
        raise ValueError('Median source frame differs from exact frozen20eventtraining')
    before = frozen_hashes()
    frame = pd.read_csv(training_csv)
    if (len(frame) != 74 or tuple(sorted(frame.ticket_event_id.unique())) != EVENT_IDS
            or frame.duplicated(['ticket_event_id', 'as_of_at']).any()):
        raise ValueError('Training identities changed')
    target, capacity = frame.actual_attendance.to_numpy(float), frame.stadium_capacity.to_numpy(float)
    if (not np.isfinite(target).all() or not np.isfinite(capacity).all()
            or (target <= 0).any() or (target > capacity).any()):
        raise ValueError('Invalid frozen labels/capacity')
    features = list(ridge.features)
    preprocessor = deepcopy(ridge.estimator.named_steps['prep'])
    transformed = preprocessor.transform(frame[features])
    # Serialize the already-fitted representation before fitting only the new head.
    preprocessor_hash = joblib.hash(preprocessor)
    output.mkdir(parents=True)
    (output/'FIT_STARTED.json').write_text(json.dumps({'package_version': PACKAGE,
        'at': datetime.now(timezone.utc).isoformat()})+'\n')
    model = QuantileRegressor(quantile=.5, alpha=.1, solver='highs', fit_intercept=True)
    model.fit(transformed, target, sample_weight=event_weights(frame))
    if joblib.hash(preprocessor) != preprocessor_hash: raise ValueError('Frozen representation changed')
    runtime = C1SeatMedianRuntimeV1(Pipeline([('prep', preprocessor), ('model', model)]), tuple(features), EVENT_IDS, 74)
    path = output/'c1_seat_median_v1.joblib'; joblib.dump(runtime, path, compress=3)
    loaded = joblib.load(path); predictions = loaded.predict_live_p50(frame)
    if len(predictions) != 74 or not np.isfinite(predictions).all(): raise ValueError('Median load-back failed')
    manifest = {'package_version': PACKAGE, 'live_model_id': MODEL_ID, 'status': 'EXPERIMENTAL_SHADOW',
        'production_change': False, 'production_activation': False, 'live_adjustment': 0,
        'frozen_at': datetime.now(timezone.utc).isoformat(), 'training_cutoff': CUTOFF.isoformat(),
        'precommit_sha256': sha256_file(PRECOMMIT), 'source_frame_sha256': sha256_file(training_csv),
        'baseline_manifest_sha256': baseline['_verified_manifest_sha256'],
        'baseline_ridge_artifact_sha256': baseline['artifact']['sha256'],
        'training': {'event_ids': list(EVENT_IDS), 'events': 20, 'rows': 74, 'clubs': 11,
                     'all_training_exposed': True, 'target': 'direct_attendance_persons', 'equal_event_weights': True},
        'features': features, 'preprocessor_reused_without_fit': True, 'preprocessor_joblib_hash': preprocessor_hash,
        'estimator': {'family': 'QuantileRegressor', 'quantile': .5, 'alpha': .1, 'solver': 'highs',
                      'fit_intercept': True, 'fit_count': 1, 'nonzero_coefficients': int(np.count_nonzero(model.coef_))},
        'output': {'units': 'persons', 'multiply_by_capacity': False, 'clipping': '[0,stadium_capacity]'},
        'artifact': {'filename': path.name, 'sha256': sha256_file(path)},
        'source_code_sha256': {name: sha256_file(ROOT/name) for name in
            ['ml/demand_engine/c1_seat_median_runtime_v1.py', 'ml/freeze_c1_seat_median_v1.py',
             'ml/capture_c1_seat_median_v1.py', 'ml/collect_c1_training_expansion_v1.py',
             'ml/score_c1_training_expansion_v1.py', 'ml/watch_c1_training_expansion_v1.py',
             'ml/export_c1_matched_audit_inputs_v1.py']},
        'old_frozen_hashes': before, 'libraries': installed, 'attendance_mae': None,
        'training_mae_computed': False, 'prospective_validation_required': True}
    if before != frozen_hashes(): raise ValueError('Old frozen artifacts changed')
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    (output/'freeze_receipt.json').write_text(json.dumps({'package_version': PACKAGE,
        'manifest_sha256': sha256_file(output/'manifest.json')}, indent=2)+'\n')
    print(json.dumps({k: manifest[k] for k in ['package_version', 'frozen_at', 'artifact', 'estimator', 'attendance_mae']}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--training-csv', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, default=ARTIFACT_DIR)
    a = p.parse_args(); fit_once(a.training_csv, a.output_dir)


if __name__ == '__main__': main()
