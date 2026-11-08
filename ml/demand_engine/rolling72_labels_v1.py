"""Genuine rolling72 labels as known by a declared scoring/training cutoff.

This pure matcher never persists forecasts, fits a model or creates prospective
evidence. Capture-time and knowledge-time must both be available. An immutable
issued forecast and a later original source receipt are still required for an
actual prospective score. Input schema is rolling72_features_v1's event schema.
"""
from __future__ import annotations

from datetime import timedelta

from ml.demand_engine.rolling72_features_v1 import (
    EVENT_FIELDS, ROW_FIELDS, ROW_REQUIRED, _count, _hash, _id, _time, features,
)


VERSION = "rolling72-genuine-labels-v1"
MAX_TARGET_STALENESS_HOURS = 6


def match_target(event: dict, issue: dict, horizon_hours: int, available_by) -> dict:
    """Match latest known real capture <= target, never interpolate or fallback.

    The scoring cutoff must be >= nominal target, even when an observation
    within the six-hour pre-target tolerance is already present earlier.
    Measurements later than target or known after cutoff do not enter value
    validation, hashes or identity conflicts. Malformed clocks raise because
    their knowledge membership cannot be established. All known identities in
    (issue,target] must be consistent; a changed pool/source that later returns
    to the original key cannot silently become a comparable same-key endpoint.
    """
    coordinate = features(issue, horizon_hours)  # Verify issue hash and schema.
    cutoff = _time(available_by)
    issued = _time(issue["issued_at"])
    if cutoff < issued:
        raise ValueError("Label cutoff precedes issue")
    result = {
        "version": VERSION, "input_manifest_sha256": issue["input_manifest_sha256"],
        "horizon_hours": horizon_hours, "target_at": coordinate["target_at"],
        "available_by": cutoff.isoformat(), "status": coordinate["status"],
        "label": None, "label_sha256": None,
        "evidence_kind": "source_match_only_not_proof_of_prospective_forecast",
        "production_change": False, "live_adjustment": 0, "model_fit_performed": False,
    }
    if coordinate["status"] != "READY":
        return result
    target = _time(coordinate["target_at"])
    if cutoff < target:
        result["status"] = "PENDING_TARGET"
        return result
    if not isinstance(event, dict) or set(event) != EVENT_FIELDS:
        raise ValueError("Exact declared event schema required")
    if _time(event["known_at"]) > cutoff:
        result["status"] = "LABEL_EVENT_NOT_KNOWN"
        return result
    original = issue["event"]
    if (_id(event["ticket_event_id"]) != original["ticket_event_id"]
            or not isinstance(event["club_slug"], str)
            or event["club_slug"].strip() != original["club_slug"]
            or _time(event["kickoff_at"]) != _time(original["kickoff_at"])):
        result["status"] = "EVENT_METADATA_CHANGED"
        return result
    observations = event["observations"]
    if not isinstance(observations, list):
        raise ValueError("Observation list required")
    candidates = []
    for raw in observations:
        if not isinstance(raw, dict):
            raise ValueError("Observation timing requires an object")
        captured, known = _time(raw.get("captured_at")), _time(raw.get("known_at"))
        if known < captured:
            raise ValueError("Observation known_at precedes captured_at")
        if issued < captured <= target and known <= cutoff:
            candidates.append((captured, known, raw))
    if not candidates:
        result["status"] = "NO_KNOWN_FUTURE_OBSERVATION"
        return result
    candidates.sort(key=lambda item: (item[0], _id(item[2].get("snapshot_id"))))
    seen = {}
    prefix_ids = {row["snapshot_id"] for row in issue["observed_prefix"]}
    for captured, known, raw in candidates:
        identifier = _id(raw.get("snapshot_id"))
        if identifier in prefix_ids or (identifier in seen and seen[identifier] != raw):
            result["status"] = "CONFLICTING_OBSERVATION_IDENTITY"
            return result
        seen[identifier] = raw
        key = raw.get("measurement_key")
        if not isinstance(key, str) or not key.strip():
            result["status"] = "INVALID_LABEL_IDENTITY"
            return result
        if key.strip() != issue["measurement_key"]:
            result["status"] = "MEASUREMENT_CHANGED"
            return result
    captured, known, raw = candidates[-1]
    staleness = (target - captured).total_seconds() / 3600
    if staleness > MAX_TARGET_STALENESS_HOURS:
        result["status"] = "STALE_TARGET_OBSERVATION"
        return result
    try:
        if set(raw) - ROW_FIELDS or not ROW_REQUIRED <= set(raw):
            raise ValueError("Exact declared observation schema required")
        flags = {key: raw.get(key) for key in ("source_active", "source_visible")}
        if any(value is not None and not isinstance(value, bool) for value in flags.values()):
            raise ValueError("Source flags must be boolean or null")
        if any(value is False for value in flags.values()):
            result["status"] = "TARGET_SOURCE_UNUSABLE"
            return result
        value = _count(raw["available_total"])
    except ValueError:
        result["status"] = "INVALID_TARGET_OBSERVATION"
        return result
    result["label"] = {
        "snapshot_id": raw["snapshot_id"], "captured_at": captured.isoformat(),
        "known_at": known.isoformat(), "available_total": value,
        "measurement_key": issue["measurement_key"], **flags,
        "target_staleness_hours": staleness,
        "actual_elapsed_since_issue_hours": (captured - issued).total_seconds() / 3600,
        "delta_from_last_observation": value - issue["last_available_total"],
    }
    result["label_sha256"] = _hash(result["label"])
    result["status"] = "MATCHED"
    return result
