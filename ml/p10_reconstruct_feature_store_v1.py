#!/usr/bin/env python3
"""Reconstruct the canonical 7,650-row Structural Prior PIT store for P10.

Input is the immutable 1,530-match raw history artifact already committed at:
ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz

The adapter verifies the pinned SHA, reproduces the exact temporal semantics
used by structural_prior_feature_store_v1, calls the canonical feature builder,
and adds one explicit common residual anchor for the controlled P10 comparison.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from ml.features.structural_prior_feature_store_v1 import (
    COMMON_COLUMNS,
    COMPLETION_BUFFER_HOURS,
    WARSAW_TZ,
    build_feature_store,
    quality_report,
)

VERSION = "p10-reconstruct-feature-store-v1"
PINNED_RAW_SHA256 = "3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569"
PINNED_MATCHES = 1530
PINNED_PIT_ROWS = 7650
BASELINE_COLUMN = "baseline_season"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_raw(path: Path) -> pd.DataFrame:
    actual_sha = sha256(path)
    if actual_sha != PINNED_RAW_SHA256:
        raise RuntimeError(f"P10 raw history SHA drift: {actual_sha}")
    data = pd.read_csv(path)
    missing = sorted(set(COMMON_COLUMNS) - set(data.columns))
    if missing:
        raise RuntimeError(f"P10 canonical raw history missing columns: {missing}")
    if len(data) != PINNED_MATCHES or data["match_key"].nunique() != PINNED_MATCHES:
        raise RuntimeError(f"P10 expected {PINNED_MATCHES} unique matches")
    data = data[COMMON_COLUMNS].copy()
    data["round"] = data["round"].astype(int)
    data["date"] = pd.to_datetime(data["date"])
    local = pd.to_datetime(
        data["date"].dt.strftime("%Y-%m-%d") + " " + data["kickoff_time_local"].astype(str),
        format="mixed",
    )
    data["kickoff_at"] = local.dt.tz_localize(
        WARSAW_TZ, ambiguous="raise", nonexistent="raise"
    ).dt.tz_convert("UTC")
    data["completed_at"] = data["kickoff_at"] + pd.Timedelta(hours=COMPLETION_BUFFER_HOURS)
    data = data.sort_values(["kickoff_at", "home_club_key"]).reset_index(drop=True)
    data["training_eligible"] = ~data["attendance"].eq(0)
    return data


def reconstruct(path: Path) -> tuple[pd.DataFrame, dict]:
    raw = prepare_raw(path)
    store = build_feature_store(raw)
    report = quality_report(store)
    if report["status"] != "PASS":
        raise RuntimeError(f"P10 canonical feature-store quality failure: {report}")
    if len(store) != PINNED_PIT_ROWS:
        raise RuntimeError(f"P10 expected {PINNED_PIT_ROWS} PIT rows")
    if BASELINE_COLUMN not in store.columns:
        raise RuntimeError(f"P10 missing canonical residual baseline {BASELINE_COLUMN}")
    eligible = store["training_eligible"]
    if store.loc[eligible, BASELINE_COLUMN].isna().any():
        raise RuntimeError("P10 eligible rows contain null baseline_season")
    store = store.copy()
    # Fixed common anchor for both local and pooled candidate. Pooling is the
    # only intended treatment difference in P10 v1.
    store["baseline_fixed"] = store[BASELINE_COLUMN]
    report = {
        **report,
        "version": VERSION,
        "raw_sha256": PINNED_RAW_SHA256,
        "baseline_fixed_source": BASELINE_COLUMN,
        "p10_rows": int(len(store)),
        "p10_matches": int(store["match_key"].nunique()),
    }
    return store, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    store, report = reconstruct(args.raw_history)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    store.to_csv(args.output, index=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
