#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter

import requests

API = 'https://api.fundacjanh.org/api/kibice/matches'
HEADERS = {'User-Agent': 'Mozilla/5.0 BeyondTicketingResearch/1.0'}
SEASONS = {
    '2021/22': ('2021-07-01', '2022-06-30'),
    '2022/23': ('2022-07-01', '2023-06-30'),
    '2023/24': ('2023-07-01', '2024-06-30'),
    '2024/25': ('2024-07-01', '2025-06-30'),
}


def fetch_all(date_from: str, date_to: str) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    expected_total = None
    while True:
        params = {
            'tier': 1,
            'dateFrom': date_from,
            'dateTo': date_to,
            'limit': 100,
            'offset': offset,
        }
        response = requests.get(API, params=params, headers=HEADERS, timeout=45)
        print('REQUEST', response.url, 'STATUS', response.status_code, 'LEN', len(response.text))
        response.raise_for_status()
        payload = response.json()
        batch = payload.get('matches') or []
        total = payload.get('total')
        if expected_total is None and isinstance(total, int):
            expected_total = total
        print('BATCH', len(batch), 'TOTAL', total, 'OFFSET', offset)
        rows.extend(batch)
        if not batch:
            break
        offset += len(batch)
        if isinstance(total, int) and offset >= total:
            break
        if len(batch) < 100 and total is None:
            break
        if offset > 2000:
            raise RuntimeError('pagination safety stop')
    if expected_total is not None and len(rows) != expected_total:
        raise RuntimeError(f'Expected {expected_total} API rows, got {len(rows)}')
    return rows


for season, (date_from, date_to) in SEASONS.items():
    rows = fetch_all(date_from, date_to)
    season_counts = Counter(str(row.get('season')) for row in rows)
    tier_counts = Counter(str(row.get('tier_level')) for row in rows)
    attendance_count = sum(row.get('attendance') is not None for row in rows)
    print('\nSEASON_WINDOW', season)
    print('ROWS', len(rows))
    print('SEASON_COUNTS', season_counts)
    print('TIER_COUNTS', tier_counts)
    print('ATTENDANCE_ROWS', attendance_count)
    if rows:
        print('KEYS', sorted(rows[0].keys()))
        print('FIRST', rows[0])
        print('LAST', rows[-1])
