import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const VERSION = "stellis-collector-v1";
const TZ = "Europe/Warsaw";
const HEADERS = {
  "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36",
  "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
};

type Alias = { alias: string; club_key: string };
type Club = { club_slug: string; club_name: string; base_url: string; source_domain: string };
type ParsedEvent = {
  club_slug: string;
  external_event_id: string;
  event_name: string | null;
  home_team: string | null;
  away_team: string | null;
  home_club_key: string | null;
  away_club_key: string | null;
  kickoff_at: string | null;
  source_url: string;
  availability_exposed: boolean;
  available_total: number | null;
  sold_total: number | null;
  parser: string;
  raw_metadata: Record<string, unknown>;
};

function normalize(value: string | null | undefined): string {
  return String(value || "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ł/g, "l")
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}
function cleanHtml(value: string): string {
  return value
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
function toNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) && n >= 0 ? n : null;
}
function canonicalTeamKey(name: string | null, aliases: Alias[]): string | null {
  if (!name) return null;
  const n = normalize(name);
  const exact = aliases.find((a) => normalize(a.alias) === n);
  if (exact) return exact.club_key;
  const hits = aliases.filter((a) => {
    const x = normalize(a.alias);
    return x.length >= 4 && (` ${n} `).includes(` ${x} `);
  });
  const keys = [...new Set(hits.map((h) => h.club_key))];
  return keys.length === 1 ? keys[0] : null;
}
function teamKeysInText(text: string, aliases: Alias[]): string[] {
  const n = normalize(text);
  const keys = new Set<string>();
  for (const row of aliases) {
    const a = normalize(row.alias);
    if (a.length >= 4 && (` ${n} `).includes(` ${a} `)) keys.add(row.club_key);
  }
  return [...keys];
}

async function db(path: string, options: RequestInit = {}) {
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("Missing Supabase service environment");
  const headers: Record<string, string> = {
    apikey: key,
    Authorization: `Bearer ${key}`,
    "Content-Type": "application/json",
    Prefer: "return=representation",
    ...((options.headers || {}) as Record<string, string>),
  };
  const response = await fetch(`${url}/rest/v1/${path}`, { ...options, headers });
  const text = await response.text();
  if (!response.ok) throw new Error(`DB ${path} ${response.status}: ${text.slice(0, 1200)}`);
  return text ? JSON.parse(text) : null;
}
function unwrapRpc(value: unknown, name: string): any {
  if (Array.isArray(value) && value.length === 1 && value[0] && typeof value[0] === "object") {
    const row = value[0] as Record<string, unknown>;
    return row[name] ?? row.payload ?? value[0];
  }
  return value;
}
async function rpc(name: string, body: Record<string, unknown> = {}) {
  return unwrapRpc(await db(`rpc/${name}`, { method: "POST", body: JSON.stringify(body) }), name);
}

