#!/usr/bin/env python3
"""Beyond Forecast Benchmark v2.

Goal: improve predictive quality, not model complexity.

The benchmark reuses the exact recovered v1.7 T-7 point-in-time feature builder
and evaluates pre-registered model families under the same season-block
walk-forward protocol. Candidate selection uses development seasons only;
2024/25 and 2025/26 remain the untouched holdout.

No model is promoted or persisted by this script.
"""
from __future__ import annotations

import argparse
import json
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

from ml.recovered.v17.reconstruct_t7_v17 import (
    CAPACITY,
    NUMERIC_FEATURES,
    OPPONENT_MIN_HISTORY,
    build_template_model,
    prepare_dataset,
    season_start,
)
from ml.recovered.v17.t7_bundle import load_t7_frames

DEV_SEASONS = ["2022/2023", "2023/2024"]
HOLDOUT_SEASONS = ["2024/2025", "2025/2026"]
ALL_OOS_SEASONS = DEV_SEASONS + HOLDOUT_SEASONS
ROOT = Path(__file__).resolve().parent
PRESERVED_V17 = ROOT / "recovered" / "v17" / "v17_t7_oos_predictions.csv"


@dataclass(frozen=True)
class Candidate:
    name: str
    family: str
    factory: Callable[[], Pipeline]


