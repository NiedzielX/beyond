from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd

from ml.capture_c1_seat_median_v1 import capture, ensure_runtime
from ml.demand_engine.c1_seat_median_runtime_v1 import C1SeatMedianRuntimeV1, PACKAGE
from ml.demand_engine.c1_shadow_runtime_v8 import C1ShadowRuntimeV8
from ml.freeze_c1_seat_median_v1 import fit_once
from ml.score_c1_seat_median_v1 import score_rows, summary
from ml.test_c1_training_expansion_v1 import candidate, NOW, FREEZE, FixedEstimator
from ml.watch_c1_seat_median_v1 import MedianStorage, source_lock


def fixture():
    features = ('prior_p50', 'stadium_capacity')
    models = {'seat_median': C1SeatMedianRuntimeV1(FixedEstimator(800), features, (), 74),
        'ridge20': C1ShadowRuntimeV8(FixedEstimator(.7), features, 'synthetic-ridge20', (), 74),
        'original9': C1ShadowRuntimeV8(FixedEstimator(.4), features, 'synthetic-original9', (), 30)}
    hashes = {name: name+'-test-hash' for name in models}
    manifest = {'frozen_at': FREEZE, '_verified_manifest_sha256': 'test-manifest', 'precommit_sha256': 'test-precommit'}
    payload = {'version': 'c1-shadow-v8-inputs-v1', 'package_version': 'c1-shadow-v8-frozen-2026-10-16-n9',
               'requested_at': NOW, 'candidate_count': 1, 'candidates': [candidate()]}
    return payload, manifest, models, hashes


def scored_fixture():
    payload, manifest, models, hashes = fixture()
    with tempfile.TemporaryDirectory() as d:
        capture(payload, manifest, models, hashes, runtime=Path(d), labelled_ids=set(), now=NOW)
        evidence = [json.loads(next((Path(d)/'evidence').glob('event-*.json')).read_text())]
    outcomes = [{'ticket_event_id': 501, 'actual_attendance': 800, 'confirmed_at': '2026-11-05T21:00:00Z',
                 'source_name': 'synthetic', 'source_url': 'https://example.invalid/fixture-only'}]
    metadata = [{'id': 501, 'club_slug': 'synthetic', 'kickoff_at': evidence[0]['kickoff_at']}]
    return evidence, outcomes, metadata, manifest, hashes, '2026-11-05T22:00:00Z'


