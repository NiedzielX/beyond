from copy import deepcopy
from datetime import datetime, timezone
import json
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ml.export_structural_known_at_inputs_v1 import (
    VERSION, TABLES, SourceReader, capture, checked_rows, digest, validate_envelope, write_private,
)
from ml.structural_known_at_shadow_v1 import infer, prepare

ACTIVATION = '2026-11-04T16:00:00Z'
NOW = '2026-11-04T16:35:00Z'


def seal(parts):
    value = {'version': VERSION, 'requested_at': '2026-11-04T16:34:00Z',
        'completed_at': '2026-11-04T16:34:10Z', 'parts': parts,
        'receipts': {n:{'count': len(v), 'sha256': digest(v)} for n,v in parts.items()},
        'read_only': True, 'production_change': False, 'live_adjustment': 0}
    value['export_sha256'] = digest(value)
    return value


def fixture():
    event = {'ticket_event_id': 449, 'home_team': 'Górnik Zabrze', 'away_team': 'Wieczysta Kraków',
        'kickoff_at': '2026-11-07T16:30:00Z', 'target_as_of_at': '2026-11-04T16:30:00Z',
        'horizon': 'T-3', 'input_status': 'ready', 'season': '2026/2027', 'round_no': 14,
        'home_club_key': 'gornikzabrze', 'away_club_key': 'wieczysta_krakow', 'stadium_capacity': 28007,
        'model_spec_id': 'synthetic', 'model_family': 'synthetic', 'feature_contract': 'synthetic',
        'capacity_verification_status': 'verified', 'capacity_source_url':'https://example.invalid/capacity'}
    history = [{'id': 1, 'club_slug': 'gornikzabrze', 'competition_key': 'ekstraklasa',
        'season': '2026/2027', 'kickoff_at': '2026-08-01T16:00:00Z', 'actual_attendance': 25000,
        'source_observed_at': '2026-08-02T12:00:00Z', 'created_at': '2026-08-02T12:00:00Z',
        'updated_at':'2026-08-02T12:00:00Z',
        'source_payload': {}, 'source_name': 'synthetic-fixture', 'source_url': 'https://example.invalid'}]
    targets = [{'id': 449, 'club_slug': 'gornikzabrze', 'home_team': event['home_team'],
        'away_team': event['away_team'], 'kickoff_at': event['kickoff_at'], 'competition': 'Ekstraklasa'}]
    aliases = [{'alias': name, 'club_key': key} for name,key in [
        ('Górnik Zabrze','gornikzabrze'), ('Wieczysta Kraków','wieczysta_krakow'), ('Lech Poznań','lech')]]
    sporting = [{'source_event_id': str(i+1), 'season': '2026-2027', 'event_date': '2026-11-01',
        'home_team': name, 'away_team': 'Lech Poznań', 'home_score': 1, 'away_score': 0,
        'completed': True} for i,name in enumerate(['Górnik Zabrze','Wieczysta Kraków'])]
    return seal({'due':[event], 'history':history, 'outcomes':[], 'ticket_events':targets,
                 'sporting':sporting, 'aliases':aliases})


