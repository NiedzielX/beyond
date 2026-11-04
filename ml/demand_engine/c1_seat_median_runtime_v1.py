"""Inference-only direct-person median expert; outputs are already in persons."""
from dataclasses import dataclass
from typing import Any

import numpy as np

from ml.demand_engine.c1_shadow_runtime_v8 import POLICY_ID

PACKAGE = 'c1-live-seat-median-v1-frozen-2026-11-04-n20'
MODEL_ID = 'c1-live-linear-seat-median-q50-a01-n20'
FEATURE_CONTRACT = 'live-trajectory-v1.1+c1-compact-direct-seat-median-v1'


@dataclass
class C1SeatMedianRuntimeV1:
    estimator: Any
    features: tuple[str, ...]
    training_event_ids: tuple[int, ...]
    training_rows: int
    package_version: str = PACKAGE
    live_model_id: str = MODEL_ID
    feature_contract: str = FEATURE_CONTRACT
    policy_id: str = POLICY_ID

    def predict_live_p50(self, frame):
        if any(name not in frame for name in self.features) or 'stadium_capacity' not in frame:
            raise ValueError('Median runtime missing compact features/capacity')
        capacity = frame.stadium_capacity.to_numpy(dtype=float)
        predictions = np.asarray(self.estimator.predict(frame[list(self.features)]), dtype=float)
        if (predictions.shape != (len(frame),) or not np.isfinite(predictions).all()
                or not np.isfinite(capacity).all() or (capacity <= 0).any()):
            raise ValueError('Invalid direct-person predictions or capacities')
        return np.clip(predictions, 0, capacity)  # No multiplication by capacity.
