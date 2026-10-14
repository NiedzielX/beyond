"""Prospective media-attention v2 sampler for Beyond Ticketing.

Each run samples several recent GDELT Web News NGrams files. Every source file is
persisted separately, so overlapping workflow runs stay idempotent while sparse
minute-level news files do not create false zero attention.
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
USER_AGENT = "BeyondTicketingResearch/0.2"


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


def build_event_doc_sets(
    events: list[dict[str, Any]],
    all_docs: dict[str, set[int]],
    strong_docs: dict[str, set[int]],
) -> dict[int, dict[str, set[int]]]:
    result: dict[int, dict[str, set[int]]] = {}
    for event in events:
        event_id = int(event["id"])
        home = event["homeTeam"]
        away = event["awayTeam"]
        home_all = all_docs.get(home, set())
        away_all = all_docs.get(away, set())
        home_strong = strong_docs.get(home, set())
        away_strong = strong_docs.get(away, set())
        result[event_id] = {
            "home": home_strong,
            "away": away_strong,
            "union": home_strong | away_strong,
            "pair": home_all & away_all,
        }
    return result


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


def find_recent_files(now: datetime | None = None) -> list[dict[str, str]]:
    """Return up to six available source files spread across roughly 30 minutes."""
    now = now or datetime.now(timezone.utc)
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for target_offset in (5, 10, 15, 20, 25, 30):
        for minutes in range(target_offset, target_offset + 4):
            stamp = gdelt_stamp(now - timedelta(minutes=minutes))
            if stamp in seen:
                continue
            base = f"{GDELT_BASE}/{stamp}"
            ngrams_url = f"{base}.ngrams.txt.gz"
            if probe(ngrams_url):
                seen.add(stamp)
                results.append({
                    "source_file_timestamp": stamp_to_iso(stamp),
                    "ngrams_url": ngrams_url,
                    "toc_url": f"{base}.toc.json.gz",
                })
                break
    if not results:
        raise RuntimeError("No GDELT Web NGrams files found in the recent sampling window")
    return results


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


def _tokens(event: dict[str, Any], key: str) -> list[str]:
    return [normalize(x) for x in event.get(key) or [] if normalize(x)]


def prepare_tokens(events: list[dict[str, Any]]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    all_tokens: dict[str, list[str]] = {}
    strong_tokens: dict[str, list[str]] = {}
    for event in events:
        all_tokens[event["homeTeam"]] = _tokens(event, "homeTokens")
        all_tokens[event["awayTeam"]] = _tokens(event, "awayTokens")
        strong_tokens[event["homeTeam"]] = _tokens(event, "homeStrongTokens")
        strong_tokens[event["awayTeam"]] = _tokens(event, "awayStrongTokens")
    return all_tokens, strong_tokens


def collect_file(
    file_info: dict[str, str],
    events: list[dict[str, Any]],
    all_tokens: dict[str, list[str]],
    strong_tokens: dict[str, list[str]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    all_docs: dict[str, set[int]] = {team: set() for team in all_tokens}
    strong_docs: dict[str, set[int]] = {team: set() for team in strong_tokens}

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
            for team, tokens in all_tokens.items():
                if any(contains_token(phrase, token) for token in tokens):
                    all_docs[team].add(doc_id)
            for team, tokens in strong_tokens.items():
                if any(contains_token(phrase, token) for token in tokens):
                    strong_docs[team].add(doc_id)
    finally:
        stream.close()
        response.close()

    event_sets = build_event_doc_sets(events, all_docs, strong_docs)
    candidate_union: set[int] = set()
    for sets in event_sets.values():
        candidate_union |= sets["union"] | sets["pair"]

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
                toc_meta[doc_id] = {"title": row.get("title"), "url": row.get("url"), "lang": lang}
                if is_polish_lang(lang):
                    polish_docs.add(doc_id)
        finally:
            stream.close()
            response.close()

    samples: list[dict[str, Any]] = []
    for event in events:
        event_id = int(event["id"])
        sets = event_sets[event_id]
        home_pl = sets["home"] & polish_docs
        away_pl = sets["away"] & polish_docs
        union_pl = sets["union"] & polish_docs
        pair_pl = sets["pair"] & polish_docs
        examples = [{
            "docId": doc_id,
            "matchesHome": doc_id in home_pl,
            "matchesAway": doc_id in away_pl,
            "matchesPair": doc_id in pair_pl,
            **toc_meta.get(doc_id, {}),
        } for doc_id in sorted(union_pl)[:5]]
        samples.append({
            "ticketEventId": event_id,
            "unionMentionsPl": len(union_pl),
            "pairMentionsPl": len(pair_pl),
            "homeMentionsPl": len(home_pl),
            "awayMentionsPl": len(away_pl),
            "pairDocsGlobal": len(sets["pair"]),
            "unionDocsGlobal": len(sets["union"]),
            "examples": examples,
        })

    return samples, {
        "ngram_lines": line_count,
        "candidate_docs_global": len(candidate_union),
        "candidate_docs_polish": len(candidate_union & polish_docs),
        "broad_nonzero_events": sum(1 for row in samples if row["unionMentionsPl"] > 0),
        "pair_nonzero_events": sum(1 for row in samples if row["pairMentionsPl"] > 0),
    }


def collect(config_path: Path, output_path: Path) -> dict[str, Any]:
    events = load_config(config_path)
    all_tokens, strong_tokens = prepare_tokens(events)
    files = find_recent_files()
    sample_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    batches: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for file_info in files:
        samples, stats = collect_file(file_info, events, all_tokens, strong_tokens)
        batches.append({
            "sourceFileTimestamp": file_info["source_file_timestamp"],
            "sourceFileUrl": file_info["ngrams_url"],
            "samples": samples,
        })
        summaries.append({"source_file_timestamp": file_info["source_file_timestamp"], **stats})

    payload = {"sampleAt": sample_at, "batches": batches}
    output_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    summary = {
        "configured_events": len(events),
        "sampled_files": len(batches),
        "broad_nonzero_file_events": sum(x["broad_nonzero_events"] for x in summaries),
        "pair_nonzero_file_events": sum(x["pair_nonzero_events"] for x in summaries),
        "files": summaries,
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