class ExactExportTests(unittest.TestCase):
    def test_http_count_receipt_detects_truncation_and_preserves_source_metadata(self):
        value=fixture()['parts']['history']; reader=object.__new__(SourceReader)
        reader.base='https://example.invalid';reader.headers={'apikey':'synthetic-only'}
        class Response(io.BytesIO):
            def __init__(self,total):
                super().__init__(json.dumps(value).encode());self.headers={'Content-Range':'0-0/'+str(total)}
        with patch('urllib.request.urlopen',return_value=Response(1)) as call:
            self.assertEqual(reader.counted('history'),value)
            self.assertEqual(call.call_args[0][0].get_header('Prefer'),'count=exact')
        with patch('urllib.request.urlopen',return_value=Response(2)):
            with self.assertRaisesRegex(ValueError,'count mismatch'):reader.counted('history')

    def test_count_receipt_rejects_silent_cap_duplicate_unknown_identity(self):
        for rows,count in [([{'id':1}],2), ([{'id':1},{'id':1}],2), ([{'id':None}],1),([],1001)]:
            with self.assertRaises(ValueError): checked_rows(rows,count,'id')
        self.assertEqual(checked_rows([],0,'id'),[])

    def test_source_and_outer_hashes_both_enforced(self):
        good = fixture(); self.assertEqual(validate_envelope(good),good)
        wrong = deepcopy(good);wrong['parts']['history'][0]['created_at']='2026-07-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'hash mismatch'):validate_envelope(wrong)
        wrong['export_sha256']=digest({k:v for k,v in wrong.items() if k!='export_sha256'})
        with self.assertRaisesRegex(ValueError,'receipt mismatch'):validate_envelope(wrong)

    def test_conflicting_aliases_cannot_silently_choose_the_last_mapping(self):
        parts=fixture()['parts'];parts['aliases'].append({**parts['aliases'][0], 'club_key':'other'})
        with self.assertRaisesRegex(ValueError,'alias identity'):validate_envelope(seal(parts))

    def test_private_write_is_new_and_preserves_raw_knowledge_metadata(self):
        value=fixture()
        with tempfile.TemporaryDirectory() as d:
            path=write_private(Path(d)/'new',value)
            self.assertEqual(json.loads(path.read_text()),value);self.assertEqual(path.stat().st_mode & 0o777,0o600)
            with self.assertRaises(FileExistsError):write_private(Path(d)/'new',value)
        with self.assertRaisesRegex(ValueError,'outside'):write_private(Path(__file__).parent/'forbidden',value)

    def test_real_capture_contract_forwards_explicit_read_only_rpcs_and_counted_tables(self):
        value=fixture(); calls=[]
        class FakeReader:
            def request(self,path,payload):
                calls.append((path,payload));return value['parts']['due' if 'due_' in path else 'aliases']
            def counted(self,name,filters=()):
                calls.append((name,filters));return value['parts'][name]
        times=iter([datetime(2026,11,4,16,34,tzinfo=timezone.utc),datetime(2026,11,4,16,34,10,tzinfo=timezone.utc)])
        result=capture(FakeReader(),lambda:next(times))
        self.assertEqual(result['parts']['history'],value['parts']['history'])
        self.assertIsNone(calls[0][1]['p_include_ready_event_id']);self.assertEqual(len(calls),6)
        self.assertIn(('sporting',[('season','in.(2026-2027)')]),calls)


