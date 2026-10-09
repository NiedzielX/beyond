#!/usr/bin/env python3
"""Forensic reconstruction harness for Lech Early Demand Model v1.7 T-30.

The original v1.7 archive preserves OOS predictions and the model design, but
not its training source/model binary. This harness makes reconstruction
falsifiable instead of relying on prose or memory.

Required external evidence files:
- enriched historical dataset from the preserved v1.2 artifact;
- v1.6.1 fitted T-30 joblib (used only as pipeline/template evidence);
- preserved v1.6.1 T-30 OOS predictions;
- preserved v1.7 T-30 OOS predictions.

The harness first reconstructs v1.6.1. If that control cannot reproduce the
preserved v1.6.1 predictions to a tight tolerance, no claim about v1.7 is valid.
It then evaluates the currently best-supported v1.7 raw residual specification
and reports its gap to the original v1.7 `pred` column.

It NEVER silently promotes the reconstruction.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone

CAPACITY = 43_269
HORIZON_DAYS = 30
OPPONENT_MIN_HISTORY = 3
RECENCY_HALF_LIFE_YEARS = 3.0
ONLINE_CORRECTION_K = 3.0

NUMERIC_FEATURES = [
    "month",
    "weekday",
    "kickoff_minutes",
    "is_weekend",
    "month_sin",
    "month_cos",
    "doy_sin",
    "doy_cos",
    "kickoff_sin",
    "kickoff_cos",
    "is_winter_month",
    "is_summer_month",
    "target_round_no",
    "target_season_progress",
    "target_matches_remaining",
    "rolling_3",
    "rolling_5",
    "rolling_10",
    "season_avg_so_far",
    "recent_attendance_trend",
    "opponent_draw_ratio",
    "opponent_recent_draw_ratio",
    "history_n",
    "season_home_matches_known",
]


def local_match_key(frame: pd.DataFrame) -> pd.Series:
    local = (
        frame["match_date"]
        .astype(str)
        .str.replace("T", " ", regex=False)
        .str.replace(r"[+-]\d{2}:\d{2}$", "", regex=True)
    )
    return frame["season"].astype(str) + "|" + local + "|" + frame["opponent_key"].astype(str)


def evidence_key(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["season"].astype(str)
        + "|"
        + frame["match_date"].astype(str)
        + "|"
        + frame["opponent_key"].astype(str)
    )


def prepare_dataset(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    df = pd.read_csv(path)
    df["dt"] = pd.to_datetime(df["match_date"], utc=True)
    df = df.sort_values("dt").reset_index(drop=True)

    constrained = df["capacity_constrained_for_model"].fillna(False).astype(bool)
    valid_target = (~constrained) & df["attendance"].notna()

    features: list[dict] = []
    for _, row in df.iterrows():
        cutoff = row["dt"] - pd.Timedelta(days=HORIZON_DAYS)
        hist = df[(df["dt"] < cutoff) & valid_target].sort_values("dt")
        attendance = hist["attendance"].astype(float)
        global_mean = float(attendance.mean()) if len(attendance) else np.nan

        same_season = hist[hist["season"] == row["season"]]
        season_avg = (
            float(same_season["attendance"].mean()) if len(same_season) else global_mean
        )

        opponent = hist[hist["opponent_key"] == row["opponent_key"]]
        opponent_mean = (
            float(opponent["attendance"].mean()) if len(opponent) else global_mean
        )
        opponent_recent = (
            float(opponent.tail(3)["attendance"].mean()) if len(opponent) else opponent_mean
        )

        def rolling(n: int) -> float:
            return float(attendance.tail(n).mean()) if len(attendance) else np.nan

        r3, r5, r10 = rolling(3), rolling(5), rolling(10)
        features.append(
            {
                "opponent_key": row["opponent_key"],
                "month": row["month"],
                "weekday": row["weekday"],
                "kickoff_minutes": row["kickoff_minutes"],
                "is_weekend": int(row["weekday"] >= 5),
                "month_sin": row["month_sin"],
                "month_cos": row["month_cos"],
                "doy_sin": row["doy_sin"],
                "doy_cos": row["doy_cos"],
                "kickoff_sin": row["kickoff_sin"],
                "kickoff_cos": row["kickoff_cos"],
                "is_winter_month": row["is_winter_month"],
                "is_summer_month": row["is_summer_month"],
                "target_round_no": row["round_no"],
                "target_season_progress": row["season_progress"],
                # Recovered control: v1.6.1 uses matches_remaining_after.
                "target_matches_remaining": row["matches_remaining_after"],
                "rolling_3": r3,
                "rolling_5": r5,
                "rolling_10": r10,
                "season_avg_so_far": season_avg,
                "recent_attendance_trend": r3 / r10 if r10 and np.isfinite(r10) else np.nan,
                "opponent_draw_ratio": (
                    float(np.clip(opponent_mean / global_mean, 0.5, 1.8))
                    if global_mean and np.isfinite(global_mean)
                    else np.nan
                ),
                "opponent_recent_draw_ratio": (
                    float(np.clip(opponent_recent / global_mean, 0.5, 1.8))
                    if global_mean and np.isfinite(global_mean)
                    else np.nan
                ),
                "history_n": len(hist),
                "season_home_matches_known": len(same_season),
                "cutoff": cutoff,
            }
        )

    feature_frame = pd.DataFrame(features, index=df.index)
    missing = [name for name in NUMERIC_FEATURES if name not in feature_frame]
    if missing:
        raise RuntimeError(f"Missing reconstructed features: {missing}")

    df["evidence_key"] = local_match_key(df)
    return df, feature_frame, valid_target


def season_start(season: str) -> pd.Timestamp:
    return pd.Timestamp(f"{str(season).split('/')[0]}-07-01", tz="UTC")


def recency_weights(df: pd.DataFrame, train_index: pd.Index) -> np.ndarray:
    # Recovered from the fitted v1.6.1 binary: three-year half-life and the most
    # recent training match receives weight 1. Global rescaling would change the
    # effective Ridge alpha, so this reference point is material.
    reference = df.loc[train_index, "dt"].max()
    age_days = (reference - df.loc[train_index, "dt"]).dt.total_seconds() / 86400.0
    return np.power(0.5, age_days / (365.25 * RECENCY_HALF_LIFE_YEARS)).to_numpy()


def train_indices(df: pd.DataFrame, valid_target: pd.Series, target_row: pd.Series) -> pd.Index:
    # Exact v1.6.1 control recovery: model parameters are trained on completed
    # prior seasons only. Same-season observations may update target features at
    # the forecast checkpoint, but they do not enter that season's Ridge fit.
    mask = (df["dt"] < season_start(str(target_row["season"]))) & valid_target
    return df.index[mask]


def design_matrix(
    df: pd.DataFrame,
    features: pd.DataFrame,
    train_index: pd.Index,
    target_index: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    counts = df.loc[train_index, "opponent_key"].value_counts()
    kept = set(counts[counts >= OPPONENT_MIN_HISTORY].index)

    cols = ["opponent_key"] + NUMERIC_FEATURES
    train = features.loc[train_index, cols].copy()
    target = features.loc[[target_index], cols].copy()
    train["opponent_group"] = train["opponent_key"].where(
        train["opponent_key"].isin(kept), "other"
    )
    target["opponent_group"] = target["opponent_key"].where(
        target["opponent_key"].isin(kept), "other"
    )
    return train, target


def reconstruct_predictions(
    *,
    df: pd.DataFrame,
    features: pd.DataFrame,
    valid_target: pd.Series,
    template_model,
    evidence: pd.DataFrame,
    target_mode: str,
) -> np.ndarray:
    key_to_index = {key: int(i) for i, key in enumerate(df["evidence_key"])}
    predictions: list[float] = []

    for row in evidence.itertuples(index=False):
        target_index = key_to_index[row.evidence_key]
        target_row = df.loc[target_index]
        train_index = train_indices(df, valid_target, target_row)
        train_x, target_x = design_matrix(df, features, train_index, target_index)

        model = clone(template_model)
        model.named_steps["reg"].set_params(alpha=0.3)

        y = df.loc[train_index, "attendance"].astype(float).to_numpy()
        if target_mode == "season_residual":
            baseline = features.loc[train_index, "season_avg_so_far"].astype(float).to_numpy()
            y = y - baseline
        elif target_mode != "direct":
            raise ValueError(target_mode)

        model.fit(
            train_x,
            y,
            reg__sample_weight=recency_weights(df, train_index),
        )
        prediction = float(model.predict(target_x)[0])
        if target_mode == "season_residual":
            prediction += float(features.loc[target_index, "season_avg_so_far"])
        predictions.append(prediction)

    return np.asarray(predictions)


def apply_exact_online_correction(evidence: pd.DataFrame, raw: np.ndarray) -> np.ndarray:
    final: list[float] = []
    previous_raw_residuals: dict[str, list[float]] = {}
    for idx, row in enumerate(evidence.itertuples(index=False)):
        season = str(row.season)
        history = previous_raw_residuals.setdefault(season, [])
        n = len(history)
        correction = float(np.mean(history) * n / (n + ONLINE_CORRECTION_K)) if n else 0.0
        corrected = raw[idx] + correction
        final.append(min(float(CAPACITY), max(0.0, corrected)))
        history.append(float(row.attendance) - raw[idx])
    return np.asarray(final)


def comparison(actual: np.ndarray, reconstructed: np.ndarray) -> dict:
    delta = reconstructed - actual
    return {
        "mean_absolute_prediction_difference": round(float(np.mean(np.abs(delta))), 6),
        "max_absolute_prediction_difference": round(float(np.max(np.abs(delta))), 6),
        "mean_prediction_difference": round(float(np.mean(delta)), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--v161-model", required=True, type=Path)
    parser.add_argument("--v161-oos", required=True, type=Path)
    parser.add_argument("--v17-oos", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--control-max-mean-diff", type=float, default=10.0)
    args = parser.parse_args()

    df, features, valid_target = prepare_dataset(args.dataset)
    template = joblib.load(args.v161_model)

    v161 = pd.read_csv(args.v161_oos)
    v161["evidence_key"] = evidence_key(v161)
    v17 = pd.read_csv(args.v17_oos)
    v17["evidence_key"] = evidence_key(v17)

    if len(v161) != 68 or len(v17) != 68:
        raise RuntimeError("Expected 68 preserved OOS rows for both v1.6.1 and v1.7")

    control = reconstruct_predictions(
        df=df,
        features=features,
        valid_target=valid_target,
        template_model=template,
        evidence=v161,
        target_mode="direct",
    )
    control_diff = comparison(v161["pred"].astype(float).to_numpy(), control)

    if control_diff["mean_absolute_prediction_difference"] > args.control_max_mean_diff:
        raise RuntimeError(
            "v1.6.1 forensic control failed: "
            f"mean prediction difference={control_diff['mean_absolute_prediction_difference']}"
        )

    raw_candidate = reconstruct_predictions(
        df=df,
        features=features,
        valid_target=valid_target,
        template_model=template,
        evidence=v17,
        target_mode="season_residual",
    )
    raw_diff = comparison(v17["pred"].astype(float).to_numpy(), raw_candidate)

    final_candidate = apply_exact_online_correction(v17, raw_candidate)
    final_diff = comparison(v17["pred_final"].astype(float).to_numpy(), final_candidate)

    actual = v17["attendance"].astype(float).to_numpy()
    report = {
        "reconstruction_version": "v17-t30-forensic-v1",
        "status": "raw_residual_spec_not_exact",
        "protocol": {
            "horizon_days": HORIZON_DAYS,
            "training_fold": "prior_seasons_only",
            "target_features": "as_of_target_kickoff_minus_30_days",
            "opponent_frequency_gate": OPPONENT_MIN_HISTORY,
            "recency_half_life_years": RECENCY_HALF_LIFE_YEARS,
            "recency_reference": "latest_training_match_weight_1",
            "ridge_alpha": 0.3,
            "candidate_target": "attendance_minus_t30_season_avg_so_far",
            "online_correction": "mean(previous raw residuals actual-pred) * n/(n+3)",
            "capacity_cap": CAPACITY,
        },
        "v161_control": control_diff,
        "v17_raw_candidate_vs_original": raw_diff,
        "v17_final_candidate_vs_original": final_diff,
        "candidate_accuracy": {
            "raw_mae": round(float(np.mean(np.abs(raw_candidate - actual))), 3),
            "final_mae": round(float(np.mean(np.abs(final_candidate - actual))), 3),
        },
        "original_v17_accuracy": {
            "raw_mae": round(float(np.mean(np.abs(v17["pred"].astype(float).to_numpy() - actual))), 3),
            "final_mae": round(float(np.mean(np.abs(v17["pred_final"].astype(float).to_numpy() - actual))), 3),
        },
        "promotion_allowed": False,
        "next_condition": "Do not mark runtime-reproducible until raw v1.7 OOS predictions match to numerical tolerance.",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
