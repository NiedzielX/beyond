#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

from ml.d2_long72_stage1_model_tournament_v1 import (
    choose_research_lead,
    event_balanced_band_score,
)


def test_band_score_is_event_balanced() -> None:
    predictions = pd.DataFrame([
        {"ticket_event_id": 1, "hours_to_kickoff": 60.0, "absolute_error": 100.0, "anchor_absolute_error": 200.0},
        {"ticket_event_id": 1, "hours_to_kickoff": 54.0, "absolute_error": 100.0, "anchor_absolute_error": 200.0},
        {"ticket_event_id": 2, "hours_to_kickoff": 60.0, "absolute_error": 500.0, "anchor_absolute_error": 400.0},
    ])
    score = event_balanced_band_score(predictions, 48.0, 72.0)
    assert score["event_count"] == 2
    assert score["row_count"] == 3
    assert score["event_balanced_mae"] == 300.0
    assert score["anchor_event_balanced_mae"] == 300.0
    assert score["mae_improvement"] == 0.0
    assert score["event_improvement_rate"] == 0.5


def _candidate(candidate_id: str, overall_imp: float, early_mae: float, early_imp: float, far_mae: float, far_imp: float, tail: float) -> dict:
    return {
        "candidate_id": candidate_id,
        "overall_0_72h": {
            "window_mae_improvement": overall_imp,
            "event_balanced_window_mae": 1000.0 - overall_imp,
        },
        "bands": {
            "24_72h": {
                "event_balanced_mae": early_mae,
                "mae_improvement": early_imp,
                "worst_event_degradation": tail,
            },
            "48_72h": {
                "event_balanced_mae": far_mae,
                "mae_improvement": far_imp,
            },
        },
    }


def test_selector_focuses_on_new_early_window_and_far_band_gate() -> None:
    rows = [
        _candidate("frozen-v2-zero-correction", 0.0, 1000.0, 0.0, 1000.0, 0.0, 0.0),
        _candidate("good", 100.0, 800.0, 200.0, 850.0, 150.0, 300.0),
        _candidate("better-overall-but-worse-far", 200.0, 750.0, 250.0, 1010.0, -10.0, 100.0),
    ]
    assert choose_research_lead(rows) == "good"


def test_selector_falls_back_to_anchor_when_no_candidate_passes() -> None:
    rows = [
        _candidate("frozen-v2-zero-correction", 0.0, 1000.0, 0.0, 1000.0, 0.0, 0.0),
        _candidate("bad", -1.0, 1001.0, -1.0, 999.0, 1.0, 10.0),
    ]
    assert choose_research_lead(rows) == "frozen-v2-zero-correction"


def main() -> None:
    test_band_score_is_event_balanced()
    test_selector_focuses_on_new_early_window_and_far_band_gate()
    test_selector_falls_back_to_anchor_when_no_candidate_passes()
    print("d2 long72 Stage1 tournament unit checks: PASS")


if __name__ == "__main__":
    main()
