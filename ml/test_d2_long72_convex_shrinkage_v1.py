#!/usr/bin/env python3
from __future__ import annotations

import math

import pandas as pd

from ml.d2_long72_convex_shrinkage_v1 import prediction_for_weight, train_score


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ticket_event_id": "1", "actual_attendance": 100.0, "anchor_p50": 80.0, "forecast_p50": 120.0, "live_delta": 40.0},
            {"ticket_event_id": "1", "actual_attendance": 100.0, "anchor_p50": 80.0, "forecast_p50": 120.0, "live_delta": 40.0},
            {"ticket_event_id": "2", "actual_attendance": 100.0, "anchor_p50": 100.0, "forecast_p50": 140.0, "live_delta": 40.0},
        ]
    )


def test_convex_prediction_identity() -> None:
    frame = _frame()
    anchor = prediction_for_weight(frame, 0.0)
    p2 = prediction_for_weight(frame, 1.0)
    half = prediction_for_weight(frame, 0.5)
    assert anchor.tolist() == frame["anchor_p50"].tolist()
    assert p2.tolist() == frame["forecast_p50"].tolist()
    assert half.tolist() == [100.0, 100.0, 120.0]


def test_train_score_is_event_balanced() -> None:
    frame = _frame()
    # w=.5 gives event 1 MAE 0 and event 2 MAE 20 -> event-balanced 10.
    assert math.isclose(train_score(frame, 0.5), 10.0)
    # Row weighting would be 6.67, so this guards the independent-event contract.


def main() -> None:
    test_convex_prediction_identity()
    test_train_score_is_event_balanced()
    print("d2_long72_convex_shrinkage_v1 tests passed")


if __name__ == "__main__":
    main()
