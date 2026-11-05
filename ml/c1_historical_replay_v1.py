"""Fixed, exposed historical recipe diagnostics; never the frozen26 live model."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor, Ridge

from ml.c1_alpha_t1_tournament_v2 import event_weights, pipeline
from ml.c1_support26_v1 import (BASE_IDS, NEW_IDS, ROOT, benchmark_bundle, read_training,
                               dependency_hashes, numerical_environment, LIBRARIES)
from ml.demand_engine.c1_shadow_runtime_v8 import apply_v8_policy
from ml.demand_engine.current_structural_prior_features import DEFAULT_KEY_ALIASES
from ml.demand_engine.run_c1_shadow_v8 import feature_record, sha256_file

VERSION = 'c1-historical-recipe-replay-v1'
PRECOMMIT = ROOT/'ml/C1_HISTORICAL_REPLAY_PRECOMMIT_V1.md'
SOURCES = ROOT/'ml/artifacts/c1_historical_replay_v1_source_hashes.json'
MIN_TRAIN_EVENTS = 9
RECIPES = ('median_expanded', 'median_base20', 'ridge_expanded')
FORECASTS = tuple(n+'_'+k for n in RECIPES for k in ('raw', 'policy')) + ('prior', 'original_c1_raw', 'original_c1_policy')


def stamp(value):
    t = pd.Timestamp(value)
    if pd.isna(t) or t.tzinfo is None:
        raise ValueError('Explicit timestamp required')
    return t.tz_convert('UTC')


def label_known_at(row):
    return max(stamp(row[k]) for k in ('confirmed_at', 'created_at', 'updated_at'))


def canonical_key(fixture):
    club = str(fixture['club_slug']).strip().lower()
    club = DEFAULT_KEY_ALIASES.get(club, club)
    return club, stamp(fixture['kickoff_at']).tz_convert('Europe/Warsaw').date().isoformat()


def unique_rows(rows, key):
    result = {int(r[key]): r for r in rows}
    if len(result) != len(rows):
        raise ValueError('Duplicate source identity')
    return result


def freeze_state():
    paths = [PRECOMMIT, SOURCES, Path(__file__), ROOT/'ml/C1_SUPPORT26_PRECOMMIT_V1.md']
    paths += list((ROOT/'ml/artifacts/c1_support26_v1').glob('*'))
    return {**dependency_hashes(), **{str(p.relative_to(ROOT)): sha256_file(p) for p in paths if p.is_file()}}


def write_json(path, value):
    with path.open('x') as file:
        json.dump(value, file, indent=2, sort_keys=True, allow_nan=False)
        file.write('\n')
    path.chmod(0o440)


def verify_sources(roots):
    expected = json.loads(SOURCES.read_text())
    for name, wanted in expected.items():
        root, filename = name.split('/', 1)
        if roots[root].resolve().is_relative_to(ROOT) or sha256_file(roots[root]/filename) != wanted:
            raise ValueError('Private historical source checksum/path differs')
    return expected


def load_data(roots):
    hashes = verify_sources(roots)
    _, benchmarks, _ = benchmark_bundle()
    training, features, _ = read_training(roots['training'], benchmarks)
    fixtures = unique_rows(json.loads((roots['training']/'canonical-fixtures.json').read_text()), 'id')
    keys = [canonical_key(v) for v in fixtures.values()]
    if len(set(keys)) != len(keys):
        raise ValueError('Canonical fixture aliases are not independent')
    outcomes = unique_rows(json.loads((roots['current']/'outcomes.json').read_text()), 'ticket_event_id')
    events = unique_rows(json.loads((roots['current']/'events.json').read_text()), 'ticket_event_id')
    if len(events) != 17 or set(events) != set(fixtures)-set(benchmarks['original9'].training_event_ids):
        raise ValueError('Exact seventeen historical live evaluation events changed')
    for event_id, rows in training.groupby('ticket_event_id'):
        truth = outcomes[int(event_id)]
        if rows.actual_attendance.nunique() != 1 or rows.actual_attendance.iloc[0] != truth['actual_attendance']:
            raise ValueError('Training labels changed across source rows')
        if label_known_at(truth) < stamp(fixtures[int(event_id)]['kickoff_at']):
            raise ValueError('Training label knowledge precedes its match')
    priors = {}
    for row in json.loads((roots['matched']/'resolved-priors.json').read_text()):
        if len(row['resolved']) != 1 or row['ticket_event_id'] in priors:
            raise ValueError('One unique actual historical prior required')
        priors[int(row['ticket_event_id'])] = row['resolved'][0]
    reps = {}
    matched = json.loads((roots['matched']/'matched-final24.json').read_text())['liveRows']
    if len(matched) != 44 or len({r['ticket_event_id'] for r in matched}) != 11:
        raise ValueError('Exact old eleven/44 prefix support changed')
    for row in matched:
        reps.setdefault(int(row['ticket_event_id']), []).append(row)
    for src in json.loads((roots['training']/'sources.json').read_text()):
        event_id = int(src['event']['ticket_event_id'])
        if event_id in priors or event_id in reps:
            raise ValueError('New six overlap older inputs')
        priors[event_id] = src['prior']
        reps[event_id] = [{'requested_as_of_at': src['event']['latest_as_of_at'],
            'requested_snapshot_id': src['feature']['snapshot_id'], 'features': src['feature']}]
    if set(reps) != set(events) or sum(map(len, reps.values())) != 50:
        raise ValueError('Exact actual live-time evaluation coverage changed')
    evaluation, parity = {}, []
    for event_id, raw_reps in reps.items():
        event, prior, fixture, truth = events[event_id], priors[event_id], fixtures[event_id], outcomes[event_id]
        raw_reps = sorted(raw_reps, key=lambda r: stamp(r['requested_as_of_at']))
        rows = validate_evaluation(event_id, raw_reps, prior, event, fixture, truth, benchmarks['original9'])
        original = benchmarks['original9'].predict_live_p50(rows[list(features)])
        error = abs(float(original[-1])-float(event['v2_live_p50']))
        if error > 1e-7:
            raise ValueError('Historical original C1raw parity failed')
        parity.append(error)
        rows['original_c1_raw'] = original
        rows['original_c1_policy'] = np.nan
        rows.loc[rows.index[-1], 'original_c1_policy'] = float(event['policy_prediction'])
        evaluation[event_id] = rows
    return training, features, fixtures, outcomes, events, evaluation, hashes, max(parity)


def validate_evaluation(event_id, reps, prior, event, fixture, truth, runtime):
    kickoff = stamp(fixture['kickoff_at'])
    times = [stamp(r['requested_as_of_at']) for r in reps]
    if (len(set(times)) != len(times) or not 1 <= len(times) <= 4
            or stamp(event['latest_as_of_at']) != times[-1]
            or stamp(event['kickoff_at']) != kickoff
            or event['actual_attendance'] != truth['actual_attendance']
            or not prior.get('point_in_time_validated') or prior.get('status') != 'ready'
            or prior.get('horizon') != 'T-1' or prior['ticket_event_id'] != event_id
            or float(prior['p50']) != float(event['structural_prior_p50'])
            or stamp(prior['target_as_of_at']) != kickoff-pd.Timedelta(hours=24)
            or stamp(prior['generated_at']) > times[0]
            or not kickoff-pd.Timedelta(hours=24) < times[0] <= times[-1] < kickoff < label_known_at(truth)):
        raise ValueError('Historical event/prior/label/time identity failed')
    actual, cap = float(truth['actual_attendance']), float(prior['stadium_capacity'])
    if not np.isfinite([actual, cap]).all() or not 0 < actual <= cap:
        raise ValueError('Invalid historical target/capacity')
    for name, error in [('structural_prior_p50', 'latest_prior_error'), ('v2_live_p50', 'latest_live_error'),
                        ('policy_prediction', 'latest_policy_error')]:
        if not np.isclose(abs(float(event[name])-actual), float(event[error]), rtol=0, atol=1e-7):
            raise ValueError('Persisted baseline error differs')
    selected = 'v2_live_p50' if event['selected_expert'] == 'LIVE' else 'structural_prior_p50'
    if event['selected_expert'] not in ('LIVE', 'PRIOR') or event['policy_prediction'] != event[selected]:
        raise ValueError('Persisted baseline selection differs')
    records = []
    for t, rep in zip(times, reps):
        f = rep['features']
        if (f.get('point_in_time_validated') is not True or stamp(f['as_of_at']) != t
                or f['snapshot_id'] != rep['requested_snapshot_id']
                or stamp(f.get('snapshot_captured_at', t)) > t
                or not np.isclose(float(f['hours_to_kickoff']), (kickoff-t).total_seconds()/3600, atol=1e-5)):
            raise ValueError('Historical feature source/PIT identity failed')
        record = feature_record({'prior': prior}, rep, runtime)
        records.append({'ticket_event_id': event_id, 'as_of_at': t.isoformat(),
                        'actual_attendance': actual, **record})
    return pd.DataFrame(records)


def training_fold(training, target_id, cutoff, fixtures, outcomes, design, base_only=False):
    if design not in ('chronological', 'leave_one_fixture_out'):
        raise ValueError('Unknown backtest design')
    target_key = canonical_key(fixtures[target_id])
    allowed = []
    for event_id, group in training.groupby('ticket_event_id'):
        event_id = int(event_id)
        if canonical_key(fixtures[event_id]) == target_key:
            continue
        if base_only and event_id not in BASE_IDS:
            continue
        if design == 'chronological' and (stamp(fixtures[event_id]['kickoff_at']) >= stamp(cutoff)
                or label_known_at(outcomes[event_id]) > stamp(cutoff)
                or any(stamp(v) >= stamp(cutoff) for v in group.as_of_at)):
            continue
        allowed.append(event_id)
    result = training[training.ticket_event_id.isin(allowed)].copy()
    if target_id in result.ticket_event_id.values:
        raise ValueError('Held-out fixture entered training')
    return result


def fit_predict(train, test, features, kind):
    if kind not in ('median', 'ridge') or len(train) == 0:
        raise ValueError('Unknown recipe/empty fold')
    target = train.actual_attendance.to_numpy(float)
    learner = QuantileRegressor(quantile=.5, alpha=.1, solver='highs', fit_intercept=True)
    if kind == 'ridge':
        learner = Ridge(alpha=10.0)
        target = target/train.stadium_capacity.to_numpy(float)
    # New unfitted imputer/indicators/scaler for EVERY fold, never a live artifact.
    estimator = pipeline(list(features), False, learner, scale=True)
    estimator.fit(train[list(features)], target, model__sample_weight=event_weights(train))
    predicted = np.asarray(estimator.predict(test[list(features)]), dtype=float)
    if kind == 'ridge':
        predicted *= test.stadium_capacity.to_numpy(float)
    if not np.isfinite(predicted).all():
        raise ValueError('Non-finite historical prediction')
    return np.clip(predicted, 0, test.stadium_capacity.to_numpy(float)), {
        'preprocessor_joblib_hash': joblib.hash(estimator.named_steps['prep']),
        'fit_rows': len(train), 'fit_events': int(train.ticket_event_id.nunique())}


def policy_prefixes(raw, rows):
    times = [stamp(t) for t in rows.as_of_at]
    elapsed = np.array([(t-times[0]).total_seconds()/3600 for t in times])
    prior, cap = float(rows.prior_p50.iloc[0]), float(rows.stadium_capacity.iloc[0])
    return [apply_v8_policy(prior_p50=prior, stadium_capacity=cap,
            live_history_p50=raw[:i+1], elapsed_hours=elapsed[:i+1])['policy_prediction'] for i in range(len(raw))]


def metrics(rows):
    if not rows:
        return {'events': 0, 'rows': 0, 'models': {}, 'comparisons': {}}
    by_event = {}
    for row in rows:
        by_event.setdefault(row['ticket_event_id'], []).append(row)
    latest = [max(v, key=lambda r: stamp(r['as_of_at'])) for v in by_event.values()]
    model_metrics = {}
    errors = {}
    for name in FORECASTS:
        ae = np.array([abs(r['predictions'][name]-r['actual_attendance']) for r in latest])
        bias = [r['predictions'][name]-r['actual_attendance'] for r in latest]
        window = None
        if name != 'original_c1_policy':
            window = float(np.mean([np.mean([abs(r['predictions'][name]-r['actual_attendance']) for r in group])
                                    for group in by_event.values()]))
        errors[name] = ae
        model_metrics[name] = {'latest_row_mae': float(ae.mean()), 'event_balanced_window_mae': window,
            'signed_bias': float(np.mean(bias)), 'p90_event_absolute_error': float(np.quantile(ae, .9)),
            'worst_event_absolute_error': float(max(ae))}
    pairs = [(n, b) for n in ('median_expanded_raw', 'median_expanded_policy')
             for b in ('prior', 'original_c1_policy', 'median_base20_'+n.rsplit('_', 1)[1],
                       'ridge_expanded_'+n.rsplit('_', 1)[1])]
    comparisons = {}
    for challenger, baseline in pairs:
        delta = errors[challenger]-errors[baseline]
        rng = np.random.default_rng(42)
        draws = rng.choice(delta, size=(10000, len(delta)), replace=True).mean(axis=1)
        comparisons[challenger+'_minus_'+baseline] = {
            'delta_latest_mae': float(delta.mean()), 'median_delta_absolute_error': float(np.median(delta)),
            'event_improvement_rate': float(np.mean(delta < 0)), 'worst_event_degradation': float(max(delta)),
            'paired_event_bootstrap_95_interval': np.quantile(draws, [.025, .975]).tolist(),
            'descriptive_only': True}
    return {'events': len(latest), 'rows': len(rows), 'models': model_metrics, 'comparisons': comparisons}


def run_design(training, features, fixtures, outcomes, evaluation, design):
    forecasts, folds, failures = [], [], []
    for target_id in sorted(evaluation, key=lambda i: stamp(evaluation[i].as_of_at.iloc[0])):
        test = evaluation[target_id].copy()
        cutoff = stamp(test.as_of_at.iloc[0])
        expanded = training_fold(training, target_id, cutoff, fixtures, outcomes, design)
        base = training_fold(training, target_id, cutoff, fixtures, outcomes, design, base_only=True)
        sizes = {'expanded': int(expanded.ticket_event_id.nunique()), 'base20': int(base.ticket_event_id.nunique())}
        fold = {'ticket_event_id': target_id, 'cutoff': cutoff.isoformat(), 'train_events': sizes,
                'expanded_ids': sorted(int(v) for v in expanded.ticket_event_id.unique()),
                'base20_ids': sorted(int(v) for v in base.ticket_event_id.unique()),
                'test_rows': len(test), 'target_in_training': False,
                'new6_training_events': int(expanded.ticket_event_id.isin(NEW_IDS).groupby(expanded.ticket_event_id).any().sum())}
        if min(sizes.values()) < MIN_TRAIN_EVENTS:
            failures.append({**fold, 'status': 'INSUFFICIENT_EARLIER_TRAINING_SUPPORT'})
            continue
        predictions, fits = {}, {}
        for name in RECIPES:
            train = base if name == 'median_base20' else expanded
            raw, receipt = fit_predict(train, test, features, 'ridge' if name.startswith('ridge') else 'median')
            predictions[name+'_raw'] = raw
            predictions[name+'_policy'] = policy_prefixes(raw, test)
            fits[name] = receipt
        fold['fits'] = fits
        folds.append(fold)
        for i, row in enumerate(test.to_dict('records')):
            values = {name: float(predictions[name][i]) for name in predictions}
            values['prior'] = float(row['prior_p50'])
            values['original_c1_raw'] = float(row['original_c1_raw'])
            values['original_c1_policy'] = None if pd.isna(row['original_c1_policy']) else float(row['original_c1_policy'])
            forecasts.append({'ticket_event_id': target_id, 'as_of_at': row['as_of_at'],
                'club_slug': fixtures[target_id]['club_slug'], 'hours_to_kickoff': float(row['hours_to_kickoff']),
                'actual_attendance': float(row['actual_attendance']), 'predictions': values,
                'sparse_single_latest_context': len(test) == 1,
                'sample_group': 'later6_single_prefix' if target_id in NEW_IDS else 'earlier11_four_prefixes'})
    groups = {}
    for field in ('club_slug', 'sample_group'):
        groups[field] = {str(v): metrics([r for r in forecasts if r[field] == v]) for v in sorted({r[field] for r in forecasts})}
    horizon = lambda r: '0_to_6h' if r['hours_to_kickoff'] <= 6 else '6_to_12h' if r['hours_to_kickoff'] <= 12 else '12_to_24h'
    groups['horizon'] = {}
    for bucket in ('0_to_6h', '6_to_12h', '12_to_24h'):
        subset = [r for r in forecasts if horizon(r) == bucket]
        # Stored C1policy exists only at each fixture's final representative.
        # Horizon reports use only forecasts with that baseline actually available.
        subset = [r for r in subset if r['predictions']['original_c1_policy'] is not None]
        groups['horizon'][bucket] = metrics(subset)
    return {'design': design, 'headline': metrics(forecasts), 'groups': groups,
        'coverage': {'predeclared_target_events': len(evaluation), 'eligible_events': len(folds),
            'excluded_events': len(failures), 'scored_prefixes': len(forecasts),
            'new6_training_count_by_fold': [r['new6_training_events'] for r in folds]},
        'folds': folds, 'failures': failures, 'forecasts': forecasts}


def public_result(result):
    output = {k: v for k, v in result.items() if k != 'designs'}
    output['designs'] = {}
    for name, design in result['designs'].items():
        # Public aggregate results contain no fixture source rows/identities.
        output['designs'][name] = {k: design[k] for k in ('design', 'headline', 'coverage')}
        output['designs'][name]['sample_groups'] = design['groups']['sample_group']
        output['designs'][name]['horizon_latest_only'] = design['groups']['horizon']
    return output


def execute(roots, output, publication):
    if output.resolve().is_relative_to(ROOT) or output.exists():
        raise ValueError('Require new private run directory outside Git')
    if numerical_environment() != LIBRARIES:
        raise ValueError('Pinned numerical environment differs')
    proof = json.loads(publication.read_text())
    if (proof.get('implementation_sha256') != sha256_file(Path(__file__))
            or proof.get('precommit_sha256') != sha256_file(PRECOMMIT)
            or proof.get('source_manifest_sha256') != sha256_file(SOURCES)
            or proof.get('remote_ref_verified') is not True):
        raise ValueError('Require exact implementation/protocol publication before fitting')
    before = freeze_state()
    training, features, fixtures, outcomes, events, evaluation, sources, parity = load_data(roots)
    output.mkdir(mode=0o700, parents=True)
    write_json(output/'RUN_STARTED.json', {'version': VERSION, 'started_at': datetime.now(timezone.utc).isoformat(),
                                         'publication': proof, 'frozen_sha256': before})
    result = {'version': VERSION, 'evidence_kind': 'EXPOSED_HISTORICAL_RECIPE_DIAGNOSTIC',
        'production_change': False, 'live_adjustment': 0, 'frozen26_accuracy_estimated': False,
        'historical_source_publication_times_independently_verified': False,
        'chronological_training_label_knowledge_enforced': True, 'prospective_evidence': False,
        'source_sha256': sources, 'precommit_sha256': sha256_file(PRECOMMIT),
        'implementation_sha256': sha256_file(Path(__file__)), 'frozen_sources_and_artifacts_unchanged': True,
        'original_c1_latest_raw_max_parity_error': parity, 'evaluation_events': len(events),
        'available_evaluation_prefixes': sum(map(len, evaluation.values())), 'training_rows': len(training),
        'features': len(features), 'libraries': numerical_environment(),
        'policy_sparse_context_caveat': 'later6 have one reconstructed latest input, not complete original policy history',
        'designs': {}}
    for design in ('chronological', 'leave_one_fixture_out'):
        result['designs'][design] = run_design(training, features, fixtures, outcomes, evaluation, design)
    if before != freeze_state():
        raise ValueError('Frozen model/source/protocol changed during diagnostic')
    result['completed_at'] = datetime.now(timezone.utc).isoformat()
    write_json(output/'result.json', result)
    write_json(output/'public-summary.json', public_result(result))
    print(json.dumps({'version': VERSION, 'designs': {n: {'events': d['headline']['events'],
        'models': d['headline']['models'], 'coverage': d['coverage']} for n, d in result['designs'].items()},
        'frozen_sources_and_artifacts_unchanged': True}, allow_nan=False))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--training-dir', type=Path, required=True)
    p.add_argument('--matched-dir', type=Path, required=True)
    p.add_argument('--current-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--publication-receipt', type=Path, required=True)
    a = p.parse_args()
    execute({'training': a.training_dir, 'matched': a.matched_dir, 'current': a.current_dir}, a.output_dir, a.publication_receipt)


if __name__ == '__main__':
    main()
