#!/usr/bin/env python3
"""Compatibility runner for the d2 long72 anchor-contract replay.

Reuses the already-audited d2 early-season sporting-state adapter introduced in
`run_d2_live_replay_anchor_v1.py` for the exact same reason: the first home
matches of a new league season can occur before any completed sporting-state
row exists for the participating club.

The adapter is local to offline d2 replay. Shared production materialization is
not changed, no fixture outcome is injected, and zero-match clubs receive only
PIT-safe zero/NaN pre-season state.
"""
from __future__ import annotations

import ml.c1_alpha_model_tournament_v1 as c1
import ml.d2_long72_anchor_contract_v1 as long72
from ml.run_d2_live_replay_anchor_v1 import complete_sporting_state

# Keep the compatibility behavior explicit in this runner even though importing
# the audited Stage-0 runner already patches the same module namespace.
c1.build_sporting_state = complete_sporting_state


if __name__ == "__main__":
    long72.main()
