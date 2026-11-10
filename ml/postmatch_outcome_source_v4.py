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

VERSION = 'postmatch-outcome-source-v4'
ROW = re.compile(r'^(?P<home>.+?) (?P<hs>\d+):(?P<as>\d+) (?P<away>.+?) '
                 r'(?P<attendance>\d[\d ]*) 2026/2027 • Ekstraklasa • '
                 r'(?P<date>\d{2}\.\d{2}\.\d{4}) (?P<time>\d{2}:\d{2})$')
SPORTING_NAMES = {'Legia Warsaw': 'Legia Warszawa', 'Zagłębie Lubin': 'KGHM Zagłębie Lubin'}
ROOT = Path(__file__).resolve().parents[1]
URLS = {'motorlublin':'https://www.frekwencyjny.pl/kluby/motor-lublin',
        'wislakrakow':'https://www.frekwencyjny.pl/kluby/wisla-krakow',
        'gornikzabrze':'https://www.frekwencyjny.pl/kluby/gornik-zabrze',
        'widzewlodz':'https://www.frekwencyjny.pl/kluby/widzew-lodz'}


def validate_profile(value):
    profile = json.loads(json.dumps(value,allow_nan=False))
    if (profile.get('version')!='postmatch-outcome-contract-v4' or profile.get('production_change')is not False
            or type(profile.get('live_adjustment'))is not int or profile['live_adjustment']!=0
            or not re.fullmatch(r'\d{4}-\d{2}-\d{2}-[a-z0-9-]+',profile.get('id',''))):
        raise ValueError('Invalid frozen forward outcome contract')
    fixtures=profile['fixtures'];slots=[stamp(s) for s in profile['slots']];created=stamp(profile['created_at']);until=stamp(profile['until'])
    if (not 1<=len(fixtures)<=2 or len({t['id'] for t in fixtures})!=len(fixtures)
            or len({t['source_url'] for t in fixtures})!=len(fixtures)
            or len(slots)!=3 or slots!=sorted(set(slots)) or slots[-1]>=until
            or until-created>timedelta(hours=72) or created>=min(stamp(t['kickoff_at']) for t in fixtures)
            or slots[0]<min(stamp(t['kickoff_at']) for t in fixtures)+timedelta(hours=3)
            or slots[-1]<max(stamp(t['kickoff_at']) for t in fixtures)+timedelta(hours=3)):
        raise ValueError('Bounded unique fixtures and genuinely future postmatch opportunities required')
    for t in fixtures:
        if (type(t['id'])is not int or t['id']<=0 or type(t['capacity'])is not int or not 0<t['capacity']<=500000
                or t.get('capacity_verification_status')!='verified' or type(t.get('capacity_source_prior_id'))is not int or t['capacity_source_prior_id']<=0
                or t['club_slug'] not in URLS or t['source_url']!=URLS.get(t['club_slug']) or t['competition']!='Ekstraklasa'
                or not t['home_team'] or not t['away_team'] or t['home_team']==t['away_team']):
            raise ValueError('Registered fixture and verified actual prior capacity required')
        if profile['club_aliases'].get(t['club_slug'])!=t['club_slug']:
            raise ValueError('Explicit canonical home alias required')
    profile['_sha256']=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    return profile


def load_profile(path):
    path=Path(path)
    relative=str(path) if not path.is_absolute() else str(path.resolve().relative_to(ROOT))
    if not re.fullmatch(r'ml/artifacts/postmatch_outcome_contracts/\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.json',relative):
        raise ValueError('Only published outcome contract paths are allowed')
    actual=ROOT/relative
    if not actual.resolve().is_relative_to(ROOT) or actual.is_symlink() or len(actual.read_bytes())>65536:raise ValueError('Bounded immutable profile file required')
    return validate_profile(json.loads(actual.read_text()))


WARSAW = ZoneInfo('Europe/Warsaw')


def stamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None: raise ValueError('Explicit actual source clock required')
    return result.astimezone(timezone.utc)


