"""Offline, privacy-conscious validator for Rolling72 club-pilot metric JSONL.

This module validates local aggregate feed text only.  It performs no network
access and writes no files.  Error messages deliberately contain line numbers,
field names, and fixed reason codes only; they never echo row values.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import re
from typing import Any


SCHEMA_VERSION = "rolling72-club-pilot-v1"
REQUIRED_FIELDS = frozenset({
    "schema_version", "club_id", "event_id", "kickoff_at", "source_id",
    "metric_family", "bucket_start_at", "bucket_end_at", "measure",
    "value", "unit", "value_status", "known_at", "revision",
    "source_record_ref",
})
OPTIONAL_FIELDS = frozenset({"pool_id"})
ALLOWED_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS

# This is intentionally limited to the five operational metric families. The
# separate final-attendance target requires an authoritative reconciliation
# status that is not representable in this metric-row schema, so it is rejected.
MEASURE_UNITS: dict[tuple[str, str], str] = {
    ("ticket_sales", "gross_sold_delta"): "tickets",
    ("ticket_sales", "net_sold_delta"): "tickets",
    ("ticket_sales", "gross_sold_cumulative"): "tickets",
    ("ticket_sales", "net_sold_cumulative"): "tickets",
    ("refunds", "refund_delta"): "tickets",
    ("inventory_pool", "available_pool_snapshot"): "tickets",
    ("inventory_pool", "pool_delta"): "tickets",
    ("season_membership", "member_entitlement_snapshot"): "tickets",
    ("season_membership", "member_reservation_delta"): "tickets",
    ("entry_scans", "scan_accepted_delta"): "scans",
    ("entry_scans", "scan_rejected_delta"): "scans",
    ("entry_scans", "scan_reversed_delta"): "scans",
}
SIGNED_MEASURES = frozenset({"pool_delta", "net_sold_delta"})
CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
RFC3339_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$"
)


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    row_count: int
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "row_count": self.row_count, "errors": list(self.errors)}


def _error(errors: list[str], line: int, code: str, field: str | None = None) -> None:
    # Never include caller-controlled values in diagnostics.
    suffix = f":{field}" if field else ""
    errors.append(f"line_{line}:{code}{suffix}")


def _reject_constant(_value: str) -> None:
    raise ValueError("nonstandard_json_number")


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate_json_key")
        out[key] = value
    return out


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not RFC3339_UTC_RE.fullmatch(value):
        return None
    # RFC 3339 UTC: require an explicit UTC marker; reject naive and non-UTC
    # offsets instead of silently normalizing local civil time.
    if not (value.endswith("Z") or value.endswith("+00:00")):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except (ValueError, OverflowError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed.astimezone(timezone.utc)


def _code(value: Any) -> bool:
    return isinstance(value, str) and CODE_RE.fullmatch(value) is not None


def validate_jsonl_text(text: str) -> ValidationReport:
    """Validate JSONL rows and cross-row scope/revision rules in memory.

    Blank input, including whitespace-only input, is invalid. Blank lines inside
    a feed are invalid as well. Error strings are safe to display or persist.
    """
    errors: list[str] = []
    if not isinstance(text, str):
        return ValidationReport(False, 0, ("line_0:input_not_text",))
    if not text.strip():
        return ValidationReport(False, 0, ("line_0:empty_feed",))

    rows: list[tuple[int, dict[str, Any], dict[str, datetime]]] = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            _error(errors, line_no, "blank_line")
            continue
        try:
            row = json.loads(raw, object_pairs_hook=_pairs_no_duplicates,
                             parse_constant=_reject_constant)
        except (json.JSONDecodeError, ValueError, TypeError):
            _error(errors, line_no, "invalid_json")
            continue
        if not isinstance(row, dict):
            _error(errors, line_no, "row_not_object")
            continue
        missing = REQUIRED_FIELDS - row.keys()
        extra = row.keys() - ALLOWED_FIELDS
        for field in sorted(missing):
            _error(errors, line_no, "missing_field", field)
        for field in sorted(extra):
            # Field names are under caller control too. Keep unknown-key
            # diagnostics generic to avoid echoing PII-like keys.
            _error(errors, line_no, "unknown_field")
        if missing or extra:
            continue

        row_times: dict[str, datetime] = {}
        for field in ("kickoff_at", "bucket_start_at", "bucket_end_at", "known_at"):
            parsed = _timestamp(row[field])
            if parsed is None:
                _error(errors, line_no, "invalid_utc_timestamp", field)
            else:
                row_times[field] = parsed
        if len(row_times) != 4:
            continue
        if row_times["bucket_end_at"] <= row_times["bucket_start_at"]:
            _error(errors, line_no, "invalid_bucket_interval", "bucket_end_at")
        if row["schema_version"] != SCHEMA_VERSION:
            _error(errors, line_no, "unsupported_schema", "schema_version")
        for field in ("club_id", "event_id", "source_id", "source_record_ref"):
            if not _code(row[field]):
                _error(errors, line_no, "invalid_code", field)
        if "pool_id" in row and not _code(row["pool_id"]):
            _error(errors, line_no, "invalid_code", "pool_id")

        family, measure = row["metric_family"], row["measure"]
        if family == "final_attendance" or measure == "final_attendance":
            _error(errors, line_no, "final_attendance_requires_reconciled_target_record", "metric_family")
        expected_unit = MEASURE_UNITS.get((family, measure)) if (
            isinstance(family, str) and isinstance(measure, str)
        ) else None
        if expected_unit is None:
            _error(errors, line_no, "unsupported_measure", "measure")
        elif row["unit"] != expected_unit:
            _error(errors, line_no, "unit_mismatch", "unit")
        if family == "inventory_pool" and "pool_id" not in row:
            _error(errors, line_no, "missing_field", "pool_id")
        elif family != "inventory_pool" and "pool_id" in row:
            _error(errors, line_no, "pool_id_requires_inventory", "pool_id")

        status, value = row["value_status"], row["value"]
        if not isinstance(status, str) or status not in {"observed", "unknown", "not_applicable"}:
            _error(errors, line_no, "invalid_value_status", "value_status")
        elif status == "observed":
            if row_times["known_at"] < row_times["bucket_end_at"]:
                _error(errors, line_no, "known_before_bucket_closed", "known_at")
            if isinstance(value, bool) or not isinstance(value, int):
                _error(errors, line_no, "observed_value_not_integer", "value")
            elif (not isinstance(measure, str) or measure not in SIGNED_MEASURES) and value < 0:
                _error(errors, line_no, "negative_value", "value")
        elif value is not None:
            _error(errors, line_no, "non_observed_value_must_be_null", "value")

        revision = row["revision"]
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            _error(errors, line_no, "invalid_revision", "revision")
        rows.append((line_no, row, row_times))

    # Revisions are append-only for each exact source/event/measure/bucket.
    # Distinct intervals within a source/event/measure/pool series may not
    # overlap; repeated identical intervals are allowed only as revisions.
    buckets: dict[tuple[Any, ...], list[tuple[int, int, datetime]]] = {}
    series: dict[tuple[Any, ...], list[tuple[int, datetime, datetime, tuple[Any, ...]]]] = {}
    for line_no, row, times in rows:
        group_values = (row.get("club_id"), row.get("event_id"), row.get("source_id"),
                        row.get("metric_family"), row.get("measure"))
        if (not all(isinstance(v, str) for v in group_values)
                or ("pool_id" in row and not isinstance(row.get("pool_id"), str))):
            continue
        series_key = group_values + (row.get("pool_id"),)
        bucket_key = series_key + (times["bucket_start_at"], times["bucket_end_at"])
        revision = row.get("revision")
        if isinstance(revision, int) and not isinstance(revision, bool):
            buckets.setdefault(bucket_key, []).append((revision, line_no, times["known_at"]))
        series.setdefault(series_key, []).append((line_no, times["bucket_start_at"],
                                                   times["bucket_end_at"], bucket_key))
    for versions in buckets.values():
        ordered = sorted(versions, key=lambda item: (item[0], item[1]))
        prior_revision = 0
        prior_known: datetime | None = None
        seen_revisions: set[int] = set()
        for revision, line_no, known_at in ordered:
            if revision in seen_revisions or revision <= prior_revision:
                _error(errors, line_no, "revision_not_strictly_increasing", "revision")
            if prior_known is not None and known_at < prior_known:
                _error(errors, line_no, "revision_known_at_regressed", "known_at")
            seen_revisions.add(revision)
            prior_revision, prior_known = max(prior_revision, revision), known_at
    for intervals in series.values():
        intervals.sort(key=lambda item: (item[1], item[2], item[0]))
        previous_end: datetime | None = None
        previous_bucket: tuple[Any, ...] | None = None
        for line_no, start, end, bucket_key in intervals:
            if bucket_key == previous_bucket:
                previous_end = max(previous_end or end, end)
                continue
            if previous_end is not None and start < previous_end:
                _error(errors, line_no, "overlapping_bucket_intervals", "bucket_start_at")
            previous_end, previous_bucket = max(previous_end or end, end), bucket_key

    return ValidationReport(not errors, len(rows), tuple(errors))


def validate_jsonl_file(path: str | Path) -> ValidationReport:
    """Read a caller-selected local UTF-8 JSONL file and validate it."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ValidationReport(False, 0, ("line_0:unreadable_input",))
    return validate_jsonl_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="local aggregate feed JSONL file")
    args = parser.parse_args(argv)
    report = validate_jsonl_file(args.jsonl)
    print(json.dumps(report.as_dict(), sort_keys=True))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
