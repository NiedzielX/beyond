"""Build point-in-time target state for the recovered v1.7 T-7 forecaster.

The builder is intentionally provider-agnostic. Feed it completed league results
from any trusted source, but each row must carry the actual kickoff timestamp.
Only results whose *local calendar date* is strictly before the canonical T-7
calendar date are visible to the sporting-state features.

This reproduces the recovered v1.7 semantics and prevents accidental use of a
current/pre-kickoff table snapshot.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")


@dataclass(frozen=True)
class LeagueResult:
    kickoff_at: datetime
    home_team_key: str
    away_team_key: str
    home_goals: int
    away_goals: int

    def __post_init__(self) -> None:
        if self.kickoff_at.tzinfo is None:
            raise ValueError("LeagueResult.kickoff_at must be timezone-aware")
        if self.home_team_key == self.away_team_key:
            raise ValueError("A team cannot play itself")
        if self.home_goals < 0 or self.away_goals < 0:
            raise ValueError("Goals cannot be negative")


@dataclass
class _TeamState:
    played: int = 0
    points: int = 0
    goals_for: int = 0
    goals_against: int = 0


def _positions(states: Mapping[str, _TeamState]) -> dict[str, int]:
    """Recovered historical tie-breaker: points, GD, GF, stable team key."""
    ranking = sorted(
        states.items(),
        key=lambda item: (
            -item[1].points,
            -(item[1].goals_for - item[1].goals_against),
            -item[1].goals_for,
            item[0],
        ),
    )
    return {team: index for index, (team, _) in enumerate(ranking, start=1)}


def build_t7_static_features(
    *,
    season: str,
    target_kickoff_at: datetime,
    home_team_key: str,
    opponent_key: str,
    target_round_no: int,
    total_rounds: int,
    league_team_keys: Sequence[str],
    completed_results: Iterable[LeagueResult],
    current_season_home_attendance: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Return the exact static_features contract consumed by v1.7 T-7.

    `completed_results` may contain later matches; they are filtered internally.
    A match played on the local T-7 calendar date is deliberately excluded even
    if its kickoff happened before the target match's exact T-7 clock time.
    """
    if target_kickoff_at.tzinfo is None:
        raise ValueError("target_kickoff_at must be timezone-aware")
    if target_round_no < 1 or total_rounds < target_round_no:
        raise ValueError("Invalid target round/total rounds")

    teams = [str(team) for team in league_team_keys]
    if len(teams) != len(set(teams)):
        raise ValueError("league_team_keys must be unique")
    if home_team_key not in teams or opponent_key not in teams:
        raise ValueError("Home team and opponent must both belong to the league")

    cutoff_local_date = (
        target_kickoff_at.astimezone(WARSAW) - timedelta(days=7)
    ).date()
    states = {team: _TeamState() for team in teams}

    visible = sorted(
        (
            result
            for result in completed_results
            if result.kickoff_at.astimezone(WARSAW).date() < cutoff_local_date
        ),
        key=lambda result: result.kickoff_at,
    )

    for result in visible:
        if result.home_team_key not in states or result.away_team_key not in states:
            raise ValueError(
                f"Result contains team outside league: {result.home_team_key} vs {result.away_team_key}"
            )
        home = states[result.home_team_key]
        away = states[result.away_team_key]
        home.played += 1
        away.played += 1
        home.goals_for += result.home_goals
        home.goals_against += result.away_goals
        away.goals_for += result.away_goals
        away.goals_against += result.home_goals

        if result.home_goals > result.away_goals:
            home.points += 3
        elif result.home_goals < result.away_goals:
            away.points += 3
        else:
            home.points += 1
            away.points += 1

    position = _positions(states)
    home = states[home_team_key]
    opponent = states[opponent_key]
    matches_remaining_after = total_rounds - target_round_no
    season_progress = (target_round_no - 1) / total_rounds

    return {
        "season": season,
        "opponent_key": opponent_key,
        "target_round_no": target_round_no,
        "target_season_progress": season_progress,
        "target_matches_remaining": matches_remaining_after,
        "lech_position_at_t7": position[home_team_key],
        "opponent_position_at_t7": position[opponent_key],
        "lech_matches_played_at_t7": home.played,
        "opponent_matches_played_at_t7": opponent.played,
        "league_team_count": len(teams),
        "current_season_home_attendance": list(current_season_home_attendance or []),
        "t7_state_cutoff_local_date": cutoff_local_date.isoformat(),
        "t7_visible_league_results": len(visible),
    }
