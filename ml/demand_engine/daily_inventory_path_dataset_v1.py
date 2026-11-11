"""PIT-safe public-inventory prefixes and genuine future daily targets.

This is a separate research contract from terminal-attendance trajectory v1.
It never fills missing days, synthesizes inventory or changes existing ledgers.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from numbers import Real
from typing import Any


DATASET_VERSION = "daily-inventory-path-dataset-v1"
MAX_CONTEXT_DAYS = 60
MIN_OBSERVATIONS = 4
MIN_SPAN_HOURS = 24.0
MAX_STALENESS_HOURS = 6.0
UTC = timezone.utc


def parse_timestamp(value: str | datetime) -> datetime:
    """Parse an aware timestamp and normalize it to UTC; naive times fail closed."""
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("Timestamp must be an ISO string or datetime")
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timezone-aware timestamp required")
    return result.astimezone(UTC)


def utc_iso(value: str | datetime) -> str:
    return parse_timestamp(value).isoformat()


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def issue_manifest(issue: dict) -> dict:
    """Return the exact public preimage of an issue's input manifest hash."""
    return {
        key: issue[key]
        for key in (
            "dataset_version", "ticket_event_id", "club_slug", "kickoff_at",
            "issued_as_of_at", "days_to_event", "measurement_key",
            "prefix_sha256", "status", "status_reason", "rejected_snapshot_ids",
        )
    }


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a positive integer")
    if isinstance(value, int) and value > 0:
        return value
    # REST clients occasionally preserve integer identifiers as strings.
    if isinstance(value, str) and value.isdecimal() and int(value) > 0:
        return int(value)
    raise ValueError(f"{name} must be a positive integer")


def _timed_observations(event: dict) -> list[tuple[datetime, dict]]:
    observations = event.get("observations", [])
    if not isinstance(observations, list):
        raise ValueError("observations must be a list")
    timed = []
    for row in observations:
        if not isinstance(row, dict):
            raise ValueError("Each observation must be an object")
        timed.append((parse_timestamp(row.get("captured_at")), row))
    return sorted(timed, key=lambda pair: pair[0])


def _deduplicate_timestamps(
    timed: list[tuple[datetime, dict]],
) -> list[tuple[datetime, dict]]:
    by_timestamp: dict[datetime, tuple[int, dict]] = {}
    by_snapshot_id: dict[int, tuple[datetime, dict]] = {}
    for captured, row in timed:
        snapshot_id = _positive_integer(row.get("snapshot_id"), "snapshot_id")
        previous_identity = by_snapshot_id.get(snapshot_id)
        if previous_identity is not None and previous_identity != (captured, row):
            raise ValueError("Conflicting observation payloads for identical snapshot identity")
        by_snapshot_id[snapshot_id] = captured, row
        previous = by_timestamp.get(captured)
        if previous is None or snapshot_id > previous[0]:
            by_timestamp[captured] = snapshot_id, row
        elif snapshot_id == previous[0] and row != previous[1]:
            raise ValueError("Conflicting observation payloads for identical snapshot identity")
    return [(t, pair[1]) for t, pair in sorted(by_timestamp.items())]


def _normalize_observation(captured: datetime, row: dict) -> dict:
    snapshot_id = _positive_integer(row.get("snapshot_id"), "snapshot_id")
    value = row.get("available_total")
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("available_total must be a finite nonnegative number")
    try:
        numeric = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError("available_total must be finite") from exc
    if not math.isfinite(numeric) or numeric < 0:
        raise ValueError("available_total must be a finite nonnegative number")
    measurement_key = row.get("measurement_key")
    if not isinstance(measurement_key, str) or not measurement_key.strip():
        raise ValueError("Explicit measurement_key is required")
    result = {
        "snapshot_id": snapshot_id,
        "captured_at": captured.isoformat(),
        "available_total": numeric,
        "measurement_key": measurement_key.strip(),
    }
    for name in ("source_active", "source_visible"):
        if name in row:
            flag = row[name]
            if flag is not None and not isinstance(flag, bool):
                raise ValueError(f"{name} must be a boolean or null")
            result[name] = flag
    return result


