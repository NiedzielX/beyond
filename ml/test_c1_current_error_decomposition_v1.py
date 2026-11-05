from copy import deepcopy
import unittest

from ml.c1_current_error_decomposition_v1 import decompose, EXPECTED_PACKAGE


def inputs():
    rows, outcomes, metadata = [], [], []
    for event_id, prior, raw, selected in [(5, 800, 400, 'PRIOR'), (6, 600, 750, 'LIVE')]:
        policy = prior if selected == 'PRIOR' else raw
        rows.append({'ticket_event_id': event_id, 'package_version': EXPECTED_PACKAGE,
            'kickoff_at': '2026-10-31T17:00:00Z', 'latest_as_of_at': '2026-10-31T16:00:00Z',
            'hours_to_kickoff': 1, 'structural_prior_p50': prior, 'v2_live_p50': raw,
            'policy_prediction': policy, 'selected_expert': selected, 'actual_attendance': 700,
            'outcome_available': True, 'scored_at': '2026-11-01T17:00:00Z',
            'latest_prior_error': abs(prior-700), 'latest_live_error': abs(raw-700),
            'latest_policy_error': abs(policy-700), 'window_prior_mae': abs(prior-700),
            'window_live_mae': abs(raw-700), 'window_policy_mae': abs(policy-700)})
        outcomes.append({'ticket_event_id': event_id, 'actual_attendance': 700,
            'confirmed_at': '2026-11-01T16:00:00Z', 'source_name': 'verified source', 'source_url': 'https://example.com/report'})
        metadata.append({'id': event_id, 'club_slug': f'club{event_id}', 'kickoff_at': rows[-1]['kickoff_at']})
    status = {'package_version': EXPECTED_PACKAGE, 'production_live_adjustment': 0,
        'refreshed_at': '2026-11-05T10:00:00Z', 'prospective_event_count': 2, 'scored_event_count': 2,
        'latest_row_prior_mae': 100, 'latest_row_live_mae': 175, 'latest_row_policy_mae': 75,
        'representative_window_prior_mae': 100, 'representative_window_live_mae': 175,
        'representative_window_policy_mae': 75}
    return rows, status, outcomes, metadata, '2026-11-05T10:00:00Z'


class DecompositionTests(unittest.TestCase):
    def test_event_balanced_reconciliation_and_diagnostic_oracle(self):
        args = inputs(); before = deepcopy(args)
        result = decompose(*args)
        self.assertEqual(args, before)
        self.assertEqual(result['headline']['metrics']['policy']['latest_row_mae'], 75)
        self.assertEqual(result['headline']['metrics']['policy']['signed_bias'], 75)
        self.assertEqual(result['headline']['policy_minus_prior_mae'], -25)
        self.assertEqual(result['headline']['policy_improvement_rate'], .5)
        self.assertEqual(result['headline']['outcome_aware_prior_raw_oracle_mae_DIAGNOSTIC_ONLY'], 75)
        self.assertEqual(result['by_exposed_cohort']['earlier_11']['independent_events'], 1)
        self.assertEqual(result['by_exposed_cohort']['subsequently_scored']['independent_events'], 1)
        self.assertEqual(result['models_fitted'], 0)

    def test_wrong_label_corrupt_error_and_selected_expert_fail_closed(self):
        for key, value in [('actual_attendance', 701), ('latest_policy_error', 999),
                           ('policy_prediction', 400), ('v2_live_p50', float('nan')),
                           ('structural_prior_p50', True), ('window_prior_mae', -1)]:
            args = inputs(); args[0][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                decompose(*args)

    def test_chronology_and_naive_timestamps_fail_closed(self):
        for source, key, value in [(0, 'latest_as_of_at', '2026-10-31T18:00:00Z'),
                                   (0, 'latest_as_of_at', '2026-10-31T16:00:00'),
                                   (0, 'scored_at', '2026-11-01T15:00:00Z'),
                                   (2, 'confirmed_at', '2026-10-31T15:00:00Z'),
                                   (2, 'confirmed_at', '2026-11-06T15:00:00Z')]:
            args = inputs(); args[source][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                decompose(*args)

    def test_duplicate_ticket_and_canonical_fixture_do_not_inflate_events(self):
        args = inputs(); args[0].append(deepcopy(args[0][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate event'):
            decompose(*args)
        args = inputs(); args[3][1]['club_slug'] = args[3][0]['club_slug']
        with self.assertRaisesRegex(ValueError, 'same canonical'):
            decompose(*args)
        args = inputs(); args[3][0]['club_slug'] = 'korona'; args[3][1]['club_slug'] = 'koronakielce'
        with self.assertRaisesRegex(ValueError, 'same canonical'):
            decompose(*args)

    def test_status_counts_and_latest_and_window_metrics_must_all_match(self):
        for key, value in [('prospective_event_count', 3), ('scored_event_count', 1),
                           ('latest_row_policy_mae', 50), ('representative_window_live_mae', 50),
                           ('package_version', 'other'), ('production_live_adjustment', 1),
                           ('refreshed_at', '2026-11-05T09:55:00Z')]:
            args = inputs(); args[1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                decompose(*args)

    def test_unscored_coverage_remains_visible_and_cannot_hide_known_labels(self):
        args = inputs(); row = args[0][1]; row['outcome_available'] = False
        for key in ['actual_attendance', 'scored_at', 'latest_prior_error', 'latest_live_error',
                    'latest_policy_error', 'window_prior_mae', 'window_live_mae', 'window_policy_mae']:
            row[key] = None
        with self.assertRaisesRegex(ValueError, 'Unscored row conflicts'):
            decompose(*args)
        args[2].pop(); args[1]['scored_event_count'] = 1
        for key in ['latest_row_prior_mae', 'representative_window_prior_mae',
                    'latest_row_policy_mae', 'representative_window_policy_mae']:
            args[1][key] = 100
        args[1]['latest_row_live_mae'] = args[1]['representative_window_live_mae'] = 300
        result = decompose(*args)
        self.assertEqual(result['pending_event_ids'], [6])
        self.assertEqual(result['forecast_events'], 2)
        self.assertEqual(result['headline']['independent_events'], 1)


if __name__ == '__main__':
    unittest.main()
