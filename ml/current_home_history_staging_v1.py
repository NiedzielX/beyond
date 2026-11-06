"""Pure verified source staging; no network, database, inference or fitting."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from zoneinfo import ZoneInfo

from ml.current_home_history_source_audit_v1 import SOURCES, MAX_BYTES
from ml.public_attendance_source_audit_v1 import extract
from ml.verified_attendance_source_rows_v1 import TEAMS, prepare_import_rows
from ml.demand_engine.current_structural_prior_features import DEFAULT_KEY_ALIASES

VERSION = 'current-home-history-staging-v1'
TEAMS_V1 = {**TEAMS, 'Radomiak': ('radomiak_radom', 'Radomiak Radom', 'radomiak_radom')}
PAGE_HOMES = dict(zip(SOURCES, ('Motor', 'Korona', 'Widzew', 'Piast')))
SPORTING_NAMES = {'Legia Warsaw': 'Legia Warszawa', 'Zagłębie Lubin': 'KGHM Zagłębie Lubin'}
ROW = re.compile(r'^(?P<home>.+?) (?P<hs>\d+):(?P<as>\d+) (?P<away>.+?) '
                 r'(?P<attendance>\d[\d ]*) 2026/2027 • Ekstraklasa • '
                 r'(?P<date>\d{2}\.\d{2}\.\d{4}) (?P<time>\d{2}:\d{2})$')
WARSAW = ZoneInfo('Europe/Warsaw')


def stamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Explicit source knowledge time required')
    return result.astimezone(timezone.utc)


def stage(sources, raw_sources, sporting, events, existing, *, run_id, verified_at, now):
    if type(run_id) is not int or run_id <= 0:
        raise ValueError('Actual source run identity required')
    verified = stamp(verified_at)
    if verified > stamp(now):
        raise ValueError('Future verification cannot establish knowledge')
    if len(sources) != 4 or len({s['url'] for s in sources}) != 4 or set(raw_sources) != set(SOURCES):
        raise ValueError('Exactly four original fixed source pages required')
    staged, identities, matchdays = [], set(), set()
    for source in sources:
        url = source['url']
        if (url not in PAGE_HOMES or source.get('http_status') != 200 or source.get('error_type')
                or source.get('text_truncated') is not False
                or not stamp(source['retrieved_at']) <= stamp(source['receipt_completed_at']) <= verified):
            raise ValueError('Incomplete or not-yet-received source')
        raw = raw_sources[url]
        if len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError('Original public source bytes changed')
        if extract(raw)['text'] != source['text']:
            raise ValueError('Extracted source text differs from original bytes')
        for line in source['text'].splitlines():
            match = ROW.fullmatch(line)
            if match is None:
                if '2026/2027 • Ekstraklasa •' in line:
                    raise ValueError('Unparsed current-season source fixture')
                continue
            value = match.groupdict()
            if value['home'] != PAGE_HOMES[url] or value['home'] not in TEAMS_V1 or value['away'] not in TEAMS_V1:
                raise ValueError('Source page club or exact opponent identity differs')
            home, away = TEAMS_V1[value['home']], TEAMS_V1[value['away']]
            local = datetime.strptime(value['date'] + ' ' + value['time'], '%d.%m.%Y %H:%M').replace(tzinfo=WARSAW)
            kickoff = local.astimezone(timezone.utc)
            actual = int(value['attendance'].replace(' ', ''))
            if (home[0] == away[0] or actual <= 0 or kickoff >= stamp(source['retrieved_at'])
                    or not datetime(2026, 7, 1, tzinfo=WARSAW) <= local < datetime(2027, 7, 1, tzinfo=WARSAW)):
                raise ValueError('Invalid fixture, season, attendance or completion time')
            matches = [s for s in sporting if s['season'] == '2026-2027'
                and SPORTING_NAMES.get(s['home_team'], s['home_team']) == home[1]
                and SPORTING_NAMES.get(s['away_team'], s['away_team']) == away[1]
                and s['event_date'] == local.date().isoformat()]
            if (len(matches) != 1 or matches[0]['completed'] is not True
                    or any(type(matches[0][k]) is not int for k in ('home_score', 'away_score'))
                    or (matches[0]['home_score'], matches[0]['away_score']) != (int(value['hs']), int(value['as']))):
                raise ValueError('Unique completed sporting date/result verification required')
            identity = (home[0], away[0], kickoff)
            matchday = (home[0], local.date())
            if identity in identities or matchday in matchdays:
                raise ValueError('Duplicate or ambiguous home-matchday source')
            identities.add(identity); matchdays.add(matchday)
            for event in events:
                event_home = DEFAULT_KEY_ALIASES.get(event['club_slug'], event['club_slug'])
                if event_home == home[0] and stamp(event['kickoff_at']).astimezone(WARSAW).date() == local.date():
                    if stamp(event['kickoff_at']) != kickoff:
                        raise ValueError('Canonical tracked fixture clock conflict')
            staged.append({'club_slug': home[0], 'home_team': home[1], 'away_team': away[1],
                'opponent_key': away[2], 'kickoff_at': kickoff.isoformat(), 'actual_attendance': actual,
                'season': '2026/2027', 'competition': 'Ekstraklasa', 'competition_key': 'ekstraklasa',
                'source_url': url, 'source_observed_at': source['retrieved_at'],
                'source_name': 'frekwencyjny.pl — verified fixture record',
                'verification_reason': 'Exact registered home/away, season/date/result and unique completed sporting fixture; public source provides reported kickoff/attendance',
                'source_payload': {'source_sha256': source['sha256'], 'source_line': line,
                    'retrieved_at': source['retrieved_at'], 'historical_publication_time_verified': False,
                    'verification_run_id': run_id, 'knowledge_backdated': False,
                    'sporting_source_event_id': matches[0]['source_event_id'],
                    'independent_kickoff_clock_verified': False}})
    # Reject canonical aliases and date-clock conflicts before the legacy exact-key preparer.
    for row in staged:
        for old in existing:
            home = DEFAULT_KEY_ALIASES.get(old['club_slug'], old['club_slug'])
            if home == row['club_slug'] and stamp(old['kickoff_at']).astimezone(WARSAW).date() == stamp(row['kickoff_at']).astimezone(WARSAW).date():
                if home != old['club_slug'] or stamp(old['kickoff_at']) != stamp(row['kickoff_at']):
                    raise ValueError('Existing canonical history alias or source clock conflicts')
    return prepare_import_rows(staged, existing, verified_at)
