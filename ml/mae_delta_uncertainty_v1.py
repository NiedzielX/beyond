#!/usr/bin/env python3
"""Paired block-bootstrap uncertainty for challenger-vs-incumbent MAE deltas.

The independent resampling unit is an event/fixture, never an individual
trajectory snapshot. Optional strata (for example temporal fold IDs) preserve
the evaluation composition inside each bootstrap draw.

Convention:
    delta_mae = challenger_mae - incumbent_mae

Negative delta is an improvement.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BootstrapConfig:
    n_resamples: int = 5000
    seed: int = 42
    lower_quantile: float = 0.025
    upper_quantile: float = 0.975


def _validate_config(config: BootstrapConfig) -> None:
    if config.n_resamples < 100:
        raise ValueError("n_resamples must be >= 100")
    if not 0.0 < config.lower_quantile < config.upper_quantile < 1.0:
        raise ValueError("invalid bootstrap quantiles")


def paired_event_errors(
    frame: pd.DataFrame,
    *,
    event_col: str,
    actual_col: str,
    incumbent_col: str,
    challenger_col: str,
    strata_cols: Sequence[str] = (),
) -> pd.DataFrame:
    required = {event_col, actual_col, incumbent_col, challenger_col, *strata_cols}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"missing uncertainty columns: {missing}")
    if frame.empty:
        raise RuntimeError("cannot estimate uncertainty on empty data")

    work = frame[list(strata_cols) + [event_col, actual_col, incumbent_col, challenger_col]].copy()
    work[event_col] = work[event_col].astype(str)
    for column in (actual_col, incumbent_col, challenger_col):
        work[column] = pd.to_numeric(work[column], errors="raise")
    if work[[actual_col, incumbent_col, challenger_col]].isna().any().any():
        raise RuntimeError("uncertainty input contains null numeric values")

    group_cols = list(strata_cols) + [event_col]
    # Multiple rows for one event (e.g. trajectory observations) are collapsed
    # to one event-level MAE before resampling.
    grouped = (
        work.assign(
            incumbent_ae=(work[incumbent_col] - work[actual_col]).abs(),
            challenger_ae=(work[challenger_col] - work[actual_col]).abs(),
        )
        .groupby(group_cols, sort=True, dropna=False)
        .agg(
            incumbent_ae=("incumbent_ae", "mean"),
            challenger_ae=("challenger_ae", "mean"),
            rows=(event_col, "size"),
        )
        .reset_index()
    )
    grouped["delta_ae"] = grouped["challenger_ae"] - grouped["incumbent_ae"]
    return grouped


def bootstrap_delta_mae(
    event_errors: pd.DataFrame,
    *,
    strata_cols: Sequence[str] = (),
    config: BootstrapConfig = BootstrapConfig(),
) -> dict[str, Any]:
    _validate_config(config)
    if event_errors.empty:
        raise RuntimeError("empty event error table")
    required = {"incumbent_ae", "challenger_ae", "delta_ae", *strata_cols}
    missing = sorted(required - set(event_errors.columns))
    if missing:
        raise RuntimeError(f"event error table missing columns: {missing}")

    incumbent_mae = float(event_errors["incumbent_ae"].mean())
    challenger_mae = float(event_errors["challenger_ae"].mean())
    point_delta = challenger_mae - incumbent_mae
    rng = np.random.default_rng(config.seed)
    draws = np.empty(config.n_resamples, dtype=float)

    if strata_cols:
        group_key = strata_cols[0] if len(strata_cols) == 1 else list(strata_cols)
        strata = [group.reset_index(drop=True) for _, group in event_errors.groupby(group_key, sort=True, dropna=False)]
    else:
        strata = [event_errors.reset_index(drop=True)]

    for index in range(config.n_resamples):
        incumbent_sum = 0.0
        challenger_sum = 0.0
        sampled_events = 0
        for stratum in strata:
            n = len(stratum)
            if n == 0:
                continue
            sample_idx = rng.integers(0, n, size=n)
            sample = stratum.iloc[sample_idx]
            incumbent_sum += float(sample["incumbent_ae"].sum())
            challenger_sum += float(sample["challenger_ae"].sum())
            sampled_events += n
        if sampled_events == 0:
            raise RuntimeError("bootstrap produced zero events")
        draws[index] = challenger_sum / sampled_events - incumbent_sum / sampled_events

    lower = float(np.quantile(draws, config.lower_quantile))
    upper = float(np.quantile(draws, config.upper_quantile))
    return {
        "independent_event_count": int(len(event_errors)),
        "incumbent_mae": incumbent_mae,
        "challenger_mae": challenger_mae,
        "delta_mae": point_delta,
        "relative_delta_mae": point_delta / incumbent_mae if incumbent_mae > 0 else None,
        "event_improvement_rate": float(np.mean(event_errors["delta_ae"] < 0.0)),
        "bootstrap": {
            "method": "paired_event_block_percentile",
            "stratified": bool(strata_cols),
            "strata_cols": list(strata_cols),
            "n_resamples": config.n_resamples,
            "seed": config.seed,
            "lower_quantile": config.lower_quantile,
            "upper_quantile": config.upper_quantile,
            "delta_mae_lower": lower,
            "delta_mae_upper": upper,
            "p_delta_mae_below_zero": float(np.mean(draws < 0.0)),
            "median_bootstrap_delta_mae": float(np.median(draws)),
        },
    }


def evaluate_candidate(
    predictions: pd.DataFrame,
    *,
    candidate_id: str,
    incumbent_id: str,
    event_col: str,
    actual_col: str,
    prediction_col: str,
    candidate_col: str,
    strata_cols: Sequence[str] = (),
    config: BootstrapConfig = BootstrapConfig(),
) -> dict[str, Any]:
    incumbent = predictions[predictions[candidate_col].astype(str) == incumbent_id].copy()
    challenger = predictions[predictions[candidate_col].astype(str) == candidate_id].copy()
    if incumbent.empty or challenger.empty:
        raise RuntimeError(f"missing paired predictions incumbent={incumbent_id} candidate={candidate_id}")

    key_cols = list(strata_cols) + [event_col]
    inc = incumbent[key_cols + [actual_col, prediction_col]].rename(
        columns={prediction_col: "incumbent_prediction", actual_col: "incumbent_actual"}
    )
    chal = challenger[key_cols + [actual_col, prediction_col]].rename(
        columns={prediction_col: "challenger_prediction", actual_col: "challenger_actual"}
    )
    paired = inc.merge(chal, on=key_cols, how="inner", validate="one_to_one")
    if len(paired) != len(incumbent) or len(paired) != len(challenger):
        raise RuntimeError("challenger/incumbent prediction identities do not pair one-to-one")
    if not np.allclose(
        paired["incumbent_actual"].astype(float),
        paired["challenger_actual"].astype(float),
        rtol=0.0,
        atol=0.0,
    ):
        raise RuntimeError("paired challenger/incumbent actual labels differ")

    canonical = paired.rename(
        columns={
            "incumbent_actual": "actual",
            "incumbent_prediction": "incumbent",
            "challenger_prediction": "challenger",
        }
    )
    errors = paired_event_errors(
        canonical,
        event_col=event_col,
        actual_col="actual",
        incumbent_col="incumbent",
        challenger_col="challenger",
        strata_cols=strata_cols,
    )
    result = bootstrap_delta_mae(errors, strata_cols=strata_cols, config=config)
    result.update({
        "candidate_id": candidate_id,
        "incumbent_id": incumbent_id,
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--candidate-id", action="append", required=True)
    parser.add_argument("--incumbent-id", default="incumbent-runtime")
    parser.add_argument("--event-col", default="match_key")
    parser.add_argument("--actual-col", default="actual_attendance")
    parser.add_argument("--prediction-col", default="forecast_p50")
    parser.add_argument("--candidate-col", default="candidate_id")
    parser.add_argument("--strata-col", action="append", default=[])
    parser.add_argument("--n-resamples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    frame = pd.read_csv(args.predictions_csv)
    config = BootstrapConfig(n_resamples=args.n_resamples, seed=args.seed)
    results = [
        evaluate_candidate(
            frame,
            candidate_id=candidate,
            incumbent_id=args.incumbent_id,
            event_col=args.event_col,
            actual_col=args.actual_col,
            prediction_col=args.prediction_col,
            candidate_col=args.candidate_col,
            strata_cols=args.strata_col,
            config=config,
        )
        for candidate in args.candidate_id
    ]
    payload = {
        "version": "mae-delta-uncertainty-v1",
        "production_change": False,
        "resampling_unit": "event_or_fixture",
        "results": results,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
