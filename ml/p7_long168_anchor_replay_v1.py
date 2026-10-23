#!/usr/bin/env python3
"""P7 Long168 Structural Prior T-7 historical PIT replay.

P7 historical long-horizon events predate the production persistence of their
T-7 Structural Prior rows. This module therefore replays the *frozen* Runtime
v1 T-7 artifact from historical facts that were chronologically available at
the T-7 cutoff. The result is explicitly classified as ``historical_pit_replay``
and must never be described as a persisted/prospective forecast.

No P7 challenger is fitted here.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay
from ml.p7_long168_harness_v1 import (
    EXPECTED_EXPORT_VERSION,
    MIN_INDEPENDENT_EVENTS,
    WINDOW_LOWER_EXCLUSIVE_HOURS,
    WINDOW_UPPER_INCLUSIVE_HOURS,
)

VERSION = "p7-long168-anchor-replay-v1"
EXPECTED_EVENTS_VERSION = "c1-alpha-v7-events-v1"
EXPECTED_ATTENDANCE_VERSION = "c1-alpha-v7-attendance-v1"
EXPECTED_SPORTING_VERSION = "c1-alpha-v7-sporting-v1"
EXPECTED_ALIASES_VERSION = "c1-alpha-v7-aliases-v1"
EXPECTED_HORIZON = "T-7"
EXPECTED_T7_ARTIFACT_SHA256 = "97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927"
EXPECTED_HISTORICAL_RUNTIME_SHA256 = "3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569"
ANCHOR_EVIDENCE_CLASS = "historical_pit_replay"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def _validate_version(payload: dict[str, Any], expected: str, label: str) -> None:
    require(payload.get("version") == expected, f"unexpected {label} version: {payload.get('version')}")


def _eligible_long168_rows(long168: dict[str, Any]) -> list[dict[str, Any]]:
    _validate_version(long168, EXPECTED_EXPORT_VERSION, "Long168")
    rows: list[dict[str, Any]] = []
    for row in long168.get("liveRows") or []:
        hours = float(row["hours_to_kickoff"])
        if not (WINDOW_LOWER_EXCLUSIVE_HOURS < hours <= WINDOW_UPPER_INCLUSIVE_HOURS):
            continue
        features = row.get("features") or {}
        require(bool(features.get("point_in_time_validated")), "Long168 row is not PIT validated")
        rows.append(row)
    require(rows, "no Long168 rows in P7 window")
    return rows


def eligible_event_ids(long168: dict[str, Any]) -> list[int]:
    return sorted({int(row["ticket_event_id"]) for row in _eligible_long168_rows(long168)})


def _support_payload(
    *,
    target_event_ids: list[int],
    events_payload: dict[str, Any],
    attendance_payload: dict[str, Any],
    sporting_payload: dict[str, Any],
    aliases_payload: dict[str, Any],
) -> dict[str, Any]:
    _validate_version(events_payload, EXPECTED_EVENTS_VERSION, "events")
    _validate_version(attendance_payload, EXPECTED_ATTENDANCE_VERSION, "attendance")
    _validate_version(sporting_payload, EXPECTED_SPORTING_VERSION, "sporting")
    _validate_version(aliases_payload, EXPECTED_ALIASES_VERSION, "aliases")

    events_by_id = {int(row["ticket_event_id"]): row for row in events_payload.get("events") or []}
    missing = sorted(set(target_event_ids) - set(events_by_id))
    require(not missing, f"P7 anchor support missing event metadata: {missing}")

    # Strip target labels before replay. _event_prior_replay does not require
    # actual_attendance. This protects the anchor contract even if the upstream
    # event support export includes labels for other research workflows.
    sanitized_events: list[dict[str, Any]] = []
    for event_id in target_event_ids:
        event = dict(events_by_id[event_id])
        event.pop("actual_attendance", None)
        sanitized_events.append(event)

    return {
        "events": sanitized_events,
        "attendance": copy.deepcopy(attendance_payload.get("attendance") or []),
        "sportingMatches": copy.deepcopy(sporting_payload.get("sportingMatches") or []),
        "aliases": copy.deepcopy(aliases_payload.get("aliases") or []),
    }


def _artifact_lineage(artifact_dir: Path) -> dict[str, Any]:
    manifest_path = artifact_dir / "manifest.json"
    require(manifest_path.exists(), f"Structural Prior manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    t7 = manifest.get("artifacts", {}).get(EXPECTED_HORIZON)
    require(bool(t7), "frozen Structural Prior T-7 artifact missing")
    require(t7.get("sha256") == EXPECTED_T7_ARTIFACT_SHA256, "Structural Prior T-7 artifact SHA drift")
    historical = manifest.get("historical_runtime") or {}
    require(
        historical.get("sha256") == EXPECTED_HISTORICAL_RUNTIME_SHA256,
        "Structural Prior historical runtime SHA drift",
    )
    return {
        "artifact_version": manifest.get("artifact_version"),
        "t7_artifact_filename": t7.get("filename"),
        "t7_artifact_sha256": t7.get("sha256"),
        "historical_runtime_filename": historical.get("filename"),
        "historical_runtime_sha256": historical.get("sha256"),
    }


def _replay_t7(support: dict[str, Any], artifact_dir: Path) -> pd.DataFrame:
    priors = _event_prior_replay(support, artifact_dir)
    t7 = priors[priors["horizon"].astype(str) == EXPECTED_HORIZON].copy()
    require(len(t7) == len(support["events"]), "P7 replay did not return exactly one T-7 row per event")
    require(t7["prior_p50"].notna().all(), f"P7 T-7 replay errors: {t7[t7['prior_p50'].isna()].to_dict('records')}")
    require(t7["ticket_event_id"].astype(int).nunique() == len(t7), "duplicate T-7 replay event")
    return t7.sort_values("ticket_event_id").reset_index(drop=True)


def _target_attendance_invariance(
    *,
    support: dict[str, Any],
    base_t7: pd.DataFrame,
    artifact_dir: Path,
) -> dict[str, Any]:
    """Prove each target's own attendance value cannot affect its T-7 anchor.

    For each target event, mutate a same-home exact-kickoff attendance row to an
    impossible sentinel. If the feature builder is correctly PIT-filtered to
    kickoff < T-7 cutoff, the target's T-7 replay must remain bitwise-close.
    """
    event_by_id = {int(row["ticket_event_id"]): row for row in support["events"]}
    base = {int(row.ticket_event_id): float(row.prior_p50) for row in base_t7.itertuples(index=False)}
    checked: list[int] = []
    no_exact_attendance_row: list[int] = []

    for event_id, event in sorted(event_by_id.items()):
        mutated = copy.deepcopy(support)
        target_kickoff = _utc(event["kickoff_at"])
        home_slug = str(event.get("club_slug"))
        matched = False
        for row in mutated["attendance"]:
            if str(row.get("club_slug")) != home_slug:
                continue
            if _utc(row.get("kickoff_at")) != target_kickoff:
                continue
            row["actual_attendance"] = 999_999_999.0
            matched = True
        if not matched:
            no_exact_attendance_row.append(event_id)
            continue

        one_event = copy.deepcopy(mutated)
        one_event["events"] = [dict(event)]
        replay = _replay_t7(one_event, artifact_dir)
        changed = float(replay.iloc[0]["prior_p50"])
        require(
            np.isclose(changed, base[event_id], rtol=0.0, atol=1e-9),
            f"target attendance leakage changed T-7 anchor event={event_id} base={base[event_id]} changed={changed}",
        )
        checked.append(event_id)

    return {
        "status": "PASS",
        "checked_event_ids": checked,
        "no_exact_attendance_row_event_ids": no_exact_attendance_row,
        "sentinel_attendance": 999_999_999.0,
        "tolerance": 1e-9,
    }


def build_anchor_package(
    *,
    long168: dict[str, Any],
    events_payload: dict[str, Any],
    attendance_payload: dict[str, Any],
    sporting_payload: dict[str, Any],
    aliases_payload: dict[str, Any],
    artifact_dir: Path,
    require_research_gate: bool,
    run_target_invariance_gate: bool = True,
) -> dict[str, Any]:
    event_ids = eligible_event_ids(long168)
    if require_research_gate:
        require(
            len(event_ids) >= MIN_INDEPENDENT_EVENTS,
            f"P7_NOT_READY: independent_events_gt_72h={len(event_ids)} threshold={MIN_INDEPENDENT_EVENTS}",
        )

    support = _support_payload(
        target_event_ids=event_ids,
        events_payload=events_payload,
        attendance_payload=attendance_payload,
        sporting_payload=sporting_payload,
        aliases_payload=aliases_payload,
    )
    lineage = _artifact_lineage(artifact_dir)
    t7 = _replay_t7(support, artifact_dir)
    events_by_id = {int(row["ticket_event_id"]): row for row in support["events"]}
    long_rows = _eligible_long168_rows(long168)
    rows_by_event: dict[int, list[dict[str, Any]]] = {}
    for row in long_rows:
        rows_by_event.setdefault(int(row["ticket_event_id"]), []).append(row)

    anchors: list[dict[str, Any]] = []
    for replay in t7.to_dict("records"):
        event_id = int(replay["ticket_event_id"])
        event = events_by_id[event_id]
        cutoff = _utc(replay["target_as_of_at"])
        kickoff = _utc(event["kickoff_at"])
        require(cutoff == kickoff - pd.Timedelta(days=7), f"T-7 cutoff drift event={event_id}")
        live_as_of = [
            _utc((row.get("features") or {}).get("as_of_at") or row["requested_as_of_at"])
            for row in rows_by_event[event_id]
        ]
        require(live_as_of and cutoff <= min(live_as_of), f"T-7 anchor is from future vs Long168 row event={event_id}")
        capacity = int(event["stadium_capacity"])
        p50 = float(replay["prior_p50"])
        require(0.0 <= p50 <= capacity, f"T-7 anchor outside capacity event={event_id}")
        anchors.append({
            "ticket_event_id": event_id,
            "kickoff_at": kickoff.isoformat(),
            "target_as_of_at": cutoff.isoformat(),
            "p50": p50,
            "stadium_capacity": capacity,
            "prior_model_spec_id": replay.get("prior_model_spec_id"),
            "artifact_version": replay.get("artifact_version"),
            "anchor_evidence_class": ANCHOR_EVIDENCE_CLASS,
            "persisted_forecast": False,
            "historical_replay": True,
        })

    invariance = (
        _target_attendance_invariance(support=support, base_t7=t7, artifact_dir=artifact_dir)
        if run_target_invariance_gate
        else {"status": "NOT_RUN"}
    )

    semantic_inputs = {
        "long168_identities": [
            {
                "ticket_event_id": int(row["ticket_event_id"]),
                "requested_snapshot_id": int(row["requested_snapshot_id"]),
                "requested_as_of_at": str(row["requested_as_of_at"]),
                "bucket_6h": int(row["bucket_6h"]),
            }
            for row in long_rows
        ],
        "events": support["events"],
        "attendance": support["attendance"],
        "sportingMatches": support["sportingMatches"],
        "aliases": support["aliases"],
    }
    core = {
        "version": VERSION,
        "status": "P7_T7_ANCHOR_REPLAY_READY",
        "anchor_evidence_class": ANCHOR_EVIDENCE_CLASS,
        "persisted_forecast": False,
        "model_training_performed": False,
        "model_results_opened": False,
        "production_change": False,
        "research_gate_required": require_research_gate,
        "independent_event_count": len(event_ids),
        "event_ids": event_ids,
        "anchor_count": len(anchors),
        "anchors": anchors,
        "target_attendance_invariance": invariance,
        "lineage": {
            **lineage,
            "support_versions": {
                "events": EXPECTED_EVENTS_VERSION,
                "attendance": EXPECTED_ATTENDANCE_VERSION,
                "sporting": EXPECTED_SPORTING_VERSION,
                "aliases": EXPECTED_ALIASES_VERSION,
                "long168": EXPECTED_EXPORT_VERSION,
            },
            "support_semantic_sha256": _canonical_sha(semantic_inputs),
            "sporting_replay_rule": "completed fixture event_date strictly before T-7 cutoff local date; historical factual replay, not system-as-known persistence",
            "attendance_replay_rule": "current-season attendance rows with kickoff strictly before T-7 cutoff only",
            "target_event_actual_stripped_from_event_metadata": True,
        },
    }
    return {**core, "package_sha256": _canonical_sha(core)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--long168", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--attendance", type=Path, required=True)
    parser.add_argument("--sporting", type=Path, required=True)
    parser.add_argument("--aliases", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("audit", "build"), default="audit")
    parser.add_argument("--skip-target-invariance-gate", action="store_true")
    args = parser.parse_args()

    result = build_anchor_package(
        long168=json.loads(args.long168.read_text()),
        events_payload=json.loads(args.events.read_text()),
        attendance_payload=json.loads(args.attendance.read_text()),
        sporting_payload=json.loads(args.sporting.read_text()),
        aliases_payload=json.loads(args.aliases.read_text()),
        artifact_dir=args.artifact_dir,
        require_research_gate=args.mode == "build",
        run_target_invariance_gate=not args.skip_target_invariance_gate,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "independent_event_count": result["independent_event_count"],
        "anchor_count": result["anchor_count"],
        "anchor_evidence_class": result["anchor_evidence_class"],
        "persisted_forecast": result["persisted_forecast"],
        "target_attendance_invariance": result["target_attendance_invariance"],
        "package_sha256": result["package_sha256"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
