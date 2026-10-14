#!/usr/bin/env python3
"""Compatibility entry point for the legacy historical builder.

Paszport exposes season labels as YYYY/YY, while the canonical Beyond dataset
and independent reference use YYYY/YYYY. Keep the original strict builder and
normalize only this presentation difference before its ID-block drift gate.
"""
from __future__ import annotations

import re

from ml.data import build_historical_multiclub_legacy as legacy

_original_parse_match_page = legacy.parse_match_page


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


def parse_match_page(match_id: int, html: str) -> dict:
    row = _original_parse_match_page(match_id, html)
    row["season"] = _canonical_season(row["season"])
    return row


legacy.parse_match_page = parse_match_page


if __name__ == "__main__":
    legacy.main()
