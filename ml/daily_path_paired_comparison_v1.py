"""Read-only three-way comparison of identical immutable inventory targets."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import sqlite3

import numpy as np

from ml.c1_live_matched_audit_v1 import ROOT, number
from ml.daily_inventory_drift_ledger_v1 import DriftLedger, MARKER, REFERENCE_SHA
from ml.daily_path_prefix_diagnostics_v1 import read_ledger
from ml.demand_engine.daily_inventory_path_dataset_v1 import canonical_hash, parse_timestamp
from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger

DRIFT_SHA = '332f6fd37bc2a09ce665668ef3c9c23d8d34ec3613f18435ec729d95d3bb43cf'
NAMES = ('daily_model', 'drift', 'persistence')


def identity(point):
    return (point['ticket_event_id'], parse_timestamp(point['issued_as_of_at']), parse_timestamp(point['target_at']))


def validated_points(attempts, points, lane, now):
    expected_sha = REFERENCE_SHA if lane == 'daily_model' else DRIFT_SHA
    validator = DailyInventoryPathLedger if lane == 'daily_model' else DriftLedger
    expected, attempts_seen, attempt_ids = {}, set(), set()
    for attempt in attempts:
        issue = attempt['issue']; issued = parse_timestamp(issue['issued_as_of_at'])
        execution = parse_timestamp(attempt['executed_at'])
        key = (issue['ticket_event_id'], issued)
        if key in attempts_seen or attempt['attempt_id'] in attempt_ids:
            raise ValueError('Duplicate attempt identity')
        attempts_seen.add(key); attempt_ids.add(attempt['attempt_id'])
        if execution > now:
            raise ValueError('Future execution cannot enter current comparison')
        if (attempt['artifact'].get('model_sha256') != expected_sha
                or attempt.get('production_change') is not False
                or attempt.get('evidence_kind') != 'local_post_freeze_prospective'):
            raise ValueError('Unexpected frozen model or evidence identity')
        _, clean, _ = validator._validate(issue, attempt['points'], attempt['artifact'], execution)
        for point in clean:
            expected[identity(point)] = (attempt['attempt_id'], point)
    actual = {}
    for point in points:
        key = identity(point)
        if key in actual:
            raise ValueError('Duplicate point identity')
        if key not in expected:
            raise ValueError('Orphan point or mismatched vintage')
        attempt_id, clean = expected[key]
        if (point['attempt_id'] != attempt_id
                or canonical_hash({k: point[k] for k in clean}) != canonical_hash(clean)):
            raise ValueError('Point differs from immutable frozen attempt')
        actual[key] = point
    if set(actual) != set(expected):
        raise ValueError('Persisted points do not cover all declared future targets')
    return actual


def validate_score(point, now):
    score = point.get('score')
    if score is None:
        return None
    issued, target = parse_timestamp(point['issued_as_of_at']), parse_timestamp(point['target_at'])
    captured, scored = parse_timestamp(score['target_captured_at']), parse_timestamp(score['scored_at'])
    actual = number(score['target_available_total'], 'observed target')
    snapshot = score['target_snapshot_id']
    if (not issued < captured <= target <= scored or captured < target - timedelta(hours=6)
            or not isinstance(snapshot, int) or isinstance(snapshot, bool) or snapshot <= 0 or actual < 0
            or score.get('measurement_key') != point['measurement_key']
            or score.get('production_change') is not False):
        raise ValueError('Invalid immutable target label or score chronology')
    errors = {'candidate': point['predicted_available_total'] - actual,
              'baseline': point['baseline_available_total'] - actual}
    for name, error in errors.items():
        for suffix, expected in [('error', error), ('abs_error', abs(error))]:
            if not math.isclose(number(score[f'{name}_{suffix}'], 'stored error'), expected, rel_tol=0, abs_tol=1e-8):
                raise ValueError('Stored score arithmetic differs from immutable target')
    return score if scored <= now else None


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['ticket_event_id']].append(row)
    avg = lambda values: math.fsum(values) / len(values) if values else None
    event_errors = {name: [avg([abs(r['signed_errors'][name]) for r in values])
                            for values in groups.values()] for name in NAMES}
    metrics = {name: {'event_balanced_mae': avg(errors),
        'event_balanced_signed_bias': avg([avg([r['signed_errors'][name] for r in values]) for values in groups.values()]),
        'p90_event_mae': float(np.quantile(errors, .9)) if errors else None,
        'worst_event_mae': max(errors) if errors else None} for name, errors in event_errors.items()}
    pairs = {}
    for candidate, baseline in [('daily_model', 'persistence'), ('drift', 'persistence'), ('drift', 'daily_model')]:
        deltas = [a-b for a, b in zip(event_errors[candidate], event_errors[baseline])]
        pairs[f'{candidate}_minus_{baseline}'] = {'delta_event_balanced_mae': avg(deltas),
            'event_improvement_rate': avg([float(v < 0) for v in deltas]),
            'median_event_delta_ae': float(np.median(deltas)) if deltas else None,
            'worst_event_degradation': max(0., max(deltas)) if deltas else None}
    return {'scored_points': len(rows), 'independent_events': len(groups),
        'distinct_clubs': len({r['club_slug'] for r in rows}), 'metrics': metrics, 'paired_comparisons': pairs}


def compare(daily_attempts, daily_points, drift_attempts, drift_points, as_of_at):
    now = parse_timestamp(as_of_at)
    daily = validated_points(daily_attempts, daily_points, 'daily_model', now)
    drift = validated_points(drift_attempts, drift_points, 'drift', now)
    if set(drift) - set(daily):
        raise ValueError('Drift target lacks an identical original daily vintage')
    # Validate every source score, including targets outside the intersection.
    daily_scores = {key: validate_score(p, now) for key, p in daily.items()}
    drift_scores = {key: validate_score(p, now) for key, p in drift.items()}
    counts = Counter(); rows = []
    for key, point in drift.items():
        original = daily[key]
        for field in ['measurement_key', 'prefix_sha256', 'input_manifest_sha256',
                      'baseline_available_total', 'lead_days', 'club_slug']:
            if point[field] != original[field]:
                raise ValueError('Paired input lineage, lead or persistence differs')
        first, second = daily_scores[key], drift_scores[key]
        if key[2] > now:
            counts['pending_targets'] += 1
        elif first is None:
            if second is not None:
                raise ValueError('Drift score exists without its immutable reference score')
            counts['mature_without_reference_label'] += 1
        elif second is None:
            counts['reference_scored_waiting_for_drift_score'] += 1
        else:
            for field in ['target_snapshot_id', 'target_available_total', 'measurement_key']:
                if first[field] != second[field]:
                    raise ValueError('Paired immutable labels differ')
            if (parse_timestamp(first['target_captured_at']) != parse_timestamp(second['target_captured_at'])
                    or parse_timestamp(second['reference_source_scored_at']) != parse_timestamp(first['scored_at'])
                    or parse_timestamp(second['scored_at']) < parse_timestamp(first['scored_at'])):
                raise ValueError('Drift score does not reference the exact immutable source label')
            actual = first['target_available_total']
            predictions = {'daily_model': original['predicted_available_total'],
                'drift': point['predicted_available_total'], 'persistence': original['baseline_available_total']}
            rows.append({'ticket_event_id': point['ticket_event_id'], 'club_slug': point['club_slug'],
                'lead_days': point['lead_days'], 'signed_errors': {name: value - actual for name, value in predictions.items()}})
    if len(rows) + sum(counts.values()) != len(drift):
        raise ValueError('Paired target coverage does not reconcile')
    return {'version': 'daily-path-paired-comparison-v1', 'checked_at': now.isoformat(),
        'target_kind': 'available_total', 'unit': 'places',
        'evidence_kind': 'read_only_identical_target_diagnostic',
        'coverage': {'daily_attempts': len(daily_attempts), 'daily_points': len(daily),
            'drift_attempts': len(drift_attempts), 'drift_points': len(drift),
            'daily_points_without_drift': len(set(daily) - set(drift)),
            'paired_points': len(drift), 'paired_scored_points': len(rows),
            **{name: counts[name] for name in ['pending_targets', 'mature_without_reference_label',
                                             'reference_scored_waiting_for_drift_score']}},
        'overlap': summarize(rows),
        'per_lead': {str(lead): summarize([r for r in rows if r['lead_days'] == lead])
                     for lead in sorted({p['lead_days'] for p in drift.values()})},
        'original_primary_metrics_replaced': False, 'review_or_promotion_gates_changed': False,
        'models_fitted': 0, 'production_change': False, 'live_adjustment': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--daily-ledger', type=Path, required=True)
    p.add_argument('--drift-ledger', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.resolve().is_relative_to(ROOT) or a.daily_ledger.resolve() == a.drift_ledger.resolve():
        raise ValueError('Separate ledgers and private report path required')
    with sqlite3.connect(a.drift_ledger.resolve().as_uri()+'?mode=ro', uri=True) as db:
        marker = db.execute('select version from drift_ledger_meta where singleton=1').fetchone()
        if marker != (MARKER,):
            raise ValueError('Wrong drift ledger identity')
    # Drift is derived from v1; reading it first allows a concurrent v1 score append.
    drift = read_ledger(a.drift_ledger)
    daily = read_ledger(a.daily_ledger)
    report = compare(*daily, *drift, datetime.now(timezone.utc).isoformat())
    with a.output.open('x') as file:
        json.dump(report, file, indent=2, sort_keys=True, allow_nan=False); file.write('\n')
    print(json.dumps({key: report[key] for key in ['version', 'checked_at', 'coverage', 'overlap',
                                                 'models_fitted', 'production_change']}))


if __name__ == '__main__':
    main()
