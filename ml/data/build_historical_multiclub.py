#!/usr/bin/env python3
"""Build a canonical historical Ekstraklasa match-attendance dataset.

Source v1: a public, versioned GitHub mirror of FBref club match logs for the
completed 2025/26 Ekstraklasa season. We intentionally do not bypass FBref's
403 protection from CI.

The mirror is pinned to an immutable commit for reproducibility. Only HOME
Ekstraklasa rows are used, so every league match occurs exactly once.

This script is data acquisition + quality gating only. It never trains or
promotes a model.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

SOURCE_REPO = "Mewhoosh/ekstraklasa-2025-26-analytics"
SOURCE_COMMIT = "bce5fb1ef95298a7f2c8687177bd6e9c5461c63a"
SOURCE_DIR = "data/processed/fbref"
SEASON = "2025/2026"
EXPECTED_MATCHES = 306
EXPECTED_HOME_CLUBS = 18

SOURCE_FILE_TO_CANONICAL = {
    "arka_gdynia": "arkagdynia",
    "cracovia": "cracovia",
    "gks_katowice": "gkskatowice",
    "gornik_zabrze": "gornikzabrze",
    "jagiellonia": "jagiellonia",
    "korona_kielce": "koronakielce",
    "lech": "lech",
    "lechia_gdansk": "lechiagdansk",
    "legia": "legia",
    "motor_lublin": "motorlublin",
    "piast_gliwice": "piastgliwice",
    "pogon_szczecin": "pogonszczecin",
    "radomiak": "radomiak",
    "rakow": "rakow",
    "termalica": "termalica",
    "widzew_lodz": "widzewlodz",
    "wisla_plock": "wisla_plock",
    "zaglebie_lubin": "zaglebie_lubin",
}

DISPLAY_NAMES = {
    "arkagdynia": "Arka Gdynia",
    "cracovia": "Cracovia",
    "gkskatowice": "GKS Katowice",
    "gornikzabrze": "Górnik Zabrze",
    "jagiellonia": "Jagiellonia Białystok",
    "koronakielce": "Korona Kielce",
    "lech": "Lech Poznań",
    "lechiagdansk": "Lechia Gdańsk",
    "legia": "Legia Warszawa",
    "motorlublin": "Motor Lublin",
    "piastgliwice": "Piast Gliwice",
    "pogonszczecin": "Pogoń Szczecin",
    "radomiak": "Radomiak Radom",
    "rakow": "Raków Częstochowa",
    "termalica": "Bruk-Bet Termalica Nieciecza",
    "widzewlodz": "Widzew Łódź",
    "wisla_plock": "Wisła Płock",
    "zaglebie_lubin": "Zagłębie Lubin",
}

OPPONENT_ALIASES = {
    "arka gdynia": "arkagdynia",
    "cracovia": "cracovia",
    "katowice": "gkskatowice",
    "gks katowice": "gkskatowice",
    "gornik zabrze": "gornikzabrze",
    "jagiellonia": "jagiellonia",
    "jagiellonia bialystok": "jagiellonia",
    "korona kielce": "koronakielce",
    "lech poznan": "lech",
    "lechia gdansk": "lechiagdansk",
    "legia warsaw": "legia",
    "legia warszawa": "legia",
    "motor lublin": "motorlublin",
    "piast gliwice": "piastgliwice",
    "pogon szczecin": "pogonszczecin",
    "radomiak": "radomiak",
    "radomiak radom": "radomiak",
    "rakow": "rakow",
    "rakow czestochowa": "rakow",
    "nieciecza": "termalica",
    "termalica": "termalica",
    "widzew lodz": "widzewlodz",
    "wisla plock": "wisla_plock",
    "zaglebie lubin": "zaglebie_lubin",
}


def ascii_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", ascii_only.lower().replace("ł", "l")).strip()


def canonical_opponent(value: str) -> str:
    key = ascii_key(value)
    return OPPONENT_ALIASES.get(key, key.replace(" ", "_"))


def discover_match_logs(session: requests.Session) -> list[str]:
    url = f"https://api.github.com/repos/{SOURCE_REPO}/git/trees/{SOURCE_COMMIT}?recursive=1"
    response = session.get(url, timeout=45)
    response.raise_for_status()
    tree = response.json().get("tree", [])
    paths = sorted(
        item["path"]
        for item in tree
        if item.get("type") == "blob"
        and item.get("path", "").startswith(f"{SOURCE_DIR}/")
        and item.get("path", "").endswith("_match_log.csv")
    )
    if len(paths) != EXPECTED_HOME_CLUBS:
        raise RuntimeError(
            f"Expected {EXPECTED_HOME_CLUBS} club match logs at pinned source commit, got {len(paths)}"
        )
    return paths


def read_log(session: requests.Session, path: str) -> pd.DataFrame:
    url = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/{path}"
    response = session.get(url, timeout=45)
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text))
    frame["_source_path"] = path
    frame["_source_url"] = url
    return frame


def source_file_key(path: str) -> str:
    return Path(path).name.removesuffix("_match_log.csv")


def normalize_home_rows(frame: pd.DataFrame, path: str) -> pd.DataFrame:
    required = {
        "Date", "Time", "Comp", "Round", "Venue", "GF", "GA",
        "Opponent", "Attendance", "Referee",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"{path} missing columns: {missing}")

    source_key = source_file_key(path)
    club_key = SOURCE_FILE_TO_CANONICAL.get(source_key, source_key)

    out = frame[
        frame["Comp"].astype(str).str.strip().eq("Ekstraklasa")
        & frame["Venue"].astype(str).str.strip().eq("Home")
    ].copy()

    out["date"] = pd.to_datetime(out["Date"], errors="coerce")
    out["attendance"] = pd.to_numeric(out["Attendance"], errors="coerce").astype("Int64")
    out["home_goals"] = pd.to_numeric(out["GF"], errors="coerce").astype("Int64")
    out["away_goals"] = pd.to_numeric(out["GA"], errors="coerce").astype("Int64")
    out["round"] = (
        out["Round"].astype(str).str.extract(r"(\d+)", expand=False)
        .pipe(pd.to_numeric, errors="coerce").astype("Int64")
    )

    result = pd.DataFrame({
        "season": SEASON,
        "round": out["round"],
        "date": out["date"].dt.strftime("%Y-%m-%d"),
        "kickoff_time_local": out["Time"].astype("string"),
        "home_team": DISPLAY_NAMES.get(club_key, source_key.replace("_", " ").title()),
        "away_team": out["Opponent"].astype(str).str.strip(),
        "home_club_key": club_key,
        "away_club_key": out["Opponent"].map(canonical_opponent),
        "home_goals": out["home_goals"],
        "away_goals": out["away_goals"],
        "attendance": out["attendance"],
        "referee": out["Referee"].astype("string"),
        "source_name": "github_mirror_fbref",
        "source_repo": SOURCE_REPO,
        "source_commit": SOURCE_COMMIT,
        "source_path": path,
        "source_url": out["_source_url"].astype("string"),
    })
    result["match_key"] = (
        result["season"] + "|" + result["date"] + "|"
        + result["home_club_key"] + "|" + result["away_club_key"]
    )
    result["completed"] = result["home_goals"].notna() & result["away_goals"].notna()
    result["attendance_observed"] = result["attendance"].notna()
    result["attendance_positive"] = result["attendance"].fillna(0).astype(int) > 0
    return result


def quality_report(data: pd.DataFrame, source_paths: list[str]) -> dict:
    failures: list[str] = []
    completed = data[data["completed"]]
    attendance_count = int(completed["attendance_observed"].sum())
    coverage = attendance_count / len(completed) if len(completed) else 0.0
    duplicate_count = int(data["match_key"].duplicated().sum())
    home_clubs = int(data["home_club_key"].nunique())
    away_clubs = int(data["away_club_key"].nunique())
    positive_count = int(completed["attendance_positive"].sum())

    if len(completed) != EXPECTED_MATCHES:
        failures.append(f"expected {EXPECTED_MATCHES} completed matches, got {len(completed)}")
    if home_clubs != EXPECTED_HOME_CLUBS:
        failures.append(f"expected {EXPECTED_HOME_CLUBS} home clubs, got {home_clubs}")
    if away_clubs != EXPECTED_HOME_CLUBS:
        failures.append(f"expected {EXPECTED_HOME_CLUBS} canonical away clubs, got {away_clubs}")
    if coverage < 0.98:
        failures.append(f"attendance coverage below 98% ({coverage:.2%})")
    if duplicate_count:
        failures.append(f"duplicate match_key rows: {duplicate_count}")
    if positive_count != attendance_count:
        failures.append(
            f"non-positive observed attendance rows: {attendance_count - positive_count}"
        )

    club_counts = {
        str(key): int(value)
        for key, value in data.groupby("home_club_key").size().sort_index().items()
    }
    unexpected_home_counts = {
        key: count for key, count in club_counts.items() if count != 17
    }
    if unexpected_home_counts:
        failures.append(f"clubs without 17 home league matches: {unexpected_home_counts}")

    return {
        "dataset_version": "historical-multiclub-2025-26-v1",
        "source": {
            "type": "public_git_mirror_of_fbref_match_logs",
            "repository": SOURCE_REPO,
            "commit": SOURCE_COMMIT,
            "files": len(source_paths),
        },
        "season": SEASON,
        "rows": int(len(data)),
        "completed_rows": int(len(completed)),
        "attendance_rows": attendance_count,
        "attendance_coverage_pct": round(coverage * 100.0, 2),
        "attendance_min": int(completed["attendance"].min()),
        "attendance_max": int(completed["attendance"].max()),
        "home_clubs": home_clubs,
        "away_clubs": away_clubs,
        "club_home_match_counts": club_counts,
        "min_date": str(data["date"].min()),
        "max_date": str(data["date"].max()),
        "duplicate_match_keys": duplicate_count,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    session = requests.Session()
    source_paths = discover_match_logs(session)
    frames = [normalize_home_rows(read_log(session, path), path) for path in source_paths]
    data = pd.concat(frames, ignore_index=True)
    data = data.sort_values(["date", "home_club_key", "away_club_key"]).reset_index(drop=True)
    report = quality_report(data, source_paths)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit("Historical multi-club dataset failed quality gate")


if __name__ == "__main__":
    main()
