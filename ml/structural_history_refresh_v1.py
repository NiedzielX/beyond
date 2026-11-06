"""New actual-knowledge forecasts from the unchanged frozen T1structural model."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from ml.attendance_knowledge_time_guard_v1 import available_at, COMPETITIONS
from ml.c1_history_residual_v1 import fixture_unit, TRAIN_IDS
from ml.demand_engine.materialize_structural_priors import materialize, load_frozen_bundle
from ml.export_structural_known_at_inputs_v1 import digest
from ml.features.c1_history_support_v1 import catalog, canonical_club

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'structural-history-refresh-shadow-v1-2026-11-06'
ARTIFACT = ROOT/'ml/artifacts/structural_history_refresh_v1'
STRUCTURAL = ROOT/'ml/artifacts/structural_prior_runtime_v1'
PROTOCOL = ROOT/'ml/STRUCTURAL_HISTORY_REFRESH_PRECOMMIT_V1.md'
BASELINES = ('prior', 'median26_policy', 'median20_policy', 'ridge20_policy', 'original9_policy')
SOURCES = ('ml/structural_history_refresh_v1.py', 'ml/run_structural_history_refresh_v1.py',
    'ml/features/c1_history_support_v1.py', 'ml/c1_history_residual_v1.py',
    'ml/c1_support26_v1.py', 'ml/attendance_knowledge_time_guard_v1.py',
    'ml/structural_known_at_shadow_v1.py', 'ml/export_structural_known_at_inputs_v1.py',
    'ml/select_structural_known_at_snapshot_v1.py', 'ml/demand_engine/materialize_structural_priors.py',
    'ml/demand_engine/current_structural_prior_features.py', 'ml/demand_engine/structural_prior_runtime.py')


def stamp(value):
    result = pd.Timestamp(value)
    if pd.isna(result) or result.tzinfo is None:
        raise ValueError('Explicit aware source/issue time required')
    return result.tz_convert('UTC')


def hashes():
    names = [*SOURCES, str(PROTOCOL.relative_to(ROOT))]
    names += [str(p.relative_to(ROOT)) for p in STRUCTURAL.iterdir() if p.is_file()]
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(names)}


def freeze(directory=ARTIFACT, published_commit=None):
    import re
    if not isinstance(published_commit, str) or not re.fullmatch('[0-9a-f]{40}', published_commit):
        raise ValueError('Published source receipt identity required')
    directory.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    (directory/'FREEZE_STARTED.json').write_text(json.dumps({'started_at': started, 'fits': 0})+'\n')
    before = hashes(); model_manifest, _, models = load_frozen_bundle(STRUCTURAL, {'T-1'})
    if hashes() != before or set(models) != {'T-1'}:
        raise ValueError('Frozen source changed during activation')
    old = json.loads((ROOT/'ml/artifacts/c1_history_residual_v1/manifest.json').read_text())
    manifest = {'package_version': PACKAGE, 'frozen_at': datetime.now(timezone.utc).isoformat(),
        'published_source_commit': published_commit, 'source_sha256': before,
        'structural_artifact': model_manifest['artifacts']['T-1'],
        'training_fixture_unit_hashes': old['training_fixture_unit_hashes'],
        'excluded_training_ids': list(TRAIN_IDS), 'models_fitted': 0,
        'attendance_mae': None, 'official_persistence_allowed': False,
        'production_change': False, 'live_adjustment': 0}
    with (directory/'manifest.json').open('x') as file: json.dump(manifest, file, indent=2, sort_keys=True); file.write('\n')
    return manifest


def load_manifest(directory=ARTIFACT):
    raw = (directory/'manifest.json').read_bytes(); manifest = json.loads(raw)
    if (manifest.get('package_version') != PACKAGE or manifest.get('source_sha256') != hashes()
            or manifest.get('models_fitted') != 0 or manifest.get('official_persistence_allowed') is not False
            or manifest.get('production_change') is not False or manifest.get('live_adjustment') != 0):
        raise ValueError('Frozen structural refresh identity changed')
    manifest['_manifest_sha256'] = hashlib.sha256(raw).hexdigest()
    return manifest


def context(candidate, resolved, source):
    prior = candidate['prior']
    for key in ('source_prior_id', 'horizon', 'p50', 'stadium_capacity', 'model_spec_id', 'feature_contract'):
        if resolved.get(key) != prior.get(key): raise ValueError('Exact persisted anchor identity differs')
    if (resolved.get('status') != 'ready' or resolved['horizon'] != 'T-1'
            or resolved.get('point_in_time_validated') is not True
            or resolved.get('ticket_event_id') != candidate['ticket_event_id']
            or stamp(resolved['generated_at']) != stamp(prior['generated_at'])):
        raise ValueError('Exact ready T1anchor required')
    kickoff = stamp(candidate['kickoff_at']); cutoff = stamp(prior['target_as_of_at'])
    if cutoff != kickoff-pd.Timedelta(days=1) or stamp(resolved['target_as_of_at']) != cutoff:
        raise ValueError('Canonical T1context changed')
    metadata = resolved.get('metadata') or {}
    if metadata.get('capacity_verification_status') != 'verified': raise ValueError('Verified anchor capacity required')
    aliases = {r['alias']: r['club_key'] for r in source['parts']['aliases']}
    home = canonical_club(candidate['club_slug']); away = aliases.get(candidate['away_team'])
    if away is None: raise ValueError('Exact registered opponent identity required')
    round_no = metadata.get('round_no')
    if type(round_no) is not int or round_no <= 0: raise ValueError('Actual saved round required')
    local = kickoff.tz_convert('Europe/Warsaw'); year = local.year if local.month >= 7 else local.year-1
    return {'ticket_event_id': candidate['ticket_event_id'], 'home_team': candidate['home_team'],
        'away_team': candidate['away_team'], 'kickoff_at': kickoff.isoformat(), 'horizon': 'T-1',
        'target_as_of_at': cutoff.isoformat(), 'season': f'{year}/{year+1}', 'round_no': round_no,
        'home_club_key': home, 'away_club_key': canonical_club(away),
        'stadium_capacity': prior['stadium_capacity'], 'capacity_verification_status': 'verified',
        'capacity_source_url': None, 'input_status': 'ready', 'model_spec_id': resolved['model_spec_id'],
        'model_family': resolved['model_family'], 'feature_contract': resolved['feature_contract']}


def predict(candidate, resolved, source, as_of_at, generated_at, predictor=None):
    asof, now = stamp(as_of_at), stamp(generated_at)
    event = context(candidate, resolved, source); kickoff = stamp(event['kickoff_at']); cutoff = stamp(event['target_as_of_at'])
    if not cutoff < asof <= now < kickoff or stamp(resolved['generated_at']) > asof:
        raise ValueError('New real final24observation and available anchor required')
    if not pd.Timedelta(0) <= asof-stamp(source['completed_at']) <= pd.Timedelta(minutes=60):
        raise ValueError('Genuine source archive must precede observation and be fresh')
    c = catalog(source)
    targets = [r for r in source['parts']['ticket_events'] if r['id'] == event['ticket_event_id']]
    if (len(targets) != 1 or targets[0]['competition'] not in COMPETITIONS
            or canonical_club(targets[0]['club_slug']) != event['home_club_key']
            or stamp(targets[0]['kickoff_at']) != kickoff
            or any(targets[0][k] != candidate[k] for k in ('home_team','away_team'))):
        raise ValueError('Canonical target event/competition differs')
    if any(r['ticket_event_id'] == event['ticket_event_id'] for r in source['parts']['outcomes']):
        raise ValueError('Target attendance already present in source')
    target_date = kickoff.tz_convert('Europe/Warsaw').date()
    # Reject a leaked target even when malformed knowledge clocks would make the
    # catalogue discard it. Catalogue rejection must not conceal target labels.
    raw_history = source['parts']['history']
    for row in [*c['records'], *raw_history]:
        if canonical_club(row['club_slug']) == event['home_club_key'] and stamp(row['kickoff_at']).tz_convert('Europe/Warsaw').date() == target_date:
            raise ValueError('Canonical target matchday attendance in source')
    audit = available_at(c, asof.isoformat())
    if audit['conflicts']: raise ValueError('Conflicting known source attendance')
    eligible = [r for r in audit['eligible'] if r['season'] == event['season']
                and stamp(r['kickoff_at']) < cutoff and stamp(r['known_at']) <= stamp(source['completed_at'])]
    attendance = [{k:r[k] for k in ('club_slug','kickoff_at','actual_attendance','season','source_name','source_url')} for r in eligible]
    payload = {'events': [event], 'aliases': source['parts']['aliases'],
               'sportingMatches': source['parts']['sporting'], 'attendance': attendance}
    original = (predictor or materialize)(payload, STRUCTURAL, now)
    if original.get('version') != 'structural-prior-materializer-v1' or len(original.get('predictions', [])) != 1:
        raise ValueError('One unchanged frozen prediction required')
    row = original['predictions'][0]; value = float(row['p50'])
    if (row['ticket_event_id'] != event['ticket_event_id'] or stamp(row['target_as_of_at']) != cutoff
            or not math.isfinite(value) or not 0 <= value <= float(event['stadium_capacity'])):
        raise ValueError('Frozen predictor output/context/bounds differ')
    later = [r for r in eligible if stamp(r['known_at']) > stamp(resolved['generated_at'])]
    return {'p50': value, 'model_context_cutoff_at': cutoff.isoformat(),
        'knowledge_as_of_at': asof.isoformat(), 'eligible_known_records': len(eligible),
        'later_known_record_count': len(later),
        'later_known_home_record_count': sum(r['club_slug'] == event['home_club_key'] for r in later),
        'source_record_manifest': [{k:r[k] for k in ('club_slug','kickoff_at','known_at','source_kind','source_id')} for r in eligible],
        'feature_row_sha256': row['input_lineage']['feature_row_sha256'],
        'predictor_metadata': row['metadata'], 'context': event,
        'source_export_sha256': source['export_sha256'], 'official_persistence_allowed': False}


def summary(scores, captured, missing):
    groups = {}
    for row in scores: groups.setdefault(row['fixture_unit'], []).append(row)
    if any(len({r['ticket_event_id'] for r in rows}) > 1 for rows in groups.values()):
        raise ValueError('Multiple ticket IDs alias one independent fixture')
    latest = [max(rows, key=lambda r: stamp(r['as_of_at'])) for rows in groups.values()]
    clubs = len({r['club_slug'] for r in latest}); ready = len(latest) >= 30 and clubs >= 8
    avg = lambda values: math.fsum(values)/len(values) if values else None
    metrics = {}
    for name in ('fresh', *BASELINES):
        ae = [r['absolute_errors'][name] for r in latest]
        metrics[name] = {'latest_per_event_mae': avg(ae), 'event_balanced_window_mae': avg([
            avg([r['absolute_errors'][name] for r in rows]) for rows in groups.values()]),
            'signed_bias': avg([r['signed_errors'][name] for r in latest]),
            'p90_absolute_error': float(np.quantile(ae,.9)) if ae else None,
            'worst_absolute_error': max(ae) if ae else None}
    comparisons = {}
    for baseline in BASELINES:
        delta = np.array([r['absolute_errors']['fresh']-r['absolute_errors'][baseline] for r in latest]); ci = None
        if ready:
            rng = np.random.default_rng(42)
            draws = np.concatenate([rng.choice(delta,size=(250,len(delta)),replace=True).mean(axis=1) for _ in range(40)])
            ci = [float(v) for v in np.quantile(draws,[.025,.975])]
        comparisons[baseline] = {'paired_delta_mae': avg(delta.tolist()),
            'median_event_delta_ae': float(np.median(delta)) if len(delta) else None,
            'event_improvement_rate': avg((delta<0).astype(float).tolist()),
            'worst_event_degradation': max(0.,float(delta.max())) if len(delta) else None,
            'paired_event_bootstrap_95_interval': ci,
            'gate_met': bool(ready and delta.mean()<0 and ci[1]<0)}
    def grouped(items):
        units = {}
        for item in items: units.setdefault(item['fixture_unit'], []).append(item)
        return {'independent_events': len(units), 'rows': len(items), 'event_balanced_window_mae': {
            name: avg([avg([r['absolute_errors'][name] for r in rows]) for rows in units.values()])
            for name in ('fresh', *BASELINES)}}
    by_club = {club: grouped([r for r in scores if r['club_slug'] == club]) for club in sorted({r['club_slug'] for r in scores})}
    horizon = lambda r: '0_to_6h' if (stamp(r['kickoff_at'])-stamp(r['as_of_at'])).total_seconds() <= 21600 else '6_to_12h' if (stamp(r['kickoff_at'])-stamp(r['as_of_at'])).total_seconds() <= 43200 else '12_to_24h'
    by_horizon = {key: grouped([r for r in scores if horizon(r) == key]) for key in ('0_to_6h','6_to_12h','12_to_24h')}
    by_later = {key: grouped([r for r in scores if bool(r.get('later_known_record_count', 0)) == flag])
                for key,flag in [('new_later_source',True),('no_later_source',False)]}
    return {'by_club': by_club, 'by_horizon': by_horizon, 'by_later_source': by_later,
        'package_version': PACKAGE, 'captured_events': captured, 'scored_events': len(latest),
        'clubs': clubs, 'scored_rows': len(scores), 'missing_outcomes': missing, 'metrics': metrics,
        'comparisons': comparisons, 'review_ready': ready,
        'primary_gate_met': comparisons['prior']['gate_met'],
        'product_gate_met': ready and all(comparisons[k]['gate_met'] for k in BASELINES[1:]),
        'early_scores_descriptive_only': not ready, 'production_change': False, 'live_adjustment': 0}
