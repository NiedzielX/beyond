import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const VERSION = "stellis-public-collector-v1";
const HEADERS = {
  "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36",
  "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
};

function normalize(value: string): string {
  return String(value || "").toLowerCase().normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "").replace(/ł/g, "l")
    .replace(/[^a-z0-9]+/g, " ").trim().replace(/\s+/g, " ");
}
function clean(value: string): string {
  return value.replace(/<[^>]+>/g, " ").replace(/&nbsp;/gi, " ").replace(/&amp;/gi, "&")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n))).replace(/\s+/g, " ").trim();
}
function decodeHtml(value: string): string {
  return value.replace(/&quot;/g, '"').replace(/&#34;/g, '"').replace(/&amp;/g, "&").replace(/&#39;/g, "'");
}
function uniqById(rows: any[]): any[] {
  const out = new Map<string, any>();
  for (const row of rows) {
    if (!row?.eventId) continue;
    const old = out.get(String(row.eventId));
    const score = (x: any) => (x.homeTeamName ? 100 : 0) + (x.awayTeamName ? 100 : 0) +
      (x.eventDate ? 50 : 0) + (x.availableTicketsCount !== null && x.availableTicketsCount !== undefined ? 20 : 0) +
      (x.eventName ? 10 : 0);
    if (!old || score(row) > score(old)) out.set(String(row.eventId), row);
  }
  return [...out.values()];
}

function supabaseSecret(): { value: string; isLegacyJwt: boolean } {
  const secretJson = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (secretJson) {
    const parsed = JSON.parse(secretJson);
    const value = String(parsed?.default || "");
    if (value) return { value, isLegacyJwt: false };
  }
  const legacy = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (legacy) return { value: legacy, isLegacyJwt: true };
  throw new Error("missing Supabase backend secret");
}
async function db(path: string, options: RequestInit = {}) {
  const url = Deno.env.get("SUPABASE_URL");
  if (!url) throw new Error("missing SUPABASE_URL");
  const secret = supabaseSecret();
  const headers: Record<string, string> = {
    apikey: secret.value,
    "Content-Type": "application/json",
    Prefer: "return=representation",
    ...((options.headers || {}) as Record<string, string>),
  };
  if (secret.isLegacyJwt) headers.Authorization = `Bearer ${secret.value}`;
  const response = await fetch(`${url}/rest/v1/${path}`, { ...options, headers });
  const text = await response.text();
  if (!response.ok) throw new Error(`DB ${path} ${response.status}: ${text.slice(0, 1000)}`);
  return text ? JSON.parse(text) : null;
}
function unwrapRpc(value: any, name: string): any {
  if (Array.isArray(value) && value.length === 1 && value[0] && typeof value[0] === "object") {
    return value[0][name] ?? value[0].payload ?? value[0];
  }
  return value;
}
async function rpc(name: string, body: Record<string, unknown> = {}) {
  return unwrapRpc(await db(`rpc/${name}`, { method: "POST", body: JSON.stringify(body) }), name);
}

function extractJsonArrays(html: string, key = "events"): any[][] {
  const source = decodeHtml(html);
  const marker = `"${key}"`;
  const arrays: any[][] = [];
  let pos = source.indexOf(marker);
  while (pos >= 0) {
    const colon = source.indexOf(":", pos + marker.length);
    const start = colon >= 0 ? source.indexOf("[", colon + 1) : -1;
    if (start < 0) break;
    let depth = 0, inString = false, escaped = false, end = -1;
    for (let i = start; i < source.length; i++) {
      const ch = source[i];
      if (inString) {
        if (escaped) escaped = false;
        else if (ch === "\\") escaped = true;
        else if (ch === '"') inString = false;
        continue;
      }
      if (ch === '"') { inString = true; continue; }
      if (ch === "[") depth++;
      else if (ch === "]") {
        depth--;
        if (depth === 0) {
          end = i;
          try {
            const parsed = JSON.parse(source.slice(start, i + 1));
            if (Array.isArray(parsed)) arrays.push(parsed);
          } catch {}
          break;
        }
      }
    }
    pos = source.indexOf(marker, Math.max(pos + marker.length, end + 1));
  }
  return arrays;
}
function embeddedEvents(html: string): any[] {
  const rows: any[] = [];
  for (const array of extractJsonArrays(html, "events")) {
    for (const item of array) {
      if (!item || typeof item !== "object" || Array.isArray(item) || item.eventId == null || !item.eventName) continue;
      rows.push({
        parser: "embedded_json",
        eventId: String(item.eventId),
        eventName: String(item.eventName),
        eventType: item.eventType == null ? null : Number(item.eventType),
        eventDate: item.eventDate == null ? null : String(item.eventDate),
        homeTeamName: item.homeTeamName == null ? null : String(item.homeTeamName),
        awayTeamName: item.awayTeamName == null ? null : String(item.awayTeamName),
        availableTicketsCount: item.availableTicketsCount == null ? null : Number(item.availableTicketsCount),
        soldTicketsCount: item.soldTicketsCount == null ? null : Number(item.soldTicketsCount),
        hasActiveStage: Boolean(item.hasActiveStage),
        buyTicketUrl: item.buyTicketUrl == null ? null : String(item.buyTicketUrl),
        venueName: item.venueName == null ? null : String(item.venueName),
      });
    }
  }
  return rows;
}
function legacyEvents(html: string, base: string): any[] {
  const source = decodeHtml(html);
  const rows: any[] = [];
  for (const match of source.matchAll(/<div[^>]*class=["'][^"']*event-wrapper[^"']*["'][^>]*>([\s\S]*?)(?=<div[^>]*class=["'][^"']*event-wrapper|<\/section>|<\/form>|$)/gi)) {
    const card = match[1];
    const id = card.match(/(?:eventId|eventid)=([0-9]+)/i)?.[1];
    if (!id) continue;
    const nameHtml = card.match(/class=["'][^"']*event-name[^"']*["'][^>]*>([\s\S]*?)<\//i)?.[1] ?? "";
    const timestamp = card.match(/class=["'][^"']*event-date[^"']*["'][^>]*data-timestamp=["']([0-9]+)["']/i)?.[1] ?? null;
    const hrefRaw = card.match(/<a[^>]+href=["']([^"']*(?:eventId|eventid)=[0-9]+[^"']*)["']/i)?.[1] ?? null;
    rows.push({ parser: "legacy_dom", eventId: id, eventName: clean(nameHtml) || null, eventType: 0, eventDate: timestamp,
      homeTeamName: null, awayTeamName: null, availableTicketsCount: null, soldTicketsCount: null,
      hasActiveStage: true, buyTicketUrl: hrefRaw ? new URL(hrefRaw.replace(/&amp;/g,"&"), base).toString() : null, venueName: null });
  }
  return rows;
}
function eventIso(value: string | null): string | null {
  if (!value || !/^\d+$/.test(value)) return null;
  const date = new Date(Number(value));
  return Number.isFinite(date.getTime()) ? date.toISOString() : null;
}
function nonMatch(row: any): boolean {
  const name = normalize(row.eventName || "");
  if (row.eventType !== null && row.eventType !== undefined && Number(row.eventType) !== 0) return true;
  return /(^| )(karnet|parking|vip|eskorta|voucher|zwiedzanie|conference|konferencja|puchar|cup|towarzyski|friendly)( |$)/.test(name)
    || /(^| )ii( |$)|(^| )u19( |$)|(^| )u17( |$)/.test(name);
}
function aliasIndex(rows: any[]): Map<string, string> {
  const index = new Map<string,string>();
  for (const row of rows) {
    const key = String(row.club_key || "");
    for (const raw of [row.alias, row.canonical_name]) {
      const n = normalize(String(raw || ""));
      if (n && key) index.set(n,key);
    }
  }
  return index;
}
function resolveClub(name: string | null, index: Map<string,string>): string | null {
  return name ? (index.get(normalize(name)) ?? null) : null;
}

async function collectClub(club: any, aliases: Map<string,string>) {
  const response = await fetch(`${club.base_url}/lista-wydarzen`, { headers: HEADERS, redirect: "follow" });
  const html = await response.text();
  if (!response.ok) throw new Error(`event list HTTP ${response.status}`);
  const events = uniqById([...embeddedEvents(html), ...legacyEvents(html, club.base_url)]);
  const capturedAt = new Date().toISOString();
  const results: any[] = [];

  for (const event of events) {
    const kickoffAt = eventIso(event.eventDate);
    const isNonMatch = nonMatch(event);
    const homeClubKey = resolveClub(event.homeTeamName, aliases);
    const awayClubKey = resolveClub(event.awayTeamName, aliases);
    const hasIdentity = Boolean(event.homeTeamName && event.awayTeamName && homeClubKey && awayClubKey);
    const availabilityExposed = !isNonMatch && Number.isFinite(event.availableTicketsCount) && event.availableTicketsCount >= 0;
    let status = isNonMatch ? "invalid" : (availabilityExposed ? "discovered" : "hidden_availability");
    if (!kickoffAt || (!hasIdentity && event.parser === "embedded_json")) status = isNonMatch ? "invalid" : "hidden_availability";

    const sourceUrl = event.buyTicketUrl || `${club.base_url}/lista-wydarzen`;
    const candidate = {
      club_slug: club.club_slug,
      external_event_id: String(event.eventId),
      event_name: event.eventName,
      home_team: event.homeTeamName,
      away_team: event.awayTeamName,
      home_club_key: homeClubKey,
      away_club_key: awayClubKey,
      kickoff_at: kickoffAt,
      source_url: sourceUrl,
      availability_exposed: availabilityExposed,
      available_total: availabilityExposed ? Math.trunc(event.availableTicketsCount) : null,
      sold_total: Number.isFinite(event.soldTicketsCount) && event.soldTicketsCount >= 0 ? Math.trunc(event.soldTicketsCount) : null,
      status,
      last_seen_at: capturedAt,
      metadata: {
        collector_version: VERSION,
        parser: event.parser,
        event_type: event.eventType,
        has_active_stage: event.hasActiveStage,
        venue_name: event.venueName,
        target_values_used: false,
      },
    };

    await db("stellis_event_candidates_v1?on_conflict=club_slug,external_event_id", {
      method: "POST",
      headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
      body: JSON.stringify([candidate]),
    });

    let rawInsert: any = null;
    if (!isNonMatch) {
      rawInsert = await rpc("insert_stellis_raw_observation_v1", { p_payload: {
        club_slug: club.club_slug,
        external_event_id: String(event.eventId),
        captured_at: capturedAt,
        event_name: event.eventName,
        home_team: event.homeTeamName,
        away_team: event.awayTeamName,
        home_club_key: homeClubKey,
        away_club_key: awayClubKey,
        kickoff_at: kickoffAt,
        availability_exposed: availabilityExposed,
        available_total: availabilityExposed ? Math.trunc(event.availableTicketsCount) : null,
        sold_total: Number.isFinite(event.soldTicketsCount) && event.soldTicketsCount >= 0 ? Math.trunc(event.soldTicketsCount) : null,
        source_url: sourceUrl,
        source_version: VERSION,
        raw_metadata: { parser: event.parser, event_type: event.eventType, has_active_stage: event.hasActiveStage, venue_name: event.venueName },
        target_values_used: false,
        production_change: false,
      }});
    }
    results.push({ eventId: event.eventId, eventName: event.eventName, parser: event.parser, status,
      kickoffAt, homeClubKey, awayClubKey, availabilityExposed,
      availableTotal: availabilityExposed ? Math.trunc(event.availableTicketsCount) : null,
      rawInsert });
  }
  return { club: club.club_slug, eventCount: events.length, results };
}

Deno.serve(async () => {
  try {
    const clubs = await db("stellis_clubs_v1?active=eq.true&select=club_slug,club_name,base_url,source_domain", { method: "GET" });
    const aliasPayload = await rpc("export_c1_alpha_v7_aliases_v1");
    const aliases = aliasIndex(Array.isArray(aliasPayload?.aliases) ? aliasPayload.aliases : []);
    if (!aliases.size) throw new Error("alias universe unavailable");

    const results: any[] = [];
    for (const club of clubs || []) {
      try { results.push({ ok: true, ...(await collectClub(club, aliases)) }); }
      catch (error) { results.push({ ok: false, club: club.club_slug, error: String(error) }); }
    }
    const promotion = await rpc("promote_stellis_visible_observations_v1");
    return new Response(JSON.stringify({
      ok: results.every(r => r.ok), version: VERSION, results, promotion,
      targetValuesUsed: false, productionChange: false,
    }), { status: results.every(r => r.ok) ? 200 : 207, headers: { "content-type": "application/json" } });
  } catch (error) {
    return new Response(JSON.stringify({ ok: false, version: VERSION, error: String(error), targetValuesUsed: false, productionChange: false }), {
      status: 500, headers: { "content-type": "application/json" },
    });
  }
});