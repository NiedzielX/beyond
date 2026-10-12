"""Transparent research-only context scoring v0.1.

These scores are heuristics for research / dashboard interpretation only.
They MUST NOT modify production P10/P50/P90 until validated out-of-sample.
"""
from __future__ import annotations

from dataclasses import dataclass


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class LeagueStakesInput:
    home_rank: int
    away_rank: int
    home_points: int
    away_points: int
    home_played: int
    away_played: int
    total_rounds: int = 34


def league_match_stakes_v01(data: LeagueStakesInput) -> dict:
    """Score league-match stakes on a 0-100 research scale.

    Design goals:
    - early-season table position matters, but less than late-season consequence;
    - direct table clashes add urgency;
    - rivalry/opponent attractiveness is intentionally excluded because it is a
      separate feature in the Context Matrix.
    """
    avg_played = (data.home_played + data.away_played) / 2.0
    progress = min(max(avg_played / data.total_rounds, 0.0), 1.0)

    base = 20.0
    progress_component = 25.0 * progress

    if data.home_rank <= 2:
        home_zone_component = 15.0
        home_zone = "title/champions-league-zone"
    elif data.home_rank <= 4:
        home_zone_component = 12.0
        home_zone = "europe-zone"
    elif data.home_rank >= 16:
        home_zone_component = 15.0
        home_zone = "relegation-zone"
    elif data.home_rank <= 6 or data.home_rank >= 14:
        home_zone_component = 6.0
        home_zone = "zone-proximity"
    else:
        home_zone_component = 3.0
        home_zone = "mid-table"

    point_gap = abs(data.home_points - data.away_points)
    rank_gap = abs(data.home_rank - data.away_rank)
    if point_gap <= 3 and rank_gap <= 3:
        direct_clash_component = 10.0
    elif point_gap <= 6 and rank_gap <= 5:
        direct_clash_component = 5.0
    else:
        direct_clash_component = 0.0

    endgame_component = 0.0
    if progress >= 0.75 and home_zone_component >= 12.0:
        endgame_component = 15.0 * ((progress - 0.75) / 0.25)

    score = _clamp(
        base
        + progress_component
        + home_zone_component
        + direct_clash_component
        + endgame_component
    )
    return {
        "score": round(score, 1),
        "components": {
            "base": round(base, 1),
            "season_progress": round(progress_component, 1),
            "home_zone": round(home_zone_component, 1),
            "direct_table_clash": round(direct_clash_component, 1),
            "endgame": round(endgame_component, 1),
        },
        "season_progress": round(progress, 4),
        "home_zone": home_zone,
        "point_gap": point_gap,
        "rank_gap": rank_gap,
        "status": "research_heuristic_not_model_active",
    }


def european_league_phase_stakes_v01(
    *, matchday: int, total_matchdays: int = 8, home_points_before: int | None = None
) -> dict:
    """Research stakes score for a UEFA-style league phase.

    Opponent prestige is excluded and belongs in rivalry/opponent attractiveness.
    """
    base = 45.0
    progress = 0.0 if total_matchdays <= 1 else (matchday - 1) / (total_matchdays - 1)
    progress_component = 10.0 * min(max(progress, 0.0), 1.0)

    if home_points_before is None:
        pressure_component = 0.0
    elif home_points_before == 0:
        pressure_component = 8.0
    elif home_points_before == 1:
        pressure_component = 4.0
    else:
        pressure_component = 0.0

    score = _clamp(base + progress_component + pressure_component)
    return {
        "score": round(score, 1),
        "components": {
            "base_european_competition": round(base, 1),
            "league_phase_progress": round(progress_component, 1),
            "previous_result_pressure": round(pressure_component, 1),
        },
        "status": "research_heuristic_not_model_active",
    }


def absence_demand_shock_v01(
    *, player_salience: float | None, absence_certainty: float, novelty: float
) -> dict:
    """Estimate ticket-demand shock from an absence, not sporting-performance loss.

    Inputs are 0..1. If player salience is not evidenced, the function refuses to
    invent a score. Long-known injuries should have low novelty even when the
    absence itself is certain.
    """
    if player_salience is None:
        return {
            "score": None,
            "status": "insufficient_evidence_player_salience",
            "absence_certainty": absence_certainty,
            "novelty": novelty,
        }
    score = 100.0 * player_salience * absence_certainty * novelty
    return {
        "score": round(_clamp(score), 1),
        "status": "research_heuristic_not_model_active",
        "player_salience": player_salience,
        "absence_certainty": absence_certainty,
        "novelty": novelty,
    }
