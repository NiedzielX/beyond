import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const TARGET_CLUB = "wislakrakow";
const USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36";
const VAO_BATCH_SIZE = 20;
const MIN_GEOMETRY_SEATS = 1000;
const RECENT_SNAPSHOT_MS = 10 * 60 * 1000;

function colorId(t: number) {
  const e = Math.floor(t / 1000 / 60).toString(16);
  const r = e.split("").reverse().join("");
  let out = "";
  for (let i = 0; i < e.length; i++) out += (e.charCodeAt(i) ^ r.charCodeAt(i)).toString(16);
  return out;
}

function chunks<T>(rows: T[], size: number) {
  const out: T[][] = [];
  for (let i = 0; i < rows.length; i += size) out.push(rows.slice(i, i + size));
  return out;
}

async function db(path: string, options: RequestInit = {}) {
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceKey) throw new Error("Missing Supabase service environment");
  const headers = {
    apikey: serviceKey,
    Authorization: `Bearer ${serviceKey}`,
    "Content-Type": "application/json",
    Prefer: "return=representation",
    ...((options.headers || {}) as Record<string, string>),
  };
  const res = await fetch(`${supabaseUrl}/rest/v1/${path}`, { ...options, headers });
  const text = await res.text();
  if (!res.ok) throw new Error(`DB ${path} ${res.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

async function roboticketJson(base: string, pageUrl: string, cookie: string, path: string) {
  const now = Date.now();
  const headers: Record<string, string> = {
    "User-Agent": USER_AGENT,
    Accept: "application/json, text/plain, */*",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
    Referer: pageUrl,
    "X-Requested-With": "XMLHttpRequest",
    "x-theme-id": now.toString(36),
    "x-color-id": colorId(now),
    "Content-Type": "application/x-www-form-urlencoded",
  };
  if (cookie) headers.Cookie = cookie;
  const res = await fetch(base + path, { method: "POST", headers, body: "" });
  const text = await res.text();
  if (!res.ok) throw new Error(`${path} HTTP ${res.status}`);
  if (!text) throw new Error(`${path} returned empty body`);
  return JSON.parse(text);
}

function flattenSeatPayload(payload: unknown) {
  const rows: any[] = [];
  if (Array.isArray(payload)) rows.push(...payload);
  else if (payload && typeof payload === "object") {
    for (const value of Object.values(payload as Record<string, unknown>)) {
      if (Array.isArray(value)) rows.push(...value);
    }
  }
  return rows;
}

async function loadEvents() {
  const [clubs, events] = await Promise.all([
    db(`roboticket_clubs?active=eq.true&club_slug=eq.${TARGET_CLUB}&select=club_slug,base_url,source_domain`, { method: "GET" }),
    db(`ticket_events?provider=eq.roboticket&club_slug=eq.${TARGET_CLUB}&select=id,club_slug,source_domain,external_event_id,match_date,kickoff_at&order=kickoff_at.asc`, { method: "GET" }),
  ]);
  const club = clubs?.[0];
  if (!club) return [];
  const now = Date.now();
  return (events || [])
    .filter((e: any) => new Date(e.kickoff_at).getTime() > now)
    .map((e: any) => ({
      ticketEventId: Number(e.id),
      club: e.club_slug,
      base: club.base_url,
      domain: e.source_domain || club.source_domain,
      eventId: String(e.external_event_id),
      matchDate: String(e.match_date),
      kickoff: String(e.kickoff_at),
    }));
}

async function latestSnapshot(ticketEventId: number) {
  const rows = await db(`snapshots?ticket_event_id=eq.${ticketEventId}&select=id,captured_at,source,available_total&order=captured_at.desc&limit=1`, { method: "GET" });
  return rows?.[0] || null;
}

async function collectEvent(cfg: any) {
  if (new Date() >= new Date(cfg.kickoff)) {
    return { ok: true, skipped: true, reason: "kickoff_reached", ticketEventId: cfg.ticketEventId, eventId: cfg.eventId };
  }

  const prior = await latestSnapshot(cfg.ticketEventId);
  if (prior) {
    const ageMs = Date.now() - new Date(prior.captured_at).getTime();
    if (ageMs >= 0 && ageMs < RECENT_SNAPSHOT_MS) {
      return { ok: true, skipped: true, reason: "recent_snapshot", ticketEventId: cfg.ticketEventId, eventId: cfg.eventId };
    }
  }

  const pageUrl = `${cfg.base}/Stadium/Index?eventId=${cfg.eventId}`;
  const page = await fetch(pageUrl, {
    headers: { "User-Agent": USER_AGENT, "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8" },
    redirect: "follow",
  });
  if (!page.ok) throw new Error(`${cfg.club}/${cfg.eventId} stadium page HTTP ${page.status}`);
  const html = await page.text();
  const setCookies = page.headers.getSetCookie ? page.headers.getSetCookie() : [page.headers.get("set-cookie")].filter(Boolean) as string[];
  const cookie = setCookies.map((v: string) => v.split(";")[0]).join("; ");

  // This collector is a fallback only. If the standard sector contract works,
  // the existing Roboticket collector remains authoritative.
  const sectorInfo = await roboticketJson(cfg.base, pageUrl, cookie, `/Stadium/GetWGLSectorsInfo?eventId=${cfg.eventId}`);
  if (Array.isArray(sectorInfo?.sectors) && sectorInfo.sectors.length > 0) {
    return { ok: true, skipped: true, reason: "standard_sector_contract_available", ticketEventId: cfg.ticketEventId, eventId: cfg.eventId };
  }

  const shiftMatch = html.match(/"spatialHashShift"\s*:\s*(\d+)/);
  if (!shiftMatch) throw new Error(`${cfg.club}/${cfg.eventId} missing spatialHashShift`);
  const spatialHashShift = Number(shiftMatch[1]);
  if (!Number.isInteger(spatialHashShift) || spatialHashShift < 1 || spatialHashShift > 20) {
    throw new Error(`${cfg.club}/${cfg.eventId} invalid spatialHashShift=${spatialHashShift}`);
  }

  const geometry = await roboticketJson(cfg.base, pageUrl, cookie, `/Stadium/GetWGLSeats?eventId=${cfg.eventId}`);
  const seats = Array.isArray(geometry?.seats) ? geometry.seats : [];
  if (seats.length < MIN_GEOMETRY_SEATS) throw new Error(`${cfg.club}/${cfg.eventId} seat geometry too small: ${seats.length}`);

  const geometryIds = new Set<string>();
  const vaoKeys = new Set<string>();
  for (const seat of seats) {
    if (seat?.id == null || !Number.isFinite(seat?.x) || !Number.isFinite(seat?.y)) {
      throw new Error(`${cfg.club}/${cfg.eventId} invalid seat geometry row`);
    }
    geometryIds.add(String(seat.id));
    vaoKeys.add(`${seat.x >> spatialHashShift}_${seat.y >> spatialHashShift}`);
  }
  if (geometryIds.size !== seats.length) throw new Error(`${cfg.club}/${cfg.eventId} duplicate geometry seat IDs`);

  const byId = new Map<string, any>();
  for (const batch of chunks([...vaoKeys].sort(), VAO_BATCH_SIZE)) {
    const payload = await roboticketJson(
      cfg.base,
      pageUrl,
      cookie,
      `/Stadium/GetWGLSeatsOccInfo?eventId=${cfg.eventId}&vaoKeysForCache=${encodeURIComponent(batch.join("v"))}`,
    );
    for (const row of flattenSeatPayload(payload)) {
      if (row?.id != null) byId.set(String(row.id), row);
    }
  }

  const matched: any[] = [];
  for (const id of geometryIds) {
    const row = byId.get(id);
    if (!row) throw new Error(`${cfg.club}/${cfg.eventId} incomplete VAO coverage: missing seat ${id}`);
    matched.push(row);
  }

  let selectableSeats = 0;
  let rightsTrue = 0;
  const occCounts: Record<string, number> = {};
  for (const row of matched) {
    if (typeof row.anyRight !== "boolean" || typeof row.hasSgRight !== "boolean" || typeof row.hasResRight !== "boolean") {
      throw new Error(`${cfg.club}/${cfg.eventId} VAO rights fields missing`);
    }
    if (![0, 1, 2, 3].includes(row.occ)) throw new Error(`${cfg.club}/${cfg.eventId} unknown Roboticket occ=${String(row.occ)}`);
    const rights = row.anyRight && row.hasSgRight && row.hasResRight;
    if (rights) rightsTrue += 1;
    occCounts[String(row.occ)] = (occCounts[String(row.occ)] || 0) + 1;
    // Roboticket renderer contract: At.Empty=0, At.My=1, At.Other=2, At.NotAvailable=3.
    // A seat is selectable only when all rights are true and occupancy is Empty/My.
    if (rights && (row.occ === 0 || row.occ === 1)) selectableSeats += 1;
  }

  if (selectableSeats <= 0) {
    return {
      ok: true,
      skipped: true,
      reason: "no_public_selectable_seats",
      ticketEventId: cfg.ticketEventId,
      eventId: cfg.eventId,
      geometrySeats: seats.length,
      vaoKeyCount: vaoKeys.size,
      rightsTrue,
      occCounts,
    };
  }

  // Re-check immediately before write to reduce duplicate risk if two invocations overlap.
  const beforeWrite = await latestSnapshot(cfg.ticketEventId);
  if (beforeWrite) {
    const ageMs = Date.now() - new Date(beforeWrite.captured_at).getTime();
    if (ageMs >= 0 && ageMs < RECENT_SNAPSHOT_MS) {
      return { ok: true, skipped: true, reason: "recent_snapshot_before_write", ticketEventId: cfg.ticketEventId, eventId: cfg.eventId };
    }
  }

  const capturedAt = new Date().toISOString();
  const inserted = await db("snapshots", {
    method: "POST",
    body: JSON.stringify([{
      event_id: /^\d+$/.test(cfg.eventId) ? Number(cfg.eventId) : null,
      source: "roboticket_vao_selectable_v1",
      captured_at: capturedAt,
      ticket_event_id: cfg.ticketEventId,
      event_match_date_at_capture: cfg.matchDate,
      event_kickoff_at_capture: cfg.kickoff,
      available_total: selectableSeats,
      sector_count: null,
    }]),
  });

  return {
    ok: true,
    skipped: false,
    mode: "vao_selectable_v1",
    ticketEventId: cfg.ticketEventId,
    eventId: cfg.eventId,
    snapshotId: inserted?.[0]?.id ?? null,
    capturedAt,
    availableTotal: selectableSeats,
    geometrySeats: seats.length,
    vaoKeyCount: vaoKeys.size,
    rightsTrue,
    occCounts,
  };
}

Deno.serve(async () => {
  try {
    const events = await loadEvents();
    const results = [];
    for (const cfg of events) {
      try {
        results.push(await collectEvent(cfg));
      } catch (error) {
        results.push({ ok: false, ticketEventId: cfg.ticketEventId, eventId: cfg.eventId, error: String(error) });
      }
    }
    return new Response(JSON.stringify({
      ok: results.every((r: any) => r.ok),
      version: "roboticket-vao-collect-v1",
      targetClub: TARGET_CLUB,
      eventCount: events.length,
      results,
      target_values_used: false,
      production_change: false,
    }), {
      status: results.every((r: any) => r.ok) ? 200 : 207,
      headers: { "content-type": "application/json" },
    });
  } catch (error) {
    return new Response(JSON.stringify({
      ok: false,
      version: "roboticket-vao-collect-v1",
      error: String(error),
      target_values_used: false,
      production_change: false,
    }), { status: 500, headers: { "content-type": "application/json" } });
  }
});
