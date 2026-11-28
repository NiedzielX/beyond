"""Compose the full offline stable-pair policy on exact parent issue rows."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from typing import Any, Iterable

from ml.rolling72_stable_pair_candidate_v1 import HORIZONS, VERSION


def _clock(value: datetime | str) -> datetime:
    instant = datetime.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(instant, datetime) or instant.utcoffset() is None:
        raise ValueError("issue clocks must include a time zone")
    return instant.astimezone(timezone.utc)


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _index(rows: Iterable[dict], keys: tuple[str, ...]) -> dict:
    indexed = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key in indexed:
            raise ValueError("duplicate issue coordinate")
        indexed[key] = row
    return indexed


def compose_stable_pair_policy(
    bundle: dict, parent_predictions: Iterable[dict], candidate: dict | None = None,
) -> list[dict]:
    """Produce three full-policy rows on a single parent bundle's exact clocks.

    The input is an offline export. This does not attest the parent's receipt,
    create a prospective issue or select a target label.
    """
    parents = _index(parent_predictions, ("method", "horizon_hours"))
    if set(parents) != {(m, h) for m in ("PERS", "DRIFT24") for h in HORIZONS}:
        raise ValueError("one PERS and DRIFT24 row is required at each horizon")

    issued = _clock(bundle["issued_at"])
    reference = _clock(bundle["projection_reference_at"])
    captured = _clock(bundle["source_captured_at"])
    known = _clock(bundle["source_known_at"])
    if not captured <= known <= reference <= issued:
        raise ValueError("source and issue clocks are out of order")
    if issued - reference > timedelta(seconds=90) or issued - captured > timedelta(hours=1):
        raise ValueError("issue latency or source age exceeds its limit")

    replacement = {}
    candidate_reason = "MISSING_CANDIDATE_INPUT"
    if candidate is not None:
        if (candidate["version"] != VERSION
                or bundle["fallback_reason"] != "SCOPE_MISMATCH"
                or candidate["eligible_parent_fallback"] is not True
                or candidate["event_id"] != bundle["ticket_event_id"]
                or candidate["origin_seal_id"] != bundle["seal_id"]
                or candidate["anchor_seal_id"] != bundle["anchor_seal_id"]
                or candidate["origin_available_total"] != bundle["origin_available_total"]
                or _clock(candidate["projection_reference_at"]) != reference):
            raise ValueError("candidate does not bind to this scope mismatch bundle")
        candidate_reason = candidate["support_status"]
        candidate_status = candidate["candidate_policy_status"]
        if candidate_status == "SUPPORTED":
            if candidate_reason != "SUPPORTED":
                raise ValueError("candidate support status disagrees")
            replacement = _index(candidate["forecast_values"], ("horizon_hours",))
            if set(replacement) != {(h,) for h in HORIZONS} or any(
                v["status"] != "READY" or not _number(v["prediction"])
                for v in replacement.values()
            ):
                raise ValueError("supported candidate lacks complete numeric forecasts")
        elif candidate_status not in {"FALLBACK_PERS", "ZERO_ORIGIN"}:
            raise ValueError("unsupported candidate status")

    kickoff = _clock(bundle["kickoff_at"])
    decisions = []
    for horizon in HORIZONS:
        pers, drift = parents["PERS", horizon], parents["DRIFT24", horizon]
        target = issued + timedelta(hours=horizon)
        for parent in (pers, drift):
            if (parent["bundle_id"] != bundle["id"]
                    or parent["ticket_event_id"] != bundle["ticket_event_id"]
                    or _clock(parent["issued_at"]) != issued
                    or _clock(parent["target_at"]) != target):
                raise ValueError("parent issue identity or clocks disagree")
        reason = override_reason = None
        if target >= kickoff:
            if any(p["status"] != "OUTSIDE_KICKOFF" or p["prediction"] is not None
                   for p in (pers, drift)):
                raise ValueError("parents disagree with kickoff eligibility")
            status, prediction = "OUTSIDE_KICKOFF", None
        elif (pers["status"] != "READY" or not _number(pers["prediction"])
              or pers["prediction"] != bundle["origin_available_total"]
              or pers["fallback_reason"] is not None or not _number(drift["prediction"])):
            raise ValueError("incomplete numeric parent pair")
        elif (drift["status"] == bundle["drift_status"] == "READY"
              and drift["fallback_reason"] is None and bundle["fallback_reason"] is None):
            status, prediction = "INHERITED_DRIFT24", drift["prediction"]
        elif (drift["status"] == bundle["drift_status"] == "FALLBACK_PERS"
              and drift["fallback_reason"] == bundle["fallback_reason"]
              and drift["fallback_reason"] in {"NO_24H_ANCHOR", "SCOPE_MISMATCH", "SOURCE_BREAK"}
              and drift["prediction"] == pers["prediction"] == bundle["origin_available_total"]):
            if replacement:
                status, prediction = "STABLE_PAIR_OVERRIDE", replacement[horizon,]["prediction"]
                override_reason = candidate_reason
            else:
                status, prediction = "INHERITED_PERS", pers["prediction"]
                reason = bundle["fallback_reason"]
                if reason == "SCOPE_MISMATCH":
                    override_reason = candidate_reason
        else:
            raise ValueError("parent drift status or fallback disagrees")
        decisions.append({
            "bundle_id": bundle["id"], "ticket_event_id": bundle["ticket_event_id"],
            "horizon_hours": horizon, "issued_at": issued, "target_at": target,
            "method": "STABLE_PAIR", "status": status, "prediction": prediction,
            "fallback_reason": reason, "stable_pair_support_reason": override_reason,
        })
    return decisions
