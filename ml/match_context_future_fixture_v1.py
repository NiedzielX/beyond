#!/usr/bin/env python3
"""Evaluate future-home-fixture context as a Structural Prior challenger.

Workstream: c) Context meczu — rozbudować.

The incumbent is always fitted/predicted on the untouched canonical feature
store first. Challenger-only future-fixture columns are then added to a copy.

Important limitation: the committed historical dataset contains recorded final
fixture timestamps, not a versioned historical schedule. Therefore these
features are SCHEDULE_AS_RECORDED_RETROSPECTIVE_PROXY evidence only and can
never trigger automatic production promotion.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.current_season_adjustment_v1 import (
    BENCHMARK_ATOL,
    DEV_SEASON,
    DEV_TRAIN,
    HOLDOUTS,
    HORIZONS,
    eligible,
    load_feature_store,
    metrics,
    verify_frozen_incumbent,
)
from ml.demand_engine.structural_prior_runtime import fit_structural_prior_runtime

EXPERIMENT = "match-context-future-fixture-v1"
WORKSTREAM = "c) Context meczu — rozbudować"
SCHEDULE_EVIDENCE = "SCHEDULE_AS_RECORDED_RETROSPECTIVE_PROXY"

TIMING_FEATURES = [
    "next_home_fixture_days",
    "next_home_fixture_within7",
    "next_home_fixture_within14",
    "home_fixtures_next7",
    "home_fixtures_next14",
    "home_fixtures_next30",
]
ATTRACTIVENESS_FEATURES = [
    "next_home_context_available",
    "next_home_context_snapshot_age_days",
    "next_home_opponent_draw_ratio_mean",
    "next_home_opponent_draw_ratio_recent3",
    "next_home_away_ppg",
    "next_home_away_position",
    "next_vs_current_opponent_draw_gap",
    "future_fixture_cannibalization_proxy",
]


@dataclass(frozen=True)
class ContextVariant:
    id: str
    columns: tuple[str, ...]


VARIANTS = [
    ContextVariant("future_timing", tuple(TIMING_FEATURES)),
    ContextVariant(
        "future_timing_attractiveness",
        tuple(TIMING_FEATURES + ATTRACTIVENESS_FEATURES),
    ),
]


def _as_float(value: Any) -> float:
    if value is None or pd.isna(value):
        return float("nan")
    return float(value)


def add_future_fixture_context(frame: pd.DataFrame) -> pd.DataFrame:
    """Derive schedule-as-recorded future-home-fixture research features.

    For next-fixture attractiveness, only a snapshot of that future fixture with
    as_of_at <= the current row's as_of_at may be used. If none exists, the
    attractiveness fields remain missing.
    """
    out = frame.copy().reset_index(drop=True)
    out["as_of_at"] = pd.to_datetime(out["as_of_at"], utc=True)
    out["kickoff_at"] = pd.to_datetime(out["kickoff_at"], utc=True)

    fixture_cols = [
        "match_key", "season", "home_club_key", "away_club_key", "kickoff_at"
    ]
    fixtures = (
        out[fixture_cols]
        .drop_duplicates("match_key")
        .sort_values(["season", "home_club_key", "kickoff_at", "match_key"])
        .reset_index(drop=True)
    )

    schedule_by_home: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for key, group in fixtures.groupby(["season", "home_club_key"], sort=False):
        schedule_by_home[(str(key[0]), str(key[1]))] = group.to_dict("records")

    future_by_match: dict[str, list[dict[str, Any]]] = {}
    for schedule in schedule_by_home.values():
        for i, fixture in enumerate(schedule):
            future_by_match[str(fixture["match_key"])] = schedule[i + 1 :]

    context_columns = [
        "as_of_at",
        "opponent_draw_ratio_mean",
        "opponent_draw_ratio_recent3",
        "away_ppg",
        "away_position",
    ]
    snapshots_by_match: dict[str, pd.DataFrame] = {}
    for match_key, group in out.groupby("match_key", sort=False):
        snapshots_by_match[str(match_key)] = (
            group[context_columns].sort_values("as_of_at").reset_index(drop=True)
        )

    records: list[dict[str, float]] = []
    for _, row in out.iterrows():
        current_key = str(row["match_key"])
        current_kickoff = pd.Timestamp(row["kickoff_at"])
        current_as_of = pd.Timestamp(row["as_of_at"])
        future = future_by_match.get(current_key, [])

        deltas = [
            (pd.Timestamp(item["kickoff_at"]) - current_kickoff).total_seconds() / 86400.0
            for item in future
        ]
        positive = [float(value) for value in deltas if value > 0.0]
        next_fixture = future[0] if future else None
        next_days = positive[0] if positive else float("nan")

        feature: dict[str, float] = {
            "next_home_fixture_days": next_days,
            "next_home_fixture_within7": float(bool(positive and next_days <= 7.0)),
            "next_home_fixture_within14": float(bool(positive and next_days <= 14.0)),
            "home_fixtures_next7": float(sum(value <= 7.0 for value in positive)),
            "home_fixtures_next14": float(sum(value <= 14.0 for value in positive)),
            "home_fixtures_next30": float(sum(value <= 30.0 for value in positive)),
            "next_home_context_available": 0.0,
            "next_home_context_snapshot_age_days": float("nan"),
            "next_home_opponent_draw_ratio_mean": float("nan"),
            "next_home_opponent_draw_ratio_recent3": float("nan"),
            "next_home_away_ppg": float("nan"),
            "next_home_away_position": float("nan"),
            "next_vs_current_opponent_draw_gap": float("nan"),
            "future_fixture_cannibalization_proxy": float("nan"),
        }

        if next_fixture is not None:
            next_key = str(next_fixture["match_key"])
            candidate = snapshots_by_match[next_key]
            candidate = candidate[candidate["as_of_at"] <= current_as_of]
            if not candidate.empty:
                latest = candidate.iloc[-1]
                feature["next_home_context_available"] = 1.0
                feature["next_home_context_snapshot_age_days"] = float(
                    (current_as_of - pd.Timestamp(latest["as_of_at"])).total_seconds() / 86400.0
                )
                feature["next_home_opponent_draw_ratio_mean"] = _as_float(
                    latest["opponent_draw_ratio_mean"]
                )
                feature["next_home_opponent_draw_ratio_recent3"] = _as_float(
                    latest["opponent_draw_ratio_recent3"]
                )
                feature["next_home_away_ppg"] = _as_float(latest["away_ppg"])
                feature["next_home_away_position"] = _as_float(latest["away_position"])

                current_draw = _as_float(row["opponent_draw_ratio_mean"])
                next_draw = feature["next_home_opponent_draw_ratio_mean"]
                if np.isfinite(current_draw) and np.isfinite(next_draw):
                    gap = next_draw - current_draw
                    feature["next_vs_current_opponent_draw_gap"] = float(gap)
                    # Research-only monotonic proxy: only a more attractive next
                    # opponent creates positive cannibalization pressure, decayed
                    # by temporal distance. The model still receives the raw inputs.
                    if np.isfinite(next_days) and next_days <= 30.0:
                        feature["future_fixture_cannibalization_proxy"] = float(
                            max(gap, 0.0) / (1.0 + next_days / 14.0)
                        )

        records.append(feature)

    feature_frame = pd.DataFrame(records)
    for column in TIMING_FEATURES + ATTRACTIVENESS_FEATURES:
        out[column] = pd.to_numeric(feature_frame[column], errors="coerce")
    return out


def frame_with_variant(
    base: pd.DataFrame,
    enriched: pd.DataFrame,
    variant: ContextVariant,
) -> pd.DataFrame:
    if len(base) != len(enriched):
        raise RuntimeError("Base/enriched context frame length mismatch")
    identity = ["match_key", "horizon", "as_of_at"]
    for column in identity:
        left = base[column].astype(str).reset_index(drop=True)
        right = enriched[column].astype(str).reset_index(drop=True)
        if not left.equals(right):
            raise RuntimeError(f"Base/enriched row identity mismatch: {column}")
    challenger = base.copy().reset_index(drop=True)
    for column in variant.columns:
        challenger[column] = enriched[column].to_numpy()
    return challenger


def _eligible_for_model(
    frame: pd.DataFrame,
    model: Any,
    horizon: str,
    season: str,
) -> pd.DataFrame:
    rows = eligible(frame, horizon, season)
    return rows[rows[model.spec.baseline_column].notna()].copy().reset_index(drop=True)


def context_diagnostics(rows: pd.DataFrame, variant: ContextVariant) -> dict[str, Any]:
    return {
        "variant": variant.id,
        "rows": int(len(rows)),
        "next_fixture_known_share": float(rows["next_home_fixture_days"].notna().mean()),
        "next_fixture_within14_share": float(rows["next_home_fixture_within14"].fillna(0).mean()),
        "next_context_available_share": float(rows["next_home_context_available"].fillna(0).mean())
        if "next_home_context_available" in variant.columns
        else None,
        "feature_missing_rate": {
            column: float(rows[column].isna().mean()) for column in variant.columns
        },
    }


def score_variant_on_season(
    base: pd.DataFrame,
    enriched: pd.DataFrame,
    horizon: str,
    training_seasons: list[str],
    test_season: str,
    variant: ContextVariant,
) -> dict[str, Any]:
    challenger_frame = frame_with_variant(base, enriched, variant)
    model = fit_structural_prior_runtime(challenger_frame, horizon, training_seasons)
    test = _eligible_for_model(challenger_frame, model, horizon, test_season)
    prediction = model.predict(test)
    return {
        "variant": variant.id,
        "columns": list(variant.columns),
        "metrics": metrics(test["target_attendance"], prediction),
        "diagnostics": context_diagnostics(test, variant),
    }


def evaluate_horizon(base: pd.DataFrame, enriched: pd.DataFrame, horizon: str) -> dict[str, Any]:
    incumbent_dev_model = fit_structural_prior_runtime(base, horizon, DEV_TRAIN)
    dev_base = _eligible_for_model(base, incumbent_dev_model, horizon, DEV_SEASON)
    dev_incumbent_prediction = incumbent_dev_model.predict(dev_base)
    dev_incumbent_metrics = metrics(dev_base["target_attendance"], dev_incumbent_prediction)

    candidates = [
        score_variant_on_season(base, enriched, horizon, DEV_TRAIN, DEV_SEASON, variant)
        for variant in VARIANTS
    ]
    best_nonzero = min(candidates, key=lambda row: (row["metrics"]["mae"], row["variant"]))

    if float(best_nonzero["metrics"]["mae"]) + BENCHMARK_ATOL < float(dev_incumbent_metrics["mae"]):
        selected_id = str(best_nonzero["variant"])
        selected_variant = next(variant for variant in VARIANTS if variant.id == selected_id)
        selected_dev = best_nonzero
    else:
        selected_id = "NO_CONTEXT_EXTENSION"
        selected_variant = None
        selected_dev = {
            "variant": selected_id,
            "columns": [],
            "metrics": dev_incumbent_metrics,
            "diagnostics": None,
        }

    holdouts: dict[str, Any] = {}
    for test_season, train_seasons in HOLDOUTS:
        incumbent_model = fit_structural_prior_runtime(base, horizon, train_seasons)
        test_base = _eligible_for_model(base, incumbent_model, horizon, test_season)
        incumbent_prediction = incumbent_model.predict(test_base)
        incumbent_metrics = metrics(test_base["target_attendance"], incumbent_prediction)
        verify_frozen_incumbent(horizon, test_season, float(incumbent_metrics["mae"]))

        if selected_variant is None:
            challenger_metrics = incumbent_metrics
            diagnostics = None
        else:
            scored = score_variant_on_season(
                base, enriched, horizon, train_seasons, test_season, selected_variant
            )
            challenger_metrics = scored["metrics"]
            diagnostics = scored["diagnostics"]

        holdouts[test_season] = {
            "training_seasons": train_seasons,
            "incumbent": incumbent_metrics,
            "challenger": challenger_metrics,
            "mae_delta_vs_incumbent": float(incumbent_metrics["mae"] - challenger_metrics["mae"]),
            "diagnostics": diagnostics,
        }

    deltas = [float(value["mae_delta_vs_incumbent"]) for value in holdouts.values()]
    mean_incumbent = float(np.mean([value["incumbent"]["mae"] for value in holdouts.values()]))
    mean_challenger = float(np.mean([value["challenger"]["mae"] for value in holdouts.values()]))

    if selected_variant is None:
        signal = "NO_CONTEXT_EXTENSION_SELECTED"
    elif all(delta > BENCHMARK_ATOL for delta in deltas):
        signal = "PROMISING_SCHEDULE_PROXY_CONSISTENT_HOLDOUT_IMPROVEMENT"
    elif mean_challenger + BENCHMARK_ATOL < mean_incumbent:
        signal = "MIXED_SCHEDULE_PROXY_POSITIVE_MEAN"
    else:
        signal = "NOT_PROVEN"

    return {
        "horizon": horizon,
        "incumbent_model_spec_id": incumbent_dev_model.spec.model_spec_id,
        "development": {
            "season": DEV_SEASON,
            "training_seasons": DEV_TRAIN,
            "incumbent": dev_incumbent_metrics,
            "selected_variant": selected_dev,
            "best_nonzero_variant": best_nonzero,
            "candidates": sorted(candidates, key=lambda row: (row["metrics"]["mae"], row["variant"])),
        },
        "holdouts": holdouts,
        "mean_holdout_incumbent_mae": mean_incumbent,
        "mean_holdout_challenger_mae": mean_challenger,
        "mean_holdout_mae_delta": mean_incumbent - mean_challenger,
        "signal": signal,
        "promotion_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    base = load_feature_store(args.historical_runtime).reset_index(drop=True)
    enriched = add_future_fixture_context(base)
    results = [evaluate_horizon(base, enriched, horizon) for horizon in HORIZONS]

    report = {
        "experiment": EXPERIMENT,
        "workstream": WORKSTREAM,
        "dataset": "committed-frozen-runtime-input / five Ekstraklasa seasons",
        "evidence_class": SCHEDULE_EVIDENCE,
        "audit": {
            "existing_context_already_present": [
                "opponent demand history",
                "pair demand history",
                "home/away PPG and GD/game",
                "home/away last-5 form",
                "table positions and gaps",
                "past rest and congestion",
            ],
            "new_gap_tested": "future home fixture timing and next-opponent attractiveness",
            "squad_context_available": False,
        },
        "protocol": {
            "development_train": DEV_TRAIN,
            "development_selection": DEV_SEASON,
            "holdouts": [season for season, _ in HOLDOUTS],
            "candidate_variants": [variant.id for variant in VARIANTS],
            "no_context_candidate": True,
            "incumbent_isolated_before_challenger_features": True,
            "frozen_incumbent_benchmark_asserted": True,
            "future_fixture_context_snapshot_must_be_asof_lte_current": True,
            "historical_schedule_versioned": False,
            "automatic_promotion": False,
            "production_changed": False,
        },
        "summary": {
            "consistent_holdout_improvement_horizons": [
                row["horizon"] for row in results
                if row["signal"] == "PROMISING_SCHEDULE_PROXY_CONSISTENT_HOLDOUT_IMPROVEMENT"
            ],
            "positive_mean_holdout_improvement_horizons": [
                row["horizon"] for row in results if row["mean_holdout_mae_delta"] > BENCHMARK_ATOL
            ],
            "no_context_selected_horizons": [
                row["horizon"] for row in results
                if row["signal"] == "NO_CONTEXT_EXTENSION_SELECTED"
            ],
            "promotion_allowed": False,
            "production_changed": False,
        },
        "horizons": results,
        "interpretation_guard": (
            "Future fixture timestamps come from the recorded final historical schedule. "
            "Without historical schedule versioning this is research evidence only, even if holdout MAE improves."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({
        "experiment": EXPERIMENT,
        "evidence_class": SCHEDULE_EVIDENCE,
        "summary": report["summary"],
        "horizons": [{
            "horizon": row["horizon"],
            "signal": row["signal"],
            "selected_variant": row["development"]["selected_variant"]["variant"],
            "mean_holdout_incumbent_mae": row["mean_holdout_incumbent_mae"],
            "mean_holdout_challenger_mae": row["mean_holdout_challenger_mae"],
            "mean_holdout_mae_delta": row["mean_holdout_mae_delta"],
        } for row in results],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
