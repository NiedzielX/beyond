"""Bounded public-source retrieval only; no attendance import or model operation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

SOURCES = (
    'https://www.frekwencyjny.pl/kluby/wisla-krakow',
    'https://www.frekwencyjny.pl/kluby/gornik-zabrze',
    'https://www.frekwencyjny.pl/kluby/lech-poznan',
    'https://www.frekwencyjny.pl/',
    'https://piast.gliwice.pl/2026/10/18/piast-zatrzymal-lidera-2/',
    'https://wroclife.pl/amp/artykul/8667/w-koncu-wygrana-slask-opuszcza-strefe-spadkowa',
)
MAX_BYTES = 2*1024*1024
MAX_TEXT = 24000


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = 0; self.title = False; self.parts = []; self.titles = []
    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'noscript'}: self.skip += 1
        if tag == 'title': self.title = True
        if tag in {'tr', 'p', 'h1', 'h2', 'h3', 'li', 'br'} and not self.skip: self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in {'script', 'style', 'noscript'}: self.skip = max(0, self.skip-1)
        if tag == 'title': self.title = False
        if tag in {'tr', 'p', 'div', 'section', 'article'} and not self.skip: self.parts.append('\n')
    def handle_data(self, value):
        if not self.skip:
            self.parts.append(value+' ')
            if self.title: self.titles.append(value)


def extract(raw):
    parser = Text(); parser.feed(raw.decode('utf-8', errors='replace'))
    lines = [' '.join(line.split()) for line in ''.join(parser.parts).splitlines()]
    text = '\n'.join(line for line in lines if line)
    return {'title': ' '.join(parser.titles), 'text': text[:MAX_TEXT], 'text_truncated': len(text) > MAX_TEXT,
            'full_extracted_characters': len(text)}


def fetch(url, directory, index):
    if url not in SOURCES: raise ValueError('Only the fixed declared public source pages are allowed')
    result = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
              'fixture_identity_verified': False, 'automatic_label_import': False}
    request = urllib.request.Request(url, headers={'User-Agent': 'Beyond-public-source-verification/1.0', 'Accept-Encoding': 'identity'})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read(MAX_BYTES+1)
            result.update(http_status=response.status, final_url=response.url, content_type=response.headers.get('Content-Type'))
        if len(raw) > MAX_BYTES: raise ValueError('Public response exceeds declared size bound')
        (directory/f'source-{index}.html').write_bytes(raw)
        result.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), **extract(raw))
    except Exception as exc:
        result.update(error_type=type(exc).__name__, http_status=getattr(exc, 'code', result.get('http_status')))
    return result


def publish(results):
    if os.environ.get('GITHUB_REPOSITORY') != 'NiedzielX/beyond': raise ValueError('Audit check restricted to the authorized repository')
    token = os.environ['GITHUB_TOKEN']; sha = os.environ['GITHUB_SHA']
    for index, result in enumerate(results):
        body = {'name': f'public-attendance-source-{index}', 'head_sha': sha, 'status': 'completed', 'conclusion': 'neutral',
            'output': {'title': 'Read-only public attendance source audit',
                       'summary': 'Retrieval evidence only. Fixture identity unverified; no label import or model change.',
                       'text': json.dumps({'version': 'public-attendance-source-audit-v1', **result}, ensure_ascii=False)}}
        if len(body['output']['text'].encode()) > 60000: raise ValueError('Structured check output exceeds bound')
        request = urllib.request.Request('https://api.github.com/repos/NiedzielX/beyond/check-runs',
            data=json.dumps(body).encode(), headers={'Authorization': 'Bearer '+token, 'Accept': 'application/vnd.github+json',
                'Content-Type': 'application/json', 'User-Agent': 'Beyond-source-audit'}, method='POST')
        with urllib.request.urlopen(request, timeout=25) as response:
            saved = json.load(response)
        print(json.dumps({'check_run_id': saved['id'], 'source_index': index, 'http_status': result.get('http_status'),
                          'fixture_identity_verified': False, 'automatic_label_import': False}), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True); p.add_argument('--publish-checks', action='store_true')
    a = p.parse_args(); a.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    results = [fetch(url, a.output_dir, index) for index, url in enumerate(SOURCES)]
    (a.output_dir/'manifest.json').write_text(json.dumps({'version': 'public-attendance-source-audit-v1',
        'sources': results, 'automatic_label_import': False, 'production_change': False}, indent=2, ensure_ascii=False)+'\n')
    if a.publish_checks: publish(results)
    print(json.dumps({'retrievals_attempted': len(results), 'http_200': sum(r.get('http_status') == 200 and not r.get('error_type') for r in results),
                      'verified_fixtures': 0, 'labels_imported': 0, 'production_change': False}))


if __name__ == '__main__': main()
