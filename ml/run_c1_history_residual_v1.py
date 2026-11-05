"""Bounded private prospective sidecar for the fixed history-support ablation."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import time
import zlib

import numpy as np
import pandas as pd

from ml.c1_history_residual_v1 import PACKAGE, ROOT, TRAIN_IDS, fixture_unit, load_models
from ml.c1_support26_v1 import score_rows as verify_benchmark_rows
from ml.c1_training_expansion_capture_v1 import immutable_save, validate_current
from ml.demand_engine.c1_shadow_runtime_v8 import apply_v8_policy
from ml.demand_engine.daily_inventory_path_storage_v1 import PrivateResearchStorage, encode, digest
from ml.demand_engine.run_c1_shadow_v8 import feature_record
from ml.export_c1_matched_audit_inputs_v1 import Reader
from ml.features.c1_history_support_v1 import feature_row, canonical_club
from ml.score_c1_training_expansion_v1 import persist_score
from ml.select_structural_known_at_snapshot_v1 import select_snapshot

VERSION='c1-history-residual-paired-evidence-v1'
PREDICTIONS=('control_raw','control_policy','history_raw','history_policy','median26_policy','median20_policy',
             'ridge20_policy','original9_policy','prior')
PRODUCT_BASELINES=('control_policy','median26_policy','median20_policy','ridge20_policy','original9_policy','prior')


def stamp(value):
    t=pd.Timestamp(value)
    if pd.isna(t) or t.tzinfo is None:raise ValueError('Explicit evidence timestamp required')
    return t.tz_convert('UTC')


def write_json(path,value,exclusive=False):
    with path.open('x' if exclusive else 'w') as f:json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')


def ensure_runtime(runtime,manifest):
    if runtime.resolve().is_relative_to(ROOT):raise ValueError('Private history evidence must remain outside Git')
    runtime.mkdir(mode=0o700,parents=True,exist_ok=True)
    marker=runtime/'experiment.json';expected={'package_version':PACKAGE,'manifest_sha256':manifest['_verified_manifest_sha256']}
    if marker.exists():
        if json.loads(marker.read_text())!=expected:raise ValueError('Different experiment owns runtime')
    else:
        if any(runtime.iterdir()):raise ValueError('Nonempty unmarked runtime cannot be reused')
        write_json(marker,expected,True)


def put_blob(runtime,folder,payload):
    raw=encode(payload);sha=digest(raw);directory=runtime/folder;directory.mkdir(mode=0o700,exist_ok=True)
    path=directory/(sha+'.json')
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('Immutable source blob conflict')
    else:
        with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        path.chmod(0o440)
    return sha


def get_blob(runtime,folder,sha):
    if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):raise ValueError('Invalid immutable blob key')
    raw=(runtime/folder/(sha+'.json')).read_bytes()
    if digest(raw)!=sha:raise ValueError('Immutable input/source blob checksum differs')
    return json.loads(raw)


def source_has_target(payload,candidate,fixture):
    if any(r['ticket_event_id']==candidate['ticket_event_id'] for r in payload['parts']['outcomes']):return True
    home=canonical_club(fixture['club_slug']);date=stamp(fixture['kickoff_at']).tz_convert('Europe/Warsaw').date()
    return any(canonical_club(r['club_slug'])==home and stamp(r['kickoff_at']).tz_convert('Europe/Warsaw').date()==date
               for r in payload['parts']['history'] if r.get('actual_attendance') is not None)


def decisions(candidate,fixture,sources,models,original_runtime):
    reps=sorted(candidate['representatives'],key=lambda r:stamp(r['requested_as_of_at']))
    if len(sources)!=len(reps):raise ValueError('Every prefix needs its own preserved source snapshot')
    values=[];manifests=[]
    for rep,source in zip(reps,sources):
        if source_has_target(source,candidate,fixture):raise ValueError('Known target attendance in preserved source archive')
        row={**feature_record(candidate,rep,original_runtime),'ticket_event_id':candidate['ticket_event_id'],
             'as_of_at':rep['requested_as_of_at']}
        x,manifest=feature_row(row,fixture,source,historical_reconstruction=False)
        values.append(x);manifests.append(manifest)
    x=pd.DataFrame(values);x['prior_p50']=float(candidate['prior']['p50']);x['stadium_capacity']=float(candidate['prior']['stadium_capacity'])
    times=[stamp(r['requested_as_of_at']) for r in reps]
    elapsed=np.array([(t-times[0]).total_seconds()/3600 for t in times])
    result={}
    for name,model in models.items():
        raw=model.predict_live_p50(x)
        policy=apply_v8_policy(prior_p50=float(candidate['prior']['p50']),stadium_capacity=float(candidate['prior']['stadium_capacity']),
                               live_history_p50=raw,elapsed_hours=elapsed)
        result[name]={'raw':float(raw[-1]),'policy':float(policy['policy_prediction']),
                      'live_history_p50':[float(v) for v in raw],'policy_decision':policy}
    return result,manifests


def forecasts(upstream,decision):
    result={k:float(upstream['forecasts'][k]) for k in PREDICTIONS if k not in ('control_raw','control_policy','history_raw','history_policy')}
    for head in ('control','history'):
        for kind in ('raw','policy'):result[head+'_'+kind]=decision[head][kind]
    if set(result)!=set(PREDICTIONS) or not np.isfinite(list(result.values())).all():raise ValueError('Paired forecast schema differs')
    return result


def validate_timing(row,candidate,fixture,manifest,now):
    asof,issued,kickoff=map(stamp,[row['as_of_at'],row['issued_at'],row['kickoff_at']])
    if (row.get('version')!=VERSION or row.get('package_version')!=PACKAGE
            or row.get('manifest_sha256')!=manifest['_verified_manifest_sha256']
            or row.get('precommit_sha256')!=manifest['precommit_sha256']
            or row.get('production_change') is not False or row.get('live_adjustment')!=0
            or row.get('known_outcome_at_capture') is not False or row['ticket_event_id'] in TRAIN_IDS
            or fixture_unit(fixture) in manifest['training_fixture_unit_hashes']
            or not stamp(manifest['frozen_at'])<=asof<=issued<kickoff or issued>stamp(now)
            or row['ticket_event_id']!=candidate['ticket_event_id'] or stamp(fixture['kickoff_at'])!=kickoff):
        raise ValueError('Invalid new prospective identity/clock or exposed training fixture')
    validate_current(candidate,row['input_requested_at'],issued,manifest['frozen_at'],set())


def capture_one(runtime,upstream,source_candidate,fixture,manifest,models,bench_bundle,archive,now,clock=None):
    old_manifest,benchmarks,hashes=bench_bundle
    if source_candidate['ticket_event_id']!=fixture['id'] or stamp(source_candidate['kickoff_at'])!=stamp(fixture['kickoff_at']):
        raise ValueError('Canonical candidate fixture differs')
    if fixture_unit(fixture) in manifest['training_fixture_unit_hashes']:raise ValueError('Canonical training aliases excluded')
    validate_current(source_candidate,upstream['input_requested_at'],now,manifest['frozen_at'],set())
    verify_benchmark_rows([upstream],[],[fixture],old_manifest,hashes,now,models=benchmarks,
        source_inputs={upstream['candidate_input_sha256']:source_candidate})
    candidate_sha=put_blob(runtime,'inputs',source_candidate)
    upstream_sha=put_blob(runtime,'upstream',upstream)
    sources=[];source_shas=[]
    for rep in sorted(source_candidate['representatives'],key=lambda r:stamp(r['requested_as_of_at'])):
        selected=select_snapshot(archive,rep['requested_as_of_at'],now=stamp(now).to_pydatetime())
        if selected['source'] is None:raise ValueError('No genuine pre-observation source archive; no reconstruction')
        source=selected['source'];source_shas.append(put_blob(runtime,'sources',source));sources.append(source)
    result,feature_manifests=decisions(source_candidate,fixture,sources,models,benchmarks['original9'])
    issued=stamp(clock() if clock else datetime.now(timezone.utc))
    if issued<stamp(upstream['issued_at']) or issued<stamp(now):raise ValueError('New issue cannot precede original issue or actual computation')
    evidence={'version':VERSION,'package_version':PACKAGE,'ticket_event_id':source_candidate['ticket_event_id'],
        'source_snapshot_id':upstream['source_snapshot_id'],'as_of_at':upstream['as_of_at'],'kickoff_at':upstream['kickoff_at'],
        'issued_at':issued.isoformat(),'upstream_issued_at':upstream['issued_at'],'input_requested_at':upstream['input_requested_at'],
        'candidate_blob_sha256':candidate_sha,'upstream_blob_sha256':upstream_sha,'source_blob_sha256':source_shas,
        'manifest_sha256':manifest['_verified_manifest_sha256'],'precommit_sha256':manifest['precommit_sha256'],
        'feature_manifests':feature_manifests,'decisions':result,'forecasts':forecasts(upstream,result),
        'known_outcome_at_capture':False,'production_change':False,'live_adjustment':0}
    validate_timing(evidence,source_candidate,fixture,manifest,issued)
    return immutable_save(runtime/'evidence',evidence)


def score_rows(runtime,evidence,outcomes,metadata,manifest,models,bench_bundle,now):
    old_manifest,benchmarks,hashes=bench_bundle
    truth={r['ticket_event_id']:r for r in outcomes};meta={r['id']:r for r in metadata}
    if len(truth)!=len(outcomes) or len(meta)!=len(metadata):raise ValueError('Duplicate outcome/canonical identities')
    seen=set();units={};scores=[];missing=set()
    for row in evidence:
        event=row['ticket_event_id'];key=(event,row['source_snapshot_id'])
        if key in seen:raise ValueError('Duplicate new evidence identity')
        seen.add(key)
        candidate=get_blob(runtime,'inputs',row['candidate_blob_sha256'])
        old=get_blob(runtime,'upstream',row['upstream_blob_sha256'])
        fixture=meta[event];validate_timing(row,candidate,fixture,manifest,now)
        unit=fixture_unit(fixture)
        if unit in units and units[unit]!=event:raise ValueError('Different IDs share one canonical fixture')
        units[unit]=event
        if (row['upstream_issued_at']!=old['issued_at'] or stamp(row['issued_at'])<stamp(old['issued_at'])
                or row['source_snapshot_id']!=old['source_snapshot_id'] or row['as_of_at']!=old['as_of_at']):
            raise ValueError('Original observation or actual issue was substituted')
        old_scores,_,_=verify_benchmark_rows([old],outcomes,metadata,old_manifest,hashes,now,models=benchmarks,
            source_inputs={old['candidate_input_sha256']:candidate})
        source=[get_blob(runtime,'sources',sha) for sha in row['source_blob_sha256']]
        result,manifests=decisions(candidate,fixture,source,models,benchmarks['original9'])
        if row['decisions']!=result or row['feature_manifests']!=manifests or row['forecasts']!=forecasts(old,result):
            raise ValueError('Complete new decisions/input/source replay differs')
        label=truth.get(event)
        if label is None:missing.add(event);continue
        if len(old_scores)!=1:raise ValueError('Paired benchmark outcome was not validated')
        known=min(stamp(label['created_at']),stamp(label['confirmed_at']))
        if (not stamp(row['issued_at'])<known or stamp(label['updated_at'])>stamp(now)
                or stamp(label['updated_at'])<stamp(label['created_at'])):
            raise ValueError('Attendance was known before new actual issue or has future revision')
        actual=old_scores[0]['actual_attendance'];values=row['forecasts']
        scores.append({'ticket_event_id':event,'source_snapshot_id':row['source_snapshot_id'],'as_of_at':row['as_of_at'],
            'issued_at':row['issued_at'],'kickoff_at':row['kickoff_at'],'club_slug':canonical_club(fixture['club_slug']),
            'capture_sha256':digest(encode(row)),'actual_attendance':actual,'confirmed_at':label['confirmed_at'],
            'label_created_at':label['created_at'],'label_updated_at':label['updated_at'],
            'source_name':label['source_name'],'source_url':label['source_url'],
            'forecasts':values,'absolute_errors':{k:abs(v-actual) for k,v in values.items()},
            'signed_errors':{k:v-actual for k,v in values.items()}})
    return scores,sorted(missing)


def summarize(scores,missing,captured_events):
    groups={}
    for row in scores:groups.setdefault(row['ticket_event_id'],[]).append(row)
    latest=[max(v,key=lambda r:stamp(r['as_of_at'])) for v in groups.values()]
    clubs=len({r['club_slug'] for r in latest});ready=len(latest)>=30 and clubs>=8
    mean=lambda x:float(np.mean(x)) if len(x) else None
    metrics={}
    for name in PREDICTIONS:
        ae=[r['absolute_errors'][name] for r in latest]
        metrics[name]={'latest_row_mae':mean(ae),
            'event_balanced_window_mae':mean([mean([r['absolute_errors'][name] for r in v]) for v in groups.values()]),
            'signed_bias':mean([r['signed_errors'][name] for r in latest]),
            'p90_absolute_error':float(np.quantile(ae,.9)) if ae else None,'worst_absolute_error':max(ae) if ae else None}
    def pair(a,b):
        delta=np.array([r['absolute_errors'][a]-r['absolute_errors'][b] for r in latest]);ci=None
        if ready:
            rng=np.random.default_rng(42);draws=rng.choice(delta,size=(10000,len(delta)),replace=True).mean(axis=1)
            ci=np.quantile(draws,[.025,.975]).tolist()
        return {'delta_mae':mean(delta),'median_event_delta_ae':float(np.median(delta)) if len(delta) else None,
            'event_improvement_rate':mean((delta<0).astype(float)),
            'worst_event_degradation':max(0.,float(delta.max())) if len(delta) else None,
            'paired_event_bootstrap_95_interval':ci,'gate_met':bool(ready and delta.mean()<0 and ci[1]<0)}
    primary=pair('history_raw','control_raw');product={name:pair('history_policy',name) for name in PRODUCT_BASELINES}
    def grouped_metrics(selected):
        by={}
        for row in selected:by.setdefault(row['ticket_event_id'],[]).append(row)
        return {'events':len(by),'rows':len(selected),'event_balanced_window_mae':{
            name:mean([mean([r['absolute_errors'][name] for r in rows]) for rows in by.values()]) for name in PREDICTIONS}}
    by_club={club:grouped_metrics([r for r in scores if r['club_slug']==club]) for club in sorted({r['club_slug'] for r in scores})}
    horizon=lambda row:'0_to_6h' if (stamp(row['kickoff_at'])-stamp(row['as_of_at'])).total_seconds()<=21600 else '6_to_12h' if (stamp(row['kickoff_at'])-stamp(row['as_of_at'])).total_seconds()<=43200 else '12_to_24h'
    by_horizon={name:grouped_metrics([r for r in scores if horizon(r)==name]) for name in ('0_to_6h','6_to_12h','12_to_24h')}
    return {'package_version':PACKAGE,'by_club':by_club,'by_horizon':by_horizon,'scored_events':len(latest),'clubs':clubs,'captured_events':captured_events,
        'missing_outcomes':missing,'metrics':metrics,'primary':primary,'product_comparisons':product,
        'review_ready':ready,'information_gate_met':primary['gate_met'],
        'product_gate_met':bool(ready and all(v['gate_met'] for v in product.values())),
        'status':'REVIEW_READY' if ready else 'PROSPECTIVE_COLLECTING','production_change':False,'live_adjustment':0}


class Storage(PrivateResearchStorage):
    @staticmethod
    def _key(key):
        if not re.fullmatch(r'c1-history-residual-v1/[0-9a-f]{64}\.json',key):raise ValueError('Wrong history residual recovery namespace')
        return key


def backup(runtime):
    files=[p for p in runtime.rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl') and p.name!='latest-cycle.json']
    if len(files)>5000:raise ValueError('Bounded backup file limit exceeded')
    data=encode({'version':VERSION,'files':[{'name':str(p.relative_to(runtime)),'sha256':digest(p.read_bytes()),
        'base64':base64.b64encode(p.read_bytes()).decode()} for p in sorted(files)]})
    if len(data)>32*1024*1024:raise ValueError('Bounded recovery payload exceeded')
    raw=encode({'version':VERSION,'encoding':'zlib+base64','payload_sha256':digest(data),
                'payload':base64.b64encode(zlib.compress(data)).decode()})
    storage=Storage();storage.ensure_private_bucket();receipt=storage.put_verified('c1-history-residual-v1/'+digest(raw)+'.json',raw,'application/json')
    restored=json.loads(storage.read(receipt['key']));payload=zlib.decompress(base64.b64decode(restored['payload']))
    if digest(payload)!=restored['payload_sha256']:raise ValueError('Private decompression checksum differs')
    for entry in json.loads(payload)['files']:
        if digest(base64.b64decode(entry['base64']))!=entry['sha256']:raise ValueError('Private restored file differs')
    return {**receipt,'files':len(files),'independent_remote_decompression_verified':True}


def run_cycle(runtime,support_runtime,archive,bundle=None):
    manifest,models,bench_bundle=load_models()
    if bundle is not None and bundle[0]['_verified_manifest_sha256']!=manifest['_verified_manifest_sha256']:
        raise ValueError('The watcher freeze identity changed')
    ensure_runtime(runtime,manifest)
    with (runtime/'cycle.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Another history cycle is running') from None
        now=datetime.now(timezone.utc);reader=Reader()
        outcomes=reader.request('ticket_event_outcomes?select=*&limit=1001')
        metadata=reader.request('ticket_events?select=id,club_slug,kickoff_at&limit=1001')
        if len(outcomes)>=1000 or len(metadata)>=1000:raise ValueError('Unpaginated source expanded')
        labelled={r['ticket_event_id'] for r in outcomes};meta={r['id']:r for r in metadata}
        if len(meta)!=len(metadata):raise ValueError('Duplicate canonical metadata')
        attempts=[]
        for path in sorted((support_runtime/'evidence').glob('*.json')):
            old=json.loads(path.read_text());event=old['ticket_event_id']
            target=runtime/'evidence'/path.name
            if target.exists() or event in labelled or stamp(old['as_of_at'])<stamp(manifest['frozen_at']):continue
            if stamp(now)-stamp(old['input_requested_at'])>pd.Timedelta(minutes=15):continue
            try:
                candidate=json.loads((support_runtime/'inputs'/('candidate-'+old['candidate_input_sha256']+'.json')).read_text())
                result=capture_one(runtime,old,candidate,meta[event],manifest,models,bench_bundle,archive,now)
                attempts.append({'ticket_event_id':event,**result})
            except (ValueError,KeyError,RuntimeError,TypeError) as exc:
                attempts.append({'ticket_event_id':event,'status':'FAILED_CLOSED','reason':str(exc)[:200]})
        captured=[json.loads(p.read_text()) for p in sorted((runtime/'evidence').glob('*.json'))]
        scores,missing=score_rows(runtime,captured,outcomes,metadata,manifest,models,bench_bundle,datetime.now(timezone.utc))
        for row in scores:persist_score(runtime/'scores',row)
        report=summarize(scores,missing,len({r['ticket_event_id'] for r in captured}))
        write_json(runtime/'current-report.json',report)
        if report['review_ready'] and not (runtime/'first-review.json').exists():write_json(runtime/'first-review.json',report,True)
        with (runtime/'attempts.jsonl').open('a') as f:f.write(json.dumps({'checked_at':now.isoformat(),'attempts':attempts})+'\n')
        receipt=backup(runtime)
        if load_models()[0]['_verified_manifest_sha256']!=manifest['_verified_manifest_sha256']:
            raise ValueError('The freeze changed during the cycle')
        result={'status':'CYCLE_VERIFIED','checked_at':datetime.now(timezone.utc).isoformat(),'package_version':PACKAGE,
            'new_predictions':sum(r['status']=='CAPTURED_IMMUTABLE' for r in attempts),'scored_events':report['scored_events'],
            'history_policy_mae':report['metrics']['history_policy']['latest_row_mae'],'private_backup':receipt,
            'host_dependent':True,'production_change':False,'live_adjustment':0}
        write_json(runtime/'latest-cycle.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['cycle','watch'])
    p.add_argument('--runtime',type=Path,required=True);p.add_argument('--support-runtime',type=Path,required=True)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--until');p.add_argument('--interval',type=int,default=900)
    a=p.parse_args();bundle=load_models();ensure_runtime(a.runtime,bundle[0])
    if a.action=='cycle':print(json.dumps(run_cycle(a.runtime,a.support_runtime,a.archive,bundle)));return
    now=stamp(datetime.now(timezone.utc));until=stamp(a.until)
    if not now<until<=now+pd.Timedelta(hours=72) or not 60<=a.interval<=3600:raise ValueError('Bounded watch deadline/interval required')
    with (a.runtime/'watcher.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Another history watcher is running') from None
        write_json(a.runtime/'watcher-launch.json',{'pid':os.getpid(),'started_at':now.isoformat(),
            'until':until.isoformat(),'interval_seconds':a.interval,'host_dependent':True,'production_change':False})
        while stamp(datetime.now(timezone.utc))<until:
            try:print(json.dumps(run_cycle(a.runtime,a.support_runtime,a.archive,bundle)),flush=True)
            except Exception as exc:
                write_json(a.runtime/'latest-cycle.json',{'status':'FAILED_CLOSED','checked_at':datetime.now(timezone.utc).isoformat(),
                    'error_type':type(exc).__name__,'reason':str(exc)[:200],'production_change':False})
            remaining=(until-stamp(datetime.now(timezone.utc))).total_seconds()
            if remaining>0:time.sleep(min(a.interval,remaining))


if __name__=='__main__':main()
