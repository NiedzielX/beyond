#!/usr/bin/env python3
"""Blocked time-split version of Beyond Global Historical Benchmark v1.

Protocol per horizon:
1. consume the canonical point-in-time Feature Store v2 artifact;
2. evaluation targets require >=3 prior home attendances;
3. model training may also use earlier warm-up rows when their residual baseline
   is already observable, preserving chronology while avoiding needless data loss;
4. candidate selection uses autumn 2025 only;
5. selected candidate is refit strictly before the earliest spring holdout
   snapshot and then frozen for holdout scoring.

No production promotion is performed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml.global_historical_benchmark_v1 import (
    CATEGORICAL,
    NUMERIC,
    DEV_END,
    DEV_START,
    HOLDOUT_START,
    MATCH_COMPLETION_BUFFER,
    baseline_column,
    baseline_report,
    candidates,
    metrics,
)

MIN_TARGET_HOME_HISTORY = 3
MIN_TRAIN_ROWS = 24


def load_store(path: Path) -> pd.DataFrame:
    store = pd.read_csv(path)
    store["as_of_at"] = pd.to_datetime(store["as_of_at"], utc=True)
    store["kickoff_at"] = pd.to_datetime(store["kickoff_at"], utc=True)
    return store.sort_values(["horizon", "as_of_at", "match_key"]).reset_index(drop=True)


def fit_predict_block(
    training_pool: pd.DataFrame,
    target_frame: pd.DataFrame,
    candidate,
    baseline_name: str,
) -> tuple[pd.DataFrame, int, str]:
    if target_frame.empty:
        return pd.DataFrame(), 0, "no_targets"

    baseline_col = baseline_column(baseline_name)
    block_cutoff = target_frame["as_of_at"].min()
    training = training_pool[
        (training_pool["kickoff_at"] + MATCH_COMPLETION_BUFFER < block_cutoff)
        & training_pool[baseline_col].notna()
        & training_pool["target_attendance"].notna()
    ].copy()
    if len(training) < MIN_TRAIN_ROWS:
        return pd.DataFrame(), int(len(training)), "insufficient_training_rows"

    X_train = training[CATEGORICAL + NUMERIC].copy()
    y_train = (
        training["target_attendance"].astype(float)
        - training[baseline_col].astype(float)
    ).to_numpy()

    model = candidate.factory()
    model.fit(X_train, y_train)

    X_target = target_frame[CATEGORICAL + NUMERIC].copy()
    residual = model.predict(X_target)
    baseline = target_frame[baseline_col].astype(float).to_numpy()
    prediction = np.maximum(0.0, baseline + residual)

    out = target_frame[["match_key", "as_of_at", "kickoff_at", "target_attendance"]].copy()
    out["actual"] = out["target_attendance"].astype(float)
    out["baseline"] = baseline
    out["prediction"] = prediction
    out["train_rows"] = int(len(training))
    return out, int(len(training)), "ok"


def score(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"n": 0, "mae": None}
    return metrics(frame["actual"].to_numpy(), frame["prediction"].to_numpy())


def eligible_targets(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[
        (frame["home_history_n"] >= MIN_TARGET_HOME_HISTORY)
        & frame["home_attendance_rolling3"].notna()
        & frame["target_attendance"].notna()
    ].copy()


def evaluate_horizon(store: pd.DataFrame, horizon: str) -> dict:
    training_pool = store[store["horizon"] == horizon].copy()
    targets = eligible_targets(training_pool)
    dev = targets[(targets["kickoff_at"] >= DEV_START) & (targets["kickoff_at"] < DEV_END)].copy()
    holdout = targets[targets["kickoff_at"] >= HOLDOUT_START].copy()

    if dev.empty or holdout.empty:
        raise RuntimeError(f"Missing development/holdout targets for {horizon}")

    dev_baselines = baseline_report(dev)
    baseline_name = dev_baselines["winner"]
    baseline_col = baseline_column(baseline_name)

    development = {}
    for candidate in candidates():
        pred, train_rows, status = fit_predict_block(training_pool, dev, candidate, baseline_name)
        development[candidate.name] = {
            "family": candidate.family,
            "train_rows": train_rows,
            "status": status,
            "metrics": score(pred),
        }

    usable = [
        name for name, result in development.items()
        if result["status"] == "ok" and result["metrics"].get("n", 0) > 0
    ]
    if not usable:
        counts = sorted({result["train_rows"] for result in development.values()})
        raise RuntimeError(
            f"No usable development candidate for {horizon}; training row counts={counts}"
        )

    selected_name = min(
        usable,
        key=lambda name: (
            development[name]["metrics"]["mae"],
            development[name]["metrics"]["wape_pct"],
            abs(development[name]["metrics"]["bias"]),
        ),
    )
    selected = next(candidate for candidate in candidates() if candidate.name == selected_name)

    holdout_pred, holdout_train_rows, holdout_status = fit_predict_block(
        training_pool, holdout, selected, baseline_name
    )
    if holdout_status != "ok":
        raise RuntimeError(f"Holdout unavailable for {horizon}: {holdout_status}")

    model_metrics = score(holdout_pred)
    comparable = holdout[holdout["match_key"].isin(set(holdout_pred["match_key"]))].copy()
    baseline_metrics = metrics(
        comparable["target_attendance"].astype(float).to_numpy(),
        comparable[baseline_col].astype(float).to_numpy(),
    )
    delta = baseline_metrics["mae"] - model_metrics["mae"]

    return {
        "horizon": horizon,
        "training_pool_rows": int(len(training_pool)),
        "eligible_target_rows": int(len(targets)),
        "development_rows": int(len(dev)),
        "holdout_rows": int(len(holdout)),
        "development_training_cutoff": dev["as_of_at"].min().isoformat(),
        "holdout_training_cutoff": holdout["as_of_at"].min().isoformat(),
        "development_baselines": dev_baselines,
        "selected_baseline": baseline_name,
        "development_candidates": development,
        "selected_model": selected_name,
        "holdout_training_rows": holdout_train_rows,
        "holdout_baseline": baseline_metrics,
        "holdout_model": model_metrics,
        "holdout_mae_improvement": round(float(delta), 2),
        "holdout_improvement_pct": round(float(delta / baseline_metrics["mae"] * 100.0), 2),
        "decision": "GLOBAL_MODEL_BETTER" if delta > 0 else "CLUB_BASELINE_BETTER",
    }


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Global Historical Benchmark v1 — blocked time split",
        "",
        "Target eligibility: >=3 previous home attendances. Training can use earlier warm-up rows with an observable baseline. Model selection: autumn 2025. Untouched holdout: spring 2026.",
        "",
        "| Horizon | Baseline | Model | Baseline MAE | Model MAE | Δ MAE | Improvement | Decision |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for horizon, r in report["horizons"].items():
        lines.append(
            f"| {horizon} | {r['selected_baseline']} | {r['selected_model']} | "
            f"{r['holdout_baseline']['mae']:.1f} | {r['holdout_model']['mae']:.1f} | "
            f"{r['holdout_mae_improvement']:+.1f} | {r['holdout_improvement_pct']:+.2f}% | {r['decision']} |"
        )
    lines.extend([
        "",
        "> One-season global proof-of-signal only. Multiple historical seasons are required before any production promotion or season-level generalisation claim.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    store = load_store(args.feature_store)
    results = {
        horizon: evaluate_horizon(store, horizon)
        for horizon in sorted(store["horizon"].unique())
    }
    report = {
        "benchmark_version": "global-historical-v1-blocked-v2",
        "dataset_version": str(store["dataset_version"].iloc[0]),
        "feature_set_version": str(store["feature_set_version"].iloc[0]),
        "protocol": "blocked point-in-time train/dev/holdout",
        "development_window": [DEV_START.isoformat(), DEV_END.isoformat()],
        "holdout_start": HOLDOUT_START.isoformat(),
        "minimum_target_home_history": MIN_TARGET_HOME_HISTORY,
        "minimum_training_rows": MIN_TRAIN_ROWS,
        "automatic_promotion": False,
        "horizons": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.markdown_output:
        write_markdown(report, args.markdown_output)

    print(json.dumps({
        h: {
            "baseline": r["selected_baseline"],
            "model": r["selected_model"],
            "baseline_mae": r["holdout_baseline"]["mae"],
            "model_mae": r["holdout_model"]["mae"],
            "delta_mae": r["holdout_mae_improvement"],
            "improvement_pct": r["holdout_improvement_pct"],
            "decision": r["decision"],
        }
        for h, r in results.items()
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
