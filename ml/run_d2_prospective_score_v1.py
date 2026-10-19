#!/usr/bin/env python3
"""Canonical compatibility runner for d2 prospective scoring.

Uses the same semantic Pre-Live freeze verifier and early-season sporting-state
adapter as canonical Stage-0 replay. This wrapper does not change model/policy
logic, training lineage, event eligibility, or scoring.
"""
from __future__ import annotations

import ml.d2_prospective_score_v1 as prospective
import ml.run_d2_live_replay_anchor_v1 as stage0_runner

prospective.load_and_verify_freeze_manifest = (
    stage0_runner.load_and_verify_freeze_manifest_semantic
)


if __name__ == "__main__":
    prospective.main()
