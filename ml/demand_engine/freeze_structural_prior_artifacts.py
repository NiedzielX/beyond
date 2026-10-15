#!/usr/bin/env python3
"""Freeze selected Structural Prior Runtime v1 models into reusable artifacts.

This is deliberately a build-time operation, not a scheduled inference step.
It reconstructs the canonical five-season PIT feature store, verifies the
approved development/holdout metrics, fits the production runtimes on all five
completed seasons, and writes joblib artifacts plus a hash manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.demand_engine.structural_prior_runtime import fit_structural_prior_runtime
from ml.features.structural_prior_feature_store_v1 import build_feature_store, quality_report, WARSAW_TZ

TRAINING_SEASONS = ["2021/2022", "2022/2023", "2023/2024", "2024/2025", "2025/2026"]
EXPECTED_HOLDOUT_MAE = {
    "T-30": {"2024/2025": 1889.3672272292858, "2025/2026": 1846.2792557036205},
    "T-14": {"2024/2025": 1748.4970512511325, "2025/2026": 1870.393553818474},
    "T-7": {"2024/2025": 1777.6927306628588, "2025/2026": 1802.2755802253876},
    "T-3": {"2024/2025": 1661.715966441126, "2025/2026": 1775.069078799718},
}
EXPECTED_HOLDOUT_ATOL = {"T-30": 1e-9, "T-14": 1e-9, "T-7": 1e-9, "T-3": 1e-9}
EXPECTED_DEVELOPMENT_MAE = {
    "T-7": 2476.8168272009416,
    "T-3": 2311.6246893162593,
}
ARTIFACT_VERSION = "structural-prior-runtime-v1-frozen-2026-10-15-t3"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_matches(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows).copy()
    required = {
        "dataset_version", "season", "round_no", "match_date", "kickoff_time_local",
        "home_team", "away_team", "home_club_key", "away_club_key", "home_goals",
        "away_goals", "attendance", "default_demand_training_eligible", "match_key",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"training export missing columns: {missing}")
    frame = frame.rename(columns={"round_no": "round", "match_date": "date"})
    frame["round"] = frame["round"].astype(int)
    frame["date"] = pd.to_datetime(frame["date"])
    local = pd.to_datetime(
        frame["date"].dt.strftime("%Y-%m-%d") + " " + frame["kickoff_time_local"].astype(str),
        format="mixed",
    )
    frame["kickoff_at"] = local.dt.tz_localize(
        WARSAW_TZ, ambiguous="raise", nonexistent="raise"
    ).dt.tz_convert("UTC")
    frame["completed_at"] = frame["kickoff_at"] + pd.Timedelta(hours=3)
    frame["training_eligible"] = frame["default_demand_training_eligible"].astype(bool)
    return frame.sort_values(["kickoff_at", "home_club_key"]).reset_index(drop=True)


def _mae(actual, predicted) -> float:
    return float(np.mean(np.abs(np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float))))


def _score_season(
    store: pd.DataFrame,
    horizon: str,
    training_seasons: list[str],
    test_season: str,
) -> float:
    runtime = fit_structural_prior_runtime(store, horizon, training_seasons)
    spec = runtime.spec
    test = store[
        (store["horizon"].astype(str) == horizon)
        & store["training_eligible"].astype(bool)
        & (store["season"] == test_season)
        & store[spec.baseline_column].notna()
    ].copy()
    return _mae(test["target_attendance"], runtime.predict(test))


def verify_frozen_selection(store: pd.DataFrame) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    mismatches: list[str] = []

    development: dict[str, dict[str, float]] = {}
    for horizon in ("T-7", "T-3"):
        value = _score_season(
            store,
            horizon,
            ["2021/2022", "2022/2023"],
            "2023/2024",
        )
        development[horizon] = {"2023/2024": value}
        expected = EXPECTED_DEVELOPMENT_MAE[horizon]
        if not np.isclose(value, expected, rtol=0.0, atol=1e-9):
            mismatches.append(
                f"{horizon}/development-2023/2024: actual={value} expected={expected}"
            )

    holdouts: dict[str, dict[str, float]] = {}
    for horizon in ("T-30", "T-14", "T-7", "T-3"):
        holdouts[horizon] = {}
        for test_season, training_seasons in (
            ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
            ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
        ):
            value = _score_season(store, horizon, training_seasons, test_season)
            expected = EXPECTED_HOLDOUT_MAE[horizon][test_season]
            holdouts[horizon][test_season] = value
            if not np.isclose(value, expected, rtol=0.0, atol=EXPECTED_HOLDOUT_ATOL[horizon]):
                mismatches.append(
                    f"{horizon}/{test_season}: actual={value} expected={expected}"
                )

    if mismatches:
        raise RuntimeError("frozen benchmark mismatch: " + "; ".join(mismatches))
    return holdouts, development


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="JSON returned by materializer gateway mode=training")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    rows = payload.get("rows") or []
    matches = _canonical_matches(rows)
    if len(matches) != 1530 or matches["match_key"].nunique() != 1530:
        raise RuntimeError(f"expected 1530 canonical matches, got rows={len(matches)} unique={matches['match_key'].nunique()}")

    store = build_feature_store(matches)
    quality = quality_report(store)
    if quality["status"] != "PASS":
        raise RuntimeError(f"feature-store quality failed: {quality}")
    benchmark, development = verify_frozen_selection(store)

    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    historical_path = output / "historical_runtime_v1.csv.gz"
    export_columns = [
        "season", "round", "date", "kickoff_time_local", "home_team", "away_team",
        "home_club_key", "away_club_key", "home_goals", "away_goals", "attendance", "match_key",
    ]
    matches[export_columns].to_csv(historical_path, index=False, compression="gzip")

    manifest = {
        "artifact_version": ARTIFACT_VERSION,
        "feature_contract": "structural-prior-pit-v1+verified-capacity-v1",
        "training_seasons": TRAINING_SEASONS,
        "historical_dataset_versions": sorted(matches["dataset_version"].astype(str).unique().tolist()),
        "libraries": {
            "scikit_learn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
        "benchmark_reproduction": benchmark,
        "development_verification": development,
        "quality": quality,
        "historical_runtime": {
            "filename": historical_path.name,
            "sha256": sha256_file(historical_path),
            "matches": 1530,
        },
        "artifacts": {},
    }

    artifact_files = (
        ("T-30", "structural_prior_t30_v1.joblib"),
        ("T-14", "structural_prior_t14_v1.joblib"),
        ("T-7", "structural_prior_t7_v1.joblib"),
        ("T-3", "structural_prior_t3_v1.joblib"),
    )
    for horizon, filename in artifact_files:
        runtime = fit_structural_prior_runtime(store, horizon, TRAINING_SEASONS)
        path = output / filename
        joblib.dump(runtime, path, compress=3)
        manifest["artifacts"][horizon] = {
            "filename": filename,
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "model_spec_id": runtime.spec.model_spec_id,
            "model_family": type(runtime.estimator).__name__,
            "feature_contract": runtime.spec.feature_contract,
            "training_rows": runtime.training_rows,
            "numeric_feature_count": len(runtime.numeric_features),
        }

    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
