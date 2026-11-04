from copy import deepcopy
import unittest
from ml.attendance_knowledge_time_guard_v1 import source_catalog, available_at, build_guarded_feature_row


def history(**changes):
    row = {'id': 1, 'club_slug': 'example', 'competition_key': 'ekstraklasa', 'season': '2026/2027',
           'kickoff_at': '2026-07-01T18:00:00Z', 'actual_attendance': 10000,
           'source_observed_at': '2026-11-04T13:45:00Z', 'created_at': '2026-11-04T17:18:36Z',
           'source_payload': {'verified_at': '2026-11-04T17:18:36Z'}}
    return {**row, **changes}


class KnowledgeTimeTests(unittest.TestCase):
    def test_old_fixture_is_not_knowable_before_actual_verification_and_insertion(self):
        row = history(); old = deepcopy(row); c = source_catalog([row], [], [])
        self.assertEqual(available_at(c, '2026-11-04T16:30:00Z')['eligible'], [])
        self.assertEqual(available_at(c, '2026-11-04T17:18:36Z')['eligible'][0]['known_at'], '2026-11-04T17:18:36+00:00')
        self.assertEqual(row, old)

    def test_verified_timestamp_cannot_be_ignored_by_earlier_observed_or_created_fields(self):
        row = history(created_at='2026-11-04T14:00:00Z')
        c = source_catalog([row], [], [])
        self.assertEqual(available_at(c, '2026-11-04T17:00:00Z')['eligible'], [])

    def test_missing_invalid_and_naive_knowledge_metadata_is_rejected(self):
        for change in [{'created_at': None}, {'source_observed_at': None}, {'created_at': '2026-11-04T17:00:00'}, {'source_observed_at': 'invalid'}]:
            c = source_catalog([history(**change)], [], [])
            self.assertEqual(len(c['rejected_sources']), 1)
            self.assertEqual(c['records'], [])

    def test_later_outcome_does_not_hide_known_history_at_earlier_cutoff(self):
        event = {'id': 5, 'club_slug': 'example', 'competition': 'Ekstraklasa', 'kickoff_at': '2026-07-01T18:00:00Z'}
        outcome = {'ticket_event_id': 5, 'actual_attendance': 10000, 'confirmed_at': '2026-11-04T19:00:00Z', 'created_at': '2026-11-04T19:00:00Z'}
        c = source_catalog([history()], [outcome], [event])
        self.assertEqual(available_at(c, '2026-11-04T18:00:00Z')['eligible'][0]['source_kind'], 'history')
        self.assertEqual(available_at(c, '2026-11-04T20:00:00Z')['eligible'][0]['source_kind'], 'outcome')

    def test_registered_pko_competition_alias_preserves_genuine_old_outcomes(self):
        event = {'id': 5, 'club_slug': 'example', 'competition': 'PKO BP Ekstraklasa', 'kickoff_at': '2026-07-01T18:00:00Z'}
        outcome = {'ticket_event_id': 5, 'actual_attendance': 10000, 'confirmed_at': '2026-10-01T19:00:00Z', 'created_at': '2026-10-01T19:00:00Z'}
        c = source_catalog([], [outcome], [event])
        self.assertFalse(c['rejected_sources'])
        self.assertEqual(len(available_at(c, '2026-11-04T16:30:00Z')['eligible']), 1)

    def test_conflicting_known_counts_fail_closed_without_priority_override(self):
        c = source_catalog([history(), history(id=2, actual_attendance=9999)], [], [])
        result = available_at(c, '2026-11-04T18:00:00Z')
        self.assertEqual(result['eligible'], []); self.assertEqual(len(result['conflicts']), 1)

    def test_future_fixture_cannot_supply_attendance_and_bad_labels_are_rejected(self):
        for value in [True, 0, -1, float('nan'), 1.5]:
            c = source_catalog([history(actual_attendance=value)], [], [])
            self.assertEqual(c['records'], [])
        row = history(kickoff_at='2026-11-05T18:00:00Z')
        self.assertEqual(source_catalog([row], [], [])['records'], [])

    def test_wrong_season_competition_or_missing_identity_is_rejected(self):
        for change in [{'season': '2025/2026'}, {'season': None}, {'id': None}, {'competition_key': 'cup'}]:
            self.assertEqual(source_catalog([history(**change)], [], [])['records'], [])

    def test_guard_integrates_with_unchanged_frozen_features_before_and_after_knowledge(self):
        import pandas as pd
        from ml.demand_engine.test_current_structural_prior_features import CurrentStructuralPriorFeaturesTest
        from ml.demand_engine.current_structural_prior_features import CurrentStructuralPriorEvent
        fixture = CurrentStructuralPriorFeaturesTest(); fixture.setUp()
        event = CurrentStructuralPriorEvent(999, '2026/2027', 10, pd.Timestamp('2026-10-02T16:30:00Z'), 'home', 'away', 30000)
        unknown = history(club_slug='home', source_observed_at='2026-10-01T17:00:00Z',
            created_at='2026-10-01T17:00:00Z', source_payload={})
        late_catalog = source_catalog([unknown], [], [])
        row, audit = build_guarded_feature_row(catalog=late_catalog, historical_matches=fixture.historical,
            sporting_state=fixture.sporting, event=event, horizon='T-1')
        self.assertEqual(row.iloc[0]['season_home_n'], 0)
        self.assertFalse(audit['model_inference_performed'])
        known = {**unknown, 'source_observed_at': '2026-10-01T16:00:00Z', 'created_at': '2026-10-01T16:00:00Z'}
        row, _ = build_guarded_feature_row(catalog=source_catalog([known], [], []), historical_matches=fixture.historical,
            sporting_state=fixture.sporting, event=event, horizon='T-1')
        self.assertEqual(row.iloc[0]['season_home_n'], 1)
        self.assertEqual(row.iloc[0]['season_home_mean'], 10000)

    def test_known_conflict_stops_feature_build_instead_of_using_partial_data(self):
        import pandas as pd
        from ml.demand_engine.current_structural_prior_features import CurrentStructuralPriorEvent
        event = CurrentStructuralPriorEvent(999, '2026/2027', 10, pd.Timestamp('2026-11-06T16:30:00Z'), 'home', 'away', 30000)
        c = source_catalog([history(), history(id=2, actual_attendance=9999)], [], [])
        with self.assertRaisesRegex(ValueError, 'feature build refused'):
            build_guarded_feature_row(catalog=c, historical_matches=None, sporting_state=None, event=event, horizon='T-1')


if __name__ == '__main__': unittest.main()
