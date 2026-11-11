"""Direct daily public-inventory forecasts; isolated from frozen attendance lanes.

The fitting procedure is fixed in DAILY_INVENTORY_PATH_PRECOMMIT_V1.md.
Only sklearn fitting needs sklearn; deployed prediction uses JSON coefficients.
Neither fitting nor preview prediction writes prospective evidence.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np


MODEL_VERSION = "daily-inventory-direct-median-v1"
BASELINE_VERSION = "daily-inventory-persistence-v1"
FEATURE_VERSION = "daily-inventory-prefix-60bins-lead-interactions-v1"
FEATURE_COUNT = 250
PRECOMMIT_ID = "daily-inventory-path-v1"
MIN_TRAIN_EVENTS = 5
QUANTILE = 0.5
ALPHA = 0.01
UTC = timezone.utc


def _time(value: str | datetime) -> datetime:
    result = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timestamps must contain an explicit timezone")
    return result.astimezone(UTC)


def _iso(value: str | datetime) -> str:
    return _time(value).isoformat()


def _number(value: Any, name: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or (nonnegative and result < 0):
        raise ValueError(f"Invalid {name}")
    return result


def _integer(value: Any, name: str, *, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or int(value) < minimum:
        raise ValueError(f"Invalid {name}")
    return int(value)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def artifact_sha256(artifact: dict[str, Any]) -> str:
    """Canonical JSON hash excluding only the artifact's self-hash."""
    return _canonical_hash({key: value for key, value in artifact.items() if key != "model_sha256"})


def _validate_issue(issue: dict[str, Any]) -> tuple[datetime, datetime, list[dict[str, Any]], float]:
    if issue.get("status") != "READY":
        raise ValueError("Only a READY issue can be used by the model")
    _integer(issue.get("ticket_event_id"), "ticket_event_id")
    days = _integer(issue.get("days_to_event"), "days_to_event")
    if days > 60:
        raise ValueError("Issue is outside P-60…P-1")
    issued = _time(issue["issued_as_of_at"])
    kickoff = _time(issue["kickoff_at"])
    if kickoff - issued != timedelta(days=days):
        raise ValueError("Issue must be an exact kickoff-relative daily cutoff")
    measurement = issue.get("measurement_key")
    if not isinstance(measurement, str) or not measurement.strip():
        raise ValueError("An explicit measurement identity is required")
    prefix = issue.get("observed_prefix")
    if not isinstance(prefix, list) or len(prefix) < 4:
        raise ValueError("At least four genuine prefix observations are required")
    captures: list[datetime] = []
    values: list[float] = []
    ids: set[int] = set()
    buckets: set[int] = set()
    for observation in prefix:
        capture = _time(observation["captured_at"])
        snapshot_id = _integer(observation.get("snapshot_id"), "snapshot_id")
        if capture > issued or capture < kickoff - timedelta(days=60):
            raise ValueError("Prefix contains future or out-of-contract observations")
        bucket = math.floor(capture.timestamp() / 3600)
        if snapshot_id in ids or bucket in buckets or (captures and capture <= captures[-1]):
            raise ValueError("Prefix must be sorted and hourly deduplicated")
        if observation.get("measurement_key") != measurement:
            raise ValueError("Measurement identity changed within prefix")
        if observation.get("source_active") is False or observation.get("source_visible") is False:
            raise ValueError("Inactive or hidden source observation")
        ids.add(snapshot_id)
        buckets.add(bucket)
        captures.append(capture)
        values.append(_number(observation.get("available_total"), "available_total", nonnegative=True))
    if captures[-1] - captures[0] < timedelta(hours=24):
        raise ValueError("Prefix must span at least 24h")
    if issued - captures[-1] > timedelta(hours=6):
        raise ValueError("Latest genuine observation is stale")
    if _time(issue["latest_captured_at"]) != captures[-1]:
        raise ValueError("Latest observation lineage does not match prefix")
    if _number(issue.get("last_available_total"), "last_available_total", nonnegative=True) != values[-1]:
        raise ValueError("Latest inventory does not match prefix")
    for key in ("prefix_sha256", "input_manifest_sha256"):
        if not isinstance(issue.get(key), str) or not issue[key]:
            raise ValueError(f"Missing {key}")
    return issued, kickoff, prefix, max(1.0, max(values))


def _valid_lead(issue: dict[str, Any], lead_days: Any) -> int:
    lead = _integer(lead_days, "lead_days")
    if lead >= issue["days_to_event"]:
        raise ValueError("Future inventory targets must precede kickoff")
    return lead


