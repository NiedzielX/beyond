import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-p9a-booking-curve";
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

function supabaseSecret(): { value: string; isLegacyJwt: boolean } {
  const secretJson = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (secretJson) {
    try {
      const parsed = JSON.parse(secretJson);
      const value = String(parsed?.default || "");
      if (value) return { value, isLegacyJwt: false };
    } catch {
      throw new Error("invalid SUPABASE_SECRET_KEYS JSON");
    }
  }
  const legacy = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (legacy) return { value: legacy, isLegacyJwt: true };
  throw new Error("missing Supabase backend secret");
}

async function rpc(name: string, body: Record<string, unknown>) {
  const base = Deno.env.get("SUPABASE_URL");
  if (!base) throw new Error("missing SUPABASE_URL");
  const secret = supabaseSecret();
  const headers: Record<string, string> = {
    apikey: secret.value,
    "Content-Type": "application/json",
  };
  if (secret.isLegacyJwt) headers.Authorization = `Bearer ${secret.value}`;
  const response = await fetch(`${base}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`RPC ${name} ${response.status}: ${text.slice(0, 1000)}`);
  }
  return text ? JSON.parse(text) : null;
}

Deno.serve(async (req: Request) => {
  let claims: any;
  try {
    claims = await authorize(req);
  } catch (error) {
    return json({ ok: false, error: `unauthorized: ${String(error)}` }, 401);
  }

  if (req.method !== "GET") return json({ ok: false, error: "method not allowed" }, 405);

  const url = new URL(req.url);
  const version = url.searchParams.get("version");
  const cutoff = Number(url.searchParams.get("cutoff") || "24");
  if (version !== "p9a-booking-curve-inputs-v1") {
    return json({ ok: false, error: "unsupported version" }, 400);
  }
  if (![24, 48].includes(cutoff)) {
    return json({ ok: false, error: "cutoff must be 24 or 48" }, 400);
  }

  try {
    const payload = await rpc("export_p9a_booking_curve_inputs_v1", {
      p_cutoff_hours: cutoff,
    });
    if (!payload || typeof payload !== "object") {
      throw new Error("P9a input RPC returned invalid payload");
    }
    const p = payload as Record<string, unknown>;
    if (p.target_values_used !== false || p.production_change !== false) {
      throw new Error("P9a input RPC violated target-free/production-neutral contract");
    }
    if (p.post_cutoff_target_snapshots_exported !== false) {
      throw new Error("P9a input RPC did not certify post-cutoff target exclusion");
    }
    return json({
      ok: true,
      exportVersion: version,
      cutoffHours: cutoff,
      targetFieldsIncluded: false,
      labelsIncluded: false,
      targetValuesUsed: false,
      productionChange: false,
      repository: claims.repository,
      sha: claims.sha || null,
      payload,
    });
  } catch (error) {
    return json({
      ok: false,
      exportVersion: version,
      cutoffHours: cutoff,
      error: String(error),
      targetValuesUsed: false,
      productionChange: false,
    }, 500);
  }
});
