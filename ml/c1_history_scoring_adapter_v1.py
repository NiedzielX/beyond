"""Storage-call adapter; original frozen history capture/inference/scoring stay unchanged."""
from __future__ import annotations

import argparse
from datetime import datetime,timedelta,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from ml.c1_history_residual_v1 import ResidualRuntime
from ml import run_c1_history_residual_v1 as frozen
from ml.run_postmatch_outcome_closure_v1 import save

VERSION='c1-history-score-path-adapter-v1'
ROOT=Path(__file__).resolve().parents[1]


def recover_score_directory(runtime,expected_scores,backup_receipt):
    """Relocate a fully replayed partial score, preserving its exact original bytes."""
    if runtime.resolve().is_relative_to(ROOT):raise ValueError('Private recovery runtime required')
    with (runtime/'watcher.lock').open('a') as watcher,(runtime/'cycle.lock').open('a') as cycle_lock:
        for lock in (watcher,cycle_lock):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=runtime/'scores';journal_path=runtime/'score-path-recovery.json'
        journal=json.loads(journal_path.read_text()) if journal_path.exists() else None
        if path.is_symlink():raise ValueError('Unexpected score-path symlink')
        if journal:
            digest=journal['original_sha256']
            if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('Invalid recovery identity')
            archive=runtime/('score-path-original-'+digest+'.json')
            if archive.is_symlink():raise ValueError('Unexpected archived score symlink')
            raw=archive.read_bytes() if archive.exists() else path.read_bytes()
        else:
            if not path.is_file():raise ValueError('Exactly one malformed original score file required')
            raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();archive=runtime/('score-path-original-'+digest+'.json')
        if (hashlib.sha256(raw).hexdigest()!=digest
                or backup_receipt.get('original_score_sha256')!=digest
                or backup_receipt.get('independent_remote_decompression_verified')is not True
                or backup_receipt.get('read_back_verified')is not True or not backup_receipt.get('key')):
            raise ValueError('Independent original-byte recovery proof required')
        original=json.loads(raw)
        matches=[row for row in expected_scores if row==original]
        if len(matches)!=1 or (json.dumps(matches[0],sort_keys=True,indent=2,allow_nan=False)+'\n').encode()!=raw:
            raise ValueError('Partial score does not exactly match one genuine frozen replay')
        if any(type(original.get(k))is not int or original[k]<=0 for k in ('ticket_event_id','source_snapshot_id')):
            raise ValueError('Invalid original score identity')
        name=f"event-{original['ticket_event_id']}-snapshot-{original['source_snapshot_id']}.json"
        if journal and (journal['destination']!=name or journal['backup_key']!=backup_receipt['key']):
            raise ValueError('Recovery identity/receipt changed')
        if path.is_dir():
            if not journal or not archive.is_file() or (path/name).read_bytes()!=raw:
                raise ValueError('Existing recovered directory/archived bytes differ')
            if journal['status']!='RELOCATED_IDENTICALLY':
                journal.update(status='RELOCATED_IDENTICALLY',completed_at=datetime.now(timezone.utc).isoformat());save(journal_path,journal)
            return {**journal,'status':'ALREADY_RELOCATED_IDENTICALLY'}
        staged=runtime/('.score-path-recovery-'+digest)
        if staged.is_symlink() or archive.is_symlink():raise ValueError('Unexpected recovery symlink')
        if not journal:
            journal={'version':'c1-history-score-path-relocation-v1','status':'PREPARED',
                'started_at':datetime.now(timezone.utc).isoformat(),'original_sha256':digest,
                'destination':name,'backup_key':backup_receipt['key'],'forecast_clocks_changed':False,
                'models_fitted':0,'production_change':False,'live_adjustment':0}
            with journal_path.open('x') as file:json.dump(journal,file,indent=2,sort_keys=True);file.write('\n');file.flush();os.fsync(file.fileno())
        staged.mkdir(mode=0o700,exist_ok=True)
        target=staged/name
        if target.is_symlink():raise ValueError('Unexpected prepared score symlink')
        if target.exists():
            if target.read_bytes()!=raw:raise ValueError('Prepared score bytes conflict')
        else:
            with target.open('xb') as file:file.write(raw);file.flush();os.fsync(file.fileno())
            target.chmod(0o440)
        if set(p.name for p in staged.iterdir())!={name}:raise ValueError('Unexpected prepared recovery contents')
        if path.exists():
            if not path.is_file() or path.read_bytes()!=raw or archive.exists():raise ValueError('Original layout changed during recovery')
            os.rename(path,archive)
        elif not archive.exists() or archive.read_bytes()!=raw:
            raise ValueError('Neither original nor verified archived score exists')
        os.rename(staged,path)
        if archive.read_bytes()!=raw or (path/name).read_bytes()!=raw:raise ValueError('Relocated bytes differ')
        journal.update(status='RELOCATED_IDENTICALLY',completed_at=datetime.now(timezone.utc).isoformat())
        save(journal_path,journal);return journal


def persist_scores(runtime, scores):
    directory=runtime/'scores'
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise ValueError('Existing scores path is not a directory; preserve it for review')
    for row in scores:
        if any(type(row.get(k))is not int or row[k]<=0 for k in ('ticket_event_id','source_snapshot_id')):
            raise ValueError('Exact positive event/snapshot identities required')
        path=directory/f"event-{row['ticket_event_id']}-snapshot-{row['source_snapshot_id']}.json"
        frozen.persist_score(path,row)


