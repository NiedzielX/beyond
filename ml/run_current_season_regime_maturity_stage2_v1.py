#!/usr/bin/env python3
"""Canonical compatibility runner for b2 maturity Stage 2.

Stage 2 was authored against the earlier internal source label
`ewma_residual_fraction`. Canonical Stage-1 v1 on main now names the exact same
signal `ewma50_residual_fraction` and exposes additional signal families.

This runner patches only the enum label so Stage 2 reuses the exact frozen
Stage-1 selected policies:
- T-7: ewma50-resid-k6-cap05
- T-3: ewma50-resid-k2-cap05
- T-1: ewma50-resid-k6-cap05

No parameters, predictions, thresholds, or selection rules are changed.
"""
from __future__ import annotations

import ml.current_season_regime_maturity_stage2_v1 as impl
from ml.current_season_residual_regime_v1 import RegimeVariant

impl.STAGE1_VARIANTS = {
    "T-7": RegimeVariant(source="ewma50_residual_fraction", shrink_k=6),
    "T-3": RegimeVariant(source="ewma50_residual_fraction", shrink_k=2),
    "T-1": RegimeVariant(source="ewma50_residual_fraction", shrink_k=6),
}


if __name__ == "__main__":
    impl.main()
