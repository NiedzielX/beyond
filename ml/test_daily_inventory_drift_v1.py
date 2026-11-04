from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from ml.daily_inventory_drift_comparator_v1 import freeze_artifact, predict, validate_artifact
from ml.daily_inventory_drift_ledger_v1 import DriftLedger, REFERENCE_SHA
from ml.demand_engine.daily_inventory_path_dataset_v1 import build_issue, canonical_hash, issue_manifest
from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger
from ml.run_daily_inventory_drift_v1 import DriftStorage, backup, run_cycle


ISSUED=datetime(2027,2,17,18,tzinfo=timezone.utc)


def make_issue(velocity=0, latest=100, gap=False, empty=False):
    event={'ticket_event_id':999,'club_slug':'synthetic','kickoff_at':(ISSUED+timedelta(days=3)).isoformat(),
           'observations':[]}
    for hour in range(36,-1,-1):
        if gap and 24<=hour<=30:continue
        event['observations'].append({'snapshot_id':1000+hour,'captured_at':(ISSUED-timedelta(hours=hour+1)).isoformat(),
            'available_total':latest-velocity*hour/24,'measurement_key':'synthetic/inventory'})
    if empty:event['observations']=[]
    return build_issue(event,ISSUED)


def model():return freeze_artifact('2026-11-04T10:00:00Z')


class MemoryStorage:
    def __init__(self):self.objects={}
    def ensure_private_bucket(self):pass
    def put_verified(self,key,data,mime):
        if key in self.objects and self.objects[key]!=data:raise ValueError('conflict')
        self.objects[key]=data
        return {'key':key,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'read_back_verified':True}


