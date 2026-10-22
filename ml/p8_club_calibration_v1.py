#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

VERSION = "p8-club-calibration-v1"
EXPECTED_SHA = "827bebabf14fe3640361e79259893ebc25621b15b97d6eac97a24f9de043674d"
EXPECTED_INCUMBENT_ROWS = 4491
SHRINKAGE_K = 80.0
BOOTSTRAPS = 5000
SEED = 42


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def simulate(frame: pd.DataFrame, key_col: str) -> pd.DataFrame:
    """Strict forward rolling calibration.

    All predictions sharing one kickoff timestamp are produced before any
    residual from that timestamp is added to history, so tied fixtures cannot
    train one another.
    """
    work = frame.sort_values(["kickoff_at", "match_key"]).copy()
    history: dict[str, list[float]] = defaultdict(list)
    output: list[tuple[int, float, float, int]] = []

    for _, group in work.groupby("kickoff_at", sort=True):
        for idx, row in group.iterrows():
            values = history[str(row[key_col])]
            if values:
                median = float(np.median(values))
                weight = len(values) / (len(values) + SHRINKAGE_K)
                correction = weight * median
            else:
                correction = 0.0
            calibrated = float(row["forecast_p50"]) - correction
            output.append((idx, calibrated, correction, len(values)))

        for _, row in group.iterrows():
            residual = float(row["forecast_p50"]) - float(row["actual_attendance"])
            history[str(row[key_col])].append(residual)

    aux = pd.DataFrame(
        output,
        columns=["idx", "calibrated_p50", "correction", "history_n"],
    ).set_index("idx")
    work = work.join(aux)
    work["calibrated_signed_error"] = work["calibrated_p50"] - work["actual_attendance"]
    work["calibrated_absolute_error"] = work["calibrated_signed_error"].abs()
    return work


def bootstrap_delta(delta: np.ndarray) -> dict:
    rng = np.random.default_rng(SEED)
    n = len(delta)
    draws = np.empty(BOOTSTRAPS)
    for i in range(BOOTSTRAPS):
        sample_idx = rng.integers(0, n, n)
        draws[i] = float(delta[sample_idx].mean())
    lower, upper = np.quantile(draws, [0.025, 0.975])
    return {
        "n_resamples": BOOTSTRAPS,
        "seed": SEED,
        "delta_mae_lower": float(lower),
        "delta_mae_upper": float(upper),
        "p_delta_lt_zero": float(np.mean(draws < 0.0)),
    }


def summarize(frame: pd.DataFrame, key_col: str) -> dict:
    calibrated = simulate(frame, key_col)
    delta = (
        calibrated["calibrated_absolute_error"] - calibrated["absolute_error"]
    ).to_numpy(float)

    season_base = calibrated.groupby("season")["absolute_error"].mean()
    season_calibrated = calibrated.groupby("season")["calibrated_absolute_error"].mean()
    season_delta = season_calibrated - season_base

    by_key = calibrated.groupby(key_col).agg(
        base_mae=("absolute_error", "mean"),
        calibrated_mae=("calibrated_absolute_error", "mean"),
    )

    return {
        "key_col": key_col,
        "row_count": int(len(calibrated)),
        "base_mae": float(calibrated["absolute_error"].mean()),
        "calibrated_mae": float(calibrated["calibrated_absolute_error"].mean()),
        "delta_mae": float(delta.mean()),
        "relative_delta_pct": float(
            delta.mean() / calibrated["absolute_error"].mean() * 100.0
        ),
        "base_bias": float(calibrated["signed_error"].mean()),
        "calibrated_bias": float(calibrated["calibrated_signed_error"].mean()),
        "base_p90_ae": float(np.quantile(calibrated["absolute_error"], 0.9)),
        "calibrated_p90_ae": float(
            np.quantile(calibrated["calibrated_absolute_error"], 0.9)
        ),
        "season_deltas": {str(k): float(v) for k, v in season_delta.items()},
        "season_wins": int((season_delta < 0).sum()),
        "key_improvement_rate": float(
            (by_key["calibrated_mae"] < by_key["base_mae"]).mean()
        ),
        "bootstrap": bootstrap_delta(delta),
    }


def evaluate(path: Path) -> dict:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_SHA:
        raise RuntimeError(f"predictions SHA mismatch: {actual_sha}")

    frame = pd.read_csv(path)
    incumbent = frame[frame["candidate_id"].astype(str) == "incumbent-runtime"].copy()
    if len(incumbent) != EXPECTED_INCUMBENT_ROWS:
        raise RuntimeError(f"unexpected incumbent rows: {len(incumbent)}")

    incumbent["kickoff_at"] = pd.to_datetime(
        incumbent["kickoff_at"], utc=True, errors="raise"
    )

    horizons = {}
    for horizon, group in incumbent.groupby("horizon", sort=True):
        horizons[horizon] = {
            "home_club_primary": summarize(group, "home_club_key"),
            "away_opponent_secondary": summarize(group, "away_club_key"),
        }

    robust_wins = []
    for value in horizons.values():
        primary = value["home_club_primary"]
        robust_wins.append(
            primary["delta_mae"] < 0
            and primary["bootstrap"]["delta_mae_upper"] < 0
            and primary["season_wins"] >= 2
        )

    decision = (
        "ADVANCE_CLUB_CALIBRATION"
        if any(robust_wins)
        else "RETAIN_INCUMBENT_NO_ROBUST_CLUB_CALIBRATION_GAIN"
    )

    return {
        "version": VERSION,
        "status": "COMPLETED_P8_FORWARD_CLUB_CALIBRATION",
        "source_predictions_sha256": EXPECTED_SHA,
        "source_artifact_id": 12378567266,
        "evidence_class": "historical_forward_event_exposed_research",
        "policy": {
            "primary": "rolling home-club median signed-error correction",
            "secondary_control": "rolling away-opponent median signed-error correction",
            "shrinkage": "n/(n+80)",
            "same_kickoff_rule": (
                "all predictions at a kickoff are made before any residual from that kickoff is added"
            ),
            "future_data_allowed": False,
        },
        "horizons": horizons,
        "decision": decision,
        "production_change": False,
        "promotion_allowed": False,
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
