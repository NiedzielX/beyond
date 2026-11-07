"""Offline engineering test: synthetic outcomes, real frozen forecast replay, no MAE claim."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
from unittest.mock import patch

# Canonical binding also reads the original CLI-built pickle without refitting.
from ml.c1_history_residual_v1 import ResidualRuntime, load_models as history_models
from ml import run_postmatch_outcome_closure_v1 as closure
from ml import run_c1_history_residual_v1 as history
from ml import run_structural_history_refresh_v1 as fresh
from ml import c1_history_scoring_adapter_v1 as adapter
from ml.c1_support26_v1 import score_rows as support_scores, summary as support_summary
from ml.export_structural_known_at_inputs_v1 import TABLES
from ml.postmatch_outcome_source_v1 import SOURCES, TARGETS, VERSION, WARSAW, stamp
from ml.public_attendance_source_audit_v1 import extract
from ml.select_structural_known_at_snapshot_v1 import select_snapshot
from ml.structural_history_refresh_v1 import load_manifest, summary as fresh_summary

SIMULATED_VERIFICATION = '2026-11-06T23:30:00+00:00'
SIMULATED_SCORE_TIME = '2026-11-06T23:31:00+00:00'
TARGET_IDS = {t['id'] for t in TARGETS}
BASE = Path('/workspace/ops-runtime')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def representative_rows(runtime):
    by_event = {}
    for path in (runtime/'evidence').glob('*.json'):
        raw = path.read_bytes(); row = json.loads(raw)
        if row['ticket_event_id'] in TARGET_IDS:
            by_event.setdefault(row['ticket_event_id'], []).append((row, path, raw))
    if set(by_event) != TARGET_IDS:
        raise ValueError('Both actual forecast fixtures must exist before readiness test')
    chosen = []
    for values in by_event.values():
        values.sort(key=lambda item: stamp(item[0]['as_of_at']))
        chosen.extend([values[0], *([values[-1]] if len(values)>1 else [])])
    return chosen


def copy_evidence(source, destination, selected, folders, originals):
    destination.mkdir(parents=True)
    for row, path, raw in selected:
        originals[path] = sha(raw)
        target = destination/'evidence'/path.name; target.parent.mkdir(exist_ok=True)
        target.write_bytes(raw)
        for field, folder in folders:
            keys = row[field] if isinstance(row[field], list) else [row[field]]
            for key in keys:
                if len(key)!=64 or any(c not in '0123456789abcdef' for c in key):
                    raise ValueError('Invalid immutable source key')
                origin=source/folder/(key+'.json'); data=origin.read_bytes()
                if sha(data)!=key:raise ValueError('Original blob hash differs')
                originals[origin]=key
                target=destination/folder/origin.name;target.parent.mkdir(exist_ok=True);target.write_bytes(data)


def synthetic_sources():
    """Fixed capacity/2 outcomes; never selected against forecast values."""
    raw, receipts, sporting = {}, [], []
    for index, (url, target) in enumerate(zip(SOURCES, TARGETS)):
        home, away = ('Motor', 'Wisła Pł.') if index==0 else ('Wisła K.', 'Cracovia')
        local=stamp(target['kickoff_at']).astimezone(WARSAW)
        actual=target['capacity']//2
        line=f'{home} 2:1 {away} {actual} 2026/2027 • Ekstraklasa • {local:%d.%m.%Y %H:%M}'
        raw[url]=('<h1>SYNTHETIC ENGINEERING READINESS ONLY</h1><p>'+line+'</p>').encode()
        receipts.append({'version':VERSION,'url':url,'http_status':200,'retrieved_at':'2026-11-06T23:20:00+00:00',
            'receipt_completed_at':'2026-11-06T23:20:10+00:00','sha256':sha(raw[url]),
            'bytes':len(raw[url]),**extract(raw[url])})
        sporting.append({'source_event_id':str(990000+index),'season':'2026-2027','round_number':14,
            'event_date':local.date().isoformat(),'home_team':target['home_team'],'away_team':target['away_team'],
            'completed':True,'match_status':'FT','home_score':2,'away_score':1,'fetched_at':'2026-11-06T23:15:00+00:00'})
    return receipts,raw,sporting


class SyntheticDatabase:
    """Only an in-memory HTTP/table contract; cannot address any real service."""
    base='https://postmatch-readiness.invalid'
    headers={}

    def __init__(self, parts, sporting):
        self.events=[deepcopy(e) for e in parts['ticket_events'] if e['id'] in TARGET_IDS]
        self.history=deepcopy(parts['history']);self.sporting=sporting;self.outcomes=[];self.posts=0;self.syncs=0
        if any(o['ticket_event_id'] in TARGET_IDS for o in parts['outcomes']):
            raise ValueError('Readiness test must precede genuine target outcomes')
        for target in TARGETS:
            if any(h['club_slug']==target['club_slug'] and stamp(h['kickoff_at'])==stamp(target['kickoff_at']) for h in self.history):
                raise ValueError('Target history already known; no synthetic substitution')

    def counted(self, name, filters=()):
        rows={'ticket_events':self.events,'history':self.history,'sporting':self.sporting,'outcomes':self.outcomes}[name]
        columns=TABLES[name][2].split(',')
        return [{column:deepcopy(row[column]) for column in columns} for row in rows]

    def append(self, request, **kwargs):
        if (request.full_url!=self.base+'/rest/v1/ml_match_history' or request.method!='POST'
                or request.get_header('Prefer')!='return=representation'):
            raise AssertionError('Synthetic test attempted unexpected network operation')
        rows=json.loads(request.data);inserted=[]
        for row in rows:
            if any(h.get('external_match_key')==row['external_match_key'] for h in self.history):
                raise ValueError('Synthetic append attempted duplicate identity')
            row={**row,'id':max([h['id'] for h in self.history],default=0)+1,
                 'created_at':'2026-11-06T23:30:01+00:00','updated_at':'2026-11-06T23:30:01+00:00'}
            self.history.append(row);inserted.append(row)
        self.posts+=1
        response=io.BytesIO(json.dumps(inserted).encode());response.status=201;return response

    def request(self, path, payload=None):
        if path!='rpc/sync_ticket_event_outcomes_from_home_history_v1' or payload!={}:raise AssertionError('Unexpected simulated RPC')
        self.syncs+=1;inserted=0
        for event in self.events:
            matches=[h for h in self.history if h['club_slug']==event['club_slug']
                     and stamp(h['kickoff_at'])==stamp(event['kickoff_at']) and h['competition_key']=='ekstraklasa']
            if stamp(event['kickoff_at'])>=stamp(SIMULATED_VERIFICATION)-timedelta(hours=3):continue
            if any(o['ticket_event_id']==event['id'] for o in self.outcomes):continue
            if len(matches)!=1:raise ValueError('Ambiguous simulated exact-history sync')
            h=matches[0];self.outcomes.append({'ticket_event_id':event['id'],'actual_attendance':h['actual_attendance'],
                'source_name':h['source_name'],'source_url':h['source_url'],'confirmed_at':'2026-11-06T23:30:02+00:00',
                'created_at':'2026-11-06T23:30:02+00:00','updated_at':'2026-11-06T23:30:02+00:00'})
            inserted+=1
        return inserted


def require_failure(operation):
    try:operation()
    except (ValueError, KeyError):return
    raise AssertionError('Corrupted synthetic truth/forecast was accepted')


def run(fresh_runtime, history_runtime, archive):
    real_now=datetime.now(timezone.utc)
    if real_now>=min(stamp(t['kickoff_at']) for t in TARGETS):
        raise ValueError('This readiness protocol is restricted to actual pregame operation')
    cached=select_snapshot(archive,real_now.isoformat())['source']
    if cached is None:raise ValueError('Genuine current cached source required; no DB fallback')
    fresh_selected=representative_rows(fresh_runtime);history_selected=representative_rows(history_runtime)
    manifest=load_manifest();hm,models,bench=history_models(); originals={}
    receipts,raw,sporting=synthetic_sources();db=SyntheticDatabase(cached['parts'],sporting)
    class SimulatedClock:
        @staticmethod
        def now(tz=None):return stamp(SIMULATED_VERIFICATION)
    with tempfile.TemporaryDirectory(prefix='beyond-SYNTHETIC-postmatch-only-') as temp:
        root=Path(temp);fr=root/'fresh';hr=root/'history'
        copy_evidence(fresh_runtime,fr,fresh_selected,[('input_blob_sha256','blobs')],originals)
        copy_evidence(history_runtime,hr,history_selected,[('candidate_blob_sha256','inputs'),('upstream_blob_sha256','upstream'),('source_blob_sha256','sources')],originals)
        (hr/'experiment.json').write_bytes((history_runtime/'experiment.json').read_bytes())
        # Every possible network route is disabled. Only the explicit in-memory
        # POST implementation can run; normal live collectors are separate processes.
        with patch('socket.socket',side_effect=AssertionError('Network forbidden in synthetic readiness')), patch.object(closure,'datetime',SimulatedClock), patch('urllib.request.urlopen',side_effect=db.append):
            applied=closure.apply_verified(root/'apply',{'id':990001},receipts,raw,db)
            if applied['appended_rows']!=2 or applied['actual_target_outcomes']!=2 or db.posts!=1:raise AssertionError('Positive source-to-outcome chain incomplete')
            retried=closure.apply_verified(root/'retry',{'id':990001},receipts,raw,db)
            if retried['appended_rows']!=0 or db.posts!=1 or len(db.outcomes)!=2:raise AssertionError('Append/sync retry is not idempotent')
        now=stamp(SIMULATED_SCORE_TIME);truth=db.counted('outcomes');metadata=db.counted('ticket_events')
        fresh_rows=[item[0] for item in fresh_selected];history_rows=[item[0] for item in history_selected]
        missing=[fresh.score_one(fr,row,manifest,bench,[],metadata,now) for row in fresh_rows]
        if any(row is not None for row in missing):raise AssertionError('Missing truth became a score')
        scored=[fresh.score_one(fr,row,manifest,bench,truth,metadata,now) for row in fresh_rows]
        for row,score in zip(fresh_rows,scored):
            actual=next(o['actual_attendance'] for o in truth if o['ticket_event_id']==row['ticket_event_id'])
            if any(score['absolute_errors'][name]!=abs(value-actual) for name,value in row['forecasts'].items()):raise AssertionError('Absolute error accounting differs')
            if fresh.score_one(fr,row,manifest,bench,truth,metadata,now+timedelta(minutes=1))!=score:raise AssertionError('Immutable score retry changed the original score')
        report=fresh_summary(scored,2,[])
        if report['scored_events']!=2 or report['review_ready'] or report['primary_gate_met'] or report['product_gate_met']:raise AssertionError('Prefix count or early promotion gate differs')
        latest={}
        for score in scored:
            if score['fixture_unit'] not in latest or stamp(score['as_of_at'])>stamp(latest[score['fixture_unit']]['as_of_at']):latest[score['fixture_unit']]=score
        expected=math.fsum(s['absolute_errors']['fresh'] for s in latest.values())/2
        if report['metrics']['fresh']['latest_per_event_mae']!=expected:raise AssertionError('Event-balanced denominator differs')
        hs,hm_missing=history.score_rows(hr,history_rows,truth,metadata,hm,models,bench,now)
        if len({s['ticket_event_id'] for s in hs})!=2 or hm_missing:raise AssertionError('Frozen residual/benchmark positive scoring incomplete')
        bm,benchmark_models,benchmark_hashes=bench;upstream=[];source_inputs={}
        for row in fresh_rows:
            saved=fresh.read_blob(fr,row['input_blob_sha256']);old=saved['benchmark'];upstream.append(old)
            source_inputs[old['candidate_input_sha256']]=saved['candidate']
        paired,missing,count=support_scores(upstream,truth,metadata,bm,benchmark_hashes,now,models=benchmark_models,source_inputs=source_inputs)
        paired_report=support_summary(paired,missing,count)
        if paired_report['scored_independent_events']!=2 or paired_report['first_review_ready']:
            raise AssertionError('Paired benchmark event denominator or review gate differs')
        class SimulatedScoreClock:
            @staticmethod
            def now(tz=None):return now
        class OutcomeReader:
            def request(self,path):
                if path.startswith('ticket_event_outcomes?'):return truth
                if path.startswith('ticket_events?'):return metadata
                raise AssertionError('Heavyweight or unexpected source RPC in readiness test')
        broken=root/'original-cycle-defect'
        copy_evidence(history_runtime,broken,history_selected,[('candidate_blob_sha256','inputs'),('upstream_blob_sha256','upstream'),('source_blob_sha256','sources')],originals)
        (broken/'experiment.json').write_bytes((history_runtime/'experiment.json').read_bytes())
        with patch('socket.socket',side_effect=AssertionError('Network forbidden')), patch.object(history,'Reader',OutcomeReader),patch.object(history,'datetime',SimulatedScoreClock),patch.object(adapter,'datetime',SimulatedScoreClock),patch.object(history,'backup',side_effect=AssertionError('Broken collector must not reach remote backup')):
            require_failure(lambda:history.run_cycle(broken,root/'no-upstream',root/'no-archive'))
            if not (broken/'scores').is_file():raise AssertionError('Expected exact frozen storage caller defect was not reproduced')
        def isolated_backup(runtime):
            if len(list((runtime/'scores').glob('event-*.json')))!=len(hs):raise AssertionError('Scores omitted from recovery input')
            return {'synthetic_only':True,'read_back_verified':True,'files':len(hs)}
        with patch('socket.socket',side_effect=AssertionError('Network forbidden')),patch.object(history,'Reader',OutcomeReader),patch.object(adapter,'datetime',SimulatedScoreClock),patch.object(history,'backup',side_effect=isolated_backup):
            cycle_result=adapter.cycle(hr,root/'no-upstream',root/'no-archive')
            if cycle_result['scored_events']!=2 or not (hr/'scores').is_dir():raise AssertionError('Corrected full positive cycle incomplete')
            before_retry={p.name:sha(p.read_bytes()) for p in (hr/'scores').glob('*.json')}
            adapter.cycle(hr,root/'no-upstream',root/'no-archive')
            if before_retry!={p.name:sha(p.read_bytes()) for p in (hr/'scores').glob('*.json')}:raise AssertionError('History cycle retry overwrote score evidence')
        early=deepcopy(truth);early[0]['created_at']='2026-11-01T00:00:00+00:00'
        first=next(row for row in fresh_rows if row['ticket_event_id']==early[0]['ticket_event_id'])
        require_failure(lambda:fresh.score_one(fr,first,manifest,bench,early,metadata,now))
        require_failure(lambda:history.score_rows(hr,history_rows,early,metadata,hm,models,bench,now))
        require_failure(lambda:fresh.score_one(fr,first,manifest,bench,[*truth,truth[0]],metadata,now))
        revised=deepcopy(truth);revised[0]['updated_at']='2026-11-06T23:30:03+00:00'
        require_failure(lambda:fresh.score_one(fr,first,manifest,bench,revised,metadata,now))
        before=sha((fr/'scores'/f"event-{first['ticket_event_id']}-snapshot-{first['source_snapshot_id']}.json").read_bytes())
        wrong=deepcopy(first);wrong['forecasts']['fresh']+=1
        require_failure(lambda:fresh.score_one(fr,wrong,manifest,bench,truth,metadata,now))
        after=sha((fr/'scores'/f"event-{first['ticket_event_id']}-snapshot-{first['source_snapshot_id']}.json").read_bytes())
        if before!=after:raise AssertionError('Invalid replay altered an immutable score')
    if any(sha(path.read_bytes())!=digest for path,digest in originals.items()):raise AssertionError('Original live evidence was mutated')
    load_manifest();history_models()  # Re-establish exact frozen source/artifact identities.
    return {'version':'postmatch-scoring-readiness-v1','status':'OFFLINE_SYNTHETIC_CHAIN_VERIFIED',
        'checked_at':datetime.now(timezone.utc).isoformat(),'synthetic_only':True,'network_allowed':False,
        'real_outcomes_imported':0,'real_scores_written':0,'models_fitted':0,'attendance_mae':None,
        'simulated_independent_events':2,'fresh_prefixes_replayed':len(fresh_rows),'history_prefixes_replayed':len(history_rows),
        'source_append_readback_sync_and_idempotency_verified':True,'frozen_model_and_all_benchmark_replay_verified':True,
        'original_score_path_defect_reproduced_in_temporary_clone':True,'adapter_full_positive_cycle_and_immutable_retry_verified':True,
        'early_duplicate_revised_labels_and_forecast_substitution_rejected':True,'original_files_hash_verified':len(originals),
        'scientific_review_open':False,'production_change':False,'live_adjustment':0}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fresh-runtime',type=Path,default=BASE/'2026-11-06-structural-history-refresh-collector')
    p.add_argument('--history-runtime',type=Path,default=BASE/'2026-11-05-c1-history-residual-collector')
    p.add_argument('--archive',type=Path,default=BASE/'2026-11-04-known-at-source-archive')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.resolve().is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('Private readiness receipt required')
    if any(a.output.resolve().is_relative_to(p.resolve()) for p in (a.fresh_runtime,a.history_runtime,a.archive)):
        raise ValueError('Synthetic readiness receipt must stay outside real evidence runtimes')
    result=run(a.fresh_runtime,a.history_runtime,a.archive);a.output.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    with a.output.open('x') as file:json.dump(result,file,indent=2,sort_keys=True);file.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()
