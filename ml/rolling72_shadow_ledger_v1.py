"""Separate actual-time baseline forecasts and immutable genuine later scores.

No hosted DB writes, backdate option, fitted model or production activation.
Freeze the exact recipe/code before capture. Existing exposed fixtures provide
operational future targets, not new independent review fixtures. The source
copy must already be received, and the last actual capture must still be fresh.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3

from ml.demand_engine.rolling72_features_v1 import _hash, _id, _time
from ml.demand_engine.rolling72_labels_v1 import match_target
from ml.rolling72_receipt_store_v1 import METRIC, prepare_receipt


VERSION = "rolling72-baseline-shadow-ledger-v1"
APPLICATION_ID = 0x52374C31
ROOT = Path(__file__).resolve().parents[1]
PRECOMMIT = ROOT / "ml/artifacts/rolling72_v1/precommit.json"
CODE_PATHS = (
    "ml/demand_engine/rolling72_features_v1.py",
    "ml/demand_engine/rolling72_labels_v1.py",
    "ml/rolling72_receipt_store_v1.py",
    "ml/demand_engine/rolling72_benchmarks_v1.py",
    "ml/rolling72_shadow_ledger_v1.py",
)


def _now():
    return datetime.now(timezone.utc)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def create_freeze(destination: str | Path) -> dict:
    """Record actual freeze time and exact code; destination must not exist."""
    config = json.loads(PRECOMMIT.read_text())
    if config["precommit_sha256"] != _hash({k: v for k, v in config.items() if k != "precommit_sha256"}):
        raise ValueError("Precommit checksum mismatch")
    frozen = _now()
    if _time(config["created_at"]) > frozen:
        raise ValueError("Cannot freeze before the precommit exists")
    value = {"version": VERSION, "frozen_at": frozen.isoformat(),
             "precommit_sha256": config["precommit_sha256"],
             "code_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                             for name in CODE_PATHS},
             "model_fit_performed": False, "production_change": False, "live_adjustment": 0}
    value["freeze_sha256"] = _hash(value)
    with Path(destination).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return value


def _load_freeze(path, at):
    freeze = json.loads(Path(path).read_text())
    if (freeze.get("version") != VERSION or freeze.get("freeze_sha256") != _hash({
            k: v for k, v in freeze.items() if k != "freeze_sha256"})
            or freeze.get("production_change") is not False or freeze.get("live_adjustment") != 0
            or freeze.get("model_fit_performed") is not False):
        raise ValueError("Invalid baseline freeze")
    if _time(freeze["frozen_at"]) > at:
        raise ValueError("Freeze is later than execution")
    config = json.loads(PRECOMMIT.read_text())
    if (config["precommit_sha256"] != freeze["precommit_sha256"]
            or config["precommit_sha256"] != _hash({k: v for k, v in config.items() if k != "precommit_sha256"})):
        raise ValueError("Frozen precommit changed")
    actual = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in CODE_PATHS}
    if freeze["code_sha256"] != actual:
        raise ValueError("Frozen baseline code changed; use a separately versioned lane")
    return freeze


def _connect(path):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(destination, timeout=10)
    try:
        app = db.execute("pragma application_id").fetchone()[0]
        tables = db.execute("select name from sqlite_master where type='table'").fetchall()
        if app != APPLICATION_ID and (app != 0 or tables):
            raise ValueError("Refusing a foreign/frozen ledger")
        db.execute(f"pragma application_id={APPLICATION_ID}")
        db.execute("pragma foreign_keys=on")
        db.executescript("""
            create table if not exists lane (singleton integer primary key check(singleton=1), freeze_json text not null);
            create table if not exists sources (sha text primary key, receipt_json text not null);
            create table if not exists source_observations (
                snapshot_id integer primary key, event_id integer not null,
                observation_sha text not null, payload_json text not null);
            create table if not exists issues (
                event_id integer, issued_at text, source_sha text not null references sources(sha),
                written_at text not null, issue_json text not null, primary key(event_id,issued_at));
            create table if not exists predictions (
                event_id integer, issued_at text, horizon integer, model text, target_at text,
                prediction real, payload_json text not null, primary key(event_id,issued_at,horizon,model),
                foreign key(event_id,issued_at) references issues(event_id,issued_at));
            create table if not exists target_matches (
                event_id integer, issued_at text, horizon integer, source_sha text not null references sources(sha),
                matched_at text not null, label_json text not null, primary key(event_id,issued_at,horizon),
                foreign key(event_id,issued_at) references issues(event_id,issued_at));
            create table if not exists scores (
                event_id integer, issued_at text, horizon integer, model text,
                error real not null, absolute_error real not null, primary key(event_id,issued_at,horizon,model),
                foreign key(event_id,issued_at,horizon,model) references predictions(event_id,issued_at,horizon,model));
            create table if not exists scoring_attempts (
                event_id integer, issued_at text, horizon integer, source_sha text, status text not null,
                primary key(event_id,issued_at,horizon,source_sha));
        """)
        return db
    except BaseException:
        db.close()
        raise


def _bind_lane(db, freeze):
    previous = db.execute("select freeze_json from lane where singleton=1").fetchone()
    if previous is not None and previous[0] != _json(freeze):
        raise ValueError("Ledger belongs to a different immutable freeze")
    if previous is None:
        db.execute("insert into lane values (1,?)", (_json(freeze),))


def _source(db, receipt):
    sha = receipt["source_file_sha256"]
    previous = db.execute("select receipt_json from sources where sha=?", (sha,)).fetchone()
    if previous and previous[0] != _json(receipt):
        raise ValueError("Source receipt conflict")
    if not previous:
        db.execute("insert into sources values (?,?)", (sha, _json(receipt)))
    return sha


def _register_observations(db, source_payload):
    """Reject revisions even for old prefix rows or not-yet-mature targets.

    Receipt knowledge bounds legitimately change; original source values and
    material scope metadata do not. Register the whole received copy inside
    the same transaction as issues/scores, before filtering by target time.
    """
    source = json.loads(source_payload)
    for event in source["events"]:
        event_id = _id(event["ticket_event_id"])
        for row in event["observations"]:
            snapshot = _id(row.get("snapshot_id"))
            value = row.get("available_total")
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
                value = float(value)
            canonical = {"snapshot_id": snapshot, "event_id": event_id,
                         "captured_at": _time(row["captured_at"]).isoformat(),
                         "available_total": value, "measurement_key": row.get("measurement_key"),
                         **{key: row.get(key) for key in ("source", "sector_count", "source_active", "source_visible")}}
            digest = _hash(canonical)
            previous = db.execute("select event_id,observation_sha from source_observations where snapshot_id=?", (snapshot,)).fetchone()
            if previous is not None and previous != (event_id, digest):
                raise ValueError("Immutable source snapshot payload conflict")
            if previous is None:
                db.execute("insert into source_observations values (?,?,?,?)", (snapshot, event_id, digest, _json(canonical)))


def capture(database, source_payload: bytes, freeze_path) -> dict:
    """Issue now, preserve every status, persist numeric baselines before targets."""
    from ml.demand_engine.rolling72_benchmarks_v1 import predict_baselines

    issued = _now()
    freeze = _load_freeze(freeze_path, issued)
    batch = prepare_receipt(source_payload, issued)
    prepared = [(record["issue"], predict_baselines(record["issue"])) for record in batch["records"]]
    written = _now()
    if not 0 <= (written - issued).total_seconds() <= 90:
        raise ValueError("Issue computation exceeded actual-time write allowance")
    db = _connect(database)
    numeric = rows = 0
    try:
        db.execute("begin immediate")
        _bind_lane(db, freeze)
        source_sha = _source(db, batch["receipt"])
        _register_observations(db, source_payload)
        for issue, prediction in prepared:
            identity = (issue["event"]["ticket_event_id"], issue["issued_at"])
            if db.execute("select 1 from issues where event_id=? and issued_at=?", identity).fetchone():
                raise ValueError("Issue already exists; never replace or backfill a forecast")
            db.execute("insert into issues values (?,?,?,?,?)", (*identity, source_sha, written.isoformat(), _json(issue)))
            for point in prediction["points"]:
                target = point["target_at"]
                for name, output in point["models"].items():
                    value = output.get("predicted_available_total")
                    if value is not None:
                        if (isinstance(value, bool) or not isinstance(value, (int, float))
                                or not math.isfinite(value) or value < 0 or target is None
                                or _time(target) <= written):
                            raise ValueError("Invalid or already elapsed forecast")
                        numeric += 1
                    payload = {**output, "input_manifest_sha256": issue["input_manifest_sha256"],
                               "precommit_sha256": freeze["precommit_sha256"],
                               "freeze_sha256": freeze["freeze_sha256"],
                               "cohort": "exposed_or_unverified_fixture_not_new_review",
                               "scenario_stability": "UNKNOWN"}
                    db.execute("insert into predictions values (?,?,?,?,?,?,?)",
                               (*identity, point["horizon_hours"], name, target, value, _json(payload)))
                    rows += 1
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    return {"version": VERSION, "issued_at": issued.isoformat(), "written_at": written.isoformat(),
            "input_issue_count": len(prepared), "prediction_status_rows": rows,
            "numeric_forecast_count": numeric, "production_change": False, "live_adjustment": 0}


def _label_events(source_payload, received):
    data = json.loads(source_payload)
    result = {}
    for event in data["events"]:
        observations = []
        for raw in event["observations"]:
            key = raw.get("measurement_key")
            observations.append({"snapshot_id": raw.get("snapshot_id"), "captured_at": raw["captured_at"],
                                 "known_at": received, "available_total": raw.get("available_total"),
                                 "measurement_key": METRIC + ":" + key if isinstance(key, str) and key.strip() else None,
                                 "source_active": raw.get("source_active"), "source_visible": raw.get("source_visible")})
        result[event["ticket_event_id"]] = {
            "ticket_event_id": event["ticket_event_id"], "club_slug": event["club_slug"],
            "kickoff_at": event["kickoff_at"], "known_at": received, "observations": observations}
    return result


def score(database, source_payload: bytes, freeze_path) -> dict:
    """Freeze first accepted genuine labels; later runs never rewrite a score."""
    scored_at = _now()
    freeze = _load_freeze(freeze_path, scored_at)
    source = prepare_receipt(source_payload, scored_at)  # Validate original bytes/clocks.
    received = source["receipt"]["retrieved_at"]
    events = _label_events(source_payload, received)
    db = _connect(database)
    accepted = added_scores = 0
    try:
        db.execute("begin immediate")
        _bind_lane(db, freeze)
        sha = _source(db, source["receipt"])
        _register_observations(db, source_payload)
        targets = db.execute("""select distinct p.event_id,p.issued_at,p.horizon,i.issue_json
            from predictions p join issues i using(event_id,issued_at)
            where p.prediction is not null order by p.issued_at,p.event_id,p.horizon""").fetchall()
        for event_id, issued, horizon, original in targets:
            identity = (event_id, issued, horizon)
            if db.execute("select 1 from target_matches where event_id=? and issued_at=? and horizon=?", identity).fetchone():
                continue
            if db.execute("select 1 from scoring_attempts where event_id=? and issued_at=? and horizon=? and source_sha=?", (*identity, sha)).fetchone():
                continue
            matched = (match_target(events[event_id], json.loads(original), horizon, received)
                       if event_id in events and _time(received) >= _time(issued)
                       else {"status": "EVENT_NOT_IN_RECEIPT"})
            db.execute("insert into scoring_attempts values (?,?,?,?,?)", (*identity, sha, matched["status"]))
            if matched["status"] != "MATCHED":
                continue
            db.execute("insert into target_matches values (?,?,?,?,?,?)", (*identity, sha, scored_at.isoformat(), _json(matched)))
            actual = matched["label"]["available_total"]
            for model, predicted in db.execute("select model,prediction from predictions where event_id=? and issued_at=? and horizon=? and prediction is not null", identity).fetchall():
                error = predicted - actual
                db.execute("insert into scores values (?,?,?,?,?,?)", (*identity, model, error, abs(error)))
                added_scores += 1
            accepted += 1
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    return {"version": VERSION, "accepted_targets": accepted, "added_scores": added_scores,
            "scored_at": scored_at.isoformat(), "production_change": False, "live_adjustment": 0}


def report(database) -> dict:
    """Read-only, per-horizon equal-event summaries; empty score means null MAE."""
    path = Path(database).resolve()
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        if db.execute("pragma application_id").fetchone()[0] != APPLICATION_ID:
            raise ValueError("Foreign ledger")
        grouped = defaultdict(lambda: defaultdict(list))
        for event, horizon, model, error in db.execute("select event_id,horizon,model,error from scores"):
            grouped[(horizon, model)][event].append(error)
        metrics = {f"+{h}h/{model}": {
            "scored_fixtures": len(events), "scored_points": sum(map(len, events.values())),
            "event_balanced_mae": sum(sum(abs(x) for x in v) / len(v) for v in events.values()) / len(events),
            "event_balanced_bias": sum(sum(v) / len(v) for v in events.values()) / len(events),
            "worst_absolute_error": max(abs(x) for v in events.values() for x in v),
            "p90_absolute_error_pooled_points_nearest_rank": sorted(abs(x) for v in events.values() for x in v)[
                math.ceil(.9 * sum(map(len, events.values()))) - 1]}
            for (h, model), events in grouped.items()}
        targets = db.execute("""select distinct p.event_id,p.issued_at,p.horizon,p.target_at,
            t.event_id from predictions p left join target_matches t
            using(event_id,issued_at,horizon) where p.prediction is not null""").fetchall()
        now = _now()
        pending = sum(_time(row[3]) > now for row in targets)
        missing = sum(_time(row[3]) <= now and row[4] is None for row in targets)
        return {"version": VERSION, "issues": db.execute("select count(*) from issues").fetchone()[0],
                "prediction_status_rows": db.execute("select count(*) from predictions").fetchone()[0],
                "numeric_forecasts": db.execute("select count(*) from predictions where prediction is not null").fetchone()[0],
                "matched_targets": db.execute("select count(*) from target_matches").fetchone()[0],
                "scores": db.execute("select count(*) from scores").fetchone()[0], "metrics": metrics,
                "pending_targets": pending, "mature_unmatched_targets": missing,
                "review_eligible_new_fixtures": 0, "production_change": False, "live_adjustment": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "capture", "score", "report"))
    parser.add_argument("--database", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--freeze", type=Path)
    args = parser.parse_args()
    if args.command == "freeze":
        if args.freeze is None:
            parser.error("--freeze destination required")
        output = create_freeze(args.freeze)
    elif args.command == "report":
        if args.database is None:
            parser.error("--database required")
        output = report(args.database)
    else:
        if any(value is None for value in (args.database, args.input, args.freeze)):
            parser.error("--database, --input and --freeze required")
        output = (capture if args.command == "capture" else score)(args.database, args.input.read_bytes(), args.freeze)
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