class PerCutoffInferenceTests(unittest.TestCase):
    def test_later_revision_and_unknown_revision_never_become_old_inputs(self):
        for updated in ['2026-11-04T16:32:00Z',None]:
            parts=fixture()['parts'];parts['history'][0]['updated_at']=updated
            ready,_=prepare(seal(parts),NOW,ACTIVATION)
            self.assertEqual(ready[0]['input']['attendance'],[])

    def test_ready_input_retains_known_rows_drops_late_rows_and_never_mutates_sources(self):
        original=fixture();parts=deepcopy(original['parts']);late={**parts['history'][0], 'id':2,
            'kickoff_at':'2026-09-01T16:00:00Z','created_at':'2026-11-04T16:32:00Z','updated_at':'2026-11-04T16:32:00Z'}
        parts['history'].append(late);data=seal(parts);before=deepcopy(data)
        ready,attempts=prepare(data,NOW,ACTIVATION)
        self.assertEqual(len(ready[0]['input']['attendance']),1);self.assertEqual(attempts[0]['status'],'GUARDED_INPUT_READY')
        self.assertEqual(data,before)

    def test_each_target_uses_its_own_cutoff_not_global_latest(self):
        parts=fixture()['parts'];other={**parts['due'][0], 'ticket_event_id':450,
            'kickoff_at':'2026-11-07T16:33:00Z','target_as_of_at':'2026-11-04T16:33:00Z'}
        parts['due'].append(other);parts['ticket_events'].append({**parts['ticket_events'][0], 'id':450,'kickoff_at':other['kickoff_at']})
        parts['history'][0]['created_at']='2026-11-04T16:32:00Z'
        parts['history'][0]['updated_at']='2026-11-04T16:32:00Z'
        ready,_=prepare(seal(parts),NOW,ACTIVATION)
        self.assertEqual([len(r['input']['attendance']) for r in ready],[0,1])

    def test_known_outcome_in_either_source_prevents_target_forecast(self):
        for source in ['outcomes','history']:
            parts=fixture()['parts']
            if source=='outcomes':parts[source]=[{'ticket_event_id':449,'actual_attendance':25000}]
            else:parts[source].append({**parts['history'][0],'id':2,'kickoff_at':parts['due'][0]['kickoff_at']})
            ready,attempts=prepare(seal(parts),NOW,ACTIVATION)
            self.assertFalse(ready);self.assertEqual(attempts[0]['status'],'TARGET_OUTCOME_ALREADY_KNOWN')

    def test_activation_future_and_closed_windows_are_not_backfilled(self):
        for activation,now,expected in [('2026-11-04T16:31:00Z',NOW,'PRE_ACTIVATION_NO_BACKFILL'),
                (ACTIVATION,'2026-11-04T16:20:00Z','NOT_DUE'),(ACTIVATION,'2026-11-04T18:01:00Z','WINDOW_CLOSED_NO_BACKFILL')]:
            value=fixture();value['requested_at']=now;value['completed_at']=now
            value['export_sha256']=digest({k:v for k,v in value.items() if k!='export_sha256'})
            ready,attempts=prepare(value,now,activation)
            self.assertFalse(ready);self.assertEqual(attempts[0]['status'],expected)

    def test_stale_or_future_export_refused_before_predictor(self):
        for now in ['2026-11-04T16:34:05Z','2026-11-04T16:50:00Z']:
            with self.assertRaisesRegex(ValueError,'Stale/future'):prepare(fixture(),now,ACTIVATION)

    def test_conflict_stops_target_and_cutoff_identity_drift_is_rejected(self):
        parts=fixture()['parts'];parts['history'].append({**parts['history'][0],'id':2,'actual_attendance':1})
        ready,attempts=prepare(seal(parts),NOW,ACTIVATION)
        self.assertFalse(ready);self.assertEqual(attempts[0]['status'],'CONFLICTING_KNOWN_ATTENDANCE')
        parts=fixture()['parts'];parts['due'][0]['target_as_of_at']='2026-11-04T16:31:00Z'
        with self.assertRaisesRegex(ValueError,'cutoff drift'):prepare(seal(parts),NOW,ACTIVATION)

    def test_empty_or_closed_input_does_not_load_a_predictor(self):
        parts=fixture()['parts'];parts['due']=[]
        def forbidden(*args):raise AssertionError('No-due input must not invoke predictor')
        result=infer(seal(parts),Path('/missing'),NOW,ACTIVATION,predictor=forbidden)
        self.assertEqual(result['shadow_forecasts'],[]);self.assertNotIn('predictions',result)
        self.assertFalse(result['official_persistence_allowed']);self.assertFalse(result['prospective_lane_activated'])

    def test_predictor_output_target_identity_is_checked(self):
        def wrong(*args):return {'version':'structural-prior-materializer-v1','predictions':[
            {'ticket_event_id':999,'target_as_of_at':'2026-11-04T16:30:00Z'}]}
        with self.assertRaisesRegex(ValueError,'target/cutoff mismatch'):infer(fixture(),Path('/missing'),NOW,ACTIVATION,predictor=wrong)

    def test_due_target_label_or_canonical_club_mismatch_is_rejected(self):
        parts=fixture()['parts'];parts['due'][0]['actual_attendance']=25000
        with self.assertRaisesRegex(ValueError,'target forbidden'):prepare(seal(parts),NOW,ACTIVATION)
        parts=fixture()['parts'];parts['ticket_events'][0]['home_team']='Wrong club'
        with self.assertRaisesRegex(ValueError,'target identity mismatch'):prepare(seal(parts),NOW,ACTIVATION)

    def test_actual_frozen_predictor_matches_unmodified_already_known_inputs(self):
        from ml.demand_engine.materialize_structural_priors import materialize
        import pandas as pd
        value=fixture();artifact=Path(__file__).parent/'artifacts/structural_prior_runtime_v1'
        manifest=json.loads((artifact/'manifest.json').read_text());contract=manifest['artifacts']['T-3']
        # This is an explicitly synthetic, non-persisted correctness integration.
        event=value['parts']['due'][0]
        # Use the same immutable artifact identity the normal predictor expects.
        event.update({k:contract[k] for k in ['model_spec_id','model_family','feature_contract']})
        value=seal(value['parts']);parts=value['parts']
        original_input={'events':parts['due'],'aliases':parts['aliases'],
                        'attendance':parts['history'],'sportingMatches':parts['sporting']}
        expected=materialize(original_input,artifact,pd.Timestamp(NOW))['predictions'][0]
        with patch('sklearn.ensemble.HistGradientBoostingRegressor.fit',side_effect=AssertionError('Inference must not fit')):
            actual=infer(value,artifact,NOW,ACTIVATION)
        self.assertEqual(actual['shadow_forecasts'][0]['frozen_predictor_output'],expected)
        self.assertNotIn('predictions',actual);self.assertEqual(expected['metadata']['season_home_n'],1)


if __name__=='__main__':unittest.main()