function balancedArray(text: string, start: number): string | null {
  if (text[start] !== "[") return null;
  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let i = start; i < text.length; i++) {
    const ch = text[i];
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
      if (depth === 0) return text.slice(start, i + 1);
    }
  }
  return null;
}
function scriptBodies(html: string): string[] {
  return [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map((m) => m[1] || "");
}
function parseReactEvents(html: string, club: Club, aliases: Alias[]): ParsedEvent[] {
  const result: ParsedEvent[] = [];
  for (const body of scriptBodies(html)) {
    if (!body.includes("UpcomingEvents") || !body.includes('"events"')) continue;
    const showAvailable = /"showAvailableTicketsCount"\s*:\s*true/i.test(body);
    let cursor = 0;
    while (true) {
      const marker = body.indexOf('"events"', cursor);
      if (marker < 0) break;
      const colon = body.indexOf(":", marker + 8);
      const start = colon >= 0 ? body.indexOf("[", colon + 1) : -1;
      if (start < 0) break;
      const raw = balancedArray(body, start);
      cursor = start + 1;
      if (!raw) continue;
      let events: any[];
      try { events = JSON.parse(raw); } catch { continue; }
      for (const e of events) {
        const id = String(e?.eventId || "").trim();
        if (!id) continue;
        const home = e?.homeTeamName ? String(e.homeTeamName).trim() : null;
        const away = e?.awayTeamName ? String(e.awayTeamName).trim() : null;
        const epoch = toNumber(e?.eventDate);
        const available = showAvailable ? toNumber(e?.availableTicketsCount) : null;
        result.push({
          club_slug: club.club_slug,
          external_event_id: id,
          event_name: e?.eventName ? String(e.eventName).trim() : [home, away].filter(Boolean).join(" - ") || null,
          home_team: home,
          away_team: away,
          home_club_key: canonicalTeamKey(home, aliases),
          away_club_key: canonicalTeamKey(away, aliases),
          kickoff_at: epoch ? new Date(epoch).toISOString() : null,
          source_url: e?.buyTicketUrl ? String(e.buyTicketUrl) : club.base_url,
          availability_exposed: showAvailable && available !== null,
          available_total: available,
          sold_total: toNumber(e?.soldTicketsCount),
          parser: "stellis-react-events-v1",
          raw_metadata: {
            event_type: e?.eventType ?? null,
            show_available_tickets_count: showAvailable,
            has_active_stage: e?.hasActiveStage ?? null,
            venue_name: e?.venueName ?? null,
          },
        });
      }
    }
  }
  return result;
}

function zonedLocalToIso(year: number, month: number, day: number, hour: number, minute: number): string {
  const desired = Date.UTC(year, month - 1, day, hour, minute, 0);
  let guess = desired;
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ,
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
  });
  for (let i = 0; i < 3; i++) {
    const parts = Object.fromEntries(formatter.formatToParts(new Date(guess)).map((p) => [p.type, p.value]));
    const represented = Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day), Number(parts.hour), Number(parts.minute), Number(parts.second));
    guess += desired - represented;
  }
  return new Date(guess).toISOString();
}
function inferYear(month: number, day: number): number {
  const now = new Date();
  let year = now.getUTCFullYear();
  const candidate = Date.UTC(year, month - 1, day, 12, 0, 0);
  if (candidate < now.getTime() - 45 * 24 * 3600_000) year += 1;
  return year;
}
function parseLegacyEvents(html: string, club: Club, aliases: Alias[]): ParsedEvent[] {
  const ids = [...new Set([
    ...[...html.matchAll(/EventListWebPortlet_eventId=(\d+)/gi)].map((m) => m[1]),
    ...[...html.matchAll(/TicketSaleWebPortlet_eventId=(\d+)/gi)].map((m) => m[1]),
  ])];
  const result: ParsedEvent[] = [];
  for (const id of ids) {
    const positions: number[] = [];
    let pos = 0;
    while ((pos = html.indexOf(id, pos)) >= 0) { positions.push(pos); pos += id.length; }
    let best: ParsedEvent | null = null;
    for (const at of positions) {
      const window = html.slice(Math.max(0, at - 5000), Math.min(html.length, at + 6500));
      const text = cleanHtml(window);
      const keys = teamKeysInText(text, aliases);
      if (!keys.includes(club.club_slug) || keys.length < 2) continue;
      const opponents = keys.filter((k) => k !== club.club_slug);
      if (opponents.length !== 1) continue;
      const dateMatch = text.match(/\b(0?[1-9]|[12]\d|3[01])[.\/-](0?[1-9]|1[0-2])(?:[.\/-](20\d{2}))?\b[\s\S]{0,40}?(?:g\.?\s*)?([01]?\d|2[0-3]):([0-5]\d)\b/i);
      const availableMatch = text.match(/Dost[eę]pne\s+miejsca\s*:\s*([0-9][0-9\s]*)/i);
      const occupiedMatch = text.match(/([0-9][0-9\s]*)\s+zaj[eę]tych\s+miejsc/i);
      if (!dateMatch) continue;
      const day = Number(dateMatch[1]);
      const month = Number(dateMatch[2]);
      const year = dateMatch[3] ? Number(dateMatch[3]) : inferYear(month, day);
      const hour = Number(dateMatch[4]);
      const minute = Number(dateMatch[5]);
      const homeAlias = aliases.find((a) => a.club_key === club.club_slug)?.alias || club.club_name;
      const awayKey = opponents[0];
      const awayAlias = aliases.find((a) => a.club_key === awayKey)?.alias || awayKey;
      const available = availableMatch ? Number(availableMatch[1].replace(/\s/g, "")) : null;
      const sold = occupiedMatch ? Number(occupiedMatch[1].replace(/\s/g, "")) : null;
      const candidate: ParsedEvent = {
        club_slug: club.club_slug,
        external_event_id: id,
        event_name: `${homeAlias} - ${awayAlias}`,
        home_team: homeAlias,
        away_team: awayAlias,
        home_club_key: club.club_slug,
        away_club_key: awayKey,
        kickoff_at: zonedLocalToIso(year, month, day, hour, minute),
        source_url: club.base_url,
        availability_exposed: available !== null,
        available_total: available,
        sold_total: sold,
        parser: "stellis-server-card-v1",
        raw_metadata: { source_window_hash_basis: `${id}:${day}.${month}.${year}:${hour}:${minute}` },
      };
      if (!best || (candidate.availability_exposed && !best.availability_exposed)) best = candidate;
    }
    if (best) result.push(best);
  }
  return result;
}

