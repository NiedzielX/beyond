"""Read-only preparation of expanded exposed training support; never fits/scores."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml.export_c1_matched_audit_inputs_v1 import Reader
from ml.c1_live_matched_audit_v1 import ROOT
from ml.demand_engine.run_c1_shadow_v8 import feature_record
from ml.attendance_knowledge_time_guard_v1 import COMPETITIONS
from ml.demand_engine.current_structural_prior_features import DEFAULT_KEY_ALIASES

VERSION='c1-training-support-data26-v1'
BASE_SHA='be9aab4721e69661b8f14d3e1e8938abde569dabd6f7878e0986868fc0756549'
BASE_IDS=(1,3,4,5,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23)
NEW_IDS=(6,443,444,445,446,447)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def fixture_units(events):
    required=set(BASE_IDS+NEW_IDS);selected=[e for e in events if e['id'] in required]
    if len(selected)!=26 or {e['id'] for e in selected}!=required:raise ValueError('Canonical26fixture coverage missing or duplicated')
    keys=[];clubs=[]
    for event in selected:
        if event['competition'] not in COMPETITIONS:raise ValueError('Canonical competition outside frozen scope')
        kickoff=pd.Timestamp(event['kickoff_at'])
        if kickoff.tzinfo is None:raise ValueError('Canonical fixture time is naive')
        club=DEFAULT_KEY_ALIASES.get(event['club_slug'],event['club_slug']);clubs.append(club)
        keys.append((club,kickoff.tz_convert('Europe/Warsaw').date()))
    if len(set(keys))!=26:raise ValueError('Multiple ticket IDs refer to the same home-club matchday')
    return {'independent_fixtures':26,'training_clubs':len(set(clubs))}


def validate_row(event,truth,prior,feature,snapshot,known_at,runtime):
    as_of=pd.Timestamp(event['latest_as_of_at']);kickoff=pd.Timestamp(event['kickoff_at']);known=pd.Timestamp(known_at)
    stamps=[as_of,kickoff,known,pd.Timestamp(truth['confirmed_at']),pd.Timestamp(prior['generated_at']),
            pd.Timestamp(feature['as_of_at']),pd.Timestamp(snapshot['captured_at'])]
    if any(pd.isna(t) or t.tzinfo is None for t in stamps):raise ValueError('Explicit timezone-aware source times required')
    if (pd.Timestamp(truth['confirmed_at'])>known or truth['actual_attendance']!=event['actual_attendance']
            or not kickoff-pd.Timedelta(hours=24)<as_of<kickoff<known
            or pd.Timestamp(truth['confirmed_at'])<kickoff):
        raise ValueError('Invalid target timing or label knowledge')
    if (prior.get('status')!='ready' or prior.get('horizon')!='T-1' or prior.get('point_in_time_validated') is not True
            or pd.Timestamp(prior['generated_at'])>as_of or prior['ticket_event_id']!=event['ticket_event_id']
            or abs(float(prior['p50'])-event['structural_prior_p50'])>1e-7):
        raise ValueError('Actual stored prior identity/value/availability mismatch')
    if (feature.get('point_in_time_validated') is not True or pd.Timestamp(feature['as_of_at'])!=as_of
            or snapshot['ticket_event_id']!=event['ticket_event_id'] or snapshot['id']!=feature.get('snapshot_id')
            or pd.Timestamp(snapshot['captured_at'])!=as_of):
        raise ValueError('Feature/snapshot/actual forecast time mismatch')
    if any(k in feature for k in ['actual_attendance','target_attendance','attendance_label']):
        raise ValueError('Target attendance must stay outside feature inputs')
    record=feature_record({'prior':prior},{'features':feature},runtime)
    actual=float(truth['actual_attendance']);capacity=float(prior['stadium_capacity'])
    if not 0<actual<=capacity:raise ValueError('Invalid target/capacity')
    reconstructed=float(runtime.predict_live_p50(pd.DataFrame([record]))[0])
    error=abs(reconstructed-event['v2_live_p50'])
    if not np.isfinite(error) or error>1e-7:raise ValueError('Frozen serving prediction does not reproduce')
    return {**record,'ticket_event_id':event['ticket_event_id'],'as_of_at':as_of.isoformat(),
            'actual_attendance':actual},error


def append_frame(base_raw,records,features,expected_base_sha=BASE_SHA):
    if sha(base_raw)!=expected_base_sha:raise ValueError('Frozen20event CSV bytes changed')
    base=pd.read_csv(io.BytesIO(base_raw),float_precision='round_trip')
    if len(base)!=74 or tuple(sorted(base.ticket_event_id.unique()))!=BASE_IDS:
        raise ValueError('Frozen20event support changed')
    if set(base.columns)!=set(features)|{'ticket_event_id','as_of_at','actual_attendance'}:
        raise ValueError('Frozen feature frame columns changed')
    if tuple(c for c in base.columns if c in features)!=tuple(features):
        raise ValueError('Frozen feature order changed')
    added=pd.DataFrame(records)
    if len(added)!=6 or tuple(sorted(added.ticket_event_id))!=NEW_IDS or added.duplicated(['ticket_event_id','as_of_at']).any():
        raise ValueError('Exactly six disjoint verified source rows required')
    if set(added.columns)!=set(base.columns):raise ValueError('Expanded rows changed feature schema')
    if not base_raw.endswith(b'\n'):raise ValueError('Frozen CSV prefix requires its original final newline')
    appended=added[list(base.columns)].to_csv(index=False,header=False).encode()
    result=base_raw+appended
    if not result.startswith(base_raw):raise ValueError('Frozen prefix was rewritten')
    combined=pd.read_csv(io.BytesIO(result),float_precision='round_trip')
    if len(combined)!=80 or combined.ticket_event_id.nunique()!=26:
        raise ValueError('Expanded support is not26events/80rows')
    return result


def prepare(base_csv,output_dir):
    output_dir=Path(output_dir).resolve()
    if output_dir.is_relative_to(ROOT) or output_dir.exists():raise ValueError('New private output directory required')
    raw=Path(base_csv).read_bytes()
    if sha(raw)!=BASE_SHA:raise ValueError('Do not rebuild the frozen training CSV')
    base_frame=pd.read_csv(io.BytesIO(raw),float_precision='round_trip')
    reader=Reader();started=datetime.now(timezone.utc).isoformat()
    events=reader.request('dashboard_c1_shadow_v8_events_v1?select=*&limit=1000')
    outcomes=reader.request('ticket_event_outcomes?select=*&limit=1000')
    fixtures=reader.request('ticket_events?select=id,club_slug,competition,kickoff_at&limit=1000')
    if len(events)>=1000 or len(outcomes)>=1000:raise ValueError('Small source expanded; no truncation allowed')
    if len(fixtures)>=1000:raise ValueError('Canonical fixture export expanded')
    units=fixture_units(fixtures)
    event_by={r['ticket_event_id']:r for r in events};truth_by={r['ticket_event_id']:r for r in outcomes}
    old_manifest=json.loads((ROOT/'ml/artifacts/c1_shadow_v8/manifest.json').read_text());artifact=ROOT/'ml/artifacts/c1_shadow_v8'/old_manifest['artifact']['filename']
    if sha(artifact.read_bytes())!=old_manifest['artifact']['sha256']:raise ValueError('Frozen runtime changed')
    runtime=joblib.load(artifact);records=[];inputs=[];parity=[]
    for event_id in NEW_IDS:
        event,truth=event_by[event_id],truth_by[event_id]
        if event.get('outcome_available') is not True or event.get('package_version')!='c1-shadow-v8-frozen-2026-10-16-n9':
            raise ValueError('Expected actually evaluated original C1forecast')
        priors=reader.request('rpc/get_structural_prior_v1',{'p_ticket_event_id':event_id,'p_requested_as_of_at':event['latest_as_of_at']})
        if len(priors)!=1:raise ValueError('One actual prior required')
        prior=priors[0]
        features=reader.request('rpc/get_live_trajectory_features_v1_1_asof',{'p_ticket_event_id':event_id,
            'p_as_of':event['latest_as_of_at'],'p_stadium_capacity':prior['stadium_capacity']})
        if len(features)!=1:raise ValueError('One actual source feature record required')
        f=features[0];snapshots=reader.request('snapshots?select=id,ticket_event_id,captured_at&id=eq.'+str(int(f['snapshot_id'])))
        if len(snapshots)!=1:raise ValueError('One immutable source snapshot required')
        record,error=validate_row(event,truth,prior,f,snapshots[0],started,runtime)
        records.append(record);parity.append(error)
        inputs.append({'event':event,'truth':truth,'prior':prior,'feature':f,'snapshot':snapshots[0]})
    for event_id in BASE_IDS:
        expected=base_frame.loc[base_frame.ticket_event_id==event_id,'actual_attendance'].unique()
        if len(expected)!=1 or float(expected[0])!=truth_by[event_id]['actual_attendance']:
            raise ValueError('Old training label changed')
    combined=append_frame(raw,records,runtime.features)
    manifest={'version':VERSION,'prepared_at':datetime.now(timezone.utc).isoformat(),'label_knowledge_cutoff':started,
        'events':26,'rows':80,'base_events':20,'base_rows':74,'added_events':list(NEW_IDS),'added_rows':6,**units,
        'features':list(runtime.features),'all_events_training_exposed':True,'fresh_validation_events':0,
        'base_csv_sha256':BASE_SHA,'combined_csv_sha256':sha(combined),'base_prefix_byte_identical':True,
        'base_prefix_bytes':len(raw),
        'preparation_code_sha256':sha(Path(__file__).read_bytes()),'old_runtime_artifact_sha256':old_manifest['artifact']['sha256'],
        'new_rows_sampling':'one actually persisted latest C1-time point per added event; frozen-feature reconstruction, not a dump of original private input vectors',
        'max_original_serving_reconstruction_error':max(parity),'model_fit':False,'attendance_mae_computed':False,
        'prospective_forecasts_issued':0,'production_change':False,'live_adjustment':0}
    output_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
    for name,body in [('training.csv',combined),('sources.json',(json.dumps(inputs,indent=2)+'\n').encode()),
                      ('canonical-fixtures.json',(json.dumps([e for e in fixtures if e['id'] in set(BASE_IDS+NEW_IDS)],indent=2)+'\n').encode()),
                      ('manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())]:
        with (output_dir/name).open('xb') as stream:stream.write(body)
        (output_dir/name).chmod(0o600)
    print(json.dumps(manifest))
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-csv',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();prepare(a.base_csv,a.output_dir)


if __name__=='__main__':main()
