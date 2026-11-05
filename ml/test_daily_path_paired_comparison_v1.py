from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from ml.c1_live_matched_audit_v1 import ROOT
from ml.daily_inventory_drift_comparator_v1 import predict
from ml.daily_inventory_drift_ledger_v1 import DriftLedger
from ml.daily_path_paired_comparison_v1 import compare, summarize
from ml.daily_path_prefix_diagnostics_v1 import read_ledger
from ml.demand_engine.daily_inventory_path_dataset_v1 import build_issue
from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger
from ml.demand_engine.daily_inventory_path_model_v1 import predict_path

ISSUED = datetime(2027, 2, 17, 18, tzinfo=timezone.utc)


def fixture():
    issue = build_issue({'ticket_event_id': 999, 'club_slug': 'synthetic',
        'kickoff_at': (ISSUED + timedelta(days=3)).isoformat(),
        'observations': [{'snapshot_id': 1000 + hour,
            'captured_at': (ISSUED - timedelta(hours=hour + 1)).isoformat(),
            'available_total': 100 + hour, 'measurement_key': 'synthetic/inventory'}
            for hour in range(36, -1, -1)]}, ISSUED)
    model = json.loads((ROOT/'ml/artifacts/daily_inventory_path_v1.json').read_text())
    drift = json.loads((ROOT/'ml/artifacts/daily_inventory_drift_comparator_v1.json').read_text())
    source_points = predict_path(issue, model)
    _, drift_points = predict(issue, drift)
    first, clean, _ = DailyInventoryPathLedger._validate(issue, source_points, model, ISSUED)
    second, sidecar, _ = DriftLedger._validate(issue, drift_points, drift, ISSUED)
    attempts = [{**first, 'attempt_id': 1, 'executed_at': ISSUED.isoformat()}]
    comparators = [{**second, 'attempt_id': 1, 'executed_at': ISSUED.isoformat()}]
    points = [{**p, 'attempt_id': 1, 'score': None} for p in clean]
    sidecar = [{**p, 'attempt_id': 1, 'score': None} for p in sidecar]
    return attempts, points, comparators, sidecar


def attach_score(point, actual=80., *, drift=False):
    target = datetime.fromisoformat(point['target_at'])
    signed = point['predicted_available_total'] - actual
    baseline = point['baseline_available_total'] - actual
    point['score'] = {'target_snapshot_id': 9000, 'target_captured_at': target.isoformat(),
        'target_available_total': actual, 'measurement_key': point['measurement_key'],
        'candidate_error': signed, 'candidate_abs_error': abs(signed),
        'baseline_error': baseline, 'baseline_abs_error': abs(baseline),
        'scored_at': (target + timedelta(minutes=1 if drift else 0)).isoformat(), 'production_change': False}
    if drift:
        point['score']['reference_source_scored_at'] = target.isoformat()


