"""Offline paired evaluation for the stable-pair full policy.

Input is an explicit intersection of accepted shared-label rows and all three
method outputs from one parent issue. This module validates the replacement
gate and delegates all metrics/bootstrap calculations to the shared paired
scorecard. It cannot establish prospective status, runtime coverage, or source
receipt validity.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from collections.abc import Iterable, Mapping
from typing import Any

from ml.rolling72_paired_drift24_scorecard_v1 import analyze as analyze_pair


SCHEMA_VERSION = "rolling72-stable-pair-offline-paired-evaluation-v1"
OFFLINE_CLAIM = "OFFLINE_PAIRED_LABEL_AUDIT_ONLY"
HORIZONS = (24, 48, 72)
FALLBACK_REASONS = {"NO_24H_ANCHOR", "SCOPE_MISMATCH", "SOURCE_BREAK"}
POLICY_STATUSES = {"INHERITED_DRIFT24", "STABLE_PAIR_OVERRIDE", "INHERITED_PERS"}


def _identity(value: Any, name: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{name} must be a non-empty string or positive integer")
    if isinstance(value, int):
        if value <= 0:
            raise ValueError(f"{name} must be a non-empty string or positive integer")
        return str(value)
    result = value.strip()
    if not result:
        raise ValueError(f"{name} must be a non-empty string or positive integer")
    return result


def _prediction(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite non-negative number")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return value


def _clock(value: Any, name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO-8601 string with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 string with timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be an ISO-8601 string with timezone")
    return parsed.astimezone(timezone.utc)


def _scorecard_rows(facts: list[dict[str, Any]], baseline_key: str, candidate_key: str) -> list[dict[str, Any]]:
    """Map the same accepted facts into the shared scorecard's left/right API."""
    return [{
        "bundle_id": row["bundle_id"], "ticket_event_id": row["ticket_event_id"],
        "club_id": row["club_id"], "horizon_hours": row["horizon_hours"],
        "actual": row["actual"], "pers_prediction": row[baseline_key],
        "drift24_prediction": row[candidate_key],
    } for row in facts]


def _name_scorecard(report: dict[str, Any], baseline: str, candidate: str) -> dict[str, Any]:
    """Replace scorer-specific PERS/DRIFT24 labels with explicit pair roles."""
    named = dict(report)
    horizons = {}
    for horizon, summary in report["horizons"].items():
        if summary is None:
            horizons[horizon] = None
            continue
        item = dict(summary)
        item["baseline_method"] = item.pop("pers")
        item["candidate_method"] = item.pop("drift24")
        item["delta_candidate_minus_baseline"] = item.pop("delta_drift24_minus_pers")
        item["paired_event_deltas"] = [
            {"ticket_event_id": delta["ticket_event_id"],
             "delta_candidate_minus_baseline": delta["delta_mae"]}
            for delta in item["paired_event_deltas"]
        ]
        horizons[horizon] = item
    named["horizons"] = horizons
    primary = dict(report["primary_72h"])
    primary["baseline_event_balanced_mae"] = primary.pop("pers_event_balanced_mae")
    primary["candidate_event_balanced_mae"] = primary.pop("drift24_event_balanced_mae")
    primary["delta_candidate_minus_baseline"] = primary.pop("delta_drift24_minus_pers")
    named["primary_72h"] = primary
    named["pair_roles"] = {"baseline": baseline, "candidate": candidate}
    return named


