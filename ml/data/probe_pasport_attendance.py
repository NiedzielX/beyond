#!/usr/bin/env python3
"""Probe Paszport Kibica Ekstraklasa archive structure without persisting data.

Checks both the competition route and the dedicated season route. The latter is
indexed publicly as "Wszystkie mecze sezonu" and may expose the complete 306-row
match table without pagination.
"""
from __future__ import annotations

import argparse
import json
import re
from io import StringIO
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

SEASONS = ["2022-23", "2023-24", "2024-25"]
ROUTES = {
    "competition": "https://kibice.krakow.business/rozgrywki/ekstraklasa-{season}",
    "season": "https://kibice.krakow.business/sezon/{season}",
}
UA = "Mozilla/5.0 (compatible; BeyondTicketingResearch/1.0)"


def probe_url(session: requests.Session, season: str, route_name: str, template: str) -> dict:
    url = template.format(season=season)
    response = session.get(url, headers={"User-Agent": UA}, timeout=45)
    result = {
        "season": season,
        "route": route_name,
        "url": url,
        "status_code": response.status_code,
        "bytes": len(response.content),
        "tables": [],
        "candidate_links": [],
        "forms": [],
    }
    if response.status_code != 200:
        return result

    html = response.text
    try:
        tables = pd.read_html(StringIO(html))
    except ValueError:
        tables = []
    for i, table in enumerate(tables):
        result["tables"].append({
            "index": i,
            "rows": int(len(table)),
            "columns": [str(c) for c in table.columns],
            "head": table.head(3).astype(str).to_dict(orient="records"),
            "tail": table.tail(3).astype(str).to_dict(orient="records"),
        })

    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(url, anchor["href"])
        text = " ".join(anchor.stripped_strings)
        fingerprint = f"{href}|{text}"
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        haystack = (href + " " + text).lower()
        if any(token in haystack for token in ["page", "strona", "next", "nast", "więcej", "wiecej", "306", "mecz"]):
            result["candidate_links"].append({"href": href, "text": text})

    for form in soup.find_all("form"):
        result["forms"].append({
            "action": urljoin(url, form.get("action") or ""),
            "method": (form.get("method") or "get").lower(),
            "inputs": [
                {"name": inp.get("name"), "value": inp.get("value"), "type": inp.get("type")}
                for inp in form.find_all("input")
            ],
        })

    result["raw_patterns"] = sorted(set(re.findall(
        r"(?:href=|fetch\(|url:|endpoint[^=]*=)[\"']([^\"']*(?:page|strona|api|mecz)[^\"']*)[\"']",
        html,
        flags=re.IGNORECASE,
    )))[:100]
    result["text_head"] = " ".join(soup.stripped_strings)[:2000]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    session = requests.Session()
    rows = []
    for season in SEASONS:
        for route_name, template in ROUTES.items():
            rows.append(probe_url(session, season, route_name, template))
    report = {"source": "Paszport Kibica", "probes": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
