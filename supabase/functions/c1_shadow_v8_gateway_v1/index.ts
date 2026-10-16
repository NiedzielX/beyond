import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-c1-shadow-v8";
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

async function rpc(name: string, body: Record<string, unknown>) {
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("Missing Supabase service environment");
  const response = await fetch(`${url}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`RPC ${name} ${response.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

Deno.serve(async (req: Request) => {
  let claims: any;
  try {
    claims = await authorize(req);
  } catch (error) {
    return json({ ok: false, error: `unauthorized: ${String(error)}` }, 401);
  }

  try {
    if (req.method === "GET") {
      const requestedAt = new Date().toISOString();
      const payload = await rpc("get_c1_shadow_v8_inputs_v1", {
        p_requested_at: requestedAt,
      });
      return json({
        ok: true,
        ...payload,
        repository: claims.repository,
        sha: claims.sha || null,
      });
    }

    if (req.method === "POST") {
      const body = await req.json();
      const predictions = Array.isArray(body?.predictions) ? body.predictions : null;
      const requestedAt = body?.requested_at;
      if (!predictions || !requestedAt) {
        return json({ ok: false, error: "predictions array and requested_at are required" }, 400);
      }
      const result = await rpc("insert_c1_shadow_v8_predictions_v1", {
        p_rows: predictions,
        p_requested_at: requestedAt,
      });
      return json({
        ok: true,
        ...result,
        repository: claims.repository,
        sha: claims.sha || null,
      });
    }

    return json({ ok: false, error: "method not allowed" }, 405);
  } catch (error) {
    return json({
      ok: false,
      version: "c1-shadow-v8-gateway-v1",
      error: String(error),
      repository: claims.repository,
      sha: claims.sha || null,
    }, 500);
  }
});
