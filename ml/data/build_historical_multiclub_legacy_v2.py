#!/usr/bin/env python3
"""Strict historical Ekstraklasa attendance builder for 2021/22-2024/25.

This compatibility layer extends the proven Paszport Kibica + pinned POL.csv
reconciliation pipeline to four complete seasons (1,224 matches) while keeping
source anomalies explicit and auditable.

Verified source anomalies
-------------------------
1. Paszport pages for 14 matches in 2021/22 rounds 5-6 expose the correct
   month/day, teams and result but year=2022 instead of 2021.
2. Paszport pages for 39 matches in 2023/24 rounds 2-6 expose the correct
   month/day, teams and result but year=2024 instead of 2023.
3. Radomiak Radom - Piast Gliwice on 2021-12-14 has attendance=0 because the
   match was played behind closed doors. It remains historical ground truth but
   is excluded from default demand-model training.
4. The independent reference uses abbreviated club names in a few seasons
   (e.g. `Legnica` for Miedz Legnica). These are normalized to one canonical
   cross-season club-key contract before reconciliation.

No mismatch is tolerated. Every season still has to reconcile exactly 306/306
matches on canonical date + home + away + final score against the pinned
independent reference.
"""
from __future__ import annotations

import re

from ml.data import build_historical_multiclub_legacy as legacy

_original_parse_match_page = legacy.parse_match_page
_original_canonical_team = legacy.canonical_team
_original_reconcile = legacy.reconcile

# Probe-verified contiguous ID block for 2021/22, followed by the three blocks
# already verified by the v1 legacy builder.
legacy.BLOCKS = [
    legacy.SeasonBlock("2021/2022", 17815, 18120),
    legacy.SeasonBlock("2022/2023", 18427, 18732),
    legacy.SeasonBlock("2023/2024", 18121, 18426),
    legacy.SeasonBlock("2024/2025", 18733, 19038),
]

KEY_REMAP = {
    # Cross-season contract used by Global Model v2.1 / 2025-26 data.
    "legnica": "miedz_legnica",
    "miedzlegnica": "miedz_legnica",
    "lkslodz": "lks_lodz",
    "puszcza": "puszcza_niepolomice",
    "radomiak": "radomiak_radom",
    "ruchchorzow": "ruch_chorzow",
    "slaskwroclaw": "slask_wroclaw",
    "stalmielec": "stal_mielec",
    "wartapoznan": "warta_poznan",
    "wislaplock": "wisla_plock",
    "zaglebie": "zaglebie_lubin",
}

CLOSED_DOORS_MATCH_ID = 17964


def _canonical_season(value: str) -> str:
    match = re.fullmatch(r"(\d{4})/(\d{2})", str(value))
    if not match:
        return str(value)
    start_year = int(match.group(1))
    end_two = int(match.group(2))
    century = (start_year // 100) * 100
    end_year = century + end_two
    if end_year < start_year:
        end_year += 100
    return f"{start_year:04d}/{end_year:04d}"


def canonical_team(value: str) -> str:
    key = _original_canonical_team(value)
    return KEY_REMAP.get(key, key)


def parse_match_page(match_id: int, html: str) -> dict:
    row = _original_parse_match_page(match_id, html)
    row["season"] = _canonical_season(row["season"])
    row["home_club_key"] = canonical_team(row["home_team"])
    row["away_club_key"] = canonical_team(row["away_team"])

    raw_date = str(row["match_date"])
    row["source_match_date"] = raw_date
    row["source_date_reconciled"] = False
    row["source_date_delta_days"] = 0
    row["date_correction_reason"] = None

    # 2021/22: 14 independently matched pages in rounds 5-6 have year+1.
    if (
        row["season"] == "2021/2022"
        and int(row["round_no"]) in {5, 6}
        and re.fullmatch(r"2022-08-\d{2}", raw_date)
    ):
        row["match_date"] = "2021-" + raw_date[5:]
        row["source_date_reconciled"] = True
        row["source_date_delta_days"] = 365
        row["date_correction_reason"] = (
            "paszport_2021_22_rounds_5_6_year_plus_one_"
            "verified_against_pinned_reference"
        )

    # 2023/24: 39 independently matched pages in rounds 2-6 have year+1.
    if (
        row["season"] == "2023/2024"
        and int(row["round_no"]) in {2, 3, 4, 5, 6}
        and re.fullmatch(r"2024-(07|08)-\d{2}", raw_date)
    ):
        row["match_date"] = "2023-" + raw_date[5:]
        row["source_date_reconciled"] = True
        row["source_date_delta_days"] = 366
        row["date_correction_reason"] = (
            "paszport_2023_24_rounds_2_6_year_plus_one_"
            "verified_against_pinned_reference"
        )

    row["attendance_exception"] = None
    row["default_demand_training_eligible"] = True
    if match_id == CLOSED_DOORS_MATCH_ID:
        row["attendance_exception"] = "closed_doors_government_order"
        row["default_demand_training_eligible"] = False

    return row


def reconcile(scraped, reference):
    """Keep the base exact reconciliation gate, allowing one verified zero-attendance exception."""
    mismatches, report = _original_reconcile(scraped, reference)

    closed = scraped[scraped["paszport_match_id"] == CLOSED_DOORS_MATCH_ID]
    exception_valid = (
        len(closed) == 1
        and closed.iloc[0]["season"] == "2021/2022"
        and closed.iloc[0]["match_date"] == "2021-12-14"
        and int(closed.iloc[0]["attendance"]) == 0
        and closed.iloc[0]["home_club_key"] == "radomiak_radom"
        and closed.iloc[0]["away_club_key"] == "piastgliwice"
    )

    if exception_valid:
        report["failures"] = [
            failure
            for failure in report["failures"]
            if failure != "2021/2022: non-positive attendance"
        ]

    report["dataset_version"] = "historical-multiclub-2021-25-v2"
    report["source_date_reconciled_rows"] = int(scraped["source_date_reconciled"].sum())
    report["default_demand_training_excluded_rows"] = int(
        (~scraped["default_demand_training_eligible"]).sum()
    )
    report["closed_doors_exception_validated"] = bool(exception_valid)

    if not exception_valid:
        report["failures"].append("verified closed-doors match exception missing or changed")

    if report["source_date_reconciled_rows"] != 53:
        report["failures"].append(
            f"expected 53 source-date reconciliations, got {report['source_date_reconciled_rows']}"
        )

    if report["default_demand_training_excluded_rows"] != 1:
        report["failures"].append(
            "expected exactly 1 default demand-training exclusion"
        )

    report["status"] = "PASS" if not report["failures"] else "FAIL"
    return mismatches, report


# Patch before legacy.main() loads either source.
legacy.canonical_team = canonical_team
legacy.parse_match_page = parse_match_page
legacy.reconcile = reconcile


if __name__ == "__main__":
    legacy.main()
