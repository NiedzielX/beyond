import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";
import {
  buildAliasIndex,
  extractBookmakerQuotes,
  matchProviderEvent,
  parseProviderEvents,
  sha256CanonicalJson,
  type ClubAlias,
  type LocalTicketEvent,
} from "./provider.ts";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-p11-odds-capture";
const REPOSITORY = "NiedzielX/beyond";
const MAIN_REF = "refs/heads/main";
const PROVIDER = "the-odds-api-v4";
const SPORT_KEY = "soccer_poland_ekstraklasa";
const PROVIDER_BASE = `https://api.the-odds-api.com/v4/sports/${SPORT_KEY}/odds`;
const SOURCE_URL = PROVIDER_BASE;
const KICKOFF_TOLERANCE_SECONDS = 5400;
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

async function db(path: string, options: RequestInit = {}) {
  const url = Deno.env.get("SUPABASE_URL");
  if (!url) throw new Error("missing SUPABASE_URL");
  const secret = supabaseSecret();
  const headers: Record<string, string> = {
    apikey: secret.value,
    "Content-Type": "application/json",
    Prefer: "return=representation",
    ...((options.headers || {}) as Record<string, string>),
  };
  if (secret.isLegacyJwt) headers.Authorization = `Bearer ${secret.value}`;

  const response = await fetch(`${url}/rest/v1/${path}`, {
    ...options,
    headers,
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`DB ${path} ${response.status}: ${text.slice(0, 1000)}`);
  }
  return text ? JSON.parse(text) : null;
}

