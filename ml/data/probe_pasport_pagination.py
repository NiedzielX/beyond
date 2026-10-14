#!/usr/bin/env python3
from __future__ import annotations

import re
from collections import Counter
from io import StringIO
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = 'https://kibice.krakow.business'
HEADERS = {'User-Agent': 'Mozilla/5.0 BeyondTicketingResearch/1.0'}


def inspect(url: str, *, show_scripts: bool = False) -> None:
    r = requests.get(url, headers=HEADERS, timeout=45)
    print('\nURL', url, 'STATUS', r.status_code, 'LEN', len(r.text), 'FINAL', r.url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    try:
        tables = pd.read_html(StringIO(r.text), flavor='lxml')
    except ValueError:
        tables = []
    matched_tables = []
    for idx, t in enumerate(tables):
        cols = [str(c) for c in t.columns]
        if any('Mecz' in c for c in cols) or any('Widz' in c for c in cols):
            matched_tables.append(t)
            print('TABLE', idx, 'ROWS', len(t), 'COLS', cols)
            if len(t):
                print('FIRST', t.head(1).to_dict(orient='records'))
                print('LAST', t.tail(1).to_dict(orient='records'))

    hrefs = [a.get('href') for a in soup.find_all('a', href=True)]
    path_heads = Counter()
    for href in hrefs:
        path = urlparse(href).path
        parts = [p for p in path.split('/') if p]
        if parts:
            path_heads[parts[0]] += 1
    print('LINK_PREFIX_COUNTS', path_heads.most_common(15))
    match_like = sorted({href for href in hrefs if '/mecz' in href.lower() or '/match' in href.lower()})
    print('MATCH_LIKE_LINKS', len(match_like), match_like[:10], match_like[-5:])

    for marker in ['Pokazujemy 100 z 306', '306 mecz', 'Widzów', 'Zagłębie Lubin', 'pageSize', 'limit', 'offset', 'cursor']:
        print('MARKER', marker, 'COUNT', r.text.lower().count(marker.lower()))

    if show_scripts:
        scripts = [s.get('src') for s in soup.find_all('script', src=True)]
        print('SCRIPT_COUNT', len(scripts))
        for src in scripts:
            full = src if src.startswith('http') else BASE + src
            js = requests.get(full, headers=HEADERS, timeout=45)
            if js.status_code != 200:
                continue
            body = js.text
            hits = []
            for token in ['pageSize', 'limit', 'offset', 'cursor', 'searchParams', 'season', 'tier', '/api/', 'supabase']:
                if token.lower() in body.lower():
                    hits.append(token)
            if hits:
                print('SCRIPT_HITS', src, hits, 'LEN', len(body))
                for token in hits:
                    m = re.search(re.escape(token), body, re.I)
                    if m:
                        print('CTX', token, body[max(0,m.start()-250):m.end()+500][:800])


base_listing = f'{BASE}/mecze?season=2024%2F25&tier=1'
inspect(base_listing, show_scripts=True)
for param in [
    'limit=500', 'take=500', 'perPage=500', 'per_page=500', 'pageSize=500',
    'page_size=500', 'size=500', 'offset=100', 'skip=100', 'cursor=100',
]:
    inspect(base_listing + '&' + param)

competition = f'{BASE}/rozgrywki/ekstraklasa-2024-25'
inspect(competition, show_scripts=True)
for param in ['limit=500', 'take=500', 'perPage=500', 'pageSize=500', 'offset=100']:
    inspect(competition + '?' + param)
