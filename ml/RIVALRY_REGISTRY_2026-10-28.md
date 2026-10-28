# Verified rivalry registry — 2026-10-28 update

## Added relation

`Cracovia <-> Wisła Kraków` — **Derby Krakowa**

Evidence:

- official Cracovia communication describes the 6 November 2026 Wisła Kraków–Cracovia fixture as the long-awaited Kraków derby;
- current official Wisła Kraków communication independently refers to the upcoming Cracovia match as `derby Krakowa`.

Primary source persisted in the registry:

`https://www.cracovia.pl/posts/poznalismy-date-meczu-z-wisla-krakow/6443`

## Live propagation

The relation was propagated forward-only through the existing verified-rivalry context path.

Future event **448 Wisła Kraków–Cracovia** now has:

- `feature_key = sport.rivalry_opponent`
- `numeric_value = 1`
- `rivalry_type = Derby Krakowa`
- confidence `0.99`
- `production_impact = none_context_research_only`

The observation was created before the match and before any attendance outcome exists.

## Guardrails

- Registry presence means a rivalry is verified.
- Registry absence remains **unknown**, never `false`.
- The rivalry flag is not an attendance multiplier by itself.
- No P50 / P10 / P90 forecast is changed by this seed.
- No production promotion occurs.
- No historical match is rewritten or backfilled from the future observation.

This creates clean forward evidence for a materially different context hypothesis without retuning previously rejected match-stakes, timing, Ticketing or Hype candidates.
