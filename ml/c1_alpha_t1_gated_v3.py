#!/usr/bin/env python3
"""C1-alpha T-1 gated/blended tournament v3.

v2 proved that live ticketing can materially reduce aggregate T-1 MAE but an
unconditional live replacement damages events where Structural Prior is already
excellent. v3 treats this as a gating/blending problem.

Validation is nested Leave-One-Event-Out:
- outer event is untouched test evidence;
- inner LOEO on outer-training events selects a policy;
- the base live model is refit on all outer-training events;
- selected policy is applied to the untouched outer event.

No outer-event outcome can influence policy selection.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay, _training_frame
from ml.c1_alpha_t1_tournament_v2 import (
    COMPACT_NUMERIC,
    WINDOW_HOURS,
    event_weights,
    fit_with_weights,
    pipeline,
)


@dataclass(frozen=True)
class BlendPolicy:
    disagreement_threshold: float
    weight: float
    max_correction_pct_capacity: float

    @property
    def name(self) -> str:
        return (
            f"gate_d{self.disagreement_threshold:.2f}_"
            f"w{self.weight:.2f}_cap{self.max_correction_pct_capacity:.2f}"
        )


def policy_grid() -> list[BlendPolicy]:
    # Compact predeclared grid. Threshold and cap are fractions of verified
    # capacity. They use only prior/live disagreement, never the actual outcome.
    thresholds = (0.00, 0.03, 0.05, 0.08, 0.12, 0.16)
    weights = (0.25, 0.50, 0.75, 1.00)
    caps = (0.05, 0.10, 0.15, 0.25)
    return [
        BlendPolicy(threshold, weight, cap)
        for threshold in thresholds
        for weight in weights
        for cap in caps
    ]


def base_features(frame: pd.DataFrame) -> list[str]:
    return [column for column in COMPACT_NUMERIC if column in frame.columns]


def fit_base_live(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Exact v2 winner: generic compact Ridge alpha=10, direct occupancy."""
    features = base_features(train)
    model = pipeline(features, False, Ridge(alpha=10.0), scale=True)
    target = (
        train["actual_attendance"].astype(float)
        / train["stadium_capacity"].astype(float)
    ).to_numpy()
    fitted = fit_with_weights(
        model,
        train[features],
        target,
        event_weights(train),
    )
    occupancy = np.asarray(fitted.predict(test[features]), dtype=float)
    capacity = test["stadium_capacity"].astype(float).to_numpy()
    return np.clip(occupancy * capacity, 0.0, capacity)


def apply_policy(frame: pd.DataFrame, live: np.ndarray, policy: BlendPolicy) -> np.ndarray:
    prior = frame["prior_p50"].astype(float).to_numpy()
    capacity = frame["stadium_capacity"].astype(float).to_numpy()
    raw_correction = np.asarray(live, dtype=float) - prior
    disagreement = np.abs(raw_correction) / capacity
    eligible = disagreement >= policy.disagreement_threshold
    limit = policy.max_correction_pct_capacity * capacity
    bounded = np.clip(raw_correction, -limit, limit)
    applied = np.where(eligible, policy.weight * bounded, 0.0)
    return np.clip(prior + applied, 0.0, capacity)


def event_metrics(frame: pd.DataFrame, prediction: np.ndarray) -> dict[str, float]:
    actual = frame["actual_attendance"].astype(float).to_numpy()
    prior = frame["prior_p50"].astype(float).to_numpy()
    prediction = np.asarray(prediction, dtype=float)
    prior_error = np.abs(prior - actual)
    live_error = np.abs(prediction - actual)
    return {
        "prior_window_mae": float(np.mean(prior_error)),
        "live_window_mae": float(np.mean(live_error)),
        "prior_first_error": float(prior_error[0]),
        "live_first_error": float(live_error[0]),
        "prior_latest_error": float(prior_error[-1]),
        "live_latest_error": float(live_error[-1]),
        "degradation": float(np.mean(live_error) - np.mean(prior_error)),
    }


def inner_oof_predictions(outer_train: pd.DataFrame) -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    event_ids = sorted(int(value) for value in outer_train["ticket_event_id"].unique())
    for inner_held_out in event_ids:
        inner_train = outer_train[outer_train["ticket_event_id"] != inner_held_out].copy()
        inner_test = (
            outer_train[outer_train["ticket_event_id"] == inner_held_out]
            .copy()
            .sort_values("as_of_at")
        )
        if inner_train["ticket_event_id"].nunique() < 2:
            continue
        live = fit_base_live(inner_train, inner_test)
        block = inner_test.copy()
        block["base_live_prediction"] = live
        records.append(block)
    if not records:
        raise RuntimeError("Nested C1 gate could not create inner OOF predictions")
    return pd.concat(records, ignore_index=True)


