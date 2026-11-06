from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ml.structural_history_refresh_v1 import predict, summary, BASELINES, PACKAGE, context, stamp
from ml.run_structural_history_refresh_v1 import capture_one, validate_row, score_one, backup, blob, cycle, ensure_runtime
from ml.test_structural_known_at_inputs_v1 import fixture, seal

ASOF='2026-11-04T16:39:00Z'
NOW='2026-11-04T16:40:00Z'
KICKOFF='2026-11-05T16:30:00Z'


def inputs(event=9999):
    source=fixture();parts=source['parts'];parts['ticket_events'][0].update(id=event,kickoff_at=KICKOFF)
    source=seal(parts)
    prior={'source_prior_id':1,'horizon':'T-1','p50':10000.,'stadium_capacity':28007,
        'model_spec_id':'synthetic','model_family':'synthetic','feature_contract':'synthetic',
        'generated_at':'2026-11-04T15:00:00Z','target_as_of_at':'2026-11-04T16:30:00Z',
        'point_in_time_validated':True}
    candidate={'ticket_event_id':event,'club_slug':'gornikzabrze','home_team':'Górnik Zabrze',
        'away_team':'Wieczysta Kraków','kickoff_at':KICKOFF,'prior':prior}
    resolved={**prior,'ticket_event_id':event,'status':'ready','metadata':{'round_no':14,'capacity_verification_status':'verified'}}
    return candidate,resolved,source


def fake_predictor(payload, directory, generated):
    e=payload['events'][0]
    return {'version':'structural-prior-materializer-v1','predictions':[{'ticket_event_id':e['ticket_event_id'],
        'target_as_of_at':e['target_as_of_at'],'p50':11000.,
        'input_lineage':{'feature_row_sha256':'synthetic'},'metadata':{'season_home_n':len(payload['attendance'])}}]}


class StructuralRefreshSourceTests(unittest.TestCase):
    def test_new_knowledge_changes_input_without_moving_model_context_or_kickoff(self):
        c,r,s=inputs();calls=[]
        def run(payload,directory,generated):calls.append(payload);return fake_predictor(payload,directory,generated)
        result=predict(c,r,s,ASOF,NOW,run)
        self.assertEqual(result['p50'],11000.);self.assertEqual(result['eligible_known_records'],1)
        self.assertEqual(calls[0]['events'][0]['kickoff_at'],stamp(KICKOFF).isoformat())
        self.assertEqual(result['model_context_cutoff_at'],stamp(c['prior']['target_as_of_at']).isoformat())
        self.assertFalse(result['official_persistence_allowed']);self.assertNotIn('predictions',result)

    def test_genuine_later_history_is_allowed_only_after_actual_receipt(self):
        c,r,s=inputs();p=s['parts'];p['history'][0].update(source_observed_at='2026-11-04T16:33:00Z',
            created_at='2026-11-04T16:33:00Z',updated_at='2026-11-04T16:33:00Z')
        result=predict(c,r,seal(p),ASOF,NOW,fake_predictor)
        self.assertEqual(result['later_known_home_record_count'],1)

    def test_future_or_stale_source_archive_never_predicts(self):
        c,r,s=inputs()
        for asof,now in [('2026-11-04T16:33:00Z',NOW),('2026-11-04T17:40:00Z','2026-11-04T17:41:00Z')]:
            with self.assertRaises(ValueError):predict(c,r,s,asof,now,fake_predictor)

    def test_tampered_envelope_cannot_change_attendance(self):
        c,r,s=inputs();s['parts']['history'][0]['actual_attendance']=1
        with self.assertRaises(ValueError):predict(c,r,s,ASOF,NOW,fake_predictor)

    def test_known_target_or_same_home_target_date_is_rejected(self):
        c,r,s=inputs();p=s['parts'];p['outcomes']=[{'ticket_event_id':9999}]
        with self.assertRaises((ValueError,KeyError)):predict(c,r,seal(p),ASOF,NOW,fake_predictor)
        p=inputs()[2]['parts'];p['history'][0].update(kickoff_at=KICKOFF)
        with self.assertRaises(ValueError):predict(c,r,seal(p),ASOF,NOW,fake_predictor)

    def test_canonical_competition_kickoff_and_identity_are_preserved(self):
        for field,value in [('competition','cup'),('club_slug','lech'),('kickoff_at','2026-11-05T16:31:00Z')]:
            c,r,s=inputs();p=s['parts'];p['ticket_events'][0][field]=value
            with self.assertRaises(ValueError):predict(c,r,seal(p),ASOF,NOW,fake_predictor)

    def test_prior_identity_or_canonical_horizon_cannot_be_substituted(self):
        for changes in [{'source_prior_id':2},{'horizon':'T-3'},{'metadata':{'round_no':14,'capacity_verification_status':'unknown'}}]:
            c,r,s=inputs();r.update(changes)
            with self.assertRaises(ValueError):predict(c,r,s,ASOF,NOW,fake_predictor)

    def test_postcutoff_fixture_and_previous_season_do_not_enter_context(self):
        for changes in [{'season':'2025/2026','kickoff_at':'2026-05-01T16:00:00Z'},
                        {'kickoff_at':'2026-11-04T16:35:00Z','source_observed_at':'2026-11-04T16:36:00Z','created_at':'2026-11-04T16:36:00Z','updated_at':'2026-11-04T16:36:00Z'}]:
            c,r,s=inputs();p=s['parts'];p['history'][0].update(changes)
            out=predict(c,r,seal(p),ASOF,NOW,fake_predictor);self.assertEqual(out['eligible_known_records'],0)

    def test_conflicting_canonical_source_fails_closed(self):
        c,r,s=inputs();p=s['parts'];p['history'].append({**p['history'][0],'id':2,'actual_attendance':999})
        with self.assertRaisesRegex(ValueError,'Conflicting'):predict(c,r,seal(p),ASOF,NOW,fake_predictor)

    def test_out_of_capacity_or_wrong_predictor_target_cannot_be_emitted(self):
        c,r,s=inputs()
        for changes in [{'p50':40000.},{'ticket_event_id':12}]:
            def invalid(payload,directory,generated):
                result=fake_predictor(payload,directory,generated);result['predictions'][0].update(changes);return result
            with self.assertRaises(ValueError):predict(c,r,s,ASOF,NOW,invalid)


