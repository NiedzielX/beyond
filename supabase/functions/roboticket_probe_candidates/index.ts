const CANDIDATES = [
  { slug: 'gkskatowice', base: 'https://bilety.gkskatowice.eu', id: '5769', label: 'GKS Katowice-Pogon' },
  { slug: 'cracovia', base: 'https://bilety.cracovia.pl', id: '10434', label: 'Cracovia-Legia' },
  { slug: 'zaglebie_lubin', base: 'https://bilety.zaglebie.com', id: '1953', label: 'Zaglebie-Jagiellonia' },
  { slug: 'wisla_plock', base: 'https://bilety.wisla-plock.pl', id: '3042', label: 'Wisla Plock-Radomiak' },
  { slug: 'pogonszczecin', base: 'https://bilety.pogonszczecin.pl', id: '13399', label: 'Pogon-Radomiak' },
  { slug: 'wislakrakow', base: 'https://wislakrakow.roboticket.com', id: '11521', label: 'Wisla Krakow-Rakow' }
];

function colorId(t: number) {
  const e = Math.floor(t / 1000 / 60).toString(16);
  const r = e.split('').reverse().join('');
  let out = '';
  for (let i = 0; i < e.length; i++) out += (e.charCodeAt(i) ^ r.charCodeAt(i)).toString(16);
  return out;
}

async function roboJson(base: string, pageUrl: string, cookie: string, path: string) {
  const now = Date.now();
  const headers: Record<string, string> = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36',
    Accept: 'application/json, text/plain, */*',
    'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
    Referer: pageUrl,
    'X-Requested-With': 'XMLHttpRequest',
    'x-theme-id': now.toString(36),
    'x-color-id': colorId(now),
    'Content-Type': 'application/x-www-form-urlencoded'
  };
  if (cookie) headers.Cookie = cookie;
  const res = await fetch(base + path, { method: 'POST', headers, body: '', redirect: 'manual' });
  const text = await res.text();
  let json: any = null;
  try { json = JSON.parse(text); } catch {}
  return {
    status: res.status,
    location: res.headers.get('location'),
    json,
    length: text.length,
    excerpt: json ? null : text.slice(0, 180)
  };
}

function primitiveShape(value: any) {
  if (value === null) return null;
  if (Array.isArray(value)) return `[array:${value.length}]`;
  if (typeof value === 'object') return '[object]';
  return value;
}

function priceAreaDiagnostics(infoSectors: any[]) {
  const rows: Array<{ sectorId: string; priceArea: Record<string, unknown> }> = [];
  const keys = new Set<string>();
  const types: Record<string, Set<string>> = {};

  for (const sector of infoSectors) {
    const priceAreas = Array.isArray(sector?.freeSeatsByPriceArea) ? sector.freeSeatsByPriceArea : [];
    for (const priceArea of priceAreas) {
      if (!priceArea || typeof priceArea !== 'object') continue;
      const sanitized: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(priceArea)) {
        keys.add(key);
        if (!types[key]) types[key] = new Set<string>();
        const type = value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value;
        types[key].add(type);
        sanitized[key] = primitiveShape(value);
      }
      if (rows.length < 12) rows.push({ sectorId: String(sector?.id ?? ''), priceArea: sanitized });
    }
  }

  return {
    priceAreaObjectCount: infoSectors.reduce(
      (sum, sector) => sum + (Array.isArray(sector?.freeSeatsByPriceArea) ? sector.freeSeatsByPriceArea.length : 0),
      0
    ),
    keys: Array.from(keys).sort(),
    types: Object.fromEntries(Object.entries(types).map(([key, values]) => [key, Array.from(values).sort()])),
    samples: rows
  };
}

function objectPrimitiveSample(value: any) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const out: Record<string, unknown> = {};
  for (const [key, child] of Object.entries(value)) {
    if (child === null || ['string', 'number', 'boolean'].includes(typeof child)) out[key] = child;
    else if (Array.isArray(child)) out[key] = `[array:${child.length}]`;
  }
  return out;
}

