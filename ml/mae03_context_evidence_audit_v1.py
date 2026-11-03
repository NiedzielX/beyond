"""Audit existing stored context vintages without fitting or opening label values."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.run_daily_inventory_path_v1 import PublicInventoryReader

VERSION = "mae03-context-evidence-audit-v1"
CHECKPOINT_HOURS = {"T-7d": 168, "T-3d": 72, "T-24h": 24, "T-6h": 6}
MIN_EVENTS, MIN_CLUBS, MIN_DISTINCT = 8, 5, 2


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def screening_status(events: int, clubs: int, distinct: int, grouped_variance: bool = True) -> str:
    if events < MIN_EVENTS:
        return "INSUFFICIENT_EVENTS"
    if clubs < MIN_CLUBS:
        return "INSUFFICIENT_CLUBS"
    if distinct < MIN_DISTINCT:
        return "NO_VARIANCE"
    if not grouped_variance:
        return "INSUFFICIENT_GROUPED_VARIATION"
    return "CANDIDATE_FOR_PRECOMMIT_ONLY"


def baseline_status(row: dict, cutoff: datetime) -> str:
    if row.get("baseline_historical_p50") is None:
        return "BASELINE_MISSING"
    if (not finite_number(row["baseline_historical_p50"]) or row["baseline_historical_p50"] < 0
            or not row.get("baseline_forecast_id") or not row.get("baseline_model_version")
            or not row.get("baseline_historical_model")):
        return "BASELINE_LINEAGE_INVALID"
    try:
        if parse_timestamp(row["baseline_forecast_generated_at"]) > cutoff:
            return "BASELINE_AFTER_CUTOFF"
    except (KeyError, ValueError, TypeError):
        return "BASELINE_LINEAGE_INVALID"
    return "BASELINE_TIME_VALID"


def feature_status(feature: dict, cutoff: datetime) -> str:
    status = feature.get("status")
    if status != "observed":
        return status if status in {"unknown", "blocked_external_access", "degraded_automation"} else "INVALID_STATUS"
    try:
        observed = parse_timestamp(feature["observed_at"])
        source_observed = parse_timestamp(feature.get("source_observed_at") or feature["observed_at"])
    except (KeyError, TypeError, ValueError):
        return "INVALID_OBSERVATION_TIME"
    if max(observed, source_observed) > cutoff:
        return "OBSERVATION_AFTER_CUTOFF"
    if not feature.get("source_name") or not feature.get("source_record_key"):
        return "MISSING_SOURCE_LINEAGE"
    value = feature.get("numeric_value")
    if value is None:
        return "OBSERVED_NONNUMERIC"
    if not finite_number(value):
        return "INVALID_NUMERIC_VALUE"
    return "OBSERVED_NUMERIC_CAPTURE_TIME_VALID"


def audit(snapshots: list[dict], outcomes: list[dict], checked_at: str) -> dict:
    checked = parse_timestamp(checked_at)
    identities = [(row["ticket_event_id"], row["checkpoint_code"]) for row in snapshots]
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate event/checkpoint snapshot")
    outcome_ids = [row["ticket_event_id"] for row in outcomes]
    if len(set(outcome_ids)) != len(outcome_ids):
        raise ValueError("Duplicate confirmed outcome identity")
    confirmed = {}
    for row in outcomes:
        try:
            when = parse_timestamp(row["confirmed_at"])
            if when <= checked:
                confirmed[row["ticket_event_id"]] = when
        except (KeyError, TypeError, ValueError):
            continue
    capture_counts, baseline_counts, feature_counts = Counter(), Counter(), Counter()
    groups = defaultdict(list)
    prospective_events, paired_events = set(), set()
    for row in snapshots:
        if row.get("capture_mode") != "prospective":
            capture_counts["RETROSPECTIVE_EXCLUDED"] += 1
            continue
        try:
            cutoff = parse_timestamp(row["checkpoint_at"])
            captured, created = parse_timestamp(row["captured_at"]), parse_timestamp(row["created_at"])
            meta = row["metadata"]
            kickoff = parse_timestamp(meta["kickoff_at"])
            if not meta.get("club_slug"):
                raise ValueError("Missing frozen club identity")
            if row["checkpoint_code"] not in CHECKPOINT_HOURS or cutoff != kickoff-timedelta(hours=CHECKPOINT_HOURS[row["checkpoint_code"]]):
                capture_counts["INCORRECT_CHECKPOINT_COORDINATE"] += 1
                continue
            if not (cutoff <= captured <= cutoff+timedelta(minutes=30)
                    and cutoff <= created <= cutoff+timedelta(minutes=30)
                    and max(captured, created) <= checked):
                capture_counts["OUTSIDE_PROSPECTIVE_CAPTURE_WINDOW"] += 1
                continue
        except (KeyError, TypeError, ValueError):
            capture_counts["INVALID_SNAPSHOT_IDENTITY_OR_TIME"] += 1
            continue
        capture_counts["PROSPECTIVE_CAPTURE_VALID"] += 1
        prospective_events.add(row["ticket_event_id"])
        base = baseline_status(row, cutoff)
        baseline_counts[base] += 1
        # The sync job's three-hour waiting period is not the definition of a
        # genuine manually confirmed outcome. Do not exclude valid earlier FT confirmations.
        labeled = (row["ticket_event_id"] in confirmed
                   and kickoff < confirmed[row["ticket_event_id"]])
        if base == "BASELINE_TIME_VALID" and labeled:
            paired_events.add(row["ticket_event_id"])
        for key, feature in row.get("context_features", {}).items():
            if not isinstance(feature, dict):
                feature_counts["INVALID_PAYLOAD"] += 1
                continue
            state = feature_status(feature, cutoff)
            feature_counts[state] += 1
            if state != "OBSERVED_NUMERIC_CAPTURE_TIME_VALID" or base != "BASELINE_TIME_VALID":
                continue
            group_key = (key, feature["source_name"], row["checkpoint_code"],
                         row["baseline_model_version"], row["baseline_historical_model"])
            groups[group_key].append({"event": row["ticket_event_id"], "club": meta["club_slug"],
                                      "value": float(feature["numeric_value"]), "labeled": labeled})
    tables = []
    for key, rows in sorted(groups.items()):
        paired = [row for row in rows if row["labeled"]]
        events, clubs = {r["event"] for r in paired}, {r["club"] for r in paired}
        values = {r["value"] for r in paired}
        loeo_variation = min((len({r["value"] for r in paired if r["event"] != event})
                             for event in events), default=0)
        loco_variation = min((len({r["value"] for r in paired if r["club"] != club})
                             for club in clubs), default=0)
        tables.append({"feature_key": key[0], "source_name": key[1], "checkpoint_code": key[2],
                       "baseline_model_version": key[3], "baseline_historical_model": key[4],
                       "available_event_count": len({r["event"] for r in rows}),
                       "paired_event_count": len(events), "paired_club_count": len(clubs),
                       "paired_distinct_values": len(values),
                       "paired_zero_count": sum(r["value"] == 0 for r in paired),
                       "paired_nonzero_count": sum(r["value"] != 0 for r in paired),
                       "paired_value_min": min(values) if values else None,
                       "paired_value_max": max(values) if values else None,
                       "loeo_min_training_distinct_values": loeo_variation,
                       "loco_min_training_distinct_values": loco_variation,
                       "screening_status": screening_status(len(events), len(clubs), len(values),
                                                             min(loeo_variation, loco_variation) >= MIN_DISTINCT),
                       "independent_original_ingestion_time_proven": False,
                       "model_fit_authorized": False})
    return {"version": VERSION, "checked_at": checked.isoformat(), "target_values_opened": False,
            "source_snapshot_count": len(snapshots), "capture_counts": dict(capture_counts),
            "baseline_counts": dict(baseline_counts), "feature_status_counts": dict(feature_counts),
            "distinct_prospective_events": len(prospective_events), "distinct_paired_events_any_checkpoint": len(paired_events),
            "screening_thresholds_not_model_promotion": {"events": MIN_EVENTS, "clubs": MIN_CLUBS, "distinct_values": MIN_DISTINCT},
            "feature_source_checkpoint_groups": tables,
            "limitations": ["Snapshot payload lacks original observation ID/created_at; only capture/source times independently inspected",
                            "Existing capture SQL filters observed_at, created_at and source_observed_at by cutoff; source review is not per-row ingestion proof",
                            "Snapshot insert-only application behavior is not independently proven DB immutability",
                            "Source names and baseline models remain separate; source version/unit compatibility needs review",
                            "Counts/variance screening is not permission to fit, select or promote a model",
                            "No post-hoc checkpoint selection: sparse variation must persist in every event/club training fold",
                            "Previously rejected mechanisms remain closed; no inference from missing values as zero"],
            "production_change": False, "live_adjustment": 0, "model_fit_performed": False}


def export_and_audit(output: Path) -> dict:
    if output.exists():
        raise ValueError("Refusing to overwrite an existing export")
    checked = datetime.now(timezone.utc).isoformat()
    reader = PublicInventoryReader()
    fields = ("id,ticket_event_id,checkpoint_code,checkpoint_at,captured_at,capture_mode,created_at,metadata,"
              "baseline_forecast_id,baseline_forecast_generated_at,baseline_model_version,"
              "baseline_historical_model,baseline_historical_p50,context_features")
    snapshots = reader.rows("event_context_snapshots_v1", [("select", fields), ("created_at", "lte."+checked)])
    # Outcome values are deliberately excluded. Count header prevents silent truncation.
    parameters = urllib.parse.urlencode({"select": "ticket_event_id,confirmed_at", "confirmed_at": "lte."+checked,
                                        "order": "ticket_event_id.asc", "limit": "1000"})
    request = urllib.request.Request(reader.base+"/rest/v1/ticket_event_outcomes?"+parameters,
                                     headers={**reader.headers, "Prefer": "count=exact"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            outcomes = json.load(response)
            total = response.headers.get("Content-Range", "").rsplit("/", 1)[-1]
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Read-only outcome metadata export returned HTTP{exc.code}") from None
    if not total.isdigit() or int(total) != len(outcomes):
        raise ValueError("Outcome metadata export incomplete")
    report = audit(snapshots, outcomes, checked)
    output.mkdir(parents=True)
    for name, data in (("context-snapshots.json", snapshots), ("outcome-presence.json", outcomes)):
        (output/name).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+"\n")
    report["provenance"] = {"code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                            "snapshots_sha256": hashlib.sha256((output/"context-snapshots.json").read_bytes()).hexdigest(),
                            "outcome_presence_sha256": hashlib.sha256((output/"outcome-presence.json").read_bytes()).hexdigest()}
    (output/"report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Private runtime directory, not a Git raw-data artifact")
    args = parser.parse_args()
    report = export_and_audit(args.output)
    print(json.dumps({"version": VERSION, "source_snapshot_count": report["source_snapshot_count"],
                      "capture_counts": report["capture_counts"],
                      "distinct_paired_events_any_checkpoint": report["distinct_paired_events_any_checkpoint"],
                      "model_fit_performed": False}, indent=2))


if __name__ == "__main__":
    main()
