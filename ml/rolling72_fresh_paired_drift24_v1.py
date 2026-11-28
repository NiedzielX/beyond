"""Offline preparation contract for fresh PERS versus fixed drift24.

This module computes candidate values only. It does not issue forecasts, create
database clocks, read live sources, fit parameters, or persist receipts.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any, Iterable

VERSION = "rolling72-mvp-paired-drift24-v1"
HORIZONS = (24, 48, 72)
ANCHOR_MIN_HOURS = 24.0
ANCHOR_MAX_HOURS = 30.0
MAX_SOURCE_AGE_HOURS = 1.0
MAX_ISSUE_LATENCY_SECONDS = 90.0
REFERENCE_HASHES = {
    "supabase/sql/rolling72_forward_baselines_b_v1.sql": "c9621bb692ca7de38037a204a9ca204ed3be370657b9ab89dc3aa438575effb4",
    "supabase/sql/rolling72_lad_shadow_v5.sql": "c2a3071d7109b74040228fb6b4ee77a6524afccc7174550acb7fa362e9f7afd2",
}
BREAK_STATUSES = {"MISSING_SOURCE", "SKIPPED_STALE", "INVALID_SOURCE", "INTERNAL_ERROR"}


def _dt(value: Any, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _identity(record: dict[str, Any]) -> tuple[Any, Any, Any]:
    return record.get("event_id"), record.get("source_family"), record.get("unit")


def _ids(record: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    pairs = record.get("sector_price_area_ids")
    if not isinstance(pairs, (list, tuple)) or not pairs:
        raise ValueError("sector_price_area_ids must be a complete nonempty membership list")
    normalized = []
    for pair in pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("each membership item must be a (sector_source_id, price_area_id) pair")
        sector, area = pair
        if (isinstance(sector, bool) or isinstance(area, bool)
                or not isinstance(sector, (str, int)) or not isinstance(area, (str, int))
                or not str(sector).strip() or not str(area).strip()):
            raise ValueError("membership IDs must be nonempty stable string/integer IDs")
        normalized.append((str(sector), str(area)))
    if len(set(normalized)) != len(normalized):
        raise ValueError("sector/price-area membership pairs must be unique")
    return tuple(sorted(normalized))


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def _validate_record(record: dict[str, Any], reference_at: datetime, *, origin=False) -> None:
    if record.get("source_status") != "READY":
        raise ValueError("source record must be READY")
    if not record.get("event_id") or not isinstance(record.get("source_family"), str) or not record["source_family"]:
        raise ValueError("registered event and source family are required")
    if origin and record.get("source_family") != "roboticket/roboticket":
        raise ValueError("current source family must be roboticket/roboticket")
    if record.get("unit") != "available_total_seats":
        raise ValueError("source unit must be available_total_seats")
    if not isinstance(record.get("seal_id"), (str, int)) or isinstance(record.get("seal_id"), bool):
        raise ValueError("source seal_id is required")
    if not isinstance(record.get("content_hash"), str) or not record["content_hash"]:
        raise ValueError("source content_hash is required")
    _ids(record)
    available = _number(record.get("available_total"), "available_total")
    if available < 0:
        raise ValueError("available_total must be nonnegative")
    cap = _dt(record.get("captured_at"), "captured_at")
    known = _dt(record.get("known_at"), "known_at")
    if cap > known or known > reference_at:
        raise ValueError("record clocks must satisfy captured_at <= known_at <= projection reference")
    if origin and not 0 <= (reference_at - cap).total_seconds() <= MAX_SOURCE_AGE_HOURS * 3600:
        raise ValueError("origin source age must be in [0, 1h]")


def prepare_values(origin: dict[str, Any], history: Iterable[dict[str, Any]], *,
                   projection_reference_at: datetime,
                   attempts: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    """Calculate six numeric policy values before an issue clock exists.

    The caller must capture ``projection_reference_at`` at actual read
    completion before calling this function. It is only an input assertion;
    this offline helper cannot prove database clock provenance.
    """
    ref = _dt(projection_reference_at, "projection_reference_at")
    rows = list(history)
    attempt_rows = list(attempts)
    if origin.get("source_status") != "READY":
        return {"version": VERSION, "event_id": origin.get("event_id"),
                "projection_reference_at": ref, "bundle_status": "UNAVAILABLE_SOURCE",
                "forecast_values": [], "kickoff_at": None,
                "provenance": {"history_input_hash": _digest(rows),
                               "clock_claim": "caller-provided input; no clock attested or generated"}}
    _validate_record(origin, ref, origin=True)
    otime = _dt(origin["captured_at"], "origin.captured_at")
    pers = _number(origin["available_total"], "origin.available_total")
    for row in rows:
        if row.get("source_status") not in ("READY", *BREAK_STATUSES):
            raise ValueError("history source_status must be explicit and recognized")
        if _dt(row.get("known_at"), "history.known_at") > ref:
            continue
        if row.get("source_status") == "READY":
            _validate_record(row, ref)
    eligible = []
    for row in rows:
        if row.get("source_status") != "READY" or _dt(row["known_at"], "known_at") > ref:
            continue
        t = _dt(row["captured_at"], "captured_at")
        hours = (otime - t).total_seconds() / 3600
        if ANCHOR_MIN_HOURS <= hours <= ANCHOR_MAX_HOURS:
            eligible.append((row, hours))
    eligible.sort(key=lambda item: (_dt(item[0]["captured_at"], "captured_at"), str(item[0].get("seal_id", ""))), reverse=True)

    reason = None
    anchor = None
    if eligible:
        anchor, _ = eligible[0]
        if _identity(anchor) != _identity(origin):
            reason = "SOURCE_BREAK"
        elif _ids(anchor) != _ids(origin):
            reason = "SCOPE_MISMATCH"
    else:
        reason = "NO_24H_ANCHOR"

    # A known failed attempt after the chosen anchor and through this origin
    # breaks continuity, even if older READY anchors exist.
    if anchor is not None and reason is None:
        atime = _dt(anchor["captured_at"], "anchor.captured_at")
        for row in rows:
            row_status = row.get("source_status")
            if row_status != "READY":
                if row_status in BREAK_STATUSES:
                    known = _dt(row.get("known_at"), "history.known_at")
                    observed = row.get("captured_at")
                    if observed is not None and _dt(observed, "history.captured_at") > known:
                        raise ValueError("history clocks must satisfy captured_at <= known_at")
                    t = _dt(observed, "history.captured_at") if observed is not None else known
                    if known <= ref and atime < t <= otime:
                        reason = "SOURCE_BREAK"
                        break
                continue
            if _dt(row.get("known_at"), "known_at") > ref:
                continue
            t = _dt(row.get("captured_at"), "captured_at")
            if not atime < t <= otime:
                continue
            if _identity(row) != _identity(origin):
                reason = "SOURCE_BREAK"
                break
            if _ids(row) != _ids(origin):
                reason = "SCOPE_MISMATCH"
                break
        breaks = []
        for attempt in attempt_rows:
            if attempt.get("status") not in BREAK_STATUSES:
                continue
            known = _dt(attempt.get("known_at"), "attempt.known_at")
            observed = attempt.get("captured_at")
            if observed is not None and _dt(observed, "attempt.captured_at") > known:
                raise ValueError("attempt clocks must satisfy captured_at <= known_at")
            if known > ref:
                continue
            # Unknown capture time is conservatively a break if its knowledge
            # arrived after the anchor and before this issue.
            t = _dt(observed, "attempt.captured_at") if observed is not None else known
            if atime < t <= otime:
                breaks.append(attempt)
        if breaks and reason is None:
            reason = "SOURCE_BREAK"

    slope = None
    age_hours = (ref - otime).total_seconds() / 3600
    if anchor is not None and reason is None:
        elapsed = (otime - _dt(anchor["captured_at"], "anchor.captured_at")).total_seconds() / 3600
        if elapsed <= 0:
            reason = "NO_24H_ANCHOR"
        else:
            slope = (pers - _number(anchor["available_total"], "anchor.available_total")) / elapsed

    forecasts = []
    for h in HORIZONS:
        forecasts.append({"method": "PERS", "horizon_hours": h,
                          "status": "READY", "prediction": pers, "fallback_reason": None})
        if reason is not None:
            forecasts.append({"method": "DRIFT24", "horizon_hours": h,
                              "status": "FALLBACK_PERS", "prediction": pers, "fallback_reason": reason})
        else:
            extrapolated = pers + slope * (h + age_hours)
            if not math.isfinite(extrapolated):
                raise ValueError("drift24 float8 forecast overflow")
            estimate = max(0.0, extrapolated)
            forecasts.append({"method": "DRIFT24", "horizon_hours": h,
                              "status": "READY", "prediction": estimate, "fallback_reason": None})
    if slope is not None and not math.isfinite(slope):
        raise ValueError("drift24 float8 slope overflow")
    provenance = {
        "version": VERSION,
        "origin_seal_id": origin.get("seal_id"),
        "anchor_seal_id": anchor.get("seal_id") if anchor else None,
        "origin_hash": origin.get("content_hash"),
        "anchor_hash": anchor.get("content_hash") if anchor else None,
        "origin_membership_hash": _digest(_ids(origin)),
        "anchor_membership_hash": _digest(_ids(anchor)) if anchor else None,
        "history_input_hash": _digest(rows),
        "projection_reference_at": ref.isoformat(),
        "projection_reference_clock_claim": "caller_provided_actual_read_completion; not generated here",
        "age_hours": age_hours,
        "slope24": slope,
        "formula": "max(0, origin_total + slope24 * (horizon_hours + age_hours)); float8-like; no rounding/cap",
        "reference_hashes": dict(REFERENCE_HASHES),
    }
    return {"version": VERSION, "event_id": origin["event_id"],
            "projection_reference_at": ref, "bundle_status": "READY",
            "forecast_values": forecasts, "kickoff_at": None,
            "provenance": provenance, "_origin_captured_at": otime}


def bind_actual_issue(prepared: dict[str, Any], *, issued_at: datetime,
                      kickoff_at: datetime) -> dict[str, Any]:
    """Bind post-calculation issue clock and target coordinates to prepared values."""
    issue = _dt(issued_at, "issued_at")
    kickoff = _dt(kickoff_at, "kickoff_at")
    if prepared.get("version") != VERSION:
        raise ValueError("prepared values version mismatch")
    ref = prepared.get("projection_reference_at")
    if isinstance(ref, str):
        ref = datetime.fromisoformat(ref)
    ref = _dt(ref, "projection_reference_at")
    latency = (issue - ref).total_seconds()
    if not 0 <= latency <= MAX_ISSUE_LATENCY_SECONDS:
        raise ValueError("caller-provided issue clock must follow projection reference within 90 seconds")
    from datetime import timedelta
    if prepared.get("bundle_status") == "UNAVAILABLE_SOURCE":
        forecasts = []
        for h in HORIZONS:
            target = issue + timedelta(hours=h)
            status = "OUTSIDE_KICKOFF" if target >= kickoff else "UNAVAILABLE_SOURCE"
            for method in ("PERS", "DRIFT24"):
                forecasts.append({"method": method, "horizon_hours": h, "target_at": target.isoformat(),
                                  "status": status, "prediction": None, "fallback_reason": None})
        return {**prepared, "issued_at": issue.isoformat(), "latency_seconds": latency,
                "kickoff_at": kickoff.isoformat(), "forecasts": forecasts}
    captured = prepared.get("_origin_captured_at")
    if isinstance(captured, str):
        captured = datetime.fromisoformat(captured)
    captured = _dt(captured, "origin.captured_at")
    if not 0 <= (issue - captured).total_seconds() <= MAX_SOURCE_AGE_HOURS * 3600:
        raise ValueError("origin source age at actual issued_at must be in [0, 1h]")
    forecasts = []
    by_horizon = {h: [r for r in prepared["forecast_values"] if r["horizon_hours"] == h] for h in HORIZONS}
    for h in HORIZONS:
        target = issue + timedelta(hours=h)
        if target >= kickoff:
            forecasts.extend({"method": method, "horizon_hours": h, "target_at": target.isoformat(),
                              "status": "OUTSIDE_KICKOFF", "prediction": None, "fallback_reason": None}
                             for method in ("PERS", "DRIFT24"))
        else:
            forecasts.extend({**row, "target_at": target.isoformat()} for row in by_horizon[h])
    provenance = dict(prepared["provenance"])
    provenance.update({"issued_at": issue.isoformat(),
                       "issued_at_clock_claim": "caller-provided actual post-calculation clock; not generated here",
                       "issue_latency_seconds": latency})
    return {"version": VERSION, "event_id": prepared["event_id"], "issued_at": issue.isoformat(),
            "projection_reference_at": ref.isoformat(), "latency_seconds": latency,
            "kickoff_at": kickoff.isoformat(), "bundle_status": "READY", "forecasts": forecasts,
            "provenance": provenance}


def prepare_pair(origin: dict[str, Any], history: Iterable[dict[str, Any]], *,
                 projection_reference_at: datetime, issued_at: datetime,
                 kickoff_at: datetime, attempts: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    """Offline convenience wrapper; neither supplied clock is generated here."""
    prepared = prepare_values(origin, history, projection_reference_at=projection_reference_at,
                              attempts=attempts)
    return bind_actual_issue(prepared, issued_at=issued_at, kickoff_at=kickoff_at)


def event_grouped_mae(rows: Iterable[dict[str, Any]], *, horizon_hours: int) -> dict[str, Any]:
    """Return per-event MAE for exactly one declared 24/48/72h horizon."""
    if horizon_hours not in HORIZONS:
        raise ValueError("horizon_hours must be exactly one of 24, 48, or 72")
    groups: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        if row.get("horizon_hours") != horizon_hours:
            raise ValueError("all metric rows must match the explicitly requested horizon")
        p, d, y = row.get("pers"), row.get("drift24"), row.get("target")
        if any(v is None for v in (p, d, y)):
            continue
        p, d, y = (_number(v, k) for v, k in ((p, "pers"), (d, "drift24"), (y, "target")))
        groups[str(row["event_id"])].append((abs(p - y), abs(d - y)))
    per_event = {event: {"n": len(values), "pers_mae": sum(x for x, _ in values) / len(values),
                         "drift24_mae": sum(y for _, y in values) / len(values),
                         "delta_mae": sum(y - x for x, y in values) / len(values)}
                 for event, values in sorted(groups.items())}
    n = len(per_event)
    return {"horizon_hours": horizon_hours, "events": n, "points": sum(x["n"] for x in per_event.values()), "per_event": per_event,
            "pers_event_balanced_mae": sum(x["pers_mae"] for x in per_event.values()) / n if n else None,
            "drift24_event_balanced_mae": sum(x["drift24_mae"] for x in per_event.values()) / n if n else None,
            "delta_event_balanced_mae": sum(x["delta_mae"] for x in per_event.values()) / n if n else None}
