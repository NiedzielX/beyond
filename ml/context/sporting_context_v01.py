"""Beyond Ticketing Sporting Context collector v0.1.

Collects point-in-time context without changing the production P50 forecast.
The collector deliberately stores raw evidence first. Heuristic matrix weights are
research priors, not trained coefficients, and normalized_score remains NULL until
a scoring rule is independently validated.

Required for all runs:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY

Optional external sporting data:
    API_FOOTBALL_KEY

If API_FOOTBALL_KEY is absent, the collector still persists static match context
from ticket_events and exits successfully after reporting that sporting API data
was skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


WARSAW = ZoneInfo("Europe/Warsaw")
API_FOOTBALL_BASE = "https://v3.football.api-sports.io"


class ContextCollectorError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class TicketEvent:
    id: int
    club_slug: str
    home_team: str
    away_team: str
    competition: str | None
    kickoff_at: datetime


class SupabaseRest:
    def __init__(self, url: str | None = None, service_role_key: str | None = None) -> None:
        self.url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.key = service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not self.url or not self.key:
            raise ContextCollectorError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    def _request(self, path: str, *, method: str = "GET", query: dict[str, str] | None = None,
                 body: Any | None = None, prefer: str | None = None) -> Any:
        url = f"{self.url}/rest/v1/{path.lstrip('/')}"
        if query:
            url += "?" + urlencode(query, safe=",.*()!:-")
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
        }
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = _json_bytes(body)
        if prefer:
            headers["Prefer"] = prefer
        request = Request(url, data=data, method=method, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ContextCollectorError(f"Supabase {method} {path} failed ({exc.code}): {detail}") from exc

    def upcoming_events(self, days: int = 30) -> list[TicketEvent]:
        start = _utc_now() - timedelta(hours=3)
        end = _utc_now() + timedelta(days=days)
        rows = self._request(
            "ticket_events",
            query={
                "select": "id,club_slug,home_team,away_team,competition,kickoff_at",
                "kickoff_at": f"gte.{_iso(start)}",
                "order": "kickoff_at.asc",
            },
        ) or []
        events: list[TicketEvent] = []
        for row in rows:
            kickoff = _parse_dt(row["kickoff_at"])
            if kickoff > end:
                continue
            events.append(TicketEvent(
                id=int(row["id"]),
                club_slug=row["club_slug"],
                home_team=row["home_team"],
                away_team=row["away_team"],
                competition=row.get("competition"),
                kickoff_at=kickoff,
            ))
        return events

    def insert_observation(self, payload: dict[str, Any]) -> None:
        self._request(
            "event_context_observations",
            method="POST",
            query={"on_conflict": "ticket_event_id,feature_key,source_name,source_record_key"},
            body=payload,
            prefer="resolution=ignore-duplicates,return=minimal",
        )


class ApiFootball:
    def __init__(self, api_key: str | None = None) -> None:
        self.key = api_key or os.environ.get("API_FOOTBALL_KEY", "")
        if not self.key:
            raise ContextCollectorError("API_FOOTBALL_KEY is required for sporting API collection")
        self._team_cache: dict[str, dict[str, Any]] = {}
        self._league_cache: dict[tuple[str, int], dict[str, Any] | None] = {}

    def get(self, endpoint: str, **params: Any) -> list[dict[str, Any]]:
        query = {key: value for key, value in params.items() if value is not None}
        url = f"{API_FOOTBALL_BASE}/{endpoint.lstrip('/')}?{urlencode(query)}"
        request = Request(url, method="GET", headers={"x-apisports-key": self.key, "Accept": "application/json"})
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ContextCollectorError(f"API-Football {endpoint} failed ({exc.code}): {detail}") from exc
        errors = payload.get("errors")
        if errors:
            raise ContextCollectorError(f"API-Football {endpoint} returned errors: {errors}")
        return payload.get("response") or []

    def resolve_team(self, name: str) -> dict[str, Any] | None:
        key = _norm(name)
        if key in self._team_cache:
            return self._team_cache[key]
        rows = self.get("teams", search=name)
        if not rows:
            self._team_cache[key] = None  # type: ignore[assignment]
            return None
        exact = [row for row in rows if _norm(row.get("team", {}).get("name", "")) == key]
        candidates = exact or rows
        poland = [row for row in candidates if _norm(row.get("team", {}).get("country", "")) == "poland"]
        chosen = (poland or candidates)[0]
        self._team_cache[key] = chosen
        return chosen

    def resolve_league(self, competition: str, season: int) -> dict[str, Any] | None:
        lookup_name = "Ekstraklasa" if "ekstraklasa" in _norm(competition) else competition
        cache_key = (_norm(lookup_name), season)
        if cache_key in self._league_cache:
            return self._league_cache[cache_key]
        rows = self.get("leagues", search=lookup_name, season=season)
        if not rows:
            self._league_cache[cache_key] = None
            return None
        poland = [row for row in rows if _norm(row.get("country", {}).get("name", "")) == "poland"]
        chosen = (poland or rows)[0]
        self._league_cache[cache_key] = chosen
        return chosen

    def last_five(self, team_id: int) -> dict[str, Any]:
        fixtures = self.get("fixtures", team=team_id, last=5, status="FT")
        wins = draws = losses = gf = ga = 0
        ordered: list[dict[str, Any]] = []
        for row in fixtures:
            teams = row.get("teams", {})
            goals = row.get("goals", {})
            home = teams.get("home", {})
            away = teams.get("away", {})
            home_goals = goals.get("home")
            away_goals = goals.get("away")
            if home_goals is None or away_goals is None:
                continue
            is_home = int(home.get("id")) == team_id
            scored = int(home_goals if is_home else away_goals)
            conceded = int(away_goals if is_home else home_goals)
            gf += scored
            ga += conceded
            if scored > conceded:
                wins += 1
                result = "W"
            elif scored == conceded:
                draws += 1
                result = "D"
            else:
                losses += 1
                result = "L"
            ordered.append({
                "fixture_id": row.get("fixture", {}).get("id"),
                "date": row.get("fixture", {}).get("date"),
                "result": result,
                "goals_for": scored,
                "goals_against": conceded,
            })
        return {
            "matches": len(ordered),
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "points": wins * 3 + draws,
            "goals_for": gf,
            "goals_against": ga,
            "goal_difference": gf - ga,
            "fixtures": ordered,
        }

    def standings(self, league_id: int, season: int) -> list[dict[str, Any]]:
        rows = self.get("standings", league=league_id, season=season)
        if not rows:
            return []
        groups = rows[0].get("league", {}).get("standings", [])
        return [entry for group in groups for entry in group]

    def injuries(self, *, league_id: int, season: int, team_id: int) -> list[dict[str, Any]]:
        return self.get("injuries", league=league_id, season=season, team=team_id)


def _observation(event: TicketEvent, feature_key: str, *, source_name: str,
                 source_record_key: str, observed_at: datetime, text_value: str | None = None,
                 numeric_value: float | int | None = None, confidence: float | None = None,
                 source_url: str | None = None, source_observed_at: datetime | None = None,
                 metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ticket_event_id": event.id,
        "feature_key": feature_key,
        "observed_at": _iso(observed_at),
        "source_name": source_name,
        "source_record_key": source_record_key,
        "metadata": metadata or {},
    }
    if text_value is not None:
        payload["text_value"] = text_value
    if numeric_value is not None:
        payload["numeric_value"] = numeric_value
    if confidence is not None:
        payload["confidence"] = confidence
    if source_url is not None:
        payload["source_url"] = source_url
    if source_observed_at is not None:
        payload["source_observed_at"] = _iso(source_observed_at)
    return payload


def persist_static_match_context(db: SupabaseRest, event: TicketEvent, observed_at: datetime) -> int:
    local = event.kickoff_at.astimezone(WARSAW)
    timing_key = f"ticket-events:timing:v1:{event.id}"
    db.insert_observation(_observation(
        event,
        "match.timing",
        source_name="ticket_events",
        source_record_key=timing_key,
        observed_at=observed_at,
        text_value=f"{local.strftime('%A')} {local.strftime('%H:%M')} Europe/Warsaw",
        confidence=1.0,
        metadata={
            "weekday": local.strftime("%A"),
            "weekday_iso": local.isoweekday(),
            "local_hour": local.hour,
            "local_minute": local.minute,
            "kickoff_at": _iso(event.kickoff_at),
        },
    ))
    competition = event.competition or "unknown"
    db.insert_observation(_observation(
        event,
        "match.competition_stage",
        source_name="ticket_events",
        source_record_key=f"ticket-events:competition:v1:{event.id}",
        observed_at=observed_at,
        text_value=competition,
        confidence=1.0,
        metadata={"competition": competition, "stage": None},
    ))
    return 2


def _find_standing(standings: Iterable[dict[str, Any]], team_id: int) -> dict[str, Any] | None:
    for row in standings:
        if int(row.get("team", {}).get("id", -1)) == team_id:
            return row
    return None


def persist_sporting_context(db: SupabaseRest, api: ApiFootball, event: TicketEvent,
                             observed_at: datetime) -> int:
    home_row = api.resolve_team(event.home_team)
    away_row = api.resolve_team(event.away_team)
    if not home_row or not away_row:
        print(f"event {event.id}: team resolution failed; sporting context skipped")
        return 0

    home_team = home_row["team"]
    away_team = away_row["team"]
    home_id = int(home_team["id"])
    away_id = int(away_team["id"])
    hour_key = observed_at.astimezone(timezone.utc).strftime("%Y%m%dT%H")
    inserted = 0

    home_form = api.last_five(home_id)
    away_form = api.last_five(away_id)
    form_text = (
        f"{event.home_team}: {home_form['points']}/15; "
        f"{event.away_team}: {away_form['points']}/15"
    )
    db.insert_observation(_observation(
        event,
        "sport.form5",
        source_name="API-Football",
        source_record_key=f"api-football:form5:v1:{event.id}:{hour_key}",
        observed_at=observed_at,
        text_value=form_text,
        confidence=0.95 if home_form["matches"] == 5 and away_form["matches"] == 5 else 0.7,
        metadata={
            "home_team": {"id": home_id, "name": home_team["name"], "form5": home_form},
            "away_team": {"id": away_id, "name": away_team["name"], "form5": away_form},
            "scoring_status": "raw_only_not_model_scored",
        },
    ))
    inserted += 1

    competition = event.competition or ""
    season = event.kickoff_at.astimezone(WARSAW).year
    league_row = api.resolve_league(competition, season) if competition else None
    if not league_row:
        return inserted

    league = league_row["league"]
    league_id = int(league["id"])
    table = api.standings(league_id, season)
    home_standing = _find_standing(table, home_id)
    away_standing = _find_standing(table, away_id)
    if home_standing or away_standing:
        summary = {
            "league_id": league_id,
            "league_name": league.get("name"),
            "season": season,
            "home": home_standing,
            "away": away_standing,
            "scoring_status": "raw_standings_only_stakes_rule_not_yet_promoted",
        }
        db.insert_observation(_observation(
            event,
            "sport.match_stakes",
            source_name="API-Football",
            source_record_key=f"api-football:standings:v1:{event.id}:{hour_key}",
            observed_at=observed_at,
            text_value=(
                f"{event.home_team} rank {home_standing.get('rank') if home_standing else '?'}; "
                f"{event.away_team} rank {away_standing.get('rank') if away_standing else '?'}"
            ),
            confidence=0.95,
            metadata=summary,
        ))
        inserted += 1

    home_injuries = api.injuries(league_id=league_id, season=season, team_id=home_id)
    away_injuries = api.injuries(league_id=league_id, season=season, team_id=away_id)
    db.insert_observation(_observation(
        event,
        "sport.absence_impact",
        source_name="API-Football",
        source_record_key=f"api-football:injuries:v1:{event.id}:{hour_key}",
        observed_at=observed_at,
        text_value=f"raw absences: home={len(home_injuries)}, away={len(away_injuries)}; impact not scored",
        confidence=0.8,
        metadata={
            "home_team": {"id": home_id, "injuries": home_injuries},
            "away_team": {"id": away_id, "injuries": away_injuries},
            "scoring_status": "raw_absences_only_player_importance_not_yet_scored",
        },
    ))
    inserted += 1
    return inserted


def run(days: int = 30) -> dict[str, Any]:
    observed_at = _utc_now()
    db = SupabaseRest()
    events = db.upcoming_events(days=days)
    counts = {"events": len(events), "static_observations": 0, "sporting_observations": 0}

    for event in events:
        counts["static_observations"] += persist_static_match_context(db, event, observed_at)

    api_key = os.environ.get("API_FOOTBALL_KEY", "").strip()
    if not api_key:
        counts["sporting_api_status"] = "skipped_missing_API_FOOTBALL_KEY"
        print(json.dumps(counts, ensure_ascii=False))
        return counts

    api = ApiFootball(api_key)
    for event in events:
        try:
            counts["sporting_observations"] += persist_sporting_context(db, api, event, observed_at)
        except ContextCollectorError as exc:
            # Fail per event, not for the entire batch. This preserves available evidence
            # while making the failing event visible in Actions logs.
            print(f"event {event.id}: {exc}")

    counts["sporting_api_status"] = "attempted"
    print(json.dumps(counts, ensure_ascii=False))
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Beyond point-in-time sporting context")
    parser.add_argument("--days", type=int, default=30, help="Upcoming-event horizon in days")
    args = parser.parse_args()
    run(days=args.days)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
