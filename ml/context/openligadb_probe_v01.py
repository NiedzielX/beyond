"""Probe OpenLigaDB as a no-key sporting-context source.

Diagnostic only. Prints whether the 2026 league catalogue contains Polish
competitions / Ekstraklasa-like entries. No database writes.
"""
from __future__ import annotations

import json
from urllib.request import Request, urlopen


URLS = [
    "https://api.openligadb.de/getavailableleagues/2026",
    "https://api.openligadb.de/getavailableleagues",
]


def fetch_json(url: str):
    req = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "BeyondTicketingResearch/0.7",
        },
    )
    with urlopen(req, timeout=30) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def main() -> int:
    for url in URLS:
        try:
            status, payload = fetch_json(url)
            rows = payload if isinstance(payload, list) else []
            candidates = [
                row
                for row in rows
                if any(
                    token in json.dumps(row, ensure_ascii=False).casefold()
                    for token in ("poland", "polska", "ekstraklasa", "lech pozn", "legia")
                )
            ]
            print(json.dumps({
                "url": url,
                "status": status,
                "row_count": len(rows),
                "polish_candidates": candidates,
            }, ensure_ascii=False, indent=2))
        except Exception as exc:
            print(json.dumps({"url": url, "error": repr(exc)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