function dedupe(events: ParsedEvent[]): ParsedEvent[] {
  const by = new Map<string, ParsedEvent>();
  for (const e of events) {
    const key = `${e.club_slug}:${e.external_event_id}`;
    const old = by.get(key);
    if (!old || (e.parser.startsWith("stellis-react") && !old.parser.startsWith("stellis-react")) || (e.availability_exposed && !old.availability_exposed)) by.set(key, e);
  }
  return [...by.values()];
}
async function fetchClub(club: Club, aliases: Alias[]): Promise<{ club: Club; events: ParsedEvent[]; error?: string }> {
  try {
    const response = await fetch(`${club.base_url}/`, { headers: HEADERS, redirect: "follow" });
    const html = await response.text();
    if (!response.ok) throw new Error(`home HTTP ${response.status}`);
    const events = dedupe([...parseReactEvents(html, club, aliases), ...parseLegacyEvents(html, club, aliases)]);
    return { club, events };
  } catch (error) {
    return { club, events: [], error: String(error) };
  }
}

Deno.serve(async (req: Request) => {
  const mode = new URL(req.url).searchParams.get("mode") || "audit";
  if (!['audit','collect'].includes(mode)) return new Response(JSON.stringify({ ok:false,error:'unsupported mode' }), { status:400,headers:{'content-type':'application/json'} });
  try {
    const [clubsRaw, aliasPayload] = await Promise.all([
      db("stellis_clubs_v1?active=eq.true&select=club_slug,club_name,base_url,source_domain", { method: "GET" }),
      rpc("export_c1_alpha_v7_aliases_v1"),
    ]);
    const clubs = (clubsRaw || []) as Club[];
    const aliases = Array.isArray(aliasPayload?.aliases) ? aliasPayload.aliases as Alias[] : [];
    if (!aliases.length) throw new Error("football alias universe unavailable");

    const audited = [];
    for (const club of clubs) audited.push(await fetchClub(club, aliases));
    const events = audited.flatMap((r) => r.events);
    const safeEvents = events.map((e) => ({
      ...e,
      eligible_home_pair: Boolean(e.home_club_key && e.away_club_key && e.home_club_key === e.club_slug),
    }));

    if (mode === "audit") {
      return new Response(JSON.stringify({
        ok: true,
        version: VERSION,
        mode,
        club_count: clubs.length,
        event_count: safeEvents.length,
        clubs: audited.map((x) => ({ club_slug:x.club.club_slug,error:x.error || null,event_count:x.events.length })),
        events: safeEvents,
        target_values_used: false,
        production_change: false,
      }), { headers: { "content-type": "application/json" } });
    }

    const now = new Date().toISOString();
    const inserts = [];
    for (const e of safeEvents) {
      const status = !e.home_club_key || !e.away_club_key || e.home_club_key !== e.club_slug
        ? "invalid"
        : e.availability_exposed ? "discovered" : "hidden_availability";
      await db("stellis_event_candidates_v1?on_conflict=club_slug,external_event_id", {
        method: "POST",
        headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
        body: JSON.stringify({
          club_slug:e.club_slug,external_event_id:e.external_event_id,event_name:e.event_name,home_team:e.home_team,away_team:e.away_team,
          home_club_key:e.home_club_key,away_club_key:e.away_club_key,kickoff_at:e.kickoff_at,source_url:e.source_url,
          availability_exposed:e.availability_exposed,available_total:e.available_total,sold_total:e.sold_total,status,last_seen_at:now,
          metadata:{ parser:e.parser,...e.raw_metadata },
        }),
      });
      const inserted = await rpc("insert_stellis_raw_observation_v1", { p_payload: {
        club_slug:e.club_slug,external_event_id:e.external_event_id,captured_at:now,event_name:e.event_name,home_team:e.home_team,away_team:e.away_team,
        home_club_key:e.home_club_key,away_club_key:e.away_club_key,kickoff_at:e.kickoff_at,availability_exposed:e.availability_exposed,
        available_total:e.available_total,sold_total:e.sold_total,source_url:e.source_url,source_version:VERSION,raw_metadata:{ parser:e.parser,...e.raw_metadata },
        target_values_used:false,
      }});
      inserts.push({ identity:`${e.club_slug}:${e.external_event_id}`,status,inserted });
    }
    const promotion = await rpc("promote_stellis_visible_observations_v1");
    return new Response(JSON.stringify({
      ok:true,version:VERSION,mode,club_count:clubs.length,event_count:safeEvents.length,events:safeEvents,inserts,promotion,
      target_values_used:false,production_change:false,
    }), { headers:{"content-type":"application/json"} });
  } catch (error) {
    return new Response(JSON.stringify({ ok:false,version:VERSION,mode,error:String(error),production_change:false }), { status:500,headers:{"content-type":"application/json"} });
  }
});
