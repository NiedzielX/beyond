import "jsr:@supabase/functions-js/edge-runtime.d.ts";

// Research-only collector. Raw attention signals MUST NOT modify production forecasts.
const CRON_SECRET = Deno.env.get("BEYOND_GDELT_CRON_SECRET") ?? "__runtime-configured__";
const GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc";
const SOURCE_NAME = "GDELT DOC 2.0";

interface TicketEvent { id: number; club_slug: string; home_team: string; away_team: string; kickoff_at: string; }
interface TimelinePoint { date: string; value: number; norm?: number; }

function teamAlias(name: string): string {
  const clean = name.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^A-Za-z0-9 ]+/g, " ").replace(/\s+/g, " ").trim();
  if (/^Lech Poznan$/i.test(clean)) return "Lech";
  if (/Bayer/i.test(clean) && /Leverkusen/i.test(clean)) return "Bayer Leverkusen";
  return clean.replace(/\b\d+\b/g, "").replace(/\s+/g, " ").trim();
}

function queryForEvent(event: TicketEvent): string {
  return `near25:"${teamAlias(event.home_team)} ${teamAlias(event.away_team)}" sourcelang:polish`;
}

function parseDate(value: string): Date | null {
  const m = value.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z?$/);
  if (m) return new Date(`${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}Z`);
  const d = new Date(value);
  return Number.isFinite(d.getTime()) ? d : null;
}

function sumWindow(points: TimelinePoint[], start: Date, end: Date): number {
  return points.reduce((sum, p) => {
    const at = parseDate(p.date);
    return at && at >= start && at < end ? sum + Number(p.value || 0) : sum;
  }, 0);
}

async function sb(path: string, init: RequestInit = {}) {
  const url = Deno.env.get("SUPABASE_URL")!;
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const headers = new Headers(init.headers || {});
  headers.set("apikey", key);
  headers.set("Authorization", `Bearer ${key}`);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  return fetch(`${url}/rest/v1/${path}`, { ...init, headers });
}

async function upcomingLech(): Promise<TicketEvent[]> {
  const now = new Date();
  const end = new Date(now.getTime() + 14 * 86400000);
  const params = new URLSearchParams({
    select: "id,club_slug,home_team,away_team,kickoff_at",
    club_slug: "eq.lech",
    kickoff_at: `gte.${now.toISOString()}`,
    order: "kickoff_at.asc",
    limit: "4"
  });
  const r = await sb(`ticket_events?${params}`);
  if (!r.ok) throw new Error(`ticket_events ${r.status}: ${await r.text()}`);
  return ((await r.json()) as TicketEvent[]).filter(e => new Date(e.kickoff_at) <= end);
}

async function timeline(query: string): Promise<TimelinePoint[]> {
  const url = new URL(GDELT_URL);
  url.searchParams.set("query", query);
  url.searchParams.set("mode", "TimelineVolRaw");
  url.searchParams.set("format", "json");
  url.searchParams.set("timespan", "7d");
  url.searchParams.set("TIMELINESMOOTH", "0");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const r = await fetch(url, { signal: controller.signal, headers: { "User-Agent": "BeyondTicketingResearch/0.3", "Accept": "application/json" } });
    const body = await r.text();
    if (r.status === 429) throw new Error("GDELT_RATE_LIMIT");
    if (!r.ok) throw new Error(`GDELT ${r.status}: ${body.slice(0, 300)}`);
    if (!(r.headers.get("content-type") || "").includes("json")) throw new Error(`GDELT non-JSON: ${body.slice(0, 300)}`);
    const parsed = JSON.parse(body);
    const series = Array.isArray(parsed?.timeline) ? parsed.timeline[0] : null;
    return Array.isArray(series?.data) ? series.data : [];
  } finally { clearTimeout(timer); }
}