def score_policy(oof: pd.DataFrame, policy: BlendPolicy) -> dict[str, float]:
    event_scores = []
    for _, event in oof.groupby("ticket_event_id", sort=True):
        event = event.sort_values("as_of_at")
        final = apply_policy(event, event["base_live_prediction"].to_numpy(), policy)
        m = event_metrics(event, final)
        event_scores.append(m)
    return {
        "mae": float(np.mean([row["live_window_mae"] for row in event_scores])),
        "prior_mae": float(np.mean([row["prior_window_mae"] for row in event_scores])),
        "worst_degradation": float(max(row["degradation"] for row in event_scores)),
        "mean_abs_degradation": float(np.mean([abs(row["degradation"]) for row in event_scores])),
    }


def select_policy(outer_train: pd.DataFrame) -> tuple[BlendPolicy, dict[str, Any]]:
    oof = inner_oof_predictions(outer_train)
    scored = []
    for policy in policy_grid():
        result = score_policy(oof, policy)
        scored.append((policy, result))
    # MAE first. On near ties prefer lower catastrophic risk and then the more
    # conservative policy (lower weight/cap, higher threshold).
    scored.sort(key=lambda item: (
        item[1]["mae"],
        item[1]["worst_degradation"],
        item[0].weight,
        item[0].max_correction_pct_capacity,
        -item[0].disagreement_threshold,
    ))
    policy, result = scored[0]
    return policy, {
        "selected": asdict(policy),
        "selected_name": policy.name,
        "inner_mae": result["mae"],
        "inner_prior_mae": result["prior_mae"],
        "inner_uplift": result["prior_mae"] - result["mae"],
        "inner_worst_degradation": result["worst_degradation"],
        "runner_up": [
            {
                "policy": item[0].name,
                **item[1],
            }
            for item in scored[1:4]
        ],
    }


def outer_nested_evaluation(frame: pd.DataFrame) -> dict[str, Any]:
    event_ids = sorted(int(value) for value in frame["ticket_event_id"].unique())
    folds = []
    selected_policies = Counter()

    for held_out in event_ids:
        outer_train = frame[frame["ticket_event_id"] != held_out].copy()
        outer_test = (
            frame[frame["ticket_event_id"] == held_out]
            .copy()
            .sort_values("as_of_at")
        )
        policy, policy_evidence = select_policy(outer_train)
        selected_policies[policy.name] += 1
        base_live = fit_base_live(outer_train, outer_test)
        final = apply_policy(outer_test, base_live, policy)
        m = event_metrics(outer_test, final)

        prior = outer_test["prior_p50"].astype(float).to_numpy()
        capacity = outer_test["stadium_capacity"].astype(float).to_numpy()
        disagreement = np.abs(base_live - prior) / capacity
        applied_share = float(np.mean(disagreement >= policy.disagreement_threshold))

        folds.append({
            "ticket_event_id": held_out,
            "home_team": str(outer_test["home_team"].iloc[0]),
            "away_team": str(outer_test["away_team"].iloc[0]),
            "rows": int(len(outer_test)),
            "selected_policy": policy.name,
            "policy_evidence": policy_evidence,
            "base_live_disagreement_pct_capacity_mean": float(np.mean(disagreement)),
            "policy_applied_row_share": applied_share,
            **m,
            "improved": bool(m["live_window_mae"] < m["prior_window_mae"]),
        })

    prior_mae = float(np.mean([row["prior_window_mae"] for row in folds]))
    live_mae = float(np.mean([row["live_window_mae"] for row in folds]))
    prior_first = float(np.mean([row["prior_first_error"] for row in folds]))
    live_first = float(np.mean([row["live_first_error"] for row in folds]))
    prior_latest = float(np.mean([row["prior_latest_error"] for row in folds]))
    live_latest = float(np.mean([row["live_latest_error"] for row in folds]))
    return {
        "event_count": len(folds),
        "prior_window_mae": prior_mae,
        "live_window_mae": live_mae,
        "absolute_uplift": prior_mae - live_mae,
        "relative_improvement": (prior_mae - live_mae) / prior_mae if prior_mae else 0.0,
        "event_improvement_rate": float(np.mean([row["improved"] for row in folds])),
        "worst_event_degradation": float(max(row["degradation"] for row in folds)),
        "prior_first_row_mae": prior_first,
        "live_first_row_mae": live_first,
        "prior_latest_row_mae": prior_latest,
        "live_latest_row_mae": live_latest,
        "selected_policy_frequency": dict(selected_policies),
        "folds": folds,
    }


