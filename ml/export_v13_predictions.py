#!/usr/bin/env python3
"""Export reproducible Beyond GB v1.3 season walk-forward predictions.

Uses the exact incumbent implementation from benchmark_v01.py and writes the
out-of-sample prediction rows needed for model-specific conformal calibration.
No model selection is performed here.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ml.benchmark_v01 import FEATURE_SETS, add_features, walk_forward_incumbent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    raw = pd.read_csv(args.dataset)
    df = add_features(raw)
    predictions = walk_forward_incumbent(df, FEATURE_SETS["early"])

    # walk_forward_incumbent intentionally outputs only OOS rows. Enrich with
    # date/horizon-independent identifiers useful for audit/calibration.
    lookup = df[["match_date", "season"]].copy()
    lookup["row_index"] = lookup.index.astype(int)
    output = predictions.merge(
        lookup[["row_index", "match_date"]],
        left_on="index",
        right_on="row_index",
        how="left",
        validate="one_to_one",
    ).drop(columns=["row_index"])

    output["absolute_error"] = (output["pred"] - output["actual"]).abs()
    output["signed_error"] = output["pred"] - output["actual"]
    output["ape_pct"] = output["absolute_error"] / output["actual"] * 100.0
    output["point_model"] = "lech-v13-early-seasonality"
    output["protocol"] = "season_walk_forward_oos"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    print(f"Saved {len(output)} OOS v1.3 prediction rows to {args.output}")


if __name__ == "__main__":
    main()
