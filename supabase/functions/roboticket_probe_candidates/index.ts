const CANDIDATES = [
  { slug: 'gkskatowice', base: 'https://bilety.gkskatowice.eu', id: '5769', label: 'GKS Katowice-Pogon' },
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
  return { status: res.status, location: res.headers.get('location'), json, length: text.length, excerpt: json ? null : text.slice(0, 180) };
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
  for (const sector of infoSectors) {
    const priceAreas = Array.isArray(sector?.freeSeatsByPriceArea) ? sector.freeSeatsByPriceArea : [];
    for (const priceArea of priceAreas) {
      if (!priceArea || typeof priceArea !== 'object') continue;
      const sanitized: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(priceArea)) {
        keys.add(key);
        sanitized[key] = primitiveShape(value);
      }
      if (rows.length < 16) rows.push({ sectorId: String(sector?.id ?? ''), priceArea: sanitized });
    }
  }
  return {
    priceAreaObjectCount: infoSectors.reduce((sum, sector) => sum + (Array.isArray(sector?.freeSeatsByPriceArea) ? sector.freeSeatsByPriceArea.length : 0), 0),
    keys: Array.from(keys).sort(),
    samples: rows
  };
}

function commercialFieldScan(root: any) {
  const matches: Array<{ path: string; key: string; sample: unknown }> = [];
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
        const signature = `${childPath}:${JSON.stringify(primitiveShape(child))}`;
        if (!seen.has(signature)) {
          seen.add(signature);
          matches.push({ path: childPath, key, sample: primitiveShape(child) });
        }
      }
      visit(child, childPath, depth + 1);
    }
  }
  visit(root, '', 0);
  return matches;
}

function scriptUrls(html: string, pageUrl: string) {
  const urls: string[] = [];
  const re = /<script[^>]+src=["']([^"']+)["'][^>]*>/gi;
  let match: RegExpExecArray | null;
  while ((match = re.exec(html)) !== null && urls.length < 24) {
    try { urls.push(new URL(match[1], pageUrl).toString()); } catch {}
  }
  return [...new Set(urls)];
}

function commercialTextHits(text: string) {
  const needles = ['pricearea', 'price area', 'priceareaid', 'paid', 'tariff', 'currency', 'ticketprice', 'getprice', 'prices'];
  const lower = text.toLowerCase();
  const hits: string[] = [];
  for (const needle of needles) {
    let from = 0;
    for (let i = 0; i < 12; i++) {
      const pos = lower.indexOf(needle, from);
      if (pos < 0) break;
      hits.push(text.slice(Math.max(0, pos - 160), Math.min(text.length, pos + 260)).replace(/\s+/g, ' '));
      from = pos + needle.length;
    }
  }
  return [...new Set(hits)].slice(0, 40);
}

async function scriptDiagnostics(html: string, pageUrl: string) {
  const scripts = scriptUrls(html, pageUrl);
  const sameOrigin = scripts.filter(url => {
    try { return new URL(url).origin === new URL(pageUrl).origin; } catch { return false; }
  }).slice(-12);
  const results: Array<{ url: string; status: number; length: number; commercialHits: string[] }> = [];
  for (const url of sameOrigin) {
    try {
      const response = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0', Referer: pageUrl } });
      const text = await response.text();
      const hits = commercialTextHits(text);
      if (hits.length) results.push({ url, status: response.status, length: text.length, commercialHits: hits });
    } catch {}
  }
  return {
    scriptCount: scripts.length,
    sameOriginScanned: sameOrigin.length,
    htmlCommercialHits: commercialTextHits(html),
    scriptsWithCommercialHits: results
  };
}

async function probe(c: { slug: string; base: string; id: string; label: string }) {
  const pageUrl = `${c.base}/Stadium/Index?eventId=${c.id}`;
  const page = await fetch(pageUrl, { headers: { 'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8' }, redirect: 'follow' });
  const html = await page.text();
  const setCookies = (page.headers as any).getSetCookie ? (page.headers as any).getSetCookie() : [page.headers.get('set-cookie')].filter(Boolean);
  const cookie = setCookies.map((v: string) => v.split(';')[0]).join('; ');
  const [info, sectors, seats, scripts] = await Promise.all([
    roboJson(c.base, pageUrl, cookie, `/Stadium/GetWGLSectorsInfo?eventId=${c.id}`),
    roboJson(c.base, pageUrl, cookie, `/Stadium/GetWGLSectors?eventId=${c.id}`),
    roboJson(c.base, pageUrl, cookie, `/Stadium/GetWGLSeats?eventId=${c.id}`),
    scriptDiagnostics(html, pageUrl)
  ]);
  const infoSectors = Array.isArray(info.json?.sectors) ? info.json.sectors : [];
  const sectorShapes = Array.isArray(sectors.json?.sectors) ? sectors.json.sectors : [];
  const seatRows = Array.isArray(seats.json?.seats) ? seats.json.seats : [];
  return {
    slug: c.slug,
    eventId: c.id,
    label: c.label,
    pageStatus: page.status,
    finalPageUrl: page.url,
    infoStatus: info.status,
    sectorsStatus: sectors.status,
    seatsStatus: seats.status,
    seatsCount: seatRows.length,
    sectorInfoCount: infoSectors.length,
    sectorShapeCount: sectorShapes.length,
    sourceTimestamp: info.json?.timestamp || null,
    priceAreaDiagnostics: priceAreaDiagnostics(infoSectors),
    payloadDiagnostics: {
      infoCommercialFields: commercialFieldScan(info.json),
      sectorsCommercialFields: commercialFieldScan(sectors.json),
      seatsCommercialFields: commercialFieldScan(seats.json),
      firstSeat: seatRows[0] ? { id: seatRows[0].id, sectorId: seatRows[0].sectorId, paId: seatRows[0].paId } : null
    },
    scriptDiagnostics: scripts
  };
}

Deno.serve(async () => {
  const results = await Promise.all(CANDIDATES.map(async c => {
    try { return await probe(c); }
    catch (e) { return { slug: c.slug, eventId: c.id, label: c.label, error: String(e) }; }
  }));
  return new Response(JSON.stringify(results), { headers: { 'content-type': 'application/json' } });
});
