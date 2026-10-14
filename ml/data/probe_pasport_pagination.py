#!/usr/bin/env python3
from __future__ import annotations

import re
import requests
from bs4 import BeautifulSoup

URL = 'https://kibice.krakow.business/sezon/2024-25'
HEADERS = {'User-Agent': 'Mozilla/5.0 BeyondTicketingResearch/1.0'}

r = requests.get(URL, headers=HEADERS, timeout=45)
print('status', r.status_code, 'len', len(r.text), 'url', r.url)
r.raise_for_status()
html = r.text
soup = BeautifulSoup(html, 'html.parser')

print('\nFORMS')
for form in soup.find_all('form'):
    print('form', form.get('action'), form.get('method'), form.attrs)

print('\nLINKS_WITH_PAGINATION_HINTS')
seen=set()
for a in soup.find_all('a', href=True):
    href=a['href']
    text=' '.join(a.stripped_strings)
    candidate=f'{text} -> {href}'
    low=candidate.lower()
    if any(k in low for k in ['page', 'strona', 'offset', 'next', 'nast', 'więcej', 'wiecej', 'ekstraklasa', '2024-25']):
        if candidate not in seen:
            seen.add(candidate)
            print(candidate)

print('\nSCRIPTS')
for script in soup.find_all('script'):
    src=script.get('src')
    body=script.get_text(' ', strip=True)
    if src:
        print('src', src)
    if body and any(k in body.lower() for k in ['page', 'offset', 'cursor', 'match', 'mecz', 'api', 'fetch', 'htmx']):
        print('body', body[:1500])

print('\nKEYWORD_CONTEXTS')
for pattern in ['page', 'offset', 'cursor', 'api/', 'fetch(', 'hx-get', 'load-more', 'pagination', 'strona', 'mecze']:
    matches=list(re.finditer(pattern, html, re.I))
    print('PATTERN', pattern, 'COUNT', len(matches))
    for m in matches[:10]:
        start=max(0,m.start()-250); end=min(len(html),m.end()+500)
        print(html[start:end].replace('\n',' ')[:900])
        print('---')
