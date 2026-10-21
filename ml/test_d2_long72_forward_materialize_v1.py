#!/usr/bin/env python3
"""Unit checks for Long72 forward prospective materialization v1."""
from __future__ import annotations

import math

import pandas as pd

from ml.d2_long72_forward_materialize_v1 import (
    compute_b2_t3_correction,
)
from ml.d2_long72_stage2_reliability_gating_v1 import (
    add_causal_reliability_state,
    maturity_reliability,
)


def test_b2_maturity_gate() -> None:
    none = compute_b2_t3_correction([], 20_000)
    assert none["prior_home_matches"] == 0
    assert none["active"] is False
    assert none["correction_seats"] == 0.0

    one = compute_b2_t3_correction([0.10], 20_000)
    assert one["prior_home_matches"] == 1
    assert one["active"] is False
    assert one["correction_seats"] == 0.0


def test_b2_frozen_cap() -> None:
    result = compute_b2_t3_correction([0.10, 0.10, 0.10], 20_000)
    assert result["active"] is True
    assert math.isclose(float(result["ewma_residual_fraction"]), 0.10, abs_tol=1e-12)
    # n/(n+2)=0.6 -> raw 1200 seats, frozen cap is 5% = 1000 seats.
    assert math.isclose(float(result["correction_seats"]), 1000.0, abs_tol=1e-9)


def test_p2_observation_maturity() -> None:
    frame = pd.DataFrame({
        "ticket_event_id": [1, 1, 1],
        "as_of_at": pd.to_datetime([
            "2026-10-21T18:00:00Z",
            "2026-10-22T00:00:00Z",
            "2026-10-22T12:00:00Z",
        ], utc=True),
        "hours_to_kickoff": [70.0, 58.0, 46.0],
    })
    enriched = add_causal_reliability_state(frame)
    assert enriched["stage2_observation_index"].tolist() == [1, 2, 3]
    reliability = maturity_reliability(enriched)
    assert [round(float(v), 6) for v in reliability] == [0.25, 0.60, 1.0]


def main() -> None:
    test_b2_maturity_gate()
    test_b2_frozen_cap()
    test_p2_observation_maturity()
    print("d2 long72 forward materialize v1 unit checks passed")


if __name__ == "__main__":
    main()
