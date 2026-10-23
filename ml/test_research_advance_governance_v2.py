#!/usr/bin/env python3
from ml.research_advance_governance_v2 import ResearchAdvanceInput, decide_research_advance


def test_missing_business_threshold_caps_at_uncertainty_limited() -> None:
    result = decide_research_advance(ResearchAdvanceInput(
        incumbent_mae=3000,
        challenger_mae=2800,
        event_improvement_rate=0.70,
        fold_improvement_rate=0.75,
        delta_mae_ci_lower=-350,
        delta_mae_ci_upper=-20,
        minimum_meaningful_mae_improvement=None,
    ))
    assert result.decision == "POINT_GAIN_UNCERTAINTY_LIMITED"
    assert not result.robust_advance_allowed
    assert "business_meaningful_mae_threshold_not_defined" in result.reason_codes


def test_interval_crossing_zero_caps_at_uncertainty_limited() -> None:
    result = decide_research_advance(ResearchAdvanceInput(
        incumbent_mae=3000,
        challenger_mae=2700,
        event_improvement_rate=0.70,
        fold_improvement_rate=0.75,
        delta_mae_ci_lower=-500,
        delta_mae_ci_upper=40,
        minimum_meaningful_mae_improvement=200,
    ))
    assert result.decision == "POINT_GAIN_UNCERTAINTY_LIMITED"
    assert not result.precision_pass


def test_tiny_gain_below_threshold_is_not_robust() -> None:
    result = decide_research_advance(ResearchAdvanceInput(
        incumbent_mae=3012,
        challenger_mae=2998,
        event_improvement_rate=0.70,
        fold_improvement_rate=0.75,
        delta_mae_ci_lower=-30,
        delta_mae_ci_upper=-1,
        minimum_meaningful_mae_improvement=100,
    ))
    assert result.mae_improvement == 14
    assert result.decision == "POINT_GAIN_UNCERTAINTY_LIMITED"
    assert "gain_below_business_meaningful_threshold" in result.reason_codes


def test_robust_requires_all_gates() -> None:
    result = decide_research_advance(ResearchAdvanceInput(
        incumbent_mae=3000,
        challenger_mae=2700,
        event_improvement_rate=0.70,
        fold_improvement_rate=0.75,
        delta_mae_ci_lower=-450,
        delta_mae_ci_upper=-80,
        minimum_meaningful_mae_improvement=200,
    ))
    assert result.decision == "ROBUST_RESEARCH_ADVANCE"
    assert result.robust_advance_allowed


def test_no_point_gain_is_no_research_gain() -> None:
    result = decide_research_advance(ResearchAdvanceInput(
        incumbent_mae=3000,
        challenger_mae=3050,
        event_improvement_rate=0.70,
        fold_improvement_rate=0.75,
        delta_mae_ci_lower=-20,
        delta_mae_ci_upper=120,
        minimum_meaningful_mae_improvement=100,
    ))
    assert result.decision == "NO_RESEARCH_GAIN"


if __name__ == "__main__":
    test_missing_business_threshold_caps_at_uncertainty_limited()
    test_interval_crossing_zero_caps_at_uncertainty_limited()
    test_tiny_gain_below_threshold_is_not_robust()
    test_robust_requires_all_gates()
    test_no_point_gain_is_no_research_gain()
    print("research_advance_governance_v2 tests passed")
