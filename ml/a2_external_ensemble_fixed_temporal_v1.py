#!/usr/bin/env python3
"""Fixed-temporal robustness audit for the exact a2 ensemble closure winners.

No model-family, variant or ensemble-weight selection occurs here. The exact
T-30/T-7/T-1 contracts selected on 2023/24 in
`a2-external-ensemble-closure-v1` are frozen and replayed through four rolling
season folds, including one earlier pre-selection fold.

This is historical challenger evidence only. It does not mutate Frozen
Pre-Live v2, b2/c2, d2, or production.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import catboost
import lightgbm
import numpy as np
import pandas as pd
import sklearn
import xgboost

from ml.a2_external_ensemble_closure_v1 import (
    candidate_specs,
    current_a2_prediction,
    fit_candidate,
    weighted_prediction,
)
from ml.pre_live_baseline_optimization_v1 import (
    comparison_scorecard,
    eligible_rows,
    load_feature_store,
    metrics,
    sha256_file,
)
from ml.demand_engine.structural_prior_runtime import CURRENT_EARLY_RUNTIME_SPECS

EXPERIMENT = "a2-external-ensemble-fixed-temporal-v1"
WORKSTREAM = "a2 — External/ensemble fixed-temporal robustness"
RANDOM_SEED = 42
BOOTSTRAP_SAMPLES = 10_000
EXPECTED_ATOL = 1e-9
MIN_CLUB_EVENTS = 10
LARGE_DEGRADATION_THRESHOLDS = (500.0, 1000.0, 2000.0, 3000.0)

FOLDS = [
    ("2022/2023", ["2021/2022"], "additional_preselection_historical_fold"),
    ("2023/2024", ["2021/2022", "2022/2023"], "development_selection_season"),
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"], "exposed_reference"),
    (
        "2025/2026",
        ["2021/2022", "2022/2023", "2023/2024", "2024/2025"],
        "exposed_reference",
    ),
]


@dataclass(frozen=True)
class FixedEnsembleContract:
    horizon: str
    member_ids: tuple[str, ...]
    weights: tuple[float, ...]
    source_experiment: str = "a2-external-ensemble-closure-v1"


FIXED_CONTRACTS: dict[str, FixedEnsembleContract] = {
    "T-30": FixedEnsembleContract(
        horizon="T-30",
        member_ids=(
            "current-a2-base",
            "hist31-leaf20-l2-1",
            "catboost-mae-depth6-l2-5",
            "lightgbm-l1-leaves15-l2-5",
            "xgboost-l1-depth3-l2-5",
        ),
        weights=(0.75, 0.0, 0.0, 0.0, 0.25),
    ),
    "T-7": FixedEnsembleContract(
        horizon="T-7",
        member_ids=(
            "current-a2-base",
            "catboost-mae-depth4-l2-5",
            "lightgbm-l1-leaves15-l2-5",
            "xgboost-l1-depth3-l2-5",
        ),
        weights=(0.25, 0.25, 0.50, 0.0),
    ),
    "T-1": FixedEnsembleContract(
        horizon="T-1",
        member_ids=(
            "current-a2-base",
            "hist31-leaf20-l2-1",
            "catboost-mae-depth4-l2-5",
            "lightgbm-l1-leaves15-l2-5",
            "xgboost-l1-depth3-l2-5",
        ),
        weights=(0.0, 0.25, 0.50, 0.25, 0.0),
    ),
}

# Exact reproduction gates from closure run 39624170933. The earlier 2022/23
# rolling fold is new audit evidence, so it intentionally has no expected value.
EXPECTED_REPRODUCTION: dict[str, dict[str, dict[str, float]]] = {
    "T-30": {
        "2023/2024": {"current_a2": 2559.7406941266854, "candidate": 2526.2452034717307},
        "2024/2025": {"current_a2": 1889.3672272292858, "candidate": 1834.434818303733},
        "2025/2026": {"current_a2": 1846.2792557036205, "candidate": 1816.5413180631813},
    },
    "T-7": {
        "2023/2024": {"current_a2": 2317.3395349341495, "candidate": 2308.435275277083},
        "2024/2025": {"current_a2": 1650.9668467458935, "candidate": 1640.6989858884936},
        "2025/2026": {"current_a2": 1773.7952605857984, "candidate": 1745.937314191296},
    },
    "T-1": {
        "2023/2024": {"current_a2": 2347.9931110468183, "candidate": 2292.5322249664005},
        "2024/2025": {"current_a2": 1651.733625020056, "candidate": 1649.466408528945},
        "2025/2026": {"current_a2": 1742.835142803119, "candidate": 1736.555451206648},
    },
}


def validate_fixed_contracts() -> None:
    if set(FIXED_CONTRACTS) != {"T-30", "T-7", "T-1"}:
        raise RuntimeError("fixed contract horizon set changed")
    for horizon, contract in FIXED_CONTRACTS.items():
        if contract.horizon != horizon:
            raise RuntimeError(f"contract horizon mismatch for {horizon}")
        if len(contract.member_ids) != len(contract.weights):
            raise RuntimeError(f"member/weight length mismatch for {horizon}")
        if not np.isclose(sum(contract.weights), 1.0, rtol=0.0, atol=1e-12):
            raise RuntimeError(f"weights do not sum to one for {horizon}")
        if sum(weight > 0 for weight in contract.weights) < 2:
            raise RuntimeError(f"ensemble degenerates to one model for {horizon}")
        available_ids = {item.id for item in candidate_specs(horizon)}
        missing = set(contract.member_ids) - available_ids
        if missing:
            raise RuntimeError(f"unknown members for {horizon}: {sorted(missing)}")


def fixed_candidate_prediction(
    store: pd.DataFrame,
    horizon: str,
    training_seasons: list[str],
    rows: pd.DataFrame,
) -> np.ndarray:
    contract = FIXED_CONTRACTS[horizon]
    specs = {item.id: item for item in candidate_specs(horizon)}
    predictions = [
        fit_candidate(store, horizon, training_seasons, specs[member_id]).predict(rows)
        for member_id in contract.member_ids
    ]
    return weighted_prediction(predictions, contract.weights)


def paired_bootstrap_improvement(
    incumbent_ae: np.ndarray,
    candidate_ae: np.ndarray,
    seed: int,
    samples: int = BOOTSTRAP_SAMPLES,
) -> dict[str, float | int]:
    incumbent_ae = np.asarray(incumbent_ae, dtype=float)
    candidate_ae = np.asarray(candidate_ae, dtype=float)
    if len(incumbent_ae) != len(candidate_ae) or len(incumbent_ae) == 0:
        raise ValueError("paired bootstrap requires equal non-empty arrays")

    improvement = incumbent_ae - candidate_ae
    rng = np.random.default_rng(seed)
    n = len(improvement)
    means = np.empty(samples, dtype=float)
    chunk = 500
    offset = 0
    while offset < samples:
        take = min(chunk, samples - offset)
        idx = rng.integers(0, n, size=(take, n))
        means[offset : offset + take] = improvement[idx].mean(axis=1)
        offset += take

    return {
        "samples": int(samples),
        "seed": int(seed),
        "observed_mean_improvement": float(improvement.mean()),
        "ci95_low": float(np.quantile(means, 0.025)),
        "ci95_high": float(np.quantile(means, 0.975)),
        "probability_improvement_gt_0": float(np.mean(means > 0.0)),
    }


def fold_diagnostics(
    rows: pd.DataFrame,
    incumbent_prediction: np.ndarray,
    candidate_prediction: np.ndarray,
    seed: int,
) -> dict[str, Any]:
    actual = rows["target_attendance"].astype(float).to_numpy()
    incumbent_prediction = np.asarray(incumbent_prediction, dtype=float)
    candidate_prediction = np.asarray(candidate_prediction, dtype=float)
    incumbent_ae = np.abs(incumbent_prediction - actual)
    candidate_ae = np.abs(candidate_prediction - actual)
    degradation = candidate_ae - incumbent_ae
    revision = candidate_prediction - incumbent_prediction
    capacity = rows["capacity"].astype(float).to_numpy()

    thresholds = {
        str(int(threshold)): {
            "count": int(np.sum(degradation > threshold)),
            "rate": float(np.mean(degradation > threshold)),
        }
        for threshold in LARGE_DEGRADATION_THRESHOLDS
    }

    clubs: dict[str, Any] = {}
    frame = pd.DataFrame(
        {
            "club": rows["home_club_key"].astype(str).to_numpy(),
            "incumbent_ae": incumbent_ae,
            "candidate_ae": candidate_ae,
        }
    )
    for club, group in frame.groupby("club", sort=True):
        if len(group) < MIN_CLUB_EVENTS:
            continue
        inc = float(group["incumbent_ae"].mean())
        cand = float(group["candidate_ae"].mean())
        clubs[str(club)] = {
            "n": int(len(group)),
            "incumbent_mae": inc,
            "candidate_mae": cand,
            "mae_improvement": inc - cand,
            "improved": bool(cand < inc),
        }

    return {
        "bootstrap": paired_bootstrap_improvement(incumbent_ae, candidate_ae, seed),
        "degradation_quantiles": {
            "p50": float(np.quantile(degradation, 0.50)),
            "p75": float(np.quantile(degradation, 0.75)),
            "p90": float(np.quantile(degradation, 0.90)),
            "p95": float(np.quantile(degradation, 0.95)),
            "p99": float(np.quantile(degradation, 0.99)),
            "max": float(np.max(degradation)),
        },
        "large_harmful_regressions": thresholds,
        "revision": {
            "mean_abs": float(np.mean(np.abs(revision))),
            "median_abs": float(np.median(np.abs(revision))),
            "p90_abs": float(np.quantile(np.abs(revision), 0.90)),
            "max_abs": float(np.max(np.abs(revision))),
            "mean_abs_share_of_capacity": float(np.mean(np.abs(revision) / capacity)),
            "p90_abs_share_of_capacity": float(
                np.quantile(np.abs(revision) / capacity, 0.90)
            ),
        },
        "club_consistency": {
            "min_events": MIN_CLUB_EVENTS,
            "clubs_reported": int(len(clubs)),
            "clubs_improved": int(sum(1 for value in clubs.values() if value["improved"])),
            "clubs_worsened_or_equal": int(
                sum(1 for value in clubs.values() if not value["improved"])
            ),
            "details": clubs,
        },
    }


def assert_reproduction(
    horizon: str,
    season: str,
    incumbent_mae: float,
    candidate_mae: float,
) -> None:
    expected = EXPECTED_REPRODUCTION.get(horizon, {}).get(season)
    if expected is None:
        return
    if not np.isclose(
        incumbent_mae, expected["current_a2"], rtol=0.0, atol=EXPECTED_ATOL
    ):
        raise RuntimeError(
            f"current a2 reproduction mismatch {horizon}/{season}: "
            f"actual={incumbent_mae} expected={expected['current_a2']}"
        )
    if not np.isclose(
        candidate_mae, expected["candidate"], rtol=0.0, atol=EXPECTED_ATOL
    ):
        raise RuntimeError(
            f"candidate reproduction mismatch {horizon}/{season}: "
            f"actual={candidate_mae} expected={expected['candidate']}"
        )


def score_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    evidence_role: str,
    seed: int,
) -> dict[str, Any]:
    runtime = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = eligible_rows(store, horizon, season, runtime.baseline_column)
    if rows.empty:
        raise RuntimeError(f"empty fold {horizon}/{season}")

    incumbent_prediction = current_a2_prediction(
        store, horizon, training_seasons, rows
    )
    candidate_prediction = fixed_candidate_prediction(
        store, horizon, training_seasons, rows
    )
    actual = rows["target_attendance"].astype(float).to_numpy()

    incumbent_metrics = metrics(actual, incumbent_prediction)
    candidate_metrics = metrics(actual, candidate_prediction)
    assert_reproduction(
        horizon,
        season,
        float(incumbent_metrics["mae"]),
        float(candidate_metrics["mae"]),
    )

    return {
        "horizon": horizon,
        "season": season,
        "evidence_role": evidence_role,
        "training_seasons": list(training_seasons),
        "rows": int(len(rows)),
        "fixed_contract": {
            "member_ids": list(FIXED_CONTRACTS[horizon].member_ids),
            "weights": list(FIXED_CONTRACTS[horizon].weights),
        },
        "scorecard": comparison_scorecard(
            rows, candidate_prediction, incumbent_prediction
        ),
        "diagnostics": fold_diagnostics(
            rows, incumbent_prediction, candidate_prediction, seed
        ),
    }


def summarize_horizon(folds: list[dict[str, Any]]) -> dict[str, Any]:
    improvements = [float(item["scorecard"]["mae_improvement"]) for item in folds]
    incumbent_maes = [float(item["scorecard"]["incumbent"]["mae"]) for item in folds]
    probabilities = [
        float(item["diagnostics"]["bootstrap"]["probability_improvement_gt_0"])
        for item in folds
    ]
    clubs_total = sum(
        int(item["diagnostics"]["club_consistency"]["clubs_reported"])
        for item in folds
    )
    clubs_improved = sum(
        int(item["diagnostics"]["club_consistency"]["clubs_improved"])
        for item in folds
    )
    mean_improvement = float(np.mean(improvements))
    mean_incumbent = float(np.mean(incumbent_maes))
    all_positive = all(value > 0.0 for value in improvements)
    decision = (
        "ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE"
        if all_positive
        else "ROBUSTNESS_REJECT_NOT_ALL_ROLLING_FOLDS_POSITIVE"
    )
    return {
        "decision": decision,
        "fold_count": int(len(folds)),
        "folds_with_positive_mae_improvement": int(sum(value > 0.0 for value in improvements)),
        "all_rolling_folds_positive": all_positive,
        "mean_fold_mae_improvement": mean_improvement,
        "relative_mean_improvement_vs_incumbent": (
            mean_improvement / mean_incumbent if mean_incumbent else float("nan")
        ),
        "median_fold_mae_improvement": float(np.median(improvements)),
        "min_fold_mae_improvement": float(np.min(improvements)),
        "max_fold_mae_improvement": float(np.max(improvements)),
        "minimum_fold_bootstrap_probability_improvement_gt_0": float(
            np.min(probabilities)
        ),
        "maximum_worst_event_degradation_across_folds": max(
            float(item["scorecard"]["worst_event_degradation"]) for item in folds
        ),
        "club_season_cells_reported": int(clubs_total),
        "club_season_cells_improved": int(clubs_improved),
        "club_season_improvement_rate": (
            float(clubs_improved / clubs_total) if clubs_total else float("nan")
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    validate_fixed_contracts()

    manifest = json.loads(args.manifest.read_text())
    actual_hash = sha256_file(args.historical_runtime)
    expected_hash = manifest["historical_runtime"]["sha256"]
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    per_horizon: dict[str, Any] = {}

    for horizon_index, horizon in enumerate(FIXED_CONTRACTS):
        folds = [
            score_fold(
                store,
                horizon,
                season,
                training_seasons,
                evidence_role,
                RANDOM_SEED + horizon_index * 10 + fold_index,
            )
            for fold_index, (season, training_seasons, evidence_role) in enumerate(FOLDS)
        ]
        per_horizon[horizon] = {
            "fixed_contract": {
                "member_ids": list(FIXED_CONTRACTS[horizon].member_ids),
                "weights": list(FIXED_CONTRACTS[horizon].weights),
                "source_experiment": FIXED_CONTRACTS[horizon].source_experiment,
            },
            "folds": folds,
            "summary": summarize_horizon(folds),
        }

    passed = [
        horizon
        for horizon, result in per_horizon.items()
        if result["summary"]["decision"] == "ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE"
    ]
    rejected = [horizon for horizon in per_horizon if horizon not in passed]

    payload = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_FIXED_CONFIG_TEMPORAL_ROBUSTNESS_AUDIT",
        "evidence_class": "HISTORICAL_ROLLING_FIXED_CONFIG_MIXED_EXPOSURE",
        "promotion_allowed": False,
        "production_change": False,
        "frozen_pre_live_mutation": False,
        "protocol": {
            "tuning_or_selection_in_this_audit": False,
            "selection_source_run": 39624170933,
            "folds": [
                {
                    "season": season,
                    "training_seasons": training_seasons,
                    "evidence_role": evidence_role,
                }
                for season, training_seasons, evidence_role in FOLDS
            ],
            "bootstrap_samples_per_fold": BOOTSTRAP_SAMPLES,
            "bootstrap_unit": "event row within fold; paired current-a2-vs-candidate AE",
            "decision_gate": "positive MAE improvement in all four rolling folds",
            "references_are_already_exposed": True,
        },
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_hash,
            "manifest_sha256": sha256_file(args.manifest),
            "artifact_version": manifest.get("artifact_version"),
            "feature_contract": manifest.get("feature_contract"),
            "matches": int(store["match_key"].nunique()),
            "feature_rows": int(len(store)),
        },
        "runtime": {
            "random_seed": RANDOM_SEED,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "catboost": catboost.__version__,
            "lightgbm": lightgbm.__version__,
            "xgboost": xgboost.__version__,
        },
        "expected_reproduction": EXPECTED_REPRODUCTION,
        "horizons": per_horizon,
        "summary": {
            "passed_horizons": passed,
            "rejected_horizons": rejected,
            "passed_count": len(passed),
            "frozen_current_a2_changed": False,
            "frozen_pre_live_changed": False,
            "production_changed": False,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "experiment": EXPERIMENT,
                "summary": payload["summary"],
                "horizons": {
                    horizon: {
                        "decision": result["summary"]["decision"],
                        "fold_improvements": [
                            fold["scorecard"]["mae_improvement"]
                            for fold in result["folds"]
                        ],
                        "mean_improvement": result["summary"]["mean_fold_mae_improvement"],
                        "relative_mean_improvement": result["summary"][
                            "relative_mean_improvement_vs_incumbent"
                        ],
                        "min_bootstrap_p": result["summary"][
                            "minimum_fold_bootstrap_probability_improvement_gt_0"
                        ],
                        "worst_event_degradation": result["summary"][
                            "maximum_worst_event_degradation_across_folds"
                        ],
                    }
                    for horizon, result in per_horizon.items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
