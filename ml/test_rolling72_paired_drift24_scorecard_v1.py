import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

from ml.rolling72_paired_drift24_scorecard_v1 import analyze


MODULE = Path(__file__).with_name("rolling72_paired_drift24_scorecard_v1.py")


def rows_for(events=30, clubs=8, horizons=(24, 48, 72)):
    rows = []
    bundle = 1
    for event in range(1, events + 1):
        club = f"club-{((event - 1) % clubs) + 1}"
        for horizon in horizons:
            # A simple fixed synthetic fixture: drift beats PERS by two seats.
            rows.append({
                "bundle_id": bundle,
                "ticket_event_id": event,
                "club_id": club,
                "horizon_hours": horizon,
                "actual": 100,
                "pers_prediction": 110,
                "drift24_prediction": 108,
            })
            bundle += 1
    return rows


class ScorecardTests(unittest.TestCase):
    def test_unequal_event_sizes_are_event_balanced(self):
        facts = [
            {"bundle_id": 1, "ticket_event_id": 1, "club_id": "a", "horizon_hours": 24,
             "actual": 0, "pers_prediction": 10, "drift24_prediction": 8},
            {"bundle_id": 2, "ticket_event_id": 1, "club_id": "a", "horizon_hours": 24,
             "actual": 0, "pers_prediction": 10, "drift24_prediction": 8},
            {"bundle_id": 3, "ticket_event_id": 2, "club_id": "b", "horizon_hours": 24,
             "actual": 0, "pers_prediction": 0, "drift24_prediction": 0},
        ]
        result = analyze(facts)
        metric = result["horizons"]["24"]
        self.assertEqual(metric["accepted_shared_labels"], 3)
        self.assertEqual(metric["pers"]["event_balanced_mae"], 5)
        self.assertEqual(metric["drift24"]["event_balanced_mae"], 4)
        self.assertNotEqual(metric["pers"]["event_balanced_mae"], 20 / 3)
        self.assertEqual(metric["pers"]["event_balanced_bias"], 5)
        self.assertEqual(metric["pers"]["event_mae_p90"], 9)
        self.assertEqual(metric["pers"]["event_mae_p90_quantile_method"], "linear")
        self.assertEqual(metric["pers"]["worst_event_mae"], 10)

    def test_supported_requires_floor_primary_ci_and_guardrails(self):
        result = analyze(rows_for())
        self.assertEqual(result["decision"], "SUPPORTED")
        self.assertEqual(result["support"]["accepted_event_count"], 30)
        self.assertEqual(result["support"]["club_count"], 8)
        primary = result["primary_72h"]
        self.assertEqual(primary["relative_reduction"], 0.2)
        self.assertEqual(primary["bootstrap_95_percentile_interval"]["draws"], 10_000)
        self.assertEqual(primary["bootstrap_95_percentile_interval"]["seed"], 42)
        self.assertLess(primary["bootstrap_95_percentile_interval"]["upper"], 0)
        self.assertTrue(primary["guardrails_pass"])
        self.assertEqual(result["coverage"]["status"], "UNKNOWN")
        self.assertIsNone(result["coverage"]["forecast_coverage"])
        self.assertIsNone(result["coverage"]["scoring_coverage"])

    def test_bootstrap_is_fixed_and_uses_events(self):
        facts = rows_for()
        for row in facts:
            if row["horizon_hours"] == 72:
                row["drift24_prediction"] = 108 + (row["ticket_event_id"] % 5)
        left = analyze(facts)["primary_72h"]["bootstrap_95_percentile_interval"]
        right = analyze(facts)["primary_72h"]["bootstrap_95_percentile_interval"]
        self.assertEqual(left, right)
        self.assertEqual(left["resampling_unit"], "ticket_event_id")
        self.assertEqual(left["draws"], 10_000)
        self.assertTrue(math.isfinite(left["lower"]))
        self.assertTrue(math.isfinite(left["upper"]))

    def test_below_event_or_club_floor_is_partial(self):
        self.assertEqual(analyze(rows_for(events=29))["decision"], "PARTIAL")
        self.assertEqual(analyze(rows_for(events=30, clubs=7))["decision"], "PARTIAL")

    def test_empty_or_missing_horizons_are_unknown_with_null_metrics(self):
        empty = analyze([])
        self.assertEqual(empty["decision"], "UNKNOWN")
        self.assertEqual(empty["primary_72h"]["bootstrap_95_percentile_interval"], None)
        self.assertEqual(empty["horizons"], {"24": None, "48": None, "72": None})
        self.assertEqual(analyze(rows_for(horizons=(72,)))["decision"], "UNKNOWN")
        self.assertEqual(analyze(rows_for(horizons=(24, 72)))["decision"], "UNKNOWN")

    def test_supported_cohort_failing_primary_is_not_supported(self):
        facts = rows_for()
        for row in facts:
            if row["horizon_hours"] == 72:
                row["drift24_prediction"] = 112
        result = analyze(facts)
        self.assertEqual(result["decision"], "NOT_SUPPORTED")
        self.assertGreater(result["primary_72h"]["delta_drift24_minus_pers"], 0)

    def test_supported_cohort_failing_either_guardrail_is_not_supported(self):
        facts = rows_for()
        for row in facts:
            if row["horizon_hours"] == 24:
                row["drift24_prediction"] = 111
        result = analyze(facts)
        self.assertEqual(result["decision"], "NOT_SUPPORTED")
        self.assertFalse(result["primary_72h"]["guardrails_pass"])

    def test_duplicate_bundle_horizon_and_inconsistent_identity_rejected(self):
        base = rows_for(events=1, clubs=1)
        duplicate = base + [dict(base[0])]
        with self.assertRaisesRegex(ValueError, "duplicate bundle_id/horizon"):
            analyze(duplicate)
        wrong_club = [dict(row) for row in base]
        wrong_club[1]["club_id"] = "different"
        with self.assertRaisesRegex(ValueError, "more than one club"):
            analyze(wrong_club)
        wrong_event = [dict(row) for row in base]
        wrong_event[1]["ticket_event_id"] = 2
        wrong_event[1]["bundle_id"] = wrong_event[0]["bundle_id"]
        with self.assertRaisesRegex(ValueError, "more than one ticket_event_id"):
            analyze(wrong_event)

    def test_invalid_horizons_numbers_and_identifiers_rejected(self):
        base = rows_for(events=1, clubs=1)
        for field, value in (("horizon_hours", True), ("horizon_hours", 12),
                             ("actual", True), ("actual", -1), ("actual", math.inf),
                             ("pers_prediction", math.nan), ("drift24_prediction", -0.1),
                             ("bundle_id", False), ("ticket_event_id", 0), ("club_id", " ")):
            candidate = [dict(row) for row in base]
            candidate[0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                analyze(candidate)

    def test_cli_reads_json_and_emits_machine_readable_unknown(self):
        completed = subprocess.run(
            [sys.executable, str(MODULE)], input=json.dumps({"rows": []}),
            text=True, capture_output=True, check=True,
        )
        output = json.loads(completed.stdout)
        self.assertEqual(output["decision"], "UNKNOWN")
        self.assertIsNone(output["horizons"]["72"])
        self.assertEqual(completed.stderr, "")


if __name__ == "__main__":
    unittest.main()
