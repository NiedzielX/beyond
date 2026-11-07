"""Lossless ISO representation adapter using the frozen collector's explicit reader hook."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import fcntl
import hashlib
import json
from pathlib import Path
import os
import time

import pandas as pd

from ml import c1_support26_v1 as frozen
from ml.export_c1_matched_audit_inputs_v1 import Reader
from ml.demand_engine.daily_inventory_path_storage_v1 import encode
from ml.run_postmatch_outcome_closure_v1 import save

VERSION='c1-lossless-representative-timestamp-encoding-v1'


def normalize(payload):
    result=deepcopy(payload);changes=[]
    for candidate in result.get('candidates') or []:
        for rep in candidate.get('representatives') or []:
            original=rep['requested_as_of_at'];instant=pd.Timestamp(original)
            if not isinstance(original,str) or pd.isna(instant) or instant.tzinfo is None:
                raise ValueError('Explicit original aware representative timestamp required')
            normalized=instant.tz_convert('UTC').isoformat(timespec='nanoseconds')
            if pd.Timestamp(normalized)!=instant:raise ValueError('Timestamp codec changed actual instant')
            rep['requested_as_of_at']=normalized
            if original!=normalized:
                changes.append({'ticket_event_id':candidate['ticket_event_id'],
                    'snapshot_id':rep['requested_snapshot_id'],'original':original,'normalized':normalized})
    return result,changes


def store(runtime,prefix,value):
    raw=encode(value);digest=hashlib.sha256(raw).hexdigest();folder=runtime/'inputs';folder.mkdir(mode=0o700,exist_ok=True)
    path=folder/(prefix+'-'+digest+'.json')
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('Immutable codec provenance conflict')
    else:
        with path.open('xb') as file:file.write(raw);file.flush();os.fsync(file.fileno())
        path.chmod(0o440)
    return digest


class LosslessReader:
    def __init__(self,runtime,reader=None):self.runtime=runtime;self.reader=reader or Reader()

    def request(self,path,payload=None):
        value=self.reader.request(path,payload)
        if path!='rpc/get_c1_shadow_v8_inputs_v1':return value
        original_digest=store(self.runtime,'codec-original-rpc',value)
        normalized,changes=normalize(value)
        receipt={'version':VERSION,'actual_received_at':datetime.now(timezone.utc).isoformat(),
            'original_rpc_sha256':original_digest,'normalized_rpc_sha256':hashlib.sha256(encode(normalized)).hexdigest(),
            'changes':changes,'actual_instants_changed':False,'models_changed':False,
            'production_change':False,'live_adjustment':0}
        store(self.runtime,'codec-receipt',receipt)
        return normalized


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--until',required=True);a=p.parse_args();now=datetime.now(timezone.utc);until=frozen.stamp(a.until).to_pydatetime()
    if not now<until<=now+timedelta(hours=72):raise ValueError('Explicit bounded deadline required')
    manifest,*_=frozen.load_models();frozen.ensure_runtime(a.runtime,manifest)
    identity=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    configuration={'version':VERSION,'source_sha256':identity,'manifest_sha256':manifest['_verified_manifest_sha256']}
    path=a.runtime/'timestamp-codec-contract.json'
    if path.exists():
        if json.loads(path.read_text())!=configuration:raise ValueError('Timestamp codec source changed')
    else:save(path,configuration)
    with (a.runtime/'cycle.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        save(a.runtime/'watcher-launch.json',{'pid':os.getpid(),'started_at':now.isoformat(),'until':until.isoformat(),
            'interval_seconds':900,'operational_adapter':VERSION,'host_dependent':True,'production_change':False,'live_adjustment':0})
        while datetime.now(timezone.utc)<until:
            try:
                if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=identity:raise ValueError('Active timestamp codec changed')
                result=frozen.run_cycle(a.runtime,reader=LosslessReader(a.runtime));result['operational_adapter']=VERSION
            except Exception as exc:
                result={'status':'FAILED_CLOSED','checked_at':datetime.now(timezone.utc).isoformat(),'error_type':type(exc).__name__,
                    'reason':str(exc)[:200],'production_change':False,'live_adjustment':0}
                save(a.runtime/'latest-cycle.json',result)
            save(a.runtime/'codec-latest-cycle.json',result);print(json.dumps(result),flush=True)
            time.sleep(min(900,max(0,(until-datetime.now(timezone.utc)).total_seconds())))


if __name__=='__main__':main()
