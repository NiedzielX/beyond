from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from ml import c1_support26_v1 as lane
from ml.demand_engine.c1_seat_median_runtime_v1 import C1SeatMedianRuntimeV1
from ml.demand_engine.c1_shadow_runtime_v8 import C1ShadowRuntimeV8
from ml.test_c1_training_expansion_v1 import candidate, NOW, FREEZE, FixedEstimator
from ml.test_daily_inventory_drift_v1 import MemoryStorage


def fixture():
    features = ('prior_p50', 'stadium_capacity')
    models = {
        'median26': C1SeatMedianRuntimeV1(FixedEstimator(800), features, lane.TRAIN_IDS, 80,
            package_version=lane.PACKAGE, live_model_id=lane.MODEL_ID),
        'median20': C1SeatMedianRuntimeV1(FixedEstimator(750), features, lane.BASE_IDS, 74),
        'ridge20': C1ShadowRuntimeV8(FixedEstimator(.7), features, 'synthetic-ridge20', (), 74),
        'original9': C1ShadowRuntimeV8(FixedEstimator(.4), features, lane.EXPECTED_PACKAGE, (), 30)}
    hashes = {name: name+'-synthetic-sha' for name in models}
    manifest = {'frozen_at': FREEZE, '_verified_manifest_sha256': 'synthetic-manifest',
        'precommit_sha256': 'synthetic-precommit', 'benchmark_packages':
            {name: model.package_version for name, model in models.items() if name != 'median26'}}
    payload = {'version': 'c1-shadow-v8-inputs-v1', 'package_version': lane.EXPECTED_PACKAGE,
        'requested_at': NOW, 'candidate_count': 1, 'candidates': [candidate()]}
    return payload, manifest, models, hashes


def read_capture(runtime):
    evidence = [json.loads(p.read_text()) for p in sorted((runtime/'evidence').glob('event-*.json'))]
    inputs = {p.stem.removeprefix('candidate-'): json.loads(p.read_text()) for p in (runtime/'inputs').glob('candidate-*.json')}
    return evidence, inputs


def scored_fixture():
    payload, manifest, models, hashes = fixture()
    with tempfile.TemporaryDirectory() as temp:
        runtime = Path(temp)
        lane.capture(payload, manifest, models, hashes, runtime=runtime, labelled_ids=set(), now=NOW)
        evidence, inputs = read_capture(runtime)
    outcomes = [{'ticket_event_id': 501, 'actual_attendance': 800, 'confirmed_at': '2026-11-05T21:00:00Z',
        'source_name': 'synthetic fixture', 'source_url': 'https://example.invalid/synthetic-fixture'}]
    metadata = [{'id': 501, 'club_slug': 'synthetic', 'kickoff_at': evidence[0]['kickoff_at']}]
    return evidence, outcomes, metadata, manifest, hashes, '2026-11-05T22:00:00Z', models, inputs


def scored(args):
    return lane.score_rows(*args[:6], models=args[6], source_inputs=args[7])


def training_fixture():
    manifest = json.loads((lane.ROOT/'ml/artifacts/c1_seat_median_v1/manifest.json').read_text())
    features = manifest['features']; fixtures = []
    for index, event in enumerate(lane.TRAIN_IDS):
        fixtures.append({'id': event, 'club_slug': 'synthetic'+str(index % 12), 'competition': 'Ekstraklasa',
            'kickoff_at': f'2026-10-{index+1:02d}T20:00:00Z'})
    by_id = {r['id']: r for r in fixtures}; records = []
    for index, event in enumerate(lane.BASE_IDS+lane.NEW_IDS):
        count = (4 if index < 14 else 3) if event in lane.BASE_IDS else 1
        for bucket in range(count):
            records.append({'ticket_event_id': event,
                'as_of_at': (pd.Timestamp(by_id[event]['kickoff_at'])-pd.Timedelta(hours=bucket*6+1)).isoformat(),
                'actual_attendance': 800, **{name: 1. for name in features}, 'stadium_capacity': 1000.})
    frame = pd.DataFrame(records)[['ticket_event_id', 'as_of_at', 'actual_attendance', *features]]
    metadata = {'features': features, 'all_events_training_exposed': True, 'fresh_validation_events': 0,
        'label_knowledge_cutoff': lane.LABEL_CUTOFF, 'base_prefix_byte_identical': True}
    return frame, features, fixtures, metadata


