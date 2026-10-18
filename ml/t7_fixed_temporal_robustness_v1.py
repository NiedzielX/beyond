#!/usr/bin/env python3
"""Fixed-config temporal robustness audit for the strongest T-7 challenger.

No tuning or model selection occurs here. The Stage-3 winner
`hist31-leaf20-l2-1` is frozen and replayed through rolling season folds to
measure stability, tails, club consistency and paired uncertainty before any
T-7 freeze/promotion decision.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.demand_engine.structural_prior_runtime import CURRENT_EARLY_RUNTIME_SPECS, fit_structural_prior_runtime
from ml.pre_live_baseline_optimization_v1 import eligible_rows, load_feature_store, metrics, sha256_file
from ml.t7_robust_estimator_v1 import CANDIDATES, fit_estimator, score_candidate

EXPERIMENT = "t7-fixed-temporal-robustness-v1"
WORKSTREAM = "a2 — Historical / Structural Prior optimization — T-7 fixed-config temporal robustness"
HORIZON = "T-7"
RANDOM_SEED = 42
BOOTSTRAP_SAMPLES = 10_000

FOLDS = [
    ("2022/2023", ["2021/2022"], "additional_preselection_historical_fold"),
    ("2023/2024", ["2021/2022", "2022/2023"], "development_selection_season"),
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"], "exposed_reference"),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"], "exposed_reference"),
]

FIXED_CANDIDATE_ID = "hist31-leaf20-l2-1"
FIXED_CANDIDATE = next(candidate for candidate in CANDIDATES if candidate.id == FIXED_CANDIDATE_ID)

# Exact canonical Stage-3 reproduction gates. The 2022/23 fold is new audit
# evidence and therefore intentionally has no pre-existing expected value.
EXPECTED_FIXED_MAE = {
    "2023/2024": 2317.3395349341495,
    "2024/2025": 1650.9668467458935,
    "2025/2026": 1773.7952605857984,
}
EXPECTED_ATOL = 1e-9

LARGE_DEGRADATION_THRESHOLDS = (500.0, 1000.0, 2000.0, 3000.0)
MIN_CLUB_EVENTS = 10


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
    # Chunk to avoid creating one huge 10k x N allocation unnecessarily.
    means = np.empty(samples, dtype=float)
    chunk = 500
    offset = 0
    while offset < samples:
        take = min(chunk, samples - offset)
        idx = rng.integers(0, n, size=(take, n))
        means[offset:offset + take] = improvement[idx].mean(axis=1)
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
    frame = pd.DataFrame({
        "club": rows["home_club_key"].astype(str).to_numpy(),
        "incumbent_ae": incumbent_ae,
        "candidate_ae": candidate_ae,
    })
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
            "p90_abs_share_of_capacity": float(np.quantile(np.abs(revision) / capacity, 0.90)),
        },
        "club_consistency": {
            "min_events": MIN_CLUB_EVENTS,
            "clubs_reported": int(len(clubs)),
            "clubs_improved": int(sum(1 for value in clubs.values() if value["improved"])),
            "clubs_worsened_or_equal": int(sum(1 for value in clubs.values() if not value["improved"])),
            "details": clubs,
        },
    }


def score_fold(
    store: pd.DataFrame,
    season: str,
    training_seasons: list[str],
    evidence_role: str,
    fold_index: int,
) -> dict[str, Any]:
    runtime_spec = CURRENT_EARLY_RUNTIME_SPECS[HORIZON]
    rows = eligible_rows(store, HORIZON, season, runtime_spec.baseline_column)
    if rows.empty:
        raise RuntimeError(f"empty fold {season}")

    incumbent = fit_structural_prior_runtime(store, HORIZON, training_seasons)
    incumbent_prediction = incumbent.predict(rows)
    fitted = fit_estimator(store, training_seasons, FIXED_CANDIDATE)
    candidate_prediction = fitted.predict(rows)

    actual = rows["target_attendance"].astype(float).to_numpy()
    incumbent_metrics = metrics(actual, incumbent_prediction)
    candidate_metrics = metrics(actual, candidate_prediction)

    expected = EXPECTED_FIXED_MAE.get(season)
    if expected is not None and not np.isclose(
        float(candidate_metrics["mae"]), expected, rtol=0.0, atol=EXPECTED_ATOL
    ):
        raise RuntimeError(
            f"fixed challenger reproduction mismatch {season}: "
            f"actual={candidate_metrics['mae']} expected={expected}"
        )

    scorecard = score_candidate(rows, candidate_prediction, incumbent_prediction)
    return {
        "season": season,
        "evidence_role": evidence_role,
        "training_seasons": list(training_seasons),
        "rows": int(len(rows)),
        "incumbent_training_rows": int(incumbent.training_rows),
        "candidate_training_rows": int(fitted.training_rows),
        "candidate_mae_reproduction_expected": expected,
        "scorecard": scorecard,
        "diagnostics": fold_diagnostics(
            rows,
            incumbent_prediction,
            candidate_prediction,
            RANDOM_SEED + fold_index,
        ),
    }


def pooled_summary(folds: list[dict[str, Any]]) -> dict[str, Any]:
    mae_improvements = [float(fold["scorecard"]["mae_improvement"]) for fold in folds]
    clubs_total = sum(int(fold["diagnostics"]["club_consistency"]["clubs_reported"]) for fold in folds)
    clubs_improved = sum(int(fold["diagnostics"]["club_consistency"]["clubs_improved"]) for fold in folds)
    probabilities = [
        float(fold["diagnostics"]["bootstrap"]["probability_improvement_gt_0"])
        for fold in folds
    ]
    max_harm = max(float(fold["scorecard"]["worst_event_degradation"]) for fold in folds)
    return {
        "fold_count": int(len(folds)),
        "folds_with_positive_mae_improvement": int(sum(value > 0.0 for value in mae_improvements)),
        "mean_fold_mae_improvement": float(np.mean(mae_improvements)),
        "median_fold_mae_improvement": float(np.median(mae_improvements)),
        "min_fold_mae_improvement": float(np.min(mae_improvements)),
        "max_fold_mae_improvement": float(np.max(mae_improvements)),
        "minimum_fold_bootstrap_probability_improvement_gt_0": float(np.min(probabilities)),
        "maximum_worst_event_degradation_across_folds": max_harm,
        "club_season_cells_reported": int(clubs_total),
        "club_season_cells_improved": int(clubs_improved),
        "club_season_improvement_rate": float(clubs_improved / clubs_total) if clubs_total else float("nan"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    actual_hash = sha256_file(args.historical_runtime)
    expected_hash = manifest["historical_runtime"]["sha256"]
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    folds = [
        score_fold(store, season, train, role, index)
        for index, (season, train, role) in enumerate(FOLDS)
    ]

    result = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_FIXED_CONFIG_TEMPORAL_ROBUSTNESS_AUDIT",
        "evidence_class": "HISTORICAL_ROLLING_FIXED_CONFIG_MIXED_EXPOSURE",
        "promotion_allowed": False,
        "production_change": False,
        "horizon": HORIZON,
        "fixed_candidate": {
            "id": FIXED_CANDIDATE_ID,
            "spec": FIXED_CANDIDATE.__dict__,
            "stage3_result": "ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md",
            "stage3_json_sha256": "83da3d85daa7c7bc844b8cb6b63cdf47070068cdabb774d0f4c01e5a3e0258fe",
        },
        "protocol": {
            "tuning_or_selection_in_this_audit": False,
            "folds": [
                {"season": season, "training_seasons": train, "evidence_role": role}
                for season, train, role in FOLDS
            ],
            "bootstrap_samples_per_fold": BOOTSTRAP_SAMPLES,
            "bootstrap_unit": "event row within fold; paired incumbent-vs-candidate AE",
            "bootstrap_seed_base": RANDOM_SEED,
            "large_degradation_thresholds": list(LARGE_DEGRADATION_THRESHOLDS),
            "club_breakdown_min_events": MIN_CLUB_EVENTS,
            "references_are_already_exposed": True,
        },
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_hash,
            "artifact_version": manifest.get("artifact_version"),
            "feature_contract": manifest.get("feature_contract"),
            "historical_dataset_versions": manifest.get("historical_dataset_versions"),
            "matches": int(store["match_key"].nunique()),
            "feature_rows": int(len(store)),
        },
        "runtime": {
            "random_seed": RANDOM_SEED,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "exact_candidate_mae_assertions": EXPECTED_FIXED_MAE,
        "folds": folds,
        "summary": pooled_summary(folds),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "fixed_candidate": FIXED_CANDIDATE_ID,
        "promotion_allowed": False,
        "folds": [
            {
                "season": fold["season"],
                "role": fold["evidence_role"],
                "incumbent_mae": fold["scorecard"]["incumbent"]["mae"],
                "candidate_mae": fold["scorecard"]["candidate"]["mae"],
                "mae_improvement": fold["scorecard"]["mae_improvement"],
                "bootstrap_p_improvement": fold["diagnostics"]["bootstrap"]["probability_improvement_gt_0"],
                "worst_degradation": fold["scorecard"]["worst_event_degradation"],
            }
            for fold in folds
        ],
        "summary": result["summary"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
