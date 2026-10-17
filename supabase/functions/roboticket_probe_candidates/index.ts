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

function extractEmbeddedJsonArray(html: string, key: string) {
  const marker = `"${key}"`;
  let markerPos = html.indexOf(marker);
  while (markerPos >= 0) {
    const colonPos = html.indexOf(':', markerPos + marker.length);
    const start = colonPos >= 0 ? html.indexOf('[', colonPos + 1) : -1;
    if (start < 0) return [];
    let depth = 0;
    let inString = false;
    let escaped = false;
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
          try {
            const parsed = JSON.parse(html.slice(start, i + 1));
            return Array.isArray(parsed) ? parsed : [];
          } catch {
            break;
          }
        }
      }
    }
    markerPos = html.indexOf(marker, markerPos + marker.length);
  }
  return [];
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
  const priceAreas = extractEmbeddedJsonArray(html, 'priceAreas');
  const priceTypes = extractEmbeddedJsonArray(html, 'priceTypes');
  const prices = extractEmbeddedJsonArray(html, 'prices');

  return {
    slug: c.slug,
    eventId: c.id,
    pageStatus: page.status,
    finalPageUrl: page.url,
    currency: extractCurrency(html),
    priceAreaCount: priceAreas.length,
    priceTypeCount: priceTypes.length,
    priceCount: prices.length,
    priceAreas: priceAreas.slice(0, 20),
    priceTypes: priceTypes.slice(0, 30),
    prices: prices.slice(0, 60),
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
