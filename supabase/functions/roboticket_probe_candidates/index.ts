const CANDIDATES = [
  {slug:'zaglebie_lubin', base:'https://bilety.zaglebie.com', id:'1953', label:'Zaglebie-Jagiellonia'},
  {slug:'wisla_plock', base:'https://bilety.wisla-plock.pl', id:'3042', label:'Wisla Plock-Radomiak'},
  {slug:'korona', base:'https://bilety.korona-kielce.pl', id:'46927', label:'Korona candidate'},
  {slug:'wislakrakow', base:'https://wislakrakow.roboticket.com', id:'11521', label:'Wisla Krakow-Rakow candidate 11521'},
  {slug:'wislakrakow', base:'https://wislakrakow.roboticket.com', id:'11718', label:'Wisla Krakow-Cracovia candidate 11718'}
];

function colorId(t:number){
  const e=Math.floor(t/1000/60).toString(16),r=e.split('').reverse().join('');
  let out='';
  for(let i=0;i<e.length;i++) out+=(e.charCodeAt(i)^r.charCodeAt(i)).toString(16);
  return out;
}

async function roboJson(base:string,pageUrl:string,cookie:string,path:string){
  const now=Date.now();
  const headers:Record<string,string>={
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36',
    'Accept':'application/json, text/plain, */*',
    'Accept-Language':'pl-PL,pl;q=0.9,en;q=0.8',
    'Referer':pageUrl,
    'X-Requested-With':'XMLHttpRequest',
    'x-theme-id':now.toString(36),
    'x-color-id':colorId(now),
    'Content-Type':'application/x-www-form-urlencoded'
  };
  if(cookie) headers['Cookie']=cookie;
  const res=await fetch(base+path,{method:'POST',headers,body:'',redirect:'manual'});
  const text=await res.text();
  let json:any=null;
  try{json=JSON.parse(text);}catch{}
  return {status:res.status,location:res.headers.get('location'),json,length:text.length,excerpt:json?null:text.slice(0,180)};
}

function primitiveProjection(value:any){
  if(!value || typeof value!=='object') return value;
  const out:Record<string,unknown>={};
  for(const [key,item] of Object.entries(value)){
    if(item===null || ['string','number','boolean'].includes(typeof item)) out[key]=item;
  }
  return out;
}

function arrayDiagnostic(items:any[],limit=5){
  const keys=[...new Set(items.flatMap((item:any)=>item&&typeof item==='object'?Object.keys(item):[]))].sort();
  return {
    count:items.length,
    objectKeys:keys,
    primitiveSamples:items.slice(0,limit).map(primitiveProjection)
  };
}

function priceAreaDiagnostic(infoSectors:any[]){
  const areas=infoSectors.flatMap((sector:any)=>Array.isArray(sector?.freeSeatsByPriceArea)?sector.freeSeatsByPriceArea:[]);
  return arrayDiagnostic(areas);
}

async function probe(c:{slug:string;base:string;id:string;label:string}){
  const pageUrl=`${c.base}/Stadium/Index?eventId=${c.id}`;
  const page=await fetch(pageUrl,{headers:{'User-Agent':'Mozilla/5.0','Accept-Language':'pl-PL,pl;q=0.9,en;q=0.8'},redirect:'follow'});
  const html=await page.text();
  const setCookies=(page.headers as any).getSetCookie?(page.headers as any).getSetCookie():[page.headers.get('set-cookie')].filter(Boolean);
  const cookie=setCookies.map((v:string)=>v.split(';')[0]).join('; ');
  const title=(html.match(/<title>([^<]+)<\/title>/i)||[])[1]||null;
  const [info,sectors,seats]=await Promise.all([
    roboJson(c.base,pageUrl,cookie,`/Stadium/GetWGLSectorsInfo?eventId=${c.id}`),
    roboJson(c.base,pageUrl,cookie,`/Stadium/GetWGLSectors?eventId=${c.id}`),
    roboJson(c.base,pageUrl,cookie,`/Stadium/GetWGLSeats?eventId=${c.id}`)
  ]);
  const infoSectors=Array.isArray(info.json?.sectors)?info.json.sectors:[];
  const sectorShapes=Array.isArray(sectors.json?.sectors)?sectors.json.sectors:[];
  const seatRows=Array.isArray(seats.json?.seats)?seats.json.seats:[];
  const availableTotal=infoSectors.reduce((sum:number,s:any)=>sum+(s.freeSeatsByPriceArea||[]).reduce((a:number,p:any)=>a+Number(p.freeSeatsNo||0),0),0);
  const htmlPriceTokens=[...new Set((html.match(/.{0,35}(?:priceArea|price|cena|currency).{0,80}/gi)||[]).slice(0,20))];
  return {
    slug:c.slug,eventId:c.id,label:c.label,pageStatus:page.status,finalPageUrl:page.url,title,
    infoStatus:info.status,sectorsStatus:sectors.status,seatsStatus:seats.status,
    seatsCount:seatRows.length,
    sectorInfoCount:infoSectors.length,
    sectorShapeCount:sectorShapes.length,
    availableTotal,
    sourceTimestamp:info.json?.timestamp||null,
    priceAreaDiagnostic:priceAreaDiagnostic(infoSectors),
    sectorShapeDiagnostic:arrayDiagnostic(sectorShapes,3),
    seatDiagnostic:arrayDiagnostic(seatRows,3),
    htmlPriceTokens,
    redirects:{info:info.location,sectors:sectors.location,seats:seats.location},
    debug:{infoLength:info.length,sectorsLength:sectors.length,seatsLength:seats.length,infoExcerpt:info.excerpt,sectorsExcerpt:sectors.excerpt}
  };
}

Deno.serve(async()=>{
  const results=await Promise.all(CANDIDATES.map(async c=>{
    try{return await probe(c);}catch(e){return{slug:c.slug,eventId:c.id,label:c.label,error:String(e)};}
  }));
  return new Response(JSON.stringify(results),{headers:{'content-type':'application/json'}});
});