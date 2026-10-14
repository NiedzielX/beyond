#!/usr/bin/env python3
"""Build Beyond historical multi-season Ekstraklasa attendance dataset v2.

Attendance source:
  Public Paszport Kibica API, whose match records identify their source as
  `90minut`.

Independent fixture/result cross-check:
  `tmorcinek/ekstraklasa-analysis/data/POL.csv`, pinned to an immutable Git
  commit. The file is derived from football-data.co.uk and contains
  Ekstraklasa fixtures/results across the target seasons.

The builder does not silently repair mismatches. Every desired season must
contain exactly 306 unique Ekstraklasa matches and every attendance record must
match exactly one independent fixture by season + home + away + score. Date
mismatches are reported separately and block the dataset unless explicitly
understood and encoded in a later dataset version.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from io import StringIO
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

PASZPORT_API = "https://api.fundacjanh.org/api/kibice/matches"
PASZPORT_UI = "https://kibice.krakow.business"
USER_AGENT = "Mozilla/5.0 BeyondTicketingResearch/2.0"
TARGET_SEASONS = ["2021/22", "2022/23", "2023/24", "2024/25"]
REFERENCE_SEASON_TO_CANONICAL = {
    "2021/2022": "2021/22",
    "2022/2023": "2022/23",
    "2023/2024": "2023/24",
    "2024/2025": "2024/25",
}
EXPECTED_MATCHES_PER_SEASON = 306

REFERENCE_REPO = "tmorcinek/ekstraklasa-analysis"
REFERENCE_COMMIT = "390b85cd67aae2223be1c9a0ff558259559596a5"
REFERENCE_PATH = "data/POL.csv"
REFERENCE_URL = (
    f"https://raw.githubusercontent.com/{REFERENCE_REPO}/"
    f"{REFERENCE_COMMIT}/{REFERENCE_PATH}"
)

# Broad range is deliberate. Paszport contains a small number of records whose
# query-indexed date falls outside a nominal season window while the explicit
# source `season` label is correct. Retrieve a wider interval and select the
# target seasons by their explicit season label.
DATE_FROM = "2021-07-01"
DATE_TO = "2025-08-31"
PAGE_SIZE = 100
DATASET_VERSION = "historical-multiclub-2021-25-v2"

SLUG_ALIASES = {
    "arka-gdynia": "arkagdynia",
    "bruk-bet-termalica-nieciecza": "termalica",
    "cracovia": "cracovia",
    "gks-katowice": "gkskatowice",
    "gornik-leczna": "gornik_leczna",
    "gornik-zabrze": "gornikzabrze",
    "jagiellonia-bialystok": "jagiellonia",
    "korona-kielce": "koronakielce",
    "lech-poznan": "lech",
    "lechia-gdansk": "lechiagdansk",
    "legia-warszawa": "legia",
    "lks-lodz": "lks_lodz",
    "miedz-legnica": "miedz_legnica",
    "motor-lublin": "motorlublin",
    "piast-gliwice": "piastgliwice",
    "podbeskidzie-bielsko-biala": "podbeskidzie",
    "pogon-szczecin": "pogonszczecin",
    "puszcza-niepolomice": "puszcza_niepolomice",
    "radomiak-radom": "radomiak",
    "rakow-czestochowa": "rakow",
    "ruch-chorzow": "ruch_chorzow",
    "slask-wroclaw": "slask_wroclaw",
    "stal-mielec": "stal_mielec",
    "warta-poznan": "warta_poznan",
    "widzew-lodz": "widzewlodz",
    "wisla-krakow": "wisla_krakow",
    "wisla-plock": "wisla_plock",
    "zaglebie-lubin": "zaglebie_lubin",
}

REFERENCE_NAME_ALIASES = {
    "arka gdynia": "arkagdynia",
    "cracovia": "cracovia",
    "gks katowice": "gkskatowice",
    "gornik l": "gornik_leczna",
    "gornik leczna": "gornik_leczna",
    "gornik z": "gornikzabrze",
    "gornik zabrze": "gornikzabrze",
    "jagiellonia": "jagiellonia",
    "korona kielce": "koronakielce",
    "lech poznan": "lech",
    "lechia gdansk": "lechiagdansk",
    "legia": "legia",
    "legia warsaw": "legia",
    "legia warszawa": "legia",
    "legnica": "miedz_legnica",
    "miedz legnica": "miedz_legnica",
    "lks lodz": "lks_lodz",
    "motor lublin": "motorlublin",
    "piast gliwice": "piastgliwice",
    "podbeskidzie": "podbeskidzie",
    "pogon szczecin": "pogonszczecin",
    "puszcza": "puszcza_niepolomice",
    "puszcza niepolomice": "puszcza_niepolomice",
    "radomiak radom": "radomiak",
    "radomiak": "radomiak",
    "rakow": "rakow",
    "rakow czestochowa": "rakow",
    "ruch": "ruch_chorzow",
    "ruch chorzow": "ruch_chorzow",
    "slask wroclaw": "slask_wroclaw",
    "stal mielec": "stal_mielec",
    "termalica b b": "termalica",
    "termalica": "termalica",
    "warta poznan": "warta_poznan",
    "widzew lodz": "widzewlodz",
    "wisla krakow": "wisla_krakow",
    "wisla plock": "wisla_plock",
    "zaglebie": "zaglebie_lubin",
    "zaglebie lubin": "zaglebie_lubin",
}


def ascii_text(value: object) -> str:
    text = str(value).replace("Ł", "L").replace("ł", "l")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def slug_to_key(slug: object, fallback_name: object) -> str:
    slug_text = str(slug or "").strip().lower()
    if slug_text in SLUG_ALIASES:
        return SLUG_ALIASES[slug_text]
    return ascii_text(fallback_name).replace(" ", "_")


def reference_name_to_key(value: object) -> str:
    normalized = ascii_text(value)
    return REFERENCE_NAME_ALIASES.get(normalized, normalized.replace(" ", "_"))


def fetch_pasport(session: requests.Session) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    expected_total: int | None = None
    while True:
        response = session.get(
            PASZPORT_API,
            params={
                "tier": 1,
                "dateFrom": DATE_FROM,
                "dateTo": DATE_TO,
                "limit": PAGE_SIZE,
                "offset": offset,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        batch = payload.get("matches") or []
        total = payload.get("total")
        if expected_total is None and isinstance(total, int):
            expected_total = total
        rows.extend(batch)
        if not batch:
            break
        offset += len(batch)
        if isinstance(total, int) and offset >= total:
            break
        if len(batch) < PAGE_SIZE and total is None:
            break
        if offset > 5000:
            raise RuntimeError("Paszport pagination safety stop")
    if expected_total is not None and len(rows) != expected_total:
        raise RuntimeError(
            f"Paszport pagination mismatch: expected {expected_total}, got {len(rows)}"
        )
    return rows


def normalize_pasport(rows: Iterable[dict]) -> pd.DataFrame:
    raw = pd.DataFrame(list(rows))
    if raw.empty:
        raise RuntimeError("Paszport API returned no rows")
    required = {
        "id", "external_id", "match_date", "match_time", "round_number",
        "home_name_raw", "away_name_raw", "home_goals", "away_goals",
        "attendance", "source", "home_slug", "away_slug", "competition_name",
        "season", "tier_level",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise RuntimeError(f"Paszport API missing fields: {missing}")

    raw = raw[
        raw["season"].isin(TARGET_SEASONS)
        & raw["competition_name"].astype(str).str.casefold().eq("ekstraklasa")
        & pd.to_numeric(raw["tier_level"], errors="coerce").eq(1)
    ].copy()
    raw["match_date_parsed"] = pd.to_datetime(
        raw["match_date"], utc=True, errors="coerce"
    )
    raw["match_date_only"] = raw["match_date_parsed"].dt.date
    raw["home_club_key"] = [
        slug_to_key(slug, name)
        for slug, name in zip(raw["home_slug"], raw["home_name_raw"])
    ]
    raw["away_club_key"] = [
        slug_to_key(slug, name)
        for slug, name in zip(raw["away_slug"], raw["away_name_raw"])
    ]
    raw["home_goals"] = pd.to_numeric(raw["home_goals"], errors="coerce").astype("Int64")
    raw["away_goals"] = pd.to_numeric(raw["away_goals"], errors="coerce").astype("Int64")
    raw["attendance"] = pd.to_numeric(raw["attendance"], errors="coerce").astype("Int64")
    raw["round_number"] = pd.to_numeric(raw["round_number"], errors="coerce").astype("Int64")
    raw["paszport_id"] = raw["id"].astype(str)
    raw["paszport_external_id"] = raw["external_id"].astype("string")
    raw["identity_key"] = (
        raw["season"].astype(str) + "|" + raw["home_club_key"] + "|"
        + raw["away_club_key"] + "|" + raw["home_goals"].astype(str)
        + "-" + raw["away_goals"].astype(str)
    )
    return raw


def load_reference(session: requests.Session) -> pd.DataFrame:
    response = session.get(
        REFERENCE_URL, headers={"User-Agent": USER_AGENT}, timeout=45
    )
    response.raise_for_status()
    ref = pd.read_csv(StringIO(response.text))
    required = {"Country", "League", "Season", "Date", "Home", "Away", "HG", "AG"}
    missing = sorted(required - set(ref.columns))
    if missing:
        raise RuntimeError(f"Reference POL.csv missing fields: {missing}")

    ref["season"] = ref["Season"].map(REFERENCE_SEASON_TO_CANONICAL)
    ref = ref[
        ref["Country"].astype(str).str.casefold().eq("poland")
        & ref["League"].astype(str).str.casefold().eq("ekstraklasa")
        & ref["season"].isin(TARGET_SEASONS)
    ].copy()
    ref["reference_date"] = pd.to_datetime(
        ref["Date"], dayfirst=True, errors="coerce"
    ).dt.date
    ref["home_club_key"] = ref["Home"].map(reference_name_to_key)
    ref["away_club_key"] = ref["Away"].map(reference_name_to_key)
    ref["home_goals_ref"] = pd.to_numeric(ref["HG"], errors="coerce").astype("Int64")
    ref["away_goals_ref"] = pd.to_numeric(ref["AG"], errors="coerce").astype("Int64")
    ref["identity_key"] = (
        ref["season"].astype(str) + "|" + ref["home_club_key"] + "|"
        + ref["away_club_key"] + "|" + ref["home_goals_ref"].astype(str)
        + "-" + ref["away_goals_ref"].astype(str)
    )
    return ref


def quality_and_join(
    paszport: pd.DataFrame, reference: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    failures: list[str] = []
    seasons: dict[str, dict] = {}

    for season in TARGET_SEASONS:
        p = paszport[paszport["season"] == season].copy()
        r = reference[reference["season"] == season].copy()
        p_duplicate_ids = int(p["paszport_id"].duplicated().sum())
        p_duplicate_identity = int(p["identity_key"].duplicated().sum())
        r_duplicate_identity = int(r["identity_key"].duplicated().sum())
        attendance_rows = int(p["attendance"].notna().sum())
        seasons[season] = {
            "paszport_rows": int(len(p)),
            "reference_rows": int(len(r)),
            "attendance_rows": attendance_rows,
            "paszport_duplicate_ids": p_duplicate_ids,
            "paszport_duplicate_identity_keys": p_duplicate_identity,
            "reference_duplicate_identity_keys": r_duplicate_identity,
        }
        if len(p) != EXPECTED_MATCHES_PER_SEASON:
            failures.append(f"{season}: Paszport expected 306 rows, got {len(p)}")
        if len(r) != EXPECTED_MATCHES_PER_SEASON:
            failures.append(f"{season}: reference expected 306 rows, got {len(r)}")
        if attendance_rows != len(p):
            failures.append(
                f"{season}: missing attendance on {len(p) - attendance_rows} rows"
            )
        if p_duplicate_ids:
            failures.append(f"{season}: duplicate Paszport ids={p_duplicate_ids}")
        if p_duplicate_identity:
            failures.append(
                f"{season}: duplicate Paszport identity keys={p_duplicate_identity}"
            )
        if r_duplicate_identity:
            failures.append(
                f"{season}: duplicate reference identity keys={r_duplicate_identity}"
            )

    joined = paszport.merge(
        reference[
            [
                "identity_key", "reference_date", "Home", "Away",
                "home_goals_ref", "away_goals_ref",
            ]
        ],
        on="identity_key",
        how="left",
        validate="one_to_one" if not failures else "many_to_many",
        indicator=True,
    )
    unmatched = joined[joined["_merge"] != "both"].copy()
    matched = joined[joined["_merge"] == "both"].copy()
    date_mismatch = matched[
        matched["match_date_only"].notna()
        & matched["reference_date"].notna()
        & (matched["match_date_only"] != matched["reference_date"])
    ].copy()

    if len(unmatched):
        examples = unmatched[
            [
                "season", "home_name_raw", "away_name_raw",
                "home_goals", "away_goals", "match_date",
            ]
        ].head(10).to_dict(orient="records")
        failures.append(
            f"reference unmatched Paszport rows={len(unmatched)}; examples={examples}"
        )
    if len(date_mismatch):
        examples = date_mismatch[
            [
                "season", "home_name_raw", "away_name_raw",
                "match_date_only", "reference_date",
            ]
        ].head(10).astype(str).to_dict(orient="records")
        failures.append(
            f"date mismatches={len(date_mismatch)}; examples={examples}"
        )

    reverse = reference.merge(
        paszport[["identity_key", "paszport_id"]],
        on="identity_key",
        how="left",
        indicator=True,
    )
    reverse_unmatched = reverse[reverse["_merge"] != "both"]
    if len(reverse_unmatched):
        examples = reverse_unmatched[
            ["season", "Home", "Away", "HG", "AG"]
        ].head(10).to_dict(orient="records")
        failures.append(
            f"reference fixtures missing in Paszport={len(reverse_unmatched)}; examples={examples}"
        )

    out = pd.DataFrame({
        "dataset_version": DATASET_VERSION,
        "season": matched["season"],
        "round": matched["round_number"],
        "date": matched["reference_date"].astype(str),
        "kickoff_time_local": matched["match_time"].astype("string"),
        "home_team": matched["home_name_raw"].astype(str),
        "away_team": matched["away_name_raw"].astype(str),
        "home_club_key": matched["home_club_key"],
        "away_club_key": matched["away_club_key"],
        "home_goals": matched["home_goals"],
        "away_goals": matched["away_goals"],
        "attendance": matched["attendance"],
        "paszport_id": matched["paszport_id"],
        "paszport_external_id": matched["paszport_external_id"],
        "source_name": "paszport_kibica_api_90minut",
        "source_url": PASZPORT_API,
        "source_record_url": (
            PASZPORT_UI + "/mecze/" + matched["paszport_id"].astype(str)
        ),
        "source_declared_origin": matched["source"].astype("string"),
        "reference_name": "tmorcinek_ekstraklasa_analysis_POL.csv",
        "reference_repo": REFERENCE_REPO,
        "reference_commit": REFERENCE_COMMIT,
        "reference_path": REFERENCE_PATH,
    })
    out["match_key"] = (
        out["season"].astype(str) + "|" + out["date"].astype(str) + "|"
        + out["home_club_key"] + "|" + out["away_club_key"]
    )
    match_key_duplicates = int(out["match_key"].duplicated().sum())
    if match_key_duplicates:
        failures.append(
            f"canonical duplicate match_key rows={match_key_duplicates}"
        )

    report = {
        "dataset_version": DATASET_VERSION,
        "sources": {
            "attendance": {
                "name": "Paszport Kibica public matches API",
                "url": PASZPORT_API,
                "declared_underlying_source": "90minut",
            },
            "fixture_result_reference": {
                "repository": REFERENCE_REPO,
                "commit": REFERENCE_COMMIT,
                "path": REFERENCE_PATH,
            },
        },
        "target_seasons": TARGET_SEASONS,
        "expected_total_rows": EXPECTED_MATCHES_PER_SEASON * len(TARGET_SEASONS),
        "canonical_rows": int(len(out)),
        "matched_to_reference": int(len(matched)),
        "unmatched_pasport_rows": int(len(unmatched)),
        "unmatched_reference_rows": int(len(reverse_unmatched)),
        "date_mismatches": int(len(date_mismatch)),
        "duplicate_match_keys": match_key_duplicates,
        "seasons": seasons,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    return out.sort_values(
        ["date", "home_club_key", "away_club_key"]
    ).reset_index(drop=True), report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    session = requests.Session()
    paszport = normalize_pasport(fetch_pasport(session))
    reference = load_reference(session)
    output, report = quality_and_join(paszport, reference)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    if report["status"] != "PASS":
        raise SystemExit("Historical multi-season dataset failed quality gate")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
