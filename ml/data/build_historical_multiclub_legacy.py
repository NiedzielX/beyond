#!/usr/bin/env python3
"""Build Beyond's 2022/23–2024/25 Ekstraklasa attendance archive.

Attendance source
-----------------
Paszport Kibica individual match pages. The three seasons occupy contiguous,
probe-verified 306-ID blocks. Each page explicitly identifies competition,
season, round, date, score and attendance, and cites 90minut.pl as its source.

Independent validation source
-----------------------------
`tmorcinek/ekstraklasa-analysis:data/POL.csv`, pinned to an immutable Git commit.
It contains Ekstraklasa dates, home/away teams and final scores. Paszport data is
accepted only when all 306 matches in every season match the independent
reference on date, teams and final score.

No model code lives here. A failed reconciliation blocks the dataset.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import date
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; BeyondTicketingResearch/1.0)"
PASZPORT_MATCH = "https://kibice.krakow.business/mecze/{match_id}"
REFERENCE_REPO = "tmorcinek/ekstraklasa-analysis"
REFERENCE_COMMIT = "390b85cd67aae2223be1c9a0ff558259559596a5"
REFERENCE_URL = (
    f"https://raw.githubusercontent.com/{REFERENCE_REPO}/{REFERENCE_COMMIT}/data/POL.csv"
)
EXPECTED_MATCHES = 306

POLISH_MONTHS = {
    "stycznia": 1,
    "lutego": 2,
    "marca": 3,
    "kwietnia": 4,
    "maja": 5,
    "czerwca": 6,
    "lipca": 7,
    "sierpnia": 8,
    "września": 9,
    "wrzesnia": 9,
    "października": 10,
    "pazdziernika": 10,
    "listopada": 11,
    "grudnia": 12,
}


@dataclass(frozen=True)
class SeasonBlock:
    season: str
    first_id: int
    last_id: int

    @property
    def ids(self) -> range:
        return range(self.first_id, self.last_id + 1)


# Boundaries were independently probed on 2026-10-14:
# 18121 = 2023/24 R1, 18426 = 2023/24 R34
# 18427 = 2022/23 R1, 18732 = 2022/23 R34
# 18733 = 2024/25 R1, 19038 = 2024/25 R34
BLOCKS = [
    SeasonBlock("2022/2023", 18427, 18732),
    SeasonBlock("2023/2024", 18121, 18426),
    SeasonBlock("2024/2025", 18733, 19038),
]

TEAM_ALIASES = {
    # stable keys
    "arka gdynia": "arkagdynia",
    "cracovia": "cracovia",
    "gks katowice": "gkskatowice",
    "katowice": "gkskatowice",
    "gornik z": "gornikzabrze",
    "gornik zabrze": "gornikzabrze",
    "jagiellonia": "jagiellonia",
    "jagiellonia bialystok": "jagiellonia",
    "korona kielce": "koronakielce",
    "lech poznan": "lech",
    "lechia gdansk": "lechiagdansk",
    "legia": "legia",
    "legia warszawa": "legia",
    "legia warsaw": "legia",
    "lks lodz": "lkslodz",
    "miedz legnica": "miedzlegnica",
    "motor lublin": "motorlublin",
    "piast gliwice": "piastgliwice",
    "pogon szczecin": "pogonszczecin",
    "puszcza": "puszcza",
    "puszcza niepolomice": "puszcza",
    "radomiak radom": "radomiak",
    "radomiak": "radomiak",
    "rakow": "rakow",
    "rakow czestochowa": "rakow",
    "ruch": "ruchchorzow",
    "ruch chorzow": "ruchchorzow",
    "slask wroclaw": "slaskwroclaw",
    "stal mielec": "stalmielec",
    "warta poznan": "wartapoznan",
    "widzew lodz": "widzewlodz",
    "wisla plock": "wislaplock",
    "zaglebie": "zaglebie",
    "zaglebie lubin": "zaglebie",
}


def ascii_words(value: str) -> str:
    value = str(value).replace("Ł", "L").replace("ł", "l")
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", ascii_only.lower()).strip()


def canonical_team(value: str) -> str:
    normalized = ascii_words(value)
    return TEAM_ALIASES.get(normalized, normalized.replace(" ", ""))


def parse_polish_date(day: str, month: str, year: str) -> date:
    month_key = month.lower()
    if month_key not in POLISH_MONTHS:
        raise ValueError(f"Unknown Polish month: {month}")
    return date(int(year), POLISH_MONTHS[month_key], int(day))


def compact_text(soup: BeautifulSoup) -> str:
    return " ".join(soup.stripped_strings).replace("\xa0", " ")


def parse_match_page(match_id: int, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = compact_text(soup)
    h1 = soup.find("h1")
    if h1 is None:
        raise RuntimeError(f"Match {match_id}: missing h1")
    title = " ".join(h1.stripped_strings)
    parts = re.split(r"\s+[—–-]\s+", title, maxsplit=1)
    if len(parts) != 2:
        raise RuntimeError(f"Match {match_id}: cannot split teams from h1={title!r}")
    home_team, away_team = parts[0].strip(), parts[1].strip()

    season_match = re.search(r"Ekstraklasa\s+·\s+(\d{4}/\d{2})\s+·\s+kolejka\s+(\d+)", text)
    if not season_match:
        raise RuntimeError(f"Match {match_id}: missing season/round")
    season = season_match.group(1)
    round_no = int(season_match.group(2))

    score_match = re.search(
        re.escape(home_team)
        + r"\s+[—–-]\s+"
        + re.escape(away_team)
        + r"\s+(\d+)\s*[–—-]\s*(\d+)\s+Data",
        text,
    )
    if not score_match:
        raise RuntimeError(f"Match {match_id}: missing score for {title}")
    home_goals, away_goals = int(score_match.group(1)), int(score_match.group(2))

    date_match = re.search(
        r"Data\s+(\d{1,2})\s+([A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż]+)\s+(\d{4})\s+·\s+(\d{1,2}:\d{2})",
        text,
    )
    if not date_match:
        raise RuntimeError(f"Match {match_id}: missing date/time")
    match_date = parse_polish_date(date_match.group(1), date_match.group(2), date_match.group(3))
    kickoff_time = date_match.group(4)

    attendance_match = re.search(r"Frekwencja\s+([\d\s]+)\s+widzów", text)
    if not attendance_match:
        raise RuntimeError(f"Match {match_id}: missing attendance")
    attendance = int(re.sub(r"\s+", "", attendance_match.group(1)))

    return {
        "paszport_match_id": match_id,
        "season": season,
        "round_no": round_no,
        "match_date": match_date.isoformat(),
        "kickoff_time_local": kickoff_time,
        "home_team": home_team,
        "away_team": away_team,
        "home_club_key": canonical_team(home_team),
        "away_club_key": canonical_team(away_team),
        "home_goals": home_goals,
        "away_goals": away_goals,
        "attendance": attendance,
        "attendance_source": "Paszport Kibica / 90minut.pl",
        "source_url": PASZPORT_MATCH.format(match_id=match_id),
    }


def fetch_match(session: requests.Session, match_id: int, *, retries: int = 3) -> dict:
    url = PASZPORT_MATCH.format(match_id=match_id)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, headers={"User-Agent": UA}, timeout=45)
            response.raise_for_status()
            return parse_match_page(match_id, response.text)
        except Exception as exc:  # diagnostic context preserved in final error
            last_error = exc
            if attempt < retries:
                time.sleep(attempt * 0.8)
    raise RuntimeError(f"Match {match_id}: failed after {retries} attempts: {last_error}")


def load_reference(session: requests.Session) -> pd.DataFrame:
    response = session.get(REFERENCE_URL, headers={"User-Agent": UA}, timeout=60)
    response.raise_for_status()
    reference = pd.read_csv(StringIO(response.text))
    reference = reference[reference["Season"].isin([b.season for b in BLOCKS])].copy()
    reference["match_date"] = pd.to_datetime(reference["Date"], dayfirst=True, errors="raise").dt.date.astype(str)
    reference["home_club_key"] = reference["Home"].map(canonical_team)
    reference["away_club_key"] = reference["Away"].map(canonical_team)
    reference["home_goals"] = pd.to_numeric(reference["HG"], errors="raise").astype(int)
    reference["away_goals"] = pd.to_numeric(reference["AG"], errors="raise").astype(int)
    reference["reference_key"] = (
        reference["Season"] + "|" + reference["match_date"] + "|"
        + reference["home_club_key"] + "|" + reference["away_club_key"]
    )
    return reference[
        ["Season", "match_date", "home_club_key", "away_club_key", "home_goals", "away_goals", "reference_key"]
    ].rename(columns={"Season": "season"})


def reconcile(scraped: pd.DataFrame, reference: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    scraped = scraped.copy()
    scraped["reference_key"] = (
        scraped["season"] + "|" + scraped["match_date"] + "|"
        + scraped["home_club_key"] + "|" + scraped["away_club_key"]
    )
    joined = scraped.merge(
        reference,
        on=["season", "match_date", "home_club_key", "away_club_key", "reference_key"],
        how="outer",
        suffixes=("_attendance", "_reference"),
        indicator=True,
    )
    joined["score_matches"] = (
        (joined["home_goals_attendance"] == joined["home_goals_reference"])
        & (joined["away_goals_attendance"] == joined["away_goals_reference"])
    )
    mismatches = joined[(joined["_merge"] != "both") | (~joined["score_matches"].fillna(False))].copy()

    season_reports = {}
    failures = []
    for block in BLOCKS:
        s_scraped = scraped[scraped["season"] == block.season]
        s_reference = reference[reference["season"] == block.season]
        s_joined = joined[joined["season"] == block.season]
        s_mismatch = mismatches[mismatches["season"] == block.season]
        report = {
            "expected_id_count": len(block.ids),
            "attendance_rows": int(len(s_scraped)),
            "reference_rows": int(len(s_reference)),
            "matched_rows": int(((s_joined["_merge"] == "both") & s_joined["score_matches"].fillna(False)).sum()),
            "mismatch_rows": int(len(s_mismatch)),
            "attendance_min": int(s_scraped["attendance"].min()) if len(s_scraped) else None,
            "attendance_max": int(s_scraped["attendance"].max()) if len(s_scraped) else None,
            "attendance_sum": int(s_scraped["attendance"].sum()) if len(s_scraped) else None,
        }
        if len(s_scraped) != EXPECTED_MATCHES:
            failures.append(f"{block.season}: Paszport rows {len(s_scraped)} != {EXPECTED_MATCHES}")
        if len(s_reference) != EXPECTED_MATCHES:
            failures.append(f"{block.season}: reference rows {len(s_reference)} != {EXPECTED_MATCHES}")
        if len(s_mismatch):
            failures.append(f"{block.season}: {len(s_mismatch)} reconciliation mismatches")
        if not (s_scraped["attendance"] > 0).all():
            failures.append(f"{block.season}: non-positive attendance")
        season_reports[block.season] = report

    if scraped["paszport_match_id"].duplicated().any():
        failures.append("duplicate Paszport match IDs")
    if scraped["reference_key"].duplicated().any():
        failures.append("duplicate normalized match keys")

    report = {
        "dataset_version": "historical-multiclub-2022-25-v1",
        "attendance_source": "Paszport Kibica individual match pages (90minut.pl provenance)",
        "reference_source": {
            "repository": REFERENCE_REPO,
            "commit": REFERENCE_COMMIT,
            "path": "data/POL.csv",
        },
        "rows": int(len(scraped)),
        "seasons": season_reports,
        "total_mismatch_rows": int(len(mismatches)),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    return mismatches, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--mismatches", required=True, type=Path)
    parser.add_argument("--sleep-seconds", type=float, default=0.10)
    args = parser.parse_args()

    session = requests.Session()
    rows = []
    for block in BLOCKS:
        for idx, match_id in enumerate(block.ids):
            row = fetch_match(session, match_id)
            if row["season"] != block.season:
                raise RuntimeError(
                    f"Paszport ID block drift: id={match_id}, expected {block.season}, got {row['season']}"
                )
            rows.append(row)
            if args.sleep_seconds > 0 and idx < EXPECTED_MATCHES - 1:
                time.sleep(args.sleep_seconds)

    scraped = pd.DataFrame(rows).sort_values(["season", "match_date", "paszport_match_id"]).reset_index(drop=True)
    reference = load_reference(session)
    mismatches, report = reconcile(scraped, reference)

    scraped["dataset_version"] = report["dataset_version"]
    scraped["match_key"] = (
        scraped["season"] + "|" + scraped["match_date"] + "|"
        + scraped["home_club_key"] + "|" + scraped["away_club_key"]
    )
    scraped["reference_repo"] = REFERENCE_REPO
    scraped["reference_commit"] = REFERENCE_COMMIT

    args.output.parent.mkdir(parents=True, exist_ok=True)
    scraped.to_csv(args.output, index=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.mismatches.parent.mkdir(parents=True, exist_ok=True)
    mismatches.to_csv(args.mismatches, index=False)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit("Historical 2022-25 dataset failed independent reconciliation gate")


if __name__ == "__main__":
    main()
