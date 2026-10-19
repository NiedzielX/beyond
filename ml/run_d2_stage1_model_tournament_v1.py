#!/usr/bin/env python3
"""Canonical d2 Stage-1 runner with pinned TSFM model revisions.

The implementation module keeps model loading injectable for unit tests. The
canonical workflow uses this runner so the Hugging Face model weights cannot
silently drift behind a mutable `main` ref.
"""
from __future__ import annotations

import ml.d2_stage1_model_tournament_v1 as impl

CHRONOS_MODEL_REVISIONS = {
    # Commit that added the Chronos-2 config + model weights.
    "amazon/chronos-2": "95a9710e2596287d08352589f42634fa5abdf0a7",
    # Initial Chronos-Bolt-small commit contains config + model weights.
    "amazon/chronos-bolt-small": "0e96a1377adca89eebae3bbde4f859dc3b9f4b46",
}


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
    return BaseChronosPipeline.from_pretrained(
        model_id,
        revision=revision,
        device_map="cpu",
        torch_dtype=torch.float32,
    )


impl.load_chronos_pipeline = load_pinned_chronos_pipeline


if __name__ == "__main__":
    impl.main()