def fetch(url, directory, index, profile, opener=None):
    SOURCES=tuple(t['source_url'] for t in profile['fixtures'])
    if url not in SOURCES or SOURCES[index] != url:
        raise ValueError('Only the two fixed indexed public pages are permitted')
    result = {'version': VERSION, 'contract_sha256':profile['_sha256'], 'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
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
    return [{**chunk, 'version': VERSION, 'contract_sha256':source['contract_sha256']} for chunk in raw_chunks(directory,index,source)]


def publish(results, directory):
    if os.environ.get('GITHUB_REPOSITORY')!='NiedzielX/beyond': raise ValueError('Wrong authorized repository')
    entries=[]
    for index,result in enumerate(results):
        entries.append((f'postmatch-v4-source-{index}',result))
        entries.extend((f'postmatch-v4-raw-{index}-{part["part"]}',part) for part in chunks(directory,index,result))
    for name,value in entries:
        run_id=int(os.environ['GITHUB_RUN_ID']);attempt=int(os.environ['GITHUB_RUN_ATTEMPT'])
        value={**value,'workflow_run_id':run_id,'workflow_run_attempt':attempt}
        text=json.dumps(value,ensure_ascii=False)
        if len(text.encode())>60000: raise ValueError('Public check exceeds bound')
        body={'name':name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral',
              'external_id':f'postmatch-v4:{run_id}:{attempt}:{name}',
              'details_url':f'https://github.com/NiedzielX/beyond/actions/runs/{run_id}',
              'output':{'title':'Public postmatch source retrieval', 'summary':'Raw retrieval only; no label verification or database access.', 'text':text}}
        req=urllib.request.Request('https://api.github.com/repos/NiedzielX/beyond/check-runs',data=json.dumps(body).encode(),
            headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=25) as response: saved=json.load(response)
        print(json.dumps({'check_id':saved['id'],'name':name,'labels_imported':0}),flush=True)


def recover(checks, head_sha, run_id, run_attempt, profile):
    SOURCES=tuple(t['source_url'] for t in profile['fixtures'])
    """Custom checks can attach to another suite: bind actual run/attempt explicitly."""
    relevant=[]
    for check in checks:
        if not check['name'].startswith('postmatch-v4-'):continue
        value=json.loads(check['output']['text'])
        if value.get('workflow_run_id')!=run_id or value.get('workflow_run_attempt')!=run_attempt:continue
        # The GitHub Actions app normalizes details_url to its own check-run URL.
        # Run identity therefore comes from the explicit external/payload fields.
        links={f'https://github.com/NiedzielX/beyond/actions/runs/{run_id}'}
        if type(check.get('id'))is int:links.add(f'https://github.com/NiedzielX/beyond/runs/{check["id"]}')
        if (check.get('details_url') not in links or check.get('app',{}).get('slug')!='github-actions'
                or check.get('external_id')!=f'postmatch-v4:{run_id}:{run_attempt}:{check["name"]}'):
            raise ValueError('Custom check run/attempt linkage differs')
        relevant.append(check)
    if len({c['name'] for c in relevant})!=len(relevant): raise ValueError('Duplicate source check identity')
    if any(c['head_sha']!=head_sha or c['status']!='completed' for c in relevant): raise ValueError('Source checks from wrong run/source')
    values={c['name']:json.loads(c['output']['text']) for c in relevant};sources=[];raw={}
    for index,url in enumerate(SOURCES):
        source=values[f'postmatch-v4-source-{index}']
        if source.get('version')!=VERSION or source['url']!=url or source.get('contract_sha256')!=profile['_sha256']: raise ValueError('Wrong source receipt')
        sources.append(source)
        if source.get('error_type') or source.get('http_status')!=200: continue
        parts=[v for k,v in values.items() if k.startswith(f'postmatch-v4-raw-{index}-')]
        if not parts or len(parts)>8 or {p['parts'] for p in parts}!={len(parts)} or {p['part'] for p in parts}!=set(range(len(parts))):
            raise ValueError('Incomplete bounded raw-source transport')
        if any(p['version']!=VERSION or p.get('contract_sha256')!=profile['_sha256'] or p['source_index']!=index or p['source_sha256']!=source['sha256'] or p['encoding']!='zlib+base64' for p in parts):
            raise ValueError('Substituted raw source identity')
        import base64,zlib
        packed=base64.b64decode(''.join(p['payload'] for p in sorted(parts,key=lambda p:p['part'])),validate=True)
        decoder=zlib.decompressobj();data=decoder.decompress(packed,MAX_BYTES+1)
        if len(data)>MAX_BYTES or not decoder.eof or decoder.unused_data or hashlib.sha256(data).hexdigest()!=source['sha256']:
            raise ValueError('Raw public source recovery differs')
        if len(data)!=source['bytes'] or any(p['raw_bytes']!=len(data) for p in parts): raise ValueError('Raw byte count changed')
        raw[url]=data
    return sources,raw


def stage(sources, raw, events, sporting, existing, *, run_id, verified_at, profile):
    TARGETS=profile['fixtures'];SOURCES=tuple(t['source_url'] for t in TARGETS);ALIASES=profile['club_aliases']
    now=stamp(verified_at)
    if type(run_id)is not int or run_id<=0 or len(sources)!=len(SOURCES) or [s['url'] for s in sources]!=list(SOURCES):
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
        if (source.get('version')!=VERSION or source.get('contract_sha256')!=profile['_sha256'] or source.get('text_truncated') is not False
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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--publish-checks',action='store_true');a=p.parse_args()
    profile=load_profile(a.contract);a.output_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
    results=[fetch(t['source_url'],a.output_dir,i,profile) for i,t in enumerate(profile['fixtures'])]
    (a.output_dir/'manifest.json').write_text(json.dumps({'version':VERSION,'contract_id':profile['id'],
        'contract_sha256':profile['_sha256'],'sources':results,'labels_imported':0,'production_change':False},indent=2)+'\n')
    if a.publish_checks:publish(results,a.output_dir)
    print(json.dumps({'retrievals_attempted':len(results),'contract_id':profile['id'],'labels_imported':0,'production_change':False}))


if __name__=='__main__':main()