def _finish(issue: dict, status: str, reason: str | None = None) -> dict:
    issue["status"] = status
    issue["status_reason"] = reason
    issue["prefix_sha256"] = canonical_hash(issue["observed_prefix"])
    issue["input_manifest_sha256"] = canonical_hash(issue_manifest(issue))
    return issue


def _build_issue(
    event: dict,
    issued_as_of_at: str | datetime,
    timed: list[tuple[datetime, dict]] | None,
    preparation_error: str | None = None,
) -> dict:
    ticket_event_id = _positive_integer(event.get("ticket_event_id"), "ticket_event_id")
    club_slug = event.get("club_slug")
    if not isinstance(club_slug, str) or not club_slug.strip():
        raise ValueError("Nonempty club_slug required")
    kickoff = parse_timestamp(event.get("kickoff_at"))
    issued = parse_timestamp(issued_as_of_at)
    days_float = (kickoff - issued).total_seconds() / 86400.0
    rounded = round(days_float)
    days = int(rounded) if abs(days_float - rounded) <= 1e-10 else None
    issue = {
        "dataset_version": DATASET_VERSION,
        "ticket_event_id": ticket_event_id,
        "club_slug": club_slug.strip(),
        "kickoff_at": kickoff.isoformat(),
        "issued_as_of_at": issued.isoformat(),
        "days_to_event": days,
        "measurement_key": None,
        "observed_prefix": [],
        "latest_captured_at": None,
        "last_available_total": None,
        "raw_observation_count": 0,
        "clean_observation_count": 0,
        "prefix_span_hours": 0.0,
        "latest_staleness_hours": None,
        "source_state_metadata_complete": False,
        "rejected_snapshot_ids": [],
        "target_values_used": False,
        "production_change": False,
    }
    if days is None or not 1 <= days <= MAX_CONTEXT_DAYS:
        return _finish(issue, "INVALID_ISSUE_CUTOFF", "Expected an exact P-60 through P-1 daily cutoff")
    if preparation_error is not None:
        return _finish(issue, "INVALID_OBSERVATION", preparation_error)
    earliest = kickoff - timedelta(days=MAX_CONTEXT_DAYS)
    visible = [(t, row) for t, row in timed or [] if earliest <= t <= issued]
    issue["raw_observation_count"] = len(visible)
    if not visible:
        return _finish(issue, "NO_OBSERVATIONS", "No genuine observation visible by this cutoff")
    try:
        unique = _deduplicate_timestamps(visible)
    except ValueError as exc:
        return _finish(issue, "INVALID_OBSERVATION", str(exc))

    normalized = []
    error_status = None
    error_reason = None
    for captured, raw in unique:
        try:
            row = _normalize_observation(captured, raw)
        except ValueError as exc:
            if error_status is None:
                error_status, error_reason = "INVALID_OBSERVATION", str(exc)
            try:
                issue["rejected_snapshot_ids"].append(_positive_integer(raw.get("snapshot_id"), "snapshot_id"))
            except ValueError:
                pass
            continue
        normalized.append(row)
        for flag, status in (("source_active", "SOURCE_INACTIVE"), ("source_visible", "SOURCE_HIDDEN")):
            if row.get(flag) is False:
                if error_status is None:
                    error_status, error_reason = status, f"Explicit {flag}=false in observed prefix"
                issue["rejected_snapshot_ids"].append(row["snapshot_id"])

    # Source changes and invalid states are checked before hourly compression:
    # a later reading in an hour cannot hide an incompatible measurement.
    keys = {row["measurement_key"] for row in normalized}
    if len(keys) == 1:
        issue["measurement_key"] = next(iter(keys))
    elif len(keys) > 1 and error_status is None:
        error_status, error_reason = "MEASUREMENT_CHANGED", "Observed prefix contains multiple measurement identities"

    hourly = {}
    for row in normalized:
        captured = parse_timestamp(row["captured_at"])
        hour = captured.replace(minute=0, second=0, microsecond=0)
        hourly[hour] = row  # normalized rows already ascend by captured time
    prefix = list(hourly.values())
    issue["observed_prefix"] = prefix
    issue["clean_observation_count"] = len(prefix)
    issue["rejected_snapshot_ids"] = sorted(set(issue["rejected_snapshot_ids"]))
    issue["source_state_metadata_complete"] = bool(prefix) and all(
        row.get("source_active") is not None and row.get("source_visible") is not None
        for row in prefix
    )
    if prefix:
        first = parse_timestamp(prefix[0]["captured_at"])
        latest = parse_timestamp(prefix[-1]["captured_at"])
        issue["latest_captured_at"] = latest.isoformat()
        issue["last_available_total"] = prefix[-1]["available_total"]
        issue["prefix_span_hours"] = (latest - first).total_seconds() / 3600.0
        issue["latest_staleness_hours"] = (issued - latest).total_seconds() / 3600.0
    if error_status is not None:
        return _finish(issue, error_status, error_reason)
    if len(prefix) < MIN_OBSERVATIONS:
        return _finish(issue, "INSUFFICIENT_OBSERVATIONS", "At least 4 genuine hourly observations required")
    if issue["prefix_span_hours"] < MIN_SPAN_HOURS:
        return _finish(issue, "INSUFFICIENT_PREFIX_SPAN", "At least 24h observed prefix span required")
    if issue["latest_staleness_hours"] > MAX_STALENESS_HOURS:
        return _finish(issue, "STALE_INPUT", "Latest genuine observation is older than 6h")
    return _finish(issue, "READY")


