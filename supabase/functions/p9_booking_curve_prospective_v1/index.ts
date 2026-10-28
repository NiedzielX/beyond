import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-p9-booking-curve-prospective";
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
  const base = Deno.env.get("SUPABASE_URL");
  if (!base) throw new Error("missing SUPABASE_URL");
  const secret = supabaseSecret();
  const headers: Record<string, string> = { apikey: secret.value, "content-type": "application/json" };
  if (secret.isLegacyJwt) headers.Authorization = `Bearer ${secret.value}`;
  const response = await fetch(`${base}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`RPC ${name} ${response.status}: ${text.slice(0, 1200)}`);
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
    if (req.method === "GET") {
      const mode = String(url.searchParams.get("mode") || "summary");
      if (mode === "preflight") {
        const rawDays = Number(url.searchParams.get("days") || "10");
        if (!Number.isInteger(rawDays) || rawDays < 1 || rawDays > 31) {
          return json({ ok: false, error: "days must be an integer between 1 and 31" }, 400);
        }
        const payload = await rpc("p9_prospective_preflight_v1", { p_horizon_days: rawDays });
        const familySupport = await rpc("p9_family_support_preflight_v1", { p_horizon_days: rawDays });
        return json({
          ok: true,
          version: "p9-prospective-gateway-v1",
          mode,
          horizonDays: rawDays,
          payload: { ...payload, family_support: familySupport },
          targetValuesUsed: false,
          productionChange: false,
        });
      }
      if (mode === "inputs") {
        const cutoff = Number(url.searchParams.get("cutoff"));
        if (![24, 48].includes(cutoff)) return json({ ok: false, error: "cutoff must be 24 or 48" }, 400);
        const payload = await rpc("export_p9_prospective_inputs_v1", { p_cutoff_hours: cutoff });
        return json({ ok: true, version: "p9-prospective-gateway-v1", mode, cutoffHours: cutoff, payload, targetValuesUsed: false, productionChange: false });
      }
      if (mode === "incumbents") {
        const cutoff = Number(url.searchParams.get("cutoff"));
        if (![24, 48].includes(cutoff)) return json({ ok: false, error: "cutoff must be 24 or 48" }, 400);
        const payload = await rpc("export_p9_prospective_incumbent_catalog_v1", { p_cutoff_hours: cutoff });
        return json({ ok: true, version: "p9-prospective-gateway-v1", mode, cutoffHours: cutoff, payload, targetValuesUsed: false, productionChange: false });
      }
      if (mode === "reference-outcomes") {
        const payload = await rpc("export_p9_prospective_reference_outcomes_v1");
        return json({ ok: true, version: "p9-prospective-gateway-v1", mode, payload, targetAttendanceIncluded: false, productionChange: false });
      }
      if (mode === "summary") {
        const payload = await rpc("p9_booking_curve_prospective_summary_v1");
        return json({ ok: true, version: "p9-prospective-gateway-v1", mode, payload, productionChange: false });
      }
      return json({ ok: false, error: "unsupported GET mode" }, 400);
    }

    if (req.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);
    const body = await req.json().catch(() => ({}));
    const mode = String(body?.mode || "");
    const githubSha = String(claims.sha || body?.github_sha || "");

    if (mode === "record-attempt") {
      const payload = body?.payload;
      if (!payload || typeof payload !== "object") return json({ ok: false, error: "payload required" }, 400);
      if (
        payload.target_values_used !== false ||
        payload.production_activation_allowed !== false ||
        payload.live_adjustment !== 0 ||
        payload.production_change !== false
      ) {
        return json({ ok: false, error: "target-free / production-safe flags required" }, 400);
      }
      const result = await rpc("record_p9_booking_curve_prospective_attempt_v1", {
        p_payload: payload,
        p_github_sha: githubSha,
      });
      return json({ ok: true, version: "p9-prospective-gateway-v1", mode, result, productionChange: false });
    }

    if (mode === "persist") {
      const payload = body?.payload;
      if (!payload || typeof payload !== "object") return json({ ok: false, error: "payload required" }, 400);
      if (payload.target_values_used !== false || payload.production_change !== false) {
        return json({ ok: false, error: "target-free / production-safe flags required" }, 400);
      }
      const result = await rpc("insert_p9_booking_curve_prospective_predictions_v1", {
        p_payload: payload,
        p_github_sha: githubSha,
      });
      return json({ ok: true, version: "p9-prospective-gateway-v1", mode, result, productionChange: false });
    }

    if (mode === "score") {
      const result = await rpc("score_p9_booking_curve_prospective_completed_v1");
      const summary = await rpc("p9_booking_curve_prospective_summary_v1");
      return json({ ok: true, version: "p9-prospective-gateway-v1", mode, result, summary, productionChange: false });
    }

    return json({ ok: false, error: "unsupported POST mode" }, 400);
  } catch (error) {
    return json({
      ok: false,
      version: "p9-prospective-gateway-v1",
      error: String(error),
      repository: claims.repository,
      sha: claims.sha || null,
      productionChange: false,
    }, 500);
  }
});
