const EXCLUDED_CLUBS = new Set(['lech']);

function colorId(t){
  const e=Math.floor(t/1000/60).toString(16), r=e.split('').reverse().join('');
  let out=''; for(let i=0;i<e.length;i++) out+=(e.charCodeAt(i)^r.charCodeAt(i)).toString(16); return out;
}

async function roboJson(base,pageUrl,cookie,path){
  const now=Date.now();
  const headers={
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36',
    'Accept':'application/json, text/plain, */*','Accept-Language':'pl-PL,pl;q=0.9,en;q=0.8',
    'Referer':pageUrl,'X-Requested-With':'XMLHttpRequest','x-theme-id':now.toString(36),
    'x-color-id':colorId(now),'Content-Type':'application/x-www-form-urlencoded'
  };
  if(cookie) headers['Cookie']=cookie;
  const res=await fetch(base+path,{method:'POST',headers,body:''});
  const text=await res.text();
  if(!res.ok) throw new Error(`${path} HTTP ${res.status}`);
  if(!text) throw new Error(`${path} returned empty body`);
  return JSON.parse(text);
}

async function db(path,options={}){
  const supabaseUrl=Deno.env.get('SUPABASE_URL');
  const serviceKey=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if(!supabaseUrl||!serviceKey) throw new Error('Missing Supabase service environment');
  const headers={'apikey':serviceKey,'Authorization':`Bearer ${serviceKey}`,'Content-Type':'application/json','Prefer':'return=representation',...(options.headers||{})};
  const res=await fetch(`${supabaseUrl}/rest/v1/${path}`,{...options,headers});
  const text=await res.text();
  if(!res.ok) throw new Error(`DB ${path} ${res.status}: ${text}`);
  return text?JSON.parse(text):null;
}

async function loadEvents(){
  const [clubs,events]=await Promise.all([
    db('roboticket_clubs?active=eq.true&select=club_slug,base_url,source_domain',{method:'GET'}),
    db('ticket_events?provider=eq.roboticket&select=id,club_slug,source_domain,external_event_id,match_date,kickoff_at&order=kickoff_at.asc',{method:'GET'})
  ]);
  const clubMap=new Map((clubs||[]).map(c=>[c.club_slug,c]));
  const now=Date.now();
  return (events||[]).filter(e=>!EXCLUDED_CLUBS.has(e.club_slug)).filter(e=>new Date(e.kickoff_at).getTime()>now).filter(e=>clubMap.has(e.club_slug)).map(e=>{
    const club=clubMap.get(e.club_slug);
    return {ticketEventId:Number(e.id),club:e.club_slug,base:club.base_url,domain:e.source_domain||club.source_domain,eventId:String(e.external_event_id),matchDate:String(e.match_date),kickoff:String(e.kickoff_at)};
  });
}

async function collectEvent(cfg){
  if(new Date()>=new Date(cfg.kickoff)) return {ok:true,club:cfg.club,eventId:cfg.eventId,skipped:true,reason:'kickoff_reached'};
  const last=await db(`snapshots?ticket_event_id=eq.${cfg.ticketEventId}&select=captured_at&order=captured_at.desc&limit=1`,{method:'GET'});
  if(last?.length){
    const ageMs=Date.now()-new Date(last[0].captured_at).getTime();
    if(ageMs<10*60*1000) return {ok:true,club:cfg.club,eventId:cfg.eventId,ticketEventId:cfg.ticketEventId,skipped:true,reason:'recent_snapshot'};
  }
  const pageUrl=`${cfg.base}/Stadium/Index?eventId=${cfg.eventId}`;
  const page=await fetch(pageUrl,{headers:{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36','Accept-Language':'pl-PL,pl;q=0.9,en;q=0.8'},redirect:'follow'});
  if(!page.ok) throw new Error(`${cfg.club}/${cfg.eventId} stadium page HTTP ${page.status}`);
  await page.text();
  const setCookies=page.headers.getSetCookie?page.headers.getSetCookie():[page.headers.get('set-cookie')].filter(Boolean);
  const cookie=setCookies.map(v=>v.split(';')[0]).join('; ');
  const [sectorsInfo,sectorsShape]=await Promise.all([
    roboJson(cfg.base,pageUrl,cookie,`/Stadium/GetWGLSectorsInfo?eventId=${cfg.eventId}`),
    roboJson(cfg.base,pageUrl,cookie,`/Stadium/GetWGLSectors?eventId=${cfg.eventId}`)
  ]);
  const names=new Map();
  for(const s of (sectorsShape.sectors||[])) names.set(Number(s.id),String(s.name||s.id));
  const sectors=(sectorsInfo.sectors||[]).map(s=>({sector:names.get(Number(s.id))||String(s.id),available:(s.freeSeatsByPriceArea||[]).reduce((sum,p)=>sum+Number(p.freeSeatsNo||0),0)}));
  if(!sectors.length) throw new Error(`${cfg.club}/${cfg.eventId} returned no ticket sectors`);
  const availableTotal=sectors.reduce((sum,s)=>sum+s.available,0);
  const capturedAt=new Date().toISOString();
  const snapshots=await db('snapshots',{method:'POST',body:JSON.stringify([{event_id:Number(cfg.eventId),source:'roboticket',captured_at:capturedAt,ticket_event_id:cfg.ticketEventId,event_match_date_at_capture:cfg.matchDate,event_kickoff_at_capture:cfg.kickoff,available_total:availableTotal,sector_count:sectors.length}])});
  const snapshotId=snapshots[0].id;
  await db('sector_inventory',{method:'POST',headers:{'Prefer':'return=minimal'},body:JSON.stringify(sectors.map(s=>({snapshot_id:snapshotId,event_id:Number(cfg.eventId),sector:s.sector,available:s.available})))});
  return {ok:true,club:cfg.club,eventId:cfg.eventId,ticketEventId:cfg.ticketEventId,snapshotId,capturedAt,availableTotal,sectorCount:sectors.length,sourceTimestamp:sectorsInfo.timestamp||null};
}

Deno.serve(async()=>{
  try{
    const events=await loadEvents();
    const results=await Promise.all(events.map(async cfg=>{try{return await collectEvent(cfg);}catch(error){return {ok:false,club:cfg.club,eventId:cfg.eventId,ticketEventId:cfg.ticketEventId,error:String(error)};}}));
    const ok=results.every(r=>r.ok);
    return new Response(JSON.stringify({ok,eventCount:events.length,results}),{status:ok?200:207,headers:{'content-type':'application/json'}});
  }catch(error){return new Response(JSON.stringify({ok:false,error:String(error)}),{status:500,headers:{'content-type':'application/json'}});}
});