def build_issue(event: dict, issued_as_of_at: str | datetime) -> dict:
    """Build one immutable, point-in-time input description, including failures."""
    try:
        timed = _timed_observations(event)
    except ValueError as exc:
        return _build_issue(event, issued_as_of_at, None, str(exc))
    return _build_issue(event, issued_as_of_at, timed)


def future_targets(issue: dict) -> list[dict]:
    """Return daily target coordinates; no inventory labels are constructed."""
    kickoff = parse_timestamp(issue["kickoff_at"])
    issued = parse_timestamp(issue["issued_as_of_at"])
    days = issue.get("days_to_event")
    if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= MAX_CONTEXT_DAYS:
        raise ValueError("Invalid issue days_to_event")
    if issued != kickoff - timedelta(days=days):
        raise ValueError("Issue timestamp and days_to_event disagree")
    return [
        {
            "lead_days": lead,
            "target_at": (issued + timedelta(days=lead)).isoformat(),
            "target_days_to_event": days - lead,
        }
        for lead in range(1, days)
    ]


def _match_target(
    timed: list[tuple[datetime, dict]],
    target_at: str | datetime,
    available_by: str | datetime,
    measurement_key: str,
) -> dict | None:
    target = parse_timestamp(target_at)
    available = parse_timestamp(available_by)
    if target > available:
        return None
    oldest = target - timedelta(hours=MAX_STALENESS_HOURS)
    candidates = [(t, row) for t, row in timed if oldest <= t <= target]
    if not candidates:
        return None
    try:
        captured, raw = _deduplicate_timestamps(candidates)[-1]
        row = _normalize_observation(captured, raw)
    except ValueError:
        return None
    if row["measurement_key"] != measurement_key:
        return None
    if row.get("source_active") is False or row.get("source_visible") is False:
        return None
    return {
        **row,
        "target_at": target.isoformat(),
        "target_staleness_hours": (target - captured).total_seconds() / 3600.0,
    }


def match_target(
    event: dict,
    target_at: str | datetime,
    available_by: str | datetime,
    measurement_key: str,
) -> dict | None:
    """Match a matured target to a real, fresh observation without filling."""
    if not isinstance(measurement_key, str) or not measurement_key.strip():
        return None
    if parse_timestamp(target_at) >= parse_timestamp(event.get("kickoff_at")):
        return None
    try:
        timed = _timed_observations(event)
    except ValueError:
        return None
    return _match_target(timed, target_at, available_by, measurement_key)


