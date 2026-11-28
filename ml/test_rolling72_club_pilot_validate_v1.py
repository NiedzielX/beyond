"""Substantive offline tests for the privacy-safe club aggregate feed validator."""
from __future__ import annotations

from copy import deepcopy
import json
import unittest

from ml.rolling72_club_pilot_validate_v1 import (
    validate_jsonl_file,
    validate_jsonl_text,
)


def row(**changes):
    value = {
        "schema_version": "rolling72-club-pilot-v1",
        "club_id": "club-17",
        "event_id": "event-901",
        "kickoff_at": "2026-12-05T18:00:00Z",
        "source_id": "ticketing-a",
        "metric_family": "ticket_sales",
        "bucket_start_at": "2026-12-01T10:00:00Z",
        "bucket_end_at": "2026-12-01T11:00:00Z",
        "measure": "net_sold_delta",
        "value": 12,
        "unit": "tickets",
        "value_status": "observed",
        "known_at": "2026-12-01T11:02:00Z",
        "revision": 1,
        "source_record_ref": "batch-44-row-9",
    }
    value.update(changes)
    return value


def feed(*rows):
    return "\n".join(json.dumps(value, separators=(",", ":")) for value in rows) + "\n"


class ClubPilotValidatorTests(unittest.TestCase):
    def test_accepts_valid_sales_and_all_declared_family_measure_units(self):
        cases = [
            ("ticket_sales", "gross_sold_delta", "tickets"),
            ("ticket_sales", "gross_sold_cumulative", "tickets"),
            ("ticket_sales", "net_sold_cumulative", "tickets"),
            ("refunds", "refund_delta", "tickets"),
            ("inventory_pool", "available_pool_snapshot", "tickets"),
            ("inventory_pool", "pool_delta", "tickets"),
            ("season_membership", "member_entitlement_snapshot", "tickets"),
            ("season_membership", "member_reservation_delta", "tickets"),
            ("entry_scans", "scan_accepted_delta", "scans"),
            ("entry_scans", "scan_rejected_delta", "scans"),
            ("entry_scans", "scan_reversed_delta", "scans"),
        ]
        rows = []
        for i, (family, measure, unit) in enumerate(cases):
            changes = {
                "metric_family": family, "measure": measure, "unit": unit,
                "bucket_start_at": f"2026-12-01T{i:02d}:00:00+00:00",
                "bucket_end_at": f"2026-12-01T{i + 1:02d}:00:00+00:00",
                "known_at": f"2026-12-01T{i + 1:02d}:02:00Z",
                "value": -3 if measure in {"net_sold_delta", "pool_delta"} else 3,
            }
            if family == "inventory_pool":
                changes["pool_id"] = "north"
            rows.append(row(**changes))
        result = validate_jsonl_text(feed(*rows))
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.row_count, len(cases))

    def test_preserves_unknown_and_not_applicable_as_null_and_observed_zero(self):
        rows = [
            row(value=0),
            row(value=None, value_status="unknown", revision=2,
                known_at="2026-12-01T11:03:00Z"),
            row(value=None, value_status="not_applicable", revision=3,
                known_at="2026-12-01T11:04:00Z"),
        ]
        result = validate_jsonl_text(feed(*rows))
        self.assertTrue(result.ok, result.errors)

    def test_empty_and_whitespace_only_feed_rejected(self):
        for text in ("", " \t\n"):
            result = validate_jsonl_text(text)
            self.assertFalse(result.ok)
            self.assertEqual(result.row_count, 0)
            self.assertEqual(result.errors, ("line_0:empty_feed",))

    def test_rejects_missing_extra_and_duplicate_keys_without_echoing_values(self):
        raw = json.dumps(row())
        missing = row()
        del missing["event_id"]
        extra = row()
        extra["email"] = "person@example.invalid"
        duplicate = raw[:-1] + ',"club_id":"person@example.invalid"}'
        result = validate_jsonl_text(feed(missing, extra) + duplicate + "\n")
        self.assertFalse(result.ok)
        joined = " ".join(result.errors)
        self.assertIn("missing_field:event_id", joined)
        self.assertIn("unknown_field", joined)
        self.assertIn("invalid_json", joined)
        self.assertNotIn("person@example.invalid", joined)
        self.assertNotIn("event-901", joined)

    def test_rejects_non_utc_or_invalid_time_and_non_positive_bucket(self):
        for changes, expected in [
            ({"known_at": "2026-12-01T11:02:00"}, "invalid_utc_timestamp:known_at"),
            ({"known_at": "2026-12-01 11:02:00Z"}, "invalid_utc_timestamp:known_at"),
            ({"bucket_start_at": "2026-12-01T12:00:00Z"}, "invalid_bucket_interval"),
            ({"kickoff_at": "not a timestamp"}, "invalid_utc_timestamp:kickoff_at"),
            ({"known_at": "2026-12-01T12:02:00+01:00"}, "invalid_utc_timestamp:known_at"),
            ({"known_at": "2026-12-01T10:59:59Z"}, "known_before_bucket_closed:known_at"),
        ]:
            result = validate_jsonl_text(feed(row(**changes)))
            self.assertFalse(result.ok)
            self.assertTrue(any(expected in error for error in result.errors), result.errors)

    def test_rejects_family_measure_unit_and_value_contract_violations(self):
        cases = [
            (row(measure="made_up"), "unsupported_measure"),
            (row(unit="scans"), "unit_mismatch"),
            (row(value=-1, measure="gross_sold_delta"), "negative_value"),
            (row(value=True), "observed_value_not_integer"),
            (row(value=2.5), "observed_value_not_integer"),
            (row(value=0, value_status="unknown"), "non_observed_value_must_be_null"),
            (row(value=None, value_status="observed"), "observed_value_not_integer"),
            (row(revision=True), "invalid_revision"),
            (row(revision=0), "invalid_revision"),
            (row(pool_id="sales-partition"), "pool_id_requires_inventory"),
        ]
        for bad, reason in cases:
            result = validate_jsonl_text(feed(bad))
            self.assertFalse(result.ok)
            self.assertTrue(any(reason in error for error in result.errors), result.errors)

    def test_final_attendance_requires_a_separate_reconciled_target_record(self):
        bad = row(metric_family="final_attendance", measure="final_attendance", unit="people")
        result = validate_jsonl_text(feed(bad))
        self.assertFalse(result.ok)
        self.assertTrue(any("final_attendance_requires_reconciled_target_record" in e
                            for e in result.errors))

    def test_inventory_pool_requires_pool_code(self):
        invalid = row(metric_family="inventory_pool", measure="pool_delta")
        result = validate_jsonl_text(feed(invalid))
        self.assertTrue(any("missing_field:pool_id" in error for error in result.errors))
        valid = row(metric_family="inventory_pool", measure="pool_delta", pool_id="north")
        self.assertTrue(validate_jsonl_text(feed(valid)).ok)

    def test_rejects_overlapping_intervals_in_same_series_but_not_other_series(self):
        first = row()
        overlap = row(bucket_start_at="2026-12-01T10:30:00Z",
                      bucket_end_at="2026-12-01T11:30:00Z")
        isolated_source = row(source_id="ticketing-b",
                              bucket_start_at="2026-12-01T10:30:00Z",
                              bucket_end_at="2026-12-01T11:30:00Z")
        result = validate_jsonl_text(feed(first, overlap, isolated_source))
        self.assertFalse(result.ok)
        self.assertEqual(sum("overlapping_bucket_intervals" in e for e in result.errors), 1)

    def test_identical_bucket_revisions_are_allowed_only_in_known_time_order(self):
        first = row()
        second = row(revision=2, value=13, known_at="2026-12-01T11:03:00Z")
        self.assertTrue(validate_jsonl_text(feed(first, second)).ok)
        duplicate_revision = row(revision=1, value=13, known_at="2026-12-01T11:03:00Z")
        bad = validate_jsonl_text(feed(first, duplicate_revision))
        self.assertTrue(any("revision_not_strictly_increasing" in e for e in bad.errors))
        reversed_clock = row(revision=2, value=13, known_at="2026-12-01T11:01:00Z")
        bad = validate_jsonl_text(feed(first, reversed_clock))
        self.assertTrue(any("revision_known_at_regressed" in e for e in bad.errors))

    def test_local_file_api_does_not_expose_path_or_contents_in_read_error(self):
        result = validate_jsonl_file("/definitely/not/a/real/personal@example.invalid.jsonl")
        self.assertFalse(result.ok)
        self.assertEqual(result.errors, ("line_0:unreadable_input",))

    def test_duplicate_json_key_and_nonstandard_nan_are_rejected(self):
        duplicate = json.dumps(row())[:-1] + ',"value":42}'
        nan_row = row(value=float("nan"))
        text = duplicate + "\n" + json.dumps(nan_row) + "\n"
        result = validate_jsonl_text(text)
        self.assertFalse(result.ok)
        self.assertEqual(result.errors, ("line_1:invalid_json", "line_2:invalid_json"))


if __name__ == "__main__":
    unittest.main()