def _validate(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(rows, (str, bytes, Mapping)):
        raise ValueError("rows must be an iterable of row objects")
    try:
        inputs = list(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of row objects") from exc

    required = {
        "issue_id", "pers_issue_id", "drift24_issue_id", "stable_pair_issue_id", "label_issue_id",
        "label_id", "label_status", "bundle_id", "ticket_event_id", "club_id",
        "horizon_hours", "issued_at", "target_at", "label_target_at", "target_seal_id",
        "actual", "pers_prediction", "drift24_prediction",
        "drift24_status", "parent_fallback_reason", "stable_pair_status",
        "stable_pair_prediction", "stable_pair_support_reason",
    }
    normalized: list[dict[str, Any]] = []
    seen_coords: set[tuple[int, int]] = set()
    seen_labels: set[str] = set()
    issue_coordinates: dict[str, tuple[int, int]] = {}
    coordinate_issues: dict[tuple[int, int], str] = {}
    coordinate_clocks: dict[tuple[int, int], datetime] = {}
    for index, row in enumerate(inputs):
        if not isinstance(row, Mapping):
            raise ValueError(f"rows[{index}] must be an object")
        missing = required - row.keys()
        if missing:
            raise ValueError(f"rows[{index}] missing fields: {', '.join(sorted(missing))}")

        issue = _identity(row["issue_id"], f"rows[{index}].issue_id")
        for field in ("pers_issue_id", "drift24_issue_id", "stable_pair_issue_id", "label_issue_id"):
            if _identity(row[field], f"rows[{index}].{field}") != issue:
                raise ValueError("all methods and label must share the exact issue_id")
        label_id = _identity(row["label_id"], f"rows[{index}].label_id")
        if label_id in seen_labels:
            raise ValueError(f"duplicate label_id: {label_id}")
        seen_labels.add(label_id)
        if row["label_status"] != "SCORED":
            raise ValueError("only accepted SCORED shared labels may be evaluated")

        bundle = row["bundle_id"]
        event = row["ticket_event_id"]
        if type(bundle) is not int or bundle <= 0 or type(event) is not int or event <= 0:
            raise ValueError("bundle_id and ticket_event_id must be positive integers")
        if issue in issue_coordinates and issue_coordinates[issue] != (bundle, event):
            raise ValueError("issue_id must bind to exactly one bundle/event")
        issue_coordinates[issue] = (bundle, event)
        bundle_event = (bundle, event)
        if bundle_event in coordinate_issues and coordinate_issues[bundle_event] != issue:
            raise ValueError("bundle/event must bind to exactly one issue_id across horizons")
        coordinate_issues[bundle_event] = issue
        horizon = row["horizon_hours"]
        if type(horizon) is not int or horizon not in HORIZONS:
            raise ValueError("horizon_hours must be one of 24, 48, 72")
        issued_at = _clock(row["issued_at"], f"rows[{index}].issued_at")
        target_at = _clock(row["target_at"], f"rows[{index}].target_at")
        label_target_at = _clock(row["label_target_at"], f"rows[{index}].label_target_at")
        if target_at != issued_at + timedelta(hours=horizon):
            raise ValueError("target_at must equal issued_at plus horizon_hours")
        if bundle_event in coordinate_clocks and coordinate_clocks[bundle_event] != issued_at:
            raise ValueError("issued_at must be common across horizons for each bundle/event")
        coordinate_clocks[bundle_event] = issued_at
        if label_target_at != target_at:
            raise ValueError("label_target_at must exactly match the shared forecast target")
        target_seal_id = row["target_seal_id"]
        if type(target_seal_id) is not int or target_seal_id <= 0:
            raise ValueError("target_seal_id must be a positive integer")
        coordinate = (bundle, horizon)
        if coordinate in seen_coords:
            raise ValueError(f"duplicate bundle_id/horizon pair: {bundle}/{horizon}")
        seen_coords.add(coordinate)

        club = _identity(row["club_id"], f"rows[{index}].club_id")
        pers = _prediction(row["pers_prediction"], f"rows[{index}].pers_prediction")
        drift = _prediction(row["drift24_prediction"], f"rows[{index}].drift24_prediction")
        stable = _prediction(row["stable_pair_prediction"], f"rows[{index}].stable_pair_prediction")
        drift_status = row["drift24_status"]
        fallback = row["parent_fallback_reason"]
        policy = row["stable_pair_status"]
        support_reason = row["stable_pair_support_reason"]

        if policy not in POLICY_STATUSES:
            raise ValueError("outside-kickoff or unknown stable-pair rows cannot have scored labels")
        if drift_status == "READY" and fallback is None:
            if policy != "INHERITED_DRIFT24" or stable != drift:
                raise ValueError("READY DRIFT24 must be inherited exactly")
        elif drift_status == "FALLBACK_PERS" and fallback in FALLBACK_REASONS:
            if drift != pers:
                raise ValueError("parent PERS fallback must equal the exact PERS prediction")
            if policy == "STABLE_PAIR_OVERRIDE":
                if fallback != "SCOPE_MISMATCH" or support_reason != "SUPPORTED":
                    raise ValueError("stable-pair override requires supported SCOPE_MISMATCH")
            elif policy == "INHERITED_PERS":
                if stable != pers:
                    raise ValueError("unsupported or ineligible policy must retain exact PERS")
                if support_reason == "SUPPORTED":
                    raise ValueError("SUPPORTED candidate must use STABLE_PAIR_OVERRIDE")
            else:
                raise ValueError("fallback parent cannot be reported as inherited DRIFT24")
        else:
            raise ValueError("parent DRIFT24 status and fallback reason disagree")

        normalized.append({
            "issue_id": issue,
            "label_id": label_id,
            "target_seal_id": target_seal_id,
            "bundle_id": bundle,
            "ticket_event_id": event,
            "club_id": club,
            "horizon_hours": horizon,
            "actual": _prediction(row["actual"], f"rows[{index}].actual"),
            "pers_prediction": pers,
            "drift24_prediction": drift,
            "stable_pair_prediction": stable,
            "stable_pair_status": policy,
        })
    return normalized


def analyze(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate the exact cohort and return primary/secondary paired scorecards."""
    facts = _validate(rows)
    primary = _name_scorecard(
        analyze_pair(_scorecard_rows(facts, "pers_prediction", "stable_pair_prediction")),
        "PERS", "STABLE_PAIR_POLICY",
    )
    secondary = _name_scorecard(
        analyze_pair(_scorecard_rows(facts, "drift24_prediction", "stable_pair_prediction")),
        "DRIFT24", "STABLE_PAIR_POLICY",
    )
    drift24_vs_pers = _name_scorecard(
        analyze_pair(_scorecard_rows(facts, "pers_prediction", "drift24_prediction")),
        "PERS", "DRIFT24",
    )
    statuses = {status: sum(row["stable_pair_status"] == status for row in facts)
                for status in sorted(POLICY_STATUSES)}
    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_claim": OFFLINE_CLAIM,
        "prospective_claim": False,
        "runtime_coverage": "UNKNOWN",
        "accepted_shared_label_rows": len(facts),
        "distinct_events": len({row["ticket_event_id"] for row in facts}),
        "policy_status_counts": statuses,
        "cohort": "exact validated input intersection; identical rows for all three comparisons",
        "comparison_semantics": {
            "primary": {"baseline_method": "PERS", "candidate_method": "STABLE_PAIR_POLICY"},
            "secondary": {"baseline_method": "DRIFT24", "candidate_method": "STABLE_PAIR_POLICY"},
            "parent_baseline": {"baseline_method": "PERS", "candidate_method": "DRIFT24"},
            "scorecard_decisions_are_descriptive_only": True,
        },
        "primary_stable_pair_vs_pers": primary,
        "secondary_stable_pair_vs_drift24": secondary,
        "parent_drift24_vs_pers": drift24_vs_pers,
    }
