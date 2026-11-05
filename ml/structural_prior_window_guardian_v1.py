"""Bounded dispatch of existing main materialization for genuinely open windows."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone,timedelta
import fcntl,hashlib,json,os
from pathlib import Path
import time
from ml.c1_live_matched_audit_v1 import ROOT
from ml.demand_engine.current_structural_prior_features import HORIZON_DAYS
from ml.frozen_window_guardian_v1 import GuardianAPI,GITHUB_BASE
from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp

VERSION='structural-prior-window-guardian-v1'
WORKFLOW='structural-prior-materializer.yml'
MAIN='e04033fb2e01622cf393da398eead16a2d1c4831'


def window_key(row):return f"{row['ticket_event_id']}/{row['horizon']}/{parse_timestamp(row['target_as_of_at']).isoformat()}"


def classify(rows,now):
    if not isinstance(rows,list) or len(rows)>=1000:raise ValueError('Bounded due source required')
    legal=[];unsafe=[];nonready=[];seen=set()
    for row in rows:
        if type(row.get('ticket_event_id')) is not int or row['ticket_event_id']<=0:raise ValueError('Positive canonical event ID required')
        key=(row['ticket_event_id'],row['horizon'])
        if key in seen:raise ValueError('Duplicate due event/horizon')
        seen.add(key)
        if row.get('input_status')!='ready':nonready.append(row);continue
        horizon=row['horizon'];cutoff=parse_timestamp(row['target_as_of_at']);kickoff=parse_timestamp(row['kickoff_at'])
        if horizon not in HORIZON_DAYS or cutoff!=kickoff-timedelta(days=HORIZON_DAYS[horizon]):raise ValueError('Canonical horizon/cutoff mismatch')
        if kickoff<=now or cutoff>now or now>cutoff+timedelta(minutes=90):unsafe.append(row)
        else:legal.append(row)
    return {'legal':legal,'unsafe':unsafe,'nonready':nonready}


class API(GuardianAPI):
    def due(self,now):
        return self.request(self.supabase_base+'/rest/v1/rpc/get_due_early_structural_prior_inputs_v1',
            {**self.supabase_headers,'Content-Type':'application/json'},
            {'p_requested_at':now.isoformat(),'p_include_ready_event_id':None})
    def active(self):
        data=self.request(GITHUB_BASE+f'/actions/workflows/{WORKFLOW}/runs?per_page=20',self.github_headers)
        return [r for r in data['workflow_runs'] if r['head_branch']=='main' and r['status']!='completed']
    def main_sha(self):return self.request(GITHUB_BASE+'/git/ref/heads/main',self.github_headers)['object']['sha']
    def dispatch(self):return self.request(GITHUB_BASE+f'/actions/workflows/{WORKFLOW}/dispatches',self.github_headers,{'ref':'main'})


def save(path,value):
    with path.open('w') as f:json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())


def source_hashes():
    return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in
            ['ml/structural_prior_window_guardian_v1.py','ml/frozen_window_guardian_v1.py']}


def ensure_runtime(runtime):
    if runtime.resolve().is_relative_to(ROOT):raise ValueError('Guardian evidence must remain outside Git')
    runtime.mkdir(mode=0o700,parents=True,exist_ok=True)
    path=runtime/'source-contract.json';expected={'version':VERSION,'source_sha256':source_hashes(),'expected_main':MAIN,'workflow':WORKFLOW}
    if path.exists():
        if json.loads(path.read_text())!=expected:raise ValueError('Guardian source/runtime changed')
    else:
        if any(runtime.iterdir()):raise ValueError('Nonempty unmarked guardian runtime')
        save(path,expected)


def tick(api,state,save_state,now,clock=None):
    rows=api.due(now);checked=(clock or (lambda:datetime.now(timezone.utc)))()
    if checked<now or checked-now>timedelta(minutes=2):raise ValueError('Stale source preflight')
    classified=classify(rows,checked)
    result={'version':VERSION,'checked_at':checked.isoformat(),'open_windows':[window_key(r) for r in classified['legal']],
        'unsafe_windows':[window_key(r) for r in classified['unsafe']],'nonready_inputs':len(classified['nonready']),
        'dispatched':False,'workflow_executed':False,'db_record_proven':False,'production_change':False,'live_adjustment':0}
    if classified['unsafe']:return {**result,'status':'BLOCKED_OTHER_UNSAFE_READY_INPUT_NO_BACKFILL'}
    if not classified['legal']:return {**result,'status':'NO_LEGAL_READY_MISSING_PRIOR'}
    if api.active():return {**result,'status':'EXISTING_MAIN_RUN_ACTIVE'}
    if api.main_sha()!=MAIN:raise ValueError('Main changed; inspect before dispatch')
    issued=(clock or (lambda:datetime.now(timezone.utc)))()
    if issued-now>timedelta(minutes=2) or classify(rows,issued)['unsafe']:return {**result,'status':'WINDOW_CHANGED_NO_DISPATCH'}
    last=state.get('last_dispatch_at')
    if last and issued-parse_timestamp(last)<timedelta(minutes=10):return {**result,'status':'DISPATCH_COOLDOWN'}
    counts=state.setdefault('window_dispatch_counts',{})
    if any(type(v) is not int or v<0 or v>3 for v in counts.values()):raise ValueError('Invalid durable dispatch accounting')
    keys=[window_key(r) for r in classified['legal']]
    if any(counts.get(k,0)>=3 for k in keys):return {**result,'status':'WINDOW_DISPATCH_LIMIT'}
    for key in keys:counts[key]=counts.get(key,0)+1
    state['last_dispatch_at']=issued.isoformat();state['last_intent_windows']=keys
    save_state(state)  # Durable intent must precede any mutation, even an uncertain HTTP outcome.
    api.dispatch()
    return {**result,'status':'MAIN_MATERIALIZER_DISPATCH_ACCEPTED','dispatched':True,'dispatch_requested_at':issued.isoformat()}


def cycle(runtime,api=None):
    ensure_runtime(runtime)
    with (runtime/'cycle.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Another structural cycle holds the runtime lock') from None
        state_path=runtime/'guardian-state.json'
        state=json.loads(state_path.read_text()) if state_path.exists() else {}
        now=datetime.now(timezone.utc)
        result=tick(api or API(),state,lambda x:save(state_path,x),now)
        with (runtime/'guardian-audit.jsonl').open('a') as f:f.write(json.dumps(result,sort_keys=True)+'\n')
        save(runtime/'guardian-latest.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--until',required=True);p.add_argument('--interval',type=int,default=300);a=p.parse_args()
    now=datetime.now(timezone.utc);until=parse_timestamp(a.until)
    if not now<until<=now+timedelta(hours=72) or not 60<=a.interval<=900:raise ValueError('Explicit bounded deadline/interval required')
    ensure_runtime(a.runtime)
    with (a.runtime/'guardian.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Existing structural guardian holds lifetime lock') from None
        save(a.runtime/'guardian-launch.json',{'pid':os.getpid(),'started_at':now.isoformat(),'until':until.isoformat(),
            'interval_seconds':a.interval,'host_dependent':True,'production_change':False,'live_adjustment':0})
        while datetime.now(timezone.utc)<until:
            try:print(json.dumps(cycle(a.runtime)),flush=True)
            except Exception as exc:
                save(a.runtime/'guardian-latest.json',{'status':'FAILED_CLOSED','checked_at':datetime.now(timezone.utc).isoformat(),
                    'error_type':type(exc).__name__,'reason':str(exc)[:200],'production_change':False,'live_adjustment':0})
            remaining=(until-datetime.now(timezone.utc)).total_seconds()
            if remaining>0:time.sleep(min(a.interval,remaining))


if __name__=='__main__':main()
