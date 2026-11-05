from copy import deepcopy
import math
import unittest

from ml.features.c1_history_support_v1 import feature_row, FEATURES, HISTORY_FEATURES, prepare_training_features
from ml.export_structural_known_at_inputs_v1 import digest
from ml.test_structural_known_at_inputs_v1 import fixture,seal
import pandas as pd


def input_row():
    return {'ticket_event_id':449,'as_of_at':'2026-11-04T17:00:00Z','prior_p50':10000.,'stadium_capacity':30000.,
            'available_total':0.,'net_removed_24h':-300.,'net_removed_6h':600.,'observation_window_hours':48.}


def target():
    return {'id':449,'club_slug':'gornikzabrze','kickoff_at':'2026-11-05T16:30:00Z'}


class HistorySupportFeatureTests(unittest.TestCase):
    def test_three_new_features_have_known_history_and_fixed_order(self):
        x,m=feature_row(input_row(),target(),fixture())
        self.assertEqual(tuple(x),FEATURES)
        self.assertAlmostEqual(x['verified_home_n_log'],math.log(2))
        self.assertAlmostEqual(x['verified_home_recent_gap'],.5)
        self.assertEqual(m['verified_home_n'],1)
        self.assertEqual(m['sha256'],digest({k:v for k,v in m.items() if k!='sha256'}))

    def test_unknown_history_has_missing_level_not_zero_attendance(self):
        p=fixture()['parts'];p['history']=[]
        x,m=feature_row(input_row(),target(),seal(p))
        self.assertEqual(x['verified_home_n_log'],0)
        self.assertTrue(math.isnan(x['verified_home_recent_gap']))
        self.assertTrue(math.isnan(x['verified_home_age_days']))
        self.assertTrue(m['zero_known_rows_is_not_zero_attendance'])

    def test_late_revision_and_late_confirmation_cannot_enter_old_features(self):
        for column in ['updated_at','source_observed_at','created_at']:
            p=fixture()['parts'];p['history'][0][column]='2026-11-04T18:00:00Z'
            x,m=feature_row(input_row(),target(),seal(p));self.assertEqual(m['verified_home_n'],0)

    def test_actual_zero_inventory_and_unknown_inventory_remain_distinct(self):
        x,_=feature_row(input_row(),target(),fixture());self.assertEqual(x['available_share'],0)
        row=input_row();row['available_total']=None
        x,_=feature_row(row,target(),fixture());self.assertTrue(math.isnan(x['available_share']))

    def test_releases_and_absorption_keep_signed_changes(self):
        x,_=feature_row(input_row(),target(),fixture())
        self.assertEqual(x['removed_24h_share'],-.01);self.assertEqual(x['removed_6h_share'],.02)

    def test_future_or_stale_source_snapshot_cannot_serve_forward_features(self):
        row=input_row()
        for issue in ['2026-11-04T16:34:00Z','2026-11-04T18:00:00Z']:
            row['as_of_at']=issue
            with self.assertRaisesRegex(ValueError,'fresh actual source'):feature_row(row,target(),fixture())

    def test_historical_reconstruction_is_explicit_and_not_original_snapshot_proof(self):
        row=input_row();row['as_of_at']='2026-11-04T16:34:00Z'
        _,m=feature_row(row,target(),fixture(),historical_reconstruction=True)
        self.assertTrue(m['historical_reconstruction']);self.assertFalse(m['original_source_snapshot_used'])

    def test_target_label_is_rejected_before_feature_preparation(self):
        row=input_row();row['actual_attendance']=12345
        with self.assertRaisesRegex(ValueError,'Separate target'):feature_row(row,target(),fixture())
        with self.assertRaisesRegex(ValueError,'Target-free'):prepare_training_features(pd.DataFrame([row]),[target()],fixture())

    def test_canonical_alias_conflict_fails_closed(self):
        p=fixture()['parts'];p['history'][0]['club_slug']='wislakrakow'
        p['history'].append({**deepcopy(p['history'][0]),'id':2,'club_slug':'wisla_krakow','actual_attendance':9999})
        t=target();t['club_slug']='wisla_krakow'
        with self.assertRaisesRegex(ValueError,'Conflicting known'):feature_row(input_row(),t,seal(p))

    def test_previous_season_cannot_be_reclassified_as_current(self):
        p=fixture()['parts'];p['history'][0].update(season='2025/2026',kickoff_at='2026-05-01T16:00:00Z')
        x,m=feature_row(input_row(),target(),seal(p));self.assertEqual(m['verified_home_n'],0)

    def test_actual_issue_horizon_cannot_include_post_match_features(self):
        row=input_row();row['as_of_at']=target()['kickoff_at']
        with self.assertRaisesRegex(ValueError,'final24'):feature_row(row,target(),fixture())


if __name__=='__main__':unittest.main()
