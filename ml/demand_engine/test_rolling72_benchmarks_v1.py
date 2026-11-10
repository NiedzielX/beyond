"""Clock, grouping and exact-event-median tests; all fit data are synthetic."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.rolling72_benchmarks_v1 import (
    PRECOMMIT_SHA256, event_balanced_median, fit_pickup, load_precommit,
    maturity_cell, predict_baselines, source_family, validated_training_rows,
)
from ml.demand_engine.rolling72_features_v1 import _hash, build_issue
from ml.demand_engine.rolling72_labels_v1 import match_target


TRAIN_ISSUE = datetime(2026, 10, 1, 12, 15, tzinfo=timezone.utc)
FAMILY = "public-displayed-available-total-v1:roboticket/roboticket"


def observation(identifier, issued, age, value=1000, family=FAMILY):
    return {"snapshot_id": identifier, "captured_at": (issued - timedelta(hours=age)).isoformat(),
            "known_at": issued.isoformat(), "available_total": value, "measurement_key": family}


def make_issue(issued=None, ages=(48, 25, 12, 0), values=None, event_id=999, days=10, family=FAMILY):
    issued = issued or datetime.now(timezone.utc) + timedelta(days=1)
    values = [1000] * len(ages) if values is None else values
    event = {"ticket_event_id": event_id, "club_slug": "future-club",
             "kickoff_at": (issued + timedelta(days=days)).isoformat(), "known_at": issued.isoformat(),
             "observations": [observation(i + 1, issued, age, value, family)
                              for i, (age, value) in enumerate(zip(ages, values))]}
    return build_issue(event, issued)


def training_row(index=0, horizon=24, delta=-100, issued=TRAIN_ISSUE, days=10):
    issue = make_issue(issued, event_id=100 + index, days=days)
    event = {**issue["event"], "club_slug": "club-" + str(index % 3),
             "observations": issue["observed_prefix"]}
    issue = build_issue(event, issued)
    target = issued + timedelta(hours=horizon)
    receipt = target + timedelta(hours=1)
    label_row = observation(1000 + index, target, 0, 1000 + delta)
    label_row["known_at"] = receipt.isoformat()
    label_event = {**event, "observations": [*event["observations"], label_row]}
    matched = match_target(label_event, issue, horizon, receipt)
    assert matched["status"] == "MATCHED"
    return {"issue": issue, "matched_label": matched, "fixture_group": "fixture-" + str(index),
            "source_lineage": {"evidence": "original-receipt-known-bounds-only",
                               "input_receipt_sha256": "1" * 64, "label_receipt_sha256": "2" * 64,
                               "identity_registry_sha256": "3" * 64, "identity_proven": True,
                               "input_receipt_known_at": issued.isoformat(),
                               "label_receipt_known_at": receipt.isoformat()}}


def model_point(payload, horizon=24, model="pickup"):
    return next(point for point in payload["points"] if point["horizon_hours"] == horizon)["models"][model]


class Rolling72BenchmarkTests(unittest.TestCase):
    def test_pinned_recipe_and_only_declared_family_namespace(self):
        self.assertEqual(load_precommit()["precommit_sha256"], PRECOMMIT_SHA256)
        self.assertEqual(source_family(make_issue()), "roboticket/roboticket")
        for family in ("roboticket/roboticket_candidate_backfill", "roboticket/roboticket_vao_selectable_v1",
                       "someotherprefix:roboticket/roboticket"):
            self.assertIsNone(source_family(make_issue(family=family)))

    def test_first_point_at_p50_and_p10_keeps_persistence_without_fake_drift(self):
        for days in (50, 10):
            issue = make_issue(ages=(0,), days=days)
            result = predict_baselines(issue)
            for point in result["points"]:
                self.assertEqual(point["models"]["persistence"]["predicted_available_total"], 1000)
                self.assertEqual(point["models"]["drift"]["status"], "UNAVAILABLE")
                self.assertIsNone(point["models"]["pickup"]["predicted_available_total"])
            self.assertEqual(result["scenario_stability"], "UNKNOWN")

    def test_drift_uses_actual_forecast_elapsed_including_staleness(self):
        # Latest is2h old; 24h anchor is26h old. Rise240/24=10places/h.
        issue = make_issue(ages=(50, 26, 14, 2), values=(520, 760, 880, 1000))
        result = model_point(predict_baselines(issue), model="drift")
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["slope_places_per_hour"], 10)
        self.assertEqual(result["elapsed_forecast_hours"], 26)
        self.assertEqual(result["predicted_available_total"], 1260)

    def test_irregular_anchor_uses_real_elapsed_and_exact_six_hour_boundary(self):
        issue = make_issue(ages=(50, 30, 12, 0), values=(500, 700, 900, 1000))
        result = model_point(predict_baselines(issue), model="drift")
        self.assertEqual(result["slope_places_per_hour"], 10)
        self.assertEqual(result["anchor"]["elapsed_hours"], 30)
        bad = make_issue(ages=(50, 30.001, 12, 0), values=(500, 700, 900, 1000))
        self.assertEqual(model_point(predict_baselines(bad), model="drift")["status_reason"], "DRIFT_ANCHOR_INSUFFICIENT")

    def test_drift_hourly_support_uses_latest_per_utc_hour_and_its_span(self):
        # The first true point is discarded by hourlylatest sampling; span<24h.
        issue = make_issue(ages=(24, 23.9, 12, 6, 0))
        drift = model_point(predict_baselines(issue), model="drift")
        self.assertEqual(drift["hourly_point_count"], 4)
        self.assertAlmostEqual(drift["hourly_prefix_span_hours"], 23.9)
        self.assertEqual(drift["status_reason"], "DRIFT_HOURLY_SUPPORT_INSUFFICIENT")

    def test_rising_falling_flat_zero_and_nonnegative_projection(self):
        for values, expected in (((1480, 1250, 1120, 1000), 750),
                                 ((1000, 1000, 1000, 1000), 1000),
                                 ((0, 0, 0, 0), 0),
                                 ((3000, 2500, 2000, 100), 0)):
            # Use24h anchor for exact slopes.
            issue = make_issue(ages=(48, 24, 12, 0), values=values)
            actual = model_point(predict_baselines(issue), model="drift")["predicted_available_total"]
            self.assertAlmostEqual(actual, expected)

    def test_nonfinite_extrapolation_fails_closed_instead_of_serializing_infinity(self):
        issue = make_issue(ages=(48, 24, 12, 0), values=(0, 0, 0, 1e308))
        result = model_point(predict_baselines(issue), horizon=72, model="drift")
        self.assertEqual(result["status_reason"], "NUMERIC_PREDICTION_INVALID")
        self.assertIsNone(result["predicted_available_total"])

    def test_target_at_kickoff_and_failed_issue_never_make_number(self):
        issue = make_issue(days=2)
        points = predict_baselines(issue)["points"]
        self.assertEqual(points[0]["status"], "READY")
        self.assertEqual(points[1]["status"], "TARGET_NOT_BEFORE_KICKOFF")
        self.assertTrue(all(value["predicted_available_total"] is None for value in points[1]["models"].values()))
        failed = make_issue(ages=(7,))
        self.assertEqual(model_point(predict_baselines(failed), model="persistence")["status_reason"], "STALE_INPUT")

    def test_weighted_median_is_equal_event_not_row_or_median_of_medians(self):
        rows = [{"fixture_group": "a", "delta": delta} for delta in (0, 100, 100)]
        rows += [{"fixture_group": "b", "delta": 50}]
        self.assertEqual(event_balanced_median(rows), 50)
        replicated = [r for r in rows if r["fixture_group"] == "b"] + [r for r in rows if r["fixture_group"] == "a"] * 20
        self.assertEqual(event_balanced_median(replicated), 50)
        self.assertEqual(event_balanced_median(list(reversed(rows))), 50)
        self.assertEqual(event_balanced_median([{"fixture_group": "a", "delta": 0},
                                              {"fixture_group": "b", "delta": 100}]), 0)

    def test_two_events_cannot_make_fitted_pickup_lookup(self):
        artifact = fit_pickup([training_row(0), training_row(1)])
        self.assertEqual(artifact["status"], "NO_FIT_INSUFFICIENT_SUPPORT")
        self.assertEqual(artifact["cells"], [])
        prediction = model_point(predict_baselines(make_issue(), artifact))
        self.assertEqual(prediction["status_reason"], "PICKUP_SUPPORT_INSUFFICIENT")

    def test_pickup_cell_and_pooled_routes_are_explicit_and_horizon_specific(self):
        artifact = fit_pickup([training_row(i, delta=-100 - i) for i in range(5)])
        self.assertEqual(artifact["status"], "FIT_SUPPORTED_LOOKUPS")
        matched = model_point(predict_baselines(make_issue(), artifact, fixture_group="future-fixture"))
        self.assertEqual(matched["route"], "MATURITY_CELL")
        self.assertEqual(matched["predicted_available_total"], 898)
        self.assertTrue(matched["maturity_conditioning_used"])
        early = model_point(predict_baselines(make_issue(days=50), artifact, fixture_group="future-fixture"))
        self.assertEqual(early["route"], "POOLED_HORIZON")
        self.assertFalse(early["maturity_conditioning_used"])
        missing = model_point(predict_baselines(make_issue(), artifact, fixture_group="future-fixture"), horizon=72)
        self.assertEqual(missing["status"], "UNAVAILABLE")

    def test_support_gate_five_fixtures_and_three_clubs_is_not_row_count(self):
        self.assertEqual(fit_pickup([training_row(i) for i in range(4)])["status"], "NO_FIT_INSUFFICIENT_SUPPORT")
        rows = [training_row(i) for i in range(5)]
        # Rebuild club metadata consistently while reducing to2clubs.
        for i, row in enumerate(rows):
            event = {**row["issue"]["event"], "club_slug": "club-" + str(i % 2),
                     "observations": row["issue"]["observed_prefix"]}
            row["issue"] = build_issue(event, row["issue"]["issued_at"])
            row["matched_label"]["input_manifest_sha256"] = row["issue"]["input_manifest_sha256"]
        self.assertEqual(fit_pickup(rows)["status"], "NO_FIT_INSUFFICIENT_SUPPORT")

    def test_current_fixture_and_unknown_registry_identity_cannot_use_pickup(self):
        artifact = fit_pickup([training_row(i) for i in range(5)])
        missing = model_point(predict_baselines(make_issue(), artifact))
        self.assertEqual(missing["status_reason"], "INFERENCE_FIXTURE_IDENTITY_UNPROVEN")
        alias = model_point(predict_baselines(make_issue(), artifact, fixture_group="fixture-0"))
        self.assertEqual(alias["status_reason"], "CURRENT_FIXTURE_IN_TRAINING")
        same_event = model_point(predict_baselines(make_issue(event_id=100), artifact, fixture_group="different"))
        self.assertEqual(same_event["status_reason"], "CURRENT_FIXTURE_IN_TRAINING")

    def test_late_unknown_ongoing_duplicate_and_forged_lineage_are_rejected(self):
        row = training_row()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            fit_pickup([row, deepcopy(row)])
        for change in ("late", "ongoing", "identity", "clock", "source"):
            bad = deepcopy(row)
            if change == "late":
                bad["source_lineage"]["label_receipt_known_at"] = "2027-01-01T00:00:00+00:00"
            elif change == "ongoing":
                event = {**bad["issue"]["event"], "kickoff_at": "2027-01-01T00:00:00+00:00",
                         "observations": bad["issue"]["observed_prefix"]}
                bad["issue"] = build_issue(event, TRAIN_ISSUE)
            elif change == "identity":
                bad["source_lineage"]["identity_proven"] = False
            elif change == "clock":
                bad["source_lineage"]["input_receipt_known_at"] = (TRAIN_ISSUE - timedelta(seconds=1)).isoformat()
            elif change == "source":
                bad["source_lineage"]["input_receipt_sha256"] = "not-a-hash"
            with self.subTest(change=change), self.assertRaises(ValueError):
                fit_pickup([bad])

    def test_one_event_cannot_inflate_independent_groups(self):
        one = training_row()
        other = training_row(0, issued=TRAIN_ISSUE + timedelta(hours=1))
        other["fixture_group"] = "new-fake-fixture"
        with self.assertRaisesRegex(ValueError, "inflate independent"):
            fit_pickup([one, other])

    def test_label_payload_tamper_rejected_even_with_recomputed_label_hash(self):
        bad = training_row()
        bad["matched_label"]["label"]["target_staleness_hours"] = 5
        bad["matched_label"]["label_sha256"] = _hash(bad["matched_label"]["label"])
        with self.assertRaisesRegex(ValueError, "statistics"):
            fit_pickup([bad])
        bad = training_row()
        bad["matched_label"]["label"]["available_total"] = 0
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            fit_pickup([bad])

    def test_maturity_boundaries_source_mismatch_and_artifact_tamper(self):
        for days, cell in ((2.999, 0), (3, 3), (7, 7), (15, 15), (30, 30), (50, 50)):
            self.assertEqual(maturity_cell(days * 24), cell)
        artifact = fit_pickup([training_row(i) for i in range(5)])
        stellis = make_issue(family="public-displayed-available-total-v1:stellis/stellis_visible_available")
        self.assertEqual(model_point(predict_baselines(stellis, artifact, fixture_group="future"))["status"], "UNAVAILABLE")
        bad = deepcopy(artifact); bad["cells"][0]["median_delta"] = 999
        with self.assertRaisesRegex(ValueError, "hash/version"):
            predict_baselines(make_issue(), bad, fixture_group="future")

    def test_old_inference_cannot_use_later_frozen_artifact(self):
        artifact = fit_pickup([training_row(i) for i in range(5)])
        old = make_issue(issued=TRAIN_ISSUE, days=50)
        self.assertEqual(model_point(predict_baselines(old, artifact, fixture_group="future"))["status_reason"],
                         "PICKUP_ARTIFACT_NOT_KNOWN_AS_OF")

    def test_inputs_unchanged_and_arbitrary_fit_cutoff_refused(self):
        rows = [training_row(i) for i in range(5)]
        before = deepcopy(rows)
        artifact = fit_pickup(rows)
        issue = make_issue()
        old_issue = deepcopy(issue)
        predict_baselines(issue, artifact, fixture_group="future")
        self.assertEqual(rows, before)
        self.assertEqual(issue, old_issue)
        with self.assertRaisesRegex(ValueError, "cutoff"):
            validated_training_rows(rows, "2027-01-01T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
