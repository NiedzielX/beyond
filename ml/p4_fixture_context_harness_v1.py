#!/usr/bin/env python3
"""P4a fixture-context precommit harness v1.

Research question:
    Does previous-home match spacing reduce event-level attendance MAE beyond
    the frozen Long72 pre-live T3+B2 anchor?

The input payload is deliberately target-free. Exact event/context/anchor
identities are frozen before a separate labels payload may be attached.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from ml.mae_delta_uncertainty_v1 import BootstrapConfig, bootstrap_delta_mae, paired_event_errors
from ml.temporal_validation_v1 import build_forward_event_folds, fold_manifest

VERSION = "p4-fixture-context-harness-v1"
INPUT_VERSION = "p4-fixture-context-inputs-v1"
LABEL_VERSION = "p4-fixture-context-labels-v1"
PRIMARY_FEATURE = "previous_home_match_days"
ANCHOR_ID = "long72-prelive-t3-b2-anchor"
CHALLENGER_ID = "q50-linear-prev-home-spacing-a002"
MIN_LABELED_EVENTS = 9
MIN_DISTINCT_VALUES = 3
MIN_FORWARD_TRAIN_EVENTS = 5
TARGET_KEYS = {
    "actual_attendance",
    "attendance",
    "target",
    "label",
    "outcome",
    "p2_mae",
    "anchor_mae",
}
INACTIVE_FEATURES = (
    "next_home_match_days",
    "team_fixture_density_next_7d",
    "team_fixture_density_next_14d",
    "team_fixture_density_next_30d",
    "home_fixture_density_next_7d",
    "home_fixture_density_next_14d",
    "home_fixture_density_next_30d",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _walk_for_targets(value: Any, path: str = "root") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in TARGET_KEYS or "actual_attendance" in lowered:
                hits.append(f"{path}.{key}")
            hits.extend(_walk_for_targets(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(_walk_for_targets(child, f"{path}[{idx}]") )
    return hits


def _utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def validate_inputs(payload: dict[str, Any]) -> list[dict[str, Any]]:
    require(payload.get("version") == INPUT_VERSION, f"unexpected input version: {payload.get('version')}")
    require(payload.get("independentUnit") == "ticket_event", "P4a independent unit must be ticket_event")
    require(payload.get("primaryFeature") == PRIMARY_FEATURE, "P4a primary feature drift")
    require(payload.get("targetFieldsIncluded") is False, "P4a input claims target fields are present")
    require(payload.get("labelsIncluded") is False, "P4a input claims labels are present")
    hits = _walk_for_targets(payload)
    require(not hits, f"P4A_TARGET_LEAKAGE: {hits[:5]}")
    rows = list(payload.get("events") or [])
    require(int(payload.get("eventCount") or 0) == len(rows), "P4a input eventCount mismatch")
    require(len(rows) == len({int(row["ticket_event_id"]) for row in rows}), "duplicate P4a ticket_event_id")
    for row in rows:
        require(row.get(PRIMARY_FEATURE) is not None, f"missing {PRIMARY_FEATURE} event={row.get('ticket_event_id')}")
        require(row.get("anchor_p50") is not None, f"missing anchor_p50 event={row.get('ticket_event_id')}")
        require(row.get("kickoff_at") is not None, f"missing kickoff event={row.get('ticket_event_id')}")
        require(row.get("forecast_as_of_at") is not None, f"missing forecast_as_of event={row.get('ticket_event_id')}")
        require(_utc(row["forecast_as_of_at"]) < _utc(row["kickoff_at"]), f"non-PIT context event={row.get('ticket_event_id')}")
        capacity = float(row["stadium_capacity"])
        anchor = float(row["anchor_p50"])
        require(0.0 <= anchor <= capacity, f"anchor outside capacity event={row.get('ticket_event_id')}")
    return sorted(rows, key=lambda row: (str(row["kickoff_at"]), int(row["ticket_event_id"])))


def contract() -> dict[str, Any]:
    return {
        "version": VERSION,
        "research_question": "Does previous-home match spacing reduce event-level attendance MAE beyond the frozen Long72 pre-live T3+B2 anchor?",
        "independent_unit": "ticket_event",
        "selection_rule": "first READY fixture-context row per reproducible Long72 event",
        "anchor": {
            "id": ANCHOR_ID,
            "definition": "frozen Long72 pre-live T3 Structural Prior plus frozen B2 current-season correction",
        },
        "primary_feature": PRIMARY_FEATURE,
        "inactive_features": list(INACTIVE_FEATURES),
        "research_start_gate": {
            "minimum_labeled_events": MIN_LABELED_EVENTS,
            "minimum_distinct_primary_feature_values": MIN_DISTINCT_VALUES,
            "purpose": "research start only; not promotion sufficiency",
        },
        "candidate_family": [
            {"candidate_id": ANCHOR_ID, "type": "control"},
            {
                "candidate_id": CHALLENGER_ID,
                "type": "anchor residual correction",
                "estimator": "QuantileRegressor",
                "quantile": 0.5,
                "alpha": 0.002,
                "scaler": "RobustScaler",
                "feature": PRIMARY_FEATURE,
            },
        ],
        "validation": {
            "type": "strict_forward_event",
            "min_train_events": MIN_FORWARD_TRAIN_EVENTS,
            "random_split_allowed": False,
        },
        "primary_metric": "event_level_mae",
        "uncertainty": {"method": "paired_event_block_bootstrap", "n_resamples": 5000, "seed": 42},
        "advance_rule": {
            "mae_below_anchor": True,
            "event_improvement_rate": ">0.5",
            "forward_fold_improvement_rate": ">0.5",
        },
        "production": {"promotion_allowed_from_p4a_v1": False, "live_adjustment": 0},
    }


def freeze_manifest(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = validate_inputs(inputs)
    identities = [
        {
            "ticket_event_id": int(row["ticket_event_id"]),
            "context_id": int(row["context_id"]),
            "forward_prediction_id": int(row["forward_prediction_id"]),
            "source_prior_id": int(row["source_prior_id"]),
            "forecast_as_of_at": _utc(row["forecast_as_of_at"]).isoformat(),
            "kickoff_at": _utc(row["kickoff_at"]).isoformat(),
            "schedule_batch_id": int(row["schedule_batch_id"]),
            "stadium_capacity": int(row["stadium_capacity"]),
            "anchor_p50": float(row["anchor_p50"]),
            PRIMARY_FEATURE: float(row[PRIMARY_FEATURE]),
        }
        for row in rows
    ]
    core = {
        "version": VERSION,
        "status": "P4A_FIXTURE_CONTEXT_IDENTITIES_FROZEN",
        "production_change": False,
        "target_values_opened": False,
        "model_training_performed": False,
        "event_count": len(identities),
        "event_ids": [row["ticket_event_id"] for row in identities],
        "distinct_primary_feature_values": len({row[PRIMARY_FEATURE] for row in identities}),
        "identities": identities,
        "contract": contract(),
    }
    return {**core, "manifest_sha256": canonical_sha(core)}


def _validate_labels(labels: dict[str, Any]) -> dict[int, dict[str, Any]]:
    require(labels.get("version") == LABEL_VERSION, f"unexpected label version: {labels.get('version')}")
    rows = list(labels.get("labels") or [])
    require(int(labels.get("eventCount") or 0) == len(rows), "P4a label eventCount mismatch")
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        event_id = int(row["ticket_event_id"])
        require(event_id not in result, f"duplicate P4a label event={event_id}")
        result[event_id] = row
    return result


def labeled_frame(inputs: dict[str, Any], frozen: dict[str, Any], labels: dict[str, Any]) -> pd.DataFrame:
    reproduced = freeze_manifest(inputs)
    require(frozen.get("status") == "P4A_FIXTURE_CONTEXT_IDENTITIES_FROZEN", "P4a identities are not frozen")
    require(frozen.get("manifest_sha256") == reproduced.get("manifest_sha256"), "P4A_FREEZE_DRIFT")
    require(frozen.get("identities") == reproduced.get("identities"), "P4A_IDENTITY_DRIFT")

    label_by_id = _validate_labels(labels)
    rows: list[dict[str, Any]] = []
    for identity in reproduced["identities"]:
        event_id = int(identity["ticket_event_id"])
        label = label_by_id.get(event_id)
        if label is None:
            continue
        actual = float(label["actual_attendance"])
        capacity = float(identity["stadium_capacity"])
        require(0.0 <= actual <= capacity, f"invalid attendance/capacity event={event_id}")
        rows.append({
            **identity,
            "actual_attendance": actual,
            "outcome_confirmed_at": label.get("outcome_confirmed_at"),
            "outcome_version_at": label.get("outcome_version_at"),
        })

    frame = pd.DataFrame(rows)
    require(len(frame) >= MIN_LABELED_EVENTS, f"P4A_NOT_READY: labeled_events={len(frame)} threshold={MIN_LABELED_EVENTS}")
    distinct = int(frame[PRIMARY_FEATURE].nunique())
    require(distinct >= MIN_DISTINCT_VALUES, f"P4A_NOT_READY: distinct_{PRIMARY_FEATURE}={distinct} threshold={MIN_DISTINCT_VALUES}")
    frame["kickoff_at"] = pd.to_datetime(frame["kickoff_at"], utc=True)
    frame["target_residual"] = frame["actual_attendance"] - frame["anchor_p50"]
    return frame.sort_values(["kickoff_at", "ticket_event_id"]).reset_index(drop=True)


def _model() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", RobustScaler()),
        ("model", QuantileRegressor(quantile=0.5, alpha=0.002, solver="highs")),
    ])


def _mae(frame: pd.DataFrame, prediction_col: str) -> float:
    return float(np.mean(np.abs(frame[prediction_col].to_numpy(float) - frame["actual_attendance"].to_numpy(float))))


def evaluate(inputs: dict[str, Any], frozen: dict[str, Any], labels: dict[str, Any]) -> tuple[dict[str, Any], pd.DataFrame, dict[str, Any]]:
    frame = labeled_frame(inputs, frozen, labels)
    folds = build_forward_event_folds(
        frame,
        entity_col="ticket_event_id",
        time_col="kickoff_at",
        min_train_entities=MIN_FORWARD_TRAIN_EVENTS,
    )
    require(len(folds) >= 2, f"P4A_INSUFFICIENT_FORWARD_FOLDS: {len(folds)}")
    manifest = fold_manifest(
        folds,
        protocol_id="p4a-fixture-context-strict-forward-event-v1",
        source_id=str(frozen["manifest_sha256"]),
    )

    outputs: list[pd.DataFrame] = []
    fold_scores: list[dict[str, Any]] = []
    for fold in folds:
        train_ids = {int(value) for value in fold.train_entities}
        test_ids = {int(value) for value in fold.test_entities}
        train = frame[frame["ticket_event_id"].isin(train_ids)].copy()
        test = frame[frame["ticket_event_id"].isin(test_ids)].copy()
        model = _model()
        model.fit(train[[PRIMARY_FEATURE]], train["target_residual"])
        residual = np.asarray(model.predict(test[[PRIMARY_FEATURE]]), dtype=float)
        prediction = np.clip(
            test["anchor_p50"].to_numpy(float) + residual,
            0.0,
            test["stadium_capacity"].to_numpy(float),
        )
        out = test[["ticket_event_id", "kickoff_at", PRIMARY_FEATURE, "anchor_p50", "actual_attendance"]].copy()
        out["challenger_p50"] = prediction
        out["fold_id"] = fold.fold_id
        outputs.append(out)
        anchor_mae = _mae(out.rename(columns={"anchor_p50": "prediction"}), "prediction")
        challenger_mae = _mae(out.rename(columns={"challenger_p50": "prediction"}), "prediction")
        fold_scores.append({
            "fold_id": fold.fold_id,
            "test_event_ids": sorted(test_ids),
            "anchor_mae": anchor_mae,
            "challenger_mae": challenger_mae,
            "delta_mae": challenger_mae - anchor_mae,
            "improved": challenger_mae < anchor_mae,
        })

    pred = pd.concat(outputs, ignore_index=True).sort_values(["kickoff_at", "ticket_event_id"]).reset_index(drop=True)
    anchor_mae = _mae(pred.rename(columns={"anchor_p50": "prediction"}), "prediction")
    challenger_mae = _mae(pred.rename(columns={"challenger_p50": "prediction"}), "prediction")
    pred["anchor_abs_error"] = (pred["anchor_p50"] - pred["actual_attendance"]).abs()
    pred["challenger_abs_error"] = (pred["challenger_p50"] - pred["actual_attendance"]).abs()
    pred["delta_abs_error"] = pred["challenger_abs_error"] - pred["anchor_abs_error"]

    paired = pred[["ticket_event_id", "actual_attendance", "anchor_p50", "challenger_p50"]].rename(
        columns={"anchor_p50": "anchor_prediction", "challenger_p50": "challenger_prediction"}
    )
    errors = paired_event_errors(
        paired,
        event_col="ticket_event_id",
        actual_col="actual_attendance",
        incumbent_col="anchor_prediction",
        challenger_col="challenger_prediction",
    )
    uncertainty = bootstrap_delta_mae(errors, config=BootstrapConfig(n_resamples=5000, seed=42))
    delta = challenger_mae - anchor_mae
    event_improvement_rate = float((pred["delta_abs_error"] < 0.0).mean())
    fold_improvement_rate = float(np.mean([row["improved"] for row in fold_scores]))
    advance = bool(delta < 0.0 and event_improvement_rate > 0.5 and fold_improvement_rate > 0.5)

    core = {
        "version": VERSION,
        "status": "P4A_FIXTURE_CONTEXT_EVALUATION_COMPLETE",
        "evidence_class": "true_post_freeze_prospective_context",
        "production_change": False,
        "production_activation_allowed": False,
        "live_adjustment": 0,
        "freeze_manifest_sha256": frozen["manifest_sha256"],
        "labeled_event_count": int(len(frame)),
        "distinct_primary_feature_values": int(frame[PRIMARY_FEATURE].nunique()),
        "forward_test_event_count": int(len(pred)),
        "fold_count": len(folds),
        "fold_manifest_sha256": manifest["folds_sha256"],
        "anchor_id": ANCHOR_ID,
        "challenger_id": CHALLENGER_ID,
        "anchor_mae": anchor_mae,
        "challenger_mae": challenger_mae,
        "delta_mae": delta,
        "event_improvement_rate": event_improvement_rate,
        "forward_fold_improvement_rate": fold_improvement_rate,
        "worst_event_degradation": float(pred["delta_abs_error"].max()),
        "uncertainty": uncertainty,
        "fold_scores": fold_scores,
        "decision": "ADVANCE_RESEARCH" if advance else "RETAIN_ANCHOR",
    }
    return {**core, "scorecard_sha256": canonical_sha(core)}, pred, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("contract", "freeze", "evaluate"), required=True)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--fold-manifest", type=Path)
    args = parser.parse_args()

    if args.mode == "contract":
        result = contract()
    elif args.mode == "freeze":
        require(args.inputs is not None, "--inputs required")
        result = freeze_manifest(json.loads(args.inputs.read_text()))
    else:
        require(args.inputs is not None and args.freeze is not None and args.labels is not None, "--inputs/--freeze/--labels required")
        scorecard, predictions, manifest = evaluate(
            json.loads(args.inputs.read_text()),
            json.loads(args.freeze.read_text()),
            json.loads(args.labels.read_text()),
        )
        result = scorecard
        require(args.predictions is not None and args.fold_manifest is not None, "--predictions/--fold-manifest required")
        args.predictions.parent.mkdir(parents=True, exist_ok=True)
        predictions.to_csv(args.predictions, index=False)
        args.fold_manifest.parent.mkdir(parents=True, exist_ok=True)
        args.fold_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
