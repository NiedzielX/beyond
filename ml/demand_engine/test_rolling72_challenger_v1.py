"""Synthetic-only candidate tests; never fit current real observations."""
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import math
import unittest
from unittest.mock import patch

from threadpoolctl import threadpool_limits

from ml.demand_engine.rolling72_challenger_v1 import (
    FEATURE_NAMES, PRECOMMIT_SHA256, _feature_values, fit_candidate,
    load_precommit, predict_candidate, training_weights,
)
from ml.demand_engine.rolling72_features_v1 import HORIZONS, _hash, build_issue, features
from ml.demand_engine.rolling72_labels_v1 import match_target


CUTOFF = datetime(2026, 11, 8, 14, 28, 33, 607511, tzinfo=timezone.utc)
KEY = "public-displayed-available-total-v1:roboticket/roboticket"


def training_examples(fixtures=5, clubs=3, origins=4):
    """Entirely fabricated receipt/group declarations for isolated unit tests."""
    result = []
    for fixture in range(fixtures):
        kickoff = CUTOFF - timedelta(days=10 - fixture)
        slope = (fixture - 2) * 2
        for origin in range(origins):
            issued = kickoff - timedelta(days=6) + timedelta(hours=origin)
            observations = [
                {"snapshot_id": 10000 * (fixture + 1) + 10 * origin + index,
                 "captured_at": (issued - timedelta(hours=age)).isoformat(),
                 "known_at": issued.isoformat(), "available_total": 1000 - slope * age,
                 "measurement_key": KEY}
                for index, age in enumerate((72, 24, 6, 0), 1)
            ]
            event = {"ticket_event_id": fixture + 1, "club_slug": f"synthetic-club-{fixture % clubs}",
                     "kickoff_at": kickoff.isoformat(), "known_at": issued.isoformat(),
                     "observations": observations}
            issue = build_issue(event, issued)
            for horizon in HORIZONS:
                target = issued + timedelta(hours=horizon)
                received = target + timedelta(minutes=15)
                label_event = {**event, "observations": observations + [
                    {"snapshot_id": 100000 * (fixture + 1) + 100 * origin + horizon,
                     "captured_at": target.isoformat(), "known_at": received.isoformat(),
                     "available_total": 1000 + slope * horizon, "measurement_key": KEY}]}
                matched = match_target(label_event, issue, horizon, received)
                result.append({"issue": issue, "matched_label": matched,
                               "fixture_group": f"synthetic-fixture-{fixture}",
                               "source_lineage": {
                                   "evidence": "original-receipt-known-bounds-only", "identity_proven": True,
                                   "input_receipt_sha256": _hash([fixture, origin, "synthetic-input"]),
                                   "label_receipt_sha256": _hash([fixture, origin, horizon, "synthetic-label"]),
                                   "identity_registry_sha256": _hash("synthetic-registry-not-real-evidence"),
                                   "input_receipt_known_at": issued.isoformat(),
                                   "label_receipt_known_at": received.isoformat(),
                               }})
    return result


def inference_issue(event_id=999, slope=0, issued=None, source_key=KEY):
    issued = datetime.now(timezone.utc) if issued is None else issued
    event = {
        "ticket_event_id": event_id, "club_slug": "synthetic-unseen-club",
        "kickoff_at": (issued + timedelta(days=10)).isoformat(),
        "known_at": issued.isoformat(),
        "observations": [
            {"snapshot_id": event_id * 10 + index, "captured_at": (issued - timedelta(hours=age)).isoformat(),
             "known_at": issued.isoformat(), "available_total": 1000 - slope * age,
             "measurement_key": source_key}
            for index, age in enumerate((72, 24, 6, 0), 1)
        ],
    }
    return build_issue(event, issued)


