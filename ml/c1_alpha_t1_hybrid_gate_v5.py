#!/usr/bin/env python3
"""C1-alpha T-1 Hybrid Gate v5.

Adds the PIT-safe T-24h `hybrid_v6` signal from Ticketing Challenger v1 to the
nested whole-event meta-gate. The base live expert stays frozen to the v2 winner.

Validation remains outer Leave-One-Event-Out. Base-live estimates used for meta
training are inner-LOEO out-of-fold predictions only. Missing hybrid signal is
explicitly represented and never reconstructed from outcomes.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay, _training_frame
from ml.c1_alpha_t1_stacked_v4 import (
    add_event_context,
    add_meta_features,
    event_weights,
    fit_base_live,
    fold_metrics,
    inner_oof_meta_frame,
)
from ml.c1_alpha_t1_tournament_v2 import WINDOW_HOURS


HYBRID_NUMERIC = [
    "prior_expected_occupancy",
    "base_live_occupancy",
    "signed_disagreement_occupancy",
    "abs_disagreement_occupancy",
    "hybrid_v6",
    "hybrid_missing",
    "hybrid_release_activity",
    "hybrid_sector_coverage_change",
    "available_share_of_capacity",
    "available_index",
    "velocity_6h",
    "velocity_24h",
    "acceleration_6h_vs_24h",
    "observation_window_hours",
    "raw_snapshot_count",
    "clean_snapshot_count",
    "matched_absorption",
    "matched_release",
    "signal_ready",
    "feature_quality_good",
    "season_home_evidence_n",
    "round_no",
]

HYBRID_MINIMAL = [
    "prior_expected_occupancy",
    "base_live_occupancy",
    "signed_disagreement_occupancy",
    "abs_disagreement_occupancy",
    "hybrid_v6",
    "hybrid_missing",
    "hybrid_release_activity",
    "hybrid_sector_coverage_change",
    "available_share_of_capacity",
    "available_index",
    "season_home_evidence_n",
    "round_no",
]

CATEGORICAL = ["hybrid_v6_source"]


@dataclass(frozen=True)
class Spec:
    name: str
    mode: str
    numeric: tuple[str, ...]
    model: Any


def add_hybrid_features(frame: pd.DataFrame, payload: dict) -> pd.DataFrame:
    out = frame.copy()
    hybrid_rows = {
        int(row["ticket_event_id"]): row
        for row in payload.get("ticketingChallengerRows") or []
    }
    values = []
    sources = []
    release = []
    coverage = []
    for event_id in out["ticket_event_id"].astype(int):
        row = hybrid_rows.get(int(event_id))
        if row is None:
            values.append(np.nan)
            sources.append("missing")
            release.append(np.nan)
            coverage.append(np.nan)
            continue
        values.append(pd.to_numeric(row.get("hybrid_v6"), errors="coerce"))
        sources.append(str(row.get("hybrid_v6_source") or "missing"))
        release.append(
            np.nan if row.get("release_activity_flag") is None
            else float(bool(row.get("release_activity_flag")))
        )
        coverage.append(
            np.nan if row.get("sector_coverage_change_flag") is None
            else float(bool(row.get("sector_coverage_change_flag")))
        )
    out["hybrid_v6"] = values
    out["hybrid_v6_source"] = sources
    out["hybrid_missing"] = out["hybrid_v6"].isna().astype(float)
    out["hybrid_release_activity"] = release
    out["hybrid_sector_coverage_change"] = coverage
    return out


def preprocessor(numeric: list[str], scale: bool = True) -> ColumnTransformer:
    num_steps: list[tuple[str, Any]] = [
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
    ]
    if scale:
        num_steps.append(("scale", StandardScaler()))
    return ColumnTransformer([
        ("num", Pipeline(num_steps), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
    ], remainder="drop")


def make_pipeline(numeric: list[str], model: Any, scale: bool = True) -> Pipeline:
    return Pipeline([
        ("prep", preprocessor(numeric, scale=scale)),
        ("model", model),
    ])


def specs(frame: pd.DataFrame) -> list[Spec]:
    full = tuple(col for col in HYBRID_NUMERIC if col in frame.columns)
    minimal = tuple(col for col in HYBRID_MINIMAL if col in frame.columns)
    result: list[Spec] = []
    for feature_name, features in (("minimal", minimal), ("full", full)):
        for alpha in (1.0, 10.0, 100.0):
            result.append(Spec(
                f"stack_ridge_hybrid_{feature_name}_a{alpha:g}",
                "direct_occupancy",
                features,
                make_pipeline(list(features), Ridge(alpha=alpha), scale=True),
            ))
            result.append(Spec(
                f"blendweight_ridge_hybrid_{feature_name}_a{alpha:g}",
                "blend_weight",
                features,
                make_pipeline(list(features), Ridge(alpha=alpha), scale=True),
            ))
        for epsilon, alpha in ((1.35, 0.001), (1.5, 0.001)):
            result.append(Spec(
                f"stack_huber_hybrid_{feature_name}_e{epsilon:g}_a{alpha:g}",
                "direct_occupancy",
                features,
                make_pipeline(
                    list(features),
                    HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=2000),
                    scale=True,
                ),
            ))
            result.append(Spec(
                f"blendweight_huber_hybrid_{feature_name}_e{epsilon:g}_a{alpha:g}",
                "blend_weight",
                features,
                make_pipeline(
                    list(features),
                    HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=2000),
                    scale=True,
                ),
            ))
        for c in (0.01, 0.1, 1.0):
            result.append(Spec(
                f"softgate_logit_hybrid_{feature_name}_c{c:g}",
                "soft_gate",
                features,
                make_pipeline(
                    list(features), LogisticRegression(C=c, max_iter=2000, random_state=42), scale=True
                ),
            ))
            result.append(Spec(
                f"hardgate_logit_hybrid_{feature_name}_c{c:g}",
                "hard_gate",
                features,
                make_pipeline(
                    list(features), LogisticRegression(C=c, max_iter=2000, random_state=42), scale=True
                ),
            ))
    for depth in (1, 2):
        result.append(Spec(
            f"softgate_tree_hybrid_d{depth}",
            "soft_gate",
            minimal,
            make_pipeline(
                list(minimal),
                DecisionTreeClassifier(max_depth=depth, min_samples_leaf=4, random_state=42),
                scale=False,
            ),
        ))
        result.append(Spec(
            f"blendweight_tree_hybrid_d{depth}",
            "blend_weight",
            minimal,
            make_pipeline(
                list(minimal),
                DecisionTreeRegressor(max_depth=depth, min_samples_leaf=4, random_state=42),
                scale=False,
            ),
        ))
    return result


def optimal_blend_weight(frame: pd.DataFrame) -> np.ndarray:
    prior = frame["prior_p50"].astype(float).to_numpy()
    live = frame["base_live_prediction"].astype(float).to_numpy()
    actual = frame["actual_attendance"].astype(float).to_numpy()
    denominator = live - prior
    raw = np.divide(
        actual - prior,
        denominator,
        out=np.zeros_like(prior, dtype=float),
        where=np.abs(denominator) > 1e-9,
    )
    return np.clip(raw, 0.0, 1.0)


def fit_predict(spec: Spec, train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    xcols = list(spec.numeric) + CATEGORICAL
    weights = event_weights(train)
    model = clone(spec.model)
    prior = test["prior_p50"].astype(float).to_numpy()
    base_live = test["base_live_prediction"].astype(float).to_numpy()
    capacity = test["stadium_capacity"].astype(float).to_numpy()

    if spec.mode == "direct_occupancy":
        target = (
            train["actual_attendance"].astype(float)
            / train["stadium_capacity"].astype(float)
        ).to_numpy()
        try:
            model.fit(train[xcols], target, model__sample_weight=weights)
        except (TypeError, ValueError):
            model.fit(train[xcols], target)
        occupancy = np.asarray(model.predict(test[xcols]), dtype=float)
        return np.clip(occupancy, 0.0, 1.0) * capacity

    if spec.mode == "blend_weight":
        target = optimal_blend_weight(train)
        try:
            model.fit(train[xcols], target, model__sample_weight=weights)
        except (TypeError, ValueError):
            model.fit(train[xcols], target)
        blend = np.clip(np.asarray(model.predict(test[xcols]), dtype=float), 0.0, 1.0)
        return np.clip(prior + blend * (base_live - prior), 0.0, capacity)

    target = train["oracle_live_better"].astype(int).to_numpy()
    if np.unique(target).size < 2:
        return prior.copy()
    try:
        model.fit(train[xcols], target, model__sample_weight=weights)
    except (TypeError, ValueError):
        model.fit(train[xcols], target)
    probability = np.asarray(model.predict_proba(test[xcols])[:, 1], dtype=float)
    if spec.mode == "hard_gate":
        probability = (probability >= 0.5).astype(float)
    return np.clip(prior + probability * (base_live - prior), 0.0, capacity)


def evaluate(frame: pd.DataFrame, spec: Spec) -> dict[str, Any]:
    folds = []
    event_ids = sorted(int(v) for v in frame["ticket_event_id"].unique())
    for held_out in event_ids:
        outer_train = frame[frame["ticket_event_id"] != held_out].copy()
        outer_test = frame[frame["ticket_event_id"] == held_out].copy().sort_values("as_of_at")

        meta_train = add_hybrid_features(inner_oof_meta_frame(outer_train), {
            "ticketingChallengerRows": frame.attrs["hybrid_rows"]
        })
        outer_base = fit_base_live(outer_train, outer_test)
        outer_meta = add_hybrid_features(add_meta_features(outer_test, outer_base), {
            "ticketingChallengerRows": frame.attrs["hybrid_rows"]
        })
        prediction = fit_predict(spec, meta_train, outer_meta)
        m = fold_metrics(outer_test, prediction)
        folds.append({
            "ticket_event_id": held_out,
            "home_team": str(outer_test["home_team"].iloc[0]),
            "away_team": str(outer_test["away_team"].iloc[0]),
            "rows": int(len(outer_test)),
            "hybrid_v6": None if outer_meta["hybrid_v6"].isna().all() else float(outer_meta["hybrid_v6"].iloc[0]),
            "hybrid_v6_source": str(outer_meta["hybrid_v6_source"].iloc[0]),
            **m,
            "improved": bool(m["live_window_mae"] < m["prior_window_mae"]),
        })

    prior_mae = float(np.mean([f["prior_window_mae"] for f in folds]))
    live_mae = float(np.mean([f["live_window_mae"] for f in folds]))
    return {
        "candidate": spec.name,
        "mode": spec.mode,
        "event_count": len(folds),
        "prior_window_mae": prior_mae,
        "live_window_mae": live_mae,
        "absolute_uplift": prior_mae - live_mae,
        "relative_improvement": (prior_mae - live_mae) / prior_mae if prior_mae else 0.0,
        "event_improvement_rate": float(np.mean([f["improved"] for f in folds])),
        "worst_event_degradation": float(max(f["degradation"] for f in folds)),
        "prior_first_row_mae": float(np.mean([f["prior_first_error"] for f in folds])),
        "live_first_row_mae": float(np.mean([f["live_first_error"] for f in folds])),
        "prior_latest_row_mae": float(np.mean([f["prior_latest_error"] for f in folds])),
        "live_latest_row_mae": float(np.mean([f["live_latest_error"] for f in folds])),
        "folds": folds,
    }


def incumbent(frame: pd.DataFrame) -> dict[str, Any]:
    folds = []
    for event_id, test in frame.groupby("ticket_event_id", sort=True):
        test = test.sort_values("as_of_at")
        prior = test["prior_p50"].astype(float).to_numpy()
        m = fold_metrics(test, prior)
        folds.append({"ticket_event_id": int(event_id), **m})
    mae = float(np.mean([f["prior_window_mae"] for f in folds]))
    return {"live_window_mae": mae, "folds": folds}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    if payload.get("version") != "c1-alpha-training-export-v2":
        raise RuntimeError(f"v5 requires C1 export v2, got {payload.get('version')}")

    priors = _event_prior_replay(payload, args.artifact_dir)
    frame = add_event_context(_training_frame(payload, priors), payload)
    frame = frame[
        (frame["hours_to_kickoff"].astype(float) >= 0.0)
        & (frame["hours_to_kickoff"].astype(float) <= WINDOW_HOURS)
        & (frame["prior_horizon"] == "T-1")
    ].copy()
    frame.attrs["hybrid_rows"] = payload.get("ticketingChallengerRows") or []
    frame = add_hybrid_features(frame, payload)

    if frame["ticket_event_id"].nunique() < 6:
        raise RuntimeError("C1 hybrid gate v5 requires at least 6 independent events")

    base = incumbent(frame)
    candidates = [evaluate(frame, spec) for spec in specs(frame)]
    candidates.sort(key=lambda row: (
        row["live_window_mae"],
        row["worst_event_degradation"],
        -row["event_improvement_rate"],
        row["candidate"],
    ))
    best = candidates[0]

    report = {
        "experiment": "c1-alpha-t1-hybrid-gate-v5",
        "dataset_version": payload.get("version"),
        "ticketing_challenger_contract": payload.get("ticketingChallengerContract"),
        "event_count": int(frame["ticket_event_id"].nunique()),
        "row_count": int(len(frame)),
        "hybrid_event_count": len({int(r["ticket_event_id"]) for r in payload.get("ticketingChallengerRows") or []}),
        "validation": "outer LOEO; inner-LOEO OOF base predictions for meta training",
        "incumbent": base,
        "best": best,
        "goal": {
            "beat_structural_prior": bool(best["live_window_mae"] < base["live_window_mae"]),
            "under_1900": bool(best["live_window_mae"] < 1900.0),
            "under_1700": bool(best["live_window_mae"] < 1700.0),
            "under_1500_stretch": bool(best["live_window_mae"] < 1500.0),
        },
        "leaderboard": candidates,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({
        "experiment": report["experiment"],
        "event_count": report["event_count"],
        "row_count": report["row_count"],
        "hybrid_event_count": report["hybrid_event_count"],
        "incumbent_mae": base["live_window_mae"],
        "best": {k: best[k] for k in (
            "candidate", "mode", "live_window_mae", "absolute_uplift",
            "relative_improvement", "event_improvement_rate", "worst_event_degradation",
            "live_first_row_mae", "live_latest_row_mae"
        )},
        "goal": report["goal"],
        "top_10": [
            {k: row[k] for k in (
                "candidate", "mode", "live_window_mae", "absolute_uplift",
                "relative_improvement", "event_improvement_rate", "worst_event_degradation"
            )}
            for row in candidates[:10]
        ],
        "best_folds": best["folds"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
