from copy import deepcopy
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from ml.postmatch_outcome_source_v4 import load_profile,validate_profile,fetch,chunks,recover,stage,extract,VERSION,stamp,WARSAW

PROFILE='ml/artifacts/postmatch_outcome_contracts/2026-11-07-gornik-widzew-v1.json'
NOW='2026-11-08T08:30:00Z'


def inputs():
    profile=load_profile(PROFILE);raw={};sources=[];events=[];sporting=[]
    for i,t in enumerate(profile['fixtures']):
        local=stamp(t['kickoff_at']).astimezone(WARSAW)
        home,away=('Górnik Z.','Wieczysta') if i==0 else ('Widzew','Pogoń')
        line=f'{home} 2:1 {away} {t["capacity"]//2} 2026/2027 • Ekstraklasa • {local:%d.%m.%Y %H:%M}'
        url=t['source_url'];raw[url]=('<p>'+line+'</p>').encode()
        sources.append({'version':VERSION,'contract_sha256':profile['_sha256'],'url':url,'http_status':200,
            'retrieved_at':'2026-11-08T08:20:00Z','receipt_completed_at':'2026-11-08T08:20:02Z',
            'sha256':hashlib.sha256(raw[url]).hexdigest(),'bytes':len(raw[url]),**extract(raw[url])})
        events.append({k:t[k] for k in ('id','club_slug','home_team','away_team','kickoff_at','competition')})
        sporting.append({'source_event_id':str(990000+i),'season':'2026-2027','event_date':'2026-11-07',
            'home_team':t['home_team'],'away_team':t['away_team'],'completed':True,'match_status':'FT',
            'home_score':2,'away_score':1,'fetched_at':'2026-11-08T08:00:00Z'})
    return profile,sources,raw,events,sporting


def staged(profile,sources,raw,events,sporting,existing=(),now=NOW):
    return stage(sources,raw,events,sporting,list(existing),run_id=123,verified_at=now,profile=profile)


class ForwardSourceTests(unittest.TestCase):
    def test_real_published_contract_is_bounded_and_uses_actual_verified_prior_capacities(self):
        p=load_profile(PROFILE);self.assertEqual([t['capacity'] for t in p['fixtures']],[28236,18018]);self.assertEqual(len(p['slots']),3)
        for changes in [{'production_change':True},{'slots':p['slots']*2},{'created_at':'2026-11-07T17:00:00Z'}]:
            bad={k:v for k,v in p.items() if k!='_sha256'};bad.update(changes)
            with self.assertRaises(ValueError):validate_profile(bad)
        with self.assertRaises(ValueError):load_profile('../../outside.json')

    def test_forged_capacity_source_or_url_is_rejected(self):
        p=load_profile(PROFILE)
        for changes in [{'capacity_verification_status':'unknown'},{'capacity_source_prior_id':0},{'source_url':'https://example.invalid/'}]:
            bad=deepcopy({k:v for k,v in p.items() if k!='_sha256'});bad['fixtures'][0].update(changes)
            with self.assertRaises(ValueError):validate_profile(bad)

    def test_exact_postmatch_source_result_preserves_actual_run_and_knowledge_times(self):
        values=inputs();result=staged(*values)
        self.assertEqual(len(result['rows']),2)
        self.assertEqual([r['actual_attendance'] for r in result['rows']],[14118,9009])
        for r in result['rows']:
            self.assertEqual(r['source_observed_at'],NOW);self.assertEqual(r['source_payload']['verification_run_id'],123)
            self.assertFalse(r['source_payload']['knowledge_backdated'])

    def test_before_game_missing_and_incomplete_sources_never_become_labels(self):
        values=inputs();self.assertEqual(staged(*values,now='2026-11-07T12:00:00Z')['rows'],[])
        profile,sources,raw,events,sporting=inputs();sources[0]['http_status']=503;sporting[1]['completed']=False
        result=staged(profile,sources,raw,events,sporting);self.assertEqual(result['rows'],[])
        self.assertEqual({s['status'] for s in result['statuses']},{'SOURCE_UNAVAILABLE','INDEPENDENT_COMPLETION_PENDING'})

    def test_contract_raw_bytes_canonical_clock_or_independent_result_substitution_fails(self):
        for mode in ['contract','raw','clock','result']:
            p,s,r,e,sp=inputs()
            if mode=='contract':s[0]['contract_sha256']='0'*64
            if mode=='raw':r[s[0]['url']]=b'changed'
            if mode=='clock':e[0]['kickoff_at']='2026-11-07T16:31:00Z'
            if mode=='result':sp[0]['home_score']=0
            with self.assertRaises(ValueError):staged(p,s,r,e,sp)

    def test_existing_different_or_aliased_history_is_never_overwritten(self):
        values=inputs();row=staged(*values)['rows'][0]
        self.assertEqual(len(staged(*values,existing=[row])['rows']),1)
        for changes in [{'actual_attendance':1},{'club_slug':'gornik_zabrze'}]:
            with self.assertRaises(ValueError):staged(*values,existing=[{**row,**changes}])

    def test_actual_run_attempt_contract_and_raw_check_roundtrip(self):
        p,sources,raw,_,_=inputs();checks=[]
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for i,s in enumerate(sources):
                (root/f'source-{i}.html').write_bytes(raw[s['url']])
                entries=[(f'postmatch-v4-source-{i}',s),*[(f'postmatch-v4-raw-{i}-{c["part"]}',c) for c in chunks(root,i,s)]]
                for name,value in entries:
                    cid=100+len(checks);checks.append({'id':cid,'app':{'slug':'github-actions'},'name':name,'head_sha':'a'*40,'status':'completed',
                        'details_url':f'https://github.com/NiedzielX/beyond/runs/{cid}','external_id':f'postmatch-v4:123:1:{name}',
                        'output':{'text':json.dumps({**value,'workflow_run_id':123,'workflow_run_attempt':1})}})
            self.assertEqual(recover(checks,'a'*40,123,1,p)[1],raw)
            with self.assertRaises(ValueError):recover(checks,'b'*40,123,1,p)
            with self.assertRaises(KeyError):recover(checks,'a'*40,124,1,p)
            wrong=deepcopy(p);wrong['_sha256']='0'*64
            with self.assertRaises(ValueError):recover(checks,'a'*40,123,1,wrong)

    def test_fetch_rejects_any_url_outside_declared_profile_without_network(self):
        p=load_profile(PROFILE);opener=Mock()
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):fetch('https://example.invalid/',Path(temp),0,p,opener)
            opener.open.assert_not_called()


if __name__=='__main__':unittest.main()
