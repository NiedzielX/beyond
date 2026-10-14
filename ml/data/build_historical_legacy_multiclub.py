#!/usr/bin/env python3
"""Build Beyond historical multi-club attendance for 2022/23-2024/25.

Attendance source:
  Paszport Kibica individual match pages. The verified season blocks contain
  exactly 306 consecutive match IDs each and each page attributes the match data
  to 90minut.pl.

Independent reference schedule/result source:
  tmorcinek/ekstraklasa-analysis `data/POL.csv`, pinned to an immutable commit.

A season is accepted only if all 306 Paszport records exactly match the
reference schedule by date, canonical home team, canonical away team and score.
Attendance is NOT taken from the reference source.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PASZPORT_MATCH_URL = "https://kibice.krakow.business/mecze/{match_id}"
REFERENCE_REPO = "tmorcinek/ekstraklasa-analysis"
REFERENCE_COMMIT = "390b85cd67aae2223be1c9a0ff558259559596a5"
REFERENCE_URL = (
    "https://raw.githubusercontent.com/"
    f"{REFERENCE_REPO}/{REFERENCE_COMMIT}/data/POL.csv"
)
DATASET_VERSION = "historical-multiclub-2022-25-v1"
UA = "Mozilla/5.0 (compatible; BeyondTicketingResearch/1.0)"
EXPECTED_MATCHES = 306

SEASON_BLOCKS = {
    "2022/2023": (18427, 18732),
    "2023/2024": (18121, 18426),
    "2024/2025": (18733, 19038),
}

POLISH_MONTHS = {
    "stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4,
    "maja": 5, "czerwca": 6, "lipca": 7, "sierpnia": 8,
    "wrzesnia": 9, "września": 9, "pazdziernika": 10,
    "października": 10, "listopada": 11, "grudnia": 12,
}

ALIASES = {
    "gornik z": "gornik_zabrze",
    "gornik zabrze": "gornik_zabrze",
    "jagiellonia": "jagiellonia_bialystok",
    "jagiellonia bialystok": "jagiellonia_bialystok",
    "legia": "legia_warszawa",
    "legia warszawa": "legia_warszawa",
    "rakow": "rakow_czestochowa",
    "rakow czestochowa": "rakow_czestochowa",
    "zaglebie": "zaglebie_lubin",
    "zaglebie lubin": "zaglebie_lubin",
    "puszcza": "puszcza_niepolomice",
    "puszcza niepolomice": "puszcza_niepolomice",
    "miedz": "miedz_legnica",
    "miedz legnica": "miedz_legnica",
    "lks lodz": "lks_lodz",
    "ruch": "ruch_chorzow",
    "ruch chorzow": "ruch_chorzow",
    "wisla plock": "wisla_plock",
    "slask wroclaw": "slask_wroclaw",
    "pogon szczecin": "pogon_szczecin",
    "lech poznan": "lech_poznan",
    "warta poznan": "warta_poznan",
    "lechia gdansk": "lechia_gdansk",
    "widzew lodz": "widzew_lodz",
    "korona kielce": "korona_kielce",
    "piast gliwice": "piast_gliwice",
    "radomiak radom": "radomiak_radom",
    "stal mielec": "stal_mielec",
    "cracovia": "cracovia",
}


def ascii_words(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_only = ascii_only.lower().replace("ł", "l")
    return re.sub(r"[^a-z0-9]+", " ", ascii_only).strip()


def canonical_team(value: str) -> str:
    key = ascii_words(value)
    return ALIASES.get(key, key.replace(" ", "_"))


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=0.35,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8))
    session.headers.update({"User-Agent": UA})
    return session


def parse_polish_date(value: str) -> str:
    parts = ascii_words(value).split()
    if len(parts) != 3:
        raise ValueError(f"Unexpected Polish date: {value!r}")
    day = int(parts[0])
    month_name = parts[1]
    year = int(parts[2])
    month = POLISH_MONTHS.get(month_name)
    if month is None:
        # dictionary also contains diacritic spellings, but ascii_words removes them
        normalized_months = {ascii_words(k): v for k, v in POLISH_MONTHS.items()}
        month = normalized_months.get(month_name)
    if month is None:
        raise ValueError(f"Unknown Polish month in {value!r}")
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_match_page(match_id: int) -> dict:
    session = make_session()
    url = PASZPORT_MATCH_URL.format(match_id=match_id)
    response = session.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = " ".join(soup.stripped_strings)

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    title_match = re.match(r"^(.*?)\s+—\s+(.*?),\s+(\d{1,2}\s+[^·,]+?\s+\d{4})\s+·\s+Paszport Kibica$", title)
    if not title_match:
        raise ValueError(f"match {match_id}: cannot parse title {title!r}")
    home, away, title_date = title_match.groups()

    meta = re.search(r"Ekstraklasa\s+·\s+(\d{4}/\d{2})\s+·\s+kolejka\s+(\d+)", text)
    if not meta:
        raise ValueError(f"match {match_id}: missing season/round")
    season_short, round_no = meta.groups()
    season = f"{season_short[:4]}/20{season_short[-2:]}"

    score_pattern = re.escape(home) + r"\s+—\s+" + re.escape(away) + r"\s+(\d+)\s*[–-]\s*(\d+)"
    score = re.search(score_pattern, text)
    if not score:
        raise ValueError(f"match {match_id}: missing score")
    home_goals, away_goals = map(int, score.groups())

    date_time = re.search(r"Data\s+(\d{1,2}\s+[A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż]+\s+\d{4})\s+·\s+(\d{1,2}:\d{2})", text)
    if not date_time:
        raise ValueError(f"match {match_id}: missing date/time")
    date_text, kickoff_time = date_time.groups()
    match_date = parse_polish_date(date_text)
    if match_date != parse_polish_date(title_date):
        raise ValueError(f"match {match_id}: title/body date mismatch")

    attendance_match = re.search(r"Frekwencja\s+([0-9\s\u00a0]+)\s+widz", text)
    if not attendance_match:
        raise ValueError(f"match {match_id}: missing attendance")
    attendance = int(re.sub(r"\D", "", attendance_match.group(1)))
    if attendance <= 0:
        raise ValueError(f"match {match_id}: non-positive attendance {attendance}")

    if "Źródło danych: 90minut.pl" not in text and "Zrodlo danych: 90minut.pl" not in ascii_words(text):
        # Retain source page even if text presentation changes; this is diagnostic only.
        source_attribution_90minut = False
    else:
        source_attribution_90minut = True

    return {
        "source_match_id": match_id,
        "season": season,
        "round": int(round_no),
        "date": match_date,
        "kickoff_time_local": kickoff_time,
        "home_team": home.strip(),
        "away_team": away.strip(),
        "home_club_key": canonical_team(home),
        "away_club_key": canonical_team(away),
        "home_goals": home_goals,
        "away_goals": away_goals,
        "attendance": attendance,
        "source_name": "paszport_kibica",
        "source_url": url,
        "source_attribution_90minut": source_attribution_90minut,
    }


def fetch_season(season: str, start_id: int, end_id: int, workers: int) -> pd.DataFrame:
    expected = end_id - start_id + 1
    if expected != EXPECTED_MATCHES:
        raise ValueError(f"{season}: ID block length {expected}, expected {EXPECTED_MATCHES}")
    rows = []
    failures = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(parse_match_page, match_id): match_id for match_id in range(start_id, end_id + 1)}
        for future in as_completed(futures):
            match_id = futures[future]
            try:
                row = future.result()
                if row["season"] != season:
                    raise ValueError(f"page reports season {row['season']}, expected {season}")
                rows.append(row)
            except Exception as exc:  # capture all parse/network failures for one report
                failures.append({"match_id": match_id, "error": str(exc)})
    if failures:
        raise RuntimeError(f"{season}: {len(failures)} failed pages: {failures[:20]}")
    frame = pd.DataFrame(rows).sort_values(["date", "kickoff_time_local", "source_match_id"]).reset_index(drop=True)
    if len(frame) != EXPECTED_MATCHES:
        raise RuntimeError(f"{season}: expected {EXPECTED_MATCHES} rows, got {len(frame)}")
    return frame


def load_reference() -> pd.DataFrame:
    session = make_session()
    response = session.get(REFERENCE_URL, timeout=45)
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text.lstrip("\ufeff")))
    frame = frame[(frame["Country"] == "Poland") & (frame["League"] == "Ekstraklasa")].copy()
    frame["date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="raise").dt.strftime("%Y-%m-%d")
    frame["home_club_key"] = frame["Home"].map(canonical_team)
    frame["away_club_key"] = frame["Away"].map(canonical_team)
    frame["home_goals"] = pd.to_numeric(frame["HG"], errors="raise").astype(int)
    frame["away_goals"] = pd.to_numeric(frame["AG"], errors="raise").astype(int)
    return frame


def validate_against_reference(data: pd.DataFrame, reference: pd.DataFrame) -> dict:
    seasons_report = {}
    failures = []
    key_cols = ["date", "home_club_key", "away_club_key", "home_goals", "away_goals"]

    for season in SEASON_BLOCKS:
        source = data[data["season"] == season].copy()
        ref = reference[reference["Season"] == season].copy()
        source_keys = set(map(tuple, source[key_cols].itertuples(index=False, name=None)))
        ref_keys = set(map(tuple, ref[key_cols].itertuples(index=False, name=None)))
        missing_from_pas = sorted(ref_keys - source_keys)
        extra_in_pas = sorted(source_keys - ref_keys)
        duplicate_keys = int(source.duplicated(key_cols).sum())
        attributed = int(source["source_attribution_90minut"].sum())
        clubs = sorted(set(source["home_club_key"]).union(source["away_club_key"]))

        status = "PASS"
        if len(source) != EXPECTED_MATCHES:
            failures.append(f"{season}: Paszport row count {len(source)}")
            status = "FAIL"
        if len(ref) != EXPECTED_MATCHES:
            failures.append(f"{season}: reference row count {len(ref)}")
            status = "FAIL"
        if missing_from_pas or extra_in_pas:
            failures.append(
                f"{season}: schedule mismatch missing={len(missing_from_pas)} extra={len(extra_in_pas)}"
            )
            status = "FAIL"
        if duplicate_keys:
            failures.append(f"{season}: duplicate reference keys in Paszport={duplicate_keys}")
            status = "FAIL"
        if source["attendance"].isna().any() or (source["attendance"] <= 0).any():
            failures.append(f"{season}: missing/non-positive attendance")
            status = "FAIL"
        if source["round"].min() != 1 or source["round"].max() != 34:
            failures.append(f"{season}: round range {source['round'].min()}-{source['round'].max()}")
            status = "FAIL"

        seasons_report[season] = {
            "status": status,
            "paszport_rows": int(len(source)),
            "reference_rows": int(len(ref)),
            "clubs": len(clubs),
            "attendance_rows": int(source["attendance"].notna().sum()),
            "attendance_min": int(source["attendance"].min()),
            "attendance_max": int(source["attendance"].max()),
            "round_min": int(source["round"].min()),
            "round_max": int(source["round"].max()),
            "90minut_attribution_pages": attributed,
            "missing_reference_matches": len(missing_from_pas),
            "extra_pasport_matches": len(extra_in_pas),
            "missing_examples": [list(x) for x in missing_from_pas[:10]],
            "extra_examples": [list(x) for x in extra_in_pas[:10]],
        }

    return {
        "dataset_version": DATASET_VERSION,
        "attendance_source": "Paszport Kibica individual match pages",
        "attendance_source_note": "pages attribute match data to 90minut.pl",
        "reference_source": REFERENCE_REPO,
        "reference_commit": REFERENCE_COMMIT,
        "rows": int(len(data)),
        "seasons": seasons_report,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    frames = []
    for season, (start_id, end_id) in SEASON_BLOCKS.items():
        print(f"Fetching {season}: IDs {start_id}-{end_id}", flush=True)
        frames.append(fetch_season(season, start_id, end_id, max(1, min(args.workers, 8))))
        time.sleep(0.5)

    data = pd.concat(frames, ignore_index=True)
    data["dataset_version"] = DATASET_VERSION
    data["match_key"] = (
        data["season"] + "|" + data["date"] + "|" + data["home_club_key"] + "|" + data["away_club_key"]
    )
    data["completed"] = True
    data["attendance_observed"] = True
    data["attendance_positive"] = data["attendance"] > 0

    reference = load_reference()
    report = validate_against_reference(data, reference)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.sort_values(["date", "kickoff_time_local", "source_match_id"]).to_csv(args.output, index=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)

    if report["status"] != "PASS":
        raise SystemExit("Legacy historical dataset failed cross-source quality gate")


if __name__ == "__main__":
    main()
