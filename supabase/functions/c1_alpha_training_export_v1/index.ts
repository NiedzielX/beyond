import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-c1-alpha-training";
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
  const response = await fetch(`${url}/rest/v1/${path}`, {
    ...options,
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`DB ${path} ${response.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

const ROUTES: Record<string, string> = {
  "v1": "export_c1_alpha_training_payload_v1",
  "v2": "export_c1_alpha_training_payload_v2",
  "event-v1": "export_c1_alpha_event_training_payload_v1",
  "v7-final24": "export_c1_alpha_v7_final24_rows_v1",
  "v7-events": "export_c1_alpha_v7_events_v1",
  "v7-attendance": "export_c1_alpha_v7_attendance_v1",
  "v7-sporting": "export_c1_alpha_v7_sporting_v1",
  "v7-aliases": "export_c1_alpha_v7_aliases_v1",
  "v7-hybrid": "export_c1_alpha_v7_hybrid_v1",
  "v8-long168": "export_d2_long_horizon_168_rows_v1",
  "v8-capacity": "export_d2_capacity_registry_v1",
  "d2-readiness": "export_d2_prospective_readiness_v1",
};

Deno.serve(async (req: Request) => {
  let claims: any;
  try {
    claims = await authorize(req);
  } catch (error) {
    return json({ ok: false, error: `unauthorized: ${String(error)}` }, 401);
  }

  if (req.method !== "GET") {
    return json({ ok: false, error: "method not allowed" }, 405);
  }

  try {
    const url = new URL(req.url);
    const requestedVersion = url.searchParams.get("version") || "v1";
    const rpcName = ROUTES[requestedVersion];
    if (!rpcName) throw new Error(`unsupported export version: ${requestedVersion}`);

    const raw = await db(`rpc/${rpcName}`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    const payload = Array.isArray(raw)
      ? (raw[0]?.[rpcName] ?? raw[0]?.payload ?? raw[0])
      : raw;

    if (requestedVersion === "v7-attendance" || requestedVersion === "v7-sporting" || requestedVersion === "v7-aliases" || requestedVersion === "v7-hybrid" || requestedVersion === "v8-capacity") {
      const rowCount = Number(payload?.rowCount ?? 0);
      if (rowCount < 1) throw new Error(`invalid split/support payload rows=${rowCount}`);
    } else {
      const eventCount = Number(payload?.eventCount ?? 0);
      if (eventCount < 2) throw new Error(`invalid C1 training payload events=${eventCount}`);
    }

    if (requestedVersion === "v1" || requestedVersion === "v2" || requestedVersion === "v7-final24" || requestedVersion === "v8-long168") {
      const eventCount = Number(payload?.eventCount ?? 0);
      const liveRowCount = Number(payload?.liveRowCount ?? 0);
      if (liveRowCount < eventCount) {
        throw new Error(`invalid C1 training payload events=${eventCount} liveRows=${liveRowCount}`);
      }
    }

    if (requestedVersion === "v2" || requestedVersion === "event-v1" || requestedVersion === "v7-hybrid") {
      const hybridRows = Array.isArray(payload?.ticketingChallengerRows)
        ? payload.ticketingChallengerRows.length
        : 0;
      if (hybridRows < 1) throw new Error("C1 payload missing ticketing challenger rows");
    }

    return json({
      ok: true,
      ...payload,
      repository: claims.repository,
      sha: claims.sha || null,
    });
  } catch (error) {
    return json({
      ok: false,
      version: "c1-alpha-training-export-gateway-v8-long72-support",
      error: String(error),
      repository: claims.repository,
      sha: claims.sha || null,
    }, 500);
  }
});