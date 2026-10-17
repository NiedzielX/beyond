const EXCLUDED_CLUBS = new Set(['lech']);

function colorId(t) {
  const e = Math.floor(t / 1000 / 60).toString(16);
  const r = e.split('').reverse().join('');
  let out = '';
  for (let i = 0; i < e.length; i++) out += (e.charCodeAt(i) ^ r.charCodeAt(i)).toString(16);
  return out;
}

async function roboJson(base, pageUrl, cookie, path) {
  const now = Date.now();
  const headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
    'Referer': pageUrl,
    'X-Requested-With': 'XMLHttpRequest',
    'x-theme-id': now.toString(36),
    'x-color-id': colorId(now),
    'Content-Type': 'application/x-www-form-urlencoded'
  };
  if (cookie) headers['Cookie'] = cookie;
  const res = await fetch(base + path, { method: 'POST', headers, body: '' });
  const text = await res.text();
  if (!res.ok) throw new Error(`${path} HTTP ${res.status}`);
  if (!text) throw new Error(`${path} returned empty body`);
  return JSON.parse(text);
}

async function db(path, options = {}) {
  const supabaseUrl = Deno.env.get('SUPABASE_URL');
  const serviceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if (!supabaseUrl || !serviceKey) throw new Error('Missing Supabase service environment');
  const headers = {
    apikey: serviceKey,
    Authorization: `Bearer ${serviceKey}`,
    'Content-Type': 'application/json',
    Prefer: 'return=representation',
    ...(options.headers || {})
  };
  const res = await fetch(`${supabaseUrl}/rest/v1/${path}`, { ...options, headers });
  const text = await res.text();
  if (!res.ok) throw new Error(`DB ${path} ${res.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

function extractJsonArrayCandidates(html, key) {
  const marker = `"${key}"`;
  const candidates = [];
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

function selectEmbeddedArray(html, key, kind) {
  const candidates = extractJsonArrayCandidates(html, key);
  const score = rows => {
    if (!rows.length) return -1;
    const sample = rows.slice(0, 10);
    if (kind === 'areas' || kind === 'types') {
      return sample.filter(row => row && typeof row === 'object' && !Array.isArray(row)
        && Number.isFinite(Number(row.id)) && typeof row.name === 'string').length;
    }
    return sample.filter(row => row && typeof row === 'object' && !Array.isArray(row)
      && Number.isFinite(Number(row.priceAreaId))
      && Number.isFinite(Number(row.priceTypeId))
      && Number.isFinite(Number(row.price))).length;
  };
  return candidates.sort((a, b) => score(b) - score(a) || b.length - a.length)[0] || [];
}

function extractCurrency(html) {
  const match = html.match(/(?:const|let|var)\s+currencyName\s*=\s*['"]([^'"]+)['"]/i);
  return match ? String(match[1]).trim() : null;
}

function parsePricing(html) {
  const priceAreas = selectEmbeddedArray(html, 'priceAreas', 'areas');
  const priceTypes = selectEmbeddedArray(html, 'priceTypes', 'types');
  const prices = selectEmbeddedArray(html, 'prices', 'prices');
  const currency = extractCurrency(html);

  const priceAreaNames = new Map();
  for (const row of priceAreas) {
    const id = Number(row?.id);
    if (Number.isFinite(id)) priceAreaNames.set(id, row?.name == null ? null : String(row.name));
  }

  const priceTypeNames = new Map();
  for (const row of priceTypes) {
    const id = Number(row?.id);
    if (Number.isFinite(id)) priceTypeNames.set(id, row?.name == null ? null : String(row.name));
  }

  const normalizedPrices = [];
  const seen = new Set();
  for (const row of prices) {
    const priceAreaId = Number(row?.priceAreaId);
    const priceTypeId = Number(row?.priceTypeId);
    const price = Number(row?.price);
    if (!Number.isFinite(priceAreaId) || !Number.isFinite(priceTypeId) || !Number.isFinite(price) || price < 0) continue;
    const key = `${priceAreaId}:${priceTypeId}`;
    if (seen.has(key)) continue;
    seen.add(key);
    normalizedPrices.push({
      priceAreaId,
      priceAreaName: priceAreaNames.get(priceAreaId) ?? null,
      priceTypeId,
      priceTypeName: priceTypeNames.get(priceTypeId) ?? null,
      price,
      currency
    });
  }

  return { priceAreaNames, priceTypeNames, prices: normalizedPrices, currency };
}

async function loadEvents() {
  const [clubs, events] = await Promise.all([
    db('roboticket_clubs?active=eq.true&select=club_slug,base_url,source_domain', { method: 'GET' }),
    db('ticket_events?provider=eq.roboticket&select=id,club_slug,source_domain,external_event_id,match_date,kickoff_at&order=kickoff_at.asc', { method: 'GET' })
  ]);
  const clubMap = new Map((clubs || []).map(c => [c.club_slug, c]));
  const now = Date.now();
  return (events || [])
    .filter(e => !EXCLUDED_CLUBS.has(e.club_slug))
    .filter(e => new Date(e.kickoff_at).getTime() > now)
    .filter(e => clubMap.has(e.club_slug))
    .map(e => {
      const club = clubMap.get(e.club_slug);
      return {
        ticketEventId: Number(e.id),
        club: e.club_slug,
        base: club.base_url,
        domain: e.source_domain || club.source_domain,
        eventId: String(e.external_event_id),
        matchDate: String(e.match_date),
        kickoff: String(e.kickoff_at)
      };
    });
}

async function collectEvent(cfg) {
  if (new Date() >= new Date(cfg.kickoff)) {
    return { ok: true, club: cfg.club, eventId: cfg.eventId, skipped: true, reason: 'kickoff_reached' };
  }

  const last = await db(`snapshots?ticket_event_id=eq.${cfg.ticketEventId}&select=captured_at&order=captured_at.desc&limit=1`, { method: 'GET' });
  if (last?.length) {
    const ageMs = Date.now() - new Date(last[0].captured_at).getTime();
    if (ageMs < 10 * 60 * 1000) {
      return { ok: true, club: cfg.club, eventId: cfg.eventId, ticketEventId: cfg.ticketEventId, skipped: true, reason: 'recent_snapshot' };
    }
  }

  const pageUrl = `${cfg.base}/Stadium/Index?eventId=${cfg.eventId}`;
  const page = await fetch(pageUrl, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36',
      'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8'
    },
    redirect: 'follow'
  });
  if (!page.ok) throw new Error(`${cfg.club}/${cfg.eventId} stadium page HTTP ${page.status}`);
  const html = await page.text();

  const setCookies = page.headers.getSetCookie ? page.headers.getSetCookie() : [page.headers.get('set-cookie')].filter(Boolean);
  const cookie = setCookies.map(v => v.split(';')[0]).join('; ');
  const [sectorsInfo, sectorsShape] = await Promise.all([
    roboJson(cfg.base, pageUrl, cookie, `/Stadium/GetWGLSectorsInfo?eventId=${cfg.eventId}`),
    roboJson(cfg.base, pageUrl, cookie, `/Stadium/GetWGLSectors?eventId=${cfg.eventId}`)
  ]);

  const pricing = parsePricing(html);
  const names = new Map();
  for (const s of (sectorsShape.sectors || [])) names.set(Number(s.id), String(s.name || s.id));

  const sectors = [];
  const sectorPriceAreas = [];
  for (const s of (sectorsInfo.sectors || [])) {
    const sectorSourceId = Number(s.id);
    const sector = names.get(sectorSourceId) || String(s.id);
    let available = 0;
    for (const p of (s.freeSeatsByPriceArea || [])) {
      const priceAreaId = Number(p.priceAreaId);
      const priceAreaAvailable = Number(p.freeSeatsNo || 0);
      if (!Number.isFinite(priceAreaId) || !Number.isFinite(priceAreaAvailable) || priceAreaAvailable < 0) continue;
      available += priceAreaAvailable;
      sectorPriceAreas.push({
        sector,
        sectorSourceId: Number.isFinite(sectorSourceId) ? sectorSourceId : null,
        priceAreaId,
        priceAreaName: pricing.priceAreaNames.get(priceAreaId) ?? null,
        available: priceAreaAvailable
      });
    }
    sectors.push({ sector, available });
  }

  if (!sectors.length) throw new Error(`${cfg.club}/${cfg.eventId} returned no ticket sectors`);
  const availableTotal = sectors.reduce((sum, s) => sum + s.available, 0);
  const capturedAt = new Date().toISOString();
  const snapshots = await db('snapshots', {
    method: 'POST',
    body: JSON.stringify([{
      event_id: Number(cfg.eventId),
      source: 'roboticket',
      captured_at: capturedAt,
      ticket_event_id: cfg.ticketEventId,
      event_match_date_at_capture: cfg.matchDate,
      event_kickoff_at_capture: cfg.kickoff,
      available_total: availableTotal,
      sector_count: sectors.length
    }])
  });
  const snapshotId = snapshots[0].id;

  await db('sector_inventory', {
    method: 'POST',
    headers: { Prefer: 'return=minimal' },
    body: JSON.stringify(sectors.map(s => ({
      snapshot_id: snapshotId,
      event_id: Number(cfg.eventId),
      sector: s.sector,
      available: s.available
    })))
  });

  if (sectorPriceAreas.length) {
    await db('sector_price_area_observations_v1', {
      method: 'POST',
      headers: { Prefer: 'return=minimal' },
      body: JSON.stringify(sectorPriceAreas.map(row => ({
        ticket_event_id: cfg.ticketEventId,
        snapshot_id: snapshotId,
        captured_at: capturedAt,
        sector: row.sector,
        sector_source_id: row.sectorSourceId,
        price_area_id: row.priceAreaId,
        price_area_name: row.priceAreaName,
        available: row.available,
        source: 'roboticket'
      })))
    });
  }

  if (pricing.prices.length) {
    await db('ticket_price_observations_v1', {
      method: 'POST',
      headers: { Prefer: 'return=minimal' },
      body: JSON.stringify(pricing.prices.map(row => ({
        ticket_event_id: cfg.ticketEventId,
        snapshot_id: snapshotId,
        captured_at: capturedAt,
        price_area_id: row.priceAreaId,
        price_area_name: row.priceAreaName,
        price_type_id: row.priceTypeId,
        price_type_name: row.priceTypeName,
        price: row.price,
        currency: row.currency,
        source: 'roboticket'
      })))
    });
  }

  return {
    ok: true,
    club: cfg.club,
    eventId: cfg.eventId,
    ticketEventId: cfg.ticketEventId,
    snapshotId,
    capturedAt,
    availableTotal,
    sectorCount: sectors.length,
    priceAreaInventoryRows: sectorPriceAreas.length,
    priceRows: pricing.prices.length,
    currency: pricing.currency,
    priceDataStatus: pricing.prices.length ? 'CAPTURED' : 'MISSING',
    sourceTimestamp: sectorsInfo.timestamp || null
  };
}

Deno.serve(async () => {
  try {
    const events = await loadEvents();
    const results = await Promise.all(events.map(async cfg => {
      try { return await collectEvent(cfg); }
      catch (error) {
        return { ok: false, club: cfg.club, eventId: cfg.eventId, ticketEventId: cfg.ticketEventId, error: String(error) };
      }
    }));
    const ok = results.every(r => r.ok);
    return new Response(JSON.stringify({ ok, eventCount: events.length, results }), {
      status: ok ? 200 : 207,
      headers: { 'content-type': 'application/json' }
    });
  } catch (error) {
    return new Response(JSON.stringify({ ok: false, error: String(error) }), {
      status: 500,
      headers: { 'content-type': 'application/json' }
    });
  }
});
