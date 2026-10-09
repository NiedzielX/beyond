"""Exact recovered Lech v1.7 T-7 historical forecaster.

This adapter is deliberately narrow:
- Lech only;
- canonical T-7 shadow use only;
- exact recovered v1.7 point model;
- matching 80% split-conformal interval;
- no live correction and no production promotion implied.

The immutable historical training/checkpoint evidence ships with the repository
under ml/recovered/v17. For a genuinely future season, the caller supplies only
information that was available at the canonical T-7 checkpoint through
ForecastRequest.static_features.
"""
from __future__ import annotations

from datetime import datetime
from math import cos, pi, sin
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from sklearn.base import clone

from ml.recovered.v17.reconstruct_t7_v17 import (
    CAPACITY,
    NUMERIC_FEATURES,
    OPPONENT_MIN_HISTORY,
    build_template_model,
    prepare_dataset,
)
from ml.recovered.v17.t7_bundle import load_t7_frames

from .contracts import ForecastRequest, QuantileForecast

MODEL_NAME = "lech-v17-horizon-specific"
MODEL_VERSION = "lech-v17-t7-recovered-exact"
FEATURE_SET_VERSION = "v17-t7-recovered-exact-v1"
CALIBRATION_VERSION = "v17-split-conformal-80-v1:T-7"
INTERVAL_METHOD = "split_conformal_absolute_residual_80:horizon:T-7"
CONFORMAL_RADIUS = 8336.593429081528
WARSAW = ZoneInfo("Europe/Warsaw")

REQUIRED_STATIC_FEATURES = {
    "season",
    "opponent_key",
    "target_round_no",
    "target_season_progress",
    "target_matches_remaining",
    "lech_position_at_t7",
    "opponent_position_at_t7",
    "lech_matches_played_at_t7",
    "opponent_matches_played_at_t7",
    "league_team_count",
}


class V17T7StateError(ValueError):
    pass


def _season_start(season: str) -> pd.Timestamp:
    return pd.Timestamp(f"{str(season).split('/')[0]}-07-01", tz="UTC")


def _current_season_rows(static_features: Mapping[str, Any]) -> pd.DataFrame:
    rows = static_features.get("current_season_home_attendance", [])
    if rows is None:
        rows = []
    if not isinstance(rows, Iterable) or isinstance(rows, (str, bytes, Mapping)):
        raise V17T7StateError("current_season_home_attendance must be a list of row objects")

    normalized: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, Mapping):
            raise V17T7StateError("Each current-season attendance row must be an object")
        for key in ("season", "match_date", "opponent_key", "attendance"):
            if item.get(key) is None:
                raise V17T7StateError(f"Current-season attendance row missing {key}")
        normalized.append(
            {
                "season": str(item["season"]),
                "match_date": str(item["match_date"]),
                "opponent_key": str(item["opponent_key"]),
                "attendance": float(item["attendance"]),
                "capacity_constrained_for_model": bool(
                    item.get("capacity_constrained_for_model", False)
                ),
            }
        )
    return pd.DataFrame(normalized)


