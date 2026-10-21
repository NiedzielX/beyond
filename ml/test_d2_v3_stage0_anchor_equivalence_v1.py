#!/usr/bin/env python3
"""Unit checks for d2-v3 Stage-0 final24 anchor equivalence."""
from __future__ import annotations

import copy
import numpy as np
import pandas as pd

from ml.d2_v3_stage0_anchor_equivalence_v1 import (
    EXPECTED_V2_FREEZE,
    EXPECTED_V3_FREEZE,
    assert_row_equivalence,
    build_equivalence_frame,
    verify_t1_equivalence,
)


def manifests() -> tuple[dict, dict]:
    contract = {
        "historical_base": "structural-prior-runtime-v1-t1-hist-full",
        "current_season_regime": "ewma50-resid-k6-cap05-min3",
        "historical_context_extension": "NO_CONTEXT",
    }
    mae = {
        "2022/2023": 1.0,
        "2023/2024": 2.0,
        "2024/2025": 3.0,
        "2025/2026": 4.0,
    }
    shared_input = {
        "historical_runtime_sha256": "abc",
        "feature_contract": "pit-v1",
    }
    v2 = {
        "freeze_id": EXPECTED_V2_FREEZE,
        "input": shared_input,
        "expected_final_mae": {"T-1": mae},
        "horizons": [{"horizon": "T-1", "contract": contract}],
    }
    v3 = copy.deepcopy(v2)
    v3["freeze_id"] = EXPECTED_V3_FREEZE
    return v2, v3


def test_manifest_equivalence_passes() -> None:
    v2, v3 = manifests()
    result = verify_t1_equivalence(v2, v3)
    assert result["contracts_exactly_equal"] is True
    assert result["expected_mae_exactly_equal"] is True


def test_manifest_contract_drift_fails() -> None:
    v2, v3 = manifests()
    v3["horizons"][0]["contract"]["current_season_regime"] = "changed"
    try:
        verify_t1_equivalence(v2, v3)
    except RuntimeError as exc:
        assert "contract differs" in str(exc)
    else:
        raise AssertionError("expected T-1 contract drift failure")


def test_row_equivalence() -> None:
    frame = pd.DataFrame({
        "ticket_event_id": [1, 1],
        "as_of_at": pd.to_datetime(["2026-01-01T00:00:00Z", "2026-01-01T06:00:00Z"], utc=True),
        "actual_attendance": [900.0, 900.0],
        "stadium_capacity": [1000.0, 1000.0],
        "frozen_v2_p50": [800.0, 800.0],
        "frozen_v2_expected_occupancy": [0.8, 0.8],
        "target_live_delta_attendance": [100.0, 100.0],
        "target_live_delta_occupancy": [0.1, 0.1],
    })
    out = build_equivalence_frame(frame)
    result = assert_row_equivalence(out)
    assert result["max_abs_anchor_delta_seats"] == 0.0
    assert result["max_abs_target_attendance_delta"] == 0.0
    assert np.isclose(result["max_abs_target_occupancy_delta"], 0.0)


def main() -> None:
    test_manifest_equivalence_passes()
    test_manifest_contract_drift_fails()
    test_row_equivalence()
    print("d2-v3 Stage0 anchor equivalence unit checks: PASS")


if __name__ == "__main__":
    main()
