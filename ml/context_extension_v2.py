#!/usr/bin/env python3
"""C2 Context Extension v2 — PIT-safe match stakes + sequence-aware form.

The experiment measures incremental context value over the frozen historical
A2+B2 Pre-Live candidate stack, not over the older production-only Structural
Prior.

Candidate groups are deliberately small and predeclared:
- sequence_only;
- stakes_only;
- sequence_stakes;
- NO_CONTEXT fallback.

Development selection uses 2022/23 and 2023/24 only. 2024/25 and 2025/26 are
exposed reference seasons scored only after the context contract is frozen.
No production activation occurs automatically.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor

from ml.current_season_residual_regime_v1 import (
    RegimeVariant,
    add_same_season_residual_state,
    apply_variant,
    base_predictions_for_season,
)
from ml.demand_engine.freeze_structural_prior_artifacts import _canonical_matches
from ml.demand_engine.structural_prior_runtime import (
    CAT,
    CURRENT_EARLY_RUNTIME_SPECS,
    _estimator,
    _preprocessor,
    feature_columns,
)
from ml.pre_live_baseline_optimization_v1 import (
    _historical_rows,
    comparison_scorecard,
    eligible_rows,
    load_feature_store,
    sha256_file,
)

EXPERIMENT = "c2-context-extension-v2"
WORKSTREAM = "c2 — Match context"
HORIZONS = ["T-30", "T-14", "T-7", "T-3", "T-1"]
DEVELOPMENT_FOLDS = [
    ("2022/2023", ["2021/2022"]),
    ("2023/2024", ["2021/2022", "2022/2023"]),
]
REFERENCE_HOLDOUTS = [
    ("2024/2025", ["2021/2022", "2022/2023", "2023/2024"]),
    ("2025/2026", ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]),
]
RANDOM_SEED = 42
TOTAL_LEAGUE_MATCHES_PER_TEAM = 34
MIN_MEAN_RELATIVE_MAE_IMPROVEMENT = 0.005
NEAR_BEST_GAIN_RETENTION = 0.90
SELECTION_ATOL = 1e-12

T7_CONTEXT_CONFIG = {
    "loss": "absolute_error",
    "learning_rate": 0.04,
    "max_iter": 300,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
    "random_state": RANDOM_SEED,
}

FROZEN_B2: dict[str, RegimeVariant] = {
    "T-7": RegimeVariant(source="ewma50_residual_fraction", shrink_k=6),
    "T-3": RegimeVariant(source="ewma50_residual_fraction", shrink_k=2),
    "T-1": RegimeVariant(source="ewma50_residual_fraction", shrink_k=6),
}
FROZEN_B2_MIN_PRIOR = 3

# Exact frozen A2+B2 stack MAE from the final b2 fixed temporal audit.
EXPECTED_FROZEN_STACK_MAE: dict[str, dict[str, float]] = {
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
    # T-30 / T-14 have no frozen b2 layer. Reference values are hard-asserted;
    # early-development folds remain visible evidence without inventing an
    # expected number that was not previously frozen canonically.
    "T-30": {
        "2024/2025": 1889.3672272292858,
        "2025/2026": 1846.2792557036205,
    },
    "T-14": {
        "2024/2025": 1748.4970512511325,
        "2025/2026": 1870.393553818474,
    },
}
EXPECTED_ATOL = 1e-9

SEQUENCE_COLUMNS = (
    "ctx_home_win_streak",
    "ctx_away_win_streak",
    "ctx_home_unbeaten_streak",
    "ctx_away_unbeaten_streak",
    "ctx_home_loss_streak",
    "ctx_away_loss_streak",
    "ctx_home_points_accel3",
    "ctx_away_points_accel3",
    "ctx_win_streak_gap",
    "ctx_unbeaten_streak_gap",
    "ctx_loss_streak_gap",
    "ctx_points_accel3_gap",
    "ctx_home_home_win_streak",
    "ctx_home_home_unbeaten_streak",
)

STAKES_COLUMNS = (
    "ctx_home_title_pressure",
    "ctx_away_title_pressure",
    "ctx_home_top4_pressure",
    "ctx_away_top4_pressure",
    "ctx_home_bottom4_pressure",
    "ctx_away_bottom4_pressure",
    "ctx_direct_points_pressure",
    "ctx_home_max_stakes",
    "ctx_away_max_stakes",
    "ctx_match_max_stakes",
    "ctx_match_mean_stakes",
)

ALL_CONTEXT_COLUMNS = tuple([*SEQUENCE_COLUMNS, *STAKES_COLUMNS])


@dataclass(frozen=True)
class ContextCandidate:
    id: str
    columns: tuple[str, ...]


CANDIDATES = (
    ContextCandidate("NO_CONTEXT", ()),
    ContextCandidate("sequence_only", SEQUENCE_COLUMNS),
    ContextCandidate("stakes_only", STAKES_COLUMNS),
    ContextCandidate("sequence_stakes", ALL_CONTEXT_COLUMNS),
)


@dataclass
class FittedContextModel:
    horizon: str
    baseline_column: str
    preprocessor: Any
    estimator: Any
    numeric_features: list[str]
    training_rows: int
    training_seasons: list[str]
    candidate_id: str

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        matrix = self.preprocessor.transform(rows[CAT + self.numeric_features])
        residual = self.estimator.predict(matrix)
        capacity = rows["capacity"].astype(float).to_numpy()
        baseline = rows[self.baseline_column].astype(float).to_numpy()
        return np.clip(baseline + residual * capacity, 0.0, capacity)


def _result_symbol(gf: int, ga: int) -> str:
    return "W" if gf > ga else ("D" if gf == ga else "L")


def _trailing_count(values: list[str], predicate) -> int:
    count = 0
    for value in reversed(values):
        if not predicate(value):
            break
        count += 1
    return count


def streak_features(results: list[str]) -> dict[str, int]:
    return {
        "win": _trailing_count(results, lambda result: result == "W"),
        "unbeaten": _trailing_count(results, lambda result: result != "L"),
        "loss": _trailing_count(results, lambda result: result == "L"),
    }


def points_acceleration3(points: list[int]) -> float:
    if len(points) < 6:
        return float("nan")
    return float(sum(points[-3:]) - sum(points[-6:-3]))


def _pressure(points: float, target_points: float, remaining_max_points: float, progress: float) -> float:
    denominator = max(float(remaining_max_points), 3.0)
    proximity = 1.0 - abs(float(points) - float(target_points)) / denominator
    return float(progress * np.clip(proximity, 0.0, 1.0))


def _title_pressure(points: float, leader_points: float, remaining_max_points: float, progress: float) -> float:
    denominator = max(float(remaining_max_points), 3.0)
    gap = max(float(leader_points) - float(points), 0.0)
    return float(progress * np.clip(1.0 - gap / denominator, 0.0, 1.0))


def build_context_store(matches: pd.DataFrame, snapshots: pd.DataFrame) -> pd.DataFrame:
    """Build PIT context rows aligned 1:1 with the canonical snapshot store."""
    required_matches = {
        "match_key", "season", "home_club_key", "away_club_key", "home_goals",
        "away_goals", "kickoff_at", "completed_at",
    }
    required_snapshots = {
        "match_key", "season", "horizon", "as_of_at", "kickoff_at",
        "home_club_key", "away_club_key", "season_progress",
    }
    if missing := sorted(required_matches - set(matches.columns)):
        raise RuntimeError(f"context matches missing columns: {missing}")
    if missing := sorted(required_snapshots - set(snapshots.columns)):
        raise RuntimeError(f"context snapshots missing columns: {missing}")

    participants = {
        season: sorted(
            set(group["home_club_key"].astype(str)) | set(group["away_club_key"].astype(str))
        )
        for season, group in matches.groupby("season", sort=False)
    }

    def fresh_state() -> dict[str, Any]:
        return {
            "played": 0,
            "points": 0,
            "gf": 0,
            "ga": 0,
            "results": [],
            "points_seq": [],
            "home_results": [],
        }

    state: dict[tuple[str, str], dict[str, Any]] = defaultdict(fresh_state)
    events: list[tuple[pd.Timestamp, int, str, Any]] = []
    for row in snapshots.itertuples(index=False):
        events.append((pd.Timestamp(row.as_of_at), 0, "snapshot", row))
    for row in matches.itertuples(index=False):
        events.append((pd.Timestamp(row.completed_at), 1, "complete", row))
    events.sort(key=lambda item: (item[0], item[1], str(getattr(item[3], "match_key", ""))))

    output: list[dict[str, Any]] = []
    for timestamp, _, event_type, row in events:
        if event_type == "complete":
            season = str(row.season)
            home = str(row.home_club_key)
            away = str(row.away_club_key)
            home_goals = int(row.home_goals)
            away_goals = int(row.away_goals)
            for club, gf, ga, is_home in (
                (home, home_goals, away_goals, True),
                (away, away_goals, home_goals, False),
            ):
                current = state[(season, club)]
                result = _result_symbol(gf, ga)
                points = 3 if result == "W" else (1 if result == "D" else 0)
                current["played"] += 1
                current["points"] += points
                current["gf"] += gf
                current["ga"] += ga
                current["results"].append(result)
                current["points_seq"].append(points)
                if is_home:
                    current["home_results"].append(result)
            continue

        season = str(row.season)
        home = str(row.home_club_key)
        away = str(row.away_club_key)
        progress = float(row.season_progress)
        home_state = state[(season, home)]
        away_state = state[(season, away)]
        home_streak = streak_features(home_state["results"])
        away_streak = streak_features(away_state["results"])
        home_home_streak = streak_features(home_state["home_results"])
        home_accel = points_acceleration3(home_state["points_seq"])
        away_accel = points_acceleration3(away_state["points_seq"])

        table = []
        for club in participants[season]:
            club_state = state[(season, club)]
            table.append(
                (
                    club,
                    float(club_state["points"]),
                    int(club_state["gf"] - club_state["ga"]),
                    int(club_state["gf"]),
                    int(club_state["played"]),
                )
            )
        table.sort(key=lambda item: (-item[1], -item[2], -item[3], item[0]))
        if not table:
            raise RuntimeError(f"empty participant table for {season}")
        leader_points = float(table[0][1])
        p4_points = float(table[min(3, len(table) - 1)][1])
        p15_points = float(table[min(14, len(table) - 1)][1])

        home_remaining = 3.0 * max(TOTAL_LEAGUE_MATCHES_PER_TEAM - int(home_state["played"]), 1)
        away_remaining = 3.0 * max(TOTAL_LEAGUE_MATCHES_PER_TEAM - int(away_state["played"]), 1)
        home_points = float(home_state["points"])
        away_points = float(away_state["points"])

        home_title = _title_pressure(home_points, leader_points, home_remaining, progress)
        away_title = _title_pressure(away_points, leader_points, away_remaining, progress)
        home_top4 = _pressure(home_points, p4_points, home_remaining, progress)
        away_top4 = _pressure(away_points, p4_points, away_remaining, progress)
        home_bottom4 = _pressure(home_points, p15_points, home_remaining, progress)
        away_bottom4 = _pressure(away_points, p15_points, away_remaining, progress)
        avg_remaining = max((home_remaining + away_remaining) / 2.0, 3.0)
        direct_pressure = float(
            progress * np.clip(1.0 - abs(home_points - away_points) / avg_remaining, 0.0, 1.0)
        )
        home_max_stakes = max(home_title, home_top4, home_bottom4)
        away_max_stakes = max(away_title, away_top4, away_bottom4)

        output.append({
            "match_key": str(row.match_key),
            "season": season,
            "horizon": str(row.horizon),
            "as_of_at": pd.Timestamp(row.as_of_at),
            "ctx_home_win_streak": home_streak["win"],
            "ctx_away_win_streak": away_streak["win"],
            "ctx_home_unbeaten_streak": home_streak["unbeaten"],
            "ctx_away_unbeaten_streak": away_streak["unbeaten"],
            "ctx_home_loss_streak": home_streak["loss"],
            "ctx_away_loss_streak": away_streak["loss"],
            "ctx_home_points_accel3": home_accel,
            "ctx_away_points_accel3": away_accel,
            "ctx_win_streak_gap": home_streak["win"] - away_streak["win"],
            "ctx_unbeaten_streak_gap": home_streak["unbeaten"] - away_streak["unbeaten"],
            "ctx_loss_streak_gap": home_streak["loss"] - away_streak["loss"],
            "ctx_points_accel3_gap": home_accel - away_accel if not (np.isnan(home_accel) or np.isnan(away_accel)) else np.nan,
            "ctx_home_home_win_streak": home_home_streak["win"],
            "ctx_home_home_unbeaten_streak": home_home_streak["unbeaten"],
            "ctx_home_title_pressure": home_title,
            "ctx_away_title_pressure": away_title,
            "ctx_home_top4_pressure": home_top4,
            "ctx_away_top4_pressure": away_top4,
            "ctx_home_bottom4_pressure": home_bottom4,
            "ctx_away_bottom4_pressure": away_bottom4,
            "ctx_direct_points_pressure": direct_pressure,
            "ctx_home_max_stakes": home_max_stakes,
            "ctx_away_max_stakes": away_max_stakes,
            "ctx_match_max_stakes": max(home_max_stakes, away_max_stakes, direct_pressure),
            "ctx_match_mean_stakes": float((home_max_stakes + away_max_stakes + direct_pressure) / 3.0),
        })

    context = pd.DataFrame(output)
    if len(context) != len(snapshots):
        raise RuntimeError(f"context rows mismatch: {len(context)} vs {len(snapshots)}")
    if context.duplicated(["match_key", "horizon"]).any():
        raise RuntimeError("duplicate context match/horizon rows")
    return context.sort_values(["as_of_at", "match_key", "horizon"]).reset_index(drop=True)


def augment_feature_store(base_store: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    merged = base_store.merge(
        context.drop(columns=["season", "as_of_at"]),
        on=["match_key", "horizon"],
        how="left",
        validate="one_to_one",
    )
    if len(merged) != len(base_store):
        raise RuntimeError("context merge changed feature-store row count")
    if merged[list(ALL_CONTEXT_COLUMNS)].isna().all(axis=None):
        raise RuntimeError("all context values are missing")
    return merged.sort_values(["as_of_at", "match_key", "horizon"]).reset_index(drop=True)


def context_missingness(store: pd.DataFrame, columns: tuple[str, ...]) -> dict[str, float]:
    return {column: float(store[column].isna().mean()) for column in columns}


def fit_context_model(
    store: pd.DataFrame,
    horizon: str,
    training_seasons: list[str],
    candidate: ContextCandidate,
) -> FittedContextModel:
    if not candidate.columns:
        raise ValueError("NO_CONTEXT is represented by canonical frozen baseline, not refit")
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = store[
        (store["horizon"].astype(str) == horizon)
        & store["training_eligible"].astype(bool)
        & store["season"].isin(training_seasons)
        & store[spec.baseline_column].notna()
    ].copy()
    if rows.empty:
        raise RuntimeError(f"no context training rows for {horizon}/{training_seasons}")

    without_context = store.drop(columns=list(ALL_CONTEXT_COLUMNS), errors="ignore")
    numeric = feature_columns(without_context, spec.feature_mode)
    numeric = [*numeric, *candidate.columns]
    if len(numeric) != len(set(numeric)):
        raise RuntimeError(f"duplicate numeric context features for {candidate.id}")

    preprocessor = _preprocessor(numeric)
    matrix = preprocessor.fit_transform(rows[CAT + numeric])
    capacity = rows["capacity"].astype(float).to_numpy()
    target = (
        rows["target_attendance"].astype(float).to_numpy() / capacity
        - rows[spec.baseline_column].astype(float).to_numpy() / capacity
    )
    if horizon == "T-7":
        estimator = HistGradientBoostingRegressor(**T7_CONTEXT_CONFIG)
    else:
        estimator = _estimator(spec.estimator_name)
    estimator.fit(matrix, target)
    return FittedContextModel(
        horizon=horizon,
        baseline_column=spec.baseline_column,
        preprocessor=preprocessor,
        estimator=estimator,
        numeric_features=numeric,
        training_rows=int(len(rows)),
        training_seasons=list(training_seasons),
        candidate_id=candidate.id,
    )


def apply_frozen_b2(
    rows: pd.DataFrame,
    base_prediction: np.ndarray,
    horizon: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    base = np.asarray(base_prediction, dtype=float)
    if horizon not in FROZEN_B2:
        return base.copy(), {
            "policy": "NO_ADJUSTMENT",
            "active_rows": 0,
            "active_share": 0.0,
        }
    state_rows = add_same_season_residual_state(rows, base)
    candidate, diagnostics = apply_variant(state_rows, base, FROZEN_B2[horizon])
    n = state_rows["regime_prior_home_matches"].astype(int).to_numpy()
    active = n >= FROZEN_B2_MIN_PRIOR
    final = np.where(active, candidate, base)
    return final, {
        "policy": f"{FROZEN_B2[horizon].id}-min{FROZEN_B2_MIN_PRIOR}",
        "active_rows": int(np.sum(np.abs(final - base) > 1e-12)),
        "active_share": float(np.mean(np.abs(final - base) > 1e-12)),
        "mean_abs_correction_seats": float(np.mean(np.abs(final - base))),
        "v1_diagnostics": diagnostics,
    }


def frozen_stack_for_season(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
) -> tuple[pd.DataFrame, np.ndarray, dict[str, Any]]:
    base = base_predictions_for_season(store, horizon, season, training_seasons)
    final, b2_diag = apply_frozen_b2(base.rows, base.prediction, horizon)
    actual = base.rows["target_attendance"].astype(float).to_numpy()
    mae = float(np.mean(np.abs(final - actual)))
    expected = EXPECTED_FROZEN_STACK_MAE.get(horizon, {}).get(season)
    if expected is not None and not np.isclose(mae, expected, rtol=0.0, atol=EXPECTED_ATOL):
        raise RuntimeError(
            f"frozen a2+b2 baseline mismatch {horizon}/{season}: actual={mae} expected={expected}"
        )
    return base.rows.copy(), final, {
        "a2_base_model_id": base.model_id,
        "a2_training_rows": int(base.training_rows),
        "b2": b2_diag,
        "mae": mae,
        "hard_expected_mae": expected,
    }


def candidate_stack_for_season(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    candidate: ContextCandidate,
) -> tuple[pd.DataFrame, np.ndarray, dict[str, Any]]:
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = eligible_rows(store, horizon, season, spec.baseline_column)
    model = fit_context_model(store, horizon, training_seasons, candidate)
    context_base = model.predict(rows)
    final, b2_diag = apply_frozen_b2(rows, context_base, horizon)
    return rows, final, {
        "context_candidate_id": candidate.id,
        "context_columns": list(candidate.columns),
        "training_rows": model.training_rows,
        "numeric_feature_count": len(model.numeric_features),
        "b2": b2_diag,
    }


def score_fold(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
    candidates: tuple[ContextCandidate, ...],
) -> dict[str, Any]:
    baseline_rows, baseline_prediction, baseline_detail = frozen_stack_for_season(
        store, horizon, season, training_seasons
    )
    actual = baseline_rows["target_attendance"].astype(float).to_numpy()
    baseline_score = comparison_scorecard(baseline_rows, baseline_prediction, baseline_prediction)
    scored: dict[str, Any] = {
        "NO_CONTEXT": {
            "candidate": asdict(CANDIDATES[0]),
            "detail": baseline_detail,
            "scorecard": baseline_score,
        }
    }

    for candidate in candidates:
        if candidate.id == "NO_CONTEXT":
            continue
        rows, prediction, detail = candidate_stack_for_season(
            store, horizon, season, training_seasons, candidate
        )
        if rows["match_key"].astype(str).tolist() != baseline_rows["match_key"].astype(str).tolist():
            raise RuntimeError(f"context/base row alignment mismatch {horizon}/{season}/{candidate.id}")
        scored[candidate.id] = {
            "candidate": asdict(candidate),
            "detail": detail,
            "scorecard": comparison_scorecard(baseline_rows, prediction, baseline_prediction),
        }

    return {
        "horizon": horizon,
        "season": season,
        "training_seasons": list(training_seasons),
        "test_rows": int(len(baseline_rows)),
        "baseline": baseline_detail,
        "candidates": scored,
        "target_mean": float(np.mean(actual)),
    }


def aggregate_development(
    folds: list[dict[str, Any]],
    candidates: tuple[ContextCandidate, ...],
) -> list[dict[str, Any]]:
    result = []
    for candidate in candidates:
        fold_rows = []
        for fold in folds:
            score = fold["candidates"][candidate.id]["scorecard"]
            incumbent_mae = float(score["incumbent"]["mae"])
            candidate_mae = float(score["candidate"]["mae"])
            improvement = float(score["mae_improvement"])
            fold_rows.append({
                "season": fold["season"],
                "baseline_mae": incumbent_mae,
                "candidate_mae": candidate_mae,
                "mae_improvement": improvement,
                "relative_mae_improvement": improvement / incumbent_mae,
                "median_ae_delta": float(score["candidate"]["median_ae"] - score["incumbent"]["median_ae"]),
                "p90_ae_delta": float(score["candidate"]["p90_ae"] - score["incumbent"]["p90_ae"]),
                "bias_abs_delta": float(abs(float(score["candidate"]["bias"])) - abs(float(score["incumbent"]["bias"]))),
                "worst_event_degradation": float(score["worst_event_degradation"]),
                "event_improvement_rate": float(score["event_improvement_rate"]),
            })
        mean_base = float(np.mean([row["baseline_mae"] for row in fold_rows]))
        mean_candidate = float(np.mean([row["candidate_mae"] for row in fold_rows]))
        gain = mean_base - mean_candidate
        result.append({
            "candidate_id": candidate.id,
            "context_columns": list(candidate.columns),
            "folds": fold_rows,
            "all_development_folds_improve": bool(all(row["mae_improvement"] > 0 for row in fold_rows)),
            "mean_baseline_mae": mean_base,
            "mean_candidate_mae": mean_candidate,
            "mean_mae_improvement": gain,
            "mean_relative_mae_improvement": gain / mean_base,
            "mean_median_ae_delta": float(np.mean([row["median_ae_delta"] for row in fold_rows])),
            "mean_p90_ae_delta": float(np.mean([row["p90_ae_delta"] for row in fold_rows])),
            "mean_bias_abs_delta": float(np.mean([row["bias_abs_delta"] for row in fold_rows])),
            "max_worst_event_degradation": float(np.max([row["worst_event_degradation"] for row in fold_rows])),
            "mean_event_improvement_rate": float(np.mean([row["event_improvement_rate"] for row in fold_rows])),
        })
    return result


def select_candidate(development: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    no_context = next(row for row in development if row["candidate_id"] == "NO_CONTEXT")
    eligible = [
        row for row in development
        if row["candidate_id"] != "NO_CONTEXT"
        and row["all_development_folds_improve"]
        and row["mean_relative_mae_improvement"] + SELECTION_ATOL >= MIN_MEAN_RELATIVE_MAE_IMPROVEMENT
    ]
    if not eligible:
        return "NO_CONTEXT", {
            "reason": "NO_CONTEXT_GROUP_MEETS_TWO_FOLD_STABILITY_GATE",
            "eligible_candidate_ids": [],
            "selected_row": no_context,
        }

    best_gain = max(float(row["mean_mae_improvement"]) for row in eligible)
    near_best = [
        row for row in eligible
        if float(row["mean_mae_improvement"]) + SELECTION_ATOL >= NEAR_BEST_GAIN_RETENTION * best_gain
    ]
    selected = min(
        near_best,
        key=lambda row: (
            float(row["max_worst_event_degradation"]),
            float(row["mean_p90_ae_delta"]),
            float(row["mean_bias_abs_delta"]),
            len(row["context_columns"]),
            str(row["candidate_id"]),
        ),
    )
    return str(selected["candidate_id"]), {
        "reason": "TWO_FOLD_0P5PCT_GATE_THEN_90PCT_GAIN_RETENTION_AND_TAIL_MINIMIZATION",
        "best_mean_mae_improvement": best_gain,
        "near_best_required_improvement": NEAR_BEST_GAIN_RETENTION * best_gain,
        "eligible_candidate_ids": [str(row["candidate_id"]) for row in eligible],
        "near_best_candidate_ids": [str(row["candidate_id"]) for row in near_best],
        "selected_row": selected,
    }


def horizon_experiment(store: pd.DataFrame, horizon: str) -> dict[str, Any]:
    development_folds = [
        score_fold(store, horizon, season, training, CANDIDATES)
        for season, training in DEVELOPMENT_FOLDS
    ]
    aggregate = aggregate_development(development_folds, CANDIDATES)
    selected_id, selection = select_candidate(aggregate)
    selected = next(candidate for candidate in CANDIDATES if candidate.id == selected_id)
    reference_candidates = (CANDIDATES[0],) if selected_id == "NO_CONTEXT" else (CANDIDATES[0], selected)
    reference_folds = [
        score_fold(store, horizon, season, training, reference_candidates)
        for season, training in REFERENCE_HOLDOUTS
    ]

    references = []
    for fold in reference_folds:
        score = fold["candidates"][selected_id]["scorecard"]
        references.append({
            "season": fold["season"],
            "baseline_mae": float(score["incumbent"]["mae"]),
            "candidate_mae": float(score["candidate"]["mae"]),
            "mae_improvement": float(score["mae_improvement"]),
            "median_ae_delta": float(score["candidate"]["median_ae"] - score["incumbent"]["median_ae"]),
            "p90_ae_delta": float(score["candidate"]["p90_ae"] - score["incumbent"]["p90_ae"]),
            "bias_abs_delta": float(abs(float(score["candidate"]["bias"])) - abs(float(score["incumbent"]["bias"]))),
            "worst_event_degradation": float(score["worst_event_degradation"]),
            "worst_event": score["worst_event"],
            "event_improvement_rate": float(score["event_improvement_rate"]),
            "club_breakdown_min_n_5": score["club_breakdown_min_n_5"],
        })

    mean_base = float(np.mean([row["baseline_mae"] for row in references]))
    mean_candidate = float(np.mean([row["candidate_mae"] for row in references]))
    gain = mean_base - mean_candidate
    both_positive = bool(all(row["mae_improvement"] > 0 for row in references))
    if selected_id == "NO_CONTEXT":
        signal = "NO_STABLE_CONTEXT_EXTENSION_ON_DEVELOPMENT"
    elif both_positive and gain > 0:
        signal = "CONTEXT_EXTENSION_POSITIVE_BOTH_REFERENCES"
    elif gain > 0:
        signal = "CONTEXT_EXTENSION_POSITIVE_MEAN_MIXED_REFERENCES"
    else:
        signal = "CONTEXT_EXTENSION_NOT_PROVEN_ON_REFERENCES"

    return {
        "horizon": horizon,
        "frozen_baseline_contract": {
            "a2_b2_stack": True,
            "b2_policy": "NO_ADJUSTMENT" if horizon not in FROZEN_B2 else f"{FROZEN_B2[horizon].id}-min3",
        },
        "development_folds": development_folds,
        "development_aggregate": aggregate,
        "selection": selection,
        "selected_candidate_id": selected_id,
        "selected_context_columns": list(selected.columns),
        "reference_folds": reference_folds,
        "reference_summary": references,
        "mean_reference_baseline_mae": mean_base,
        "mean_reference_candidate_mae": mean_candidate,
        "mean_reference_mae_improvement": gain,
        "both_reference_seasons_improve": both_positive,
        "signal": signal,
        "promotion_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--horizons", default=",".join(HORIZONS))
    args = parser.parse_args()

    requested = [item.strip() for item in args.horizons.split(",") if item.strip()]
    invalid = sorted(set(requested) - set(HORIZONS))
    if invalid:
        raise ValueError(f"unsupported horizons: {invalid}")

    manifest = json.loads(args.manifest.read_text())
    actual_hash = sha256_file(args.historical_runtime)
    expected_hash = manifest["historical_runtime"]["sha256"]
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"historical runtime hash mismatch actual={actual_hash} expected={expected_hash}"
        )

    matches = _canonical_matches(_historical_rows(args.historical_runtime))
    store = load_feature_store(args.historical_runtime)
    context = build_context_store(matches, store)
    augmented = augment_feature_store(store, context)

    results = [horizon_experiment(augmented, horizon) for horizon in requested]
    payload = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "status": "COMPLETED_HISTORICAL_CONTEXT_CHALLENGER_EVIDENCE",
        "evidence_class": "EXPOSED_HISTORICAL_REFERENCE_SEASONS",
        "promotion_allowed": False,
        "production_change": False,
        "context_contract": {
            "candidate_groups": [asdict(candidate) for candidate in CANDIDATES],
            "sequence_columns": list(SEQUENCE_COLUMNS),
            "stakes_columns": list(STAKES_COLUMNS),
            "table_state": "completed matches only at as_of",
            "future_results_allowed": False,
            "final_table_state_allowed": False,
            "known_schedule_participants_only": True,
            "stakes_are_continuous_table_pressure_proxies_not_official_qualification_labels": True,
        },
        "selection_contract": {
            "development_folds": [
                {"season": season, "training_seasons": training}
                for season, training in DEVELOPMENT_FOLDS
            ],
            "reference_holdouts": [
                {"season": season, "training_seasons": training}
                for season, training in REFERENCE_HOLDOUTS
            ],
            "minimum_mean_relative_mae_improvement": MIN_MEAN_RELATIVE_MAE_IMPROVEMENT,
            "near_best_gain_retention": NEAR_BEST_GAIN_RETENTION,
            "references_used_for_selection": False,
            "baseline_is_frozen_a2_b2_stack": True,
        },
        "context_quality": {
            "rows": int(len(context)),
            "unique_match_horizon": int(context[["match_key", "horizon"]].drop_duplicates().shape[0]),
            "missingness_sequence": context_missingness(augmented, SEQUENCE_COLUMNS),
            "missingness_stakes": context_missingness(augmented, STAKES_COLUMNS),
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
        "horizons": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "promotion_allowed": False,
        "horizons": [
            {
                "horizon": row["horizon"],
                "selected_candidate_id": row["selected_candidate_id"],
                "signal": row["signal"],
                "mean_reference_baseline_mae": row["mean_reference_baseline_mae"],
                "mean_reference_candidate_mae": row["mean_reference_candidate_mae"],
                "mean_reference_mae_improvement": row["mean_reference_mae_improvement"],
            }
            for row in results
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
