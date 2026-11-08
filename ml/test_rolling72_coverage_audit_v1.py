"""Semantic leakage/missingness tests for the read-only coverage audit."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from ml.demand_engine.daily_inventory_path_dataset_v1 import canonical_hash
from ml.rolling72_coverage_audit_v1 import audit_cache, audit_export, maturity_bucket


BASE = datetime(2026, 9, 1, tzinfo=timezone.utc)


def observation(hours, value=100, key="provider/source", **extra):
    return {"snapshot_id": int(hours * 1000) + 1,
            "captured_at": (BASE + timedelta(hours=hours)).isoformat(),
            "available_total": value, "measurement_key": key, **extra}


def export(rows, kickoff_days=10, export_hours=120):
    data = {"version": "daily-inventory-public-export-v1",
            "exported_at": (BASE + timedelta(hours=export_hours)).isoformat(),
            "retrieved_at": (BASE + timedelta(hours=export_hours)).isoformat(),
            "events": [{"ticket_event_id": 1, "club_slug": "club",
                        "kickoff_at": (BASE + timedelta(days=kickoff_days)).isoformat(),
                        "observations": rows}]}
    data["export_sha256"] = canonical_hash(data)
    return data


class CoverageAuditTests(unittest.TestCase):
    def test_maturity_boundaries(self):
        for days, expected in [(50, "P50plus"), (49.99, "P30_to_P50"),
                               (30, "P30_to_P50"), (15, "P15_to_P30"),
                               (7, "P7_to_P15"), (3, "P3_to_P7"), (0, "P0_to_P3")]:
            self.assertEqual(maturity_bucket(days), expected)

    def test_first_observation_is_kept_when_same_hour_has_later_point(self):
        result = audit_export(export([observation(0), observation(.5), observation(24), observation(48), observation(72)]))
        self.assertEqual(result["first_observation_target_support"]["72"]["matched"], 1)
        self.assertGreater(result["prefix_age_horizon_matrix"]["first_or_under1h/+72h"]["issues"], 1)
        self.assertFalse(result["historical_ingestion_known_at_proven"])

    def test_exact_six_hour_boundary_and_no_interpolation(self):
        accepted = audit_export(export([observation(0), observation(18)]))
        rejected = audit_export(export([observation(0), observation(17.999)]))
        future_only = audit_export(export([observation(0), observation(24.001)]))
        self.assertEqual(accepted["first_observation_target_support"]["24"]["matched"], 1)
        self.assertEqual(rejected["first_observation_target_support"]["24"]["matched"], 0)
        self.assertEqual(future_only["first_observation_target_support"]["24"]["matched"], 0)

    def test_kickoff_is_not_a_future_inventory_target(self):
        result = audit_export(export([observation(0), observation(24), observation(48), observation(72)], kickoff_days=3))
        self.assertEqual(result["first_observation_target_support"]["72"]["past_kickoff"], 1)
        self.assertEqual(result["first_observation_target_support"]["72"]["matched"], 0)

    def test_source_change_blocks_later_prefix_and_mismatched_target(self):
        result = audit_export(export([observation(0), observation(24, key="other"), observation(48, key="other")]))
        self.assertEqual(result["events_with_measurement_changes"], 1)
        self.assertEqual(result["first_observation_target_support"]["24"]["matched"], 0)
        self.assertEqual(result["maturity_horizon_matrix"]["P7_to_P15/+24h"]["source_changed_prefix"], 2)

    def test_literal_zero_is_valid_missing_value_is_not(self):
        zero = audit_export(export([observation(0, 0), observation(24, 0)]))
        missing = audit_export(export([observation(0, None), observation(24)]))
        self.assertEqual(zero["literal_zero_rows"], 2)
        self.assertEqual(zero["first_observation_target_support"]["24"]["matched"], 1)
        self.assertEqual(missing["first_observation_target_support"]["24"]["invalid_prefix"], 1)

    def test_explicit_hidden_source_fails_closed_unknown_remains_unknown(self):
        hidden = audit_export(export([observation(0, source_visible=False), observation(24)]))
        self.assertEqual(hidden["first_observation_target_support"]["24"]["hidden_prefix"], 1)
        self.assertEqual(hidden["source_flag_counts"]["source_visible/None"], 1)

    def test_pending_target_is_not_missing_or_clipped(self):
        result = audit_export(export([observation(0)], export_hours=12))
        self.assertEqual(result["first_observation_target_support"]["24"]["pending"], 1)
        self.assertEqual(result["first_observation_target_support"]["24"]["mature"], 0)

    def test_input_hash_and_file_receipt(self):
        data = export([observation(0)])
        corrupted = deepcopy(data)
        corrupted["events"][0]["observations"][0]["available_total"] = 99
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            audit_export(corrupted)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.json"
            payload = json.dumps(data).encode()
            path.write_bytes(payload)
            result = audit_cache(path)
            self.assertEqual(result["source_file_sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(result["rows_with_sector_payload_fields"], 0)

    def test_future_capture_cannot_enter_export(self):
        with self.assertRaisesRegex(ValueError, "cutoff"):
            audit_export(export([observation(24)], export_hours=12))

    def test_conflicting_ids_cannot_multiply_historical_support(self):
        first = observation(0)
        conflict = {**observation(24), "snapshot_id": first["snapshot_id"]}
        with self.assertRaisesRegex(ValueError, "Duplicate snapshot"):
            audit_export(export([first, conflict]))

    def test_receipt_clock_cannot_precede_export_cutoff(self):
        data = export([observation(0)])
        data["retrieved_at"] = BASE.isoformat()
        data["export_sha256"] = canonical_hash({key: value for key, value in data.items()
                                                if key != "export_sha256"})
        with self.assertRaisesRegex(ValueError, "receipt"):
            audit_export(data)


if __name__ == "__main__":
    unittest.main()