class FreshEvidenceTests(unittest.TestCase):
    def make(self,temp,**changes):
        c,r,s=inputs();old={'ticket_event_id':9999,'source_snapshot_id':1,'as_of_at':ASOF,'issued_at':NOW,
            'input_requested_at':ASOF,'forecasts':{name:10000. for name in BASELINES}}
        manifest={'_manifest_sha256':'a'*64,'frozen_at':'2026-11-04T16:35:00Z','training_fixture_unit_hashes':[]}
        decision={'p50':11000.,'later_known_record_count':1}
        with patch('ml.run_structural_history_refresh_v1.validate_current'),patch('ml.run_structural_history_refresh_v1.verify_upstream'),patch('ml.run_structural_history_refresh_v1.predict',return_value=decision):
            row=capture_one(Path(temp),old,c,r,s,manifest,None,stamp(NOW),clock=lambda:stamp('2026-11-04T16:41:00Z'))
        return row,manifest,decision

    def test_real_own_issue_is_distinct_from_older_benchmark_and_immutable(self):
        with tempfile.TemporaryDirectory() as temp:
            row,m,d=self.make(temp);self.assertGreater(stamp(row['issued_at']),stamp(row['upstream_issued_at']))
            with self.assertRaises(FileExistsError):self.make(temp)

    def test_modified_forecast_or_source_blob_is_detected_in_full_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            row,m,d=self.make(temp);row['forecasts']['fresh']=9999.
            with patch('ml.run_structural_history_refresh_v1.validate_current'),patch('ml.run_structural_history_refresh_v1.verify_upstream'),patch('ml.run_structural_history_refresh_v1.predict',return_value=d):
                with self.assertRaisesRegex(ValueError,'replay differs'):validate_row(Path(temp),row,m,None,stamp(NOW)+__import__('pandas').Timedelta(minutes=2))
            path=Path(temp)/'blobs'/(row['input_blob_sha256']+'.json');path.chmod(0o640);path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'blob changed'):validate_row(Path(temp),row,m,None,stamp('2026-11-04T16:42:00Z'))

    def test_missing_outcome_is_not_zero_error(self):
        with tempfile.TemporaryDirectory() as temp:
            row,m,d=self.make(temp)
            with patch('ml.run_structural_history_refresh_v1.validate_row',return_value={}):
                self.assertIsNone(score_one(Path(temp),row,m,None,[],[],stamp('2026-11-05T19:00:00Z')))

    def test_genuine_outcome_scores_once_and_later_revision_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            row,m,d=self.make(temp);truth={'ticket_event_id':9999,'actual_attendance':12000,'confirmed_at':'2026-11-05T18:30:00Z','created_at':'2026-11-05T18:31:00Z','updated_at':'2026-11-05T18:31:00Z'}
            stored={'benchmark':{},'candidate':{},'resolved':{'stadium_capacity':28007}}
            with patch('ml.run_structural_history_refresh_v1.validate_row',return_value=stored),patch('ml.run_structural_history_refresh_v1.verify_upstream',return_value=([{'actual_attendance':12000}],set(),1)):
                result=score_one(Path(temp),row,m,None,[truth],[],stamp('2026-11-05T19:00:00Z'))
                self.assertEqual(result['absolute_errors']['fresh'],1000.)
                self.assertEqual(score_one(Path(temp),row,m,None,[truth],[],stamp('2026-11-05T19:10:00Z')),result)
                with self.assertRaises(ValueError):score_one(Path(temp),row,m,None,[{**truth,'updated_at':'2026-11-05T18:32:00Z'}],[],stamp('2026-11-05T19:10:00Z'))

    def test_preexisting_or_future_label_cannot_validate_a_new_issue(self):
        with tempfile.TemporaryDirectory() as temp:
            row,m,d=self.make(temp)
            for changes in [{'created_at':'2026-11-04T16:00:00Z'},{'confirmed_at':'2026-11-06T20:00:00Z'}]:
                truth={'ticket_event_id':9999,'actual_attendance':12000,'confirmed_at':'2026-11-05T18:30:00Z','created_at':'2026-11-05T18:31:00Z','updated_at':'2026-11-05T18:31:00Z',**changes}
                with patch('ml.run_structural_history_refresh_v1.validate_row',return_value={}):
                    with self.assertRaises(ValueError):score_one(Path(temp),row,m,None,[truth],[],stamp('2026-11-05T19:00:00Z'))

    def test_private_backup_is_read_back_and_unchanged_state_avoids_uploads(self):
        class Storage:
            calls=0
            def ensure_private_bucket(self):pass
            def put_verified(self,key,raw,mime):self.calls+=1;self.raw=raw;return {'key':key,'read_back_verified':True}
            def read(self,key):return self.raw
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'runtime';root.mkdir();(root/'experiment.json').write_text('{}');artifact=Path(temp)/'artifact';artifact.mkdir();(artifact/'manifest.json').write_text('{}');s=Storage()
            with patch('ml.run_structural_history_refresh_v1.ARTIFACT',artifact):
                a=backup(root,s);b=backup(root,s)
            self.assertEqual(a,b);self.assertEqual(s.calls,1);self.assertTrue(a['independent_remote_decompression_verified'])


