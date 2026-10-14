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
  const { payload } = await jwtVerify(token, JWKS, { issuer: ISSUER, audience: AUDIENCE });
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
        "media_attention_team_aliases?is_active=eq.true&select=team_name,ngram_tokens,strong_ngram_tokens",
        { method: "GET" }
      ) || [];
      const aliasMap = new Map(aliases.map((row: any) => [row.team_name, {
        all: row.ngram_tokens || [],
        strong: row.strong_ngram_tokens || row.ngram_tokens || [],
      }]));
      const usable = events.filter((event: any) => aliasMap.has(event.home_team) && aliasMap.has(event.away_team)).map((event: any) => ({
        id: event.id,
        homeTeam: event.home_team,
        awayTeam: event.away_team,
        kickoffAt: event.kickoff_at,
        homeTokens: aliasMap.get(event.home_team)?.all || [],
        awayTokens: aliasMap.get(event.away_team)?.all || [],
        homeStrongTokens: aliasMap.get(event.home_team)?.strong || [],
        awayStrongTokens: aliasMap.get(event.away_team)?.strong || [],
      }));
      return json({ ok: true, version: "v2", repository: claims.repository, events: usable });
    }

    if (req.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);
    const body = await req.json();
    const sampleAt = String(body.sampleAt || "");
    const batches = Array.isArray(body.batches) ? body.batches : [];
    if (!sampleAt || !batches.length || batches.length > 12) return json({ ok: false, error: "invalid batch payload" }, 400);

    const nowMs = Date.now();
    parseRecentIso(sampleAt, "sampleAt", nowMs, 60 * 60_000);
    const allowedEvents = await db(
      `ticket_events?kickoff_at=gte.${encodeURIComponent(windowStart.toISOString())}` +
      `&kickoff_at=lt.${encodeURIComponent(windowEnd.toISOString())}&select=id`,
      { method: "GET" }
    ) || [];
    const allowedIds = new Set(allowedEvents.map((row: any) => Number(row.id)));

    let insertedRows = 0;
    let skippedBatches = 0;
    const processed: string[] = [];

    for (const batch of batches) {
      const sourceFileTimestamp = String(batch.sourceFileTimestamp || "");
      const sourceFileUrl = String(batch.sourceFileUrl || "");
      const samples = Array.isArray(batch.samples) ? batch.samples : [];
      if (!sourceFileTimestamp || !sourceFileUrl || !samples.length || samples.length > 100) throw new Error("invalid source batch");
      if (!sourceFileUrl.startsWith(GDELT_PREFIX) || !sourceFileUrl.endsWith(".ngrams.txt.gz")) throw new Error("invalid source file URL");
      const sourceMs = parseRecentIso(sourceFileTimestamp, "sourceFileTimestamp", nowMs, 3 * 3_600_000);
      if (Date.parse(sampleAt) < sourceMs) throw new Error("sampleAt predates source file");

      const existingSource = await db(
        `media_attention_samples_v2?source_file_timestamp=eq.${encodeURIComponent(sourceFileTimestamp)}&select=id&limit=1`,
        { method: "GET" }
      ) || [];
      if (existingSource.length) {
        skippedBatches += 1;
        continue;
      }

      const rows = samples.map((sample: any) => {
        const eventId = Number(sample.ticketEventId);
        const unionMentionsPl = Number(sample.unionMentionsPl);
        const pairMentionsPl = Number(sample.pairMentionsPl);
        const homeMentionsPl = Number(sample.homeMentionsPl);
        const awayMentionsPl = Number(sample.awayMentionsPl);
        const pairDocsGlobal = Number(sample.pairDocsGlobal);
        const unionDocsGlobal = Number(sample.unionDocsGlobal);
        const ints = [unionMentionsPl,pairMentionsPl,homeMentionsPl,awayMentionsPl,pairDocsGlobal,unionDocsGlobal];
        if (!allowedIds.has(eventId)) throw new Error(`event ${eventId} not allowed`);
        if (ints.some((v) => !Number.isInteger(v) || v < 0)) throw new Error("invalid v2 media counts");
        if (pairMentionsPl > unionMentionsPl || pairDocsGlobal > unionDocsGlobal) throw new Error("pair count exceeds union count");
        return {
          ticket_event_id: eventId,
          sample_at: sourceFileTimestamp,
          source_file_timestamp: sourceFileTimestamp,
          source_file_url: sourceFileUrl,
          union_mentions_pl: unionMentionsPl,
          pair_mentions_pl: pairMentionsPl,
          home_mentions_pl: homeMentionsPl,
          away_mentions_pl: awayMentionsPl,
          pair_docs_global: pairDocsGlobal,
          union_docs_global: unionDocsGlobal,
          source_name: "GDELT Web News NGrams v2",
          metadata: {
            examples: Array.isArray(sample.examples) ? sample.examples.slice(0, 5) : [],
            matching: "strong alias union for broad attention; all-alias intersection for pair mentions",
            collected_at: sampleAt,
            github_run_id: claims.run_id || null,
            github_sha: claims.sha || null,
            production_impact: "none_shadow_only",
          },
        };
      });

      await db("media_attention_samples_v2?on_conflict=ticket_event_id,source_file_timestamp", {
        method: "POST",
        headers: { Prefer: "resolution=ignore-duplicates,return=representation" },
        body: JSON.stringify(rows),
      });
      insertedRows += rows.length;
      processed.push(sourceFileTimestamp);
    }

    const refreshed = await db("rpc/refresh_media_attention_context_v02", { method: "POST", body: JSON.stringify({}) });
    return json({ ok: true, version: "v2-multifile", insertedRows, processedBatches: processed.length, skippedBatches,
      processedSourceTimestamps: processed, refreshed, repository: claims.repository, sha: claims.sha || null });
  } catch (error) {
    return json({ ok: false, error: String(error) }, 500);
  }
});
