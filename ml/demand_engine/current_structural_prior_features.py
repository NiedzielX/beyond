"""Point-in-time current-event feature builder for Structural Prior Runtime v1.

This module converts canonical historical attendance, current-season verified
attendance observations, and precomputed point-in-time sporting state into the
same feature-row contract used by ``structural_prior_feature_store_v1.py``.

It is intentionally pure: it does not fetch data or write forecasts. Callers
must provide inputs that were available at or before the target horizon cutoff.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

from ml.features.structural_prior_feature_store_v1 import (
    FEATURE_SET_VERSION,
    WARSAW_TZ,
    calendar_features,
    history_stats,
)

HORIZON_DAYS = {"T-30": 30, "T-14": 14, "T-7": 7, "T-3": 3}

DEFAULT_KEY_ALIASES = {
    "korona": "koronakielce",
    "motor": "motorlublin",
    "piast": "piastgliwice",
    "radomiak": "radomiak_radom",
    "slaskwroclaw": "slask_wroclaw",
    "widzew": "widzewlodz",
    "wislakrakow": "wisla_krakow",
    "zaglebie": "zaglebie_lubin",
}


@dataclass(frozen=True)
class CurrentStructuralPriorEvent:
    ticket_event_id: int
    season: str
    round_no: int
    kickoff_at: pd.Timestamp
    home_club_key: str
    away_club_key: str
    stadium_capacity: int

    def normalized(self) -> "CurrentStructuralPriorEvent":
        kickoff = pd.Timestamp(self.kickoff_at)
        if kickoff.tzinfo is None:
            raise ValueError("kickoff_at must be timezone-aware")
        if self.round_no < 1:
            raise ValueError("round_no must be >= 1")
        if self.stadium_capacity <= 0:
            raise ValueError("stadium_capacity must be > 0")
        return CurrentStructuralPriorEvent(
            ticket_event_id=int(self.ticket_event_id),
            season=str(self.season),
            round_no=int(self.round_no),
            kickoff_at=kickoff.tz_convert("UTC"),
            home_club_key=str(self.home_club_key),
            away_club_key=str(self.away_club_key),
            stadium_capacity=int(self.stadium_capacity),
        )


def _canonical_key(value: object, aliases: Mapping[str, str]) -> str | None:
    if value is None or pd.isna(value):
        return None
    key = str(value).strip()
    return aliases.get(key, key)


def _historical_kickoff(frame: pd.DataFrame) -> pd.Series:
    if "kickoff_at" in frame.columns:
        result = pd.to_datetime(frame["kickoff_at"], utc=True)
        if result.isna().any():
            raise ValueError("historical kickoff_at contains nulls")
        return result
    required = {"date", "kickoff_time_local"}
    if not required.issubset(frame.columns):
        raise ValueError("historical matches require kickoff_at or date + kickoff_time_local")
    local = pd.to_datetime(
        pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
        + " "
        + frame["kickoff_time_local"].astype(str),
        format="mixed",
    )
    return local.dt.tz_localize(
        WARSAW_TZ, ambiguous="raise", nonexistent="raise"
    ).dt.tz_convert("UTC")


def _attendance_columns(frame: pd.DataFrame) -> tuple[str, str, str]:
    home_col = "home_club_key" if "home_club_key" in frame.columns else "club_slug"
    attendance_col = "attendance" if "attendance" in frame.columns else "actual_attendance"
    if "away_club_key" in frame.columns:
        away_col = "away_club_key"
    elif "opponent_key" in frame.columns:
        away_col = "opponent_key"
    else:
        away_col = ""
    if home_col not in frame.columns or attendance_col not in frame.columns:
        raise ValueError(
            "current attendance requires home_club_key/club_slug and attendance/actual_attendance"
        )
    return home_col, away_col, attendance_col


def build_current_structural_prior_row(
    *,
    historical_matches: pd.DataFrame,
    current_attendance: pd.DataFrame,
    sporting_state: pd.DataFrame,
    event: CurrentStructuralPriorEvent,
    horizon: str,
    aliases: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Return one PIT feature row compatible with Structural Prior Runtime v1.

    ``sporting_state`` must contain one row per club with: ``club_key``,
    ``as_of_at``, ``matches_played``, ``points``, ``ppg``, ``gdpg``,
    ``form5_points``, ``form5_gd``, ``last_kickoff_at``, ``matches_last14``
    and ``position``.
    """
    if horizon not in HORIZON_DAYS:
        raise ValueError(f"Unsupported early horizon: {horizon}")
    event = event.normalized()
    aliases = {**DEFAULT_KEY_ALIASES, **(dict(aliases) if aliases else {})}
    as_of = event.kickoff_at - pd.Timedelta(days=HORIZON_DAYS[horizon])

    required_hist = {"season", "home_club_key", "away_club_key", "attendance"}
    missing_hist = sorted(required_hist - set(historical_matches.columns))
    if missing_hist:
        raise ValueError(f"Historical matches missing columns: {missing_hist}")

    hist = historical_matches.copy()
    hist["kickoff_at"] = _historical_kickoff(hist)
    hist["home_club_key"] = hist["home_club_key"].map(
        lambda x: _canonical_key(x, aliases)
    )
    hist["away_club_key"] = hist["away_club_key"].map(
        lambda x: _canonical_key(x, aliases)
    )
    hist = hist[hist["kickoff_at"] < as_of].sort_values(
        ["kickoff_at", "home_club_key"]
    )

    home_vals: dict[str, list[float]] = {}
    home_times: dict[str, list[pd.Timestamp]] = {}
    season_home_vals: dict[tuple[str, str], list[float]] = {}
    season_home_times: dict[tuple[str, str], list[pd.Timestamp]] = {}
    opp_ratios: dict[str, list[float]] = {}
    opp_raw: dict[str, list[float]] = {}
    pair_ratios: dict[tuple[str, str], list[float]] = {}
    pair_raw: dict[tuple[str, str], list[float]] = {}
    league_attendance: list[float] = []

    def bucket(mapping, key):
        return mapping.setdefault(key, [])

    def add_attendance(
        *,
        season: str,
        home: str,
        away: str | None,
        attendance: float,
        kickoff_at: pd.Timestamp,
    ) -> None:
        if not np.isfinite(attendance) or attendance <= 0:
            return
        prior_values = bucket(home_vals, home)
        prior_mean = float(np.mean(prior_values)) if prior_values else np.nan
        if away is not None:
            if prior_values and prior_mean > 0:
                ratio = float(attendance) / prior_mean
                bucket(opp_ratios, away).append(ratio)
                bucket(pair_ratios, (home, away)).append(ratio)
            bucket(opp_raw, away).append(float(attendance))
            bucket(pair_raw, (home, away)).append(float(attendance))
        prior_values.append(float(attendance))
        bucket(home_times, home).append(kickoff_at)
        bucket(season_home_vals, (season, home)).append(float(attendance))
        bucket(season_home_times, (season, home)).append(kickoff_at)
        league_attendance.append(float(attendance))

    for row in hist.itertuples(index=False):
        add_attendance(
            season=str(row.season),
            home=str(row.home_club_key),
            away=str(row.away_club_key),
            attendance=float(row.attendance),
            kickoff_at=pd.Timestamp(row.kickoff_at),
        )

    current = current_attendance.copy()
    if not current.empty:
        home_col, away_col, attendance_col = _attendance_columns(current)
        if "kickoff_at" not in current.columns:
            raise ValueError("current attendance requires exact kickoff_at")
        current["kickoff_at"] = pd.to_datetime(current["kickoff_at"], utc=True)
        current = current[current["kickoff_at"] < as_of].sort_values(
            ["kickoff_at", home_col]
        )
        for row in current.to_dict("records"):
            home = _canonical_key(row.get(home_col), aliases)
            away = _canonical_key(row.get(away_col), aliases) if away_col else None
            if home is None:
                continue
            add_attendance(
                season=event.season,
                home=home,
                away=away,
                attendance=float(row[attendance_col]),
                kickoff_at=pd.Timestamp(row["kickoff_at"]),
            )

    home = _canonical_key(event.home_club_key, aliases)
    away = _canonical_key(event.away_club_key, aliases)
    hstat = history_stats(bucket(home_vals, home), bucket(home_times, home), as_of)
    shstat = history_stats(
        bucket(season_home_vals, (event.season, home)),
        bucket(season_home_times, (event.season, home)),
        as_of,
    )

    previous_seasons = (
        hist.loc[hist["season"] != event.season, ["season", "kickoff_at"]]
        .sort_values("kickoff_at")["season"]
        .drop_duplicates()
        .tolist()
    )
    previous_season = previous_seasons[-1] if previous_seasons else None
    prev_values = (
        bucket(season_home_vals, (previous_season, home)) if previous_season else []
    )
    prev_mean = float(np.mean(prev_values)) if prev_values else np.nan
    league_median = float(np.median(league_attendance)) if league_attendance else np.nan

    required_sport = {
        "club_key",
        "as_of_at",
        "matches_played",
        "points",
        "ppg",
        "gdpg",
        "form5_points",
        "form5_gd",
        "last_kickoff_at",
        "matches_last14",
        "position",
    }
    missing_sport = sorted(required_sport - set(sporting_state.columns))
    if missing_sport:
        raise ValueError(f"Sporting state missing columns: {missing_sport}")

    sport = sporting_state.copy()
    sport["club_key"] = sport["club_key"].map(lambda x: _canonical_key(x, aliases))
    sport["as_of_at"] = pd.to_datetime(sport["as_of_at"], utc=True)
    sport["last_kickoff_at"] = pd.to_datetime(sport["last_kickoff_at"], utc=True)

    def sport_row(club: str) -> pd.Series:
        rows = sport[sport["club_key"] == club]
        if len(rows) != 1:
            raise ValueError(
                f"Expected one sporting-state row for {club}, got {len(rows)}"
            )
        row = rows.iloc[0]
        if row["as_of_at"] > as_of:
            raise ValueError(f"Sporting state for {club} is from the future")
        if row["last_kickoff_at"] >= as_of:
            raise ValueError(f"Last kickoff for {club} is not before PIT cutoff")
        return row

    home_s = sport_row(home)
    away_s = sport_row(away)

    def team_features(row: pd.Series) -> dict[str, float]:
        return {
            "matches_played": int(row["matches_played"]),
            "points": float(row["points"]),
            "ppg": float(row["ppg"]),
            "gdpg": float(row["gdpg"]),
            "form5_points": float(row["form5_points"]),
            "form5_gd": float(row["form5_gd"]),
            "days_since_last": float(
                (as_of - row["last_kickoff_at"]).total_seconds() / 86400.0
            ),
            "matches_last14": int(row["matches_last14"]),
        }

    home_f = team_features(home_s)
    away_f = team_features(away_s)
    home_pos = int(home_s["position"])
    away_pos = int(away_s["position"])

    opponent_ratio_values = bucket(opp_ratios, away)
    opponent_raw_values = bucket(opp_raw, away)
    pair_ratio_values = bucket(pair_ratios, (home, away))
    pair_raw_values = bucket(pair_raw, (home, away))

    baseline_season = shstat["mean"] if shstat["n"] > 0 else (
        hstat["mean"] if hstat["n"] > 0 else league_median
    )

    output = {
        "feature_set_version": FEATURE_SET_VERSION,
        "match_key": (
            f"{event.season}|{event.kickoff_at.tz_convert(WARSAW_TZ).date()}|"
            f"{home}|{away}"
        ),
        "season": event.season,
        "horizon": horizon,
        "as_of_at": as_of,
        "kickoff_at": event.kickoff_at,
        "home_club_key": home,
        "away_club_key": away,
        "target_attendance": np.nan,
        "target_eligible": False,
        "capacity": float(event.stadium_capacity),
        **calendar_features(event.kickoff_at, event.round_no),
        "home_history_n": hstat["n"],
        "home_attendance_mean": hstat["mean"],
        "home_attendance_median": hstat["median"],
        "home_attendance_last": hstat["last"],
        "home_attendance_rolling3": hstat["r3"],
        "home_attendance_rolling5": hstat["r5"],
        "home_attendance_rolling10": hstat["r10"],
        "home_attendance_std": hstat["std"],
        "home_attendance_p90": hstat["p90"],
        "home_attendance_trend3_vs_mean": (
            hstat["r3"] / hstat["mean"]
            if hstat["mean"] and not np.isnan(hstat["mean"])
            else np.nan
        ),
        "days_since_last_home": hstat["days_since"],
        "season_home_n": shstat["n"],
        "season_home_mean": shstat["mean"],
        "season_home_last": shstat["last"],
        "season_home_r3": shstat["r3"],
        "season_vs_long_ratio": (
            shstat["mean"] / hstat["mean"]
            if shstat["mean"]
            and hstat["mean"]
            and not np.isnan(shstat["mean"])
            and not np.isnan(hstat["mean"])
            else np.nan
        ),
        "prev_season_home_mean": prev_mean,
        "home_demand_vs_league_median": (
            hstat["mean"] / league_median
            if hstat["mean"] and league_median and not np.isnan(hstat["mean"])
            else np.nan
        ),
        "opponent_draw_n": len(opponent_ratio_values),
        "opponent_draw_ratio_mean": (
            float(np.mean(opponent_ratio_values)) if opponent_ratio_values else np.nan
        ),
        "opponent_draw_ratio_recent3": (
            float(np.mean(opponent_ratio_values[-3:]))
            if opponent_ratio_values
            else np.nan
        ),
        "opponent_raw_attendance_mean": (
            float(np.mean(opponent_raw_values)) if opponent_raw_values else np.nan
        ),
        "pair_n": len(pair_ratio_values),
        "pair_ratio_mean": (
            float(np.mean(pair_ratio_values)) if pair_ratio_values else np.nan
        ),
        "pair_ratio_recent2": (
            float(np.mean(pair_ratio_values[-2:])) if pair_ratio_values else np.nan
        ),
        "pair_attendance_mean": (
            float(np.mean(pair_raw_values)) if pair_raw_values else np.nan
        ),
        "baseline_r3": hstat["r3"],
        "baseline_r5": hstat["r5"],
        "baseline_mean": hstat["mean"],
        "baseline_season": baseline_season,
    }
    for prefix, features in (("home", home_f), ("away", away_f)):
        for key, value in features.items():
            output[f"{prefix}_{key}"] = value

    output["home_position"] = home_pos
    output["away_position"] = away_pos
    output["position_gap"] = away_pos - home_pos
    output["ppg_gap"] = home_f["ppg"] - away_f["ppg"]
    output["form5_points_gap"] = home_f["form5_points"] - away_f["form5_points"]
    output["gdpg_gap"] = home_f["gdpg"] - away_f["gdpg"]
    output["combined_ppg"] = home_f["ppg"] + away_f["ppg"]
    output["abs_ppg_gap"] = abs(output["ppg_gap"])
    output["abs_position_gap"] = abs(output["position_gap"])
    output["combined_table_strength"] = home_pos + away_pos
    output["top4_any"] = int(home_pos <= 4 or away_pos <= 4)
    output["top4_both"] = int(home_pos <= 4 and away_pos <= 4)
    output["bottom4_any"] = int(home_pos >= 15 or away_pos >= 15)
    output["late_season_top4"] = output["season_progress"] * output["top4_any"]
    output["late_season_bottom4"] = (
        output["season_progress"] * output["bottom4_any"]
    )
    output["combined_form5"] = home_f["form5_points"] + away_f["form5_points"]
    output["abs_form5_gap"] = abs(output["form5_points_gap"])
    output["rest_gap"] = home_f["days_since_last"] - away_f["days_since_last"]
    output["congestion_sum"] = home_f["matches_last14"] + away_f["matches_last14"]
    output["opponent_demand_x_progress"] = (
        output["opponent_draw_ratio_mean"] * output["season_progress"]
        if not pd.isna(output["opponent_draw_ratio_mean"])
        else np.nan
    )
    output["opponent_demand_x_weekend"] = (
        output["opponent_draw_ratio_mean"] * output["is_weekend"]
        if not pd.isna(output["opponent_draw_ratio_mean"])
        else np.nan
    )
    output["training_eligible"] = False

    return pd.DataFrame([output])
