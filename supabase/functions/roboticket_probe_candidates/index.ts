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
  return { status: res.status, json };
}

function extractJsonArrayCandidates(html: string, key: string) {
  const marker = `"${key}"`;
  const candidates: any[][] = [];
  let markerPos = html.indexOf(marker);
  while (markerPos >= 0) {
    const colonPos = html.indexOf(':', markerPos + marker.length);
    const start = colonPos >= 0 ? html.indexOf('[', colonPos + 1) : -1;
    if (start < 0) break;
    let depth = 0;
    let inString = false;
    let escaped = false;
    let parsedEnd = -1;
    for (let i = start; i < html.length; i++) {
      const ch = html[i];
      if (inString) {
        if (escaped) escaped = false;
        else if (ch === '\\') escaped = true;
        else if (ch === '"') inString = false;
        continue;
      }
      if (ch === '"') { inString = true; continue; }
      if (ch === '[') depth += 1;
      else if (ch === ']') {
        depth -= 1;
        if (depth === 0) {
          parsedEnd = i;
          try {
            const parsed = JSON.parse(html.slice(start, i + 1));
            if (Array.isArray(parsed)) candidates.push(parsed);
          } catch {}
          break;
        }
      }
    }
    markerPos = html.indexOf(marker, Math.max(markerPos + marker.length, parsedEnd + 1));
  }
  return candidates;
}

function selectEmbeddedArray(html: string, key: string, kind: 'areas' | 'types' | 'prices') {
  const candidates = extractJsonArrayCandidates(html, key);
  const score = (rows: any[]) => {
    if (!rows.length) return -1;
    const sample = rows.slice(0, 10);
    if (kind === 'areas' || kind === 'types') {
      return sample.filter(row => row && typeof row === 'object' && !Array.isArray(row) && Number.isFinite(Number(row.id)) && typeof row.name === 'string').length;
    }
    return sample.filter(row => row && typeof row === 'object' && !Array.isArray(row)
      && Number.isFinite(Number(row.priceAreaId))
      && Number.isFinite(Number(row.priceTypeId))
      && Number.isFinite(Number(row.price))).length;
  };
  return candidates.sort((a, b) => score(b) - score(a) || b.length - a.length)[0] || [];
}

function extractCurrency(html: string) {
  const match = html.match(/(?:const|let|var)\s+currencyName\s*=\s*['"]([^'"]+)['"]/i);
  return match ? String(match[1]).trim() : null;
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
  const info = await roboJson(c.base, pageUrl, cookie, `/Stadium/GetWGLSectorsInfo?eventId=${c.id}`);
  const infoSectors = Array.isArray(info.json?.sectors) ? info.json.sectors : [];
  const priceAreas = selectEmbeddedArray(html, 'priceAreas', 'areas');
  const priceTypes = selectEmbeddedArray(html, 'priceTypes', 'types');
  const prices = selectEmbeddedArray(html, 'prices', 'prices');

  return {
    slug: c.slug,
    eventId: c.id,
    pageStatus: page.status,
    finalPageUrl: page.url,
    currency: extractCurrency(html),
    priceAreaCount: priceAreas.length,
    priceTypeCount: priceTypes.length,
    priceCount: prices.length,
    priceAreas: priceAreas.slice(0, 30),
    priceTypes: priceTypes.slice(0, 30),
    prices: prices.slice(0, 80),
    availablePriceAreaSamples: infoSectors.slice(0, 12).map((sector: any) => ({
      sectorId: sector.id,
      freeSeatsByPriceArea: sector.freeSeatsByPriceArea || []
    }))
  };
}

Deno.serve(async () => {
  const results = await Promise.all(CANDIDATES.map(async c => {
    try { return await probe(c); }
    catch (e) { return { slug: c.slug, eventId: c.id, error: String(e) }; }
  }));
  return new Response(JSON.stringify(results), { headers: { 'content-type': 'application/json' } });
});
