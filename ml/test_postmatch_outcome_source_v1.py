import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from ml.postmatch_outcome_source_v1 import SOURCES,TARGETS,VERSION,fetch,chunks,recover,stage
from ml.public_attendance_source_audit_v1 import extract,MAX_BYTES

NOW='2026-11-06T23:30:00Z'


def inputs():
    texts=['Motor 2:1 Wisła Pł. 12 000 2026/2027 • Ekstraklasa • 06.11.2026 18:00',
           'Wisła K. 1:0 Cracovia 25 000 2026/2027 • Ekstraklasa • 06.11.2026 20:30']
    raw={url:('<p>'+text+'</p>').encode() for url,text in zip(SOURCES,texts)}
    sources=[{'version':VERSION,'url':url,'http_status':200,'retrieved_at':'2026-11-06T23:20:00Z',
              'receipt_completed_at':'2026-11-06T23:20:10Z','sha256':hashlib.sha256(raw[url]).hexdigest(),
              'bytes':len(raw[url]),**extract(raw[url])} for url in SOURCES]
    events=[{k:v for k,v in t.items() if k!='capacity'}|{'competition':'Ekstraklasa'} for t in TARGETS]
    sporting=[{'source_event_id':str(i+1),'season':'2026-2027','event_date':'2026-11-06','home_team':t['home_team'],
               'away_team':t['away_team'],'completed':True,'match_status':'FT','home_score':2 if i==0 else 1,
               'away_score':1 if i==0 else 0,'fetched_at':'2026-11-06T23:00:00Z'} for i,t in enumerate(TARGETS)]
    return sources,raw,events,sporting


def staged(sources=None,raw=None,events=None,sporting=None,existing=(),now=NOW):
    values=inputs()
    return stage(sources or values[0],raw or values[1],events or values[2],sporting or values[3],list(existing),run_id=123,verified_at=now)


class PostmatchStagingTests(unittest.TestCase):
    def test_exact_verified_targets_keep_actual_verification_and_source_provenance(self):
        result=staged();self.assertEqual(len(result['rows']),2)
        self.assertEqual([r['actual_attendance'] for r in result['rows']],[12000,25000])
        for row in result['rows']:
            self.assertEqual(row['source_observed_at'],NOW);self.assertEqual(row['source_payload']['verification_run_id'],123)
            self.assertFalse(row['source_payload']['knowledge_backdated'])
            self.assertEqual(row['attendance_definition'],'reported_match_attendance')

    def test_pregame_never_imports_a_label_even_with_source_fixture_text(self):
        result=staged(now='2026-11-06T13:00:00Z');self.assertEqual(result['rows'],[])
        self.assertTrue(all(s['status']=='NOT_POSTMATCH_3H' for s in result['statuses']))

    def test_second_game_waits_for_its_own_three_hour_boundary(self):
        sources,raw,events,sporting=inputs()
        sources[0].update(retrieved_at='2026-11-06T20:20:00Z',receipt_completed_at='2026-11-06T20:20:10Z')
        sporting[0]['fetched_at']='2026-11-06T20:00:00Z'
        result=staged(sources,raw,events,sporting,now='2026-11-06T20:30:00Z')
        self.assertEqual(len(result['rows']),1);self.assertEqual(result['statuses'][1]['status'],'NOT_POSTMATCH_3H')

    def test_missing_source_and_unfinished_sporting_remain_unknown(self):
        sources,raw,events,sporting=inputs();sources[0]['http_status']=503;sporting[1]['completed']=False
        result=staged(sources,raw,events,sporting);self.assertEqual(result['rows'],[])
        self.assertEqual({s['status'] for s in result['statuses']},{'SOURCE_UNAVAILABLE','INDEPENDENT_COMPLETION_PENDING'})

    def test_changed_raw_or_extraction_or_future_clock_is_rejected(self):
        for key,value in [('sha256','0'*64),('text','changed'),('text_truncated',True),('receipt_completed_at','2026-11-07T00:00:00Z'),('retrieved_at','2026-11-06T18:00:00Z')]:
            sources,raw,events,sporting=inputs();sources[0][key]=value
            with self.assertRaises(ValueError):staged(sources,raw,events,sporting)

    def test_exact_canonical_fixture_reschedule_or_competition_conflict_fails(self):
        for key,value in [('kickoff_at','2026-11-06T18:00:00Z'),('away_team','Legia Warszawa'),('competition','Cup')]:
            sources,raw,events,sporting=inputs();events[0][key]=value
            with self.assertRaises(ValueError):staged(sources,raw,events,sporting)

    def test_independent_score_or_fetch_time_conflict_fails(self):
        for key,value in [('home_score',0),('match_status','NS'),('fetched_at','2026-11-06T12:00:00Z')]:
            sources,raw,events,sporting=inputs();sporting[0][key]=value
            with self.assertRaises(ValueError):staged(sources,raw,events,sporting)

    def test_duplicate_or_conflicting_home_matchday_cannot_be_appended(self):
        row=staged()['rows'][0]
        for changes in [{'club_slug':'motor_lublin'},{'actual_attendance':1},{'kickoff_at':'2026-11-06T18:00:00Z'}]:
            with self.assertRaises(ValueError):staged(existing=[{**row,**changes}])
        self.assertEqual(len(staged(existing=[row])['rows']),1)

    def test_duplicate_completed_sporting_identity_is_not_arbitrarily_chosen(self):
        sources,raw,events,sporting=inputs();sporting.append(deepcopy(sporting[0]))
        with self.assertRaises(ValueError):staged(sources,raw,events,sporting)


class PostmatchRetrievalTests(unittest.TestCase):
    def response(self,raw,url):
        response=Mock(status=200,url=url,headers={'Content-Type':'text/html'});response.read.return_value=raw
        response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        opener=Mock();opener.open.return_value=response;return opener

    def test_raw_roundtrip_has_exact_hash_no_verification_or_import(self):
        sources,raw,_,_=inputs();checks=[]
        with tempfile.TemporaryDirectory() as temp:
            for i,url in enumerate(SOURCES):
                result=fetch(url,Path(temp),i,self.response(raw[url],url))
                self.assertFalse(result['fixture_identity_verified']);self.assertFalse(result['automatic_label_import'])
                entries=[(f'postmatch-outcome-source-{i}',result)]
                entries += [(f'postmatch-outcome-raw-{i}-{c["part"]}',c) for c in chunks(Path(temp),i,result)]
                checks += [{'name':name,'head_sha':'a'*40,'status':'completed','output':{'text':json.dumps(value)}} for name,value in entries]
            _,restored=recover(checks,'a'*40);self.assertEqual(restored,raw)
            with self.assertRaises(ValueError):recover(checks,'b'*40)
            with self.assertRaises(ValueError):recover(checks+checks[:1],'a'*40)
            with self.assertRaises(ValueError):recover(checks[:-1],'a'*40)

    def test_unlisted_page_index_or_redirect_never_yields_source(self):
        with tempfile.TemporaryDirectory() as temp:
            opener=Mock()
            with self.assertRaises(ValueError):fetch('https://example.invalid',Path(temp),0,opener)
            opener.open.assert_not_called()
            result=fetch(SOURCES[0],Path(temp),0,self.response(b'html','https://example.invalid'))
            self.assertIn('error_type',result);self.assertNotIn('sha256',result)

    def test_oversized_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            result=fetch(SOURCES[0],Path(temp),0,self.response(b'x'*(MAX_BYTES+1),SOURCES[0]))
            self.assertIn('error_type',result);self.assertEqual(list(Path(temp).iterdir()),[])


if __name__=='__main__':unittest.main()
