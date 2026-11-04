from copy import deepcopy
import unittest

import pandas as pd

from ml.c1_live_matched_audit_v1 import describe, followup_queue, require_common_times
from ml.export_c1_matched_audit_inputs_v1 import select_representatives


def fixture():
    c1, d2, priors, events, outcomes = [], [], {}, {}, {}
    for event, actual, prior, live, d2error in [(5, 100, 80, 110, 5), (16, 1000, 500, 600, 300)]:
        c1.append({'ticket_event_id':event, 'home_team':str(event), 'away_team':'synthetic',
            'latest_as_of_at':'2026-10-24T17:00:00Z', 'kickoff_at':'2026-10-24T18:00:00Z',
            'actual_attendance':actual, 'structural_prior_p50':prior, 'v2_live_p50':live,
            'policy_prediction':prior, 'latest_prior_error':abs(actual-prior),
            'latest_live_error':abs(actual-live), 'latest_policy_error':abs(actual-prior),
            'selected_expert':'PRIOR', 'reason_code':'synthetic'})
        d2.append({'ticket_event_id':event, 'stadium_capacity':2000,
            'component_diagnostics':{'structural_t1_base_p50':prior,'b2_correction_seats':0},
            'scores':{'frozen_v2':{'latest_error':abs(actual-prior)},
                      'p2_governed_ridge':{'latest_error':d2error,'window_mae':d2error+10}}})
        priors[event]={'status':'ready', 'horizon':'T-1', 'point_in_time_validated':True,
            'p50':prior, 'stadium_capacity':2000, 'generated_at':'2026-10-23T19:00:00Z',
            'target_as_of_at':'2026-10-23T18:00:00Z', 'metadata':{'season_home_n':0}}
        events[event]={'actual_attendance':actual, 'stadium_capacity':2000,
                       'club_slug':str(event), 'season':'2026/2027'}
        outcomes[event]={'actual_attendance':actual,'confirmed_at':'2026-10-24T21:00:00Z',
                         'source_name':'synthetic','source_url':'https://example.invalid/fixture'}
    return c1, d2, priors, events, [], outcomes


def result(data):return describe(*data,cohort=(5,16))


def matched_fixture():
    c1=fixture()[0]
    rows=[]
    for event in [5,16]:
        for hour in [11,17]:
            time=f'2026-10-24T{hour:02d}:00:00Z'
            rows.append({'ticket_event_id':event,'requested_as_of_at':time,'requested_snapshot_id':event*100+hour,
                         'features':{'as_of_at':time,'snapshot_id':event*100+hour,'point_in_time_validated':True}})
    frame=pd.DataFrame([{'ticket_event_id':r['ticket_event_id'],'as_of_at':r['requested_as_of_at']} for r in rows])
    return c1,rows,frame


