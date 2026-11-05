"""Reconcile persisted C1 errors without fitting, replaying or writing forecasts."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from ml.c1_live_matched_audit_v1 import COHORT, ROOT, number
from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.demand_engine.current_structural_prior_features import DEFAULT_KEY_ALIASES
from ml.demand_engine.run_c1_shadow_v8 import EXPECTED_PACKAGE
from ml.export_c1_matched_audit_inputs_v1 import Reader

EXPERTS = {
    'prior': ('structural_prior_p50', 'latest_prior_error', 'window_prior_mae'),
    'raw': ('v2_live_p50', 'latest_live_error', 'window_live_mae'),
    'policy': ('policy_prediction', 'latest_policy_error', 'window_policy_mae'),
}
WARSAW = ZoneInfo('Europe/Warsaw')


def mean(values):
    return math.fsum(values) / len(values) if len(values) else None


def metrics(rows):
    result = {}
    for name in EXPERTS:
        errors = [r['errors'][name] for r in rows]
        result[name] = {
            'latest_row_mae': mean(errors),
            'event_balanced_window_mae': mean([r['window_errors'][name] for r in rows]),
            'signed_bias': mean([r['signed_errors'][name] for r in rows]),
            'p90_absolute_error': float(np.quantile(errors, .9)) if errors else None,
            'worst_absolute_error': max(errors) if errors else None,
        }
    delta = [r['errors']['policy'] - r['errors']['prior'] for r in rows]
    return {'independent_events': len(rows), 'metrics': result,
            'policy_minus_prior_mae': mean(delta),
            'policy_improvement_rate': mean([float(v < 0) for v in delta]),
            'policy_worsening_rate': mean([float(v > 0) for v in delta]),
            'selection_counts': dict(Counter(r['selected_expert'] for r in rows)),
            'outcome_aware_prior_raw_oracle_mae_DIAGNOSTIC_ONLY':
                mean([min(r['errors']['prior'], r['errors']['raw']) for r in rows])}


def decompose(events, status, outcomes, metadata, checked_at):
    now = parse_timestamp(checked_at)
    if (status.get('package_version') != EXPECTED_PACKAGE
            or status.get('production_live_adjustment') != 0
            or abs((now - parse_timestamp(status['refreshed_at'])).total_seconds()) > 120):
        raise ValueError('Unexpected package, governance or stale status')
    truth = {r['ticket_event_id']: r for r in outcomes}
    catalog = {r['id']: r for r in metadata}
    if len(truth) != len(outcomes) or len(catalog) != len(metadata):
        raise ValueError('Duplicate outcome or canonical source identity')
    identities, fixtures, scored, pending = set(), set(), [], []
    for event in events:
        event_id = event['ticket_event_id']
        if (isinstance(event_id, bool) or not isinstance(event_id, int) or event_id <= 0
                or event_id in identities or event.get('package_version') != EXPECTED_PACKAGE):
            raise ValueError('Duplicate event identity or wrong package')
        identities.add(event_id)
        canonical = catalog[event_id]
        kickoff, as_of = map(parse_timestamp, [event['kickoff_at'], event['latest_as_of_at']])
        hours = (kickoff - as_of).total_seconds() / 3600
        club = canonical.get('club_slug')
        if (not isinstance(club, str) or not club.strip()
                or parse_timestamp(canonical['kickoff_at']) != kickoff
                or not 0 < hours <= 24 or as_of > now
                or abs(number(event['hours_to_kickoff'], 'horizon') - hours) > 1e-5):
            raise ValueError('Invalid canonical fixture or forecast chronology')
        club = DEFAULT_KEY_ALIASES.get(club, club)
        fixture = (club, kickoff.astimezone(WARSAW).date())
        if fixture in fixtures:
            raise ValueError('Multiple ticket IDs describe the same canonical home-matchday')
        fixtures.add(fixture)
        forecasts = {name: number(event[fields[0]], name) for name, fields in EXPERTS.items()}
        if min(forecasts.values()) < 0:
            raise ValueError('Negative attendance forecast')
        selected = event.get('selected_expert')
        if selected not in ('PRIOR', 'LIVE') or not math.isclose(
                forecasts['policy'], forecasts['prior' if selected == 'PRIOR' else 'raw'], abs_tol=1e-7, rel_tol=0):
            raise ValueError('Selected expert disagrees with persisted policy output')
        label = truth.get(event_id)
        has_score = event.get('outcome_available')
        score_fields = ['actual_attendance', 'scored_at'] + [key for fields in EXPERTS.values() for key in fields[1:]]
        if has_score is False:
            if label is not None or any(event.get(key) is not None for key in score_fields):
                raise ValueError('Unscored row conflicts with label or stored score fields')
            pending.append(event_id)
            continue
        if has_score is not True or label is None:
            raise ValueError('Scored status disagrees with confirmed outcome')
        actual = number(event['actual_attendance'], 'actual attendance')
        confirmed = parse_timestamp(label['confirmed_at'])
        scored_at = parse_timestamp(event['scored_at'])
        if (actual <= 0 or actual != number(label['actual_attendance'], 'canonical attendance')
                or not as_of < kickoff <= confirmed <= scored_at <= now
                or not label.get('source_name') or not str(label.get('source_url', '')).startswith('https://')):
            raise ValueError('Invalid label identity, provenance or confirmation chronology')
        errors = {name: abs(value - actual) for name, value in forecasts.items()}
        windows = {}
        for name, fields in EXPERTS.items():
            stored = number(event[fields[1]], 'stored absolute error')
            windows[name] = number(event[fields[2]], 'stored window MAE')
            if not math.isclose(errors[name], stored, abs_tol=1e-7, rel_tol=0) or windows[name] < 0:
                raise ValueError('Stored error does not reconcile to persisted forecast and outcome')
        scored.append({'ticket_event_id': event_id, 'club_slug': club,
            'as_of_at': event['latest_as_of_at'], 'kickoff_at': event['kickoff_at'],
            'hours_to_kickoff': hours, 'actual_attendance': actual,
            'selected_expert': selected, 'forecasts': forecasts, 'errors': errors,
            'window_errors': windows, 'signed_errors': {name: value - actual for name, value in forecasts.items()}})
    headline = metrics(scored)
    if (status.get('prospective_event_count') != len(events)
            or status.get('scored_event_count') != len(scored)):
        raise ValueError('Status denominators disagree with complete event view')
    for name, live_name in [('prior', 'prior'), ('raw', 'live'), ('policy', 'policy')]:
        for metric, field in [('latest_row_mae', f'latest_row_{live_name}_mae'),
                              ('event_balanced_window_mae', f'representative_window_{live_name}_mae')]:
            value = headline['metrics'][name][metric]
            if value is None:
                if status.get(field) is not None:
                    raise ValueError('Empty cohort cannot have a non-null headline')
            elif not math.isclose(value, number(status[field], field), abs_tol=1e-7, rel_tol=0):
                raise ValueError('Status aggregate MAE does not reconcile; retry consistent reads')
    def group(key):
        groups = defaultdict(list)
        for row in scored:
            groups[key(row)].append(row)
        return {name: metrics(rows) for name, rows in sorted(groups.items())}
    ranked = sorted(scored, key=lambda r: (-r['errors']['policy'], r['ticket_event_id']))
    total = math.fsum(r['errors']['policy'] for r in ranked)
    for row in ranked:
        row['policy_error_share'] = row['errors']['policy'] / total if total else None
    return {'version': 'c1-current-error-decomposition-v1', 'checked_at': checked_at,
        'package_version': EXPECTED_PACKAGE, 'evidence_kind': 'persisted_exposed_diagnostic_not_new_validation',
        'forecast_events': len(events), 'pending_event_ids': sorted(pending), 'headline': headline,
        'top4_policy_error_share': math.fsum(r['errors']['policy'] for r in ranked[:4]) / total if total else None,
        'top4_event_ids': [r['ticket_event_id'] for r in ranked[:4]],
        'selection_regret_to_outcome_aware_oracle_DIAGNOSTIC_ONLY':
            headline['metrics']['policy']['latest_row_mae'] - headline['outcome_aware_prior_raw_oracle_mae_DIAGNOSTIC_ONLY']
            if scored else None,
        'by_club_descriptive': group(lambda r: r['club_slug']),
        'by_horizon_descriptive': group(lambda r: '0_to_1_hours' if r['hours_to_kickoff'] <= 1
                                      else '1_to_6_hours' if r['hours_to_kickoff'] <= 6 else '6_to_24_hours'),
        'by_attendance_level_descriptive_outcome_conditioned': group(lambda r:
            'under_10000' if r['actual_attendance'] < 10000 else '10000_to_19999' if r['actual_attendance'] < 20000 else '20000_plus'),
        'by_exposed_cohort': group(lambda r: 'earlier_11' if r['ticket_event_id'] in COHORT else 'subsequently_scored'),
        'ranked_events_PRIVATE': ranked, 'models_fitted': 0, 'parameters_selected': False,
        'historical_source_publication_times_reverified': False,
        'new_accuracy_improvement_claimed': False, 'production_change': False, 'live_adjustment': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.resolve().is_relative_to(ROOT):
        raise ValueError('Raw source rows and detailed reports must remain outside Git')
    args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    reader = Reader()
    sources = [('events', 'dashboard_c1_shadow_v8_events_v1?select=*&limit=1001'),
               ('outcomes', 'ticket_event_outcomes?select=*&limit=1001'),
               ('metadata', 'ticket_events?select=id,club_slug,kickoff_at&limit=1001'),
               ('status', 'dashboard_c1_shadow_v8_status_v1?select=*&limit=1001')]
    def read(part):
        name, path = part
        requested = datetime.now(timezone.utc).isoformat()
        value = reader.request(path)
        if not isinstance(value, list) or len(value) >= 1000:
            raise ValueError('Unpaginated source expanded or malformed')
        raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
        with (args.output_dir / (name + '.json')).open('xb') as file:
            file.write(raw)
        return name, value, {'source': path, 'requested_at': requested,
            'completed_at': datetime.now(timezone.utc).isoformat(), 'rows': len(value), 'sha256': hashlib.sha256(raw).hexdigest()}
    with ThreadPoolExecutor(max_workers=4) as pool:
        captured = list(pool.map(read, sources))
    values = {name: value for name, value, _ in captured}
    if len(values['status']) != 1:
        raise ValueError('Require exactly one C1 package status')
    result = decompose(values['events'], values['status'][0], values['outcomes'], values['metadata'],
                       datetime.now(timezone.utc).isoformat())
    result['source_receipts'] = [receipt for _, _, receipt in captured]
    result['implementation_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with (args.output_dir / 'diagnostic.json').open('x') as file:
        json.dump(result, file, indent=2, sort_keys=True, allow_nan=False); file.write('\n')
    print(json.dumps({key: result[key] for key in ['version', 'checked_at', 'forecast_events', 'pending_event_ids',
        'headline', 'top4_policy_error_share', 'top4_event_ids', 'by_exposed_cohort', 'production_change']}))


if __name__ == '__main__':
    main()
