#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from ml.d2_long72_anchor_contract_v1 import (
    canonical_club_key,
    resolve_capacity,
)


def test_canonical_slug_mapping() -> None:
    assert canonical_club_key("slaskwroclaw") == "slask_wroclaw"
    assert canonical_club_key("zaglebie") == "zaglebie_lubin"
    assert canonical_club_key("lech") == "lech"


def test_capacity_validity_resolution() -> None:
    rows = [
        {"id": 1, "club_key": "lech", "stadium_capacity": 40000, "valid_from": "2025-01-01", "valid_to": "2026-06-30"},
        {"id": 2, "club_key": "lech", "stadium_capacity": 43269, "valid_from": "2026-07-01", "valid_to": None},
    ]
    resolved = resolve_capacity(rows, "lech", pd.Timestamp("2026-10-01T18:00:00Z"))
    assert resolved["id"] == 2
    assert resolved["stadium_capacity"] == 43269


def test_missing_capacity_fails() -> None:
    try:
        resolve_capacity([], "lech", pd.Timestamp("2026-10-01T18:00:00Z"))
    except RuntimeError as exc:
        assert "no capacity registry row" in str(exc)
    else:
        raise AssertionError("expected missing capacity failure")


def main() -> None:
    test_canonical_slug_mapping()
    test_capacity_validity_resolution()
    test_missing_capacity_fails()
    print("d2 long72 anchor contract unit checks: PASS")


if __name__ == "__main__":
    main()
