"""Versioned source-state feature row; never fit or alter a frozen forecast."""
from __future__ import annotations

import argparse
from datetime import timedelta
import json
import math
from pathlib import Path

from ml.demand_engine.daily_inventory_path_dataset_v1 import canonical_hash, parse_timestamp

VERSION = "daily-inventory-source-state-features-v2"
SOURCE_VERSION = "daily-inventory-source-state-as-known-v2"
KNOWN_STATES = {"VISIBLE_ACTIVE", "VISIBLE_LEGACY_STAGE_UNKNOWN", "HIDDEN_SOURCE", "INACTIVE_STAGE",
                "INVALID_SOURCE_METADATA", "VISIBLE_COUNT_MISSING"}


def count(value, name: str, *, nullable=False):
    if value is None and nullable:
        return None
    if (isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value)
            or value < 0 or not float(value).is_integer()):
        raise ValueError(f"Invalid {name}")
    return float(value)


def build_features(payload: dict) -> dict:
    if (payload.get("version") != SOURCE_VERSION or payload.get("production_change") is not False
            or payload.get("live_adjustment") != 0 or payload.get("target_values_used") is not False):
        raise ValueError("Unexpected source-state contract")
    event = payload.get("ticket_event_id")
    if not isinstance(event,int) or isinstance(event,bool) or event <= 0:
        raise ValueError("Invalid event identity")
    cutoff = parse_timestamp(payload["as_of_at"])
    observations = payload.get("observations")
    if not isinstance(observations,list):
        raise ValueError("Source-state observation array required")
    status = payload.get("status")
    if status not in {"SOURCE_STATE_EXPORT","EVENT_NOT_FOUND","EVENT_NOT_KNOWN_AS_OF","UNSUPPORTED_PROVIDER"}:
        raise ValueError("Unknown source-state status")
    if status != "SOURCE_STATE_EXPORT" and observations:
        raise ValueError("Unavailable event/source cannot carry model observations")
    clean, seen = [], set()
    for row in observations:
        identifier = row.get("raw_observation_id")
        if not isinstance(identifier,int) or isinstance(identifier,bool) or identifier <= 0 or identifier in seen:
            raise ValueError("Invalid or duplicate raw observation identity")
        seen.add(identifier)
        captured, received, known = [parse_timestamp(row[key]) for key in ("captured_at","raw_created_at","known_at")]
        if known != max(captured,received) or known > cutoff:
            raise ValueError("Future or inconsistent source receipt time")
        if not isinstance(row.get("source_version"),str) or not row["source_version"].strip():
            raise ValueError("Source parser version required")
        active, visible = row.get("source_active"), row.get("source_visible")
        if (active is not None and not isinstance(active,bool)) or not isinstance(visible,bool):
            raise ValueError("Boolean source-state flags required; unknown active stage stays null")
        state = row.get("status")
        if state not in KNOWN_STATES:
            raise ValueError("Invalid observation state")
        raw_value = count(row.get("raw_available_total"),"raw source count",nullable=True)
        value = count(row.get("available_total"),"model-usable count",nullable=True)
        blocked = state == "INVALID_SOURCE_METADATA" or active is False or visible is False
        if blocked and value is not None:
            raise ValueError("Hidden, inactive or malformed source must not become a usable count")
        if not blocked and value != raw_value:
            raise ValueError("Usable count differs from the genuine source value")
        if ((state == "VISIBLE_ACTIVE" and active is not True)
                or (state == "VISIBLE_LEGACY_STAGE_UNKNOWN" and active is not None)
                or (state == "HIDDEN_SOURCE" and visible is not False)
                or (state == "INACTIVE_STAGE" and active is not False)):
            raise ValueError("Source-state label/flag mismatch")
        if ((state in {"VISIBLE_ACTIVE","VISIBLE_LEGACY_STAGE_UNKNOWN"} and (not visible or raw_value is None))
                or (state == "VISIBLE_COUNT_MISSING" and raw_value is not None)):
            raise ValueError("Source-state label/count mismatch")
        snapshot, promotion = row.get("public_snapshot_id"), row.get("promotion_known_at")
        if snapshot is None:
            if promotion is not None:
                raise ValueError("Promotion time without an as-known snapshot link")
        elif (not isinstance(snapshot,int) or isinstance(snapshot,bool) or snapshot <= 0
                or promotion is None or parse_timestamp(promotion) > cutoff):
            raise ValueError("Invalid or future promotion link")
        clean.append({**row,"captured":captured,"known":known,"value":value})
    clean.sort(key=lambda row:(row["captured"],row["raw_observation_id"]))
    hourly = {}
    for row in clean:
        hourly[row["captured"].replace(minute=0,second=0,microsecond=0)] = row
    recent = [row for row in hourly.values() if row["captured"] >= cutoff-timedelta(hours=48)]
    valid = [row for row in recent if row["status"] != "INVALID_SOURCE_METADATA"]
    active_known = [row for row in valid if row["source_active"] is not None]
    latest = clean[-1] if clean else None
    latest_valid = latest is not None and latest["status"] != "INVALID_SOURCE_METADATA"
    features = {
        "latest_usable_available_total": latest["value"] if latest_valid else None,
        "last_source_active": latest["source_active"] if latest_valid else None,
        "last_source_visible": latest["source_visible"] if latest_valid else None,
        "latest_source_age_hours": (cutoff-latest["captured"]).total_seconds()/3600 if latest else None,
        "active_stage_known_fraction_48h": len(active_known)/len(recent) if recent else None,
        "active_fraction_given_known_48h": sum(row["source_active"] for row in active_known)/len(active_known) if active_known else None,
        "visible_fraction_48h": sum(row["source_visible"] for row in valid)/len(valid) if valid else None,
    }
    return {"version":VERSION,"ticket_event_id":event,"as_of_at":cutoff.isoformat(),
            "source_status":status,"features":features,"missing":{key:value is None for key,value in features.items()},
            "provenance":{"source_response_sha256":canonical_hash(payload),
                          "raw_observation_ids":[row["raw_observation_id"] for row in clean],
                          "source_versions":sorted({row["source_version"] for row in clean}),
                          "observation_count":len(clean),"recent_48h_observation_count":len(recent),
                          "sampling":"latest captured_at/id per UTC hour; genuine rows only",
                          "raw_immutability_independently_proven":False,"historical_event_revisions_independently_proven":False},
            "model_fit_performed":False,"production_change":False,"live_adjustment":0,"target_values_used":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=build_features(json.loads(args.input.read_text()))
    with args.output.open('x') as output:
        json.dump(result,output,indent=2,sort_keys=True,allow_nan=False);output.write('\n')
    print(json.dumps({'version':VERSION,'source_status':result['source_status'],
                      'observation_count':result['provenance']['observation_count'],'model_fit_performed':False}))


if __name__=='__main__':main()
