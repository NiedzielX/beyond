#!/usr/bin/env python3
"""Frozen evidence-class boundary for d2 prospective accumulation.

Only events whose kickoff occurs after the canonical Stage-2 freeze may count
as genuinely post-freeze prospective evidence for promotion. Earlier events
that were not used in development may still be useful delayed-label holdouts,
but must not inflate the true prospective sample size.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from ml.d2_live_replay_anchor_v1 import utc_timestamp

# Canonical Stage-2 main workflow run 39308629738 completed at 19:11:01 UTC.
STAGE2_FREEZE_CUTOFF_AT = pd.Timestamp("2026-10-19T19:11:01Z")

EVIDENCE_DELAYED_LABEL = "DELAYED_LABEL_HOLDOUT"
EVIDENCE_TRUE_PROSPECTIVE = "TRUE_POST_FREEZE_PROSPECTIVE"


def evidence_class(kickoff_at: Any) -> str:
    kickoff = utc_timestamp(kickoff_at)
    return (
        EVIDENCE_TRUE_PROSPECTIVE
        if kickoff > STAGE2_FREEZE_CUTOFF_AT
        else EVIDENCE_DELAYED_LABEL
    )


def counts_toward_true_prospective_promotion_evidence(kickoff_at: Any) -> bool:
    return evidence_class(kickoff_at) == EVIDENCE_TRUE_PROSPECTIVE