def choose_deployment_policy(frame: pd.DataFrame) -> dict[str, Any]:
    """Policy that would be frozen after nested validation, using all events."""
    policy, evidence = select_policy(frame)
    return {
        "policy": asdict(policy),
        "policy_name": policy.name,
        "training_evidence": evidence,
    }


def oracle_switch_diagnostic(frame: pd.DataFrame) -> dict[str, float]:
    """Non-deployable ceiling: choose prior/live with outcome knowledge.

    This is diagnostic only and is never used in policy/model selection.
    """
    event_ids = sorted(int(value) for value in frame["ticket_event_id"].unique())
    prior_errors = []
    live_errors = []
    oracle_errors = []
    for held_out in event_ids:
        train = frame[frame["ticket_event_id"] != held_out].copy()
        test = frame[frame["ticket_event_id"] == held_out].copy().sort_values("as_of_at")
        base_live = fit_base_live(train, test)
        actual = test["actual_attendance"].astype(float).to_numpy()
        prior = test["prior_p50"].astype(float).to_numpy()
        prior_mae = float(np.mean(np.abs(prior - actual)))
        live_mae = float(np.mean(np.abs(base_live - actual)))
        prior_errors.append(prior_mae)
        live_errors.append(live_mae)
        oracle_errors.append(min(prior_mae, live_mae))
    return {
        "prior_mae": float(np.mean(prior_errors)),
        "unconditional_base_live_mae": float(np.mean(live_errors)),
        "oracle_event_switch_mae": float(np.mean(oracle_errors)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    priors = _event_prior_replay(payload, args.artifact_dir)
    frame = _training_frame(payload, priors)
    frame = frame[
        (frame["hours_to_kickoff"].astype(float) >= 0.0)
        & (frame["hours_to_kickoff"].astype(float) <= WINDOW_HOURS)
        & (frame["prior_horizon"] == "T-1")
    ].copy()
    if frame["ticket_event_id"].nunique() < 6:
        raise RuntimeError("C1-alpha gated v3 requires at least 6 independent events")

    nested = outer_nested_evaluation(frame)
    deployment_policy = choose_deployment_policy(frame)
    oracle = oracle_switch_diagnostic(frame)

    report = {
        "experiment": "c1-alpha-t1-gated-v3",
        "window": "T-1 to kickoff / <=24h",
        "base_live_model": "ridge_directocc_compact_generic_a10",
        "dataset_version": payload.get("version"),
        "event_count": int(frame["ticket_event_id"].nunique()),
        "row_count": int(len(frame)),
        "validation": "nested Leave-One-Event-Out; inner policy selection; untouched outer event",
        "policy_grid_size": len(policy_grid()),
        "nested_result": nested,
        "deployment_candidate": deployment_policy,
        "oracle_diagnostic_not_for_selection": oracle,
        "goal": {
            "beat_structural_prior": bool(nested["live_window_mae"] < nested["prior_window_mae"]),
            "under_1900": bool(nested["live_window_mae"] < 1900.0),
            "under_1700": bool(nested["live_window_mae"] < 1700.0),
            "under_1500_stretch": bool(nested["live_window_mae"] < 1500.0),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({
        "experiment": report["experiment"],
        "event_count": report["event_count"],
        "row_count": report["row_count"],
        "nested_result": {key: nested[key] for key in (
            "prior_window_mae", "live_window_mae", "absolute_uplift",
            "relative_improvement", "event_improvement_rate", "worst_event_degradation",
            "prior_first_row_mae", "live_first_row_mae",
            "prior_latest_row_mae", "live_latest_row_mae",
            "selected_policy_frequency"
        )},
        "deployment_candidate": deployment_policy,
        "oracle_diagnostic_not_for_selection": oracle,
        "goal": report["goal"],
        "folds": [
            {key: fold[key] for key in (
                "ticket_event_id", "home_team", "away_team", "selected_policy",
                "prior_window_mae", "live_window_mae", "degradation", "improved"
            )}
            for fold in nested["folds"]
        ],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
