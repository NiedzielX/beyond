#!/usr/bin/env python3
"""d2 Long72 Stage 1 — bounded event-level LOEO live-residual tournament.

This experiment consumes the immutable 14-event / 130-row long72 artifact and
asks a materially new question versus the original final-24h Stage 1:

    does live ticket trajectory improve the PIT Pre-Live anchor in 24–72h?

All 14 labels are already exposed historical research evidence. Selection is
therefore research ranking only and cannot promote production.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import ml.d2_stage1_model_tournament_v1 as base
from ml.run_d2_stage1_model_tournament_v1 import (
    load_pinned_chronos_pipeline,
    normalize_quantile_output_canonical,
)

EXPERIMENT = "d2-long72-stage1-model-tournament-v1"
STAGE = "d2-long72-stage1-live-residual-loeo"
EXPECTED_EVENT_IDS = (1, 3, 4, 5, 8, 9, 11, 12, 13, 14, 15, 17, 18, 19)
EXPECTED_EVENT_COUNT = 14
EXPECTED_ROW_COUNT = 130
EXPECTED_ROWS_BY_BAND = {"0_24h": 50, "24_48h": 45, "48_72h": 35}
PINNED_DATASET_SHA256 = "2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c"
PINNED_CONTRACT_SHA256 = "0083b82be7de4599574b90ed0af44e1accd1a993c1d07b7f263bfbf01f3a1a27"
MAX_LIVE_CORRECTION_OCCUPANCY = 0.10

# Reuse the same bounded model families tested in final-24h Stage 1. The new
# experiment changes the data window/anchor mapping, not the candidate zoo.
CANDIDATES = base.CANDIDATES

# Keep the canonical pinned Chronos/Bolt runtime and singleton-output adapter.
base.normalize_quantile_output = normalize_quantile_output_canonical


def load_long72_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if len(frame) != EXPECTED_ROW_COUNT:
        raise RuntimeError(f"long72 Stage1 expects {EXPECTED_ROW_COUNT} rows, got {len(frame)}")
    ids = tuple(sorted(frame["ticket_event_id"].astype(int).unique()))
    if ids != EXPECTED_EVENT_IDS:
        raise RuntimeError(f"long72 event IDs drifted: {ids}")
    required = {
        "ticket_event_id", "as_of_at", "hours_to_kickoff", "anchor_horizon",
        "anchor_p50", "anchor_expected_occupancy", "stadium_capacity",
        "actual_attendance", "target_live_delta_occupancy",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"long72 dataset missing columns: {missing}")
    frame["as_of_at"] = pd.to_datetime(frame["as_of_at"], utc=True)
    frame["hours_to_kickoff"] = frame["hours_to_kickoff"].astype(float)
    if not ((frame["hours_to_kickoff"] > 0.0) & (frame["hours_to_kickoff"] <= 72.0)).all():
        raise RuntimeError("long72 row outside 0<h<=72")
    expected_horizon = np.where(frame["hours_to_kickoff"] <= 24.0, "T-1", "T-3")
    if not np.array_equal(frame["anchor_horizon"].astype(str).to_numpy(), expected_horizon):
        raise RuntimeError("long72 anchor horizon mapping drifted")

    rows_by_band = {
        "0_24h": int((frame["hours_to_kickoff"] <= 24.0).sum()),
        "24_48h": int(((frame["hours_to_kickoff"] > 24.0) & (frame["hours_to_kickoff"] <= 48.0)).sum()),
        "48_72h": int(((frame["hours_to_kickoff"] > 48.0) & (frame["hours_to_kickoff"] <= 72.0)).sum()),
    }
    if rows_by_band != EXPECTED_ROWS_BY_BAND:
        raise RuntimeError(f"long72 band row counts drifted: {rows_by_band}")

    # Compatibility aliases for the already-audited Stage-1 candidate engine.
    frame["frozen_v2_p50"] = frame["anchor_p50"].astype(float)
    frame["frozen_v2_expected_occupancy"] = frame["anchor_expected_occupancy"].astype(float)
    frame = frame.sort_values(["ticket_event_id", "as_of_at"]).reset_index(drop=True)
    return frame


def event_balanced_band_score(predictions: pd.DataFrame, low_exclusive: float, high_inclusive: float) -> dict[str, Any]:
    band = predictions[
        (predictions["hours_to_kickoff"].astype(float) > low_exclusive)
        & (predictions["hours_to_kickoff"].astype(float) <= high_inclusive)
    ].copy()
    if band.empty:
        return {
            "event_count": 0,
            "row_count": 0,
            "event_balanced_mae": None,
            "anchor_event_balanced_mae": None,
            "mae_improvement": None,
            "event_improvement_rate": None,
            "worst_event_degradation": None,
        }
    per_event = (
        band.groupby("ticket_event_id", sort=True)
        .agg(
            candidate_mae=("absolute_error", "mean"),
            anchor_mae=("anchor_absolute_error", "mean"),
            rows=("ticket_event_id", "size"),
        )
        .reset_index()
    )
    degradation = per_event["candidate_mae"].astype(float) - per_event["anchor_mae"].astype(float)
    return {
        "event_count": int(len(per_event)),
        "row_count": int(len(band)),
        "event_balanced_mae": float(per_event["candidate_mae"].mean()),
        "anchor_event_balanced_mae": float(per_event["anchor_mae"].mean()),
        "mae_improvement": float((per_event["anchor_mae"] - per_event["candidate_mae"]).mean()),
        "event_improvement_rate": float(np.mean(degradation < 0.0)),
        "worst_event_degradation": float(max(0.0, degradation.max())),
        "best_event_improvement": float(max(0.0, (-degradation).max())),
    }


def enrich_predictions(frame: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    context = frame[["ticket_event_id", "as_of_at", "hours_to_kickoff", "anchor_horizon"]].copy()
    enriched = predictions.merge(
        context,
        on=["ticket_event_id", "as_of_at"],
        how="left",
        validate="one_to_one",
    )
    if enriched["hours_to_kickoff"].isna().any():
        raise RuntimeError("failed to restore long72 row context onto predictions")
    return enriched


def score_candidate(frame: pd.DataFrame, spec: base.CandidateSpec) -> tuple[dict[str, Any], pd.DataFrame]:
    predictions = enrich_predictions(frame, base.loeo_predictions(frame, spec))
    overall = base.candidate_scorecard(predictions)
    bands = {
        "0_24h": event_balanced_band_score(predictions, 0.0, 24.0),
        "24_48h": event_balanced_band_score(predictions, 24.0, 48.0),
        "48_72h": event_balanced_band_score(predictions, 48.0, 72.0),
        "24_72h": event_balanced_band_score(predictions, 24.0, 72.0),
    }
    return {
        "candidate_id": spec.id,
        "spec": asdict(spec),
        "overall_0_72h": overall,
        "bands": bands,
    }, predictions


def choose_research_lead(scorecards: list[dict[str, Any]]) -> str:
    """Predeclared research selector focused on the new earlier-live hypothesis.

    Eligible candidates must improve both the full 0–72h window and the new
    24–72h window, and must not worsen the sparsest admitted 48–72h band.
    Rank by 24–72h MAE, then 48–72h MAE, overall MAE and early-band tail risk.
    """
    eligible: list[dict[str, Any]] = []
    for row in scorecards:
        if row["candidate_id"] == "frozen-v2-zero-correction":
            continue
        overall = row["overall_0_72h"]
        early = row["bands"]["24_72h"]
        far = row["bands"]["48_72h"]
        if (
            overall["window_mae_improvement"] > 0.0
            and early["mae_improvement"] is not None
            and early["mae_improvement"] > 0.0
            and far["mae_improvement"] is not None
            and far["mae_improvement"] >= 0.0
        ):
            eligible.append(row)
    if not eligible:
        return "frozen-v2-zero-correction"
    return min(
        eligible,
        key=lambda row: (
            row["bands"]["24_72h"]["event_balanced_mae"],
            row["bands"]["48_72h"]["event_balanced_mae"],
            row["overall_0_72h"]["event_balanced_window_mae"],
            row["bands"]["24_72h"]["worst_event_degradation"],
            row["candidate_id"],
        ),
    )["candidate_id"]


def run_tournament(frame: pd.DataFrame, include_tsfm: bool) -> tuple[dict[str, Any], pd.DataFrame]:
    working = frame.copy()
    tsfm: dict[str, Any] = {
        "enabled": bool(include_tsfm),
        "target_series": "available_share_of_capacity",
        "label_leakage_allowed": False,
        "chronos2_model_id": base.CHRONOS2_MODEL_ID,
        "chronos_bolt_model_id": base.CHRONOS_BOLT_MODEL_ID,
    }
    if include_tsfm:
        chronos2 = load_pinned_chronos_pipeline(base.CHRONOS2_MODEL_ID)
        bolt = load_pinned_chronos_pipeline(base.CHRONOS_BOLT_MODEL_ID)
        working = base.add_tsfm_features(working, chronos2, "chronos2")
        working = base.add_tsfm_features(working, bolt, "bolt")
        tsfm["chronos2_ready_rows"] = int(working["chronos2_ready"].sum())
        tsfm["bolt_ready_rows"] = int(working["bolt_ready"].sum())
    else:
        tsfm["status"] = "NOT_RUN"

    specs = [spec for spec in CANDIDATES if include_tsfm or spec.tsfm_prefix is None]
    scorecards: list[dict[str, Any]] = []
    prediction_parts: list[pd.DataFrame] = []
    for spec in specs:
        score, predictions = score_candidate(working, spec)
        scorecards.append(score)
        prediction_parts.append(predictions)

    lead = choose_research_lead(scorecards)
    result = {
        "experiment": EXPERIMENT,
        "stage": STAGE,
        "status": "COMPLETED_HISTORICAL_RESEARCH_TOURNAMENT",
        "production_change": False,
        "promotion_allowed": False,
        "evidence_class": "EXPOSED_HISTORICAL_R_AND_D",
        "independent_evaluation_unit": "event",
        "validation": "LOEO_ALL_ROWS_HELD_OUT_BY_EVENT",
        "event_balanced_training_weights": True,
        "event_count": int(working["ticket_event_id"].nunique()),
        "row_count": int(len(working)),
        "max_live_correction_occupancy": MAX_LIVE_CORRECTION_OCCUPANCY,
        "pinned_input": {
            "dataset_sha256": PINNED_DATASET_SHA256,
            "contract_sha256": PINNED_CONTRACT_SHA256,
        },
        "selection_rule": (
            "Require positive 0-72h and 24-72h event-balanced MAE improvement, "
            "non-negative 48-72h improvement; rank by 24-72h MAE, 48-72h MAE, "
            "overall MAE, then 24-72h worst-event degradation."
        ),
        "tsfm": tsfm,
        "candidates": scorecards,
        "research_lead_candidate_id": lead,
        "decision_boundary": (
            "Research ranking only. All 14 outcomes are already exposed historical evidence; "
            "no production promotion or unseen-holdout claim is allowed."
        ),
    }
    return result, pd.concat(prediction_parts, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-predictions-csv", type=Path, required=True)
    parser.add_argument("--with-tsfm", action="store_true")
    args = parser.parse_args()

    frame = load_long72_frame(args.input_csv)
    result, predictions = run_tournament(frame, include_tsfm=bool(args.with_tsfm))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    predictions.to_csv(args.output_predictions_csv, index=False)

    print(json.dumps({
        "experiment": result["experiment"],
        "research_lead_candidate_id": result["research_lead_candidate_id"],
        "event_count": result["event_count"],
        "row_count": result["row_count"],
        "tsfm": result["tsfm"],
        "candidates": [
            {
                "candidate_id": row["candidate_id"],
                "overall_0_72h_mae": row["overall_0_72h"]["event_balanced_window_mae"],
                "overall_improvement": row["overall_0_72h"]["window_mae_improvement"],
                "early_24_72h_mae": row["bands"]["24_72h"]["event_balanced_mae"],
                "early_24_72h_improvement": row["bands"]["24_72h"]["mae_improvement"],
                "far_48_72h_improvement": row["bands"]["48_72h"]["mae_improvement"],
                "early_worst_event_degradation": row["bands"]["24_72h"]["worst_event_degradation"],
            }
            for row in result["candidates"]
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
