#!/usr/bin/env python3
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from ml.club_calibration_shrinkage_v1 import CandidateSpec, calibration_table, correction_occupancy


def _history() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"home_club_key": "a", "incumbent_residual_occ": 0.10},
            {"home_club_key": "a", "incumbent_residual_occ": 0.20},
            {"home_club_key": "b", "incumbent_residual_occ": -0.10},
            {"home_club_key": "b", "incumbent_residual_occ": 0.00},
        ]
    )


def test_calibration_table_uses_medians() -> None:
    global_median, clubs = calibration_table(_history())
    assert math.isclose(global_median, 0.05)
    lookup = clubs.set_index("home_club_key")
    assert math.isclose(float(lookup.loc["a", "club_median_occ"]), 0.15)
    assert math.isclose(float(lookup.loc["b", "club_median_occ"]), -0.05)
    assert int(lookup.loc["a", "club_history_n"]) == 2


def test_zero_shrinkage_and_unseen_club() -> None:
    global_median, clubs = calibration_table(_history())
    test = pd.DataFrame({"home_club_key": ["a", "c"]})
    corr = correction_occupancy(
        test,
        global_median_occ=global_median,
        club_table=clubs,
        spec=CandidateSpec("club-zero-k8", "club_zero", 8.0),
    )
    # Club a: n/(n+k) * median = 2/10 * .15 = .03.
    assert np.allclose(corr, [0.03, 0.0])


def test_global_shrinkage_falls_back_to_global_for_unseen_club() -> None:
    global_median, clubs = calibration_table(_history())
    test = pd.DataFrame({"home_club_key": ["a", "c"]})
    corr = correction_occupancy(
        test,
        global_median_occ=global_median,
        club_table=clubs,
        spec=CandidateSpec("club-global-k8", "club_global", 8.0),
    )
    # Club a: .05 + .2*(.15-.05) = .07; unseen club -> global .05.
    assert np.allclose(corr, [0.07, 0.05])


def main() -> None:
    test_calibration_table_uses_medians()
    test_zero_shrinkage_and_unseen_club()
    test_global_shrinkage_falls_back_to_global_for_unseen_club()
    print("club_calibration_shrinkage_v1 tests passed")


if __name__ == "__main__":
    main()
