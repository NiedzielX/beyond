import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-p11-odds-capture";
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

async function health() {
  const url = Deno.env.get("SUPABASE_URL");
  if (!url) throw new Error("missing SUPABASE_URL");
  const secret = supabaseSecret();
  const headers: Record<string, string> = {
    apikey: secret.value,
    "content-type": "application/json",
  };
  if (secret.isLegacyJwt) headers.Authorization = `Bearer ${secret.value}`;
  const response = await fetch(`${url}/rest/v1/rpc/p11_market_odds_capture_health_v2`, {
    method: "POST",
    headers,
    body: "{}",
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`health RPC ${response.status}: ${text.slice(0,1000)}`);
  const parsed = text ? JSON.parse(text) : null;
  if (Array.isArray(parsed) && parsed.length === 1 && parsed[0] && typeof parsed[0] === "object") {
    return (parsed[0] as Record<string, unknown>).p11_market_odds_capture_health_v2 ?? parsed[0];
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
    const payload = await health();
    return json({
      ok: true,
      version: "p11-odds-capture-health-gateway-v2",
      health: payload,
      repository: claims.repository,
      sha: claims.sha || null,
      productionChange: false,
    });
  } catch (error) {
    return json({ ok: false, error: String(error), productionChange: false }, 500);
  }
});
