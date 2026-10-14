#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

BASE = "https://kibice.krakow.business/rozgrywki/ekstraklasa-2022-23"
VARIANTS = [
    "",
    "?page=2",
    "?page=3",
    "?strona=2",
    "?offset=100",
    "?offset=200",
    "?limit=400",
    "?per_page=400",
    "?show=all",
    "?all=1",
]
UA = "Mozilla/5.0 (compatible; BeyondTicketingResearch/1.0)"


def inspect(session: requests.Session, suffix: str) -> dict:
    url = BASE + suffix
    r = session.get(url, headers={"User-Agent": UA}, timeout=45)
    result = {
        "suffix": suffix or "base",
        "url": url,
        "status": r.status_code,
        "bytes": len(r.content),
        "sha256": hashlib.sha256(r.content).hexdigest(),
        "rows": 0,
        "first": None,
        "last": None,
    }
    if r.status_code != 200:
        return result
    try:
        tables = pd.read_html(StringIO(r.text))
    except ValueError:
        tables = []
    target = next((t for t in tables if {"Data", "Mecz", "Wynik", "Widzów"}.issubset(set(map(str, t.columns)))), None)
    if target is not None:
        result["rows"] = int(len(target))
        if len(target):
            result["first"] = {str(k): str(v) for k, v in target.iloc[0].to_dict().items()}
            result["last"] = {str(k): str(v) for k, v in target.iloc[-1].to_dict().items()}
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    session = requests.Session()
    report = {"variants": [inspect(session, v) for v in VARIANTS]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