def make_features(issue: dict[str, Any], lead_days: int) -> np.ndarray:
    """Encode genuine prefix context and explicit lead interactions, 250 features."""
    issued, _, prefix, scale = _validate_issue(issue)
    lead = _valid_lead(issue, lead_days)
    last = float(issue["last_available_total"])
    values = np.zeros(60, dtype=float)
    masks = np.zeros(60, dtype=float)
    for observation in prefix:
        capture = _time(observation["captured_at"])
        age_days = (issued - capture).total_seconds() / 86400
        index = math.floor(age_days)
        if not 0 <= index < 60:
            raise ValueError("Observation falls outside the 60-day feature window")
        # Ascending observations replace only an older real point in that bin.
        values[index] = (float(observation["available_total"]) - last) / scale
        masks[index] = 1.0
    first, latest = _time(prefix[0]["captured_at"]), _time(prefix[-1]["captured_at"])
    globals_ = np.asarray([
        1.0,
        issue["days_to_event"] / 60.0,
        (latest - first).total_seconds() / 86400 / 60.0,
        (issued - latest).total_seconds() / 86400,
        math.log1p(len(prefix)) / math.log1p(1440),
    ], dtype=float)
    context = np.concatenate((globals_, values, masks))
    h = lead / 7.0
    return np.concatenate((h * context, h * h * context))


def _row_identity(row: dict[str, Any]) -> tuple[int, str, str]:
    issue = row["issue"]
    return (int(issue["ticket_event_id"]), _iso(issue["issued_as_of_at"]), _iso(row["target_at"]))


def _validate_label(row: dict[str, Any], *, trained_through: datetime | None = None) -> float:
    issue = row["issue"]
    issued, _, _, scale = _validate_issue(issue)
    lead = _valid_lead(issue, row["lead_days"])
    target, captured = _time(row["target_at"]), _time(row["target_captured_at"])
    if target != issued + timedelta(days=lead):
        raise ValueError("Target does not match issue and lead")
    if captured > target or captured <= issued or target - captured > timedelta(hours=6):
        raise ValueError("Target observation violates PIT or freshness rules")
    if row.get("measurement_key") != issue["measurement_key"]:
        raise ValueError("Target measurement differs from input measurement")
    target_snapshot_id = _integer(row.get("target_snapshot_id"), "target_snapshot_id")
    if target_snapshot_id in {observation["snapshot_id"] for observation in issue["observed_prefix"]}:
        raise ValueError("A future target cannot reuse a prefix snapshot identity")
    _number(row.get("target_available_total"), "target_available_total", nonnegative=True)
    if trained_through is not None and (issued > trained_through or target > trained_through or captured > trained_through):
        raise ValueError("Training labels or prefixes exceed the training cutoff")
    return scale


def fit_model(rows: Iterable[dict[str, Any]], trained_through: str | datetime) -> dict[str, Any]:
    """Fit the one precommitted candidate; no exposed-result selection or tuning."""
    cutoff = _time(trained_through)
    records = sorted(list(rows), key=_row_identity)
    if not records:
        raise ValueError("No labeled training rows")
    identities: set[tuple[int, str, str]] = set()
    scales: list[float] = []
    for row in records:
        identity = _row_identity(row)
        if identity in identities:
            raise ValueError("Duplicate event/issue/target training identity")
        identities.add(identity)
        scales.append(_validate_label(row, trained_through=cutoff))
    event_counts = Counter(int(row["issue"]["ticket_event_id"]) for row in records)
    if len(event_counts) < MIN_TRAIN_EVENTS:
        raise ValueError("At least five independent training events are required")

    from sklearn import __version__ as sklearn_version
    from sklearn.linear_model import QuantileRegressor

    x = np.stack([make_features(row["issue"], row["lead_days"]) for row in records])
    y = np.asarray([
        (float(row["target_available_total"]) - float(row["issue"]["last_available_total"])) / scale
        for row, scale in zip(records, scales)
    ])
    weights = np.asarray([
        scale / event_counts[int(row["issue"]["ticket_event_id"])]
        for row, scale in zip(records, scales)
    ])
    weights /= weights.mean()
    estimator = QuantileRegressor(quantile=QUANTILE, alpha=ALPHA, solver="highs", fit_intercept=False)
    estimator.fit(x, y, sample_weight=weights)
    manifest = [{
        "ticket_event_id": row["issue"]["ticket_event_id"],
        "issued_as_of_at": _iso(row["issue"]["issued_as_of_at"]),
        "lead_days": row["lead_days"],
        "target_at": _iso(row["target_at"]),
        "target_snapshot_id": row["target_snapshot_id"],
        "target_captured_at": _iso(row["target_captured_at"]),
        "target_available_total": float(row["target_available_total"]),
        "measurement_key": row["measurement_key"],
        "input_manifest_sha256": row["issue"]["input_manifest_sha256"],
        "prefix_sha256": row["issue"]["prefix_sha256"],
    } for row in records]
    artifact: dict[str, Any] = {
        "model_version": MODEL_VERSION,
        "baseline_version": BASELINE_VERSION,
        "feature_version": FEATURE_VERSION,
        "feature_count": FEATURE_COUNT,
        "precommit_id": PRECOMMIT_ID,
        "target_kind": "available_total",
        "unit": "places",
        "quantile": QUANTILE,
        "alpha": ALPHA,
        "solver": "highs",
        "fit_intercept": False,
        "trained_through": cutoff.isoformat(),
        "fitted_at": datetime.now(UTC).isoformat(),
        "training_event_ids": sorted(event_counts),
        "training_club_count": len({str(row["issue"].get("club_slug", "")) for row in records}),
        "training_row_count": len(records),
        "training_manifest_sha256": _canonical_hash(manifest),
        "sklearn_version": sklearn_version,
        "coefficients": estimator.coef_.astype(float).tolist(),
        "intercept": float(estimator.intercept_),
        "production_change": False,
        "live_adjustment": 0,
    }
    artifact["model_sha256"] = artifact_sha256(artifact)
    validate_model(artifact)
    return artifact


