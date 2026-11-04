from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from ml.c1_training_expansion_v1 import PACKAGE, MODEL_ID, fit_once
from ml.c1_training_expansion_capture_v1 import capture, immutable_save, validate_current, load_frozen
from ml.demand_engine.c1_shadow_runtime_v8 import C1ShadowRuntimeV8
from ml.demand_engine.run_c1_shadow_v8 import EXPECTED_PACKAGE


NOW = '2026-11-05T14:00:00Z'
FREEZE = '2026-11-04T13:00:00Z'


class FixedEstimator:
    def __init__(self, value): self.value = value
    def predict(self, frame): return np.full(len(frame), self.value)
    def fit(self, *args, **kwargs): raise AssertionError('Inference must never fit')


def candidate():
    return {'ticket_event_id': 501, 'kickoff_at': '2026-11-05T18:00:00Z',
        'prior': {'stadium_capacity': 1000, 'p50': 300, 'source_prior_id': 88,
                  'horizon': 'T-1', 'point_in_time_validated': True,
                  'target_as_of_at': '2026-11-04T18:00:00Z', 'generated_at': '2026-11-04T18:01:00Z'},
        'representatives': [{'ticket_event_id': 501, 'requested_snapshot_id': 50101, 'bucket_6h': 0,
            'requested_as_of_at': '2026-11-05T13:30:00Z',
            'features': {'as_of_at': '2026-11-05T13:30:00Z', 'snapshot_id': 50101,
                         'hours_to_kickoff': 4.5, 'point_in_time_validated': True}}]}


def fixture():
    new = C1ShadowRuntimeV8(FixedEstimator(.8), ('prior_p50', 'stadium_capacity'), PACKAGE, (), 74, live_model_id=MODEL_ID)
    old = C1ShadowRuntimeV8(FixedEstimator(.4), new.features, EXPECTED_PACKAGE, (), 30)
    payload = {'version': 'c1-shadow-v8-inputs-v1', 'package_version': EXPECTED_PACKAGE,
               'requested_at': NOW, 'candidate_count': 1, 'candidates': [candidate()]}
    manifest = {'frozen_at': FREEZE, 'artifact': {'sha256': 'new-test-hash'}, 'precommit_sha256': 'test-precommit',
                '_verified_manifest_sha256': 'test-manifest-hash',
                'old_frozen_hashes': {'ml/artifacts/c1_shadow_v8/c1_v2_live_expert_v1.joblib': 'original-test-hash'}}
    old_manifest = {'artifact': {'sha256': 'original-test-hash'}}
    return payload, manifest, old_manifest, new, old