class PairedTests(unittest.TestCase):
    def test_pending_points_have_null_mae_and_all_denominators(self):
        args = fixture(); before = deepcopy(args)
        result = compare(*args, (ISSUED + timedelta(hours=2)).isoformat())
        self.assertEqual(args, before)
        self.assertEqual(result['coverage']['paired_points'], 2)
        self.assertEqual(result['coverage']['pending_targets'], 2)
        self.assertIsNone(result['overlap']['metrics']['drift']['event_balanced_mae'])

    def test_exact_same_future_label_scores_three_experts(self):
        args = fixture(); attach_score(args[1][0]); attach_score(args[3][0], drift=True)
        result = compare(*args, (ISSUED + timedelta(days=1, hours=1)).isoformat())
        self.assertEqual(result['overlap']['independent_events'], 1)
        self.assertEqual(result['coverage']['paired_scored_points'], 1)
        self.assertEqual(result['coverage']['pending_targets'], 1)
        self.assertEqual(result['overlap']['metrics']['persistence']['event_balanced_mae'], 20)
        self.assertAlmostEqual(result['overlap']['metrics']['drift']['event_balanced_mae'], 5)

    def test_event_balance_does_not_turn_multiple_prefixes_into_events(self):
        rows = [{'ticket_event_id': 1, 'club_slug': 'a', 'signed_errors':
                 {'daily_model': 1, 'drift': 2, 'persistence': 3}} for _ in range(3)]
        rows.append({'ticket_event_id': 2, 'club_slug': 'b', 'signed_errors':
                     {'daily_model': 9, 'drift': 8, 'persistence': 7}})
        result = summarize(rows)
        self.assertEqual(result['independent_events'], 2)
        self.assertEqual(result['metrics']['daily_model']['event_balanced_mae'], 5)
        self.assertEqual(result['metrics']['drift']['event_balanced_mae'], 5)
        self.assertEqual(result['paired_comparisons']['drift_minus_daily_model']['event_improvement_rate'], .5)

    def test_missing_comparator_or_lagging_score_is_coverage_not_zero_error(self):
        args = fixture()
        result = compare(args[0], args[1], [], [], (ISSUED + timedelta(days=1, hours=1)).isoformat())
        self.assertEqual(result['coverage']['daily_points_without_drift'], 2)
        self.assertIsNone(result['overlap']['metrics']['daily_model']['event_balanced_mae'])
        attach_score(args[1][0])
        result = compare(*args, (ISSUED + timedelta(days=1, hours=1)).isoformat())
        self.assertEqual(result['coverage']['reference_scored_waiting_for_drift_score'], 1)
        self.assertIsNone(result['overlap']['metrics']['drift']['event_balanced_mae'])

    def test_duplicate_wrong_artifact_and_different_vintage_are_rejected(self):
        for variant in ('duplicate', 'model', 'vintage', 'prefix', 'execution', 'missing_point'):
            args = fixture()
            if variant == 'duplicate': args[3].append(deepcopy(args[3][0]))
            elif variant == 'model': args[2][0]['artifact']['model_sha256'] = '0'*64
            elif variant == 'vintage': args[3][0]['issued_as_of_at'] = (ISSUED + timedelta(days=1)).isoformat()
            elif variant == 'prefix': args[3][0]['prefix_sha256'] = '0'*64
            elif variant == 'execution': args[2][0]['executed_at'] = (ISSUED + timedelta(hours=2)).isoformat()
            else: args[3].pop()
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                compare(*args, (ISSUED + timedelta(days=1, hours=1)).isoformat())

    def test_changed_label_clock_and_stored_errors_are_rejected(self):
        for variant in ('label', 'capture', 'arithmetic', 'clock', 'reference', 'unscored_reference'):
            args = fixture(); attach_score(args[1][0]); attach_score(args[3][0], drift=True)
            score = args[3][0]['score']
            if variant == 'label': score['target_snapshot_id'] += 1
            elif variant == 'capture': score['target_captured_at'] = (ISSUED + timedelta(days=1, seconds=1)).isoformat()
            elif variant == 'arithmetic': score['candidate_abs_error'] += 1
            elif variant == 'clock': score['scored_at'] = ISSUED.isoformat()
            elif variant == 'reference': score['reference_source_scored_at'] = (ISSUED + timedelta(days=1, seconds=1)).isoformat()
            else: args[1][0]['score'] = None
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                compare(*args, (ISSUED + timedelta(days=1, hours=1)).isoformat())

    def test_real_ledger_reader_and_frozen_validation_leave_both_files_unchanged(self):
        attempts, points, comparators, sidecar = fixture()
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp)/'daily.sqlite', Path(temp)/'drift.sqlite'
            with DailyInventoryPathLedger(first) as ledger:
                ledger.record(attempts[0]['issue'], attempts[0]['points'], attempts[0]['artifact'], ISSUED)
            with DriftLedger(second) as ledger:
                ledger.record(comparators[0]['issue'], comparators[0]['points'], comparators[0]['artifact'], ISSUED)
            before = first.read_bytes(), second.read_bytes()
            result = compare(*read_ledger(first), *read_ledger(second), (ISSUED + timedelta(hours=2)).isoformat())
            self.assertEqual(result['coverage']['paired_points'], 2)
            self.assertEqual(before, (first.read_bytes(), second.read_bytes()))


if __name__ == '__main__':
    unittest.main()
