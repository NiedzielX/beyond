#!/usr/bin/env python3
"""Seal the exact Pre-Live v3 historical research candidate.

No tuning or selection occurs here. This gate reproduces the exact mixed-horizon
v3 package that passed `pre-live-v3-fixed-temporal-package-v1`, hard-asserts all
20 horizon-season MAEs, and emits an immutable manifest with source/evidence
hashes. This is a research freeze, not production promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import catboost
import joblib
import lightgbm
import numpy as np
import pandas as pd
import sklearn
import xgboost

from ml.pre_live_baseline_optimization_v1 import load_feature_store, metrics, sha256_file
from ml.pre_live_v3_fixed_temporal_package_v1 import (
    CHANGED_HORIZONS,
    FOLDS,
    candidate_prediction,
)
from ml.pre_live_v3_regime_revalidation_v1 import frozen_v2_for_season, v3_historical_base_for_season

FREEZE_ID = "pre-live-v3-historical-candidate-2026-10-21-v1"
EXPERIMENT = "pre-live-v3-historical-freeze-v1"
HORIZONS = ["T-30", "T-14", "T-7", "T-3", "T-1"]
EXPECTED_ATOL = 1e-9
MANIFEST_FLOAT_DECIMALS = 9

EXPECTED_FINAL_MAE = {
    "T-30": {
        "2022/2023": 2151.1705123012266,
        "2023/2024": 2526.2452034717307,
        "2024/2025": 1834.434818303733,
        "2025/2026": 1816.5413180631813,
    },
    "T-14": {
        "2022/2023": 1986.701536006362,
        "2023/2024": 2339.9504993283904,
        "2024/2025": 1748.4970512511325,
        "2025/2026": 1870.393553818474,
    },
    "T-7": {
        "2022/2023": 1880.9364117629486,
        "2023/2024": 2235.391355367507,
        "2024/2025": 1630.112559463305,
        "2025/2026": 1711.095982768726,
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
        "historical_base": "ensemble(current-a2-base=0.75,xgboost-l1-depth3-l2-5=0.25)",
        "current_season_regime": "NO_ADJUSTMENT",
        "historical_context_extension": "NO_CONTEXT",
    },
    "T-14": {
        "historical_base": "structural-prior-runtime-v1-t14-hist-base",
        "current_season_regime": "NO_ADJUSTMENT",
        "historical_context_extension": "NO_CONTEXT",
    },
    "T-7": {
        "historical_base": "ensemble(current-a2-base=0.25,catboost-mae-depth4-l2-5=0.25,lightgbm-l1-leaves15-l2-5=0.50)",
        "current_season_regime": "ewma50-resid-k4-cap05-min2",
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
    "ml/a2_external_ensemble_closure_v1.py",
    "ml/a2_external_ensemble_fixed_temporal_v1.py",
    "ml/current_season_residual_regime_v1.py",
    "ml/current_season_regime_maturity_stage2_v1.py",
    "ml/current_season_regime_fixed_temporal_audit_v1.py",
    "ml/pre_live_v2_historical_freeze_v1.py",
    "ml/pre_live_v3_regime_revalidation_v1.py",
    "ml/pre_live_v3_fixed_temporal_package_v1.py",
    "ml/features/structural_prior_feature_store_v1.py",
    "ml/demand_engine/structural_prior_runtime.py",
]

EVIDENCE_FILES = [
    "ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md",
    "ml/results/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1_2026-10-21.md",
    "ml/results/PRE_LIVE_V3_REGIME_REVALIDATION_V1_2026-10-21.md",
    "ml/results/PRE_LIVE_V3_FIXED_TEMPORAL_PACKAGE_V1_2026-10-21.md",
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_metric(value: float) -> float:
    return round(float(value), MANIFEST_FLOAT_DECIMALS)


def canonicalize_floats(value: Any) -> Any:
    if isinstance(value, float):
        return canonical_metric(value)
    if isinstance(value, dict):
        return {key: canonicalize_floats(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonicalize_floats(item) for item in value]
    return value


def verify_mae(horizon: str, season: str, actual: float) -> None:
    expected = float(EXPECTED_FINAL_MAE[horizon][season])
    if not np.isclose(actual, expected, rtol=0.0, atol=EXPECTED_ATOL):
        raise RuntimeError(
            f"Pre-Live v3 freeze reproduction mismatch {horizon}/{season}: "
            f"actual={actual} expected={expected}"
        )


def score_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
) -> dict[str, Any]:
    if horizon in CHANGED_HORIZONS:
        rows, prediction, runtime_contract = candidate_prediction(
            store, horizon, season, training_seasons
        )
    else:
        base = v3_historical_base_for_season(store, horizon, season, training_seasons)
        prediction, frozen_diag = frozen_v2_for_season(
            store, horizon, season, training_seasons, base.rows
        )
        rows = base.rows
        runtime_contract = {
            "historical_model_id": base.model_id,
            "current_season_regime": frozen_diag["policy_id"],
            "unchanged_from_frozen_v2": True,
        }

    value = float(metrics(rows["target_attendance"], prediction)["mae"])
    verify_mae(horizon, season, value)
    return {
        "season": season,
        "training_seasons": list(training_seasons),
        "rows": int(len(rows)),
        "final_mae": value,
        "runtime_contract": runtime_contract,
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
    horizons: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        folds = [
            score_fold(store, horizon, season, training_seasons)
            for season, training_seasons in FOLDS
        ]
        horizons.append({
            "horizon": horizon,
            "contract": CONTRACT[horizon],
            "folds": folds,
            "mean_four_fold_mae": float(np.mean([fold["final_mae"] for fold in folds])),
            "reference_mean_mae": float(np.mean([
                fold["final_mae"]
                for fold in folds
                if fold["season"] in {"2024/2025", "2025/2026"}
            ])),
        })

    source_hashes = {
        path: file_sha256(args.repo_root / path)
        for path in SOURCE_FILES
    }
    evidence_hashes = {
        path: file_sha256(args.repo_root / path)
        for path in EVIDENCE_FILES
    }

    raw_manifest = {
        "freeze_id": FREEZE_ID,
        "experiment": EXPERIMENT,
        "status": "FROZEN_HISTORICAL_RESEARCH_CANDIDATE",
        "candidate_scope": "historical_pre_live_v3_mixed_horizon",
        "production_promotion": False,
        "production_change": False,
        "track_a_replacement": False,
        "live_adjustment": 0,
        "selection_performed": False,
        "historical_context_extension": "NO_CONTEXT_ALL_HORIZONS",
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_input_hash,
            "input_manifest_path": str(args.input_manifest),
            "input_manifest_sha256": sha256_file(args.input_manifest),
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
            "catboost": catboost.__version__,
            "lightgbm": lightgbm.__version__,
            "xgboost": xgboost.__version__,
        },
        "manifest_float_decimals": MANIFEST_FLOAT_DECIMALS,
        "expected_final_mae": EXPECTED_FINAL_MAE,
        "horizons": horizons,
        "parent_evidence": {
            "regime_revalidation_run_id": 39627633502,
            "regime_revalidation_artifact_id": 12357223004,
            "regime_revalidation_json_sha256": "020685afde0d3becd0bd115a020df558360f55931638ce8cf6b875312ca7def6",
            "fixed_package_run_id": 39628607689,
            "fixed_package_artifact_id": 12358477269,
            "fixed_package_json_sha256": "f7c665b861cbd9cc7a7d8fd859c8b97a174c65bdad8888b14dee2dc7b20ebf01",
        },
        "limitations": [
            "The 2024/25 and 2025/26 reference seasons are exposed historical references, not fresh prospective validation.",
            "The package-level MAE gain versus Frozen Pre-Live v2 is modest because only T-30 and T-7 change.",
            "T-30 and T-7 retain material event-level tail degradation despite positive four-fold MAE.",
            "Historical c2 remains no-context; forward-only context is not backfilled.",
            "This research freeze does not replace the Track-A Frozen Pre-Live v2 / Ridge / P2 package or production behavior.",
        ],
        "next_workstream": "d2_v3_rebuild_against_frozen_pre_live_v3_research_anchor",
    }

    manifest = canonicalize_floats(raw_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "freeze_id": FREEZE_ID,
        "status": manifest["status"],
        "production_change": False,
        "track_a_replacement": False,
        "horizons": [
            {
                "horizon": row["horizon"],
                "reference_mean_mae": row["reference_mean_mae"],
                "contract": row["contract"],
            }
            for row in manifest["horizons"]
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
