from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from ml.daily_inventory_source_state_features_v2 import build_features


CUTOFF=datetime(2026,11,4,10,tzinfo=timezone.utc)


def row(identifier=1,age=1,active=None,visible=True,value=0,state=None):
    captured=CUTOFF-timedelta(hours=age)
    received=captured+timedelta(minutes=5)
    if state is None:state='HIDDEN_SOURCE' if not visible else 'INACTIVE_STAGE' if active is False else 'VISIBLE_LEGACY_STAGE_UNKNOWN' if active is None else 'VISIBLE_ACTIVE'
    return {'raw_observation_id':identifier,'captured_at':captured.isoformat(),'raw_created_at':received.isoformat(),
            'known_at':received.isoformat(),'source_version':'synthetic-source-v2','source_active':active,
            'source_visible':visible,'raw_available_total':value,
            'available_total':value if visible and active is not False else None,'status':state,
            'public_snapshot_id':None,'promotion_known_at':None}


def payload(rows=None):
    return {'version':'daily-inventory-source-state-as-known-v2','ticket_event_id':603,'as_of_at':CUTOFF.isoformat(),
            'status':'SOURCE_STATE_EXPORT','observations':rows if rows is not None else [row()],
            'production_change':False,'live_adjustment':0,'target_values_used':False}


class SourceStateFeatureTests(unittest.TestCase):
    def test_explicit_zero_is_not_missing_and_unknown_active_is_not_false(self):
        result=build_features(payload())
        self.assertEqual(result['features']['latest_usable_available_total'],0)
        self.assertFalse(result['missing']['latest_usable_available_total'])
        self.assertIsNone(result['features']['last_source_active'])
        self.assertTrue(result['missing']['last_source_active'])
        self.assertEqual(result['features']['active_stage_known_fraction_48h'],0)
        self.assertIsNone(result['features']['active_fraction_given_known_48h'])

    def test_hidden_or_inactive_raw_zero_cannot_become_model_count(self):
        for observation in [row(visible=False),row(active=False)]:
            result=build_features(payload([observation]))
            self.assertTrue(result['missing']['latest_usable_available_total'])
            bad=deepcopy(observation);bad['available_total']=0
            with self.assertRaisesRegex(ValueError,'Hidden'):build_features(payload([bad]))

    def test_future_receipt_or_forged_known_time_rejected(self):
        for name in ['raw_created_at','known_at']:
            observation=row();observation[name]=(CUTOFF+timedelta(seconds=1)).isoformat()
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'receipt'):build_features(payload([observation]))

    def test_duplicate_ids_and_fractional_or_nonfinite_source_counts_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):build_features(payload([row(),row()]))
        for value in [True,-1,float('nan'),float('inf'),.5]:
            observation=row();observation.update(raw_available_total=value,available_total=value)
            with self.subTest(value=value),self.assertRaises(ValueError):build_features(payload([observation]))

    def test_latest_hourly_capture_wins_without_filling_gaps(self):
        older=row(identifier=1,age=1.5,active=False)
        newer=row(identifier=2,age=1.1,active=True,value=10)
        result=build_features(payload([newer,older]))
        self.assertEqual(result['provenance']['observation_count'],2)
        self.assertEqual(result['provenance']['recent_48h_observation_count'],1)
        self.assertEqual(result['features']['active_fraction_given_known_48h'],1)
        self.assertEqual(result['features']['latest_usable_available_total'],10)

    def test_old_state_does_not_enter_48h_summary(self):
        result=build_features(payload([row(age=60,active=False),row(2,age=1,active=True)]))
        self.assertEqual(result['features']['active_fraction_given_known_48h'],1)
        self.assertEqual(result['provenance']['recent_48h_observation_count'],1)

    def test_invalid_latest_metadata_does_not_fall_back_to_old_usable_count(self):
        invalid=row(2,age=1,state='INVALID_SOURCE_METADATA');invalid['available_total']=None
        result=build_features(payload([row(age=3,active=True,value=10),invalid]))
        self.assertIsNone(result['features']['latest_usable_available_total'])
        self.assertIsNone(result['features']['last_source_visible'])
        self.assertEqual(result['features']['active_stage_known_fraction_48h'],.5)

    def test_source_label_and_quantity_must_agree(self):
        for change in [{'status':'VISIBLE_ACTIVE'},{'available_total':1},{'status':'VISIBLE_COUNT_MISSING'}]:
            observation=row();observation.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):build_features(payload([observation]))

    def test_future_promotion_link_rejected(self):
        observation=row();observation.update(public_snapshot_id=100,promotion_known_at=(CUTOFF+timedelta(seconds=1)).isoformat())
        with self.assertRaisesRegex(ValueError,'promotion'):build_features(payload([observation]))

    def test_no_rows_yield_explicit_missing_features_not_fake_zeroes(self):
        data=payload([]);data['status']='UNSUPPORTED_PROVIDER'
        result=build_features(data)
        self.assertTrue(all(result['missing'].values()))
        self.assertFalse(result['model_fit_performed'])

    def test_unavailable_source_with_rows_and_wrong_production_flags_rejected(self):
        data=payload();data['status']='EVENT_NOT_KNOWN_AS_OF'
        with self.assertRaises(ValueError):build_features(data)
        data=payload();data['production_change']=True
        with self.assertRaises(ValueError):build_features(data)

    def test_input_is_not_modified_and_source_hash_is_stable(self):
        data=payload();before=deepcopy(data)
        self.assertEqual(build_features(data)['provenance']['source_response_sha256'],build_features(data)['provenance']['source_response_sha256'])
        self.assertEqual(data,before)


if __name__=='__main__':unittest.main()
