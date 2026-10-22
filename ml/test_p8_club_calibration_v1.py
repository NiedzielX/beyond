#!/usr/bin/env python3
from __future__ import annotations

import math
import pandas as pd

from ml.p8_club_calibration_v1 import simulate


def test_tied_kickoff_cannot_train_each_other() -> None:
    frame = pd.DataFrame([
        {"match_key":"a","kickoff_at":pd.Timestamp("2026-01-01T12:00:00Z"),"home_club_key":"x","away_club_key":"u","forecast_p50":120.0,"actual_attendance":100.0,"signed_error":20.0,"absolute_error":20.0,"season":"s"},
        {"match_key":"b","kickoff_at":pd.Timestamp("2026-01-01T12:00:00Z"),"home_club_key":"x","away_club_key":"v","forecast_p50":120.0,"actual_attendance":100.0,"signed_error":20.0,"absolute_error":20.0,"season":"s"},
        {"match_key":"c","kickoff_at":pd.Timestamp("2026-01-02T12:00:00Z"),"home_club_key":"x","away_club_key":"w","forecast_p50":120.0,"actual_attendance":100.0,"signed_error":20.0,"absolute_error":20.0,"season":"s"},
    ])
    out = simulate(frame, "home_club_key").sort_values("match_key")
    assert out.loc[out.match_key=="a","history_n"].iloc[0] == 0
    assert out.loc[out.match_key=="b","history_n"].iloc[0] == 0
    assert out.loc[out.match_key=="c","history_n"].iloc[0] == 2


def test_shrinkage_is_conservative() -> None:
    frame = pd.DataFrame([
        {"match_key":"a","kickoff_at":pd.Timestamp("2026-01-01T12:00:00Z"),"home_club_key":"x","away_club_key":"u","forecast_p50":120.0,"actual_attendance":100.0,"signed_error":20.0,"absolute_error":20.0,"season":"s"},
        {"match_key":"b","kickoff_at":pd.Timestamp("2026-01-02T12:00:00Z"),"home_club_key":"x","away_club_key":"v","forecast_p50":120.0,"actual_attendance":100.0,"signed_error":20.0,"absolute_error":20.0,"season":"s"},
    ])
    out = simulate(frame, "home_club_key").sort_values("match_key")
    correction = out.loc[out.match_key=="b","correction"].iloc[0]
    assert math.isclose(correction, 20.0/81.0)


if __name__ == "__main__":
    test_tied_kickoff_cannot_train_each_other()
    test_shrinkage_is_conservative()
    print("p8_club_calibration_v1 tests passed")
