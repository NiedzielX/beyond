"""Historical capture-segment training data, explicitly NOT historical PIT proof.

Historical capture origins are feature coordinates, never previously issued
forecasts. Their knowledge clocks and exact metadata versions are unproven.
This module deliberately never calls the live issue builder or invents known_at.
Only subsequent genuinely issued forecasts can evaluate a fitted challenger.

The original source retains every observation and incompatible source segment.
Numeric prefixes use the last contiguous exact measurement-key segment at each
origin. Candidate/backfill/VAO keys are never aliased into a supported family.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path

from ml.demand_engine.rolling72_features_v1 import HORIZONS, _count, _hash, _id, _time
from ml.rolling72_receipt_dataset_v1 import _registry


VERSION = "rolling72-offline-capture-segment-dataset-v2"
PRECOMMIT_SHA256 = "c48c3c9d8128a518bb6ae2b3f2d459537f3b032adc84b2749f753daaaf8b4371"
ROOT = Path(__file__).resolve().parents[1]
PRECOMMIT_PATH = ROOT / "ml/artifacts/rolling72_v2/precommit.json"


def load_precommit(*, synthetic_test=False, precommit=None):
    if not isinstance(synthetic_test, bool):
        raise ValueError("synthetic_test must be an explicit boolean")
    if precommit is not None and not synthetic_test:
        raise ValueError("Custom precommit is permitted only for nonservable synthetic tests")
    result = json.loads(PRECOMMIT_PATH.read_text()) if precommit is None else precommit
    if (not isinstance(result, dict)
            or result.get("version") != "rolling72-offline-fit-prospective-shadow-precommit-v2"
            or result.get("precommit_sha256") != _hash({k: v for k, v in result.items() if k != "precommit_sha256"})):
        raise ValueError("Verified v2 precommit required")
    if not synthetic_test and result["precommit_sha256"] != PRECOMMIT_SHA256:
        raise ValueError("Pinned real v2 precommit changed")
    evidence = result.get("data_evidence", {})
    if (evidence.get("historical_knowledge_unproven") is not True
            or evidence.get("historical_input_known_at", "missing") is not None
            or evidence.get("historical_validation_accuracy_claim_allowed") is not False
            or evidence.get("candidate_or_VAO_aliases") is not False
            or evidence.get("ongoing_or_unconfirmed_in_fit") is not False
            or result.get("production_change") is not False or result.get("live_adjustment") != 0):
        raise ValueError("Offline-unproven training and production-off boundaries required")
    return result


def _digest(raw):
    if not isinstance(raw, bytes):
        raise ValueError("Original source bytes required")
    return hashlib.sha256(raw).hexdigest()


def _key(row):
    value = row.get("measurement_key")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _usable(row):
    try:
        _count(row.get("available_total"))
    except ValueError:
        return False
    return (_key(row) is not None
            and all(row.get(flag) is None or isinstance(row[flag], bool)
                    for flag in ("source_active", "source_visible"))
            and row.get("source_active") is not False and row.get("source_visible") is not False)


def _normalized(row):
    """Capture/value provenance only; there is intentionally no knowledge field."""
    return {"snapshot_id": _id(row["snapshot_id"]), "captured_at": _time(row["captured_at"]).isoformat(),
            "available_total": _count(row["available_total"]), "measurement_key": _key(row),
            "source_active": row.get("source_active"), "source_visible": row.get("source_visible")}


def capture_features(prefix, origin, kickoff, horizon):
    """The same twelve numeric definitions as live v1, without false clocks.

    Visible rows are already checked before exact-time compression. Retain the
    greatest genuine ID at the same capture time, matching the live encoder.
    Six/24/72-hour anchors use actual elapsed time and at most six-hour lag.
    """
    if horizon not in HORIZONS or isinstance(horizon, bool):
        raise ValueError("Only declared rolling horizons are supported")
    origin, kickoff = _time(origin), _time(kickoff)
    if not prefix or origin >= kickoff:
        raise ValueError("A genuine pre-kickoff prefix is required")
    clean = sorted((_normalized(row) for row in prefix), key=lambda row: (_time(row["captured_at"]), row["snapshot_id"]))
    if any(not _usable(row) or _time(row["captured_at"]) > origin for row in prefix):
        raise ValueError("Future, invalid or hidden capture in offline prefix")
    if len({_key(row) for row in clean}) != 1:
        raise ValueError("Offline prefix cannot join incompatible measurements")
    by_time = {}
    for row in clean:
        by_time[row["captured_at"]] = row
    clean = list(by_time.values())
    first, last = clean[0], clean[-1]
    latest = _time(last["captured_at"])
    if latest != origin:
        raise ValueError("Offline origins must be actual capture coordinates")
    result = {"last_available_total": last["available_total"],
              "observed_delta_since_first": last["available_total"] - first["available_total"],
              "prefix_span_hours": (latest - _time(first["captured_at"])).total_seconds() / 3600,
              "latest_staleness_hours": 0.0,
              "hours_to_kickoff": (kickoff - origin).total_seconds() / 3600,
              "horizon_hours": horizon}
    for hours in (6, 24, 72):
        boundary = latest - timedelta(hours=hours)
        anchors = [row for row in clean if _time(row["captured_at"]) <= boundary]
        anchor = anchors[-1] if anchors else None
        if anchor is not None and boundary - _time(anchor["captured_at"]) > timedelta(hours=6):
            anchor = None
        delta = slope = None
        if anchor is not None:
            elapsed = (latest - _time(anchor["captured_at"])).total_seconds() / 3600
            delta = last["available_total"] - anchor["available_total"]
            slope = delta / elapsed
        result[f"delta_{hours}h"], result[f"slope_{hours}h"] = delta, slope
    return result, clean


def _confirmations(outcomes, archive, cutoff, bindings):
    if not isinstance(outcomes, list) or not isinstance(archive, dict):
        raise ValueError("Original confirmation list/archive required")
    bound = _time(bindings["outcomes"]["knowledge_bound_at"])
    archive_bound = _time(archive["completed_at"])
    if (bound > cutoff or archive_bound > cutoff
            or archive_bound != _time(bindings["outcome_archive"]["knowledge_bound_at"])):
        raise ValueError("Confirmation source was received after training cutoff")
    archived = archive.get("parts", {}).get("outcomes")
    if not isinstance(archived, list):
        raise ValueError("Original archived confirmation rows required")
    result = defaultdict(list)
    for rows, receipt_bound in ((outcomes, bound), (archived, archive_bound)):
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Confirmation must be an object")
            # Never read attendance values or any feature-like outcome columns.
            confirmed = _time(row["confirmed_at"])
            clocks = [_time(row[key]) for key in ("confirmed_at", "created_at", "updated_at") if row.get(key)]
            if max(clocks) <= min(cutoff, receipt_bound):
                result[_id(row["ticket_event_id"])].append(confirmed)
    return result


def _maturity(days):
    for lower, label in ((50, "P50plus"), (30, "P30_to_P50"), (15, "P15_to_P30"),
                         (7, "P7_to_P15"), (3, "P3_to_P7"), (0, "P0_to_P3")):
        if days >= lower:
            return label
    raise ValueError("Only pre-kickoff origins have a maturity")


def build_dataset(source_bytes, registry_bytes, outcomes_bytes, archive_bytes, *, synthetic_test=False, precommit=None):
    """Bind original bytes; return flat training rows and explicit source limits."""
    protocol = load_precommit(synthetic_test=synthetic_test, precommit=precommit)
    supplied = {"inventory": source_bytes, "identity_registry": registry_bytes,
                "outcomes": outcomes_bytes, "outcome_archive": archive_bytes}
    bindings = protocol["source_bindings"]
    for name, raw in supplied.items():
        if _digest(raw) != bindings[name]["file_sha256"]:
            raise ValueError(f"Pinned {name} source byte hash mismatch")
    source, registry, outcomes, archive = [json.loads(supplied[key]) for key in supplied]
    if source.get("version") != "daily-inventory-public-export-v1" or not isinstance(source.get("events"), list):
        raise ValueError("Original inventory export required")
    manifest = _hash({k: v for k, v in source.items() if k != "export_sha256"})
    if source.get("export_sha256") != manifest or manifest != bindings["inventory"]["manifest_sha256"]:
        raise ValueError("Inventory export manifest mismatch")
    exported, received, cutoff = (_time(source["exported_at"]), _time(source["retrieved_at"]),
                                  _time(protocol["training_data_cutoff_at"]))
    if not exported <= received <= cutoff or received != _time(bindings["inventory"]["received_at"]):
        raise ValueError("Inventory receipt is incompatible with training cutoff")
    groups_by_id, fixture_groups, identities = _registry(registry_bytes)
    confirmations = _confirmations(outcomes, archive, cutoff, bindings)
    allowed = set(protocol["data_evidence"]["source_families"])
    raw_counts, event_status, input_status, coordinate_status = Counter(), Counter(), Counter(), Counter()
    owners, revisions, event_ids, eligible = {}, set(), set(), []
    for event in source["events"]:
        event_id = _id(event.get("ticket_event_id"))
        if event_id in event_ids:
            raise ValueError("Duplicate event in original inventory source")
        event_ids.add(event_id)
        rows = event.get("observations")
        if not isinstance(rows, list):
            raise ValueError("Observations must be a list")
        group = groups_by_id.get(event_id, "unresolved:" + str(event_id))
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Observation must be an object")
            captured, identifier = _time(row["captured_at"]), _id(row.get("snapshot_id"))
            if captured > exported:
                raise ValueError("Snapshot exceeds original export cutoff")
            raw_counts["snapshot_rows"] += 1
            raw_counts["unusable_rows"] += not _usable(row)
            raw_counts["literal_zero_rows"] += _usable(row) and row["available_total"] == 0
            value = row.get("available_total")
            try:
                value = _count(value)
            except ValueError:
                pass
            fingerprint = _hash({"owner": event_id, "capture": captured.isoformat(), "value": value,
                                 "key": _key(row), **{key: row.get(key) for key in
                                                    ("source_active", "source_visible", "source", "sector_count")}})
            previous = owners.get(identifier)
            if previous == (group, fingerprint):
                raise ValueError("Duplicate snapshot identity in original source")
            if previous is not None and previous != (group, fingerprint):
                revisions.update((group, previous[0]))
            owners[identifier] = group, fingerprint
        if event_id not in groups_by_id:
            event_status["UNKNOWN_SOURCE_IDENTITY"] += 1
            continue
        if not any(key[0] == event.get("provider") and key[2] == event.get("club_slug")
                   for key in identities[event_id]):
            event_status["REGISTRY_SOURCE_IDENTITY_MISMATCH"] += 1
            continue
        kickoff = _time(event["kickoff_at"])
        if kickoff >= cutoff:
            event_status["ONGOING_FIXTURE"] += 1
            continue
        if not any(kickoff <= at <= cutoff for at in confirmations[event_id]):
            event_status["UNCONFIRMED_COMPLETED_FIXTURE"] += 1
            continue
        eligible.append(event)
    selected = {}
    alias_metadata = defaultdict(set)
    for event in eligible:
        alias_metadata[groups_by_id[event["ticket_event_id"]]].add((event["club_slug"], _time(event["kickoff_at"])))
    for event in sorted(eligible, key=lambda row: row["ticket_event_id"]):
        event_id, kickoff = event["ticket_event_id"], _time(event["kickoff_at"])
        group = groups_by_id[event_id]
        if group in revisions:
            event_status["SOURCE_SNAPSHOT_CONFLICT"] += 1
        elif len(alias_metadata[group]) != 1:
            event_status["ALIAS_METADATA_CONFLICT"] += 1
        elif not any(_time(row["captured_at"]) < kickoff for row in event["observations"]):
            event_status["NO_PRE_KICKOFF_DATA"] += 1
        elif group in selected:
            event_status["ALIAS_EVENT_EXCLUDED"] += 1
        else:
            selected[group] = event
            event_status["SELECTED_CONFIRMED_FIXTURE"] += 1
    rows, catalogue, by_maturity = [], [], defaultdict(lambda: {"rows": 0, "groups": set(), "clubs": set()})
    complete_target_source_flags = 0
    for group, event in selected.items():
        kickoff = _time(event["kickoff_at"])
        observations = sorted((row for row in event["observations"] if _time(row["captured_at"]) < kickoff),
                              key=lambda row: (_time(row["captured_at"]), row["snapshot_id"]))
        times = [_time(row["captured_at"]) for row in observations]
        segments, segment_ids = [], []
        for index, raw in enumerate(observations):
            if not segments or _key(raw) != segments[-1]["key"]:
                segments.append({"start": index, "key": _key(raw)})
            segment_ids.append(len(segments) - 1)
        for number, segment in enumerate(segments):
            segment["end"] = segments[number + 1]["start"] - 1 if number + 1 < len(segments) else len(observations) - 1
            first, last = segment["start"], segment["end"]
            catalogue.append({"ticket_event_id": event["ticket_event_id"], "fixture_group": group,
                              "segment_id": number, "measurement_key": segment["key"],
                              "supported_family": segment["key"] in allowed,
                              "start_at": times[first].isoformat(), "last_capture_at": times[last].isoformat(),
                              "row_count": last - first + 1,
                              "raw_snapshot_ids": [r["snapshot_id"] for r in observations[first:last + 1]]})
        origins = {segment["start"] for segment in segments}
        seen_days = set()
        for index, captured in enumerate(times):
            if captured.date() not in seen_days:
                origins.add(index)
                seen_days.add(captured.date())
        # Resolve same-key/same-capture ties to the latest original ID, as live v1 does.
        resolved = set()
        for index in origins:
            while (index + 1 < len(observations) and times[index + 1] == times[index]
                   and segment_ids[index + 1] == segment_ids[index]):
                index += 1
            resolved.add(index)
        for index in sorted(resolved):
            origin, segment_id = times[index], segment_ids[index]
            start = segments[segment_id]["start"]
            prefix = observations[start:index + 1]
            family = _key(observations[index])
            if family not in allowed:
                input_status["UNSUPPORTED_SEGMENT_FAMILY"] += 1
                continue
            if any(not _usable(raw) for raw in prefix):
                input_status["INVALID_OR_HIDDEN_PREFIX"] += 1
                continue
            input_status["ELIGIBLE_OFFLINE_CAPTURE_ORIGIN"] += 1
            for horizon in HORIZONS:
                target = origin + timedelta(hours=horizon)
                status = None
                if target >= kickoff:
                    status = "TARGET_NOT_BEFORE_KICKOFF"
                elif target > exported:
                    status = "TARGET_NOT_COVERED_BY_RECEIVED_SOURCE"
                else:
                    label_index = bisect_right(times, target) - 1
                    if label_index < 0 or times[label_index] <= origin:
                        status = "NO_STRICT_FUTURE_OBSERVATION"
                    elif segment_ids[label_index] != segment_id:
                        status = "SOURCE_SCOPE_TRANSITION_BEFORE_TARGET"
                    elif target - times[label_index] > timedelta(hours=6):
                        status = "STALE_TARGET_OBSERVATION"
                    elif not _usable(observations[label_index]):
                        status = "INVALID_OR_HIDDEN_LATEST_TARGET"
                    elif any(not _usable(raw) for raw in observations[index + 1:label_index + 1]):
                        status = "INVALID_OR_HIDDEN_FUTURE_INTERVAL"
                    else:
                        feature_values, clean_prefix = capture_features(prefix, origin, kickoff, horizon)
                        last = feature_values["last_available_total"]
                        label_value = _count(observations[label_index]["available_total"])
                        row = {"features": feature_values, "nominal_horizon_hours": horizon,
                               "target_delta": label_value - last, "matched_available_total": label_value,
                               "last_available_total": last, "origin_capture_at": origin.isoformat(),
                               "target_at": target.isoformat(), "label_captured_at": times[label_index].isoformat(),
                               "kickoff_at": kickoff.isoformat(), "ticket_event_id": event["ticket_event_id"],
                               "fixture_group": group, "club_slug": event["club_slug"], "source_family": family,
                               "historical_input_known_at": None, "historical_knowledge_unproven": True,
                               "source_received_at": received.isoformat(),
                               "segment_lineage": {"segment_id": segment_id, "measurement_key": family,
                                   "start_snapshot_id": observations[start]["snapshot_id"],
                                   "origin_snapshot_id": observations[index]["snapshot_id"],
                                   "label_snapshot_id": observations[label_index]["snapshot_id"],
                                   "raw_prefix_snapshot_ids": [r["snapshot_id"] for r in prefix],
                                   "prior_incompatible_rows_retained": start,
                                   "first_event_point": start == 0 and origin == times[0]},
                               "prefix_sha256": _hash(clean_prefix)}
                        row["row_sha256"] = _hash(row)
                        rows.append(row)
                        complete_target_source_flags += all(isinstance(observations[label_index].get(flag), bool)
                                                            for flag in ("source_active", "source_visible"))
                        status = "MATCHED_OFFLINE_TRAINING_ROW"
                        cell = by_maturity[(_maturity((kickoff - origin).total_seconds() / 86400), horizon)]
                        cell["rows"] += 1
                        cell["groups"].add(group)
                        cell["clubs"].add(event["club_slug"])
                coordinate_status[status] += 1
    rows.sort(key=lambda row: (row["fixture_group"], row["origin_capture_at"], row["nominal_horizon_hours"]))
    support = {}
    for horizon in HORIZONS:
        subset = [row for row in rows if row["nominal_horizon_hours"] == horizon]
        support[str(horizon)] = {"rows": len(subset), "fixtures": len({r["fixture_group"] for r in subset}),
                                 "clubs": len({r["club_slug"] for r in subset})}
    common = set.intersection(*({r["fixture_group"] for r in rows if r["nominal_horizon_hours"] == h} for h in HORIZONS))
    common_rows = [row for row in rows if row["fixture_group"] in common]
    result = {"version": VERSION, "precommit_sha256": protocol["precommit_sha256"],
              "training_data_cutoff_at": cutoff.isoformat(), "rows": rows,
              "segment_catalogue": catalogue, "fixture_groups": fixture_groups,
              "source_bindings": {key: {**bindings[key], "verified_file_sha256": _digest(raw)} for key, raw in supplied.items()},
              "coverage": {"raw_source_counts": dict(raw_counts), "event_status_counts": dict(event_status),
                  "input_status_counts": dict(input_status), "coordinate_status_counts": dict(coordinate_status),
                  "per_horizon": support, "common_fixture_count": len(common),
                  "common_club_count": len({r["club_slug"] for r in common_rows}), "common_row_count": len(common_rows),
                  "matched_row_count": len(rows), "matched_zero_labels": sum(r["matched_available_total"] == 0 for r in rows),
                  "first_segment_point_rows": sum(r["features"]["prefix_span_hours"] == 0 for r in rows),
                  "first_event_point_rows": sum(r["segment_lineage"]["first_event_point"] for r in rows),
                  "maximum_labeled_days_to_kickoff": max((( _time(r["kickoff_at"]) - _time(r["origin_capture_at"])).total_seconds() / 86400 for r in rows), default=None),
                  "maturity_horizon_support": {f"{maturity}/+{h}h": {"rows": cell["rows"], "fixtures": len(cell["groups"]), "clubs": len(cell["clubs"])}
                                                 for (maturity, h), cell in sorted(by_maturity.items())},
                  "snapshot_conflict_groups": sorted(revisions),
                  "matched_targets_with_complete_source_flags": complete_target_source_flags,
                  "offline_capture_alignment_implies_nominal_staleness_zero": True,
                  "historical_delivery_staleness_observed": False},
              "synthetic_test": synthetic_test, "servable_training_input": not synthetic_test,
              "historical_knowledge_unproven": True, "historical_input_known_at": None,
              "historical_metadata_versions_proven": False, "attendance_values_used": False,
              "historical_accuracy_computed": False, "model_fit_performed": False,
              "prospective_forecasts_created": 0, "production_change": False, "live_adjustment": 0,
              "limitations": ["Capture-aligned origins are offline training coordinates, not issued forecasts or historical PIT inputs.",
                  "Actual historical delivery latency and exact metadata versions are unproven.",
                  "Public availability and recorded zero do not establish paid sales, attendance or constant released pool.",
                  "All original exposed fixtures remain exposed; only genuine future forecasts can evaluate accuracy."]}
    result["dataset_sha256"] = _hash(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "registry", "outcomes", "archive", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT) or output.exists():
        parser.error("New private output outside Git required; existing datasets are never overwritten")
    result = build_dataset(*(path.read_bytes() for path in (args.source, args.registry, args.outcomes, args.archive)))
    output.parent.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"version": VERSION, "dataset_sha256": result["dataset_sha256"],
                      "coverage": result["coverage"], "model_fit_performed": False}))


if __name__ == "__main__":
    main()
