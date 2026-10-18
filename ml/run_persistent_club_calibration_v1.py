#!/usr/bin/env python3
"""Canonical runner for persistent club calibration v1.

T-7 must reuse the exact Stage-3 fitter/spec that produced and later froze
`hist31-leaf20-l2-1`. Reimplementing the estimator locally caused a valid CI
reproduction failure (2327.04 vs canonical 2317.34) because the local copy
passed explicit uniform sample weights while the canonical fitter does not.

This adapter makes the dependency explicit and preserves the hard MAE gates.
"""
from __future__ import annotations

import ml.persistent_club_calibration_v1 as impl
from ml.t7_robust_estimator_v1 import CANDIDATES as T7_CANDIDATES, fit_estimator

T7_FROZEN_SPEC = next(
    candidate for candidate in T7_CANDIDATES if candidate.id == "hist31-leaf20-l2-1"
)
_ORIGINAL_FIT_BASE_MODEL = impl.fit_base_model


def fit_base_model_canonical(store, horizon: str, training_seasons: list[str]):
    if horizon == "T-7":
        return fit_estimator(store, training_seasons, T7_FROZEN_SPEC)
    return _ORIGINAL_FIT_BASE_MODEL(store, horizon, training_seasons)


impl.fit_base_model = fit_base_model_canonical


if __name__ == "__main__":
    impl.main()
