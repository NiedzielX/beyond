from copy import deepcopy
import unittest
import numpy as np
import pandas as pd

from ml.prepare_c1_training_data26_v1 import BASE_IDS,NEW_IDS,append_frame,sha,validate_row,fixture_units


class Runtime:
    features=('prior_p50','prior_expected_occupancy','stadium_capacity','signal_ready','feature_quality_good')
    def predict_live_p50(self,frame):
        if 'actual_attendance' in frame:raise AssertionError('Target entered features')
        return np.array([600.0])


def row_inputs():
    event={'ticket_event_id':6,'latest_as_of_at':'2026-10-31T15:00:00Z','kickoff_at':'2026-10-31T16:30:00Z',
           'actual_attendance':700,'structural_prior_p50':500.0,'v2_live_p50':600.0}
    truth={'actual_attendance':700,'confirmed_at':'2026-11-04T18:00:00Z'}
    prior={'status':'ready','horizon':'T-1','point_in_time_validated':True,'generated_at':'2026-10-30T17:00:00Z',
           'ticket_event_id':6,'p50':500.0,'stadium_capacity':1000}
    feature={'as_of_at':event['latest_as_of_at'],'point_in_time_validated':True,'snapshot_id':12,
             'signal_readiness':'ready','feature_quality':'raw_only'}
    snapshot={'id':12,'ticket_event_id':6,'captured_at':event['latest_as_of_at']}
    return event,truth,prior,feature,snapshot


class TrainingDataTests(unittest.TestCase):
    def test_original_csv_bytes_and_values_survive_append_exactly(self):
        features=['prior_p50','stadium_capacity'];records=[]
        for i,event in enumerate(BASE_IDS):
            for bucket in range(4 if i<14 else 3):
                records.append({'ticket_event_id':event,'as_of_at':f'2026-10-01T0{bucket}:00:00Z',
                                'actual_attendance':700,'prior_p50':500.0,'stadium_capacity':1000})
        base=pd.DataFrame(records).to_csv(index=False).encode()
        added=[{**records[0],'ticket_event_id':event} for event in NEW_IDS]
        combined=append_frame(base,added,features,expected_base_sha=sha(base))
        self.assertTrue(combined.startswith(base));self.assertEqual(combined.count(b'\n'),81)
        with self.assertRaisesRegex(ValueError,'CSV bytes changed'):append_frame(base+b'\n',added,features,expected_base_sha=sha(base))
        with self.assertRaisesRegex(ValueError,'six disjoint'):append_frame(base,added[:-1],features,expected_base_sha=sha(base))
        repeated=deepcopy(added);repeated[-1]['ticket_event_id']=repeated[0]['ticket_event_id']
        with self.assertRaisesRegex(ValueError,'six disjoint'):append_frame(base,repeated,features,expected_base_sha=sha(base))
        extra=deepcopy(added);extra[0]['new_unapproved_feature']=1
        with self.assertRaisesRegex(ValueError,'feature schema'):append_frame(base,extra,features,expected_base_sha=sha(base))

    def test_actual_frozen_serving_output_is_verified_without_a_new_accuracy_score(self):
        args=row_inputs();before=deepcopy(args)
        record,error=validate_row(*args,'2026-11-04T19:00:00Z',Runtime())
        self.assertEqual(error,0.0);self.assertEqual(record['actual_attendance'],700)
        self.assertEqual(args,before)

    def test_future_or_different_prior_and_unreproducible_serving_output_are_rejected(self):
        for field,value in [('generated_at','2026-10-31T15:01:00Z'),('p50',501.0)]:
            args=list(row_inputs());args[2][field]=value
            with self.assertRaisesRegex(ValueError,'prior identity'):validate_row(*args,'2026-11-04T19:00:00Z',Runtime())
        args=list(row_inputs());args[0]['v2_live_p50']=601.0
        with self.assertRaisesRegex(ValueError,'does not reproduce'):validate_row(*args,'2026-11-04T19:00:00Z',Runtime())

    def test_unknown_label_time_wrong_snapshot_and_target_in_features_fail_closed(self):
        args=list(row_inputs());args[1]['confirmed_at']='2026-11-04T20:00:00Z'
        with self.assertRaisesRegex(ValueError,'label knowledge'):validate_row(*args,'2026-11-04T19:00:00Z',Runtime())
        args=list(row_inputs());args[4]['id']=99
        with self.assertRaisesRegex(ValueError,'snapshot'):validate_row(*args,'2026-11-04T19:00:00Z',Runtime())
        args=list(row_inputs());args[3]['actual_attendance']=700
        with self.assertRaisesRegex(ValueError,'outside feature'):validate_row(*args,'2026-11-04T19:00:00Z',Runtime())

    def test_naive_source_time_cannot_enter_training(self):
        args=list(row_inputs());args[4]['captured_at']='2026-10-31T15:00:00'
        with self.assertRaisesRegex(ValueError,'timezone-aware'):validate_row(*args,'2026-11-04T19:00:00Z',Runtime())

    def test_ticket_ids_must_represent_distinct_canonical_home_matchdays(self):
        rows=[{'id':event,'club_slug':'home','competition':'PKO BP Ekstraklasa',
               'kickoff_at':f'2026-10-{i+1:02d}T17:00:00Z'} for i,event in enumerate(BASE_IDS+NEW_IDS)]
        self.assertEqual(fixture_units(rows),{'independent_fixtures':26,'training_clubs':1})
        rows[-1]['kickoff_at']=rows[0]['kickoff_at']
        with self.assertRaisesRegex(ValueError,'same home-club matchday'):fixture_units(rows)


if __name__=='__main__':unittest.main()
