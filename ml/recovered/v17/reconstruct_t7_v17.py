#!/usr/bin/env python3
"""Forensic reconstruction harness for Lech Early Demand Model v1.7 T-7.

T-7 cannot be reconstructed honestly from the stored pre-kickoff league-table
columns. The original v1.4/v1.6.1 architecture explicitly rebuilt sporting
state as of target kickoff minus seven days and activated table-position
features only after both teams had played at least ten league matches.

This harness therefore REQUIRES an external checkpoint-state CSV generated from
completed league results available at each exact T-7 cutoff. It first reproduces
the preserved v1.6.1 direct-Ridge OOS predictions. Only if that control is within
tolerance does it evaluate candidate v1.7 residual specifications.

Expected checkpoint-state CSV columns:
- season
- match_date
- opponent_key
- lech_position_at_cutoff
- opponent_position_at_cutoff
- lech_matches_played_at_cutoff
- opponent_matches_played_at_cutoff

The input may contain more columns. Values must describe information available
at target kickoff minus 7 days, never kickoff-time state.
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
HORIZON_DAYS = 7
OPPONENT_MIN_HISTORY = 3
TABLE_GATE_MATCHES = 10

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
    "lech_pos_gate_10",
    "opp_pos_gate_10",
    "pos_gap_gate_10",
    "pos_gate_active_10",
]

CHECKPOINT_COLUMNS = [
    "season",
    "match_date",
    "opponent_key",
    "lech_position_at_cutoff",
    "opponent_position_at_cutoff",
    "lech_matches_played_at_cutoff",
    "opponent_matches_played_at_cutoff",
]


def normalize_local_match_time(values: pd.Series) -> pd.Series:
    return (
        values.astype(str)
        .str.replace("T", " ", regex=False)
        .str.replace(r"[+-]\d{2}:\d{2}$", "", regex=True)
    )


def evidence_key(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["season"].astype(str)
        + "|"
        + normalize_local_match_time(frame["match_date"])
        + "|"
        + frame["opponent_key"].astype(str)
    )


def season_start(season: str) -> pd.Timestamp:
    return pd.Timestamp(f"{str(season).split('/')[0]}-07-01", tz="UTC")


def prepare_dataset(
    dataset_path: Path,
    checkpoint_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    df = pd.read_csv(dataset_path)
    df["dt"] = pd.to_datetime(df["match_date"], utc=True)
    df = df.sort_values("dt").reset_index(drop=True)
    df["evidence_key"] = evidence_key(df)

    checkpoint = pd.read_csv(checkpoint_path)
    missing = [c for c in CHECKPOINT_COLUMNS if c not in checkpoint.columns]
    if missing:
        raise RuntimeError(f"Checkpoint-state CSV missing columns: {missing}")
    checkpoint["evidence_key"] = evidence_key(checkpoint)
    if checkpoint["evidence_key"].duplicated().any():
        raise RuntimeError("Checkpoint-state CSV contains duplicate match keys")
    checkpoint = checkpoint.set_index("evidence_key")

    constrained = df["capacity_constrained_for_model"].fillna(False).astype(bool)
    valid_target = (~constrained) & df["attendance"].notna()

    features: list[dict] = []
    for _, row in df.iterrows():
        key = row["evidence_key"]
        if key not in checkpoint.index:
            raise RuntimeError(
                f"Missing exact T-7 checkpoint state for {key}. "
                "Do not substitute pre-kickoff table state."
            )
        state = checkpoint.loc[key]

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
        gate = int(
            float(state["lech_matches_played_at_cutoff"]) >= TABLE_GATE_MATCHES
            and float(state["opponent_matches_played_at_cutoff"]) >= TABLE_GATE_MATCHES
        )
        lech_pos = float(state["lech_position_at_cutoff"]) if gate else 0.0
        opp_pos = float(state["opponent_position_at_cutoff"]) if gate else 0.0

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
                "lech_pos_gate_10": lech_pos,
                "opp_pos_gate_10": opp_pos,
                "pos_gap_gate_10": opp_pos - lech_pos if gate else 0.0,
                "pos_gate_active_10": gate,
            }
        )

    return df, pd.DataFrame(features, index=df.index), valid_target


def train_indices(
    df: pd.DataFrame,
    valid_target: pd.Series,
    target_row: pd.Series,
) -> pd.Index:
    # v1.6.1 control architecture is season-block walk-forward.
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
    columns = ["opponent_key"] + NUMERIC_FEATURES
    train = features.loc[train_index, columns].copy()
    target = features.loc[[target_index], columns].copy()
    train["opponent_group"] = train["opponent_key"].where(
        train["opponent_key"].isin(kept), "other"
    )
    target["opponent_group"] = target["opponent_key"].where(
        target["opponent_key"].isin(kept), "other"
    )
    return train, target


def reconstruct(
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
        y = df.loc[train_index, "attendance"].astype(float)

        if target_mode == "direct":
            usable = y.notna()
            y_fit = y.loc[usable].to_numpy()
        elif target_mode == "season_residual":
            baseline = features.loc[train_index, "season_avg_so_far"].astype(float)
            usable = y.notna() & baseline.notna()
            y_fit = (y.loc[usable] - baseline.loc[usable]).to_numpy()
        else:
            raise ValueError(target_mode)

        model.fit(train_x.loc[usable], y_fit)
        prediction = float(model.predict(target_x)[0])
        if target_mode == "season_residual":
            prediction += float(features.loc[target_index, "season_avg_so_far"])
        predictions.append(prediction)

    return np.asarray(predictions)


def compare(original: np.ndarray, reconstructed: np.ndarray) -> dict:
    delta = reconstructed - original
    return {
        "mean_absolute_prediction_difference": round(float(np.mean(np.abs(delta))), 6),
        "max_absolute_prediction_difference": round(float(np.max(np.abs(delta))), 6),
        "mean_prediction_difference": round(float(np.mean(delta)), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--checkpoint-state", required=True, type=Path)
    parser.add_argument("--v161-model", required=True, type=Path)
    parser.add_argument("--v161-oos", required=True, type=Path)
    parser.add_argument("--v17-oos", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--control-max-mean-diff", type=float, default=10.0)
    args = parser.parse_args()

    df, features, valid_target = prepare_dataset(args.dataset, args.checkpoint_state)
    template = joblib.load(args.v161_model)
    v161 = pd.read_csv(args.v161_oos)
    v17 = pd.read_csv(args.v17_oos)
    v161["evidence_key"] = evidence_key(v161)
    v17["evidence_key"] = evidence_key(v17)

    control = reconstruct(
        df=df,
        features=features,
        valid_target=valid_target,
        template_model=template,
        evidence=v161,
        target_mode="direct",
    )
    control_diff = compare(v161["pred"].astype(float).to_numpy(), control)
    if control_diff["mean_absolute_prediction_difference"] > args.control_max_mean_diff:
        raise RuntimeError(
            "v1.6.1 T-7 forensic control failed. Exact checkpoint-state recovery "
            "must be fixed before testing v1.7 residual inference. "
            f"Mean prediction difference={control_diff['mean_absolute_prediction_difference']}"
        )

    candidate = reconstruct(
        df=df,
        features=features,
        valid_target=valid_target,
        template_model=template,
        evidence=v17,
        target_mode="season_residual",
    )
    candidate_final = np.clip(candidate, 0.0, float(CAPACITY))
    original_final = v17["pred_final"].astype(float).to_numpy()

    report = {
        "reconstruction_version": "v17-t7-forensic-v1",
        "protocol": {
            "horizon_days": HORIZON_DAYS,
            "training_fold": "prior_seasons_only",
            "opponent_frequency_gate": OPPONENT_MIN_HISTORY,
            "table_gate_matches": TABLE_GATE_MATCHES,
            "table_state": "exact_as_of_target_minus_7_days",
            "recency_weighting": False,
            "ridge_alpha": 0.3,
            "candidate_target": "attendance_minus_t7_season_avg_so_far",
            "capacity_cap": CAPACITY,
        },
        "v161_control": control_diff,
        "v17_candidate_vs_original_raw": compare(
            v17["pred"].astype(float).to_numpy(), candidate
        ),
        "v17_candidate_vs_original_final": compare(original_final, candidate_final),
        "promotion_allowed": False,
        "promotion_condition": "Original raw/final T-7 OOS predictions must reproduce to numerical tolerance.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
