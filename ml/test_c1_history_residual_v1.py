from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from ml import c1_history_residual_v1 as core
from ml import run_c1_history_residual_v1 as lane
from ml.c1_alpha_t1_tournament_v2 import COMPACT_NUMERIC
from ml.demand_engine.c1_shadow_runtime_v8 import C1ShadowRuntimeV8
from ml.export_structural_known_at_inputs_v1 import digest
from ml.features.c1_history_support_v1 import BASE_FEATURES,FEATURES
from ml.test_c1_training_expansion_v1 import candidate
from ml.test_structural_known_at_inputs_v1 import fixture as source_fixture

NOW='2026-11-05T14:00:00Z'

class Constant:
    def __init__(self,value):self.value=value
    def predict(self,frame):return np.full(len(frame),self.value,dtype=float)
    def fit(self,*a,**kw):raise AssertionError('Inference must never fit')


def setup():
    c=candidate();f={'id':501,'club_slug':'gornikzabrze','kickoff_at':c['kickoff_at']}
    m={'frozen_at':'2026-11-05T13:00:00Z','_verified_manifest_sha256':'a'*64,
       'precommit_sha256':'b'*64,'training_fixture_unit_hashes':[]}
    models={'control':core.ResidualRuntime(Constant(0),BASE_FEATURES,'control'),
            'history':core.ResidualRuntime(Constant(100),FEATURES,'history')}
    old={'input_requested_at':NOW,'issued_at':NOW,'ticket_event_id':501,
         'source_snapshot_id':50101,'as_of_at':'2026-11-05T13:30:00Z','kickoff_at':c['kickoff_at'],
         'candidate_input_sha256':'c'*64,'forecasts':{name:300. for name in ['prior','median26_policy','median20_policy','ridge20_policy','original9_policy']}}
    source=source_fixture();source['requested_at']='2026-11-05T13:14:00Z';source['completed_at']='2026-11-05T13:15:00Z'
    source['export_sha256']=digest({k:v for k,v in source.items() if k!='export_sha256'})
    old_runtime=C1ShadowRuntimeV8(Constant(.3),tuple(COMPACT_NUMERIC),'synthetic-only',(),0)
    bundle=({}, {'original9':old_runtime}, {})
    return c,f,m,models,old,source,bundle


def fake_benchmark(*args,**kwargs):
    return ([{'actual_attendance':400}],[],1) if args[1] else ([],[501],1)


