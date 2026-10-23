# Beyond Ticketing — Near-Term ML Trigger Timeline

Last updated: **2026-10-23**

Status: **OPERATING TIMELINE / DATA-DEPENDENT**

This document adds expected timing to the already frozen P4a and P7 research contracts. It does not change any scientific gate or model configuration.

## Current state

- P7 Long168: `8/9` independent events with valid observations >72h.
- P4a previous-home spacing: `5` independent READY events / `0` genuine labels.
- Long72 prospective: `0` genuine scored events.
- P4b next-opponent attractiveness: `0 READY`.
- Production: `live_adjustment = 0`.

## Expected first trigger — P7 Long168

Candidate ninth event:

- event `6` — Lech Poznań vs Wisła Kraków;
- kickoff: `2026-10-31 16:30 UTC`;
- first captured snapshot: `2026-10-01 10:02:27 UTC`;
- observation history already exceeds the Long168 requirement;
- the event enters the `<=168h` Long168 window at approximately `2026-10-24 16:30 UTC` / `18:30 Europe/Warsaw`.

Expected operational consequence:

> The first successful Long168 collection after approximately **24 October 2026, 18:30 Europe/Warsaw** should be able to raise P7 from `8/9` to `9/9`, assuming normal collection and PIT validation.

When readiness confirms `9/9`, execute the already-frozen P7 sequence:

`readiness -> explicit execute -> freeze exact identities + SHA -> verify T-7 replay -> attach labels -> strict forward folds -> fixed tournament -> paired event-block uncertainty -> research decision`.

Do not execute based only on the clock; always confirm `public.ml_research_readiness_v1()` first.

## Expected first genuine Long72 score

Nearest completed-event candidate:

- event `10` — Pogoń Szczecin vs Radomiak Radom;
- kickoff: `2026-10-24 15:30 UTC` / `17:30 Europe/Warsaw`.

Outcome-history sync and prospective scoring are already scheduled hourly.

Expected operational consequence:

> If the attendance outcome is ingested normally after the match, the first genuine Long72 score may appear during the evening of **24 October 2026**, likely in an hourly sync/scoring cycle after completion.

This is an evidence-review trigger only. Do not retune the frozen Long72 package from the first score.

## Expected P4a labels

Current P4a READY events:

- `10` Pogoń Szczecin vs Radomiak Radom — 24 Oct;
- `16` Wisła Kraków vs Raków Częstochowa — 24 Oct;
- `23` Śląsk Wrocław vs Wieczysta Kraków — 25 Oct;
- `21` Jagiellonia Białystok vs Wisła Płock — 25 Oct;
- `22` Legia Warszawa vs Lech Poznań — 25 Oct.

If outcome ingestion works normally, genuine labels for these five events should begin appearing after their respective matches on **24–25 October 2026**.

P4a model evaluation still remains blocked until the frozen gate is satisfied:

- `>=9` labeled independent events; and
- `>=3` distinct labeled `previous_home_match_days` values.

Even if all current five events become labeled, P4a will be only `5/9` and must remain blocked.

## Next known event after current weekend

- event `6` — Lech Poznań vs Wisła Kraków — `31 October 2026`.

If it becomes P4a READY and later labeled, it can increase the P4a labeled set, but it still cannot by itself satisfy the `9`-event research-start gate.

## Operating rule

Expected timestamps are planning estimates, not execution conditions.

Every real experiment starts only from the canonical readiness state:

`public.ml_research_readiness_v1()`

No gate is lowered and no model is opened early because a planned time has arrived.
