#!/usr/bin/env python3
"""Exact forensic reconstruction harness for Lech Early Demand Model v1.7 T-7.

Recovered semantics are independently controlled against the preserved v1.6.1
T-7 OOS predictions before v1.7 is evaluated.

Important recovered detail: attendance-history features use the exact T-7
forecast timestamp, while sporting/table state is the state at the *calendar
forecast date* (all completed league matches strictly before that local date).
The gated position features are centered around league mid-table, not raw ranks.
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
RIDGE_ALPHA = 0.3

NUMERIC_FEATURES = [
    "month", "weekday", "kickoff_minutes", "is_weekend", "month_sin", "month_cos",
    "doy_sin", "doy_cos", "kickoff_sin", "kickoff_cos", "is_winter_month",
    "is_summer_month", "target_round_no", "target_season_progress",
    "target_matches_remaining", "rolling_3", "rolling_5", "rolling_10",
    "season_avg_so_far", "recent_attendance_trend", "opponent_draw_ratio",
    "opponent_recent_draw_ratio", "history_n", "season_home_matches_known",
    "lech_pos_gate_10", "opp_pos_gate_10", "pos_gap_gate_10", "pos_gate_active_10",
]

CHECKPOINT_COLUMNS = [
    "season", "match_date", "opponent_key", "lech_position_at_cutoff",
    "opponent_position_at_cutoff", "lech_matches_played_at_cutoff",
    "opponent_matches_played_at_cutoff", "league_team_count",
]


def normalize_local_match_time(values: pd.Series) -> pd.Series:
    return (
        values.astype(str)
        .str.replace("T", " ", regex=False)
        .str.replace(r"[+-]\d{2}:\d{2}$", "", regex=True)
    )


def evidence_key(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["season"].astype(str) + "|" + normalize_local_match_time(frame["match_date"])
        + "|" + frame["opponent_key"].astype(str)
    )


def season_start(season: str) -> pd.Timestamp:
    return pd.Timestamp(f"{str(season).split('/')[0]}-07-01", tz="UTC")


def prepare_dataset(dataset_path: Path, checkpoint_path: Path):
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

    rows = []
    for _, row in df.iterrows():
        state = checkpoint.loc[row["evidence_key"]]

        cutoff = row["dt"] - pd.Timedelta(days=HORIZON_DAYS)
        hist = df[(df["dt"] < cutoff) & valid_target].sort_values("dt")
        attendance = hist["attendance"].astype(float)
        global_mean = float(attendance.mean()) if len(attendance) else np.nan
        same_season = hist[hist["season"] == row["season"]]
        season_avg = float(same_season["attendance"].mean()) if len(same_season) else global_mean
        opponent = hist[hist["opponent_key"] == row["opponent_key"]]
        opponent_mean = float(opponent["attendance"].mean()) if len(opponent) else global_mean
        opponent_recent = float(opponent.tail(3)["attendance"].mean()) if len(opponent) else opponent_mean

        def rolling(n: int) -> float:
            return float(attendance.tail(n).mean()) if len(attendance) else np.nan

        r3, r5, r10 = rolling(3), rolling(5), rolling(10)
        gate = int(
            float(state["lech_matches_played_at_cutoff"]) >= TABLE_GATE_MATCHES
            and float(state["opponent_matches_played_at_cutoff"]) >= TABLE_GATE_MATCHES
        )
        raw_lech_pos = float(state["lech_position_at_cutoff"])
        raw_opp_pos = float(state["opponent_position_at_cutoff"])
        midpoint = (float(state["league_team_count"]) + 1.0) / 2.0
        lech_pos = (midpoint - raw_lech_pos) * gate
        opp_pos = (midpoint - raw_opp_pos) * gate
        pos_gap = (raw_opp_pos - raw_lech_pos) * gate

        rows.append({
            "opponent_key": row["opponent_key"],
            "month": row["month"], "weekday": row["weekday"],
            "kickoff_minutes": row["kickoff_minutes"], "is_weekend": int(row["weekday"] >= 5),
            "month_sin": row["month_sin"], "month_cos": row["month_cos"],
            "doy_sin": row["doy_sin"], "doy_cos": row["doy_cos"],
            "kickoff_sin": row["kickoff_sin"], "kickoff_cos": row["kickoff_cos"],
            "is_winter_month": row["is_winter_month"], "is_summer_month": row["is_summer_month"],
            "target_round_no": row["round_no"], "target_season_progress": row["season_progress"],
            "target_matches_remaining": row["matches_remaining_after"],
            "rolling_3": r3, "rolling_5": r5, "rolling_10": r10,
            "season_avg_so_far": season_avg,
            "recent_attendance_trend": r3 / r10 if r10 and np.isfinite(r10) else np.nan,
            "opponent_draw_ratio": float(np.clip(opponent_mean / global_mean, 0.5, 1.8))
                if global_mean and np.isfinite(global_mean) else np.nan,
            "opponent_recent_draw_ratio": float(np.clip(opponent_recent / global_mean, 0.5, 1.8))
                if global_mean and np.isfinite(global_mean) else np.nan,
            "history_n": len(hist), "season_home_matches_known": len(same_season),
            "lech_pos_gate_10": lech_pos, "opp_pos_gate_10": opp_pos,
            "pos_gap_gate_10": pos_gap, "pos_gate_active_10": gate,
        })

    return df, pd.DataFrame(rows, index=df.index), valid_target


def train_indices(df, valid_target, target_row):
    return df.index[(df["dt"] < season_start(str(target_row["season"]))) & valid_target]


def design_matrix(df, features, train_index, target_index):
    counts = df.loc[train_index, "opponent_key"].value_counts()
    kept = set(counts[counts >= OPPONENT_MIN_HISTORY].index)
    columns = ["opponent_key"] + NUMERIC_FEATURES
    train = features.loc[train_index, columns].copy()
    target = features.loc[[target_index], columns].copy()
    train["opponent_group"] = train["opponent_key"].where(train["opponent_key"].isin(kept), "other")
    target["opponent_group"] = target["opponent_key"].where(target["opponent_key"].isin(kept), "other")
    return train, target


def reconstruct(*, df, features, valid_target, template_model, evidence, residual):
    key_to_index = {key: int(i) for i, key in enumerate(df["evidence_key"])}
    predictions = []
    for row in evidence.itertuples(index=False):
        target_index = key_to_index[row.evidence_key]
        train_index = train_indices(df, valid_target, df.loc[target_index])
        train_x, target_x = design_matrix(df, features, train_index, target_index)
        model = clone(template_model)
        model.named_steps["reg"].set_params(alpha=RIDGE_ALPHA)
        y = df.loc[train_index, "attendance"].astype(float)
        if residual:
            baseline = features.loc[train_index, "season_avg_so_far"].astype(float)
            usable = y.notna() & baseline.notna()
            y_fit = (y.loc[usable] - baseline.loc[usable]).to_numpy()
        else:
            usable = y.notna()
            y_fit = y.loc[usable].to_numpy()
        model.fit(train_x.loc[usable], y_fit)
        prediction = float(model.predict(target_x)[0])
        if residual:
            prediction += float(features.loc[target_index, "season_avg_so_far"])
        predictions.append(prediction)
    return np.asarray(predictions)


def compare(original, reconstructed):
    delta = reconstructed - original
    return {
        "mean_absolute_prediction_difference": float(np.mean(np.abs(delta))),
        "max_absolute_prediction_difference": float(np.max(np.abs(delta))),
        "mean_prediction_difference": float(np.mean(delta)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--checkpoint-state", required=True, type=Path)
    parser.add_argument("--v161-model", required=True, type=Path)
    parser.add_argument("--v161-oos", required=True, type=Path)
    parser.add_argument("--v17-oos", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    args = parser.parse_args()

    df, features, valid_target = prepare_dataset(args.dataset, args.checkpoint_state)
    template = joblib.load(args.v161_model)
    v161 = pd.read_csv(args.v161_oos); v161["evidence_key"] = evidence_key(v161)
    v17 = pd.read_csv(args.v17_oos); v17["evidence_key"] = evidence_key(v17)

    control = reconstruct(df=df, features=features, valid_target=valid_target,
                          template_model=template, evidence=v161, residual=False)
    control_diff = compare(v161["pred"].astype(float).to_numpy(), control)
    if control_diff["max_absolute_prediction_difference"] > args.tolerance:
        raise RuntimeError(f"v1.6.1 T-7 control failed: {control_diff}")

    raw = reconstruct(df=df, features=features, valid_target=valid_target,
                      template_model=template, evidence=v17, residual=True)
    final = np.clip(raw, 0.0, float(CAPACITY))
    raw_diff = compare(v17["pred"].astype(float).to_numpy(), raw)
    final_diff = compare(v17["pred_final"].astype(float).to_numpy(), final)
    if raw_diff["max_absolute_prediction_difference"] > args.tolerance:
        raise RuntimeError(f"v1.7 T-7 raw reconstruction failed: {raw_diff}")
    if final_diff["max_absolute_prediction_difference"] > args.tolerance:
        raise RuntimeError(f"v1.7 T-7 final reconstruction failed: {final_diff}")

    actual = v17["attendance"].astype(float).to_numpy()
    report = {
        "reconstruction_version": "v17-t7-exact-v2",
        "status": "runtime_reconstructed_exactly",
        "protocol": {
            "horizon_days": 7,
            "attendance_state": "exact_timestamp_target_minus_7_days",
            "table_state": "completed_league_matches_strictly_before_local_calendar_T7_date",
            "table_position_transform": "((league_team_count + 1) / 2) - raw_position",
            "table_gate_matches_both_clubs": 10,
            "training_fold": "prior_seasons_only",
            "opponent_frequency_gate": 3,
            "recency_weighting": False,
            "ridge_alpha": RIDGE_ALPHA,
            "v17_target": "attendance_minus_t7_season_avg_so_far",
            "capacity_cap": CAPACITY,
        },
        "v161_control": control_diff,
        "v17_raw_vs_original": raw_diff,
        "v17_final_vs_original": final_diff,
        "reconstructed_final_mae": float(np.mean(np.abs(final - actual))),
        "promotion_allowed_for_t7_shadow": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
