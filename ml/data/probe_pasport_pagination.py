#!/usr/bin/env python3
from __future__ import annotations

from io import StringIO
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = 'https://kibice.krakow.business'
HEADERS = {'User-Agent': 'Mozilla/5.0 BeyondTicketingResearch/1.0'}


def inspect(url: str) -> None:
    r = requests.get(url, headers=HEADERS, timeout=45)
    print('\nURL', url, 'STATUS', r.status_code, 'LEN', len(r.text), 'FINAL', r.url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = pd.read_html(StringIO(r.text))
    for idx, t in enumerate(tables):
        cols = [str(c) for c in t.columns]
        if any('Mecz' in c for c in cols) or any('Widz' in c for c in cols):
            print('TABLE', idx, 'ROWS', len(t), 'COLS', cols)
            if len(t):
                print('FIRST', t.head(2).to_dict(orient='records'))
                print('LAST', t.tail(2).to_dict(orient='records'))

    print('PAGINATION_LINKS')
    seen = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = ' '.join(a.stripped_strings)
        candidate = f'{text} -> {href}'
        low = candidate.lower()
        if any(k in low for k in ['page=', 'strona', 'nast', 'poprz', 'next', 'previous', 'cursor', 'offset']):
            if candidate not in seen:
                seen.add(candidate)
                print(candidate)

    print('FORMS')
    for form in soup.find_all('form'):
        print('form', form.get('action'), form.get('method'), form.attrs)
        for inp in form.find_all(['input','select','button']):
            print(' ', inp.name, inp.get('name'), inp.get('value'), inp.get('type'))


inspect(f'{BASE}/mecze?season=2024%2F25&tier=1')
for page in [2, 3, 10, 11]:
    inspect(f'{BASE}/mecze?season=2024%2F25&tier=1&page={page}')

inspect(f'{BASE}/rozgrywki/ekstraklasa-2024-25')
for page in [2, 3, 10, 11]:
    inspect(f'{BASE}/rozgrywki/ekstraklasa-2024-25?page={page}')
