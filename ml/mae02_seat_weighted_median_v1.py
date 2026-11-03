"""One precommitted weighting diagnostic; no serving models are written."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from threadpoolctl import threadpool_limits

from ml.demand_engine.freeze_structural_prior_artifacts import EXPECTED_DEVELOPMENT_MAE, EXPECTED_HOLDOUT_MAE
from ml.demand_engine.structural_prior_runtime import CAT, FittedStructuralPriorRuntime, fit_structural_prior_runtime
from ml.features.structural_prior_feature_store_v1 import build_feature_store, quality_report
from ml.mae01_incumbent_error_audit_v1 import FOLDS, canonical_matches, sha256, validate_rows, verify_sources

VERSION = "structural-seat-weighted-median-v1"
HORIZONS = ("T-3", "T-1")
ANCHORS = ("baseline_season", "home_attendance_median", "home_attendance_rolling3", "home_attendance_last")


def capacity_weights(capacity) -> np.ndarray:
    values = np.asarray(capacity, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Finite positive training capacities required")
    return values / values.mean()


def fit_weighted_copy(incumbent: FittedStructuralPriorRuntime, training: pd.DataFrame) -> FittedStructuralPriorRuntime:
    spec = incumbent.spec
    if spec.horizon not in HORIZONS or incumbent.estimator.get_params().get("loss") != "absolute_error":
        raise ValueError("Only existing absolute-loss T-3/T-1 specifications are authorized")
    if (set(training.season) - set(incumbent.training_seasons)
            or set(training.horizon) != {spec.horizon}
            or training.match_key.duplicated().any()
            or len(training) != incumbent.training_rows):
        raise ValueError("Weighted fit must use the same eligible training events and seasons")
    capacity = training.capacity.to_numpy(dtype=float)
    weights = capacity_weights(capacity)
    target = (training.target_attendance.to_numpy(dtype=float)
              - training[spec.baseline_column].to_numpy(dtype=float)) / capacity
    if not np.isfinite(target).all():
        raise ValueError("Invalid training target")
    x = incumbent.preprocessor.transform(training[CAT + incumbent.numeric_features])
    estimator = clone(incumbent.estimator)
    estimator.fit(x, target, sample_weight=weights)
    return FittedStructuralPriorRuntime(spec=spec, preprocessor=incumbent.preprocessor, estimator=estimator,
        numeric_features=list(incumbent.numeric_features), training_seasons=incumbent.training_seasons,
        training_rows=incumbent.training_rows)


def paired_metrics(frame: pd.DataFrame) -> dict:
    if frame.empty or frame.duplicated(["match_key", "horizon"]).any():
        raise ValueError("Nonempty unique event/horizon pairs required")
    values = frame[["incumbent", "challenger", "target_attendance"]].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Invalid paired predictions or outcome")
    if (not set(frame.horizon).issubset(HORIZONS)
            or frame.groupby("match_key").target_attendance.nunique(dropna=False).gt(1).any()):
        raise ValueError("Inconsistent event outcomes or unauthorized horizon")
    work = frame.assign(inc_error=frame.incumbent-frame.target_attendance,
                        cand_error=frame.challenger-frame.target_attendance)
    events = work.assign(inc_ae=work.inc_error.abs(), cand_ae=work.cand_error.abs()).groupby("match_key").agg(
        incumbent_ae=("inc_ae", "mean"), challenger_ae=("cand_ae", "mean"),
        incumbent_bias=("inc_error", "mean"), challenger_bias=("cand_error", "mean"))
    delta = events.challenger_ae-events.incumbent_ae
    return {"event_count": int(len(events)), "row_count": int(len(frame)),
            "incumbent_event_balanced_mae": float(events.incumbent_ae.mean()),
            "challenger_event_balanced_mae": float(events.challenger_ae.mean()),
            "delta_mae": float(delta.mean()), "event_improvement_rate": float((delta < 0).mean()),
            "median_event_delta_ae": float(delta.median()), "best_event_improvement": float(delta.min()),
            "worst_event_degradation": float(delta.max()),
            "incumbent_signed_bias": float(events.incumbent_bias.mean()),
            "challenger_signed_bias": float(events.challenger_bias.mean()),
            "incumbent_median_event_ae": float(events.incumbent_ae.median()),
            "challenger_median_event_ae": float(events.challenger_ae.median()),
            "incumbent_p90_event_ae": float(events.incumbent_ae.quantile(.9)),
            "challenger_p90_event_ae": float(events.challenger_ae.quantile(.9)),
            "delta_p90_event_ae": float(events.challenger_ae.quantile(.9)-events.incumbent_ae.quantile(.9))}


def development_gate(horizons: dict) -> bool:
    if set(horizons) != set(HORIZONS):
        return False
    return all(np.isfinite(item["delta_mae"]) and np.isfinite(item["delta_p90_event_ae"])
               and item["delta_mae"] < 0 and item["delta_p90_event_ae"] <= 0 for item in horizons.values())


def evaluate_fold(store: pd.DataFrame, matches: pd.DataFrame, test_season: str,
                  train_seasons: tuple[str, ...], expected: dict[str, float]) -> tuple[pd.DataFrame, list[dict]]:
    frames, checks = [], []
    for horizon in HORIZONS:
        # The canonical store is kept clean of all evaluation/output columns.
        with threadpool_limits(limits=1):
            incumbent = fit_structural_prior_runtime(store, horizon, train_seasons)
            spec = incumbent.spec
            selected = store[(store.horizon == horizon) & store.training_eligible.astype(bool)
                             & store[spec.baseline_column].notna()]
            training = selected[selected.season.isin(train_seasons)].copy()
            test = selected[selected.season == test_season].copy()
            latest_label = matches.loc[matches.match_key.isin(training.match_key), "completed_at"].max()
            if (test.empty or latest_label >= test.as_of_at.min()
                    or set(training.match_key) & set(test.match_key)):
                raise ValueError("Temporal/event separation failed")
            base_prediction = incumbent.predict(test)
            base_mae = float(np.abs(base_prediction-test.target_attendance.to_numpy()).mean())
            if not np.isclose(base_mae, expected[horizon], rtol=0, atol=1e-7):
                raise ValueError(f"Frozen incumbent mismatch {horizon}/{test_season}")
            challenger = fit_weighted_copy(incumbent, training)
            candidate_prediction = challenger.predict(test)
            if not np.array_equal(base_prediction, incumbent.predict(test)):
                raise ValueError("Weighted fitting mutated the incumbent")
        validate_rows(test.assign(prediction=base_prediction, baseline=test[spec.baseline_column]))
        test["incumbent"], test["challenger"] = base_prediction, candidate_prediction
        frames.append(test)
        checks.append({"season": test_season, "horizon": horizon, "training_seasons": list(train_seasons),
                       "training_rows": len(training), "evaluated_events": len(test),
                       "latest_training_label_at": str(latest_label),
                       "earliest_evaluation_cutoff": str(test.as_of_at.min()),
                       "incumbent_expected_mae": expected[horizon], "incumbent_replayed_mae": base_mae,
                       "incumbent_prediction_unchanged_after_weighted_fit": True,
                       "normalized_training_weight_min": float(capacity_weights(training.capacity).min()),
                       "normalized_training_weight_max": float(capacity_weights(training.capacity).max())})
    return pd.concat(frames, ignore_index=True), checks


def summarize(frame: pd.DataFrame) -> dict:
    per_horizon = {h: paired_metrics(frame[frame.horizon == h]) for h in HORIZONS}
    event_weight = 1.0/frame.groupby("match_key").horizon.transform("count")
    work = frame.assign(weighted_delta=event_weight*((frame.challenger-frame.target_attendance).abs()
                                                     - (frame.incumbent-frame.target_attendance).abs()))
    clubs = [{"club": str(club), **paired_metrics(group),
              "contribution_to_overall_delta_mae": float(group.weighted_delta.sum()/frame.match_key.nunique())}
             for club, group in work.groupby("home_club_key")]
    anchors = {}
    for horizon in HORIZONS:
        candidates = frame[frame.horizon == horizon]
        anchors[horizon] = {}
        for column in ANCHORS:
            rows = candidates[candidates[column].notna()].copy()
            if rows.empty:
                anchors[horizon][column] = {"event_count": 0, "coverage": 0.0}
                continue
            rows["challenger"] = rows[column].clip(lower=0, upper=rows.capacity)
            anchors[horizon][column] = {**paired_metrics(rows), "coverage": len(rows)/len(candidates)}
    return {"overall": paired_metrics(frame), "per_horizon": per_horizon,
            "clubs": sorted(clubs, key=lambda x: (x["contribution_to_overall_delta_mae"], x["club"])),
            "fixed_simple_pit_anchors_not_selected": anchors}


def run(directory: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("Refusing to overwrite existing experiment output")
    manifest = verify_sources(directory)
    matches = canonical_matches(directory/manifest["historical_runtime"]["filename"])
    store = build_feature_store(matches)
    if quality_report(store)["status"] != "PASS":
        raise ValueError("Canonical feature quality failed")
    development, checks = evaluate_fold(store, matches, "2023/2024", ("2021/2022", "2022/2023"),
                                        {h: EXPECTED_DEVELOPMENT_MAE[h] for h in HORIZONS})
    summary = summarize(development)
    passed = development_gate(summary["per_horizon"])
    report = {"version": VERSION, "status": "DEVELOPMENT_SUPPORTED" if passed else "REJECT_FOR_PROSPECTIVE",
              "production_change": False, "live_adjustment": 0, "new_serving_artifact": False,
              "fresh_confirmatory_evidence": False,
              "provenance": {"historical_sha256": manifest["historical_runtime"]["sha256"],
                             "manifest_sha256": sha256(directory/"manifest.json"),
                             "audit_code_sha256": sha256(Path(__file__)),
                             "precommit_sha256": sha256(Path(__file__).with_name("MAE02_SEAT_WEIGHTED_MEDIAN_PRECOMMIT_V1.md"))},
              "development": summary, "reproduction": checks,
              "exposed_holdout_checks": {}, "weighted_holdout_fits_performed": False,
              "limitations": ["Development and old test seasons already exposed; no new independent validation",
                              "Historical capacity/publication-time limitations inherited from incumbent replay",
                              "Clubs and horizons are descriptive; no post-result variant/horizon selection",
                              "Training objective identity is before capacity clipping; weighting need not improve generalization"]}
    all_frames = [development]
    if passed:
        for season, training in FOLDS:
            frame, fold_checks = evaluate_fold(store, matches, season, training,
                {h: EXPECTED_HOLDOUT_MAE[h][season] for h in HORIZONS})
            report["exposed_holdout_checks"][season] = summarize(frame)
            report["reproduction"].extend(fold_checks)
            all_frames.append(frame)
        report["weighted_holdout_fits_performed"] = True
    verify_sources(directory)
    output.mkdir(parents=True)
    columns = ["match_key", "season", "horizon", "as_of_at", "kickoff_at", "home_club_key", "away_club_key",
               "target_attendance", "incumbent", "challenger", "capacity"]
    pd.concat(all_frames, ignore_index=True)[columns].to_csv(output/"event_predictions.csv", index=False)
    report["provenance"]["event_predictions_sha256"] = sha256(output/"event_predictions.csv")
    (output/"report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=Path("ml/artifacts/structural_prior_runtime_v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.artifact_dir, args.output)
    print(json.dumps({"version": VERSION, "status": report["status"],
                      "development": report["development"]["per_horizon"],
                      "weighted_holdout_fits_performed": report["weighted_holdout_fits_performed"],
                      "production_change": False}, indent=2))


if __name__ == "__main__":
    main()
