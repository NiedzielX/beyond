"""Operational later-clock validation retry; frozen inference code stays unchanged."""
from __future__ import annotations

import argparse
from datetime import datetime,timezone,timedelta
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from ml.run_structural_history_refresh_v1 import cycle,ensure_runtime,save
from ml.structural_history_refresh_v1 import ROOT,load_manifest,stamp


def evidence_hashes(runtime):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (runtime/'evidence').glob('*.json')}


def run_once(runtime,support,archive,execute=cycle):
    before=evidence_hashes(runtime)
    try:return execute(runtime,support,archive)
    except ValueError as exc:
        if str(exc)!='New actual forecast clock invalid':raise
        after=evidence_hashes(runtime)
        if any(after.get(k)!=v for k,v in before.items()) or not set(after)-set(before):raise
        # The unchanged second call uses actual later wall time, while all own
        # issue/input/model bytes remain exactly as issued on the first call.
        result=execute(runtime,support,archive)
        if evidence_hashes(runtime)!=after:raise ValueError('Evidence changed during validation-only retry')
        return {**result,'unchanged_later_clock_retry':True,'new_evidence_first_pass':len(set(after)-set(before))}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--support',type=Path,default=Path('/workspace/ops-runtime/2026-11-05-c1-support26-collector'))
    p.add_argument('--archive',type=Path,default=Path('/workspace/ops-runtime/2026-11-04-known-at-source-archive'))
    p.add_argument('--until',required=True);p.add_argument('--interval',type=int,default=900);a=p.parse_args()
    now=datetime.now(timezone.utc);until=stamp(a.until).to_pydatetime()
    if not now<until<=now+timedelta(hours=72) or a.interval!=900:raise ValueError('Bounded unchanged 900s cadence required')
    manifest=load_manifest();ensure_runtime(a.runtime,manifest)
    identity=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();path=a.runtime/'later-clock-watcher-contract.json'
    configuration={'version':'structural-history-refresh-later-clock-watcher-v1','source_sha256':identity,'frozen_manifest_sha256':manifest['_manifest_sha256']}
    if path.exists():
        if json.loads(path.read_text())!=configuration:raise ValueError('Operational watcher source changed')
    else:save(path,configuration,True)
    with (a.runtime/'watcher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        save(a.runtime/'watcher-launch.json',{'pid':os.getpid(),'started_at':now.isoformat(),'until':until.isoformat(),'interval_seconds':900,'host_dependent':True,'operational_later_clock_retry':True,'production_change':False,'live_adjustment':0})
        while datetime.now(timezone.utc)<until:
            try:
                if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=identity:raise ValueError('Watcher source changed')
                result=run_once(a.runtime,a.support,a.archive)
            except Exception as exc:
                result={'status':'FAILED_CLOSED','checked_at':datetime.now(timezone.utc).isoformat(),'error_type':type(exc).__name__,'reason':str(exc)[:180],'production_change':False,'live_adjustment':0}
            save(a.runtime/'watcher-latest.json',result);print(json.dumps(result),flush=True)
            time.sleep(min(900,max(0,(until-datetime.now(timezone.utc)).total_seconds())))


if __name__=='__main__':main()
