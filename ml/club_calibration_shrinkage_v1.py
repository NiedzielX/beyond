#!/usr/bin/env python3
"""P8a club-specific residual calibration/shrinkage diagnostic.

Research question
-----------------
Can a small home-club-specific correction improve MAE over the unchanged
Structural Prior Runtime v1 without learning from the evaluation season?

The calibration residuals are themselves generated out of sample. For each
historical season S after the first season, the incumbent is fitted only on
seasons strictly before S and predicts S. When season T is evaluated, club
corrections may use only these already-out-of-sample residuals from seasons
strictly before T.

This avoids the optimistic shortcut of estimating club corrections from
in-sample residuals of the same model.

Evidence class: historical nested-forward research. All historical seasons are
already exposed research evidence. No frozen runtime or production forecast is
modified.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.demand_engine.structural_prior_runtime import fit_structural_prior_runtime
from ml.mae_delta_uncertainty_v1 import BootstrapConfig, bootstrap_delta_mae, paired_event_errors
from ml.mae_native_global_tournament_v1 import (
    EXPECTED_HISTORY_SHA256,
    EXPECTED_MATCHES,
    EXPECTED_STORE_ROWS,
    build_store,
    eligible_rows,
    load_canonical_history,
)
from ml.temporal_validation_v1 import forecast_metrics

VERSION = "club-calibration-shrinkage-v1"
EVIDENCE_CLASS = "historical_nested_forward_fold"
HORIZONS = ("T-30", "T-14", "T-7", "T-3", "T-1")
EVAL_SEASONS = ("2023/2024", "2024/2025", "2025/2026")
SHRINK_K = (8.0, 20.0)


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    target: str
    k: float | None = None


CANDIDATES = (
    CandidateSpec("incumbent-runtime", "none"),
    CandidateSpec("global-median-occ", "global"),
    CandidateSpec("club-zero-k8", "club_zero", 8.0),
    CandidateSpec("club-zero-k20", "club_zero", 20.0),
    CandidateSpec("club-global-k8", "club_global", 8.0),
    CandidateSpec("club-global-k20", "club_global", 20.0),
)


def ordered_seasons(store: pd.DataFrame) -> tuple[str, ...]:
    season_time = (
        store.groupby("season", sort=False)["kickoff_at"]
        .min()
        .sort_values()
    )
    seasons = tuple(season_time.index.astype(str))
    expected = (
        "2021/2022",
        "2022/2023",
        "2023/2024",
        "2024/2025",
        "2025/2026",
    )
    if seasons != expected:
        raise RuntimeError(f"unexpected canonical seasons: {seasons}")
    return seasons


def build_nested_oos_incumbent(store: pd.DataFrame, horizon: str) -> pd.DataFrame:
    """Generate one strictly-forward incumbent prediction for seasons 2..5."""
    seasons = ordered_seasons(store)
    parts: list[pd.DataFrame] = []
    for target_index in range(1, len(seasons)):
        target_season = seasons[target_index]
        training_seasons = seasons[:target_index]
        test = eligible_rows(store, horizon=horizon, seasons=(target_season,))
        runtime = fit_structural_prior_runtime(store, horizon, training_seasons)
        prediction = runtime.predict(test)
        part = test[
            [
                "match_key",
                "season",
                "horizon",
                "kickoff_at",
                "home_club_key",
                "away_club_key",
                "capacity",
                "target_attendance",
            ]
        ].copy()
        part["training_seasons"] = ",".join(training_seasons)
        part["incumbent_p50"] = prediction.astype(float)
        part["actual_attendance"] = part["target_attendance"].astype(float)
        part["incumbent_residual_seats"] = part["actual_attendance"] - part["incumbent_p50"]
        part["incumbent_residual_occ"] = (
            part["incumbent_residual_seats"] / part["capacity"].astype(float)
        )
        parts.append(part.drop(columns=["target_attendance"]))
    out = pd.concat(parts, ignore_index=True)
    if out["match_key"].duplicated().any():
        raise RuntimeError(f"nested OOS predictions duplicate match_key horizon={horizon}")
    return out.sort_values(["kickoff_at", "match_key"]).reset_index(drop=True)


def calibration_table(history: pd.DataFrame) -> tuple[float, pd.DataFrame]:
    if history.empty:
        raise RuntimeError("club calibration history is empty")
    global_median = float(history["incumbent_residual_occ"].median())
    club = (
        history.groupby("home_club_key", sort=True)["incumbent_residual_occ"]
        .agg([("club_median_occ", "median"), ("club_history_n", "size")])
        .reset_index()
    )
    return global_median, club


def correction_occupancy(
    test: pd.DataFrame,
    *,
    global_median_occ: float,
    club_table: pd.DataFrame,
    spec: CandidateSpec,
) -> np.ndarray:
    if spec.target == "none":
        return np.zeros(len(test), dtype=float)
    if spec.target == "global":
        return np.full(len(test), global_median_occ, dtype=float)

    joined = test[["home_club_key"]].merge(
        club_table,
        on="home_club_key",
        how="left",
        validate="many_to_one",
    )
    n = joined["club_history_n"].fillna(0.0).astype(float).to_numpy()
    club_median = joined["club_median_occ"].fillna(0.0).astype(float).to_numpy()
    k = float(spec.k)
    shrink = n / (n + k)

    if spec.target == "club_zero":
        return shrink * club_median
    if spec.target == "club_global":
        # Missing club history (n=0) falls back to the global median.
        return global_median_occ + shrink * (club_median - global_median_occ)
    raise KeyError(spec.target)


def apply_candidate(
    test: pd.DataFrame,
    *,
    global_median_occ: float,
    club_table: pd.DataFrame,
    spec: CandidateSpec,
) -> np.ndarray:
    correction_occ = correction_occupancy(
        test,
        global_median_occ=global_median_occ,
        club_table=club_table,
        spec=spec,
    )
    raw = test["incumbent_p50"].astype(float).to_numpy() + correction_occ * test["capacity"].astype(float).to_numpy()
    return np.clip(raw, 0.0, test["capacity"].astype(float).to_numpy())


def metric_row(frame: pd.DataFrame) -> dict[str, float | int]:
    metrics = forecast_metrics(frame["actual_attendance"], frame["forecast_p50"])
    return {
        "n": int(metrics["n"]),
        "mae": float(metrics["mae"]),
        "median_ae": float(metrics["median_ae"]),
        "p90_ae": float(metrics["p90_ae"]),
        "bias": float(metrics["bias"]),
        "rmse": float(metrics["rmse"]),
    }


def club_diagnostics(candidate: pd.DataFrame, incumbent: pd.DataFrame) -> dict[str, Any]:
    left = candidate[["match_key", "home_club_key", "absolute_error"]].rename(
        columns={"absolute_error": "candidate_ae"}
    )
    right = incumbent[["match_key", "absolute_error"]].rename(
        columns={"absolute_error": "incumbent_ae"}
    )
    paired = left.merge(right, on="match_key", how="inner", validate="one_to_one")
    club = paired.groupby("home_club_key", sort=True).agg(
        candidate_mae=("candidate_ae", "mean"),
        incumbent_mae=("incumbent_ae", "mean"),
        matches=("match_key", "count"),
    )
    club["delta_mae"] = club["candidate_mae"] - club["incumbent_mae"]
    return {
        "club_count": int(len(club)),
        "club_improvement_rate": float(np.mean(club["delta_mae"] < 0.0)),
        "club_non_degradation_rate": float(np.mean(club["delta_mae"] <= 0.0)),
        "worst_club_degradation": float(max(0.0, club["delta_mae"].max())),
        "best_club_improvement": float(max(0.0, -club["delta_mae"].min())),
        "per_club": [
            {
                "home_club_key": str(index),
                "matches": int(row["matches"]),
                "incumbent_mae": float(row["incumbent_mae"]),
                "candidate_mae": float(row["candidate_mae"]),
                "delta_mae": float(row["delta_mae"]),
            }
            for index, row in club.sort_index().iterrows()
        ],
    }


def run_horizon(store: pd.DataFrame, horizon: str) -> tuple[dict[str, Any], pd.DataFrame]:
    nested = build_nested_oos_incumbent(store, horizon)
    prediction_parts: list[pd.DataFrame] = []
    fold_meta: list[dict[str, Any]] = []

    for test_season in EVAL_SEASONS:
        test_start = nested.loc[nested["season"] == test_season, "kickoff_at"].min()
        calibration = nested[nested["kickoff_at"] < test_start].copy()
        test = nested[nested["season"] == test_season].copy()
        if test.empty or calibration.empty:
            raise RuntimeError(f"empty P8 fold horizon={horizon} season={test_season}")
        if calibration["kickoff_at"].max() >= test["kickoff_at"].min():
            raise RuntimeError("P8 calibration violates strict temporal ordering")

        global_median_occ, clubs = calibration_table(calibration)
        fold_id = f"{horizon}:{test_season}"
        fold_meta.append(
            {
                "fold_id": fold_id,
                "test_season": test_season,
                "test_matches": int(len(test)),
                "calibration_matches": int(len(calibration)),
                "calibration_seasons": sorted(calibration["season"].astype(str).unique().tolist()),
                "calibration_clubs": int(clubs["home_club_key"].nunique()),
                "global_median_residual_occ": global_median_occ,
                "calibration_end": calibration["kickoff_at"].max().isoformat(),
                "test_start": test["kickoff_at"].min().isoformat(),
            }
        )

        for spec in CANDIDATES:
            forecast = apply_candidate(
                test,
                global_median_occ=global_median_occ,
                club_table=clubs,
                spec=spec,
            )
            part = test[
                [
                    "match_key",
                    "season",
                    "horizon",
                    "kickoff_at",
                    "home_club_key",
                    "away_club_key",
                    "capacity",
                    "actual_attendance",
                    "incumbent_p50",
                ]
            ].copy()
            part["fold_id"] = fold_id
            part["candidate_id"] = spec.candidate_id
            part["forecast_p50"] = forecast
            part["signed_error"] = part["forecast_p50"] - part["actual_attendance"]
            part["absolute_error"] = part["signed_error"].abs()
            prediction_parts.append(part)

    predictions = pd.concat(prediction_parts, ignore_index=True)
    incumbent = predictions[predictions["candidate_id"] == "incumbent-runtime"].copy()
    incumbent_fold = (
        incumbent.groupby("fold_id", sort=True)
        .apply(lambda rows: float((rows["forecast_p50"] - rows["actual_attendance"]).abs().mean()), include_groups=False)
        .to_dict()
    )
    incumbent_mean_fold_mae = float(np.mean(list(incumbent_fold.values())))

    candidate_rows: list[dict[str, Any]] = []
    for spec in CANDIDATES:
        rows = predictions[predictions["candidate_id"] == spec.candidate_id].copy()
        per_fold: dict[str, dict[str, float | int]] = {}
        fold_deltas: list[float] = []
        for fold_id, fold_rows in rows.groupby("fold_id", sort=True):
            metrics = metric_row(fold_rows)
            per_fold[str(fold_id)] = metrics
            fold_deltas.append(float(metrics["mae"]) - incumbent_fold[str(fold_id)])

        mean_fold_mae = float(np.mean([float(v["mae"]) for v in per_fold.values()]))
        pooled = metric_row(rows)
        diag = (
            {
                "club_count": 0,
                "club_improvement_rate": 0.0,
                "club_non_degradation_rate": 0.0,
                "worst_club_degradation": 0.0,
                "best_club_improvement": 0.0,
                "per_club": [],
            }
            if spec.candidate_id == "incumbent-runtime"
            else club_diagnostics(rows, incumbent)
        )
        candidate_rows.append(
            {
                "candidate_id": spec.candidate_id,
                "target": spec.target,
                "k": spec.k,
                "mean_fold_mae": mean_fold_mae,
                "pooled_metrics": pooled,
                "mae_delta_vs_incumbent": mean_fold_mae - incumbent_mean_fold_mae,
                "relative_mae_delta_vs_incumbent": (
                    (mean_fold_mae - incumbent_mean_fold_mae) / incumbent_mean_fold_mae
                ),
                "fold_wins_vs_incumbent": int(np.sum(np.asarray(fold_deltas) < 0.0)),
                "worst_fold_degradation": float(max(0.0, max(fold_deltas))),
                "per_fold": per_fold,
                **diag,
            }
        )

    for row in candidate_rows:
        row["selector_eligible"] = bool(
            row["candidate_id"] != "incumbent-runtime"
            and row["mae_delta_vs_incumbent"] < 0.0
            and row["fold_wins_vs_incumbent"] >= 2
            and row["club_improvement_rate"] >= 0.50
        )

    eligible = [row for row in candidate_rows if row["selector_eligible"]]
    if eligible:
        lead = min(
            eligible,
            key=lambda row: (
                row["mean_fold_mae"],
                row["worst_fold_degradation"],
                row["candidate_id"],
            ),
        )
        lead_id = str(lead["candidate_id"])
        decision = "ADVANCE_CLUB_CALIBRATION_RESEARCH_CHALLENGER"
    else:
        lead_id = "incumbent-runtime"
        decision = "RETAIN_GLOBAL_INCUMBENT"

    uncertainty = None
    if lead_id != "incumbent-runtime":
        lead_rows = predictions[predictions["candidate_id"] == lead_id][
            ["match_key", "fold_id", "actual_attendance", "forecast_p50"]
        ].rename(columns={"forecast_p50": "challenger_p50"})
        inc_rows = incumbent[
            ["match_key", "fold_id", "actual_attendance", "forecast_p50"]
        ].rename(columns={"forecast_p50": "incumbent_p50", "actual_attendance": "inc_actual"})
        paired = inc_rows.merge(
            lead_rows,
            on=["match_key", "fold_id"],
            how="inner",
            validate="one_to_one",
        )
        if not np.allclose(paired["inc_actual"], paired["actual_attendance"], rtol=0.0, atol=0.0):
            raise RuntimeError("P8 paired actual attendance mismatch")
        canonical = paired.rename(columns={"inc_actual": "actual"})
        event_errors = paired_event_errors(
            canonical,
            event_col="match_key",
            actual_col="actual",
            incumbent_col="incumbent_p50",
            challenger_col="challenger_p50",
            strata_cols=("fold_id",),
        )
        uncertainty = bootstrap_delta_mae(
            event_errors,
            strata_cols=("fold_id",),
            config=BootstrapConfig(n_resamples=5000, seed=42),
        )

    return (
        {
            "horizon": horizon,
            "nested_oos_prediction_seasons": sorted(nested["season"].astype(str).unique().tolist()),
            "folds": fold_meta,
            "incumbent_mean_fold_mae": incumbent_mean_fold_mae,
            "candidates": candidate_rows,
            "research_lead_candidate_id": lead_id,
            "lead_uncertainty": uncertainty,
            "decision": decision,
        },
        predictions,
    )


def run(history_path: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    history = load_canonical_history(history_path)
    store = build_store(history)
    horizon_results: list[dict[str, Any]] = []
    prediction_parts: list[pd.DataFrame] = []

    for horizon in HORIZONS:
        result, predictions = run_horizon(store, horizon)
        horizon_results.append(result)
        prediction_parts.append(predictions)

    advanced = [
        result["horizon"]
        for result in horizon_results
        if result["decision"] == "ADVANCE_CLUB_CALIBRATION_RESEARCH_CHALLENGER"
    ]
    payload = {
        "version": VERSION,
        "status": "COMPLETED_HISTORICAL_NESTED_FORWARD_RESEARCH",
        "evidence_class": EVIDENCE_CLASS,
        "history_sha256": EXPECTED_HISTORY_SHA256,
        "match_count": EXPECTED_MATCHES,
        "feature_row_count": EXPECTED_STORE_ROWS,
        "calibration_target": "home_club residual occupancy",
        "calibration_source": "strictly out-of-sample prior-season incumbent residuals only",
        "candidate_family": [
            {"candidate_id": spec.candidate_id, "target": spec.target, "k": spec.k}
            for spec in CANDIDATES
        ],
        "selector": {
            "primary": "lower mean forward-fold MAE",
            "minimum_fold_wins": 2,
            "minimum_club_improvement_rate": 0.50,
        },
        "horizons": horizon_results,
        "advanced_horizons": advanced,
        "decision": "ADVANCE_SOME_CLUB_CALIBRATION" if advanced else "CLOSE_P8A_RETAIN_GLOBAL_INCUMBENT",
        "production_change": False,
        "promotion_allowed": False,
    }
    return payload, pd.concat(prediction_parts, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-predictions-csv", type=Path, required=True)
    args = parser.parse_args()

    payload, predictions = run(args.history)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    predictions.to_csv(args.output_predictions_csv, index=False)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