class RecoveredV17T7Forecaster:
    """Exact v1.7 T-7 point model + model-specific conformal interval.

    `static_features` is intentionally explicit. It must contain the sporting
    state reconstructed at the canonical T-7 checkpoint, not a current table
    snapshot taken later. This prevents silent point-in-time leakage.
    """

    def __init__(self) -> None:
        frames = load_t7_frames()

        # Reuse the exact recovered feature builder for historical training rows.
        # It accepts paths, so write the immutable repo bundle into a short-lived
        # temporary directory only during initialization.
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history_path = root / "history.csv"
            checkpoint_path = root / "checkpoint.csv"
            frames["history.csv"].to_csv(history_path, index=False)
            frames["checkpoint.csv"].to_csv(checkpoint_path, index=False)
            self.history, self.training_features, self.valid_target = prepare_dataset(
                history_path, checkpoint_path
            )

        self.history = self.history.copy()
        self.history["dt"] = pd.to_datetime(self.history["match_date"], utc=True)
        self._template = build_template_model()

    @staticmethod
    def supports(request: ForecastRequest) -> bool:
        # A six-hour cron can first see the match shortly after the canonical
        # T-7 instant. Never run before T-7 because the exact checkpoint state
        # would not yet exist. Wider use belongs to a separately benchmarked model.
        hours = request.hours_to_kickoff
        return (
            request.club_slug.lower() in {"lech", "lech-poznan", "lech_poznan"}
            and 162.0 <= hours <= 168.25
        )

    def _validate_state(self, request: ForecastRequest) -> Mapping[str, Any]:
        state = request.static_features
        missing = sorted(REQUIRED_STATIC_FEATURES - set(state))
        if missing:
            raise V17T7StateError(
                "Missing exact T-7 static features: " + ", ".join(missing)
            )
        if int(state["lech_matches_played_at_t7"]) < 0 or int(
            state["opponent_matches_played_at_t7"]
        ) < 0:
            raise V17T7StateError("T-7 matches-played values cannot be negative")
        if int(state["league_team_count"]) <= 1:
            raise V17T7StateError("league_team_count must be greater than 1")
        return state

    def _combined_attendance_history(
        self, request: ForecastRequest, state: Mapping[str, Any]
    ) -> pd.DataFrame:
        base = self.history[
            [
                "season",
                "match_date",
                "opponent_key",
                "attendance",
                "capacity_constrained_for_model",
                "dt",
            ]
        ].copy()
        current = _current_season_rows(state)
        if not current.empty:
            current["dt"] = pd.to_datetime(current["match_date"], utc=True)
            # The immutable bundle already includes seasons through 2025/26.
            # Refuse duplicate target-season history rather than double-counting.
            if str(state["season"]) in set(base["season"].astype(str)):
                current = current[~current["season"].isin(set(base["season"].astype(str)))]
            base = pd.concat([base, current], ignore_index=True, sort=False)
        base["attendance"] = pd.to_numeric(base["attendance"], errors="coerce")
        base["capacity_constrained_for_model"] = (
            base["capacity_constrained_for_model"].fillna(False).astype(bool)
        )
        return base.sort_values("dt").reset_index(drop=True)

    def _target_features(
        self, request: ForecastRequest, state: Mapping[str, Any]
    ) -> pd.DataFrame:
        history = self._combined_attendance_history(request, state)
        cutoff = pd.Timestamp(request.kickoff_at).tz_convert("UTC") - pd.Timedelta(days=7)
        usable = history[
            (history["dt"] < cutoff)
            & (~history["capacity_constrained_for_model"])
            & history["attendance"].notna()
        ].copy()
        if usable.empty:
            raise V17T7StateError("No leakage-safe attendance history available at T-7")

        attendance = usable["attendance"].astype(float)
        global_mean = float(attendance.mean())
        season = str(state["season"])
        same_season = usable[usable["season"].astype(str) == season]
        season_avg = (
            float(same_season["attendance"].mean()) if len(same_season) else global_mean
        )
        opponent = usable[
            usable["opponent_key"].astype(str) == str(state["opponent_key"])
        ]
        opponent_mean = (
            float(opponent["attendance"].mean()) if len(opponent) else global_mean
        )
        opponent_recent = (
            float(opponent.tail(3)["attendance"].mean())
            if len(opponent)
            else opponent_mean
        )

        def rolling(n: int) -> float:
            return float(attendance.tail(n).mean())

        r3, r5, r10 = rolling(3), rolling(5), rolling(10)
        local = request.kickoff_at.astimezone(WARSAW)
        month = local.month
        weekday = local.weekday()
        kickoff_minutes = local.hour * 60 + local.minute
        day_of_year = local.timetuple().tm_yday

        gate = int(
            int(state["lech_matches_played_at_t7"]) >= 10
            and int(state["opponent_matches_played_at_t7"]) >= 10
        )
        raw_lech = float(state["lech_position_at_t7"])
        raw_opp = float(state["opponent_position_at_t7"])
        midpoint = (float(state["league_team_count"]) + 1.0) / 2.0

        row = {
            "opponent_key": str(state["opponent_key"]),
            "month": month,
            "weekday": weekday,
            "kickoff_minutes": kickoff_minutes,
            "is_weekend": int(weekday >= 5),
            "month_sin": sin(2 * pi * month / 12.0),
            "month_cos": cos(2 * pi * month / 12.0),
            "doy_sin": sin(2 * pi * day_of_year / 365.25),
            "doy_cos": cos(2 * pi * day_of_year / 365.25),
            "kickoff_sin": sin(2 * pi * kickoff_minutes / 1440.0),
            "kickoff_cos": cos(2 * pi * kickoff_minutes / 1440.0),
            "is_winter_month": int(month in (12, 1, 2)),
            "is_summer_month": int(month in (6, 7, 8)),
            "target_round_no": float(state["target_round_no"]),
            "target_season_progress": float(state["target_season_progress"]),
            "target_matches_remaining": float(state["target_matches_remaining"]),
            "rolling_3": r3,
            "rolling_5": r5,
            "rolling_10": r10,
            "season_avg_so_far": season_avg,
            "recent_attendance_trend": r3 / r10 if r10 else np.nan,
            "opponent_draw_ratio": float(
                np.clip(opponent_mean / global_mean, 0.5, 1.8)
            ),
            "opponent_recent_draw_ratio": float(
                np.clip(opponent_recent / global_mean, 0.5, 1.8)
            ),
            "history_n": len(usable),
            "season_home_matches_known": len(same_season),
            "lech_pos_gate_10": (midpoint - raw_lech) * gate,
            "opp_pos_gate_10": (midpoint - raw_opp) * gate,
            "pos_gap_gate_10": (raw_opp - raw_lech) * gate,
            "pos_gate_active_10": gate,
        }
        return pd.DataFrame([row])

    def forecast(self, request: ForecastRequest) -> QuantileForecast:
        if not self.supports(request):
            raise V17T7StateError(
                "Recovered v1.7 T-7 forecaster supports only Lech in the first six hours after canonical T-7."
            )
        state = self._validate_state(request)
        target = self._target_features(request, state)

        train_index = self.history.index[
            (self.history["dt"] < _season_start(str(state["season"])))
            & self.valid_target
        ]
        counts = self.history.loc[train_index, "opponent_key"].value_counts()
        kept = set(counts[counts >= OPPONENT_MIN_HISTORY].index)

        columns = ["opponent_key"] + NUMERIC_FEATURES
        train = self.training_features.loc[train_index, columns].copy()
        train["opponent_group"] = train["opponent_key"].where(
            train["opponent_key"].isin(kept), "other"
        )
        target["opponent_group"] = target["opponent_key"].where(
            target["opponent_key"].isin(kept), "other"
        )

        y = self.history.loc[train_index, "attendance"].astype(float)
        baseline = self.training_features.loc[
            train_index, "season_avg_so_far"
        ].astype(float)
        usable = y.notna() & baseline.notna()
        residual = (y.loc[usable] - baseline.loc[usable]).to_numpy()

        model = clone(self._template)
        model.fit(train.loc[usable], residual)
        predicted_residual = float(model.predict(target)[0])
        p50 = float(target.iloc[0]["season_avg_so_far"]) + predicted_residual

        capacity = float(request.stadium_capacity or CAPACITY)
        p50 = min(capacity, max(0.0, p50))
        p10 = max(0.0, p50 - CONFORMAL_RADIUS)
        p90 = min(capacity, p50 + CONFORMAL_RADIUS)

        return QuantileForecast(
            p10=p10,
            p50=p50,
            p90=p90,
            model_name=MODEL_NAME,
            model_version=MODEL_VERSION,
            feature_set_version=FEATURE_SET_VERSION,
            interval_method=INTERVAL_METHOD,
            calibration_version=CALIBRATION_VERSION,
        )
