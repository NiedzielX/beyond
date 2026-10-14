#!/usr/bin/env python3
"""Readiness gate for the first global historical benchmark.

The gate refuses to treat a one-season dataset as a valid model tournament when
there is insufficient pre-development training history. It reports the exact
available training rows by horizon instead of weakening the benchmark protocol.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

DEV_START = pd.Timestamp("2025-10-01T00:00:00Z")
MATCH_COMPLETION_BUFFER = pd.Timedelta(hours=3)
MIN_TRAIN_ROWS = 40
BASELINE_COLUMNS = [
    "home_attendance_rolling3",
    "home_attendance_rolling5",
    "home_attendance_mean",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-store", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    frame = pd.read_csv(args.feature_store)
    frame["as_of_at"] = pd.to_datetime(frame["as_of_at"], utc=True)
    frame["kickoff_at"] = pd.to_datetime(frame["kickoff_at"], utc=True)

    horizons = {}
    all_ready = True
    for horizon, group in frame.groupby("horizon", sort=True):
        dev = group[group["kickoff_at"] >= DEV_START].copy()
        first_dev_as_of = dev["as_of_at"].min()
        baseline_counts = {}
        for baseline in BASELINE_COLUMNS:
            train = group[
                (group["kickoff_at"] + MATCH_COMPLETION_BUFFER < first_dev_as_of)
                & group[baseline].notna()
                & group["target_attendance"].notna()
            ]
            baseline_counts[baseline] = int(len(train))
        best_available = max(baseline_counts.values()) if baseline_counts else 0
        ready = best_available >= MIN_TRAIN_ROWS
        all_ready = all_ready and ready
        horizons[horizon] = {
            "first_development_as_of": first_dev_as_of.isoformat(),
            "training_rows_by_baseline": baseline_counts,
            "best_available_training_rows": best_available,
            "minimum_required_training_rows": MIN_TRAIN_ROWS,
            "ready": ready,
        }

    report = {
        "gate_version": "global-historical-readiness-v1",
        "dataset_version": str(frame["dataset_version"].iloc[0]),
        "feature_set_version": str(frame["feature_set_version"].iloc[0]),
        "status": "READY" if all_ready else "INSUFFICIENT_HISTORY",
        "rule": "do not weaken time-split validation to make a one-season dataset benchmarkable",
        "horizons": horizons,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    if args.markdown_output:
        lines = [
            "# Global historical benchmark readiness",
            "",
            f"Status: **{report['status']}**",
            "",
            "| Horizon | Best pre-dev training rows | Minimum | Ready |",
            "|---|---:|---:|---|",
        ]
        for horizon, result in horizons.items():
            lines.append(
                f"| {horizon} | {result['best_available_training_rows']} | "
                f"{MIN_TRAIN_ROWS} | {'yes' if result['ready'] else 'no'} |"
            )
        lines += [
            "",
            "A NOT READY result is expected until older historical seasons are added. "
            "It is not a CI failure and must not be worked around by lowering the evidence gate.",
        ]
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text("\n".join(lines) + "\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
