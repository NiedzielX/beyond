"""Bounded three-opportunity outcome acquisition; private, append-only and no fits."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from ml.postmatch_outcome_source_v1 import SOURCES, TARGETS, recover, stage, stamp

ROOT=Path(__file__).resolve().parents[1]
BASE='https://api.github.com/repos/NiedzielX/beyond'
WORKFLOW='ml-research-readiness-contract-v1.yml'
SLOTS=('2026-11-06T20:20:00Z','2026-11-06T23:20:00Z','2026-11-07T08:20:00Z')
UNTIL='2026-11-07T10:30:00Z'
SOURCE_FILES=('ml/postmatch_outcome_source_v1.py','ml/run_postmatch_outcome_closure_v1.py',
              'ml/public_attendance_source_audit_v1.py','ml/current_home_history_source_audit_v1.py',
              'ml/verified_attendance_source_rows_v1.py',
              '.github/workflows/ml-research-readiness-contract-v1.yml')


def save(path,value):
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    with tmp.open('w') as file:json.dump(value,file,indent=2,sort_keys=True,allow_nan=False);file.write('\n');file.flush();os.fsync(file.fileno())
    os.replace(tmp,path)


def api(path,body=None):
    req=urllib.request.Request(BASE+path,data=None if body is None else json.dumps(body).encode(),
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response:
        raw=response.read(8*1024*1024+1)
        if len(raw)>8*1024*1024:raise ValueError('Bounded GitHub response expanded')
        return json.loads(raw) if raw else {'http_status':response.status}


def contract(branch,commit):
    return {'version':'postmatch-outcome-closure-v1','branch':branch,'commit':commit,
        'slots':list(SLOTS),'until':UNTIL,'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCE_FILES},
        'production_change':False,'live_adjustment':0}


def due_slot(now,state):
    for slot in SLOTS:
        if slot not in state.get('dispatches',{}) and stamp(slot)<=now<=stamp(slot)+timedelta(minutes=30):return slot
    return None


def dispatch(state,slot,branch,commit,now,persist,github=api):
    if (slot not in SLOTS or not stamp(slot)<=now<=stamp(slot)+timedelta(minutes=30)
            or slot in state.get('dispatches',{})):
        raise ValueError('No historical catchup or duplicate source dispatch')
    if github('/git/ref/heads/'+branch)['object']['sha']!=commit:raise ValueError('Published source branch moved')
    entry={'intent_at':now.isoformat(),'branch':branch,'commit':commit,'status':'DISPATCH_INTENT_RECORDED'}
    state.setdefault('dispatches',{})[slot]=entry;persist(state)
    receipt=github('/actions/workflows/'+WORKFLOW+'/dispatches',{'ref':branch,'inputs':{'postmatch_outcome_source_audit':True}})
    if receipt.get('http_status')!=204:raise ValueError('Expected workflow dispatch acceptance')
    entry.update(status='DISPATCH_ACCEPTED',accepted_at=datetime.now(timezone.utc).isoformat());persist(state)
    return entry


def find_run(entry,github=api):
    import urllib.parse
    values=github('/actions/workflows/'+WORKFLOW+'/runs?branch='+urllib.parse.quote(entry['branch'],safe='')+'&event=workflow_dispatch&per_page=30')
    runs=[r for r in values['workflow_runs'] if r['head_sha']==entry['commit']
          and stamp(entry['intent_at'])-timedelta(seconds=2)<=stamp(r['created_at'])<=stamp(entry['intent_at'])+timedelta(minutes=5)]
    if len(runs)>1:raise ValueError('Ambiguous source dispatch run; no arbitrary selection')
    if not runs or runs[0]['status']!='completed':return None
    run=runs[0]
    if run['conclusion']!='success':raise ValueError('Source workflow failed; no import')
    checks=github('/check-suites/'+str(run['check_suite_id'])+'/check-runs?per_page=100')
    if checks['total_count']>100:raise ValueError('Source check-suite expanded')
    sources,raw=recover(checks['check_runs'],entry['commit'])
    return run,sources,raw


def read_sources(reader):
    from ml.export_structural_known_at_inputs_v1 import SourceReader
    r=reader or SourceReader()
    events=r.counted('ticket_events',[('id','in.(5091,448)')])
    history=r.counted('history',[('club_slug','in.(motorlublin,motor_lublin,wislakrakow,wisla_krakow)')])
    sporting=r.counted('sporting',[('season','eq.2026-2027'),('event_date','eq.2026-11-06')])
    outcomes=r.counted('outcomes',[('ticket_event_id','in.(5091,448)')])
    return r,events,history,sporting,outcomes


def apply_verified(runtime,run,sources,raw,reader=None):
    r,events,history,sporting,before=read_sources(reader)
    verified=datetime.now(timezone.utc).isoformat()
    result=stage(sources,raw,events,sporting,history,run_id=run['id'],verified_at=verified)
    for outcome in before:
        target=next(t for t in TARGETS if t['id']==outcome['ticket_event_id'])
        if not 0<outcome['actual_attendance']<=target['capacity'] or stamp(outcome['confirmed_at'])<stamp(target['kickoff_at']):raise ValueError('Existing target outcome invalid')
        if any(row['club_slug']==target['club_slug'] and row['actual_attendance']!=outcome['actual_attendance'] for row in result['verified_rows']):
            raise ValueError('Verified source conflicts with existing outcome')
    save(runtime/'stage.json',result)
    if result['rows']:
        rows=result['rows'];payload=json.dumps(rows,ensure_ascii=False,allow_nan=False).encode()
        intent={'requested_at':datetime.now(timezone.utc).isoformat(),'payload_sha256':hashlib.sha256(payload).hexdigest(),'rows':len(rows),'operation':'append_only_no_upsert'}
        # Persist intent; a failed response is never silently retried.
        save(runtime/'append-intent.json',intent)
        req=urllib.request.Request(r.base+'/rest/v1/ml_match_history',data=payload,method='POST',
            headers={**r.headers,'Content-Type':'application/json','Prefer':'return=representation'})
        with urllib.request.urlopen(req,timeout=45) as response:
            if response.status!=201:raise ValueError('Expected append-only creation')
            inserted=json.load(response)
        save(runtime/'append-receipt.json',inserted)
        if len(inserted)!=len(rows):raise ValueError('Append receipt row count differs')
        expected={row['external_match_key']:row for row in rows}
        for actual in inserted:
            planned=expected.pop(actual['external_match_key'])
            for k,v in planned.items():
                differs = stamp(actual[k])!=stamp(v) if k.endswith('_at') else actual[k]!=v
                if differs:raise ValueError('Append payload/readback differs')
            if stamp(actual['created_at'])<stamp(verified):raise ValueError('Database availability backdated')
        if expected:raise ValueError('Missing appended source identity')
        after=r.counted('history',[('club_slug','in.(motorlublin,motor_lublin,wislakrakow,wisla_krakow)')]);by_id={row['id']:row for row in after}
        if any(by_id.get(old['id'])!=old for old in history):raise ValueError('Existing history changed')
        # Counted history projection is narrower than the creation response.
        if any(any(by_id.get(row['id'],{}).get(k)!=v for k,v in row.items() if k in by_id.get(row['id'],{})) for row in inserted):raise ValueError('Actual append readback differs')
        for row in inserted:
            if row['id'] not in by_id:raise ValueError('Appended row missing in readback')
        result['appended_rows']=len(inserted)
    else:result['appended_rows']=0
    if any(s['status']=='EXACT_SOURCE_AND_RESULT_VERIFIED' for s in result['statuses']):
        result['outcome_sync_inserted']=r.request('rpc/sync_ticket_event_outcomes_from_home_history_v1',{})
    else:result['outcome_sync_inserted']=0
    outcomes=r.counted('outcomes',[('ticket_event_id','in.(5091,448)')])
    old={x['ticket_event_id']:x for x in before};after={x['ticket_event_id']:x for x in outcomes}
    if any(after.get(key)!=value for key,value in old.items()):raise ValueError('Original outcomes changed')
    result['actual_target_outcomes']=len(outcomes)
    save(runtime/'apply-result.json',result)
    return result


def backup_sources(runtime):
    import base64,re,zlib
    from ml.demand_engine.daily_inventory_path_storage_v1 import PrivateResearchStorage,encode,digest
    class Storage(PrivateResearchStorage):
        @staticmethod
        def _key(key):
            if not re.fullmatch(r'postmatch-outcome-closure-v1/[0-9a-f]{64}\.json',key):raise ValueError('Wrong private source namespace')
            return key
    files=[p for p in sorted(runtime.iterdir()) if p.is_file() and p.name!='private-backup.json']
    if len(files)>25:raise ValueError('Bounded postmatch audit expanded')
    body=encode({'files':[{'name':p.name,'sha256':digest(p.read_bytes()),'base64':base64.b64encode(p.read_bytes()).decode()} for p in files]})
    if len(body)>10*1024*1024:raise ValueError('Bounded source recovery expanded')
    raw=encode({'encoding':'zlib+base64','payload_sha256':digest(body),'payload':base64.b64encode(zlib.compress(body)).decode()})
    storage=Storage();storage.ensure_private_bucket();receipt=storage.put_verified('postmatch-outcome-closure-v1/'+digest(raw)+'.json',raw,'application/json')
    remote=storage.read(receipt['key'])
    if remote!=raw:raise ValueError('Private source recovery bytes changed')
    restored=zlib.decompress(base64.b64decode(json.loads(remote)['payload']))
    if digest(restored)!=digest(body) or any(digest(base64.b64decode(p['base64']))!=p['sha256'] for p in json.loads(restored)['files']):raise ValueError('Private source decompression differs')
    receipt.update(files=len(files),independent_remote_decompression_verified=True);save(runtime/'private-backup.json',receipt);return receipt


def score_support_only(runtime):
    from ml.c1_support26_v1 import load_models,score_rows,persist_score,summary,backup,ARTIFACT_DIR
    from ml.export_c1_matched_audit_inputs_v1 import Reader
    from ml.demand_engine.daily_inventory_path_storage_v1 import encode,digest
    with (runtime/'cycle.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'DELEGATED_TO_ACTIVE_FROZEN_COLLECTOR'}
        manifest,models,hashes=load_models();reader=Reader()
        outcomes=reader.request('ticket_event_outcomes?select=*&limit=1001');metadata=reader.request('ticket_events?select=id,club_slug,kickoff_at&limit=1001')
        if len(outcomes)>=1000 or len(metadata)>=1000:raise ValueError('Bounded outcome source expanded')
        rows=[json.loads(p.read_text()) for p in sorted((runtime/'evidence').glob('event-*.json'))];inputs={}
        for p in (runtime/'inputs').glob('candidate-*.json'):
            value=json.loads(p.read_text());sha=p.stem.removeprefix('candidate-')
            if digest(encode(value))!=sha:raise ValueError('Support input changed')
            inputs[sha]=value
        scores,missing,count=score_rows(rows,outcomes,metadata,manifest,hashes,datetime.now(timezone.utc),models=models,source_inputs=inputs)
        for row in scores:persist_score(runtime/'scores'/f"event-{row['ticket_event_id']}-snapshot-{row['source_snapshot_id']}.json",row)
        report=summary(scores,missing,count)
        previous=json.loads((runtime/'latest-scorecard.json').read_text())
        if 'coverage' in previous:report['coverage']=previous['coverage']
        save(runtime/'latest-scorecard.json',report)
        if report['first_review_ready'] and not (runtime/'first-review.json').exists():
            with (runtime/'first-review.json').open('x') as f:json.dump({'checked_at':datetime.now(timezone.utc).isoformat(),'scorecard':report,'event_ids':sorted({r['ticket_event_id'] for r in scores})},f)
        return {'status':'UNCHANGED_FROZEN_SCORE_ONLY','scored_events':report['scored_independent_events'],'private_backup':backup(runtime,ARTIFACT_DIR)}


def score_unchanged():
    """Only outcome scoring; no full-history feature export or fit."""
    from ml.c1_outcome_scoring_bridge_v1 import run_scorers
    results={'old_fixed_lanes':run_scorers(),
             'support26':score_support_only(Path('/workspace/ops-runtime/2026-11-05-c1-support26-collector'))}
    for name,module,runtime,args in (
        ('history','ml.launch_c1_history_residual_v1','2026-11-05-c1-history-residual-collector',
         ['--support-runtime','/workspace/ops-runtime/2026-11-05-c1-support26-collector','--archive','/workspace/ops-runtime/2026-11-04-known-at-source-archive']),
        ('fresh_structural','ml.run_structural_history_refresh_v1','2026-11-06-structural-history-refresh-collector',[])):
        command=[sys.executable,'-m',module,'cycle','--runtime','/workspace/ops-runtime/'+runtime,*args]
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=240)
        if result.returncode:raise ValueError('Unchanged scorer failed closed: '+name)
        results[name]=json.loads(result.stdout)
    return results


def tick(runtime,state,configuration,now,github=api,apply=apply_verified,scorer=score_unchanged,backuper=backup_sources):
    persist=lambda value:save(runtime/'state.json',value)
    slot=due_slot(now,state)
    if slot:dispatch(state,slot,configuration['branch'],configuration['commit'],now,persist,github)
    work=[]
    for key,entry in state.get('dispatches',{}).items():
        if entry.get('status') not in ('DISPATCH_ACCEPTED','DISPATCH_INTENT_RECORDED'):continue
        # Never poll Actions indefinitely or revisit old source receipts.
        if now-stamp(entry['intent_at'])>timedelta(minutes=40):
            entry['status']='RUN_NOT_PROVEN_WITHIN_BUDGET';persist(state);continue
        previous=entry.get('last_run_check_at')
        if previous and now-stamp(previous)<timedelta(minutes=2):continue
        entry['last_run_check_at']=now.isoformat();persist(state)
        found=find_run(entry,github)
        if found is None:continue
        run,sources,raw=found;folder=runtime/('source-run-'+str(run['id']));folder.mkdir(mode=0o700,exist_ok=True)
        save(folder/'run.json',run);save(folder/'sources.json',sources)
        for index,url in enumerate(SOURCES):
            if url in raw:
                path=folder/f'source-{index}.html'
                if path.exists():
                    if path.read_bytes()!=raw[url]:raise ValueError('Immutable raw source conflict')
                else:path.write_bytes(raw[url]);path.chmod(0o440)
        entry.update(status='APPLY_INTENT_RECORDED',run_id=run['id']);persist(state)
        result=apply(folder,run,sources,raw)
        if result['actual_target_outcomes']:
            result['unchanged_scorers']=scorer();save(folder/'final-result.json',result)
        result['private_source_recovery']=backuper(folder)
        entry.update(status='SOURCE_VERIFIED_OR_PENDING_RESULT_RECORDED',result=result);persist(state);work.append(result)
    return {'status':'BOUNDED_POSTMATCH_CHECK','checked_at':now.isoformat(),'due_dispatch':slot,'work':work,
            'production_change':False,'live_adjustment':0,'host_dependent':True}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--branch',required=True);p.add_argument('--commit',required=True);p.add_argument('--once',action='store_true');a=p.parse_args()
    if a.runtime.resolve().is_relative_to(ROOT):raise ValueError('Private runtime required')
    a.runtime.mkdir(mode=0o700,parents=True,exist_ok=True);configuration=contract(a.branch,a.commit);path=a.runtime/'source-contract.json'
    if path.exists():
        if json.loads(path.read_text())!=configuration:raise ValueError('Source closure contract changed')
    else:
        if api('/git/ref/heads/'+a.branch)['object']['sha']!=a.commit:raise ValueError('Published source commit required')
        save(path,configuration)
    with (a.runtime/'closure.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        save(a.runtime/'launch.json',{'pid':os.getpid(),'started_at':datetime.now(timezone.utc).isoformat(),'until':UNTIL,'local_check_seconds':60,'host_dependent':True})
        statepath=a.runtime/'state.json';state=json.loads(statepath.read_text()) if statepath.exists() else {}
        while datetime.now(timezone.utc)<stamp(UNTIL):
            if configuration!=contract(a.branch,a.commit):raise ValueError('Active closure source changed')
            try:result=tick(a.runtime,state,configuration,datetime.now(timezone.utc))
            except Exception as exc:result={'status':'FAILED_CLOSED','checked_at':datetime.now(timezone.utc).isoformat(),'error_type':type(exc).__name__,'reason':str(exc)[:180],'production_change':False}
            save(a.runtime/'latest-cycle.json',result)
            with (a.runtime/'audit.jsonl').open('a') as file:file.write(json.dumps(result)+'\n')
            print(json.dumps(result),flush=True)
            if a.once:break
            time.sleep(min(60,max(0,(stamp(UNTIL)-datetime.now(timezone.utc)).total_seconds())))


if __name__=='__main__':main()
