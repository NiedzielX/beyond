"""Private bounded capture/scoring for the new fixed structural-source contract."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import re
import time
import zlib

import pandas as pd

from ml.c1_support26_v1 import load_models as benchmark_models, score_rows as verify_benchmarks
from ml.c1_training_expansion_capture_v1 import validate_current
from ml.demand_engine.daily_inventory_path_storage_v1 import PrivateResearchStorage, encode, digest as hash_bytes
from ml.export_c1_matched_audit_inputs_v1 import Reader
from ml.export_structural_known_at_inputs_v1 import validate_envelope
from ml.select_structural_known_at_snapshot_v1 import select_snapshot
from ml.structural_history_refresh_v1 import (
    ROOT, PACKAGE, ARTIFACT, BASELINES, TRAIN_IDS, fixture_unit, canonical_club,
    stamp, predict, freeze, load_manifest, summary,
)


def save(path, value, exclusive=False):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w') as file:
        json.dump(value, file, indent=2, sort_keys=True, allow_nan=False); file.write('\n')


def ensure_runtime(runtime, manifest):
    if runtime.resolve().is_relative_to(ROOT): raise ValueError('Evidence must remain private outside Git')
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    expected = {'package_version': PACKAGE, 'manifest_sha256': manifest['_manifest_sha256']}
    marker = runtime/'experiment.json'
    if marker.exists():
        if json.loads(marker.read_text()) != expected: raise ValueError('Different experiment owns runtime')
    else:
        if any(runtime.iterdir()): raise ValueError('Nonempty unmarked runtime')
        save(marker, expected, True)


def blob(runtime, payload):
    raw = encode(payload); sha = hash_bytes(raw); path = runtime/'blobs'/(sha+'.json')
    path.parent.mkdir(mode=0o700, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw: raise ValueError('Immutable input blob conflict')
    else:
        with path.open('xb') as file: file.write(raw)
        path.chmod(0o440)
    return sha


def read_blob(runtime, sha):
    if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha): raise ValueError('Invalid source key')
    raw = (runtime/'blobs'/(sha+'.json')).read_bytes()
    if hash_bytes(raw) != sha: raise ValueError('Source blob changed')
    return json.loads(raw)


def resolve_prior(support, upstream, candidate):
    for path in sorted((support/'inputs').glob('collector-*.json')):
        envelope = json.loads(path.read_text())
        if stamp(envelope['original']['requested_at']) != stamp(upstream['input_requested_at']): continue
        if hash_bytes(encode(envelope)) != path.stem.removeprefix('collector-'): raise ValueError('Collector source hash changed')
        matching = [c for c in envelope['enriched']['candidates'] if hash_bytes(encode(c)) == upstream['candidate_input_sha256']]
        if len(matching) != 1 or matching[0] != candidate: raise ValueError('Exact original candidate resolution missing')
        rows = [r for r in envelope['resolutions'] if r['ticket_event_id'] == upstream['ticket_event_id']]
        if len(rows) != 1 or len(rows[0]['prior']) != 1: raise ValueError('One original anchor resolution required')
        return rows[0]['prior'][0]
    raise ValueError('No original contemporaneous prior resolution')


def fixture(candidate):
    return {'id': candidate['ticket_event_id'], 'club_slug': candidate['club_slug'], 'kickoff_at': candidate['kickoff_at']}


def verify_upstream(upstream, candidate, bundle, now, outcomes=(), metadata=None):
    manifest, models, hashes = bundle
    return verify_benchmarks([upstream], list(outcomes), metadata or [fixture(candidate)], manifest, hashes, now,
        models=models, source_inputs={upstream['candidate_input_sha256']: candidate})


def capture_one(runtime, old, candidate, resolved, source, manifest, bundle, now, clock=None):
    asof = stamp(old['as_of_at']); event = fixture(candidate)
    if (old['ticket_event_id'] in TRAIN_IDS or fixture_unit(event) in manifest['training_fixture_unit_hashes']
            or asof < stamp(manifest['frozen_at'])):
        raise ValueError('Exposed or pre-activation fixture/source')
    for path in (runtime/'evidence').glob('*.json'):
        existing = json.loads(path.read_text())
        if existing['fixture_unit'] == fixture_unit(event) and existing['ticket_event_id'] != old['ticket_event_id']:
            raise ValueError('Canonical future fixture alias collision')
    validate_current(candidate, old['input_requested_at'], now, manifest['frozen_at'], set())
    verify_upstream(old, candidate, bundle, now)
    result = predict(candidate, resolved, source, asof, now)
    inputs = {'candidate': candidate, 'benchmark': old, 'resolved': resolved, 'source': source}
    source_key = blob(runtime, inputs)
    issued = stamp(clock() if clock else datetime.now(timezone.utc))
    if not stamp(now) <= issued < stamp(candidate['kickoff_at']) or issued < stamp(old['issued_at']):
        raise ValueError('Actual new issue must follow inference/benchmark and precede kickoff')
    forecasts = {'fresh': result['p50'], **{name: old['forecasts'][name] for name in BASELINES}}
    row = {'version': 'structural-history-refresh-evidence-v1', 'package_version': PACKAGE,
        'ticket_event_id': old['ticket_event_id'], 'fixture_unit': fixture_unit(event),
        'club_slug': canonical_club(candidate['club_slug']), 'source_snapshot_id': old['source_snapshot_id'],
        'as_of_at': asof.isoformat(), 'issued_at': issued.isoformat(), 'upstream_issued_at': old['issued_at'],
        'input_requested_at': old['input_requested_at'], 'kickoff_at': candidate['kickoff_at'],
        'manifest_sha256': manifest['_manifest_sha256'], 'input_blob_sha256': source_key,
        'decision': result, 'forecasts': forecasts, 'known_outcome_at_capture': False,
        'official_persistence_allowed': False, 'production_change': False, 'live_adjustment': 0}
    path = runtime/'evidence'/f"event-{row['ticket_event_id']}-snapshot-{row['source_snapshot_id']}.json"
    save(path, row, True); path.chmod(0o440); return row


def validate_row(runtime, row, manifest, bundle, now):
    if (row.get('version') != 'structural-history-refresh-evidence-v1' or row.get('package_version') != PACKAGE
            or row.get('manifest_sha256') != manifest['_manifest_sha256'] or row.get('production_change') is not False
            or row.get('live_adjustment') != 0 or row.get('official_persistence_allowed') is not False
            or row.get('known_outcome_at_capture') is not False or row['ticket_event_id'] in TRAIN_IDS):
        raise ValueError('Invalid immutable fresh evidence contract')
    asof, issued, kickoff = map(stamp, [row['as_of_at'],row['issued_at'],row['kickoff_at']])
    if not stamp(manifest['frozen_at']) <= asof <= issued < kickoff or issued > stamp(now):
        raise ValueError('New actual forecast clock invalid')
    stored = read_blob(runtime,row['input_blob_sha256']); candidate = stored['candidate']; old = stored['benchmark']
    if (row['ticket_event_id'] != old['ticket_event_id'] or row['source_snapshot_id'] != old['source_snapshot_id']
            or asof != stamp(old['as_of_at']) or row['fixture_unit'] != fixture_unit(fixture(candidate))
            or row['fixture_unit'] in manifest['training_fixture_unit_hashes']
            or kickoff != stamp(candidate['kickoff_at']) or stamp(row['upstream_issued_at']) != stamp(old['issued_at'])
            or issued < stamp(old['issued_at']) or stamp(row['input_requested_at']) != stamp(old['input_requested_at'])):
        raise ValueError('Source, fixture or benchmark clocks substituted')
    validate_current(candidate,row['input_requested_at'],issued,manifest['frozen_at'],set())
    verify_upstream(old,candidate,bundle,issued)
    replay = predict(candidate,stored['resolved'],stored['source'],asof,issued)
    expected = {'fresh':replay['p50'], **{name:old['forecasts'][name] for name in BASELINES}}
    if replay != row['decision'] or expected != row['forecasts']:
        raise ValueError('Frozen new predictor/benchmark replay differs')
    return stored


def score_one(runtime, row, manifest, bundle, outcomes, metadata, now):
    stored = validate_row(runtime,row,manifest,bundle,now)
    labels = [r for r in outcomes if r['ticket_event_id'] == row['ticket_event_id']]
    if not labels: return None
    if len(labels) != 1: raise ValueError('Duplicate outcome identity')
    truth = labels[0]; issued = stamp(row['issued_at']); kickoff = stamp(row['kickoff_at'])
    if (not issued < kickoff <= stamp(truth['confirmed_at']) <= stamp(now)
            or stamp(truth['created_at']) <= issued or stamp(truth['created_at']) > stamp(now)
            or stamp(truth['updated_at']) < stamp(truth['created_at']) or stamp(truth['updated_at']) > stamp(now)):
        raise ValueError('Outcome early/unknown/revised clock invalid')
    scores, _, _ = verify_upstream(stored['benchmark'],stored['candidate'],bundle,now,outcomes,metadata)
    if len(scores) != 1 or scores[0]['actual_attendance'] != truth['actual_attendance']:
        raise ValueError('Genuine paired benchmark truth not verified')
    actual = float(truth['actual_attendance'])
    if not 0 < actual <= float(stored['resolved']['stadium_capacity']): raise ValueError('Invalid attendance/capacity')
    signed = {name:float(value)-actual for name,value in row['forecasts'].items()}
    result = {'package_version':PACKAGE,'ticket_event_id':row['ticket_event_id'],'fixture_unit':row['fixture_unit'],
        'club_slug':row['club_slug'],'as_of_at':row['as_of_at'],'issued_at':row['issued_at'],
        'kickoff_at':row['kickoff_at'],'source_snapshot_id':row['source_snapshot_id'],
        'capture_sha256':hash_bytes(encode(row)),'outcome_sha256':hash_bytes(encode(truth)),
        'actual_attendance':actual,'confirmed_at':truth['confirmed_at'],
        'later_known_record_count':row['decision']['later_known_record_count'],
        'signed_errors':signed,'absolute_errors':{k:abs(v) for k,v in signed.items()},
        'scored_at':stamp(now).isoformat(),'production_change':False,'live_adjustment':0}
    path=runtime/'scores'/f"event-{row['ticket_event_id']}-snapshot-{row['source_snapshot_id']}.json"
    if path.exists():
        existing=json.loads(path.read_text())
        if {k:v for k,v in existing.items() if k!='scored_at'}!={k:v for k,v in result.items() if k!='scored_at'}:
            raise ValueError('Outcome revision/immutable score conflict')
        return existing
    save(path,result,True);path.chmod(0o440);return result


class Storage(PrivateResearchStorage):
    @staticmethod
    def _key(key):
        if not re.fullmatch(r'structural-history-refresh-v1/[0-9a-f]{64}\.json',key): raise ValueError('Wrong private namespace')
        return key


def backup(runtime, storage=None):
    files=[p for folder in ('blobs','evidence','scores') for p in (runtime/folder).glob('*.json')]
    files += [runtime/'experiment.json',ARTIFACT/'manifest.json']
    if len(files) > 10000: raise ValueError('Bounded private evidence source expanded')
    body=encode({'package_version':PACKAGE,'files':[{'name':str(p.relative_to(runtime)) if p.is_relative_to(runtime) else 'artifact-manifest.json',
        'sha256':hash_bytes(p.read_bytes()),'base64':base64.b64encode(p.read_bytes()).decode()} for p in sorted(files)]})
    raw=encode({'encoding':'zlib+base64','payload_sha256':hash_bytes(body),'payload':base64.b64encode(zlib.compress(body)).decode()});key='structural-history-refresh-v1/'+hash_bytes(raw)+'.json'
    old=runtime/'private-backup.json'
    if old.exists() and json.loads(old.read_text()).get('key')==key:return json.loads(old.read_text())
    if len(raw) > 10*1024*1024: raise ValueError('Bounded private recovery object expanded')
    s=storage or Storage();s.ensure_private_bucket();receipt=s.put_verified(key,raw,'application/json')
    remote=s.read(key)
    if remote != raw: raise ValueError('Remote recovery bytes changed')
    env=json.loads(remote);restored=zlib.decompress(base64.b64decode(env['payload']))
    if remote!=raw or hash_bytes(restored)!=env['payload_sha256']: raise ValueError('Remote recovery differs')
    parts=json.loads(restored)['files']
    if any(hash_bytes(base64.b64decode(p['base64']))!=p['sha256'] for p in parts): raise ValueError('Recovery file hash differs')
    receipt.update(files=len(parts),independent_remote_decompression_verified=True);save(old,receipt);return receipt


def cycle(runtime,support,archive):
    manifest=load_manifest();ensure_runtime(runtime,manifest);bundle=benchmark_models()
    with (runtime/'cycle.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);now=datetime.now(timezone.utc);attempts=[]
        for path in sorted((support/'evidence').glob('*.json')):
            old=json.loads(path.read_text());target=runtime/'evidence'/path.name
            if target.exists() or stamp(old['as_of_at'])<stamp(manifest['frozen_at']) or stamp(now)-stamp(old['input_requested_at'])>pd.Timedelta(minutes=15):continue
            try:
                candidate=json.loads((support/'inputs'/('candidate-'+old['candidate_input_sha256']+'.json')).read_text())
                if hash_bytes(encode(candidate))!=old['candidate_input_sha256']:raise ValueError('Original input changed')
                resolved=resolve_prior(support,old,candidate);source=select_snapshot(archive,old['as_of_at'],now=now)['source']
                if source is None:raise ValueError('No genuine pre-observation archive')
                row=capture_one(runtime,old,candidate,resolved,source,manifest,bundle,now)
                attempts.append({'ticket_event_id':row['ticket_event_id'],'status':'CAPTURED_IMMUTABLE','issued_at':row['issued_at']})
            except (ValueError,KeyError,RuntimeError,TypeError) as exc:
                attempts.append({'ticket_event_id':old['ticket_event_id'],'status':'FAILED_CLOSED','reason':str(exc)[:180]})
        rows=[json.loads(p.read_text()) for p in sorted((runtime/'evidence').glob('*.json'))]
        outcomes=[];metadata=[]
        if any(stamp(row['kickoff_at'])<stamp(now) for row in rows):
            reader=Reader();outcomes=reader.request('ticket_event_outcomes?select=*&limit=1001');metadata=reader.request('ticket_events?select=id,club_slug,kickoff_at&limit=1001')
            if len(outcomes)>=1000 or len(metadata)>=1000:raise ValueError('Bounded outcome source expanded')
        scores=[];missing=[]
        for row in rows:
            score=score_one(runtime,row,manifest,bundle,outcomes,metadata,now)
            if score is None:missing.append(row['ticket_event_id'])
            else:scores.append(score)
        report=summary(scores,len({r['fixture_unit'] for r in rows}),sorted(set(missing)));save(runtime/'report.json',report)
        if report['review_ready'] and not (runtime/'first-review.json').exists():save(runtime/'first-review.json',report,True)
        receipt=backup(runtime)
        if load_manifest()['_manifest_sha256']!=manifest['_manifest_sha256']:raise ValueError('Freeze changed midcycle')
        result={'status':'CYCLE_VERIFIED','checked_at':datetime.now(timezone.utc).isoformat(),
            'new_predictions':len([a for a in attempts if a['status']=='CAPTURED_IMMUTABLE']),
            'captured_events':report['captured_events'],'scored_events':report['scored_events'],
            'fresh_mae':report['metrics']['fresh']['latest_per_event_mae'],'attempts':attempts,
            'private_backup':receipt,'production_change':False,'live_adjustment':0}
        with (runtime/'attempts.jsonl').open('a') as file:file.write(json.dumps(result)+'\n')
        save(runtime/'latest-cycle.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','check','cycle','watch'])
    p.add_argument('--published-commit');p.add_argument('--runtime',type=Path)
    p.add_argument('--support',type=Path,default=Path('/workspace/ops-runtime/2026-11-05-c1-support26-collector'))
    p.add_argument('--archive',type=Path,default=Path('/workspace/ops-runtime/2026-11-04-known-at-source-archive'))
    p.add_argument('--until');p.add_argument('--interval',type=int,default=900);a=p.parse_args()
    if a.action=='freeze':print(json.dumps(freeze(published_commit=a.published_commit)));return
    manifest=load_manifest()
    if a.action=='check':print(json.dumps({'status':'FROZEN_INFERENCE_IDENTITIES_VERIFIED','package_version':PACKAGE,'fits':0}));return
    if a.runtime is None:p.error('--runtime required')
    ensure_runtime(a.runtime,manifest)
    if a.action=='cycle':print(json.dumps(cycle(a.runtime,a.support,a.archive)));return
    now=stamp(datetime.now(timezone.utc));until=stamp(a.until)
    if not now<until<=now+pd.Timedelta(hours=72) or not 60<=a.interval<=1800:raise ValueError('Bounded72hourdeadline/cadence required')
    with (a.runtime/'watcher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);save(a.runtime/'watcher-launch.json',{'pid':__import__('os').getpid(),'started_at':now.isoformat(),'until':until.isoformat(),'interval_seconds':a.interval,'host_dependent':True,'production_change':False,'live_adjustment':0})
        while stamp(datetime.now(timezone.utc))<until:
            try:result=cycle(a.runtime,a.support,a.archive)
            except Exception as exc:result={'status':'FAILED_CLOSED','checked_at':datetime.now(timezone.utc).isoformat(),'error_type':type(exc).__name__,'production_change':False,'live_adjustment':0};save(a.runtime/'latest-cycle.json',result)
            print(json.dumps(result),flush=True);time.sleep(min(a.interval,max(0,(until-stamp(datetime.now(timezone.utc))).total_seconds())))


if __name__=='__main__':main()
