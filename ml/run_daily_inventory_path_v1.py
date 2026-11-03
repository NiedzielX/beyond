"""Research CLI for genuine-prefix -> future daily public-inventory paths.

No command writes to Supabase or changes production. Historical replay is
explicitly diagnostic. Only ``shadow`` can create local prospective evidence,
using wall-clock execution time and a model frozen before the daily cutoff.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from ml.demand_engine.daily_inventory_path_dataset_v1 import (
    DATASET_VERSION, build_dataset, build_issue, canonical_hash, parse_timestamp,
)
from ml.demand_engine.daily_inventory_path_model_v1 import (
    MIN_TRAIN_EVENTS, MODEL_VERSION, evaluate_points, fit_model, load_model,
    predict_path, save_model,
)

UTC = timezone.utc
EXPORT_VERSION = "daily-inventory-public-export-v1"
PREVIEW_VERSION = "daily-inventory-path-preview-v1"
FROZEN_MODEL_REGISTRY = Path(__file__).parent / "artifacts/daily_inventory_path_v1.json"


def _now() -> datetime:
    return datetime.now(UTC)


def _dump(path: str | Path, payload: Any, *, exclusive: bool = False) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if exclusive:
        with destination.open("x") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        return
    with tempfile.NamedTemporaryFile("w", dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    temporary.replace(destination)


def load_export(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text())
    if data.get("version") != EXPORT_VERSION or not isinstance(data.get("events"), list):
        raise ValueError("Expected a daily-inventory-public-export-v1 manifest")
    parse_timestamp(data["exported_at"])
    expected = canonical_hash({key: value for key, value in data.items() if key != "export_sha256"})
    if data.get("export_sha256") != expected:
        raise ValueError("Public export manifest hash mismatch")
    return data


class PublicInventoryReader:
    """Read only the public-source event/snapshot columns needed by this lane."""

    def __init__(self) -> None:
        base = os.environ.get("SUPABASE_URL", "").rstrip("/")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        parsed = urllib.parse.urlparse(base)
        if parsed.scheme != "https" or not parsed.hostname or not key:
            raise ValueError("HTTPS SUPABASE_URL and service-role binding are required")
        self.base = base
        self.headers = {"apikey": key, "Accept": "application/json"}
        if not key.startswith("sb_"):
            self.headers["Authorization"] = "Bearer " + key

    def rows(self, table: str, parameters: list[tuple[str, str]]) -> list[dict]:
        # Keyset pagination avoids silently truncating the common 1000-row cap.
        result: list[dict] = []
        after = 0
        while True:
            query = urllib.parse.urlencode(parameters + [
                ("id", f"gt.{after}"), ("order", "id.asc"), ("limit", "1000"),
            ])
            request = urllib.request.Request(
                self.base + "/rest/v1/" + table + "?" + query,
                headers=self.headers,
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    page = json.load(response)
            except urllib.error.HTTPError as exc:
                # Never echo request headers or secret-bearing exception details.
                raise ValueError(f"Read-only {table} export returned HTTP {exc.code}") from None
            if not isinstance(page, list):
                raise ValueError("Unexpected REST export shape")
            if not page:
                return result
            next_id = max(int(row["id"]) for row in page)
            if next_id <= after:
                raise ValueError("Export pagination did not advance")
            result.extend(page)
            after = next_id


def export_public(reader: PublicInventoryReader, as_of_at: str | datetime) -> dict:
    as_of = parse_timestamp(as_of_at)
    if as_of > _now():
        raise ValueError("A public export cannot use a future cutoff")
    events = reader.rows("ticket_events", [
        ("select", "id,club_slug,provider,kickoff_at,competition,home_team,away_team"),
        ("kickoff_at", "gte." + (as_of - timedelta(days=90)).isoformat()),
        ("kickoff_at", "lte." + (as_of + timedelta(days=60)).isoformat()),
    ])
    registry: dict[int, dict] = {}
    excluded = Counter()
    for event in events:
        if not event.get("club_slug") or not event.get("provider") or not event.get("kickoff_at"):
            excluded["missing_event_identity"] += 1
            continue
        registry[int(event["id"])] = {
            "ticket_event_id": int(event["id"]),
            "club_slug": event["club_slug"], "provider": event["provider"],
            "kickoff_at": parse_timestamp(event["kickoff_at"]).isoformat(),
            "home_team": event.get("home_team"), "away_team": event.get("away_team"),
            "competition": event.get("competition"), "observations": [],
        }
    identifiers = sorted(registry)
    for offset in range(0, len(identifiers), 100):
        group = identifiers[offset:offset + 100]
        snapshots = reader.rows("snapshots", [
            ("select", "id,ticket_event_id,captured_at,available_total,source,sector_count"),
            ("ticket_event_id", "in.(" + ",".join(map(str, group)) + ")"),
            ("captured_at", "lte." + as_of.isoformat()),
        ])
        for row in snapshots:
            event = registry[int(row["ticket_event_id"])]
            source = row.get("source")
            event["observations"].append({
                "snapshot_id": int(row["id"]),
                "captured_at": parse_timestamp(row["captured_at"]).isoformat(),
                "available_total": row.get("available_total"),
                # Missing identity remains missing, rather than inventing one.
                "measurement_key": f'{event["provider"]}/{source}' if source else "",
                "source": source, "sector_count": row.get("sector_count"),
            })
    result = {
        "version": EXPORT_VERSION, "exported_at": as_of.isoformat(),
        "retrieved_at": _now().isoformat(), "production_change": False,
        "source_state_metadata_available": False,
        "limitations": [
            "Public snapshots do not contain active/visible source-state flags.",
            "Measurement key identifies provider/source, not verified sales or a constant released pool.",
            "Current event kickoff metadata is not a historical kickoff-revision ledger.",
            "Retrospective replay is diagnostic, never backfilled prospective evidence.",
        ],
        "excluded_event_counts": dict(excluded),
        "events": sorted(registry.values(), key=lambda e: (e["kickoff_at"], e["ticket_event_id"])),
    }
    result["export_sha256"] = canonical_hash(result)
    return result


def diagnostic_evaluation(dataset: dict, events: list[dict]) -> dict:
    """One fixed event-grouped chronological split; never choose a winning split."""
    rows = dataset["rows"]
    present = {row["issue"]["ticket_event_id"] for row in rows}
    ordered = sorted(
        (event for event in events if event["ticket_event_id"] in present),
        key=lambda e: (parse_timestamp(e["kickoff_at"]), e["ticket_event_id"]),
    )
    result: dict[str, Any] = {
        "status": "INSUFFICIENT_DIAGNOSTIC_EVIDENCE",
        "evidence_kind": "retrospective_diagnostic_not_prospective",
        "production_change": False,
        "split_protocol": "event_grouped_chronological_70_30_same_kickoff_together",
    }
    if len(ordered) < MIN_TRAIN_EVENTS + 1:
        return {**result, "reason": "Too few labeled independent events"}
    boundary_index = min(len(ordered) - 1, math.ceil(.7 * len(ordered)))
    boundary = parse_timestamp(ordered[boundary_index]["kickoff_at"])
    train_ids = {e["ticket_event_id"] for e in ordered if parse_timestamp(e["kickoff_at"]) < boundary}
    test_ids = present - train_ids
    test_rows = [row for row in rows if row["issue"]["ticket_event_id"] in test_ids]
    if not test_rows:
        return {**result, "reason": "No test labels after same-kickoff grouping"}
    cutoff = min(parse_timestamp(row["issue"]["issued_as_of_at"]) for row in test_rows)
    train_rows = [
        row for row in rows if row["issue"]["ticket_event_id"] in train_ids
        and parse_timestamp(row["target_at"]) <= cutoff
        and parse_timestamp(row["target_captured_at"]) <= cutoff
    ]
    supporting = {row["issue"]["ticket_event_id"] for row in train_rows}
    result.update({
        "train_event_ids": sorted(supporting), "test_event_ids": sorted(test_ids),
        "trained_through": cutoff.isoformat(), "train_row_count": len(train_rows),
    })
    if len(supporting) < MIN_TRAIN_EVENTS:
        return {**result, "reason": "Fewer than five train events with labels known at the first test issue"}
    model = fit_model(train_rows, cutoff)
    points = []
    unique = {}
    for row in test_rows:
        issue = row["issue"]
        unique[(issue["ticket_event_id"], issue["issued_as_of_at"])] = issue
    for issue in unique.values():
        points.extend(predict_path(issue, model))
    return {**result, "status": "DIAGNOSTIC_ONLY", "metrics": evaluate_points(points, test_rows)}


def fit_research(data: dict, trained_through: str, artifact_path: str | Path) -> dict:
    cutoff = parse_timestamp(trained_through)
    if cutoff > parse_timestamp(data["exported_at"]):
        raise ValueError("Training cutoff exceeds export cutoff")
    if Path(artifact_path).exists():
        raise ValueError("Artifact already exists: use preview/shadow; v1 is not refitted")
    if FROZEN_MODEL_REGISTRY.exists():
        raise ValueError("Candidate v1 is already frozen: a different output filename does not authorize a refit")
    dataset = build_dataset(data["events"], data["exported_at"])
    completed = {
        event["ticket_event_id"] for event in data["events"]
        if parse_timestamp(event["kickoff_at"]) <= cutoff
    }
    train_rows = [
        row for row in dataset["rows"]
        if row["issue"]["ticket_event_id"] in completed
        and parse_timestamp(row["target_at"]) <= cutoff
        and parse_timestamp(row["target_captured_at"]) <= cutoff
    ]
    # The diagnostic cannot tune or choose this separately precommitted final fit.
    model = fit_model(train_rows, cutoff)
    save_model(model, artifact_path)
    return {
        "version": "daily-inventory-path-research-report-v1",
        "export_sha256": data["export_sha256"], "dataset_version": DATASET_VERSION,
        "generated_at": _now().isoformat(), "evidence_kind": "retrospective_diagnostic_not_prospective",
        "coverage": dataset["coverage"], "diagnostic_evaluation": diagnostic_evaluation(dataset, data["events"]),
        "final_research_fit": {key: model[key] for key in (
            "model_version", "model_sha256", "trained_through", "fitted_at",
            "training_event_ids", "training_row_count", "training_manifest_sha256",
        )},
        "production_change": False, "live_adjustment": 0,
    }


def preview(data: dict, model: dict, as_of_at: str | datetime) -> dict:
    as_of = parse_timestamp(as_of_at)
    if as_of > parse_timestamp(data["exported_at"]):
        raise ValueError("Preview cutoff exceeds the public export cutoff")
    result = []
    for event in data["events"]:
        kickoff = parse_timestamp(event["kickoff_at"])
        if kickoff <= as_of:
            continue
        days = math.ceil((kickoff - as_of).total_seconds() / 86400)
        if not 1 <= days <= 60:
            continue
        issue = build_issue(event, kickoff - timedelta(days=days))
        points = []
        prediction_status = issue["status"]
        reason = issue.get("status_reason")
        if issue["status"] == "READY":
            if parse_timestamp(model["trained_through"]) > parse_timestamp(issue["issued_as_of_at"]):
                prediction_status, reason = "MODEL_AFTER_ISSUE", "Training cutoff is later than this daily issue"
            elif issue["ticket_event_id"] in model["training_event_ids"]:
                prediction_status, reason = "EVENT_IN_TRAINING", "Target event belongs to the training registry"
            else:
                points = predict_path(issue, model)
        ready = issue["status"] == "READY"
        result.append({
            "ticket_event_id": issue["ticket_event_id"], "club_slug": issue["club_slug"],
            "kickoff_at": issue["kickoff_at"], "issued_as_of_at": issue["issued_as_of_at"],
            "days_to_event": issue["days_to_event"], "status": prediction_status, "status_reason": reason,
            "input_status": issue["status"],
            "measurement_key": issue["measurement_key"] if ready else None,
            "observations": issue["observed_prefix"] if ready else [], "points": points,
            "model_version": model["model_version"], "model_sha256": model["model_sha256"],
            "input_manifest_sha256": issue["input_manifest_sha256"],
            "source_state_metadata_complete": issue["source_state_metadata_complete"],
        })
    return {
        "version": PREVIEW_VERSION, "generated_at": _now().isoformat(),
        "data_as_of_at": as_of.isoformat(), "training_cutoff": model["trained_through"],
        "evidence_kind": "research_preview_not_prospective", "production_change": False,
        "export_sha256": data["export_sha256"], "events": result,
    }


def ledger_metrics(ledger_path: str | Path, as_of_at: str | datetime) -> dict:
    """Descriptive paired metrics from immutable scored rows, never retraining."""
    as_of = parse_timestamp(as_of_at)
    from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger
    with DailyInventoryPathLedger(ledger_path) as ledger:
        attempts = {a["attempt_id"]: a for a in ledger.export_attempts()}
        points = ledger.export_points()
    labels = []
    for point in points:
        score = point.get("score")
        if score is None or parse_timestamp(score["scored_at"]) > as_of:
            continue
        labels.append({"issue": attempts[point["attempt_id"]]["issue"],
            "lead_days": point["lead_days"], "target_at": point["target_at"],
            "target_snapshot_id": score["target_snapshot_id"],
            "target_captured_at": score["target_captured_at"],
            "target_available_total": score["target_available_total"],
            "measurement_key": point["measurement_key"]})
    visible = [point for point in points if parse_timestamp(point["issued_as_of_at"]) <= as_of]
    result = evaluate_points(visible, labels)
    mature = sum(parse_timestamp(point["target_at"]) <= as_of for point in visible)
    result.update({"checked_at": as_of.isoformat(), "evidence_kind": "local_post_freeze_prospective",
        "status": "PROSPECTIVE_COLLECTING", "source": "immutable_local_daily_path_ledger",
        "mature_prediction_count": mature, "pending_prediction_count": len(visible)-mature,
        "mature_unscored_count": mature-len(labels),
        "mature_label_coverage": len(labels)/mature if mature else None,
        "production_activation_allowed": False})
    return result


def attach_training_support(feed: dict) -> dict:
    path = Path(__file__).parent / "artifacts/daily_inventory_path_training_support_v1.json"
    if path.exists():
        support = json.loads(path.read_text())
        if support.get("version") != "daily-inventory-training-support-v1":
            raise ValueError("Unexpected training support metadata")
        feed["training_support"] = support
    return feed


def ledger_preview(ledger_path: str | Path) -> dict:
    """Render original immutable vintages; never regenerate old forecast inputs."""
    from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger

    events = []
    with DailyInventoryPathLedger(ledger_path) as ledger:
        attempts = ledger.export_attempts()
        scores = {(point["attempt_id"], point["target_at"]): point.get("score")
                  for point in ledger.export_points()}
    for attempt in attempts:
        issue, artifact = attempt["issue"], attempt["artifact"]
        ready = issue["status"] == "READY"
        events.append({
            "ticket_event_id": issue["ticket_event_id"], "club_slug": issue["club_slug"],
            "kickoff_at": issue["kickoff_at"], "issued_as_of_at": issue["issued_as_of_at"],
            "status": issue["status"], "input_status": issue["status"],
            "measurement_key": issue["measurement_key"] if ready else None,
            "observations": issue["observed_prefix"] if ready else [],
            "model_version": artifact["model_version"], "model_sha256": artifact["model_sha256"],
            "points": [{**point, "evidence_kind": "research_preview_not_prospective",
                        "score": scores.get((attempt["attempt_id"], point["target_at"]))}
                       for point in attempt["points"]],
            "origin_evidence_kind": attempt["evidence_kind"],
            "executed_at": attempt["executed_at"],
        })
    generated = _now()
    return attach_training_support({"version": PREVIEW_VERSION, "generated_at": generated.isoformat(),
            "evidence_kind": "research_preview_not_prospective",
            "production_change": False, "events": events,
            "evaluation": ledger_metrics(ledger_path, generated)})


def shadow(data: dict, model: dict, ledger_path: str | Path) -> dict:
    from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger

    executed = _now()  # Never accept a caller-supplied historical execution time.
    if parse_timestamp(data["exported_at"]) > executed:
        raise ValueError("Export cutoff is in the future")
    outcomes = []
    with DailyInventoryPathLedger(ledger_path) as ledger:
        for event in data["events"]:
            kickoff = parse_timestamp(event["kickoff_at"])
            days = math.ceil((kickoff - executed).total_seconds() / 86400)
            if not 1 <= days <= 60:
                continue
            issued = kickoff - timedelta(days=days)
            if executed - issued > timedelta(minutes=90):
                continue  # No backfill of a missed daily issue.
            issue = build_issue(event, issued)
            if parse_timestamp(model["fitted_at"]) > issued:
                outcomes.append({"ticket_event_id": event["ticket_event_id"], "status": "MODEL_NOT_FROZEN_AT_ISSUE"})
                continue
            if event["ticket_event_id"] in model["training_event_ids"]:
                outcomes.append({"ticket_event_id": event["ticket_event_id"], "status": "EVENT_IN_TRAINING"})
                continue
            points = predict_path(issue, model) if issue["status"] == "READY" else []
            outcomes.append({"ticket_event_id": event["ticket_event_id"], **ledger.record(issue, points, model, executed.isoformat())})
    return {"executed_at": executed.isoformat(), "evidence_kind": "local_post_freeze_prospective", "attempts": outcomes, "production_change": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export_parser = commands.add_parser("export", help="Read public snapshots; never write to DB")
    export_parser.add_argument("--output", required=True)
    export_parser.add_argument("--as-of")
    audit_parser = commands.add_parser("audit")
    audit_parser.add_argument("--input", required=True)
    audit_parser.add_argument("--output", required=True)
    fit_parser = commands.add_parser("fit")
    fit_parser.add_argument("--input", required=True)
    fit_parser.add_argument("--train-through", required=True)
    fit_parser.add_argument("--artifact", required=True)
    fit_parser.add_argument("--report", required=True)
    preview_parser = commands.add_parser("preview")
    preview_parser.add_argument("--input", required=True)
    preview_parser.add_argument("--artifact", required=True)
    preview_parser.add_argument("--output", required=True)
    shadow_parser = commands.add_parser("shadow")
    shadow_parser.add_argument("--input", required=True)
    shadow_parser.add_argument("--artifact", required=True)
    shadow_parser.add_argument("--ledger", required=True)
    score_parser = commands.add_parser("score")
    score_parser.add_argument("--input", required=True)
    score_parser.add_argument("--ledger", required=True)
    score_parser.add_argument("--output", required=True)
    ledger_parser = commands.add_parser("export-ledger", help="Export preserved vintages for panel preview")
    ledger_parser.add_argument("--ledger", required=True)
    ledger_parser.add_argument("--output", required=True)
    backup_parser = commands.add_parser("backup", help="Verified immutable copy in private Supabase Storage")
    backup_parser.add_argument("--ledger", required=True)
    backup_parser.add_argument("--artifact", required=True)
    backup_parser.add_argument("--output", required=True)
    restore_parser = commands.add_parser("restore", help="Restore verified private backup to a new file")
    restore_parser.add_argument("--manifest-key", required=True)
    restore_parser.add_argument("--ledger", required=True)
    metrics_parser = commands.add_parser("metrics", help="Paired event-balanced errors from genuine local scores")
    metrics_parser.add_argument("--ledger", required=True)
    metrics_parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "export":
            result = export_public(PublicInventoryReader(), args.as_of or _now())
            _dump(args.output, result, exclusive=True)
            print(json.dumps({"event_count": len(result["events"]), "snapshot_count": sum(len(e["observations"]) for e in result["events"]), "export_sha256": result["export_sha256"]}))
        elif args.command == "export-ledger":
            _dump(args.output, ledger_preview(args.ledger))
        elif args.command == "backup":
            from ml.demand_engine.daily_inventory_path_storage_v1 import backup_ledger
            result = backup_ledger(args.ledger, args.artifact)
            _dump(args.output, result)
            print(json.dumps({"bucket": result["bucket"], "private": result["private"],
                              "manifest_key": result["manifest_object"]["key"], "read_back_verified": True}))
        elif args.command == "restore":
            from ml.demand_engine.daily_inventory_path_storage_v1 import restore_ledger
            print(json.dumps(restore_ledger(args.manifest_key, args.ledger)))
        elif args.command == "metrics":
            _dump(args.output, ledger_metrics(args.ledger, _now()))
        else:
            data = load_export(args.input)
            if args.command == "audit":
                _dump(args.output, build_dataset(data["events"], data["exported_at"])["coverage"])
            elif args.command == "fit":
                result = fit_research(data, args.train_through, args.artifact)
                _dump(args.report, result)
                print(json.dumps(result["final_research_fit"]))
            elif args.command == "preview":
                result = preview(data, load_model(args.artifact), data["exported_at"])
                _dump(args.output, result)
                print(json.dumps({"event_status_counts": dict(Counter(e["status"] for e in result["events"])), "future_point_count": sum(len(e["points"]) for e in result["events"])}))
            elif args.command == "shadow":
                print(json.dumps(shadow(data, load_model(args.artifact), args.ledger)))
            elif args.command == "score":
                from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger
                with DailyInventoryPathLedger(args.ledger) as ledger:
                    _dump(args.output, ledger.score(data["events"], data["exported_at"]))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Daily inventory path failed closed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
