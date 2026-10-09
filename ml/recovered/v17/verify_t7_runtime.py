#!/usr/bin/env python3
"""Verify exact v1.7 T-7 runtime reconstruction from repo-only evidence."""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from ml.recovered.v17.reconstruct_t7_v17 import (
    CAPACITY,
    normalize_local_match_time,
    prepare_dataset,
    reconstruct,
)
from ml.recovered.v17.t7_bundle import ROOT, load_t7_frames

TOLERANCE = 1e-6
EXPECTED_MAE = 4151.081861936878
OOS_FILE = ROOT / "v17_t7_oos_predictions.csv"
OOS_SEASONS = {"2022/2023", "2023/2024", "2024/2025", "2025/2026"}


def main() -> None:
    frames = load_t7_frames()

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        history_path = root / "history.csv"
        checkpoint_path = root / "checkpoint.csv"
        frames["history.csv"].to_csv(history_path, index=False)
        frames["checkpoint.csv"].to_csv(checkpoint_path, index=False)
        df, features, valid_target = prepare_dataset(history_path, checkpoint_path)

    evidence = df[df["season"].isin(OOS_SEASONS)][
        ["season", "match_date", "opponent_key", "attendance"]
    ].copy()
    evidence["evidence_key"] = (
        evidence["season"].astype(str)
        + "|"
        + normalize_local_match_time(evidence["match_date"])
        + "|"
        + evidence["opponent_key"].astype(str)
    )
    if len(evidence) != 68:
        raise AssertionError(f"Expected 68 T-7 OOS target rows, got {len(evidence)}")

    raw = reconstruct(
        df=df,
        features=features,
        valid_target=valid_target,
        evidence=evidence,
        residual=True,
    )
    final = np.clip(raw, 0.0, float(CAPACITY))

    preserved = pd.read_csv(OOS_FILE).copy()
    preserved["local_match_time"] = normalize_local_match_time(preserved["match_date"])
    evidence["local_match_time"] = normalize_local_match_time(evidence["match_date"])
    observed = evidence.assign(reconstructed=final).merge(
        preserved[["season", "local_match_time", "actual", "v17"]],
        on=["season", "local_match_time"],
        how="inner",
        validate="one_to_one",
    )
    if len(observed) != 68:
        raise AssertionError(
            f"Preserved T-7 OOS join must contain 68 rows, got {len(observed)}"
        )
    if not np.allclose(observed["attendance"], observed["actual"], atol=TOLERANCE):
        raise AssertionError("Preserved actual attendance does not match runtime history")

    delta = observed["reconstructed"].to_numpy() - observed["v17"].to_numpy()
    max_delta = float(np.max(np.abs(delta)))
    mean_delta = float(np.mean(np.abs(delta)))
    if max_delta > TOLERANCE:
        raise AssertionError(
            f"v1.7 final T-7 reconstruction drifted: mean={mean_delta}, max={max_delta}"
        )

    mae = float(
        np.mean(
            np.abs(
                observed["reconstructed"].to_numpy()
                - observed["actual"].to_numpy()
            )
        )
    )
    if abs(mae - EXPECTED_MAE) > TOLERANCE:
        raise AssertionError(f"v1.7 T-7 MAE drifted: {mae} != {EXPECTED_MAE}")

    print("v1.7 T-7 runtime reconstruction verified from repo-only evidence.")
    print(f"68-match final max prediction delta: {max_delta:.3e}")
    print(f"68-match final mean prediction delta: {mean_delta:.3e}")
    print(f"v1.7 T-7 MAE: {mae:.6f}")


if __name__ == "__main__":
    main()
