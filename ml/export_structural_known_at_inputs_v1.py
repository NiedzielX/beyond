"""Bounded private read-only export retaining actual attendance knowledge times."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

from ml.export_c1_matched_audit_inputs_v1 import Reader

VERSION = 'structural-known-at-input-export-v1'
ROOT = Path(__file__).resolve().parents[1]
LIMIT = 1000
MAX_BYTES = 16 * 1024 * 1024
TABLES = {
    'history': ('ml_match_history', 'id', 'id,club_slug,external_match_key,season,competition,competition_key,kickoff_at,actual_attendance,source_observed_at,created_at,updated_at,source_name,source_url,source_payload'),
    'outcomes': ('ticket_event_outcomes', 'ticket_event_id', 'ticket_event_id,actual_attendance,confirmed_at,created_at,updated_at,source_name,source_url'),
    'ticket_events': ('ticket_events', 'id', 'id,club_slug,home_team,away_team,competition,kickoff_at'),
    'sporting': ('sporting_league_matches_shadow', 'source_event_id', 'source_event_id,season,round_number,event_date,home_team,away_team,home_score,away_score,completed,match_status,fetched_at'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def checked_rows(rows, total, key):
    if (not isinstance(rows, list) or type(total) is not int or not 0 <= total <= LIMIT
            or len(rows) != total):
        raise ValueError('Exact count mismatch or bounded source truncated')
    identities = [r.get(key) for r in rows]
    valid = lambda i: (type(i) is int and i > 0) or (key == 'source_event_id' and isinstance(i, str) and i.isdigit() and int(i) > 0)
    if any(not valid(i) for i in identities) or len(set(map(str,identities))) != len(rows):
        raise ValueError('Missing or duplicate source identity')
    return rows


class SourceReader(Reader):
    def counted(self, name, filters=()):
        table, key, columns = TABLES[name]
        params = [('select', columns), ('order', key+'.asc'), ('limit', str(LIMIT)), *filters]
        request = urllib.request.Request(self.base+'/rest/v1/'+table+'?'+urllib.parse.urlencode(params),
            headers={**self.headers, 'Prefer': 'count=exact'})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                content_range = response.headers.get('Content-Range', '')
                total_text = content_range.rsplit('/', 1)[-1]
                if not total_text.isdigit(): raise ValueError('Exact count receipt missing')
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES: raise ValueError('Bounded source byte limit exceeded')
                rows = json.loads(raw); total = int(total_text)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f'Bounded source read failed: {type(exc).__name__}') from None
        return checked_rows(rows, total, key)


def validate_envelope(data):
    if data.get('version') != VERSION or data.get('read_only') is not True or data.get('production_change') is not False:
        raise ValueError('Invalid private source contract identity')
    if data.get('live_adjustment') != 0: raise ValueError('Production adjustment forbidden')
    from ml.attendance_knowledge_time_guard_v1 import timestamp
    started, completed = timestamp(data['requested_at']), timestamp(data['completed_at'])
    if completed < started or (completed-started).total_seconds() > 300:
        raise ValueError('Source capture interval invalid or too long')
    expected = digest({k: v for k,v in data.items() if k != 'export_sha256'})
    if expected != data.get('export_sha256'): raise ValueError('Private source hash mismatch')
    if len(json.dumps(data, allow_nan=False).encode()) > MAX_BYTES:
        raise ValueError('Private export exceeds byte bound')
    parts = data.get('parts'); receipts = data.get('receipts')
    if set(parts or {}) != {'due','aliases',*TABLES} or set(receipts or {}) != set(parts):
        raise ValueError('Missing required source partition')
    for name, value in parts.items():
        if not isinstance(value, list) or receipts[name] != {'count': len(value), 'sha256': digest(value)}:
            raise ValueError('Source partition receipt mismatch')
        if name in TABLES: checked_rows(value, len(value), TABLES[name][1])
        elif len(value)>LIMIT: raise ValueError('RPC source expanded beyond bound')
    aliases = parts['aliases']
    if (any(not isinstance(r.get('alias'), str) or not r['alias'] or not isinstance(r.get('club_key'), str)
            or not r['club_key'] for r in aliases)
            or len({r['alias'] for r in aliases}) != len(aliases)):
        raise ValueError('Ambiguous or missing club alias identity')
    return data


def capture(reader=None, clock=None):
    reader = reader or SourceReader(); clock = clock or (lambda: datetime.now(timezone.utc))
    requested = clock().isoformat()
    parts = {'due': reader.request('rpc/get_due_early_structural_prior_inputs_v1',
                                 {'p_requested_at': requested, 'p_include_ready_event_id': None}),
             'aliases': reader.request('rpc/get_structural_prior_club_aliases_v1', {})}
    for name in ['history', 'outcomes', 'ticket_events']: parts[name] = reader.counted(name)
    seasons = sorted({r['season'].replace('/', '-') for r in parts['due'] if r.get('season')})
    if any(not s[:4].isdigit() or len(s)!=9 or not s[5:].isdigit() or s[4]!='-' for s in seasons):
        raise ValueError('Unexpected due season')
    parts['sporting'] = reader.counted('sporting', [('season', 'in.('+','.join(seasons)+')')]) if seasons else []
    payload = {'version': VERSION, 'requested_at': requested, 'completed_at': clock().isoformat(),
        'parts': parts, 'receipts': {n:{'count': len(v), 'sha256': digest(v)} for n,v in parts.items()},
        'read_only': True, 'production_change': False, 'live_adjustment': 0,
        'consistency': 'bounded independent REST reads; created/known timestamps filtered per cutoff; not a DB transaction'}
    payload['export_sha256'] = digest(payload)
    return validate_envelope(payload)


def write_private(directory, payload):
    validate_envelope(payload)
    directory = Path(directory).resolve()
    if directory.is_relative_to(ROOT): raise ValueError('Raw sources must remain outside the repository')
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    file = directory/'inputs.json'
    with file.open('x') as handle: json.dump(payload, handle, indent=2, allow_nan=False); handle.write('\n')
    file.chmod(0o600)
    return file


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args(); value = capture(); path = write_private(args.output_dir, value)
    print(json.dumps({'status': 'PRIVATE_EXACT_COUNT_EXPORT_VERIFIED', 'path': str(path),
        'export_sha256': value['export_sha256'], 'counts': {n:r['count'] for n,r in value['receipts'].items()},
        'read_only': True, 'production_change': False}))


if __name__ == '__main__': main()
