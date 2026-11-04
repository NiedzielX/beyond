from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ml.daily_path_prefix_diagnostics_v1 import build_report, prefix_regime, read_ledger
from ml.demand_engine.test_daily_inventory_path_model_v1 import issue, label


AS_OF='2027-02-19T20:00:00+00:00'


def records(event,regime='varying',leads=(1,),prediction=80,actual=100,attempt_id=None,days=5):
    current=issue(event,days=days,last=0 if regime=='zero' else 100)
    if regime in {'zero','constant'}:
        for point in current['observed_prefix']:point['available_total']=current['last_available_total']
    identifier=attempt_id or event
    attempt={'attempt_id':identifier,'issue':current,'executed_at':current['issued_as_of_at']}
    points=[]
    for lead in leads:
        target=label(current,lead,actual)
        points.append({'attempt_id':identifier,'ticket_event_id':event,'issued_as_of_at':current['issued_as_of_at'],
          'target_at':target['target_at'],'lead_days':lead,'predicted_available_total':prediction,
          'baseline_available_total':current['last_available_total'],'measurement_key':current['measurement_key'],
          'model_version':'synthetic-diagnostic-only','score':{key:target[key] for key in
          ['target_snapshot_id','target_captured_at','target_available_total']}})
        points[-1]['score']['scored_at']=(datetime.fromisoformat(target['target_at'])+timedelta(minutes=5)).isoformat()
    return attempt,points


class PrefixDiagnosticsTests(unittest.TestCase):
    def test_zero_group_does_not_erase_error_in_variable_events(self):
        a,p=records(1,'zero',prediction=0,actual=0)
        b,q=records(2,leads=(1,2,3),prediction=80,actual=100)
        result=build_report([a,b],p+q,AS_OF)
        self.assertEqual(result['primary']['challenger_event_balanced_mae'],10)
        self.assertEqual(result['primary']['scored_event_count'],2)
        zero=result['prefix_groups']['ZERO_ONLY_PREFIX'];vary=result['prefix_groups']['VARYING_PREFIX']
        self.assertEqual(zero['challenger_event_balanced_mae'],0)
        self.assertEqual(vary['challenger_event_balanced_mae'],20)
        self.assertEqual(vary['contribution_to_primary_challenger_mae'],10)
        self.assertFalse(result['primary_evaluator_changed'])

    def test_no_outcomes_means_null_error_even_for_zero_prefix(self):
        a,p=records(1,'zero',prediction=0,actual=0);p[0]['score']=None
        result=build_report([a],p,AS_OF)
        self.assertIsNone(result['primary']['challenger_event_balanced_mae'])
        self.assertIsNone(result['prefix_groups']['ZERO_ONLY_PREFIX']['challenger_event_balanced_mae'])
        self.assertEqual(result['prefix_groups']['ZERO_ONLY_PREFIX']['mature_unscored_count'],1)

    def test_same_event_across_regimes_is_still_one_independent_event(self):
        a,p=records(1,'zero',prediction=0,actual=0,attempt_id=1)
        b,q=records(1,'varying',prediction=80,actual=100,attempt_id=2,days=6)
        result=build_report([a,b],p+q,AS_OF)
        self.assertEqual(result['primary']['scored_event_count'],1)
        self.assertEqual(result['primary']['challenger_event_balanced_mae'],10)
        self.assertTrue(result['group_event_counts_may_overlap_across_vintages'])
        self.assertEqual(sum(group['contribution_to_primary_challenger_mae'] or 0 for group in result['prefix_groups'].values()),10)

    def test_future_score_and_unpublished_attempt_are_not_current_evidence(self):
        a,p=records(1)
        p[0]['score']['scored_at']='2027-02-21T20:00:00Z'
        self.assertEqual(build_report([a],p,AS_OF)['primary']['labeled_target_count'],0)
        a['executed_at']='2027-02-21T20:00:00Z'
        self.assertEqual(build_report([a],p,AS_OF)['primary']['prediction_count'],0)

    def test_invalid_or_failed_prefix_is_not_a_fake_zero_group(self):
        self.assertEqual(prefix_regime({'status':'MODEL_INPUT_INSUFFICIENT'}),'INPUT_NOT_READY')
        with self.assertRaises(ValueError):prefix_regime({'status':'READY','observed_prefix':[]})
        a,p=records(1);a['issue']['status']='MODEL_INPUT_INSUFFICIENT'
        with self.assertRaisesRegex(ValueError,'Failed-input'):build_report([a],p,AS_OF)

    def test_constant_positive_prefix_keeps_its_own_group(self):
        a,p=records(1,'constant')
        result=build_report([a],p,AS_OF)
        self.assertEqual(result['prefix_groups']['CONSTANT_POSITIVE_PREFIX']['scored_event_count'],1)

    def test_orphan_or_cross_event_prediction_fails_closed(self):
        a,p=records(1)
        with self.assertRaisesRegex(ValueError,'Orphan'):build_report([],p,AS_OF)
        p[0]['ticket_event_id']=2
        with self.assertRaisesRegex(ValueError,'event mismatch'):build_report([a],p,AS_OF)

    def test_sqlite_read_does_not_create_or_modify_source(self):
        a,p=records(1)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.sqlite'
            with sqlite3.connect(path) as db:
                db.executescript('''create table daily_path_meta(singleton integer,version text);
                  insert into daily_path_meta values(1,'daily-inventory-path-local-ledger-v1');
                  create table daily_path_attempts(id integer,executed_at text,payload_json text);
                  create table daily_path_points(id integer,attempt_id integer,payload_json text);
                  create table daily_path_scores(point_id integer,payload_json text);''')
                db.execute('insert into daily_path_attempts values(?,?,?)',(a['attempt_id'],a['executed_at'],json.dumps({'issue':a['issue']})))
                point=deepcopy(p[0]);score=point.pop('score');point.pop('attempt_id')
                db.execute('insert into daily_path_points values(1,1,?)',(json.dumps(point),))
                db.execute('insert into daily_path_scores values(1,?)',(json.dumps(score),))
            before=hashlib.sha256(path.read_bytes()).hexdigest()
            attempts,points=read_ledger(path)
            self.assertEqual(build_report(attempts,points,AS_OF)['primary']['scored_event_count'],1)
            self.assertEqual(before,hashlib.sha256(path.read_bytes()).hexdigest())
            missing=Path(directory)/'missing.sqlite'
            with self.assertRaises(ValueError):read_ledger(missing)
            self.assertFalse(missing.exists())


if __name__=='__main__':unittest.main()
