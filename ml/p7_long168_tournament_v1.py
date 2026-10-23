#!/usr/bin/env python3
"""Execute the precommitted P7 Long168 fixed challenger tournament.

This code is intentionally unusable before a valid >=9-event identity freeze.
The source Long168 payload is re-frozen and must exactly reproduce the supplied
manifest before labels are read. The historical T-7 anchor package must also
match the frozen event set and be explicitly classified as historical PIT
replay rather than a persisted forecast.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from ml.mae_delta_uncertainty_v1 import BootstrapConfig, bootstrap_delta_mae, paired_event_errors
from ml.p7_long168_anchor_replay_v1 import ANCHOR_EVIDENCE_CLASS, VERSION as ANCHOR_VERSION
from ml.p7_long168_harness_v1 import FEATURE_ALLOWLIST, MIN_FORWARD_TRAIN_EVENTS, VERSION as HARNESS_VERSION, freeze_manifest
from ml.temporal_validation_v1 import build_forward_event_folds, fold_manifest

VERSION = "p7-long168-tournament-v1"
ANCHOR_ID = "anchor-only-t7"
QLIN_ID = "q50-linear-residual-a002"
GBR_ID = "gbr-l1-depth2-n50-lr003"
CANDIDATES = (ANCHOR_ID, QLIN_ID, GBR_ID)
EXPECTED_EVENTS_VERSION = "c1-alpha-v7-events-v1"
BOOLEAN_FEATURES = {
    "data_gap_detected",
    "release_activity_flag",
    "unexplained_inventory_increase_flag",
}
BANDS = (
    ("72_96", 72.0, 96.0),
    ("96_120", 96.0, 120.0),
    ("120_144", 120.0, 144.0),
    ("144_168", 144.0, 168.0),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate_freeze(long168: dict[str, Any], supplied: dict[str, Any]) -> dict[str, Any]:
    require(supplied.get("version") == HARNESS_VERSION, "unexpected P7 freeze version")
    require(supplied.get("status") == "P7_LONG168_IDENTITIES_FROZEN", "P7 identities are not frozen")
    recomputed = freeze_manifest(long168)
    require(
        supplied.get("manifest_sha256") == recomputed.get("manifest_sha256"),
        "P7 freeze SHA does not reproduce from Long168 source",
    )
    require(supplied.get("identities") == recomputed.get("identities"), "P7 frozen identity drift")
    return recomputed


def _validate_anchor(anchor: dict[str, Any], freeze: dict[str, Any]) -> dict[int, dict[str, Any]]:
    require(anchor.get("version") == ANCHOR_VERSION, "unexpected P7 anchor package version")
    require(anchor.get("status") == "P7_T7_ANCHOR_REPLAY_READY", "P7 T-7 anchor package not ready")
    require(anchor.get("anchor_evidence_class") == ANCHOR_EVIDENCE_CLASS, "P7 anchor evidence class drift")
    require(anchor.get("persisted_forecast") is False, "historical P7 replay must not claim persisted forecast")
    require(anchor.get("model_training_performed") is False, "anchor package unexpectedly trained a model")
    require(anchor.get("target_attendance_invariance", {}).get("status") == "PASS", "target-attendance invariance gate not passed")

    frozen_ids = [int(value) for value in freeze["event_ids"]]
    require(sorted(int(value) for value in anchor.get("event_ids") or []) == sorted(frozen_ids), "anchor event set != frozen P7 event set")
    anchors = {int(row["ticket_event_id"]): row for row in anchor.get("anchors") or []}
    require(sorted(anchors) == sorted(frozen_ids), "missing/extra P7 anchors")
    require(len(anchors) == int(anchor.get("anchor_count") or -1), "anchor_count mismatch")
    return anchors


def _labels(events_payload: dict[str, Any], frozen_ids: list[int]) -> tuple[dict[int, float], dict[int, int]]:
    require(events_payload.get("version") == EXPECTED_EVENTS_VERSION, "unexpected P7 label event export version")
    rows = {int(row["ticket_event_id"]): row for row in events_payload.get("events") or []}
    missing = sorted(set(frozen_ids) - set(rows))
    require(not missing, f"P7 labels missing frozen events: {missing}")
    actual: dict[int, float] = {}
    capacity: dict[int, int] = {}
    for event_id in frozen_ids:
        row = rows[event_id]
        value = float(row["actual_attendance"])
        cap = int(row["stadium_capacity"])
        require(np.isfinite(value) and 0.0 <= value <= cap, f"invalid P7 label/capacity event={event_id}")
        actual[event_id] = value
        capacity[event_id] = cap
    return actual, capacity


def _numeric_feature(value: Any, feature: str) -> float:
    if value is None:
        return np.nan
    if feature in BOOLEAN_FEATURES:
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return 1.0
            if lowered in {"false", "0", "no"}:
                return 0.0
        return float(bool(value))
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def _build_frame(
    *,
    long168: dict[str, Any],
    freeze: dict[str, Any],
    anchors: dict[int, dict[str, Any]],
    actual: dict[int, float],
    capacities: dict[int, int],
) -> pd.DataFrame:
    source_rows = {
        (
            int(row["ticket_event_id"]),
            pd.Timestamp(row["requested_as_of_at"]).isoformat(),
            int(row["requested_snapshot_id"]),
            int(row["bucket_6h"]),
        ): row
        for row in long168.get("liveRows") or []
    }
    records: list[dict[str, Any]] = []
    for identity in freeze["identities"]:
        key = (
            int(identity["ticket_event_id"]),
            pd.Timestamp(identity["requested_as_of_at"]).isoformat(),
            int(identity["requested_snapshot_id"]),
            int(identity["bucket_6h"]),
        )
        row = source_rows.get(key)
        require(row is not None, f"frozen Long168 identity missing from source: {key}")
        event_id = key[0]
        f = dict(row.get("features") or {})
        anchor = anchors[event_id]
        kickoff = pd.Timestamp(identity["kickoff_at"])
        if kickoff.tzinfo is None:
            kickoff = kickoff.tz_localize("UTC")
        else:
            kickoff = kickoff.tz_convert("UTC")
        as_of = pd.Timestamp(identity["requested_as_of_at"])
        if as_of.tzinfo is None:
            as_of = as_of.tz_localize("UTC")
        else:
            as_of = as_of.tz_convert("UTC")
        anchor_cutoff = pd.Timestamp(anchor["target_as_of_at"])
        if anchor_cutoff.tzinfo is None:
            anchor_cutoff = anchor_cutoff.tz_localize("UTC")
        else:
            anchor_cutoff = anchor_cutoff.tz_convert("UTC")
        require(anchor_cutoff <= as_of, f"future anchor leakage event={event_id}")
        require(int(anchor["stadium_capacity"]) == capacities[event_id], f"anchor/label capacity mismatch event={event_id}")

        record: dict[str, Any] = {
            "ticket_event_id": event_id,
            "kickoff_at": kickoff,
            "as_of_at": as_of,
            "requested_snapshot_id": key[2],
            "bucket_6h": key[3],
            "hours_to_kickoff": float(identity["hours_to_kickoff"]),
            "actual_attendance": actual[event_id],
            "stadium_capacity": capacities[event_id],
            "anchor_p50": float(anchor["p50"]),
        }
        for feature in FEATURE_ALLOWLIST:
            value = row.get(feature) if feature in row else f.get(feature)
            if feature == "hours_to_kickoff":
                value = identity["hours_to_kickoff"]
            record[feature] = _numeric_feature(value, feature)
        records.append(record)

    frame = pd.DataFrame(records).sort_values(["kickoff_at", "ticket_event_id", "as_of_at"]).reset_index(drop=True)
    require(frame["ticket_event_id"].nunique() == len(freeze["event_ids"]), "P7 frame event count drift")
    require(not frame[["actual_attendance", "anchor_p50", "stadium_capacity"]].isna().any().any(), "P7 frame missing target/anchor/capacity")
    frame["target_residual"] = frame["actual_attendance"] - frame["anchor_p50"]
    return frame


def _event_weights(frame: pd.DataFrame) -> np.ndarray:
    counts = frame.groupby("ticket_event_id")["ticket_event_id"].transform("count").astype(float)
    weights = 1.0 / counts.to_numpy()
    return weights / float(np.mean(weights))


def _qlin() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", RobustScaler()),
        ("model", QuantileRegressor(quantile=0.5, alpha=0.002, solver="highs")),
    ])


def _gbr() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("model", GradientBoostingRegressor(
            loss="absolute_error",
            n_estimators=50,
            learning_rate=0.03,
            max_depth=2,
            min_samples_leaf=4,
            random_state=42,
        )),
    ])


def _candidate_model(candidate_id: str) -> Pipeline:
    if candidate_id == QLIN_ID:
        return _qlin()
    if candidate_id == GBR_ID:
        return _gbr()
    raise ValueError(f"unknown learned P7 candidate: {candidate_id}")


def _event_level(frame: pd.DataFrame, prediction_col: str) -> pd.DataFrame:
    work = frame.copy()
    work["error"] = work[prediction_col] - work["actual_attendance"]
    work["absolute_error"] = work["error"].abs()
    return (
        work.groupby("ticket_event_id", sort=True)
        .agg(
            mae=("absolute_error", "mean"),
            bias=("error", "mean"),
            row_count=("absolute_error", "size"),
        )
        .reset_index()
    )


def _summary(frame: pd.DataFrame, prediction_col: str) -> dict[str, Any]:
    event = _event_level(frame, prediction_col)
    return {
        "independent_event_count": int(len(event)),
        "row_count": int(len(frame)),
        "event_balanced_mae": float(event["mae"].mean()),
        "event_median_ae": float(event["mae"].median()),
        "event_p90_ae": float(event["mae"].quantile(0.90)),
        "event_balanced_bias": float(event["bias"].mean()),
    }


def _band_metrics(frame: pd.DataFrame, prediction_col: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    h = frame["hours_to_kickoff"].astype(float)
    for band_id, lower, upper in BANDS:
        mask = (h > lower) & (h <= upper)
        band = frame[mask]
        result[band_id] = None if band.empty else _summary(band, prediction_col)
    return result


def _uncertainty(paired: pd.DataFrame, challenger_col: str) -> dict[str, Any]:
    errors = paired_event_errors(
        paired,
        event_col="ticket_event_id",
        actual_col="actual_attendance",
        incumbent_col="anchor_prediction",
        challenger_col=challenger_col,
    )
    return bootstrap_delta_mae(
        errors,
        config=BootstrapConfig(n_resamples=5000, seed=42),
    )


def run_tournament(
    *,
    long168: dict[str, Any],
    freeze: dict[str, Any],
    anchor: dict[str, Any],
    events_payload: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame, dict[str, Any]]:
    # CRITICAL ORDER: identity freeze and anchor integrity are verified before
    # actual attendance labels are read from the events support payload.
    reproduced_freeze = _validate_freeze(long168, freeze)
    anchors = _validate_anchor(anchor, reproduced_freeze)
    frozen_ids = [int(value) for value in reproduced_freeze["event_ids"]]

    actual, capacities = _labels(events_payload, frozen_ids)
    frame = _build_frame(
        long168=long168,
        freeze=reproduced_freeze,
        anchors=anchors,
        actual=actual,
        capacities=capacities,
    )
    folds = build_forward_event_folds(
        frame,
        entity_col="ticket_event_id",
        time_col="kickoff_at",
        min_train_entities=MIN_FORWARD_TRAIN_EVENTS,
    )
    require(len(folds) >= 2, f"P7_INSUFFICIENT_FORWARD_FOLDS: {len(folds)}")
    manifest = fold_manifest(
        folds,
        protocol_id="p7-long168-strict-forward-event-v1",
        source_id=reproduced_freeze["manifest_sha256"],
    )

    feature_cols = list(FEATURE_ALLOWLIST)
    predictions: list[pd.DataFrame] = []
    fold_scores: list[dict[str, Any]] = []

    for fold in folds:
        train_ids = {int(value) for value in fold.train_entities}
        test_ids = {int(value) for value in fold.test_entities}
        train = frame[frame["ticket_event_id"].isin(train_ids)].copy()
        test = frame[frame["ticket_event_id"].isin(test_ids)].copy()
        require(not train.empty and not test.empty, f"empty P7 fold {fold.fold_id}")

        base = test[[
            "ticket_event_id", "kickoff_at", "as_of_at", "requested_snapshot_id", "bucket_6h",
            "hours_to_kickoff", "actual_attendance", "stadium_capacity", "anchor_p50",
        ]].copy()
        base["fold_id"] = fold.fold_id
        base["candidate_id"] = ANCHOR_ID
        base["forecast_p50"] = base["anchor_p50"]
        predictions.append(base)
        anchor_mae = _summary(base.rename(columns={"forecast_p50": "prediction"}), "prediction")["event_balanced_mae"]

        fold_entry: dict[str, Any] = {
            "fold_id": fold.fold_id,
            "train_event_count": len(train_ids),
            "test_event_ids": sorted(test_ids),
            "anchor_event_balanced_mae": anchor_mae,
            "candidates": {},
        }
        weights = _event_weights(train)

        for candidate_id in (QLIN_ID, GBR_ID):
            model = _candidate_model(candidate_id)
            model.fit(
                train[feature_cols],
                train["target_residual"],
                model__sample_weight=weights,
            )
            residual = np.asarray(model.predict(test[feature_cols]), dtype=float)
            prediction = np.clip(
                test["anchor_p50"].to_numpy(dtype=float) + residual,
                0.0,
                test["stadium_capacity"].to_numpy(dtype=float),
            )
            out = base.drop(columns=["candidate_id", "forecast_p50"]).copy()
            out["candidate_id"] = candidate_id
            out["forecast_p50"] = prediction
            predictions.append(out)
            candidate_mae = _summary(out.rename(columns={"forecast_p50": "prediction"}), "prediction")["event_balanced_mae"]
            fold_entry["candidates"][candidate_id] = {
                "event_balanced_mae": candidate_mae,
                "delta_mae": candidate_mae - anchor_mae,
                "improved": candidate_mae < anchor_mae,
            }
        fold_scores.append(fold_entry)

    pred = pd.concat(predictions, ignore_index=True)
    anchor_pred = pred[pred["candidate_id"] == ANCHOR_ID].copy()
    require(not anchor_pred.empty, "P7 anchor predictions missing")
    anchor_summary = _summary(anchor_pred.rename(columns={"forecast_p50": "prediction"}), "prediction")

    candidate_results: dict[str, Any] = {}
    for candidate_id in (QLIN_ID, GBR_ID):
        challenger = pred[pred["candidate_id"] == candidate_id].copy()
        paired = anchor_pred[[
            "ticket_event_id", "as_of_at", "requested_snapshot_id", "actual_attendance", "forecast_p50",
        ]].rename(columns={"forecast_p50": "anchor_prediction"}).merge(
            challenger[["ticket_event_id", "as_of_at", "requested_snapshot_id", "forecast_p50"]].rename(
                columns={"forecast_p50": "challenger_prediction"}
            ),
            on=["ticket_event_id", "as_of_at", "requested_snapshot_id"],
            how="inner",
            validate="one_to_one",
        )
        require(len(paired) == len(anchor_pred) == len(challenger), f"paired P7 prediction identity drift {candidate_id}")
        summary = _summary(challenger.rename(columns={"forecast_p50": "prediction"}), "prediction")
        event_anchor = _event_level(anchor_pred.rename(columns={"forecast_p50": "prediction"}), "prediction").rename(columns={"mae": "anchor_mae"})
        event_chal = _event_level(challenger.rename(columns={"forecast_p50": "prediction"}), "prediction").rename(columns={"mae": "challenger_mae"})
        event_cmp = event_anchor[["ticket_event_id", "anchor_mae"]].merge(
            event_chal[["ticket_event_id", "challenger_mae"]], on="ticket_event_id", validate="one_to_one"
        )
        event_cmp["delta"] = event_cmp["challenger_mae"] - event_cmp["anchor_mae"]
        fold_rows = [row["candidates"][candidate_id] for row in fold_scores]
        uncertainty = _uncertainty(paired, "challenger_prediction")
        delta = summary["event_balanced_mae"] - anchor_summary["event_balanced_mae"]
        event_rate = float((event_cmp["delta"] < 0.0).mean())
        fold_rate = float(np.mean([bool(row["improved"]) for row in fold_rows]))
        worst_degradation = float(event_cmp["delta"].max())
        ci_upper = float(uncertainty["bootstrap"]["delta_mae_upper"])
        if delta >= 0.0:
            evidence = "NO_MAE_GAIN"
        elif ci_upper < 0.0:
            evidence = "SUPPORTED_HISTORICAL_FORWARD_GAIN"
        else:
            evidence = "POINT_GAIN_UNCERTAINTY_LIMITED"
        candidate_results[candidate_id] = {
            "summary": summary,
            "delta_mae_vs_anchor": delta,
            "relative_delta_mae_vs_anchor": delta / anchor_summary["event_balanced_mae"],
            "event_improvement_rate": event_rate,
            "forward_fold_improvement_rate": fold_rate,
            "worst_event_degradation": worst_degradation,
            "horizon_bands": _band_metrics(challenger.rename(columns={"forecast_p50": "prediction"}), "prediction"),
            "uncertainty": uncertainty,
            "evidence_interpretation": evidence,
            "passes_precommitted_research_advance_rule": bool(delta < 0.0 and event_rate > 0.5 and fold_rate > 0.5),
        }

    best_id = min(candidate_results, key=lambda key: candidate_results[key]["summary"]["event_balanced_mae"])
    best = candidate_results[best_id]
    decision = "ADVANCE_RESEARCH" if best["passes_precommitted_research_advance_rule"] else "RETAIN_ANCHOR"

    core = {
        "version": VERSION,
        "status": "P7_LONG168_TOURNAMENT_COMPLETE",
        "evidence_class": "historical_forward_fold",
        "production_change": False,
        "production_activation_allowed": False,
        "live_adjustment": 0,
        "freeze_manifest_sha256": reproduced_freeze["manifest_sha256"],
        "anchor_package_sha256": anchor.get("package_sha256"),
        "anchor_evidence_class": anchor.get("anchor_evidence_class"),
        "candidate_ids": list(CANDIDATES),
        "feature_allowlist": list(FEATURE_ALLOWLIST),
        "independent_frozen_event_count": len(frozen_ids),
        "forward_test_event_count": int(anchor_summary["independent_event_count"]),
        "fold_count": len(folds),
        "fold_manifest_sha256": manifest["folds_sha256"],
        "anchor": {
            "summary": anchor_summary,
            "horizon_bands": _band_metrics(anchor_pred.rename(columns={"forecast_p50": "prediction"}), "prediction"),
        },
        "candidates": candidate_results,
        "fold_scores": fold_scores,
        "best_learned_candidate": best_id,
        "decision": decision,
        "decision_basis": {
            "primary": "strict-forward event-balanced MAE",
            "required_event_improvement_rate": ">0.5",
            "required_forward_fold_improvement_rate": ">0.5",
            "uncertainty_required": True,
            "production_promotion_from_p7_v1": False,
        },
    }
    scorecard = {**core, "scorecard_sha256": _canonical_sha(core)}
    return scorecard, pred.sort_values(["fold_id", "candidate_id", "ticket_event_id", "as_of_at"]).reset_index(drop=True), manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--long168", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--anchor", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--scorecard", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--fold-manifest", type=Path, required=True)
    args = parser.parse_args()

    scorecard, predictions, manifest = run_tournament(
        long168=json.loads(args.long168.read_text()),
        freeze=json.loads(args.freeze.read_text()),
        anchor=json.loads(args.anchor.read_text()),
        events_payload=json.loads(args.events.read_text()),
    )
    args.scorecard.parent.mkdir(parents=True, exist_ok=True)
    args.predictions.parent.mkdir(parents=True, exist_ok=True)
    args.fold_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.scorecard.write_text(json.dumps(scorecard, indent=2, sort_keys=True) + "\n")
    predictions.to_csv(args.predictions, index=False)
    args.fold_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": scorecard["status"],
        "decision": scorecard["decision"],
        "independent_frozen_event_count": scorecard["independent_frozen_event_count"],
        "forward_test_event_count": scorecard["forward_test_event_count"],
        "fold_count": scorecard["fold_count"],
        "anchor_mae": scorecard["anchor"]["summary"]["event_balanced_mae"],
        "best_learned_candidate": scorecard["best_learned_candidate"],
        "best_candidate": scorecard["candidates"][scorecard["best_learned_candidate"]],
        "scorecard_sha256": scorecard["scorecard_sha256"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
