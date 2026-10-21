#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

from ml.d2_long72_stage1_model_tournament_v1 import (
    choose_research_lead,
    early_frame,
    is_selector_eligible,
)


def test_early_frame_keeps_only_24_72h() -> None:
    rows = []
    # Exact early contract shape: 13 early events / 80 rows. Counts >=5 create
    # a 48-72h observation when spaced by 6h; exactly 10 events meet that rule.
    event_ids = [1, 3, 4, 5, 8, 9, 11, 12, 14, 15, 17, 18, 19]
    counts = [8, 8, 8, 8, 2, 5, 8, 1, 6, 8, 2, 8, 8]
    for event_id, count in zip(event_ids, counts):
        for index in range(count):
            rows.append({
                "ticket_event_id": event_id,
                "hours_to_kickoff": 30.0 + 6.0 * index,
                "anchor_horizon": "T-3",
            })
    assert len(rows) == 80

    # Pad final24 rows to full 130 and ensure the full contract has 14 events.
    for index in range(50):
        rows.append({
            "ticket_event_id": 13 if index == 0 else event_ids[index % len(event_ids)],
            "hours_to_kickoff": 12.0,
            "anchor_horizon": "T-1",
        })
    frame = pd.DataFrame(rows)
    early = early_frame(frame)
    assert len(early) == 80
    assert early["ticket_event_id"].nunique() == 13
    assert early.loc[early["hours_to_kickoff"] > 48, "ticket_event_id"].nunique() == 10
    assert (early["hours_to_kickoff"] > 24).all()
    assert (early["hours_to_kickoff"] <= 72).all()


def score(candidate_id: str, overall: float, b1: float, b2: float, mae: float) -> dict:
    return {
        "candidate_id": candidate_id,
        "scorecard": {
            "overall_24_72h": {
                "mae_improvement": overall,
                "event_balanced_mae": mae,
                "worst_event_degradation": 100.0,
            },
            "band_24_48h": {"mae_improvement": b1},
            "band_48_72h": {"mae_improvement": b2, "event_balanced_mae": mae},
        },
    }


def test_selector_requires_positive_all_bands() -> None:
    good = score("good", 100.0, 50.0, 25.0, 3000.0)
    mixed = score("mixed", 200.0, 100.0, -1.0, 2500.0)
    assert is_selector_eligible(good)
    assert not is_selector_eligible(mixed)
    assert choose_research_lead([
        score("anchor-zero-correction", 0.0, 0.0, 0.0, 3500.0),
        good,
        mixed,
    ]) == "good"


def main() -> None:
    test_early_frame_keeps_only_24_72h()
    test_selector_requires_positive_all_bands()
    print("d2 long72 Stage1 tournament unit checks: PASS")


if __name__ == "__main__":
    main()
