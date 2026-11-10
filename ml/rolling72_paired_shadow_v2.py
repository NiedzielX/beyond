"""Actual-time, separately frozen paired rolling72 v2 research evidence.

No fit, backdate option, production activation or writes to any old ledger.
Only our trusted private model artifacts may be loaded. Source hashes bind
supplied original copies, not independently authenticated upstream history.
The current pinned registry contains exposed/unverified identities: this module
does not manufacture fresh-review eligibility. Public availability is the target.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from urllib.parse import urlparse

from ml.demand_engine.rolling72_features_v1 import HORIZONS, _hash, _id, _time, build_issue, features
from ml.demand_engine.rolling72_benchmarks_v1 import predict_baselines
from ml.demand_engine.rolling72_labels_v1 import match_target
from ml.rolling72_offline_challenger_v2 import load_artifact, load_precommit, predict
from ml.rolling72_offline_dataset_v2 import _key, _usable
from ml.rolling72_receipt_dataset_v1 import _registry
from ml.rolling72_receipt_store_v1 import METRIC, prepare_receipt
from ml.rolling72_shadow_ledger_v1 import _json, _label_events, _register_observations, _source


VERSION = "rolling72-paired-prospective-shadow-v2"
APPLICATION_ID = 0x52374C32
ROOT = Path(__file__).resolve().parents[1]
CODE_PATHS = (
    "ml/rolling72_paired_shadow_v2.py", "ml/rolling72_offline_challenger_v2.py",
    "ml/rolling72_offline_dataset_v2.py", "ml/rolling72_receipt_dataset_v1.py",
    "ml/demand_engine/rolling72_features_v1.py", "ml/demand_engine/rolling72_labels_v1.py",
    "ml/demand_engine/rolling72_benchmarks_v1.py", "ml/rolling72_receipt_store_v1.py",
    "ml/rolling72_shadow_ledger_v1.py",
)
COHORT = "exposed_or_unverified_fixture_not_new_review"


def _now():
    return datetime.now(timezone.utc)


def _code_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in CODE_PATHS}


def _registry_bound(payload, synthetic_test):
    if not isinstance(payload, bytes):
        raise ValueError("Original registry bytes required")
    digest = hashlib.sha256(payload).hexdigest()
    if not synthetic_test and digest != load_precommit()["source_bindings"]["identity_registry"]["file_sha256"]:
        raise ValueError("Exact precommitted identity registry required")
    groups, catalogue, identities = _registry(payload)
    if not groups:
        raise ValueError("Nonempty verified identity registry required")
    return digest, groups, catalogue, identities


def create_freeze(destination, artifactdir, identity_registry_payload, *, synthetic_test=False):
    """Freeze actual time/code/model/registry once, after the model was fitted."""
    if not isinstance(synthetic_test, bool):
        raise ValueError("Explicit boolean synthetic mode required")
    loaded = load_artifact(artifactdir, allow_synthetic_test=synthetic_test)
    manifest = loaded["manifest"]
    if manifest["synthetic_test"] is not synthetic_test:
        raise ValueError("Model and freeze synthetic modes differ")
    registry_sha, _, _, _ = _registry_bound(identity_registry_payload, synthetic_test)
    frozen = _now()
    if _time(manifest["frozen_at"]) > frozen:
        raise ValueError("Cannot freeze before the model exists")
    result = {"version": VERSION, "frozen_at": frozen.isoformat(),
              "precommit_sha256": manifest["precommit_sha256"],
              "model_manifest_sha256": manifest["manifest_sha256"],
              "model_file_sha256": manifest["model_file_sha256"],
              "identity_registry_sha256": registry_sha, "code_sha256": _code_hashes(),
              "synthetic_test": synthetic_test, "cohort": COHORT,
              "production_change": False, "live_adjustment": 0}
    result["freeze_sha256"] = _hash(result)
    with Path(destination).open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return result


def _load_freeze(path, artifactdir, registry_payload, at, synthetic_test):
    if not isinstance(synthetic_test, bool):
        raise ValueError("Explicit boolean synthetic mode required")
    freeze = json.loads(Path(path).read_text())
    if (freeze.get("version") != VERSION or freeze.get("freeze_sha256") != _hash({
            key: value for key, value in freeze.items() if key != "freeze_sha256"})
            or freeze.get("production_change") is not False or freeze.get("live_adjustment") != 0
            or freeze.get("synthetic_test") is not synthetic_test or freeze.get("cohort") != COHORT
            or freeze.get("precommit_sha256") != load_precommit()["precommit_sha256"]):
        raise ValueError("Invalid exact v2 shadow freeze or synthetic mode")
    if _time(freeze["frozen_at"]) >= at:
        raise ValueError("Shadow freeze must precede actual execution")
    if freeze.get("code_sha256") != _code_hashes():
        raise ValueError("Frozen paired shadow code changed")
    registry_sha, groups, catalogue, identities = _registry_bound(registry_payload, synthetic_test)
    if freeze.get("identity_registry_sha256") != registry_sha:
        raise ValueError("Frozen identity registry changed")
    loaded = load_artifact(artifactdir, allow_synthetic_test=synthetic_test)
    if (loaded["manifest"]["manifest_sha256"] != freeze.get("model_manifest_sha256")
            or loaded["manifest"]["model_file_sha256"] != freeze.get("model_file_sha256")
            or loaded["manifest"]["synthetic_test"] is not synthetic_test):
        raise ValueError("Frozen model identity changed")
    return freeze, loaded, groups, catalogue, identities


SCHEMA = """
    create table lane (singleton integer primary key check(singleton=1), freeze_json text not null);
    create table sources (sha text primary key, receipt_json text not null);
    create table source_observations (
        snapshot_id integer primary key, event_id integer not null,
        observation_sha text not null, payload_json text not null);
    create table issues (
        event_id integer, issued_at text, fixture_group text not null, club_slug text not null,
        source_sha text not null references sources(sha), written_at text not null,
        issue_json text not null, lineage_json text not null, primary key(event_id,issued_at));
    create table predictions (
        event_id integer, issued_at text, horizon integer, model text, target_at text,
        prediction real, payload_json text not null, primary key(event_id,issued_at,horizon,model),
        foreign key(event_id,issued_at) references issues(event_id,issued_at));
    create table target_matches (
        event_id integer, issued_at text, horizon integer, source_sha text not null references sources(sha),
        matched_at text not null, label_json text not null, primary key(event_id,issued_at,horizon),
        foreign key(event_id,issued_at) references issues(event_id,issued_at));
    create table scores (
        event_id integer, issued_at text, horizon integer, model text, error real not null,
        absolute_error real not null, primary key(event_id,issued_at,horizon,model),
        foreign key(event_id,issued_at,horizon,model) references predictions(event_id,issued_at,horizon,model));
    create table scoring_attempts (
        event_id integer, issued_at text, horizon integer, source_sha text, status text not null,
        primary key(event_id,issued_at,horizon,source_sha));
