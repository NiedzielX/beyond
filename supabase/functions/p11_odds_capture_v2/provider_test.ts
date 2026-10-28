import {
  buildAliasIndex,
  extractBookmakerQuotes,
  matchProviderEvent,
  normalizeTeamName,
  parseProviderEvents,
  sha256CanonicalJson,
  type ClubAlias,
  type LocalTicketEvent,
  type ProviderOddsEvent,
} from "./provider.ts";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function aliases(): ClubAlias[] {
  return [
    { alias: "Lech Poznań", club_key: "lech", canonical_name: "Lech Poznań" },
    { alias: "Legia Warszawa", club_key: "legia", canonical_name: "Legia Warszawa" },
    { alias: "Legia Warsaw", club_key: "legia", canonical_name: "Legia Warszawa" },
    { alias: "Pogoń Szczecin", club_key: "pogonszczecin", canonical_name: "Pogoń Szczecin" },
    { alias: "Radomiak Radom", club_key: "radomiak_radom", canonical_name: "Radomiak Radom" },
  ];
}

function localEvent(): LocalTicketEvent {
  return {
    ticket_event_id: 10,
    home_team: "Pogoń Szczecin",
    away_team: "Radomiak Radom",
    competition: "PKO BP Ekstraklasa",
    kickoff_at: "2026-10-24T15:30:00Z",
    club_slug: "pogonszczecin",
  };
}

function providerEvent(id = "provider-10", kickoff = "2026-10-24T15:30:00Z"): ProviderOddsEvent {
  return {
    id,
    sport_key: "soccer_poland_ekstraklasa",
    commence_time: kickoff,
    home_team: "Pogon Szczecin",
    away_team: "Radomiak Radom",
    bookmakers: [
      {
        key: "book-a",
        title: "Book A",
        markets: [
          {
            key: "h2h",
            last_update: "2026-10-24T10:00:00Z",
            outcomes: [
              { name: "Pogon Szczecin", price: 1.95 },
              { name: "Draw", price: 3.45 },
              { name: "Radomiak Radom", price: 4.2 },
            ],
          },
        ],
      },
      {
        key: "book-b",
        title: "Book B",
        markets: [
          {
            key: "h2h",
            last_update: "2026-10-24T10:01:00Z",
            outcomes: [
              { name: "Radomiak Radom", price: 4.0 },
              { name: "Pogon Szczecin", price: 2.0 },
              { name: "Draw", price: 3.4 },
            ],
          },
        ],
      },
    ],
  };
}

Deno.test("normalization handles Polish diacritics and whitespace", () => {
  assert(normalizeTeamName("  POGOŃ   Szczecin ") === "pogon szczecin", "pogon normalization failed");
  assert(normalizeTeamName("Lech Poznań") === "lech poznan", "poznan normalization failed");
});

Deno.test("verified alias can resolve provider English naming", () => {
  const index = buildAliasIndex(aliases());
  assert(index.get(normalizeTeamName("Legia Warsaw")) === "legia", "Legia Warsaw alias missing");
  assert(index.get(normalizeTeamName("Legia Warszawa")) === "legia", "Legia Warszawa alias missing");
});

Deno.test("alias collisions fail closed", () => {
  let failed = false;
  try {
    buildAliasIndex([
      { alias: "Same Club", club_key: "a" },
      { alias: "Same Club", club_key: "b" },
    ]);
  } catch {
    failed = true;
  }
  assert(failed, "ambiguous normalized alias should fail");
});

Deno.test("provider mapping requires club identity and kickoff tolerance", () => {
  const index = buildAliasIndex(aliases());
  const matched = matchProviderEvent(localEvent(), [providerEvent()], index);
  assert(matched.status === "MATCHED", "expected match");
  if (matched.status === "MATCHED") {
    assert(matched.homeClubKey === "pogonszczecin", "home key mismatch");
    assert(matched.awayClubKey === "radomiak_radom", "away key mismatch");
    assert(matched.kickoffDeltaSeconds === 0, "kickoff delta mismatch");
  }

  const tooFar = matchProviderEvent(
    localEvent(),
    [providerEvent("far", "2026-10-24T18:30:01Z")],
    index,
  );
  assert(tooFar.status === "NO_PROVIDER_MATCH", "kickoff mismatch should fail closed");
  if (tooFar.status === "NO_PROVIDER_MATCH") {
    assert(tooFar.reason.includes("nearest_provider_fixtures="), "nearest provider diagnostics missing");
    assert(tooFar.reason.includes('"provider_event_id":"far"'), "provider event id missing from diagnostics");
    assert(tooFar.reason.includes('"kickoff_delta_seconds":10801'), "kickoff delta missing from diagnostics");
  }
});

Deno.test("multiple provider matches are ambiguous", () => {
  const index = buildAliasIndex(aliases());
  const result = matchProviderEvent(
    localEvent(),
    [
      providerEvent("a", "2026-10-24T15:30:00Z"),
      providerEvent("b", "2026-10-24T15:45:00Z"),
    ],
    index,
  );
  assert(result.status === "AMBIGUOUS_PROVIDER_MATCH", "multiple candidates must fail closed");
});

Deno.test("bookmaker quote extraction preserves raw bookmaker-level 1X2", () => {
  const quotes = extractBookmakerQuotes(providerEvent());
  assert(quotes.length === 2, "expected two complete bookmaker quotes");
  assert(quotes[0].bookmaker_key === "book-a", "quotes must be deterministic by bookmaker key");
  assert(quotes[0].home_decimal === 1.95, "home decimal mismatch");
  assert(quotes[0].draw_decimal === 3.45, "draw decimal mismatch");
  assert(quotes[0].away_decimal === 4.2, "away decimal mismatch");
  assert(quotes.every((quote) => quote.is_in_play === false), "v2 must remain pre-match only");
});

Deno.test("incomplete bookmaker markets are skipped, not guessed", () => {
  const event = providerEvent();
  event.bookmakers.push({
    key: "bad-book",
    title: "Bad Book",
    markets: [{
      key: "h2h",
      outcomes: [
        { name: "Pogon Szczecin", price: 2.0 },
        { name: "Radomiak Radom", price: 4.0 },
      ],
    }],
  });
  const quotes = extractBookmakerQuotes(event);
  assert(quotes.length === 2, "incomplete market must be skipped");
});

Deno.test("canonical payload hash ignores object key ordering", async () => {
  const a = await sha256CanonicalJson({ b: 2, a: { y: 2, x: 1 } });
  const b = await sha256CanonicalJson({ a: { x: 1, y: 2 }, b: 2 });
  assert(a === b, "canonical hash changed with key order");
  assert(/^[0-9a-f]{64}$/.test(a), "invalid sha256 hex");
});

Deno.test("provider parser rejects malformed event identity", () => {
  let failed = false;
  try {
    parseProviderEvents([{ id: "x", home_team: "A" }]);
  } catch {
    failed = true;
  }
  assert(failed, "malformed provider event should fail");
});
