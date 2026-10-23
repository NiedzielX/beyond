#!/usr/bin/env python3
"""Research-advance governance for Beyond MAE challengers.

This layer deliberately separates a positive point estimate from a robust
research advance. It never invents the minimum practically meaningful MAE
improvement: that threshold must come from an approved business-value contract.

Frozen earlier experiment scorecards are not mutated by this module. New
experiments may call it as an interpretation/promotion layer.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Decision = Literal[
    "NO_RESEARCH_GAIN",
    "POINT_GAIN_UNCERTAINTY_LIMITED",
    "ROBUST_RESEARCH_ADVANCE",
]


@dataclass(frozen=True)
class ResearchAdvanceInput:
    incumbent_mae: float
    challenger_mae: float
    event_improvement_rate: float
    fold_improvement_rate: float
    delta_mae_ci_lower: float | None
    delta_mae_ci_upper: float | None
    minimum_meaningful_mae_improvement: float | None
    pit_pass: bool = True
    lineage_pass: bool = True
    reproducibility_pass: bool = True
    minimum_event_improvement_rate: float = 0.50
    minimum_fold_improvement_rate: float = 0.50


@dataclass(frozen=True)
class ResearchAdvanceDecision:
    version: str
    decision: Decision
    incumbent_mae: float
    challenger_mae: float
    mae_improvement: float
    relative_mae_improvement: float
    minimum_meaningful_mae_improvement: float | None
    point_gain: bool
    stability_pass: bool
    precision_pass: bool
    meaningful_gain_pass: bool
    evidence_integrity_pass: bool
    robust_advance_allowed: bool
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def decide_research_advance(value: ResearchAdvanceInput) -> ResearchAdvanceDecision:
    _validate(value)
    improvement = float(value.incumbent_mae - value.challenger_mae)
    relative = improvement / float(value.incumbent_mae)
    point_gain = improvement > 0.0
    stability_pass = (
        value.event_improvement_rate > value.minimum_event_improvement_rate
        and value.fold_improvement_rate > value.minimum_fold_improvement_rate
    )
    evidence_integrity_pass = bool(
        value.pit_pass and value.lineage_pass and value.reproducibility_pass
    )
    precision_pass = bool(
        value.delta_mae_ci_upper is not None
        and value.delta_mae_ci_upper < 0.0
    )
    meaningful_gain_pass = bool(
        value.minimum_meaningful_mae_improvement is not None
        and improvement >= value.minimum_meaningful_mae_improvement
    )

    reasons: list[str] = []
    if not point_gain:
        reasons.append("no_positive_mae_point_gain")
    if not stability_pass:
        reasons.append("event_or_fold_stability_failed")
    if not evidence_integrity_pass:
        reasons.append("evidence_integrity_failed")
    if value.minimum_meaningful_mae_improvement is None:
        reasons.append("business_meaningful_mae_threshold_not_defined")
    elif not meaningful_gain_pass:
        reasons.append("gain_below_business_meaningful_threshold")
    if value.delta_mae_ci_upper is None:
        reasons.append("delta_mae_precision_not_available")
    elif not precision_pass:
        reasons.append("delta_mae_interval_includes_no_gain")

    robust = bool(
        point_gain
        and stability_pass
        and evidence_integrity_pass
        and precision_pass
        and meaningful_gain_pass
    )

    if robust:
        decision: Decision = "ROBUST_RESEARCH_ADVANCE"
    elif point_gain and stability_pass and evidence_integrity_pass:
        decision = "POINT_GAIN_UNCERTAINTY_LIMITED"
    else:
        decision = "NO_RESEARCH_GAIN"

    return ResearchAdvanceDecision(
        version="research-advance-governance-v2",
        decision=decision,
        incumbent_mae=float(value.incumbent_mae),
        challenger_mae=float(value.challenger_mae),
        mae_improvement=improvement,
        relative_mae_improvement=relative,
        minimum_meaningful_mae_improvement=value.minimum_meaningful_mae_improvement,
        point_gain=point_gain,
        stability_pass=stability_pass,
        precision_pass=precision_pass,
        meaningful_gain_pass=meaningful_gain_pass,
        evidence_integrity_pass=evidence_integrity_pass,
        robust_advance_allowed=robust,
        reason_codes=tuple(reasons),
    )


def _validate(value: ResearchAdvanceInput) -> None:
    if value.incumbent_mae <= 0 or value.challenger_mae < 0:
        raise ValueError("MAE values must be non-negative and incumbent_mae > 0")
    for name, rate in (
        ("event_improvement_rate", value.event_improvement_rate),
        ("fold_improvement_rate", value.fold_improvement_rate),
        ("minimum_event_improvement_rate", value.minimum_event_improvement_rate),
        ("minimum_fold_improvement_rate", value.minimum_fold_improvement_rate),
    ):
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"{name} must be in [0,1]")
    if (
        value.minimum_meaningful_mae_improvement is not None
        and value.minimum_meaningful_mae_improvement <= 0
    ):
        raise ValueError("minimum meaningful MAE improvement must be > 0")
    if (
        value.delta_mae_ci_lower is not None
        and value.delta_mae_ci_upper is not None
        and value.delta_mae_ci_lower > value.delta_mae_ci_upper
    ):
        raise ValueError("invalid delta MAE interval")