class MatchedAuditTests(unittest.TestCase):
    def test_event_balanced_metrics_and_oracle_are_descriptive(self):
        report=result(fixture())
        self.assertEqual(report['latest_row_mae']['c1_policy_mae'],260)
        self.assertEqual(report['latest_row_mae']['d2_p2_mae'],152.5)
        self.assertEqual(report['outcome_aware_selector_mae_DIAGNOSTIC_ONLY'],205)
        self.assertFalse(report['parameters_selected']);self.assertFalse(report['production_change'])
        self.assertFalse(report['external_outcome_source_independently_reverified'])

    def test_difficult_event_cannot_disappear_or_be_duplicated(self):
        for mutate in ['missing_c1','missing_d2','duplicate']:
            data=fixture()
            if mutate=='missing_c1':data[0].pop()
            elif mutate=='missing_d2':data[1].pop()
            else:data[0].append(deepcopy(data[0][0]))
            with self.subTest(mutate=mutate),self.assertRaisesRegex(ValueError,'cohort'):result(data)

    def test_conflicting_truth_is_not_silently_relabelled(self):
        data=fixture();data[-1][16]['actual_attendance']=999
        with self.assertRaisesRegex(ValueError,'Outcome sources'):result(data)

    def test_stored_score_or_anchor_drift_fails_closed(self):
        for kind in ['score','resolved','replayed']:
            data=fixture()
            if kind=='score':data[0][0]['latest_policy_error']=0
            elif kind=='resolved':data[2][5]['p50']=81
            else:data[1][0]['component_diagnostics']['structural_t1_base_p50']=81
            with self.subTest(kind=kind),self.assertRaises(ValueError):result(data)

    def test_late_or_wrong_horizon_anchor_is_rejected(self):
        for change in [{'generated_at':'2026-10-24T17:01:00Z'}, {'target_as_of_at':'2026-10-24T17:30:00Z'},
                       {'target_as_of_at':'2026-10-22T18:00:00Z'}]:
            data=fixture();data[2][5].update(change)
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'cutoff'):result(data)

    def test_capacity_anomaly_is_reported_without_dropping_the_event(self):
        data=fixture();data[2][16]['stadium_capacity']=900;data[3][16]['stadium_capacity']=900;data[1][1]['stadium_capacity']=900
        report=result(data)
        self.assertEqual(report['independent_events'],2)
        self.assertEqual(report['top4_actual_exceeds_capacity_count'],1)

    def test_exact_current_source_history_excludes_target_and_future(self):
        data=fixture();data[4].extend([
            {'club_slug':'5','season':'2026/2027','kickoff_at':t} for t in
            ['2026-10-10T17:00:00Z','2026-10-24T18:00:00Z','2026-11-01T18:00:00Z']])
        report=result(data)
        event=next(r for r in report['events'] if r['ticket_event_id']==5)
        self.assertEqual(event['earlier_current_season_rows_in_current_export'],1)
        self.assertEqual(event['season_home_n_at_materialization'],0)

    def test_same_events_at_later_d2_times_are_not_a_fair_comparison(self):
        c1,rows,frame=matched_fixture();frame.loc[0,'as_of_at']='2026-10-24T11:05:00Z'
        with self.assertRaisesRegex(ValueError,'timestamps'):require_common_times(c1,rows,frame)

    def test_latest_timestamp_and_snapshot_identity_are_required(self):
        for kind in ['latest','snapshot','future']:
            c1,rows,frame=matched_fixture()
            if kind=='latest':c1[0]['latest_as_of_at']='2026-10-24T17:05:00Z'
            elif kind=='snapshot':rows[0]['features']['snapshot_id']=999
            else:c1[0]['kickoff_at']='2026-10-24T16:00:00Z'
            with self.subTest(kind=kind),self.assertRaises(ValueError):require_common_times(c1,rows,frame)

    def test_valid_pairing_does_not_modify_source(self):
        c1,rows,frame=matched_fixture();before=deepcopy((c1,rows))
        require_common_times(c1,rows,frame)
        self.assertEqual((c1,rows),before)

    def test_source_representatives_do_not_use_later_snapshots(self):
        snapshots=[{'id':1,'captured_at':'2026-10-24T16:00:00Z'},
                   {'id':2,'captured_at':'2026-10-24T16:00:00Z'},
                   {'id':3,'captured_at':'2026-10-24T17:30:00Z'},
                   {'id':4,'captured_at':'2026-10-23T18:00:00Z'}]
        rows=select_representatives(snapshots,'2026-10-24T18:00:00Z','2026-10-24T17:00:00Z')
        self.assertEqual([row['id'] for _,row in rows],[2])

    def test_followup_queue_contains_missing_truth_without_inventing_values(self):
        events=[{'ticket_event_id':16,'club_slug':'wisla','home_club_key':'wisla','season':'2026/2027'}]
        priors={16:{'target_as_of_at':'2026-10-23T18:00:00Z'}}
        sporting=[{'home_team':'Wisła','away_team':'A','season':'2026-2027','completed':True,'event_date':'2026-08-01'},
                  {'home_team':'Wisła','away_team':'B','season':'2026-2027','completed':True,'event_date':'2026-09-01'}]
        attendance=[{'club_slug':'wisla','season':'2026/2027','kickoff_at':'2026-08-01T16:00:00Z'}]
        readiness=[{'ticket_event_id':443,'club_slug':'other','home_team':'C','away_team':'D',
                    'kickoff_at':'2026-10-30T17:00:00Z','actual_attendance':None}]
        queue=followup_queue(events,priors,attendance,sporting,[{'alias':'Wisła','club_key':'wisla'}],
                              readiness,'2026-11-04T11:00:00Z')
        self.assertEqual(len(queue),2)
        self.assertEqual(queue[0]['match_date'],'2026-09-01')
        self.assertTrue(all(r['actual_attendance'] is None and not r['independently_verified'] for r in queue))


if __name__=='__main__':unittest.main()
