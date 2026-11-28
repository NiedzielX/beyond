"""Adapt already-verified paired bundle/seal/attempt rows to the offline candidate.

No row selection or database verification occurs here. The caller must provide
only rows already read and verified under the strict parent source contract and
explicit verification ID sets. This adapter checks their cross-record bindings
and preserves provenance before calling the existing pure candidate helper.
"""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import islice
from typing import Any, Iterable
import re

from ml.rolling72_stable_pair_candidate_v1 import prepare_stable_pair_candidate

MAX_INTERVAL_SEALS = 130
MAX_INTERVAL_ATTEMPTS = 512


class VerifiedRecordMismatch(ValueError):
    """Input records fail a cross-record identity, clock, or attempt binding."""


def _int(row: dict[str, Any], key: str) -> int:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise VerifiedRecordMismatch(f"invalid {key}")
    return value


def _dt(value: Any, name: str) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise VerifiedRecordMismatch(f"invalid {name}") from exc
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise VerifiedRecordMismatch(f"{name} must be an aware timestamp")
    return value.astimezone(timezone.utc)


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise VerifiedRecordMismatch(f"invalid {name}")
    return value


def _membership(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("sector_price_area_rows")
    if not isinstance(rows, list) or not rows:
        raise VerifiedRecordMismatch("missing source pair rows")
    keys: list[list[str]] = []
    sectors: set[str] = set()
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise VerifiedRecordMismatch("malformed source pair row")
        sector, area = row.get("sector_source_id"), row.get("price_area_id")
        if any(re.fullmatch(r"[0-9]+", str(x)) is None for x in (sector, area)):
            raise VerifiedRecordMismatch("invalid pair identity")
        key = (str(sector), str(area))
        if key in seen:
            raise VerifiedRecordMismatch("duplicate pair identity")
        seen.add(key)
        sectors.add(key[0])
        keys.append([key[0], key[1]])
    return {"sector_ids": sorted(sectors), "pairs": sorted(keys)}


def _assert_membership(actual: Any, payload: dict[str, Any], name: str) -> None:
    if actual != _membership(payload):
        raise VerifiedRecordMismatch(f"{name} membership does not match sealed payload")


def _normalize_seal(
    seal: dict[str, Any], attempts_by_id: dict[int, dict[str, Any]],
    verified_seal_ids: set[int], verified_attempt_ids: set[int],
    event_id: int, projection_ref: datetime, expected_source_lane_id: str,
) -> dict[str, Any]:
    seal_id = _int(seal, "id")
    attempt_id = _int(seal, "attempt_id")
    if seal_id not in verified_seal_ids or attempt_id not in verified_attempt_ids:
        raise VerifiedRecordMismatch("seal or linked attempt lacks caller verification")
    if _int(seal, "ticket_event_id") != event_id:
        raise VerifiedRecordMismatch("seal ticket_event_id mismatch")
    attempt = attempts_by_id.get(attempt_id)
    if attempt is None or _int(attempt, "id") != attempt_id:
        raise VerifiedRecordMismatch("linked source attempt is absent")
    if _int(attempt, "ticket_event_id") != event_id:
        raise VerifiedRecordMismatch("attempt ticket_event_id mismatch")
    snapshot_id = _int(seal, "snapshot_id")
    if _int(attempt, "snapshot_id") != snapshot_id:
        raise VerifiedRecordMismatch("attempt snapshot_id mismatch")
    for key in ("captured_at", "known_at", "read_started_at", "read_completed_at"):
        if _dt(seal.get(key), f"seal.{key}") != _dt(attempt.get(key), f"attempt.{key}"):
            raise VerifiedRecordMismatch(f"seal/attempt {key} mismatch")
    if not (_dt(seal.get("read_started_at"), "read_started_at")
            <= _dt(seal.get("read_completed_at"), "read_completed_at")
            <= _dt(seal.get("known_at"), "known_at")):
        raise VerifiedRecordMismatch("seal read clocks are out of order")
    source_hash = _digest(seal.get("source_content_sha256"), "seal source hash")
    snapshot_hash = _digest(seal.get("snapshot_sha256"), "seal snapshot hash")
    if _digest(attempt.get("source_content_sha256"), "attempt source hash") != source_hash:
        raise VerifiedRecordMismatch("seal/attempt source digest mismatch")
    if _digest(attempt.get("snapshot_sha256"), "attempt snapshot hash") != snapshot_hash:
        raise VerifiedRecordMismatch("seal/attempt snapshot digest mismatch")
    _digest(attempt.get("attempt_binding_sha256"), "attempt binding hash")
    if attempt.get("status") != "READY":
        raise VerifiedRecordMismatch("sealed source attempt is not READY")
    payload = seal.get("source_payload")
    if not isinstance(payload, dict) or payload != attempt.get("raw_source"):
        raise VerifiedRecordMismatch("seal payload differs from linked raw attempt")
    if payload.get("lane_id") != expected_source_lane_id:
        raise VerifiedRecordMismatch("unexpected source lane")
    if payload.get("source_family") != "roboticket/roboticket" or payload.get("unit") != "available_total_seats":
        raise VerifiedRecordMismatch("source family or unit mismatch")
    binding, snapshot = payload.get("binding"), payload.get("snapshot")
    if not isinstance(binding, dict) or _int(binding, "ticket_event_id") != event_id:
        raise VerifiedRecordMismatch("sealed binding ticket_event_id mismatch")
    if not isinstance(snapshot, dict):
        raise VerifiedRecordMismatch("missing sealed snapshot header")
    if _int(snapshot, "id") != snapshot_id or _int(snapshot, "ticket_event_id") != event_id:
        raise VerifiedRecordMismatch("snapshot header identity mismatch")
    if (_dt(snapshot.get("captured_at"), "snapshot.captured_at")
            != _dt(seal.get("captured_at"), "seal.captured_at")):
        raise VerifiedRecordMismatch("snapshot capture clock mismatch")
    if snapshot.get("available_total") != seal.get("available_total"):
        raise VerifiedRecordMismatch("snapshot inventory total mismatch")
    binding_payload = attempt.get("binding_payload")
    expected_binding = {
        "attempt_id": attempt_id, "run_id": attempt.get("run_id"),
        "lane_id": expected_source_lane_id, "ticket_event_id": event_id,
        "snapshot_id": snapshot_id, "source_content_sha256": source_hash,
        "read_started_at": attempt.get("read_started_at"),
        "read_completed_at": attempt.get("read_completed_at"),
        "known_at": attempt.get("known_at"), "status": "READY",
        "reason": attempt.get("reason"),
    }
    if not isinstance(binding_payload, dict) or binding_payload != expected_binding:
        raise VerifiedRecordMismatch("attempt binding payload mismatch")
    known_at = _dt(seal.get("known_at"), "seal.known_at")
    if known_at > projection_ref:
        raise VerifiedRecordMismatch("seal was not known by the projection reference")
    if _dt(seal.get("captured_at"), "seal.captured_at") > known_at:
        raise VerifiedRecordMismatch("seal capture is after known_at")
    return {
        "seal_id": seal_id,
        "snapshot_id": snapshot_id,
        "event_id": event_id,
        "source_family": payload["source_family"],
        "unit": payload["unit"],
        "captured_at": _dt(seal["captured_at"], "seal.captured_at"),
        "known_at": known_at,
        "available_total": seal["available_total"],
        "sector_price_area_rows": payload["sector_price_area_rows"],
        "source_status": "READY",
        "committed": True,
        "source_content_sha256": source_hash,
        "transition_status": seal.get("transition_status"),
        "gap_count": seal.get("gap_count"),
        "prior_seal_id": seal.get("prior_seal_id"),
        "attempt_id": attempt_id,
    }


def prepare_from_verified_records(
    bundle: dict[str, Any],
    seals: Iterable[dict[str, Any]],
    attempts: Iterable[dict[str, Any]],
    *,
    verified_bundle_ids: set[int],
    verified_seal_ids: set[int],
    verified_attempt_ids: set[int],
    expected_source_lane_id: str,
) -> dict[str, Any]:
    """Bind verified database-shaped inputs, then prepare the existing candidate.

    The `verified_*_ids` are assertions from the upstream read/commit verifier,
    not something this pure adapter derives. Failed attempts known after the
    anchor and by the bundle projection reference veto candidate support over
    the interval, matching the parent source-break rule.
    """
    if not isinstance(bundle, dict):
        raise VerifiedRecordMismatch("bundle must be an object")
    bundle_id = _int(bundle, "id")
    event_id = _int(bundle, "ticket_event_id")
    if not isinstance(expected_source_lane_id, str) or not expected_source_lane_id:
        raise VerifiedRecordMismatch("expected source lane ID is required")
    if bundle_id not in verified_bundle_ids:
        raise VerifiedRecordMismatch("bundle lacks caller verification")
    if bundle.get("fallback_reason") != "SCOPE_MISMATCH":
        raise VerifiedRecordMismatch("candidate adapter only accepts SCOPE_MISMATCH bundles")
    projection_ref = _dt(bundle.get("projection_reference_at"), "projection_reference_at")
    origin_id = _int(bundle, "seal_id")
    anchor_id = _int(bundle, "anchor_seal_id")
    origin_capture = _dt(bundle.get("source_captured_at"), "source_captured_at")
    origin_known = _dt(bundle.get("source_known_at"), "source_known_at")
    anchor_capture = _dt(bundle.get("anchor_captured_at"), "anchor_captured_at")
    anchor_known = _dt(bundle.get("anchor_known_at"), "anchor_known_at")
    if origin_known > projection_ref or anchor_known > projection_ref:
        raise VerifiedRecordMismatch("bundle endpoint not known by projection reference")
    if origin_capture > origin_known or anchor_capture > anchor_known:
        raise VerifiedRecordMismatch("bundle endpoint capture exceeds known_at")
    origin_hash = _digest(bundle.get("source_content_sha256"), "bundle origin source hash")
    origin_membership_hash = _digest(bundle.get("origin_membership_sha256"), "bundle origin membership hash")
    anchor_membership_hash = _digest(bundle.get("anchor_membership_sha256"), "bundle anchor membership hash")

    attempt_rows = list(islice(attempts, MAX_INTERVAL_ATTEMPTS + 1))
    if len(attempt_rows) > MAX_INTERVAL_ATTEMPTS:
        raise VerifiedRecordMismatch("interval attempt cap exceeded")
    attempts_by_id: dict[int, dict[str, Any]] = {}
    for attempt in attempt_rows:
        aid = _int(attempt, "id")
        if aid in attempts_by_id:
            raise VerifiedRecordMismatch("duplicate source attempt id")
        attempts_by_id[aid] = attempt
    raw_seals = list(islice(seals, MAX_INTERVAL_SEALS + 1))
    if len(raw_seals) > MAX_INTERVAL_SEALS:
        raise VerifiedRecordMismatch("interval seal cap exceeded")
    normalized = [
        _normalize_seal(seal, attempts_by_id, verified_seal_ids, verified_attempt_ids,
                        event_id, projection_ref, expected_source_lane_id)
        for seal in raw_seals
    ]
    normalized.sort(key=lambda row: (row["captured_at"], row["snapshot_id"]))
    by_seal = {row["seal_id"]: row for row in normalized}
    if len(by_seal) != len(normalized):
        raise VerifiedRecordMismatch("duplicate seal id")
    origin = by_seal.get(origin_id)
    anchor = by_seal.get(anchor_id)
    if origin is None or anchor is None:
        raise VerifiedRecordMismatch("bundle endpoint seal missing from verified interval")
    if (origin["captured_at"] != origin_capture or origin["known_at"] != origin_known
            or origin["source_content_sha256"] != origin_hash
            or origin["available_total"] != bundle.get("origin_available_total")):
        raise VerifiedRecordMismatch("origin seal does not match bundle boundary")
    if (anchor["captured_at"] != anchor_capture or anchor["known_at"] != anchor_known
            or anchor["available_total"] != bundle.get("anchor_available_total")):
        raise VerifiedRecordMismatch("anchor seal does not match bundle boundary")

    origin_payload = next(seal["source_payload"] for seal in raw_seals if seal["id"] == origin_id)
    anchor_payload = next(seal["source_payload"] for seal in raw_seals if seal["id"] == anchor_id)
    _assert_membership(bundle.get("origin_membership"), origin_payload, "origin")
    _assert_membership(bundle.get("anchor_membership"), anchor_payload, "anchor")

    # Only the seals in the inclusive capture interval and known by the exact
    # bundle projection reference enter candidate arithmetic.
    interval = [row for row in normalized
                if anchor_capture <= row["captured_at"] <= origin_capture
                and row["known_at"] <= projection_ref]
    if len(interval) != len(normalized):
        raise VerifiedRecordMismatch("provided seal set contains rows outside the bundle interval/as-of view")
    adverse = []
    for attempt in attempt_rows:
        if _int(attempt, "ticket_event_id") != event_id:
            raise VerifiedRecordMismatch("attempt ticket_event_id mismatch")
        known = _dt(attempt.get("known_at"), "attempt.known_at")
        if known > projection_ref:
            continue
        captured_value = attempt.get("captured_at")
        captured = _dt(captured_value, "attempt.captured_at") if captured_value is not None else None
        if (known > anchor_known and attempt.get("status") in {
                "MISSING_SOURCE", "SKIPPED_STALE", "INVALID_SOURCE", "INTERNAL_ERROR"}
                and (captured is None or anchor_capture <= captured <= origin_capture)):
            adverse.append(_int(attempt, "id"))
            if _int(attempt, "id") not in verified_attempt_ids:
                raise VerifiedRecordMismatch("adverse source attempt lacks caller verification")

    if not adverse:
        candidate = prepare_stable_pair_candidate(
            origin, interval, anchor_seal_id=anchor_id,
            parent_fallback_reason="SCOPE_MISMATCH",
            projection_reference_at=projection_ref,
        )
    else:
        candidate = prepare_stable_pair_candidate(
            origin, [], anchor_seal_id=anchor_id,
            parent_fallback_reason="SCOPE_MISMATCH",
            projection_reference_at=projection_ref,
        )
        candidate["support_status"] = "KNOWN_FAILED_SOURCE_ATTEMPT"
        candidate["candidate_policy_status"] = "FALLBACK_PERS"
        for row in candidate["forecast_values"]:
            row.update(status="FALLBACK_PERS", prediction=bundle["origin_available_total"],
                       fallback_reason="KNOWN_FAILED_SOURCE_ATTEMPT")

    candidate["provenance"] = {
        "bundle_id": bundle_id,
        "ticket_event_id": event_id,
        "anchor": {"seal_id": anchor_id, "snapshot_id": anchor["snapshot_id"],
                   "attempt_id": anchor["attempt_id"], "captured_at": anchor_capture,
                   "known_at": anchor_known, "source_content_sha256": anchor["source_content_sha256"],
                   "membership_sha256": anchor_membership_hash},
        "origin": {"seal_id": origin_id, "snapshot_id": origin["snapshot_id"],
                   "attempt_id": origin["attempt_id"], "captured_at": origin_capture,
                   "known_at": origin_known, "source_content_sha256": origin_hash,
                   "membership_sha256": origin_membership_hash},
        "projection_reference_at": projection_ref,
        "interval_seal_ids": [row["seal_id"] for row in interval],
        "verified_adverse_attempt_ids": adverse,
        "verification_attested_by_adapter": False,
    }
    return candidate
