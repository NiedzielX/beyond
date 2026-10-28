export type ClubAlias = {
  alias: string;
  club_key: string;
  canonical_name?: string | null;
};

export type LocalTicketEvent = {
  ticket_event_id: number;
  home_team: string;
  away_team: string;
  competition: string;
  kickoff_at: string;
  club_slug?: string | null;
};

export type OddsOutcome = {
  name: string;
  price: number;
};

export type OddsMarket = {
  key: string;
  last_update?: string | null;
  outcomes: OddsOutcome[];
};

export type OddsBookmaker = {
  key: string;
  title?: string | null;
  last_update?: string | null;
  markets: OddsMarket[];
};

export type ProviderOddsEvent = {
  id: string;
  sport_key: string;
  sport_title?: string | null;
  commence_time: string;
  home_team: string;
  away_team: string;
  bookmakers: OddsBookmaker[];
};

export type MatchResult =
  | {
      status: "MATCHED";
      providerEvent: ProviderOddsEvent;
      homeClubKey: string;
      awayClubKey: string;
      kickoffDeltaSeconds: number;
      mappingMethod: "verified_alias_exact+kickoff_tolerance";
    }
  | {
      status: "UNRESOLVED_LOCAL_ALIAS" | "NO_PROVIDER_MATCH" | "AMBIGUOUS_PROVIDER_MATCH";
      reason: string;
    };

export type BookmakerQuote = {
  bookmaker_key: string;
  bookmaker_title: string | null;
  provider_updated_at: string | null;
  home_decimal: number;
  draw_decimal: number;
  away_decimal: number;
  is_in_play: false;
};

const POLISH_TRANSLITERATION: Record<string, string> = {
  "ą": "a",
  "ć": "c",
  "ę": "e",
  "ł": "l",
  "ń": "n",
  "ó": "o",
  "ś": "s",
  "ź": "z",
  "ż": "z",
};

export function normalizeTeamName(value: string): string {
  const lowered = String(value || "").trim().toLowerCase();
  const transliterated = [...lowered]
    .map((char) => POLISH_TRANSLITERATION[char] ?? char)
    .join("");
  return transliterated
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}

export function buildAliasIndex(aliases: ClubAlias[]): Map<string, string> {
  const index = new Map<string, string>();
  for (const row of aliases) {
    const clubKey = String(row.club_key || "").trim();
    if (!clubKey) throw new Error("club alias missing club_key");
    for (const raw of [row.alias, row.canonical_name || ""]) {
      const normalized = normalizeTeamName(raw);
      if (!normalized) continue;
      const existing = index.get(normalized);
      if (existing && existing !== clubKey) {
        throw new Error(`ambiguous normalized alias '${normalized}' => ${existing}/${clubKey}`);
      }
      index.set(normalized, clubKey);
    }
  }
  return index;
}

export function resolveClubKey(name: string, aliasIndex: Map<string, string>): string | null {
  return aliasIndex.get(normalizeTeamName(name)) ?? null;
}

function parseIsoMs(value: string, label: string): number {
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) throw new Error(`invalid ${label}: ${value}`);
  return parsed;
}

function nearestProviderFixtures(
  localKickoff: number,
  providerEvents: ProviderOddsEvent[],
  aliasIndex: Map<string, string>,
  limit = 3,
) {
  return providerEvents
    .map((event) => {
      const providerKickoff = Date.parse(event.commence_time);
      if (!Number.isFinite(providerKickoff)) return null;
      return {
        provider_event_id: event.id,
        commence_time: event.commence_time,
        home_team: event.home_team,
        away_team: event.away_team,
        resolved_home_club_key: resolveClubKey(event.home_team, aliasIndex),
        resolved_away_club_key: resolveClubKey(event.away_team, aliasIndex),
        kickoff_delta_seconds: Math.round((providerKickoff - localKickoff) / 1000),
      };
    })
    .filter((row): row is NonNullable<typeof row> => row !== null)
    .sort((a, b) => Math.abs(a.kickoff_delta_seconds) - Math.abs(b.kickoff_delta_seconds))
    .slice(0, limit);
}

