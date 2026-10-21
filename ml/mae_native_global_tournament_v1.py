#!/usr/bin/env python3
"""MAE-native challenger tournament on the canonical five-season Structural Prior store.

Research question
-----------------
Can a genuinely different median/L1 residual estimator reduce time-respecting
MAE versus the currently frozen Structural Prior Runtime v1 estimator, while
holding each horizon's baseline and feature mode fixed?

Evidence class: historical forward-fold research. All five historical seasons
are already exposed to research; this script makes no unseen/prospective claim.
No production model or frozen artifact is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.demand_engine.structural_prior_runtime import (
    CAT,
    CURRENT_EARLY_RUNTIME_SPECS,
    feature_columns,
    fit_structural_prior_runtime,
)
from ml.features.structural_prior_feature_store_v1 import (
    WARSAW_TZ,
    build_feature_store,
    quality_report,
)
from ml.temporal_validation_v1 import (
    build_expanding_group_folds,
    fold_manifest,
    forecast_metrics,
)

EXPERIMENT = "mae-native-global-tournament-v1"
EVIDENCE_CLASS = "historical_forward_fold"
EXPECTED_HISTORY_SHA256 = "3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569"
EXPECTED_MATCHES = 1530
EXPECTED_STORE_ROWS = 7650
HORIZONS = ("T-30", "T-14", "T-7", "T-3", "T-1")
RANDOM_SEED = 42


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    family: str
    alpha: float | None = None


# Compact, predeclared candidate set. The two alpha values are deliberately
# sparse rather than a broad hyperparameter sweep.
CANDIDATES = (
    CandidateSpec("incumbent-runtime", "incumbent"),
    CandidateSpec("quantile-linear-a0005", "quantile_linear", 0.0005),
    CandidateSpec("quantile-linear-a002", "quantile_linear", 0.002),
    CandidateSpec("gbr-l1-depth2", "gbr_l1"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_canonical_history(path: Path) -> pd.DataFrame:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_HISTORY_SHA256:
        raise RuntimeError(
            f"canonical historical runtime drift actual={actual_sha} expected={EXPECTED_HISTORY_SHA256}"
        )
    frame = pd.read_csv(path, compression="gzip")
    if len(frame) != EXPECTED_MATCHES or frame["match_key"].nunique() != EXPECTED_MATCHES:
        raise RuntimeError(
            f"expected {EXPECTED_MATCHES} canonical matches, rows={len(frame)} "
            f"unique={frame['match_key'].nunique()}"
        )
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
    frame["training_eligible"] = ~frame["attendance"].eq(0)
    return frame.sort_values(["kickoff_at", "home_club_key"]).reset_index(drop=True)


def build_store(history: pd.DataFrame) -> pd.DataFrame:
    store = build_feature_store(history)
    report = quality_report(store)
    if report["status"] != "PASS":
        raise RuntimeError(f"canonical feature-store quality failed: {report}")
    if len(store) != EXPECTED_STORE_ROWS:
        raise RuntimeError(f"expected {EXPECTED_STORE_ROWS} feature rows, got {len(store)}")
    return store


def _linear_preprocessor(numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
            (
                "num",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric,
            ),
        ],
        remainder="drop",
    )


def _tree_preprocessor(numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
            ("num", SimpleImputer(strategy="median", add_indicator=True), numeric),
        ],
        remainder="drop",
    )


def _residual_occupancy(rows: pd.DataFrame, baseline_column: str) -> np.ndarray:
    return (
        rows["target_attendance"].astype(float).to_numpy()
        - rows[baseline_column].astype(float).to_numpy()
    ) / rows["capacity"].astype(float).to_numpy()


def _final_forecast(
    rows: pd.DataFrame,
    baseline_column: str,
    residual_occupancy: np.ndarray,
) -> np.ndarray:
    capacity = rows["capacity"].astype(float).to_numpy()
    baseline = rows[baseline_column].astype(float).to_numpy()
    return np.clip(baseline + np.asarray(residual_occupancy, dtype=float) * capacity, 0.0, capacity)


def fit_predict_challenger(
    spec: CandidateSpec,
    *,
    store: pd.DataFrame,
    horizon: str,
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> np.ndarray:
    runtime_spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    numeric = feature_columns(store, runtime_spec.feature_mode)
    feature_names = CAT + numeric
    y = _residual_occupancy(train, runtime_spec.baseline_column)

    if spec.family == "quantile_linear":
        model = Pipeline(
            [
                ("prep", _linear_preprocessor(numeric)),
                (
                    "model",
                    QuantileRegressor(
                        quantile=0.50,
                        alpha=float(spec.alpha),
                        solver="highs",
                        fit_intercept=True,
                    ),
                ),
            ]
        )
    elif spec.family == "gbr_l1":
        model = Pipeline(
            [
                ("prep", _tree_preprocessor(numeric)),
                (
                    "model",
                    GradientBoostingRegressor(
                        loss="absolute_error",
                        n_estimators=180,
                        learning_rate=0.03,
                        max_depth=2,
                        min_samples_leaf=8,
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        )
    else:
        raise KeyError(spec.family)

    model.fit(train[feature_names], y)
    residual = np.asarray(model.predict(test[feature_names]), dtype=float)
    return _final_forecast(test, runtime_spec.baseline_column, residual)


def eligible_rows(
    store: pd.DataFrame,
    *,
    horizon: str,
    seasons: tuple[str, ...],
) -> pd.DataFrame:
    runtime_spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = store[
        (store["horizon"].astype(str) == horizon)
        & store["training_eligible"].astype(bool)
        & store["season"].astype(str).isin(seasons)
        & store[runtime_spec.baseline_column].notna()
    ].copy()
    if rows.empty:
        raise RuntimeError(f"no eligible rows horizon={horizon} seasons={seasons}")
    return rows.sort_values(["kickoff_at", "match_key"]).reset_index(drop=True)


def incumbent_predictions(
    store: pd.DataFrame,
    *,
    horizon: str,
    train_groups: tuple[str, ...],
    test: pd.DataFrame,
) -> np.ndarray:
    runtime = fit_structural_prior_runtime(store, horizon, list(train_groups))
    return runtime.predict(test)


def paired_club_diagnostics(
    candidate: pd.DataFrame,
    incumbent: pd.DataFrame,
) -> dict[str, Any]:
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
    delta = club["candidate_mae"] - club["incumbent_mae"]
    return {
        "club_count": int(len(club)),
        "club_improvement_rate": float(np.mean(delta < 0.0)),
        "worst_club_degradation": float(max(0.0, delta.max())),
        "best_club_improvement": float(max(0.0, (-delta).max())),
    }


def score_predictions(rows: pd.DataFrame) -> dict[str, Any]:
    scored = forecast_metrics(rows["actual_attendance"], rows["forecast_p50"])
    return {
        "row_count": int(scored["n"]),
        "mae": float(scored["mae"]),
        "median_ae": float(scored["median_ae"]),
        "p90_ae": float(scored["p90_ae"]),
        "bias": float(scored["bias"]),
        "rmse": float(scored["rmse"]),
    }


def run_horizon(store: pd.DataFrame, horizon: str) -> tuple[dict[str, Any], pd.DataFrame]:
    horizon_all = store[store["horizon"].astype(str) == horizon].copy()
    folds = build_expanding_group_folds(
        horizon_all,
        entity_col="match_key",
        time_col="kickoff_at",
        group_col="season",
        min_train_groups=2,
    )
    if [fold.test_groups for fold in folds] != [
        ("2023/2024",),
        ("2024/2025",),
        ("2025/2026",),
    ]:
        raise RuntimeError(f"unexpected temporal fold structure horizon={horizon}")

    prediction_parts: list[pd.DataFrame] = []
    fold_scores: dict[str, dict[str, dict[str, Any]]] = {}

    for fold in folds:
        train = eligible_rows(store, horizon=horizon, seasons=fold.train_groups)
        test = eligible_rows(store, horizon=horizon, seasons=fold.test_groups)
        fold_scores[fold.fold_id] = {}

        incumbent_forecast = incumbent_predictions(
            store,
            horizon=horizon,
            train_groups=fold.train_groups,
            test=test,
        )

        for spec in CANDIDATES:
            if spec.family == "incumbent":
                forecast = incumbent_forecast
            else:
                forecast = fit_predict_challenger(
                    spec,
                    store=store,
                    horizon=horizon,
                    train=train,
                    test=test,
                )
            part = test[
                ["match_key", "season", "horizon", "kickoff_at", "home_club_key", "away_club_key", "target_attendance"]
            ].copy()
            part["fold_id"] = fold.fold_id
            part["candidate_id"] = spec.candidate_id
            part["forecast_p50"] = forecast
            part["actual_attendance"] = part["target_attendance"].astype(float)
            part["signed_error"] = part["forecast_p50"] - part["actual_attendance"]
            part["absolute_error"] = part["signed_error"].abs()
            prediction_parts.append(part.drop(columns=["target_attendance"]))
            fold_scores[fold.fold_id][spec.candidate_id] = score_predictions(part)

    predictions = pd.concat(prediction_parts, ignore_index=True)
    scorecards: list[dict[str, Any]] = []
    incumbent_rows = predictions[predictions["candidate_id"] == "incumbent-runtime"].copy()
    incumbent_fold_maes = {
        fold_id: scores["incumbent-runtime"]["mae"] for fold_id, scores in fold_scores.items()
    }
    incumbent_mean_fold_mae = float(np.mean(list(incumbent_fold_maes.values())))

    for spec in CANDIDATES:
        rows = predictions[predictions["candidate_id"] == spec.candidate_id].copy()
        per_fold = {
            fold_id: scores[spec.candidate_id] for fold_id, scores in fold_scores.items()
        }
        fold_maes = [score["mae"] for score in per_fold.values()]
        fold_deltas = [
            per_fold[fold_id]["mae"] - incumbent_fold_maes[fold_id]
            for fold_id in per_fold
        ]
        club_diag = (
            {
                "club_count": 0,
                "club_improvement_rate": 0.0,
                "worst_club_degradation": 0.0,
                "best_club_improvement": 0.0,
            }
            if spec.family == "incumbent"
            else paired_club_diagnostics(rows, incumbent_rows)
        )
        aggregate = score_predictions(rows)
        row = {
            "candidate_id": spec.candidate_id,
            "spec": asdict(spec),
            "mean_fold_mae": float(np.mean(fold_maes)),
            "pooled_metrics": aggregate,
            "mae_delta_vs_incumbent": float(np.mean(fold_maes) - incumbent_mean_fold_mae),
            "relative_mae_delta_vs_incumbent": float(
                (np.mean(fold_maes) - incumbent_mean_fold_mae) / incumbent_mean_fold_mae
            ),
            "fold_wins_vs_incumbent": int(np.sum(np.asarray(fold_deltas) < 0.0)),
            "worst_fold_degradation": float(max(0.0, max(fold_deltas))),
            "per_fold": per_fold,
            **club_diag,
        }
        row["selector_eligible"] = bool(
            spec.family != "incumbent"
            and row["mae_delta_vs_incumbent"] < 0.0
            and row["fold_wins_vs_incumbent"] >= 2
        )
        scorecards.append(row)

    eligible = [row for row in scorecards if row["selector_eligible"]]
    if eligible:
        lead = min(
            eligible,
            key=lambda row: (
                row["mean_fold_mae"],
                row["worst_fold_degradation"],
                row["candidate_id"],
            ),
        )["candidate_id"]
        decision = "NEW_HISTORICAL_RESEARCH_CHALLENGER_LEAD"
    else:
        lead = "incumbent-runtime"
        decision = "RETAIN_INCUMBENT"

    manifest = fold_manifest(
        folds,
        protocol_id=f"{EXPERIMENT}-{horizon}",
        source_id=EXPECTED_HISTORY_SHA256,
    )
    return {
        "horizon": horizon,
        "runtime_spec": asdict(CURRENT_EARLY_RUNTIME_SPECS[horizon]),
        "fold_manifest": manifest,
        "incumbent_mean_fold_mae": incumbent_mean_fold_mae,
        "candidates": scorecards,
        "research_lead_candidate_id": lead,
        "decision": decision,
    }, predictions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-predictions-csv", type=Path, required=True)
    args = parser.parse_args()

    history = load_canonical_history(args.history)
    store = build_store(history)
    horizon_results: list[dict[str, Any]] = []
    predictions: list[pd.DataFrame] = []
    for horizon in HORIZONS:
        result, pred = run_horizon(store, horizon)
        horizon_results.append(result)
        predictions.append(pred)

    output = {
        "experiment": EXPERIMENT,
        "status": "COMPLETED_HISTORICAL_FORWARD_RESEARCH",
        "evidence_class": EVIDENCE_CLASS,
        "production_change": False,
        "promotion_allowed": False,
        "historical_runtime_sha256": EXPECTED_HISTORY_SHA256,
        "match_count": int(history["match_key"].nunique()),
        "feature_row_count": int(len(store)),
        "training_loss_note": (
            "Current incumbents are not uniformly squared-error: T-14/T-3/T-1 use HistGBR absolute_error, "
            "T-7 uses Huber, T-30 uses ExtraTrees. Challengers test genuinely different L1/median estimators."
        ),
        "selector": {
            "primary": "lowest mean fold MAE across strict expanding-season folds",
            "eligibility": [
                "positive MAE improvement versus incumbent mean-fold MAE",
                "wins at least 2 of 3 forward folds",
            ],
            "tie_break": ["lowest mean fold MAE", "lowest worst fold degradation", "candidate id"],
            "unseen_claim": False,
        },
        "horizons": horizon_results,
        "libraries": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    pd.concat(predictions, ignore_index=True).to_csv(args.output_predictions_csv, index=False)

    print(json.dumps({
        "experiment": EXPERIMENT,
        "status": output["status"],
        "horizons": [
            {
                "horizon": row["horizon"],
                "incumbent_mean_fold_mae": row["incumbent_mean_fold_mae"],
                "research_lead_candidate_id": row["research_lead_candidate_id"],
                "decision": row["decision"],
                "candidates": [
                    {
                        "candidate_id": c["candidate_id"],
                        "mean_fold_mae": c["mean_fold_mae"],
                        "mae_delta_vs_incumbent": c["mae_delta_vs_incumbent"],
                        "fold_wins_vs_incumbent": c["fold_wins_vs_incumbent"],
                        "selector_eligible": c["selector_eligible"],
                    }
                    for c in row["candidates"]
                ],
            }
            for row in horizon_results
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
