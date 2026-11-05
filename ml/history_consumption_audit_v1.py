"""Read-only imported-history consumption audit; no model fitting or forecasts."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path

import pandas as pd

from ml.attendance_knowledge_time_guard_v1 import available_at
from ml.c1_live_matched_audit_v1 import ROOT
from ml.c1_historical_replay_v1 import freeze_state
from ml.demand_engine.current_structural_prior_features import (
    DEFAULT_KEY_ALIASES, HORIZON_DAYS, CurrentStructuralPriorEvent, build_current_structural_prior_row)
from ml.demand_engine.materialize_structural_priors import load_frozen_bundle, build_sporting_state
from ml.export_structural_known_at_inputs_v1 import digest, validate_envelope
from ml.structural_known_at_shadow_v1 import revision_catalog

VERSION = 'verified-history-consumption-audit-v1'
IMPORT_RUN = '41840960556'
FIELDS = ('season_home_n', 'home_history_n', 'baseline_season', 'baseline_r3')


def stamp(value):
    t = pd.Timestamp(value)
    if pd.isna(t) or t.tzinfo is None:
        raise ValueError('Explicit timezone-aware source time required')
    return t.tz_convert('UTC')


def club_key(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Canonical source club required')
    key = value.strip().lower()
    return DEFAULT_KEY_ALIASES.get(key, key)


def fixture_key(row):
    return club_key(row['club_slug']), stamp(row['kickoff_at']).isoformat()


def verified_imports(history):
    selected = [r for r in history if str((r.get('source_payload') or {}).get('verification_run_id')) == IMPORT_RUN]
    if len(selected) != 16 or len({r['id'] for r in selected}) != 16:
        raise ValueError('Exact sixteen verified import identities required')
    if len({fixture_key(r) for r in selected}) != 16:
        raise ValueError('Imported canonical fixture duplicates')
    for row in selected:
        payload = row['source_payload']
        if (not payload.get('source_sha256') or not payload.get('verified_at')
                or payload.get('historical_publication_time_verified') is not False
                or stamp(row['created_at']) < stamp('2026-11-04T17:18:00Z')
                or stamp(payload['verified_at']) > stamp(row['created_at'])+pd.Timedelta(minutes=5)):
            raise ValueError('Verified import provenance/time changed')
    return selected


def source_maps(view, imports):
    groups = {}
    for row in view:
        key = fixture_key(row)
        if key in groups:
            raise ValueError('Public view has duplicate canonical fixtures')
        actual = row['actual_attendance']
        if type(actual) not in (int, float) or not math.isfinite(actual) or actual <= 0:
            raise ValueError('Invalid public history value')
        groups[key] = row
    present = []
    for row in imports:
        found = groups.get(fixture_key(row))
        if found is None or found['actual_attendance'] != row['actual_attendance']:
            raise ValueError('Verified imported value absent/changed in serving view')
        present.append(fixture_key(row))
    return groups, set(present)


def canonical_catalog(parts):
    catalog = revision_catalog(parts)
    return {**catalog, 'records': [{**r, 'club_slug': club_key(r['club_slug'])} for r in catalog['records']]}


def import_known_at(row):
    times = [stamp(row[k]) for k in ('created_at', 'updated_at', 'source_observed_at')]
    verified = (row.get('source_payload') or {}).get('verified_at')
    if verified is not None:
        times.append(stamp(verified))
    return max(times)


def eligible_imports(imports, home_club, boundary):
    return [r for r in imports if club_key(r['club_slug']) == home_club
            and stamp(r['kickoff_at']) < stamp(boundary) and import_known_at(r) <= stamp(boundary)]


def finite_number(value):
    if value is None or pd.isna(value):
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Invalid numerical feature metadata')
    return result


def metadata_slice(row):
    return {k: finite_number(row.get(k)) for k in FIELDS}


def matching(stored, reconstructed):
    if set(stored) != set(FIELDS) or set(reconstructed) != set(FIELDS):
        return False
    if any(stored[k] is None or reconstructed[k] is None for k in ('season_home_n', 'home_history_n')):
        return False
    for k in FIELDS:
        if stored[k] is None or reconstructed[k] is None:
            if stored[k] != reconstructed[k]: return False
        elif not math.isclose(stored[k], reconstructed[k], rel_tol=0, abs_tol=1e-7): return False
    return True


def evidence_level(stored, with_imports, without_imports):
    yes, no = matching(stored, with_imports), matching(stored, without_imports)
    if yes and no: return 'IMPORTS_NOT_DISTINGUISHABLE_IN_HOME_METADATA'
    if yes: return 'HOME_METADATA_MATCHES_WITH_IMPORTS'
    if no: return 'HOME_METADATA_MATCHES_WITHOUT_IMPORTS'
    return 'HOME_METADATA_DIFFERS_CURRENT_RECONSTRUCTION'


def build_metadata(rows, historical, sporting, aliases, event, horizon):
    frame = pd.DataFrame(rows, columns=['club_slug', 'kickoff_at', 'actual_attendance', 'season'])
    cutoff = event.kickoff_at-pd.Timedelta(days=HORIZON_DAYS[horizon])
    state = build_sporting_state(sporting, aliases, as_of_at=cutoff, source_season=event.season)
    feature = build_current_structural_prior_row(historical_matches=historical, current_attendance=frame,
        sporting_state=state, event=event, horizon=horizon).iloc[0]
    return metadata_slice({'season_home_n':feature['season_home_n'], 'home_history_n':feature['home_history_n'],
                           'baseline_season':feature['baseline_season'], 'baseline_r3':feature['baseline_r3']})


def audit(source, captured, artifact_dir=ROOT/'ml/artifacts/structural_prior_runtime_v1'):
    validate_envelope(source)
    if (captured.get('version') != 'history-consumption-source-v1' or captured.get('read_only') is not True
            or captured.get('production_change') is not False or captured.get('live_adjustment') != 0
            or captured.get('sha256') != digest({k:v for k,v in captured.items() if k != 'sha256'})
            or captured.get('history_export_sha256') != source['export_sha256']
            or captured.get('view_total') != len(captured['view'])):
        raise ValueError('History/view/prior source envelope differs')
    started, completed = stamp(captured['requested_at']), stamp(captured['completed_at'])
    if completed < started or completed-started > pd.Timedelta(minutes=10):
        raise ValueError('Invalid bounded audit capture interval')
    parts = source['parts']; imports = verified_imports(parts['history'])
    view, imported_keys = source_maps(captured['view'], imports)
    catalog = canonical_catalog(parts)
    canonical = {r['id']:r for r in parts['ticket_events']}
    aliases = {r['alias']:r['club_key'] for r in parts['aliases']}
    _, historical, models = load_frozen_bundle(artifact_dir, set())
    assert not models  # Source-feature reconstruction must not load/fit/predict a learner.
    rows, missing, seen = [], [], set()
    for item in captured['priors']:
        identity = (item['ticket_event_id'], item['horizon'])
        if identity in seen or len(item['rows']) != 1: raise ValueError('Duplicate/malformed prior audit identity')
        seen.add(identity)
        p = item['rows'][0]; target = canonical[item['ticket_event_id']]
        cutoff, kickoff = stamp(p['target_as_of_at']), stamp(p['kickoff_at'])
        if (p['horizon'] != item['horizon'] or p['ticket_event_id'] != item['ticket_event_id']
                or kickoff != stamp(target['kickoff_at']) or cutoff > started
                or kickoff <= started or cutoff != kickoff-pd.Timedelta(days=HORIZON_DAYS[p['horizon']])):
            raise ValueError('Actual future target/prior cutoff identity differs')
        if p['status'] != 'ready':
            missing.append({'ticket_event_id': identity[0], 'horizon':identity[1], 'status':p['status']}); continue
        if p.get('point_in_time_validated') is not True or stamp(p['generated_at']) > stamp(item['read_requested_at']):
            raise ValueError('Invalid stored prior availability')
        local = kickoff.tz_convert('Europe/Warsaw'); year = local.year if local.month >= 7 else local.year-1
        season = f'{year}/{year+1}'
        metadata = p.get('metadata') or {}
        if not set(FIELDS).issubset(metadata) or metadata.get('round_no') is None:
            missing.append({'ticket_event_id': identity[0], 'horizon':identity[1], 'status':'STORED_METADATA_INCOMPLETE'}); continue
        event = CurrentStructuralPriorEvent(ticket_event_id=target['id'], season=season,
            round_no=int(metadata['round_no']), kickoff_at=kickoff, home_club_key=aliases[target['home_team']],
            away_club_key=aliases[target['away_team']], stadium_capacity=int(p['stadium_capacity']))
        full = build_metadata(list(view.values()), historical, parts['sporting'], aliases, event, p['horizon'])
        without = build_metadata([r for key,r in view.items() if key not in imported_keys], historical,
                                 parts['sporting'], aliases, event, p['horizon'])
        known = available_at(catalog, cutoff.isoformat())
        if known['conflicts']:
            rows.append({'ticket_event_id':target['id'],'horizon':p['horizon'],'status':'CONFLICTING_KNOWN_SOURCE',
                         'conflicts':known['conflicts']});continue
        strict = build_metadata([r for r in known['eligible'] if r['season']==season], historical,
                                parts['sporting'], aliases, event, p['horizon'])
        stored = metadata_slice(metadata)
        home_imports = [r for r in imports if club_key(r['club_slug'])==event.home_club_key
                        and stamp(r['kickoff_at'])<cutoff]
        valid_at_cutoff = eligible_imports(imports,event.home_club_key,cutoff)
        valid_at_generation = eligible_imports(imports,event.home_club_key,p['generated_at'])
        rows.append({'ticket_event_id':target['id'],'source_prior_id':p['source_prior_id'],
            'home_club_key':event.home_club_key,'horizon':p['horizon'],'cutoff':cutoff.isoformat(),
            'generated_at':p['generated_at'],'status':evidence_level(stored,full,without),
            'stored_home_metadata':stored,'current_unfiltered_home_metadata':full,
            'current_without_imports_home_metadata':without,'known_at_cutoff_home_metadata':strict,
            'stored_matches_known_at_cutoff':matching(stored,strict),
            'home_import_rows_before_cutoff':len(home_imports),'home_import_rows_known_at_cutoff':len(valid_at_cutoff),
            'home_import_rows_known_at_generation':len(valid_at_generation),
            'generated_after_cutoff':stamp(p['generated_at'])>cutoff,
            'exact_source_row_consumption_proven':False,
            'feature_hash_exposed_by_prior_rpc':False})
    summary={'version':VERSION,'checked_at':datetime.now(timezone.utc).isoformat(),
        'source_export_sha256':source['export_sha256'],'prior_view_capture_sha256':captured['sha256'],
        'verified_import_rows':len(imports),'verified_imports_present_in_serving_view':len(imported_keys),
        'serving_view_rows':len(view),'queried_event_horizons':len(seen),'stored_prior_rows_audited':len(rows),
        'missing_or_incomplete_priors':len(missing),'evidence_counts':dict(Counter(r['status'] for r in rows)),
        'stored_rows_matching_knowledge_safe_home_metadata':sum(r.get('stored_matches_known_at_cutoff',False) for r in rows),
        'exact_source_row_consumption_proven':False,'model_fit_performed':False,'forecast_created':False,
        'attendance_accuracy_measured':False,'production_change':False,'live_adjustment':0,
        'limits':['prior RPC exposes aggregates, not original per-source rows or feature hash',
                  'current revised sporting/history values do not independently prove original serving inputs',
                  'import presence and metadata matches are not an MAE improvement']}
    return summary, {'summary':summary,'priors':rows,'missing_priors':missing,
                      'import_source_ids':[r['id'] for r in imports],'rejected_source_count':len(catalog['rejected_sources'])}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output-dir',type=Path);a=p.parse_args()
    if a.runtime.resolve().is_relative_to(ROOT):raise ValueError('Raw audit evidence must remain private')
    source=json.loads((a.runtime/'current-export/inputs.json').read_text())
    captured=json.loads((a.runtime/'consumption-sources.json').read_text())
    before=freeze_state();summary,detail=audit(source,captured)
    if freeze_state()!=before:raise ValueError('Frozen artifact changed')
    output=a.output_dir or a.runtime
    if output.resolve().is_relative_to(ROOT):raise ValueError('Audit results must remain private')
    output.mkdir(mode=0o700,parents=True,exist_ok=True)
    summary['implementation_sha256']=__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest()
    for name,value in [('result.json',detail),('public-summary.json',summary)]:
        with (output/name).open('x') as f:json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    print(json.dumps(summary,allow_nan=False))


if __name__=='__main__':main()
