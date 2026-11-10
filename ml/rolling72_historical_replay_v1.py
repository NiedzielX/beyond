"""Chronological, whole-fixture-held-out retrospective diagnostics, never live v2.

Prediction reads no truth vault. Models are a bounded batch of nonservable fits
of the fixed recipe, on different already-completed fixtures only. All outputs
are explicitly capture-clock retrospective: historical knowledge is unproven.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path

from ml.demand_engine.rolling72_features_v1 import _hash, _time, _id
from ml.rolling72_offline_challenger_v2 import FEATURE_NAMES

VERSION = 'rolling72-chronological-event-heldout-replay-v1'
PRECOMMIT_SHA256 = '4acdfd98b79b781b8704fcfa56097bc0bf0e114e81357085af5075514c1bfdb4'
ROOT = Path(__file__).resolve().parents[1]
PRECOMMIT = ROOT / 'ml/artifacts/rolling72_historical_replay_v1/precommit.json'
MODELS = ('candidate', 'persistence', 'drift', 'pickup')
HORIZONS = (24, 48, 72)
BINS = (0, 3, 7, 15, 30, 50)


def _now():
    return datetime.now(timezone.utc)


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _write(path, value):
    raw = _bytes(value)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as stream:
        stream.write(raw)
    return _sha(raw)


def _regular(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Original regular research file required')
    return path.read_bytes()


def load_precommit(*, synthetic_test=False, precommit=None):
    if precommit is not None:
        if not synthetic_test:
            raise ValueError("Custom protocol is synthetic-only")
        from ml.rolling72_historical_replay_packets_v1 import load_precommit as packet_protocol
        recipe = packet_protocol(synthetic_test=True, precommit=precommit)
        actual = json.loads(_regular(PRECOMMIT))
        for field in ("candidate", "features", "gate", "benchmarks", "protocol", "evaluation", "version", "experiment_id"):
            if recipe[field] != actual[field]:
                raise ValueError("Synthetic data cannot change the fixed modeling recipe")
        return recipe
    recipe = json.loads(_regular(PRECOMMIT))
    if (recipe.get('precommit_sha256') != PRECOMMIT_SHA256
            or _hash({k: v for k, v in recipe.items() if k != 'precommit_sha256'}) != PRECOMMIT_SHA256
            or recipe.get('experiment_id') != VERSION
            or recipe.get('features') != list(FEATURE_NAMES)
            or recipe.get('production_change') is not False or recipe.get('live_adjustment') != 0):
        raise ValueError('Exact published historical precommit required')
    return recipe


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Finite actual numeric value required')
    return float(value)


def _features(value):
    if not isinstance(value, dict) or set(value) != set(FEATURE_NAMES):
        raise ValueError('Exactly twelve declared features required')
    for key, item in value.items():
        if item is None and key.startswith(('delta_', 'slope_')):
            continue
        _number(item)
    if value['last_available_total'] < 0 or value['prefix_span_hours'] < 0 or value['latest_staleness_hours'] != 0:
        raise ValueError('Retrospective inputs must be genuine capture-aligned prefixes')
    for hours in (6, 24, 72):
        if (value[f'delta_{hours}h'] is None) != (value[f'slope_{hours}h'] is None):
            raise ValueError('Delta/slope missingness conflict')
    return value


def _packet(packetdir, synthetic_test, precommit=None):
    """Deliberately allowlists three files. Does not open or inspect truth.json."""
    if not isinstance(synthetic_test, bool):
        raise ValueError('Explicit synthetic mode required')
    recipe = load_precommit(synthetic_test=synthetic_test, precommit=precommit)
    root = Path(packetdir)
    manifest_raw = _regular(root / 'manifest.json')
    manifest = json.loads(manifest_raw)
    if (manifest.get('manifest_sha256') != _hash({k:v for k,v in manifest.items() if k != 'manifest_sha256'})
            or manifest.get('version') != 'rolling72-historical-replay-packets-v1'
            or manifest.get('precommit_sha256') != recipe['precommit_sha256']
            or manifest.get('synthetic_test') is not synthetic_test
            or manifest.get('servable') is not False
            or manifest.get('historical_knowledge_unproven') is not True
            or manifest.get('production_change') is not False or manifest.get('live_adjustment') != 0):
        raise ValueError('Historical packet identity/mode mismatch')
    if not synthetic_test and manifest.get('dataset_sha256') != recipe['dataset']['dataset_sha256']:
        raise ValueError('Pinned real dataset required')
    contents = {}
    for name in ('training_rows.json', 'test_inputs.json'):
        raw = _regular(root / name)
        if _sha(raw) != manifest.get('file_sha256', {}).get(name):
            raise ValueError('Packet file bytes differ from manifest')
        contents[name] = json.loads(raw)
    training, inputs = contents['training_rows.json'], contents['test_inputs.json']
    declared = recipe['dataset']
    if (not isinstance(training, list) or not isinstance(inputs, list)
            or len(training) != declared['known_matched_labels']
            or len(inputs) != declared['all_horizon_coordinates']
            or len({(r['fixture_group'], r['origin_capture_at']) for r in inputs}) != declared['all_feature_origins_before_label_filter']
            or sum(r['status']=='TARGET_NOT_BEFORE_KICKOFF' for r in inputs) != declared['known_postkickoff_coordinates']):
        raise ValueError('Actual packet coverage differs from exact precommit')
    if not synthetic_test and len({r['fixture_group'] for r in inputs}) != declared['completed_selected_fixture_catalogue']:
        raise ValueError('Real test fixture catalogue was silently subsetted')
    for origin in {(r['fixture_group'], r['origin_capture_at']) for r in inputs}:
        if {r['horizon_hours'] for r in inputs if (r['fixture_group'],r['origin_capture_at'])==origin} != set(HORIZONS):
            raise ValueError('All three horizon statuses required at every origin')
    index = {(r['fixture_group'], r['origin_capture_at'], r['horizon_hours']):r for r in inputs}
    for row in training:
        test = index.get((row['fixture_group'], row['origin_capture_at'], row['nominal_horizon_hours']))
        if test is None or any(test[k] != row[k] for k in ('features','ticket_event_id','club_slug','kickoff_at','source_family')):
            raise ValueError('Training/test capture metadata or source features conflict')
    return recipe, manifest, _sha(manifest_raw), training, inputs


def _validate_rows(rows):
    if not isinstance(rows, list):
        raise ValueError('Training row list required')
    ownership, group_clubs, group_kickoffs, seen = {}, {}, {}, set()
    for row in rows:
        if not isinstance(row, dict) or row.get('row_sha256') != _hash({k: v for k, v in row.items() if k != 'row_sha256'}):
            raise ValueError('Training row checksum mismatch')
        f = _features(row['features'])
        event, group, club = _id(row['ticket_event_id']), row['fixture_group'], row['club_slug']
        if not isinstance(group, str) or not group or not isinstance(club, str) or not club:
            raise ValueError('Whole fixture and club identity required')
        if (event in ownership and ownership[event] != group) or (group in group_clubs and group_clubs[group] != club):
            raise ValueError('Fixture identity inflation')
        ownership[event], group_clubs[group] = group, club
        origin, target, label, kickoff = [_time(row[k]) for k in ('origin_capture_at', 'target_at', 'label_captured_at', 'kickoff_at')]
        if group in group_kickoffs and group_kickoffs[group] != kickoff:
            raise ValueError('Fixture kickoff conflict')
        group_kickoffs[group] = kickoff
        h = row['nominal_horizon_hours']
        if (isinstance(h, bool) or h not in HORIZONS or target != origin + timedelta(hours=h)
                or not origin < label <= target < kickoff or target - label > timedelta(hours=6)
                or f['horizon_hours'] != h
                or not math.isclose(f['hours_to_kickoff'], (kickoff - origin).total_seconds()/3600, abs_tol=1e-9)
                or row.get('historical_input_known_at') is not None or row.get('historical_knowledge_unproven') is not True):
            raise ValueError('Training capture clocks/evidence differ')
        last, actual, delta = [_number(row[k]) for k in ('last_available_total', 'matched_available_total', 'target_delta')]
        if actual < 0 or last != f['last_available_total'] or not math.isclose(delta, actual-last, abs_tol=1e-9):
            raise ValueError('Training target arithmetic differs')
        key = (group, origin, h)
        if key in seen:
            raise ValueError('Duplicate training coordinate')
        seen.add(key)


def _validate_inputs(inputs):
    if not isinstance(inputs, list):
        raise ValueError('Test feature list required')
    seen, metadata = set(), {}
    for row in inputs:
        if not isinstance(row, dict) or any(k in row for k in ('target_delta', 'matched_available_total', 'label_status', 'label_captured_at', 'available_total')):
            raise ValueError('Future labels forbidden in test feature packets')
        f = _features(row['features'])
        event = _id(row['ticket_event_id'])
        group, origin, h = row['fixture_group'], _time(row['origin_capture_at']), row['horizon_hours']
        kickoff, target = _time(row['kickoff_at']), _time(row['target_at'])
        identity = {'fixture_group': group, 'origin_capture_at': row['origin_capture_at'], 'horizon_hours': h}
        if (not isinstance(group, str) or not group or row['coordinate_id'] != _hash(identity)
                or isinstance(h, bool) or h not in HORIZONS or row['coordinate_id'] in seen
                or not origin < kickoff or target != origin + timedelta(hours=h)
                or f['horizon_hours'] != h
                or not math.isclose(f['hours_to_kickoff'], (kickoff-origin).total_seconds()/3600, abs_tol=1e-9)
                or row['status'] != ('READY' if target < kickoff else 'TARGET_NOT_BEFORE_KICKOFF')):
            raise ValueError('Test coordinate identity/clock mismatch')
        seen.add(row['coordinate_id'])
        declared = (group, row['club_slug'], kickoff)
        if event in metadata and metadata[event] != declared:
            raise ValueError('Conflicting test fixture metadata')
        metadata[event] = declared
        q = row['history_quality']
        if (not isinstance(q, dict) or isinstance(q.get('hourly_latest_bins'), bool)
                or not isinstance(q.get('hourly_latest_bins'), int) or q['hourly_latest_bins'] < 1
                or _number(q.get('hourly_span_hours')) < 0 or not isinstance(q.get('delta24_anchor_valid'), bool)):
            raise ValueError('Genuine input history quality required')
        ids = row['raw_prefix_snapshot_ids']
        if not isinstance(ids, list) or not ids or len(set(ids)) != len(ids) or any(_id(i) != i for i in ids):
            raise ValueError('Actual prefix snapshot identities required')


def _past(rows, origin, test_group):
    eligible = [row for row in rows if row['fixture_group'] != test_group
                and _time(row['kickoff_at']) < origin and _time(row['target_at']) < origin]
    horizons = defaultdict(set)
    for row in eligible:
        horizons[row['fixture_group']].add(row['nominal_horizon_hours'])
    common = {g for g, hs in horizons.items() if hs == set(HORIZONS)}
    return sorted((r for r in eligible if r['fixture_group'] in common), key=lambda r: r['row_sha256'])


def _gate(rows):
    groups, clubs = {r['fixture_group'] for r in rows}, {r['club_slug'] for r in rows}
    ready = len(groups) >= 5 and len(clubs) >= 3 and len(rows) >= 60
    return {'status': 'READY_TO_FIT' if ready else 'NO_FIT', 'training_rows': len(rows),
            'common_fixtures': len(groups), 'common_clubs': len(clubs), 'training_fixture_groups': sorted(groups)}


def _weights(rows):
    n, groups = len(rows), {r['fixture_group'] for r in rows}
    counts = Counter((r['fixture_group'], r['nominal_horizon_hours']) for r in rows)
    if not rows or any((g,h) not in counts for g in groups for h in HORIZONS):
        raise ValueError('Common all-horizon training cohort required')
    return [n/(len(groups)*3*counts[r['fixture_group'],r['nominal_horizon_hours']]) for r in rows]


def _matrix(rows):
    import numpy as np
    return np.asarray([[float('nan') if r['features'][k] is None else r['features'][k] for k in FEATURE_NAMES] for r in rows], dtype=float)


def _maturity(days):
    return max(b for b in BINS if days >= b)


def _pickup(train, row):
    family, horizon = row['source_family'], row['horizon_hours']
    maturity = _maturity(row['features']['hours_to_kickoff']/24)
    pooled = [r for r in train if r['source_family'] == family and r['nominal_horizon_hours'] == horizon
              and r['fixture_group'] != row['fixture_group']]
    narrow = [r for r in pooled if _maturity(r['features']['hours_to_kickoff']/24) == maturity]
    for scope, selected in (('same_family_horizon_maturity',narrow), ('same_family_horizon_pooled',pooled)):
        groups, clubs = {r['fixture_group'] for r in selected}, {r['club_slug'] for r in selected}
        if len(groups) < 5 or len(clubs) < 3:
            continue
        counts = Counter(r['fixture_group'] for r in selected)
        ordered = sorted((r['target_delta'],1/counts[r['fixture_group']]) for r in selected)
        boundary, cumulative = sum(w for _,w in ordered)/2, 0
        for delta, weight in ordered:
            cumulative += weight
            if cumulative >= boundary - 1e-12:
                return max(0.0,row['features']['last_available_total']+delta),scope
    return None,'INSUFFICIENT_PICKUP_SUPPORT'


def _code_hashes():
    return {name:_sha(_regular(ROOT/name)) for name in ('ml/rolling72_historical_replay_v1.py',
            'ml/rolling72_historical_replay_packets_v1.py', 'ml/demand_engine/rolling72_features_v1.py')}


def run_predictions(packetdir, outdir, *, synthetic_test=False, precommit=None):
    """Fit fixed historical recipes and seal predictions BEFORE truth is read."""
    recipe, manifest, packet_sha, training, inputs = _packet(packetdir, synthetic_test, precommit)
    _validate_rows(training); _validate_inputs(inputs)
    destination = Path(outdir)
    if destination.exists() or destination.is_symlink() or destination.resolve().is_relative_to(ROOT):
        raise ValueError('New exclusive private output directory required; never overwrite/refit')
    destination.mkdir(mode=0o700,parents=True)
    started, code = _now(), _code_hashes()
    if started < _time(recipe['created_at']):
        raise ValueError('Published precommit must precede actual fits')
    _write(destination/'run-marker.json', {'status':'STARTED_NO_REFIT','started_at':started.isoformat(),'precommit_sha256':recipe['precommit_sha256'],'synthetic_test':synthetic_test})
    try:
        import joblib
        import numpy as np
        import sklearn
        from sklearn.ensemble import HistGradientBoostingRegressor
        from threadpoolctl import threadpool_limits
        if sklearn.__version__ != recipe['candidate']['sklearn_version']:
            raise ValueError('Exact precommitted sklearn version required')
        cache, folds, predictions = {}, [], []
        with threadpool_limits(limits=1):
            for row in sorted(inputs,key=lambda r:(_time(r['origin_capture_at']),r['fixture_group'],r['horizon_hours'])):
                origin = _time(row['origin_capture_at'])
                if row['status'] != 'READY':
                    predictions.append({'coordinate_id':row['coordinate_id'],'input':row,'fold_model_id':None,
                        'models':{name:{'status':'UNAVAILABLE','predicted_available_total':None,'reason':row['status']} for name in MODELS}})
                    continue
                train = _past(training,origin,row['fixture_group'])
                key = _hash([r['row_sha256'] for r in train]); gate = _gate(train)
                if key not in cache:
                    model = None
                    fold = {'fold_model_id':VERSION+':'+key,'training_rows_sha256':key,'gate':gate,
                        'simulated_training_cutoff_at':origin.isoformat(),'actual_fit_started_at':None,'actual_fitted_at':None,
                        'candidate_recipe_id':recipe['candidate']['id'],'active_v2_artifact_used':False,'servable':False,
                        'synthetic_test':synthetic_test,'historical_knowledge_unproven':True}
                    if gate['status']=='READY_TO_FIT':
                        if sum(f['actual_fitted_at'] is not None for f in folds)>=31:
                            raise ValueError('Precommitted diagnostic fit bound exceeded')
                        model=HistGradientBoostingRegressor(**recipe['candidate']['parameters'])
                        fold['actual_fit_started_at']=_now().isoformat()
                        weights=_weights(train)
                        model.fit(_matrix(train),np.asarray([r['target_delta'] for r in train]),sample_weight=np.asarray(weights))
                        fold['actual_fitted_at']=_now().isoformat();fold['training_weights_sha256']=_hash(weights)
                        modelpath=destination/('fold-'+key+'.joblib')
                        with os.fdopen(os.open(modelpath,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as stream:
                            joblib.dump(model,stream,compress=3,protocol=5)
                        fold['model_file_sha256']=_sha(_regular(modelpath));fold['model_filename']=modelpath.name
                    cache[key]=(model,fold);folds.append(fold)
                model,fold=cache[key]
                outputs={name:{'status':'UNAVAILABLE','predicted_available_total':None,'reason':row['status']} for name in MODELS}
                if row['status']=='READY':
                    last=row['features']['last_available_total'];q=row['history_quality']
                    outputs['persistence']={'status':'READY','predicted_available_total':last,'reason':None}
                    if q['hourly_latest_bins']>=4 and q['hourly_span_hours']>=24 and q['delta24_anchor_valid'] and row['features']['slope_24h'] is not None:
                        outputs['drift']={'status':'READY','predicted_available_total':max(0.0,last+row['features']['slope_24h']*row['horizon_hours']),'reason':None}
                    else:outputs['drift']['reason']='INSUFFICIENT_OBSERVED_HISTORY'
                    value,scope=_pickup(train,row)
                    outputs['pickup']={'status':'READY' if value is not None else 'UNAVAILABLE','predicted_available_total':value,'reason':None if value is not None else scope,'support_scope':scope}
                    if model is not None:
                        delta=float(model.predict(_matrix([row]))[0]); value=max(0.0,last+delta)
                        if not math.isfinite(value):raise ValueError('Nonfinite candidate prediction')
                        outputs['candidate']={'status':'READY','predicted_available_total':value,'reason':None}
                    else:outputs['candidate']['reason']='NO_FIT'
                predictions.append({'coordinate_id':row['coordinate_id'],'input':row,'fold_model_id':fold['fold_model_id'],'models':outputs})
        if code != _code_hashes():raise ValueError('Prediction pipeline changed during diagnostic batch')
        pred={'version':VERSION,'precommit_sha256':recipe['precommit_sha256'],'packet_manifest_sha256':packet_sha,
            'predictions':predictions,'synthetic_test':synthetic_test,'servable':False,'historical_knowledge_unproven':True,
            'evidence_kind':'retrospective_predictions_not_previously_issued_forecasts','active_v2_artifact_used':False,
            'production_change':False,'live_adjustment':0}
        pred_sha=_write(destination/'predictions.json',pred)
        folds_sha=_write(destination/'folds.json',folds)
        seal={'version':VERSION,'precommit_sha256':recipe['precommit_sha256'],'packet_manifest_sha256':packet_sha,
            'prediction_file_sha256':pred_sha,'folds_file_sha256':folds_sha,'code_sha256':code,
            'started_at':started.isoformat(),'sealed_at':_now().isoformat(),'truth_vault_opened':False,
            'diagnostic_model_fits':sum(f['actual_fitted_at'] is not None for f in folds),'support_sets':len(folds),
            'coordinates':len(predictions),'synthetic_test':synthetic_test,'servable':False,
            'active_v2_artifact_used':False,'production_change':False,'live_adjustment':0}
        seal['seal_sha256']=_hash(seal);_write(destination/'seal.json',seal)
        return seal
    except BaseException as exc:
        _write(destination/'failed-no-refit.json',{'error_type':type(exc).__name__,'failed_at':_now().isoformat(),'refit_permitted':False})
        raise


def _metrics(rows):
    if not rows:return {'scored_points':0,'scored_fixtures':0,'scored_clubs':0,'event_balanced_mae':None,'event_balanced_bias':None,'worst_absolute_error':None,'p90_pooled_absolute_error_nearest_rank':None}
    grouped=defaultdict(list)
    for row in rows:grouped[row['fixture_group']].append(row['error'])
    absolute=sorted(abs(r['error']) for r in rows)
    return {'scored_points':len(rows),'scored_fixtures':len(grouped),'scored_clubs':len({r['club_slug'] for r in rows}),
        'event_balanced_mae':sum(sum(abs(e) for e in es)/len(es) for es in grouped.values())/len(grouped),
        'event_balanced_bias':sum(sum(es)/len(es) for es in grouped.values())/len(grouped),
        'worst_absolute_error':absolute[-1],'p90_pooled_absolute_error_nearest_rank':absolute[math.ceil(.9*len(absolute))-1]}


def _history(span):
    return 'first_point' if span==0 else 'under24h' if span<24 else '24_to72h' if span<72 else '72hplus'


def _paired(candidate,baseline):
    import numpy as np
    a={r['coordinate_id']:r for r in candidate};b={r['coordinate_id']:r for r in baseline};keys=sorted(set(a)&set(b))
    ar,br=[a[k] for k in keys],[b[k] for k in keys];groups=defaultdict(list)
    for left,right in zip(ar,br):groups[left['fixture_group']].append(abs(left['error'])-abs(right['error']))
    values=np.asarray([sum(v)/len(v) for _,v in sorted(groups.items())],dtype=float)
    point=float(values.mean()) if len(values) else None;interval=None
    if len(values)>=2:
        generator=np.random.default_rng(42)
        draws=generator.choice(values,size=(10000,len(values)),replace=True).mean(axis=1)
        interval=[float(x) for x in np.percentile(draws,[2.5,97.5],method='linear')]
    return {'candidate':_metrics(ar),'baseline':_metrics(br),'event_balanced_mae_difference_candidate_minus_baseline':point,
        'fixture_bootstrap_95_percentile_interval':interval,'bootstrap_replicates':10000 if interval else 0,
        'bootstrap_seed':42,'scope':'descriptive_exposed_retrospective_not_formal_review'}


def score_predictions(packetdir,outdir,*,synthetic_test=False,precommit=None):
    """Open future observations only after verifying the complete prediction seal."""
    recipe,manifest,packet_sha,_,inputs=_packet(packetdir,synthetic_test,precommit)
    destination=Path(outdir);seal=json.loads(_regular(destination/'seal.json'))
    if (seal.get('version')!=VERSION or seal.get('precommit_sha256')!=recipe['precommit_sha256']
            or seal.get('packet_manifest_sha256')!=packet_sha or seal.get('synthetic_test') is not synthetic_test
            or seal.get('seal_sha256')!=_hash({k:v for k,v in seal.items() if k!='seal_sha256'})
            or seal.get('truth_vault_opened') is not False or seal.get('code_sha256')!=_code_hashes()
            or seal.get('servable') is not False or _time(seal['sealed_at'])>_now()):
        raise ValueError('Complete unchanged prediction seal required before truth access')
    predraw,foldraw=_regular(destination/'predictions.json'),_regular(destination/'folds.json')
    if _sha(predraw)!=seal['prediction_file_sha256'] or _sha(foldraw)!=seal['folds_file_sha256']:
        raise ValueError('Sealed prediction/model metadata bytes changed')
    for fold in json.loads(foldraw):
        if fold.get('model_filename') and _sha(_regular(destination/fold['model_filename']))!=fold['model_file_sha256']:
            raise ValueError('Diagnostic model bytes changed')
    # First truth read occurs below, only after all preceding seal checks.
    truthraw=_regular(Path(packetdir)/'truth.json')
    if _sha(truthraw)!=manifest['file_sha256']['truth.json']:raise ValueError('Truth vault differs from its packet binding')
    truth=json.loads(truthraw);predictions=json.loads(predraw)['predictions']
    if not isinstance(truth,dict) or set(truth)!={r['coordinate_id'] for r in predictions} or len(predictions)!=len(inputs):
        raise ValueError('Complete truth and input coordinate sets must match')
    errors=defaultdict(list);truthstatus=Counter();predictionstatus=defaultdict(Counter)
    for item in predictions:
        row=item['input'];coordinate=item['coordinate_id'];label=truth[coordinate];status=label['status'];truthstatus[status]+=1
        if (label['fixture_group']!=row['fixture_group'] or label['origin_capture_at']!=row['origin_capture_at']
                or label['horizon_hours']!=row['horizon_hours'] or label['target_at']!=row['target_at']):
            raise ValueError('Truth is bound to a different coordinate')
        actual=None
        if status=='MATCHED':
            actual=_number(label['available_total']);origin,target,kickoff=[_time(row[k]) for k in ('origin_capture_at','target_at','kickoff_at')]
            captured=_time(label['label_captured_at']);identifier=_id(label['label_snapshot_id'])
            if (actual<0 or not origin<captured<=target<kickoff or target-captured>timedelta(hours=6)
                    or identifier in row['raw_prefix_snapshot_ids'] or row['status']!='READY'):
                raise ValueError('Matched target is not a genuine later coordinate')
        elif any(label.get(k) is not None for k in ('available_total','label_captured_at','label_snapshot_id')):
            raise ValueError('Unavailable truth must stay null')
        for model in MODELS:
            output=item['models'][model];predictionstatus[model][output['status']]+=1;value=output['predicted_available_total']
            if value is None:
                if output['status']=='READY':raise ValueError('READY prediction cannot be null')
            elif output['status']!='READY' or _number(value)<0 or row['status']!='READY':
                raise ValueError('Invalid sealed numeric prediction')
            elif actual is not None:
                errors[row['horizon_hours'],model].append({'coordinate_id':coordinate,'fixture_group':row['fixture_group'],
                    'club_slug':row['club_slug'],'error':value-actual,'maturity_bin_days':_maturity(row['features']['hours_to_kickoff']/24),
                    'history_bin':_history(row['features']['prefix_span_hours'])})
    declared = recipe['dataset']
    for name,status in (('known_matched_labels','MATCHED'),('known_stale_target_coordinates','STALE_TARGET_OBSERVATION'),('known_postkickoff_coordinates','TARGET_NOT_BEFORE_KICKOFF')):
        if truthstatus[status] != declared[name]:
            raise ValueError('Actual truth status coverage differs from exact precommit')
    metrics={};paired={};strata={}
    for h in HORIZONS:
        for model in MODELS:
            rows=errors[h,model];key=f'+{h}h/{model}';metrics[key]=_metrics(rows)
            strata[key]={}
            for field in ('club_slug','maturity_bin_days','history_bin'):
                strata[key][field]={str(value):_metrics([r for r in rows if r[field]==value]) for value in sorted({r[field] for r in rows},key=str)}
        for model in MODELS[1:]:paired[f'+{h}h/candidate-vs-{model}']=_paired(errors[h,'candidate'],errors[h,model])
    result={'version':VERSION,'precommit_sha256':recipe['precommit_sha256'],'seal_sha256':seal['seal_sha256'],
        'scored_at':_now().isoformat(),'prediction_sealed_at':seal['sealed_at'],'metrics':metrics,'paired_metrics':paired,'strata':strata,
        'coverage':{'input_coordinates':len(inputs),'input_fixtures':len({r['fixture_group'] for r in inputs}),
            'truth_status_counts':dict(truthstatus),'prediction_status_counts':{m:dict(v) for m,v in predictionstatus.items()},
            'diagnostic_model_fits':seal['diagnostic_model_fits'],'per_horizon':{str(h):{'inputs':sum(r['horizon_hours']==h for r in inputs),
                'matched':sum(truth[r['coordinate_id']]['status']=='MATCHED' for r in inputs if r['horizon_hours']==h)} for h in HORIZONS}},
        'synthetic_test':synthetic_test,'servable':False,'historical_knowledge_unproven':True,
        'historical_metadata_versions_proven':False,'formal_review_eligible_new_fixtures':0,
        'evidence_kind':'retrospective_capture_clock_only_event_heldout','active_v2_artifact_used':False,
        'attendance_mae_computed':False,'production_change':False,'live_adjustment':0}
    result['result_sha256']=_hash(result);_write(destination/'scores.json',result)
    return result
