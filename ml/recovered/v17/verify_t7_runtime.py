#!/usr/bin/env python3
"""Verify exact v1.7 T-7 runtime reconstruction from repo-only evidence."""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from ml.recovered.v17.reconstruct_t7_v17 import (
    CAPACITY,
    compare,
    evidence_key,
    prepare_dataset,
    reconstruct,
)
from ml.recovered.v17.t7_bundle import load_t7_frames

TOLERANCE = 1e-6
EXPECTED_MAE = 4151.081861936878


def main() -> None:
    frames = load_t7_frames()

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        history_path = root / "history.csv"
        checkpoint_path = root / "checkpoint.csv"
        frames["history.csv"].to_csv(history_path, index=False)
        frames["checkpoint.csv"].to_csv(checkpoint_path, index=False)

        df, features, valid_target = prepare_dataset(history_path, checkpoint_path)

    v161 = frames["v161_oos.csv"].copy()
    v17 = frames["v17_oos.csv"].copy()
    v161["evidence_key"] = evidence_key(v161)
    v17["evidence_key"] = evidence_key(v17)

    if len(v161) != 68 or len(v17) != 68:
        raise AssertionError("Expected exactly 68 preserved OOS rows per T-7 control")

    direct = reconstruct(
        df=df,
        features=features,
        valid_target=valid_target,
        evidence=v161,
        residual=False,
    )
    direct_diff = compare(v161["pred"].astype(float).to_numpy(), direct)
    if direct_diff["max_absolute_prediction_difference"] > TOLERANCE:
        raise AssertionError(f"v1.6.1 direct control drifted: {direct_diff}")

    raw = reconstruct(
        df=df,
        features=features,
        valid_target=valid_target,
        evidence=v17,
        residual=True,
    )
    final = np.clip(raw, 0.0, float(CAPACITY))

    raw_diff = compare(v17["pred"].astype(float).to_numpy(), raw)
    final_diff = compare(v17["pred_final"].astype(float).to_numpy(), final)
    if raw_diff["max_absolute_prediction_difference"] > TOLERANCE:
        raise AssertionError(f"v1.7 raw T-7 reconstruction drifted: {raw_diff}")
    if final_diff["max_absolute_prediction_difference"] > TOLERANCE:
        raise AssertionError(f"v1.7 final T-7 reconstruction drifted: {final_diff}")

    actual = v17["attendance"].astype(float).to_numpy()
    mae = float(np.mean(np.abs(final - actual)))
    if abs(mae - EXPECTED_MAE) > TOLERANCE:
        raise AssertionError(f"v1.7 T-7 MAE drifted: {mae} != {EXPECTED_MAE}")

    print("v1.7 T-7 runtime reconstruction verified from repo-only evidence.")
    print(f"v1.6.1 max prediction delta: {direct_diff['max_absolute_prediction_difference']:.3e}")
    print(f"v1.7 raw max prediction delta: {raw_diff['max_absolute_prediction_difference']:.3e}")
    print(f"v1.7 final max prediction delta: {final_diff['max_absolute_prediction_difference']:.3e}")
    print(f"v1.7 T-7 MAE: {mae:.6f}")


if __name__ == "__main__":
    main()
