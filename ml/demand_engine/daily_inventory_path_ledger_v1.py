"""Append-only local prospective evidence for daily inventory paths.

This SQLite ledger is a local/cloud research tool, not a Supabase deployment.
It deliberately refuses retrospective preview writes as prospective evidence.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterator


EVIDENCE_KIND = "local_post_freeze_prospective"
SCHEMA_VERSION = "daily-inventory-path-local-ledger-v1"
_HEX = re.compile(r"[0-9a-f]{64}\Z")


def _time(value: str | datetime) -> datetime:
    result = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timezone-aware timestamp required")
    return result.astimezone(timezone.utc)


def _iso(value: str | datetime) -> str:
    return _time(value).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _hash(value: Any) -> str:
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _identifier(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"Invalid {label}")
    return value


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        raise ValueError(f"Invalid {label}")
    return value


def _nonnegative(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Invalid {label}")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"Invalid {label}")
    return number


class DailyInventoryPathLedger:
    """Store validated attempt vintages and immutable future-day predictions."""

    def __init__(self, path: str | Path):
        self._conn = sqlite3.connect(str(path), timeout=10)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS daily_path_meta (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1), version TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS daily_path_attempts (
                id INTEGER PRIMARY KEY,
                ticket_event_id INTEGER NOT NULL,
                issued_as_of_at TEXT NOT NULL,
                model_version TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                semantic_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(ticket_event_id, issued_as_of_at, model_version)
            );
            CREATE TABLE IF NOT EXISTS daily_path_points (
                id INTEGER PRIMARY KEY,
                attempt_id INTEGER NOT NULL REFERENCES daily_path_attempts(id),
                target_at TEXT NOT NULL,
                lead_days INTEGER NOT NULL CHECK(lead_days>0),
                payload_json TEXT NOT NULL,
                UNIQUE(attempt_id,target_at), UNIQUE(attempt_id,lead_days)
            );
            CREATE TABLE IF NOT EXISTS daily_path_scores (
                point_id INTEGER PRIMARY KEY REFERENCES daily_path_points(id),
                scored_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
        """)
        self._conn.execute(
            "INSERT OR IGNORE INTO daily_path_meta(singleton,version) VALUES(1,?)",
            (SCHEMA_VERSION,),
        )
        version = self._conn.execute("SELECT version FROM daily_path_meta WHERE singleton=1").fetchone()[0]
        if version != SCHEMA_VERSION:
            self._conn.close()
            raise ValueError("Incompatible local ledger schema")
        for table in ("daily_path_attempts", "daily_path_points", "daily_path_scores"):
            for operation in ("UPDATE", "DELETE"):
                # Table and operation names are constants, never caller-controlled.
                self._conn.execute(
                    f"CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()} "
                    f"BEFORE {operation} ON {table} BEGIN "
                    "SELECT RAISE(ABORT,'Daily inventory evidence is immutable'); END"
                )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "DailyInventoryPathLedger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._conn.rollback()
            raise
        else:
            self._conn.commit()

    @staticmethod
    def _validate(issue: dict, points: list[dict], artifact: dict, executed_at: str | datetime) -> tuple[dict, list[dict], str]:
        from .daily_inventory_path_dataset_v1 import build_issue, canonical_hash, issue_manifest
        from .daily_inventory_path_model_v1 import predict_path, validate_model

        # Validate serializability up front, including nested nonfinite values.
        _json(issue)
        _json(artifact)
        event_id = _identifier(issue.get("ticket_event_id"), "ticket_event_id")
        issued = _time(issue["issued_as_of_at"])
        kickoff = _time(issue["kickoff_at"])
        execution = _time(executed_at)
        days = issue.get("days_to_event")
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 60:
            raise ValueError("Issue horizon must be P-60 through P-1")
        if kickoff - issued != timedelta(days=days):
            raise ValueError("Issue is not an exact daily cutoff")
        if not issued <= execution <= issued + timedelta(minutes=90):
            raise ValueError("Prospective execution must be within cutoff through +90 minutes")
        trained_through = _time(artifact["trained_through"])
        fitted_at = _time(artifact["fitted_at"])
        if not trained_through <= fitted_at <= issued:
            raise ValueError("Training data cutoff and artifact fit must precede issue cutoff")
        train_ids = artifact.get("training_event_ids")
        if not isinstance(train_ids, list):
            raise ValueError("Missing training event identities")
        train_ids = [_identifier(item, "training event identity") for item in train_ids]
        if len(train_ids) != len(set(train_ids)):
            raise ValueError("Duplicate training event identities")
        if event_id in train_ids:
            raise ValueError("Prospective target event was used in training")
        model_version = artifact.get("model_version")
        if not isinstance(model_version, str) or not model_version:
            raise ValueError("Missing model version")
        model_sha = _digest(artifact.get("model_sha256"), "model hash")
        if model_sha != _hash({key: value for key, value in artifact.items() if key != "model_sha256"}):
            raise ValueError("Model artifact hash mismatch")
        validate_model(artifact)
        if issue.get("production_change", False) is not False or artifact.get("production_change", False) is not False:
            raise ValueError("Production changes are forbidden")
        prefix = issue.get("observed_prefix")
        if not isinstance(prefix, list):
            raise ValueError("Missing observed prefix")
        for observation in prefix:
            captured = _time(observation["captured_at"])
            if not kickoff - timedelta(days=60) <= captured <= issued:
                raise ValueError("Observation outside genuine issue prefix")
        prefix_sha = _digest(issue.get("prefix_sha256"), "prefix hash")
        input_sha = _digest(issue.get("input_manifest_sha256"), "input manifest hash")
        if prefix_sha != canonical_hash(prefix) or input_sha != canonical_hash(issue_manifest(issue)):
            raise ValueError("Issue input hash mismatch")
        status = issue.get("status")
        if not isinstance(status, str) or not status:
            raise ValueError("Missing issue status")
        if status != "READY" and points:
            raise ValueError("Failed-input attempts cannot have predictions")
        expected_by_lead = {}
        if status == "READY":
            # Reconstruct eligibility from actual inputs rather than trust a flag.
            rebuilt = build_issue({
                "ticket_event_id": event_id,
                "club_slug": issue.get("club_slug"),
                "kickoff_at": issue["kickoff_at"],
                "observations": prefix,
            }, issue["issued_as_of_at"])
            if rebuilt["status"] != "READY" or rebuilt["input_manifest_sha256"] != input_sha:
                raise ValueError("Claimed READY prefix failed dataset validation")
            if (_time(issue["latest_captured_at"]) != _time(rebuilt["latest_captured_at"])
                    or issue.get("last_available_total") != rebuilt["last_available_total"]):
                raise ValueError("Latest inventory lineage differs from genuine prefix")
            # Bind the persisted values to this exact artifact and prefix, not
            # merely to a caller-provided matching model hash.
            expected_by_lead = {point["lead_days"]: point for point in predict_path(issue, artifact)}
        canonical_issue = json.loads(_json(issue))
        canonical_issue["issued_as_of_at"] = _iso(issued)
        canonical_issue["kickoff_at"] = _iso(kickoff)
        clean_points: list[dict] = []
        seen: set[int] = set()
        for point in points:
            _json(point)
            lead = point.get("lead_days")
            if isinstance(lead, bool) or not isinstance(lead, int) or not 1 <= lead < days:
                raise ValueError("Invalid future-day lead")
            if lead in seen:
                raise ValueError("Duplicate target lead")
            seen.add(lead)
            target = _time(point["target_at"])
            if target != issued + timedelta(days=lead) or target >= kickoff:
                raise ValueError("Target must be an exact future daily cutoff before kickoff")
            checks = {
                "ticket_event_id": event_id,
                "model_version": model_version,
                "model_sha256": model_sha,
                "measurement_key": issue.get("measurement_key"),
                "input_manifest_sha256": input_sha,
            }
            if any(point.get(key) != value for key, value in checks.items()):
                raise ValueError("Prediction identity differs from attempt/model")
            if _time(point["issued_as_of_at"]) != issued:
                raise ValueError("Prediction issue timestamp mismatch")
            if point.get("prefix_sha256", prefix_sha) != prefix_sha:
                raise ValueError("Prediction prefix hash mismatch")
            if point.get("production_change", False) is not False or point.get("target_values_used", False) is not False:
                raise ValueError("Prediction must be research-only and target-free")
            if point.get("target_kind", "available_total") != "available_total" or point.get("unit", "places") != "places":
                raise ValueError("Invalid inventory target semantics")
            if point.get("club_slug", issue.get("club_slug")) != issue.get("club_slug"):
                raise ValueError("Prediction club mismatch")
            prediction = _nonnegative(point.get("predicted_available_total"), "predicted_available_total")
            baseline = _nonnegative(point.get("baseline_available_total"), "baseline_available_total")
            if baseline != _nonnegative(issue.get("last_available_total"), "last_available_total"):
                raise ValueError("Persistence baseline differs from latest genuine observation")
            expected = expected_by_lead[lead]
            if not math.isclose(prediction, expected["predicted_available_total"], rel_tol=0, abs_tol=1e-9):
                raise ValueError("Prediction value does not match the frozen artifact output")
            clean_points.append({
                **checks,
                "club_slug": issue.get("club_slug"),
                "issued_as_of_at": _iso(issued),
                "target_at": _iso(target),
                "lead_days": lead,
                "predicted_available_total": prediction,
                "baseline_available_total": baseline,
                "prefix_sha256": prefix_sha,
                "target_kind": "available_total",
                "unit": "places",
                "evidence_kind": EVIDENCE_KIND,
                "production_change": False,
                "target_values_used": False,
            })
        if status == "READY" and seen != set(range(1, days)):
            raise ValueError("READY attempt must contain every remaining future daily target")
        clean_points.sort(key=lambda row: row["lead_days"])
        payload = {"issue": canonical_issue, "artifact": artifact, "points": clean_points,
                   "evidence_kind": EVIDENCE_KIND, "production_change": False}
        return payload, clean_points, _iso(execution)

    def record(self, issue: dict, points: list[dict], artifact: dict, executed_at: str | datetime) -> dict:
        payload, clean_points, execution = self._validate(issue, points, artifact, executed_at)
        issue = payload["issue"]
        identity = (issue["ticket_event_id"], issue["issued_as_of_at"], artifact["model_version"])
        semantic_sha = _hash(payload)
        with self._transaction():
            old = self._conn.execute(
                "SELECT id,semantic_sha256,executed_at FROM daily_path_attempts "
                "WHERE ticket_event_id=? AND issued_as_of_at=? AND model_version=?", identity,
            ).fetchone()
            if old is not None:
                if old["semantic_sha256"] != semantic_sha:
                    raise ValueError("Conflicting retry of an immutable daily issue")
                return {"attempt_id": old["id"], "inserted": False, "point_count": len(clean_points),
                        "executed_at": old["executed_at"], "evidence_kind": EVIDENCE_KIND}
            cursor = self._conn.execute(
                "INSERT INTO daily_path_attempts(ticket_event_id,issued_as_of_at,model_version,executed_at,semantic_sha256,payload_json) "
                "VALUES(?,?,?,?,?,?)", (*identity, execution, semantic_sha, _json(payload)),
            )
            attempt_id = cursor.lastrowid
            self._conn.executemany(
                "INSERT INTO daily_path_points(attempt_id,target_at,lead_days,payload_json) VALUES(?,?,?,?)",
                [(attempt_id, point["target_at"], point["lead_days"], _json(point)) for point in clean_points],
            )
        return {"attempt_id": attempt_id, "inserted": True, "point_count": len(clean_points),
                "executed_at": execution, "evidence_kind": EVIDENCE_KIND}

    def score(self, events: list[dict], as_of_at: str | datetime) -> dict:
        from .daily_inventory_path_dataset_v1 import match_target

        as_of = _time(as_of_at)
        by_id: dict[int, dict] = {}
        for event in events:
            event_id = _identifier(event.get("ticket_event_id"), "ticket_event_id")
            if event_id in by_id:
                raise ValueError("Duplicate scoring event identity")
            by_id[event_id] = event
        counts = {"scored_count": 0, "already_scored_count": 0, "missing_target_count": 0,
                  "not_due_count": 0, "production_change": False, "evidence_kind": EVIDENCE_KIND}
        with self._transaction():
            records = self._conn.execute(
                "SELECT p.id,p.target_at,p.payload_json,a.payload_json AS attempt_json,a.executed_at,s.point_id "
                "FROM daily_path_points p JOIN daily_path_attempts a ON a.id=p.attempt_id "
                "LEFT JOIN daily_path_scores s ON s.point_id=p.id ORDER BY p.id"
            ).fetchall()
            for record in records:
                if record["point_id"] is not None:
                    counts["already_scored_count"] += 1
                    continue
                if _time(record["target_at"]) > as_of:
                    counts["not_due_count"] += 1
                    continue
                point = json.loads(record["payload_json"])
                event = by_id.get(point["ticket_event_id"])
                attempt = json.loads(record["attempt_json"])
                if event is None or _time(event["kickoff_at"]) != _time(attempt["issue"]["kickoff_at"]):
                    counts["missing_target_count"] += 1
                    continue
                matched = match_target(event, point["target_at"], as_of, point["measurement_key"])
                if matched is None:
                    counts["missing_target_count"] += 1
                    continue
                actual = _nonnegative(matched["available_total"], "target_available_total")
                captured = _time(matched["captured_at"])
                target = _time(point["target_at"])
                if not target - timedelta(hours=6) <= captured <= target <= as_of:
                    raise ValueError("Target matching violated the precommitted temporal contract")
                score = {
                    "target_snapshot_id": _identifier(matched["snapshot_id"], "target snapshot identity"),
                    "target_captured_at": _iso(captured),
                    "target_available_total": actual,
                    "candidate_error": point["predicted_available_total"] - actual,
                    "baseline_error": point["baseline_available_total"] - actual,
                    "candidate_abs_error": abs(point["predicted_available_total"] - actual),
                    "baseline_abs_error": abs(point["baseline_available_total"] - actual),
                    "measurement_key": point["measurement_key"],
                    "scored_at": _iso(as_of),
                    "production_change": False,
                }
                self._conn.execute(
                    "INSERT INTO daily_path_scores(point_id,scored_at,payload_json) VALUES(?,?,?)",
                    (record["id"], _iso(as_of), _json(score)),
                )
                counts["scored_count"] += 1
        return counts

    def export_points(self, event_id: int | None = None) -> list[dict]:
        query = (
            "SELECT p.id,p.attempt_id,p.payload_json,a.executed_at,s.payload_json AS score_json "
            "FROM daily_path_points p JOIN daily_path_attempts a ON a.id=p.attempt_id "
            "LEFT JOIN daily_path_scores s ON s.point_id=p.id"
        )
        params: tuple = ()
        if event_id is not None:
            query += " WHERE a.ticket_event_id=?"
            params = (_identifier(event_id, "ticket_event_id"),)
        query += " ORDER BY a.issued_as_of_at,p.target_at,a.ticket_event_id"
        result = []
        for row in self._conn.execute(query, params):
            point = json.loads(row["payload_json"])
            point.update({"point_id": row["id"], "attempt_id": row["attempt_id"],
                          "executed_at": row["executed_at"],
                          "score": json.loads(row["score_json"]) if row["score_json"] else None})
            result.append(point)
        return result

    def export_attempts(self, event_id: int | None = None) -> list[dict]:
        query = "SELECT id,executed_at,payload_json FROM daily_path_attempts"
        params: tuple = ()
        if event_id is not None:
            query += " WHERE ticket_event_id=?"
            params = (_identifier(event_id, "ticket_event_id"),)
        query += " ORDER BY issued_as_of_at,ticket_event_id"
        return [{"attempt_id": row["id"], "executed_at": row["executed_at"],
                 **json.loads(row["payload_json"])} for row in self._conn.execute(query, params)]
