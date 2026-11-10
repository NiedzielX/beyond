"""Archived actual-receipt rolling72 training eligibility, never model fitting.

Every input origin is a real manifest-verified export's retrieved_at, with the
exact metadata/rows received then. Labels use the first original receipt at or
after the nominal target that supplies a matching real observation. No capture
timestamp is substituted for an unknown historical ingestion clock. Replaying
these already exposed archives is NOT prospective or untouched validation.

Paths are accepted alongside bytes so the CLI can process large private receipt
archives without retaining every decoded export in memory. Files are hashed on
both reads; changing a source during construction fails closed. Registry source
identities establish conservative groups, not independent raw immutability or a
verified fixed released pool. All prefixes/aliases of one group stay together.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from ml.demand_engine.rolling72_features_v1 import HORIZONS, _hash, _id, _time, build_issue
from ml.demand_engine.rolling72_labels_v1 import match_target
from ml.rolling72_receipt_store_v1 import METRIC


VERSION = "rolling72-actual-receipt-dataset-v1"
ROOT = Path(__file__).resolve().parent.parent
PRECOMMIT_PATH = ROOT / "ml/artifacts/rolling72_v1/precommit.json"


def _payload(source: bytes | Path) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, Path):
        return source.read_bytes()
    raise ValueError("Receipt sources must be original bytes or Paths")


def _precommit(value: dict | None) -> dict:
    value = json.loads(PRECOMMIT_PATH.read_text()) if value is None else value
    if (value.get("version") != "rolling72-benchmarks-and-quantile-tree-precommit-v1"
            or value.get("precommit_sha256") != _hash({k: v for k, v in value.items()
                                                       if k != "precommit_sha256"})):
        raise ValueError("Verified rolling72 precommit required")
    if (value["training"].get("completed_only") is not True
            or value["training"].get("ongoing_fixtures_in_fit") is not False
            or value["training"].get("evidence") != "original-receipt-known-bounds-only"):
        raise ValueError("Completed-only actual-receipt training contract required")
    return value


def _registry(payload: bytes) -> tuple[dict[int, str], dict[str, dict], dict[int, set[tuple]]]:
    rows = json.loads(payload)
    if not isinstance(rows, list):
        raise ValueError("Original archived ticket-event registry list required")
    parent: dict[int, int] = {}
    identities: dict[int, set[tuple]] = defaultdict(set)
    owner: dict[tuple, int] = {}

    def find(identifier):
        parent.setdefault(identifier, identifier)
        while parent[identifier] != identifier:
            parent[identifier] = parent[parent[identifier]]
            identifier = parent[identifier]
        return identifier

    def union(one, two):
        one, two = find(one), find(two)
        parent[max(one, two)] = min(one, two)

    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Registry entries must be objects")
        identifier = _id(row.get("id"))
        provider, club, external = row.get("provider"), row.get("club_slug"), row.get("external_event_id")
        domain = row.get("source_domain") or urlparse(row.get("source_url") or "").hostname
        if (any(not isinstance(v, str) or not v.strip() for v in (provider, club, domain))
                or isinstance(external, bool) or not isinstance(external, (int, str))
                or not str(external).strip()):
            continue  # Unknown identity cannot acquire independent support.
        key = (provider.strip(), domain.strip().lower(), club.strip(), str(external).strip())
        find(identifier)
        identities[identifier].add(key)
        if key in owner:
            union(identifier, owner[key])
        else:
            owner[key] = identifier
    components: dict[int, list[int]] = defaultdict(list)
    for identifier in identities:
        components[find(identifier)].append(identifier)
    groups, result = {}, {}
    for identifiers in components.values():
        keys = sorted(set().union(*(identities[i] for i in identifiers)))
        group = _hash({"source_identities": keys})
        groups[group] = {"ticket_event_ids": sorted(identifiers), "source_identities": keys}
        for identifier in identifiers:
            result[identifier] = group
    return result, groups, identities


def _event(raw: dict, received) -> dict:
    observations = []
    for row in raw["observations"]:
        key = row.get("measurement_key")
        observations.append({
            "snapshot_id": row.get("snapshot_id"), "captured_at": row["captured_at"],
            "known_at": received.isoformat(), "available_total": row.get("available_total"),
            "measurement_key": METRIC + ":" + key if isinstance(key, str) and key.strip() else None,
            "source_active": row.get("source_active"), "source_visible": row.get("source_visible"),
        })
    return {"ticket_event_id": raw["ticket_event_id"], "club_slug": raw["club_slug"],
            "kickoff_at": raw["kickoff_at"], "known_at": received.isoformat(),
            "observations": observations}


def build_dataset(receipts: Iterable[bytes | Path], identity_registry_payload: bytes,
                  *, precommit: dict | None = None) -> dict:
    """Build immutable-origin rows and coverage using the pinned fit cutoff.

    Rows contain exactly issue, matched_label, fixture_group and source_lineage.
    matched_label is the complete MATCHED result of rolling72_labels_v1. Aliases
    share a source group; at a receipt we choose the lowest READY ticket ID in
    that group before looking at any target. Incompatible alias kickoff/club
    metadata fails closed. No ongoing fixture enters these training rows.
    """
    protocol = _precommit(precommit)
    cutoff = _time(protocol["fit_cutoff_at"])
    group_by_id, groups, identities = _registry(identity_registry_payload)
    registry_sha = hashlib.sha256(identity_registry_payload).hexdigest()
    descriptors, duplicate_receipts, excluded_future = [], 0, 0
    for source in receipts:
        payload = _payload(source)
        data = json.loads(payload)
        if not isinstance(data, dict) or data.get("version") != "daily-inventory-public-export-v1":
            raise ValueError("Original daily-inventory-public-export-v1 receipt required")
        received, exported = _time(data["retrieved_at"]), _time(data["exported_at"])
        if received > cutoff:
            excluded_future += 1
            continue  # Do not inspect future payload values or include them in hashes.
        if exported > received:
            raise ValueError("Receipt precedes its export cutoff")
        manifest = _hash({k: v for k, v in data.items() if k != "export_sha256"})
        if data.get("export_sha256") != manifest:
            raise ValueError("Original export manifest hash mismatch")
        if data.get("collection_mode") is not None or data.get("source_receipts") is not None:
            raise ValueError("Composite exports are not original training receipts")
        descriptors.append({"_source": source, "source_file_sha256": hashlib.sha256(payload).hexdigest(),
                            "source_manifest_sha256": manifest, "retrieved_at": received.isoformat(),
                            "exported_at": exported.isoformat()})
    descriptors.sort(key=lambda r: (r["retrieved_at"], r["source_manifest_sha256"], r["source_file_sha256"]))
    selected, seen_manifest, clocks = [], set(), {}
    for descriptor in descriptors:
        manifest, clock = descriptor["source_manifest_sha256"], descriptor["retrieved_at"]
        if manifest in seen_manifest:
            duplicate_receipts += 1
            continue
        if clock in clocks and clocks[clock] != manifest:
            raise ValueError("Different original receipts share an issue timestamp")
        seen_manifest.add(manifest)
        clocks[clock] = manifest
        selected.append(descriptor)
    if not selected:
        raise ValueError("No original receipts on or before the pinned fit cutoff")

    input_statuses, coordinate_statuses, label_statuses = Counter(), Counter(), Counter()
    pending, matched, revisions = {}, [], set()
    snapshot_versions, snapshot_owners, issue_metrics = {}, {}, []
    for descriptor in selected:
        payload = _payload(descriptor["_source"])
        if hashlib.sha256(payload).hexdigest() != descriptor["source_file_sha256"]:
            raise ValueError("Original receipt changed while building the dataset")
        data = json.loads(payload)
        received, exported = _time(descriptor["retrieved_at"]), _time(descriptor["exported_at"])
        if not isinstance(data.get("events"), list):
            raise ValueError("Receipt events list required")
        current = {}
        for raw in data["events"]:
            identifier = _id(raw.get("ticket_event_id"))
            if identifier in current:
                raise ValueError("Duplicate event identity in original receipt")
            if not isinstance(raw.get("observations"), list):
                raise ValueError("Original observations list required")
            local_ids = set()
            for observation in raw["observations"]:
                snapshot_id = _id(observation.get("snapshot_id"))
                if snapshot_id in local_ids:
                    raise ValueError("Duplicate snapshot identity in original receipt")
                local_ids.add(snapshot_id)
                owner = snapshot_owners.setdefault(snapshot_id, identifier)
                if owner != identifier:
                    for conflicting in (owner, identifier):
                        revisions.add(group_by_id.get(conflicting, "unresolved:" + str(conflicting)))
                captured = _time(observation["captured_at"])
                if captured > exported:
                    raise ValueError("Snapshot follows original export cutoff")
                identity = (identifier, snapshot_id)
                fingerprint = (captured.isoformat(), *(
                    (type(observation.get(key)).__name__, observation.get(key))
                    for key in ("available_total", "measurement_key", "source_active", "source_visible")))
                if identity in snapshot_versions and snapshot_versions[identity] != fingerprint:
                    revisions.add(group_by_id.get(identifier, "unresolved:" + str(identifier)))
                snapshot_versions[identity] = fingerprint
            current[identifier] = raw
        converted = {}

        def converted_event(identifier):
            if identifier not in converted:
                converted[identifier] = _event(current[identifier], received)
            return converted[identifier]

        # Labels are accepted only at/after the actual nominal horizon and remain first-accepted.
        for identity, work in list(pending.items()):
            if received < work["target_at"]:
                continue
            raw = current.get(work["issue"]["event"]["ticket_event_id"])
            if raw is None:
                work["last_status"] = "EVENT_ABSENT_FROM_LABEL_RECEIPT"
                label_statuses[work["last_status"]] += 1
                continue
            if not any(key[0] == raw.get("provider") and key[2] == raw.get("club_slug")
                       for key in identities[raw["ticket_event_id"]]):
                work["last_status"] = "REGISTRY_LABEL_SOURCE_IDENTITY_MISMATCH"
                label_statuses[work["last_status"]] += 1
                continue
            result = match_target(converted_event(raw["ticket_event_id"]), work["issue"], work["horizon"], received)
            work["last_status"] = result["status"]
            label_statuses[result["status"]] += 1
            if result["status"] != "MATCHED":
                continue
            matched.append({"issue": work["issue"], "matched_label": result,
                            "fixture_group": work["fixture_group"],
                            "source_lineage": {
                                "evidence": "original-receipt-known-bounds-only",
                                "input_receipt_sha256": work["input_receipt_sha256"],
                                "label_receipt_sha256": descriptor["source_file_sha256"],
                                "identity_registry_sha256": registry_sha, "identity_proven": True,
                                "input_receipt_known_at": work["issue"]["issued_at"],
                                "label_receipt_known_at": received.isoformat()}})
            del pending[identity]

        choices: dict[str, list[dict]] = defaultdict(list)
        for identifier, raw in sorted(current.items()):
            kickoff = _time(raw["kickoff_at"])
            if kickoff <= received:
                input_statuses["ISSUE_NOT_BEFORE_KICKOFF"] += 1
                continue
            if kickoff >= cutoff:
                input_statuses["ONGOING_FIXTURE_EXCLUDED"] += 1
                continue
            group = group_by_id.get(identifier)
            if group is None:
                input_statuses["SOURCE_IDENTITY_UNKNOWN"] += 1
                continue
            if not any(key[0] == raw.get("provider") and key[2] == raw.get("club_slug")
                       for key in identities[identifier]):
                input_statuses["REGISTRY_SOURCE_IDENTITY_MISMATCH"] += 1
                continue
            issue = build_issue(converted_event(identifier), received)
            if issue["status"] != "READY":
                input_statuses[issue["status"]] += 1
                continue
            family = issue["measurement_key"].removeprefix(METRIC + ":")
            if family not in protocol["source_families"]:
                input_statuses["UNSUPPORTED_SOURCE_FAMILY"] += 1
                continue
            choices[group].append(issue)
        for group, issues in choices.items():
            if len({(i["event"]["club_slug"], i["event"]["kickoff_at"]) for i in issues}) != 1:
                input_statuses["ALIAS_METADATA_CONFLICT"] += len(issues)
                continue
            issue = min(issues, key=lambda i: i["event"]["ticket_event_id"])
            input_statuses["READY"] += 1
            input_statuses["DUPLICATE_ALIAS_ISSUE_EXCLUDED"] += len(issues) - 1
            issue_metrics.append((group, issue["quality"]["observation_count"], issue["prefix_span_hours"],
                                  (_time(issue["event"]["kickoff_at"]) - received).total_seconds() / 86400))
            for horizon in HORIZONS:
                target = received + timedelta(hours=horizon)
                if target >= _time(issue["event"]["kickoff_at"]):
                    coordinate_statuses["TARGET_NOT_BEFORE_KICKOFF"] += 1
                    continue
                coordinate_statuses["READY"] += 1
                identity = (issue["event"]["ticket_event_id"], issue["issued_at"], horizon)
                pending[identity] = {"issue": issue, "horizon": horizon, "target_at": target,
                                     "fixture_group": group, "last_status": "NO_RECEIPT_AT_OR_AFTER_TARGET",
                                     "input_receipt_sha256": descriptor["source_file_sha256"]}

    removed = sum(row["fixture_group"] in revisions for row in matched)
    rows = [row for row in matched if row["fixture_group"] not in revisions]
    rows.sort(key=lambda r: (r["fixture_group"], r["issue"]["issued_at"], r["matched_label"]["horizon_hours"]))
    per_horizon = {}
    for horizon in HORIZONS:
        subset = [r for r in rows if r["matched_label"]["horizon_hours"] == horizon]
        per_horizon[str(horizon)] = {"row_count": len(subset),
                                     "fixture_group_count": len({r["fixture_group"] for r in subset}),
                                     "club_count": len({r["issue"]["event"]["club_slug"] for r in subset})}
    common = set.intersection(*({r["fixture_group"] for r in rows
                                 if r["matched_label"]["horizon_hours"] == h} for h in HORIZONS))
    admissible_metrics = [m for m in issue_metrics if m[0] not in revisions]
    labeled_prefix_spans = [r["issue"]["prefix_span_hours"] for r in rows]
    result = {
        "version": VERSION, "precommit_sha256": protocol["precommit_sha256"],
        "fit_cutoff_at": cutoff.isoformat(), "identity_registry_sha256": registry_sha,
        "sources": [{k: v for k, v in d.items() if k != "_source"} for d in selected],
        "fixture_groups": groups, "rows": rows,
        "coverage": {"original_receipt_count": len(selected), "duplicate_receipt_files": duplicate_receipts,
                     "receipts_after_cutoff_excluded": excluded_future,
                     "input_status_counts": dict(sorted(input_statuses.items())),
                     "coordinate_status_counts": dict(sorted(coordinate_statuses.items())),
                     "pending_target_count": sum(w["target_at"] > cutoff for w in pending.values()),
                     "mature_missing_target_count": sum(w["target_at"] <= cutoff for w in pending.values()),
                     "label_attempt_status_counts": dict(sorted(label_statuses.items())),
                     "unmatched_target_status_counts": dict(sorted(Counter(w["last_status"] for w in pending.values()).items())),
                     "snapshot_revision_conflict_groups": sorted(revisions),
                     "rows_excluded_for_snapshot_revision": removed, "per_horizon": per_horizon,
                     "common_all_horizon_fixture_groups": len(common),
                     "one_observation_input_count": sum(m[1] == 1 for m in admissible_metrics),
                     "one_observation_matched_row_count": sum(
                         r["issue"]["quality"]["observation_count"] == 1 for r in rows),
                     "minimum_labeled_prefix_span_hours": min(labeled_prefix_spans, default=None),
                     "minimum_prefix_span_hours": min((m[2] for m in admissible_metrics), default=None),
                     "maximum_days_to_kickoff": max((m[3] for m in admissible_metrics), default=None)},
        "evidence_kind": "historical_archived_actual_receipt_inputs_not_prospective_or_untouched_holdout",
        "limitations": ["Supplied original receipt clocks are conservative knowledge bounds, not original row ingestion times.",
                        "Source copies and registry hashes do not independently prove raw-table immutability or constant pool.",
                        "Missing first-point/early-maturity training support remains unsupported, never filled synthetically.",
                        "All old exposed fixtures remain exposed; no MAE or model selection is performed here."],
        "model_fit_performed": False, "prospective_forecasts_created": 0,
        "production_change": False, "live_adjustment": 0,
    }
    result["dataset_sha256"] = _hash(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputsdir", type=Path, required=True)
    parser.add_argument("--identity-registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New private JSON outside the repository")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error("Private receipt-derived training data must remain outside Git")
    if output.exists():
        parser.error("Output already exists; original datasets are never overwritten")
    result = build_dataset(args.inputsdir.glob("public-export*.json"), args.identity_registry.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"version": VERSION, "dataset_sha256": result["dataset_sha256"],
                      "coverage": result["coverage"], "model_fit_performed": False}))


if __name__ == "__main__":
    main()
