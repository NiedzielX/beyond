"""Probe TheSportsDB free v1 for Beyond sporting-context coverage.

Diagnostic only. Uses the provider-documented public free API key 123.
No database writes.
"""
from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://www.thesportsdb.com/api/v1/json/123"
SEASON = "2026-2027"
TARGET_LEAGUE = "Polish Ekstraklasa"
TARGET_LEAGUE_ID = "4422"


def fetch_json(path: str, **params):
    query = f"?{urlencode(params)}" if params else ""
    url = f"{BASE}/{path}{query}"
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "BeyondTicketingResearch/1.1"})
    with urlopen(req, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return response.status, url, json.loads(raw)


def compact_event(row: dict) -> dict:
    return {
        "idEvent": row.get("idEvent"),
        "dateEvent": row.get("dateEvent"),
        "strLeague": row.get("strLeague"),
        "strHomeTeam": row.get("strHomeTeam"),
        "strAwayTeam": row.get("strAwayTeam"),
        "idHomeTeam": row.get("idHomeTeam"),
        "idAwayTeam": row.get("idAwayTeam"),
        "intHomeScore": row.get("intHomeScore"),
        "intAwayScore": row.get("intAwayScore"),
        "strStatus": row.get("strStatus"),
        "intRound": row.get("intRound"),
    }


def is_completed(row: dict) -> bool:
    return row.get("intHomeScore") not in (None, "") and row.get("intAwayScore") not in (None, "")


def team_id_from_events(events: list[dict], team_name: str) -> str | None:
    for row in events:
        if row.get("strHomeTeam") == team_name and row.get("idHomeTeam"):
            return str(row["idHomeTeam"])
        if row.get("strAwayTeam") == team_name and row.get("idAwayTeam"):
            return str(row["idAwayTeam"])
    return None


def main() -> int:
    status, url, payload = fetch_json("search_all_leagues.php", c="Poland", s="Soccer")
    leagues = payload.get("countries") or []
    exact = [row for row in leagues if row.get("strLeague") == TARGET_LEAGUE]
    print(json.dumps({
        "step": "league",
        "status": status,
        "url": url,
        "exact_count": len(exact),
        "league_id": exact[0].get("idLeague") if exact else None,
        "current_season": exact[0].get("strCurrentSeason") if exact else None,
    }, ensure_ascii=False, indent=2))
    if not exact or str(exact[0].get("idLeague")) != TARGET_LEAGUE_ID:
        return 0

    all_round_events: list[dict] = []
    for round_number in range(1, 11):
        st, endpoint, data = fetch_json(
            "eventsround.php", id=TARGET_LEAGUE_ID, r=round_number, s=SEASON
        )
        events = data.get("events") or []
        all_round_events.extend(events)
        if round_number in (1, 8, 9, 10):
            targets = [
                compact_event(row)
                for row in events
                if any(
                    needle in str(row.get("strHomeTeam")) or needle in str(row.get("strAwayTeam"))
                    for needle in ("Lech Pozna", "Korona Kielce")
                )
            ]
            print(json.dumps({
                "step": f"round_{round_number}",
                "status": st,
                "url": endpoint,
                "event_count": len(events),
                "completed_count": sum(1 for row in events if is_completed(row)),
                "target_matches": targets,
            }, ensure_ascii=False, indent=2))

    lech_id = team_id_from_events(all_round_events, "Lech Poznań")
    korona_id = team_id_from_events(all_round_events, "Korona Kielce")
    print(json.dumps({"step": "team_ids", "Lech Poznań": lech_id, "Korona Kielce": korona_id}, ensure_ascii=False, indent=2))

    for team_name, team_id in (("Lech Poznań", lech_id), ("Korona Kielce", korona_id)):
        if not team_id:
            continue
        for path in ("eventslast.php", "eventslast.php"):
            try:
                st, endpoint, data = fetch_json(path, id=team_id)
                events = data.get("results") or data.get("events") or []
                print(json.dumps({
                    "step": f"last_events_{team_name}",
                    "status": st,
                    "url": endpoint,
                    "event_count": len(events),
                    "events": [compact_event(row) for row in events[:10]],
                }, ensure_ascii=False, indent=2))
                break
            except Exception as exc:
                print(json.dumps({"step": f"last_events_{team_name}", "error": repr(exc)}, ensure_ascii=False))

    try:
        st, endpoint, search_payload = fetch_json("searchteams.php", t="Bayer Leverkusen")
        teams = search_payload.get("teams") or []
        bayer = next((row for row in teams if "Leverkusen" in str(row.get("strTeam"))), None)
        print(json.dumps({
            "step": "bayer_team",
            "status": st,
            "url": endpoint,
            "idTeam": bayer.get("idTeam") if bayer else None,
            "strTeam": bayer.get("strTeam") if bayer else None,
        }, ensure_ascii=False, indent=2))
        if bayer and bayer.get("idTeam"):
            st, endpoint, data = fetch_json("eventslast.php", id=bayer["idTeam"])
            events = data.get("results") or data.get("events") or []
            print(json.dumps({
                "step": "last_events_Bayer",
                "status": st,
                "url": endpoint,
                "event_count": len(events),
                "events": [compact_event(row) for row in events[:10]],
            }, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"step": "last_events_Bayer", "error": repr(exc)}, ensure_ascii=False))

    print(json.dumps({
        "step": "round_probe_summary",
        "rounds_fetched": 10,
        "event_rows": len(all_round_events),
        "unique_event_ids": len({row.get('idEvent') for row in all_round_events if row.get('idEvent')}),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