def validate_model(artifact: dict[str, Any]) -> None:
    """Fail closed on corrupted artifacts or a different model contract."""
    if artifact.get("model_sha256") != artifact_sha256(artifact):
        raise ValueError("Model artifact hash mismatch")
    required = {
        "model_version": MODEL_VERSION, "feature_version": FEATURE_VERSION,
        "feature_count": FEATURE_COUNT, "quantile": QUANTILE,
        "alpha": ALPHA, "solver": "highs", "target_kind": "available_total",
        "unit": "places", "production_change": False, "live_adjustment": 0,
        "fit_intercept": False,
    }
    if any(artifact.get(key) != value for key, value in required.items()):
        raise ValueError("Model artifact violates the precommitted contract")
    if _time(artifact["trained_through"]) > _time(artifact["fitted_at"]):
        raise ValueError("Training cutoff exceeds actual artifact creation time")
    events = artifact.get("training_event_ids")
    if not isinstance(events, list) or len(events) < MIN_TRAIN_EVENTS or len(events) != len(set(events)):
        raise ValueError("Invalid training-event registry")
    for event_id in events:
        _integer(event_id, "training_event_id")
    coefficients = artifact.get("coefficients")
    if not isinstance(coefficients, list) or len(coefficients) != FEATURE_COUNT:
        raise ValueError("Model feature count mismatch")
    for value in coefficients:
        _number(value, "coefficient")
    if artifact.get("fit_intercept") is not False or _number(artifact.get("intercept"), "intercept") != 0.0:
        raise ValueError("This feature contract requires zero intercept")


