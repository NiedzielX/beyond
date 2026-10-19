#!/usr/bin/env python3
"""Canonical d2 Stage-1 runner with pinned TSFM model revisions.

The implementation module keeps model loading injectable for unit tests. The
canonical workflow uses this runner so the Hugging Face model weights cannot
silently drift behind a mutable `main` ref.

Compatibility adapters in this file are transport/runtime only:
- Chronos family members may collapse singleton quantile axes differently;
- Chronos-Bolt requires list inputs to contain torch.Tensor objects, while
  Chronos-2 accepts the NumPy contexts emitted by the shared Stage-1 builder.

No candidate, feature, parameter, split, target, or selection rule is changed
by these adapters.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

import numpy as np

import ml.d2_stage1_model_tournament_v1 as impl

CHRONOS_MODEL_REVISIONS = {
    # Commit that added the Chronos-2 config + model weights.
    "amazon/chronos-2": "95a9710e2596287d08352589f42634fa5abdf0a7",
    # Initial Chronos-Bolt-small commit contains config + model weights.
    "amazon/chronos-bolt-small": "0e96a1377adca89eebae3bbde4f859dc3b9f4b46",
}


class ContextInputAdapter:
    """Adapt context-list element type while preserving all values/order.

    The converter is injectable so PR validation can verify this compatibility
    behavior without installing the heavyweight torch/Chronos runtime.
    """

    def __init__(
        self,
        pipeline: Any,
        converter: Callable[[Iterable[Any]], list[Any]],
    ) -> None:
        self._pipeline = pipeline
        self._converter = converter

    def predict_quantiles(
        self,
        inputs: Iterable[Any],
        *,
        prediction_length: int,
        quantile_levels: list[float],
        **kwargs: Any,
    ) -> Any:
        converted = self._converter(inputs)
        return self._pipeline.predict_quantiles(
            converted,
            prediction_length=prediction_length,
            quantile_levels=quantile_levels,
            **kwargs,
        )


def torch_context_converter(inputs: Iterable[Any]) -> list[Any]:
    """Convert contexts to CPU float32 torch tensors for Chronos-Bolt."""
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - only canonical TSFM runtime
        raise RuntimeError(
            "Chronos-Bolt context conversion requires the pinned torch runtime"
        ) from exc
    return [
        torch.as_tensor(np.asarray(value, dtype=np.float32), dtype=torch.float32)
        for value in inputs
    ]


def load_pinned_chronos_pipeline(model_id: str):
    try:
        import torch
        from chronos import BaseChronosPipeline
    except ImportError as exc:
        raise RuntimeError(
            "Chronos runtime missing. Install ml/requirements-d2-tsfm-v1.txt"
        ) from exc
    revision = CHRONOS_MODEL_REVISIONS.get(model_id)
    if revision is None:
        raise RuntimeError(f"no pinned revision declared for {model_id}")
    pipeline = BaseChronosPipeline.from_pretrained(
        model_id,
        revision=revision,
        device_map="cpu",
        torch_dtype=torch.float32,
    )
    # Chronos-Bolt's list-input path calls left_pad_and_stack_1D(), which
    # explicitly asserts each context is a torch.Tensor. Keep Chronos-2 on the
    # already-working NumPy path and adapt only Bolt.
    if model_id == impl.CHRONOS_BOLT_MODEL_ID:
        return ContextInputAdapter(pipeline, torch_context_converter)
    return pipeline


def normalize_quantile_output_canonical(
    quantiles: Any,
    prediction_length: int,
    batch_size: int,
) -> list[np.ndarray]:
    """Normalize Chronos-2/Bolt quantiles, including singleton horizons.

    Canonical per-series output is always `(prediction_length, 3)` for
    p10/p50/p90. Singleton batch/horizon axes may be omitted by model/runtime
    combinations, but all non-singleton dimensions remain hard validated.
    """
    if isinstance(quantiles, list):
        items = [impl._to_numpy(item) for item in quantiles]
    else:
        arr = impl._to_numpy(quantiles)
        if arr.ndim < 2:
            raise RuntimeError(f"unexpected Chronos quantile rank {arr.shape}")
        if arr.shape[0] != batch_size:
            raise RuntimeError(
                f"unexpected Chronos batch axis shape={arr.shape} expected={batch_size}"
            )
        items = [arr[index] for index in range(batch_size)]

    normalized: list[np.ndarray] = []
    for item in items:
        arr = np.asarray(item, dtype=float)
        # Remove only redundant singleton axes. For prediction_length=1 this
        # may legitimately leave a single quantile vector `(3,)`.
        arr = np.squeeze(arr)
        if arr.ndim == 1:
            if prediction_length == 1 and arr.shape == (len(impl.QUANTILE_LEVELS),):
                arr = arr.reshape(1, len(impl.QUANTILE_LEVELS))
            else:
                raise RuntimeError(
                    f"unexpected one-dimensional Chronos quantile shape {arr.shape} "
                    f"prediction_length={prediction_length}"
                )
        if arr.ndim != 2:
            raise RuntimeError(f"unexpected per-series Chronos quantile shape {arr.shape}")
        if arr.shape == (prediction_length, len(impl.QUANTILE_LEVELS)):
            pass
        elif arr.shape == (len(impl.QUANTILE_LEVELS), prediction_length):
            arr = arr.T
        else:
            raise RuntimeError(
                f"cannot normalize Chronos quantiles shape={arr.shape} "
                f"prediction_length={prediction_length}"
            )
        normalized.append(arr.astype(float))

    if len(normalized) != batch_size:
        raise RuntimeError(
            f"Chronos result batch size changed actual={len(normalized)} expected={batch_size}"
        )
    return normalized


impl.load_chronos_pipeline = load_pinned_chronos_pipeline
impl.normalize_quantile_output = normalize_quantile_output_canonical


if __name__ == "__main__":
    impl.main()
