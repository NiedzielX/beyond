#!/usr/bin/env python3
"""Build a canonical historical Ekstraklasa match-attendance dataset.

Source: FBref Scores & Fixtures tables.
Scope: completed 2021/22 through 2025/26 Ekstraklasa seasons.

This script is a data-acquisition and quality-gate step only. It does not train,
promote, or score any model.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

SEASONS = ["2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026"]
BASE = "https://fbref.com/en/comps/36/{season}/schedule/{season}-Ekstraklasa-Scores-and-Fixtures"
EXPECTED_MATCHES_PER_SEASON = 306
USER_AGENT = (
    "Mozilla/5.0 (compatible; BeyondTicketingResearch/1.0; "
    "+https://github.com/NiedzielX/beyond)"
)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_only = ascii_only.lower().replace("ł", "l")
    return re.sub(r"[^a-z0-9]+", "_", ascii_only).strip("_")


def flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [
            next((str(part) for part in reversed(parts) if str(part) != "nan"), "")
            for parts in out.columns.to_flat_index()
        ]
    else:
        out.columns = [str(column) for column in out.columns]
    return out


def read_schedule(session: requests.Session, season: str) -> tuple[pd.DataFrame, str]:
    url = BASE.format(season=season)
    response = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=45)
    response.raise_for_status()

    # FBref sometimes wraps tables in HTML comments. Removing comment markers is
    # sufficient for pandas to discover the schedule table without browser logic.
    html = response.text.replace("<!--", "").replace("-->", "")
    tables = pd.read_html(StringIO(html))
    candidates: list[pd.DataFrame] = []
    for table in tables:
        table = flatten_columns(table)
        required = {"Date", "Home", "Away", "Attendance"}
        if required.issubset(set(table.columns)):
            candidates.append(table)
    if not candidates:
        raise RuntimeError(f"No Scores & Fixtures table found for {season}: {url}")

    # The schedule table is the candidate with the largest number of rows.
    return max(candidates, key=len).copy(), url


def parse_score(value) -> tuple[int | None, int | None]:
    if pd.isna(value):
        return None, None
    text = str(value).strip().replace("–", "-").replace("—", "-")
    match = re.match(r"^(\d+)\s*-\s*(\d+)$", text)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def normalize_season(frame: pd.DataFrame, season: str, source_url: str) -> pd.DataFrame:
    out = frame.copy()
    out = out[out["Home"].notna() & out["Away"].notna() & out["Date"].notna()].copy()

    out["date"] = pd.to_datetime(out["Date"], errors="coerce")
    out = out[out["date"].notna()].copy()

    out["attendance"] = pd.to_numeric(
        out["Attendance"].astype(str).str.replace(",", "", regex=False).str.replace(" ", "", regex=False),
        errors="coerce",
    ).astype("Int64")

    parsed_scores = out.get("Score", pd.Series(index=out.index, dtype=object)).apply(parse_score)
    out["home_goals"] = [pair[0] for pair in parsed_scores]
    out["away_goals"] = [pair[1] for pair in parsed_scores]

    result = pd.DataFrame(
        {
            "season": season.replace("-", "/"),
            "round": pd.to_numeric(out.get("Wk"), errors="coerce").astype("Int64"),
            "date": out["date"].dt.strftime("%Y-%m-%d"),
            "kickoff_time_local": out.get("Time", pd.Series(index=out.index, dtype=object)).astype("string"),
            "home_team": out["Home"].astype(str).str.strip(),
            "away_team": out["Away"].astype(str).str.strip(),
            "home_goals": pd.array(out["home_goals"], dtype="Int64"),
            "away_goals": pd.array(out["away_goals"], dtype="Int64"),
            "attendance": out["attendance"],
            "venue": out.get("Venue", pd.Series(index=out.index, dtype=object)).astype("string"),
            "referee": out.get("Referee", pd.Series(index=out.index, dtype=object)).astype("string"),
            "source_name": "fbref",
            "source_url": source_url,
        }
    )
    result["home_club_key"] = result["home_team"].map(slugify)
    result["away_club_key"] = result["away_team"].map(slugify)
    result["match_key"] = (
        result["season"].astype(str)
        + "|"
        + result["date"].astype(str)
        + "|"
        + result["home_club_key"]
        + "|"
        + result["away_club_key"]
    )
    result["completed"] = result["home_goals"].notna() & result["away_goals"].notna()
    result["attendance_observed"] = result["attendance"].notna()
    result["attendance_positive"] = result["attendance"].fillna(0).astype(int) > 0
    return result


def quality_report(data: pd.DataFrame) -> dict:
    seasons: dict[str, dict] = {}
    failures: list[str] = []

    for season, group in data.groupby("season", sort=True):
        completed = group[group["completed"]]
        attendance_count = int(completed["attendance_observed"].sum())
        expected = EXPECTED_MATCHES_PER_SEASON
        coverage = attendance_count / len(completed) if len(completed) else 0.0
        seasons[season] = {
            "rows": int(len(group)),
            "completed_rows": int(len(completed)),
            "attendance_rows": attendance_count,
            "attendance_coverage_pct": round(coverage * 100.0, 2),
            "home_clubs": int(group["home_club_key"].nunique()),
            "min_date": str(group["date"].min()),
            "max_date": str(group["date"].max()),
        }
        if len(completed) != expected:
            failures.append(f"{season}: expected {expected} completed matches, got {len(completed)}")
        if coverage < 0.95:
            failures.append(f"{season}: attendance coverage below 95% ({coverage:.2%})")

    duplicate_count = int(data["match_key"].duplicated().sum())
    if duplicate_count:
        failures.append(f"duplicate match_key rows: {duplicate_count}")

    invalid_attendance = int(
        (data["attendance_observed"] & (data["attendance"].astype("Float64") < 0)).sum()
    )
    if invalid_attendance:
        failures.append(f"negative attendance rows: {invalid_attendance}")

    return {
        "dataset_version": "historical-multiclub-fbref-v1",
        "source": "FBref Scores & Fixtures",
        "seasons": seasons,
        "rows": int(len(data)),
        "completed_rows": int(data["completed"].sum()),
        "attendance_rows": int(data["attendance_observed"].sum()),
        "clubs": int(pd.concat([data["home_club_key"], data["away_club_key"]]).nunique()),
        "duplicate_match_keys": duplicate_count,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sleep-seconds", type=float, default=4.0)
    args = parser.parse_args()

    session = requests.Session()
    frames: list[pd.DataFrame] = []
    for idx, season in enumerate(SEASONS):
        raw, source_url = read_schedule(session, season)
        frames.append(normalize_season(raw, season, source_url))
        if idx < len(SEASONS) - 1:
            time.sleep(args.sleep_seconds)

    data = pd.concat(frames, ignore_index=True)
    data = data.sort_values(["date", "home_club_key", "away_club_key"]).reset_index(drop=True)
    report = quality_report(data)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit("Historical multi-club dataset failed quality gate")


if __name__ == "__main__":
    main()
