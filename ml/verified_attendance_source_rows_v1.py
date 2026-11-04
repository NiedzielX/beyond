"""Parse declared public-source fixture text into a staging queue, never DB writes."""
from __future__ import annotations

from datetime import datetime, timezone
from copy import deepcopy
import hashlib
import re
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo('Europe/Warsaw')
TEAMS = {
    'Wisła K.': ('wislakrakow', 'Wisła Kraków', 'wisla_krakow'),
    'Górnik Z.': ('gornikzabrze', 'Górnik Zabrze', 'gornikzabrze'),
    'Lech': ('lech', 'Lech Poznań', 'lech'),
    'GKS K.': ('gkskatowice', 'GKS Katowice', 'gkskatowice'),
    'Śląsk': ('slaskwroclaw', 'Śląsk Wrocław', 'slask_wroclaw'),
    'Wisła Pł.': ('wisla_plock', 'Wisła Płock', 'wisla_plock'),
    'Jagiellonia': ('jagiellonia', 'Jagiellonia Białystok', 'jagiellonia'),
    'Raków': ('rakow', 'Raków Częstochowa', 'rakow'),
    'Wieczysta': ('wieczysta_krakow', 'Wieczysta Kraków', 'wieczysta_krakow'),
    'Legia': ('legia', 'Legia Warszawa', 'legia'),
    'Cracovia': ('cracovia', 'Cracovia', 'cracovia'),
    'Motor': ('motorlublin', 'Motor Lublin', 'motorlublin'),
    'Piast': ('piastgliwice', 'Piast Gliwice', 'piastgliwice'),
    'Widzew': ('widzewlodz', 'Widzew Łódź', 'widzew'),
    'Zagłębie L.': ('zaglebie_lubin', 'KGHM Zagłębie Lubin', 'zaglebie_lubin'),
    'Korona': ('koronakielce', 'Korona Kielce', 'koronakielce'),
    'Pogoń': ('pogonszczecin', 'Pogoń Szczecin', 'pogonszczecin'),
}
CLUB = re.compile(r'^(?P<home>.+?) \d+:\d+ (?P<away>.+?) (?P<attendance>\d[\d ]*) (?P<season>2026/2027) • (?P<competition>Ekstraklasa) • (?P<date>\d{2}\.\d{2}\.\d{4}) (?P<time>\d{2}:\d{2})$')
HOME = re.compile(r'^\d{2}\.\d{2} \d{2}:\d{2} (?P<date>\d{2}\.\d{2}\.\d{4}) (?P<time>\d{2}:\d{2}) (?P<home>.+?) \d+:\d+ (?P<away>.+?) (?P<attendance>\d[\d ]*)$')


def parse_source(source):
    if source.get('http_status') != 200 or source.get('error_type') or source.get('text_truncated'):
        raise ValueError('Source is inaccessible, incomplete or truncated')
    if not source.get('sha256') or not source.get('retrieved_at') or not source['url'].startswith('https://www.frekwencyjny.pl/'):
        raise ValueError('Unexpected source provenance')
    rows = {}
    for line in source['text'].splitlines():
        match = CLUB.fullmatch(line) or HOME.fullmatch(line)
        if match is None: continue
        values = match.groupdict()
        if values['home'] not in TEAMS or values['away'] not in TEAMS: continue
        home, away = TEAMS[values['home']], TEAMS[values['away']]
        if home[0] == away[0]: raise ValueError('Source contains an invalid same-club fixture')
        local = datetime.strptime(values['date']+' '+values['time'], '%d.%m.%Y %H:%M').replace(tzinfo=WARSAW)
        if not datetime(2026,7,1,tzinfo=WARSAW) <= local < datetime(2027,7,1,tzinfo=WARSAW):
            continue
        kickoff = local.astimezone(timezone.utc).isoformat(); actual = int(values['attendance'].replace(' ', ''))
        if actual <= 0 or local >= datetime.fromisoformat(source['retrieved_at']): raise ValueError('Invalid or not-completed source fixture')
        row = {'club_slug': home[0], 'home_team': home[1], 'away_team': away[1], 'opponent_key': away[2],
               'kickoff_at': kickoff, 'actual_attendance': actual, 'season': '2026/2027',
               'competition': 'Ekstraklasa', 'competition_key': 'ekstraklasa',
               'source_name': 'frekwencyjny.pl — verified fixture record', 'source_url': source['url'],
               'source_observed_at': source['retrieved_at'], 'source_payload': {'source_sha256': source['sha256'],
                   'source_line': line, 'retrieved_at': source['retrieved_at'], 'historical_publication_time_verified': False,
                   'verification_run_id': 41840960556, 'knowledge_backdated': False}}
        key = (home[0], away[0], kickoff)
        if key in rows and rows[key]['actual_attendance'] != actual: raise ValueError('Conflicting source attendance')
        rows[key] = row
    return list(rows.values())


def match_completed_event(event, rows):
    candidates = [r for r in rows if r['home_team'] == event['home_team'] and r['away_team'] == event['away_team']
                  and datetime.fromisoformat(r['kickoff_at']).astimezone(WARSAW).date()
                  == datetime.fromisoformat(event['kickoff_at']).astimezone(WARSAW).date()]
    if not candidates: return {'status': 'SOURCE_FIXTURE_NOT_FOUND', 'ticket_event_id': event['id']}
    if len({(r['kickoff_at'], r['actual_attendance']) for r in candidates}) != 1:
        raise ValueError('Ambiguous source fixture/time/attendance')
    row = candidates[0]
    if datetime.fromisoformat(row['kickoff_at']) != datetime.fromisoformat(event['kickoff_at']):
        return {'status': 'EXACT_KICKOFF_CONFLICT', 'ticket_event_id': event['id'], 'source': row}
    if event['club_slug'] != row['club_slug'] or event['competition'] != row['competition']:
        raise ValueError('Canonical club/competition differs')
    return {'status': 'EXACT_VERIFIED_MATCH', 'ticket_event_id': event['id'], 'source': row}


def prepare_import_rows(staged, existing, verified_at):
    """Build append-only rows with actual verification time, never earlier knowledge."""
    known = datetime.fromisoformat(verified_at)
    if known.tzinfo is None: raise ValueError('Verification must be timezone-aware')
    result, seen = [], set()
    for source in staged:
        row = deepcopy(source)
        kickoff = datetime.fromisoformat(row['kickoff_at'])
        retrieved = datetime.fromisoformat(row['source_payload']['retrieved_at'])
        if known < retrieved or known < kickoff: raise ValueError('Cannot backdate verified knowledge')
        key = (row['club_slug'], kickoff)
        if key in seen: raise ValueError('Duplicate staged fixture')
        seen.add(key)
        matches = [r for r in existing if r['club_slug'] == key[0]
                   and datetime.fromisoformat(r['kickoff_at']) == kickoff]
        if any(int(r['actual_attendance']) != row['actual_attendance'] for r in matches):
            raise ValueError('Existing attendance conflict; updates forbidden')
        if matches: continue
        row['source_payload']['verification_reason'] = row.pop('verification_reason')
        row['source_payload']['verified_at'] = verified_at
        row['source_payload']['knowledge_backdated'] = False
        row['source_observed_at'] = verified_at
        row['attendance_definition'] = 'reported_match_attendance'
        identity = '|'.join([row['club_slug'], kickoff.isoformat(), row['opponent_key']])
        row['external_match_key'] = 'verified-public-v1:'+hashlib.sha256(identity.encode()).hexdigest()
        result.append(row)
    return result
