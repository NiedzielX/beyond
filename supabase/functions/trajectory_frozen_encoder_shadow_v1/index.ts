import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-trajectory-shadow";
const REPOSITORY = "NiedzielX/beyond";
const MAIN_REF = "refs/heads/main";
const MODEL_VERSION = "trajectory-frozen-encoder-ridge-ratio-head-v1";
const PRECOMMIT_ID = MODEL_VERSION;
const DATASET_VERSION = "trajectory-frozen-encoder-shadow-input-v1";
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

async function rpc(name: string, body: unknown = {}) {
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
  if (!response.ok) throw new Error(`DB RPC ${name} ${response.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

function assertCandidate(payload: any) {
  if (payload?.model_version !== MODEL_VERSION) throw new Error("model_version mismatch");
  if (payload?.precommit_id !== PRECOMMIT_ID) throw new Error("precommit_id mismatch");
  if (payload?.dataset_version !== DATASET_VERSION) throw new Error("dataset_version mismatch");
  if (payload?.target_values_used !== false) throw new Error("target_values_used must be false");
  if (payload?.production_change !== false) throw new Error("production_change must be false");
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
    const body = await req.json();
    const action = String(body?.action || "");

    if (action === "due") {
      const payload = await rpc("get_trajectory_frozen_encoder_shadow_due_v1");
      if (payload?.target_values_used !== false || payload?.production_change !== false) {
        throw new Error("due-target evidence guard failed");
      }
      return json({
        ok: true,
        ...payload,
        repository: claims.repository,
        sha: claims.sha || null,
      });
    }

    if (action === "attempt") {
      assertCandidate(body?.payload);
      const result = await rpc("record_daily_trajectory_attempt_v1", {
        p_payload: body.payload,
        p_github_sha: claims.sha || null,
      });
      return json({ ok: true, result, repository: claims.repository, sha: claims.sha || null });
    }

    if (action === "prediction") {
      assertCandidate(body?.payload);
      const result = await rpc("insert_daily_trajectory_prediction_v1", {
        p_payload: body.payload,
        p_github_sha: claims.sha || null,
      });
      return json({ ok: true, result, repository: claims.repository, sha: claims.sha || null });
    }

    if (action === "score") {
      const result = await rpc("score_daily_trajectory_completed_v1");
      return json({ ok: true, result, repository: claims.repository, sha: claims.sha || null });
    }

    throw new Error("unsupported action");
  } catch (error) {
    return json(
      {
        ok: false,
        version: "trajectory-frozen-encoder-shadow-gateway-v1",
        error: String(error),
        repository: claims.repository,
        sha: claims.sha || null,
      },
      500,
    );
  }
});
