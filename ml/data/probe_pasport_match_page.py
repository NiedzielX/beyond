#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

IDS = [18121, 18426, 18427, 18732, 18733, 19038]
UA = "Mozilla/5.0 (compatible; BeyondTicketingResearch/1.0)"


def inspect(session: requests.Session, match_id: int) -> dict:
    url = f"https://kibice.krakow.business/mecze/{match_id}"
    r = session.get(url, headers={"User-Agent": UA}, timeout=45)
    out = {"id": match_id, "url": url, "status": r.status_code, "bytes": len(r.content)}
    if r.status_code != 200:
        return out
    soup = BeautifulSoup(r.text, "html.parser")
    out["title"] = soup.title.get_text(" ", strip=True) if soup.title else None
    out["h1"] = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    out["h2"] = [h.get_text(" ", strip=True) for h in soup.find_all("h2")][:20]
    out["dl"] = [
        {
            "dt": dl.find("dt").get_text(" ", strip=True) if dl.find("dt") else None,
            "dd": dl.find("dd").get_text(" ", strip=True) if dl.find("dd") else None,
        }
        for dl in soup.find_all("dl")[:30]
    ]
    out["text_head"] = " ".join(soup.stripped_strings)[:4000]
    try:
        tables = pd.read_html(StringIO(r.text))
    except ValueError:
        tables = []
    out["tables"] = [
        {
            "rows": len(t),
            "columns": [str(c) for c in t.columns],
            "head": t.head(5).astype(str).to_dict(orient="records"),
        }
        for t in tables[:10]
    ]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    session = requests.Session()
    report = {"matches": [inspect(session, i) for i in IDS]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
