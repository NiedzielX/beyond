import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-sporting-shadow";
const REPOSITORY = "NiedzielX/beyond";
const MAIN_REF = "refs/heads/main";
const SOURCE_NAME = "TheSportsDB v1 shadow";
const ALLOWED_FEATURE = "sport.match_stakes";
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

function parseRecentIso(value: string, label: string, maxAgeMs: number) {
  const time = Date.parse(value);
  const now = Date.now();
  if (!Number.isFinite(time)) throw new Error(`invalid ${label}`);
  if (time > now + 5 * 60_000) throw new Error(`${label} is in the future`);
  if (time < now - maxAgeMs) throw new Error(`${label} is too old`);
  return time;
}

async function upcomingLeagueEvents() {
  const now = new Date();
  const windowEnd = new Date(now.getTime() + 30 * 86_400_000);
  return await db(
    `ticket_events?kickoff_at=gte.${encodeURIComponent(now.toISOString())}` +
    `&kickoff_at=lt.${encodeURIComponent(windowEnd.toISOString())}` +
    `&competition=ilike.${encodeURIComponent("*Ekstraklasa*")}` +
    `&select=id,home_team,away_team,kickoff_at,competition&order=kickoff_at.asc`,
    { method: "GET" }
  ) || [];
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
    if (req.method === "GET" && url.searchParams.get("mode") === "config") {
      const events = await upcomingLeagueEvents();
      return json({
        ok: true,
        repository: claims.repository,
        events: events.map((event: any) => ({
          id: Number(event.id),
          homeTeam: event.home_team,
          awayTeam: event.away_team,
          kickoffAt: event.kickoff_at,
          competition: event.competition,
        })),
      });
    }

    if (req.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);
    const body = await req.json();
    const observedAt = String(body.observedAt || "");
    const sourceName = String(body.sourceName || "");
    const sourceSnapshotKey = String(body.sourceSnapshotKey || "");
    const leagueId = String(body.leagueId || "");
    const season = String(body.season || "");
    const samples = Array.isArray(body.samples) ? body.samples : [];

    if (!observedAt || !sourceSnapshotKey || sourceName !== SOURCE_NAME || leagueId !== "4422" || season !== "2026-2027") {
      return json({ ok: false, error: "invalid source payload" }, 400);
    }
    parseRecentIso(observedAt, "observedAt", 2 * 60 * 60_000);
    if (!samples.length || samples.length > 100) return json({ ok: false, error: "invalid samples" }, 400);

    const allowedEvents = await upcomingLeagueEvents();
    const allowedIds = new Set(allowedEvents.map((row: any) => Number(row.id)));
    const ready = samples.filter((sample: any) => sample?.status === "ready");
    if (!ready.length) return json({ ok: true, inserted: 0, skipped: true, reason: "no ready samples" });

    const eventIds = ready.map((sample: any) => Number(sample.ticketEventId));
    for (const eventId of eventIds) {
      if (!allowedIds.has(eventId)) throw new Error(`event ${eventId} not allowed`);
    }

    const idFilter = `in.(${eventIds.join(",")})`;
    const referenceRows = await db(
      `event_context_observations?feature_key=eq.${encodeURIComponent(ALLOWED_FEATURE)}` +
      `&ticket_event_id=${encodeURIComponent(idFilter)}` +
      `&select=ticket_event_id,observed_at,numeric_value,source_name&order=observed_at.desc`,
      { method: "GET" }
    ) || [];
    const references = new Map<number, any>();
    for (const row of referenceRows) {
      const eventId = Number(row.ticket_event_id);
      if (!references.has(eventId) && row.numeric_value !== null && row.source_name !== SOURCE_NAME) {
        references.set(eventId, row);
      }
    }

    const rows = ready.map((sample: any) => {
      const eventId = Number(sample.ticketEventId);
      if (String(sample.featureKey) !== ALLOWED_FEATURE) throw new Error("feature not allowed");
      const numericValue = Number(sample.numericValue);
      const confidence = Number(sample.confidence);
      if (!Number.isFinite(numericValue) || numericValue < 0 || numericValue > 100) throw new Error("invalid numericValue");
      if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) throw new Error("invalid confidence");

      const reference = references.get(eventId);
      const manualReference = reference ? Number(reference.numeric_value) : null;
      const delta = manualReference === null ? null : Number((numericValue - manualReference).toFixed(4));
      const validationStatus = manualReference === null
        ? "no_reference"
        : Math.abs(delta as number) <= 0.1
          ? "matched_reference"
          : "different_from_reference";

      return {
        ticket_event_id: eventId,
        feature_key: ALLOWED_FEATURE,
        observed_at: observedAt,
        numeric_value: numericValue,
        text_value: String(sample.textValue || ""),
        confidence,
        source_name: SOURCE_NAME,
        source_snapshot_key: sourceSnapshotKey,
        validation_status: validationStatus,
        manual_reference_numeric: manualReference,
        delta_numeric: delta,
        metadata: {
          ...(sample.metadata || {}),
          league_id: leagueId,
          season,
          last_completed_round: Number(body.lastCompletedRound || 0),
          rounds_requested: Number(body.roundsRequested || 0),
          matches_used: Number(body.matchesUsed || 0),
          manual_reference_source: reference?.source_name || null,
          manual_reference_observed_at: reference?.observed_at || null,
          github_run_id: claims.run_id || null,
          github_sha: claims.sha || null,
          production_impact: "none_shadow_only",
        },
      };
    });

    await db("sporting_context_shadow_samples?on_conflict=ticket_event_id,feature_key,source_name,source_snapshot_key", {
      method: "POST",
      headers: { Prefer: "resolution=merge-duplicates,return=representation" },
      body: JSON.stringify(rows),
    });

    return json({
      ok: true,
      inserted: rows.length,
      matchedReference: rows.filter((row: any) => row.validation_status === "matched_reference").length,
      differentFromReference: rows.filter((row: any) => row.validation_status === "different_from_reference").length,
      noReference: rows.filter((row: any) => row.validation_status === "no_reference").length,
      repository: claims.repository,
      sha: claims.sha || null,
    });
  } catch (error) {
    return json({ ok: false, error: String(error) }, 500);
  }
});
