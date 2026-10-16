#!/usr/bin/env python3
"""Frozen C1 v8 shadow runtime contract.

This module is inference-only. It deliberately contains no model fitting path.
The v2 live expert is fitted by the separate build-time freezer and serialized
inside :class:`C1ShadowRuntimeV8`.

Production forecasting is not changed by this runtime. Its outputs are
EXPERIMENTAL_SHADOW evidence only until prospective promotion criteria pass.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


LIVE_MODEL_ID = "c1-v2-live-ridge-directocc-compact-generic-a10"
POLICY_ID = "c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single"
FEATURE_CONTRACT = "live-trajectory-v1.1+c1-v2-compact-direct-occupancy"
MULTI_OBS_DISAGREEMENT_THRESHOLD = 0.10
SINGLE_OBS_DISAGREEMENT_THRESHOLD = 0.20


def _linear_slope(values: np.ndarray, elapsed_hours: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    elapsed_hours = np.asarray(elapsed_hours, dtype=float)
    if len(values) < 2 or np.ptp(elapsed_hours) <= 1e-9:
        return float("nan")
    return float(np.polyfit(elapsed_hours, values, 1)[0])


def apply_v8_policy(
    *,
    prior_p50: float,
    stadium_capacity: float,
    live_history_p50: list[float] | np.ndarray,
    elapsed_hours: list[float] | np.ndarray,
) -> dict[str, Any]:
    """Apply the frozen v8 policy using only observations available so far."""
    live_history = np.asarray(live_history_p50, dtype=float)
    elapsed = np.asarray(elapsed_hours, dtype=float)
    if len(live_history) < 1:
        raise ValueError("v8 policy requires at least one live prediction")
    if len(live_history) != len(elapsed):
        raise ValueError("live_history_p50 and elapsed_hours must have equal length")
    if stadium_capacity <= 0:
        raise ValueError("stadium_capacity must be positive")

    live_now = float(live_history[-1])
    prior_occ = float(prior_p50) / float(stadium_capacity)
    live_occ = live_now / float(stadium_capacity)
    disagreement = abs(live_occ - prior_occ)
    observation_count = int(len(live_history))
    slope = _linear_slope(live_history / float(stadium_capacity), elapsed)

    if observation_count == 1:
        use_live = disagreement >= SINGLE_OBS_DISAGREEMENT_THRESHOLD
        reason = (
            "single_obs_material_disagreement"
            if use_live
            else "single_obs_insufficient_disagreement"
        )
    else:
        use_live = (
            disagreement >= MULTI_OBS_DISAGREEMENT_THRESHOLD
            and np.isfinite(slope)
            and slope > 0.0
        )
        if use_live:
            reason = "material_disagreement_positive_live_slope"
        elif disagreement < MULTI_OBS_DISAGREEMENT_THRESHOLD:
            reason = "insufficient_disagreement"
        else:
            reason = "live_slope_not_positive"

    selected = "LIVE" if use_live else "PRIOR"
    prediction = live_now if use_live else float(prior_p50)
    return {
        "policy_id": POLICY_ID,
        "selected_expert": selected,
        "policy_prediction": prediction,
        "live_p50": live_now,
        "abs_disagreement_occupancy": float(disagreement),
        "live_observation_count_to_date": observation_count,
        "live_slope_occupancy_per_hour_to_date": None if not np.isfinite(slope) else float(slope),
        "reason_code": reason,
    }


@dataclass
class C1ShadowRuntimeV8:
    """Serializable, inference-only wrapper around the frozen v2 live expert."""

    estimator: Any
    features: tuple[str, ...]
    package_version: str
    training_event_ids: tuple[int, ...]
    training_rows: int
    feature_contract: str = FEATURE_CONTRACT
    live_model_id: str = LIVE_MODEL_ID
    policy_id: str = POLICY_ID

    def predict_live_p50(self, frame: pd.DataFrame) -> np.ndarray:
        missing = [feature for feature in self.features if feature not in frame.columns]
        if missing:
            raise ValueError(f"C1 shadow runtime missing features: {missing}")
        if "stadium_capacity" not in frame.columns:
            raise ValueError("C1 shadow runtime requires stadium_capacity")

        occupancy = np.asarray(self.estimator.predict(frame[list(self.features)]), dtype=float)
        capacity = frame["stadium_capacity"].astype(float).to_numpy()
        return np.clip(occupancy * capacity, 0.0, capacity)
