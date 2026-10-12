"""Sample match-specific Polish media attention from GDELT Web News NGrams.

This worker needs no Supabase credential. It receives a signed configuration from
Beyond's OIDC-protected ingest endpoint, downloads one recent GDELT NGrams file,
and emits a payload that the workflow sends back to the same endpoint.

The result is a sampled media-attention signal, not a complete publication count.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


GDELT_BASE = "https://data.gdeltproject.org/gdeltv5/weblegacy/ngrams"
USER_AGENT = "BeyondTicketingResearch/0.1"


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def contains_token(phrase: str, token: str) -> bool:
    if not phrase or not token:
        return False
    return f" {token} " in f" {phrase} "


def is_polish_lang(value: str | None) -> bool:
    return str(value or "").casefold() in {"pl", "pol", "polish"}


def build_candidate_docs(
    events: list[dict[str, Any]],
    team_docs: dict[str, set[int]],
) -> tuple[dict[int, set[int]], set[int]]:
    """Return docs mentioning both teams, per event and as one union.

    Team names may occur in different quadgram rows of the same GDELT document;
    intersecting DOCIDs is therefore intentional and avoids requiring both names
    to appear in one local phrase.
    """
    candidate_by_event: dict[int, set[int]] = {}
    candidate_union: set[int] = set()
    for event in events:
        event_id = int(event["id"])
        home_docs = team_docs.get(event["homeTeam"], set())
        away_docs = team_docs.get(event["awayTeam"], set())
        both = home_docs & away_docs
        candidate_by_event[event_id] = both
        candidate_union |= both
    return candidate_by_event, candidate_union


def gdelt_stamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%d%H%M00")


def stamp_to_iso(stamp: str) -> str:
    return datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def probe(url: str) -> bool:
    request = Request(url, headers={"Range": "bytes=0-0", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=20) as response:
            return response.status in (200, 206)
    except HTTPError as exc:
        if exc.code in (404, 416):
            return False
        raise


def find_latest_file(now: datetime | None = None) -> dict[str, str]:
    now = now or datetime.now(timezone.utc)
    for minutes in range(5, 36):
        stamp = gdelt_stamp(now - timedelta(minutes=minutes))
        base = f"{GDELT_BASE}/{stamp}"
        ngrams_url = f"{base}.ngrams.txt.gz"
        if probe(ngrams_url):
            return {
                "stamp": stamp,
                "source_file_timestamp": stamp_to_iso(stamp),
                "ngrams_url": ngrams_url,
                "toc_url": f"{base}.toc.json.gz",
            }
    raise RuntimeError("No GDELT Web NGrams file found in the last 35 minutes")


def open_gzip_url(url: str):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    response = urlopen(request, timeout=60)
    return response, gzip.GzipFile(fileobj=response)


def load_config(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not payload.get("ok"):
        raise RuntimeError(f"Config endpoint returned failure: {payload}")
    events = payload.get("events") or []
    if not events:
        raise RuntimeError("No configured upcoming events")
    return events


def collect(config_path: Path, output_path: Path) -> dict[str, Any]:
    events = load_config(config_path)
    file_info = find_latest_file()

    teams: dict[str, list[str]] = {}
    for event in events:
        teams[event["homeTeam"]] = [normalize(x) for x in event.get("homeTokens") or [] if normalize(x)]
        teams[event["awayTeam"]] = [normalize(x) for x in event.get("awayTokens") or [] if normalize(x)]

    team_docs: dict[str, set[int]] = {team: set() for team in teams}
    response, stream = open_gzip_url(file_info["ngrams_url"])
    line_count = 0
    try:
        for raw in stream:
            line_count += 1
            parts = raw.decode("utf-8", errors="replace").rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            try:
                doc_id = int(parts[0])
            except ValueError:
                continue
            phrase = normalize(parts[1])
            if not phrase:
                continue
            for team, tokens in teams.items():
                if any(contains_token(phrase, token) for token in tokens):
                    team_docs[team].add(doc_id)
    finally:
        stream.close()
        response.close()

    candidate_by_event, candidate_union = build_candidate_docs(events, team_docs)

    polish_docs: set[int] = set()
    toc_meta: dict[int, dict[str, Any]] = {}
    if candidate_union:
        response, stream = open_gzip_url(file_info["toc_url"])
        try:
            for raw in stream:
                try:
                    row = json.loads(raw.decode("utf-8", errors="replace"))
                    doc_id = int(row.get("ID"))
                except (ValueError, TypeError, json.JSONDecodeError):
                    continue
                if doc_id not in candidate_union:
                    continue
                lang = str(row.get("lang") or "").casefold()
                toc_meta[doc_id] = {
                    "title": row.get("title"),
                    "url": row.get("url"),
                    "lang": lang,
                }
                if is_polish_lang(lang):
                    polish_docs.add(doc_id)
        finally:
            stream.close()
            response.close()

    samples: list[dict[str, Any]] = []
    for event in events:
        event_id = int(event["id"])
        candidates = candidate_by_event[event_id]
        matching_polish = sorted(candidates & polish_docs)
        examples = [
            {"docId": doc_id, **toc_meta.get(doc_id, {})}
            for doc_id in matching_polish[:3]
        ]
        samples.append({
            "ticketEventId": event_id,
            "mentionsPl": len(matching_polish),
            "matchedDocsGlobal": len(candidates),
            "examples": examples,
        })

    payload = {
        "sourceFileTimestamp": file_info["source_file_timestamp"],
        "sourceFileUrl": file_info["ngrams_url"],
        "sampleAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "samples": samples,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    summary = {
        "source_file_timestamp": file_info["source_file_timestamp"],
        "ngram_lines": line_count,
        "configured_events": len(events),
        "candidate_docs_global": len(candidate_union),
        "candidate_docs_polish": len(polish_docs),
        "nonzero_events": sum(1 for row in samples if row["mentionsPl"] > 0),
        "samples": samples,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    collect(args.config, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
