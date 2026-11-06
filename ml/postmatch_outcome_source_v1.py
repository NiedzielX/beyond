"""Two fixed public pages and strict postmatch staging; no database/model calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request
from zoneinfo import ZoneInfo

from ml.current_home_history_source_audit_v1 import PublicRedirect, allowed_redirect, raw_chunks
from ml.public_attendance_source_audit_v1 import MAX_BYTES, extract
from ml.verified_attendance_source_rows_v1 import prepare_import_rows, TEAMS as TEAMS_V1

VERSION = 'postmatch-outcome-source-v1'
ROW = re.compile(r'^(?P<home>.+?) (?P<hs>\d+):(?P<as>\d+) (?P<away>.+?) '
                 r'(?P<attendance>\d[\d ]*) 2026/2027 • Ekstraklasa • '
                 r'(?P<date>\d{2}\.\d{2}\.\d{4}) (?P<time>\d{2}:\d{2})$')
SPORTING_NAMES = {'Legia Warsaw': 'Legia Warszawa', 'Zagłębie Lubin': 'KGHM Zagłębie Lubin'}
SOURCES = ('https://www.frekwencyjny.pl/kluby/motor-lublin',
           'https://www.frekwencyjny.pl/kluby/wisla-krakow')
TARGETS = (
    {'id': 5091, 'club_slug': 'motorlublin', 'home_team': 'Motor Lublin',
     'away_team': 'Wisła Płock', 'kickoff_at': '2026-11-06T17:00:00Z', 'capacity': 15243},
    {'id': 448, 'club_slug': 'wislakrakow', 'home_team': 'Wisła Kraków',
     'away_team': 'Cracovia', 'kickoff_at': '2026-11-06T19:30:00Z', 'capacity': 33130},
)
ALIASES = {'motor_lublin': 'motorlublin', 'motorlublin': 'motorlublin',
           'wisla_krakow': 'wislakrakow', 'wislakrakow': 'wislakrakow'}
WARSAW = ZoneInfo('Europe/Warsaw')


def stamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None: raise ValueError('Explicit actual source clock required')
    return result.astimezone(timezone.utc)


def fetch(url, directory, index, opener=None):
    if url not in SOURCES or SOURCES[index] != url:
        raise ValueError('Only the two fixed indexed public pages are permitted')
    result = {'version': VERSION, 'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
              'fixture_identity_verified': False, 'automatic_label_import': False}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Beyond-outcome-source/1.0', 'Accept-Encoding': 'identity'})
        with (opener or urllib.request.build_opener(PublicRedirect())).open(req, timeout=20) as response:
            if not allowed_redirect(response.url): raise ValueError('Unexpected public redirect')
            raw = response.read(MAX_BYTES+1)
            result.update(http_status=response.status, final_url=response.url, content_type=response.headers.get('Content-Type'))
        if len(raw)>MAX_BYTES or result['http_status']!=200 or 'text/html' not in (result['content_type'] or '').lower():
            raise ValueError('Bounded complete HTML required')
        with (directory/f'source-{index}.html').open('xb') as file: file.write(raw)
        result.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), **extract(raw))
    except Exception as exc:
        result.update(error_type=type(exc).__name__, http_status=getattr(exc,'code',result.get('http_status')))
    result['receipt_completed_at'] = datetime.now(timezone.utc).isoformat()
    return result


def chunks(directory, index, source):
    return [{**chunk, 'version': VERSION} for chunk in raw_chunks(directory,index,source)]


def publish(results, directory):
    if os.environ.get('GITHUB_REPOSITORY')!='NiedzielX/beyond': raise ValueError('Wrong authorized repository')
    entries=[]
    for index,result in enumerate(results):
        entries.append((f'postmatch-outcome-source-{index}',result))
        entries.extend((f'postmatch-outcome-raw-{index}-{part["part"]}',part) for part in chunks(directory,index,result))
    for name,value in entries:
        text=json.dumps(value,ensure_ascii=False)
        if len(text.encode())>60000: raise ValueError('Public check exceeds bound')
        body={'name':name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral',
              'output':{'title':'Public postmatch source retrieval', 'summary':'Raw retrieval only; no label verification or database access.', 'text':text}}
        req=urllib.request.Request('https://api.github.com/repos/NiedzielX/beyond/check-runs',data=json.dumps(body).encode(),
            headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=25) as response: saved=json.load(response)
        print(json.dumps({'check_id':saved['id'],'name':name,'labels_imported':0}),flush=True)


def recover(checks, head_sha):
    """Caller obtains checks from the successful run's exact check suite."""
    relevant=[c for c in checks if c['name'].startswith('postmatch-outcome-')]
    if len({c['name'] for c in relevant})!=len(relevant): raise ValueError('Duplicate source check identity')
    if any(c['head_sha']!=head_sha or c['status']!='completed' for c in relevant): raise ValueError('Source checks from wrong run/source')
    values={c['name']:json.loads(c['output']['text']) for c in relevant};sources=[];raw={}
    for index,url in enumerate(SOURCES):
        source=values[f'postmatch-outcome-source-{index}']
        if source.get('version')!=VERSION or source['url']!=url: raise ValueError('Wrong source receipt')
        sources.append(source)
        if source.get('error_type') or source.get('http_status')!=200: continue
        parts=[v for k,v in values.items() if k.startswith(f'postmatch-outcome-raw-{index}-')]
        if not parts or len(parts)>8 or {p['parts'] for p in parts}!={len(parts)} or {p['part'] for p in parts}!=set(range(len(parts))):
            raise ValueError('Incomplete bounded raw-source transport')
        if any(p['version']!=VERSION or p['source_index']!=index or p['source_sha256']!=source['sha256'] or p['encoding']!='zlib+base64' for p in parts):
            raise ValueError('Substituted raw source identity')
        import base64,zlib
        packed=base64.b64decode(''.join(p['payload'] for p in sorted(parts,key=lambda p:p['part'])),validate=True)
        decoder=zlib.decompressobj();data=decoder.decompress(packed,MAX_BYTES+1)
        if len(data)>MAX_BYTES or not decoder.eof or decoder.unused_data or hashlib.sha256(data).hexdigest()!=source['sha256']:
            raise ValueError('Raw public source recovery differs')
        if len(data)!=source['bytes'] or any(p['raw_bytes']!=len(data) for p in parts): raise ValueError('Raw byte count changed')
        raw[url]=data
    return sources,raw


