#!/usr/bin/env python3
"""Fixed historical regression validation for frozen T-30 Occupancy Anchor v4.

Candidate frozen first in commit:
b25d5d11212f25438358c66ff118bf3256e03c80

2024/25 and 2025/26 are exposed fixed historical regression sets. This script
performs no parameter search and cannot change k/estimator/fallback semantics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from ml.demand_engine.structural_prior_runtime import fit_structural_prior_runtime
from ml.features.structural_prior_feature_store_v1 import build_feature_store
from ml.t30_occupancy_anchor_v4 import (
    HORIZON,
    add_anchor,
    canonical_matches,
    fit_candidate,
    metrics,
    predict_candidate,
    previous_season_occupancy_map,
)

FROZEN_SPEC_COMMIT = "b25d5d11212f25438358c66ff118bf3256e03c80"
MODEL_ID = "structural-prior-t30-v4-occupancy-anchor-k3"
K = 3.0
REGRESSION_SETS = (
    ("2024/2025", ("2021/2022", "2022/2023", "2023/2024")),
    ("2025/2026", ("2021/2022", "2022/2023", "2023/2024", "2024/2025")),
)


def club_metrics(frame, current_pred: np.ndarray, candidate_pred: np.ndarray) -> dict:
    work = frame[["home_club_key", "target_attendance"]].copy().reset_index(drop=True)
    work["current"] = np.asarray(current_pred)
    work["candidate"] = np.asarray(candidate_pred)
    result = {}
    for club, group in work.groupby("home_club_key"):
        actual = group["target_attendance"].astype(float).to_numpy()
        current = metrics(actual, group["current"].to_numpy())
        candidate = metrics(actual, group["candidate"].to_numpy())
        result[str(club)] = {
            "n": int(len(group)),
            "current_mae": current["mae"],
            "candidate_mae": candidate["mae"],
            "delta_mae": candidate["mae"] - current["mae"],
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-runtime",
        type=Path,
        default=Path("ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz"),
    )
    parser.add_argument("--output", type=Path, default=Path("/tmp/t30-occupancy-anchor-v4-validation.json"))
    args = parser.parse_args()

    matches = canonical_matches(args.historical_runtime)
    base_store = build_feature_store(matches)
    store = add_anchor(base_store, previous_season_occupancy_map(matches))

    report = {
        "experiment": "t30-occupancy-anchor-v4-fixed-regression-validation",
        "model_id": MODEL_ID,
        "frozen_spec_commit": FROZEN_SPEC_COMMIT,
        "k": K,
        "search_performed": False,
        "validation_status": "EXPOSED_FIXED_HISTORICAL_REGRESSION_SET",
        "automatic_promotion": False,
        "seasons": {},
    }

    all_actual = []
    all_current = []
    all_candidate = []

    for season, train_seasons in REGRESSION_SETS:
        test = store[
            (store["horizon"].astype(str) == HORIZON)
            & store["training_eligible"].astype(bool)
            & (store["season"] == season)
            & store["baseline_season"].notna()
        ].copy()
        actual = test["target_attendance"].astype(float).to_numpy()

        current_runtime = fit_structural_prior_runtime(base_store, HORIZON, list(train_seasons))
        current_prediction = current_runtime.predict(test)

        prep, model, numeric, train_rows = fit_candidate(store, train_seasons, K)
        candidate_prediction = predict_candidate(test, prep, model, numeric, K)

        current = metrics(actual, current_prediction)
        candidate = metrics(actual, candidate_prediction)
        report["seasons"][season] = {
            "train_seasons": list(train_seasons),
            "training_rows": train_rows,
            "current": current,
            "candidate": candidate,
            "delta_mae": candidate["mae"] - current["mae"],
            "relative_improvement": (current["mae"] - candidate["mae"]) / current["mae"],
            "clubs": club_metrics(test, current_prediction, candidate_prediction),
        }
        all_actual.extend(actual.tolist())
        all_current.extend(np.asarray(current_prediction).tolist())
        all_candidate.extend(np.asarray(candidate_prediction).tolist())

    current_combined = metrics(all_actual, all_current)
    candidate_combined = metrics(all_actual, all_candidate)
    report["combined"] = {
        "current": current_combined,
        "candidate": candidate_combined,
        "delta_mae": candidate_combined["mae"] - current_combined["mae"],
        "relative_improvement": (
            current_combined["mae"] - candidate_combined["mae"]
        ) / current_combined["mae"],
    }
    improves_each = all(
        row["candidate"]["mae"] < row["current"]["mae"]
        for row in report["seasons"].values()
    )
    report["decision"] = {
        "improves_each_historical_regression_season": improves_each,
        "improves_combined": candidate_combined["mae"] < current_combined["mae"],
        "under_1700_combined": candidate_combined["mae"] < 1700.0,
        "production_promotion": "NO_AUTO_PROMOTION_PROSPECTIVE_EVIDENCE_REQUIRED",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
