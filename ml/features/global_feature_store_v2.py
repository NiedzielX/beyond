#!/usr/bin/env python3
"""Canonical point-in-time feature builder for Beyond multi-club forecasting.

The builder consumes the validated historical multi-club ground truth and emits
one feature snapshot per match and forecast horizon. Every feature is computed
strictly from matches completed before `as_of_at`.

This module deliberately contains no model code. Training and inference should
consume these same feature definitions.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from ml.data.build_historical_multiclub import (
    SOURCE_COMMIT,
    SOURCE_REPO,
    discover_match_logs,
    normalize_home_rows,
    read_log,
)

DATASET_VERSION = "historical-multiclub-2025-26-v1"
FEATURE_SET_VERSION = "global-pit-v2.0"
HORIZONS_DAYS = {
    "T-30d": 30,
    "T-14d": 14,
    "T-7d": 7,
    "T-3d": 3,
    "T-1d": 1,
}
WARSAW_TZ = "Europe/Warsaw"
MATCH_COMPLETION_BUFFER_HOURS = 3


def load_ground_truth() -> pd.DataFrame:
    """Rebuild the pinned historical ground truth from the public Git source."""
    session = requests.Session()
    paths = discover_match_logs(session)
    frames = [normalize_home_rows(read_log(session, path), path) for path in paths]
    data = pd.concat(frames, ignore_index=True)
    data = data.sort_values(["date", "kickoff_time_local", "home_club_key"]).reset_index(drop=True)

    local = pd.to_datetime(
        data["date"].astype(str) + " " + data["kickoff_time_local"].astype(str),
        errors="raise",
    ).dt.tz_localize(WARSAW_TZ, ambiguous="raise", nonexistent="raise")
    data["kickoff_at"] = local.dt.tz_convert("UTC")
    data["completed_at"] = data["kickoff_at"] + pd.Timedelta(hours=MATCH_COMPLETION_BUFFER_HOURS)
    return data


def points_for(gf: int, ga: int) -> int:
    if gf > ga:
        return 3
    if gf == ga:
        return 1
    return 0


def build_team_match_log(prior: pd.DataFrame, club: str) -> pd.DataFrame:
    home = prior[prior["home_club_key"] == club].copy()
    away = prior[prior["away_club_key"] == club].copy()

    home_rows = pd.DataFrame({
        "kickoff_at": home["kickoff_at"],
        "gf": home["home_goals"].astype(float),
        "ga": home["away_goals"].astype(float),
    })
    away_rows = pd.DataFrame({
        "kickoff_at": away["kickoff_at"],
        "gf": away["away_goals"].astype(float),
        "ga": away["home_goals"].astype(float),
    })
    out = pd.concat([home_rows, away_rows], ignore_index=True).sort_values("kickoff_at")
    if out.empty:
        out["points"] = pd.Series(dtype=float)
        return out
    out["points"] = [points_for(int(gf), int(ga)) for gf, ga in zip(out["gf"], out["ga"])]
    return out.reset_index(drop=True)


def standings(prior: pd.DataFrame) -> dict[str, dict[str, float]]:
    clubs = sorted(set(prior["home_club_key"]).union(prior["away_club_key"]))
    rows = []
    for club in clubs:
        log = build_team_match_log(prior, club)
        played = len(log)
        pts = float(log["points"].sum()) if played else 0.0
        gf = float(log["gf"].sum()) if played else 0.0
        ga = float(log["ga"].sum()) if played else 0.0
        rows.append({
            "club": club,
            "played": played,
            "points": pts,
            "gf": gf,
            "ga": ga,
            "gd": gf - ga,
            "ppg": pts / played if played else np.nan,
        })
    table = pd.DataFrame(rows)
    if table.empty:
        return {}
    table = table.sort_values(
        ["points", "gd", "gf", "club"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    table["position"] = np.arange(1, len(table) + 1)
    return {row["club"]: row for row in table.to_dict(orient="records")}


def home_attendance_state(prior: pd.DataFrame, club: str) -> dict[str, float]:
    hist = prior[prior["home_club_key"] == club].sort_values("kickoff_at")
    values = hist["attendance"].dropna().astype(float)
    if values.empty:
        return {
            "home_history_n": 0,
            "home_attendance_mean": np.nan,
            "home_attendance_last": np.nan,
            "home_attendance_rolling3": np.nan,
            "home_attendance_rolling5": np.nan,
            "home_attendance_std": np.nan,
            "home_attendance_trend3_vs_mean": np.nan,
            "days_since_last_home": np.nan,
        }
    mean = float(values.mean())
    rolling3 = float(values.tail(3).mean())
    rolling5 = float(values.tail(5).mean())
    last_kickoff = hist[hist["attendance"].notna()]["kickoff_at"].iloc[-1]
    return {
        "home_history_n": int(len(values)),
        "home_attendance_mean": mean,
        "home_attendance_last": float(values.iloc[-1]),
        "home_attendance_rolling3": rolling3,
        "home_attendance_rolling5": rolling5,
        "home_attendance_std": float(values.std(ddof=0)) if len(values) > 1 else 0.0,
        "home_attendance_trend3_vs_mean": rolling3 / mean if mean else np.nan,
        "last_home_kickoff": last_kickoff,
    }


def prior_home_baselines(data: pd.DataFrame) -> pd.Series:
    """Home-club expanding mean available immediately before each historical match."""
    baseline = pd.Series(index=data.index, dtype=float)
    histories: dict[str, list[float]] = defaultdict(list)
    for idx, row in data.sort_values("kickoff_at").iterrows():
        club = row["home_club_key"]
        prior = histories[club]
        baseline.loc[idx] = float(np.mean(prior)) if prior else np.nan
        if pd.notna(row["attendance"]):
            prior.append(float(row["attendance"]))
    return baseline


def opponent_draw_state(prior: pd.DataFrame, opponent: str) -> dict[str, float]:
    hist = prior[prior["away_club_key"] == opponent].copy()
    ratios = hist["attendance_ratio_to_home_prior"].dropna().astype(float)
    raw = hist["attendance"].dropna().astype(float)
    return {
        "opponent_draw_n": int(len(ratios)),
        "opponent_draw_ratio_mean": float(ratios.mean()) if len(ratios) else np.nan,
        "opponent_draw_ratio_recent3": float(ratios.tail(3).mean()) if len(ratios) else np.nan,
        "opponent_raw_attendance_mean": float(raw.mean()) if len(raw) else np.nan,
    }


def team_state(prior: pd.DataFrame, club: str, as_of_at: pd.Timestamp) -> dict[str, float]:
    log = build_team_match_log(prior, club)
    if log.empty:
        return {
            "matches_played": 0,
            "points": 0.0,
            "ppg": np.nan,
            "goal_diff_per_game": np.nan,
            "form5_points": np.nan,
            "form5_goal_diff": np.nan,
            "days_since_last_match": np.nan,
            "matches_last_14d": 0,
        }
    played = len(log)
    last5 = log.tail(5)
    last_kickoff = log["kickoff_at"].iloc[-1]
    recent_cutoff = as_of_at - pd.Timedelta(days=14)
    return {
        "matches_played": played,
        "points": float(log["points"].sum()),
        "ppg": float(log["points"].mean()),
        "goal_diff_per_game": float((log["gf"] - log["ga"]).mean()),
        "form5_points": float(last5["points"].sum()),
        "form5_goal_diff": float((last5["gf"] - last5["ga"]).sum()),
        "days_since_last_match": float((as_of_at - last_kickoff).total_seconds() / 86400.0),
        "matches_last_14d": int((log["kickoff_at"] >= recent_cutoff).sum()),
    }


def target_calendar_features(row: pd.Series) -> dict[str, float]:
    local = row["kickoff_at"].tz_convert(WARSAW_TZ)
    month = int(local.month)
    weekday = int(local.weekday())
    kickoff_minutes = int(local.hour * 60 + local.minute)
    doy = int(local.dayofyear)
    return {
        "round_no": int(row["round"]),
        "season_progress": (int(row["round"]) - 1) / 33.0,
        "month": month,
        "weekday": weekday,
        "kickoff_minutes": kickoff_minutes,
        "is_weekend": int(weekday >= 5),
        "month_sin": float(np.sin(2 * np.pi * month / 12.0)),
        "month_cos": float(np.cos(2 * np.pi * month / 12.0)),
        "doy_sin": float(np.sin(2 * np.pi * doy / 365.25)),
        "doy_cos": float(np.cos(2 * np.pi * doy / 365.25)),
        "kickoff_sin": float(np.sin(2 * np.pi * kickoff_minutes / 1440.0)),
        "kickoff_cos": float(np.cos(2 * np.pi * kickoff_minutes / 1440.0)),
    }


def snapshot_for(data: pd.DataFrame, row: pd.Series, horizon: str, days: int) -> dict:
    as_of_at = row["kickoff_at"] - pd.Timedelta(days=days)
    prior = data[data["completed_at"] < as_of_at].copy()
    home = row["home_club_key"]
    away = row["away_club_key"]

    features: dict[str, float | int | str | None] = {}
    features.update(target_calendar_features(row))

    attendance = home_attendance_state(prior, home)
    last_home = attendance.pop("last_home_kickoff", None)
    features.update(attendance)
    features["days_since_last_home"] = (
        float((as_of_at - last_home).total_seconds() / 86400.0)
        if last_home is not None else np.nan
    )
    features.update(opponent_draw_state(prior, away))

    home_state = team_state(prior, home, as_of_at)
    away_state = team_state(prior, away, as_of_at)
    table = standings(prior)
    htable = table.get(home, {})
    atable = table.get(away, {})

    for prefix, state in (("home", home_state), ("away", away_state)):
        for key, value in state.items():
            features[f"{prefix}_{key}"] = value

    features["home_position"] = htable.get("position", np.nan)
    features["away_position"] = atable.get("position", np.nan)
    features["position_gap"] = (
        float(features["away_position"] - features["home_position"])
        if pd.notna(features["home_position"]) and pd.notna(features["away_position"])
        else np.nan
    )
    features["ppg_gap"] = (
        float(home_state["ppg"] - away_state["ppg"])
        if pd.notna(home_state["ppg"]) and pd.notna(away_state["ppg"])
        else np.nan
    )
    features["form5_points_gap"] = (
        float(home_state["form5_points"] - away_state["form5_points"])
        if pd.notna(home_state["form5_points"]) and pd.notna(away_state["form5_points"])
        else np.nan
    )
    features["goal_diff_per_game_gap"] = (
        float(home_state["goal_diff_per_game"] - away_state["goal_diff_per_game"])
        if pd.notna(home_state["goal_diff_per_game"]) and pd.notna(away_state["goal_diff_per_game"])
        else np.nan
    )

    # JSON-safe conversion is done by the caller; the flat CSV keeps NaN for modelling.
    return {
        "dataset_version": DATASET_VERSION,
        "feature_set_version": FEATURE_SET_VERSION,
        "match_key": row["match_key"],
        "season": row["season"],
        "horizon": horizon,
        "as_of_at": as_of_at.isoformat(),
        "kickoff_at": row["kickoff_at"].isoformat(),
        "home_club_key": home,
        "away_club_key": away,
        "target_attendance": int(row["attendance"]),
        "point_in_time_validated": True,
        **features,
    }


def build_feature_store(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy().sort_values("kickoff_at").reset_index(drop=True)
    data["home_prior_mean_at_match"] = prior_home_baselines(data)
    data["attendance_ratio_to_home_prior"] = (
        data["attendance"].astype(float) / data["home_prior_mean_at_match"].replace(0, np.nan)
    )

    rows = []
    for _, row in data.iterrows():
        for horizon, days in HORIZONS_DAYS.items():
            rows.append(snapshot_for(data, row, horizon, days))
    return pd.DataFrame(rows).sort_values(["kickoff_at", "horizon", "match_key"]).reset_index(drop=True)


def quality_report(store: pd.DataFrame) -> dict:
    failures: list[str] = []
    expected = 306 * len(HORIZONS_DAYS)
    if len(store) != expected:
        failures.append(f"expected {expected} snapshots, got {len(store)}")
    duplicates = int(store.duplicated(["dataset_version", "match_key", "horizon", "feature_set_version"]).sum())
    if duplicates:
        failures.append(f"duplicate snapshot keys: {duplicates}")
    invalid_time = int((pd.to_datetime(store["as_of_at"], utc=True) >= pd.to_datetime(store["kickoff_at"], utc=True)).sum())
    if invalid_time:
        failures.append(f"snapshots with as_of_at >= kickoff_at: {invalid_time}")
    by_horizon = {
        horizon: {
            "rows": int(len(group)),
            "with_3_home_history": int((group["home_history_n"] >= 3).sum()),
            "with_opponent_draw": int((group["opponent_draw_n"] >= 1).sum()),
        }
        for horizon, group in store.groupby("horizon", sort=True)
    }
    return {
        "dataset_version": DATASET_VERSION,
        "feature_set_version": FEATURE_SET_VERSION,
        "source_repo": SOURCE_REPO,
        "source_commit": SOURCE_COMMIT,
        "rows": int(len(store)),
        "matches": int(store["match_key"].nunique()),
        "horizons": list(HORIZONS_DAYS),
        "by_horizon": by_horizon,
        "duplicate_keys": duplicates,
        "invalid_time_rows": invalid_time,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    ground_truth = load_ground_truth()
    store = build_feature_store(ground_truth)
    report = quality_report(store)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    store.to_csv(args.output, index=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit("Feature Store v2 quality gate failed")


if __name__ == "__main__":
    main()
