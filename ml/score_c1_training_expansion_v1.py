"""Score immutable future paired captures only against confirmed attendance."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml.c1_training_expansion_v1 import PACKAGE, EVENT_IDS, MODEL_ID
from ml.c1_training_expansion_capture_v1 import load_frozen
from ml.demand_engine.run_c1_shadow_v8 import EXPECTED_PACKAGE
from ml.export_c1_matched_audit_inputs_v1 import Reader

PREDICTIONS = ('expanded_policy', 'original_policy', 'shared_prior', 'expanded_raw', 'original_raw')


def score_rows(evidence, outcomes, event_metadata, manifest, now):
    truth = {r['ticket_event_id']: r for r in outcomes}
    metadata = {r['id']: r for r in event_metadata}
    if len(truth) != len(outcomes) or len(metadata) != len(event_metadata):
        raise ValueError('Duplicate outcome/event identities')
    scores, missing, identities = [], set(), set()
    original_sha = manifest['old_frozen_hashes']['ml/artifacts/c1_shadow_v8/c1_v2_live_expert_v1.joblib']
    for row in evidence:
        event = row['ticket_event_id']; as_of = pd.Timestamp(row['as_of_at'])
        kickoff, issued = pd.Timestamp(row['kickoff_at']), pd.Timestamp(row['issued_at'])
        key = (event, as_of)
        if key in identities: raise ValueError('Duplicate captured event/time')
        identities.add(key)
        if (row.get('version') != 'c1-training-expansion-paired-evidence-v1' or row.get('package_version') != PACKAGE
                or row.get('manifest_sha256') != manifest['_verified_manifest_sha256']
                or row.get('artifact_sha256') != manifest['artifact']['sha256']
                or row.get('baseline_artifact_sha256') != original_sha
                or row.get('precommit_sha256') != manifest['precommit_sha256']
                or row.get('production_change') is not False or row.get('live_adjustment') != 0
                or row.get('known_outcome_at_capture') is not False or event in EVENT_IDS
                or not pd.Timestamp(manifest['frozen_at']) <= as_of <= issued < kickoff
                or issued-as_of > pd.Timedelta(hours=2) or issued > pd.Timestamp(now)):
            raise ValueError('Invalid frozen identity or prospective capture timing')
        for branch, raw_name, policy_name in [('expanded_decision', 'expanded_raw', 'expanded_policy'),
                                               ('original_decision', 'original_raw', 'original_policy')]:
            decision = row[branch]
            expected_sha = manifest['artifact']['sha256'] if branch == 'expanded_decision' else original_sha
            expected_package = PACKAGE if branch == 'expanded_decision' else EXPECTED_PACKAGE
            if (decision['source_snapshot_id'] != row['source_snapshot_id'] or pd.Timestamp(decision['as_of_at']) != as_of
                    or decision['artifact_sha256'] != expected_sha or decision['package_version'] != expected_package
                    or decision['structural_prior_p50'] != row['shared_prior']
                    or decision['v2_live_p50'] != row[raw_name] or decision['policy_prediction'] != row[policy_name]):
                raise ValueError('Stored paired output fields disagree')
        label = truth.get(event)
        if label is None:
            missing.add(event); continue
        confirmed = pd.Timestamp(label['confirmed_at']); actual = float(label['actual_attendance'])
        capacity = float(row['expanded_decision']['stadium_capacity'])
        if (not issued < confirmed <= pd.Timestamp(now) or confirmed < kickoff or not np.isfinite(actual)
                or isinstance(label['actual_attendance'], bool) or not 0 < actual <= capacity
                or not label.get('source_name') or not str(label.get('source_url', '')).startswith('https://')):
            raise ValueError('Outcome is invalid, lacks provenance or was known at issue time')
        meta = metadata[event]
        if not meta.get('club_slug') or pd.Timestamp(meta['kickoff_at']) != kickoff:
            raise ValueError('Scoring club/kickoff identity missing or changed')
        forecasts = {name: float(row[name]) for name in PREDICTIONS}
        if any(not np.isfinite(value) or not 0 <= value <= capacity for value in forecasts.values()):
            raise ValueError('Nonfinite/out-of-capacity captured forecast')
        scores.append({'ticket_event_id': event, 'source_snapshot_id': row['source_snapshot_id'],
                       'as_of_at': row['as_of_at'], 'kickoff_at': row['kickoff_at'], 'forecast_issued_at': row['issued_at'],
                       'club_slug': meta['club_slug'], 'actual_attendance': actual,
                       'confirmed_at': label['confirmed_at'], 'source_name': label['source_name'], 'source_url': label['source_url'],
                       'predictions': forecasts, 'absolute_errors': {k: abs(v-actual) for k,v in forecasts.items()},
                       'signed_errors': {k: v-actual for k,v in forecasts.items()}})
    return scores, sorted(missing), len({r['ticket_event_id'] for r in evidence})


def summary(scores, missing, captured_events):
    by_event = {}
    for row in scores: by_event.setdefault(row['ticket_event_id'], []).append(row)
    latest = [max(rows, key=lambda r: pd.Timestamp(r['as_of_at'])) for rows in by_event.values()]
    latest.sort(key=lambda r: r['ticket_event_id'])
    clubs = sorted({r['club_slug'] for r in latest})
    mean = lambda values: float(np.mean(values)) if values else None
    metrics = {}
    for name in PREDICTIONS:
        errors = [r['absolute_errors'][name] for r in latest]
        metrics[name] = {'latest_row_mae': mean(errors),
            'event_balanced_window_mae': mean([mean([r['absolute_errors'][name] for r in rows]) for rows in by_event.values()]),
            'signed_bias': mean([r['signed_errors'][name] for r in latest]),
            'p90_absolute_error': float(np.quantile(errors, .9)) if errors else None,
            'worst_absolute_error': max(errors) if errors else None}
    ready = len(latest) >= 30 and len(clubs) >= 8
    comparisons = {}
    for benchmark in ['original_policy', 'shared_prior']:
        delta = np.asarray([r['absolute_errors']['expanded_policy']-r['absolute_errors'][benchmark] for r in latest])
        ci = None
        if ready:
            rng = np.random.default_rng(42)
            # Bounded chunks avoid allocating10000xN for long-lived collection.
            draws = np.concatenate([rng.choice(delta, size=(250, len(delta)), replace=True).mean(axis=1) for _ in range(40)])
            ci = [float(v) for v in np.quantile(draws, [.025, .975])]
        comparisons[benchmark] = {'paired_mean_absolute_error_delta': mean(delta.tolist()),
                                   'paired_event_bootstrap_95_percent_interval': ci}
    advance = ready and all(v['paired_mean_absolute_error_delta'] < 0 and v['paired_event_bootstrap_95_percent_interval'][1] < 0
                            for v in comparisons.values())
    def grouped(items, key):
        groups = {}
        for row in items: groups.setdefault(key(row), {}).setdefault(row['ticket_event_id'], []).append(row)
        return {label: {'independent_events': len(events), 'rows': sum(map(len, events.values())),
                        'event_balanced_mae': {name: mean([mean([r['absolute_errors'][name] for r in rows])
                            for rows in events.values()]) for name in PREDICTIONS}}
                for label, events in sorted(groups.items())}
    def horizon(row):
        hours = (pd.Timestamp(row['kickoff_at'])-pd.Timestamp(row['as_of_at'])).total_seconds()/3600
        return '0_to_1_hours' if hours <= 1 else '1_to_6_hours' if hours <= 6 else '6_to_24_hours'
    return {'version': 'c1-training-expansion-scorecard-v1', 'captured_independent_events': captured_events,
            'scored_independent_events': len(latest), 'scored_rows': len(scores), 'clubs': clubs,
            'missing_outcome_event_ids': missing, 'metrics': metrics, 'paired_comparisons': comparisons,
            'by_club_latest_descriptive': grouped(latest, lambda r: r['club_slug']),
            'by_horizon_window_descriptive': grouped(scores, horizon),
            'first_review_ready': ready, 'research_evidence_gate_met': advance,
            'early_scores_descriptive_only': not ready, 'production_change': False, 'live_adjustment': 0}


def persist_score(path, row):
    raw = (json.dumps(row, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    if path.exists():
        if path.read_bytes() != raw: raise ValueError('Confirmed outcome/score conflict; never overwrite evidence')
        return
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with path.open('xb') as file: file.write(raw)
    path.chmod(0o440)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--artifact-dir', type=Path, required=True)
    a = p.parse_args()
    from ml.c1_live_matched_audit_v1 import ROOT
    if a.runtime.resolve().is_relative_to(ROOT): raise ValueError('Scoring outputs must remain private outside Git')
    manifest, *_ = load_frozen(a.artifact_dir)
    files = sorted((a.runtime/'evidence').glob('event-*.json'))
    if len(files) > 10000: raise ValueError('Bounded capture source unexpectedly expanded')
    reader = Reader()
    outcomes = reader.request('ticket_event_outcomes?select=*&limit=1001')
    events = reader.request('ticket_events?select=id,club_slug,kickoff_at&limit=1001')
    if len(outcomes) >= 1000 or len(events) >= 1000: raise ValueError('Unpaginated scoring source expanded')
    now = datetime.now(timezone.utc)
    rows, missing, count = score_rows([json.loads(f.read_text()) for f in files], outcomes, events, manifest, now)
    for row in rows:
        persist_score(a.runtime/'scores'/f"event-{row['ticket_event_id']}-snapshot-{row['source_snapshot_id']}.json", row)
    report = summary(rows, missing, count)
    attempts = [json.loads(p.read_text()) for p in sorted(a.runtime.glob('attempt-*.json'))]
    failed = [e for attempt in attempts for e in attempt['events'] if e['status'] == 'FAILED_CLOSED']
    report['capture_coverage'] = {'operational_attempts': len(attempts),
        'candidate_attempts_including_repeats': sum(r['candidate_count'] for r in attempts),
        'failed_event_attempts': len(failed), 'failed_event_ids': sorted({r['ticket_event_id'] for r in failed})}
    a.runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    (a.runtime/'latest-scorecard.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    # The first completed review becomes an immutable record; future summaries
    # cannot silently replace its cohort/decision with a later favorable one.
    if report['first_review_ready'] and not (a.runtime/'first-review.json').exists():
        persist_score(a.runtime/'first-review.json', {'checked_at': now.isoformat(), 'scorecard': report,
                      'event_ids': sorted({r['ticket_event_id'] for r in rows})})
    print(json.dumps(report))


if __name__ == '__main__': main()