class SeatMedianTests(unittest.TestCase):
    def test_direct_person_output_is_not_multiplied_by_capacity(self):
        runtime = C1SeatMedianRuntimeV1(FixedEstimator(800), ('stadium_capacity',), (), 1)
        self.assertEqual(runtime.predict_live_p50(pd.DataFrame({'stadium_capacity': [20000]}))[0], 800)

    def test_runtime_clipping_serialization_and_no_fit(self):
        for value, expected in [(-1, 0), (30000, 20000)]:
            runtime = C1SeatMedianRuntimeV1(FixedEstimator(value), ('stadium_capacity',), (), 1)
            with tempfile.TemporaryDirectory() as d:
                path = Path(d)/'synthetic.joblib'; joblib.dump(runtime, path)
                self.assertEqual(joblib.load(path).predict_live_p50(pd.DataFrame({'stadium_capacity': [20000]}))[0], expected)

    def test_nonfinite_or_missing_runtime_inputs_fail_closed(self):
        for value in [float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                C1SeatMedianRuntimeV1(FixedEstimator(value), ('stadium_capacity',), (), 1).predict_live_p50(pd.DataFrame({'stadium_capacity': [1000]}))
        with self.assertRaises(ValueError): fixture()[2]['seat_median'].predict_live_p50(pd.DataFrame({'stadium_capacity': [1000]}))

    def test_all_three_experts_and_prior_share_one_real_cutoff(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as d:
            result = capture(*data, runtime=Path(d), labelled_ids=set(), now=NOW)
            self.assertEqual(result['new_predictions'], 1)
            row = json.loads(next((Path(d)/'evidence').glob('event-*.json')).read_text())
            self.assertEqual(row['forecasts'], {'prior': 300, 'seat_median_raw': 800, 'seat_median_policy': 800,
                'ridge20_raw': 700, 'ridge20_policy': 700, 'original9_raw': 400, 'original9_policy': 300})
            self.assertEqual(set(row['decisions']), {'seat_median', 'ridge20', 'original9'})

    def test_repeat_preserves_original_issue_bytes_and_conflict_cannot_overwrite(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as d:
            runtime = Path(d); capture(*data, runtime=runtime, labelled_ids=set(), now=NOW)
            path = next((runtime/'evidence').glob('event-*.json')); raw = path.read_bytes()
            repeat = capture(*data, runtime=runtime, labelled_ids=set(), now='2026-11-05T14:01:00Z')
            self.assertEqual(repeat['new_predictions'], 0); self.assertEqual(path.read_bytes(), raw)
            data[2]['seat_median'].estimator.value = 801
            failed = capture(*data, runtime=runtime, labelled_ids=set(), now=NOW)
            self.assertEqual(failed['events'][0]['status'], 'FAILED_CLOSED'); self.assertEqual(path.read_bytes(), raw)

    def test_known_outcomes_stale_and_prefreeze_sources_remain_failed_coverage(self):
        for kind in ['known', 'stale', 'prefreeze']:
            data = fixture(); now = NOW
            if kind == 'prefreeze': data[1]['frozen_at'] = '2026-11-05T13:45:00Z'
            if kind == 'stale': now = '2026-11-05T16:00:00Z'; data[0]['requested_at'] = now
            with tempfile.TemporaryDirectory() as d:
                result = capture(*data, runtime=Path(d), labelled_ids={501} if kind == 'known' else set(), now=now)
                self.assertEqual(result['candidate_count'], 1); self.assertEqual(result['new_predictions'], 0)
                self.assertEqual(result['events'][0]['status'], 'FAILED_CLOSED')

    def test_old_lane_runtime_is_refused_before_any_evidence_write(self):
        with tempfile.TemporaryDirectory() as d:
            runtime = Path(d); (runtime/'watcher-launch.json').write_text('{"other":"lane"}')
            with self.assertRaisesRegex(ValueError, 'old-lane'): ensure_runtime(runtime, fixture()[1])
            self.assertFalse((runtime/'experiment.json').exists())

    def test_runtime_marker_cannot_change_model_or_package(self):
        with tempfile.TemporaryDirectory() as d:
            runtime = Path(d); manifest = fixture()[1]; ensure_runtime(runtime, manifest)
            manifest['_verified_manifest_sha256'] = 'changed'
            with self.assertRaisesRegex(ValueError, 'Another experiment'): ensure_runtime(runtime, manifest)

    def test_canonical_freeze_guard_blocks_accidental_refit_before_reading_data(self):
        with tempfile.TemporaryDirectory() as d, patch('ml.freeze_c1_seat_median_v1.ARTIFACT_DIR', Path(d)), patch('sklearn.linear_model.QuantileRegressor.fit') as fit:
            with self.assertRaisesRegex(ValueError, 'fresh canonical'): fit_once(Path(d)/'unused', Path(d))
            fit.assert_not_called()

    def test_synthetic_capture_then_later_label_scores_all_models(self):
        rows, missing, count = score_rows(*scored_fixture()); report = summary(rows, missing, count)
        self.assertEqual(report['metrics']['seat_median_raw']['latest_row_mae'], 0)
        self.assertEqual(report['metrics']['ridge20_raw']['latest_row_mae'], 100)
        self.assertEqual(report['metrics']['original9_policy']['latest_row_mae'], 500)
        self.assertFalse(report['first_review_ready']); self.assertFalse(report['learner_gate_met'])
        self.assertIsNone(report['raw_learner_comparison']['paired_event_bootstrap_95_interval'])

    def test_no_outcome_is_null_mae_not_zero(self):
        data = list(scored_fixture()); data[1] = []
        rows, missing, count = score_rows(*data); report = summary(rows, missing, count)
        self.assertEqual(missing, [501]); self.assertEqual(count, 1)
        self.assertIsNone(report['metrics']['seat_median_policy']['latest_row_mae'])

    def test_known_future_or_changed_truth_and_identity_fail_closed(self):
        for kind in ['known', 'future', 'hash', 'value', 'duplicate', 'club']:
            data = list(scored_fixture())
            if kind == 'known': data[1][0]['confirmed_at'] = '2026-11-05T13:00:00Z'
            elif kind == 'future': data[1][0]['confirmed_at'] = '2026-11-05T23:00:00Z'
            elif kind == 'hash': data[0][0]['model_hashes']['ridge20'] = 'changed'
            elif kind == 'value': data[0][0]['forecasts']['seat_median_raw'] = 1
            elif kind == 'duplicate': data[0].append(deepcopy(data[0][0]))
            else: data[2][0]['club_slug'] = None
            with self.subTest(kind=kind), self.assertRaises(ValueError): score_rows(*data)

    def test_latest_time_and_event_weighting_do_not_select_smallest_error(self):
        rows, _, _ = score_rows(*scored_fixture())
        early = deepcopy(rows[0]); early['as_of_at'] = '2026-11-05T12:00:00Z'; early['absolute_errors']['seat_median_raw'] = 300
        other = deepcopy(rows[0]); other['ticket_event_id'] = 502; other['absolute_errors']['seat_median_raw'] = 100
        report = summary([early, rows[0], other], [], 2)
        self.assertEqual(report['metrics']['seat_median_raw']['latest_row_mae'], 50)
        self.assertEqual(report['metrics']['seat_median_raw']['event_balanced_window_mae'], 125)

    def test_raw_success_does_not_automatically_pass_the_governed_product_gate(self):
        rows, _, _ = score_rows(*scored_fixture()); cohort = []
        for index in range(30):
            row = deepcopy(rows[0]); row.update(ticket_event_id=1000+index, club_slug=str(index%8))
            row['absolute_errors']['seat_median_policy'] = 300
            cohort.append(row)
        report = summary(cohort, [], 30)
        self.assertTrue(report['first_review_ready']); self.assertTrue(report['learner_gate_met'])
        self.assertFalse(report['product_gate_met']); self.assertFalse(report['production_activation_allowed'])

    def test_full_review_requires_clubs_and_future_paired_improvement(self):
        rows, _, _ = score_rows(*scored_fixture()); cohort = []
        for index in range(30):
            row = deepcopy(rows[0]); row.update(ticket_event_id=1000+index, club_slug=str(index%8)); cohort.append(row)
        report = summary(cohort, [], 30)
        self.assertTrue(report['learner_gate_met']); self.assertTrue(report['product_gate_met'])
        self.assertEqual(report['raw_learner_comparison']['paired_event_bootstrap_95_interval'], [-100, -100])
        for row in cohort: row['club_slug'] = 'one'
        self.assertFalse(summary(cohort, [], 30)['first_review_ready'])

    def test_private_namespace_and_source_lock_cannot_mutate_an_old_lane(self):
        MedianStorage._key('c1-seat-median-v1/'+'a'*64+'.json')
        for path in ['c1-expansion-v1/'+'a'*64+'.json', 'manifests/'+'a'*64+'.json']:
            with self.assertRaises(ValueError): MedianStorage._key(path)
        with tempfile.TemporaryDirectory() as d:
            runtime = Path(d); source_lock(runtime, {'scorer': 'old'}); raw = (runtime/'collection-contract.json').read_bytes()
            with self.assertRaises(ValueError): source_lock(runtime, {'scorer': 'new'})
            self.assertEqual((runtime/'collection-contract.json').read_bytes(), raw)


if __name__ == '__main__': unittest.main()
