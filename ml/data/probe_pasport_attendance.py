#!/usr/bin/env python3
"""Probe Paszport Kibica Ekstraklasa archive structure without persisting data.

The goal is to discover stable table/pagination semantics before writing an
attendance importer. Output is a machine-readable diagnostic only.
"""
from __future__ import annotations

import argparse
import json
import re
from io import StringIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

SEASONS = ["2022-23", "2023-24", "2024-25"]
BASE = "https://kibice.krakow.business/rozgrywki/ekstraklasa-{season}"
UA = "Mozilla/5.0 (compatible; BeyondTicketingResearch/1.0)"


def probe(session: requests.Session, season: str) -> dict:
    url = BASE.format(season=season)
    response = session.get(url, headers={"User-Agent": UA}, timeout=45)
    result = {
        "season": season,
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
        })

    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(url, anchor["href"])
        parsed = urlparse(href)
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

    # Search raw HTML for likely query/pagination patterns and API-ish paths.
    patterns = sorted(set(re.findall(
        r"(?:href=|fetch\(|url:|endpoint[^=]*=)[\"']([^\"']*(?:page|strona|api|mecz)[^\"']*)[\"']",
        html,
        flags=re.IGNORECASE,
    )))
    result["raw_patterns"] = patterns[:100]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    session = requests.Session()
    report = {"source": "Paszport Kibica", "seasons": [probe(session, s) for s in SEASONS]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
