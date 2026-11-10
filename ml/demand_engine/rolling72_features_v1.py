"""Pure, separately versioned rolling inventory inputs; no labels or model fit.

``build_issue`` accepts only event fields ``ticket_event_id``, ``club_slug``,
``kickoff_at``, ``known_at`` and ``observations``. Event ``known_at`` is the
availability clock of that exact metadata version, not its match date. Each
observation requires ``snapshot_id``, ``captured_at``, ``known_at``,
``available_total`` and ``measurement_key``; optional source_active/visible
flags are bool/null. The opaque measurement key MUST identify the declared
source AND pool scope; this module cannot independently verify that assertion.

All clocks are aware. Observation known_at >= captured_at. Only observations
both captured and known by issue enter payload validation or hashing. Timing
fields must themselves be valid to determine exclusion. There is deliberately
no adapter inventing known_at for legacy exports. Supplied clocks and hashes
do not prove raw-table immutability or historical metadata lineage.

The whole available prefix is retained without a 60-day limit or hourly bins;
exact-time duplicates retain greatest snapshot ID after validating all visible
rows. Conflicting identities, invalid values, changed measurement or explicit
inactive/hidden flags fail closed. Missing flags remain unknown. One point is
sufficient; latest age must be <=6h, which is not a history-length requirement.

``features(issue, horizon_hours)`` accepts 24/48/72 from ISSUE, strictly before
kickoff. Features describe measured availability, never confirmed sales. Window
anchors are real observations at/before latest_capture minus 6/24/72h, at most
6h older than that boundary. Deltas use actual observations; slopes use actual
elapsed time. Missing windows stay None. Observation counts are quality only.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from numbers import Real
from typing import Any


VERSION = "rolling72-input-features-v1"
HORIZONS = (24, 48, 72)
MAX_STALENESS_HOURS = 6.0
ANCHOR_TOLERANCE_HOURS = 6.0
EVENT_FIELDS = {"ticket_event_id", "club_slug", "kickoff_at", "known_at", "observations"}
ROW_REQUIRED = {"snapshot_id", "captured_at", "known_at", "available_total", "measurement_key"}
ROW_FIELDS = ROW_REQUIRED | {"source_active", "source_visible"}


def _time(value: Any) -> datetime:
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("Explicit timezone-aware timestamp required")
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Explicit timezone-aware timestamp required")
    return result.astimezone(timezone.utc)


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _id(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("Positive integer identity required")
    return value


def _count(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("Finite nonnegative observed count required")
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        raise ValueError("Finite nonnegative observed count required") from None
    if not math.isfinite(result) or result < 0:
        raise ValueError("Finite nonnegative observed count required")
    return result


def _finish(issue: dict, status: str, reason: str | None = None) -> dict:
    issue["status"], issue["status_reason"] = status, reason
    issue["prefix_sha256"] = _hash(issue["observed_prefix"])
    issue["input_manifest_sha256"] = _hash(issue)
    return issue


def build_issue(event: dict, issued_at: str | datetime) -> dict:
    """Build a canonical input or explicit failed status, never a prediction.

    Structural/timing ambiguity raises ValueError; visible bad measurements
    become failed issues so coverage can retain them. Unknown metadata yields
    no event payload, even if that payload would otherwise be malformed.
    """
    issued = _time(issued_at)
    if not isinstance(event, dict) or set(event) != EVENT_FIELDS:
        raise ValueError("Exact declared event schema required")
    metadata_known = _time(event["known_at"])
    issue = {
        "version": VERSION, "issued_at": issued.isoformat(),
        "event": None, "observed_prefix": [], "measurement_key": None,
        "latest_captured_at": None, "last_available_total": None,
        "prefix_span_hours": None, "latest_staleness_hours": None,
        "quality": {"observation_count": 0, "source_flags_complete": False},
        "provenance": {"known_at_supplied": True, "raw_immutability_proven": False,
                       "historical_metadata_lineage_proven": False},
        "target_values_used": False, "model_fit_performed": False,
        "production_change": False, "live_adjustment": 0,
    }
    if metadata_known > issued:
        return _finish(issue, "EVENT_NOT_KNOWN_AS_OF")
    identity = _id(event["ticket_event_id"])
    club = event["club_slug"]
    if not isinstance(club, str) or not club.strip():
        raise ValueError("Nonempty club_slug required")
    kickoff = _time(event["kickoff_at"])
    issue["event"] = {"ticket_event_id": identity, "club_slug": club.strip(),
                      "kickoff_at": kickoff.isoformat(), "known_at": metadata_known.isoformat()}
    if issued >= kickoff:
        return _finish(issue, "ISSUE_NOT_BEFORE_KICKOFF")
    observations = event["observations"]
    if not isinstance(observations, list):
        raise ValueError("Observation list required")
    visible = []
    for row in observations:
        if not isinstance(row, dict):
            raise ValueError("Observation timing requires an object")
        captured, known = _time(row.get("captured_at")), _time(row.get("known_at"))
        if known < captured:
            raise ValueError("Observation known_at precedes captured_at")
        if captured <= issued and known <= issued:
            visible.append((captured, known, row))
    if not visible:
        return _finish(issue, "NO_KNOWN_OBSERVATIONS")
    clean = []
    for captured, known, raw in visible:
        try:
            if set(raw) - ROW_FIELDS or not ROW_REQUIRED <= set(raw):
                raise ValueError("Exact declared observation schema required")
            row_id = _id(raw["snapshot_id"])
            measurement = raw["measurement_key"]
            if not isinstance(measurement, str) or not measurement.strip():
                raise ValueError("Explicit source/pool measurement_key required")
            flags = {}
            for flag in ("source_active", "source_visible"):
                value = raw.get(flag)
                if value is not None and not isinstance(value, bool):
                    raise ValueError("Source flags must be boolean or null")
                flags[flag] = value
            value = _count(raw["available_total"])
        except ValueError as exc:
            return _finish(issue, "INVALID_OBSERVATION", str(exc))
        clean.append({"snapshot_id": row_id, "captured_at": captured.isoformat(),
                      "known_at": known.isoformat(), "available_total": value,
                      "measurement_key": measurement.strip(), **flags})
    clean.sort(key=lambda row: (row["captured_at"], row["snapshot_id"]))
    by_id = {}
    for row in clean:
        previous = by_id.get(row["snapshot_id"])
        if previous is not None and previous != row:
            return _finish(issue, "CONFLICTING_OBSERVATION_IDENTITY")
        by_id[row["snapshot_id"]] = row
    keys = {row["measurement_key"] for row in clean}
    if len(keys) != 1:
        return _finish(issue, "MEASUREMENT_CHANGED")
    # Check every visible row before a same-time tie can conceal invalid state.
    for flag, status in (("source_active", "SOURCE_INACTIVE"), ("source_visible", "SOURCE_HIDDEN")):
        if any(row[flag] is False for row in clean):
            return _finish(issue, status)
    by_time = {}
    for row in clean:
        by_time[row["captured_at"]] = row
    prefix = list(by_time.values())
    first, latest = _time(prefix[0]["captured_at"]), _time(prefix[-1]["captured_at"])
    age = (issued - latest).total_seconds() / 3600
    issue.update({"observed_prefix": prefix, "measurement_key": next(iter(keys)),
                  "latest_captured_at": latest.isoformat(),
                  "last_available_total": prefix[-1]["available_total"],
                  "prefix_span_hours": (latest - first).total_seconds() / 3600,
                  "latest_staleness_hours": age,
                  "quality": {"observation_count": len(prefix), "source_flags_complete": all(
                      row["source_active"] is not None and row["source_visible"] is not None for row in prefix)}})
    if age > MAX_STALENESS_HOURS:
        return _finish(issue, "STALE_INPUT")
    return _finish(issue, "READY")


def features(issue: dict, horizon_hours: int) -> dict:
    """Validate canonical READY inputs and return measured-state features only."""
    if isinstance(horizon_hours, bool) or not isinstance(horizon_hours, int) or horizon_hours not in HORIZONS:
        raise ValueError("Only 24/48/72-hour horizons are supported")
    if not isinstance(issue, dict) or issue.get("version") != VERSION:
        raise ValueError("Rolling72 issue version required")
    if (issue.get("prefix_sha256") != _hash(issue.get("observed_prefix"))
            or issue.get("input_manifest_sha256") != _hash({k: v for k, v in issue.items() if k != "input_manifest_sha256"})):
        raise ValueError("Issue hash mismatch")
    result = {"version": VERSION, "input_manifest_sha256": issue["input_manifest_sha256"],
              "horizon_hours": horizon_hours, "target_at": None, "status": issue["status"],
              "features": {}, "missing": {}, "quality": issue["quality"].copy(),
              "window_lineage": {}, "target_values_used": False,
              "model_fit_performed": False, "production_change": False, "live_adjustment": 0}
    if issue["status"] != "READY":
        return result
    rebuilt = build_issue({**issue["event"], "observations": issue["observed_prefix"]}, issue["issued_at"])
    if rebuilt != issue:
        raise ValueError("Issue does not match its canonical observed inputs")
    issued = _time(issue["issued_at"])
    kickoff = _time(issue["event"]["kickoff_at"])
    target = issued + timedelta(hours=horizon_hours)
    result["target_at"] = target.isoformat()
    if target >= kickoff:
        result["status"] = "TARGET_NOT_BEFORE_KICKOFF"
        return result
    prefix = issue["observed_prefix"]
    first, latest = prefix[0], prefix[-1]
    latest_time = _time(latest["captured_at"])
    values = {
        "last_available_total": latest["available_total"],
        "observed_delta_since_first": latest["available_total"] - first["available_total"],
        "prefix_span_hours": issue["prefix_span_hours"],
        "latest_staleness_hours": issue["latest_staleness_hours"],
        "hours_to_kickoff": (kickoff - issued).total_seconds() / 3600,
        "horizon_hours": horizon_hours,
    }
    for hours in (6, 24, 72):
        boundary = latest_time - timedelta(hours=hours)
        anchors = [row for row in prefix if _time(row["captured_at"]) <= boundary]
        anchor = anchors[-1] if anchors else None
        if anchor is not None and (boundary - _time(anchor["captured_at"])).total_seconds() / 3600 > ANCHOR_TOLERANCE_HOURS:
            anchor = None
        delta = slope = None
        lineage = None
        if anchor is not None:
            elapsed = (latest_time - _time(anchor["captured_at"])).total_seconds() / 3600
            delta = latest["available_total"] - anchor["available_total"]
            slope = delta / elapsed
            lineage = {"anchor_snapshot_id": anchor["snapshot_id"], "latest_snapshot_id": latest["snapshot_id"],
                       "anchor_captured_at": anchor["captured_at"], "elapsed_hours": elapsed}
        values[f"delta_{hours}h"] = delta
        values[f"slope_{hours}h"] = slope
        result["window_lineage"][str(hours)] = lineage
    result["features"] = values
    result["missing"] = {key: value is None for key, value in values.items()}
    return result
