"""Feature-only historical replay packets and a separate future-truth vault.

These are retrospective capture-clock coordinates, never previously issued
forecasts or historical PIT proof. The predictor can read training rows and
test inputs without opening the separately checksummed truth file. Selection
of input origins happens before future target matching, including stale labels.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path

from ml.demand_engine.rolling72_features_v1 import HORIZONS, _count, _hash, _id, _time
from ml.rolling72_offline_dataset_v2 import capture_features, _key, _usable


VERSION = "rolling72-historical-replay-packets-v1"
PRECOMMIT_SHA256 = "4acdfd98b79b781b8704fcfa56097bc0bf0e114e81357085af5075514c1bfdb4"
ROOT = Path(__file__).resolve().parents[1]
PRECOMMIT_PATH = ROOT / "ml/artifacts/rolling72_historical_replay_v1/precommit.json"
ALLOWED_FAMILIES = {"roboticket/roboticket", "stellis/stellis_visible_available"}


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode()


def _digest(raw):
    if not isinstance(raw, bytes):
        raise ValueError("Original bytes required")
    return hashlib.sha256(raw).hexdigest()


def load_precommit(*, synthetic_test=False, precommit=None):
    if not isinstance(synthetic_test, bool):
        raise ValueError("Explicit boolean synthetic mode required")
    if precommit is not None and not synthetic_test:
        raise ValueError("Custom protocol is synthetic-only")
    protocol = json.loads(PRECOMMIT_PATH.read_text()) if precommit is None else precommit
    if (not isinstance(protocol, dict)
            or protocol.get("version") != "rolling72-chronological-event-heldout-replay-precommit-v1"
            or protocol.get("precommit_sha256") != _hash({k: v for k, v in protocol.items() if k != "precommit_sha256"})
            or (not synthetic_test and protocol["precommit_sha256"] != PRECOMMIT_SHA256)
            or protocol.get("production_change") is not False or protocol.get("live_adjustment") != 0
            or protocol["protocol"].get("historical_knowledge_unproven") is not True
            or protocol["protocol"].get("test_target_values_passed_to_estimator") is not False
            or protocol["outputs"].get("servable") is not False):
        raise ValueError("Exact nonservable retrospective precommit required")
    return protocol


def _validate_originals(dataset_payload, source_payload, protocol, synthetic_test):
    declared = protocol["dataset"]
    if _digest(dataset_payload) != declared["dataset_file_sha256"]:
        raise ValueError("Original dataset bytes differ from precommit")
    dataset, source = json.loads(dataset_payload), json.loads(source_payload)
    if (dataset.get("dataset_sha256") != _hash({k: v for k, v in dataset.items() if k != "dataset_sha256"})
            or dataset["dataset_sha256"] != declared["dataset_sha256"]
            or dataset.get("version") != "rolling72-offline-capture-segment-dataset-v2"
            or dataset.get("historical_knowledge_unproven") is not True
            or dataset.get("historical_input_known_at", "missing") is not None
            or dataset.get("model_fit_performed") is not False
            or dataset.get("synthetic_test") is not synthetic_test
            or dataset.get("production_change") is not False or dataset.get("live_adjustment") != 0):
        raise ValueError("Dataset hash/evidence/mode differs from precommit")
    bindings = declared["source_bindings"]
    for name, expected in bindings.items():
        actual = dataset.get("source_bindings", {}).get(name)
        if (not isinstance(actual, dict) or any(actual.get(k) != v for k, v in expected.items())
                or actual.get("verified_file_sha256") != expected["file_sha256"]):
            raise ValueError("Dataset original source binding mismatch")
    inventory = bindings["inventory"]
    if (_digest(source_payload) != inventory["file_sha256"]
            or source.get("version") != "daily-inventory-public-export-v1"
            or source.get("export_sha256") != _hash({k: v for k, v in source.items() if k != "export_sha256"})
            or source["export_sha256"] != inventory["manifest_sha256"]
            or _time(source["retrieved_at"]) != _time(inventory["received_at"])
            or _time(source["exported_at"]) > _time(source["retrieved_at"])):
        raise ValueError("Original inventory byte/manifest/clock mismatch")
    if not isinstance(source.get("events"), list) or not isinstance(dataset.get("rows"), list):
        raise ValueError("Original events and training rows required")
    return dataset, source


def _history_quality(clean, values):
    hourly = {}
    for row in clean:
        bucket = _time(row["captured_at"]).replace(minute=0, second=0, microsecond=0)
        hourly[bucket] = row
    times = [_time(row["captured_at"]) for row in hourly.values()]
    return {"hourly_latest_bins": len(hourly),
            "hourly_span_hours": (max(times) - min(times)).total_seconds() / 3600 if times else 0.0,
            "delta24_anchor_valid": values["slope_24h"] is not None}


def _truth(observations, times, segment_ids, index, horizon, kickoff, exported):
    origin, target = times[index], times[index] + timedelta(hours=horizon)
    label_index = bisect_right(times, target) - 1
    if target >= kickoff:
        status = "TARGET_NOT_BEFORE_KICKOFF"
    elif target > exported:
        status = "TARGET_NOT_COVERED_BY_RECEIVED_SOURCE"
    elif label_index < 0 or times[label_index] <= origin:
        status = "NO_STRICT_FUTURE_OBSERVATION"
    elif segment_ids[label_index] != segment_ids[index]:
        status = "SOURCE_SCOPE_TRANSITION_BEFORE_TARGET"
    elif target - times[label_index] > timedelta(hours=6):
        status = "STALE_TARGET_OBSERVATION"
    elif not _usable(observations[label_index]):
        status = "INVALID_OR_HIDDEN_LATEST_TARGET"
    elif any(not _usable(row) for row in observations[index + 1:label_index + 1]):
        status = "INVALID_OR_HIDDEN_FUTURE_INTERVAL"
    else:
        status = "MATCHED"
    matched = status == "MATCHED"
    return {"status": status,
            "available_total": _count(observations[label_index]["available_total"]) if matched else None,
            "label_captured_at": times[label_index].isoformat() if matched else None,
            "label_snapshot_id": _id(observations[label_index]["snapshot_id"]) if matched else None}


def build_packets(dataset_payload: bytes, source_payload: bytes, *, synthetic_test=False, precommit=None):
    """Derive all feature inputs before consulting target values/availability."""
    protocol = load_precommit(synthetic_test=synthetic_test, precommit=precommit)
    dataset, source = _validate_originals(dataset_payload, source_payload, protocol, synthetic_test)
    events = {}
    for event in source["events"]:
        identifier = _id(event["ticket_event_id"])
        if identifier in events:
            raise ValueError("Duplicate original event identity")
        events[identifier] = event
    catalogue_by_group = defaultdict(list)
    for segment in dataset["segment_catalogue"]:
        catalogue_by_group[segment["fixture_group"]].append(segment)
    expected_rows = {}
    for row in dataset["rows"]:
        if row.get("row_sha256") != _hash({k: v for k, v in row.items() if k != "row_sha256"}):
            raise ValueError("Original training row checksum mismatch")
        key = (row["fixture_group"], row["origin_capture_at"], row["nominal_horizon_hours"])
        if key in expected_rows:
            raise ValueError("Duplicate canonical training coordinate")
        expected_rows[key] = row
    inputs, truth, statuses, input_status = [], {}, Counter(), Counter()
    seen_coordinates, matched_coordinates = set(), set()
    exported = _time(source["exported_at"])
    for group, catalogue in sorted(catalogue_by_group.items()):
        identifiers = {s["ticket_event_id"] for s in catalogue}
        if len(identifiers) != 1:
            raise ValueError("Selected catalogue cannot merge independent source events")
        identifier = next(iter(identifiers))
        if identifier not in events:
            raise ValueError("Selected event absent from original inventory")
        event = events[identifier]
        kickoff = _time(event["kickoff_at"])
        observations = sorted((r for r in event["observations"] if _time(r["captured_at"]) < kickoff),
                              key=lambda r: (_time(r["captured_at"]), _id(r["snapshot_id"])))
        if not observations:
            raise ValueError("Selected catalogue lacks pre-kickoff observations")
        if len({_id(row["snapshot_id"]) for row in observations}) != len(observations):
            raise ValueError("Duplicate snapshot identity")
        times = [_time(row["captured_at"]) for row in observations]
        if any(at > exported for at in times):
            raise ValueError("Capture exceeds original export boundary")
        segments, segment_ids = [], []
        for index, raw in enumerate(observations):
            if not segments or _key(raw) != segments[-1]["key"]:
                segments.append({"start": index, "key": _key(raw)})
            segment_ids.append(len(segments) - 1)
        derived = []
        for number, segment in enumerate(segments):
            first = segment["start"]
            end = segments[number + 1]["start"] - 1 if number + 1 < len(segments) else len(observations) - 1
            derived.append({"ticket_event_id": identifier, "fixture_group": group, "segment_id": number,
                "measurement_key": segment["key"], "supported_family": segment["key"] in ALLOWED_FAMILIES,
                "start_at": times[first].isoformat(), "last_capture_at": times[end].isoformat(),
                "row_count": end - first + 1,
                "raw_snapshot_ids": [r["snapshot_id"] for r in observations[first:end + 1]]})
        if sorted(catalogue, key=lambda s: s["segment_id"]) != derived:
            raise ValueError("Selected catalogue differs from original source segments")
        origins = {s["start"] for s in segments}
        seen_days = set()
        for index, capture in enumerate(times):
            if capture.date() not in seen_days:
                origins.add(index)
                seen_days.add(capture.date())
        resolved = set()
        for index in origins:
            while index + 1 < len(observations) and times[index + 1] == times[index] and segment_ids[index + 1] == segment_ids[index]:
                index += 1
            resolved.add(index)
        for index in sorted(resolved):
            origin = times[index]
            start = segments[segment_ids[index]]["start"]
            prefix = observations[start:index + 1]
            family = _key(observations[index])
            if family not in ALLOWED_FAMILIES:
                input_status["UNSUPPORTED_SEGMENT_FAMILY"] += 1
                continue
            if any(not _usable(row) for row in prefix):
                input_status["INVALID_OR_HIDDEN_PREFIX"] += 1
                continue
            input_status["ELIGIBLE_OFFLINE_CAPTURE_ORIGIN"] += 1
            for horizon in HORIZONS:
                # Input selection is complete before the separate target matcher.
                features, clean = capture_features(prefix, origin, kickoff, horizon)
                target = origin + timedelta(hours=horizon)
                coordinate = {"fixture_group": group, "origin_capture_at": origin.isoformat(), "horizon_hours": horizon}
                identifier_hash = _hash(coordinate)
                if identifier_hash in seen_coordinates:
                    raise ValueError("Duplicate replay coordinate")
                seen_coordinates.add(identifier_hash)
                inputs.append({"coordinate_id": identifier_hash, **coordinate, "ticket_event_id": identifier,
                    "club_slug": event["club_slug"], "kickoff_at": kickoff.isoformat(), "target_at": target.isoformat(),
                    "status": "READY" if target < kickoff else "TARGET_NOT_BEFORE_KICKOFF",
                    "features": features, "source_family": family, "prefix_sha256": _hash(clean),
                    "history_quality": _history_quality(clean, features),
                    "raw_prefix_snapshot_ids": [r["snapshot_id"] for r in prefix]})
                matched = _truth(observations, times, segment_ids, index, horizon, kickoff, exported)
                truth[identifier_hash] = {**coordinate, "target_at": target.isoformat(), **matched}
                statuses[matched["status"]] += 1
                if matched["status"] == "MATCHED":
                    key = (group, origin.isoformat(), horizon)
                    original = expected_rows.get(key)
                    if (original is None or original["features"] != features
                            or original["prefix_sha256"] != _hash(clean)
                            or original["matched_available_total"] != matched["available_total"]
                            or original["label_captured_at"] != matched["label_captured_at"]
                            or original["segment_lineage"]["label_snapshot_id"] != matched["label_snapshot_id"]):
                        raise ValueError("Re-derived input/label differs from canonical training dataset")
                    matched_coordinates.add(key)
    if matched_coordinates != set(expected_rows):
        raise ValueError("Canonical labeled coordinates missing from full replay")
    inputs.sort(key=lambda r: (r["origin_capture_at"], r["fixture_group"], r["horizon_hours"]))
    coverage = {"selected_fixture_groups": len(catalogue_by_group),
                "feature_origins": input_status["ELIGIBLE_OFFLINE_CAPTURE_ORIGIN"],
                "test_coordinates": len(inputs), "training_rows": len(dataset["rows"]),
                "input_status_counts": dict(input_status), "truth_status_counts": dict(statuses),
                "all_inputs_selected_before_label_matching": True}
    for name, actual in (("completed_selected_fixture_catalogue", len(catalogue_by_group)),
                         ("all_feature_origins_before_label_filter", coverage["feature_origins"]),
                         ("all_horizon_coordinates", len(inputs)),
                         ("known_matched_labels", statuses["MATCHED"]),
                         ("known_stale_target_coordinates", statuses["STALE_TARGET_OBSERVATION"]),
                         ("known_postkickoff_coordinates", statuses["TARGET_NOT_BEFORE_KICKOFF"])):
        if actual != protocol["dataset"][name]:
            raise ValueError("Full-coordinate coverage differs from precommitted feasibility")
    return {"training_rows": dataset["rows"], "test_inputs": inputs, "truth": truth, "coverage": coverage}


def prepare_packets(outputdir, dataset_payload: bytes, source_payload: bytes, *, synthetic_test=False, precommit=None):
    """Write one exclusive nonservable packet directory outside Git; no fitting."""
    protocol = load_precommit(synthetic_test=synthetic_test, precommit=precommit)
    result = build_packets(dataset_payload, source_payload, synthetic_test=synthetic_test, precommit=precommit)
    destination = Path(outputdir)
    if destination.is_symlink() or destination.resolve().is_relative_to(ROOT) or destination.exists():
        raise ValueError("A new private packet directory outside Git is required")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(mode=0o700)
    bodies = {name + ".json": _bytes(result[name]) for name in ("training_rows", "test_inputs", "truth")}
    manifest = {"version": VERSION, "precommit_sha256": protocol["precommit_sha256"],
                "dataset_sha256": protocol["dataset"]["dataset_sha256"],
                "file_sha256": {name: _digest(raw) for name, raw in bodies.items()},
                "created_at": datetime.now(timezone.utc).isoformat(), "coverage": result["coverage"],
                "synthetic_test": synthetic_test, "servable": False, "historical_knowledge_unproven": True,
                "production_change": False, "live_adjustment": 0}
    manifest["manifest_sha256"] = _hash(manifest)
    bodies["manifest.json"] = _bytes(manifest)
    for name, raw in bodies.items():
        with os.fdopen(os.open(destination / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
            stream.write(raw)
    return manifest
