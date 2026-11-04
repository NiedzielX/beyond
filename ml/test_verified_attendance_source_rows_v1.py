from copy import deepcopy
import unittest

from ml.verified_attendance_source_rows_v1 import parse_source, match_completed_event, prepare_import_rows


def source(text):
    return {'http_status': 200, 'error_type': None, 'text_truncated': False,
            'url': 'https://www.frekwencyjny.pl/kluby/wisla-krakow', 'sha256': 'test-hash',
            'retrieved_at': '2026-11-04T13:45:00+00:00', 'text': text}


class VerifiedSourceRowsTests(unittest.TestCase):
    def test_import_uses_actual_verification_time_preserving_retrieval(self):
        row = parse_source(source('Wisła K. 2:1 Śląsk 33 000 2026/2027 • Ekstraklasa • 18.09.2026 20:30'))[0]
        row['verification_reason'] = 'Exact verified fixture'
        before = deepcopy(row); now = '2026-11-04T17:30:00+00:00'
        result = prepare_import_rows([row], [], now)[0]
        self.assertEqual(result['source_observed_at'], now)
        self.assertEqual(result['source_payload']['retrieved_at'], before['source_observed_at'])
        self.assertEqual(row, before)
        self.assertEqual(prepare_import_rows([row], [result], now), [])
        conflict = {**result, 'actual_attendance': 1}
        with self.assertRaisesRegex(ValueError, 'updates forbidden'): prepare_import_rows([row], [conflict], now)
        with self.assertRaisesRegex(ValueError, 'backdate'): prepare_import_rows([row], [], '2026-11-04T10:00:00+00:00')

    def test_current_season_fixture_retains_count_context_and_known_at(self):
        s = source('Wisła K. 2:1 Śląsk 33 000 2026/2027 • Ekstraklasa • 18.09.2026 20:30'); before = deepcopy(s)
        r = parse_source(s)[0]
        self.assertEqual(r['actual_attendance'], 33000); self.assertEqual(r['kickoff_at'], '2026-09-18T18:30:00+00:00')
        self.assertEqual(r['source_observed_at'], s['retrieved_at']); self.assertFalse(r['source_payload']['knowledge_backdated'])
        self.assertEqual(s, before)

    def test_warsaw_dst_transition_uses_one_hour_offset_after_october25(self):
        r = parse_source(source('Śląsk 2:0 Wieczysta 12 391 2026/2027 • Ekstraklasa • 25.10.2026 12:15'))[0]
        self.assertEqual(r['kickoff_at'], '2026-10-25T11:15:00+00:00')

    def test_homepage_canonical_rows_can_match_completed_target_exactly(self):
        rows = parse_source(source('31.10 17:30 31.10.2026 17:30 Lech 3:1 Wisła K. 36 229'))
        event = {'id': 6, 'home_team': 'Lech Poznań', 'away_team': 'Wisła Kraków', 'club_slug': 'lech',
                 'competition': 'Ekstraklasa', 'kickoff_at': '2026-10-31T16:30:00+00:00'}
        self.assertEqual(match_completed_event(event, rows)['status'], 'EXACT_VERIFIED_MATCH')

    def test_ten_minute_source_difference_is_not_coerced_into_exact_join(self):
        rows = parse_source(source('02.11 18:10 02.11.2026 18:10 Zagłębie L. 1:0 Korona 3 396'))
        event = {'id': 445, 'home_team': 'KGHM Zagłębie Lubin', 'away_team': 'Korona Kielce', 'club_slug': 'zaglebie_lubin',
                 'competition': 'Ekstraklasa', 'kickoff_at': '2026-11-02T17:00:00+00:00'}
        self.assertEqual(match_completed_event(event, rows)['status'], 'EXACT_KICKOFF_CONFLICT')

    def test_conflicting_counts_are_not_silently_selected(self):
        a = 'Wisła K. 2:1 Śląsk 33 000 2026/2027 • Ekstraklasa • 18.09.2026 20:30'
        with self.assertRaisesRegex(ValueError, 'Conflicting'): parse_source(source(a+'\n'+a.replace('33 000', '32 999')))

    def test_failed_truncated_other_competition_and_future_are_not_labels(self):
        for change in [{'http_status': 403}, {'text_truncated': True}]:
            s = source(''); s.update(change)
            with self.assertRaises(ValueError): parse_source(s)
        self.assertEqual(parse_source(source('Wisła K. 2:1 Śląsk 33 000 2025/2026 • I liga • 18.09.2025 20:30')), [])
        with self.assertRaisesRegex(ValueError, 'not-completed'):
            parse_source(source('Wisła K. 2:1 Śląsk 33 000 2026/2027 • Ekstraklasa • 18.11.2026 20:30'))


if __name__ == '__main__': unittest.main()
