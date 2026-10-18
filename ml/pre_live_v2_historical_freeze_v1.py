#!/usr/bin/env python3
"""Freeze the exact historical Pre-Live v2 candidate stack.

No tuning or selection occurs here. This gate reproduces the settled a2+b2
historical candidate contract after c2 found no incremental historical context
uplift. It hard-asserts exact final MAE for all 5 horizons across the four
rolling seasons and emits a manifest with input + source-code hashes.

Manifest floating metrics are canonicalized to 9 decimal places *after* raw
reproduction assertions. This keeps the freeze hash stable across harmless
sub-1e-9 floating representation differences while preserving the exact model
gate at EXPECTED_ATOL=1e-9.

This is a historical candidate freeze, not a production promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.current_season_regime_fixed_temporal_audit_v1 import (
    FOLDS,
    score_fold as score_b2_fold,
)
from ml.current_season_residual_regime_v1 import base_predictions_for_season
from ml.pre_live_baseline_optimization_v1 import load_feature_store, metrics, sha256_file

FREEZE_ID = "pre-live-v2-historical-candidate-2026-10-18-v1"
EXPERIMENT = "pre-live-v2-historical-freeze-v1"
HORIZONS = ["T-30", "T-14", "T-7", "T-3", "T-1"]
B2_HORIZONS = {"T-7", "T-3", "T-1"}
EXPECTED_ATOL = 1e-9
MANIFEST_FLOAT_DECIMALS = 9

EXPECTED_FINAL_MAE = {
    "T-30": {
        "2022/2023": 2157.1473613912335,
        "2023/2024": 2559.7406941266854,
        "2024/2025": 1889.3672272292858,
        "2025/2026": 1846.2792557036205,
    },
    "T-14": {
        "2022/2023": 1986.701536006362,
        "2023/2024": 2339.9504993283904,
        "2024/2025": 1748.4970512511325,
        "2025/2026": 1870.393553818474,
    },
    "T-7": {
        "2022/2023": 1891.8569676571947,
        "2023/2024": 2246.567509322297,
        "2024/2025": 1643.8199399385203,
        "2025/2026": 1738.980778795042,
    },
    "T-3": {
        "2022/2023": 1826.9503009277796,
        "2023/2024": 2190.79000146779,
        "2024/2025": 1611.374341513805,
        "2025/2026": 1753.8914942230822,
    },
    "T-1": {
        "2022/2023": 1794.2577798538857,
        "2023/2024": 2261.110393081583,
        "2024/2025": 1627.0746389116598,
        "2025/2026": 1695.9606369653366,
    },
}

CONTRACT = {
    "T-30": {
        "historical_base": "structural-prior-runtime-v1-t30-extra-full",
        "current_season_regime": "NO_ADJUSTMENT",
        "historical_context_extension": "NO_CONTEXT",
    },
    "T-14": {
        "historical_base": "structural-prior-runtime-v1-t14-hist-base",
        "current_season_regime": "NO_ADJUSTMENT",
        "historical_context_extension": "NO_CONTEXT",
    },
    "T-7": {
        "historical_base": "hist31-leaf20-l2-1",
        "current_season_regime": "ewma50-resid-k6-cap05-min3",
        "historical_context_extension": "NO_CONTEXT",
    },
    "T-3": {
        "historical_base": "structural-prior-runtime-v1-t3-hist-full",
        "current_season_regime": "ewma50-resid-k2-cap05-min3",
        "historical_context_extension": "NO_CONTEXT",
    },
    "T-1": {
        "historical_base": "structural-prior-runtime-v1-t1-hist-full",
        "current_season_regime": "ewma50-resid-k6-cap05-min3",
        "historical_context_extension": "NO_CONTEXT",
    },
}

SOURCE_FILES = [
    "ml/demand_engine/structural_prior_runtime.py",
    "ml/t7_robust_estimator_v1.py",
    "ml/current_season_residual_regime_v1.py",
    "ml/current_season_regime_fixed_temporal_audit_v1.py",
    "ml/features/structural_prior_feature_store_v1.py",
]

EVIDENCE = [
    "ml/results/T7_FIXED_TEMPORAL_ROBUSTNESS_V1_2026-10-18.md",
    "ml/results/PRE_LIVE_UNRESOLVED_MULTIFOLD_V1_2026-10-18.md",
    "ml/results/CURRENT_SEASON_REGIME_FIXED_TEMPORAL_AUDIT_V1_2026-10-18.md",
    "ml/results/CONTEXT_EXTENSION_V2_2026-10-18.md",
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_metric(value: float) -> float:
    return round(float(value), MANIFEST_FLOAT_DECIMALS)


def canonicalize_manifest_floats(value: Any) -> Any:
    if isinstance(value, float):
        return canonical_metric(value)
    if isinstance(value, dict):
        return {key: canonicalize_manifest_floats(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonicalize_manifest_floats(item) for item in value]
    return value


def verify_mae(horizon: str, season: str, actual: float) -> None:
    expected = EXPECTED_FINAL_MAE[horizon][season]
    if not np.isclose(actual, expected, rtol=0.0, atol=EXPECTED_ATOL):
        raise RuntimeError(
            f"Pre-Live v2 freeze reproduction mismatch {horizon}/{season}: "
            f"actual={actual} expected={expected}"
        )


def score_no_b2_fold(store, horizon: str, season: str, training_seasons: list[str]) -> dict[str, Any]:
    base = base_predictions_for_season(store, horizon, season, training_seasons)
    value = float(metrics(base.rows["target_attendance"], base.prediction)["mae"])
    verify_mae(horizon, season, value)
    return {
        "season": season,
        "training_seasons": list(training_seasons),
        "rows": int(len(base.rows)),
        "final_mae": value,
        "base_model_id": base.model_id,
        "current_season_regime": "NO_ADJUSTMENT",
        "historical_context_extension": "NO_CONTEXT",
    }


def score_final_fold(store, horizon: str, season: str, training_seasons: list[str]) -> dict[str, Any]:
    if horizon not in B2_HORIZONS:
        return score_no_b2_fold(store, horizon, season, training_seasons)
    fold = score_b2_fold(store, horizon, season, training_seasons)
    value = float(fold["candidate_mae"])
    verify_mae(horizon, season, value)
    return {
        "season": season,
        "training_seasons": list(training_seasons),
        "rows": int(fold["test_rows"]),
        "final_mae": value,
        "base_model_id": fold["base_model_id"],
        "current_season_regime": fold["fixed_candidate_id"],
        "historical_context_extension": "NO_CONTEXT",
        "base_mae_before_b2": float(fold["base_mae"]),
        "b2_mae_improvement": float(fold["mae_improvement"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    input_manifest = json.loads(args.input_manifest.read_text())
    expected_input_hash = input_manifest["historical_runtime"]["sha256"]
    actual_input_hash = sha256_file(args.historical_runtime)
    if actual_input_hash != expected_input_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_input_hash} expected={expected_input_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    horizons = []
    for horizon in HORIZONS:
        folds = [
            score_final_fold(store, horizon, season, training_seasons)
            for season, training_seasons in FOLDS
        ]
        horizons.append({
            "horizon": horizon,
            "contract": CONTRACT[horizon],
            "folds": folds,
            "mean_four_fold_mae": float(np.mean([fold["final_mae"] for fold in folds])),
            "reference_2024_2025_mean_mae": float(np.mean([
                fold["final_mae"] for fold in folds
                if fold["season"] in {"2024/2025", "2025/2026"}
            ])),
        })

    source_hashes = {
        path: file_sha256(args.repo_root / path)
        for path in SOURCE_FILES
    }
    evidence_hashes = {
        path: file_sha256(args.repo_root / path)
        for path in EVIDENCE
    }

    raw_manifest = {
        "freeze_id": FREEZE_ID,
        "experiment": EXPERIMENT,
        "status": "FROZEN_HISTORICAL_CANDIDATE",
        "candidate_scope": "historical_pre_live_v2",
        "production_promotion": False,
        "production_change": False,
        "live_adjustment": 0,
        "selection_performed": False,
        "c2_historical_extension": "NO_CONTEXT_ALL_HORIZONS",
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_input_hash,
            "input_manifest_path": str(args.input_manifest),
            "artifact_version": input_manifest.get("artifact_version"),
            "feature_contract": input_manifest.get("feature_contract"),
            "historical_dataset_versions": input_manifest.get("historical_dataset_versions"),
            "matches": int(store["match_key"].nunique()),
            "feature_rows": int(len(store)),
        },
        "source_sha256": source_hashes,
        "evidence_sha256": evidence_hashes,
        "runtime": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "manifest_float_decimals": MANIFEST_FLOAT_DECIMALS,
        "expected_final_mae": EXPECTED_FINAL_MAE,
        "horizons": horizons,
        "limitations": [
            "Historical reference seasons are exposed and are not fresh prospective validation.",
            "b2 tail risk and club-level heterogeneity remain explicit despite positive aggregate MAE.",
            "Forward-only rivalry, absence, hype and media context are not backfilled into historical c2.",
            "This manifest freezes a historical candidate contract, not production behavior.",
        ],
        "next_workstream": "d2_continuous_live_updater_against_frozen_pre_live_v2",
    }
    manifest = canonicalize_manifest_floats(raw_manifest)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "freeze_id": FREEZE_ID,
        "status": manifest["status"],
        "production_change": False,
        "manifest_float_decimals": MANIFEST_FLOAT_DECIMALS,
        "horizons": [
            {
                "horizon": row["horizon"],
                "reference_mean_mae": row["reference_2024_2025_mean_mae"],
                "contract": row["contract"],
            }
            for row in manifest["horizons"]
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
