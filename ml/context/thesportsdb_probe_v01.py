"""Probe TheSportsDB free v1 for Ekstraklasa sporting-context coverage.

Diagnostic only. Uses the provider-documented public free API key 123.
No database writes.
"""
from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://www.thesportsdb.com/api/v1/json/123"
SEASON = "2026-2027"
TARGET_LEAGUE = "Polish Ekstraklasa"


def fetch_json(path: str, **params):
    query = f"?{urlencode(params)}" if params else ""
    url = f"{BASE}/{path}{query}"
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "BeyondTicketingResearch/0.9"})
    with urlopen(req, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return response.status, url, json.loads(raw)


def compact_event(row: dict) -> dict:
    return {
        "idEvent": row.get("idEvent"),
        "dateEvent": row.get("dateEvent"),
        "strHomeTeam": row.get("strHomeTeam"),
        "strAwayTeam": row.get("strAwayTeam"),
        "intHomeScore": row.get("intHomeScore"),
        "intAwayScore": row.get("intAwayScore"),
        "strStatus": row.get("strStatus"),
        "intRound": row.get("intRound"),
    }


def main() -> int:
    status, url, payload = fetch_json("search_all_leagues.php", c="Poland", s="Soccer")
    leagues = payload.get("countries") or []
    exact = [row for row in leagues if row.get("strLeague") == TARGET_LEAGUE]
    print(json.dumps({
        "step": "leagues",
        "status": status,
        "url": url,
        "count": len(leagues),
        "exact": exact,
    }, ensure_ascii=False, indent=2))

    if not exact:
        return 0

    league = exact[0]
    league_id = str(league.get("idLeague"))

    st, endpoint, seasons_payload = fetch_json("search_all_seasons.php", id=league_id)
    seasons = [row.get("strSeason") for row in (seasons_payload.get("seasons") or [])]
    print(json.dumps({
        "step": "seasons",
        "status": st,
        "url": endpoint,
        "season_available": SEASON in seasons,
        "latest_seasons": seasons[-5:],
    }, ensure_ascii=False, indent=2))

    st, endpoint, events_payload = fetch_json("eventsseason.php", id=league_id, s=SEASON)
    events = events_payload.get("events") or []
    completed = [
        row for row in events
        if row.get("intHomeScore") not in (None, "") and row.get("intAwayScore") not in (None, "")
    ]
    completed.sort(key=lambda row: (row.get("dateEvent") or "", row.get("strTime") or ""))
    lech = [row for row in completed if "Lech Pozna" in str(row.get("strHomeTeam")) or "Lech Pozna" in str(row.get("strAwayTeam"))]
    korona = [row for row in completed if "Korona Kielce" in str(row.get("strHomeTeam")) or "Korona Kielce" in str(row.get("strAwayTeam"))]
    print(json.dumps({
        "step": "eventsseason",
        "status": st,
        "url": endpoint,
        "event_count": len(events),
        "completed_count": len(completed),
        "latest_lech": [compact_event(row) for row in lech[-5:]],
        "latest_korona": [compact_event(row) for row in korona[-5:]],
    }, ensure_ascii=False, indent=2))

    try:
        st, endpoint, table_payload = fetch_json("lookuptable.php", l=league_id, s=SEASON)
        table = table_payload.get("table") or []
        targets = [
            row for row in table
            if row.get("name") in ("Lech Poznań", "Lech Poznan", "Korona Kielce")
            or row.get("strTeam") in ("Lech Poznań", "Lech Poznan", "Korona Kielce")
        ]
        print(json.dumps({
            "step": "table",
            "status": st,
            "url": endpoint,
            "row_count": len(table),
            "targets": targets,
        }, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"step": "table", "error": repr(exc)}, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
