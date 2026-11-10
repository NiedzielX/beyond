"""Allowlisted read-only export of immutable, paired rolling72 v2 forecasts.

No fitting, inference, backfilling, source requests or ledger writes occur here.
Hashes establish internal consistency, not independent source authentication.
Public availability is not paid sales or attendance. The model freeze timestamp
is exported only when its original hash-verified manifest is supplied.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from ml.demand_engine.rolling72_features_v1 import HORIZONS, _hash, _id, _time, features
from ml.rolling72_feed_v1 import _number, _receipt, _same, _score, _sha
from ml.rolling72_offline_challenger_v2 import VERSION as CANDIDATE_ID, PRECOMMIT_SHA256
from ml.rolling72_paired_shadow_v2 import APPLICATION_ID, COHORT, TABLES, VERSION as LEDGER_VERSION


VERSION = "rolling72-shadow-feed-v2"
METRIC = "public-displayed-available-total-v1"
MODELS = {"candidate": CANDIDATE_ID, "persistence": "rolling72-persistence-v1",
          "drift": "rolling72-observed-24h-drift-v1", "pickup": "rolling72-conditional-pickup-v1"}
EVIDENCE = "immutable_actual_time_paired_shadow"


def _manifest(value, freeze, generated):
    if value is None:
        return None
    if (not isinstance(value, dict) or value.get("manifest_sha256") != _hash({
            k: v for k, v in value.items() if k != "manifest_sha256"})
            or value.get("manifest_sha256") != freeze["model_manifest_sha256"]
            or value.get("model_file_sha256") != freeze["model_file_sha256"]
            or value.get("version") != CANDIDATE_ID
            or value.get("precommit_sha256") != PRECOMMIT_SHA256
            or value.get("synthetic_test") is not freeze["synthetic_test"]
            or value.get("historical_knowledge_unproven") is not True
            or value.get("historical_validation_accuracy_claim_allowed") is not False
            or value.get("production_change") is not False or value.get("live_adjustment") != 0):
        raise ValueError("Original model manifest does not match the immutable lane")
    if not _time(value["fit_started_at"]) <= _time(value["frozen_at"]) <= _time(freeze["frozen_at"]) <= generated:
        raise ValueError("Model fit/freeze clocks mismatch")
    return value


def build_feed(database: str | Path, *, generated_at=None, model_manifest=None, allow_synthetic_test=False):
    """Read one consistent snapshot, with explicit opt-in for synthetic fixtures."""
    if not isinstance(allow_synthetic_test, bool):
        raise ValueError("Explicit synthetic mode required")
    generated = _time(generated_at) if generated_at is not None else datetime.now(timezone.utc)
    db = sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        db.execute("pragma query_only=on")
        db.execute("begin")
        if (db.execute("pragma application_id").fetchone()[0] != APPLICATION_ID
                or {r[0] for r in db.execute("select name from sqlite_master where type='table'")} != TABLES
                or db.execute("select 1 from sqlite_master where type in ('view','trigger')").fetchone()
                or db.execute("pragma foreign_key_check").fetchall()):
            raise ValueError("Not an intact paired rolling72 v2 ledger")
        lane = db.execute("select singleton,freeze_json from lane").fetchall()
        if len(lane) != 1 or lane[0][0] != 1:
            raise ValueError("Ledger has no single immutable freeze")
        freeze = json.loads(lane[0][1])
        if (freeze.get("version") != LEDGER_VERSION
                or freeze.get("freeze_sha256") != _hash({k: v for k, v in freeze.items() if k != "freeze_sha256"})
                or freeze.get("precommit_sha256") != PRECOMMIT_SHA256 or freeze.get("cohort") != COHORT
                or not isinstance(freeze.get("synthetic_test"), bool)
                or freeze.get("production_change") is not False or freeze.get("live_adjustment") != 0
                or _time(freeze["frozen_at"]) > generated):
            raise ValueError("Paired ledger freeze mismatch")
        if freeze["synthetic_test"] and not allow_synthetic_test:
            raise ValueError("Synthetic feed needs explicit test opt-in")
        for name in ("freeze_sha256", "model_manifest_sha256", "model_file_sha256", "identity_registry_sha256"):
            _sha(freeze.get(name))
        manifest = _manifest(model_manifest, freeze, generated)
        vintages = []
        for event_id, issued_at, fixture_group, club_slug, source_sha, written_at, serialized, raw_lineage in db.execute(
                "select event_id,issued_at,fixture_group,club_slug,source_sha,written_at,issue_json,lineage_json from issues order by issued_at,event_id").fetchall():
            issue, lineage = json.loads(serialized), json.loads(raw_lineage)
            event = issue["event"]
            if (_id(event["ticket_event_id"]) != event_id or issue["issued_at"] != issued_at
                    or not isinstance(event.get("club_slug"), str) or not event["club_slug"].strip()
                    or event["club_slug"] != club_slug
                    or not isinstance(issue.get("status"), str) or not issue["status"].strip()
                    or issue.get("prefix_sha256") != _hash(issue.get("observed_prefix"))
                    or issue.get("input_manifest_sha256") != _hash({k: v for k, v in issue.items() if k != "input_manifest_sha256"})
                    or issue.get("production_change") is not False or issue.get("live_adjustment") != 0
                    or issue.get("model_fit_performed") is not False or issue.get("target_values_used") is not False
                    or lineage.get("source_file_sha256") != source_sha or lineage.get("fixture_group") != fixture_group
                    or lineage.get("current_segment_measurement_key") != issue["measurement_key"]
                    or lineage.get("scenario_stability") != "UNKNOWN"):
                raise ValueError("Persisted issue lineage mismatch")
            issued, written = _time(issued_at), _time(written_at)
            receipt = _receipt(db, source_sha)
            if (not _time(freeze["frozen_at"]) < issued <= written <= generated
                    or (written - issued).total_seconds() > 90
                    or _time(event["known_at"]) != _time(receipt["retrieved_at"])
                    or _time(event["known_at"]) > issued):
                raise ValueError("Persisted issue clocks mismatch")
            observations, seen_ids, seen_times = [], set(), set()
            for observation in issue["observed_prefix"]:
                capture, known = _time(observation["captured_at"]), _time(observation["known_at"])
                snapshot, value = _id(observation["snapshot_id"]), _number(observation["available_total"])
                if (snapshot in seen_ids or capture in seen_times or value < 0 or capture > known
                        or known != _time(receipt["retrieved_at"]) or capture > _time(receipt["exported_at"])
                        or known > issued or observation.get("measurement_key") != issue["measurement_key"]
                        or any(observation.get(flag) is not None and not isinstance(observation[flag], bool)
                               for flag in ("source_active", "source_visible"))):
                    raise ValueError("Observed prefix clocks/identity mismatch")
                seen_ids.add(snapshot); seen_times.add(capture)
                observations.append({"snapshot_id": snapshot, "captured_at": capture.isoformat(),
                    "known_at": known.isoformat(), "available_total": value, "measurement_key": observation["measurement_key"],
                    "source_active": observation.get("source_active"), "source_visible": observation.get("source_visible")})
            if observations != sorted(observations, key=lambda item: _time(item["captured_at"])):
                raise ValueError("Unsorted prefix")
            rows = db.execute("""select horizon,model,target_at,prediction,payload_json from predictions
                where event_id=? and issued_at=? order by horizon,model""", (event_id, issued_at)).fetchall()
            by_coordinate = {(h, m): (t, v, p) for h, m, t, v, p in rows}
            if len(rows) != 12 or set(by_coordinate) != {(h, m) for h in HORIZONS for m in MODELS}:
                raise ValueError("Incomplete or unexpected persisted forecast/status coordinates")
            points = []
            for horizon in HORIZONS:
                coordinate, models = features(issue, horizon), {}
                for name, model_id in MODELS.items():
                    target, predicted, raw = by_coordinate[horizon, name]
                    payload = json.loads(raw)
                    if (target != coordinate["target_at"]
                            or payload.get("model_id" if name != "candidate" else "version") != model_id
                            or payload.get("input_manifest_sha256") != issue["input_manifest_sha256"]
                            or payload.get("precommit_sha256") != freeze["precommit_sha256"]
                            or payload.get("freeze_sha256") != freeze["freeze_sha256"]
                            or payload.get("model_manifest_sha256") != freeze["model_manifest_sha256"]
                            or payload.get("scenario_stability") != "UNKNOWN" or payload.get("cohort") != COHORT
                            or payload.get("synthetic_test") is not freeze["synthetic_test"]
                            or payload.get("evidence_kind") != EVIDENCE):
                        raise ValueError("Persisted prediction lineage mismatch")
                    original_status = payload.get("status")
                    if not isinstance(original_status, str) or not original_status.strip():
                        raise ValueError("Prediction status required")
                    delta = payload.get("predicted_delta")
                    reason = None
                    if predicted is None:
                        if (original_status == "READY" or payload.get("predicted_available_total") is not None or delta is not None):
                            raise ValueError("Unavailable prediction is not null")
                        reason = payload.get("reason") or payload.get("status_reason") or original_status
                        if not isinstance(reason, str) or not reason.strip() or reason == "UNAVAILABLE":
                            raise ValueError("Unavailable prediction reason required")
                    elif (coordinate["status"] != "READY" or original_status != "READY" or _number(predicted) < 0
                            or payload.get("status_reason") is not None or payload.get("reason") is not None
                            or not _same(predicted, payload.get("predicted_available_total"))
                            or not _same(delta, predicted - issue["last_available_total"])
                            or _time(target) <= written or issue["latest_staleness_hours"] > 1):
                        raise ValueError("Numeric forecast/coordinate mismatch")
                    outside = None
                    if name == "candidate":
                        if (payload.get("historical_training_knowledge_unproven") is not True
                                or payload.get("issued_at") != issued_at or payload.get("horizon_hours") != horizon
                                or payload.get("target_at") != target
                                or payload.get("production_change") is not False or payload.get("live_adjustment") != 0
                                or not issued <= _time(payload["computed_at"]) <= written):
                            raise ValueError("Candidate issue/model computation clocks mismatch")
                        if predicted is not None:
                            outside = payload.get("outside_training_maturity_range")
                            if (not isinstance(outside, bool) or payload.get("intervals") is not None
                                    or not _same(payload.get("effective_lead_hours"), horizon + issue["latest_staleness_hours"])
                                    or not _same(payload.get("capture_alignment_shift_hours"), issue["latest_staleness_hours"])):
                                raise ValueError("Candidate coverage/horizon semantics mismatch")
                            if manifest is not None:
                                minimum, maximum = manifest["training_maturity_range_hours"]
                                expected = not minimum <= coordinate["features"]["hours_to_kickoff"] <= maximum
                                if outside is not expected:
                                    raise ValueError("Candidate maturity flag differs from frozen training range")
                    models[name] = {"model_id": model_id, "status": "UNAVAILABLE" if predicted is None else "READY",
                        "status_reason": reason, "predicted_available_total": predicted, "predicted_delta": delta,
                        "outside_training_maturity_range": outside,
                        "historical_training_knowledge_unproven": True if name == "candidate" else None,
                        "score": _score(db, (event_id, issued_at, horizon), name, predicted, issue, coordinate, generated)}
                points.append({"horizon_hours": horizon, "target_at": coordinate["target_at"], "status": coordinate["status"], "models": models})
            vintages.append({"ticket_event_id": event_id, "club_slug": club_slug, "kickoff_at": event["kickoff_at"],
                "event_known_at": event["known_at"], "issued_at": issued_at, "written_at": written_at, "status": issue["status"],
                "measurement_key": issue["measurement_key"], "input_manifest_sha256": issue["input_manifest_sha256"],
                "prefix_sha256": issue["prefix_sha256"], "source_receipt_sha256": source_sha,
                "precommit_sha256": freeze["precommit_sha256"], "freeze_sha256": freeze["freeze_sha256"],
                "model_manifest_sha256": freeze["model_manifest_sha256"], "historical_training_knowledge_unproven": True,
                "scenario_stability": "UNKNOWN", "cohort": COHORT, "observations": observations, "points": points})
        return {"version": VERSION, "generated_at": generated.isoformat(), "metric": METRIC, "evidence_kind": EVIDENCE,
                "production_change": False, "live_adjustment": 0, "synthetic_test": freeze["synthetic_test"],
                "frozen_at": freeze["frozen_at"], "model_manifest_sha256": freeze["model_manifest_sha256"],
                "model_frozen_at": manifest["frozen_at"] if manifest is not None else None,
                "historical_training_knowledge_unproven": True, "vintages": vintages}
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-manifest", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.model_manifest.read_text()) if args.model_manifest else None
    feed = build_feed(args.database, model_manifest=manifest)
    with args.output.open("x") as stream:
        json.dump(feed, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"version": VERSION, "vintage_count": len(feed["vintages"]), "production_change": False}))


if __name__ == "__main__":
    main()