class ChallengerGateTests(unittest.TestCase):
    def test_exact_recipe_and_feature_order_are_pinned(self):
        recipe = load_precommit()
        self.assertEqual(recipe["precommit_sha256"], PRECOMMIT_SHA256)
        self.assertEqual(tuple(recipe["features"]), FEATURE_NAMES)
        self.assertFalse(recipe["candidate"]["parameters"]["early_stopping"])

    def test_zero_rows_does_not_fit(self):
        result = fit_candidate([], CUTOFF)
        self.assertEqual(result["status"], "NO_FIT")
        self.assertIsNone(result["model"])
        self.assertEqual(result["gate"]["common_fixture_count"], 0)

    def test_many_correlated_rows_from_two_fixtures_do_not_open_gate(self):
        rows = training_examples(fixtures=2, clubs=2, origins=10)
        with patch("sklearn.ensemble.HistGradientBoostingRegressor.fit", side_effect=AssertionError("must not fit")):
            result = fit_candidate(rows, CUTOFF)
        self.assertEqual(result["status"], "NO_FIT")
        self.assertEqual(result["gate"]["training_row_count"], 60)
        self.assertEqual(result["gate"]["common_fixture_count"], 2)

    def test_club_and_total_row_gates_are_independent(self):
        two_clubs = fit_candidate(training_examples(clubs=2), CUTOFF)
        short = fit_candidate(training_examples(origins=3), CUTOFF)
        self.assertEqual(two_clubs["status"], "NO_FIT")
        self.assertIn("INSUFFICIENT_CLUBS_72H", two_clubs["gate"]["reasons"])
        self.assertIn("INSUFFICIENT_TOTAL_LABELED_ROWS", short["gate"]["reasons"])

    def test_each_fixture_needs_all_three_horizons(self):
        rows = training_examples()
        rows = [r for r in rows if r["fixture_group"] != "synthetic-fixture-4"
                or r["matched_label"]["horizon_hours"] != 72]
        result = fit_candidate(rows, CUTOFF)
        self.assertEqual(result["status"], "NO_FIT")
        self.assertEqual(result["gate"]["common_fixture_count"], 4)
        self.assertEqual(result["gate"]["training_row_count"], 48)

    def test_duplicate_rows_cannot_inflate_support(self):
        rows = training_examples()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            fit_candidate(rows + [deepcopy(rows[0])], CUTOFF)

    def test_aliases_cannot_claim_same_ticket_as_independent_fixtures(self):
        rows = training_examples()
        rows[-1] = {**rows[-1], "fixture_group": "invented-other-fixture"}
        with self.assertRaisesRegex(ValueError, "event|fixture"):
            fit_candidate(rows, CUTOFF)

    def test_ongoing_fixture_and_late_label_fail_before_fit(self):
        for kind in ("ongoing", "late"):
            rows = training_examples()
            row = rows[0]
            if kind == "late":
                row["source_lineage"]["label_receipt_known_at"] = (CUTOFF + timedelta(seconds=1)).isoformat()
            else:
                issue = row["issue"]
                new = build_issue({**issue["event"], "kickoff_at": (CUTOFF + timedelta(days=1)).isoformat(),
                                   "observations": issue["observed_prefix"]}, issue["issued_at"])
                row["issue"] = new
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                fit_candidate(rows, CUTOFF)

    def test_exact_cutoff_and_original_source_identity_are_required(self):
        with self.assertRaisesRegex(ValueError, "cutoff"):
            fit_candidate([], CUTOFF + timedelta(seconds=1))
        rows = training_examples()
        rows[0]["source_lineage"]["identity_proven"] = False
        with self.assertRaisesRegex(ValueError, "identity"):
            fit_candidate(rows, CUTOFF)
        rows[0]["source_lineage"]["identity_proven"] = True
        rows[0]["source_lineage"]["input_receipt_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "SHA256"):
            fit_candidate(rows, CUTOFF)

    def test_weights_balance_fixture_and_horizon_despite_sampling_counts(self):
        rows = []
        for group, counts in (("a", (8, 2, 1)), ("b", (1, 1, 1))):
            for horizon, count in zip(HORIZONS, counts):
                rows.extend({"fixture_group": group, "horizon_hours": horizon} for _ in range(count))
        weights = training_weights(rows)
        totals = defaultdict(float)
        for row, weight in zip(rows, weights):
            totals[(row["fixture_group"], row["horizon_hours"])] += weight
        self.assertAlmostEqual(sum(weights), len(rows))
        self.assertTrue(all(math.isclose(value, len(rows) / 6) for value in totals.values()))

    def test_missing_history_is_nan_never_fitted_imputation(self):
        issue = inference_issue()
        single = build_issue({**issue["event"], "observations": [issue["observed_prefix"][-1]]}, issue["issued_at"])
        values = _feature_values(single, 72)
        self.assertEqual(len(values), 12)
        self.assertTrue(math.isnan(values[FEATURE_NAMES.index("delta_24h")]))
        self.assertNotIn("observation_count", FEATURE_NAMES)


class ChallengerSyntheticFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.enterClassContext(threadpool_limits(limits=1))
        cls.synthetic = fit_candidate(training_examples(), CUTOFF, synthetic_test=True)
        if cls.synthetic["status"] != "SYNTHETIC_TEST_FITTED":
            raise AssertionError(cls.synthetic)

    def test_only_single_declared_estimator_and_parameters_are_used(self):
        result = self.synthetic
        self.assertEqual(result["manifest"]["training_row_count"], 60)
        self.assertEqual(result["manifest"]["feature_names"], list(FEATURE_NAMES))
        for key, value in load_precommit()["candidate"]["parameters"].items():
            self.assertEqual(result["model"].get_params()[key], value)
        self.assertTrue(result["manifest"]["synthetic_test"])

    def test_synthetic_estimator_is_not_served_by_default(self):
        result = predict_candidate(self.synthetic, inference_issue(), 72, "unseen")
        self.assertEqual(result["status"], "SYNTHETIC_MODEL_NOT_SERVABLE")
        self.assertIsNone(result["predicted_available_total"])

    def test_new_fixture_inference_is_finite_and_nonnegative(self):
        result = predict_candidate(self.synthetic, inference_issue(), 72, "unseen", allow_synthetic_test=True)
        self.assertEqual(result["status"], "READY")
        self.assertGreaterEqual(result["predicted_available_total"], 0)
        self.assertTrue(math.isfinite(result["raw_predicted_delta"]))
        self.assertEqual(result["scenario_stability"], "UNKNOWN")
        self.assertIsNone(result["intervals"])

    def test_same_last_level_different_histories_can_produce_different_future(self):
        low = predict_candidate(self.synthetic, inference_issue(slope=-4), 72, "unseen", allow_synthetic_test=True)
        high = predict_candidate(self.synthetic, inference_issue(slope=4), 72, "unseen", allow_synthetic_test=True)
        self.assertLess(low["predicted_available_total"], high["predicted_available_total"])

    def test_same_ticket_or_fixture_alias_cannot_become_unseen_test(self):
        for event_id, group in ((1, "unseen"), (999, "synthetic-fixture-0")):
            result = predict_candidate(self.synthetic, inference_issue(event_id=event_id), 72, group,
                                       allow_synthetic_test=True)
            self.assertEqual(result["status"], "INFERENCE_FIXTURE_IN_TRAIN")

    def test_model_cannot_predict_an_issue_before_its_freeze(self):
        early = datetime.fromisoformat(self.synthetic["manifest"]["frozen_at"]) - timedelta(seconds=1)
        result = predict_candidate(self.synthetic, inference_issue(issued=early), 72, "unseen",
                                   allow_synthetic_test=True)
        self.assertEqual(result["status"], "MODEL_NOT_FROZEN_BEFORE_ISSUE")

    def test_manifest_and_estimator_tampering_are_rejected(self):
        corrupt = deepcopy(self.synthetic)
        corrupt["manifest"]["training_row_count"] = 6000
        with self.assertRaisesRegex(ValueError, "manifest hash"):
            predict_candidate(corrupt, inference_issue(), 72, "unseen", allow_synthetic_test=True)
        corrupt = deepcopy(self.synthetic)
        corrupt["model"].set_params(learning_rate=.1)
        with self.assertRaisesRegex(ValueError, "estimator bytes"):
            predict_candidate(corrupt, inference_issue(), 72, "unseen", allow_synthetic_test=True)

    def test_unsupported_source_family_is_not_silently_pooled(self):
        result = predict_candidate(self.synthetic, inference_issue(source_key="other-provider/other-source"),
                                   72, "unseen", allow_synthetic_test=True)
        self.assertEqual(result["status"], "UNSUPPORTED_SOURCE_FAMILY")


if __name__ == "__main__":
    unittest.main()
