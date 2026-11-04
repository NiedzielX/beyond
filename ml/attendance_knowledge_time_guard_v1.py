"""Read-only source adapter: fixture time alone never proves label availability.

This version does not replace the frozen materializer or deploy a new feed.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
from zoneinfo import ZoneInfo

VERSION = 'attendance-knowledge-time-guard-v1'


def timestamp(value):
    if not isinstance(value, str): raise ValueError('Explicit knowledge timestamp required')
    try: result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError: raise ValueError('Invalid knowledge timestamp') from None
    if result.tzinfo is None or result.utcoffset() is None: raise ValueError('Timezone-aware timestamp required')
    return result.astimezone(timezone.utc)


def attendance(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0 or int(value) != value:
        raise ValueError('Positive integer attendance required')
    return int(value)


def source_catalog(history, outcomes, events):
    """Normalize raw sources without fabricating missing knowledge metadata."""
    event_by = {r['id']: r for r in events}
    if len(event_by) != len(events): raise ValueError('Ambiguous canonical event identity')
    normalized, rejected = [], []
    for kind, rows in [('history', history), ('outcome', outcomes)]:
        for row in rows:
            source_id = row.get('id') if kind == 'history' else row.get('ticket_event_id')
            try:
                fixture = row if kind == 'history' else event_by[row['ticket_event_id']]
                competition = fixture.get('competition_key', fixture.get('competition'))
                if competition not in ('ekstraklasa', 'Ekstraklasa'): raise ValueError('Competition outside contract')
                club, kickoff = fixture['club_slug'], timestamp(fixture['kickoff_at'])
                if not isinstance(club, str) or not club: raise ValueError('Missing canonical club')
                if source_id is None: raise ValueError('Missing source identity')
                local = kickoff.astimezone(ZoneInfo('Europe/Warsaw'))
                year = local.year if local.month >= 7 else local.year - 1
                season = f'{year}/{year + 1}'
                declared = fixture.get('season')
                if kind == 'history' and declared is None: raise ValueError('Missing history season')
                if declared is not None and declared.replace('-', '/') != season:
                    raise ValueError('Fixture season conflicts with kickoff')
                field = 'source_observed_at' if kind == 'history' else 'confirmed_at'
                times = [timestamp(row.get(field)), timestamp(row.get('created_at'))]
                verified_at = (row.get('source_payload') or {}).get('verified_at')
                if verified_at is not None: times.append(timestamp(verified_at))
                known = max(times)
                if known < kickoff: raise ValueError('Attendance knowledge precedes kickoff')
                value = attendance(row.get('actual_attendance'))
                normalized.append({'club_slug': club, 'kickoff_at': kickoff.isoformat(),
                    'actual_attendance': value, 'known_at': known.isoformat(),
                    'source_kind': kind, 'source_id': source_id, 'source_priority': 2 if kind == 'outcome' else 1,
                    'source_name': row.get('source_name'), 'source_url': row.get('source_url'),
                    'source_sha256': (row.get('source_payload') or {}).get('source_sha256'),
                    'season': season})
            except (KeyError, TypeError, ValueError) as exc:
                rejected.append({'source_kind': kind, 'source_id': source_id, 'reason': str(exc)})
    return {'version': VERSION, 'records': normalized, 'rejected_sources': rejected}


def available_at(catalog, cutoff):
    """Choose only genuine eligible records; conflicts never pick a winner."""
    if catalog.get('version') != VERSION: raise ValueError('Unexpected source catalog version')
    as_of = timestamp(cutoff); groups, excluded = {}, []
    for row in catalog['records']:
        kickoff, known = timestamp(row['kickoff_at']), timestamp(row['known_at'])
        if kickoff >= as_of or known > as_of:
            excluded.append({'source_kind': row['source_kind'], 'source_id': row['source_id'],
                             'reason': 'FIXTURE_NOT_COMPLETED' if kickoff >= as_of else 'SOURCE_NOT_YET_KNOWN'})
            continue
        key = (row['club_slug'], kickoff)
        groups.setdefault(key, []).append(row)
    selected, conflicts = [], []
    for key, rows in sorted(groups.items()):
        if len({r['actual_attendance'] for r in rows}) != 1:
            conflicts.append({'club_slug': key[0], 'kickoff_at': key[1].isoformat(),
                              'reason': 'CONFLICTING_KNOWN_ATTENDANCE', 'source_count': len(rows)})
            continue
        selected.append(sorted(rows, key=lambda r: (-r['source_priority'], timestamp(r['known_at']), str(r['source_id'])))[0])
    return {'version': VERSION, 'as_of_at': as_of.isoformat(), 'eligible': selected,
            'excluded_sources': excluded, 'conflicts': conflicts, 'rejected_sources': catalog['rejected_sources'],
            'production_change': False, 'live_adjustment': 0}
