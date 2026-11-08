"""Receipt-bound rolling72 feature capture, never model fitting or forecasts.

The public export lacks original row ingestion clocks. A real retrieved_at
receipt proves only a conservative knowledge upper bound for that copy. All
rows and the exact event metadata version get that bound, so no issue earlier
than retrieval can be reconstructed. Public displayed availability is the
measurement; unchanged released pool, transactions and interventions are NOT
verified. No hosted service or frozen experiment is modified.

The SQLite file is a NEW local feature store, not a prospective forecast ledger.
The CLI uses actual execution time and has no backdate option. Callers must
retain the original export outside Git. Stored input hashes identify the full
prefix and its declared provenance; raw exports are not copied into the store.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from ml.demand_engine.rolling72_features_v1 import (
    HORIZONS, _hash, _time, build_issue, features,
)


VERSION = "rolling72-receipt-feature-store-v1"
METRIC = "public-displayed-available-total-v1"
APPLICATION_ID = 0x52373231


def prepare_receipt(payload: bytes, issued_at) -> dict:
    """Prepare issues/features from bytes known by retrieval, without any I/O."""
    data = json.loads(payload)
    if not isinstance(data, dict) or data.get("version") != "daily-inventory-public-export-v1":
        raise ValueError("Expected public-export-v1 receipt")
    # Export-v1 uses canonical JSON with unescaped unicode, matching _hash.
    if data.get("export_sha256") != _hash({key: value for key, value in data.items()
                                          if key != "export_sha256"}):
        raise ValueError("Export manifest hash mismatch")
    exported = _time(data["exported_at"])
    retrieved = _time(data["retrieved_at"])
    issued = _time(issued_at)
    if exported > retrieved:
        raise ValueError("Export cutoff follows retrieval")
    if issued < retrieved:
        raise ValueError("Cannot create an issue before the original receipt")
    if not isinstance(data.get("events"), list):
        raise ValueError("Events list required")
    receipt = {
        "version": VERSION, "source_file_sha256": hashlib.sha256(payload).hexdigest(),
        "source_manifest_sha256": data["export_sha256"],
        "exported_at": exported.isoformat(), "retrieved_at": retrieved.isoformat(),
        "knowledge_clock_semantics": "known_by_receipt_upper_bound_not_original_ingestion",
        "measurement_definition": METRIC,
        "historical_ingestion_known_at_proven": False,
        "stable_released_pool_verified": False, "intervention_status": "UNKNOWN",
        "raw_table_immutability_proven": False,
    }
    records, seen = [], set()
    for source_event in data["events"]:
        event_id = source_event["ticket_event_id"]
        if event_id in seen:
            raise ValueError("Duplicate event identity in receipt")
        seen.add(event_id)
        raw_rows = source_event["observations"]
        if not isinstance(raw_rows, list):
            raise ValueError("Observation list required")
        rows = []
        for raw in raw_rows:
            captured = _time(raw["captured_at"])
            if captured > exported:
                raise ValueError("Snapshot exceeds original export cutoff")
            original_key = raw.get("measurement_key")
            # Namespace states the observable definition; pool continuity remains unproven.
            key = METRIC + ":" + original_key if isinstance(original_key, str) and original_key.strip() else None
            rows.append({"snapshot_id": raw.get("snapshot_id"),
                         "captured_at": captured.isoformat(), "known_at": retrieved.isoformat(),
                         "available_total": raw.get("available_total"), "measurement_key": key,
                         "source_active": raw.get("source_active"),
                         "source_visible": raw.get("source_visible")})
        issue = build_issue({"ticket_event_id": event_id, "club_slug": source_event["club_slug"],
                             "kickoff_at": source_event["kickoff_at"], "known_at": retrieved.isoformat(),
                             "observations": rows}, issued)
        records.append({"issue": issue, "horizons": [features(issue, lead) for lead in HORIZONS]})
    result = {"version": VERSION, "receipt": receipt, "issued_at": issued.isoformat(),
              "records": sorted(records, key=lambda record: record["issue"]["event"]["ticket_event_id"]),
              "forecast_count": 0, "model_fit_performed": False,
              "production_change": False, "live_adjustment": 0}
    result["batch_sha256"] = _hash(result)
    return result


def _connect(path: str | Path) -> sqlite3.Connection:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(destination, timeout=10)
    try:
        application = connection.execute("pragma application_id").fetchone()[0]
        tables = connection.execute("select name from sqlite_master where type='table'").fetchall()
        if application != APPLICATION_ID and (application != 0 or tables):
            raise ValueError("Refusing an existing foreign/frozen ledger")
        connection.execute(f"pragma application_id={APPLICATION_ID}")
        connection.execute("pragma foreign_keys=on")
        connection.executescript("""
            create table if not exists receipts (
                source_sha text primary key, payload_json text not null);
            create table if not exists issues (
                event_id integer not null, issued_at text not null,
                input_sha text not null, source_sha text not null references receipts(source_sha),
                payload_json text not null, primary key(event_id,issued_at));
            create table if not exists feature_rows (
                event_id integer not null, issued_at text not null, horizon integer not null,
                payload_json text not null, primary key(event_id,issued_at,horizon),
                foreign key(event_id,issued_at) references issues(event_id,issued_at));
        """)
        return connection
    except BaseException:
        connection.close()
        raise


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def persist_batch(path: str | Path, batch: dict) -> dict:
    """Append one canonical batch atomically; never revise an existing issue."""
    if batch.get("version") != VERSION or batch.get("batch_sha256") != _hash({
            key: value for key, value in batch.items() if key != "batch_sha256"}):
        raise ValueError("Batch version/hash mismatch")
    if (batch.get("production_change") is not False or batch.get("live_adjustment") != 0
            or batch.get("forecast_count") != 0 or batch.get("model_fit_performed") is not False):
        raise ValueError("Only feature capture is allowed")
    receipt = batch["receipt"]
    retrieved = _time(receipt["retrieved_at"])
    if (receipt.get("version") != VERSION or receipt.get("measurement_definition") != METRIC
            or receipt.get("knowledge_clock_semantics") != "known_by_receipt_upper_bound_not_original_ingestion"
            or _time(receipt["exported_at"]) > retrieved or _time(batch["issued_at"]) < retrieved):
        raise ValueError("Invalid receipt knowledge bound")
    # Verify every issue and derived feature against its immutable canonical prefix.
    identities = set()
    for record in batch["records"]:
        issue = record["issue"]
        identity = (issue["event"]["ticket_event_id"], issue["issued_at"])
        if identity in identities or issue["issued_at"] != batch["issued_at"]:
            raise ValueError("Duplicate or inconsistent issue identity")
        identities.add(identity)
        if (_time(issue["event"]["known_at"]) != retrieved
                or any(_time(row["known_at"]) != retrieved
                       for row in issue["observed_prefix"])):
            raise ValueError("Issue knowledge clocks differ from original receipt")
        if record["horizons"] != [features(issue, lead) for lead in HORIZONS]:
            raise ValueError("Feature rows differ from canonical issue")
    source_sha = batch["receipt"]["source_file_sha256"]
    receipt_json = _json(batch["receipt"])
    connection = _connect(path)
    inserted = 0
    try:
        connection.execute("begin immediate")
        existing_receipt = connection.execute("select payload_json from receipts where source_sha=?", (source_sha,)).fetchone()
        if existing_receipt and existing_receipt[0] != receipt_json:
            raise ValueError("Receipt identity conflict")
        if not existing_receipt:
            connection.execute("insert into receipts values (?,?)", (source_sha, receipt_json))
        for record in batch["records"]:
            issue = record["issue"]
            identity = (issue["event"]["ticket_event_id"], issue["issued_at"])
            prior = connection.execute("select payload_json,source_sha from issues where event_id=? and issued_at=?", identity).fetchone()
            serialized = _json(issue)
            if prior:
                if prior != (serialized, source_sha):
                    raise ValueError("Immutable issue conflict; refusing replacement")
                rows = connection.execute("select horizon,payload_json from feature_rows where event_id=? and issued_at=? order by horizon", identity).fetchall()
                if rows != [(lead, _json(point)) for lead, point in zip(HORIZONS, record["horizons"])]:
                    raise ValueError("Stored feature rows differ from original issue")
                continue
            connection.execute("insert into issues values (?,?,?,?,?)",
                               (*identity, issue["input_manifest_sha256"], source_sha, serialized))
            for lead, point in zip(HORIZONS, record["horizons"]):
                connection.execute("insert into feature_rows values (?,?,?,?)", (*identity, lead, _json(point)))
            inserted += 1
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"version": VERSION, "inserted_issue_count": inserted, "input_issue_count": len(batch["records"]),
            "forecast_count": 0, "source_file_sha256": source_sha, "production_change": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Existing original private export")
    parser.add_argument("--database", type=Path, required=True, help="NEW private feature-store SQLite file")
    args = parser.parse_args()
    if args.database.resolve() == args.input.resolve():
        parser.error("Input and database must be different files")
    payload = args.input.read_bytes()
    issued = datetime.now(timezone.utc)
    print(json.dumps(persist_batch(args.database, prepare_receipt(payload, issued))))


if __name__ == "__main__":
    main()
