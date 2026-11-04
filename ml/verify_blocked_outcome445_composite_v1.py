"""Narrow two-source verification; official schedule plus primary attendance.

Does not infer the cause of the ten-minute source discrepancy or mutate DB.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import re
from zoneinfo import ZoneInfo

from ml.verified_attendance_source_rows_v1 import parse_source

OFFICIAL='https://www.zaglebie.com/Aktualnosci/Pierwszy-zespol/trzy-punkty-na-rozpoczecie-tygodnia_n20423'
RULE='outcome445-official-schedule-primary-attendance-composite-v1'


def verify(primary, official, event, events, verified_at):
    known=datetime.fromisoformat(verified_at)
    if known.tzinfo is None:raise ValueError('Verification requires timezone')
    if (event.get('id')!=445 or event.get('club_slug')!='zaglebie_lubin'
            or event.get('home_team')!='KGHM Zagłębie Lubin' or event.get('away_team')!='Korona Kielce'
            or event.get('competition')!='Ekstraklasa'):
        raise ValueError('This reviewed identity rule is limited to event445')
    kickoff=datetime.fromisoformat(event['kickoff_at'])
    if kickoff.tzinfo is None:raise ValueError('Canonical kickoff requires timezone')
    local=kickoff.astimezone(ZoneInfo('Europe/Warsaw'))
    if local.isoformat()!='2026-11-02T18:00:00+01:00':raise ValueError('Official canonical schedule changed')
    if (official.get('url')!=OFFICIAL or official.get('final_url')!=OFFICIAL
            or official.get('http_status')!=200 or official.get('error_type') or official.get('text_truncated')):
        raise ValueError('Complete exact official report receipt required')
    for source in [primary,official]:
        if not re.fullmatch('[0-9a-f]{64}',source.get('sha256','')):raise ValueError('Source content hash missing')
        retrieved=datetime.fromisoformat(source['retrieved_at'])
        if retrieved.tzinfo is None or known<retrieved:raise ValueError('Cannot backdate composite verification')
    flat=' '.join(official['text'].split())
    exact_card='Zagłębie Lubin Ekstraklasa / 13 02 lis 2026 godz. 18:00 vs 1 : 0 1 : 0 Podsumowanie Korona Kielce'
    if exact_card not in flat or 'KGHM Zagłębie Lubin 1-0 Korona Kielce' not in flat:
        raise ValueError('Exact official fixture schedule and final result not proven')
    canonical=[e for e in events if e.get('club_slug')==event['club_slug'] and e.get('away_team')==event['away_team']
        and e.get('home_team')==event['home_team'] and e.get('competition')==event['competition']
        and datetime.fromisoformat(e['kickoff_at']).astimezone(ZoneInfo('Europe/Warsaw')).date()==local.date()]
    if len(canonical)!=1 or canonical[0]['id']!=445:raise ValueError('Ambiguous canonical fixture identity')
    rows=[r for r in parse_source(primary) if r['club_slug']==event['club_slug'] and r['away_team']==event['away_team']
          and r['home_team']==event['home_team'] and datetime.fromisoformat(r['kickoff_at']).astimezone(ZoneInfo('Europe/Warsaw')).date()==local.date()]
    if len(rows)!=1 or not re.search(r'Zagłębie L\. 1:0 Korona ',rows[0]['source_payload']['source_line']):
        raise ValueError('Primary attendance fixture/date/result not unique or supported')
    row=deepcopy(rows[0]);reported=row['kickoff_at'];row['kickoff_at']=kickoff.isoformat()
    row['source_name']='frekwencyjny.pl (attendance); KGHM Zagłębie Lubin (official fixture schedule)'
    row['source_observed_at']=verified_at
    row['verification_reason']='Exact independent official schedule/result and unique canonical fixture; attendance from matching primary fixture.'
    row['source_payload'].update({'verification_rule':RULE,'verified_at':verified_at,'official_url':OFFICIAL,
        'official_source_sha256':official['sha256'],'official_retrieved_at':official['retrieved_at'],
        'official_scheduled_kickoff_at':kickoff.isoformat(),'primary_reported_kickoff_at':reported,
        'official_fixture_excerpt':exact_card,'canonical_event_id':445,'official_attendance_corroborated':False,
        'cause_of_time_discrepancy_verified':False,'canonical_schedule_changed':False,'knowledge_backdated':False})
    return row