def save_model(artifact: dict[str, Any], path: str | Path) -> None:
    """Create an artifact; accept an identical retry, never overwrite a new fit."""
    validate_model(artifact)
    destination = Path(path)
    if destination.exists():
        existing = load_model(destination)
        if existing["model_sha256"] != artifact["model_sha256"]:
            raise ValueError("Refusing to overwrite a different frozen artifact")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x") as stream:
        json.dump(artifact, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def load_model(path: str | Path) -> dict[str, Any]:
    with Path(path).open() as stream:
        artifact = json.load(stream)
    validate_model(artifact)
    return artifact


def predict_path(issue: dict[str, Any], artifact: dict[str, Any]) -> list[dict[str, Any]]:
    """Predict future days directly; this returns research previews, not evidence."""
    validate_model(artifact)
    issued, kickoff, _, scale = _validate_issue(issue)
    if _time(artifact["trained_through"]) > issued:
        raise ValueError("Artifact was trained after the issue cutoff")
    if int(issue["ticket_event_id"]) in artifact["training_event_ids"]:
        raise ValueError("Target event was used to fit the artifact")
    coefficients = np.asarray(artifact["coefficients"], dtype=float)
    latest = float(issue["last_available_total"])
    result = []
    for lead in range(1, issue["days_to_event"]):
        target = issued + timedelta(days=lead)
        if target >= kickoff:
            raise AssertionError("Future daily target must precede kickoff")
        residual = float(make_features(issue, lead) @ coefficients + artifact["intercept"])
        prediction = max(0.0, latest + scale * residual)
        if not math.isfinite(prediction):
            raise ValueError("Non-finite model prediction")
        result.append({
            "ticket_event_id": int(issue["ticket_event_id"]),
            "club_slug": issue.get("club_slug", ""),
            "issued_as_of_at": issued.isoformat(),
            "target_at": target.isoformat(),
            "lead_days": lead,
            "model_version": MODEL_VERSION,
            "baseline_version": BASELINE_VERSION,
            "predicted_available_total": prediction,
            "baseline_available_total": latest,
            "target_kind": "available_total",
            "unit": "places",
            "measurement_key": issue["measurement_key"],
            "input_manifest_sha256": issue["input_manifest_sha256"],
            "prefix_sha256": issue["prefix_sha256"],
            "model_sha256": artifact["model_sha256"],
            "evidence_kind": "research_preview_not_prospective",
            "production_change": False,
        })
    return result


def _summary(scored: list[dict[str, Any]]) -> dict[str, Any]:
    events: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in scored:
        events[record["ticket_event_id"]].append(record)
    event_rows = []
    for event_id, rows in sorted(events.items()):
        event_rows.append({
            "ticket_event_id": event_id,
            "point_count": len(rows),
            "challenger_mae": float(np.mean([abs(row["challenger_error"]) for row in rows])),
            "baseline_mae": float(np.mean([abs(row["baseline_error"]) for row in rows])),
            "challenger_bias": float(np.mean([row["challenger_error"] for row in rows])),
            "baseline_bias": float(np.mean([row["baseline_error"] for row in rows])),
        })
    def mean(key: str) -> float | None:
        return float(np.mean([row[key] for row in event_rows])) if event_rows else None
    challenger, baseline = mean("challenger_mae"), mean("baseline_mae")
    deltas = [row["challenger_mae"] - row["baseline_mae"] for row in event_rows]
    return {
        "point_count": len(scored),
        "scored_event_count": len(events),
        "distinct_club_count": len({row["club_slug"] for row in scored}),
        "challenger_event_balanced_mae": challenger,
        "baseline_event_balanced_mae": baseline,
        "delta_mae": None if challenger is None else challenger - baseline,
        "challenger_signed_bias": mean("challenger_bias"),
        "baseline_signed_bias": mean("baseline_bias"),
        "event_improvement_rate": float(np.mean(np.asarray(deltas) < 0)) if deltas else None,
        "median_event_delta_ae": float(np.median(deltas)) if deltas else None,
        "worst_event_degradation": max(deltas) if deltas else None,
        "challenger_p90_event_mae": float(np.quantile([row["challenger_mae"] for row in event_rows], .9)) if event_rows else None,
        "baseline_p90_event_mae": float(np.quantile([row["baseline_mae"] for row in event_rows], .9)) if event_rows else None,
        "event_metrics": event_rows,
    }


def evaluate_points(points: Iterable[dict[str, Any]], labeled_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Paired same-target inventory errors, balanced by independent event."""
    labels: dict[tuple[int, str, str], dict[str, Any]] = {}
    for row in labeled_rows:
        _validate_label(row)
        identity = _row_identity(row)
        if identity in labels:
            raise ValueError("Duplicate evaluation label identity")
        labels[identity] = row
    predictions = list(points)
    versions = {point.get("model_version") for point in predictions}
    if len(versions) > 1:
        raise ValueError("Do not pool different model versions")
    seen: set[tuple[int, str, str]] = set()
    scored = []
    for point in predictions:
        identity = (
            _integer(point.get("ticket_event_id"), "ticket_event_id"),
            _iso(point["issued_as_of_at"]), _iso(point["target_at"]),
        )
        if identity in seen:
            raise ValueError("Duplicate event/issue/target prediction")
        seen.add(identity)
        prediction = _number(point.get("predicted_available_total"), "prediction", nonnegative=True)
        baseline = _number(point.get("baseline_available_total"), "baseline", nonnegative=True)
        lead = _integer(point.get("lead_days"), "lead_days")
        if _time(point["target_at"]) != _time(point["issued_as_of_at"]) + timedelta(days=lead):
            raise ValueError("Prediction target/lead mismatch")
        row = labels.get(identity)
        if row is None:
            continue
        if point.get("measurement_key") != row["measurement_key"] or lead != row["lead_days"]:
            raise ValueError("Prediction/label measurement mismatch")
        if baseline != float(row["issue"]["last_available_total"]):
            raise ValueError("Baseline is not persistence of the issue's last observation")
        actual = float(row["target_available_total"])
        scored.append({
            "ticket_event_id": identity[0],
            "club_slug": row["issue"].get("club_slug", ""),
            "lead_days": lead,
            "challenger_error": prediction - actual,
            "baseline_error": baseline - actual,
        })
    result = _summary(scored)
    leads = {1, 3, 7} | {point["lead_days"] for point in predictions}
    result.update({
        "version": "daily-inventory-path-evaluation-v1",
        "target_kind": "available_total",
        "unit": "places",
        "evidence_kind": "retrospective_diagnostic_not_prospective",
        "prediction_count": len(predictions),
        "labeled_target_count": len(labels),
        "unmatched_prediction_count": len(predictions) - len(scored),
        "unpredicted_labeled_target_count": len(labels) - len(scored),
        "prediction_label_coverage": len(scored) / len(predictions) if predictions else None,
        "per_lead": {str(lead): _summary([row for row in scored if row["lead_days"] == lead]) for lead in sorted(leads)},
        "production_change": False,
    })
    return result
