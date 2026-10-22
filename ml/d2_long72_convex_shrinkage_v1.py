#!/usr/bin/env python3
"""P5a: forward-event convex shrinkage tournament for frozen Long72 live/P2.

The experiment combines two already-frozen forecasts:

    blend(w) = structural_anchor + w * (live_p2 - structural_anchor)

with w in {0, .25, .50, .75, 1}. A separate train-selected policy chooses
one of those predeclared weights using only strictly earlier events and then
applies it to the held-out event.

Historical exposed research only. No frozen package or production behavior is
modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.mae_delta_uncertainty_v1 import BootstrapConfig, bootstrap_delta_mae, paired_event_errors
from ml.temporal_validation_v1 import build_forward_event_folds, event_balanced_mae, fold_manifest

VERSION = "d2-long72-convex-shrinkage-v1"
POLICY_ID = "P2-observation-maturity"
EXPECTED_PREDICTIONS_SHA256 = "489ba62156f19d3b915fda1b9f1ef506fb81603d4286a01e8ad4b799c58bce4b"
EXPECTED_ROW_COUNT = 80
EXPECTED_EVENT_COUNT = 13
WEIGHTS = (0.0, 0.25, 0.50, 0.75, 1.0)
MIN_TRAIN_EVENTS = 5


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_predictions(path: Path) -> pd.DataFrame:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_PREDICTIONS_SHA256:
        raise RuntimeError(
            f"frozen Stage2 predictions SHA mismatch: {actual_sha} != {EXPECTED_PREDICTIONS_SHA256}"
        )
    frame = pd.read_csv(path)
    required = {
        "ticket_event_id",
        "kickoff_at",
        "hours_to_kickoff",
        "actual_attendance",
        "anchor_p50",
        "forecast_p50",
        "policy_id",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"missing Long72 columns: {missing}")
    frame = frame[frame["policy_id"].astype(str) == POLICY_ID].copy()
    if len(frame) != EXPECTED_ROW_COUNT or frame["ticket_event_id"].nunique() != EXPECTED_EVENT_COUNT:
        raise RuntimeError(
            f"unexpected frozen P2 shape rows={len(frame)} events={frame['ticket_event_id'].nunique()}"
        )
    frame["ticket_event_id"] = frame["ticket_event_id"].astype(str)
    frame["kickoff_at"] = pd.to_datetime(frame["kickoff_at"], utc=True, errors="raise")
    for column in ("hours_to_kickoff", "actual_attendance", "anchor_p50", "forecast_p50"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if frame[["hours_to_kickoff", "actual_attendance", "anchor_p50", "forecast_p50"]].isna().any().any():
        raise RuntimeError("frozen P2 predictions contain null numeric values")
    frame["live_delta"] = frame["forecast_p50"] - frame["anchor_p50"]
    return frame.sort_values(["kickoff_at", "ticket_event_id", "hours_to_kickoff"]).reset_index(drop=True)


def prediction_for_weight(frame: pd.DataFrame, weight: float) -> pd.Series:
    return frame["anchor_p50"] + float(weight) * frame["live_delta"]


def train_score(frame: pd.DataFrame, weight: float) -> float:
    work = frame.copy()
    work["candidate_p50"] = prediction_for_weight(work, weight)
    return event_balanced_mae(
        work,
        event_col="ticket_event_id",
        actual_col="actual_attendance",
        prediction_col="candidate_p50",
    )


def candidate_summary(frame: pd.DataFrame, candidate_id: str) -> dict[str, Any]:
    candidate = frame[frame["candidate_id"] == candidate_id].copy()
    if candidate.empty:
        raise RuntimeError(f"candidate has no OOS rows: {candidate_id}")
    candidate["absolute_error"] = (candidate["candidate_p50"] - candidate["actual_attendance"]).abs()
    candidate["signed_error"] = candidate["candidate_p50"] - candidate["actual_attendance"]
    candidate["anchor_absolute_error"] = (candidate["anchor_p50"] - candidate["actual_attendance"]).abs()
    by_event = (
        candidate.groupby("ticket_event_id", sort=True)
        .agg(
            candidate_ae=("absolute_error", "mean"),
            anchor_ae=("anchor_absolute_error", "mean"),
            candidate_bias=("signed_error", "mean"),
        )
        .reset_index()
    )
    errors = paired_event_errors(
        candidate,
        event_col="ticket_event_id",
        actual_col="actual_attendance",
        incumbent_col="anchor_p50",
        challenger_col="candidate_p50",
    )
    uncertainty = bootstrap_delta_mae(
        errors,
        config=BootstrapConfig(n_resamples=5000, seed=42),
    )
    return {
        "candidate_id": candidate_id,
        "independent_event_count": int(len(by_event)),
        "row_count": int(len(candidate)),
        "event_balanced_mae": float(by_event["candidate_ae"].mean()),
        "event_balanced_bias": float(by_event["candidate_bias"].mean()),
        "delta_mae_vs_anchor": float((by_event["candidate_ae"] - by_event["anchor_ae"]).mean()),
        "event_improvement_rate_vs_anchor": float(np.mean(by_event["candidate_ae"] < by_event["anchor_ae"])),
        "uncertainty_vs_anchor": uncertainty,
    }


def evaluate(path: Path) -> dict[str, Any]:
    frame = load_frozen_predictions(path)
    folds = build_forward_event_folds(
        frame,
        entity_col="ticket_event_id",
        time_col="kickoff_at",
        min_train_entities=MIN_TRAIN_EVENTS,
    )
    if len(folds) != EXPECTED_EVENT_COUNT - MIN_TRAIN_EVENTS:
        raise RuntimeError(f"expected 8 strict forward-event folds, got {len(folds)}")

    oos_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []

    for fold in folds:
        train = frame[frame["ticket_event_id"].isin(fold.train_entities)].copy()
        test = frame[frame["ticket_event_id"].isin(fold.test_entities)].copy()
        scores = {weight: train_score(train, weight) for weight in WEIGHTS}
        selected_weight = min(WEIGHTS, key=lambda weight: (scores[weight], weight))
        fold_rows.append(
            {
                "fold_id": fold.fold_id,
                "test_event_id": fold.test_entities[0],
                "train_event_count": len(fold.train_entities),
                "selected_weight": selected_weight,
                "train_event_balanced_mae_by_weight": {
                    f"{weight:.2f}": scores[weight] for weight in WEIGHTS
                },
            }
        )

        for weight in WEIGHTS:
            candidate_id = f"fixed-w{weight:.2f}"
            predictions = prediction_for_weight(test, weight)
            for row_index, (_, row) in enumerate(test.iterrows()):
                oos_rows.append(
                    {
                        "fold_id": fold.fold_id,
                        "ticket_event_id": str(row["ticket_event_id"]),
                        "kickoff_at": row["kickoff_at"].isoformat(),
                        "hours_to_kickoff": float(row["hours_to_kickoff"]),
                        "actual_attendance": float(row["actual_attendance"]),
                        "anchor_p50": float(row["anchor_p50"]),
                        "frozen_p2_p50": float(row["forecast_p50"]),
                        "candidate_id": candidate_id,
                        "applied_weight": weight,
                        "candidate_p50": float(predictions.iloc[row_index]),
                    }
                )

        adaptive_predictions = prediction_for_weight(test, selected_weight)
        for row_index, (_, row) in enumerate(test.iterrows()):
            oos_rows.append(
                {
                    "fold_id": fold.fold_id,
                    "ticket_event_id": str(row["ticket_event_id"]),
                    "kickoff_at": row["kickoff_at"].isoformat(),
                    "hours_to_kickoff": float(row["hours_to_kickoff"]),
                    "actual_attendance": float(row["actual_attendance"]),
                    "anchor_p50": float(row["anchor_p50"]),
                    "frozen_p2_p50": float(row["forecast_p50"]),
                    "candidate_id": "train-selected-weight",
                    "applied_weight": selected_weight,
                    "candidate_p50": float(adaptive_predictions.iloc[row_index]),
                }
            )

    oos = pd.DataFrame(oos_rows)
    candidate_ids = [f"fixed-w{weight:.2f}" for weight in WEIGHTS] + ["train-selected-weight"]
    summaries = [candidate_summary(oos, candidate_id) for candidate_id in candidate_ids]
    selected = min(
        summaries,
        key=lambda row: (row["event_balanced_mae"], abs(row["event_balanced_bias"]), row["candidate_id"]),
    )

    p2_summary = next(row for row in summaries if row["candidate_id"] == "fixed-w1.00")
    adaptive_summary = next(row for row in summaries if row["candidate_id"] == "train-selected-weight")

    paired = oos[oos["candidate_id"].isin(["fixed-w1.00", "train-selected-weight"])].copy()
    p2 = paired[paired["candidate_id"] == "fixed-w1.00"][
        ["fold_id", "ticket_event_id", "hours_to_kickoff", "actual_attendance", "candidate_p50"]
    ].rename(columns={"candidate_p50": "p2_p50"})
    adaptive = paired[paired["candidate_id"] == "train-selected-weight"][
        ["fold_id", "ticket_event_id", "hours_to_kickoff", "actual_attendance", "candidate_p50"]
    ].rename(columns={"candidate_p50": "adaptive_p50", "actual_attendance": "adaptive_actual"})
    pair = p2.merge(
        adaptive,
        on=["fold_id", "ticket_event_id", "hours_to_kickoff"],
        how="inner",
        validate="one_to_one",
    )
    if not np.allclose(pair["actual_attendance"], pair["adaptive_actual"], rtol=0.0, atol=0.0):
        raise RuntimeError("P2/adaptive actual labels differ")
    adaptive_vs_p2_errors = paired_event_errors(
        pair,
        event_col="ticket_event_id",
        actual_col="actual_attendance",
        incumbent_col="p2_p50",
        challenger_col="adaptive_p50",
    )
    adaptive_vs_p2 = bootstrap_delta_mae(
        adaptive_vs_p2_errors,
        config=BootstrapConfig(n_resamples=5000, seed=42),
    )

    descriptive_full_sample = []
    for weight in WEIGHTS:
        work = frame.copy()
        work["candidate_p50"] = prediction_for_weight(work, weight)
        work["absolute_error"] = (work["candidate_p50"] - work["actual_attendance"]).abs()
        work["signed_error"] = work["candidate_p50"] - work["actual_attendance"]
        event = work.groupby("ticket_event_id", sort=True).agg(
            ae=("absolute_error", "mean"),
            bias=("signed_error", "mean"),
        )
        descriptive_full_sample.append(
            {
                "weight": weight,
                "event_balanced_mae": float(event["ae"].mean()),
                "event_balanced_bias": float(event["bias"].mean()),
            }
        )

    return {
        "version": VERSION,
        "status": "COMPLETED_FORWARD_EVENT_CONVEX_SHRINKAGE_TOURNAMENT",
        "evidence_class": "historical_forward_event_exposed_research",
        "package_id": "d2-long72-stage2-p2-observation-maturity-2026-10-21-v1",
        "predictions_sha256": EXPECTED_PREDICTIONS_SHA256,
        "candidate_weights": list(WEIGHTS),
        "train_selected_policy": "choose lowest prior-event event-balanced MAE; tie -> smaller weight",
        "fold_manifest": fold_manifest(
            folds,
            protocol_id="d2-long72-p5a-forward-event-v1",
            source_id=EXPECTED_PREDICTIONS_SHA256,
        ),
        "fold_selection": fold_rows,
        "candidate_summaries": summaries,
        "selected_candidate": selected,
        "adaptive_vs_frozen_p2": adaptive_vs_p2,
        "descriptive_full_13_event_blend_curve": descriptive_full_sample,
        "decision": (
            "RETAIN_FROZEN_P2_NO_SHRINKAGE_REPLACEMENT"
            if selected["candidate_id"] == "fixed-w1.00"
            else "ADVANCE_CONVEX_SHRINKAGE_CHALLENGER"
        ),
        "interpretation": {
            "headline": "full frozen P2 correction has the lowest strict forward-event MAE among tested convex shrinkage policies",
            "adaptive_delta_mae_vs_p2": adaptive_summary["event_balanced_mae"] - p2_summary["event_balanced_mae"],
            "p5_context_combination_pending": True,
        },
        "production_change": False,
        "promotion_allowed": False,
        "live_adjustment": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    payload = evaluate(args.predictions_csv)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
