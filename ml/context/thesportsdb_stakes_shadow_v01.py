"""Build research-only Ekstraklasa match-stakes samples from TheSportsDB v1.

The collector intentionally writes no database data itself. It consumes a signed
Beyond config file, reconstructs the current league table from complete round
endpoints, computes the existing transparent stakes heuristic, and emits a
payload for the OIDC-protected Supabase ingest endpoint.

This is SHADOW evidence. It must not replace verified sporting context or modify
production P10/P50/P90.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ml.context.context_scoring_v01 import LeagueStakesInput, league_match_stakes_v01

BASE = "https://www.thesportsdb.com/api/v1/json/123"
LEAGUE_ID = "4422"
SEASON = "2026-2027"
SOURCE_NAME = "TheSportsDB v1 shadow"
ROUND_LIMIT = 34
REQUEST_SPACING_SECONDS = 2.1  # keep sustained traffic below 30 requests/minute


@dataclass
class TeamStanding:
    team: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0
    rank: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


TEAM_ALIASES = {
    "kghm zaglebie lubin": "zaglebie lubin",
}


def canonical_team(value: str) -> str:
    normalized = normalize(value)
    return TEAM_ALIASES.get(normalized, normalized)


def fetch_json(path: str, **params: Any) -> dict[str, Any]:
    query = f"?{urlencode(params)}" if params else ""
    url = f"{BASE}/{path}{query}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "BeyondTicketingResearch/1.2",
        },
    )
    with urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def is_completed(row: dict[str, Any]) -> bool:
    return row.get("intHomeScore") not in (None, "") and row.get("intAwayScore") not in (None, "")


def completed_matches_from_rounds() -> tuple[list[dict[str, Any]], int, int]:
    completed: list[dict[str, Any]] = []
    rounds_requested = 0
    last_round_with_completed = 0

    for round_number in range(1, ROUND_LIMIT + 1):
        if rounds_requested:
            time.sleep(REQUEST_SPACING_SECONDS)
        payload = fetch_json("eventsround.php", id=LEAGUE_ID, r=round_number, s=SEASON)
        rounds_requested += 1
        events = payload.get("events") or []
        round_completed = [row for row in events if is_completed(row)]
        completed.extend(round_completed)

        if round_completed:
            last_round_with_completed = round_number

        # Once the next scheduled round is entirely unplayed, later rounds are
        # irrelevant to the point-in-time standings and we stop polling.
        if events and not round_completed and last_round_with_completed > 0:
            break
        if not events and last_round_with_completed > 0 and round_number > last_round_with_completed:
            break

    return completed, last_round_with_completed, rounds_requested


def build_standings(matches: list[dict[str, Any]]) -> list[TeamStanding]:
    table: dict[str, TeamStanding] = {}

    def row_for(team_name: str) -> TeamStanding:
        key = canonical_team(team_name)
        if key not in table:
            table[key] = TeamStanding(team=team_name)
        return table[key]

    for match in matches:
        home = row_for(str(match.get("strHomeTeam") or ""))
        away = row_for(str(match.get("strAwayTeam") or ""))
        home_score = int(match["intHomeScore"])
        away_score = int(match["intAwayScore"])

        home.played += 1
        away.played += 1
        home.goals_for += home_score
        home.goals_against += away_score
        away.goals_for += away_score
        away.goals_against += home_score

        if home_score > away_score:
            home.wins += 1
            away.losses += 1
            home.points += 3
        elif home_score < away_score:
            away.wins += 1
            home.losses += 1
            away.points += 3
        else:
            home.draws += 1
            away.draws += 1
            home.points += 1
            away.points += 1

    ordered = sorted(
        table.values(),
        key=lambda item: (-item.points, -item.goal_difference, -item.goals_for, canonical_team(item.team)),
    )
    for index, standing in enumerate(ordered, start=1):
        standing.rank = index
    return ordered


def standings_index(standings: list[TeamStanding]) -> dict[str, TeamStanding]:
    return {canonical_team(item.team): item for item in standings}


def tie_break_ambiguous(standings: list[TeamStanding], standing: TeamStanding) -> bool:
    for other in standings:
        if other.team == standing.team:
            continue
        if other.points == standing.points and abs(other.rank - standing.rank) <= 1:
            return True
    return False


def build_samples(config: dict[str, Any], observed_at: datetime) -> dict[str, Any]:
    events = config.get("events") or []
    matches, last_completed_round, rounds_requested = completed_matches_from_rounds()
    standings = build_standings(matches)
    index = standings_index(standings)
    samples: list[dict[str, Any]] = []

    for event in events:
        home = index.get(canonical_team(str(event.get("homeTeam") or "")))
        away = index.get(canonical_team(str(event.get("awayTeam") or "")))
        if not home or not away:
            samples.append({
                "ticketEventId": int(event["id"]),
                "featureKey": "sport.match_stakes",
                "status": "unmatched_team",
                "homeTeam": event.get("homeTeam"),
                "awayTeam": event.get("awayTeam"),
            })
            continue

        score = league_match_stakes_v01(
            LeagueStakesInput(
                home_rank=home.rank,
                away_rank=away.rank,
                home_points=home.points,
                away_points=away.points,
                home_played=home.played,
                away_played=away.played,
                total_rounds=34,
            )
        )
        ambiguous = tie_break_ambiguous(standings, home) or tie_break_ambiguous(standings, away)
        confidence = 0.68 if ambiguous else 0.76
        samples.append({
            "ticketEventId": int(event["id"]),
            "featureKey": "sport.match_stakes",
            "status": "ready",
            "numericValue": score["score"],
            "textValue": (
                f"{event['homeTeam']}: {home.rank}. miejsce, {home.points} pkt/{home.played}; "
                f"{event['awayTeam']}: {away.rank}. miejsce, {away.points} pkt/{away.played}"
            ),
            "confidence": confidence,
            "metadata": {
                "home": asdict(home) | {"goal_difference": home.goal_difference},
                "away": asdict(away) | {"goal_difference": away.goal_difference},
                "score_components": score.get("components"),
                "season_progress": score.get("season_progress"),
                "home_zone": score.get("home_zone"),
                "point_gap": score.get("point_gap"),
                "rank_gap": score.get("rank_gap"),
                "rank_method": "points_goal_difference_goals_for_shadow",
                "tie_break_ambiguous": ambiguous,
                "source_tier": "free_v1_shadow_not_canonical",
                "scoring_status": "research_heuristic_not_model_active",
            },
        })

    snapshot_key = (
        f"thesportsdb:league:{LEAGUE_ID}:season:{SEASON}:"
        f"through-round:{last_completed_round}:at:{observed_at.strftime('%Y%m%dT%H')}"
    )
    return {
        "observedAt": observed_at.isoformat().replace("+00:00", "Z"),
        "sourceName": SOURCE_NAME,
        "sourceSnapshotKey": snapshot_key,
        "leagueId": LEAGUE_ID,
        "season": SEASON,
        "lastCompletedRound": last_completed_round,
        "roundsRequested": rounds_requested,
        "matchesUsed": len(matches),
        "samples": samples,
        "standings": [asdict(row) | {"goal_difference": row.goal_difference} for row in standings],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    if not config.get("ok"):
        raise RuntimeError(f"Config endpoint returned failure: {config}")
    payload = build_samples(config, datetime.now(timezone.utc))
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(json.dumps({
        "source": payload["sourceName"],
        "last_completed_round": payload["lastCompletedRound"],
        "rounds_requested": payload["roundsRequested"],
        "matches_used": payload["matchesUsed"],
        "standings": [
            {"rank": row["rank"], "team": row["team"], "played": row["played"], "points": row["points"], "gd": row["goal_difference"]}
            for row in payload["standings"]
        ],
        "samples": payload["samples"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