class ResidualLaneTests(unittest.TestCase):
    def capture(self,directory,clock=None):
        c,f,m,models,old,source,bundle=setup()
        with patch.object(lane,'verify_benchmark_rows',side_effect=fake_benchmark), patch.object(lane,'select_snapshot',return_value={'source':source}):
            result=lane.capture_one(Path(directory),old,c,f,m,models,bundle,Path(directory)/'archive',NOW,
                                   clock=clock or (lambda:'2026-11-05T14:00:01Z'))
        row=json.loads((Path(directory)/'evidence'/result['path']).read_text())
        return row,(c,f,m,models,old,source,bundle)

    def test_full_capture_later_label_score_and_replay_use_actual_new_issue(self):
        with tempfile.TemporaryDirectory() as d:
            row,parts=self.capture(d);c,f,m,models,old,source,bundle=parts
            self.assertEqual(row['issued_at'],'2026-11-05T14:00:01+00:00')
            self.assertEqual(row['upstream_issued_at'],NOW)
            label={'ticket_event_id':501,'actual_attendance':400,'confirmed_at':'2026-11-05T19:00:00Z',
                   'created_at':'2026-11-05T19:00:00Z','updated_at':'2026-11-05T19:00:00Z',
                   'source_name':'synthetic-only','source_url':'https://example.invalid'}
            with patch.object(lane,'verify_benchmark_rows',side_effect=fake_benchmark):
                scores,missing=lane.score_rows(Path(d),[row],[label],[f],m,models,bundle,'2026-11-05T20:00:00Z')
            self.assertEqual(missing,[]);self.assertEqual(scores[0]['absolute_errors']['history_raw'],0)
            self.assertEqual(scores[0]['absolute_errors']['control_raw'],100)
            self.assertEqual(scores[0]['absolute_errors']['history_policy'],100)
            self.assertTrue(all((Path(d)/'sources'/f'{sha}.json').exists() for sha in row['source_blob_sha256']))

    def test_coherent_edited_new_output_is_rejected_by_model_replay(self):
        with tempfile.TemporaryDirectory() as d:
            row,parts=self.capture(d);c,f,m,models,old,source,bundle=parts
            row['forecasts']['history_raw']=510.;row['decisions']['history']['raw']=510.
            with patch.object(lane,'verify_benchmark_rows',side_effect=fake_benchmark),self.assertRaisesRegex(ValueError,'replay differs'):
                lane.score_rows(Path(d),[row],[],[f],m,models,bundle,NOW.replace('14:00','15:00'))

    def test_modified_raw_archive_is_rejected_before_inference(self):
        with tempfile.TemporaryDirectory() as d:
            row,parts=self.capture(d);sha=row['source_blob_sha256'][0]
            file=Path(d)/'sources'/f'{sha}.json';file.chmod(0o600);file.write_text('{}')
            with self.assertRaisesRegex(ValueError,'checksum'):lane.get_blob(Path(d),'sources',sha)

    def test_label_known_before_new_issue_is_rejected_even_if_confirmed_later(self):
        with tempfile.TemporaryDirectory() as d:
            row,parts=self.capture(d);c,f,m,models,old,source,bundle=parts
            label={'ticket_event_id':501,'confirmed_at':'2026-11-05T19:00:00Z','created_at':'2026-11-05T13:59:00Z',
                   'updated_at':'2026-11-05T19:00:00Z','source_name':'synthetic','source_url':'https://example.invalid'}
            with patch.object(lane,'verify_benchmark_rows',side_effect=fake_benchmark),self.assertRaisesRegex(ValueError,'known before'):
                lane.score_rows(Path(d),[row],[label],[f],m,models,bundle,'2026-11-05T20:00:00Z')

    def test_capture_cannot_borrow_older_issue_time(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaisesRegex(ValueError,'actual computation'):
            self.capture(d,clock=lambda:'2026-11-05T13:59:59Z')

    def test_missing_archive_is_failed_coverage_not_reconstructed_history(self):
        c,f,m,models,old,source,bundle=setup()
        with tempfile.TemporaryDirectory() as d,patch.object(lane,'verify_benchmark_rows',side_effect=fake_benchmark),patch.object(lane,'select_snapshot',return_value={'source':None}):
            with self.assertRaisesRegex(ValueError,'No genuine'):lane.capture_one(Path(d),old,c,f,m,models,bundle,Path(d)/'archive',NOW)
            self.assertFalse((Path(d)/'evidence').exists())

    def test_training_fixture_alias_cannot_be_new_validation(self):
        c,f,m,models,old,source,bundle=setup();m['training_fixture_unit_hashes']=[core.fixture_unit(f)]
        with tempfile.TemporaryDirectory() as d,self.assertRaisesRegex(ValueError,'training aliases'):
            lane.capture_one(Path(d),old,c,f,m,models,bundle,Path(d),NOW)

    def test_source_archive_containing_target_cannot_enter_inference(self):
        c,f,m,models,old,source,bundle=setup();source['parts']['outcomes']=[{'ticket_event_id':501}]
        with self.assertRaisesRegex(ValueError,'Known target'):lane.decisions(c,f,[source],models,bundle[1]['original9'])

    def test_empty_scores_keep_null_mae_and_closed_gates(self):
        report=lane.summarize([],[],0)
        self.assertIsNone(report['metrics']['history_policy']['latest_row_mae'])
        self.assertFalse(report['review_ready']);self.assertFalse(report['product_gate_met'])

    def test_multiple_prefixes_do_not_increase_independent_event_count(self):
        rows=[]
        for event,time,error in [(501,'2026-11-05T12:00:00Z',0),(501,'2026-11-05T13:00:00Z',0),(502,'2026-11-05T13:00:00Z',200)]:
            rows.append({'ticket_event_id':event,'club_slug':str(event),'as_of_at':time,'kickoff_at':'2026-11-05T18:00:00Z',
                'absolute_errors':{k:error for k in lane.PREDICTIONS},'signed_errors':{k:error for k in lane.PREDICTIONS}})
        report=lane.summarize(rows,[],2)
        self.assertEqual(report['scored_events'],2);self.assertEqual(report['metrics']['history_raw']['latest_row_mae'],100)
        self.assertEqual(report['metrics']['history_raw']['event_balanced_window_mae'],100)

    def test_residual_is_added_in_persons_and_clipped_without_capacity_multiplication(self):
        frame=pd.DataFrame([{**{k:0. for k in FEATURES},'prior_p50':300.,'stadium_capacity':1000.}])
        model=core.ResidualRuntime(Constant(100),FEATURES,'history');self.assertEqual(model.predict_live_p50(frame)[0],400)
        model=core.ResidualRuntime(Constant(10000),FEATURES,'history');self.assertEqual(model.predict_live_p50(frame)[0],1000)
        frame['actual_attendance']=400
        with self.assertRaisesRegex(ValueError,'target labels'):model.predict_live_p50(frame)

    def test_refit_existing_or_noncanonical_destination_is_blocked_before_fitting(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaisesRegex(ValueError,'fresh canonical'):
            core.fit_once(Path(d),Path(d)/'source',Path(d)/'publication',Path(d)/'newname')

    @unittest.skipUnless((core.ARTIFACT_DIR/'manifest.json').exists(),'Before artifact publication')
    def test_frozen_pair_loads_in_a_separate_inference_process_without_refit(self):
        import subprocess,sys
        code='from ml.c1_history_residual_v1 import ResidualRuntime, load_models; m, models, _ = load_models(); assert set(models) == {"control", "history"}; print(m["package_version"])'
        result=subprocess.run([sys.executable,'-c',code],cwd=core.ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn(core.PACKAGE,result.stdout)

    def test_blob_keys_and_recovery_namespaces_cannot_cross_experiments(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaisesRegex(ValueError,'blob key'):
            lane.get_blob(Path(d),'sources','../other')
        with self.assertRaisesRegex(ValueError,'namespace'):lane.Storage._key('c1-support26-v1/'+'a'*64+'.json')


if __name__=='__main__':unittest.main()
