#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from ml.d2_long72_forward_score_v1 import (
    PACKAGE_FREEZE_CUTOFF,
    PACKAGE_ID,
    compose_context,
)
from ml.d2_long72_stage2_reliability_gating_v1 import maturity_reliability
from ml.d2_stage1_model_tournament_v1 import governed_forecast, inventory_linear_delta


def test_package_identity_and_freeze_cutoff() -> None:
    assert PACKAGE_ID == "d2-long72-stage2-p2-observation-maturity-2026-10-21-v1"
    assert PACKAGE_FREEZE_CUTOFF == pd.Timestamp("2026-10-21T17:37:07Z")


def test_target_outcome_leakage_fails_closed() -> None:
    forward = {
        "events": [
            {
                "ticket_event_id": 10,
                "club_slug": "pogonszczecin",
                "kickoff_at": "2026-10-24T15:30:00Z",
            }
        ]
    }
    attendance = {
        "attendance": [
            {
                "club_slug": "pogonszczecin",
                "kickoff_at": "2026-10-24T15:30:00Z",
                "actual_attendance": 12345,
            }
        ]
    }
    try:
        compose_context(forward, attendance, {"sportingMatches": []}, {"aliases": []})
    except RuntimeError as exc:
        assert "target-event outcome leaked" in str(exc)
    else:
        raise AssertionError("expected target-outcome leakage failure")


def test_sealed_inventory_plus_p2_formula_uses_canonical_functions() -> None:
    frame = pd.DataFrame(
        {
            "stadium_capacity": [40000.0, 40000.0, 40000.0],
            "available_total": [10000.0, 9000.0, 8000.0],
            "hours_to_kickoff": [66.0, 54.0, 42.0],
            "velocity_6h": [100.0, 110.0, 120.0],
            "velocity_24h": [80.0, 90.0, 100.0],
            "velocity_since_previous": [70.0, 80.0, 90.0],
            "frozen_v2_expected_occupancy": [0.70, 0.70, 0.70],
            "stage2_observation_index": [1, 2, 3],
        }
    )
    raw = inventory_linear_delta(frame)
    raw_forecast, governed = governed_forecast(frame, raw)
    reliability = maturity_reliability(frame)
    expected_reliability = np.array([0.25, 0.60, 1.0])
    assert np.allclose(reliability, expected_reliability)
    final = np.clip(
        frame["frozen_v2_expected_occupancy"].to_numpy() * frame["stadium_capacity"].to_numpy()
        + reliability * governed * frame["stadium_capacity"].to_numpy(),
        0.0,
        frame["stadium_capacity"].to_numpy(),
    )
    assert np.all(np.isfinite(raw_forecast))
    assert np.all(np.isfinite(final))
    assert np.all(final >= 0.0)
    assert np.all(final <= frame["stadium_capacity"].to_numpy())
    # First observation must be more strongly shrunk than the frozen raw expert.
    anchor = frame["frozen_v2_expected_occupancy"].to_numpy() * frame["stadium_capacity"].to_numpy()
    assert abs(final[0] - anchor[0]) <= abs(raw_forecast[0] - anchor[0]) + 1e-9


def main() -> None:
    test_package_identity_and_freeze_cutoff()
    test_target_outcome_leakage_fails_closed()
    test_sealed_inventory_plus_p2_formula_uses_canonical_functions()
    print("d2 long72 forward scorer unit checks: PASS")


if __name__ == "__main__":
    main()