def build_dataset(events: list[dict], as_of_at: str | datetime) -> dict:
    """Materialize daily issues plus genuinely matched labels for research.

    Future nominal targets are pending, rather than counted as missing labels.
    Repeated rows reference one issue dictionary in memory. This function does
    not turn an offline reconstruction into prospective evidence.
    """
    if not isinstance(events, list):
        raise ValueError("events must be a list")
    as_of = parse_timestamp(as_of_at)
    issues, rows = [], []
    status_counts: Counter = Counter()
    by_lead: dict[int, Counter] = {}
    seen_event_ids = set()
    scheduled_targets = possible_targets = mature_targets = matched_targets = 0
    event_ids_with_labels = set()
    clubs_with_labels = set()
    for event in events:
        event_id = _positive_integer(event.get("ticket_event_id"), "ticket_event_id")
        if event_id in seen_event_ids:
            raise ValueError("Duplicate event identity in export")
        seen_event_ids.add(event_id)
        kickoff = parse_timestamp(event.get("kickoff_at"))
        preparation_error = None
        try:
            timed = _timed_observations(event)
        except ValueError as exc:
            timed, preparation_error = [], str(exc)
        for days in range(MAX_CONTEXT_DAYS, 0, -1):
            issued = kickoff - timedelta(days=days)
            if issued > as_of:
                continue
            issue = _build_issue(event, issued, timed, preparation_error)
            issues.append(issue)
            status_counts[issue["status"]] += 1
            targets = future_targets(issue)
            scheduled_targets += len(targets)
            if issue["status"] != "READY":
                continue
            for target in targets:
                lead = target["lead_days"]
                support = by_lead.setdefault(lead, Counter())
                support["possible_target_count"] += 1
                possible_targets += 1
                if parse_timestamp(target["target_at"]) > as_of:
                    support["pending_target_count"] += 1
                    continue
                support["mature_target_count"] += 1
                mature_targets += 1
                observed = _match_target(timed, target["target_at"], as_of, issue["measurement_key"])
                if observed is None:
                    support["missing_target_count"] += 1
                    continue
                support["matched_target_count"] += 1
                matched_targets += 1
                event_ids_with_labels.add(event_id)
                clubs_with_labels.add(issue["club_slug"])
                rows.append({
                    "issue": issue,
                    **target,
                    "target_available_total": observed["available_total"],
                    "target_snapshot_id": observed["snapshot_id"],
                    "target_captured_at": observed["captured_at"],
                    "target_staleness_hours": observed["target_staleness_hours"],
                    "measurement_key": observed["measurement_key"],
                })
    coverage = {
        "event_count": len(events),
        "scheduled_issue_count": len(issues),
        "ready_issue_count": status_counts["READY"],
        "issue_status_counts": dict(sorted(status_counts.items())),
        "scheduled_target_count": scheduled_targets,
        "possible_target_count": possible_targets,
        "mature_target_count": mature_targets,
        "matched_target_count": matched_targets,
        "missing_target_count": mature_targets - matched_targets,
        "pending_target_count": possible_targets - mature_targets,
        "label_coverage": matched_targets / mature_targets if mature_targets else None,
        "labeled_event_count": len(event_ids_with_labels),
        "labeled_club_count": len(clubs_with_labels),
        "per_lead": {
            str(lead): {
                key: counts[key]
                for key in (
                    "possible_target_count", "mature_target_count",
                    "matched_target_count", "missing_target_count", "pending_target_count",
                )
            }
            for lead, counts in sorted(by_lead.items())
        },
    }
    return {
        "dataset_version": DATASET_VERSION,
        "as_of_at": as_of.isoformat(),
        "evidence_kind": "retrospective_diagnostic_not_prospective",
        "production_change": False,
        "issues": issues,
        "rows": rows,
        "coverage": coverage,
    }
