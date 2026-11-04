"""Public official-source discovery for blocked445; never imports a label."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import unicodedata
import urllib.parse
import urllib.request

from ml.public_attendance_source_audit_v1 import extract, MAX_BYTES

VERSION='blocked-outcome-445-official-source-audit-v1'
SOURCES=('https://www.zaglebie.com/aktualnosci', 'https://www.zaglebie.com/mecze', 'https://www.korona-kielce.pl/')
HOSTS={'www.zaglebie.com','zaglebie.com','www.korona-kielce.pl','korona-kielce.pl'}


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value.lower()) if not unicodedata.combining(c)).replace('ł','l')


def prioritized(links):
    def priority(link):
        value=normalized(link['url']+' '+link['text'])
        match='koron' in value and 'zagle' in value
        article='/aktualnosci/' in value
        media=any(word in value for word in ['foto','galeri','konferenc','zapowiedz','przed meczem'])
        return (not (match and article and not media),not match,not article)
    return sorted(links,key=priority)


class Links(HTMLParser):
    def __init__(self,base):super().__init__();self.base=base;self.links=[];self.href=None;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.href=dict(attrs).get('href');self.parts=[]
    def handle_data(self,text):
        if self.href:self.parts.append(text)
    def handle_endtag(self,tag):
        if tag=='a' and self.href:
            url=urllib.parse.urljoin(self.base,self.href).split('#')[0];parsed=urllib.parse.urlparse(url)
            text=' '.join(' '.join(self.parts).split());match=normalized(url+' '+text)
            if (parsed.scheme=='https' and parsed.hostname in HOSTS and not parsed.username and not parsed.password
                    and len(parsed.path)>12 and ('zagle' in match or 'koron' in match)
                    and not any(x in parsed.path for x in ['/tag/','/kategoria/','/kontakt','/sklep','/tickets'])):
                self.links.append({'url':url,'text':text[:250]})
            self.href=None;self.parts=[]


def fetch(url,folder,index):
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme!='https' or parsed.hostname not in HOSTS or parsed.username or parsed.password:
        raise ValueError('Only declared official hosts are allowed')
    result={'version':VERSION,'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),
            'fixture_identity_verified':False,'automatic_label_import':False}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Beyond-public-source-verification/1.0','Accept-Encoding':'identity'})
        with urllib.request.urlopen(req,timeout=20) as response:
            final=urllib.parse.urlparse(response.url)
            if final.scheme!='https' or final.hostname not in HOSTS or final.username or final.password:
                raise ValueError('Official source redirected outside declared hosts')
            raw=response.read(MAX_BYTES+1);result.update(http_status=response.status,final_url=response.url)
        if len(raw)>MAX_BYTES:raise ValueError('Official source exceeds size bound')
        (folder/f'source-{index}.html').write_bytes(raw);links=Links(result['final_url']);links.feed(raw.decode('utf-8',errors='replace'))
        text=extract(raw);text['text_truncated']=text['text_truncated'] or len(text['text'])>18000
        text['text']=text['text'][:18000]
        result.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),links=prioritized(links.links)[:24],**text)
    except Exception as exc:result.update(error_type=type(exc).__name__,http_status=getattr(exc,'code',result.get('http_status')))
    return result


def publish(results):
    if os.environ.get('GITHUB_REPOSITORY')!='NiedzielX/beyond':raise ValueError('Authorized repository required')
    for i,value in enumerate(results):
        text=json.dumps(value,ensure_ascii=False)
        if len(text.encode())>60000:raise ValueError('Bounded official source evidence exceeded')
        body={'name':f'blocked-outcome-445-source-{i}','head_sha':os.environ['GITHUB_SHA'],
              'status':'completed','conclusion':'neutral','output':{'title':'Official public source retrieval only',
              'summary':'No verified fixture, label import, database or model operation.','text':text}}
        request=urllib.request.Request('https://api.github.com/repos/NiedzielX/beyond/check-runs',data=json.dumps(body).encode(),
            headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json',
                     'Content-Type':'application/json','User-Agent':'Beyond-source-audit'},method='POST')
        with urllib.request.urlopen(request,timeout=25) as response:saved=json.load(response)
        print(json.dumps({'check_id':saved['id'],'source_index':i,'http_status':value.get('http_status'),'labels_imported':0}),flush=True)


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    a.output_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
    results=[fetch(url,a.output_dir,i) for i,url in enumerate(SOURCES)]
    candidates=[]
    for result in results:
        for link in result.get('links',[]):
            combined=normalized(link['text']+' '+link['url'])
            if 'koron' in combined and 'zagle' in combined and link['url'] not in SOURCES and link['url'] not in candidates:
                candidates.append(link['url'])
    for url in candidates[:2]:results.append(fetch(url,a.output_dir,len(results)))
    (a.output_dir/'manifest.json').write_text(json.dumps({'version':VERSION,'sources':results,'labels_imported':0},indent=2))
    publish(results)
    print(json.dumps({'retrievals':len(results),'labels_imported':0,'production_change':False}))


if __name__=='__main__':main()
