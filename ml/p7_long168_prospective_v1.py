#!/usr/bin/env python3
"""P7 Long168 prospective validator/builder v1.

This module does not search candidates. It rebuilds the already-selected
P7 v1 GBR on the exact frozen 10-event research set, proves that the original
Long168 identity manifest still reproduces, then creates target-free future
predictions only for the latest currently-eligible 6h bucket per event.

Prediction persistence is handled separately by the database contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn

from ml.p7_long168_anchor_replay_v1 import (
    _artifact_lineage,
    _replay_t7,
    _support_payload,
    build_anchor_package,
)
from ml.p7_long168_harness_v1 import FEATURE_ALLOWLIST, freeze_manifest
from ml.p7_long168_tournament_v1 import (
    _build_frame,
    _event_weights,
    _gbr,
    _labels,
    _numeric_feature,
)

VERSION = "p7-long168-prospective-builder-v1"
CANDIDATE_ID = "gbr-l1-depth2-n50-lr003"
TRAINING_EVENT_IDS = [1, 3, 4, 5, 10, 11, 15, 16, 18, 19]
EXPECTED_TRAINING_ROW_COUNT = 139
EXPECTED_FREEZE_MANIFEST_SHA256 = "185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed"
SOURCE_SCORECARD_SHA256 = "f684570856e264dae288599a8e24dde6802f84669a43e304c1d900726aa94e45"
EXPECTED_T7_ARTIFACT_SHA256 = "97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927"
EXPECTED_HISTORICAL_RUNTIME_SHA256 = "3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569"
EXPECTED_PROSPECTIVE_VERSION = "p7-long168-prospective-inputs-v1"
EXPECTED_TRAINING_EXPORT_VERSION = "d2-long-horizon-168-rows-v1"
EXPECTED_EVENTS_VERSION = "c1-alpha-v7-events-v1"
EXPECTED_ATTENDANCE_VERSION = "c1-alpha-v7-attendance-v1"
EXPECTED_SPORTING_VERSION = "c1-alpha-v7-sporting-v1"
EXPECTED_ALIASES_VERSION = "c1-alpha-v7-aliases-v1"

# First run is fingerprint-only. This must be replaced with the observed
# deterministic fingerprint before --mode predict is allowed.
EXPECTED_MODEL_FINGERPRINT_SHA256: str | None = None

EXPECTED_TRAINING_ANCHORS = {
    1: 29247.1247487848,
    3: 30300.394400405094,
    4: 28216.30495703302,
    5: 28893.274898572,
    10: 17312.06401199996,
    11: 18952.314465733212,
    15: 11124.345924068082,
    16: 16000.289747002917,
    18: 13650.031586280957,
    19: 5536.115806257667,
}

PROHIBITED_PROSPECTIVE_KEYS = {
    "actual_attendance",
    "attendance_actual",
    "target_attendance",
    "label",
    "outcome",
    "outcome_confirmed_at",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def _clean_number(value: Any) -> Any:
    if value is None:
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _training_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require(payload.get("version") == EXPECTED_TRAINING_EXPORT_VERSION, "unexpected historical Long168 version")
    result = dict(payload)
    rows = [row for row in payload.get("liveRows") or [] if int(row["ticket_event_id"]) in TRAINING_EVENT_IDS]
    result["liveRows"] = rows
    result["eventCount"] = len({int(row["ticket_event_id"]) for row in rows})
    result["liveRowCount"] = len(rows)
    return result


def _assert_training_anchors(anchor_package: dict[str, Any]) -> None:
    anchors = {int(row["ticket_event_id"]): float(row["p50"]) for row in anchor_package.get("anchors") or []}
    require(sorted(anchors) == TRAINING_EVENT_IDS, f"training anchor event drift: {sorted(anchors)}")
    for event_id, expected in EXPECTED_TRAINING_ANCHORS.items():
        observed = anchors[event_id]
        require(np.isclose(observed, expected, rtol=0.0, atol=1e-9), f"training T-7 anchor drift event={event_id} expected={expected} observed={observed}")


def _tree_payload(estimator: Any) -> dict[str, Any]:
    tree = estimator.tree_
    return {
        "children_left": tree.children_left.tolist(),
        "children_right": tree.children_right.tolist(),
        "feature": tree.feature.tolist(),
        "threshold": [_clean_number(v) for v in tree.threshold.tolist()],
        "value": [_clean_number(v) for v in np.asarray(tree.value).reshape(-1).tolist()],
        "impurity": [_clean_number(v) for v in tree.impurity.tolist()],
        "n_node_samples": tree.n_node_samples.tolist(),
        "weighted_n_node_samples": [_clean_number(v) for v in tree.weighted_n_node_samples.tolist()],
    }


def _model_fingerprint(model: Any) -> tuple[str, dict[str, Any]]:
    imputer = model.named_steps["impute"]
    gbr = model.named_steps["model"]
    init_constant = None
    if hasattr(gbr.init_, "constant_"):
        init_constant = [_clean_number(v) for v in np.asarray(gbr.init_.constant_).reshape(-1).tolist()]
    payload = {
        "version": "p7-long168-gbr-fingerprint-v1",
        "sklearn_version": sklearn.__version__,
        "candidate_id": CANDIDATE_ID,
        "features": list(FEATURE_ALLOWLIST),
        "imputer": {
            "strategy": "median",
            "keep_empty_features": True,
            "statistics": [_clean_number(v) for v in np.asarray(imputer.statistics_).tolist()],
        },
        "gbr_params": {
            "loss": gbr.loss,
            "n_estimators": int(gbr.n_estimators),
            "learning_rate": float(gbr.learning_rate),
            "max_depth": 2,
            "min_samples_leaf": 4,
            "random_state": 42,
        },
        "n_features_in": int(gbr.n_features_in_),
        "init_constant": init_constant,
        "train_score": [_clean_number(v) for v in np.asarray(gbr.train_score_).tolist()],
        "trees": [_tree_payload(estimator) for estimator in np.asarray(gbr.estimators_).reshape(-1)],
    }
    return _sha(payload), payload


def _fit_frozen_model(bundle: dict[str, Any], artifact_dir: Path):
    long168 = _training_payload(bundle["trainingLong168"])
    freeze = freeze_manifest(long168)
    require(freeze["manifest_sha256"] == EXPECTED_FREEZE_MANIFEST_SHA256, f"training freeze manifest drift: {freeze['manifest_sha256']}")
    require(freeze["event_ids"] == TRAINING_EVENT_IDS, f"training event set drift: {freeze['event_ids']}")
    require(int(freeze["row_count"]) == EXPECTED_TRAINING_ROW_COUNT, f"training row count drift: {freeze['row_count']}")

    anchor_package = build_anchor_package(
        long168=long168,
        events_payload=bundle["trainingEvents"],
        attendance_payload=bundle["attendance"],
        sporting_payload=bundle["sporting"],
        aliases_payload=bundle["aliases"],
        artifact_dir=artifact_dir,
        require_research_gate=True,
        run_target_invariance_gate=False,
    )
    _assert_training_anchors(anchor_package)
    anchors = {int(row["ticket_event_id"]): row for row in anchor_package["anchors"]}
    actual, capacities = _labels(bundle["trainingEvents"], TRAINING_EVENT_IDS)
    frame = _build_frame(long168=long168, freeze=freeze, anchors=anchors, actual=actual, capacities=capacities)
    require(len(frame) == EXPECTED_TRAINING_ROW_COUNT, "training frame row drift")

    model = _gbr()
    weights = _event_weights(frame)
    model.fit(frame[list(FEATURE_ALLOWLIST)], frame["target_residual"].astype(float), model__sample_weight=weights)
    fingerprint, fingerprint_payload = _model_fingerprint(model)
    return model, fingerprint, fingerprint_payload, freeze, anchor_package, frame


def _latest_prospective_rows(prospective: dict[str, Any]) -> list[dict[str, Any]]:
    require(prospective.get("version") == EXPECTED_PROSPECTIVE_VERSION, "unexpected prospective input version")
    require(prospective.get("targetValuesIncluded") is False, "prospective input includes target values")
    require(prospective.get("targetValuesUsed") is False, "prospective input used target values")
    prohibited = sorted(set(_walk_keys(prospective)) & PROHIBITED_PROSPECTIVE_KEYS)
    require(not prohibited, f"prospective target leakage keys: {prohibited}")

    generated_at = _utc(prospective["generated_at"])
    events = {int(row["ticket_event_id"]): row for row in prospective.get("events") or []}
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in prospective.get("liveRows") or []:
        event_id = int(row["ticket_event_id"])
        event = events.get(event_id)
        require(event is not None, f"prospective event metadata missing event={event_id}")
        kickoff = _utc(event["kickoff_at"])
        current_hours = (kickoff - generated_at).total_seconds() / 3600.0
        require(72.0 < current_hours <= 168.0, f"prediction run outside current P7 window event={event_id} hours={current_hours}")
        row_hours = float(row["hours_to_kickoff"])
        require(72.0 < row_hours <= 168.0, f"prospective row outside P7 window event={event_id}")
        features = row.get("features") or {}
        require(bool(features.get("point_in_time_validated")), f"prospective PIT validation failed event={event_id}")
        require(int(features["snapshot_id"]) == int(row["requested_snapshot_id"]), f"prospective snapshot drift event={event_id}")
        require(_utc(features["as_of_at"]) == _utc(row["requested_as_of_at"]), f"prospective as_of drift event={event_id}")
        grouped.setdefault(event_id, []).append(row)

    # No bootstrap backfill: only the most recent currently-known bucket per
    # event is eligible on each run. Later scheduled runs add later buckets.
    selected = []
    for event_id, rows in sorted(grouped.items()):
        selected.append(max(rows, key=lambda r: _utc(r["requested_as_of_at"])))
    return selected


def _prospective_anchor_package(bundle: dict[str, Any], selected_rows: list[dict[str, Any]], artifact_dir: Path) -> dict[str, Any]:
    event_ids = sorted({int(row["ticket_event_id"]) for row in selected_rows})
    if not event_ids:
        core = {
            "version": "p7-long168-prospective-anchor-v1",
            "status": "NO_ELIGIBLE_EVENTS",
            "event_ids": [],
            "anchors": [],
            "target_values_used": False,
            "production_change": False,
        }
        return {**core, "package_sha256": _sha(core)}

    prospective = bundle["prospective"]
    event_rows = [row for row in prospective.get("events") or [] if int(row["ticket_event_id"]) in event_ids]
    events_payload = {"version": EXPECTED_EVENTS_VERSION, "events": event_rows}
    support = _support_payload(
        target_event_ids=event_ids,
        events_payload=events_payload,
        attendance_payload=bundle["attendance"],
        sporting_payload=bundle["sporting"],
        aliases_payload=bundle["aliases"],
    )
    lineage = _artifact_lineage(artifact_dir)
    require(lineage["t7_artifact_sha256"] == EXPECTED_T7_ARTIFACT_SHA256, "prospective T-7 artifact SHA drift")
    require(lineage["historical_runtime_sha256"] == EXPECTED_HISTORICAL_RUNTIME_SHA256, "prospective historical runtime SHA drift")
    replay = _replay_t7(support, artifact_dir)
    events_by_id = {int(row["ticket_event_id"]): row for row in event_rows}
    as_of_by_id = {int(row["ticket_event_id"]): _utc(row["requested_as_of_at"]) for row in selected_rows}

    anchors = []
    for row in replay.to_dict("records"):
        event_id = int(row["ticket_event_id"])
        event = events_by_id[event_id]
        kickoff = _utc(event["kickoff_at"])
        cutoff = _utc(row["target_as_of_at"])
        require(cutoff == kickoff - pd.Timedelta(days=7), f"prospective T-7 cutoff drift event={event_id}")
        require(cutoff <= as_of_by_id[event_id], f"prospective anchor from future event={event_id}")
        cap = int(event["stadium_capacity"])
        p50 = float(row["prior_p50"])
        require(0.0 <= p50 <= cap, f"prospective anchor outside capacity event={event_id}")
        anchors.append({
            "ticket_event_id": event_id,
            "kickoff_at": kickoff.isoformat(),
            "target_as_of_at": cutoff.isoformat(),
            "p50": p50,
            "stadium_capacity": cap,
            "prior_model_spec_id": row.get("prior_model_spec_id"),
            "artifact_version": row.get("artifact_version"),
            "anchor_evidence_class": "prospective_pre_target_replay",
            "persisted_with_prediction": True,
        })

    core = {
        "version": "p7-long168-prospective-anchor-v1",
        "status": "READY",
        "event_ids": event_ids,
        "anchors": anchors,
        "lineage": lineage,
        "target_values_used": False,
        "production_change": False,
    }
    return {**core, "package_sha256": _sha(core)}


def _prospective_frame(selected_rows: list[dict[str, Any]], prospective: dict[str, Any], anchor_package: dict[str, Any]) -> pd.DataFrame:
    events = {int(row["ticket_event_id"]): row for row in prospective.get("events") or []}
    anchors = {int(row["ticket_event_id"]): row for row in anchor_package.get("anchors") or []}
    records = []
    for row in selected_rows:
        event_id = int(row["ticket_event_id"])
        event = events[event_id]
        anchor = anchors[event_id]
        features = dict(row.get("features") or {})
        record: dict[str, Any] = {
            "ticket_event_id": event_id,
            "requested_snapshot_id": int(row["requested_snapshot_id"]),
            "as_of_at": _utc(row["requested_as_of_at"]),
            "target_at": _utc(event["kickoff_at"]),
            "hours_to_kickoff": float(row["hours_to_kickoff"]),
            "bucket_6h": int(row["bucket_6h"]),
            "stadium_capacity": int(event["stadium_capacity"]),
            "anchor_p50": float(anchor["p50"]),
        }
        require(int(anchor["stadium_capacity"]) == record["stadium_capacity"], f"prospective anchor capacity drift event={event_id}")
        for feature in FEATURE_ALLOWLIST:
            value = row.get(feature) if feature in row else features.get(feature)
            if feature == "hours_to_kickoff":
                value = row["hours_to_kickoff"]
            record[feature] = _numeric_feature(value, feature)
        records.append(record)
    return pd.DataFrame(records)


def build(bundle: dict[str, Any], artifact_dir: Path, mode: str) -> dict[str, Any]:
    require(bundle.get("version") == "p7-long168-prospective-bundle-v1", "unexpected prospective bundle version")
    require(bundle.get("prospectiveTargetValuesUsed") is False, "prospective target values used upstream")
    for key, expected in (
        ("trainingEvents", EXPECTED_EVENTS_VERSION),
        ("attendance", EXPECTED_ATTENDANCE_VERSION),
        ("sporting", EXPECTED_SPORTING_VERSION),
        ("aliases", EXPECTED_ALIASES_VERSION),
    ):
        require(bundle[key].get("version") == expected, f"unexpected {key} version")

    model, fingerprint, fingerprint_payload, freeze, training_anchor, training_frame = _fit_frozen_model(bundle, artifact_dir)
    selected_rows = _latest_prospective_rows(bundle["prospective"])
    prospective_anchor = _prospective_anchor_package(bundle, selected_rows, artifact_dir)

    result: dict[str, Any] = {
        "version": VERSION,
        "mode": mode,
        "candidate_id": CANDIDATE_ID,
        "training_event_ids": TRAINING_EVENT_IDS,
        "training_row_count": int(len(training_frame)),
        "training_freeze_manifest_sha256": freeze["manifest_sha256"],
        "source_scorecard_sha256": SOURCE_SCORECARD_SHA256,
        "model_fingerprint_sha256": fingerprint,
        "model_fingerprint_contract_sha256": _sha(fingerprint_payload),
        "prospective_anchor_package_sha256": prospective_anchor["package_sha256"],
        "eligible_event_ids": [int(row["ticket_event_id"]) for row in selected_rows],
        "eligible_prediction_count": len(selected_rows),
        "bootstrap_backfill_performed": False,
        "target_values_used": False,
        "production_activation_allowed": False,
        "live_adjustment": 0,
        "production_change": False,
        "predictions": [],
    }

    if mode == "fingerprint":
        return result

    require(EXPECTED_MODEL_FINGERPRINT_SHA256 is not None, "MODEL_FINGERPRINT_NOT_PINNED: run fingerprint mode first")
    require(fingerprint == EXPECTED_MODEL_FINGERPRINT_SHA256, f"model fingerprint drift expected={EXPECTED_MODEL_FINGERPRINT_SHA256} observed={fingerprint}")
    if not selected_rows:
        return result

    frame = _prospective_frame(selected_rows, bundle["prospective"], prospective_anchor)
    residual = model.predict(frame[list(FEATURE_ALLOWLIST)])
    challenger = np.clip(frame["anchor_p50"].to_numpy(dtype=float) + residual, 0.0, frame["stadium_capacity"].to_numpy(dtype=float))
    source_payload_sha = _sha(bundle["prospective"])
    predictions = []
    for idx, row in frame.iterrows():
        identity_core = {
            "ticket_event_id": int(row["ticket_event_id"]),
            "requested_snapshot_id": int(row["requested_snapshot_id"]),
            "as_of_at": row["as_of_at"].isoformat(),
            "candidate_id": CANDIDATE_ID,
            "model_fingerprint_sha256": fingerprint,
            "training_freeze_manifest_sha256": EXPECTED_FREEZE_MANIFEST_SHA256,
            "prospective_anchor_package_sha256": prospective_anchor["package_sha256"],
        }
        predictions.append({
            "ticket_event_id": int(row["ticket_event_id"]),
            "requested_snapshot_id": int(row["requested_snapshot_id"]),
            "as_of_at": row["as_of_at"].isoformat(),
            "target_at": row["target_at"].isoformat(),
            "hours_to_kickoff": float(row["hours_to_kickoff"]),
            "bucket_6h": int(row["bucket_6h"]),
            "stadium_capacity": int(row["stadium_capacity"]),
            "anchor_p50": float(row["anchor_p50"]),
            "challenger_p50": float(challenger[idx]),
            "candidate_id": CANDIDATE_ID,
            "training_freeze_manifest_sha256": EXPECTED_FREEZE_MANIFEST_SHA256,
            "source_scorecard_sha256": SOURCE_SCORECARD_SHA256,
            "model_fingerprint_sha256": fingerprint,
            "prospective_anchor_package_sha256": prospective_anchor["package_sha256"],
            "source_payload_sha256": source_payload_sha,
            "prediction_identity_sha256": _sha(identity_core),
            "source_version": VERSION,
        })
    result["predictions"] = predictions
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("fingerprint", "predict"), required=True)
    args = parser.parse_args()

    bundle = json.loads(args.bundle.read_text())
    result = build(bundle, args.artifact_dir, args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
