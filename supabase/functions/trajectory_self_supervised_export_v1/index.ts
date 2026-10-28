import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-trajectory-self-supervised";
const REPOSITORY = "NiedzielX/beyond";
const MAIN_REF = "refs/heads/main";
const JWKS = createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));

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

async function dbRpc(name: string) {
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
    body: "{}",
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`DB RPC ${name} ${response.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

Deno.serve(async (req: Request) => {
  let claims: any;
  try {
    claims = await authorize(req);
  } catch (error) {
    return json({ ok: false, error: `unauthorized: ${String(error)}` }, 401);
  }

  if (req.method !== "POST") {
    return json({ ok: false, error: "method not allowed" }, 405);
  }

  try {
    const payload = await dbRpc("export_trajectory_self_supervised_v1");
    if (
      payload?.attendance_labels_used !== false ||
      payload?.structural_prior_used !== false ||
      payload?.production_change !== false
    ) {
      throw new Error("self-supervised evidence guard failed");
    }
    if (Number(payload?.event_count ?? 0) !== 26) {
      throw new Error(`unexpected event_count=${payload?.event_count}`);
    }
    if (Number(payload?.observation_count ?? 0) < 1) {
      throw new Error("empty observation export");
    }

    return json({
      ok: true,
      ...payload,
      repository: claims.repository,
      sha: claims.sha || null,
    });
  } catch (error) {
    return json(
      {
        ok: false,
        version: "trajectory-self-supervised-export-gateway-v1",
        error: String(error),
        repository: claims.repository,
        sha: claims.sha || null,
      },
      500,
    );
  }
});
