"""Historical diagnostic replay of fixed incumbent splits; never writes models."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from threadpoolctl import threadpool_limits

from ml.demand_engine.freeze_structural_prior_artifacts import EXPECTED_HOLDOUT_MAE
from ml.demand_engine.structural_prior_runtime import CURRENT_EARLY_RUNTIME_SPECS, fit_structural_prior_runtime
from ml.features.structural_prior_feature_store_v1 import WARSAW_TZ, build_feature_store, quality_report

VERSION = "mae01-incumbent-error-decomposition-v1"
HORIZONS = ("T-30", "T-14", "T-7", "T-3", "T-1")
FOLDS = (
    ("2024/2025", ("2021/2022", "2022/2023", "2023/2024")),
    ("2025/2026", ("2021/2022", "2022/2023", "2023/2024", "2024/2025")),
)
DIMENSIONS = (
    "horizon", "home_club_key", "season", "attendance_bucket", "actual_fill_bucket",
    "baseline_fill_bucket", "week_part", "season_phase", "opponent_draw_bucket",
    "opponent_position_bucket", "history_support_bucket", "error_direction",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text())
    entries = [manifest["historical_runtime"], *manifest["artifacts"].values()]
    for entry in entries:
        if Path(entry["filename"]).name != entry["filename"]:
            raise ValueError("Unexpected artifact filename")
        if sha256(directory / entry["filename"]) != entry["sha256"]:
            raise ValueError(f"Frozen source hash mismatch: {entry['filename']}")
    return manifest


def canonical_matches(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    local = pd.to_datetime(pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
                           + " " + frame["kickoff_time_local"].astype(str), format="mixed")
    frame["kickoff_at"] = local.dt.tz_localize(WARSAW_TZ, ambiguous="raise", nonexistent="raise").dt.tz_convert("UTC")
    frame["completed_at"] = frame["kickoff_at"] + pd.Timedelta(hours=3)
    frame["training_eligible"] = frame["attendance"].astype(float).ne(0)
    frame["round"] = frame["round"].astype(int)
    if len(frame) != 1530 or frame["match_key"].nunique() != 1530:
        raise ValueError("Expected exactly 1530 distinct canonical fixtures")
    return frame.sort_values(["kickoff_at", "home_club_key"]).reset_index(drop=True)


def validate_rows(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise ValueError("No historical predictions")
    if frame.duplicated(["match_key", "horizon"]).any():
        raise ValueError("Duplicate event/horizon")
    if not set(frame["horizon"]).issubset(HORIZONS):
        raise ValueError("Unexpected horizon")
    numeric = frame[["target_attendance", "prediction", "baseline", "capacity"]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all() or (numeric[:, :3] < 0).any() or (numeric[:, 3] <= 0).any():
        raise ValueError("Invalid count or capacity")
    for column in ("target_attendance", "home_club_key", "season", "kickoff_at"):
        if frame.groupby("match_key")[column].nunique(dropna=False).gt(1).any():
            raise ValueError(f"Inconsistent event identity: {column}")
    cutoff = pd.to_datetime(frame["as_of_at"], utc=True)
    kickoff = pd.to_datetime(frame["kickoff_at"], utc=True)
    days = frame["horizon"].str.removeprefix("T-").astype(int)
    if not ((kickoff - cutoff) == pd.to_timedelta(days, unit="D")).all():
        raise ValueError("Incorrect PIT horizon cutoff")


def add_segments(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    def bins(series, boundaries, labels):
        return pd.cut(series, boundaries, labels=labels, right=False).astype(object).fillna("unknown")
    out["attendance_bucket"] = bins(out["target_attendance"], [-np.inf, 5000, 10000, 20000, np.inf],
                                     ["<5k", "5k-<10k", "10k-<20k", "20k+"])
    labels = ["low:<50%", "normal:50-<85%", "near:85-<95%", "sellout-prone:95-100%", "above-capacity"]
    boundaries = [-np.inf, .5, .85, .95, np.nextafter(1.0, np.inf), np.inf]
    out["actual_fill_bucket"] = bins(out["target_attendance"] / out["capacity"], boundaries, labels)
    out["baseline_fill_bucket"] = bins(out["baseline"] / out["capacity"], boundaries, labels)
    local = pd.to_datetime(out["kickoff_at"], utc=True).dt.tz_convert(WARSAW_TZ)
    out["week_part"] = np.where(local.dt.weekday >= 5, "weekend", "weekday")
    out["season_phase"] = bins(out["season_progress"], [-np.inf, 1/3, 2/3, np.inf], ["early", "mid", "late"])
    draw = out["opponent_draw_ratio_mean"].where(out["opponent_draw_n"] > 0)
    out["opponent_draw_bucket"] = bins(draw, [-np.inf, .9, 1.1, np.inf], ["below:.9", "typical:.9-<1.1", "above:1.1+"])
    position = out["away_position"]
    out["opponent_position_bucket"] = np.select([position <= 4, position >= 15, position.notna()],
                                                ["top4", "bottom4", "middle"], default="unknown")
    out["history_support_bucket"] = bins(out["home_history_n"], [-np.inf, 10, 30, np.inf], ["<10", "10-<30", "30+"])
    out["error"] = out["prediction"] - out["target_attendance"]
    out["baseline_error"] = out["baseline"] - out["target_attendance"]
    out["error_direction"] = np.select([out["error"] > 0, out["error"] < 0], ["over", "under"], default="exact")
    return out


def metrics(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"event_count": 0, "row_count": 0, "event_balanced_mae": None, "signed_bias": None}
    per_event = frame.assign(ae=frame["error"].abs(), bae=frame["baseline_error"].abs(),
                             over=(frame["error"] > 0).astype(float)).groupby("match_key").agg(
        ae=("ae", "mean"), bae=("bae", "mean"), bias=("error", "mean"), over=("over", "mean"))
    return {
        "event_count": int(len(per_event)), "row_count": int(len(frame)),
        "event_balanced_mae": float(per_event.ae.mean()),
        "baseline_event_balanced_mae": float(per_event.bae.mean()),
        "delta_vs_baseline": float((per_event.ae-per_event.bae).mean()),
        "signed_bias": float(per_event.bias.mean()), "overprediction_rate": float(per_event.over.mean()),
        "median_event_ae": float(per_event.ae.median()), "p90_event_ae": float(per_event.ae.quantile(.9)),
        "worst_event_ae": float(per_event.ae.max()),
        "event_improvement_rate": float((per_event.ae < per_event.bae).mean()),
    }


def segment_tables(frame: pd.DataFrame) -> dict:
    weights = 1.0 / frame.groupby("match_key")["horizon"].transform("count")
    work = frame.assign(event_weight=weights, weighted_ae=weights*frame["error"].abs())
    events = frame["match_key"].nunique()
    total_error = work.weighted_ae.sum()
    tables = {}
    for dimension in DIMENSIONS:
        table = []
        for value, group in work.groupby(dimension, dropna=False, sort=True):
            contribution = float(group.weighted_ae.sum() / events)
            table.append({"value": str(value), **metrics(group),
                          "effective_event_weight": float(group.event_weight.sum()),
                          "contribution_to_overall_mae": contribution,
                          "error_share": float(group.weighted_ae.sum()/total_error) if total_error else 0.0})
        tables[dimension] = sorted(table, key=lambda item: (-item["contribution_to_overall_mae"], item["value"]))
        if not np.isclose(sum(item["contribution_to_overall_mae"] for item in table), metrics(frame)["event_balanced_mae"]):
            raise ValueError("Error contribution does not reconcile")
    return tables


def worst_events(frame: pd.DataFrame, limit: int = 30) -> list[dict]:
    result = []
    total = frame.groupby("match_key")["error"].apply(lambda values: values.abs().mean()).sum()
    for key, group in frame.groupby("match_key"):
        first = group.iloc[0]
        tags = []
        if (group.error > 0).all() or (group.error < 0).all():
            tags.append("same_signed_error_across_available_horizons")
        if group.prediction.max() - group.prediction.min() >= 1000:
            tags.append("prediction_horizon_spread_at_least_1000")
        if group.home_history_n.min() < 10:
            tags.append("sparse_home_history")
        if (group.target_attendance > group.capacity).any():
            tags.append("actual_above_capacity_map_requires_review")
        elif (group.target_attendance / group.capacity).max() >= .95:
            tags.append("high_actual_fill")
        item = {"match_key": str(key), "season": str(first.season), "home_club_key": str(first.home_club_key),
                "away_club_key": str(first.away_club_key), "kickoff_at": str(first.kickoff_at),
                "actual_attendance": float(first.target_attendance), **metrics(group),
                "associations_only": tags,
                "unassessed": ["booking_curve_dynamics", "source_defect", "event_specific_shock"],
                "horizons": [{"horizon": str(row.horizon), "prediction": float(row.prediction),
                               "signed_error": float(row.error), "capacity": float(row.capacity)}
                              for row in group.itertuples()]}
        item["error_share"] = item["event_balanced_mae"] / total if total else 0.0
        result.append(item)
    return sorted(result, key=lambda item: (-item["event_balanced_mae"], item["match_key"]))[:limit]


def decompose(frame: pd.DataFrame) -> dict:
    validate_rows(frame)
    work = add_segments(frame)
    complete = work.groupby("match_key")["horizon"].nunique().eq(len(HORIZONS))
    common = work[work.match_key.isin(complete[complete].index)]
    return {"available_cohort": metrics(work), "common_five_horizon_cohort": metrics(common),
            "common_cohort_per_horizon": {h: metrics(common[common.horizon == h]) for h in HORIZONS},
            "club_by_season": {str(season): segment_tables(group)["home_club_key"]
                               for season, group in work.groupby("season")},
            "segments": segment_tables(work), "worst_events": worst_events(work)}


def replay(store: pd.DataFrame, matches: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    frames, checks = [], []
    for season, train_seasons in FOLDS:
        for horizon in HORIZONS:
            spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
            candidates = store[(store.season == season) & (store.horizon == horizon)]
            test = candidates[candidates.training_eligible.astype(bool) & candidates[spec.baseline_column].notna()].copy()
            training = store[(store.horizon == horizon) & store.season.isin(train_seasons)
                             & store.training_eligible.astype(bool) & store[spec.baseline_column].notna()]
            latest_label = matches.loc[matches.match_key.isin(training.match_key), "completed_at"].max()
            if test.empty or latest_label >= test.as_of_at.min() or set(training.match_key) & set(test.match_key):
                raise ValueError("Training labels unavailable at earliest evaluation cutoff")
            with threadpool_limits(limits=1):
                runtime = fit_structural_prior_runtime(store, horizon, train_seasons)
                prediction = runtime.predict(test)
            mae = float(np.mean(np.abs(prediction - test.target_attendance.to_numpy())))
            expected = EXPECTED_HOLDOUT_MAE[horizon][season]
            if not np.isclose(mae, expected, rtol=0, atol=1e-7):
                raise ValueError(f"Frozen benchmark mismatch {horizon}/{season}: {mae} vs {expected}")
            # Diagnostic fields are attached only after model fitting/prediction.
            test["prediction"] = prediction
            test["baseline"] = test[spec.baseline_column]
            frames.append(test)
            checks.append({"season": season, "horizon": horizon, "training_seasons": list(train_seasons),
                           "training_rows": runtime.training_rows, "latest_training_label_at": str(latest_label),
                           "earliest_evaluation_cutoff": str(test.as_of_at.min()),
                           "candidate_event_count": len(candidates), "evaluated_event_count": len(test),
                           "excluded_event_count": len(candidates)-len(test), "replayed_mae": mae,
                           "frozen_expected_mae": expected, "status": "MATCH"})
    return pd.concat(frames, ignore_index=True), checks


def render_report(report: dict) -> str:
    cohort = report["available_cohort"]
    common = report["common_five_horizon_cohort"]
    lines = ["# MAE-01 incumbent error decomposition v1", "",
             "Historical fixed-split replay of already exposed seasons; no new challenger, fresh holdout, prospective validation or MAE improvement claim.", "",
             f"Available cohort: **{cohort['event_count']} independent events / {cohort['row_count']} horizon rows**. "
             f"Equal-event MAE **{cohort['event_balanced_mae']:.2f} people**, bias {cohort['signed_bias']:+.2f}, "
             f"median event AE {cohort['median_event_ae']:.2f}, P90 {cohort['p90_event_ae']:.2f}.", "",
             f"Common five-horizon cohort: {common['event_count']} events; MAE {common['event_balanced_mae']:.2f}. "
             "Per-horizon comparisons below use these same events. No horizon is an additional independent event.", "",
             "The baseline in the machine report is each frozen runtime's original PIT anchor (T-14 rolling-three mean; other horizons seasonal/history mean). It is not a newly selected challenger.", "",
             "## Common-cohort horizon errors", "", "| Horizon | Events | MAE | Signed bias |",
             "|---|---:|---:|---:|"]
    for horizon in HORIZONS:
        item = report["common_cohort_per_horizon"][horizon]
        lines.append(f"| {horizon} | {item['event_count']} | {item['event_balanced_mae']:.2f} | {item['signed_bias']:+.2f} |")
    for dimension in DIMENSIONS:
        lines += ["", f"## {dimension}", "",
                  "Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.", "",
                  "| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |",
                  "|---|---:|---:|---:|---:|---:|---:|"]
        for item in report["segments"][dimension]:
            lines.append(f"| {item['value']} | {item['event_count']} | {item['effective_event_weight']:.2f} | "
                         f"{item['event_balanced_mae']:.2f} | {item['signed_bias']:+.2f} | "
                         f"{item['contribution_to_overall_mae']:.2f} | {100*item['error_share']:.2f}% |")
    lines += ["", "## Largest event errors", "", "Associations only; causes remain unassessed without supporting source/trajectory evidence.", "",
              "| Fixture | Actual attendance | Mean AE across horizons | Signed bias | Error share |",
              "|---|---:|---:|---:|---:|"]
    for item in report["worst_events"]:
        key = item["match_key"].replace("|", " / ")
        lines.append(f"| {key} | {item['actual_attendance']:.0f} | {item['event_balanced_mae']:.2f} | "
                     f"{item['signed_bias']:+.2f} | {100*item['error_share']:.2f}% |")
    lines += ["", "## Reproduction and limits", "",
              f"All {len(report['reproduction'])} frozen horizon/season MAEs reproduced within absolute tolerance 1e-7. "
              "Source/artifact hashes verified before and after; no models saved or replaced.", ""]
    lines += ["- "+item for item in report["limitations"]]
    lines += ["", "`production_change=false`, `live_adjustment=0`.", ""]
    return "\n".join(lines)


def run(directory: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("Refusing to overwrite an existing analysis directory")
    manifest = verify_sources(directory)
    matches = canonical_matches(directory / manifest["historical_runtime"]["filename"])
    store = build_feature_store(matches)
    quality = quality_report(store)
    if quality["status"] != "PASS":
        raise ValueError("Canonical feature-store quality failure")
    frame, checks = replay(store, matches)
    report = {"version": VERSION, "evidence_kind": "exposed_historical_fixed_split_diagnostic_replay",
              "production_change": False, "live_adjustment": 0, "prospective_validation": False,
              "new_model_selection": False, "target": "attendance", "unit": "people",
              "provenance": {"manifest_sha256": sha256(directory / "manifest.json"),
                             "historical_sha256": manifest["historical_runtime"]["sha256"],
                             "audit_code_sha256": sha256(Path(__file__)),
                             "runtime_code_sha256": sha256(Path(__file__).parent / "demand_engine/structural_prior_runtime.py"),
                             "feature_code_sha256": sha256(Path(__file__).parent / "features/structural_prior_feature_store_v1.py"),
                             "libraries": {"numpy": np.__version__, "pandas": pd.__version__, "sklearn": sklearn.__version__}},
              "limitations": ["Already exposed test seasons; not fresh confirmatory evidence",
                              "PIT replay of archived fixture times/capacity does not establish historical publication timestamps",
                              "Outcome-conditioned attendance/fill bins are descriptive only",
                              "No historical booking curves; event shocks and causal error attribution unassessed",
                              "Ekstraklasa-only historical cohort differs from current prospective events"],
              "quality": quality, "reproduction": checks, **decompose(frame)}
    report["coverage"] = {"candidate_events": int(matches[matches.season.isin([s for s, _ in FOLDS])].match_key.nunique()),
                          "evaluated_events": report["available_cohort"]["event_count"],
                          "common_five_horizon_events": report["common_five_horizon_cohort"]["event_count"],
                          "exclusion_contract": "Existing training-eligibility/history and baseline-availability gates; see per-fold counts"}
    verify_sources(directory)  # No frozen file may have changed during the analysis.
    output.mkdir(parents=True)
    columns = ["match_key", "season", "horizon", "as_of_at", "kickoff_at", "home_club_key", "away_club_key",
               "target_attendance", "prediction", "baseline", "capacity", "home_history_n", "season_progress",
               "opponent_draw_n", "opponent_draw_ratio_mean", "away_position"]
    frame[columns].to_csv(output / "event_predictions.csv", index=False)
    report["provenance"]["event_predictions_sha256"] = sha256(output / "event_predictions.csv")
    (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n")
    (output / "report.md").write_text(render_report(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=Path("ml/artifacts/structural_prior_runtime_v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.artifact_dir, args.output)
    print(json.dumps({"version": VERSION, "reproduction_checks": len(report["reproduction"]),
                      "available_cohort": report["available_cohort"], "output": str(args.output),
                      "production_change": False}, indent=2))


if __name__ == "__main__":
    main()
