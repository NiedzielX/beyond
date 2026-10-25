import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-p7-long168-prospective";
const REPOSITORY = "NiedzielX/beyond";
const MAIN_REF = "refs/heads/main";
const JWKS = createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

async function authorize(req: Request) {
  const auth = req.headers.get("authorization") || "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!token) throw new Error("missing bearer token");
  const { payload } = await jwtVerify(token, JWKS, { issuer: ISSUER, audience: AUDIENCE });
  if (payload.repository !== REPOSITORY) throw new Error("repository not allowed");
  if (payload.ref !== MAIN_REF) throw new Error("ref not allowed");
  return payload;
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

async function rpc(name: string, body: Record<string, unknown> = {}) {
  const url = Deno.env.get("SUPABASE_URL");
  if (!url) throw new Error("missing SUPABASE_URL");
  const secret = supabaseSecret();
  const headers: Record<string, string> = {
    apikey: secret.value,
    "content-type": "application/json",
  };
  if (secret.isLegacyJwt) headers.Authorization = `Bearer ${secret.value}`;
  const response = await fetch(`${url}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`RPC ${name} ${response.status}: ${text.slice(0, 1000)}`);
  const parsed = text ? JSON.parse(text) : null;
  if (Array.isArray(parsed) && parsed.length === 1 && parsed[0] && typeof parsed[0] === "object") {
    const row = parsed[0] as Record<string, unknown>;
    return row[name] ?? row.payload ?? parsed[0];
  }
  return parsed;
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
    if (req.method === "GET" && url.searchParams.get("mode") === "bundle") {
      const [trainingLong168, trainingEvents, attendance, sporting, aliases, prospective, summary] = await Promise.all([
        rpc("export_d2_long_horizon_168_rows_v1"),
        rpc("export_c1_alpha_v7_events_v1"),
        rpc("export_c1_alpha_v7_attendance_v1"),
        rpc("export_c1_alpha_v7_sporting_v1"),
        rpc("export_c1_alpha_v7_aliases_v1"),
        rpc("export_p7_long168_prospective_inputs_v1"),
        rpc("p7_long168_prospective_summary_v1"),
      ]);
      return json({
        ok: true,
        version: "p7-long168-prospective-bundle-v1",
        generatedAt: new Date().toISOString(),
        repository: claims.repository,
        sha: claims.sha || null,
        trainingLong168,
        trainingEvents,
        attendance,
        sporting,
        aliases,
        prospective,
        summary,
        prospectiveTargetValuesUsed: false,
        productionActivationAllowed: false,
        liveAdjustment: 0,
        productionChange: false,
      });
    }

    if (req.method === "GET" && url.searchParams.get("mode") === "summary") {
      const summary = await rpc("p7_long168_prospective_summary_v1");
      const scores = await rpc("export_p7_long168_prospective_scores_v1");
      return json({ ok: true, summary, scores, productionChange: false });
    }

    if (req.method === "POST") {
      const body = await req.json().catch(() => ({}));
      const mode = String(body?.mode || "");
      if (mode === "persist") {
        const payload = body?.payload;
        if (!payload || typeof payload !== "object") return json({ ok: false, error: "payload required" }, 400);
        if (payload.target_values_used !== false || payload.production_change !== false) {
          return json({ ok: false, error: "target-free / production-safe flags required" }, 400);
        }
        const result = await rpc("insert_p7_long168_prospective_predictions_v1", { p_payload: payload });
        return json({ ok: true, result, productionChange: false });
      }
      if (mode === "score") {
        const result = await rpc("score_p7_long168_prospective_completed_events_v1");
        const summary = await rpc("p7_long168_prospective_summary_v1");
        return json({ ok: true, result, summary, productionChange: false });
      }
      return json({ ok: false, error: "unsupported POST mode" }, 400);
    }

    return json({ ok: false, error: "method/mode not allowed" }, 405);
  } catch (error) {
    return json({
      ok: false,
      version: "p7-long168-prospective-gateway-v1",
      error: String(error),
      repository: claims.repository,
      sha: claims.sha || null,
      productionChange: false,
    }, 500);
  }
});
