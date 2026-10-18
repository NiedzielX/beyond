#!/usr/bin/env python3
"""Multi-fold a2 tournament for unresolved Pre-Live horizons.

This experiment revisits T-30/T-14/T-3/T-1 with the existing Stage-1
candidate contract but strengthens selection: a candidate must be identifiable
and improve the incumbent on both development-era rolling folds before it can
advance to the already-exposed 2024/25 and 2025/26 references.

T-7 is deliberately excluded because its historical candidate was frozen after
Stages 1-5. No production activation occurs here.
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

from ml.pre_live_baseline_optimization_v1 import (
    Candidate,
    candidate_set,
    load_feature_store,
    score_split,
    sha256_file,
)
from ml.features.structural_prior_feature_store_v1 import quality_report

EXPERIMENT = "pre-live-unresolved-multifold-v1"
WORKSTREAM = "a2 — Historical / Structural Prior optimization — unresolved-horizon multi-fold selection"
RANDOM_SEED = 42
HORIZONS = ("T-30", "T-14", "T-3", "T-1")

DEVELOPMENT_FOLDS = (
    ("2022/2023", ["2021/2022"], "additional_development_fold"),
    ("2023/2024", ["2021/2022", "2022/2023"], "canonical_stage1_development_fold"),
)
REFERENCE_HOLDOUTS = (
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
)

# Exact incumbent values from the canonical Stage-1 artifact run 39156711796.
EXPECTED_STAGE1_DEV_2023_MAE = {
    "T-30": 2559.7406941266854,
    "T-14": 2339.9504993283904,
    "T-3": 2311.6246893162593,
    "T-1": 2347.9931110468183,
}
EXPECTED_ATOL = 1e-9
MIN_IDENTIFIABLE_DEVELOPMENT_FOLDS = 2
IMPROVEMENT_ATOL = 1e-9


def is_identifiable(candidate: Candidate, training_seasons: list[str]) -> tuple[bool, str]:
    """Return whether the candidate's changed dimension exists in this fold.

    Recency weighting is not identifiable when only one season is available:
    all valid season-weight functions collapse to one effective season and any
    numerical difference from explicit sample_weight plumbing is not evidence
    for a recency hypothesis.
    """
    if candidate.family == "recency" and len(training_seasons) < 2:
        return False, "RECENCY_NOT_IDENTIFIABLE_WITH_ONE_TRAINING_SEASON"
    return True, "IDENTIFIABLE"


def verify_stage1_development_incumbent(horizon: str, split: dict[str, Any]) -> None:
    expected = EXPECTED_STAGE1_DEV_2023_MAE[horizon]
    actual = float(split["incumbent_mae"])
    if not np.isclose(actual, expected, rtol=0.0, atol=EXPECTED_ATOL):
        raise RuntimeError(
            f"Stage-1 2023/24 incumbent mismatch {horizon}: actual={actual} expected={expected}"
        )


def candidate_development_summary(
    candidate: Candidate,
    folds: list[dict[str, Any]],
    candidate_order: int,
) -> dict[str, Any]:
    identifiable_scores: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []

    for fold in folds:
        identifiable, reason = is_identifiable(candidate, list(fold["training_seasons"]))
        score = fold["candidates"][candidate.id]["scorecard"]
        row = {
            "season": fold["test_season"],
            "training_seasons": list(fold["training_seasons"]),
            "identifiable": identifiable,
            "identifiability_reason": reason,
            "candidate_mae": float(score["candidate"]["mae"]),
            "incumbent_mae": float(score["incumbent"]["mae"]),
            "mae_improvement": float(score["mae_improvement"]),
            "candidate_median_ae": float(score["candidate"]["median_ae"]),
            "incumbent_median_ae": float(score["incumbent"]["median_ae"]),
            "candidate_p90_ae": float(score["candidate"]["p90_ae"]),
            "incumbent_p90_ae": float(score["incumbent"]["p90_ae"]),
            "candidate_bias": float(score["candidate"]["bias"]),
            "incumbent_bias": float(score["incumbent"]["bias"]),
            "worst_event_degradation": float(score["worst_event_degradation"]),
            "worst_event": score["worst_event"],
            "event_improvement_rate": float(score["event_improvement_rate"]),
        }
        fold_rows.append(row)
        if identifiable:
            identifiable_scores.append(row)

    identifiable_count = len(identifiable_scores)
    improvements = [row["mae_improvement"] for row in identifiable_scores]
    enough_folds = identifiable_count >= MIN_IDENTIFIABLE_DEVELOPMENT_FOLDS
    all_identifiable_folds_improve = bool(
        enough_folds and all(value > IMPROVEMENT_ATOL for value in improvements)
    )

    if identifiable_scores:
        mean_improvement = float(np.mean(improvements))
        mean_candidate_mae = float(np.mean([row["candidate_mae"] for row in identifiable_scores]))
        mean_incumbent_mae = float(np.mean([row["incumbent_mae"] for row in identifiable_scores]))
        max_worst_degradation = float(
            np.max([row["worst_event_degradation"] for row in identifiable_scores])
        )
        mean_p90_delta = float(
            np.mean([
                row["candidate_p90_ae"] - row["incumbent_p90_ae"]
                for row in identifiable_scores
            ])
        )
        mean_median_delta = float(
            np.mean([
                row["candidate_median_ae"] - row["incumbent_median_ae"]
                for row in identifiable_scores
            ])
        )
    else:
        mean_improvement = float("nan")
        mean_candidate_mae = float("nan")
        mean_incumbent_mae = float("nan")
        max_worst_degradation = float("nan")
        mean_p90_delta = float("nan")
        mean_median_delta = float("nan")

    if candidate.id == "incumbent":
        eligibility = "INCUMBENT_FALLBACK"
    elif not enough_folds:
        eligibility = "INSUFFICIENT_IDENTIFIABLE_DEVELOPMENT_FOLDS"
    elif not all_identifiable_folds_improve:
        eligibility = "FAILS_ALL_FOLDS_MAE_IMPROVEMENT_REQUIREMENT"
    else:
        eligibility = "ELIGIBLE"

    return {
        "candidate": asdict(candidate),
        "declared_order": candidate_order,
        "development_folds": fold_rows,
        "identifiable_fold_count": identifiable_count,
        "required_identifiable_fold_count": MIN_IDENTIFIABLE_DEVELOPMENT_FOLDS,
        "all_identifiable_folds_improve_mae": all_identifiable_folds_improve,
        "mean_candidate_mae_identifiable_folds": mean_candidate_mae,
        "mean_incumbent_mae_identifiable_folds": mean_incumbent_mae,
        "mean_mae_improvement_identifiable_folds": mean_improvement,
        "mean_median_ae_delta_identifiable_folds": mean_median_delta,
        "mean_p90_ae_delta_identifiable_folds": mean_p90_delta,
        "max_worst_event_degradation_identifiable_folds": max_worst_degradation,
        "eligibility": eligibility,
    }


def select_candidate(summaries: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    eligible = [row for row in summaries if row["eligibility"] == "ELIGIBLE"]
    if not eligible:
        incumbent = next(row for row in summaries if row["candidate"]["id"] == "incumbent")
        return "incumbent", {
            "reason": "NO_NON_INCUMBENT_IMPROVES_ALL_IDENTIFIABLE_DEVELOPMENT_FOLDS",
            "eligible_candidate_ids": [],
            "selected_summary": incumbent,
        }

    # MAE-first. Tail is a deterministic tie-break/sanity dimension, not an
    # arbitrary post-hoc trade-off against MAE.
    ranked = sorted(
        eligible,
        key=lambda row: (
            -float(row["mean_mae_improvement_identifiable_folds"]),
            float(row["max_worst_event_degradation_identifiable_folds"]),
            int(row["declared_order"]),
        ),
    )
    selected = ranked[0]
    return str(selected["candidate"]["id"]), {
        "reason": "MAX_MEAN_MAE_IMPROVEMENT_AMONG_CANDIDATES_IMPROVING_BOTH_DEVELOPMENT_FOLDS",
        "eligible_candidate_ids": [str(row["candidate"]["id"]) for row in ranked],
        "selected_summary": selected,
    }


def score_reference_holdouts(
    store: pd.DataFrame,
    horizon: str,
    candidates: list[Candidate],
    groups: dict[str, list[str]],
    selected_id: str,
) -> dict[str, Any]:
    incumbent = next(candidate for candidate in candidates if candidate.id == "incumbent")
    selected = next(candidate for candidate in candidates if candidate.id == selected_id)
    reference_candidates = [incumbent] if selected_id == "incumbent" else [incumbent, selected]

    folds: dict[str, Any] = {}
    summary: list[dict[str, Any]] = []
    for season, training_seasons in REFERENCE_HOLDOUTS:
        split = score_split(
            store,
            horizon,
            training_seasons,
            season,
            "holdout",
            reference_candidates,
            groups,
        )
        folds[season] = split
        score = split["candidates"][selected_id]["scorecard"]
        summary.append({
            "season": season,
            "training_seasons": list(training_seasons),
            "incumbent_mae": float(score["incumbent"]["mae"]),
            "selected_mae": float(score["candidate"]["mae"]),
            "mae_improvement": float(score["mae_improvement"]),
            "candidate_median_ae": float(score["candidate"]["median_ae"]),
            "incumbent_median_ae": float(score["incumbent"]["median_ae"]),
            "candidate_p90_ae": float(score["candidate"]["p90_ae"]),
            "incumbent_p90_ae": float(score["incumbent"]["p90_ae"]),
            "candidate_bias": float(score["candidate"]["bias"]),
            "incumbent_bias": float(score["incumbent"]["bias"]),
            "event_improvement_rate": float(score["event_improvement_rate"]),
            "worst_event_degradation": float(score["worst_event_degradation"]),
            "worst_event": score["worst_event"],
        })

    mean_incumbent = float(np.mean([row["incumbent_mae"] for row in summary]))
    mean_selected = float(np.mean([row["selected_mae"] for row in summary]))
    mean_improvement = mean_incumbent - mean_selected
    both_improve = bool(all(row["mae_improvement"] > 0.0 for row in summary))

    if selected_id == "incumbent":
        signal = "INCUMBENT_RETAINED_AFTER_MULTIFOLD_DEVELOPMENT"
    elif both_improve and mean_improvement > 0.0:
        signal = "MULTIFOLD_SELECTED_CANDIDATE_IMPROVES_BOTH_REFERENCES"
    elif mean_improvement > 0.0:
        signal = "MULTIFOLD_SELECTED_CANDIDATE_POSITIVE_MEAN_MIXED_REFERENCES"
    else:
        signal = "MULTIFOLD_SELECTED_CANDIDATE_NOT_PROVEN_ON_REFERENCES"

    return {
        "folds": folds,
        "summary": summary,
        "mean_incumbent_mae": mean_incumbent,
        "mean_selected_mae": mean_selected,
        "mean_mae_improvement": mean_improvement,
        "both_reference_seasons_improve": both_improve,
        "signal": signal,
    }


def horizon_experiment(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    candidates, groups, protected = candidate_set(store, horizon)
    candidate_order = {candidate.id: index for index, candidate in enumerate(candidates)}

    development_folds: list[dict[str, Any]] = []
    for season, training_seasons, role in DEVELOPMENT_FOLDS:
        # 2022/23 has no prior canonical benchmark assertion and is labelled
        # audit/development. 2023/24 is verified manually below against the
        # exact Stage-1 artifact for all unresolved horizons.
        split_kind = "audit" if season == "2022/2023" else "development"
        split = score_split(
            store,
            horizon,
            training_seasons,
            season,
            split_kind,
            candidates,
            groups,
        )
        split["development_role"] = role
        development_folds.append(split)
        if season == "2023/2024":
            verify_stage1_development_incumbent(horizon, split)

    summaries = [
        candidate_development_summary(candidate, development_folds, candidate_order[candidate.id])
        for candidate in candidates
    ]
    selected_id, selection = select_candidate(summaries)
    references = score_reference_holdouts(
        store,
        horizon,
        candidates,
        groups,
        selected_id,
    )

    return {
        "horizon": horizon,
        "candidate_count": len(candidates),
        "candidates": [asdict(candidate) for candidate in candidates],
        "feature_groups_resolved": groups,
        "protected_direct_baseline_feature": protected,
        "development_folds": development_folds,
        "development_candidate_summaries": summaries,
        "selection": selection,
        "selected_candidate_id": selected_id,
        "reference_policy": "score only incumbent plus the multi-fold development-selected candidate",
        "references": references,
        "promotion_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    expected_hash = manifest["historical_runtime"]["sha256"]
    actual_hash = sha256_file(args.historical_runtime)
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    quality = quality_report(store)
    if quality["status"] != "PASS":
        raise RuntimeError(f"feature-store quality failed: {quality}")

    horizons = [horizon_experiment(store, horizon) for horizon in HORIZONS]

    result = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_MULTIFOLD_HISTORICAL_CHALLENGER_EVIDENCE",
        "evidence_class": "DEVELOPMENT_MULTIFOLD_PLUS_EXPOSED_REFERENCE_SEASONS",
        "promotion_allowed": False,
        "production_change": False,
        "excluded_horizon": {
            "horizon": "T-7",
            "reason": "historical candidate hist31-leaf20-l2-1 frozen after Stages 1-5",
        },
        "protocol": {
            "development_folds": [
                {"season": season, "training_seasons": train, "role": role}
                for season, train, role in DEVELOPMENT_FOLDS
            ],
            "reference_holdouts": [
                {"season": season, "training_seasons": train}
                for season, train in REFERENCE_HOLDOUTS
            ],
            "minimum_identifiable_development_folds": MIN_IDENTIFIABLE_DEVELOPMENT_FOLDS,
            "advancement_rule": (
                "candidate must be identifiable and improve incumbent MAE by >1e-9 in both "
                "development folds; among eligible candidates select maximum mean MAE improvement, "
                "then smaller max worst-event degradation, then predeclared order"
            ),
            "recency_one_season_rule": (
                "recency candidates are explicitly non-identifiable when only one training season exists; "
                "numerical differences caused only by fit/sample-weight plumbing are not recency evidence"
            ),
            "reference_holdouts_used_for_selection": False,
            "references_already_exposed": True,
            "event_is_independent_unit": True,
            "random_snapshot_split": False,
            "future_leakage_allowed": False,
        },
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_hash,
            "manifest_path": str(args.manifest),
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
        "quality": quality,
        "exact_stage1_2023_incumbent_assertions": EXPECTED_STAGE1_DEV_2023_MAE,
        "horizons": horizons,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "promotion_allowed": False,
        "horizons": [
            {
                "horizon": item["horizon"],
                "selected_candidate_id": item["selected_candidate_id"],
                "selection_reason": item["selection"]["reason"],
                "reference_signal": item["references"]["signal"],
                "mean_reference_incumbent_mae": item["references"]["mean_incumbent_mae"],
                "mean_reference_selected_mae": item["references"]["mean_selected_mae"],
                "mean_reference_mae_improvement": item["references"]["mean_mae_improvement"],
            }
            for item in horizons
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