class Support26Tests(unittest.TestCase):
    def test_training_support_and_event_weights_preserve_declared_independent_units(self):
        frame, features, fixtures, metadata = training_fixture()
        self.assertEqual(lane.validate_training_frame(frame, features, fixtures, metadata),
                         {'independent_fixtures': 26, 'training_clubs': 12})
        sums = pd.Series(lane.event_weights(frame)).groupby(frame.ticket_event_id).sum()
        np.testing.assert_allclose(sums, np.repeat(80/26, 26), rtol=0, atol=1e-12)

    def test_training_contract_rejects_schema_target_sampling_time_and_fixture_corruption(self):
        for kind in ['schema', 'target', 'sampling', 'naive', 'future', 'fixture', 'exposure']:
            data = list(training_fixture()); frame = data[0]
            if kind == 'schema': frame['unapproved_feature'] = 1.
            elif kind == 'target': frame.loc[0, 'actual_attendance'] = 2000.
            elif kind == 'sampling': data[0] = frame.iloc[:-1].copy()
            elif kind == 'naive': frame.loc[0, 'as_of_at'] = '2026-10-01T19:00:00'
            elif kind == 'future': frame.loc[0, 'as_of_at'] = '2027-01-01T19:00:00Z'
            elif kind == 'fixture': data[2][-1].update(club_slug=data[2][0]['club_slug'], kickoff_at=data[2][0]['kickoff_at'])
            else: data[3]['fresh_validation_events'] = 26
            with self.subTest(kind=kind), self.assertRaises(ValueError): lane.validate_training_frame(*data)

    def test_accidental_refit_and_changed_private_csv_stop_before_fitting(self):
        with tempfile.TemporaryDirectory() as temp, patch('sklearn.linear_model.QuantileRegressor.fit') as fit:
            with self.assertRaisesRegex(ValueError, 'single fresh canonical'):
                lane.fit_once(Path(temp), Path(temp))
            (Path(temp)/'training.csv').write_text('altered training data')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                lane.read_training(Path(temp), {})
            fit.assert_not_called()

    def test_four_models_and_shared_prior_use_one_input_and_never_fit(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp); result = lane.capture(*data, runtime=runtime, labelled_ids=set(), now=NOW)
            self.assertEqual(result['new_predictions'], 1)
            evidence, sources = read_capture(runtime); row = evidence[0]
            self.assertEqual(set(row['decisions']), set(lane.MODELS))
            self.assertEqual(row['forecasts'], {'median26_raw': 800., 'median26_policy': 800.,
                'median20_raw': 750., 'median20_policy': 750., 'ridge20_raw': 700., 'ridge20_policy': 700.,
                'original9_raw': 400., 'original9_policy': 300., 'prior': 300.})
            self.assertIn(row['candidate_input_sha256'], sources)

    def test_all_six_new_training_events_are_excluded_even_without_known_outcome_query(self):
        for event in lane.NEW_IDS:
            data = fixture(); data[0]['candidates'][0]['ticket_event_id'] = event
            with tempfile.TemporaryDirectory() as temp:
                result = lane.capture(*data, runtime=Path(temp), labelled_ids=set(), now=NOW)
                self.assertEqual(result['new_predictions'], 0)
                self.assertIn('All26training', result['events'][0]['reason'])

    def test_old_lane_runtime_and_different_manifest_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp); (runtime/'old-ledger.sqlite').touch()
            with self.assertRaisesRegex(ValueError, 'old-lane'): lane.ensure_runtime(runtime, fixture()[1])
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp); m = fixture()[1]; lane.ensure_runtime(runtime, m)
            m['_verified_manifest_sha256'] = 'other'
            with self.assertRaisesRegex(ValueError, 'Another model'): lane.ensure_runtime(runtime, m)

    def test_retry_preserves_original_issue_and_changed_model_output_cannot_overwrite(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp); lane.capture(*data, runtime=runtime, labelled_ids=set(), now=NOW)
            path = next((runtime/'evidence').glob('event-*.json')); original = path.read_bytes()
            repeat = lane.capture(*data, runtime=runtime, labelled_ids=set(), now='2026-11-05T14:01:00Z')
            self.assertEqual(repeat['new_predictions'], 0); self.assertEqual(path.read_bytes(), original)
            data[2]['median26'].estimator.value = 801
            failed = lane.capture(*data, runtime=runtime, labelled_ids=set(), now=NOW)
            self.assertEqual(failed['events'][0]['status'], 'FAILED_CLOSED'); self.assertEqual(path.read_bytes(), original)

    def test_current_clock_is_recorded_after_inference_and_expired_capture_stops(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp)
            lane.capture(*data, runtime=runtime, labelled_ids=set(), now=NOW, clock=lambda: '2026-11-05T14:01:00Z')
            self.assertEqual(pd.Timestamp(read_capture(runtime)[0][0]['issued_at']), pd.Timestamp('2026-11-05T14:01:00Z'))
        with tempfile.TemporaryDirectory() as temp:
            result = lane.capture(*data, runtime=Path(temp), labelled_ids=set(), now=NOW, clock=lambda: '2026-11-05T18:00:00Z')
            self.assertEqual(result['new_predictions'], 0)

    def test_known_labels_targets_staleness_bad_snapshots_and_naive_times_fail_closed(self):
        for kind in ['known', 'target', 'stale', 'prefreeze', 'snapshot', 'naive']:
            data = fixture(); labels = set(); now = NOW
            if kind == 'known': labels = {501}
            elif kind == 'target': data[0]['candidates'][0]['context'] = [{'actual_attendance': 800}]
            elif kind == 'stale': now = data[0]['requested_at'] = '2026-11-05T16:00:00Z'
            elif kind == 'prefreeze': data[1]['frozen_at'] = '2026-11-05T13:45:00Z'
            elif kind == 'snapshot': data[0]['candidates'][0]['representatives'][0]['requested_snapshot_id'] = True
            else: data[0]['candidates'][0]['prior']['generated_at'] = '2026-11-04T18:01:00'
            with tempfile.TemporaryDirectory() as temp:
                result = lane.capture(*data, runtime=Path(temp), labelled_ids=labels, now=now)
                self.assertEqual(result['new_predictions'], 0); self.assertEqual(result['candidate_count'], 1)

    def test_scoring_replays_original_inputs_and_scores_only_later_actual_attendance(self):
        rows, missing, count = scored(scored_fixture())
        self.assertEqual((count, missing), (1, [])); self.assertEqual(rows[0]['absolute_errors']['median26_raw'], 0)
        result = lane.summary(rows, missing, count)
        self.assertIsNone(result['support_comparison']['paired_event_bootstrap_95_interval'])
        self.assertFalse(result['support_gate_met']); self.assertFalse(result['first_review_ready'])

    def test_changed_decision_even_with_matching_forecast_cannot_bypass_frozen_replay(self):
        args = list(scored_fixture()); row = args[0][0]
        row['forecasts']['median26_raw'] = row['decisions']['median26']['v2_live_p50'] = 799.
        with self.assertRaisesRegex(ValueError, 'do not reproduce'): scored(args)

    def test_missing_or_mutated_original_inputs_and_duplicate_evidence_are_rejected(self):
        for kind in ['missing', 'changed', 'duplicate', 'package', 'manifest']:
            args = list(scored_fixture())
            if kind == 'missing': args[7].clear()
            elif kind == 'changed': next(iter(args[7].values()))['prior']['p50'] = 301.
            elif kind == 'duplicate': args[0].append(deepcopy(args[0][0]))
            elif kind == 'package': args[0][0]['package_version'] = 'other'
            else: args[0][0]['manifest_sha256'] = 'other'
            with self.subTest(kind=kind), self.assertRaises(ValueError): scored(args)

    def test_known_future_invalid_labels_and_changed_canonical_identity_stop_scoring(self):
        for kind in ['known', 'future', 'boolean', 'capacity', 'provenance', 'kickoff']:
            args = list(scored_fixture())
            if kind == 'known': args[1][0]['confirmed_at'] = '2026-11-05T13:59:00Z'
            elif kind == 'future': args[1][0]['confirmed_at'] = '2026-11-06T21:00:00Z'
            elif kind == 'boolean': args[1][0]['actual_attendance'] = True
            elif kind == 'capacity': args[1][0]['actual_attendance'] = 1001
            elif kind == 'provenance': args[1][0]['source_url'] = ''
            else: args[2][0]['kickoff_at'] = '2026-11-05T18:01:00Z'
            with self.subTest(kind=kind), self.assertRaises(ValueError): scored(args)

    def test_missing_outcome_retains_capture_and_null_accuracy(self):
        args = list(scored_fixture()); args[1].clear()
        rows, missing, count = scored(args); result = lane.summary(rows, missing, count)
        self.assertEqual((count, missing), (1, [501])); self.assertIsNone(result['metrics']['median26_raw']['latest_row_mae'])

    def test_event_balance_uses_latest_source_and_within_event_window_mean(self):
        rows = scored(scored_fixture())[0]; original = deepcopy(rows[0])
        earlier = deepcopy(original); earlier['as_of_at'] = '2026-11-05T12:30:00Z'
        earlier['absolute_errors']['median26_raw'] = 100.
        result = lane.summary([earlier, original], [], 1)
        self.assertEqual(result['scored_independent_events'], 1)
        self.assertEqual(result['metrics']['median26_raw']['latest_row_mae'], 0.)
        self.assertEqual(result['metrics']['median26_raw']['event_balanced_window_mae'], 50.)

    def test_raw_and_all_four_product_gates_wait_for_event_club_support_and_remain_separate(self):
        template = scored(scored_fixture())[0][0]; rows = []
        for index in range(30):
            row = deepcopy(template); row['ticket_event_id'] = 1000+index; row['club_slug'] = 'club'+str(index % 8); rows.append(row)
        result = lane.summary(rows, [], 30)
        self.assertTrue(result['first_review_ready']); self.assertTrue(result['support_gate_met']); self.assertTrue(result['product_gate_met'])
        for row in rows: row['absolute_errors']['median26_policy'] = 600.
        result = lane.summary(rows, [], 30)
        self.assertTrue(result['support_gate_met']); self.assertFalse(result['product_gate_met'])
        for index, row in enumerate(rows): row['club_slug'] = 'club'+str(index % 7)
        result = lane.summary(rows, [], 30)
        self.assertFalse(result['first_review_ready']); self.assertIsNone(result['support_comparison']['paired_event_bootstrap_95_interval'])

    def test_private_recovery_roundtrip_and_namespace_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); artifact = root/'artifact'; artifact.mkdir(); runtime = root/'runtime'
            lane.write_json(artifact/'manifest.json', {'package_version': lane.PACKAGE}, True)
            m = {'_verified_manifest_sha256': lane.sha256_file(artifact/'manifest.json')}
            lane.ensure_runtime(runtime, m); lane.write_json(runtime/'attempt-synthetic.json', {'candidate_count': 0})
            storage = MemoryStorage(); result = lane.backup(runtime, artifact, storage)
            self.assertTrue(result['read_back_verified']); self.assertTrue(result['decompression_and_file_hashes_verified'])
            raw = next(iter(storage.objects.values())); restored = root/'restored'
            lane.restore_bundle(raw, restored)
            self.assertEqual((restored/'runtime/experiment.json').read_bytes(), (runtime/'experiment.json').read_bytes())
            with self.assertRaises(ValueError): lane.restore_bundle(raw, restored)
            with self.assertRaises(ValueError): lane.SupportStorage._key('drift-v1/'+'0'*64+'.json')
            (runtime/'experiment.json').chmod(0o600)  # Deliberately corrupt only this synthetic test fixture.
            lane.write_json(runtime/'experiment.json', {'package_version': 'another'})
            with self.assertRaisesRegex(ValueError, 'matching support26'): lane.encode_bundle(runtime, artifact)

    def test_corrupt_recovery_or_unsafe_path_never_creates_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); destination = root/'restored'
            import base64, zlib
            bundle = {'version': 'c1-support26-private-evidence-v1', 'package_version': lane.PACKAGE,
                      'files': [{'name': '../escape', 'base64': base64.b64encode(b'bad').decode(), 'sha256': lane.digest(b'bad')}]}
            payload = lane.encode(bundle)
            raw = lane.encode({'version': 'c1-support26-compressed-backup-v1', 'encoding': 'zlib+base64',
                'payload_sha256': lane.digest(payload), 'payload': base64.b64encode(zlib.compress(payload)).decode()})
            with self.assertRaisesRegex(ValueError, 'Unsafe'): lane.restore_bundle(raw, destination)
            self.assertFalse(destination.exists())
            envelope = json.loads(raw); envelope['payload_sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'checksum'): lane.restore_bundle(lane.encode(envelope), destination)
            self.assertFalse(destination.exists())

    def test_corrupt_manifest_is_rejected_before_deserializing_an_estimator(self):
        with tempfile.TemporaryDirectory() as temp, patch('joblib.load') as load:
            folder = Path(temp); lane.write_json(folder/'manifest.json', {'package_version': lane.PACKAGE})
            lane.write_json(folder/'freeze_receipt.json', {'package_version': lane.PACKAGE, 'manifest_sha256': '0'*64})
            with self.assertRaisesRegex(ValueError, 'identity/data/source'):
                lane.load_models(folder)
            load.assert_not_called()

    def test_current_cycle_no_due_and_failed_anchor_preserve_coverage_and_recovery(self):
        for fail_anchor in [False, True]:
            data = fixture(); m, models, hashes = data[1:]
            class Source:
                def request(self, path, payload=None):
                    if path == 'rpc/get_c1_shadow_v8_inputs_v1':
                        return {'version': 'c1-shadow-v8-inputs-v1', 'package_version': lane.EXPECTED_PACKAGE,
                            'requested_at': payload['p_requested_at'], 'candidate_count': int(fail_anchor),
                            'candidates': [candidate()] if fail_anchor else []}
                    if path == 'rpc/get_structural_prior_v1': raise ValueError('Synthetic unresolved anchor')
                    if path.startswith('ticket_event_outcomes?') or path.startswith('ticket_events?'): return []
                    raise AssertionError('No write or unexpected source operation permitted')
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp); artifact = root/'artifact'; artifact.mkdir(); runtime = root/'runtime'
                lane.write_json(artifact/'manifest.json', {'package_version': lane.PACKAGE})
                m['_verified_manifest_sha256'] = lane.sha256_file(artifact/'manifest.json')
                with patch.object(lane, 'load_models', return_value=(m, models, hashes)):
                    result = lane.run_cycle(runtime, artifact, Source(), MemoryStorage())
                self.assertEqual(result['status'], 'CYCLE_VERIFIED'); self.assertEqual(result['capture']['new_predictions'], 0)
                self.assertEqual(result['capture']['candidate_count'], int(fail_anchor))
                self.assertIsNone(result['median26_policy_mae']); self.assertTrue(result['private_backup']['read_back_verified'])
                report = json.loads((runtime/'latest-scorecard.json').read_text())
                self.assertEqual(report['coverage']['failed_candidate_attempts'], int(fail_anchor))

    def test_input_cohort_mismatch_is_rejected_before_any_forecast_is_written(self):
        data = fixture(); data[0]['candidate_count'] = 2
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'coverage accounting'):
                lane.capture(*data, runtime=Path(temp), labelled_ids=set(), now=NOW)
            self.assertFalse((Path(temp)/'evidence').exists())

    def test_full_cycle_persists_inputs_before_prediction_then_scores_a_later_outcome(self):
        payload, m, models, hashes = fixture(); when = [NOW]
        source = candidate(); source['prior'].update(model_spec_id='synthetic-prior', feature_contract='synthetic-structural')
        class Clock:
            @staticmethod
            def now(tz=None): return pd.Timestamp(when[0]).to_pydatetime()
        class Source:
            def request(self, path, args=None):
                if path == 'rpc/get_c1_shadow_v8_inputs_v1':
                    return {'version': 'c1-shadow-v8-inputs-v1', 'package_version': lane.EXPECTED_PACKAGE,
                        'requested_at': args['p_requested_at'], 'candidate_count': int(when[0] == NOW),
                        'candidates': [deepcopy(source)] if when[0] == NOW else []}
                if path == 'rpc/get_structural_prior_v1': return [{**source['prior'], 'status': 'ready'}]
                if path.startswith('ticket_event_outcomes?'):
                    return [] if when[0] == NOW else scored_fixture()[1]
                if path.startswith('ticket_events?'):
                    return [{'id': 501, 'club_slug': 'synthetic', 'kickoff_at': source['kickoff_at']}]
                raise AssertionError('Unexpected source/write request')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); artifact = root/'artifact'; artifact.mkdir(); runtime = root/'runtime'
            lane.write_json(artifact/'manifest.json', {'package_version': lane.PACKAGE})
            m['_verified_manifest_sha256'] = lane.sha256_file(artifact/'manifest.json')
            with patch.object(lane, 'load_models', return_value=(m, models, hashes)), patch.object(lane, 'datetime', Clock):
                first = lane.run_cycle(runtime, artifact, Source(), MemoryStorage())
                self.assertEqual(first['capture']['new_predictions'], 1); self.assertEqual(first['scored_events'], 0)
                evidence_file = next((runtime/'evidence').glob('event-*.json')); original = evidence_file.read_bytes()
                when[0] = '2026-11-05T22:00:00Z'
                later = lane.run_cycle(runtime, artifact, Source(), MemoryStorage())
                self.assertEqual(later['capture']['new_predictions'], 0); self.assertEqual(later['scored_events'], 1)
                self.assertEqual(later['median26_policy_mae'], 0.)  # Synthetic correctness, never a real accuracy claim.
                self.assertEqual(evidence_file.read_bytes(), original)
                self.assertTrue(later['private_backup']['decompression_and_file_hashes_verified'])

    def test_alias_ticket_ids_for_one_canonical_match_cannot_inflate_review_support(self):
        payload, m, models, hashes = fixture()
        other = candidate(); other['ticket_event_id'] = other['representatives'][0]['ticket_event_id'] = 502
        other['representatives'][0]['requested_snapshot_id'] = other['representatives'][0]['features']['snapshot_id'] = 50201
        payload['candidates'].append(other); payload['candidate_count'] = 2
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp); lane.capture(payload, m, models, hashes, runtime=runtime, labelled_ids=set(), now=NOW)
            evidence, inputs = read_capture(runtime)
        label = scored_fixture()[1][0]
        outcomes = [{**label, 'ticket_event_id': event} for event in [501, 502]]
        metadata = [{'id': event, 'club_slug': club, 'kickoff_at': evidence[0]['kickoff_at']}
                    for event, club in [(501, 'korona'), (502, 'koronakielce')]]
        with self.assertRaisesRegex(ValueError, 'one independent fixture'):
            lane.score_rows(evidence, outcomes, metadata, m, hashes, '2026-11-05T22:00:00Z', models=models, source_inputs=inputs)


if __name__ == '__main__':
    unittest.main()
