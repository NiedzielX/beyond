"""Precommitted rolling72 benchmarks, isolated from all frozen daily ledgers.

These pure functions do not persist forecasts or fit the learned challenger.
Training rows contain ``issue``, a full ``matched_label`` from the genuine-label
matcher, ``fixture_group`` from the archived identity registry, and declared
``source_lineage``. The parent archive builder must validate original receipt
bytes and registry membership. Clock/hash checks here do not independently
authenticate those external sources or prove an unchanged released pool.

Pickup has its own five-fixture/three-club cell gate; the learned candidate's
60-row/all-horizon gate is deliberately not applied to this separate baseline.
No real pickup fit is authorised by these functions alone: the pinned precommit,
actual source evidence and caller's declared training purpose still apply.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import re

from ml.demand_engine.rolling72_features_v1 import HORIZONS, _count, _hash, _id, _time, features
from ml.demand_engine.rolling72_labels_v1 import VERSION as LABEL_VERSION


VERSION = "rolling72-baselines-v1"
PICKUP_ARTIFACT_VERSION = "rolling72-conditional-pickup-artifact-v1"
PRECOMMIT_SHA256 = "9fc87bf69f796d644585ea0a5dc96800cb4322d42ad523cab2a75fb3ef5a7bc0"
PRECOMMIT_PATH = Path(__file__).parents[1] / "artifacts" / "rolling72_v1" / "precommit.json"
MEASUREMENT_PREFIX = "public-displayed-available-total-v1:"


def load_precommit() -> dict:
    payload = json.loads(PRECOMMIT_PATH.read_text())
    calculated = _hash({key: value for key, value in payload.items() if key != "precommit_sha256"})
    if payload.get("precommit_sha256") != PRECOMMIT_SHA256 or calculated != PRECOMMIT_SHA256:
        raise ValueError("Pinned rolling72 precommit hash mismatch")
    return payload


def source_family(issue: dict) -> str | None:
    """Accept exact declared keys, optionally with the receipt adapter namespace."""
    key = issue.get("measurement_key")
    if not isinstance(key, str):
        return None
    if key.startswith(MEASUREMENT_PREFIX):
        key = key[len(MEASUREMENT_PREFIX):]
    return key if key in load_precommit()["source_families"] else None


def maturity_cell(hours_to_kickoff: float) -> int:
    days = float(hours_to_kickoff) / 24
    if not math.isfinite(days) or days <= 0:
        raise ValueError("A maturity cell requires a pre-kickoff issue")
    return max(boundary for boundary in load_precommit()["pickup"]["maturity_bins_days"]
               if days >= boundary)


def _sha(value, name):
    if not isinstance(value, str) or re.fullmatch("[a-f0-9]{64}", value) is None:
        raise ValueError(f"Invalid {name} SHA256")
    return value


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"Invalid finite {name}")
    return float(value)


def _close(left, right):
    return math.isclose(_number(left, "label statistic"), float(right), rel_tol=1e-12, abs_tol=1e-10)


def validated_training_rows(rows: list[dict], fit_cutoff_at=None) -> list[dict]:
    """Check canonical declared receipt-bound rows, without independent attestation.

    The caller proves the hash-bound original receipts and fixture registry.
    This helper refuses incompatible schema/clocks, ongoing fixtures, unknown
    identities and duplicate fixture/issue/horizon examples before fitting.
    It never substitutes capture times for missing knowledge clocks.
    """
    precommit = load_precommit()
    cutoff = _time(precommit["fit_cutoff_at"])
    if fit_cutoff_at is not None and _time(fit_cutoff_at) != cutoff:
        raise ValueError("Fit cutoff differs from pinned precommit")
    if not isinstance(rows, list):
        raise ValueError("Training rows must be a list")
    cleaned, seen, group_club, event_group = [], set(), {}, {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Training row must be an object")
        issue, matched = row.get("issue"), row.get("matched_label")
        group, lineage = row.get("fixture_group"), row.get("source_lineage")
        if not isinstance(group, str) or not group.strip():
            raise ValueError("Verified fixture group required")
        if not isinstance(lineage, dict) or lineage.get("identity_proven") is not True:
            raise ValueError("Verified source identity declaration required")
        if lineage.get("evidence") != "original-receipt-known-bounds-only":
            raise ValueError("Original receipt evidence required")
        for key in ("input_receipt_sha256", "label_receipt_sha256", "identity_registry_sha256"):
            _sha(lineage.get(key), key)
        input_known = _time(lineage.get("input_receipt_known_at"))
        label_known = _time(lineage.get("label_receipt_known_at"))
        if not isinstance(matched, dict) or matched.get("version") != LABEL_VERSION or matched.get("status") != "MATCHED":
            raise ValueError("A genuine matched label is required")
        horizon = matched.get("horizon_hours")
        coordinate = features(issue, horizon)
        if coordinate["status"] != "READY":
            raise ValueError("Only READY issue/horizon rows may train pickup")
        issued, target = _time(issue["issued_at"]), _time(coordinate["target_at"])
        kickoff = _time(issue["event"]["kickoff_at"])
        if (kickoff >= cutoff or label_known > cutoff or input_known > issued
                or target > label_known or issued >= target):
            raise ValueError("Training must use completed fixtures and labels known by cutoff")
        if (_time(issue["event"]["known_at"]) != input_known
                or any(_time(item["known_at"]) != input_known for item in issue["observed_prefix"])):
            raise ValueError("Input receipt knowledge bound differs from issue")
        if (matched.get("input_manifest_sha256") != issue["input_manifest_sha256"]
                or matched.get("target_at") != coordinate["target_at"]
                or _time(matched.get("available_by")) != label_known):
            raise ValueError("Matched label belongs to a different issue/receipt")
        if (matched.get("production_change") is not False or matched.get("live_adjustment") != 0
                or matched.get("model_fit_performed") is not False):
            raise ValueError("Unexpected label contract flags")
        label = matched.get("label")
        if not isinstance(label, dict) or matched.get("label_sha256") != _hash(label):
            raise ValueError("Matched label hash mismatch")
        capture, known = _time(label.get("captured_at")), _time(label.get("known_at"))
        if not issued < capture <= target or known != label_known or known < capture:
            raise ValueError("Label capture/knowledge clocks are incompatible")
        staleness = (target - capture).total_seconds() / 3600
        elapsed = (capture - issued).total_seconds() / 3600
        if staleness > precommit["matching"]["max_target_staleness_hours"]:
            raise ValueError("Label exceeds the precommitted target tolerance")
        if (label.get("measurement_key") != issue["measurement_key"]
                or label.get("source_active") is False or label.get("source_visible") is False):
            raise ValueError("Incompatible label measurement or source state")
        for flag in ("source_active", "source_visible"):
            value = label.get(flag)
            if value is not None and not isinstance(value, bool):
                raise ValueError("Invalid label source-state flag")
        label_value = _count(label.get("available_total"))
        _id(label.get("snapshot_id"))
        delta = label_value - issue["last_available_total"]
        if (not _close(label.get("target_staleness_hours"), staleness)
                or not _close(label.get("actual_elapsed_since_issue_hours"), elapsed)
                or not _close(label.get("delta_from_last_observation"), delta)):
            raise ValueError("Label statistics differ from their genuine coordinates")
        family = source_family(issue)
        if family is None:
            raise ValueError("Training source family is not precommitted")
        club = issue["event"]["club_slug"]
        group = group.strip()
        event_id = issue["event"]["ticket_event_id"]
        if event_id in event_group and event_group[event_id] != group:
            raise ValueError("One event identity cannot inflate independent fixture groups")
        event_group[event_id] = group
        if group in group_club and group_club[group] != club:
            raise ValueError("One fixture group cannot inflate support using multiple clubs")
        group_club[group] = club
        identity = group, issue["issued_at"], horizon
        if identity in seen:
            raise ValueError("Duplicate fixture issue/horizon training row")
        seen.add(identity)
        cleaned.append({"issue": issue, "matched_label": matched, "fixture_group": group,
                        "club_slug": club, "event_id": event_id,
                        "source_family": family, "horizon_hours": horizon,
                        "maturity_cell": maturity_cell(coordinate["features"]["hours_to_kickoff"]),
                        "delta": delta, "source_lineage": lineage})
    return cleaned


def event_balanced_median(rows: list[dict]) -> float:
    """Lower weighted median; each fixture has total weight one, exactly."""
    if not rows:
        raise ValueError("At least one row is required for a median")
    counts = Counter(row["fixture_group"] for row in rows)
    total = len(counts)
    cumulative = Fraction(0)
    for row in sorted(rows, key=lambda item: (_number(item["delta"], "delta"), item["fixture_group"])):
        cumulative += Fraction(1, counts[row["fixture_group"]])
        if cumulative * 2 >= total:
            return float(row["delta"])
    raise AssertionError("Weighted median support was inconsistent")


def fit_pickup(training_rows: list[dict], fit_cutoff_at=None) -> dict:
    """Build only cells passing their pinned engineering gate; never tune it."""
    precommit = load_precommit()
    rows = validated_training_rows(training_rows, fit_cutoff_at)
    groups = defaultdict(list)
    for row in rows:
        groups[(row["source_family"], row["horizon_hours"], row["maturity_cell"])].append(row)
        groups[(row["source_family"], row["horizon_hours"], None)].append(row)
    cells = []
    for (family, horizon, maturity), selected in sorted(groups.items(), key=lambda pair: (
            pair[0][0], pair[0][1], -1 if pair[0][2] is None else pair[0][2])):
        fixture_groups = sorted({row["fixture_group"] for row in selected})
        clubs = sorted({row["club_slug"] for row in selected})
        supported = (len(fixture_groups) >= precommit["pickup"]["min_fixtures"]
                     and len(clubs) >= precommit["pickup"]["min_clubs"])
        cells.append({"source_family": family, "horizon_hours": horizon, "maturity_cell": maturity,
                      "fixture_groups": fixture_groups, "club_slugs": clubs,
                      "fixture_count": len(fixture_groups), "club_count": len(clubs),
                      "row_count": len(selected), "supported": supported,
                      "median_delta": event_balanced_median(selected) if supported else None})
    supported = any(cell["supported"] for cell in cells)
    lineage_digest = [{"fixture_group": row["fixture_group"], "input_sha256": row["issue"]["input_manifest_sha256"],
                       "label_sha256": row["matched_label"]["label_sha256"], "horizon_hours": row["horizon_hours"],
                       "source_lineage": row["source_lineage"]} for row in rows]
    lineage_digest.sort(key=_hash)
    artifact = {
        "version": PICKUP_ARTIFACT_VERSION, "model_id": precommit["pickup"]["id"],
        "status": "FIT_SUPPORTED_LOOKUPS" if supported else "NO_FIT_INSUFFICIENT_SUPPORT",
        "precommit_sha256": PRECOMMIT_SHA256, "fit_cutoff_at": precommit["fit_cutoff_at"],
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "training_fixture_groups": sorted({row["fixture_group"] for row in rows}),
        "training_ticket_event_ids": sorted({row["event_id"] for row in rows}),
        "training_row_count": len(rows), "training_rows_sha256": _hash(lineage_digest),
        "source_lineage_independently_attested": False,
        "support_cells": cells, "cells": [cell for cell in cells if cell["supported"]],
        "production_change": False, "live_adjustment": 0,
    }
    artifact["artifact_sha256"] = _hash(artifact)
    return artifact


def _validate_pickup(artifact):
    precommit = load_precommit()
    if (not isinstance(artifact, dict) or artifact.get("version") != PICKUP_ARTIFACT_VERSION
            or artifact.get("precommit_sha256") != PRECOMMIT_SHA256
            or artifact.get("artifact_sha256") != _hash({key: value for key, value in artifact.items()
                                                       if key != "artifact_sha256"})):
        raise ValueError("Pickup artifact hash/version mismatch")
    if (artifact.get("fit_cutoff_at") != precommit["fit_cutoff_at"]
            or artifact.get("production_change") is not False or artifact.get("live_adjustment") != 0
            or artifact.get("status") not in {"FIT_SUPPORTED_LOOKUPS", "NO_FIT_INSUFFICIENT_SUPPORT"}):
        raise ValueError("Pickup artifact contract mismatch")
    if _time(artifact["frozen_at"]) < _time(artifact["fit_cutoff_at"]):
        raise ValueError("Pickup freeze precedes its training cutoff")
    if artifact["status"] == "NO_FIT_INSUFFICIENT_SUPPORT" and artifact["cells"]:
        raise ValueError("Unsupported pickup artifact cannot carry fitted lookup cells")
    if artifact["status"] == "FIT_SUPPORTED_LOOKUPS" and not artifact["cells"]:
        raise ValueError("Supported pickup artifact must contain a fitted lookup")
    identities = set()
    for cell in artifact["cells"]:
        identity = cell["source_family"], cell["horizon_hours"], cell["maturity_cell"]
        if identity in identities:
            raise ValueError("Duplicate pickup cell")
        identities.add(identity)
        if (cell["source_family"] not in precommit["source_families"]
                or cell["horizon_hours"] not in HORIZONS
                or cell["maturity_cell"] not in (None, *precommit["pickup"]["maturity_bins_days"])
                or cell.get("supported") is not True
                or cell["fixture_count"] != len(set(cell["fixture_groups"]))
                or cell["club_count"] != len(set(cell["club_slugs"]))
                or cell["fixture_count"] < precommit["pickup"]["min_fixtures"]
                or cell["club_count"] < precommit["pickup"]["min_clubs"]):
            raise ValueError("Unsupported/inconsistent pickup cell")
        _number(cell["median_delta"], "pickup median")


def _prediction(model_id, last=None, raw_delta=None, reason=None, **metadata):
    ready = reason is None and last is not None and raw_delta is not None
    if ready and (not math.isfinite(raw_delta) or not math.isfinite(last + raw_delta)):
        ready, reason = False, "NUMERIC_PREDICTION_INVALID"
    value = max(0.0, last + raw_delta) if ready else None
    return {"model_id": model_id, "status": "READY" if ready else "UNAVAILABLE",
            "status_reason": reason, "predicted_available_total": value,
            "predicted_delta": value - last if ready else None,
            "raw_predicted_delta": raw_delta if ready else None, **metadata}


def predict_baselines(issue: dict, pickup_artifact=None, *, fixture_group: str | None = None) -> dict:
    """Return three nominal horizons; failures never masquerade as persistence.

    Only a later independent ledger can establish a prospective issued forecast.
    For supported pickup, caller supplies the same verified registry group used
    for training; missing identity disables pickup rather than risking aliases.
    """
    precommit = load_precommit()
    if pickup_artifact is not None:
        _validate_pickup(pickup_artifact)
    result = {"version": VERSION, "precommit_sha256": PRECOMMIT_SHA256,
              "input_manifest_sha256": issue["input_manifest_sha256"], "points": [],
              "scenario_stability": "UNKNOWN", "target": precommit["target"],
              "evidence_kind": "prediction_payload_only_not_prospective_evidence",
              "production_change": False, "live_adjustment": 0}
    for horizon in HORIZONS:
        coordinate = features(issue, horizon)
        point = {"horizon_hours": horizon, "target_at": coordinate["target_at"],
                 "status": coordinate["status"], "source_family": source_family(issue), "models": {}}
        if coordinate["status"] != "READY":
            point["models"] = {name: _prediction(precommit[name]["id"], reason=coordinate["status"])
                               for name in ("persistence", "drift", "pickup")}
            result["points"].append(point)
            continue
        last = coordinate["features"]["last_available_total"]
        point["models"]["persistence"] = _prediction(precommit["persistence"]["id"], last, 0.0)
        hourly = {}
        for observation in issue["observed_prefix"]:
            capture = _time(observation["captured_at"])
            hourly[capture.replace(minute=0, second=0, microsecond=0)] = observation
        compressed = list(hourly.values())
        span = (_time(compressed[-1]["captured_at"]) - _time(compressed[0]["captured_at"])).total_seconds() / 3600
        drift_meta = {"hourly_point_count": len(compressed), "hourly_prefix_span_hours": span}
        reason = None
        if len(compressed) < precommit["drift"]["min_hourly_points"] or span < precommit["drift"]["min_hourly_prefix_span_hours"]:
            reason = "DRIFT_HOURLY_SUPPORT_INSUFFICIENT"
        elif coordinate["features"]["slope_24h"] is None:
            reason = "DRIFT_ANCHOR_INSUFFICIENT"
        if reason is not None:
            point["models"]["drift"] = _prediction(precommit["drift"]["id"], reason=reason, **drift_meta)
        else:
            elapsed = horizon + coordinate["features"]["latest_staleness_hours"]
            slope = coordinate["features"]["slope_24h"]
            point["models"]["drift"] = _prediction(precommit["drift"]["id"], last, slope * elapsed,
                                                      slope_places_per_hour=slope, elapsed_forecast_hours=elapsed,
                                                      anchor=coordinate["window_lineage"]["24"], **drift_meta)
        artifact = pickup_artifact
        reason, selected = "PICKUP_ARTIFACT_UNAVAILABLE", None
        if artifact is not None:
            reason = "PICKUP_SUPPORT_INSUFFICIENT"
            if artifact["status"] == "FIT_SUPPORTED_LOOKUPS":
                if _time(artifact["frozen_at"]) > _time(issue["issued_at"]):
                    reason = "PICKUP_ARTIFACT_NOT_KNOWN_AS_OF"
                elif issue["event"]["ticket_event_id"] in artifact["training_ticket_event_ids"]:
                    reason = "CURRENT_FIXTURE_IN_TRAINING"
                elif not isinstance(fixture_group, str) or not fixture_group.strip():
                    reason = "INFERENCE_FIXTURE_IDENTITY_UNPROVEN"
                elif fixture_group.strip() in artifact["training_fixture_groups"]:
                    reason = "CURRENT_FIXTURE_IN_TRAINING"
                else:
                    cell = maturity_cell(coordinate["features"]["hours_to_kickoff"])
                    for candidate_maturity in (cell, None):
                        selected = next((item for item in artifact["cells"]
                                         if item["source_family"] == point["source_family"]
                                         and item["horizon_hours"] == horizon
                                         and item["maturity_cell"] == candidate_maturity), None)
                        if selected is not None:
                            break
                    if selected is not None:
                        reason = None
        if selected is None:
            point["models"]["pickup"] = _prediction(precommit["pickup"]["id"], reason=reason,
                                                       artifact_sha256=artifact["artifact_sha256"] if artifact else None)
        else:
            point["models"]["pickup"] = _prediction(
                precommit["pickup"]["id"], last, selected["median_delta"],
                artifact_sha256=artifact["artifact_sha256"],
                route="MATURITY_CELL" if selected["maturity_cell"] is not None else "POOLED_HORIZON",
                maturity_conditioning_used=selected["maturity_cell"] is not None,
                support_fixture_count=selected["fixture_count"], support_club_count=selected["club_count"],
                support_row_count=selected["row_count"])
        result["points"].append(point)
    return result