class DriftTests(unittest.TestCase):
    def test_rise_decline_and_flat_use_actual_elapsed_time(self):
        for slope in [-24,0,24]:
            issue=make_issue(slope);status,points=predict(issue,model())
            self.assertEqual(status,'READY');self.assertEqual(len(points),2)
            self.assertEqual(points[0]['velocity_places_per_day'],slope)
            self.assertAlmostEqual(points[0]['predicted_available_total'],100+slope*25/24)
            self.assertEqual(points[0]['baseline_available_total'],100)

    def test_explicit_zero_is_zero_and_decline_is_clipped_only_at_zero(self):
        self.assertEqual(predict(make_issue(latest=0),model())[1][0]['predicted_available_total'],0)
        point=predict(make_issue(-120,latest=10),model())[1][0]
        self.assertEqual(point['predicted_available_total'],0)
        self.assertLess(point['unclipped_available_total'],0)

    def test_anchor_gap_records_failure_without_lookback_fallback(self):
        status,points=predict(make_issue(gap=True),model())
        self.assertEqual(status,'DRIFT_ANCHOR_INSUFFICIENT');self.assertEqual(points,[])

    def test_missing_prefix_is_not_a_usable_zero(self):
        status,points=predict(make_issue(empty=True),model())
        self.assertNotEqual(status,'READY');self.assertEqual(points,[])

    def test_future_observation_and_forged_hash_or_latest_cannot_enter_prediction(self):
        for mutate in ['future','hash','latest']:
            issue=make_issue()
            if mutate=='future':
                issue['observed_prefix'][-1]['captured_at']=(ISSUED+timedelta(hours=1)).isoformat()
                issue['prefix_sha256']=canonical_hash(issue['observed_prefix'])
                issue['input_manifest_sha256']=canonical_hash(issue_manifest(issue))
            elif mutate=='hash':issue['input_manifest_sha256']='bad'
            else:issue['last_available_total']=999
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):predict(issue,model())

    def test_artifact_hash_and_preissue_freeze_are_required(self):
        artifact=model();artifact['lookback_hours']=12
        with self.assertRaises(ValueError):validate_artifact(artifact)
        artifact=model();artifact['frozen_at']=(ISSUED+timedelta(seconds=1)).isoformat()
        artifact['model_sha256']=canonical_hash({k:v for k,v in artifact.items() if k!='model_sha256'})
        with self.assertRaisesRegex(ValueError,'precedes'):predict(make_issue(),artifact)

    def test_existing_v1_ledger_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'original.sqlite'
            with DailyInventoryPathLedger(path):pass
            before=path.read_bytes()
            with self.assertRaisesRegex(ValueError,'non-drift'):DriftLedger(path)
            artifact_path=Path(folder)/'artifact.json';artifact_path.write_text(json.dumps(model()))
            with self.assertRaisesRegex(ValueError,'separate ledger identity'):backup(path,artifact_path,MemoryStorage())
            self.assertEqual(path.read_bytes(),before)

    def test_record_retry_conflict_window_and_immutable_sql(self):
        artifact=model();issue=make_issue(24);_,points=predict(issue,artifact)
        with tempfile.TemporaryDirectory() as folder,DriftLedger(Path(folder)/'drift.sqlite') as ledger:
            first=ledger.record(issue,points,artifact,ISSUED)
            self.assertTrue(first['inserted'])
            self.assertFalse(ledger.record(issue,points,artifact,ISSUED+timedelta(minutes=90))['inserted'])
            for execution in [ISSUED-timedelta(seconds=1),ISSUED+timedelta(minutes=90,seconds=1)]:
                with self.assertRaisesRegex(ValueError,'window'):ledger.record(issue,points,artifact,execution)
            bad=deepcopy(points);bad[0]['predicted_available_total']+=1
            with self.assertRaisesRegex(ValueError,'exact frozen'):ledger.record(issue,bad,artifact,ISSUED)
            for table in ['daily_path_attempts','daily_path_points']:
                with self.assertRaises(sqlite3.IntegrityError):ledger._conn.execute('delete from '+table)

    def test_exact_reference_target_is_required_and_errors_are_recomputed(self):
        artifact=model();issue=make_issue(24);_,points=predict(issue,artifact)
        with tempfile.TemporaryDirectory() as folder,DriftLedger(Path(folder)/'drift.sqlite') as ledger:
            ledger.record(issue,points,artifact,ISSUED)
            reference=deepcopy(points[0]);reference['model_version']='daily-inventory-direct-median-v1'
            reference['model_sha256']=REFERENCE_SHA
            target=ISSUED+timedelta(days=1)
            reference['score']={'scored_at':target.isoformat(),'target_snapshot_id':9000,
                'target_captured_at':target.isoformat(),'target_available_total':120,
                'measurement_key':reference['measurement_key'],'candidate_abs_error':99999}
            now=target+timedelta(minutes=1)
            self.assertEqual(ledger.score_from_reference([reference],ISSUED.isoformat())['new_scores'],0)
            bad=deepcopy(reference);bad['measurement_key']='other'
            with self.assertRaisesRegex(ValueError,'lineage'):ledger.score_from_reference([bad],now.isoformat())
            self.assertEqual(ledger.score_from_reference([reference],now.isoformat())['new_scores'],1)
            score=ledger.export_points()[0]['score']
            self.assertEqual(score['target_snapshot_id'],9000)
            self.assertEqual(score['candidate_abs_error'],5)
            self.assertEqual(score['baseline_abs_error'],20)
            self.assertEqual(ledger.score_from_reference([reference],now.isoformat())['already_scored'],1)
            with self.assertRaises(sqlite3.IntegrityError):ledger._conn.execute('delete from daily_path_scores')
            with self.assertRaisesRegex(ValueError,'exact immutable'):ledger.score([],now)

    def test_private_backup_namespace_cannot_pollute_original_latest_manifests(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'drift.sqlite';artifact=root/'artifact.json'
            with DriftLedger(path):pass
            artifact.write_text(json.dumps(model()))
            storage=MemoryStorage();result=backup(path,artifact,storage)
            self.assertTrue(result['private'])
            self.assertTrue(all(key.startswith('drift-v1/') for key in storage.objects))
            with self.assertRaises(ValueError):DriftStorage._key('manifests/'+'a'*64+'.json')

    def test_cycle_does_not_backfill_pre_freeze_or_missed_reference_issues(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);runtime=root/'drift';runtime.mkdir()
            artifact=model();(runtime/'artifact.json').write_text(json.dumps(artifact))
            issue=make_issue();attempt={'attempt_id':1,'issue':issue,'executed_at':ISSUED.isoformat()}
            class Clock:
                @staticmethod
                def now(tz=None):return ISSUED+timedelta(hours=2)
            with patch('ml.run_daily_inventory_drift_v1.read_ledger',return_value=([attempt],[])),patch('ml.run_daily_inventory_drift_v1.datetime',Clock):
                result=run_cycle(root/'source.sqlite',runtime,MemoryStorage())
            self.assertEqual(result['missed_uncaptured'],1);self.assertEqual(result['point_count'],0)
            self.assertIsNone(result['diagnostics']['primary']['challenger_event_balanced_mae'])

    def test_cycle_captures_then_scores_only_later_exact_reference_outcome(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);runtime=root/'drift';runtime.mkdir()
            artifact=model();(runtime/'artifact.json').write_text(json.dumps(artifact))
            issue=make_issue(24);_,points=predict(issue,artifact)
            for point in points:
                point['model_version']='daily-inventory-direct-median-v1'
                point['model_sha256']=REFERENCE_SHA;point['score']=None
            attempt={'attempt_id':1,'issue':issue,'executed_at':ISSUED.isoformat()}
            class Clock:
                instant=ISSUED+timedelta(minutes=10)
                @staticmethod
                def now(tz=None):return Clock.instant
            with patch('ml.run_daily_inventory_drift_v1.read_ledger',return_value=([attempt],points)),patch('ml.run_daily_inventory_drift_v1.datetime',Clock):
                first=run_cycle(root/'source.sqlite',runtime,MemoryStorage())
                self.assertEqual(first['new_points'],2);self.assertEqual(first['attempt_count'],1)
                self.assertEqual(first['diagnostics']['primary']['scored_event_count'],0)
                self.assertFalse(first['production_activation_allowed'])
                target=ISSUED+timedelta(days=1)
                points[0]['score']={'scored_at':target.isoformat(),'target_snapshot_id':9000,
                    'target_captured_at':target.isoformat(),'target_available_total':120,
                    'measurement_key':points[0]['measurement_key']}
                Clock.instant=target+timedelta(minutes=10)
                second=run_cycle(root/'source.sqlite',runtime,MemoryStorage())
            self.assertEqual(second['new_attempts'],0);self.assertEqual(second['scores']['new_scores'],1)
            self.assertEqual(second['diagnostics']['primary']['challenger_event_balanced_mae'],5)
            self.assertEqual(second['diagnostics']['primary']['baseline_event_balanced_mae'],20)
            self.assertEqual(second['status'],'COLLECTING')

    def test_pre_freeze_reference_attempt_is_never_reconstructed(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);runtime=root/'drift';runtime.mkdir()
            artifact=model();(runtime/'artifact.json').write_text(json.dumps(artifact))
            issue=make_issue();issue['issued_as_of_at']='2026-11-03T17:00:00Z'
            attempt={'attempt_id':1,'issue':issue,'executed_at':issue['issued_as_of_at']}
            with patch('ml.run_daily_inventory_drift_v1.read_ledger',return_value=([attempt],[])):
                result=run_cycle(root/'source.sqlite',runtime,MemoryStorage())
            self.assertEqual(result['attempt_count'],0)
            self.assertEqual(result['post_freeze_reference_attempts'],0)


if __name__=='__main__':unittest.main()
