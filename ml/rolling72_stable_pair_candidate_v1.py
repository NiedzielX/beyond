"""Offline stable sector/price-area candidate arithmetic.

This is a pure synthetic/research helper. It does not select database rows,
attest seal visibility, issue forecasts, or persist labels. The caller must
supply the exact as-of interval from the strict parent paired-drift reader.
"""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import islice
import re
from typing import Any, Iterable

VERSION = "rolling72-mvp-stable-pair-candidate-v1"
HORIZONS = (24, 48, 72)
ANCHOR_MIN_HOURS = 24.0
ANCHOR_MAX_HOURS = 30.0
MAX_ORIGIN_AGE_HOURS = 1.0
MAX_INTERVAL_SEALS = 130
MIN_INTERVAL_SEALS = 3
MIN_STABLE_SECTORS = 3
MIN_ORIGIN_COVERAGE = 0.80


def _dt(value: Any, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware datetime")
    return value.astimezone(timezone.utc)


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _pairs(record: dict[str, Any]) -> dict[tuple[str, str], int]:
    rows = record.get("sector_price_area_rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("sector_price_area_rows must be a nonempty list")
    result: dict[tuple[str, str], int] = {}
    sectors_by_name: dict[str, set[str]] = {}
    names_by_sector: dict[str, set[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each pair row must be an object")
        raw_sector, raw_area = row.get("sector_source_id"), row.get("price_area_id")
        if any(re.fullmatch(r"[0-9]+", str(raw_id)) is None for raw_id in (raw_sector, raw_area)):
            raise ValueError("pair IDs must match the sealed Roboticket identities")
        sector_name = row.get("sector")
        if not isinstance(sector_name, str) or not sector_name:
            raise ValueError("sector name is required")
        key = (str(raw_sector), str(raw_area))
        if key in result:
            raise ValueError("duplicate sector/price-area pair")
        available = _integer(row.get("available"), "pair available")
        if available < 0:
            raise ValueError("pair available must be nonnegative")
        result[key] = available
        sectors_by_name.setdefault(sector_name, set()).add(key[0])
        names_by_sector.setdefault(key[0], set()).add(sector_name)
    if any(len(values) != 1 for values in sectors_by_name.values()) or any(len(values) != 1 for values in names_by_sector.values()):
        raise ValueError("sector labels and source IDs must map one-to-one")
    total = _integer(record.get("available_total"), "available_total")
    if total < 0 or sum(result.values()) != total:
        raise ValueError("pair availability must reconcile to available_total")
    return result


def _validate_seal(record: dict[str, Any], reference_at: datetime, event_id: str | int) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("each seal must be an object")
    if record.get("source_status") != "READY" or record.get("committed") is not True:
        raise ValueError("seal must be READY and committed")
    if record.get("event_id") != event_id:
        raise ValueError("interval seal belongs to another event")
    if record.get("source_family") != "roboticket/roboticket" or record.get("unit") != "available_total_seats":
        raise ValueError("unsupported source family or unit")
    for key in ("seal_id", "snapshot_id"):
        if _integer(record.get(key), key) <= 0:
            raise ValueError(f"{key} must be positive")
    digest = record.get("source_content_sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("source content hash is required")
    captured = _dt(record.get("captured_at"), "captured_at")
    known = _dt(record.get("known_at"), "known_at")
    if captured > known or known > reference_at:
        raise ValueError("seal clocks must satisfy captured_at <= known_at <= projection reference")
    pairs = _pairs(record)
    return {**record, "_captured": captured, "_known": known, "_pairs": pairs}


def _interval_support(
    interval_seals: Iterable[dict[str, Any]],
    origin: dict[str, Any],
    anchor_seal_id: int | None,
    reference_at: datetime,
) -> tuple[str, dict[str, Any]]:
    if anchor_seal_id is None:
        return "NO_ANCHOR", {}
    # Read one row past the cap to distinguish a complete interval from overflow.
    raw_seals = list(islice(interval_seals, MAX_INTERVAL_SEALS + 1))
    if len(raw_seals) > MAX_INTERVAL_SEALS:
        return "OVER_130_SEALS", {}
    try:
        seals = [_validate_seal(row, reference_at, origin["event_id"]) for row in raw_seals]
    except (TypeError, ValueError):
        return "INVALID_OR_INCOMPLETE_SEAL", {}
    seals.sort(key=lambda row: (row["_captured"], row["snapshot_id"]))
    ids = [row["seal_id"] for row in seals]
    order = [(row["_captured"], row["snapshot_id"]) for row in seals]
    if len(set(ids)) != len(seals) or len(set(order)) != len(seals):
        return "INVALID_OR_INCOMPLETE_SEAL", {}
    if anchor_seal_id not in ids or origin["seal_id"] not in ids:
        return "MISSING_ENDPOINT", {}
    if ids[0] != anchor_seal_id or ids[-1] != origin["seal_id"] or len(seals) == 1:
        return "INVALID_INTERVAL_ORDER", {}
    anchor, interval_origin = seals[0], seals[-1]
    endpoint_fields = (
        "snapshot_id", "_captured", "_known", "source_content_sha256",
        "available_total", "_pairs", "prior_seal_id", "transition_status", "gap_count",
    )
    if any(interval_origin.get(key) != origin.get(key) for key in endpoint_fields):
        return "ORIGIN_ENDPOINT_MISMATCH", {}
    elapsed = (origin["_captured"] - anchor["_captured"]).total_seconds() / 3600
    if not ANCHOR_MIN_HOURS <= elapsed <= ANCHOR_MAX_HOURS:
        return "ANCHOR_OUTSIDE_24_30H", {}
    if len(seals) < MIN_INTERVAL_SEALS:
        return "NO_INTERIOR_SEAL", {}
    stable = set(anchor["_pairs"])
    for previous, row in zip(seals, seals[1:]):
        if (row.get("transition_status") != "COMPLETE"
                or type(row.get("gap_count")) is not int or row["gap_count"] != 0
                or row.get("prior_seal_id") != previous["seal_id"]):
            return "GAPPED_INTERVAL", {}
        stable.intersection_update(row["_pairs"])

    origin_total = origin["available_total"]
    stable_anchor = sum(anchor["_pairs"][key] for key in stable)
    stable_origin = sum(origin["_pairs"][key] for key in stable)
    sectors = len({sector for sector, _ in stable})
    delta = stable_origin - stable_anchor
    summary = {
        "stable_pair_count": len(stable),
        "stable_sector_count": sectors,
        "stable_anchor_available": stable_anchor,
        "stable_origin_available": stable_origin,
        "origin_coverage": stable_origin / origin_total if origin_total else None,
        "uncovered_origin_available": origin_total - stable_origin,
        "stable_pair_observed_delta": delta if stable else None,
        "stable_pair_slope_per_hour": delta / elapsed if stable else None,
        "elapsed_capture_hours": elapsed,
    }
    if origin_total == 0:
        return "ZERO_ORIGIN", summary
    if not stable:
        return "NO_USABLE_STABLE_PAIRS", summary
    if sectors < MIN_STABLE_SECTORS or summary["origin_coverage"] < MIN_ORIGIN_COVERAGE:
        return "INSUFFICIENT_SUPPORT", summary
    return "SUPPORTED", summary


def prepare_stable_pair_candidate(
    origin: dict[str, Any],
    interval_seals: Iterable[dict[str, Any]],
    *,
    anchor_seal_id: int | None,
    parent_fallback_reason: str | None,
    projection_reference_at: datetime,
) -> dict[str, Any]:
    """Prepare an alternative for an already selected, valid parent bundle.

    Only SCOPE_MISMATCH is eligible for replacement. An unsupported interval
    returns PERS. Caller clocks and source/commit flags are assertions.
    """
    ref = _dt(projection_reference_at, "projection_reference_at")
    event_id = origin.get("event_id")
    if not event_id:
        raise ValueError("origin event_id is required")
    origin_valid = _validate_seal(origin, ref, event_id)
    origin_age = (ref - origin_valid["_captured"]).total_seconds() / 3600
    if not 0 <= origin_age <= MAX_ORIGIN_AGE_HOURS:
        raise ValueError("origin age must be in [0, 1h]")
    origin_total = origin_valid["available_total"]

    eligible = parent_fallback_reason == "SCOPE_MISMATCH"
    reason, support_metrics = "NOT_SCOPE_MISMATCH", {}
    if eligible:
        reason, support_metrics = _interval_support(interval_seals, origin_valid, anchor_seal_id, ref)
    metrics = dict.fromkeys((
        "stable_pair_count", "stable_sector_count", "stable_anchor_available",
        "stable_origin_available", "origin_coverage", "uncovered_origin_available",
        "stable_pair_observed_delta", "stable_pair_slope_per_hour", "elapsed_capture_hours",
    ))
    metrics.update(support_metrics, origin_age_hours=origin_age)

    policy_status, row_status, fallback_reason = "NOT_APPLICABLE", "NOT_APPLICABLE", None
    predictions = [None] * len(HORIZONS)
    if reason == "SUPPORTED":
        policy_status, row_status = "SUPPORTED", "READY"
        stable = metrics["stable_origin_available"]
        uncovered = metrics["uncovered_origin_available"]
        slope = metrics["stable_pair_slope_per_hour"]
        predictions = [uncovered + max(0.0, stable + slope * (hours + origin_age))
                       for hours in HORIZONS]
    elif reason == "ZERO_ORIGIN":
        policy_status, row_status = "ZERO_ORIGIN", "READY"
        predictions = [0] * len(HORIZONS)
    elif eligible:
        policy_status, row_status, fallback_reason = "FALLBACK_PERS", "FALLBACK_PERS", reason
        predictions = [origin_total] * len(HORIZONS)

    return {
        "version": VERSION,
        "event_id": event_id,
        "bundle_status": "PREPARED",
        "eligible_parent_fallback": eligible,
        "support_status": reason,
        "candidate_policy_status": policy_status,
        "projection_reference_at": ref,
        "origin_seal_id": origin_valid["seal_id"],
        "anchor_seal_id": anchor_seal_id,
        "origin_available_total": origin_total,
        "metrics": metrics,
        "forecast_values": [
            {"horizon_hours": horizon, "status": row_status, "prediction": prediction,
             "fallback_reason": fallback_reason}
            for horizon, prediction in zip(HORIZONS, predictions)
        ],
        "claims": {"clock_attested": False, "seal_visibility_attested": False,
                   "label_or_outcome_used": False, "runtime_or_persistence": False},
    }
