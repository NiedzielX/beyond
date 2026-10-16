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
    const raw = await db("rpc/export_c1_alpha_training_payload_v1", {
      method: "POST",
      body: JSON.stringify({}),
    });
    const payload = Array.isArray(raw)
      ? (raw[0]?.export_c1_alpha_training_payload_v1 ?? raw[0]?.payload ?? raw[0])
      : raw;

    const eventCount = Number(payload?.eventCount ?? 0);
    const liveRowCount = Number(payload?.liveRowCount ?? 0);
    if (eventCount < 2 || liveRowCount < eventCount) {
      throw new Error(`invalid C1 training payload events=${eventCount} liveRows=${liveRowCount}`);
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
      version: "c1-alpha-training-export-gateway-v1",
      error: String(error),
      repository: claims.repository,
      sha: claims.sha || null,
    }, 500);
  }
});
