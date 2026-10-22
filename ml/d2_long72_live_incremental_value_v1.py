#!/usr/bin/env python3
"""Formal P6 incremental-value evaluation for frozen Long72 live inventory.

Question:
    Does the frozen live-ticket correction reduce MAE after the strongest
    structural Long72 anchor has already explained demand?

This script does not fit or select a new model. It evaluates the frozen
P2-observation-maturity forecast against the frozen structural anchor and
quantifies paired event-block uncertainty.
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

VERSION = "d2-long72-live-incremental-value-v1"
POLICY_ID = "P2-observation-maturity"
EXPECTED_PREDICTIONS_SHA256 = "489ba62156f19d3b915fda1b9f1ef506fb81603d4286a01e8ad4b799c58bce4b"
EXPECTED_ROW_COUNT = 80
EXPECTED_EVENT_COUNT = 13


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_p2_predictions(path: Path, *, verify_sha: bool = True) -> pd.DataFrame:
    if verify_sha:
        actual_sha = sha256_file(path)
        if actual_sha != EXPECTED_PREDICTIONS_SHA256:
            raise RuntimeError(
                f"frozen Stage2 predictions SHA mismatch: {actual_sha} != {EXPECTED_PREDICTIONS_SHA256}"
            )

    frame = pd.read_csv(path)
    required = {
        "ticket_event_id",
        "hours_to_kickoff",
        "actual_attendance",
        "anchor_p50",
        "forecast_p50",
        "policy_id",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"missing Long72 columns: {missing}")

    selected = frame[frame["policy_id"].astype(str) == POLICY_ID].copy()
    if len(selected) != EXPECTED_ROW_COUNT:
        raise RuntimeError(f"expected {EXPECTED_ROW_COUNT} frozen P2 rows, got {len(selected)}")
    if selected["ticket_event_id"].nunique() != EXPECTED_EVENT_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_EVENT_COUNT} frozen P2 events, got {selected['ticket_event_id'].nunique()}"
        )

    for column in ("hours_to_kickoff", "actual_attendance", "anchor_p50", "forecast_p50"):
        selected[column] = pd.to_numeric(selected[column], errors="raise")
    if selected[["hours_to_kickoff", "actual_attendance", "anchor_p50", "forecast_p50"]].isna().any().any():
        raise RuntimeError("frozen P2 predictions contain null numeric values")
    if not ((selected["hours_to_kickoff"] > 24.0) & (selected["hours_to_kickoff"] <= 72.0)).all():
        raise RuntimeError("frozen P2 predictions contain rows outside 24<h<=72")

    return selected.sort_values(["ticket_event_id", "hours_to_kickoff"], ascending=[True, False]).reset_index(drop=True)


def evaluate_band(
    frame: pd.DataFrame,
    *,
    band_id: str,
    lower_exclusive: float,
    upper_inclusive: float,
    config: BootstrapConfig,
) -> dict[str, Any]:
    band = frame[
        (frame["hours_to_kickoff"] > lower_exclusive)
        & (frame["hours_to_kickoff"] <= upper_inclusive)
    ].copy()
    if band.empty:
        raise RuntimeError(f"empty Long72 band: {band_id}")

    event_errors = paired_event_errors(
        band,
        event_col="ticket_event_id",
        actual_col="actual_attendance",
        incumbent_col="anchor_p50",
        challenger_col="forecast_p50",
    )
    result = bootstrap_delta_mae(event_errors, config=config)

    band["anchor_signed_error"] = band["anchor_p50"] - band["actual_attendance"]
    band["challenger_signed_error"] = band["forecast_p50"] - band["actual_attendance"]
    event_bias = (
        band.groupby("ticket_event_id", sort=True)
        .agg(
            anchor_bias=("anchor_signed_error", "mean"),
            challenger_bias=("challenger_signed_error", "mean"),
        )
        .reset_index()
    )

    result.update(
        {
            "band_id": band_id,
            "hours_to_kickoff_lower_exclusive": lower_exclusive,
            "hours_to_kickoff_upper_inclusive": upper_inclusive,
            "row_count": int(len(band)),
            "anchor_event_balanced_bias": float(event_bias["anchor_bias"].mean()),
            "challenger_event_balanced_bias": float(event_bias["challenger_bias"].mean()),
        }
    )
    return result


def build_payload(predictions_csv: Path) -> dict[str, Any]:
    frame = load_frozen_p2_predictions(predictions_csv)
    config = BootstrapConfig(n_resamples=5000, seed=42)

    overall = evaluate_band(
        frame,
        band_id="24_72h",
        lower_exclusive=24.0,
        upper_inclusive=72.0,
        config=config,
    )
    band_24_48 = evaluate_band(
        frame,
        band_id="24_48h",
        lower_exclusive=24.0,
        upper_inclusive=48.0,
        config=config,
    )
    band_48_72 = evaluate_band(
        frame,
        band_id="48_72h",
        lower_exclusive=48.0,
        upper_inclusive=72.0,
        config=config,
    )

    overall_upper = float(overall["bootstrap"]["delta_mae_upper"])
    if overall_upper < 0.0:
        decision = "HISTORICAL_LIVE_INCREMENTAL_UPLIFT_UNCERTAINTY_SUPPORTED"
    else:
        decision = "HISTORICAL_LIVE_UPLIFT_PROMISING_NOT_UNCERTAINTY_CONCLUSIVE"

    return {
        "version": VERSION,
        "status": "COMPLETED_HISTORICAL_INCREMENTAL_VALUE_EVALUATION",
        "research_question": (
            "Does frozen PIT live inventory reduce MAE after the frozen structural Long72 anchor?"
        ),
        "evidence_class": "historical_exposed_research",
        "independent_evaluation_unit": "event",
        "package_id": "d2-long72-stage2-p2-observation-maturity-2026-10-21-v1",
        "policy_id": POLICY_ID,
        "predictions_sha256": EXPECTED_PREDICTIONS_SHA256,
        "bootstrap_config": {
            "n_resamples": config.n_resamples,
            "seed": config.seed,
            "method": "paired_event_block_percentile",
        },
        "decision": decision,
        "bands": {
            "overall_24_72h": overall,
            "band_24_48h": band_24_48,
            "band_48_72h": band_48_72,
        },
        "interpretation": {
            "point_estimate": "live/P2 lowers event-balanced MAE materially versus the structural anchor",
            "uncertainty": "overall 95% paired event-block interval still crosses zero at N=13",
            "promotion_implication": "historical result is promising but cannot replace prospective evidence",
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

    payload = build_payload(args.predictions_csv)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
