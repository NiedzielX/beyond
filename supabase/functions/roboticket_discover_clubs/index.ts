const DISCOVERY_KEY = 'bt-discovery-v1-Q8m2L5x7R4p9V3k6';
const VERSION = 'roboticket-discovery-v6';

function unique<T>(arr:T[]):T[]{ return Array.from(new Set(arr)); }
function clean(value:string|null|undefined):string {
  return String(value||'')
    .replace(/<[^>]+>/g,' ')
    .replace(/&nbsp;/gi,' ')
    .replace(/&amp;/gi,'&')
    .replace(/&#243;/g,'ó')
    .replace(/&#322;/g,'ł')
    .replace(/&#347;/g,'ś')
    .replace(/&#379;/g,'Ż')
    .replace(/&#380;/g,'ż')
    .replace(/\s+/g,' ')
    .trim();
}
function attr(tag:string,name:string):string|null {
  const m=tag.match(new RegExp(`${name}\\s*=\\s*["']([^"']*)["']`,'i'));
  return m?clean(m[1]):null;
}
function normalized(value:string):string {
  return clean(value).toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/ł/g,'l');
}

async function db(path:string, options:any={}){
  const supabaseUrl=Deno.env.get('SUPABASE_URL');
  const serviceKey=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if(!supabaseUrl||!serviceKey) throw new Error('Missing Supabase service environment');
  const headers:any={
    apikey:serviceKey,
    Authorization:`Bearer ${serviceKey}`,
    'Content-Type':'application/json',
    Prefer:'return=representation',
    ...(options.headers||{})
  };
  const res=await fetch(`${supabaseUrl}/rest/v1/${path}`,{...options,headers});
  const text=await res.text();
  if(!res.ok) throw new Error(`DB ${path} ${res.status}: ${text.slice(0,1200)}`);
  return text?JSON.parse(text):null;
}
async function rpc(name:string,body:any={}){
  return await db(`rpc/${name}`,{method:'POST',body:JSON.stringify(body)});
}

function parseSameElementCandidates(html:string,source:string){
  const out:any[]=[];
  const tags=[...html.matchAll(/<a\b[^>]*>[\s\S]*?<\/a>/gi)].map(m=>m[0]);
  for(const tag of tags){
    const href=attr(tag,'href')||'';
    const onclick=attr(tag,'onclick')||'';
    const combined=`${href} ${onclick}`;
    const eventId=combined.match(/eventId=(\d+)/i)?.[1] || combined.match(/eventReservationSelector\((\d+)/i)?.[1];
    if(!eventId) continue;
    const aria=attr(tag,'aria-label');
    const title=attr(tag,'title');
    const text=clean(tag.replace(/^<a\b[^>]*>/i,'').replace(/<\/a>$/i,''));
    const label=[aria,title,text].find(v=>v && v.length>=4) || null;
    out.push({eventId,label,source,href:href||null,ariaLabel:aria,title,text});
  }
  // Some RoboTicket layouts use onclick elements instead of anchors.
  for(const m of html.matchAll(/<(?:button|div|span)\b[^>]*onclick\s*=\s*["'][^"']*eventReservationSelector\(\d+[^"']*["'][^>]*>[\s\S]*?<\/(?:button|div|span)>/gi)){
    const tag=m[0];
    const onclick=attr(tag,'onclick')||'';
    const eventId=onclick.match(/eventReservationSelector\((\d+)/i)?.[1];
    if(!eventId) continue;
    const aria=attr(tag,'aria-label');
    const title=attr(tag,'title');
    const text=clean(tag.replace(/^<[^>]+>/,'').replace(/<\/[^>]+>$/,''));
    const label=[aria,title,text].find(v=>v && v.length>=4) || null;
    out.push({eventId,label,source,href:null,ariaLabel:aria,title,text});
  }
  return out;
}

const NON_MATCH_TOKENS=[
  'parking','vip:','premium:','voucher','eskorta','subskrypc','karnet','gift card','loza','loża','hospitality'
];
function obviousNonMatch(text:string):boolean {
  const n=normalized(text);
  return NON_MATCH_TOKENS.some(t=>n.includes(normalized(t)));
}
function matchLike(text:string):boolean {
  const n=clean(text);
  if(!n || obviousNonMatch(n)) return false;
  return /\s[-–]\s|\svs\s|\sv\s/i.test(n) || /kup bilet na wydarzenie/i.test(n);
}

function extractDirectIdentity(html:string){
  const title=clean(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]||'');
  const h1=clean(html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)?.[1]||'');
  return {title:title||null,h1:h1||null,identity:[h1,title].find(v=>v && !/^roboticket$/i.test(v))||null};
}
function extractKickoff(html:string):string|null {
  // Conservative semantic-key extraction only. Generic dates on a ticket page
  // may be sale windows and must never be treated as kickoff automatically.
  const patterns=[
    /(?:eventDate|eventStart|startDate|kickoff|eventTime)\s*["']?\s*[:=]\s*["'](20\d{2}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)["']/i,
    /["'](?:eventDate|eventStart|startDate|kickoff|eventTime)["']\s*:\s*["'](20\d{2}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)["']/i
  ];
  for(const p of patterns){
    const m=html.match(p); if(!m) continue;
    const raw=m[1].replace(' ','T');
    const hasZone=/Z$|[+-]\d{2}:?\d{2}$/.test(raw);
    const iso=hasZone?raw:`${raw}+01:00`;
    const d=new Date(iso);
    if(Number.isFinite(d.getTime()) && d.getTime()>Date.now()-6*3600_000) return d.toISOString();
  }
  return null;
}

async function probeEvent(base:string,eventId:string){
  const pageUrl=`${base}/Stadium/Index?eventId=${eventId}`;
  try{
    const r=await fetch(pageUrl,{headers:{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36','Accept-Language':'pl-PL,pl;q=0.9,en;q=0.8'},redirect:'follow'});
    const html=await r.text();
    const identity=extractDirectIdentity(html);
    return {status:r.status,finalUrl:r.url,loginRedirect:/\/Home\/Login/i.test(r.url),...identity,kickoffAt:extractKickoff(html)};
  }catch(error){return {error:String(error),status:null,finalUrl:null,loginRedirect:false,title:null,h1:null,identity:null,kickoffAt:null};}
}

function classify(anchor:any,probe:any){
  const direct=probe?.identity||'';
  if(direct){
    if(obviousNonMatch(direct)) return {kind:'non_match',reason:'direct_page_non_match'};
    if(matchLike(direct)) return {kind:'match',reason:'direct_page_match_identity'};
  }
  const anchorText=[anchor.ariaLabel,anchor.title,anchor.text,anchor.label].filter(Boolean).join(' | ');
  if(obviousNonMatch(anchorText)) return {kind:'non_match',reason:'same_element_non_match'};
  if(matchLike(anchorText)) return {kind:'match',reason:'same_element_match_identity'};
  return {kind:'unknown',reason:'insufficient_identity'};
}

async function inspectClub(club:any){
  const headers={'User-Agent':'Mozilla/5.0','Accept-Language':'pl-PL,pl;q=0.9,en;q=0.8'};
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),10000);
  try{
    const home=await fetch(club.base_url+'/',{headers,redirect:'follow',signal:controller.signal});
    const html=await home.text();
    const pageLayouts=unique(Array.from(html.matchAll(/https:\/\/static-fr\.roboticket\.com\/Content\/[^"']+?\.html/gi)).map(m=>m[0]));
    const sources=[{url:home.url,text:html}];
    const layoutBodies=await Promise.all(pageLayouts.slice(0,12).map(async url=>{try{const r=await fetch(url,{headers,redirect:'follow'});return {url:r.url,text:await r.text()};}catch{return null;}}));
    for(const body of layoutBodies) if(body) sources.push(body);

    const raw:any[]=[];
    for(const src of sources) raw.push(...parseSameElementCandidates(src.text,src.url));
    const byId=new Map<string,any>();
    for(const a of raw){
      const prev=byId.get(a.eventId);
      const score=(x:any)=>[x.ariaLabel,x.title,x.text].filter(v=>v&&v.length>3).length;
      if(!prev || score(a)>score(prev)) byId.set(a.eventId,a);
    }
    const events=[];
    for(const anchor of byId.values()){
      const probe=await probeEvent(club.base_url,anchor.eventId);
      const classification=classify(anchor,probe);
      const directLabel=probe.identity && !/^roboticket$/i.test(probe.identity)?probe.identity:null;
      events.push({...anchor,label:directLabel||anchor.label,probe,candidateKind:classification.kind,classificationReason:classification.reason});
    }
    return {slug:club.club_slug,base:club.base_url,finalUrl:home.url,homeStatus:home.status,pageLayouts,events};
  } finally { clearTimeout(timer); }
}

Deno.serve(async req=>{
  if(req.headers.get('x-discovery-key')!==DISCOVERY_KEY){return new Response(JSON.stringify({error:'unauthorized'}),{status:401,headers:{'content-type':'application/json'}});}
  try{
    const [clubs,existing]=await Promise.all([
      db('roboticket_clubs?active=eq.true&select=club_slug,club_name,base_url,source_domain',{method:'GET'}),
      db('roboticket_event_candidates?select=club_slug,external_event_id,status,metadata',{method:'GET'})
    ]);
    const existingMap=new Map((existing||[]).map((r:any)=>[`${r.club_slug}:${r.external_event_id}`,r]));
    const inspected=await Promise.all((clubs||[]).map(async club=>{try{return await inspectClub(club);}catch(error){return {slug:club.club_slug,base:club.base_url,error:String(error),events:[]};}}));
    const now=new Date().toISOString();
    const rows:any[]=[];
    const schedulePayloads:any[]=[];
    for(const club of inspected){
      for(const event of (club.events||[])){
        const key=`${club.slug}:${event.eventId}`;
        const old=existingMap.get(key);
        const preservedStatus=old?.status==='collecting'?'collecting':(event.candidateKind==='non_match'?'ignored':'discovered');
        const metadata={...(old?.metadata||{}),discovery_version:VERSION,discovered_base:club.base,final_url:club.finalUrl||null,home_status:club.homeStatus||null,is_roboticket:true,candidate_kind:event.candidateKind,classification_reason:event.classificationReason,anchor_href:event.href||null,anchor_aria_label:event.ariaLabel||null,direct_page_title:event.probe?.title||null,direct_page_h1:event.probe?.h1||null,direct_page_url:event.probe?.finalUrl||null,direct_page_login_redirect:Boolean(event.probe?.loginRedirect),direct_page_status:event.probe?.status||null,discovered_kickoff_at:event.probe?.kickoffAt||null};
        rows.push({club_slug:club.slug,external_event_id:String(event.eventId),label:event.label,source_url:event.source,status:preservedStatus,last_seen_at:now,metadata});
        if(event.candidateKind==='match' && event.probe?.kickoffAt && event.probe?.identity){
          const parts=event.probe.identity.split(/\s(?:-|–|vs|v)\s/i).map((x:string)=>clean(x)).filter(Boolean);
          if(parts.length===2){
            schedulePayloads.push({club_slug:club.slug,external_event_id:String(event.eventId),home_team:parts[0],away_team:parts[1],competition:'Ekstraklasa',kickoff_at:event.probe.kickoffAt,source_url:event.probe.finalUrl||event.source,source_type:'roboticket_direct_event_metadata',verification_confidence:'verified'});
          }
        }
      }
    }
    if(rows.length){
      await db('roboticket_event_candidates?on_conflict=club_slug,external_event_id',{method:'POST',headers:{Prefer:'resolution=merge-duplicates,return=minimal'},body:JSON.stringify(rows)});
    }
    const scheduleResults=[];
    for(const p of schedulePayloads){try{scheduleResults.push(await rpc('upsert_roboticket_verified_schedule_v1',{p_payload:p}));}catch(error){scheduleResults.push({ok:false,error:String(error),identity:`${p.club_slug}:${p.external_event_id}`});}}
    const promotion=await rpc('promote_roboticket_verified_candidates_v1',{});
    return new Response(JSON.stringify({ok:true,version:VERSION,clubs:inspected,candidatesUpserted:rows.length,verifiedSchedulesAttempted:schedulePayloads.length,scheduleResults,promotion}),{headers:{'content-type':'application/json'}});
  }catch(error){return new Response(JSON.stringify({ok:false,version:VERSION,error:String(error)}),{status:500,headers:{'content-type':'application/json'}});}
});
