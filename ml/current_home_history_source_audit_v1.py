"""Retrieve four fixed public club pages; no database or model operations."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request
import zlib

from ml.public_attendance_source_audit_v1 import extract, MAX_BYTES

VERSION = 'current-home-history-public-source-audit-v1'
SOURCES = tuple('https://www.frekwencyjny.pl/kluby/' + slug for slug in
                ('motor-lublin', 'korona-kielce', 'widzew-lodz', 'piast-gliwice'))
HOSTS = {'www.frekwencyjny.pl', 'frekwencyjny.pl'}


def allowed_redirect(url):
    parsed = urllib.parse.urlparse(url)
    return (parsed.scheme == 'https' and parsed.hostname in HOSTS
            and parsed.port in (None, 443) and not parsed.username and not parsed.password)


class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_redirect(newurl):
            raise ValueError('Public source redirected outside the declared HTTPS host')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, directory, index, opener=None):
    if url not in SOURCES:
        raise ValueError('Only the four fixed club source pages are allowed')
    result = {'version': VERSION, 'url': url,
              'retrieved_at': datetime.now(timezone.utc).isoformat(),
              'fixture_identity_verified': False, 'automatic_label_import': False}
    try:
        request = urllib.request.Request(url, headers={
            'User-Agent': 'Beyond-public-source-verification/1.0', 'Accept-Encoding': 'identity'})
        opener = opener or urllib.request.build_opener(PublicRedirect())
        with opener.open(request, timeout=20) as response:
            if not allowed_redirect(response.url):
                raise ValueError('Unexpected final public source host')
            raw = response.read(MAX_BYTES + 1)
            result.update(http_status=response.status, final_url=response.url,
                          content_type=response.headers.get('Content-Type'))
        if len(raw) > MAX_BYTES:
            raise ValueError('Public source exceeds the declared size bound')
        if result['http_status'] != 200 or 'text/html' not in (result['content_type'] or '').lower():
            raise ValueError('Complete HTML source required')
        with (directory / f'source-{index}.html').open('xb') as file:
            file.write(raw)
        result.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), **extract(raw))
    except Exception as exc:
        result.update(error_type=type(exc).__name__, http_status=getattr(exc, 'code', result.get('http_status')))
    result['receipt_completed_at'] = datetime.now(timezone.utc).isoformat()
    return result


def raw_chunks(directory, index, source):
    if source.get('error_type') or source.get('http_status') != 200:
        return []
    raw = (directory / f'source-{index}.html').read_bytes()
    if len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != source['sha256']:
        raise ValueError('Saved raw source differs from its receipt')
    packed = base64.b64encode(zlib.compress(raw)).decode()
    size = 40000
    chunks = [packed[i:i+size] for i in range(0, len(packed), size)]
    if not 1 <= len(chunks) <= 8:
        raise ValueError('Compressed raw source exceeds bounded check transport')
    return [{'version': VERSION, 'source_index': index, 'source_sha256': source['sha256'],
             'encoding': 'zlib+base64', 'part': i, 'parts': len(chunks), 'payload': value,
             'raw_bytes': len(raw), 'automatic_label_import': False}
            for i, value in enumerate(chunks)]


def publish(results, directory):
    if os.environ.get('GITHUB_REPOSITORY') != 'NiedzielX/beyond':
        raise ValueError('Authorized repository required')
    entries = []
    for index, result in enumerate(results):
        entries.append((f'current-home-history-source-{index}', result))
        entries.extend((f'current-home-history-raw-{index}-{chunk["part"]}', chunk)
                       for chunk in raw_chunks(directory, index, result))
    for name, result in entries:
        text = json.dumps(result, ensure_ascii=False)
        if len(text.encode()) > 60000:
            raise ValueError('Public evidence exceeds the check output bound')
        body = {'name': name, 'head_sha': os.environ['GITHUB_SHA'],
                'status': 'completed', 'conclusion': 'neutral', 'output': {
                    'title': 'Read-only public home-history coverage audit',
                    'summary': 'Public retrieval only; no verified fixture, database or model operation.',
                    'text': text}}
        request = urllib.request.Request('https://api.github.com/repos/NiedzielX/beyond/check-runs',
            data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
                'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(request, timeout=25) as response:
            saved = json.load(response)
        print(json.dumps({'check_id': saved['id'], 'evidence_name': name, 'labels_imported': 0}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--publish-checks', action='store_true')
    args = parser.parse_args()
    args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    results = [fetch(url, args.output_dir, index) for index, url in enumerate(SOURCES)]
    (args.output_dir / 'manifest.json').write_text(json.dumps({
        'version': VERSION, 'sources': results, 'labels_imported': 0,
        'production_change': False, 'live_adjustment': 0}, indent=2, ensure_ascii=False) + '\n')
    if args.publish_checks:
        publish(results, args.output_dir)
    print(json.dumps({'retrievals_attempted': len(results), 'labels_imported': 0,
                      'production_change': False, 'live_adjustment': 0}))


if __name__ == '__main__':
    main()