class ExpansionCaptureTests(unittest.TestCase):
    def validate(self, c=None, **kwargs):
        return validate_current(c or candidate(), kwargs.get('requested', NOW), kwargs.get('now', NOW),
                                kwargs.get('freeze', FREEZE), kwargs.get('labelled', set()))

    def test_genuine_current_window_is_eligible(self):
        self.assertEqual(self.validate(), pd.Timestamp('2026-11-05T13:30:00Z'))

    def test_training_and_known_outcome_events_cannot_be_reused(self):
        with self.assertRaisesRegex(ValueError, 'known-outcome'): self.validate(labelled={501})
        c = candidate(); c['ticket_event_id'] = 1
        with self.assertRaisesRegex(ValueError, 'Training'): self.validate(c)

    def test_old_collector_timestamp_is_not_a_replay_loophole(self):
        with self.assertRaisesRegex(ValueError, 'current'): self.validate(requested='2026-11-05T13:00:00Z')

    def test_post_kickoff_and_too_early_capture_fail_closed(self):
        for now in ['2026-11-05T18:00:00Z', '2026-11-04T17:00:00Z']:
            with self.subTest(now=now), self.assertRaises(ValueError): self.validate(now=now, requested=now)

    def test_stale_and_prefreeze_latest_sources_are_rejected(self):
        for change in ['2026-11-05T16:00:00Z', '2026-11-05T13:45:00Z']:
            if '16:' in change:
                with self.assertRaisesRegex(ValueError, 'stale'): self.validate(now=change, requested=change)
            else:
                with self.assertRaisesRegex(ValueError, 'predates'): self.validate(freeze=change)

    def test_snapshot_time_pit_bucket_and_event_identity_are_required(self):
        for kind in ['snapshot', 'time', 'pit', 'bucket', 'event', 'future']:
            c = candidate(); r = c['representatives'][0]
            if kind == 'snapshot': r['features']['snapshot_id'] = 0
            elif kind == 'time': r['features']['as_of_at'] = '2026-11-05T13:31:00Z'
            elif kind == 'pit': r['features']['point_in_time_validated'] = False
            elif kind == 'bucket': r['bucket_6h'] = 1
            elif kind == 'event': r['ticket_event_id'] = 502
            else:
                r['requested_as_of_at'] = r['features']['as_of_at'] = '2026-11-05T14:01:00Z'
            with self.subTest(kind=kind), self.assertRaises(ValueError): self.validate(c)

    def test_prior_must_exist_by_observation_and_use_exact_horizon(self):
        for change in [{'generated_at': '2026-11-05T13:31:00Z'}, {'horizon': 'T-7'},
                       {'target_as_of_at': '2026-11-04T17:00:00Z'}, {'stadium_capacity': 0}]:
            c = candidate(); c['prior'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError): self.validate(c)

    def test_duplicate_representatives_are_rejected(self):
        c = candidate(); c['representatives'].append(deepcopy(c['representatives'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'): self.validate(c)

    def test_current_paired_capture_uses_both_frozen_models_without_fit(self):
        with tempfile.TemporaryDirectory() as d:
            data = fixture(); before = deepcopy(data[0])
            result = capture(*data, now=NOW, labelled_ids=set(), output_dir=Path(d))
            self.assertEqual(result['new_predictions'], 1)
            stored = json.loads(next(Path(d).glob('event-*.json')).read_text())
            self.assertEqual(stored['shared_prior'], 300)
            self.assertEqual(stored['expanded_raw'], 800)
            self.assertEqual(stored['expanded_policy'], 800)
            self.assertEqual(stored['original_raw'], 400)
            self.assertEqual(stored['original_policy'], 300)
            self.assertEqual(data[0], before)
            self.assertFalse(stored['production_change'])

    def test_repeated_capture_preserves_original_issue_and_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            data = fixture(); output = Path(d)
            capture(*data, now=NOW, labelled_ids=set(), output_dir=output)
            path = next(output.glob('event-*.json')); raw = path.read_bytes()
            result = capture(*data, now='2026-11-05T14:01:00Z', labelled_ids=set(), output_dir=output)
            self.assertEqual(result['events'][0]['status'], 'EXISTING_IDENTICAL')
            self.assertEqual(path.read_bytes(), raw)
            changed = json.loads(raw); changed['expanded_policy'] += 1
            with self.assertRaisesRegex(ValueError, 'conflict'): immutable_save(output, changed)
            self.assertEqual(path.read_bytes(), raw)

    def test_failed_coverage_does_not_emit_a_prediction_or_drop_event(self):
        with tempfile.TemporaryDirectory() as d:
            result = capture(*fixture(), now=NOW, labelled_ids={501}, output_dir=Path(d))
            self.assertEqual(result['candidate_count'], 1); self.assertEqual(result['new_predictions'], 0)
            self.assertEqual(result['events'][0]['status'], 'FAILED_CLOSED')
            self.assertFalse(list(Path(d).glob('event-*.json')))

    def test_duplicate_or_wrong_collector_cohort_fails_before_capture(self):
        for kind in ['duplicate', 'count', 'version']:
            data = fixture(); p = data[0]
            if kind == 'duplicate': p['candidates'].append(deepcopy(p['candidates'][0])); p['candidate_count'] = 2
            elif kind == 'count': p['candidate_count'] = 0
            else: p['package_version'] = PACKAGE
            with tempfile.TemporaryDirectory() as d, self.subTest(kind=kind), self.assertRaises(ValueError):
                capture(*data, now=NOW, labelled_ids=set(), output_dir=Path(d))

    def test_no_due_execution_is_not_a_forecast(self):
        data = fixture(); data[0].update(candidate_count=0, candidates=[])
        with tempfile.TemporaryDirectory() as d:
            result = capture(*data, now=NOW, labelled_ids=set(), output_dir=Path(d))
            self.assertEqual(result['new_predictions'], 0); self.assertEqual(result['candidate_count'], 0)
            self.assertFalse(list(Path(d).iterdir()))

    def test_new_destination_cannot_bypass_single_fixed_freeze_path(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(ValueError, 'fixed freeze'):
            fit_once(Path(d), Path(d)/'another-freeze', Path(d)/'lineage')

    def test_manifest_edits_are_rejected_before_artifact_load(self):
        with tempfile.TemporaryDirectory() as d, patch('joblib.load') as loader:
            directory = Path(d)
            (directory/'manifest.json').write_text('{}')
            (directory/'freeze_receipt.json').write_text(json.dumps({'package_version': PACKAGE, 'manifest_sha256': 'wrong'}))
            with self.assertRaisesRegex(ValueError, 'manifest hash'): load_frozen(directory)
            loader.assert_not_called()


if __name__ == '__main__': unittest.main()
