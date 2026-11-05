from copy import deepcopy
import unittest
from unittest.mock import patch
import pandas as pd
from ml import history_consumption_audit_v1 as audit
from ml.attendance_knowledge_time_guard_v1 import available_at


def source_row(i=1, **changes):
    return {'id':i,'club_slug':'home','kickoff_at':'2026-09-01T18:00:00Z',
        'season':'2026/2027','competition_key':'ekstraklasa','actual_attendance':1000,
        'created_at':'2026-11-04T17:18:36Z','updated_at':'2026-11-04T17:18:36Z',
        'source_observed_at':'2026-11-04T17:18:36Z','source_payload':{
            'verification_run_id':audit.IMPORT_RUN,'verified_at':'2026-11-04T17:18:36Z',
            'source_sha256':'a'*64,'historical_publication_time_verified':False},**changes}


def meta(n=1, level=1000):
    return {'season_home_n':float(n),'home_history_n':float(n+10),'baseline_season':float(level),'baseline_r3':float(level)}


class ConsumptionAuditTests(unittest.TestCase):
    def test_import_presence_is_not_source_consumption_proof(self):
        row=source_row();groups,keys=audit.source_maps([row],[row])
        self.assertEqual(len(keys),1)
        self.assertEqual(audit.evidence_level(meta(1),meta(6),meta(1)), 'HOME_METADATA_MATCHES_WITHOUT_IMPORTS')

    def test_later_import_is_unavailable_at_earlier_cutoff(self):
        row=source_row()
        self.assertEqual(audit.eligible_imports([row],'home','2026-11-04T16:30:00Z'),[])
        self.assertEqual(len(audit.eligible_imports([row],'home','2026-11-04T17:55:00Z')),1)

    def test_revision_and_verification_time_are_both_respected(self):
        row=source_row(updated_at='2026-11-05T12:00:00Z')
        self.assertEqual(audit.eligible_imports([row],'home','2026-11-04T18:00:00Z'),[])
        row['updated_at']='2026-11-04T17:18:36Z';row['source_payload']['verified_at']='2026-11-05T12:00:00Z'
        self.assertEqual(audit.eligible_imports([row],'home','2026-11-04T18:00:00Z'),[])

    def test_unknown_or_naive_timestamp_cannot_be_assumed_known(self):
        for value in [None,'invalid','2026-11-04T17:00:00']:
            with self.assertRaises(ValueError):audit.stamp(value)

    def test_canonical_alias_prevents_duplicate_source_evidence(self):
        a=source_row(club_slug='wislakrakow');b=source_row(2,club_slug='wisla_krakow')
        with self.assertRaisesRegex(ValueError,'duplicate canonical'):audit.source_maps([a,b],[a])

    def test_imported_value_mismatch_stops_audit(self):
        row=source_row();different={**row,'actual_attendance':999}
        with self.assertRaisesRegex(ValueError,'absent/changed'):audit.source_maps([different],[row])

    def test_metadata_matches_are_separated_from_indistinguishable_cases(self):
        self.assertEqual(audit.evidence_level(meta(6),meta(6),meta(1)), 'HOME_METADATA_MATCHES_WITH_IMPORTS')
        self.assertEqual(audit.evidence_level(meta(1),meta(1),meta(1)), 'IMPORTS_NOT_DISTINGUISHABLE_IN_HOME_METADATA')
        self.assertEqual(audit.evidence_level(meta(4),meta(6),meta(1)), 'HOME_METADATA_DIFFERS_CURRENT_RECONSTRUCTION')

    def test_unknown_counts_cannot_prove_a_matching_input(self):
        missing=meta();missing['season_home_n']=None
        self.assertFalse(audit.matching(missing,missing))

    def test_known_conflict_across_registered_aliases_remains_conflict(self):
        rows=[source_row(club_slug='wislakrakow'),source_row(2,club_slug='wisla_krakow',actual_attendance=999)]
        catalog=audit.canonical_catalog({'history':rows,'outcomes':[],'ticket_events':[]})
        result=available_at(catalog,'2026-11-04T18:00:00Z')
        self.assertEqual(len(result['conflicts']),1);self.assertEqual(result['eligible'],[])

    def test_sixteen_import_sources_are_pinned_by_provenance_not_errors(self):
        rows=[source_row(i,club_slug='home'+str(i)) for i in range(1,17)]
        self.assertEqual(len(audit.verified_imports(rows)),16)
        with self.assertRaisesRegex(ValueError,'sixteen'):audit.verified_imports(rows[:15])
        rows[0]['source_payload']['verification_run_id']='different'
        with self.assertRaisesRegex(ValueError,'sixteen'):audit.verified_imports(rows)

    def test_read_only_source_matching_does_not_rewrite_history(self):
        row=source_row();before=deepcopy(row);audit.source_maps([row],[row]);self.assertEqual(row,before)

    def test_feature_reconstruction_calls_no_learner(self):
        from ml.demand_engine.test_current_structural_prior_features import CurrentStructuralPriorFeaturesTest
        from ml.demand_engine.current_structural_prior_features import CurrentStructuralPriorEvent
        fixture=CurrentStructuralPriorFeaturesTest();fixture.setUp()
        event=CurrentStructuralPriorEvent(999,'2026/2027',10,pd.Timestamp('2026-10-02T16:30:00Z'),'home','away',30000)
        with patch.object(audit, 'build_sporting_state', return_value=fixture.sporting):
            result=audit.build_metadata([],fixture.historical,[],{},event,'T-1')
        self.assertEqual(result['season_home_n'],0)
        self.assertGreater(result['home_history_n'],0)


if __name__=='__main__':unittest.main()
