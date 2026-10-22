#!/usr/bin/env python3
from __future__ import annotations

import math

import pandas as pd

from ml.d2_long72_live_incremental_value_v1 import evaluate_band
from ml.mae_delta_uncertainty_v1 import BootstrapConfig


def test_event_balanced_incremental_value() -> None:
    frame = pd.DataFrame(
        [
            {"ticket_event_id": 1, "hours_to_kickoff": 30.0, "actual_attendance": 100.0, "anchor_p50": 120.0, "forecast_p50": 110.0},
            {"ticket_event_id": 1, "hours_to_kickoff": 32.0, "actual_attendance": 100.0, "anchor_p50": 120.0, "forecast_p50": 110.0},
            {"ticket_event_id": 2, "hours_to_kickoff": 30.0, "actual_attendance": 100.0, "anchor_p50": 100.0, "forecast_p50": 130.0},
        ]
    )
    result = evaluate_band(
        frame,
        band_id="24_72h",
        lower_exclusive=24.0,
        upper_inclusive=72.0,
        config=BootstrapConfig(n_resamples=200, seed=42),
    )
    assert result["independent_event_count"] == 2
    assert math.isclose(result["incumbent_mae"], 10.0)
    assert math.isclose(result["challenger_mae"], 20.0)
    assert math.isclose(result["delta_mae"], 10.0)
    assert math.isclose(result["event_improvement_rate"], 0.5)


def test_band_boundaries_are_strict_lower_inclusive_upper() -> None:
    frame = pd.DataFrame(
        [
            {"ticket_event_id": 1, "hours_to_kickoff": 24.0, "actual_attendance": 100.0, "anchor_p50": 110.0, "forecast_p50": 105.0},
            {"ticket_event_id": 2, "hours_to_kickoff": 24.1, "actual_attendance": 100.0, "anchor_p50": 110.0, "forecast_p50": 105.0},
            {"ticket_event_id": 3, "hours_to_kickoff": 48.0, "actual_attendance": 100.0, "anchor_p50": 110.0, "forecast_p50": 105.0},
            {"ticket_event_id": 4, "hours_to_kickoff": 48.1, "actual_attendance": 100.0, "anchor_p50": 110.0, "forecast_p50": 105.0},
        ]
    )
    result = evaluate_band(
        frame,
        band_id="24_48h",
        lower_exclusive=24.0,
        upper_inclusive=48.0,
        config=BootstrapConfig(n_resamples=200, seed=42),
    )
    assert result["row_count"] == 2
    assert result["independent_event_count"] == 2


def main() -> None:
    test_event_balanced_incremental_value()
    test_band_boundaries_are_strict_lower_inclusive_upper()
    print("d2_long72_live_incremental_value_v1 tests passed")


if __name__ == "__main__":
    main()
