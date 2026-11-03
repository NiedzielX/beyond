// PREPARED, NOT DEPLOYED. Separate from frozen attendance gateways.
// Requires verify_jwt=false: GitHub OIDC is validated explicitly below.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const MODEL_VERSION = "daily-inventory-direct-median-v1";
const MODEL_HASH = "1137e257494583374f768622feca343f2dd7d634ef2446198703f8c27fbd9525";
const JWKS = createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { "content-type": "application/json" },
});

async function authorize(req: Request) {
  const auth = req.headers.get("authorization") || "";
  if (!auth.startsWith("Bearer ")) throw new Error("missing bearer token");
  const { payload } = await jwtVerify(auth.slice(7), JWKS, {
    issuer: "https://token.actions.githubusercontent.com",
    audience: "beyond-daily-inventory-path-v1",
  });
  if (payload.repository !== "NiedzielX/beyond" || payload.ref !== "refs/heads/main"
    || payload.workflow_ref !== "NiedzielX/beyond/.github/workflows/daily-inventory-path-shadow-v1.yml@refs/heads/main"
    || typeof payload.sha !== "string" || !/^[0-9a-f]{40}$/.test(payload.sha)) {
    throw new Error("repository/ref/sha not allowed");
  }
  return payload;
}

function credentials() {
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("service environment missing");
  return { url, headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json" } };
}

async function rpc(name: string, body = {}) {
  const { url, headers } = credentials();
  const response = await fetch(`${url}/rest/v1/rpc/${name}`, { method: "POST", headers, body: JSON.stringify(body) });
  if (!response.ok) throw new Error(`controlled RPC failed (${response.status})`);
  return response.json();
}

// Whitelisted raw-source reads only. No caller-chosen table, select or URL.
async function exportSources() {
  const { url, headers } = credentials();
  const asOf = new Date().toISOString();
  async function pages(table: string, fixed: Record<string, string>) {
    const all: any[] = [];
    let last = 0;
    while (true) {
      const params = new URLSearchParams({ ...fixed, id: `gt.${last}`, order: "id.asc", limit: "1000" });
      const response = await fetch(`${url}/rest/v1/${table}?${params}`, { headers });
      if (!response.ok) throw new Error(`source export failed (${response.status})`);
      const batch = await response.json();
      if (!Array.isArray(batch)) throw new Error("invalid source response");
      if (!batch.length) break;
      const next = Number(batch[batch.length - 1].id);
      if (!Number.isSafeInteger(next) || next <= last) throw new Error("source pagination stalled");
      all.push(...batch);
      last = next;
    }
    return all;
  }
  const events = await pages("ticket_events", {
    select: "id,club_slug,provider,kickoff_at,competition,home_team,away_team",
    kickoff_at: "not.is.null",
  });
  const eligible = events.filter((event) => event.club_slug && event.provider
    && Date.parse(event.kickoff_at) >= Date.parse(asOf) - 90 * 86400000
    && Date.parse(event.kickoff_at) <= Date.parse(asOf) + 60 * 86400000);
  const snapshots: any[] = [];
  for (let offset = 0; offset < eligible.length; offset += 100) {
    snapshots.push(...await pages("snapshots", {
      select: "id,ticket_event_id,captured_at,available_total,source,sector_count",
      ticket_event_id: `in.(${eligible.slice(offset, offset + 100).map((event) => event.id).join(",")})`,
      captured_at: `lte.${asOf}`,
    }));
  }
  return { version: "daily-inventory-gateway-source-export-v1", exported_at: asOf,
    events: eligible, snapshots, production_change: false };
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return reply({ error: "method not allowed" }, 405);
  let claims;
  try { claims = await authorize(req); }
  catch { return reply({ error: "unauthorized" }, 401); }
  try {
    const body = await req.json();
    if (body.action === "export") return reply({ ok: true, ...await exportSources() });
    if (body.action === "score") return reply({ ok: true, result: await rpc("score_daily_inventory_path_v1") });
    if (body.action === "feed") return reply({ ok: true, feed: await rpc("daily_inventory_path_feed_v1") });
    if (body.action === "capture") {
      const attempt = body.attempt;
      if (attempt?.artifact?.model_version !== MODEL_VERSION || attempt?.artifact?.model_sha256 !== MODEL_HASH
        || attempt?.production_change !== false || attempt?.issue?.production_change !== false
        || attempt?.issue?.target_values_used !== false || !Array.isArray(attempt?.points)) {
        return reply({ error: "candidate contract rejected" }, 400);
      }
      // Model mathematics are validated by the pinned Python inference/ledger
      // before publishing. SQL independently enforces source lineage and times.
      return reply({ ok: true, result: await rpc("record_daily_inventory_path_v1", {
        p_attempt: attempt, p_github_sha: claims.sha,
      }) });
    }
    return reply({ error: "unsupported action" }, 400);
  } catch {
    // Do not return raw DB/source bodies or credentials to callers.
    return reply({ error: "daily inventory gateway failed closed", production_change: false }, 500);
  }
});