def metric_set(actual: np.ndarray, prediction: np.ndarray) -> dict[str, float | int]:
    actual = np.asarray(actual, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    error = prediction - actual
    absolute = np.abs(error)
    ape = absolute / np.where(actual == 0, np.nan, actual) * 100.0
    return {
        "n": int(len(actual)),
        "mae": round(float(np.nanmean(absolute)), 4),
        "median_ae": round(float(np.nanmedian(absolute)), 4),
        "rmse": round(float(math.sqrt(np.nanmean(error ** 2))), 4),
        "mape_pct": round(float(np.nanmean(ape)), 4),
        "wape_pct": round(float(np.nansum(absolute) / np.nansum(actual) * 100.0), 4),
        "bias": round(float(np.nanmean(error)), 4),
        "p90_absolute_error": round(float(np.nanquantile(absolute, 0.90)), 4),
        "within_5_pct": round(float(np.nanmean(ape <= 5.0) * 100.0), 4),
        "within_10_pct": round(float(np.nanmean(ape <= 10.0) * 100.0), 4),
        "within_20_pct": round(float(np.nanmean(ape <= 20.0) * 100.0), 4),
    }


def preprocessor(*, scale_numeric: bool) -> ColumnTransformer:
    numeric_steps: list[tuple[str, object]] = [("imp", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scale", RobustScaler()))
    return ColumnTransformer(
        [
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["opponent_group"],
            ),
            ("num", Pipeline(numeric_steps), NUMERIC_FEATURES),
        ]
    )


def pipeline(estimator, *, scale_numeric: bool) -> Pipeline:
    return Pipeline([
        ("pre", preprocessor(scale_numeric=scale_numeric)),
        ("reg", estimator),
    ])


def candidates() -> list[Candidate]:
    specs: list[Candidate] = [
        Candidate("v17_ridge_a0_3", "ridge", build_template_model),
    ]

    for alpha in [0.03, 0.1, 1.0, 3.0, 10.0, 30.0, 100.0]:
        specs.append(Candidate(
            f"ridge_a{str(alpha).replace('.', '_')}",
            "ridge",
            lambda alpha=alpha: pipeline(Ridge(alpha=alpha), scale_numeric=True),
        ))

    for alpha, l1_ratio in [(0.01, 0.1), (0.03, 0.1), (0.1, 0.1), (0.1, 0.5), (0.3, 0.1), (0.3, 0.5)]:
        specs.append(Candidate(
            f"elastic_a{str(alpha).replace('.', '_')}_l1{str(l1_ratio).replace('.', '_')}",
            "elastic_net",
            lambda alpha=alpha, l1_ratio=l1_ratio: pipeline(
                ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=20000, random_state=42),
                scale_numeric=True,
            ),
        ))

    for epsilon in [1.2, 1.35, 1.5]:
        specs.append(Candidate(
            f"huber_e{str(epsilon).replace('.', '_')}",
            "robust_linear",
            lambda epsilon=epsilon: pipeline(
                HuberRegressor(epsilon=epsilon, alpha=0.0001, max_iter=2000),
                scale_numeric=True,
            ),
        ))

    for depth, leaf in [(1, 7), (2, 5), (2, 8), (3, 7)]:
        specs.append(Candidate(
            f"gbr_huber_d{depth}_leaf{leaf}",
            "gradient_boosting",
            lambda depth=depth, leaf=leaf: pipeline(
                GradientBoostingRegressor(
                    loss="huber",
                    n_estimators=220,
                    learning_rate=0.025,
                    max_depth=depth,
                    min_samples_leaf=leaf,
                    random_state=42,
                ),
                scale_numeric=False,
            ),
        ))

    for leaf, l2 in [(5, 0.0), (8, 0.0), (5, 1.0), (8, 1.0)]:
        specs.append(Candidate(
            f"hist_gbr_leaf{leaf}_l2{str(l2).replace('.', '_')}",
            "hist_gradient_boosting",
            lambda leaf=leaf, l2=l2: pipeline(
                HistGradientBoostingRegressor(
                    loss="absolute_error",
                    learning_rate=0.05,
                    max_iter=250,
                    max_leaf_nodes=15,
                    min_samples_leaf=leaf,
                    l2_regularization=l2,
                    random_state=42,
                ),
                scale_numeric=False,
            ),
        ))

    for leaf, max_features in [(2, 0.7), (4, 0.7), (2, 1.0), (4, 1.0)]:
        specs.append(Candidate(
            f"extra_trees_leaf{leaf}_mf{str(max_features).replace('.', '_')}",
            "extra_trees",
            lambda leaf=leaf, max_features=max_features: pipeline(
                ExtraTreesRegressor(
                    n_estimators=400,
                    min_samples_leaf=leaf,
                    max_features=max_features,
                    random_state=42,
                    n_jobs=1,
                ),
                scale_numeric=False,
            ),
        ))

    for leaf, max_features in [(2, 0.7), (4, 0.7)]:
        specs.append(Candidate(
            f"random_forest_leaf{leaf}_mf{str(max_features).replace('.', '_')}",
            "random_forest",
            lambda leaf=leaf, max_features=max_features: pipeline(
                RandomForestRegressor(
                    n_estimators=400,
                    min_samples_leaf=leaf,
                    max_features=max_features,
                    random_state=42,
                    n_jobs=1,
                ),
                scale_numeric=False,
            ),
        ))

    return specs


def load_dataset():
    frames = load_t7_frames()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        history_path = root / "history.csv"
        checkpoint_path = root / "checkpoint.csv"
        frames["history.csv"].to_csv(history_path, index=False)
        frames["checkpoint.csv"].to_csv(checkpoint_path, index=False)
        return prepare_dataset(history_path, checkpoint_path)


def design_matrices(df, features, train_index, test_index):
    counts = df.loc[train_index, "opponent_key"].value_counts()
    kept = set(counts[counts >= OPPONENT_MIN_HISTORY].index)
    columns = NUMERIC_FEATURES

    train = features.loc[train_index, columns].copy()
    test = features.loc[test_index, columns].copy()
    train["opponent_group"] = df.loc[train_index, "opponent_key"].where(
        df.loc[train_index, "opponent_key"].isin(kept), "other"
    )
    test["opponent_group"] = df.loc[test_index, "opponent_key"].where(
        df.loc[test_index, "opponent_key"].isin(kept), "other"
    )
    return train, test


def evaluate(candidate: Candidate, df, features, valid_target, seasons: list[str]) -> pd.DataFrame:
    rows: list[dict] = []
    usable_target = valid_target & features["season_avg_so_far"].notna()

    for season in seasons:
        test_index = df.index[(df["season"].astype(str) == season) & usable_target]
        if len(test_index) == 0:
            continue
        train_index = df.index[
            (df["dt"] < season_start(season)) & usable_target
        ]
        train_x, test_x = design_matrices(df, features, train_index, test_index)
        y = (
            df.loc[train_index, "attendance"].astype(float)
            - features.loc[train_index, "season_avg_so_far"].astype(float)
        )

        model = candidate.factory()
        model.fit(train_x, y)
        residual = model.predict(test_x)
        prediction = np.clip(
            features.loc[test_index, "season_avg_so_far"].astype(float).to_numpy() + residual,
            0.0,
            float(CAPACITY),
        )

        for index, pred in zip(test_index, prediction):
            rows.append({
                "row_index": int(index),
                "season": str(df.loc[index, "season"]),
                "match_date": str(df.loc[index, "match_date"]),
                "opponent_key": str(df.loc[index, "opponent_key"]),
                "actual": float(df.loc[index, "attendance"]),
                "prediction": float(pred),
            })

    return pd.DataFrame(rows).sort_values(["row_index"]).reset_index(drop=True)


def summarize(frame: pd.DataFrame) -> dict:
    overall = metric_set(frame["actual"].to_numpy(), frame["prediction"].to_numpy())
    by_season = {
        season: metric_set(group["actual"].to_numpy(), group["prediction"].to_numpy())
        for season, group in frame.groupby("season", sort=True)
    }
    return {"overall": overall, "by_season": by_season}


def combine_predictions(
    frames: dict[str, pd.DataFrame],
    members: list[str],
    weights: dict[str, float],
) -> pd.DataFrame:
    base = frames[members[0]][["row_index", "season", "match_date", "opponent_key", "actual"]].copy()
    prediction = np.zeros(len(base), dtype=float)
    for name in members:
        frame = frames[name]
        if not np.array_equal(base["row_index"].to_numpy(), frame["row_index"].to_numpy()):
            raise RuntimeError(f"Prediction rows differ for ensemble member {name}")
        prediction += frame["prediction"].to_numpy() * weights[name]
    base["prediction"] = np.clip(prediction, 0.0, float(CAPACITY))
    return base


def ranking_key(item):
    metrics = item[1]["metrics"]["overall"]
    return (metrics["mae"], metrics["wape_pct"], abs(metrics["bias"]))


def verify_v17_reproduction(frame: pd.DataFrame) -> dict:
    original = pd.read_csv(PRESERVED_V17)
    if len(original) != len(frame):
        raise RuntimeError(f"v1.7 reproduction row mismatch: {len(frame)} != {len(original)}")
    delta = frame["prediction"].to_numpy() - original["v17"].astype(float).to_numpy()
    result = {
        "n": int(len(delta)),
        "mean_absolute_difference": float(np.mean(np.abs(delta))),
        "max_absolute_difference": float(np.max(np.abs(delta))),
    }
    if result["max_absolute_difference"] > 1e-6:
        raise RuntimeError(f"Recovered v1.7 benchmark no longer reproduces: {result}")
    return result


def write_markdown(report: dict, path: Path) -> None:
    champion = report["champion_holdout"]
    selected = report["selected_holdout"]
    delta = report["holdout_delta_vs_v17_mae"]
    lines = [
        "# Beyond Forecast Benchmark v2",
        "",
        f"Development-selected candidate: **{report['selected_on_development']}**",
        f"Holdout decision: **{report['decision']}**",
        "",
        "| Metric | v1.7 champion | Dev-selected candidate | Delta |",
        "|---|---:|---:|---:|",
        f"| MAE | {champion['mae']:.1f} | {selected['mae']:.1f} | {delta:+.1f} |",
        f"| WAPE | {champion['wape_pct']:.2f}% | {selected['wape_pct']:.2f}% | {selected['wape_pct'] - champion['wape_pct']:+.2f} pp |",
        f"| Bias | {champion['bias']:.1f} | {selected['bias']:.1f} | {selected['bias'] - champion['bias']:+.1f} |",
        "",
        "Selection used 2022/23-2023/24 only. 2024/25-2025/26 were untouched for selection.",
        "No automatic production promotion is performed.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    df, features, valid_target = load_dataset()
    specs = candidates()

    dev_frames: dict[str, pd.DataFrame] = {}
    dev_reports: dict[str, dict] = {}
    spec_by_name = {spec.name: spec for spec in specs}

    for spec in specs:
        frame = evaluate(spec, df, features, valid_target, DEV_SEASONS)
        dev_frames[spec.name] = frame
        dev_reports[spec.name] = {
            "family": spec.family,
            "metrics": summarize(frame),
        }

    family_winners: list[str] = []
    for family in sorted({spec.family for spec in specs}):
        family_names = [spec.name for spec in specs if spec.family == family]
        winner = min(family_names, key=lambda name: ranking_key((name, dev_reports[name])))
        family_winners.append(winner)

    family_winners = sorted(family_winners, key=lambda name: ranking_key((name, dev_reports[name])))[:3]
    ensemble_defs: dict[str, tuple[list[str], dict[str, float]]] = {}
    if len(family_winners) >= 2:
        equal = {name: 1.0 / len(family_winners) for name in family_winners}
        ensemble_defs["ensemble_family_equal"] = (family_winners, equal)

        inverse = np.array([1.0 / dev_reports[name]["metrics"]["overall"]["mae"] for name in family_winners])
        inverse = inverse / inverse.sum()
        inverse_weights = {name: float(weight) for name, weight in zip(family_winners, inverse)}
        ensemble_defs["ensemble_family_inverse_mae"] = (family_winners, inverse_weights)

    for ensemble_name, (members, weights) in ensemble_defs.items():
        frame = combine_predictions(dev_frames, members, weights)
        dev_frames[ensemble_name] = frame
        dev_reports[ensemble_name] = {
            "family": "ensemble",
            "members": members,
            "weights": weights,
            "metrics": summarize(frame),
        }

    selected_name = min(dev_reports, key=lambda name: ranking_key((name, dev_reports[name])))

    # Holdout is evaluated only after the development-only selection rule is fixed.
    holdout_needed = {"v17_ridge_a0_3", selected_name}
    if selected_name in ensemble_defs:
        holdout_needed.update(ensemble_defs[selected_name][0])

    holdout_frames: dict[str, pd.DataFrame] = {}
    for name in holdout_needed:
        if name in spec_by_name:
            holdout_frames[name] = evaluate(spec_by_name[name], df, features, valid_target, HOLDOUT_SEASONS)

    if selected_name in ensemble_defs:
        members, weights = ensemble_defs[selected_name]
        holdout_frames[selected_name] = combine_predictions(holdout_frames, members, weights)

    champion_all = evaluate(spec_by_name["v17_ridge_a0_3"], df, features, valid_target, ALL_OOS_SEASONS)
    reproduction = verify_v17_reproduction(champion_all)

    champion_holdout = summarize(holdout_frames["v17_ridge_a0_3"])["overall"]
    selected_holdout = summarize(holdout_frames[selected_name])["overall"]
    mae_delta = champion_holdout["mae"] - selected_holdout["mae"]

    if selected_name == "v17_ridge_a0_3":
        decision = "KEEP_V17_CHAMPION_DEV_SELECTION"
    elif mae_delta > 0 and selected_holdout["wape_pct"] <= champion_holdout["wape_pct"]:
        decision = "CHALLENGER_BEATS_V17_ON_UNTOUCHED_HOLDOUT_MANUAL_REVIEW"
    else:
        decision = "KEEP_V17_CHAMPION_HOLDOUT_NOT_BETTER"

    ranking = sorted(
        [
            {
                "name": name,
                "family": value["family"],
                "mae": value["metrics"]["overall"]["mae"],
                "wape_pct": value["metrics"]["overall"]["wape_pct"],
                "bias": value["metrics"]["overall"]["bias"],
            }
            for name, value in dev_reports.items()
        ],
        key=lambda row: (row["mae"], row["wape_pct"], abs(row["bias"])),
    )

    report = {
        "benchmark_version": "forecast-benchmark-v2-t7",
        "objective": "minimise leakage-safe out-of-sample attendance forecast error",
        "horizon": "T-7",
        "dataset": {
            "history_rows": int(len(df)),
            "development_seasons": DEV_SEASONS,
            "holdout_seasons": HOLDOUT_SEASONS,
            "development_events": int(len(dev_frames["v17_ridge_a0_3"])),
            "holdout_events": int(len(holdout_frames["v17_ridge_a0_3"])),
        },
        "protocol": {
            "training_fold": "prior seasons only",
            "feature_state": "exact recovered point-in-time T-7 semantics",
            "candidate_selection": "development MAE, then WAPE, then absolute bias",
            "holdout_used_for_selection": False,
            "automatic_promotion": False,
        },
        "v17_reproduction": reproduction,
        "development_ranking": ranking,
        "development_details": dev_reports,
        "selected_on_development": selected_name,
        "champion_holdout": champion_holdout,
        "selected_holdout": selected_holdout,
        "holdout_delta_vs_v17_mae": round(float(mae_delta), 4),
        "decision": decision,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.markdown_output:
        write_markdown(report, args.markdown_output)

    print(json.dumps({
        "selected_on_development": selected_name,
        "champion_holdout": champion_holdout,
        "selected_holdout": selected_holdout,
        "holdout_delta_vs_v17_mae": mae_delta,
        "decision": decision,
        "v17_reproduction": reproduction,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