export function matchProviderEvent(
  localEvent: LocalTicketEvent,
  providerEvents: ProviderOddsEvent[],
  aliasIndex: Map<string, string>,
  kickoffToleranceSeconds = 5400,
): MatchResult {
  const localHome = resolveClubKey(localEvent.home_team, aliasIndex);
  const localAway = resolveClubKey(localEvent.away_team, aliasIndex);
  if (!localHome || !localAway) {
    return {
      status: "UNRESOLVED_LOCAL_ALIAS",
      reason: `local aliases unresolved home=${localEvent.home_team} away=${localEvent.away_team}`,
    };
  }

  const localKickoff = parseIsoMs(localEvent.kickoff_at, "local kickoff");
  const candidates: Array<{ event: ProviderOddsEvent; delta: number }> = [];
  for (const providerEvent of providerEvents) {
    const providerHome = resolveClubKey(providerEvent.home_team, aliasIndex);
    const providerAway = resolveClubKey(providerEvent.away_team, aliasIndex);
    if (!providerHome || !providerAway) continue;
    if (providerHome !== localHome || providerAway !== localAway) continue;
    const providerKickoff = parseIsoMs(providerEvent.commence_time, "provider kickoff");
    const delta = Math.round((providerKickoff - localKickoff) / 1000);
    if (Math.abs(delta) <= kickoffToleranceSeconds) {
      candidates.push({ event: providerEvent, delta });
    }
  }

  if (candidates.length === 0) {
    const nearest = nearestProviderFixtures(localKickoff, providerEvents, aliasIndex);
    return {
      status: "NO_PROVIDER_MATCH",
      reason: `no provider event matched ${localHome} vs ${localAway} within ${kickoffToleranceSeconds}s; nearest_provider_fixtures=${JSON.stringify(nearest)}`,
    };
  }
  if (candidates.length > 1) {
    return {
      status: "AMBIGUOUS_PROVIDER_MATCH",
      reason: `multiple provider events matched local event ${localEvent.ticket_event_id}`,
    };
  }

  return {
    status: "MATCHED",
    providerEvent: candidates[0].event,
    homeClubKey: localHome,
    awayClubKey: localAway,
    kickoffDeltaSeconds: candidates[0].delta,
    mappingMethod: "verified_alias_exact+kickoff_tolerance",
  };
}

function validDecimal(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value > 1;
}

function latestH2hMarket(bookmaker: OddsBookmaker): OddsMarket | null {
  const markets = (bookmaker.markets || []).filter((market) => market.key === "h2h");
  if (!markets.length) return null;
  return [...markets].sort((a, b) => {
    const aMs = a.last_update ? Date.parse(a.last_update) : 0;
    const bMs = b.last_update ? Date.parse(b.last_update) : 0;
    return bMs - aMs;
  })[0];
}

export function extractBookmakerQuotes(event: ProviderOddsEvent): BookmakerQuote[] {
  const providerHome = normalizeTeamName(event.home_team);
  const providerAway = normalizeTeamName(event.away_team);
  const quotes: BookmakerQuote[] = [];

  for (const bookmaker of event.bookmakers || []) {
    if (!bookmaker?.key) continue;
    const market = latestH2hMarket(bookmaker);
    if (!market) continue;

    let home: number | null = null;
    let draw: number | null = null;
    let away: number | null = null;
    for (const outcome of market.outcomes || []) {
      if (!validDecimal(outcome?.price)) continue;
      const normalized = normalizeTeamName(outcome.name);
      if (normalized === providerHome) home = outcome.price;
      else if (normalized === providerAway) away = outcome.price;
      else if (normalized === "draw") draw = outcome.price;
    }
    if (home === null || draw === null || away === null) continue;

    quotes.push({
      bookmaker_key: bookmaker.key,
      bookmaker_title: bookmaker.title ? String(bookmaker.title) : null,
      provider_updated_at: market.last_update || bookmaker.last_update || null,
      home_decimal: home,
      draw_decimal: draw,
      away_decimal: away,
      is_in_play: false,
    });
  }

  return quotes.sort((a, b) => a.bookmaker_key.localeCompare(b.bookmaker_key));
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    const object = value as Record<string, unknown>;
    return Object.fromEntries(
      Object.keys(object)
        .sort()
        .map((key) => [key, canonicalize(object[key])]),
    );
  }
  return value;
}

export async function sha256CanonicalJson(value: unknown): Promise<string> {
  const encoded = new TextEncoder().encode(JSON.stringify(canonicalize(value)));
  const digest = await crypto.subtle.digest("SHA-256", encoded);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function parseProviderEvents(payload: unknown): ProviderOddsEvent[] {
  if (!Array.isArray(payload)) throw new Error("provider payload must be an array");
  return payload.map((item, index) => {
    if (!item || typeof item !== "object") throw new Error(`provider event ${index} is not an object`);
    const row = item as Record<string, unknown>;
    if (!row.id || !row.commence_time || !row.home_team || !row.away_team) {
      throw new Error(`provider event ${index} missing identity fields`);
    }
    const bookmakers = Array.isArray(row.bookmakers) ? row.bookmakers as OddsBookmaker[] : [];
    return {
      id: String(row.id),
      sport_key: String(row.sport_key || ""),
      sport_title: row.sport_title ? String(row.sport_title) : null,
      commence_time: String(row.commence_time),
      home_team: String(row.home_team),
      away_team: String(row.away_team),
      bookmakers,
    };
  });
}
