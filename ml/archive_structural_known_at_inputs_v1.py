"""Bounded immutable private source snapshots; never predicts, scores or writes priors."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.parse
import zlib

from ml.export_structural_known_at_inputs_v1 import capture, validate_envelope, digest, write_private, ROOT, MAX_BYTES
from ml.demand_engine.daily_inventory_path_storage_v1 import PrivateResearchStorage, encode

VERSION = 'structural-known-at-source-archive-v1'
SOURCES = ['ml/archive_structural_known_at_inputs_v1.py', 'ml/export_structural_known_at_inputs_v1.py',
           'ml/export_c1_matched_audit_inputs_v1.py','ml/run_daily_inventory_path_v1.py',
           'ml/demand_engine/daily_inventory_path_storage_v1.py']


class SourceArchiveStorage(PrivateResearchStorage):
    @staticmethod
    def _key(key):
        if not re.fullmatch(r'structural-known-at-inputs-v1/[0-9a-f]{64}\.json',key):
            raise ValueError('Separate source archive namespace required')
        return urllib.parse.quote(key,safe='/')


def bounds(until, interval, now):
    from ml.attendance_knowledge_time_guard_v1 import timestamp
    end=timestamp(until)
    if not 300<=interval<=3600 or not 0<(end-now).total_seconds()<=72*3600:
        raise ValueError('Archive needs an explicit deadline within72hours and300..3600second interval')
    return end


def source_lock(runtime):
    expected={'version':VERSION,'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}}
    path=runtime/'source-contract.json'
    if path.exists():
        if json.loads(path.read_text())!=expected:raise ValueError('Source archive implementation changed after collection started')
    else:
        if any(p.name!='watcher.lock' for p in runtime.iterdir()):
            raise ValueError('Source archive needs its own empty runtime directory')
        with path.open('x') as stream:json.dump(expected,stream,indent=2)
        path.chmod(0o440)
    return expected


def restore(raw):
    wrapper=json.loads(raw)
    if wrapper.get('version')!=VERSION or wrapper.get('encoding')!='zlib+base64':raise ValueError('Wrong source recovery identity')
    inflater=zlib.decompressobj()
    body=inflater.decompress(base64.b64decode(wrapper['payload'],validate=True),MAX_BYTES+1)
    if len(body)>MAX_BYTES or inflater.unconsumed_tail or not inflater.eof or inflater.unused_data:
        raise ValueError('Invalid or oversized recovery payload')
    if digest(json.loads(body))!=wrapper['payload_sha256']:raise ValueError('Recovery content hash mismatch')
    return validate_envelope(json.loads(body))


def cycle(runtime, reader=None, storage=None):
    runtime=Path(runtime).resolve()
    if runtime.is_relative_to(ROOT):raise ValueError('Private archive must remain outside Git')
    runtime.mkdir(mode=0o700,parents=True,exist_ok=True);contract=source_lock(runtime)
    payload=capture(reader);directory=runtime/('capture-'+payload['export_sha256'])
    path=write_private(directory,payload)
    body=encode(payload);raw=encode({'version':VERSION,'encoding':'zlib+base64','payload_sha256':digest(payload),
        'payload':base64.b64encode(zlib.compress(body)).decode()})
    storage=storage or SourceArchiveStorage();storage.ensure_private_bucket()
    key='structural-known-at-inputs-v1/'+digest(json.loads(raw))+'.json'
    receipt=storage.put_verified(key,raw,'application/json')
    recovered=restore(storage.read(key))
    if recovered!=payload:raise ValueError('Restored source snapshot differs')
    result={'version':VERSION,'status':'SOURCE_ARCHIVED_AND_RESTORED','checked_at':datetime.now(timezone.utc).isoformat(),
        'source_export_sha256':payload['export_sha256'],'capture_completed_at':payload['completed_at'],
        'private_input_path':str(path),'partition_counts':{n:r['count'] for n,r in payload['receipts'].items()},
        'source_contract_sha256':digest(contract),'private_backup':receipt,'restore_verified':True,
        'forecast_created':False,'official_database_write':False,'host_dependent':True,
        'production_change':False,'live_adjustment':0}
    with (directory/'receipt.json').open('x') as stream:json.dump(result,stream,indent=2)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--until',required=True);p.add_argument('--interval',type=int,default=900);a=p.parse_args()
    end=bounds(a.until,a.interval,datetime.now(timezone.utc));runtime=a.runtime.resolve()
    if runtime.is_relative_to(ROOT):raise ValueError('Archive runtime must remain private')
    runtime.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (runtime/'watcher.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('An archive worker already holds this runtime') from None
        source_lock(runtime)
        (runtime/'watcher-launch.json').write_text(json.dumps({'version':VERSION,'pid':os.getpid(),
            'started_at':datetime.now(timezone.utc).isoformat(),'until':end.isoformat(),'interval_seconds':a.interval,
            'host_dependent':True,'forecast_created':False,'production_change':False},indent=2))
        while datetime.now(timezone.utc)<end:
            try:result=cycle(runtime)
            except Exception as exc:result={'version':VERSION,'status':'ARCHIVE_CYCLE_FAILED',
                'checked_at':datetime.now(timezone.utc).isoformat(),'error_type':type(exc).__name__,'production_change':False}
            (runtime/'latest-cycle.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
            time.sleep(max(0,min(a.interval,(end-datetime.now(timezone.utc)).total_seconds())))


if __name__=='__main__':main()