async function upsert(payload: Record<string, unknown>) {
  const params = new URLSearchParams({ on_conflict: "ticket_event_id,feature_key,source_name,source_record_key" });
  const r = await sb(`event_context_observations?${params}`, {
    method: "POST",
    headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
    body: JSON.stringify(payload)
  });
  if (!r.ok) throw new Error(`upsert ${r.status}: ${await r.text()}`);
}

Deno.serve(async (req: Request) => {
  if (CRON_SECRET === "__runtime-configured__" || req.headers.get("x-beyond-cron") !== CRON_SECRET) return new Response("Unauthorized", { status: 401 });
  const observedAt = new Date();
  const bucket = observedAt.toISOString().slice(0, 13).replace(/[-T:]/g, "");
  const output: Record<string, unknown>[] = [];
  try {
    const events = await upcomingLech();
    for (let index = 0; index < events.length; index += 1) {
      const event = events[index];
      if (index > 0) await new Promise(r => setTimeout(r, 5500));
      const query = queryForEvent(event);
      try {
        const points = await timeline(query);
        const now = observedAt;
        const h6 = new Date(now.getTime() - 6 * 3600000);
        const h12 = new Date(now.getTime() - 12 * 3600000);
        const h24 = new Date(now.getTime() - 24 * 3600000);
        const h48 = new Date(now.getTime() - 48 * 3600000);
        const d7 = new Date(now.getTime() - 7 * 86400000);
        const current6h = sumWindow(points, h6, now);
        const previous6h = sumWindow(points, h12, h6);
        const current24h = sumWindow(points, h24, now);
        const previous24h = sumWindow(points, h48, h24);
        const prior6d = sumWindow(points, d7, h24);
        const priorDailyMean = prior6d / 6;
        const ratio = priorDailyMean > 0 ? current24h / priorDailyMean : null;
        const acceleration = previous6h > 0 ? current6h / previous6h : (current6h === 0 ? 1 : null);
        const metadata = {
          query, window: "7d", language_filter: "polish", scope: "lech_poc",
          current_6h: current6h, previous_6h: previous6h,
          current_24h: current24h, previous_24h: previous24h,
          prior_6d_total: prior6d, prior_daily_mean: Number(priorDailyMean.toFixed(4)),
          ratio_vs_prior_daily: ratio === null ? null : Number(ratio.toFixed(4)),
          acceleration_6h: acceleration === null ? null : Number(acceleration.toFixed(4)),
          scoring_status: "raw_attention_only_not_model_scored"
        };
        await upsert({ ticket_event_id: event.id, feature_key: "hype.media_attention", observed_at: observedAt.toISOString(), numeric_value: current24h, text_value: ratio === null ? `${current24h} publikacji w ostatnich 24h; brak stabilnego baseline.` : `${current24h} publikacji w ostatnich 24h; ${ratio.toFixed(2)}× średniego dnia z wcześniejszych 6 dni.`, normalized_score: null, source_name: SOURCE_NAME, source_url: GDELT_URL, confidence: points.length ? 0.85 : 0.4, source_record_key: `gdelt:media:v01:${event.id}:${bucket}`, metadata });
        await upsert({ ticket_event_id: event.id, feature_key: "hype.mention_acceleration", observed_at: observedAt.toISOString(), numeric_value: acceleration, text_value: acceleration === null ? `${current6h} publikacji w 6h; wcześniejsze 6h = 0, ratio niestabilne.` : `Tempo publikacji 6h: ${acceleration.toFixed(2)}× (${current6h} vs ${previous6h}).`, normalized_score: null, source_name: SOURCE_NAME, source_url: GDELT_URL, confidence: points.length ? 0.8 : 0.35, source_record_key: `gdelt:acceleration:v01:${event.id}:${bucket}`, metadata });
        output.push({ event_id: event.id, status: "stored", query, points: points.length, current24h, previous24h, ratio, current6h, previous6h, acceleration });
      } catch (error) {
        output.push({ event_id: event.id, status: "error", error: String(error), query });
      }
    }
    return Response.json({ collector: "gdelt_attention_v01", observed_at: observedAt.toISOString(), scope: "lech_poc", results: output });
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
});
