"""Synthetic-only recipe/gate/private-artifact and genuine inference boundaries."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from threadpoolctl import threadpool_limits

from ml.demand_engine.rolling72_features_v1 import _hash, build_issue
from ml.rolling72_offline_challenger_v2 import (
    DATASET_VERSION, FEATURE_NAMES, PRECOMMIT_SHA256, ROOT,
    fit_once, load_artifact, load_precommit, predict, training_weights, validate_dataset,
)


def rehash_row(row):
    row["row_sha256"] = _hash({k: v for k, v in row.items() if k != "row_sha256"})
    return row


def rehash_dataset(data):
    data["dataset_sha256"] = _hash({k: v for k, v in data.items() if k != "dataset_sha256"})
    return data


def synthetic_dataset(fixtures=5, clubs=3, origins=4):
    recipe = load_precommit()
    cutoff = datetime.fromisoformat(recipe["training_data_cutoff_at"])
    rows = []
    for fixture in range(fixtures):
        kickoff = cutoff - timedelta(days=8 - fixture / 4)
        slope = (fixture - 2) * 2.0
        for origin_index in range(origins):
            origin = kickoff - timedelta(days=6) + timedelta(hours=origin_index)
            for horizon in (24, 48, 72):
                values = {"last_available_total": 1000.0, "observed_delta_since_first": 72 * slope,
                          "prefix_span_hours": 72.0, "latest_staleness_hours": 0.0,
                          "hours_to_kickoff": (kickoff - origin).total_seconds() / 3600,
                          "horizon_hours": horizon}
                for hours in (6, 24, 72):
                    values[f"delta_{hours}h"], values[f"slope_{hours}h"] = hours * slope, slope
                target = origin + timedelta(hours=horizon)
                first_id = (fixture + 1) * 10000 + origin_index * 100
                ids = [first_id + i for i in range(1, 5)]
                row = {"features": values, "nominal_horizon_hours": horizon,
                       "target_delta": slope * (horizon - .25),
                       "matched_available_total": 1000 + slope * (horizon - .25),
                       "last_available_total": 1000.0, "origin_capture_at": origin.isoformat(),
                       "target_at": target.isoformat(), "label_captured_at": (target - timedelta(minutes=15)).isoformat(),
                       "kickoff_at": kickoff.isoformat(), "ticket_event_id": fixture + 1,
                       "fixture_group": f"synthetic-fixture-{fixture}", "club_slug": f"synthetic-club-{fixture % clubs}",
                       "source_family": "roboticket/roboticket", "historical_input_known_at": None,
                       "historical_knowledge_unproven": True,
                       "source_received_at": recipe["source_bindings"]["inventory"]["received_at"],
                       "segment_lineage": {"segment_id": _hash([fixture, "segment"]),
                           "measurement_key": "roboticket/roboticket", "start_snapshot_id": ids[0],
                           "origin_snapshot_id": ids[-1], "label_snapshot_id": first_id + horizon,
                           "raw_prefix_snapshot_ids": ids, "prior_incompatible_rows_retained": 0,
                           "first_event_point": False}, "prefix_sha256": _hash([fixture, origin_index, "prefix"])}
                rows.append(rehash_row(row))
    return rehash_dataset({"version": DATASET_VERSION, "precommit_sha256": PRECOMMIT_SHA256,
                          "rows": rows, "source_bindings": {
                              kind: {**entry, "verified_file_sha256": entry["file_sha256"]}
                              for kind, entry in recipe["source_bindings"].items()},
                          "coverage": {"THIS_IS_NOT_TRUSTED_SUPPORT": 999999}, "segment_catalogue": [], "fixture_groups": {},
                          "synthetic_test": True, "servable_training_input": False,
                          "historical_knowledge_unproven": True, "historical_input_known_at": None,
                          "model_fit_performed": False, "production_change": False, "live_adjustment": 0})


def actual_issue(event_id=999, issued=None, age=0, single=False):
    issued = issued or datetime.now(timezone.utc)
    ages = (age,) if single else (72 + age, 24 + age, 6 + age, age)
    event = {"ticket_event_id": event_id, "club_slug": "unseen-synthetic-club",
             "kickoff_at": (issued + timedelta(days=10)).isoformat(), "known_at": issued.isoformat(),
             "observations": [{"snapshot_id": 900000 + i,
                  "captured_at": (issued - timedelta(hours=h)).isoformat(), "known_at": issued.isoformat(),
                  "available_total": 1000.0, "measurement_key": "public-displayed-available-total-v1:roboticket/roboticket"}
                  for i, h in enumerate(ages, 1)]}
    return build_issue(event, issued)


class OfflineGateTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def test_exact_recipe_and_fake_coverage_cannot_open_support_gate(self):
        data = synthetic_dataset(fixtures=2, clubs=2, origins=12)
        with patch("sklearn.ensemble.HistGradientBoostingRegressor.fit", side_effect=AssertionError('no fit')):
            result = fit_once(self.root / 'model', data, synthetic_test=True)
        self.assertEqual(result['status'], 'NO_FIT')
        self.assertEqual(result['gate']['common_fixtures'], 2)
        self.assertGreater(result['gate']['training_rows'], 60)
        self.assertFalse((self.root / 'model').exists())
        self.assertEqual(load_precommit()['candidate']['parameters']['quantile'], .5)

    def test_club_and_row_gates_are_recomputed_independently(self):
        _, clubs = validate_dataset(synthetic_dataset(clubs=2), synthetic_test=True)
        _, rows = validate_dataset(synthetic_dataset(origins=3), synthetic_test=True)
        self.assertIn('INSUFFICIENT_COMMON_CLUBS', clubs['reasons'])
        self.assertIn('INSUFFICIENT_ROWS', rows['reasons'])

    def test_each_whole_fixture_must_have_all_three_horizons(self):
        data = synthetic_dataset()
        data['rows'] = [r for r in data['rows'] if r['ticket_event_id'] != 5 or r['nominal_horizon_hours'] != 72]
        _, gate = validate_dataset(rehash_dataset(data), synthetic_test=True)
        self.assertEqual(gate['common_fixtures'], 4)
        self.assertEqual(gate['partial_horizon_fixture_groups_excluded'], ['synthetic-fixture-4'])

    def test_fixture_weights_are_equal_despite_unequal_origin_counts(self):
        data = synthetic_dataset(origins=5)
        data['rows'] = [r for r in data['rows'] if r['ticket_event_id'] != 1
                        or r['origin_capture_at'] == min(x['origin_capture_at'] for x in data['rows'] if x['ticket_event_id'] == 1)]
        rows, _ = validate_dataset(rehash_dataset(data), synthetic_test=True)
        totals = {}
        for row, weight in zip(rows, training_weights(rows)):
            key = (row['fixture_group'], row['nominal_horizon_hours'])
            totals[key] = totals.get(key, 0) + weight
        self.assertTrue(all(abs(v - len(rows) / 15) < 1e-10 for v in totals.values()))

    def test_clock_tampering_late_source_and_fake_historical_knowledge_fail(self):
        for field, value in [('historical_input_known_at', '2020-01-01T00:00:00Z'),
                             ('source_received_at', '2030-01-01T00:00:00Z'),
                             ('label_captured_at', '2030-01-01T00:00:00Z')]:
            data = synthetic_dataset()
            data['rows'][0][field] = value
            rehash_row(data['rows'][0])
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_dataset(rehash_dataset(data), synthetic_test=True)

    def test_counts_values_missingness_and_source_family_are_not_coerced(self):
        for change in ({'target_delta': True}, {'matched_available_total': -1}, {'source_family': 'roboticket/roboticket_candidate_backfill'}):
            data = synthetic_dataset(); data['rows'][0].update(change); rehash_row(data['rows'][0])
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_dataset(rehash_dataset(data), synthetic_test=True)
        data = synthetic_dataset(); data['rows'][0]['features']['delta_24h'] = None; rehash_row(data['rows'][0])
        with self.assertRaisesRegex(ValueError, 'missingness'):
            validate_dataset(rehash_dataset(data), synthetic_test=True)

    def test_source_dataset_row_and_feature_hash_guards(self):
        for edit in ('source', 'unverified_source', 'dataset', 'row', 'feature'):
            data = synthetic_dataset()
            if edit == 'source':
                data['source_bindings']['inventory']['file_sha256'] = '0' * 64
                rehash_dataset(data)
            elif edit == 'unverified_source':
                del data['source_bindings']['inventory']['verified_file_sha256']
                rehash_dataset(data)
            elif edit == 'dataset':
                data['coverage']['malicious'] = 1
            elif edit == 'row':
                data['rows'][0]['target_delta'] = 9
                rehash_dataset(data)
            else:
                data['rows'][0]['features']['actual_attendance'] = 12000
                rehash_row(data['rows'][0]); rehash_dataset(data)
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate_dataset(data, synthetic_test=True)

    def test_duplicates_alias_group_and_club_support_inflation_fail(self):
        for edit in ('duplicate', 'eventgroup', 'club'):
            data = synthetic_dataset()
            if edit == 'duplicate':
                data['rows'].append(deepcopy(data['rows'][0]))
            elif edit == 'eventgroup':
                data['rows'][0]['fixture_group'] = 'fake-extra-group'; rehash_row(data['rows'][0])
            else:
                data['rows'][0]['club_slug'] = 'fake-extra-club'; rehash_row(data['rows'][0])
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate_dataset(rehash_dataset(data), synthetic_test=True)

    def test_synthetic_data_requires_explicit_mode(self):
        with self.assertRaisesRegex(ValueError, 'mode mismatch'):
            validate_dataset(synthetic_dataset())


class OfflineArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.root = Path(cls.folder.name)
        cls.data = synthetic_dataset()
        with threadpool_limits(limits=1):
            cls.fitted = fit_once(cls.root / 'original', cls.data, synthetic_test=True)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def copy_model(self, name):
        import shutil
        destination = self.root / name
        shutil.copytree(self.root / 'original', destination)
        return destination

    def test_one_synthetic_fit_and_idempotent_reuse_never_refits(self):
        self.assertEqual(self.fitted['status'], 'SYNTHETIC_TEST_FITTED')
        with patch('sklearn.ensemble.HistGradientBoostingRegressor.fit', side_effect=AssertionError('no second fit')):
            result = fit_once(self.root / 'original', self.data, synthetic_test=True)
        self.assertEqual(result['status'], 'FROZEN_REUSED')
        self.assertFalse(result['model_fit_performed'])

    def test_default_loading_and_prediction_cannot_serve_synthetic_model(self):
        with self.assertRaisesRegex(ValueError, 'Synthetic model'):
            load_artifact(self.root / 'original')
        loaded = load_artifact(self.root / 'original', allow_synthetic_test=True)
        result = predict(loaded, actual_issue(), 24, 'unseen')
        self.assertEqual(result['status'], 'SYNTHETIC_MODEL_NOT_SERVABLE')
        self.assertIsNone(result['predicted_available_total'])

    def test_loader_verifies_file_before_joblib_deserialization(self):
        folder = self.copy_model('tampered-model')
        with (folder / 'model.joblib').open('ab') as stream:
            stream.write(b'corruption')
        with patch('joblib.load', side_effect=AssertionError('must not deserialize')):
            with self.assertRaisesRegex(ValueError, 'bytes checksum'):
                load_artifact(folder, allow_synthetic_test=True)

    def test_changed_recipe_or_incomplete_marker_prevents_loading(self):
        for name in ('recipe', 'marker'):
            folder = self.copy_model('tampered-' + name)
            if name == 'recipe':
                p = folder / 'manifest.json'; data = json.loads(p.read_text()); data['parameters']['max_iter'] = 101
                data['manifest_sha256'] = _hash({k: v for k, v in data.items() if k != 'manifest_sha256'})
            else:
                p = folder / 'fit-marker.json'; data = json.loads(p.read_text()); data['status'] = 'FIT_STARTED'
            p.write_text(json.dumps(data))
            with patch('joblib.load', side_effect=AssertionError('must not deserialize')):
                with self.assertRaises(ValueError):
                    load_artifact(folder, allow_synthetic_test=True)

    def test_failed_fit_marker_blocks_any_retry(self):
        folder = self.root / 'failed-fit'
        with patch('sklearn.ensemble.HistGradientBoostingRegressor.fit', side_effect=RuntimeError('synthetic failure')):
            with self.assertRaises(RuntimeError):
                fit_once(folder, self.data, synthetic_test=True)
        self.assertEqual(json.loads((folder / 'fit-marker.json').read_text())['status'], 'FAILED_NO_REFIT')
        with patch('sklearn.ensemble.HistGradientBoostingRegressor.fit', side_effect=AssertionError('no retry')):
            with self.assertRaises(FileExistsError):
                fit_once(folder, self.data, synthetic_test=True)

    def test_new_dataset_cannot_overwrite_existing_frozen_model(self):
        changed = synthetic_dataset(origins=5)
        with self.assertRaisesRegex(ValueError, 'another dataset'):
            fit_once(self.root / 'original', changed, synthetic_test=True)

    def test_actual_canonical_inference_preserves_first_point_and_targets(self):
        loaded = load_artifact(self.root / 'original', allow_synthetic_test=True)
        issue = actual_issue(single=True)
        result = predict(loaded, issue, 72, 'unseen', allow_synthetic_test=True)
        self.assertEqual(result['status'], 'READY')
        self.assertGreaterEqual(result['predicted_available_total'], 0)
        self.assertEqual(result['target_at'], (datetime.fromisoformat(issue['issued_at']) + timedelta(hours=72)).isoformat())
        self.assertIsNone(result['intervals'])
        self.assertTrue(result['historical_training_knowledge_unproven'])

    def test_inference_group_or_ticket_overlap_and_pre_freeze_issue_are_blocked(self):
        loaded = load_artifact(self.root / 'original', allow_synthetic_test=True)
        group = predict(loaded, actual_issue(), 24, 'synthetic-fixture-0', allow_synthetic_test=True)
        ticket = predict(loaded, actual_issue(event_id=1), 24, 'unseen', allow_synthetic_test=True)
        frozen = datetime.fromisoformat(loaded['manifest']['frozen_at'])
        past = predict(loaded, actual_issue(issued=frozen - timedelta(seconds=1)), 24, 'unseen', allow_synthetic_test=True)
        self.assertEqual(group['status'], 'CURRENT_FIXTURE_IN_TRAINING')
        self.assertEqual(ticket['status'], 'CURRENT_FIXTURE_IN_TRAINING')
        self.assertEqual(past['status'], 'MODEL_NOT_FROZEN_BEFORE_ISSUE')

    def test_future_issue_and_stale_input_are_not_served(self):
        loaded = load_artifact(self.root / 'original', allow_synthetic_test=True)
        with self.assertRaisesRegex(ValueError, 'Future inference'):
            predict(loaded, actual_issue(issued=datetime.now(timezone.utc) + timedelta(hours=1)), 24, 'unseen', allow_synthetic_test=True)
        result = predict(loaded, actual_issue(age=1.001), 24, 'unseen', allow_synthetic_test=True)
        self.assertEqual(result['status'], 'STALE_INPUT_FOR_V2')
        self.assertIsNone(result['predicted_available_total'])

    def test_live_horizon_feature_includes_source_age_without_moving_target(self):
        loaded = load_artifact(self.root / 'original', allow_synthetic_test=True)
        issue = actual_issue(age=.5)
        with patch('sklearn.ensemble.HistGradientBoostingRegressor.predict', return_value=np.asarray([5.0])) as call:
            result = predict(loaded, issue, 24, 'unseen', allow_synthetic_test=True)
        matrix = call.call_args.args[0]
        self.assertEqual(matrix[0, FEATURE_NAMES.index('horizon_hours')], 24.5)
        self.assertEqual(result['effective_lead_hours'], 24.5)
        self.assertEqual(result['predicted_available_total'], 1005)
        self.assertEqual(result['target_at'], (datetime.fromisoformat(issue['issued_at']) + timedelta(hours=24)).isoformat())

    def test_mutated_in_memory_estimator_is_rejected(self):
        loaded = load_artifact(self.root / 'original', allow_synthetic_test=True)
        loaded['model']._baseline_prediction += 100
        with self.assertRaisesRegex(ValueError, 'mutated after freeze'):
            predict(loaded, actual_issue(), 24, 'unseen', allow_synthetic_test=True)

    def test_mutated_in_memory_tree_is_rejected(self):
        loaded = load_artifact(self.root / 'original', allow_synthetic_test=True)
        loaded['model']._predictors[0][0].nodes['value'][0] += 100
        with self.assertRaisesRegex(ValueError, 'mutated after freeze'):
            predict(loaded, actual_issue(), 24, 'unseen', allow_synthetic_test=True)

    def test_mechanism_is_fixed_synthetic_and_not_accuracy_or_tuning(self):
        audit = self.fitted['manifest']['mechanism_audit']
        self.assertEqual([p['horizon_hours'] for p in audit['probes']], [24, 48, 72])
        self.assertFalse(audit['mae_computed'])
        self.assertFalse(audit['retune_permitted'])
        self.assertFalse(self.fitted['manifest']['mae_computed'])
        self.assertTrue(self.fitted['manifest']['historical_knowledge_unproven'])


if __name__ == '__main__':
    unittest.main()
