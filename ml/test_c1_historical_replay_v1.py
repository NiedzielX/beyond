"""Leakage, time, pairing and immutable-run protections for exposed replay."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from ml import c1_historical_replay_v1 as replay


def fold_fixture():
    fixtures = {
        1: {'club_slug': 'a', 'kickoff_at': '2026-10-01T18:00:00Z'},
        2: {'club_slug': 'b', 'kickoff_at': '2026-10-02T18:00:00Z'},
        3: {'club_slug': 'c', 'kickoff_at': '2026-10-05T18:00:00Z'},
        4: {'club_slug': 'd', 'kickoff_at': '2026-10-10T18:00:00Z'},
    }
    outcomes = {i: {k: f'2026-10-{day:02d}T21:00:00Z' for k in ('confirmed_at', 'created_at', 'updated_at')}
                for i, day in [(1, 1), (2, 2), (3, 5), (4, 10)]}
    train = pd.DataFrame([{'ticket_event_id': i, 'as_of_at': f'2026-10-{day:02d}T12:00:00Z',
        'actual_attendance': 100+i, 'stadium_capacity': 1000, 'prior_p50': 100, 'value': float(i)}
        for i, day in [(1, 1), (1, 1), (2, 2), (3, 5), (4, 10)]])
    return train, fixtures, outcomes


def score_row(event, time, actual, prediction):
    return {'ticket_event_id': event, 'as_of_at': time, 'actual_attendance': actual,
            'predictions': {name: prediction for name in replay.FORECASTS}}


class HistoricalReplayTests(unittest.TestCase):
    def test_entire_target_fixture_excluded_with_all_prefixes(self):
        train, fixtures, outcomes = fold_fixture()
        fold = replay.training_fold(train, 1, '2026-10-06T12:00:00Z', fixtures, outcomes, 'leave_one_fixture_out')
        self.assertEqual(set(fold.ticket_event_id), {2, 3, 4})

    def test_chronological_training_excludes_future_events(self):
        train, fixtures, outcomes = fold_fixture()
        fold = replay.training_fold(train, 3, '2026-10-05T12:00:00Z', fixtures, outcomes, 'chronological')
        self.assertEqual(set(fold.ticket_event_id), {1, 2})

    def test_late_label_revision_is_not_known_from_earlier_confirmation(self):
        train, fixtures, outcomes = fold_fixture()
        outcomes[2]['updated_at'] = '2026-11-04T18:00:00Z'
        fold = replay.training_fold(train, 3, '2026-10-05T12:00:00Z', fixtures, outcomes, 'chronological')
        self.assertEqual(set(fold.ticket_event_id), {1})

    def test_training_rows_at_or_after_cutoff_are_excluded_as_whole_event(self):
        train, fixtures, outcomes = fold_fixture()
        train.loc[train.ticket_event_id == 1, 'as_of_at'] = '2026-10-05T12:00:00Z'
        fold = replay.training_fold(train, 3, '2026-10-05T12:00:00Z', fixtures, outcomes, 'chronological')
        self.assertEqual(set(fold.ticket_event_id), {2})

    def test_same_canonical_fixture_under_another_id_is_excluded(self):
        train, fixtures, outcomes = fold_fixture()
        fixtures[2] = {'club_slug': ' A ', 'kickoff_at': fixtures[1]['kickoff_at']}
        fold = replay.training_fold(train, 1, '2026-10-06T12:00:00Z', fixtures, outcomes, 'leave_one_fixture_out')
        self.assertEqual(set(fold.ticket_event_id), {3, 4})

    def test_missing_knowledge_timestamp_and_naive_time_fail_closed(self):
        for row in [{'confirmed_at': '2026-10-01T12:00:00Z'},
                    {k: '2026-10-01T12:00:00' for k in ('confirmed_at', 'created_at', 'updated_at')}]:
            with self.assertRaises((ValueError, KeyError)):
                replay.label_known_at(row)

    def test_fold_local_scaler_never_sees_extreme_test_values(self):
        train, _, _ = fold_fixture()
        test = train.iloc[:1].copy(); test['value'] = 1000000
        features = ['stadium_capacity', 'prior_p50', 'value']
        real_pipeline = replay.pipeline
        built = []
        def capture(*args, **kwargs):
            estimator = real_pipeline(*args, **kwargs); built.append(estimator); return estimator
        with patch.object(replay, 'pipeline', side_effect=capture):
            replay.fit_predict(train, test, features, 'median')
        scale = built[0].named_steps['prep'].named_transformers_['num'].named_steps['scale']
        self.assertAlmostEqual(scale.mean_[-1], train.value.mean())
        self.assertLess(scale.mean_[-1], 10)

    def test_holdout_attendance_cannot_change_predictions_or_preprocessing(self):
        train, _, _ = fold_fixture()
        test = train.iloc[:1].copy()
        features = ['stadium_capacity', 'prior_p50', 'value']
        p1, receipt1 = replay.fit_predict(train, test, features, 'median')
        test['actual_attendance'] = 999999999
        p2, receipt2 = replay.fit_predict(train, test, features, 'median')
        np.testing.assert_array_equal(p1, p2)
        self.assertEqual(receipt1, receipt2)

    def test_event_weights_do_not_amplify_multiple_prefixes(self):
        train, _, _ = fold_fixture()
        weights = pd.Series(replay.event_weights(train), index=train.index)
        totals = weights.groupby(train.ticket_event_id).sum()
        self.assertEqual(totals.nunique(), 1)

    def test_policy_prefixes_never_receive_later_predictions(self):
        rows = pd.DataFrame({'as_of_at': ['2026-10-05T12:00:00Z', '2026-10-05T15:00:00Z'],
                             'prior_p50': [100, 100], 'stadium_capacity': [1000, 1000]})
        a = replay.policy_prefixes(np.array([500., 600.]), rows)
        b = replay.policy_prefixes(np.array([500., 1.]), rows)
        self.assertEqual(a[0], b[0])

    def test_primary_mae_counts_each_event_once(self):
        rows = [score_row(1, '2026-10-05T12:00:00Z', 100, 100),
                score_row(1, '2026-10-05T13:00:00Z', 100, 100),
                score_row(2, '2026-10-06T12:00:00Z', 100, 300)]
        report = replay.metrics(rows)
        self.assertEqual(report['events'], 2)
        self.assertEqual(report['models']['prior']['latest_row_mae'], 100)
        self.assertEqual(report['models']['prior']['event_balanced_window_mae'], 100)
        self.assertIsNone(report['models']['original_c1_policy']['event_balanced_window_mae'])

    def test_window_metric_does_not_read_unavailable_persisted_policy(self):
        rows = [score_row(1, '2026-10-05T12:00:00Z', 100, 100),
                score_row(1, '2026-10-05T13:00:00Z', 100, 300)]
        rows[0]['predictions']['original_c1_policy'] = None
        report = replay.metrics(rows)
        self.assertEqual(report['models']['original_c1_policy']['latest_row_mae'], 200)

    def test_empty_design_keeps_null_metrics_and_coverage(self):
        self.assertEqual(replay.metrics([]), {'events': 0, 'rows': 0, 'models': {}, 'comparisons': {}})

    def test_public_summary_excludes_private_rows_and_club_identifiers(self):
        private = {'version': replay.VERSION, 'designs': {'chronological': {
            'design': 'chronological', 'headline': {}, 'coverage': {}, 'folds': [{'ticket_event_id': 1}],
            'forecasts': [{'actual_attendance': 123}], 'groups': {'club_slug': {'private-club': {}},
                'sample_group': {}, 'horizon': {}}}}}
        raw = json.dumps(replay.public_result(private))
        for text in ['ticket_event_id', 'actual_attendance', 'private-club', 'folds', 'forecasts']:
            self.assertNotIn(text, raw)

    def test_existing_run_directory_rejected_before_fit(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(replay, 'fit_predict') as fit:
            with self.assertRaisesRegex(ValueError, 'new private run'):
                replay.execute({}, Path(directory), Path(directory)/'missing-proof')
            fit.assert_not_called()

    def test_immutable_result_file_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'result.json'; replay.write_json(path, {'first': True})
            with self.assertRaises(FileExistsError):
                replay.write_json(path, {'first': False})
            self.assertEqual(json.loads(path.read_text()), {'first': True})

    def test_source_hash_change_fails_before_reading_or_fitting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'data.json'; source.write_text('{}')
            manifest = root/'hashes.json'; manifest.write_text(json.dumps({'training/data.json': '0'*64}))
            with patch.object(replay, 'SOURCES', manifest), self.assertRaisesRegex(ValueError, 'checksum'):
                replay.verify_sources({'training': root})

    def test_insufficient_folds_remain_recorded_without_fit(self):
        train, fixtures, outcomes = fold_fixture()
        test = train[train.ticket_event_id == 3]
        with patch.object(replay, 'fit_predict') as fit:
            result = replay.run_design(train, ['stadium_capacity', 'prior_p50', 'value'], fixtures, outcomes,
                                       {3: test}, 'chronological')
        fit.assert_not_called()
        self.assertEqual(result['coverage']['excluded_events'], 1)
        self.assertEqual(result['headline']['events'], 0)
        self.assertEqual(result['failures'][0]['status'], 'INSUFFICIENT_EARLIER_TRAINING_SUPPORT')


if __name__ == '__main__':
    unittest.main()
