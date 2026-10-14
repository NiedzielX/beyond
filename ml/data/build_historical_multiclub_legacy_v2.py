#!/usr/bin/env python3
"""Compatibility entry point for the strict legacy historical builder.

This wrapper keeps the base builder's exact cross-source reconciliation gate and
normalizes only source anomalies that were proven from the failed full 918-row
run on 2026-10-14:

1. The independent POL.csv reference uses `Legnica` for Miedź Legnica in
   2022/23. Both names are mapped to the same canonical club key.
2. Paszport Kibica pages for exactly 39 matches in 2023/24 rounds 2-6 expose
   the correct day/month, teams and final score but a year of 2024 instead of
   2023. All 39 were independently matched 1:1 against the pinned reference on
   month-day + home + away + final score before this correction was introduced.

The raw Paszport date is preserved in `source_match_date` and every correction
is labelled with `date_correction_reason`. The base 306-per-season, exact
schedule/result reconciliation gate remains unchanged.
"""
from __future__ import annotations

import re

from ml.data import build_historical_multiclub_legacy as legacy

_original_parse_match_page = legacy.parse_match_page
_original_canonical_team = legacy.canonical_team

DATE_CORRECTION_REASON = (
    "paszport_2023_24_rounds_2_6_year_plus_one_"
    "verified_against_pinned_reference"
)


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
    """Add only the verified reference alias missing from the base mapping."""
    key = _original_canonical_team(value)
    if key == "legnica":
        return "miedzlegnica"
    return key


def parse_match_page(match_id: int, html: str) -> dict:
    row = _original_parse_match_page(match_id, html)
    row["season"] = _canonical_season(row["season"])

    raw_date = str(row["match_date"])
    row["source_match_date"] = raw_date
    row["date_correction_reason"] = None

    # Verified Paszport source anomaly: 39 matches in 2023/24 rounds 2-6 have
    # the correct month/day, teams and score but year=2024 instead of 2023.
    # Keep the correction deliberately narrow; anything else must still fail
    # the independent reconciliation gate.
    if (
        row["season"] == "2023/2024"
        and int(row["round_no"]) in {2, 3, 4, 5, 6}
        and re.fullmatch(r"2024-(07|08)-\d{2}", raw_date)
    ):
        row["match_date"] = "2023-" + raw_date[5:]
        row["date_correction_reason"] = DATE_CORRECTION_REASON

    return row


# Patch both parse and canonicalization before legacy.main() loads either source.
legacy.canonical_team = canonical_team
legacy.parse_match_page = parse_match_page


if __name__ == "__main__":
    legacy.main()