class RefreshAccountingTests(unittest.TestCase):
    def row(self,event,asof,fresh,prior,club='one'):
        values={'fresh':fresh,**{k:prior for k in BASELINES}}
        return {'ticket_event_id':event,'fixture_unit':str(event),'club_slug':club,'as_of_at':asof,'kickoff_at':KICKOFF,
            'absolute_errors':values,'signed_errors':values,'later_known_record_count':1}

    def test_empty_report_keeps_mae_null_and_review_closed(self):
        result=summary([],0,[]);self.assertIsNone(result['metrics']['fresh']['latest_per_event_mae']);self.assertFalse(result['review_ready'])

    def test_multiple_prefixes_do_not_inflate_independent_support(self):
        rows=[self.row(1,'2026-11-04T16:37:00Z',10,8),self.row(1,ASOF,20,30),self.row(2,ASOF,100,120,'two')]
        result=summary(rows,2,[]);self.assertEqual(result['scored_events'],2)
        self.assertEqual(result['metrics']['fresh']['latest_per_event_mae'],60)
        self.assertEqual(result['metrics']['fresh']['event_balanced_window_mae'],57.5);self.assertFalse(result['primary_gate_met'])

    def test_aliased_ids_cannot_count_as_two_fixtures(self):
        a=self.row(1,ASOF,1,2);b={**self.row(2,ASOF,1,2),'fixture_unit':'1'}
        with self.assertRaises(ValueError):summary([a,b],1,[])

    def test_fixed_review_needs_thirty_independent_events_and_eight_clubs(self):
        rows=[self.row(i,ASOF,1,2,str(i%8)) for i in range(30)]
        result=summary(rows,30,[]);self.assertTrue(result['review_ready']);self.assertTrue(result['primary_gate_met'])
        self.assertEqual(result['comparisons']['prior']['paired_event_bootstrap_95_interval'],[-1.,-1.])
        self.assertFalse(summary(rows[:29],29,[])['review_ready'])


class CollectorTests(unittest.TestCase):
    def test_no_due_forecast_never_reads_database_or_predicts(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime=Path(temp)/'runtime';support=Path(temp)/'support';archive=Path(temp)/'archive'
            manifest={'_manifest_sha256':'a'*64}
            with patch('ml.run_structural_history_refresh_v1.load_manifest',return_value=manifest), patch('ml.run_structural_history_refresh_v1.benchmark_models'), patch('ml.run_structural_history_refresh_v1.Reader') as reader, patch('ml.run_structural_history_refresh_v1.predict') as inference, patch('ml.run_structural_history_refresh_v1.backup',return_value={}):
                result=cycle(runtime,support,archive)
            self.assertEqual(result['status'],'CYCLE_VERIFIED');self.assertEqual(result['new_predictions'],0)
            reader.assert_not_called();inference.assert_not_called()
            self.assertIsNone(json.loads((runtime/'report.json').read_text())['metrics']['fresh']['latest_per_event_mae'])

    def test_runtime_refuses_nonempty_unmarked_or_different_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime=Path(temp)/'runtime';runtime.mkdir();(runtime/'foreign').write_text('x')
            with self.assertRaises(ValueError):ensure_runtime(runtime,{'_manifest_sha256':'a'*64})
        with tempfile.TemporaryDirectory() as temp:
            runtime=Path(temp)/'runtime';ensure_runtime(runtime,{'_manifest_sha256':'a'*64})
            with self.assertRaises(ValueError):ensure_runtime(runtime,{'_manifest_sha256':'b'*64})


if __name__=='__main__':unittest.main()