def cycle(runtime,support,archive):
    manifest,models,bench=frozen.load_models();frozen.ensure_runtime(runtime,manifest)
    if (runtime/'scores').exists() and not (runtime/'scores').is_dir():
        raise ValueError('Malformed existing score evidence requires review')
    with (runtime/'cycle.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        now=datetime.now(timezone.utc);reader=frozen.Reader()
        outcomes=reader.request('ticket_event_outcomes?select=*&limit=1001')
        metadata=reader.request('ticket_events?select=id,club_slug,kickoff_at&limit=1001')
        if len(outcomes)>=1000 or len(metadata)>=1000:raise ValueError('Unpaginated source expanded')
        labelled={r['ticket_event_id'] for r in outcomes};meta={r['id']:r for r in metadata}
        if len(meta)!=len(metadata):raise ValueError('Duplicate canonical metadata')
        attempts=[]
        for path in sorted((support/'evidence').glob('*.json')):
            old=json.loads(path.read_text());event=old['ticket_event_id']
            if ((runtime/'evidence'/path.name).exists() or event in labelled
                    or frozen.stamp(old['as_of_at'])<frozen.stamp(manifest['frozen_at'])
                    or frozen.stamp(now)-frozen.stamp(old['input_requested_at'])>timedelta(minutes=15)):
                continue
            try:
                candidate=json.loads((support/'inputs'/('candidate-'+old['candidate_input_sha256']+'.json')).read_text())
                result=frozen.capture_one(runtime,old,candidate,meta[event],manifest,models,bench,archive,now)
                attempts.append({'ticket_event_id':event,**result})
            except (ValueError,KeyError,RuntimeError,TypeError) as exc:
                attempts.append({'ticket_event_id':event,'status':'FAILED_CLOSED','reason':str(exc)[:200]})
        captured=[json.loads(p.read_text()) for p in sorted((runtime/'evidence').glob('*.json'))]
        scores,missing=frozen.score_rows(runtime,captured,outcomes,metadata,manifest,models,bench,datetime.now(timezone.utc))
        persist_scores(runtime,scores)
        report=frozen.summarize(scores,missing,len({r['ticket_event_id'] for r in captured}))
        frozen.write_json(runtime/'current-report.json',report)
        if report['review_ready'] and not (runtime/'first-review.json').exists():frozen.write_json(runtime/'first-review.json',report,True)
        with (runtime/'attempts.jsonl').open('a') as f:f.write(json.dumps({'checked_at':now.isoformat(),'attempts':attempts,'operational_adapter':VERSION})+'\n')
        receipt=frozen.backup(runtime)
        if frozen.load_models()[0]['_verified_manifest_sha256']!=manifest['_verified_manifest_sha256']:
            raise ValueError('Freeze changed during adapter cycle')
        result={'status':'CYCLE_VERIFIED','checked_at':datetime.now(timezone.utc).isoformat(),'package_version':frozen.PACKAGE,
            'new_predictions':sum(r['status']=='CAPTURED_IMMUTABLE' for r in attempts),'scored_events':report['scored_events'],
            'history_policy_mae':report['metrics']['history_policy']['latest_row_mae'],'private_backup':receipt,
            'operational_adapter':VERSION,'host_dependent':True,'production_change':False,'live_adjustment':0}
        frozen.write_json(runtime/'latest-cycle.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['cycle','watch']);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--support',type=Path,default=Path('/workspace/ops-runtime/2026-11-05-c1-support26-collector'))
    p.add_argument('--archive',type=Path,default=Path('/workspace/ops-runtime/2026-11-04-known-at-source-archive'))
    p.add_argument('--until');p.add_argument('--interval',type=int,default=900);a=p.parse_args()
    manifest,*_=frozen.load_models();frozen.ensure_runtime(a.runtime,manifest)
    if a.action=='cycle':print(json.dumps(cycle(a.runtime,a.support,a.archive)));return
    now=datetime.now(timezone.utc);until=frozen.stamp(a.until).to_pydatetime()
    if not now<until<=now+timedelta(hours=72) or a.interval!=900:raise ValueError('Bounded unchanged 900s cadence required')
    identity=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    configuration={'version':VERSION,'source_sha256':identity,'frozen_manifest_sha256':manifest['_verified_manifest_sha256']}
    path=a.runtime/'score-path-adapter-contract.json'
    if path.exists():
        if json.loads(path.read_text())!=configuration:raise ValueError('Operational adapter source changed')
    else:save(path,configuration)
    with (a.runtime/'watcher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        save(a.runtime/'watcher-launch.json',{'pid':os.getpid(),'started_at':now.isoformat(),'until':until.isoformat(),'interval_seconds':900,
            'host_dependent':True,'operational_adapter':VERSION,'production_change':False,'live_adjustment':0})
        while datetime.now(timezone.utc)<until:
            try:
                if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=identity:raise ValueError('Adapter source changed')
                result=cycle(a.runtime,a.support,a.archive)
            except Exception as exc:
                result={'status':'FAILED_CLOSED','checked_at':datetime.now(timezone.utc).isoformat(),'error_type':type(exc).__name__,
                    'reason':str(exc)[:200],'operational_adapter':VERSION,'production_change':False,'live_adjustment':0}
                save(a.runtime/'latest-cycle.json',result)
            print(json.dumps(result),flush=True)
            time.sleep(min(900,max(0,(until-datetime.now(timezone.utc)).total_seconds())))


if __name__=='__main__':main()
