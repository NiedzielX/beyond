#!/usr/bin/env python3
"""Canonical runner for C2 Context Extension v2.

The challenger feature store contains new `ctx_*` columns. The frozen A2+B2
baseline must never see them, because the generic Structural Prior feature
selector discovers numeric columns dynamically.

This runner strips all C2 columns only for frozen baseline reproduction while
leaving the augmented store intact for context challengers. Hard frozen-stack
MAE assertions in the experiment then verify that the baseline remains exactly
unchanged.
"""
from __future__ import annotations

import ml.context_extension_v2 as impl

_ORIGINAL_FROZEN_STACK = impl.frozen_stack_for_season


def frozen_stack_without_context(
    store,
    horizon: str,
    season: str,
    training_seasons: list[str],
):
    base_store = store.drop(columns=list(impl.ALL_CONTEXT_COLUMNS), errors="ignore")
    return _ORIGINAL_FROZEN_STACK(base_store, horizon, season, training_seasons)


impl.frozen_stack_for_season = frozen_stack_without_context


if __name__ == "__main__":
    impl.main()
