#!/usr/bin/env python3
"""Fixed-config maturity / robustness audit for b2 current-season regime winners.

No signal family, shrinkage, cap or horizon is selected in this audit.
The exact b2 v1 winners are frozen:
- T-7: ewma50-resid-k6-cap05
- T-3: ewma50-resid-k2-cap05
- T-1: ewma50-resid-k6-cap05

T-30 and T-14 are excluded because b2 v1 selected NO_ADJUSTMENT.

The audit replays four rolling seasons, checks overall and conditional quality by
number of prior completed same-season home matches, paired uncertainty, tail
risk, correction magnitude and club consistency. It does not change production.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.current_season_residual_regime_v1 import (
    RegimeVariant,
    add_same_season_residual_state,
    apply_variant,
    base_predictions_for_season,
    score_fold,
)
from ml.pre_live_baseline_optimization_v1 import metrics, load_feature_store, sha256_file

EXPERIMENT = "current-season-regime-maturity-v1"
WORKSTREAM = "b2 — Current-season regime — fixed-config maturity and robustness"
RANDOM_SEED = 42
BOOTSTRAP_SAMPLES = 10_000

FOLDS = (
    ("2022/2023", ["2021/2022"], "development_fold_1"),
    ("2023/2024", ["2021/2022", "2022/2023"], "development_fold_2"),
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"], "exposed_reference_1"),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"], "exposed_reference_2"),
)

FIXED_VARIANTS: dict[str, RegimeVariant] = {
    "T-7": RegimeVariant(source="ewma50_residual_fraction", shrink_k=6),
    "T-3": RegimeVariant(source="ewma50_residual_fraction", shrink_k=2),
    "T-1": RegimeVariant(source="ewma50_residual_fraction", shrink_k=6),
}

EXPECTED_VARIANT_IDS = {
    "T-7": "ewma50-resid-k6-cap05",
    "T-3": "ewma50-resid-k2-cap05",
    "T-1": "ewma50-resid-k6-cap05",
}

LARGE_DEGRADATION_THRESHOLDS = (500.0, 1000.0, 2000.0, 3000.0)
BUCKETS = ("0", "1", "2", "3+")
MIN_CLUB_N = 5


def paired_bootstrap_improvement(
    incumbent_ae: np.ndarray,
    candidate_ae: np.ndarray,
    seed: int,
    samples: int = BOOTSTRAP_SAMPLES,
) -> dict[str, float | int]:
    incumbent_ae = np.asarray(incumbent_ae, dtype=float)
    candidate_ae = np.asarray(candidate_ae, dtype=float)
    if len(incumbent_ae) == 0 or len(incumbent_ae) != len(candidate_ae):
        raise ValueError("paired bootstrap requires equal non-empty arrays")
    improvement = incumbent_ae - candidate_ae
    n = len(improvement)
    rng = np.random.default_rng(seed)
    means = np.empty(samples, dtype=float)
    chunk = 500
    offset = 0
    while offset < samples:
        take = min(chunk, samples - offset)
        indices = rng.integers(0, n, size=(take, n))
        means[offset:offset + take] = improvement[indices].mean(axis=1)
        offset += take
    return {
        "samples": int(samples),
        "seed": int(seed),
        "observed_mean_improvement": float(improvement.mean()),
        "ci95_low": float(np.quantile(means, 0.025)),
        "ci95_high": float(np.quantile(means, 0.975)),
        "probability_improvement_gt_0": float(np.mean(means > 0.0)),
    }


def bucket_label(n: int) -> str:
    if n <= 0:
        return "0"
    if n == 1:
        return "1"
    if n == 2:
        return "2"
    return "3+"


def detailed_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    evidence_role: str,
    fold_index: int,
) -> dict[str, Any]:
    variant = FIXED_VARIANTS[horizon]
    if variant.id != EXPECTED_VARIANT_IDS[horizon]:
        raise RuntimeError(
            f"fixed b2 variant drift {horizon}: actual={variant.id} expected={EXPECTED_VARIANT_IDS[horizon]}"
        )

    # score_fold reuses canonical b2 base assertions and PIT state builder.
    scored = score_fold(store, horizon, season, training_seasons, [variant])
    canonical = scored["candidates"][variant.id]

    # Recompute predictions through the same canonical functions only to retain
    # paired per-event arrays for additional diagnostics.
    base = base_predictions_for_season(store, horizon, season, training_seasons)
    rows = add_same_season_residual_state(base.rows, base.prediction)
    candidate_prediction, correction_diag = apply_variant(rows, base.prediction, variant)
    actual = rows["target_attendance"].astype(float).to_numpy()
    base_prediction = np.asarray(base.prediction, dtype=float)
    candidate_prediction = np.asarray(candidate_prediction, dtype=float)
    base_ae = np.abs(base_prediction - actual)
    candidate_ae = np.abs(candidate_prediction - actual)
    degradation = candidate_ae - base_ae

    # Assert the independently retained scorecard agrees with canonical b2 path.
    candidate_mae = float(np.mean(candidate_ae))
    canonical_mae = float(canonical["scorecard"]["candidate"]["mae"])
    if not np.isclose(candidate_mae, canonical_mae, rtol=0.0, atol=1e-9):
        raise RuntimeError(
            f"candidate replay mismatch {horizon}/{season}: replay={candidate_mae} canonical={canonical_mae}"
        )

    prior_n = rows["regime_prior_home_matches"].astype(int).to_numpy()
    maturity: dict[str, Any] = {}
    for bucket in BUCKETS:
        mask = np.asarray([bucket_label(int(value)) == bucket for value in prior_n], dtype=bool)
        if not np.any(mask):
            maturity[bucket] = {"n": 0}
            continue
        inc_metrics = metrics(actual[mask], base_prediction[mask])
        cand_metrics = metrics(actual[mask], candidate_prediction[mask])
        maturity[bucket] = {
            "n": int(np.sum(mask)),
            "base_mae": float(inc_metrics["mae"]),
            "candidate_mae": float(cand_metrics["mae"]),
            "mae_improvement": float(inc_metrics["mae"] - cand_metrics["mae"]),
            "base_median_ae": float(inc_metrics["median_ae"]),
            "candidate_median_ae": float(cand_metrics["median_ae"]),
            "base_p90_ae": float(inc_metrics["p90_ae"]),
            "candidate_p90_ae": float(cand_metrics["p90_ae"]),
            "bootstrap": paired_bootstrap_improvement(
                base_ae[mask],
                candidate_ae[mask],
                seed=RANDOM_SEED + fold_index * 10 + BUCKETS.index(bucket),
                samples=BOOTSTRAP_SAMPLES,
            ),
        }

    club_rows = []
    club_frame = pd.DataFrame({
        "club": rows["home_club_key"].astype(str).to_numpy(),
        "actual": actual,
        "base": base_prediction,
        "candidate": candidate_prediction,
    })
    for club, group in club_frame.groupby("club", sort=True):
        if len(group) < MIN_CLUB_N:
            continue
        y = group["actual"].astype(float).to_numpy()
        bp = group["base"].astype(float).to_numpy()
        cp = group["candidate"].astype(float).to_numpy()
        base_mae = float(np.mean(np.abs(bp - y)))
        candidate_club_mae = float(np.mean(np.abs(cp - y)))
        club_rows.append({
            "club": str(club),
            "n": int(len(group)),
            "base_mae": base_mae,
            "candidate_mae": candidate_club_mae,
            "mae_improvement": base_mae - candidate_club_mae,
            "improved": bool(candidate_club_mae < base_mae),
        })

    return {
        "season": season,
        "evidence_role": evidence_role,
        "training_seasons": list(training_seasons),
        "variant": asdict(variant) | {"id": variant.id},
        "rows": int(len(rows)),
        "canonical_b2_scorecard": canonical["scorecard"],
        "canonical_b2_regime_coverage": canonical["diagnostics"],
        "bootstrap_all_rows": paired_bootstrap_improvement(
            base_ae,
            candidate_ae,
            seed=RANDOM_SEED + fold_index,
            samples=BOOTSTRAP_SAMPLES,
        ),
        "degradation_quantiles": {
            "p50": float(np.quantile(degradation, 0.50)),
            "p75": float(np.quantile(degradation, 0.75)),
            "p90": float(np.quantile(degradation, 0.90)),
            "p95": float(np.quantile(degradation, 0.95)),
            "p99": float(np.quantile(degradation, 0.99)),
            "max": float(np.max(degradation)),
        },
        "large_harmful_regressions": {
            str(int(threshold)): {
                "count": int(np.sum(degradation > threshold)),
                "rate": float(np.mean(degradation > threshold)),
            }
            for threshold in LARGE_DEGRADATION_THRESHOLDS
        },
        "maturity_by_prior_home_matches": maturity,
        "club_consistency": {
            "min_n": MIN_CLUB_N,
            "clubs_reported": int(len(club_rows)),
            "clubs_improved": int(sum(1 for row in club_rows if row["improved"])),
            "clubs_worsened_or_equal": int(sum(1 for row in club_rows if not row["improved"])),
            "details": club_rows,
        },
        "correction_replay": correction_diag,
    }


def horizon_summary(folds: list[dict[str, Any]]) -> dict[str, Any]:
    improvements = [
        float(fold["canonical_b2_scorecard"]["mae_improvement"])
        for fold in folds
    ]
    probabilities = [
        float(fold["bootstrap_all_rows"]["probability_improvement_gt_0"])
        for fold in folds
    ]
    clubs_reported = sum(int(fold["club_consistency"]["clubs_reported"]) for fold in folds)
    clubs_improved = sum(int(fold["club_consistency"]["clubs_improved"]) for fold in folds)
    return {
        "folds": int(len(folds)),
        "positive_mae_folds": int(sum(value > 0.0 for value in improvements)),
        "mean_fold_mae_improvement": float(np.mean(improvements)),
        "median_fold_mae_improvement": float(np.median(improvements)),
        "min_fold_mae_improvement": float(np.min(improvements)),
        "max_fold_mae_improvement": float(np.max(improvements)),
        "minimum_bootstrap_probability_improvement_gt_0": float(np.min(probabilities)),
        "maximum_worst_event_degradation": float(max(
            fold["canonical_b2_scorecard"]["worst_event_degradation"]
            for fold in folds
        )),
        "club_season_cells_reported": int(clubs_reported),
        "club_season_cells_improved": int(clubs_improved),
        "club_season_improvement_rate": float(clubs_improved / clubs_reported) if clubs_reported else float("nan"),
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
    horizons = []
    for horizon, variant in FIXED_VARIANTS.items():
        folds = [
            detailed_fold(store, horizon, season, train, role, index)
            for index, (season, train, role) in enumerate(FOLDS)
        ]
        horizons.append({
            "horizon": horizon,
            "fixed_variant": asdict(variant) | {"id": variant.id},
            "folds": folds,
            "summary": horizon_summary(folds),
        })

    payload = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_FIXED_CONFIG_B2_MATURITY_AUDIT",
        "evidence_class": "TWO_DEVELOPMENT_SEASONS_PLUS_EXPOSED_REFERENCES_FIXED_CONFIG",
        "promotion_allowed": False,
        "production_change": False,
        "excluded_horizons": {
            "T-30": "b2 v1 selected NO_ADJUSTMENT",
            "T-14": "b2 v1 selected NO_ADJUSTMENT",
        },
        "protocol": {
            "model_or_variant_selection_in_this_audit": False,
            "folds": [
                {"season": season, "training_seasons": train, "role": role}
                for season, train, role in FOLDS
            ],
            "bootstrap_samples_per_fold_and_bucket": BOOTSTRAP_SAMPLES,
            "maturity_buckets": list(BUCKETS),
            "large_degradation_thresholds": list(LARGE_DEGRADATION_THRESHOLDS),
            "references_already_exposed": True,
            "same_season_pit_rule_inherited_from_b2_v1": True,
        },
        "input": {
            "historical_runtime_sha256": actual_hash,
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
            "joblib": joblib.__version__,
        },
        "horizons": horizons,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "promotion_allowed": False,
        "horizons": [
            {
                "horizon": row["horizon"],
                "fixed_variant": row["fixed_variant"]["id"],
                "summary": row["summary"],
            }
            for row in horizons
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
