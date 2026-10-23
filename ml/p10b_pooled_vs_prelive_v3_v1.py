#!/usr/bin/env python3
"""P10b — pooled-horizon challenger vs frozen Pre-Live v3.

Question: does the already-frozen P10 pooled cross-horizon HGB architecture
beat Beyond's strongest reproducible structural/pre-live research anchor under
one common, strictly temporal, complete-match-blocked protocol?

No tuning or selection occurs in P10b. Historical evidence is exposed research
evidence only and cannot change production.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from ml.mae_delta_uncertainty_v1 import BootstrapConfig, bootstrap_delta_mae, paired_event_errors
from ml.p10_pooled_horizon_global_v1 import HORIZON_DAYS, fit_residual, numeric_features, predict
from ml.pre_live_baseline_optimization_v1 import load_feature_store, sha256_file
from ml.pre_live_v3_fixed_temporal_package_v1 import (
    CHANGED_HORIZONS,
    FOLDS as PRELIVE_V3_FOLDS,
    candidate_prediction as prelive_v3_changed_prediction,
)
from ml.pre_live_v3_regime_revalidation_v1 import frozen_v2_for_season, v3_historical_base_for_season
from ml.research_advance_governance_v2 import ResearchAdvanceInput, decide_research_advance
from ml.temporal_validation_v1 import (
    build_expanding_group_folds,
    event_balanced_mae,
    fold_manifest,
)

VERSION = "p10b-pooled-vs-prelive-v3-v1"
WORKSTREAM = "P10b — pooled horizon cross-learning vs frozen Pre-Live v3"
CHALLENGER_ID = "p10-v1-pooled-hgb-residual-baseline-season"
INCUMBENT_ID = "pre-live-v3-historical-candidate-2026-10-21-v1"
EXPECTED_HISTORY_SHA256 = "3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569"
EXPECTED_MATCHES = 1530
EXPECTED_PIT_ROWS = 7650
BOOTSTRAP_SAMPLES = 5000
RANDOM_SEED = 42
BASELINE_COLUMN = "baseline_season"
HORIZONS = ("T-30", "T-14", "T-7", "T-3", "T-1")

ChampionProvider = Callable[[pd.DataFrame, str, str, list[str]], tuple[pd.DataFrame, np.ndarray]]


def exact_prelive_v3_prediction(
    store: pd.DataFrame,
    horizon: str,
    season: str,
    training_seasons: list[str],
) -> tuple[pd.DataFrame, np.ndarray]:
    """Use the frozen v3 implementation itself; never reimplement its logic."""
    if horizon in CHANGED_HORIZONS:
        rows, prediction, _ = prelive_v3_changed_prediction(
            store, horizon, season, training_seasons
        )
        return rows, np.asarray(prediction, dtype=float)

    base = v3_historical_base_for_season(store, horizon, season, training_seasons)
    prediction, _ = frozen_v2_for_season(
        store, horizon, season, training_seasons, base.rows
    )
    return base.rows, np.asarray(prediction, dtype=float)


def _eligible(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    eligible = out["training_eligible"]
    if eligible.dtype != bool:
        eligible = eligible.astype(str).str.lower().map(
            {"true": True, "false": False, "1": True, "0": False}
        ).fillna(False)
    return out[eligible].copy()


def prepare_frame(store: pd.DataFrame) -> pd.DataFrame:
    required = {
        "match_key", "season", "horizon", "kickoff_at", "home_club_key",
        "away_club_key", "target_attendance", "training_eligible", BASELINE_COLUMN,
    }
    missing = sorted(required - set(store.columns))
    if missing:
        raise RuntimeError(f"P10b feature store missing columns: {missing}")

    frame = _eligible(store)
    frame["kickoff_at"] = pd.to_datetime(frame["kickoff_at"], utc=True, errors="raise")
    frame["target_attendance"] = pd.to_numeric(frame["target_attendance"], errors="raise")
    frame["baseline_fixed"] = pd.to_numeric(frame[BASELINE_COLUMN], errors="raise")
    if frame["baseline_fixed"].isna().any():
        raise RuntimeError("P10b eligible rows contain null baseline_season")

    unknown = sorted(set(frame["horizon"].astype(str)) - set(HORIZON_DAYS))
    if unknown:
        raise RuntimeError(f"P10b unknown horizons: {unknown}")
    frame["horizon_days"] = frame["horizon"].astype(str).map(HORIZON_DAYS).astype(float)

    if frame.duplicated(["match_key", "horizon"], keep=False).any():
        raise RuntimeError("P10b requires one eligible row per match/horizon")
    return frame.reset_index(drop=True)


def canonical_folds(frame: pd.DataFrame):
    folds = build_expanding_group_folds(
        frame,
        entity_col="match_key",
        time_col="kickoff_at",
        group_col="season",
        min_train_groups=1,
    )
    observed = [
        (fold.test_groups[0], list(fold.train_groups))
        for fold in folds
    ]
    expected = [(season, list(training)) for season, training in PRELIVE_V3_FOLDS]
    if observed != expected:
        raise RuntimeError(
            f"P10b fold protocol drift observed={observed} expected={expected}"
        )
    return folds


def champion_for_fold(
    store: pd.DataFrame,
    test_season: str,
    training_seasons: list[str],
    provider: ChampionProvider,
) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    for horizon in HORIZONS:
        rows, prediction = provider(store, horizon, test_season, training_seasons)
        if len(rows) != len(prediction):
            raise RuntimeError(f"P10b champion length mismatch {horizon}/{test_season}")
        part = rows[["match_key", "horizon", "target_attendance"]].copy()
        part["champion_prediction"] = np.asarray(prediction, dtype=float)
        pieces.append(part)

    champion = pd.concat(pieces, ignore_index=True)
    if champion.duplicated(["match_key", "horizon"], keep=False).any():
        raise RuntimeError(f"P10b champion duplicate match/horizon {test_season}")
    return champion


def evaluate(
    store: pd.DataFrame,
    *,
    champion_provider: ChampionProvider = exact_prelive_v3_prediction,
    minimum_meaningful_mae_improvement: float | None = None,
) -> tuple[dict[str, Any], pd.DataFrame, dict[str, Any]]:
    frame = prepare_frame(store)
    folds = canonical_folds(frame)
    manifest = fold_manifest(folds, protocol_id="p10b-prelive-v3-common-fixed-temporal-v1")
    numeric = numeric_features(frame)

    outputs: list[pd.DataFrame] = []
    fold_scores: list[dict[str, Any]] = []

    for fold in folds:
        test_season = fold.test_groups[0]
        training_seasons = list(fold.train_groups)
        train_ids = set(fold.train_entities)
        test_ids = set(fold.test_entities)
        train = frame[frame["match_key"].astype(str).isin(train_ids)].copy()
        test = frame[frame["match_key"].astype(str).isin(test_ids)].copy()
        if train_ids & test_ids:
            raise RuntimeError(f"P10b match leakage in {fold.fold_id}")

        pooled_model = fit_residual(train, numeric)
        test["pooled_prediction"] = predict(pooled_model, test, numeric)

        champion = champion_for_fold(
            store, test_season, training_seasons, champion_provider
        )
        joined = test.merge(
            champion,
            on=["match_key", "horizon"],
            how="inner",
            validate="one_to_one",
            suffixes=("", "_champion"),
        )
        if len(joined) != len(test) or len(joined) != len(champion):
            raise RuntimeError(
                f"P10b comparator row-set mismatch {test_season}: "
                f"test={len(test)} champion={len(champion)} joined={len(joined)}"
            )
        if not np.allclose(
            joined["target_attendance"].astype(float),
            joined["target_attendance_champion"].astype(float),
            rtol=0.0,
            atol=1e-9,
        ):
            raise RuntimeError(f"P10b target mismatch {test_season}")

        out = joined[[
            "match_key", "season", "horizon", "kickoff_at", "home_club_key",
            "target_attendance", "champion_prediction", "pooled_prediction",
        ]].copy()
        out["fold_id"] = fold.fold_id
        outputs.append(out)

        incumbent_mae = event_balanced_mae(
            out, event_col="match_key", actual_col="target_attendance",
            prediction_col="champion_prediction"
        )
        challenger_mae = event_balanced_mae(
            out, event_col="match_key", actual_col="target_attendance",
            prediction_col="pooled_prediction"
        )
        fold_scores.append({
            "fold_id": fold.fold_id,
            "test_season": test_season,
            "training_seasons": training_seasons,
            "test_matches": int(out["match_key"].nunique()),
            "prelive_v3_match_balanced_mae": incumbent_mae,
            "pooled_match_balanced_mae": challenger_mae,
            "delta_mae": challenger_mae - incumbent_mae,
            "pooled_improved": challenger_mae < incumbent_mae,
        })

    predictions = pd.concat(outputs, ignore_index=True).sort_values(
        ["kickoff_at", "match_key", "horizon"]
    ).reset_index(drop=True)

    incumbent_mae = event_balanced_mae(
        predictions, event_col="match_key", actual_col="target_attendance",
        prediction_col="champion_prediction"
    )
    challenger_mae = event_balanced_mae(
        predictions, event_col="match_key", actual_col="target_attendance",
        prediction_col="pooled_prediction"
    )

    paired = paired_event_errors(
        predictions,
        event_col="match_key",
        actual_col="target_attendance",
        incumbent_col="champion_prediction",
        challenger_col="pooled_prediction",
        strata_cols=("fold_id",),
    )
    uncertainty = bootstrap_delta_mae(
        paired,
        strata_cols=("fold_id",),
        config=BootstrapConfig(n_resamples=BOOTSTRAP_SAMPLES, seed=RANDOM_SEED),
    )
    event_improvement_rate = float(uncertainty["event_improvement_rate"])
    fold_improvement_rate = float(np.mean([row["pooled_improved"] for row in fold_scores]))
    bootstrap = uncertainty["bootstrap"]

    governance = decide_research_advance(ResearchAdvanceInput(
        incumbent_mae=incumbent_mae,
        challenger_mae=challenger_mae,
        event_improvement_rate=event_improvement_rate,
        fold_improvement_rate=fold_improvement_rate,
        delta_mae_ci_lower=float(bootstrap["delta_mae_lower"]),
        delta_mae_ci_upper=float(bootstrap["delta_mae_upper"]),
        minimum_meaningful_mae_improvement=minimum_meaningful_mae_improvement,
    ))

    per_horizon: dict[str, Any] = {}
    for horizon, group in predictions.groupby("horizon", sort=True):
        actual = group["target_attendance"].astype(float).to_numpy()
        incumbent = group["champion_prediction"].astype(float).to_numpy()
        challenger = group["pooled_prediction"].astype(float).to_numpy()
        incumbent_h_mae = float(np.mean(np.abs(actual - incumbent)))
        challenger_h_mae = float(np.mean(np.abs(actual - challenger)))
        per_horizon[str(horizon)] = {
            "rows": int(len(group)),
            "matches": int(group["match_key"].nunique()),
            "prelive_v3_mae": incumbent_h_mae,
            "pooled_mae": challenger_h_mae,
            "delta_mae": challenger_h_mae - incumbent_h_mae,
        }

    result = {
        "version": VERSION,
        "workstream": WORKSTREAM,
        "status": "HISTORICAL_EXPOSED_RESEARCH_ONLY",
        "evidence_class": "historical_exposed_research",
        "production_change": False,
        "live_adjustment": 0,
        "incumbent_id": INCUMBENT_ID,
        "challenger_id": CHALLENGER_ID,
        "challenger_architecture_source": "frozen P10 v1; no P10b retuning",
        "independent_unit": "match_key",
        "match_blocking": True,
        "fold_protocol": "exact Pre-Live v3 four-fold fixed-temporal seasons",
        "fold_manifest_sha256": manifest["folds_sha256"],
        "eligible_rows": int(len(frame)),
        "matches": int(frame["match_key"].nunique()),
        "prelive_v3_match_balanced_mae": incumbent_mae,
        "pooled_match_balanced_mae": challenger_mae,
        "delta_mae": challenger_mae - incumbent_mae,
        "relative_mae_improvement": (incumbent_mae - challenger_mae) / incumbent_mae,
        "event_improvement_rate": event_improvement_rate,
        "fold_improvement_rate": fold_improvement_rate,
        "fold_scores": fold_scores,
        "per_horizon": per_horizon,
        "uncertainty": uncertainty,
        "governance_v2": governance.to_dict(),
    }
    return result, predictions, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-runtime", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--fold-manifest", type=Path, required=True)
    parser.add_argument("--minimum-meaningful-mae-improvement", type=float)
    args = parser.parse_args()

    history_sha = sha256_file(args.historical_runtime)
    if history_sha != EXPECTED_HISTORY_SHA256:
        raise RuntimeError(
            f"P10b history SHA drift actual={history_sha} expected={EXPECTED_HISTORY_SHA256}"
        )
    source_manifest = json.loads(args.input_manifest.read_text())
    if source_manifest["historical_runtime"]["sha256"] != history_sha:
        raise RuntimeError("P10b source manifest/history mismatch")

    store = load_feature_store(args.historical_runtime)
    if len(store) != EXPECTED_PIT_ROWS or store["match_key"].nunique() != EXPECTED_MATCHES:
        raise RuntimeError(
            f"P10b canonical store drift rows={len(store)} "
            f"matches={store['match_key'].nunique()}"
        )

    result, predictions, manifest = evaluate(
        store,
        minimum_meaningful_mae_improvement=args.minimum_meaningful_mae_improvement,
    )
    result["input"] = {
        "historical_runtime_sha256": history_sha,
        "source_manifest_sha256": sha256_file(args.input_manifest),
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(args.predictions_csv, index=False)
    args.fold_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.fold_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "version": VERSION,
        "incumbent": result["prelive_v3_match_balanced_mae"],
        "challenger": result["pooled_match_balanced_mae"],
        "delta_mae": result["delta_mae"],
        "governance": result["governance_v2"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
