#!/usr/bin/env python3
"""Canonical CI runner for unresolved-horizon multi-fold tournament v1.

The reused Stage-1 verify_incumbent() helper has predeclared development MAE
only for 2023/24. The new 2022/23 rolling fold is legitimate development
evidence but has no predeclared canonical expected MAE. This runner marks
only that fold as `early_development`, which makes the inherited verifier a
no-op there while preserving hard assertions for 2023/24 and both reference
holdouts.
"""
from __future__ import annotations

from typing import Any

import ml.unresolved_horizon_multifold_tournament_v1 as impl

_ORIGINAL_SCORE_FOLD = impl.score_fold


def score_fold_with_explicit_early_development(
    store,
    horizon: str,
    test_season: str,
    training_seasons: list[str],
    candidates,
    groups: dict[str, list[str]],
    split_kind: str,
) -> dict[str, Any]:
    effective_split_kind = split_kind
    if split_kind == "development" and test_season == "2022/2023":
        effective_split_kind = "early_development"

    result = _ORIGINAL_SCORE_FOLD(
        store,
        horizon,
        test_season,
        training_seasons,
        candidates,
        groups,
        effective_split_kind,
    )
    result["protocol_split_kind"] = split_kind
    result["benchmark_assertion"] = (
        "NO_PREDECLARED_CANONICAL_EXPECTED_MAE"
        if effective_split_kind == "early_development"
        else "HARD_ASSERTED_CANONICAL_INCUMBENT_MAE"
    )
    return result


impl.score_fold = score_fold_with_explicit_early_development


if __name__ == "__main__":
    impl.main()
