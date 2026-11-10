"""Sanitised read-only export of genuinely persisted rolling72 shadow vintages.

This export contains public availability and parameter-free benchmarks, never
paid sales or final attendance. It does not fit, predict, backfill or deploy a
feed. Hash checks establish internal consistency, not independent source
authentication. Historical forecasts are read as stored, never recomputed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sqlite3

from ml.demand_engine.rolling72_features_v1 import HORIZONS, _hash, _id, _time, features
from ml.demand_engine.rolling72_labels_v1 import VERSION as LABEL_VERSION
from ml.rolling72_receipt_store_v1 import VERSION as RECEIPT_VERSION
from ml.rolling72_shadow_ledger_v1 import APPLICATION_ID, VERSION as LEDGER_VERSION


VERSION = "rolling72-shadow-feed-v1"
METRIC = "public-displayed-available-total-v1"
MODELS = {
    "persistence": "rolling72-persistence-v1",
    "drift": "rolling72-observed-24h-drift-v1",
    "pickup": "rolling72-conditional-pickup-v1",
}


def _sha(value):
    if not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        raise ValueError("Invalid feed lineage SHA256")
    return value


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Invalid feed number")
    return float(value)


def _same(left, right):
    return math.isclose(_number(left), _number(right), rel_tol=1e-12, abs_tol=1e-8)


def _receipt(db, sha):
    _sha(sha)
    row = db.execute("select receipt_json from sources where sha=?", (sha,)).fetchone()
    if row is None:
        raise ValueError("Missing original source receipt")
    receipt = json.loads(row[0])
    if receipt.get("version") != RECEIPT_VERSION or receipt.get("source_file_sha256") != sha:
        raise ValueError("Source receipt identity mismatch")
    _sha(receipt.get("source_manifest_sha256"))
    if _time(receipt["exported_at"]) > _time(receipt["retrieved_at"]):
        raise ValueError("Inconsistent source receipt clocks")
    return receipt


def _score(db, identity, model, predicted, issue, coordinate, generated):
    target = db.execute("""select source_sha,matched_at,label_json from target_matches
        where event_id=? and issued_at=? and horizon=?""", identity).fetchone()
    score = db.execute("""select error,absolute_error from scores
        where event_id=? and issued_at=? and horizon=? and model=?""", (*identity, model)).fetchone()
    if target is None:
        if score is not None:
            raise ValueError("Score without an accepted target")
        return None
    if predicted is None:
        if score is not None:
            raise ValueError("Unavailable forecast has a score")
        return None
    if score is None:
        raise ValueError("Accepted target lacks the persisted forecast score")
    source_sha, scored_at, serialized = target
    receipt = _receipt(db, source_sha)
    matched = json.loads(serialized)
    label = matched.get("label")
    if (matched.get("version") != LABEL_VERSION or matched.get("status") != "MATCHED" or not isinstance(label, dict)
            or matched.get("label_sha256") != _hash(label)
            or matched.get("input_manifest_sha256") != issue["input_manifest_sha256"]
            or matched.get("horizon_hours") != identity[2]
            or _time(matched["target_at"]) != _time(coordinate["target_at"])
            or matched.get("production_change") is not False or matched.get("live_adjustment") != 0
            or matched.get("model_fit_performed") is not False):
        raise ValueError("Accepted target lineage mismatch")
    capture, known = _time(label["captured_at"]), _time(label["known_at"])
    issued, nominal, scored = _time(issue["issued_at"]), _time(coordinate["target_at"]), _time(scored_at)
    if (not issued < capture <= nominal or (nominal-capture).total_seconds() > 21600
            or known < capture or known != _time(receipt["retrieved_at"])
            or known != _time(matched["available_by"]) or not nominal <= scored <= generated
            or known > scored or label.get("measurement_key") != issue["measurement_key"]
            or label.get("source_active") is False or label.get("source_visible") is False
            or any(label.get(flag) is not None and not isinstance(label[flag], bool)
                   for flag in ("source_active", "source_visible"))):
        raise ValueError("Accepted target clocks/measurement mismatch")
    value = _number(label["available_total"])
    if value < 0 or not _same(score[0], predicted-value) or not _same(score[1], abs(predicted-value)):
        raise ValueError("Persisted score arithmetic mismatch")
    return {"target_snapshot_id": _id(label["snapshot_id"]),
            "target_captured_at": capture.isoformat(), "target_known_at": known.isoformat(),
            "target_available_total": value, "scored_at": scored.isoformat(),
            "absolute_error": float(score[1])}


def build_feed(database: str | Path, *, generated_at=None) -> dict:
    """Read one consistent SQLite snapshot; no source credentials or raw API URLs."""
    generated = _time(generated_at) if generated_at is not None else datetime.now(timezone.utc)
    db = sqlite3.connect(Path(database).resolve().as_uri()+"?mode=ro", uri=True)
    try:
        db.execute("pragma query_only=on")
        db.execute("begin")
        if db.execute("pragma application_id").fetchone()[0] != APPLICATION_ID:
            raise ValueError("Not a rolling72 shadow ledger")
        if db.execute("pragma foreign_key_check").fetchall():
            raise ValueError("Ledger foreign-key inconsistency")
        row = db.execute("select freeze_json from lane where singleton=1").fetchone()
        if row is None:
            raise ValueError("Ledger has no immutable freeze")
        freeze = json.loads(row[0])
        if (freeze.get("version") != LEDGER_VERSION
                or freeze.get("freeze_sha256") != _hash({k:v for k,v in freeze.items() if k!="freeze_sha256"})
                or freeze.get("production_change") is not False or freeze.get("live_adjustment") != 0
                or freeze.get("model_fit_performed") is not False
                or _time(freeze["frozen_at"]) > generated):
            raise ValueError("Ledger freeze mismatch")
        _sha(freeze["precommit_sha256"])
        vintages = []
        for event_id, issued_at, source_sha, written_at, serialized in db.execute(
                "select event_id,issued_at,source_sha,written_at,issue_json from issues order by issued_at,event_id").fetchall():
            issue = json.loads(serialized)
            event = issue["event"]
            if (_id(event["ticket_event_id"]) != event_id or issue["issued_at"] != issued_at
                    or not isinstance(event.get("club_slug"),str) or not event["club_slug"].strip()
                    or not isinstance(issue.get("status"),str) or not issue["status"].strip()
                    or issue.get("prefix_sha256") != _hash(issue.get("observed_prefix"))
                    or issue.get("input_manifest_sha256") != _hash({k:v for k,v in issue.items() if k!="input_manifest_sha256"})
                    or issue.get("production_change") is not False or issue.get("live_adjustment") != 0
                    or issue.get("model_fit_performed") is not False or issue.get("target_values_used") is not False):
                raise ValueError("Persisted issue lineage mismatch")
            issued, written = _time(issued_at), _time(written_at)
            receipt = _receipt(db, source_sha)
            if (not _time(freeze["frozen_at"]) <= issued <= written <= generated
                    or (written-issued).total_seconds() > 90
                    or _time(event["known_at"]) != _time(receipt["retrieved_at"])
                    or _time(event["known_at"]) > issued):
                raise ValueError("Persisted issue clocks mismatch")
            observations = []
            seen_ids, seen_times = set(), set()
            for observation in issue["observed_prefix"]:
                capture, known = _time(observation["captured_at"]), _time(observation["known_at"])
                snapshot = _id(observation["snapshot_id"])
                value = _number(observation["available_total"])
                if (snapshot in seen_ids or capture in seen_times or value < 0
                        or capture > known or known != _time(receipt["retrieved_at"])
                        or capture > _time(receipt["exported_at"]) or known > issued
                        or observation.get("measurement_key") != issue["measurement_key"]
                        or any(observation.get(flag) is not None and not isinstance(observation[flag], bool)
                               for flag in ("source_active", "source_visible"))):
                    raise ValueError("Observed prefix clocks/identity mismatch")
                seen_ids.add(snapshot); seen_times.add(capture)
                observations.append({"snapshot_id": snapshot, "captured_at": capture.isoformat(),
                                     "known_at": known.isoformat(), "available_total": value,
                                     "measurement_key": observation["measurement_key"],
                                     "source_active": observation.get("source_active"),
                                     "source_visible": observation.get("source_visible")})
            if observations != sorted(observations, key=lambda item:item["captured_at"]):
                raise ValueError("Unsorted prefix")
            points, cohorts = [], set()
            rows = db.execute("""select horizon,model,target_at,prediction,payload_json from predictions
                where event_id=? and issued_at=? order by horizon,model""", (event_id, issued_at)).fetchall()
            if len(rows) != len(HORIZONS)*len(MODELS):
                raise ValueError("Incomplete persisted forecast/status coordinates")
            by_coordinate = {(h,m):(t,v,p) for h,m,t,v,p in rows}
            if set(by_coordinate) != {(h,m) for h in HORIZONS for m in MODELS}:
                raise ValueError("Unexpected forecast/status coordinates")
            for horizon in HORIZONS:
                coordinate = features(issue, horizon)
                models = {}
                for name, model_id in MODELS.items():
                    target, predicted, raw = by_coordinate[horizon,name]
                    payload = json.loads(raw)
                    if (target != coordinate["target_at"] or payload.get("model_id") != model_id
                            or payload.get("input_manifest_sha256") != issue["input_manifest_sha256"]
                            or payload.get("precommit_sha256") != freeze["precommit_sha256"]
                            or payload.get("freeze_sha256") != freeze["freeze_sha256"]
                            or payload.get("scenario_stability") != "UNKNOWN"):
                        raise ValueError("Persisted prediction lineage mismatch")
                    cohorts.add(payload.get("cohort"))
                    status = payload.get("status")
                    delta = payload.get("predicted_delta")
                    if predicted is None:
                        if (status != "UNAVAILABLE" or payload.get("predicted_available_total") is not None or delta is not None
                                or not isinstance(payload.get("status_reason"),str) or not payload["status_reason"].strip()):
                            raise ValueError("Unavailable prediction is not null")
                    elif (coordinate["status"] != "READY" or status != "READY" or predicted < 0
                          or payload.get("status_reason") is not None
                          or not _same(predicted, payload.get("predicted_available_total"))
                          or not _same(delta, predicted-issue["last_available_total"])
                          or _time(target) <= written):
                        raise ValueError("Numeric forecast/coordinate mismatch")
                    models[name] = {"model_id": model_id, "status": status,
                                    "status_reason": payload.get("status_reason"),
                                    "predicted_available_total": predicted, "predicted_delta": delta,
                                    "score": _score(db,(event_id,issued_at,horizon),name,predicted,issue,coordinate,generated)}
                points.append({"horizon_hours": horizon, "target_at": coordinate["target_at"],
                               "status": coordinate["status"], "models": models})
            if cohorts != {"exposed_or_unverified_fixture_not_new_review"}:
                raise ValueError("Unexpected fixture evaluation cohort")
            vintages.append({"ticket_event_id": _id(event_id), "club_slug": event["club_slug"],
                             "kickoff_at": event["kickoff_at"], "event_known_at": event["known_at"],
                             "issued_at": issued_at, "written_at": written_at, "status": issue["status"],
                             "measurement_key": issue["measurement_key"],
                             "input_manifest_sha256": issue["input_manifest_sha256"],
                             "prefix_sha256": issue["prefix_sha256"], "source_receipt_sha256": source_sha,
                             "precommit_sha256": freeze["precommit_sha256"], "freeze_sha256": freeze["freeze_sha256"],
                             "scenario_stability": "UNKNOWN", "cohort": next(iter(cohorts)),
                             "observations": observations, "points": points})
        return {"version": VERSION, "generated_at": generated.isoformat(), "metric": METRIC,
                "evidence_kind": "immutable_shadow_ledger", "production_change": False, "live_adjustment": 0,
                "frozen_at": freeze["frozen_at"], "vintages": vintages}
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    feed = build_feed(args.database)
    with args.output.open("x") as stream:
        json.dump(feed, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"version": VERSION, "vintage_count": len(feed["vintages"]), "production_change": False}))


if __name__ == "__main__":
    main()
