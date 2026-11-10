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

from ml.postmatch_outcome_source_v4 import recover,stage,stamp,load_profile,WARSAW

ROOT=Path(__file__).resolve().parents[1]
BASE='https://api.github.com/repos/NiedzielX/beyond'
WORKFLOW='ml-research-readiness-contract-v1.yml'
SOURCE_FILES=('ml/postmatch_outcome_source_v4.py','ml/run_postmatch_outcome_closure_v4.py','ml/postmatch_outcome_source_v1.py','ml/run_postmatch_outcome_closure_v1.py','ml/c1_history_scoring_adapter_v1.py','ml/watch_structural_history_refresh_v1.py',
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


def contract(branch,commit,profile,profile_path):
    return {'version':'postmatch-outcome-closure-v4','branch':branch,'commit':commit,
        'slots':profile['slots'],'until':profile['until'],'contract_id':profile['id'],'contract_sha256':profile['_sha256'],'contract_path':str(profile_path),'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (*SOURCE_FILES,str(profile_path))},
        'production_change':False,'live_adjustment':0}


def due_slot(now,state,profile):
    for slot in profile['slots']:
        if slot not in state.get('dispatches',{}) and stamp(slot)<=now<=stamp(slot)+timedelta(minutes=30):return slot
    return None


def dispatch(state,slot,branch,commit,now,persist,profile,profile_path,github=api):
    if (slot not in profile['slots'] or not stamp(slot)<=now<=stamp(slot)+timedelta(minutes=30)
            or slot in state.get('dispatches',{})):
        raise ValueError('No historical catchup or duplicate source dispatch')
    if github('/git/ref/heads/'+branch)['object']['sha']!=commit:raise ValueError('Published source branch moved')
    entry={'intent_at':now.isoformat(),'branch':branch,'commit':commit,'status':'DISPATCH_INTENT_RECORDED'}
    state.setdefault('dispatches',{})[slot]=entry;persist(state)
    receipt=github('/actions/workflows/'+WORKFLOW+'/dispatches',{'ref':branch,'inputs':{'forward_outcome_contract':str(profile_path)}})
    if receipt.get('http_status')!=204:raise ValueError('Expected workflow dispatch acceptance')
    entry.update(status='DISPATCH_ACCEPTED',accepted_at=datetime.now(timezone.utc).isoformat());persist(state)
    return entry


def find_run(entry,profile,github=api):
    import urllib.parse
    values=github('/actions/workflows/'+WORKFLOW+'/runs?branch='+urllib.parse.quote(entry['branch'],safe='')+'&event=workflow_dispatch&per_page=30')
    runs=[r for r in values['workflow_runs'] if r['head_sha']==entry['commit']
          and stamp(entry['intent_at'])-timedelta(seconds=2)<=stamp(r['created_at'])<=stamp(entry['intent_at'])+timedelta(minutes=5)]
    if len(runs)>1:raise ValueError('Ambiguous source dispatch run; no arbitrary selection')
    if not runs or runs[0]['status']!='completed':return None
    run=runs[0]
    if run['conclusion']!='success':raise ValueError('Source workflow failed; no import')
    checks=github('/commits/'+entry['commit']+'/check-runs?per_page=100&filter=all')
    if checks['total_count']>100:raise ValueError('Bounded source check collection expanded')
    sources,raw=recover(checks['check_runs'],entry['commit'],run['id'],run['run_attempt'],profile)
    return run,sources,raw


def scoped_filters(profile):
    ids=','.join(str(t['id']) for t in profile['fixtures'])
    clubs=','.join(sorted(set(profile['club_aliases'])|{t['club_slug'] for t in profile['fixtures']}))
    dates=','.join(sorted({stamp(t['kickoff_at']).astimezone(WARSAW).date().isoformat() for t in profile['fixtures']}))
    return ids,clubs,dates


def read_sources(reader,profile):
    from ml.export_structural_known_at_inputs_v1 import SourceReader
    r=reader or SourceReader();ids,clubs,dates=scoped_filters(profile)
    events=r.counted('ticket_events',[('id','in.('+ids+')')])
    history=r.counted('history',[('club_slug','in.('+clubs+')')])
    sporting=r.counted('sporting',[('season','eq.2026-2027'),('event_date','in.('+dates+')')])
    outcomes=r.counted('outcomes',[('ticket_event_id','in.('+ids+')')])
    return r,events,history,sporting,outcomes


def apply_verified(runtime,run,sources,raw,profile,reader=None):
    TARGETS=profile['fixtures'];ids,clubs,_=scoped_filters(profile)
    r,events,history,sporting,before=read_sources(reader,profile)
    verified=datetime.now(timezone.utc).isoformat()
    save(runtime/'verification-inputs.json',{'actual_verified_at':verified,'events':events,'history':history,'sporting':sporting,'outcomes':before,'contract_sha256':profile['_sha256']})
    result=stage(sources,raw,events,sporting,history,run_id=run['id'],verified_at=verified,profile=profile)
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
        after=r.counted('history',[('club_slug','in.('+clubs+')')]);by_id={row['id']:row for row in after}
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
    outcomes=r.counted('outcomes',[('ticket_event_id','in.('+ids+')')])
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
            if not re.fullmatch(r'postmatch-outcome-closure-v4/[0-9a-f]{64}\.json',key):raise ValueError('Wrong private source namespace')
            return key
    files=[p for p in sorted(runtime.iterdir()) if p.is_file() and p.name!='private-backup.json']
    if len(files)>25:raise ValueError('Bounded postmatch audit expanded')
    body=encode({'files':[{'name':p.name,'sha256':digest(p.read_bytes()),'base64':base64.b64encode(p.read_bytes()).decode()} for p in files]})
    if len(body)>10*1024*1024:raise ValueError('Bounded source recovery expanded')
    raw=encode({'encoding':'zlib+base64','payload_sha256':digest(body),'payload':base64.b64encode(zlib.compress(body)).decode()})
    storage=Storage();storage.ensure_private_bucket();receipt=storage.put_verified('postmatch-outcome-closure-v4/'+digest(raw)+'.json',raw,'application/json')
    remote=storage.read(receipt['key'])
    if remote!=raw:raise ValueError('Private source recovery bytes changed')
    restored=zlib.decompress(base64.b64decode(json.loads(remote)['payload']))
    if digest(restored)!=digest(body) or any(digest(base64.b64decode(p['base64']))!=p['sha256'] for p in json.loads(restored)['files']):raise ValueError('Private source decompression differs')
    receipt.update(files=len(files),independent_remote_decompression_verified=True);save(runtime/'private-backup.json',receipt);return receipt


def score_unchanged():
    from ml.c1_outcome_scoring_bridge_v1 import run_scorers
    from ml.run_postmatch_outcome_closure_v1 import score_support_only
    from ml.watch_structural_history_refresh_v1 import run_once
    result={'old_fixed_lanes':run_scorers(),
            'support26':score_support_only(Path('/workspace/ops-runtime/2026-11-05-c1-support26-collector'))}
    process=subprocess.run([sys.executable,'-m','ml.c1_history_scoring_adapter_v1','cycle','--runtime',
        '/workspace/ops-runtime/2026-11-05-c1-history-residual-collector'],cwd=ROOT,capture_output=True,text=True,timeout=240)
    if process.returncode:raise ValueError('Frozen history scoring adapter failed closed')
    result['history']=json.loads(process.stdout)
    result['fresh_structural']=run_once(Path('/workspace/ops-runtime/2026-11-06-structural-history-refresh-collector'),
        Path('/workspace/ops-runtime/2026-11-05-c1-support26-collector'),Path('/workspace/ops-runtime/2026-11-04-known-at-source-archive'))
    from ml.export_c1_matched_audit_inputs_v1 import Reader
    result['served_c1']=Reader().request('rpc/score_c1_shadow_v8_completed_events_v1',{'p_requested_at':datetime.now(timezone.utc).isoformat()})
    return result


def tick(runtime,state,configuration,now,profile,profile_path,github=api,apply=apply_verified,scorer=score_unchanged,backuper=backup_sources):
    SOURCES=tuple(t['source_url'] for t in profile['fixtures'])
    persist=lambda value:save(runtime/'state.json',value)
    slot=due_slot(now,state,profile)
    if slot:dispatch(state,slot,configuration['branch'],configuration['commit'],now,persist,profile,profile_path,github)
    work=[]
    for key,entry in state.get('dispatches',{}).items():
        if entry.get('status') not in ('DISPATCH_ACCEPTED','DISPATCH_INTENT_RECORDED'):continue
        # Never poll Actions indefinitely or revisit old source receipts.
        if now-stamp(entry['intent_at'])>timedelta(minutes=40):
            entry['status']='RUN_NOT_PROVEN_WITHIN_BUDGET';persist(state);continue
        previous=entry.get('last_run_check_at')
        if previous and now-stamp(previous)<timedelta(minutes=2):continue
        entry['last_run_check_at']=now.isoformat();persist(state)
        found=find_run(entry,profile,github)
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
        result=apply(folder,run,sources,raw,profile)
        result['private_source_recovery_before_scoring']=backuper(folder)
        if result['actual_target_outcomes']:
            result['unchanged_scorers']=scorer();save(folder/'final-result.json',result)
        result['private_source_recovery']=backuper(folder)
        entry.update(status='SOURCE_VERIFIED_OR_PENDING_RESULT_RECORDED',result=result);persist(state);work.append(result)
    return {'status':'BOUNDED_POSTMATCH_CHECK','checked_at':now.isoformat(),'due_dispatch':slot,'work':work,
            'production_change':False,'live_adjustment':0,'host_dependent':True}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--contract',type=Path,required=True);p.add_argument('--branch',required=True);p.add_argument('--commit',required=True);p.add_argument('--once',action='store_true');a=p.parse_args()
    profile=load_profile(a.contract)
    if not datetime.now(timezone.utc)<stamp(profile['until']):raise ValueError('Outcome opportunities/deadline elapsed; no historical catchup')
    if a.runtime.resolve().is_relative_to(ROOT):raise ValueError('Private runtime required')
    a.runtime.mkdir(mode=0o700,parents=True,exist_ok=True);configuration=contract(a.branch,a.commit,profile,a.contract);path=a.runtime/'source-contract.json'
    if path.exists():
        if json.loads(path.read_text())!=configuration:raise ValueError('Closure v4 source changed')
    else:
        if api('/git/ref/heads/'+a.branch)['object']['sha']!=a.commit:raise ValueError('Published immutable source ref required')
        save(path,configuration)
    with (a.runtime/'closure.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        save(a.runtime/'launch.json',{'version':'postmatch-outcome-closure-v4','pid':os.getpid(),'started_at':datetime.now(timezone.utc).isoformat(),'until':profile['until'],'local_check_seconds':60,'host_dependent':True})
        statepath=a.runtime/'state.json';state=json.loads(statepath.read_text()) if statepath.exists() else {}
        while datetime.now(timezone.utc)<stamp(profile['until']):
            if configuration!=contract(a.branch,a.commit,load_profile(a.contract),a.contract):raise ValueError('Active v4 contract/source changed')
            try:result=tick(a.runtime,state,configuration,datetime.now(timezone.utc),profile,a.contract)
            except Exception as exc:result={'status':'FAILED_CLOSED','checked_at':datetime.now(timezone.utc).isoformat(),'error_type':type(exc).__name__,'reason':str(exc)[:180],'production_change':False,'live_adjustment':0}
            result['operational_orchestrator']='postmatch-outcome-closure-v4';save(a.runtime/'latest-cycle.json',result)
            with (a.runtime/'audit.jsonl').open('a') as file:file.write(json.dumps(result)+'\n')
            print(json.dumps(result),flush=True)
            if a.once:break
            time.sleep(min(60,max(0,(stamp(profile['until'])-datetime.now(timezone.utc)).total_seconds())))


if __name__=='__main__':main()
