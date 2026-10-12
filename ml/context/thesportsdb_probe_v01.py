"""Probe TheSportsDB free v1 for Ekstraklasa sporting-context coverage.

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
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "BeyondTicketingResearch/1.0"})
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


def is_completed(row: dict) -> bool:
    return row.get("intHomeScore") not in (None, "") and row.get("intAwayScore") not in (None, "")


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

    round_rows: dict[int, list[dict]] = {}
    for round_number in (1, 8, 9, 10):
        try:
            st, endpoint, data = fetch_json(
                "eventsround.php",
                id=TARGET_LEAGUE_ID,
                r=round_number,
                s=SEASON,
            )
            events = data.get("events") or []
            round_rows[round_number] = events
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
        except Exception as exc:
            print(json.dumps({"step": f"round_{round_number}", "error": repr(exc)}, ensure_ascii=False))

    all_events = [row for rows in round_rows.values() for row in rows]
    unique_ids = {row.get("idEvent") for row in all_events if row.get("idEvent")}
    print(json.dumps({
        "step": "round_probe_summary",
        "rounds_tested": sorted(round_rows),
        "counts": {str(r): len(rows) for r, rows in round_rows.items()},
        "unique_event_ids": len(unique_ids),
        "all_rounds_have_expected_9": all(len(rows) == 9 for rows in round_rows.values()),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
