import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-media-ingest";
const REPOSITORY = "NiedzielX/beyond";
const MAIN_REF = "refs/heads/main";
const GDELT_PREFIX = "https://data.gdeltproject.org/gdeltv5/weblegacy/ngrams/";
const JWKS = createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));

async function authorize(req: Request) {
  const auth = req.headers.get("authorization") || "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!token) throw new Error("missing bearer token");
  const { payload } = await jwtVerify(token, JWKS, {
    issuer: ISSUER,
    audience: AUDIENCE,
  });
  if (payload.repository !== REPOSITORY) throw new Error("repository not allowed");
  if (payload.ref !== MAIN_REF) throw new Error("ref not allowed");
  return payload;
}

async function db(path: string, options: RequestInit = {}) {
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("Missing Supabase service environment");
  const headers = {
    apikey: key,
    Authorization: `Bearer ${key}`,
    "Content-Type": "application/json",
    Prefer: "return=representation",
    ...(options.headers || {}),
  };
  const response = await fetch(`${url}/rest/v1/${path}`, { ...options, headers });
  const text = await response.text();
  if (!response.ok) throw new Error(`DB ${path} ${response.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { "content-type": "application/json" },
});

function parseRecentIso(value: string, label: string, nowMs: number, maxAgeMs: number) {
  const time = Date.parse(value);
  if (!Number.isFinite(time)) throw new Error(`invalid ${label}`);
  if (time > nowMs + 5 * 60_000) throw new Error(`${label} is in the future`);
  if (time < nowMs - maxAgeMs) throw new Error(`${label} is too old`);
  return time;
}

Deno.serve(async (req: Request) => {
  let claims: any;
  try {
    claims = await authorize(req);
  } catch (error) {
    return json({ ok: false, error: `unauthorized: ${String(error)}` }, 401);
  }

  try {
    const url = new URL(req.url);
    const now = new Date();
    const windowStart = new Date(now.getTime() - 3 * 3_600_000);
    const windowEnd = new Date(now.getTime() + 30 * 86_400_000);

    if (req.method === "GET" && url.searchParams.get("mode") === "config") {
      const events = await db(
        `ticket_events?kickoff_at=gte.${encodeURIComponent(windowStart.toISOString())}` +
        `&kickoff_at=lt.${encodeURIComponent(windowEnd.toISOString())}` +
        `&select=id,home_team,away_team,kickoff_at&order=kickoff_at.asc`,
        { method: "GET" }
      ) || [];
      const aliases = await db(
        "media_attention_team_aliases?is_active=eq.true&select=team_name,ngram_tokens",
        { method: "GET" }
      ) || [];
      const aliasMap = new Map(aliases.map((row: any) => [row.team_name, row.ngram_tokens || []]));
      const usable = events
        .filter((event: any) => aliasMap.has(event.home_team) && aliasMap.has(event.away_team))
        .map((event: any) => ({
          id: event.id,
          homeTeam: event.home_team,
          awayTeam: event.away_team,
          kickoffAt: event.kickoff_at,
          homeTokens: aliasMap.get(event.home_team),
          awayTokens: aliasMap.get(event.away_team),
        }));
      return json({ ok: true, repository: claims.repository, events: usable });
    }

    if (req.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);
    const body = await req.json();
    const sourceFileTimestamp = String(body.sourceFileTimestamp || "");
    const sourceFileUrl = String(body.sourceFileUrl || "");
    const sampleAt = String(body.sampleAt || "");
    const samples = Array.isArray(body.samples) ? body.samples : [];

    if (!sourceFileTimestamp || !sourceFileUrl || !sampleAt || !samples.length || samples.length > 100) {
      return json({ ok: false, error: "invalid payload" }, 400);
    }
    if (!sourceFileUrl.startsWith(GDELT_PREFIX) || !sourceFileUrl.endsWith(".ngrams.txt.gz")) {
      return json({ ok: false, error: "invalid source file URL" }, 400);
    }

    const nowMs = Date.now();
    const sourceMs = parseRecentIso(sourceFileTimestamp, "sourceFileTimestamp", nowMs, 3 * 3_600_000);
    const sampleMs = parseRecentIso(sampleAt, "sampleAt", nowMs, 60 * 60_000);
    if (sampleMs < sourceMs) return json({ ok: false, error: "sampleAt predates source file" }, 400);

    const allowedEvents = await db(
      `ticket_events?kickoff_at=gte.${encodeURIComponent(windowStart.toISOString())}` +
      `&kickoff_at=lt.${encodeURIComponent(windowEnd.toISOString())}` +
      `&select=id`,
      { method: "GET" }
    ) || [];
    const allowedIds = new Set(allowedEvents.map((row: any) => Number(row.id)));

    const rows = samples.map((sample: any) => {
      const eventId = Number(sample.ticketEventId);
      const mentionsPl = Number(sample.mentionsPl);
      const matchedGlobal = Number(sample.matchedDocsGlobal);
      if (!allowedIds.has(eventId)) throw new Error(`event ${eventId} not allowed`);
      if (!Number.isInteger(mentionsPl) || mentionsPl < 0) throw new Error("invalid mentionsPl");
      if (!Number.isInteger(matchedGlobal) || matchedGlobal < mentionsPl) throw new Error("invalid matchedDocsGlobal");
      return {
        ticket_event_id: eventId,
        sample_at: sampleAt,
        source_file_timestamp: sourceFileTimestamp,
        source_file_url: sourceFileUrl,
        mentions_pl: mentionsPl,
        matched_docs_global: matchedGlobal,
        source_name: "GDELT Web News NGrams sampled signal",
        metadata: {
          examples: Array.isArray(sample.examples) ? sample.examples.slice(0, 3) : [],
          coverage_note: "single GDELT Web News NGrams sample; not a complete count of all media publications",
          github_run_id: claims.run_id || null,
          github_sha: claims.sha || null,
        },
      };
    });

    await db("media_attention_samples?on_conflict=ticket_event_id,source_file_timestamp", {
      method: "POST",
      headers: { Prefer: "resolution=merge-duplicates,return=representation" },
      body: JSON.stringify(rows),
    });
    const refreshed = await db("rpc/refresh_media_attention_context_v01", {
      method: "POST",
      body: JSON.stringify({}),
    });

    return json({
      ok: true,
      insertedOrUpdated: rows.length,
      sourceFileTimestamp,
      refreshed,
      repository: claims.repository,
      sha: claims.sha || null,
    });
  } catch (error) {
    return json({ ok: false, error: String(error) }, 500);
  }
});
