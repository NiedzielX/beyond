import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-structural-prior-materializer";
const REPOSITORY = "NiedzielX/beyond";
const MAIN_REF = "refs/heads/main";
const JWKS = createRemoteJWKSet(
  new URL("https://token.actions.githubusercontent.com/.well-known/jwks"),
);

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });

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

function parseRecentIso(value: string, label: string, nowMs: number, maxAgeMs: number) {
  const time = Date.parse(value);
  if (!Number.isFinite(time)) throw new Error(`invalid ${label}`);
  if (time > nowMs + 5 * 60_000) throw new Error(`${label} is in the future`);
  if (time < nowMs - maxAgeMs) throw new Error(`${label} is too old`);
  return time;
}

function inFilter(values: string[]): string {
  return `in.(${values.map((value) => `"${value.replaceAll('"', '\\"')}"`).join(",")})`;
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
    const mode = url.searchParams.get("mode") || "";

    if (req.method === "GET" && mode === "training") {
      // Return one JSONB payload from Postgres so the Data API's row limit
      // cannot truncate the canonical 1,530-match training set.
      const raw = await db("rpc/export_historical_runtime_payload_v1", {
        method: "POST",
        body: JSON.stringify({}),
      });
      const payload = Array.isArray(raw)
        ? (raw[0]?.export_historical_runtime_payload_v1 ?? raw[0]?.payload ?? raw[0])
        : raw;
      const rows = Array.isArray(payload?.rows) ? payload.rows : [];
      const declaredCount = Number(payload?.rowCount ?? payload?.rowcount ?? 0);
      const matchKeys = new Set(rows.map((row: any) => String(row.match_key || "")));
      if (declaredCount !== 1530 || rows.length !== 1530 || matchKeys.size !== 1530) {
        throw new Error(
          `canonical training export expected 1530 unique rows, got declared=${declaredCount} rows=${rows.length} unique=${matchKeys.size}`,
        );
      }
      return json({
        ok: true,
        version: "structural-prior-training-export-v1",
        rowCount: rows.length,
        rows,
        repository: claims.repository,
        sha: claims.sha || null,
      });
    }

    if (req.method === "GET" && mode === "due") {
      const requestedAt = new Date().toISOString();
      const events = await db("rpc/get_due_early_structural_prior_inputs_v1", {
        method: "POST",
        body: JSON.stringify({
          p_requested_at: requestedAt,
          p_include_ready_event_id: null,
        }),
      }) || [];
      const aliases = await db("rpc/get_structural_prior_club_aliases_v1", {
        method: "POST",
        body: JSON.stringify({}),
      }) || [];

      const seasons = [...new Set(events.map((row: any) => row.season).filter(Boolean))] as string[];
      const sourceSeasons = seasons.map((value) => value.replace("/", "-"));
      let attendance: any[] = [];
      let sportingMatches: any[] = [];
      if (seasons.length) {
        attendance = await db(
          `ml_home_attendance_history_v2?season=${encodeURIComponent(inFilter(seasons))}` +
            `&competition_key=eq.ekstraklasa` +
            `&select=club_slug,kickoff_at,actual_attendance,season,source_name,source_url` +
            `&order=kickoff_at.asc`,
          { method: "GET" },
        ) || [];
        sportingMatches = await db(
          `sporting_league_matches_shadow?season=${encodeURIComponent(inFilter(sourceSeasons))}` +
            `&select=season,round_number,event_date,home_team,away_team,home_score,away_score,completed,match_status,fetched_at` +
            `&order=event_date.asc`,
          { method: "GET" },
        ) || [];
      }

      return json({
        ok: true,
        version: "structural-prior-materializer-input-v1",
        requestedAt,
        eventCount: events.length,
        events,
        aliases,
        attendance,
        sportingMatches,
        repository: claims.repository,
        sha: claims.sha || null,
      });
    }

    if (req.method !== "POST") {
      return json({ ok: false, error: "method not allowed" }, 405);
    }

    const body = await req.json();
    const predictions = Array.isArray(body.predictions) ? body.predictions : [];
    if (!predictions.length || predictions.length > 20) {
      return json({ ok: false, error: "predictions must contain 1..20 rows" }, 400);
    }

    const nowMs = Date.now();
    const inserted = [];
    for (const prediction of predictions) {
      const generatedAt = String(prediction.generated_at || "");
      parseRecentIso(generatedAt, "generated_at", nowMs, 30 * 60_000);
      const horizon = String(prediction.horizon || "");
      if (horizon !== "T-30" && horizon !== "T-14") {
        throw new Error(`unsupported horizon ${horizon}`);
      }
      const p50 = Number(prediction.p50);
      const capacity = Number(prediction.stadium_capacity);
      if (!Number.isFinite(p50) || !Number.isInteger(capacity) || capacity <= 0 || p50 < 0 || p50 > capacity) {
        throw new Error("invalid p50/capacity");
      }
      const id = await db("rpc/insert_structural_prior_forecast_v1", {
        method: "POST",
        body: JSON.stringify({ p_forecast: prediction }),
      });
      inserted.push({
        ticketEventId: Number(prediction.ticket_event_id),
        horizon,
        structuralPriorId: Number(id),
        p50,
      });
    }

    return json({
      ok: true,
      version: "structural-prior-materializer-gateway-v1",
      insertedCount: inserted.length,
      inserted,
      repository: claims.repository,
      sha: claims.sha || null,
      githubRunId: claims.run_id || null,
    });
  } catch (error) {
    return json({
      ok: false,
      version: "structural-prior-materializer-gateway-v1",
      error: String(error),
      repository: claims.repository,
      sha: claims.sha || null,
    }, 500);
  }
});
