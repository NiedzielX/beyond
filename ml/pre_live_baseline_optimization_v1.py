#!/usr/bin/env python3
"""Pre-Live v2 stage-1 baseline optimization harness.

Purpose:
- reproduce the frozen Structural Prior incumbent exactly;
- evaluate one-change-at-a-time feature-group ablations;
- evaluate explicit recency-weight policies;
- evaluate selected model-family challengers;
- select on 2023/24 development only;
- score unchanged on exposed 2024/25 and 2025/26 rolling holdouts;
- emit a complete machine-readable scorecard.

This experiment is historical challenger evidence only. It never promotes or
changes production artifacts automatically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import (
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)

from ml.demand_engine.freeze_structural_prior_artifacts import (
    EXPECTED_DEVELOPMENT_MAE,
    EXPECTED_HOLDOUT_ATOL,
    EXPECTED_HOLDOUT_MAE,
    _canonical_matches,
)
from ml.demand_engine.structural_prior_runtime import (
    CAT,
    CURRENT_EARLY_RUNTIME_SPECS,
    _estimator,
    _preprocessor,
    feature_columns,
    fit_structural_prior_runtime,
)
from ml.features.structural_prior_feature_store_v1 import build_feature_store, quality_report

EXPERIMENT = "pre-live-baseline-optimization-v1"
WORKSTREAM = "a2 — Historical / Structural Prior optimization"
RANDOM_SEED = 42

DEV_TRAIN = ["2021/2022", "2022/2023"]
DEV_SEASON = "2023/2024"
HOLDOUTS = [
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]
HORIZONS = ["T-30", "T-14", "T-7", "T-3", "T-1"]
MIN_CLUB_BREAKDOWN_N = 5

FeatureFamily = Literal["incumbent", "ablation", "recency", "model_family"]

FEATURE_GROUPS: dict[str, tuple[str, ...]] = {
    "calendar_timing": (
        "round_no", "season_progress", "month", "weekday", "kickoff_minutes", "is_weekend",
        "month_sin", "month_cos", "doy_sin", "doy_cos", "kickoff_sin", "kickoff_cos",
    ),
    "home_history": (
        "home_history_n", "home_attendance_mean", "home_attendance_median",
        "home_attendance_last", "home_attendance_rolling3", "home_attendance_rolling5",
        "home_attendance_rolling10", "home_attendance_std", "home_attendance_p90",
        "home_attendance_trend3_vs_mean", "days_since_last_home",
        "prev_season_home_mean", "home_demand_vs_league_median",
        "baseline_r3", "baseline_r5", "baseline_mean",
    ),
    "current_season": (
        "season_home_n", "season_home_mean", "season_home_last", "season_home_r3",
        "season_vs_long_ratio", "baseline_season",
    ),
    "opponent_demand": (
        "opponent_draw_n", "opponent_draw_ratio_mean", "opponent_draw_ratio_recent3",
        "opponent_raw_attendance_mean", "opponent_demand_x_progress",
        "opponent_demand_x_weekend",
    ),
    "pair_history": (
        "pair_n", "pair_ratio_mean", "pair_ratio_recent2", "pair_attendance_mean",
    ),
    "sporting_form": (
        "home_matches_played", "home_points", "home_ppg", "home_gdpg",
        "home_form5_points", "home_form5_gd",
        "away_matches_played", "away_points", "away_ppg", "away_gdpg",
        "away_form5_points", "away_form5_gd",
        "ppg_gap", "form5_points_gap", "gdpg_gap",
        "combined_ppg", "abs_ppg_gap", "combined_form5", "abs_form5_gap",
    ),
    "table_context": (
        "home_position", "away_position", "position_gap", "abs_position_gap",
        "combined_table_strength", "top4_any", "top4_both", "bottom4_any",
        "late_season_top4", "late_season_bottom4",
    ),
    "rest_congestion": (
        "home_days_since_last", "home_matches_last14",
        "away_days_since_last", "away_matches_last14",
        "rest_gap", "congestion_sum",
    ),
    "capacity": ("capacity",),
}

RECENCY_POLICIES = ("uniform", "linear_075", "exp_075", "exp_050")
MODEL_POLICIES = ("incumbent", "rf_absolute_leaf3", "extra_leaf5", "hist_absolute_31")


@dataclass(frozen=True)
class Candidate:
    id: str
    family: FeatureFamily
    dropped_group: str | None = None
    recency_policy: str = "uniform"
    model_policy: str = "incumbent"


@dataclass
class FittedCandidate:
    horizon: str
    baseline_column: str
    preprocessor: Any
    estimator: Any
    numeric_features: list[str]
    training_seasons: list[str]
    training_rows: int
    candidate: Candidate
    sample_weight_by_season: dict[str, float]

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        if rows.empty:
            return np.asarray([], dtype=float)
        matrix = self.preprocessor.transform(rows[CAT + self.numeric_features])
        residual = self.estimator.predict(matrix)
        capacity = rows["capacity"].astype(float).to_numpy()
        baseline = rows[self.baseline_column].astype(float).to_numpy()
        return np.clip(baseline + residual * capacity, 0.0, capacity)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _historical_rows(path: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(path)
    rows: list[dict[str, Any]] = []
    for row in frame.to_dict("records"):
        rows.append({
            "dataset_version": "committed-frozen-runtime-input",
            "season": row["season"],
            "round_no": int(row["round"]),
            "match_date": row["date"],
            "kickoff_time_local": row["kickoff_time_local"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "home_club_key": row["home_club_key"],
            "away_club_key": row["away_club_key"],
            "home_goals": int(row["home_goals"]),
            "away_goals": int(row["away_goals"]),
            "attendance": int(row["attendance"]),
            "default_demand_training_eligible": int(row["attendance"]) != 0,
            "match_key": row["match_key"],
        })
    return rows


def load_feature_store(path: Path) -> pd.DataFrame:
    matches = _canonical_matches(_historical_rows(path))
    if len(matches) != 1530 or matches["match_key"].nunique() != 1530:
        raise RuntimeError(
            f"expected 1530 canonical matches, got rows={len(matches)} "
            f"unique={matches['match_key'].nunique()}"
        )
    store = build_feature_store(matches)
    report = quality_report(store)
    if report["status"] != "PASS":
        raise RuntimeError(f"feature-store quality failed: {report}")
    return store


def metrics(actual: np.ndarray, prediction: np.ndarray) -> dict[str, float | int]:
    actual = np.asarray(actual, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    ae = np.abs(prediction - actual)
    denom = float(np.sum(actual))
    return {
        "n": int(len(actual)),
        "mae": float(np.mean(ae)),
        "median_ae": float(np.median(ae)),
        "bias": float(np.mean(prediction - actual)),
        "wape": float(np.sum(ae) / denom) if denom > 0 else float("nan"),
        "p90_ae": float(np.quantile(ae, 0.90)),
    }


def comparison_scorecard(
    rows: pd.DataFrame,
    candidate_prediction: np.ndarray,
    incumbent_prediction: np.ndarray,
) -> dict[str, Any]:
    actual = rows["target_attendance"].astype(float).to_numpy()
    candidate_prediction = np.asarray(candidate_prediction, dtype=float)
    incumbent_prediction = np.asarray(incumbent_prediction, dtype=float)

    candidate_metrics = metrics(actual, candidate_prediction)
    incumbent_metrics = metrics(actual, incumbent_prediction)
    candidate_ae = np.abs(candidate_prediction - actual)
    incumbent_ae = np.abs(incumbent_prediction - actual)
    degradation = candidate_ae - incumbent_ae

    clubs: dict[str, dict[str, float | int]] = {}
    club_frame = pd.DataFrame({
        "club": rows["home_club_key"].astype(str).to_numpy(),
        "actual": actual,
        "candidate": candidate_prediction,
        "incumbent": incumbent_prediction,
    })
    for club, group in club_frame.groupby("club", sort=True):
        if len(group) < MIN_CLUB_BREAKDOWN_N:
            continue
        cm = metrics(group["actual"].to_numpy(), group["candidate"].to_numpy())
        im = metrics(group["actual"].to_numpy(), group["incumbent"].to_numpy())
        clubs[str(club)] = {
            "n": int(len(group)),
            "candidate_mae": float(cm["mae"]),
            "incumbent_mae": float(im["mae"]),
            "mae_improvement": float(im["mae"] - cm["mae"]),
        }

    return {
        "candidate": candidate_metrics,
        "incumbent": incumbent_metrics,
        "mae_improvement": float(incumbent_metrics["mae"] - candidate_metrics["mae"]),
        "worst_event_degradation": float(np.max(degradation)),
        "best_event_improvement": float(np.max(-degradation)),
        "event_improvement_rate": float(np.mean(candidate_ae < incumbent_ae)),
        "event_equal_rate": float(np.mean(np.isclose(candidate_ae, incumbent_ae))),
        "club_breakdown_min_n_5": clubs,
    }


def eligible_rows(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    baseline_column: str,
) -> pd.DataFrame:
    return store[
        (store["horizon"].astype(str) == horizon)
        & store["training_eligible"].astype(bool)
        & (store["season"] == season)
        & store[baseline_column].notna()
    ].copy().reset_index(drop=True)


def season_weight_map(training_seasons: list[str], policy: str) -> dict[str, float]:
    n = len(training_seasons)
    if n == 0:
        raise ValueError("training seasons cannot be empty")
    if policy == "uniform":
        values = np.ones(n, dtype=float)
    elif policy == "linear_075":
        values = np.linspace(0.75, 1.0, n, dtype=float)
    elif policy == "exp_075":
        distance = np.arange(n - 1, -1, -1, dtype=float)
        values = np.power(0.75, distance)
    elif policy == "exp_050":
        distance = np.arange(n - 1, -1, -1, dtype=float)
        values = np.power(0.50, distance)
    else:
        raise KeyError(policy)
    return {season: float(value) for season, value in zip(training_seasons, values, strict=True)}


def resolved_feature_groups(store: pd.DataFrame, horizon: str) -> tuple[dict[str, list[str]], list[str]]:
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    numeric = feature_columns(store, spec.feature_mode)
    protected = {spec.baseline_column}
    resolved: dict[str, list[str]] = {}
    seen: set[str] = set()

    for name, declared in FEATURE_GROUPS.items():
        columns = [column for column in declared if column in numeric and column not in protected]
        if columns:
            overlap = seen.intersection(columns)
            if overlap:
                raise RuntimeError(f"feature-group overlap in {horizon}/{name}: {sorted(overlap)}")
            resolved[name] = columns
            seen.update(columns)

    unassigned = sorted(set(numeric) - protected - seen)
    if unassigned:
        raise RuntimeError(
            f"unassigned numeric features for {horizon}: {unassigned}. "
            "Update FEATURE_GROUPS explicitly; do not skip new features."
        )
    return resolved, sorted(protected.intersection(numeric))


def candidate_set(store: pd.DataFrame, horizon: str) -> tuple[list[Candidate], dict[str, list[str]], list[str]]:
    groups, protected = resolved_feature_groups(store, horizon)
    candidates = [Candidate(id="incumbent", family="incumbent")]
    candidates.extend(
        Candidate(
            id=f"ablate-{group}",
            family="ablation",
            dropped_group=group,
        )
        for group in groups
    )
    candidates.extend(
        Candidate(
            id=f"recency-{policy}",
            family="recency",
            recency_policy=policy,
        )
        for policy in RECENCY_POLICIES
        if policy != "uniform"
    )
    candidates.extend(
        Candidate(
            id=f"model-{policy}",
            family="model_family",
            model_policy=policy,
        )
        for policy in MODEL_POLICIES
        if policy != "incumbent"
    )
    return candidates, groups, protected


def estimator_for(policy: str, incumbent_name: str):
    if policy == "incumbent":
        return _estimator(incumbent_name)
    if policy == "rf_absolute_leaf3":
        return RandomForestRegressor(
            n_estimators=300,
            criterion="absolute_error",
            min_samples_leaf=3,
            max_features=0.8,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
    if policy == "extra_leaf5":
        return ExtraTreesRegressor(
            n_estimators=500,
            min_samples_leaf=5,
            max_features=0.8,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
    if policy == "hist_absolute_31":
        return HistGradientBoostingRegressor(
            loss="absolute_error",
            learning_rate=0.04,
            max_iter=300,
            max_leaf_nodes=31,
            min_samples_leaf=10,
            l2_regularization=1.0,
            random_state=RANDOM_SEED,
        )
    raise KeyError(policy)


def fit_candidate(
    store: pd.DataFrame,
    horizon: str,
    training_seasons: list[str],
    candidate: Candidate,
    groups: dict[str, list[str]],
) -> FittedCandidate:
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = store[
        (store["horizon"].astype(str) == horizon)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(training_seasons)
        & store[spec.baseline_column].notna()
    ].copy()
    if rows.empty:
        raise ValueError(f"no eligible training rows for {horizon}")

    numeric = feature_columns(store, spec.feature_mode)
    if candidate.dropped_group is not None:
        drop = set(groups[candidate.dropped_group])
        if spec.baseline_column in drop:
            raise RuntimeError("direct baseline column may not be ablated in stage 1")
        numeric = [column for column in numeric if column not in drop]

    pre = _preprocessor(numeric)
    x_train = pre.fit_transform(rows[CAT + numeric])
    capacity = rows["capacity"].astype(float).to_numpy()
    y_train = (
        rows["target_attendance"].astype(float).to_numpy() / capacity
        - rows[spec.baseline_column].astype(float).to_numpy() / capacity
    )

    weights_by_season = season_weight_map(training_seasons, candidate.recency_policy)
    sample_weight = rows["season"].map(weights_by_season).astype(float).to_numpy()

    model = estimator_for(candidate.model_policy, spec.estimator_name)
    model.fit(x_train, y_train, sample_weight=sample_weight)

    return FittedCandidate(
        horizon=horizon,
        baseline_column=spec.baseline_column,
        preprocessor=pre,
        estimator=model,
        numeric_features=numeric,
        training_seasons=list(training_seasons),
        training_rows=int(len(rows)),
        candidate=candidate,
        sample_weight_by_season=weights_by_season,
    )


def verify_incumbent(
    horizon: str,
    season: str,
    value: float,
    split_kind: str,
) -> None:
    if split_kind == "holdout":
        expected = EXPECTED_HOLDOUT_MAE[horizon][season]
        atol = EXPECTED_HOLDOUT_ATOL[horizon]
        if not np.isclose(value, expected, rtol=0.0, atol=atol):
            raise RuntimeError(
                f"incumbent benchmark mismatch {horizon}/{season}: "
                f"actual={value} expected={expected}"
            )
    elif split_kind == "development" and horizon in EXPECTED_DEVELOPMENT_MAE:
        expected = EXPECTED_DEVELOPMENT_MAE[horizon]
        if not np.isclose(value, expected, rtol=0.0, atol=1e-9):
            raise RuntimeError(
                f"incumbent development mismatch {horizon}/{season}: "
                f"actual={value} expected={expected}"
            )


def score_split(
    store: pd.DataFrame,
    horizon: str,
    training_seasons: list[str],
    test_season: str,
    split_kind: str,
    candidates: list[Candidate],
    groups: dict[str, list[str]],
) -> dict[str, Any]:
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    test = eligible_rows(store, horizon, test_season, spec.baseline_column)
    if test.empty:
        raise RuntimeError(f"empty test split {horizon}/{test_season}")

    incumbent_runtime = fit_structural_prior_runtime(store, horizon, training_seasons)
    incumbent_prediction = incumbent_runtime.predict(test)
    incumbent_metrics = metrics(
        test["target_attendance"].astype(float).to_numpy(),
        incumbent_prediction,
    )
    verify_incumbent(horizon, test_season, float(incumbent_metrics["mae"]), split_kind)

    scored: dict[str, Any] = {}
    for candidate in candidates:
        if candidate.id == "incumbent":
            prediction = incumbent_prediction
            training_rows = incumbent_runtime.training_rows
            numeric_features = incumbent_runtime.numeric_features
            weights = season_weight_map(training_seasons, "uniform")
        else:
            fitted = fit_candidate(store, horizon, training_seasons, candidate, groups)
            prediction = fitted.predict(test)
            training_rows = fitted.training_rows
            numeric_features = fitted.numeric_features
            weights = fitted.sample_weight_by_season

        scored[candidate.id] = {
            "candidate": asdict(candidate),
            "training_seasons": list(training_seasons),
            "training_rows": int(training_rows),
            "test_season": test_season,
            "test_rows": int(len(test)),
            "numeric_feature_count": int(len(numeric_features)),
            "sample_weight_by_season": weights,
            "scorecard": comparison_scorecard(test, prediction, incumbent_prediction),
        }

    return {
        "kind": split_kind,
        "training_seasons": list(training_seasons),
        "test_season": test_season,
        "incumbent_model_spec_id": spec.model_spec_id,
        "incumbent_baseline_column": spec.baseline_column,
        "incumbent_feature_mode": spec.feature_mode,
        "incumbent_mae": float(incumbent_metrics["mae"]),
        "candidates": scored,
    }


def horizon_experiment(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    candidates, groups, protected = candidate_set(store, horizon)

    development = score_split(
        store,
        horizon,
        DEV_TRAIN,
        DEV_SEASON,
        "development",
        candidates,
        groups,
    )
    holdout_results = {}
    for season, train in HOLDOUTS:
        holdout_results[season] = score_split(
            store,
            horizon,
            train,
            season,
            "holdout",
            candidates,
            groups,
        )

    development_ranking = sorted(
        (
            {
                "candidate_id": candidate.id,
                "mae": float(
                    development["candidates"][candidate.id]["scorecard"]["candidate"]["mae"]
                ),
                "mae_improvement_vs_incumbent": float(
                    development["candidates"][candidate.id]["scorecard"]["mae_improvement"]
                ),
            }
            for candidate in candidates
        ),
        key=lambda item: (item["mae"], item["candidate_id"]),
    )
    selected_id = development_ranking[0]["candidate_id"]

    holdout_summary = []
    both_improve = True
    for season, _ in HOLDOUTS:
        split = holdout_results[season]
        score = split["candidates"][selected_id]["scorecard"]
        improvement = float(score["mae_improvement"])
        both_improve = both_improve and improvement > 0.0
        holdout_summary.append({
            "season": season,
            "incumbent_mae": float(score["incumbent"]["mae"]),
            "selected_candidate_mae": float(score["candidate"]["mae"]),
            "mae_improvement": improvement,
            "worst_event_degradation": float(score["worst_event_degradation"]),
            "event_improvement_rate": float(score["event_improvement_rate"]),
        })

    mean_incumbent = float(np.mean([item["incumbent_mae"] for item in holdout_summary]))
    mean_selected = float(np.mean([item["selected_candidate_mae"] for item in holdout_summary]))
    mean_improvement = mean_incumbent - mean_selected

    if selected_id == "incumbent":
        signal = "INCUMBENT_SELECTED_ON_DEVELOPMENT"
    elif both_improve and mean_improvement > 0:
        signal = "PROMISING_CONSISTENT_HOLDOUT_IMPROVEMENT"
    elif mean_improvement > 0:
        signal = "MIXED_BUT_POSITIVE_MEAN"
    else:
        signal = "NOT_PROVEN"

    return {
        "horizon": horizon,
        "incumbent": {
            "model_spec_id": CURRENT_EARLY_RUNTIME_SPECS[horizon].model_spec_id,
            "baseline_column": CURRENT_EARLY_RUNTIME_SPECS[horizon].baseline_column,
            "feature_mode": CURRENT_EARLY_RUNTIME_SPECS[horizon].feature_mode,
        },
        "feature_groups_resolved": groups,
        "protected_direct_baseline_feature": protected,
        "candidate_count": len(candidates),
        "candidates": [asdict(candidate) for candidate in candidates],
        "development": development,
        "development_ranking": development_ranking,
        "selected_candidate_id": selected_id,
        "holdouts": holdout_results,
        "selected_holdout_summary": holdout_summary,
        "mean_holdout_incumbent_mae": mean_incumbent,
        "mean_holdout_selected_mae": mean_selected,
        "mean_holdout_mae_improvement": mean_improvement,
        "signal": signal,
        "promotion_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--horizons",
        default=",".join(HORIZONS),
        help="comma-separated subset of T-30,T-14,T-7,T-3,T-1",
    )
    args = parser.parse_args()

    requested = [item.strip() for item in args.horizons.split(",") if item.strip()]
    invalid = sorted(set(requested) - set(HORIZONS))
    if invalid:
        raise ValueError(f"unsupported horizons: {invalid}")

    manifest = json.loads(args.manifest.read_text())
    expected_input_hash = manifest["historical_runtime"]["sha256"]
    actual_input_hash = sha256_file(args.historical_runtime)
    if actual_input_hash != expected_input_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_input_hash} "
            f"expected={expected_input_hash}"
        )

    store = load_feature_store(args.historical_runtime)
    quality = quality_report(store)

    horizons = [horizon_experiment(store, horizon) for horizon in requested]

    result = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_HISTORICAL_CHALLENGER_EVIDENCE",
        "promotion_allowed": False,
        "evidence_class": "EXPOSED_HISTORICAL_REFERENCE_SEASONS",
        "protocol": {
            "selection": {
                "training_seasons": DEV_TRAIN,
                "development_season": DEV_SEASON,
                "selection_metric": "MAE",
                "candidate_changes": "one-change-at-a-time stage 1",
            },
            "holdouts": [
                {"season": season, "training_seasons": train}
                for season, train in HOLDOUTS
            ],
            "event_is_independent_unit": True,
            "random_snapshot_split": False,
            "future_leakage_allowed": False,
            "production_activation": False,
            "holdouts_already_exposed": True,
        },
        "input": {
            "historical_runtime_path": str(args.historical_runtime),
            "historical_runtime_sha256": actual_input_hash,
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
        "candidate_contract": {
            "recency_policies": list(RECENCY_POLICIES),
            "model_policies": list(MODEL_POLICIES),
            "feature_groups_declared": {
                name: list(columns) for name, columns in FEATURE_GROUPS.items()
            },
            "ablation_rule": (
                "drop exactly one resolved numeric feature group; never drop the "
                "direct baseline column in stage 1"
            ),
        },
        "horizons": horizons,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "evidence_class": result["evidence_class"],
        "promotion_allowed": False,
        "horizons": [
            {
                "horizon": item["horizon"],
                "selected_candidate_id": item["selected_candidate_id"],
                "signal": item["signal"],
                "mean_holdout_incumbent_mae": item["mean_holdout_incumbent_mae"],
                "mean_holdout_selected_mae": item["mean_holdout_selected_mae"],
                "mean_holdout_mae_improvement": item["mean_holdout_mae_improvement"],
            }
            for item in horizons
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
