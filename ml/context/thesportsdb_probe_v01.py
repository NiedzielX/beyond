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


def fetch_json(path: str, **params):
    query = f"?{urlencode(params)}" if params else ""
    url = f"{BASE}/{path}{query}"
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "BeyondTicketingResearch/0.8"})
    with urlopen(req, timeout=30) as response:
        return response.status, url, json.loads(response.read().decode("utf-8"))


def main() -> int:
    status, url, payload = fetch_json("search_all_leagues.php", c="Poland", s="Soccer")
    leagues = payload.get("countries") or []
    candidates = [
        row for row in leagues
        if any(token in json.dumps(row, ensure_ascii=False).casefold() for token in ("ekstraklasa", "polish first", "poland 1"))
    ]
    print(json.dumps({"step": "leagues", "status": status, "url": url, "count": len(leagues), "candidates": candidates}, ensure_ascii=False, indent=2))

    if not candidates:
        return 0

    league = candidates[0]
    league_id = str(league.get("idLeague"))

    for path, params in [
        ("search_all_seasons.php", {"id": league_id}),
        ("eventsseason.php", {"id": league_id, "s": SEASON}),
        ("lookuptable.php", {"l": league_id, "s": SEASON}),
    ]:
        try:
            st, endpoint, data = fetch_json(path, **params)
            print(json.dumps({
                "step": path,
                "status": st,
                "url": endpoint,
                "keys": list(data.keys()) if isinstance(data, dict) else [],
                "preview": data,
            }, ensure_ascii=False, indent=2)[:30000])
        except Exception as exc:
            print(json.dumps({"step": path, "error": repr(exc)}, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
