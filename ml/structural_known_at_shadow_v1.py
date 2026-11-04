"""Separate non-persistable attendance-guard integration with frozen predictors.

No official prior writes, model fitting, scorer or prospective lane activation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pandas as pd

from ml.attendance_knowledge_time_guard_v1 import VERSION as GUARD_VERSION, COMPETITIONS, source_catalog, available_at, timestamp
from ml.export_structural_known_at_inputs_v1 import validate_envelope, digest, ROOT
from ml.demand_engine.current_structural_prior_features import HORIZON_DAYS, DEFAULT_KEY_ALIASES
from ml.demand_engine.materialize_structural_priors import materialize

VERSION = 'structural-known-at-nonpersistable-shadow-v1'
REVISION_CONTRACT = 'attendance-source-known-at-with-row-revisions-v1'


def revision_catalog(parts):
    """A revised current row cannot stand in for an unavailable old row value."""
    catalog = source_catalog(parts['history'], parts['outcomes'], parts['ticket_events'])
    raw = {('history',r['id']):r for r in parts['history']}
    raw.update({('outcome',r['ticket_event_id']):r for r in parts['outcomes']})
    verified = []
    for record in catalog['records']:
        row = raw[(record['source_kind'],record['source_id'])]
        try: revised = timestamp(row.get('updated_at'))
        except ValueError:
            catalog['rejected_sources'].append({'source_kind':record['source_kind'], 'source_id':record['source_id'],
                'reason':'ROW_REVISION_TIME_UNKNOWN'})
            continue
        if revised < timestamp(row['created_at']):
            catalog['rejected_sources'].append({'source_kind':record['source_kind'], 'source_id':record['source_id'],
                'reason':'ROW_REVISION_PRECEDES_CREATION'})
            continue
        verified.append({**record, 'known_at':max(timestamp(record['known_at']),revised).isoformat(),
                         'row_updated_at':revised.isoformat()})
    return {**catalog, 'records':verified, 'revision_contract':REVISION_CONTRACT}


def prepare(payload, generated_at, activation_at):
    """Per-event private inputs; explicit activation prevents missed-cutoff repair."""
    validate_envelope(payload)
    now, activation = timestamp(generated_at), timestamp(activation_at)
    started, completed = timestamp(payload['requested_at']), timestamp(payload['completed_at'])
    if completed > now or now-started > timedelta(minutes=15) or activation > now:
        raise ValueError('Stale/future source capture or future activation boundary')
    parts = payload['parts']; catalog = revision_catalog(parts)
    target_outcomes = {r['ticket_event_id'] for r in parts['outcomes']}
    canonical = {r['id']:r for r in parts['ticket_events']}
    result, attempts = [], []
    due_ids = [r['ticket_event_id'] for r in parts['due']]
    if len(set(due_ids)) != len(due_ids): raise ValueError('Duplicate due target identity')
    for event in parts['due']:
        event_id = event['ticket_event_id']; base = {'ticket_event_id': event_id, 'horizon': event['horizon']}
        if any(k in event for k in ['actual_attendance','target_attendance','attendance_label']):
            raise ValueError('Attendance target forbidden in due event inputs')
        if event['input_status'] != 'ready':
            attempts.append({**base, 'status': 'INPUT_NOT_READY'}); continue
        if event['horizon'] not in HORIZON_DAYS: raise ValueError('Unknown canonical horizon')
        kickoff, cutoff = timestamp(event['kickoff_at']), timestamp(event['target_as_of_at'])
        if cutoff != kickoff-timedelta(days=HORIZON_DAYS[event['horizon']]):
            raise ValueError('Canonical cutoff drift')
        target = canonical.get(event_id)
        if (target is None or timestamp(target['kickoff_at']) != kickoff
                or any(target[k] != event[k] for k in ['home_team', 'away_team'])
                or target['competition'] not in COMPETITIONS
                or DEFAULT_KEY_ALIASES.get(target['club_slug'], target['club_slug']) != event['home_club_key']):
            raise ValueError('Canonical target identity mismatch')
        target_history_known = False
        for history in parts['history']:
            if history.get('club_slug') != target['club_slug'] or history.get('actual_attendance') is None: continue
            try: target_history_known |= timestamp(history.get('kickoff_at')) == kickoff
            except ValueError: continue  # Invalid source is already rejected by the catalog.
        if event_id in target_outcomes or target_history_known:
            attempts.append({**base, 'status': 'TARGET_OUTCOME_ALREADY_KNOWN'}); continue
        if cutoff < activation:
            attempts.append({**base, 'status': 'PRE_ACTIVATION_NO_BACKFILL'}); continue
        if now < cutoff:
            attempts.append({**base, 'status': 'NOT_DUE'}); continue
        if kickoff <= now or now > cutoff+timedelta(minutes=90):
            attempts.append({**base, 'status': 'WINDOW_CLOSED_NO_BACKFILL'}); continue
        audit = available_at(catalog, cutoff.isoformat())
        if audit['conflicts']:
            attempts.append({**base, 'status': 'CONFLICTING_KNOWN_ATTENDANCE', 'conflicts': audit['conflicts']}); continue
        attendance = [{k:r[k] for k in ['club_slug','kickoff_at','actual_attendance','season','source_name','source_url']}
                      for r in audit['eligible'] if r['season'] == event['season']]
        result.append({'event': event, 'audit': audit, 'input': {'events': [event], 'aliases': parts['aliases'],
            'attendance': attendance, 'sportingMatches': parts['sporting']}})
        attempts.append({**base, 'status': 'GUARDED_INPUT_READY', 'eligible_attendance_rows': len(attendance)})
    return result, attempts


def infer(payload, artifact_dir, generated_at, activation_at, predictor=None):
    # Always validate before loading/calling any predictor; no-due never predicts.
    prepared, attempts = prepare(payload, generated_at, activation_at)
    if prepared and predictor is None:
        manifest = json.loads((Path(artifact_dir)/'manifest.json').read_text())
        for item in prepared:
            spec = manifest['artifacts'][item['event']['horizon']]
            if any(item['event'][k] != spec[k] for k in ['model_spec_id','model_family','feature_contract']):
                raise ValueError('Frozen predictor metadata contract mismatch')
    predictor = predictor or materialize; forecasts = []
    for item in prepared:
        original = predictor(item['input'], Path(artifact_dir), pd.Timestamp(generated_at))
        if original.get('version') != 'structural-prior-materializer-v1' or len(original['predictions']) != 1:
            raise ValueError('Frozen predictor did not return one exact event')
        row = original['predictions'][0]
        if row['ticket_event_id'] != item['event']['ticket_event_id'] or timestamp(row['target_as_of_at']) != timestamp(item['event']['target_as_of_at']):
            raise ValueError('Frozen predictor target/cutoff mismatch')
        forecasts.append({'frozen_predictor_output': row, 'attendance_input_contract': GUARD_VERSION,
            'row_revision_contract': REVISION_CONTRACT,
            'attendance_source_manifest_sha256': digest(item['audit']), 'source_audit': item['audit']})
    # Intentionally no top-level `predictions`: old gateway cannot persist this.
    return {'version': VERSION, 'generated_at': generated_at, 'activation_at': activation_at,
        'source_export_sha256': payload['export_sha256'], 'attempts': attempts, 'shadow_forecasts': forecasts,
        'official_persistence_allowed': False, 'prospective_lane_activated': False,
        'production_change': False, 'live_adjustment': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True); p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--artifact-dir', type=Path, required=True); p.add_argument('--activation-at', required=True)
    a = p.parse_args(); output = a.output_dir.resolve()
    if output.is_relative_to(ROOT): raise ValueError('Private shadow evidence must remain outside Git')
    if output.exists(): raise ValueError('Never overwrite a previous shadow inspection')
    payload = json.loads(a.input.read_text()); now = datetime.now(timezone.utc).isoformat()
    result = infer(payload, a.artifact_dir, now, a.activation_at)
    output.mkdir(mode=0o700, parents=True)
    file = output/'inspection.json'
    with file.open('x') as stream: json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    file.chmod(0o600)
    print(json.dumps({'version': VERSION, 'attempts': len(result['attempts']), 'shadow_forecasts': len(result['shadow_forecasts']),
        'official_persistence_allowed': False, 'production_change': False}))


if __name__ == '__main__': main()
