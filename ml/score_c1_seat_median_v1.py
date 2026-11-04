"""Future confirmed attendance only; separate raw-learner and governed gates."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml.capture_c1_seat_median_v1 import load_models, ensure_runtime
from ml.c1_training_expansion_v1 import EVENT_IDS, digest_json
from ml.demand_engine.c1_seat_median_runtime_v1 import PACKAGE
from ml.export_c1_matched_audit_inputs_v1 import Reader
from ml.score_c1_training_expansion_v1 import persist_score

NAMES = ('seat_median_raw', 'seat_median_policy', 'ridge20_raw', 'ridge20_policy', 'original9_raw', 'original9_policy', 'prior')


def score_rows(evidence, outcomes, metadata, manifest, hashes, now):
    truth = {r['ticket_event_id']: r for r in outcomes}; meta = {r['id']: r for r in metadata}
    if len(truth) != len(outcomes) or len(meta) != len(metadata): raise ValueError('Duplicate canonical source identity')
    scores, missing, identities = [], set(), set()
    for row in evidence:
        event = row['ticket_event_id']; as_of, issued, kickoff = map(pd.Timestamp, [row['as_of_at'], row['issued_at'], row['kickoff_at']])
        identity = (event, as_of)
        if identity in identities: raise ValueError('Duplicate captured event/time')
        identities.add(identity)
        if (row.get('version') != 'c1-seat-median-paired-evidence-v1' or row.get('package_version') != PACKAGE
                or row.get('manifest_sha256') != manifest['_verified_manifest_sha256']
                or row.get('precommit_sha256') != manifest['precommit_sha256'] or row.get('model_hashes') != hashes
                or row.get('known_outcome_at_capture') is not False or row.get('production_change') is not False
                or row.get('live_adjustment') != 0 or event in EVENT_IDS
                or not pd.Timestamp(manifest['frozen_at']) <= as_of <= issued < kickoff
                or issued-as_of > pd.Timedelta(hours=2) or issued > pd.Timestamp(now)):
            raise ValueError('Invalid median identity or prospective capture timing')
        forecasts = row['forecasts']; capacity = float(row['decisions']['seat_median']['stadium_capacity'])
        if set(forecasts) != set(NAMES): raise ValueError('All declared paired outputs required')
        for name in ['seat_median', 'ridge20', 'original9']:
            decision = row['decisions'][name]
            if (decision['artifact_sha256'] != hashes[name] or pd.Timestamp(decision['as_of_at']) != as_of
                    or decision['source_snapshot_id'] != row['source_snapshot_id']
                    or float(decision['stadium_capacity']) != capacity or decision['structural_prior_p50'] != forecasts['prior']
                    or decision['v2_live_p50'] != forecasts[name+'_raw'] or decision['policy_prediction'] != forecasts[name+'_policy']):
                raise ValueError('Paired decision identity/value differs')
        if not np.isfinite(capacity) or capacity <= 0 or any(not np.isfinite(float(v)) or not 0 <= float(v) <= capacity for v in forecasts.values()):
            raise ValueError('Invalid captured capacity/forecast')
        label = truth.get(event)
        if label is None: missing.add(event); continue
        actual, confirmed = float(label['actual_attendance']), pd.Timestamp(label['confirmed_at'])
        if (isinstance(label['actual_attendance'], bool) or not np.isfinite(actual) or not 0 < actual <= capacity
                or not issued < confirmed <= pd.Timestamp(now) or confirmed < kickoff
                or not label.get('source_name') or not str(label.get('source_url', '')).startswith('https://')):
            raise ValueError('Invalid/known/future outcome or missing provenance')
        event_meta = meta[event]
        if not event_meta.get('club_slug') or pd.Timestamp(event_meta['kickoff_at']) != kickoff:
            raise ValueError('Club/kickoff identity missing or changed')
        scores.append({'ticket_event_id': event, 'source_snapshot_id': row['source_snapshot_id'], 'as_of_at': row['as_of_at'],
            'issued_at': row['issued_at'], 'kickoff_at': row['kickoff_at'], 'club_slug': event_meta['club_slug'],
            'capture_sha256': digest_json(row), 'actual_attendance': actual, 'confirmed_at': label['confirmed_at'],
            'source_name': label['source_name'], 'source_url': label['source_url'], 'forecasts': forecasts,
            'absolute_errors': {name: abs(float(value)-actual) for name, value in forecasts.items()},
            'signed_errors': {name: float(value)-actual for name, value in forecasts.items()}})
    return scores, sorted(missing), len({r['ticket_event_id'] for r in evidence})


def summary(scores, missing, captured_events):
    by_event = {}
    for row in scores: by_event.setdefault(row['ticket_event_id'], []).append(row)
    latest = sorted([max(rows, key=lambda r: pd.Timestamp(r['as_of_at'])) for rows in by_event.values()], key=lambda r: r['ticket_event_id'])
    clubs = sorted({r['club_slug'] for r in latest}); ready = len(latest) >= 30 and len(clubs) >= 8
    mean = lambda x: float(np.mean(x)) if len(x) else None
    metrics = {}
    for name in NAMES:
        ae = [r['absolute_errors'][name] for r in latest]
        metrics[name] = {'latest_row_mae': mean(ae),
            'event_balanced_window_mae': mean([mean([r['absolute_errors'][name] for r in rows]) for rows in by_event.values()]),
            'signed_bias': mean([r['signed_errors'][name] for r in latest]),
            'p90_absolute_error': float(np.quantile(ae, .9)) if ae else None, 'worst_absolute_error': max(ae) if ae else None}
    def pair(candidate, benchmark):
        delta = np.asarray([r['absolute_errors'][candidate]-r['absolute_errors'][benchmark] for r in latest])
        ci = None
        if ready:
            rng = np.random.default_rng(42)
            draws = np.concatenate([rng.choice(delta, size=(250, len(delta)), replace=True).mean(axis=1) for _ in range(40)])
            ci = [float(v) for v in np.quantile(draws, [.025, .975])]
        avg = mean(delta)
        return {'candidate': candidate, 'benchmark': benchmark, 'paired_delta_mae': avg,
            'median_event_delta_ae': float(np.median(delta)) if len(delta) else None,
            'event_improvement_rate': mean((delta < 0).astype(float)),
            'worst_event_degradation': max(0., float(delta.max())) if len(delta) else None,
            'paired_event_bootstrap_95_interval': ci,
            'evidence_gate_met': bool(ready and avg < 0 and ci[1] < 0)}
    learner = pair('seat_median_raw', 'ridge20_raw')
    governed = {name: pair('seat_median_policy', name) for name in ['ridge20_policy', 'original9_policy', 'prior']}
    def grouped(items, key):
        groups = {}
        for r in items: groups.setdefault(key(r), {}).setdefault(r['ticket_event_id'], []).append(r)
        return {label: {'independent_events': len(events), 'event_balanced_mae': {
            name: mean([mean([r['absolute_errors'][name] for r in rows]) for rows in events.values()]) for name in NAMES}}
            for label, events in sorted(groups.items())}
    def horizon(row):
        hours = (pd.Timestamp(row['kickoff_at'])-pd.Timestamp(row['as_of_at'])).total_seconds()/3600
        return '0_to_1_hours' if hours <= 1 else '1_to_6_hours' if hours <= 6 else '6_to_24_hours'
    return {'version': 'c1-seat-median-scorecard-v1', 'package_version': PACKAGE,
        'captured_independent_events': captured_events, 'scored_independent_events': len(latest), 'scored_rows': len(scores),
        'clubs': clubs, 'missing_outcome_event_ids': missing, 'metrics': metrics, 'first_review_ready': ready,
        'raw_learner_comparison': learner, 'governed_comparisons': governed,
        'learner_gate_met': learner['evidence_gate_met'],
        'product_gate_met': bool(ready and all(r['evidence_gate_met'] for r in governed.values())),
        'by_club_latest_descriptive': grouped(latest, lambda r: r['club_slug']),
        'by_horizon_window_descriptive': grouped(scores, horizon),
        'early_scores_descriptive_only': not ready, 'production_activation_allowed': False,
        'production_change': False, 'live_adjustment': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True); p.add_argument('--artifact-dir', type=Path, required=True)
    a = p.parse_args(); manifest, _, hashes = load_models(a.artifact_dir); ensure_runtime(a.runtime, manifest)
    files = sorted((a.runtime/'evidence').glob('event-*.json'))
    if len(files) > 10000: raise ValueError('Capture source exceeds bounded contract')
    reader = Reader(); outcomes = reader.request('ticket_event_outcomes?select=*&limit=1001')
    events = reader.request('ticket_events?select=id,club_slug,kickoff_at&limit=1001')
    if len(outcomes) >= 1000 or len(events) >= 1000: raise ValueError('Unpaginated scoring source expanded')
    now = datetime.now(timezone.utc)
    rows, missing, count = score_rows([json.loads(f.read_text()) for f in files], outcomes, events, manifest, hashes, now)
    for row in rows: persist_score(a.runtime/'scores'/f"event-{row['ticket_event_id']}-snapshot-{row['source_snapshot_id']}.json", row)
    report = summary(rows, missing, count)
    attempts = [json.loads(p.read_text()) for p in sorted(a.runtime.glob('attempt-*.json'))]
    failures = [e for r in attempts for e in r['events'] if e['status'] == 'FAILED_CLOSED']
    report['coverage'] = {'operational_attempts': len(attempts), 'candidate_attempts_including_repeats': sum(r['candidate_count'] for r in attempts),
                          'failed_event_attempts': len(failures), 'failed_event_ids': sorted({r['ticket_event_id'] for r in failures})}
    (a.runtime/'latest-scorecard.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    if report['first_review_ready'] and not (a.runtime/'first-review.json').exists():
        persist_score(a.runtime/'first-review.json', {'checked_at': now.isoformat(), 'scorecard': report,
                      'event_ids': sorted({r['ticket_event_id'] for r in rows})})
    print(json.dumps(report))


if __name__ == '__main__': main()
