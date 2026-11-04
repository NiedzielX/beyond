"""Read-only C1/D2 exposed-cohort audit; no serving-model or score writes."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp

COHORT = (5, 10, 11, 15, 16, 18, 19, 20, 21, 22, 23)
ROOT = Path(__file__).resolve().parents[1]


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'Invalid {name}')
    return float(value)


def frozen_hashes():
    folders = ['c1_shadow_v8', 'structural_prior_runtime_v1',
               'pre_live_v2_historical_candidate_v1', 'd2_stage2_p2_observation_maturity_v1']
    files = [p for folder in folders for p in (ROOT/'ml/artifacts'/folder).rglob('*') if p.is_file()]
    files += [ROOT/'ml/artifacts/d2_stage0_capacity_audit_v1.json',
              ROOT/'ml/artifacts/d2_prospective_capacity_audit_v1.json']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def require_common_times(c1, matched, d2_rows):
    """A later representative is not the same forecast opportunity."""
    expected = {(r['ticket_event_id'], parse_timestamp(r['requested_as_of_at'])): r for r in matched}
    if len(expected) != len(matched):
        raise ValueError('Duplicate matched event/as-of identity')
    actual = {(int(r.ticket_event_id), parse_timestamp(r.as_of_at)) for r in d2_rows.itertuples()}
    if len(actual) != len(d2_rows) or actual != set(expected):
        raise ValueError('D2/C1 comparison timestamps differ')
    for event in c1:
        times = [t for e, t in expected if e == event['ticket_event_id']]
        if not times or max(times) != parse_timestamp(event['latest_as_of_at']):
            raise ValueError('Comparison is not at the persisted C1 latest timestamp')
        for time in times:
            row = expected[(event['ticket_event_id'], time)]
            features = row['features']
            if (time >= parse_timestamp(event['kickoff_at'])
                    or parse_timestamp(features['as_of_at']) != time
                    or features['snapshot_id'] != row['requested_snapshot_id']
                    or features.get('point_in_time_validated') is not True):
                raise ValueError('Future, mismatched or unvalidated feature identity')


def describe(c1, d2_events, priors, exported_events, attendance, outcomes, *, cohort=COHORT):
    c1_by = {r['ticket_event_id']: r for r in c1}
    d2_by = {r['ticket_event_id']: r for r in d2_events}
    if (len(c1_by) != len(c1) or len(d2_by) != len(d2_events)
            or set(c1_by) != set(cohort) or set(d2_by) != set(cohort)):
        raise ValueError('Exact exposed comparison cohort must remain complete and unique')
    rows = []
    for event_id in cohort:
        c, d, prior, event, outcome = c1_by[event_id], d2_by[event_id], priors[event_id], exported_events[event_id], outcomes[event_id]
        actual = number(c['actual_attendance'], 'actual')
        if actual <= 0 or actual != event['actual_attendance'] or actual != outcome['actual_attendance']:
            raise ValueError('Outcome sources disagree; do not silently relabel a score')
        if prior.get('status') != 'ready' or prior.get('horizon') != 'T-1' or prior.get('point_in_time_validated') is not True:
            raise ValueError('Expected the actual PIT-validated T-1 anchor')
        stored = number(c['structural_prior_p50'], 'persisted prior')
        if abs(number(prior['p50'], 'resolved prior')-stored) > 1e-7:
            raise ValueError('Resolved prior differs from the actually persisted C1 anchor')
        diagnostic = d['component_diagnostics']
        if abs(number(diagnostic['structural_t1_base_p50'], 'replayed prior')-stored) > 1e-7:
            raise ValueError('Replayed structural prior differs; investigate input drift')
        as_of, kickoff = parse_timestamp(c['latest_as_of_at']), parse_timestamp(c['kickoff_at'])
        if (as_of >= kickoff or as_of >= parse_timestamp(outcome['confirmed_at'])
                or parse_timestamp(prior['generated_at']) > as_of
                or parse_timestamp(prior['target_as_of_at']) > as_of
                or (kickoff-parse_timestamp(prior['target_as_of_at'])).total_seconds() != 86400):
            raise ValueError('Forecast/anchor was not available before its evaluated cutoff')
        for prediction, error in [('structural_prior_p50', 'latest_prior_error'), ('v2_live_p50', 'latest_live_error'),
                                  ('policy_prediction', 'latest_policy_error')]:
            if abs(abs(number(c[prediction], prediction)-actual)-number(c[error], error)) > 1e-7:
                raise ValueError('Stored C1 error does not reconcile to its forecast and label')
        capacity = number(prior['stadium_capacity'], 'capacity')
        if capacity <= 0 or capacity != event['stadium_capacity'] or capacity != d['stadium_capacity']:
            raise ValueError('Capacity identity differs across compared pipelines')
        eligible = [a for a in attendance if a['club_slug'] == event['club_slug']
                    and str(a['season']) == str(event['season'])
                    and parse_timestamp(a['kickoff_at']) < parse_timestamp(prior['target_as_of_at'])]
        rows.append({'ticket_event_id': event_id, 'home_team': c['home_team'], 'away_team': c['away_team'],
            'as_of_at': c['latest_as_of_at'], 'actual': actual, 'capacity': capacity,
            'actual_exceeds_used_capacity': actual > capacity, 'actual_fill': actual/capacity,
            'c1_prior_mae': c['latest_prior_error'], 'c1_live_mae': c['latest_live_error'],
            'c1_policy_mae': c['latest_policy_error'], 'c1_selected_expert': c['selected_expert'],
            'c1_reason': c['reason_code'], 'prior_p50': stored, 'live_p50': c['v2_live_p50'],
            'policy_p50': c['policy_prediction'], 'season_home_n_at_materialization': prior.get('metadata', {}).get('season_home_n'),
            'earlier_current_season_rows_in_current_export': len(eligible),
            'd2_frozen_v2_mae': d['scores']['frozen_v2']['latest_error'],
            'd2_p2_mae': d['scores']['p2_governed_ridge']['latest_error'],
            'd2_b2_correction': diagnostic['b2_correction_seats'],
            'd2_window_mae': d['scores']['p2_governed_ridge']['window_mae'],
            'outcome_source_name': outcome.get('source_name'), 'outcome_source_url': outcome.get('source_url'),
            'outcome_confirmed_at': outcome['confirmed_at']})
    rows.sort(key=lambda r: r['c1_policy_mae'], reverse=True)
    total = math.fsum(r['c1_policy_mae'] for r in rows)
    for row in rows:
        row['share_of_policy_total_absolute_error'] = row['c1_policy_mae']/total if total else None
    mean = lambda name: math.fsum(number(r[name], name) for r in rows)/len(rows)
    return {'version': 'c1-live-matched-audit-v1', 'evidence_kind': 'exposed_retrospective_diagnostic_not_new_prospective',
        'independent_events': len(rows), 'event_ids': sorted(cohort), 'events': rows,
        'latest_row_mae': {name: mean(name) for name in ['c1_prior_mae', 'c1_live_mae', 'c1_policy_mae', 'd2_frozen_v2_mae', 'd2_p2_mae']},
        'd2_event_balanced_window_mae': mean('d2_window_mae'),
        'top4_error_share': math.fsum(r['c1_policy_mae'] for r in rows[:4])/total if total else None,
        'outcome_aware_selector_mae_DIAGNOSTIC_ONLY': math.fsum(min(r['c1_prior_mae'], r['c1_live_mae']) for r in rows)/len(rows),
        'c1_selection_counts': dict(Counter(r['c1_selected_expert'] for r in rows)),
        'top4_actual_exceeds_capacity_count': sum(r['actual_exceeds_used_capacity'] for r in rows[:4]),
        'external_outcome_source_independently_reverified': False,
        'historical_attendance_publication_times_independently_verified': False,
        'parameters_selected': False, 'serving_artifacts_changed': False, 'production_change': False, 'live_adjustment': 0}


def check_training_features(development, frozen_payload, contract, runtime):
    from ml.demand_engine.run_c1_shadow_v8 import feature_record
    by_key = {(r['ticket_event_id'], parse_timestamp(r['requested_as_of_at'])): r for r in frozen_payload['liveRows']}
    by_frame = {(int(r.ticket_event_id), parse_timestamp(r.as_of_at)): r for r in development.itertuples()}
    checked = 0
    for row in contract['rows']:
        key = (row['ticket_event_id'], parse_timestamp(row['as_of_at']))
        old = by_frame[key]
        record = feature_record({'prior': {'p50': old.legacy_prior_p50, 'stadium_capacity': old.stadium_capacity}}, by_key[key], runtime)
        for feature in runtime.features:
            actual, expected = record[feature], row['features'].get(feature)
            if not (pd.isna(actual) and expected is None or expected is not None and not pd.isna(actual)
                    and abs(float(actual)-float(expected)) <= 1e-9):
                raise ValueError('Original frozen training feature cell changed')
            checked += 1
    return checked


def followup_queue(events, priors, attendance, sporting, aliases, readiness, as_of):
    """Known fixtures with missing truth; never infer a crowd from inventory."""
    warsaw = ZoneInfo('Europe/Warsaw')
    date = lambda value: parse_timestamp(value).astimezone(warsaw).date().isoformat()
    alias = {r['alias']: r['club_key'] for r in aliases}
    queue = []
    for event in events:
        cutoff = priors[event['ticket_event_id']]['target_as_of_at']
        known = {date(r['kickoff_at']) for r in attendance
                 if r['club_slug'] == event['club_slug'] and r['season'] == event['season']}
        for match in sporting:
            if (alias.get(match['home_team']) == event['home_club_key'] and match.get('completed') is True
                    and str(match['season']).replace('-', '/') == event['season']
                    and match['event_date'] < date(cutoff) and match['event_date'] not in known):
                queue.append({'kind': 'MISSING_CURRENT_SEASON_HOME_HISTORY', 'club_slug': event['club_slug'],
                              'home_team': match['home_team'], 'away_team': match['away_team'],
                              'match_date': match['event_date'], 'needed_for_event_id': event['ticket_event_id'],
                              'actual_attendance': None, 'independently_verified': False})
    from datetime import timedelta
    for event in readiness:
        if (event.get('actual_attendance') is None
                and parse_timestamp(event['kickoff_at']) < parse_timestamp(as_of)-timedelta(hours=3)):
            queue.append({'kind': 'MISSING_COMPLETED_EVENT_OUTCOME', 'ticket_event_id': event['ticket_event_id'],
                          'club_slug': event['club_slug'], 'home_team': event['home_team'], 'away_team': event['away_team'],
                          'match_date': date(event['kickoff_at']), 'actual_attendance': None, 'independently_verified': False})
    return queue


def run(input_dir: Path, output_dir: Path):
    # Import the existing compatibility wrapper only in this isolated audit process.
    import joblib
    import ml.run_d2_prospective_score_v1 as wrapper
    import ml.d2_live_replay_anchor_v1 as stage0
    from ml.d2_stage1_payload_split_v1 import split_payload
    from ml.demand_engine.run_c1_shadow_v8 import run_candidate
    from ml.d2_stage2_reliability_gating_v1 import raw_ridge_predictions, attach_stage0_features, policy_predictions, PolicySpec, stage2_scorecard
    p = wrapper.prospective
    before = frozen_hashes()
    if output_dir.resolve().is_relative_to(ROOT):
        raise ValueError('Private audit outputs must remain outside the repository')
    output_dir.mkdir(parents=True, exist_ok=False)
    inputs = {}
    def read(name):
        file = input_dir/(name+'.json'); raw = file.read_bytes()
        inputs[file.name] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    events, attendance, sporting, aliases, full, matched, c1, resolved, outcomes, readiness, export_manifest = [read(name) for name in
        ['events', 'attendance', 'sporting', 'aliases', 'final24', 'matched-final24', 'c1-events', 'resolved-priors', 'outcomes',
         'readiness', 'export-manifest']]
    c1 = [r for r in c1 if r['outcome_available']]
    if tuple(sorted(r['ticket_event_id'] for r in c1)) != COHORT:
        raise ValueError('Source cohort changed; prepare a separately identified audit')
    contract_path = ROOT/'ml/artifacts/c1_shadow_v8/training_contract_v1.json'
    contract = json.loads(contract_path.read_text())
    frozen, split = split_payload(events_export=events, attendance_export=attendance, sporting_export=sporting,
                                  aliases_export=aliases, live_export=full, training_contract=contract)
    freeze_path = ROOT/'ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json'
    frozen_contract = stage0.load_and_verify_freeze_manifest(freeze_path)
    stage0.verify_c1_contract(frozen, contract_path)
    capacity_path = ROOT/'ml/artifacts/d2_stage0_capacity_audit_v1.json'
    legacy, anchors, event_audit = stage0.build_frozen_v2_event_anchors(frozen, ROOT/'ml/artifacts/structural_prior_runtime_v1',
                                                                     stage0.load_capacity_audit(capacity_path), frozen_contract)
    development = stage0.build_d2_frame(frozen, legacy, anchors, event_audit)
    stage2_path = ROOT/'ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json'
    stage2 = p.verify_stage2_manifest(stage2_path)
    reproduction = stage2_scorecard(policy_predictions(attach_stage0_features(development, raw_ridge_predictions(development)),
                                                       PolicySpec('P2-observation-maturity', 'fixed reproduction')))
    for actual, expected in [('latest_row_mae', 'p2_latest_mae'), ('event_balanced_window_mae', 'p2_window_mae')]:
        if abs(reproduction[actual]-stage2['metrics'][expected]) > 1e-9:
            raise ValueError('Original frozen D2 development metrics do not reproduce')
    manifest = json.loads((ROOT/'ml/artifacts/c1_shadow_v8/manifest.json').read_text())
    artifact = ROOT/'ml/artifacts/c1_shadow_v8'/manifest['artifact']['filename']
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != manifest['artifact']['sha256']:
        raise ValueError('C1 artifact hash mismatch')
    runtime = joblib.load(artifact)
    cells = check_training_features(development, frozen, contract, runtime)
    prior_by = {r['ticket_event_id']: r['resolved'][0] for r in resolved}
    capacity = json.loads((ROOT/'ml/artifacts/d2_prospective_capacity_audit_v1.json').read_text())
    payload = p.combined_payload(events, attendance, sporting, aliases, matched)
    event_by = {r['ticket_event_id']: r for r in events['events']}
    results, frames, parity = [], [], []
    for c in c1:
        event_id = c['ticket_event_id']
        reps = [r for r in matched['liveRows'] if r['ticket_event_id'] == event_id]
        replay = run_candidate({**c, 'prior': prior_by[event_id], 'representatives': reps}, runtime,
                               manifest['artifact']['sha256'], pd.Timestamp(c['latest_as_of_at']))
        error = max(abs(replay[key]-c[key]) for key in ['v2_live_p50', 'policy_prediction', 'structural_prior_p50'])
        if error > 1e-7 or replay['selected_expert'] != c['selected_expert']:
            raise ValueError('C1 reconstructed output differs from its actually persisted forecast')
        parity.append(error)
        result, frame = p.score_event(development=development, payload=payload, event=event_by[event_id],
                                      structural_artifact_dir=ROOT/'ml/artifacts/structural_prior_runtime_v1', capacity_audit=capacity)
        results.append(result); frames.append(frame)
    rows = pd.concat(frames, ignore_index=True)
    require_common_times(c1, matched['liveRows'], rows)
    report = describe(c1, results, prior_by, event_by, attendance['attendance'], {r['ticket_event_id']: r for r in outcomes})
    # Original event5 timing is a fixed golden reproduction, not an alternative selector.
    original_payload = p.combined_payload(events, attendance, sporting, aliases, full)
    original5, _ = p.score_event(development=development, payload=original_payload, event=event_by[5],
                                 structural_artifact_dir=ROOT/'ml/artifacts/structural_prior_runtime_v1', capacity_audit=capacity)
    expected5 = json.loads((ROOT/'ml/artifacts/d2_event5_holdout_v1/manifest.json').read_text())['scores']
    for variant in ['frozen_v2', 'raw_ridge', 'p2_governed_ridge']:
        for metric in ['latest_error', 'window_mae']:
            if abs(original5['scores'][variant][metric]-expected5[variant][metric]) > 1e-7:
                raise ValueError('Original event5 golden diagnostic does not reproduce')
    report.update({'checked_at': datetime.now(timezone.utc).isoformat(), 'source_hashes': inputs,
                   'frozen_training_feature_cells_verified': cells, 'max_c1_reconstruction_difference': max(parity),
                   'frozen_d2_development_reproduced': True, 'original_event5_reproduced_at_original_timing': True,
                   'heldout_outcomes_used_for_training': False, 'frozen_training_reconstructed_in_memory': True,
                   'frozen_hashes': before, 'sampling': matched['sampling']})
    report['source_followups'] = followup_queue([event_by[i] for i in COHORT], prior_by, attendance['attendance'],
        sporting['sportingMatches'], aliases['aliases'], readiness['events'], export_manifest['retrieved_at'])
    report['source_exported_at'] = export_manifest['retrieved_at']
    report['source_pack_atomic_database_snapshot'] = False
    map_events = sorted({r['ticket_event_id'] for r in full['liveRows'] if r['features'].get('public_seat_map_size') is not None})
    report['seat_map_feature_support'] = {'event_ids': map_events,
        'original_training_events': sorted(set(map_events) & set(p.EXPECTED_DEVELOPMENT_EVENT_IDS)),
        'note': 'Observed map geometry/availability, not confirmed paid sales or attendance; original C1 compact model omits these fields.'}
    if frozen_hashes() != before:
        raise ValueError('Frozen artifacts changed during read-only audit')
    (output_dir/'summary.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    pd.DataFrame(report['events']).to_csv(output_dir/'events.csv', index=False)
    rows.to_csv(output_dir/'private-d2-rows.csv', index=False)
    (output_dir/'private-d2-results.json').write_text(json.dumps(results, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: report[k] for k in ['version', 'independent_events', 'latest_row_mae',
                                               'max_c1_reconstruction_difference', 'frozen_training_feature_cells_verified']}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    run(args.input_dir, args.output_dir)


if __name__ == '__main__':
    main()
