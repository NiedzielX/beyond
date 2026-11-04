from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from ml.c1_training_expansion_capture_v1 import capture
from ml.test_c1_training_expansion_v1 import fixture, NOW
from ml.score_c1_training_expansion_v1 import score_rows, summary, persist_score


def scored_fixture():
    data = fixture()
    with tempfile.TemporaryDirectory() as d:
        capture(*data, now=NOW, labelled_ids=set(), output_dir=Path(d))
        evidence = [json.loads(next(Path(d).glob('event-*.json')).read_text())]
    outcome = [{'ticket_event_id': 501, 'actual_attendance': 750,
                'confirmed_at': '2026-11-05T21:00:00Z', 'source_name': 'synthetic',
                'source_url': 'https://example.invalid/test-only'}]
    meta = [{'id': 501, 'club_slug': 'synthetic', 'kickoff_at': evidence[0]['kickoff_at']}]
    return evidence, outcome, meta, data[1], '2026-11-05T22:00:00Z'


class ExpansionScoreTests(unittest.TestCase):
    def test_synthetic_capture_then_later_confirmed_truth_scores_both_models(self):
        rows, missing, count = score_rows(*scored_fixture())
        report = summary(rows, missing, count)
        self.assertEqual(report['metrics']['expanded_policy']['latest_row_mae'], 50)
        self.assertEqual(report['metrics']['original_policy']['latest_row_mae'], 450)
        self.assertEqual(report['paired_comparisons']['original_policy']['paired_mean_absolute_error_delta'], -400)
        self.assertFalse(report['research_evidence_gate_met']); self.assertFalse(report['first_review_ready'])
        self.assertIsNone(report['paired_comparisons']['original_policy']['paired_event_bootstrap_95_percent_interval'])

    def test_missing_truth_stays_missing_and_mae_is_null(self):
        data = list(scored_fixture()); data[1] = []
        rows, missing, count = score_rows(*data); report = summary(rows, missing, count)
        self.assertEqual(missing, [501]); self.assertEqual(count, 1)
        self.assertIsNone(report['metrics']['expanded_policy']['latest_row_mae'])

    def test_known_or_future_outcome_cannot_score(self):
        for confirmed in ['2026-11-05T13:00:00Z', '2026-11-05T23:00:00Z']:
            data = list(scored_fixture()); data[1][0]['confirmed_at'] = confirmed
            with self.subTest(confirmed=confirmed), self.assertRaisesRegex(ValueError, 'Outcome'): score_rows(*data)

    def test_identity_or_prediction_corruption_fails_instead_of_dropping_event(self):
        for change in [{'expanded_policy': 0}, {'manifest_sha256': 'changed'}, {'issued_at': '2026-11-05T19:00:00Z'}]:
            data = list(scored_fixture()); data[0][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError): score_rows(*data)

    def test_latest_time_is_selected_without_using_error_and_window_is_event_balanced(self):
        rows, _, _ = score_rows(*scored_fixture())
        early = deepcopy(rows[0]); early['as_of_at'] = '2026-11-05T12:00:00Z'
        early['absolute_errors']['expanded_policy'] = 0
        other = deepcopy(rows[0]); other['ticket_event_id'] = 502; other['club_slug'] = 'synthetic2'
        other['absolute_errors']['expanded_policy'] = 100
        report = summary([early, rows[0], other], [], 2)
        self.assertEqual(report['metrics']['expanded_policy']['latest_row_mae'], 75)
        self.assertEqual(report['metrics']['expanded_policy']['event_balanced_window_mae'], 62.5)
        self.assertEqual(report['scored_independent_events'], 2)

    def test_duplicate_and_missing_club_cannot_silently_change_denominator(self):
        data = list(scored_fixture()); data[0].append(deepcopy(data[0][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'): score_rows(*data)
        data = list(scored_fixture()); data[2][0]['club_slug'] = None
        with self.assertRaisesRegex(ValueError, 'club'): score_rows(*data)

    def test_persisted_score_cannot_be_replaced_by_new_label(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'score.json'; score = {'actual': 100}
            persist_score(path, score); raw = path.read_bytes(); persist_score(path, score)
            with self.assertRaisesRegex(ValueError, 'conflict'): persist_score(path, {'actual': 101})
            self.assertEqual(path.read_bytes(), raw)

    def test_fixed_review_requires_club_support_and_paired_uncertainty(self):
        rows, _, _ = score_rows(*scored_fixture())
        cohort = []
        for index in range(30):
            row = deepcopy(rows[0]); row['ticket_event_id'] = 1000+index; row['club_slug'] = str(index%8)
            cohort.append(row)
        report = summary(cohort, [], 30)
        self.assertTrue(report['first_review_ready']); self.assertTrue(report['research_evidence_gate_met'])
        self.assertEqual(report['paired_comparisons']['original_policy']['paired_event_bootstrap_95_percent_interval'], [-400, -400])
        for row in cohort: row['club_slug'] = 'one'
        self.assertFalse(summary(cohort, [], 30)['first_review_ready'])


if __name__ == '__main__': unittest.main()
