"""Preflight validation for exact recovered v1.7 T-7 shadow evidence.

The point model is already recovered exactly. The main remaining operational
risk is incomplete or post-checkpoint evidence. This module makes persistence
fail closed when the evidence package is not auditable.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Mapping
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")


class T7EvidenceError(ValueError):
    pass


def _dt(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise T7EvidenceError(f"Invalid {field}: {value!r}") from exc
    if parsed.tzinfo is None:
        raise T7EvidenceError(f"{field} must include a timezone")
    return parsed


def validate_t7_evidence(
    *,
    evidence: Mapping[str, Any],
    ticket_event_id: int,
    home_team: str,
    away_team: str,
    competition: str,
    kickoff_at: datetime,
    persist: bool,
) -> dict[str, Any]:
    """Validate evidence completeness and point-in-time safety.

    `expected_visible_*` fields are deliberately explicit. The runtime cannot
    infer whether a scraper/source omitted a completed match, so the evidence
    preparer must independently establish the expected counts from a trusted
    fixture/result source and record them in the package.
    """
    if kickoff_at.tzinfo is None:
        raise T7EvidenceError("kickoff_at must be timezone-aware")

    expected_event = evidence.get("ticket_event_id")
    if expected_event is not None and int(expected_event) != ticket_event_id:
        raise T7EvidenceError(
            f"Evidence event {expected_event} does not match requested event {ticket_event_id}"
        )

    expected_home = str(evidence.get("home_team", home_team)).strip()
    expected_away = str(evidence.get("away_team", away_team)).strip()
    if expected_home.casefold() != home_team.casefold():
        raise T7EvidenceError(f"Evidence home_team {expected_home!r} != {home_team!r}")
    if expected_away.casefold() != away_team.casefold():
        raise T7EvidenceError(f"Evidence away_team {expected_away!r} != {away_team!r}")

    expected_competition = str(evidence.get("competition", competition)).strip()
    if expected_competition.casefold() != competition.casefold():
        raise T7EvidenceError(
            f"Evidence competition {expected_competition!r} != {competition!r}"
        )

    evidence_kickoff = evidence.get("target_kickoff_at")
    if evidence_kickoff is not None:
        parsed = _dt(evidence_kickoff, "target_kickoff_at")
        if abs((parsed - kickoff_at).total_seconds()) > 1:
            raise T7EvidenceError(
                f"Evidence kickoff {parsed.isoformat()} != event kickoff {kickoff_at.isoformat()}"
            )

    cutoff_exact = kickoff_at - timedelta(days=7)
    cutoff_local_date = cutoff_exact.astimezone(WARSAW).date()

    league_teams = [str(team) for team in evidence.get("league_team_keys", [])]
    if len(league_teams) < 10 or len(league_teams) != len(set(league_teams)):
        raise T7EvidenceError("league_team_keys must be a unique complete league list")
    home_key = str(evidence.get("home_team_key", "lech"))
    opponent_key = str(evidence.get("opponent_key", ""))
    if home_key not in league_teams or opponent_key not in league_teams:
        raise T7EvidenceError("home_team_key and opponent_key must belong to league_team_keys")

    results = evidence.get("completed_results")
    if not isinstance(results, list):
        raise T7EvidenceError("completed_results must be a list")
    seen_results: set[tuple[str, str, str]] = set()
    for index, row in enumerate(results):
        if not isinstance(row, Mapping):
            raise T7EvidenceError(f"completed_results[{index}] must be an object")
        kickoff = _dt(row.get("kickoff_at"), f"completed_results[{index}].kickoff_at")
        home = str(row.get("home_team_key", ""))
        away = str(row.get("away_team_key", ""))
        if home not in league_teams or away not in league_teams or home == away:
            raise T7EvidenceError(f"completed_results[{index}] contains invalid teams")
        if kickoff.astimezone(WARSAW).date() >= cutoff_local_date:
            raise T7EvidenceError(
                f"completed_results[{index}] is not visible under strict T-7 calendar-date semantics"
            )
        key = (kickoff.isoformat(), home, away)
        if key in seen_results:
            raise T7EvidenceError(f"Duplicate completed result at index {index}")
        seen_results.add(key)
        for goals_field in ("home_goals", "away_goals"):
            try:
                goals = int(row[goals_field])
            except (KeyError, TypeError, ValueError) as exc:
                raise T7EvidenceError(
                    f"completed_results[{index}].{goals_field} must be an integer"
                ) from exc
            if goals < 0:
                raise T7EvidenceError(f"completed_results[{index}] has negative goals")

    home_attendance = evidence.get("current_season_home_attendance")
    if not isinstance(home_attendance, list):
        raise T7EvidenceError("current_season_home_attendance must be a list")
    seen_attendance: set[tuple[str, str]] = set()
    season = str(evidence.get("season", ""))
    visible_home_rows = 0
    for index, row in enumerate(home_attendance):
        if not isinstance(row, Mapping):
            raise T7EvidenceError(
                f"current_season_home_attendance[{index}] must be an object"
            )
        if str(row.get("season", "")) != season:
            raise T7EvidenceError(
                f"current_season_home_attendance[{index}] has a different season"
            )
        match_at = _dt(
            row.get("match_date"),
            f"current_season_home_attendance[{index}].match_date",
        )
        if match_at >= cutoff_exact:
            raise T7EvidenceError(
                f"current_season_home_attendance[{index}] is not known before exact T-7"
            )
        opponent = str(row.get("opponent_key", ""))
        if opponent not in league_teams:
            raise T7EvidenceError(
                f"current_season_home_attendance[{index}] opponent is outside the league"
            )
        try:
            attendance = int(row["attendance"])
        except (KeyError, TypeError, ValueError) as exc:
            raise T7EvidenceError(
                f"current_season_home_attendance[{index}].attendance must be an integer"
            ) from exc
        if attendance <= 0:
            raise T7EvidenceError(
                f"current_season_home_attendance[{index}] attendance must be positive"
            )
        key = (match_at.isoformat(), opponent)
        if key in seen_attendance:
            raise T7EvidenceError(f"Duplicate home attendance row at index {index}")
        seen_attendance.add(key)
        visible_home_rows += 1

    expected_results = evidence.get("expected_visible_league_results")
    expected_home_rows = evidence.get("expected_visible_home_attendance_rows")
    if persist and expected_results is None:
        raise T7EvidenceError("expected_visible_league_results is required for persistence")
    if persist and expected_home_rows is None:
        raise T7EvidenceError(
            "expected_visible_home_attendance_rows is required for persistence"
        )
    if expected_results is not None and int(expected_results) != len(results):
        raise T7EvidenceError(
            f"Expected {expected_results} visible league results, got {len(results)}"
        )
    if expected_home_rows is not None and int(expected_home_rows) != visible_home_rows:
        raise T7EvidenceError(
            f"Expected {expected_home_rows} visible Lech home attendance rows, got {visible_home_rows}"
        )

    sources = evidence.get("sources")
    if persist:
        if not isinstance(sources, Mapping):
            raise T7EvidenceError("sources audit block is required for persistence")
        for source_name in ("schedule", "league_results", "home_attendance"):
            value = sources.get(source_name)
            if not isinstance(value, list) or not value or not all(str(item).startswith("http") for item in value):
                raise T7EvidenceError(
                    f"sources.{source_name} must contain at least one source URL"
                )
        if sources.get("verified_at") is None:
            raise T7EvidenceError("sources.verified_at is required for persistence")
        _dt(sources["verified_at"], "sources.verified_at")

    return {
        "ticket_event_id": ticket_event_id,
        "cutoff_exact": cutoff_exact.isoformat(),
        "cutoff_local_date": cutoff_local_date.isoformat(),
        "league_team_count": len(league_teams),
        "visible_league_results": len(results),
        "visible_home_attendance_rows": visible_home_rows,
        "persistence_preflight": "passed" if persist else "dry_run_passed",
    }