function commercialFieldScan(root: any) {
  const matches: Array<{ path: string; key: string; type: string; sample: unknown }> = [];
  const seen = new Set<string>();
  const commercialKey = /(price|currency|amount|tariff|cost|discount|fee|value)/i;

  function visit(value: any, path: string, depth: number) {
    if (matches.length >= 80 || depth > 7 || value === null || value === undefined) return;
    if (Array.isArray(value)) {
      for (let i = 0; i < Math.min(value.length, 8); i++) visit(value[i], `${path}[${i}]`, depth + 1);
      return;
    }
    if (typeof value !== 'object') return;

    for (const [key, child] of Object.entries(value)) {
      const childPath = path ? `${path}.${key}` : key;
      if (commercialKey.test(key)) {
        const signature = `${childPath}:${typeof child}:${JSON.stringify(primitiveShape(child))}`;
        if (!seen.has(signature)) {
          seen.add(signature);
          matches.push({
            path: childPath,
            key,
            type: child === null ? 'null' : Array.isArray(child) ? 'array' : typeof child,
            sample: primitiveShape(child)
          });
        }
      }
      visit(child, childPath, depth + 1);
      if (matches.length >= 80) break;
    }
  }

  visit(root, '', 0);
  return matches;
}

async function probe(c: { slug: string; base: string; id: string; label: string }) {
  const pageUrl = `${c.base}/Stadium/Index?eventId=${c.id}`;
  const page = await fetch(pageUrl, {
    headers: { 'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8' },
    redirect: 'follow'
  });
  const html = await page.text();
  const setCookies = (page.headers as any).getSetCookie
    ? (page.headers as any).getSetCookie()
    : [page.headers.get('set-cookie')].filter(Boolean);
  const cookie = setCookies.map((v: string) => v.split(';')[0]).join('; ');
  const title = (html.match(/<title>([^<]+)<\/title>/i) || [])[1] || null;
  const [info, sectors, seats] = await Promise.all([
    roboJson(c.base, pageUrl, cookie, `/Stadium/GetWGLSectorsInfo?eventId=${c.id}`),
    roboJson(c.base, pageUrl, cookie, `/Stadium/GetWGLSectors?eventId=${c.id}`),
    roboJson(c.base, pageUrl, cookie, `/Stadium/GetWGLSeats?eventId=${c.id}`)
  ]);
  const infoSectors = Array.isArray(info.json?.sectors) ? info.json.sectors : [];
  const sectorShapes = Array.isArray(sectors.json?.sectors) ? sectors.json.sectors : [];
  const seatRows = Array.isArray(seats.json?.seats) ? seats.json.seats : [];
  const availableTotal = infoSectors.reduce(
    (sum: number, s: any) => sum + (s.freeSeatsByPriceArea || []).reduce((a: number, p: any) => a + Number(p.freeSeatsNo || 0), 0),
    0
  );

  return {
    slug: c.slug,
    eventId: c.id,
    label: c.label,
    pageStatus: page.status,
    finalPageUrl: page.url,
    title,
    infoStatus: info.status,
    sectorsStatus: sectors.status,
    seatsStatus: seats.status,
    seatsCount: seatRows.length,
    sectorInfoCount: infoSectors.length,
    sectorShapeCount: sectorShapes.length,
    availableTotal,
    sourceTimestamp: info.json?.timestamp || null,
    priceAreaDiagnostics: priceAreaDiagnostics(infoSectors),
    payloadDiagnostics: {
      infoCommercialFields: commercialFieldScan(info.json),
      sectorsCommercialFields: commercialFieldScan(sectors.json),
      seatsCommercialFields: commercialFieldScan(seats.json),
      firstSectorShape: objectPrimitiveSample(sectorShapes[0]),
      firstSeat: objectPrimitiveSample(seatRows[0])
    },
    redirects: { info: info.location, sectors: sectors.location, seats: seats.location },
    debug: {
      infoLength: info.length,
      sectorsLength: sectors.length,
      seatsLength: seats.length,
      infoExcerpt: info.excerpt,
      sectorsExcerpt: sectors.excerpt
    }
  };
}

Deno.serve(async () => {
  const results = await Promise.all(
    CANDIDATES.map(async c => {
      try { return await probe(c); }
      catch (e) { return { slug: c.slug, eventId: c.id, label: c.label, error: String(e) }; }
    })
  );
  return new Response(JSON.stringify(results), { headers: { 'content-type': 'application/json' } });
});
