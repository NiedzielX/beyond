#!/usr/bin/env python3
"""Verify the recovered Beyond Historical v1.7 benchmark evidence.

This script verifies both the original recovered benchmark report and the
normalized Beyond benchmark metrics derived from the preserved OOS predictions.
It does not claim to reconstruct the missing original v1.7 runtime model.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
NORMALIZED_METRICS = BASE.parents[1] / "results" / "historical_v17_strict_metrics.json"
DEV_SEASONS = {"2022/2023", "2023/2024"}
HOLDOUT_SEASONS = {"2024/2025", "2025/2026"}


def metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    actual = frame["actual"].astype(float).to_numpy()
    pred = frame["v17"].astype(float).to_numpy()
    error = pred - actual
    absolute = np.abs(error)
    ape = absolute / actual * 100.0
    return {
        "n": int(len(frame)),
        "mae": float(np.mean(absolute)),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "mape_pct": float(np.mean(ape)),
        "wape_pct": float(np.sum(absolute) / np.sum(actual) * 100.0),
        "bias": float(np.mean(error)),
        "within_5_pct": float(np.mean(ape <= 5.0) * 100.0),
        "within_10_pct": float(np.mean(ape <= 10.0) * 100.0),
        "within_20_pct": float(np.mean(ape <= 20.0) * 100.0),
    }


def rounded_equal(actual: float, expected: float, digits: int = 1) -> bool:
    return round(actual, digits) == round(expected, digits)


def validate_horizon(label: str, filename: str, report: dict) -> dict:
    frame = pd.read_csv(BASE / filename)
    if len(frame) != 68:
        raise AssertionError(f"{label}: expected 68 OOS rows, got {len(frame)}")

    expected_seasons = DEV_SEASONS | HOLDOUT_SEASONS
    if set(frame["season"].astype(str)) != expected_seasons:
        raise AssertionError(
            f"{label}: unexpected seasons {sorted(set(frame['season'].astype(str)))}"
        )

    recomputed_abs_error = (frame["v17"] - frame["actual"]).abs()
    if not np.allclose(recomputed_abs_error, frame["v17_abs_error"], atol=1e-8):
        raise AssertionError(f"{label}: v17_abs_error column does not match actual/pred")

    slices = {
        "dev": frame[frame["season"].isin(DEV_SEASONS)],
        "holdout": frame[frame["season"].isin(HOLDOUT_SEASONS)],
        "all": frame,
    }
    output: dict[str, dict] = {}

    for slice_name, slice_frame in slices.items():
        observed = metrics(slice_frame)
        expected = report[label][slice_name]
        if observed["n"] != expected["n"]:
            raise AssertionError(
                f"{label}/{slice_name}: n {observed['n']} != {expected['n']}"
            )
        for metric_name, expected_key in [
            ("mae", "v17_mae"),
            ("rmse", "v17_rmse"),
            ("bias", "v17_bias"),
        ]:
            if not rounded_equal(
                float(observed[metric_name]), float(expected[expected_key]), 1
            ):
                raise AssertionError(
                    f"{label}/{slice_name}: {metric_name} "
                    f"{observed[metric_name]:.4f} != {expected[expected_key]}"
                )
        output[slice_name] = observed

    return output


def validate_normalized_metrics(observed: dict[str, dict]) -> None:
    expected = json.loads(NORMALIZED_METRICS.read_text())
    mapping = {
        "T30": "T-30",
        "T7": "T-7",
    }
    slice_mapping = {
        "dev": "development",
        "holdout": "holdout",
        "all": "all",
    }
    fields = [
        "mae",
        "mape_pct",
        "wape_pct",
        "bias",
        "within_5_pct",
        "within_10_pct",
        "within_20_pct",
    ]

    for source_horizon, normalized_horizon in mapping.items():
        for source_slice, normalized_slice in slice_mapping.items():
            got = observed[source_horizon][source_slice]
            want = expected[normalized_horizon][normalized_slice]
            if got["n"] != want["n"]:
                raise AssertionError(
                    f"{normalized_horizon}/{normalized_slice}: normalized n mismatch"
                )
            for field in fields:
                if not rounded_equal(float(got[field]), float(want[field]), 2):
                    raise AssertionError(
                        f"{normalized_horizon}/{normalized_slice}: {field} "
                        f"{got[field]:.6f} != {want[field]}"
                    )


def main() -> None:
    report = json.loads((BASE / "v17_metrics_strict.json").read_text())
    if report.get("model") != "v1.7":
        raise AssertionError("Recovered metrics file is not marked as v1.7")
    if report.get("production_model_changed") is not False:
        raise AssertionError("Recovered report must preserve no-production-change decision")

    t30 = validate_horizon("T30", "v17_t30_oos_predictions.csv", report)
    t7 = validate_horizon("T7", "v17_t7_oos_predictions.csv", report)
    observed = {"T30": t30, "T7": t7}
    validate_normalized_metrics(observed)

    print("Recovered v1.7 benchmark evidence verified.")
    print(f"T-30 all OOS MAE: {t30['all']['mae']:.1f}")
    print(f"T-30 all OOS MAPE: {t30['all']['mape_pct']:.2f}%")
    print(f"T-7 all OOS MAE: {t7['all']['mae']:.1f}")
    print(f"T-7 all OOS MAPE: {t7['all']['mape_pct']:.2f}%")
    print("Normalized MAE/MAPE/WAPE/Bias/threshold metrics also match.")
    print("This verifies evidence integrity, not executable inference reproducibility.")


if __name__ == "__main__":
    main()
