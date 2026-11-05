"""Two precommitted residual fits; all later runtime use is inference-only."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor

from ml.c1_alpha_t1_tournament_v2 import event_weights, pipeline
from ml.c1_support26_v1 import (ROOT, TRAIN_IDS, read_training, load_models as load_benchmarks,
                               dependency_hashes, numerical_environment, LIBRARIES)
from ml.demand_engine.run_c1_shadow_v8 import sha256_file
from ml.export_structural_known_at_inputs_v1 import digest, validate_envelope
from ml.features.c1_history_support_v1 import (BASE_FEATURES, FEATURES, HISTORY_FEATURES,
                                              prepare_training_features, canonical_club)

PACKAGE='c1-history-support-residual-v1-frozen-2026-11-05-n26'
PRECOMMIT=ROOT/'ml/C1_HISTORY_SUPPORT_RESIDUAL_PRECOMMIT_V1.md'
ARTIFACT_DIR=ROOT/'ml/artifacts/c1_history_residual_v1'
SOURCE_SHA='ad1fc737f607297f20ea171e0ea99d4d3398fccccb959a6980339bceb6d67afa'
PARAMS={'quantile':.5,'alpha':.1,'solver':'highs','fit_intercept':True}
HEADS={'control':BASE_FEATURES,'history':FEATURES}


def locked_sources():
    files=['ml/c1_history_residual_v1.py','ml/run_c1_history_residual_v1.py','ml/features/c1_history_support_v1.py',
           'ml/select_structural_known_at_snapshot_v1.py','ml/archive_structural_known_at_inputs_v1.py',
           'ml/attendance_knowledge_time_guard_v1.py','ml/structural_known_at_shadow_v1.py',
           'ml/export_structural_known_at_inputs_v1.py']
    result={**dependency_hashes(),**{name:sha256_file(ROOT/name) for name in files}}
    result.update({str(p.relative_to(ROOT)):sha256_file(p) for p in (ROOT/'ml/artifacts/c1_support26_v1').glob('*') if p.is_file()})
    return result


def save(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    path.chmod(0o440)


def fixture_unit(fixture):
    date=pd.Timestamp(fixture['kickoff_at']).tz_convert('Europe/Warsaw').date().isoformat()
    return digest([canonical_club(fixture['club_slug']),date])


@dataclass
class ResidualRuntime:
    estimator: object
    features: tuple[str,...]
    head: str
    package_version: str=PACKAGE

    def predict_live_p50(self,frame):
        if 'actual_attendance' in frame or 'target_attendance' in frame:raise ValueError('Inference cannot receive target labels')
        if any(c not in frame for c in (*self.features,'prior_p50','stadium_capacity')):raise ValueError('Missing residual inference feature')
        prior=frame.prior_p50.to_numpy(float);cap=frame.stadium_capacity.to_numpy(float)
        residual=np.asarray(self.estimator.predict(frame[list(self.features)]),dtype=float)
        if (residual.shape!=(len(frame),) or not np.isfinite(residual).all()
                or not np.isfinite(prior).all() or not np.isfinite(cap).all()
                or (cap<=0).any() or (prior<0).any() or (prior>cap).any()):raise ValueError('Invalid residual inference values')
        return np.clip(prior+residual,0,cap)


def training_gate(frame,x,records):
    supported=[r for r in records if r['verified_home_n']>0]
    if (len(frame)!=80 or tuple(sorted(frame.ticket_event_id.unique()))!=TRAIN_IDS
            or frame.ticket_event_id.nunique()<20 or len({r['club'] for r in records})<8
            or len({r['ticket_event_id'] for r in supported})<8 or len({r['club'] for r in supported})<5
            or tuple(x.columns)!=FEATURES or len(x)!=len(frame)
            or any(x[c].nunique(dropna=True)<2 for c in HISTORY_FEATURES)):
        raise ValueError('Fixed target-free history/fixture support gate not met')
    return {'rows':80,'events':26,'clubs':len({r['club'] for r in records}),
        'history_rows':len(supported),'history_events':len({r['ticket_event_id'] for r in supported}),
        'history_clubs':len({r['club'] for r in supported})}


def fit_once(data_dir,source_path,publication,output=ARTIFACT_DIR):
    if output.resolve()!=ARTIFACT_DIR or output.exists():raise ValueError('Only a fresh canonical pair freeze is allowed')
    if numerical_environment()!=LIBRARIES:raise ValueError('Pinned numerical environment differs')
    proof=json.loads(publication.read_text())
    if (proof.get('remote_ref_verified') is not True or proof.get('precommit_sha256')!=sha256_file(PRECOMMIT)
            or proof.get('dependency_sha256')!=locked_sources()):raise ValueError('Publish exact protocol/runtime before fitting')
    source=validate_envelope(json.loads(source_path.read_text()))
    if source['export_sha256']!=SOURCE_SHA:raise ValueError('Exact declared history source changed')
    baseline,benchmarks,hashes=load_benchmarks()
    frame,_,_=read_training(data_dir,benchmarks)
    fixtures=json.loads((data_dir/'canonical-fixtures.json').read_text())
    x,records=prepare_training_features(frame.drop(columns='actual_attendance'),fixtures,source)
    support=training_gate(frame,x,records)
    imported_ids={r['id'] for r in source['parts']['history'] if str((r.get('source_payload') or {}).get('verification_run_id'))=='41840960556'}
    if any(r['kind']=='history' and r['id'] in imported_ids for item in records for r in item['source_records']):
        raise ValueError('Later-known sixteen imports cannot enter old historical training observations')
    before=locked_sources();output.mkdir(parents=True)
    save(output/'FIT_STARTED.json',{'package_version':PACKAGE,'started_at':datetime.now(timezone.utc).isoformat(),'declared_fits':2})
    target=(frame.actual_attendance-frame.prior_p50).to_numpy(float)
    details={}
    for name,features in HEADS.items():
        estimator=pipeline(list(features),False,QuantileRegressor(**PARAMS),scale=True)
        estimator.fit(x[list(features)],target,model__sample_weight=event_weights(frame))
        runtime=ResidualRuntime(estimator,tuple(features),name)
        path=output/(name+'.joblib');joblib.dump(runtime,path,compress=3)
        check=x.copy();check['prior_p50']=frame.prior_p50.to_numpy();check['stadium_capacity']=frame.stadium_capacity.to_numpy()
        values=joblib.load(path).predict_live_p50(check)
        if values.shape!=(80,) or not np.isfinite(values).all():raise ValueError('Pair finite load-back failed')
        details[name]={'filename':path.name,'sha256':sha256_file(path),'features':list(features),
            'fit_count':1,'nonzero_coefficients':int(np.count_nonzero(estimator.named_steps['model'].coef_))}
    if before!=locked_sources():raise ValueError('A frozen source changed during fitting')
    manifest={'package_version':PACKAGE,'frozen_at':datetime.now(timezone.utc).isoformat(),
        'precommit_sha256':sha256_file(PRECOMMIT),'history_source_sha256':SOURCE_SHA,
        'training_csv_sha256':sha256_file(data_dir/'training.csv'),'training':support,
        'training_event_ids':list(TRAIN_IDS),'training_fixture_unit_hashes':sorted(fixture_unit(r) for r in fixtures),
        'all_training_exposed':True,'historical_original_source_snapshots_verified':False,
        'heads':details,'estimator':{'family':'QuantileRegressor',**PARAMS,'total_fits':2},
        'target':'actual_attendance_minus_shared_prior_in_persons','training_mae_computed':False,
        'dependency_sha256':before,'libraries':LIBRARIES,'benchmark_manifest_sha256':baseline['_verified_manifest_sha256'],
        'benchmark_hashes':hashes,'production_change':False,'live_adjustment':0,'attendance_mae':None}
    save(output/'manifest.json',manifest);save(output/'freeze-receipt.json',{'manifest_sha256':sha256_file(output/'manifest.json')})
    return manifest


def load_models(folder=ARTIFACT_DIR):
    m=json.loads((folder/'manifest.json').read_text());receipt=json.loads((folder/'freeze-receipt.json').read_text())
    if (receipt['manifest_sha256']!=sha256_file(folder/'manifest.json') or m['package_version']!=PACKAGE
            or m['precommit_sha256']!=sha256_file(PRECOMMIT) or m['dependency_sha256']!=locked_sources()
            or m['libraries']!=numerical_environment() or m['libraries']!=LIBRARIES
            or m['training_event_ids']!=list(TRAIN_IDS) or m['history_source_sha256']!=SOURCE_SHA
            or m['production_change'] is not False or m['live_adjustment']!=0):raise ValueError('Residual pair/source/environment identity changed')
    baseline,benchmarks,hashes=load_benchmarks()
    if hashes!=m['benchmark_hashes'] or baseline['_verified_manifest_sha256']!=m['benchmark_manifest_sha256']:
        raise ValueError('Paired frozen benchmark changed')
    models={}
    for name,features in HEADS.items():
        spec=m['heads'][name];path=folder/spec['filename']
        if sha256_file(path)!=spec['sha256'] or spec['features']!=list(features):raise ValueError('Frozen pair artifact differs')
        model=joblib.load(path)
        if model.package_version!=PACKAGE or model.head!=name or model.features!=features:raise ValueError('Frozen pair runtime differs')
        if any(model.estimator.named_steps['model'].get_params()[k]!=v for k,v in PARAMS.items()):raise ValueError('Frozen pair parameters differ')
        models[name]=model
    m['_verified_manifest_sha256']=receipt['manifest_sha256']
    return m,models,(baseline,benchmarks,hashes)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['check','fit'])
    p.add_argument('--data-dir',type=Path);p.add_argument('--source',type=Path);p.add_argument('--publication-receipt',type=Path)
    a=p.parse_args()
    if a.action=='check':m,_,_=load_models();print(json.dumps({'status':'FROZEN_RESIDUAL_PAIR_VERIFIED','package_version':PACKAGE}));return
    if None in (a.data_dir,a.source,a.publication_receipt):p.error('Fit requires exact data, source and publication receipt')
    m=fit_once(a.data_dir,a.source,a.publication_receipt);print(json.dumps({k:m[k] for k in ['package_version','frozen_at','training','heads','attendance_mae']}))


if __name__=='__main__':main()