"""
TABLES = {"lane", "sources", "source_observations", "issues", "predictions", "target_matches", "scores", "scoring_attempts"}


def _connect(path):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(destination, timeout=10)
    try:
        app = db.execute("pragma application_id").fetchone()[0]
        tables = {row[0] for row in db.execute("select name from sqlite_master where type='table'")}
        if app == 0 and not tables:
            db.executescript(SCHEMA)
            db.execute(f"pragma application_id={APPLICATION_ID}")
        elif app != APPLICATION_ID or tables != TABLES:
            raise ValueError("Refusing a foreign/frozen ledger or incompatible schema")
        db.execute("pragma foreign_keys=on")
        return db
    except BaseException:
        db.close()
        raise


def _bind_lane(db, freeze):
    previous = db.execute("select freeze_json from lane where singleton=1").fetchone()
    if previous and previous[0] != _json(freeze):
        raise ValueError("Ledger belongs to a different immutable freeze")
    if previous is None:
        db.execute("insert into lane values (1,?)", (_json(freeze),))


def _register(db, payload):
    """Register all source rows, including old incompatible and pending ones."""
    seen = set()
    for event in json.loads(payload)["events"]:
        for raw in event["observations"]:
            snapshot = _id(raw.get("snapshot_id"))
            if snapshot in seen:
                raise ValueError("Duplicate snapshot identity in original receipt")
            seen.add(snapshot)
    _register_observations(db, payload)


def _prepare(payload, issued, groups, identities):
    if not isinstance(payload, bytes):
        raise ValueError("Original source payload bytes required")
    batch = prepare_receipt(payload, issued)
    data = json.loads(payload)
    events = _label_events(payload, batch["receipt"]["retrieved_at"])
    selected, metadata = {}, {}
    for raw in sorted(data["events"], key=lambda event: _id(event["ticket_event_id"])):
        identifier = raw["ticket_event_id"]
        if identifier not in groups:
            raise ValueError("Unknown source identity; no alias guessing")
        domains = []
        if "source_domain" in raw:
            domain = raw["source_domain"]
            if not isinstance(domain, str) or not domain.strip():
                raise ValueError("Registry source domain identity mismatch")
            domains.append(domain.strip().lower())
        if "source_url" in raw:
            url = raw["source_url"]
            if not isinstance(url, str) or not url.strip():
                raise ValueError("Registry source URL identity mismatch")
            try:
                url_domain = urlparse(url).hostname
            except ValueError:
                url_domain = None
            if not isinstance(url_domain, str) or not url_domain.strip():
                raise ValueError("Registry source URL identity mismatch")
            domains.append(url_domain.strip().lower())
        external = raw.get("external_event_id")
        if "external_event_id" in raw and (isinstance(external, bool) or not isinstance(external, (int, str))
                                            or not str(external).strip()):
            raise ValueError("Registry external event identity mismatch")
        if not any(key[0] == raw.get("provider") and key[2] == raw.get("club_slug")
                   and all(key[1] == domain for domain in domains)
                   and (external is None or key[3] == str(external).strip())
                   for key in identities[identifier]):
            raise ValueError("Registry provider/club identity mismatch")
        group = groups[identifier]
        identity = (raw["club_slug"], _time(raw["kickoff_at"]))
        if group in metadata and metadata[group] != identity:
            raise ValueError("Alias metadata conflict")
        metadata[group] = identity
        selected.setdefault(group, identifier)
    prepared = []
    for group, identifier in sorted(selected.items()):
        event = events[identifier]
        rows = sorted(event["observations"], key=lambda row: (_time(row["captured_at"]), _id(row["snapshot_id"])))
        start = 0
        for index in range(1, len(rows)):
            if _key(rows[index]) != _key(rows[index - 1]):
                start = index
        segment = rows[start:]
        issue = build_issue({**event, "observations": segment}, issued)
        lineage = {"source_file_sha256": batch["receipt"]["source_file_sha256"],
                   "fixture_group": group, "prior_incompatible_rows_retained": start,
                   "current_segment_snapshot_ids": [row["snapshot_id"] for row in segment],
                   "raw_received_snapshot_ids": [row["snapshot_id"] for row in rows],
                   "current_segment_measurement_key": issue["measurement_key"],
                   "knowledge_clock_semantics": batch["receipt"]["knowledge_clock_semantics"],
                   "stable_released_pool_verified": False, "scenario_stability": "UNKNOWN"}
        prepared.append((group, issue, lineage))
    return batch, prepared


def capture(database, source_payload, artifactdir, freeze_path, identity_registry_payload, *, synthetic_test=False):
    """Append predictions issued NOW, with the same input/targets for every model."""
    issued = _now()
    freeze, loaded, groups, _, identities = _load_freeze(
        freeze_path, artifactdir, identity_registry_payload, issued, synthetic_test)
    batch, prepared = _prepare(source_payload, issued, groups, identities)
    predictions = []
    for group, issue, lineage in prepared:
        points = predict_baselines(issue, fixture_group=group)["points"]
        for point in points:
            candidate = predict(loaded, issue, point["horizon_hours"], group, allow_synthetic_test=synthetic_test)
            point["models"]["candidate"] = candidate
            # Apply the v2 input freshness gate symmetrically to all comparisons.
            if issue["status"] == "READY" and issue["latest_staleness_hours"] > 1:
                for name, output in point["models"].items():
                    point["models"][name] = {**output, "status": "UNAVAILABLE", "reason": "STALE_INPUT_FOR_V2",
                                              "predicted_available_total": None, "predicted_delta": None}
        predictions.append((group, issue, lineage, points))
    db, count, numeric = _connect(database), 0, 0
    try:
        db.execute("begin immediate")
        _bind_lane(db, freeze)
        sha = _source(db, batch["receipt"])
        _register(db, source_payload)
        for group, issue, lineage, points in predictions:
            identity = (issue["event"]["ticket_event_id"], issue["issued_at"])
            if db.execute("select 1 from issues where event_id=? and issued_at=?", identity).fetchone():
                raise ValueError("Issue already exists; never replace or backfill")
            db.execute("insert into issues values (?,?,?,?,?,?,?,?)", (
                *identity, group, issue["event"]["club_slug"], sha, issued.isoformat(), _json(issue), _json(lineage)))
            for point in points:
                for name, output in point["models"].items():
                    value = output.get("predicted_available_total")
                    if value is not None:
                        if (output.get("status") != "READY" or isinstance(value, bool)
                                or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
                                or point["target_at"] is None or _time(point["target_at"]) <= issued):
                            raise ValueError("Invalid or already elapsed numeric forecast")
                        numeric += 1
                    if name == "candidate" and output.get("target_at") != point["target_at"]:
                        raise ValueError("Candidate/baseline target mismatch")
                    payload = {**output, "input_manifest_sha256": issue["input_manifest_sha256"],
                               "precommit_sha256": freeze["precommit_sha256"], "freeze_sha256": freeze["freeze_sha256"],
                               "model_manifest_sha256": freeze["model_manifest_sha256"], "cohort": COHORT,
                               "synthetic_test": synthetic_test, "scenario_stability": "UNKNOWN",
                               "evidence_kind": "immutable_actual_time_paired_shadow"}
                    db.execute("insert into predictions values (?,?,?,?,?,?,?)", (
                        *identity, point["horizon_hours"], name, point["target_at"], value, _json(payload)))
                    count += 1
        # Check after SQLite lock acquisition and all inserts, immediately before
        # commit. A delayed transaction rolls back instead of claiming an earlier
        # written_at. There is no caller-supplied clock or replay/backdate path.
        written = _now()
        if not 0 <= (written - issued).total_seconds() <= 90:
            raise ValueError("Issue computation exceeded actual-time write allowance")
        if any(point["target_at"] is not None and _time(point["target_at"]) <= written
               for _, _, _, points in predictions for point in points
               if any(output.get("predicted_available_total") is not None for output in point["models"].values())):
            raise ValueError("Forecast target elapsed before actual persistence")
        for _, issue, _, _ in predictions:
            db.execute("update issues set written_at=? where event_id=? and issued_at=?", (
                written.isoformat(), issue["event"]["ticket_event_id"], issue["issued_at"]))
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    return {"version": VERSION, "issued_at": issued.isoformat(), "written_at": written.isoformat(),
            "input_issue_count": len(predictions), "prediction_status_rows": count,
            "numeric_forecast_count": numeric, "synthetic_test": synthetic_test,
            "production_change": False, "live_adjustment": 0}


def _match(event, issue, horizon, received):
    result = match_target(event, issue, horizon, received)
    if result["status"] != "MATCHED":
        return result
    issued, target = _time(issue["issued_at"]), _time(result["target_at"])
    interval = [row for row in event["observations"]
                if issued < _time(row["captured_at"]) <= target and _time(row["known_at"]) <= _time(received)]
    if any(not _usable(row) for row in interval):
        return {**result, "status": "TARGET_INTERVAL_UNUSABLE", "label": None, "label_sha256": None}
    return result


def score(database, source_payload, artifactdir, freeze_path, identity_registry_payload, *, synthetic_test=False):
    """Accept first later genuine label only; existing paired scores never change."""
    scored = _now()
    freeze, _, groups, _, identities = _load_freeze(
        freeze_path, artifactdir, identity_registry_payload, scored, synthetic_test)
    batch, _ = _prepare(source_payload, scored, groups, identities)
    received = batch["receipt"]["retrieved_at"]
    events = _label_events(source_payload, received)
    db, accepted, added = _connect(database), 0, 0
    try:
        db.execute("begin immediate")
        _bind_lane(db, freeze)
        sha = _source(db, batch["receipt"])
        _register(db, source_payload)
        targets = db.execute("""select distinct p.event_id,p.issued_at,p.horizon,i.issue_json
            from predictions p join issues i using(event_id,issued_at)
            where p.prediction is not null order by p.issued_at,p.event_id,p.horizon""").fetchall()
        for event_id, issued, horizon, original in targets:
            identity = (event_id, issued, horizon)
            if db.execute("select 1 from target_matches where event_id=? and issued_at=? and horizon=?", identity).fetchone():
                continue
            if db.execute("select 1 from scoring_attempts where event_id=? and issued_at=? and horizon=? and source_sha=?", (*identity, sha)).fetchone():
                continue
            matched = (_match(events[event_id], json.loads(original), horizon, received)
                       if event_id in events and _time(received) >= _time(issued)
                       else {"status": "EVENT_NOT_IN_RECEIPT"})
            db.execute("insert into scoring_attempts values (?,?,?,?,?)", (*identity, sha, matched["status"]))
            if matched["status"] != "MATCHED":
                continue
            db.execute("insert into target_matches values (?,?,?,?,?,?)", (*identity, sha, scored.isoformat(), _json(matched)))
            actual = matched["label"]["available_total"]
            for model, value in db.execute("select model,prediction from predictions where event_id=? and issued_at=? and horizon=? and prediction is not null", identity):
                error = value - actual
                db.execute("insert into scores values (?,?,?,?,?,?)", (*identity, model, error, abs(error)))
                added += 1
            accepted += 1
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    return {"version": VERSION, "accepted_targets": accepted, "added_scores": added,
            "scored_at": scored.isoformat(), "synthetic_test": synthetic_test,
            "production_change": False, "live_adjustment": 0}


def _metrics(events):
    if not events:
        return {"scored_fixtures": 0, "scored_points": 0, "event_balanced_mae": None, "event_balanced_bias": None}
    errors = [value for values in events.values() for value in values]
    return {"scored_fixtures": len(events), "scored_points": len(errors),
            "event_balanced_mae": sum(sum(abs(value) for value in values) / len(values) for values in events.values()) / len(events),
            "event_balanced_bias": sum(sum(values) / len(values) for values in events.values()) / len(events),
            "worst_absolute_error": max(map(abs, errors)),
            "p90_absolute_error_pooled_points_nearest_rank": sorted(map(abs, errors))[math.ceil(.9 * len(errors)) - 1]}


def report(database):
    """Read-only per-horizon errors and paired cohorts, with honest missingness."""
    path = Path(database).resolve()
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        if (db.execute("pragma application_id").fetchone()[0] != APPLICATION_ID
                or {row[0] for row in db.execute("select name from sqlite_master where type='table'")} != TABLES):
            raise ValueError("Foreign ledger or incompatible schema")
        grouped = defaultdict(lambda: defaultdict(list))
        rows = db.execute("""select i.fixture_group,s.event_id,s.issued_at,s.horizon,s.model,s.error
            from scores s join issues i using(event_id,issued_at)""").fetchall()
        by_coordinate = defaultdict(dict)
        for group, event, issued, horizon, model, error in rows:
            grouped[(horizon, model)][group].append(error)
            by_coordinate[(group, event, issued, horizon)][model] = error
        metrics = {f"+{h}h/{model}": _metrics(events) for (h, model), events in grouped.items()}
        paired = {}
        for h in HORIZONS:
            for benchmark in ("persistence", "drift", "pickup"):
                candidate_events, baseline_events, delta_events = defaultdict(list), defaultdict(list), defaultdict(list)
                for (group, _, _, horizon), models in by_coordinate.items():
                    if horizon == h and "candidate" in models and benchmark in models:
                        candidate_events[group].append(models["candidate"])
                        baseline_events[group].append(models[benchmark])
                        delta_events[group].append(abs(models["candidate"]) - abs(models[benchmark]))
                paired[f"+{h}h/candidate-vs-{benchmark}"] = {
                    "candidate": _metrics(candidate_events), "baseline": _metrics(baseline_events),
                    "event_balanced_mae_difference_candidate_minus_baseline": (
                        sum(sum(values) / len(values) for values in delta_events.values()) / len(delta_events)
                        if delta_events else None)}
        targets = db.execute("""select distinct p.event_id,p.issued_at,p.horizon,p.target_at,t.event_id
            from predictions p left join target_matches t using(event_id,issued_at,horizon)
            where p.prediction is not null""").fetchall()
        now = _now()
        lane = db.execute("select freeze_json from lane where singleton=1").fetchone()
        return {"version": VERSION, "measurement": METRIC,
                "issues": db.execute("select count(*) from issues").fetchone()[0],
                "prediction_status_rows": db.execute("select count(*) from predictions").fetchone()[0],
                "numeric_forecasts": db.execute("select count(*) from predictions where prediction is not null").fetchone()[0],
                "scores": len(rows), "matched_targets": db.execute("select count(*) from target_matches").fetchone()[0],
                "pending_targets": sum(_time(row[3]) > now for row in targets),
                "mature_unmatched_targets": sum(_time(row[3]) <= now and row[4] is None for row in targets),
                "metrics": metrics, "paired_metrics": paired, "review_eligible_new_fixtures": 0,
                "formal_review_gate": "CLOSED", "required_new_fixtures": 30, "required_new_clubs": 8,
                "cohort": COHORT, "synthetic_test": json.loads(lane[0])["synthetic_test"] if lane else None,
                "production_change": False, "live_adjustment": 0}
