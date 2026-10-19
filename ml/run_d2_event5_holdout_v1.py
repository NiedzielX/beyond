#!/usr/bin/env python3
"""Canonical compatibility runner for the d2 event-5 holdout.

The holdout must use the exact same Pre-Live v2 semantic-manifest verifier and
early-season sporting-state compatibility adapter as the already-canonical
Stage-0 replay. This wrapper changes replay compatibility only; it does not
change the frozen Ridge expert, P2 policy, holdout split, features, target, or
scoring logic.
"""
from __future__ import annotations

import ml.d2_event5_holdout_v1 as holdout
import ml.run_d2_live_replay_anchor_v1 as stage0_runner

# Importing stage0_runner applies the canonical current-replay sporting-state
# adapter in the shared c1 replay namespace. Replace the old raw-byte freeze
# verifier with the canonical semantic verifier used by the green Stage-0 run.
holdout.load_and_verify_freeze_manifest = (
    stage0_runner.load_and_verify_freeze_manifest_semantic
)


if __name__ == "__main__":
    holdout.main()
