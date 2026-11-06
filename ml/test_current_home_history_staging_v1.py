from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import unittest
from ml.current_home_history_staging_v1 import stage, SOURCES
from ml.public_attendance_source_audit_v1 import extract

VERIFIED = '2026-11-05T17:24:52+00:00'
NOW = '2026-11-06T12:00:00+00:00'


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.sources = []; self.raw = {}; self.sporting = []; self.events = []; self.existing = []
        names = [('Motor', 'Motor Lublin'), ('Korona', 'Korona Kielce'),
                 ('Widzew', 'Widzew Łódź'), ('Piast', 'Piast Gliwice')]
        for i, (short, full) in enumerate(names):
            day = 23 - i; line = f'{short} 1:0 GKS K. 7 100 2026/2027 • Ekstraklasa • {day:02d}.10.2026 18:00'
            raw = ('<p>' + line + '</p>').encode(); self.raw[SOURCES[i]] = raw
            self.sources.append({'url': SOURCES[i], 'sha256': hashlib.sha256(raw).hexdigest(),
                'retrieved_at': '2026-11-05T17:20:00+00:00',
                'receipt_completed_at': '2026-11-05T17:20:01+00:00',
                'http_status': 200, **extract(raw)})
            self.sporting.append({'source_event_id': str(100+i), 'season': '2026-2027',
                'home_team': full, 'away_team': 'GKS Katowice', 'event_date': f'2026-10-{day:02d}',
                'completed': True, 'home_score': 1, 'away_score': 0})

    def call(self, **changes):
        args = {'sources': self.sources, 'raw_sources': self.raw, 'sporting': self.sporting,
                'events': self.events, 'existing': self.existing,
                'run_id': 42073601199, 'verified_at': VERIFIED, 'now': NOW, **changes}
        return stage(**args)

    def replace_source(self, index, line):
        raw = ('<p>' + line + '</p>').encode(); self.raw[SOURCES[index]] = raw
        self.sources[index].update(sha256=hashlib.sha256(raw).hexdigest(), **extract(raw))

    def test_exact_source_provenance_clock_and_current_run_survive_staging(self):
        rows = self.call(); self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]['kickoff_at'], '2026-10-23T16:00:00+00:00')
        self.assertEqual(rows[0]['actual_attendance'], 7100)
        self.assertEqual(rows[0]['source_observed_at'], VERIFIED)
        self.assertEqual(rows[0]['source_payload']['verification_run_id'], 42073601199)
        self.assertFalse(rows[0]['source_payload']['independent_kickoff_clock_verified'])
        self.assertFalse(rows[0]['source_payload']['knowledge_backdated'])

    def test_changed_raw_bytes_are_not_accepted_under_old_digest(self):
        self.raw[SOURCES[0]] += b'changed'
        with self.assertRaises(ValueError): self.call()

    def test_changed_extracted_text_cannot_substitute_an_attendance(self):
        self.sources[0]['text'] = self.sources[0]['text'].replace('7 100', '9 999')
        with self.assertRaises(ValueError): self.call()

    def test_wrong_page_home_and_unknown_opponent_are_rejected(self):
        for line in ['Korona 1:0 GKS K. 7100 2026/2027 • Ekstraklasa • 23.10.2026 18:00',
                     'Motor 1:0 Unknown 7100 2026/2027 • Ekstraklasa • 23.10.2026 18:00']:
            self.replace_source(0, line)
            with self.assertRaises(ValueError): self.call()

    def test_duplicate_independent_sporting_match_is_ambiguous(self):
        self.sporting.append(deepcopy(self.sporting[0]))
        with self.assertRaises(ValueError): self.call()

    def test_incomplete_mismatched_or_boolean_sporting_result_is_rejected(self):
        for changes in [{'completed': False}, {'home_score': 2}, {'home_score': True}]:
            rows = deepcopy(self.sporting); rows[0].update(changes)
            with self.assertRaises(ValueError): self.call(sporting=rows)

    def test_tracked_canonical_clock_conflict_is_not_rounded_into_a_match(self):
        self.events = [{'club_slug': 'motor', 'kickoff_at': '2026-10-23T16:10:00Z'}]
        with self.assertRaisesRegex(ValueError, 'clock conflict'): self.call()

    def test_existing_history_alias_or_clock_conflict_is_not_upserted(self):
        original = self.call()[0]
        for changes in [{'club_slug': 'motor'}, {'kickoff_at': '2026-10-23T16:10:00Z'}]:
            with self.assertRaises(ValueError): self.call(existing=[{**original, **changes}])

    def test_exact_existing_rows_are_skipped_without_updates(self):
        original = self.call()[0]; result = self.call(existing=[original])
        self.assertEqual(len(result), 3); self.assertEqual(original['actual_attendance'], 7100)

    def test_existing_conflicting_truth_is_rejected(self):
        original = self.call()[0]; original['actual_attendance'] = 7000
        with self.assertRaises(ValueError): self.call(existing=[original])

    def test_future_naive_or_prereceipt_verification_cannot_backdate_knowledge(self):
        for value in ['2026-11-07T12:00:00Z', '2026-11-05T17:24:52', '2026-11-05T17:19:59Z']:
            with self.assertRaises(ValueError): self.call(verified_at=value)

    def test_source_pages_must_be_complete_unique_and_original(self):
        for changes in [{'text_truncated': True}, {'http_status': 404}, {'url': 'https://example.invalid/'}]:
            sources = deepcopy(self.sources); sources[0].update(changes)
            with self.assertRaises(ValueError): self.call(sources=sources)
        with self.assertRaises(ValueError): self.call(sources=self.sources[:3])

    def test_boolean_or_missing_actual_run_id_is_rejected(self):
        for value in [True, 0, None]:
            with self.assertRaises(ValueError): self.call(run_id=value)

    def test_future_fixture_cannot_become_reported_attendance(self):
        self.replace_source(0, 'Motor 1:0 GKS K. 7100 2026/2027 • Ekstraklasa • 07.11.2026 18:00')
        with self.assertRaises(ValueError): self.call()

    def test_duplicate_source_home_matchday_fails_closed(self):
        line = self.sources[0]['text']; self.replace_source(0, line + '\n' + line)
        with self.assertRaisesRegex(ValueError, 'Duplicate'): self.call()


if __name__ == '__main__': unittest.main()
