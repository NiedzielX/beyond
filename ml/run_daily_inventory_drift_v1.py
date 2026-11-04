"""Bounded sidecar research collection; does not modify the frozen v1 source ledger."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import fcntl
import json
from pathlib import Path
import sqlite3
import time

from ml.daily_inventory_drift_comparator_v1 import freeze_artifact, predict, validate_artifact
from ml.daily_inventory_drift_ledger_v1 import DriftLedger, MARKER
from ml.daily_path_prefix_diagnostics_v1 import build_report, read_ledger
from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.demand_engine.daily_inventory_path_storage_v1 import BUCKET, PrivateResearchStorage, digest, encode, sqlite_snapshot


class DriftStorage(PrivateResearchStorage):
    @staticmethod
    def _key(key):
        import re
        if not re.fullmatch(r'drift-v1/[0-9a-f]{64}\.(sqlite|json)',key):
            raise ValueError('Unexpected drift backup namespace')
        return key


def write_json(path: Path, payload: dict, *, exclusive=False):
    with path.open('x' if exclusive else 'w') as stream:
        json.dump(payload,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')


def backup(ledger_path: Path, artifact_path: Path, storage=None):
    with sqlite3.connect(ledger_path.resolve().as_uri()+'?mode=ro',uri=True) as source:
        try:
            marker=source.execute('select version from drift_ledger_meta where singleton=1').fetchone()
        except sqlite3.Error:
            raise ValueError('Drift backup requires its separate ledger identity') from None
        if not marker or marker[0]!=MARKER:
            raise ValueError('Drift backup ledger identity mismatch')
    storage = storage or DriftStorage()
    storage.ensure_private_bucket()
    validate_artifact(json.loads(artifact_path.read_text()))
    objects = []
    for data,extension,mime in [(sqlite_snapshot(ledger_path),'sqlite','application/octet-stream'),
                               (artifact_path.read_bytes(),'json','application/json')]:
        objects.append(storage.put_verified(f'drift-v1/{digest(data)}.{extension}',data,mime))
    manifest = {'version':'daily-inventory-drift-private-backup-v1', 'bucket':BUCKET,
                'objects':objects, 'production_change':False, 'private':True}
    raw = encode(manifest)
    return {**manifest,'manifest_object':storage.put_verified(f'drift-v1/{digest(raw)}.json',raw,'application/json')}


def run_cycle(source: Path, runtime: Path, storage=None):
    runtime.mkdir(parents=True,exist_ok=True)
    with (runtime/'cycle.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Another drift cycle is active') from None
        artifact_path=runtime/'artifact.json'
        artifact=json.loads(artifact_path.read_text());validate_artifact(artifact)
        ledger_path=runtime/'drift-v1.sqlite'
        if source.resolve()==ledger_path.resolve():raise ValueError('Reference and drift ledgers must be separate')
        attempts,points=read_ledger(source)
        frozen=parse_timestamp(artifact['frozen_at'])
        now=datetime.now(timezone.utc)
        counts={'new_attempts':0,'new_points':0,'post_freeze_reference_attempts':0,'missed_uncaptured':0}
        with DriftLedger(ledger_path) as ledger:
            old={(a['issue']['ticket_event_id'],a['issue']['issued_as_of_at']) for a in ledger.export_attempts()}
            for attempt in attempts:
                issue=attempt['issue'];issued=parse_timestamp(issue['issued_as_of_at'])
                if issued<frozen:continue
                counts['post_freeze_reference_attempts']+=1
                if (issue['ticket_event_id'],issue['issued_as_of_at']) in old:continue
                if now>issued+timedelta(minutes=90):
                    counts['missed_uncaptured']+=1;continue
                if now<issued or parse_timestamp(attempt['executed_at'])>now:continue
                # Reference actual values/scores are never passed to prediction.
                _,predictions=predict(issue,artifact)
                result=ledger.record(issue,predictions,artifact,datetime.now(timezone.utc))
                if result['inserted']:
                    counts['new_attempts']+=1;counts['new_points']+=result['point_count']
            scores=ledger.score_from_reference(points,datetime.now(timezone.utc).isoformat())
            captured=ledger.export_attempts();predicted=ledger.export_points()
        checked=datetime.now(timezone.utc).isoformat()
        report=build_report(captured,predicted,checked)
        primary=report['primary']
        plus_one=primary['per_lead']['1']
        evidence_ready=plus_one['scored_event_count']>=8 and plus_one['distinct_club_count']>=5
        # Private content-addressed namespace does not alter v1's latest backup manifest.
        verified=backup(ledger_path,artifact_path,storage)
        result={'version':'daily-inventory-drift-cycle-v1','checked_at':checked,**counts,
                'attempt_count':len(captured),'point_count':len(predicted),'scores':scores,
                'attempt_status_counts':dict(Counter(a['drift_status'] for a in captured)),
                'status':'RESEARCH_REVIEW_READY' if evidence_ready else 'COLLECTING',
                'diagnostics':report,'backup':verified,'production_change':False,'live_adjustment':0,
                'production_activation_allowed':False}
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        write_json(runtime/f'cycle-{stamp}.json',result,exclusive=True)
        if evidence_ready and not (runtime/'initial-review.json').exists():
            write_json(runtime/'initial-review.json',result,exclusive=True)
        write_json(runtime/'latest-cycle.json',result)
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--source-ledger',type=Path)
    parser.add_argument('--freeze',action='store_true')
    parser.add_argument('--watch-until')
    parser.add_argument('--interval-seconds',type=int,default=300)
    args=parser.parse_args()
    args.runtime.mkdir(parents=True,exist_ok=True)
    if args.freeze:
        artifact=freeze_artifact(datetime.now(timezone.utc).isoformat())
        write_json(args.runtime/'artifact.json',artifact,exclusive=True)
        print(json.dumps({'status':'FROZEN_RULE','model_sha256':artifact['model_sha256'],'frozen_at':artifact['frozen_at']}));return
    if args.source_ledger is None:parser.error('--source-ledger is required for collection')
    stop=parse_timestamp(args.watch_until) if args.watch_until else None
    if args.interval_seconds<60 or stop is not None and not datetime.now(timezone.utc)<stop<=datetime.now(timezone.utc)+timedelta(hours=24):
        parser.error('Watch must stop within24hours; interval at least60seconds')
    with (args.runtime/'watcher.lock').open('a') as watcher:
        try:fcntl.flock(watcher,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Another drift watcher is active') from None
        while True:
            result=run_cycle(args.source_ledger,args.runtime)
            print(json.dumps({key:result[key] for key in ['checked_at','status','attempt_count','point_count']}),flush=True)
            if stop is None or datetime.now(timezone.utc)>=stop:break
            deadline=time.monotonic()+args.interval_seconds
            while datetime.now(timezone.utc)<stop and time.monotonic()<deadline:
                time.sleep(min(10,max(0,(stop-datetime.now(timezone.utc)).total_seconds()),max(0,deadline-time.monotonic())))


if __name__=='__main__':main()