async function rpc(name: string, body: Record<string, unknown>) {
  return await db(`rpc/${name}`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

function unwrapJsonbRpc(raw: unknown, functionName: string): any {
  if (Array.isArray(raw)) {
    if (raw.length === 1 && raw[0] && typeof raw[0] === "object") {
      const first = raw[0] as Record<string, unknown>;
      return first[functionName] ?? first.payload ?? first;
    }
    return raw;
  }
  return raw;
}

function requireProviderApiKey(): string {
  const key = Deno.env.get("THE_ODDS_API_KEY");
  if (!key) throw new Error("THE_ODDS_API_KEY_NOT_CONFIGURED");
  return key;
}

function providerUrl(apiKey: string, events: LocalTicketEvent[]): URL {
  const kickoffs = events.map((event) => Date.parse(event.kickoff_at)).filter(Number.isFinite);
  if (!kickoffs.length) throw new Error("no valid local kickoff times");
  const min = new Date(Math.min(...kickoffs) - 2 * 3600_000).toISOString();
  const max = new Date(Math.max(...kickoffs) + 2 * 3600_000).toISOString();
  const url = new URL(PROVIDER_BASE);
  url.searchParams.set("apiKey", apiKey);
  url.searchParams.set("regions", "eu");
  url.searchParams.set("markets", "h2h");
  url.searchParams.set("oddsFormat", "decimal");
  url.searchParams.set("dateFormat", "iso");
  url.searchParams.set("commenceTimeFrom", min);
  url.searchParams.set("commenceTimeTo", max);
  return url;
}

async function fetchProviderEvents(apiKey: string, events: LocalTicketEvent[]) {
  const response = await fetch(providerUrl(apiKey, events), {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`ODDS_PROVIDER_HTTP_${response.status}: ${text.slice(0, 500)}`);
  }
  let payload: unknown;
  try {
    payload = JSON.parse(text);
  } catch {
    throw new Error("ODDS_PROVIDER_INVALID_JSON");
  }
  return {
    events: parseProviderEvents(payload),
    quota: {
      remaining: response.headers.get("x-requests-remaining"),
      used: response.headers.get("x-requests-used"),
      last: response.headers.get("x-requests-last"),
    },
  };
}

Deno.serve(async (req: Request) => {
  let claims: any;
  try {
    claims = await authorize(req);
  } catch (error) {
    return json({ ok: false, error: `unauthorized: ${String(error)}` }, 401);
  }

  if (req.method === "GET") {
    const mode = new URL(req.url).searchParams.get("mode");
    if (mode !== "config") return json({ ok: false, error: "method not allowed" }, 405);
    return json({
      ok: true,
      version: "p11-odds-capture-v2",
      provider: PROVIDER,
      sportKey: SPORT_KEY,
      configured: Boolean(Deno.env.get("THE_ODDS_API_KEY")),
      captureEnabled: false,
      note: "manual capture only until provider secret is configured and the workflow is explicitly enabled",
      repository: claims.repository,
      sha: claims.sha || null,
      productionChange: false,
    });
  }

  if (req.method !== "POST") {
    return json({ ok: false, error: "method not allowed" }, 405);
  }

  try {
    const apiKey = requireProviderApiKey();
    const rawInputs = await rpc("p11_market_capture_inputs_v2", { p_horizon_days: 14 });
    const inputs = unwrapJsonbRpc(rawInputs, "p11_market_capture_inputs_v2") || {};
    const localEvents = Array.isArray(inputs.events) ? inputs.events as LocalTicketEvent[] : [];
    const aliases = Array.isArray(inputs.aliases) ? inputs.aliases as ClubAlias[] : [];
    if (!localEvents.length) {
      return json({
        ok: true,
        version: "p11-odds-capture-v2",
        status: "NO_LOCAL_EKSTRAKLASA_EVENTS_IN_WINDOW",
        provider: PROVIDER,
        insertedQuotes: 0,
        productionChange: false,
      });
    }
    if (!aliases.length) throw new Error("no verified club aliases returned");

    const aliasIndex = buildAliasIndex(aliases);
    const provider = await fetchProviderEvents(apiKey, localEvents);
    const providerEvents = provider.events.filter((event) => event.sport_key === SPORT_KEY);
    const capturedAt = new Date().toISOString();
    const capturedMs = Date.parse(capturedAt);

    let insertedQuotes = 0;
    let matchedEvents = 0;
    const eventResults: Array<Record<string, unknown>> = [];

    for (const localEvent of localEvents) {
      const match = matchProviderEvent(
        localEvent,
        providerEvents,
        aliasIndex,
        KICKOFF_TOLERANCE_SECONDS,
      );
      if (match.status !== "MATCHED") {
        eventResults.push({
          ticketEventId: localEvent.ticket_event_id,
          status: match.status,
          reason: match.reason,
        });
        continue;
      }

      const providerCommenceMs = Date.parse(match.providerEvent.commence_time);
      if (!Number.isFinite(providerCommenceMs) || providerCommenceMs <= capturedMs) {
        eventResults.push({
          ticketEventId: localEvent.ticket_event_id,
          providerEventId: match.providerEvent.id,
          status: "SKIPPED_IN_PLAY_OR_STARTED",
        });
        continue;
      }

      const quotes = extractBookmakerQuotes(match.providerEvent);
      if (!quotes.length) {
        eventResults.push({
          ticketEventId: localEvent.ticket_event_id,
          providerEventId: match.providerEvent.id,
          status: "NO_COMPLETE_1X2_BOOKMAKER_QUOTES",
        });
        continue;
      }

      const captureBatchId = crypto.randomUUID();
      const payloadHash = await sha256CanonicalJson(match.providerEvent);
      const capturePayload = {
        ticket_event_id: localEvent.ticket_event_id,
        provider: PROVIDER,
        provider_event_id: match.providerEvent.id,
        capture_batch_id: captureBatchId,
        captured_at: capturedAt,
        provider_commence_at: match.providerEvent.commence_time,
        source_url: SOURCE_URL,
        source_payload_hash: payloadHash,
        mapping_method: match.mappingMethod,
        home_club_key: match.homeClubKey,
        away_club_key: match.awayClubKey,
        quotes,
      };

      try {
        const rawInsert = await rpc("insert_p11_market_odds_capture_v2", {
          p_capture: capturePayload,
        });
        const inserted = unwrapJsonbRpc(rawInsert, "insert_p11_market_odds_capture_v2") || {};
        const count = Number(inserted.inserted_quotes ?? 0);
        insertedQuotes += Number.isFinite(count) ? count : 0;
        matchedEvents += 1;
        eventResults.push({
          ticketEventId: localEvent.ticket_event_id,
          providerEventId: match.providerEvent.id,
          status: "CAPTURED",
          bookmakerQuotes: quotes.length,
          insertedQuotes: count,
          captureBatchId,
          kickoffDeltaSeconds: match.kickoffDeltaSeconds,
        });
      } catch (error) {
        eventResults.push({
          ticketEventId: localEvent.ticket_event_id,
          providerEventId: match.providerEvent.id,
          status: "DB_INSERT_REJECTED",
          error: String(error),
        });
      }
    }

    return json({
      ok: true,
      version: "p11-odds-capture-v2",
      status: "CAPTURE_COMPLETE",
      provider: PROVIDER,
      sportKey: SPORT_KEY,
      capturedAt,
      localEvents: localEvents.length,
      providerEvents: providerEvents.length,
      matchedEvents,
      insertedQuotes,
      eventResults,
      quota: provider.quota,
      repository: claims.repository,
      sha: claims.sha || null,
      githubRunId: claims.run_id || null,
      targetValuesUsed: false,
      productionChange: false,
    });
  } catch (error) {
    const message = String(error);
    const notConfigured = message.includes("THE_ODDS_API_KEY_NOT_CONFIGURED");
    return json({
      ok: false,
      version: "p11-odds-capture-v2",
      status: notConfigured ? "PROVIDER_SECRET_NOT_CONFIGURED" : "CAPTURE_FAILED",
      error: message,
      repository: claims.repository,
      sha: claims.sha || null,
      targetValuesUsed: false,
      productionChange: false,
    }, notConfigured ? 503 : 500);
  }
});