def stage(sources, raw, events, sporting, existing, *, run_id, verified_at):
    now=stamp(verified_at)
    if type(run_id)is not int or run_id<=0 or len(sources)!=2 or [s['url'] for s in sources]!=list(SOURCES):
        raise ValueError('Exact two-source actual run identity required')
    staged=[];statuses=[]
    for target,source in zip(TARGETS,sources):
        event=[e for e in events if e['id']==target['id']]
        if len(event)!=1 or any(event[0][k]!=target[k] for k in ('club_slug','home_team','away_team')) or stamp(event[0]['kickoff_at'])!=stamp(target['kickoff_at']) or event[0]['competition']!='Ekstraklasa':
            raise ValueError('Fixed canonical fixture changed; manual review required')
        if now<stamp(target['kickoff_at'])+timedelta(hours=3):
            statuses.append({'ticket_event_id':target['id'],'status':'NOT_POSTMATCH_3H'});continue
        if source.get('http_status')!=200 or source.get('error_type'):
            statuses.append({'ticket_event_id':target['id'],'status':'SOURCE_UNAVAILABLE'});continue
        data=raw[source['url']]
        if (source.get('version')!=VERSION or source.get('text_truncated') is not False
                or hashlib.sha256(data).hexdigest()!=source['sha256'] or extract(data)['text']!=source['text']
                or len(data)>MAX_BYTES or source['bytes']!=len(data)
                or not stamp(target['kickoff_at'])+timedelta(hours=3)<=stamp(source['retrieved_at'])<=stamp(source['receipt_completed_at'])<=now
                or now-stamp(source['retrieved_at'])>timedelta(hours=2)):
            raise ValueError('Source is incomplete, stale, pregame or not yet received')
        rows=[]
        for line in source['text'].splitlines():
            match=ROW.fullmatch(line)
            if match is None: continue
            v=match.groupdict();home=TEAMS_V1.get(v['home']);away=TEAMS_V1.get(v['away'])
            local=datetime.strptime(v['date']+' '+v['time'],'%d.%m.%Y %H:%M').replace(tzinfo=WARSAW)
            if not home or home[1]!=target['home_team'] or local.date()!=stamp(target['kickoff_at']).astimezone(WARSAW).date(): continue
            if not away or away[1]!=target['away_team'] or local.astimezone(timezone.utc)!=stamp(target['kickoff_at']):
                raise ValueError('Target source opponent or canonical clock conflicts')
            actual=int(v['attendance'].replace(' ',''))
            if not 0<actual<=target['capacity']: raise ValueError('Positive in-capacity attendance required')
            matches=[s for s in sporting if s['season']=='2026-2027' and s['event_date']==local.date().isoformat()
                     and SPORTING_NAMES.get(s['home_team'],s['home_team'])==target['home_team']
                     and SPORTING_NAMES.get(s['away_team'],s['away_team'])==target['away_team']]
            if not matches or any(s.get('completed') is not True for s in matches):
                statuses.append({'ticket_event_id':target['id'],'status':'INDEPENDENT_COMPLETION_PENDING'});continue
            if (len(matches)!=1 or matches[0]['match_status']!='FT'
                    or any(type(matches[0][k])is not int for k in ('home_score','away_score'))
                    or (matches[0]['home_score'],matches[0]['away_score'])!=(int(v['hs']),int(v['as']))
                    or not stamp(target['kickoff_at'])<stamp(matches[0]['fetched_at'])<=now):
                raise ValueError('Independent completed sporting result conflicts')
            rows.append({'club_slug':target['club_slug'],'home_team':target['home_team'],'away_team':target['away_team'],
                'opponent_key':away[2],'kickoff_at':stamp(target['kickoff_at']).isoformat(),'actual_attendance':actual,
                'season':'2026/2027','competition':'Ekstraklasa','competition_key':'ekstraklasa',
                'source_name':'frekwencyjny.pl — verified fixture record','source_url':source['url'],
                'source_observed_at':verified_at,'verification_reason':'Exact canonical home/away/date/time and independently completed sporting result',
                'source_payload':{'source_sha256':source['sha256'],'source_line':line,'retrieved_at':source['retrieved_at'],
                    'verification_run_id':run_id,'historical_publication_time_verified':False,'knowledge_backdated':False,
                    'sporting_source_event_id':matches[0]['source_event_id'],'independent_kickoff_clock_verified':False}})
        if len(rows)>1: raise ValueError('Ambiguous duplicate target source rows')
        if not rows:
            if not any(s['ticket_event_id']==target['id'] for s in statuses):statuses.append({'ticket_event_id':target['id'],'status':'SOURCE_TARGET_NOT_FOUND'})
            continue
        row=rows[0]
        for old in existing:
            if ALIASES.get(old['club_slug'],old['club_slug'])==target['club_slug'] and stamp(old['kickoff_at']).astimezone(WARSAW).date()==stamp(target['kickoff_at']).astimezone(WARSAW).date():
                if old['club_slug']!=target['club_slug'] or stamp(old['kickoff_at'])!=stamp(target['kickoff_at']) or old['actual_attendance']!=row['actual_attendance']:
                    raise ValueError('Existing canonical history/attendance conflicts')
        staged.append(row);statuses.append({'ticket_event_id':target['id'],'status':'EXACT_SOURCE_AND_RESULT_VERIFIED'})
    return {'version':VERSION,'rows':prepare_import_rows(staged,existing,verified_at),'verified_rows':staged,'statuses':statuses,
            'production_change':False,'live_adjustment':0}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--publish-checks',action='store_true');a=p.parse_args()
    a.output_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
    results=[fetch(url,a.output_dir,i) for i,url in enumerate(SOURCES)]
    (a.output_dir/'manifest.json').write_text(json.dumps({'version':VERSION,'sources':results,'labels_imported':0,'production_change':False},indent=2)+'\n')
    if a.publish_checks:publish(results,a.output_dir)
    print(json.dumps({'retrievals_attempted':2,'labels_imported':0,'production_change':False}))


if __name__=='__main__':main()
