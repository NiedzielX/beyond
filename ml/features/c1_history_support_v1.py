"""Point-in-time historical-home support for one fixed residual ablation."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ml.attendance_knowledge_time_guard_v1 import available_at
from ml.demand_engine.current_structural_prior_features import DEFAULT_KEY_ALIASES
from ml.export_structural_known_at_inputs_v1 import digest, validate_envelope
from ml.structural_known_at_shadow_v1 import revision_catalog

VERSION='c1-known-at-home-support-features-v1'
BASE_FEATURES=('prior_occupancy','available_share','removed_24h_share','removed_6h_share','horizon_days','observed_span_days')
HISTORY_FEATURES=('verified_home_n_log','verified_home_recent_gap','verified_home_age_days')
FEATURES=BASE_FEATURES+HISTORY_FEATURES


def stamp(value):
    t=pd.Timestamp(value)
    if pd.isna(t) or t.tzinfo is None:raise ValueError('Explicit source/feature time required')
    return t.tz_convert('UTC')


def canonical_club(value):
    key=str(value).strip().lower()
    if not key or key=='none':raise ValueError('Canonical club required')
    return DEFAULT_KEY_ALIASES.get(key,key)


def catalog(payload):
    validate_envelope(payload)
    c=revision_catalog(payload['parts'])
    return {**c,'records':[{**r,'club_slug':canonical_club(r['club_slug'])} for r in c['records']]}


def known_home_features(c, *, club, as_of_at, kickoff_at, capacity, prior_p50):
    issue,kickoff=stamp(as_of_at),stamp(kickoff_at)
    if issue>=kickoff:raise ValueError('Feature source must precede target kickoff')
    if (not np.isfinite([capacity,prior_p50]).all() or capacity<=0 or not 0<=prior_p50<=capacity):
        raise ValueError('Invalid shared prior/capacity')
    home=canonical_club(club)
    local=kickoff.tz_convert('Europe/Warsaw');year=local.year if local.month>=7 else local.year-1
    season=f'{year}/{year+1}'
    # Only this home's current-season history enters these features.
    relevant={**c,'records':[r for r in c['records'] if r['club_slug']==home and r['season']==season]}
    audit=available_at(relevant,issue.isoformat())
    if audit['conflicts']:raise ValueError('Conflicting known home attendance')
    past=sorted(audit['eligible'],key=lambda r:stamp(r['kickoff_at']))
    matchdays={}
    for r in past:
        date=stamp(r['kickoff_at']).tz_convert('Europe/Warsaw').date()
        if date==local.date():raise ValueError('Target canonical fixture attendance cannot enter features')
        if date in matchdays:raise ValueError('Ambiguous home matchday clocks; no tolerance join')
        matchdays[date]=r
    n=len(past)
    recent=float(np.mean([r['actual_attendance'] for r in past[-3:]])) if past else None
    age=(issue-stamp(past[-1]['kickoff_at'])).total_seconds()/86400 if past else None
    values={'verified_home_n_log':math.log1p(n),
        'verified_home_recent_gap':float('nan') if recent is None else (recent-prior_p50)/capacity,
        'verified_home_age_days':float('nan') if age is None else age}
    manifest={'version':VERSION,'club':home,'season':season,'as_of_at':issue.isoformat(),
        'kickoff_at':kickoff.isoformat(),'verified_home_n':n,
        'source_records':[{'kind':r['source_kind'],'id':r['source_id'],'known_at':r['known_at'],
                           'kickoff_at':r['kickoff_at']} for r in past],
        'unknown_or_rejected_source_count':len(c['rejected_sources']),
        'zero_known_rows_is_not_zero_attendance':True}
    manifest['sha256']=digest(manifest)
    return values,manifest


def numeric(row,name):
    value=row.get(name)
    if value is None or pd.isna(value):return float('nan')
    if isinstance(value,bool):raise ValueError('Numeric live feature is boolean')
    value=float(value)
    if not math.isfinite(value):raise ValueError('Non-finite live feature')
    return value


def feature_row(row, fixture, payload, *, historical_reconstruction=False):
    """No target labels enter this interface; source snapshots precede forward features."""
    if 'actual_attendance' in row or 'target_attendance' in row:raise ValueError('Separate target labels before feature preparation')
    asof,kickoff=stamp(row['as_of_at']),stamp(fixture['kickoff_at'])
    if not kickoff-pd.Timedelta(hours=24)<asof<kickoff:raise ValueError('Only genuine final24source times supported')
    if not historical_reconstruction and not pd.Timedelta(0)<=asof-stamp(payload['completed_at'])<=pd.Timedelta(minutes=60):
        raise ValueError('Forward feature requires a fresh actual source capture at/before its observation')
    capacity=numeric(row,'stadium_capacity');prior=numeric(row,'prior_p50')
    h,manifest=known_home_features(catalog(payload),club=fixture['club_slug'],as_of_at=asof,
                                 kickoff_at=kickoff,capacity=capacity,prior_p50=prior)
    result={'prior_occupancy':prior/capacity,'available_share':numeric(row,'available_total')/capacity,
        'removed_24h_share':numeric(row,'net_removed_24h')/capacity,
        'removed_6h_share':numeric(row,'net_removed_6h')/capacity,
        'horizon_days':(kickoff-asof).total_seconds()/86400,
        'observed_span_days':numeric(row,'observation_window_hours')/24,**h}
    if tuple(result)!=FEATURES:raise ValueError('Fixed feature schema changed')
    manifest.update(source_export_sha256=payload['export_sha256'],
        historical_reconstruction=historical_reconstruction,
        original_source_snapshot_used=not historical_reconstruction,
        historical_publication_times_independently_verified=False)
    manifest.pop('sha256',None)
    manifest['sha256']=digest(manifest)
    return result,manifest


def prepare_training_features(frame,fixtures,payload):
    if 'actual_attendance' in frame.columns:raise ValueError('Target-free preparation requires target column excluded by parser')
    values=[];manifests=[]
    by_id={int(r['id']):r for r in fixtures}
    if len(by_id)!=len(fixtures):raise ValueError('Duplicate canonical fixture identities')
    for row in frame.to_dict('records'):
        fixture=by_id[int(row['ticket_event_id'])]
        result,manifest=feature_row(row,fixture,payload,historical_reconstruction=True)
        values.append(result);manifests.append({'ticket_event_id':int(row['ticket_event_id']),**manifest})
    return pd.DataFrame(values,columns=FEATURES),manifests
