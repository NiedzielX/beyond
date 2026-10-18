# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-18**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v2+v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector / Price-area Decision Support MVP: IMPLEMENTED**  
> **Current model-development order: Walidacja -> b -> c -> d -> tuning a**

| Phase | Scope | Status |
|---|---|---|
| A — Foundation | Canonical live trajectory / PIT evidence / registry | **DONE** |
| B — Shadow Forecasting | Structural Prior, trajectory gap, shadow revisions, audit | **DONE** |
| C0 — Provisional live decision layer | Continuation logic / sector decisions | **DONE / RUNNING** |
| C1-alpha | Frozen v2+v8 package + prospective pre-outcome evidence + scoring | **LIVE** |
| C1 — Promoted Learned Live Correction | Production promotion after sufficient fresh evidence | **EVIDENCE-GATED** |
| D — Probabilistic | Calibrated P10/P50/P90 | TODO |
| E0 — Sector / Price-area Decision Support | Sector trajectory, no-action projection, pricing scenarios, dashboard | **IMPLEMENTED** |
| E1 — Learned Pricing / Intervention | Learned elasticity / intervention uplift | **EVIDENCE-GATED** |

Canonical state:

- `ml/CURRENT_MODEL.md`;
- `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
- `AI_BOOTSTRAP.md`;
- `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
- `ml/SECTOR_DECISION_PRICING_V1.md`;
- `ml/NORTH_STAR.md`.

## Product purpose

Beyond must continuously answer:

1. where the event is likely to finish;
2. whether live evidence is strong enough to revise the Structural Prior;
3. which sectors / price areas are underperforming or outperforming;
4. what happens if the current trajectory continues;
5. what pricing action should be considered;
6. eventually, what happened after the club acted.

## Development workstreams — use these exact names

- **a) Dane historyczne — dopracować, nie przebudowywać**;
- **b) Aktualny sezon — wzmocnić**;
- **c) Context meczu — rozbudować**;
- **d) Live demand — najmocniej rozwinąć**.

Before them:

- **Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy.**

## Production forecasting state

Promoted production live adjustment remains:

`live_adjustment = 0`

C1 v8 remains separate `EXPERIMENTAL_SHADOW` evidence and does not write production forecast values.

## Structural Prior

All five horizons are executable and frozen:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

Historical reference performance is maintained in `ml/CURRENT_MODEL.md`.

Do not rebuild this layer first. It is the strongest and most mature forecasting component.

## C1-alpha development evidence

Development set:

- 9 completed in-domain Ekstraklasa events;
- 206 PIT-valid full-trajectory rows;
- 30 regularized PIT-valid final-24h rows.

Key results:

- Prior on the development subset: **3,968.7 MAE**;
- v2 live expert: **2,929.3 MAE**;
- v8 development replay: **2,713.3 window / 1,998.1 latest-row MAE**;
- non-deployable Prior/Live oracle: **1,867.9 MAE**.

These are development results only and are not fresh unseen-event validation.

## Frozen C1-alpha package

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Frozen expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Rule:

- one observation: LIVE only if disagreement >= `0.20` capacity;
- >=2 observations: LIVE only if disagreement >= `0.10` and live slope to date > 0;
- otherwise PRIOR.

Scheduled inference must never fit this package.

## Prospective C1 v8 runtime — LIVE

Workflow:

`.github/workflows/c1-shadow-v8-inference.yml`

Cadence:

`9,24,39,54 * * * *`

Current verified state on 2026-10-18:

- prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- validation state: `AWAITING_FIRST_PROSPECTIVE_SCORE`.

Therefore there is still **no confirmed prospective live MAE**.

## Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy

Run two strict tests using completed events with usable live evidence.

### Leave-One-Event-Out

For each test event:

- exclude it from fitting and tuning;
- reconstruct only features available at the historical forecast timestamp;
- evaluate Structural Prior, Live/C1 and final prediction;
- report MAE, bias and event-level degradation.

### Chronological walk-forward

At every step:

- train/tune only on events that occurred earlier;
- score later events;
- never use future outcomes or future snapshots.

**Cel:** uczciwie sprawdzić, czy obecny model jest bliżej 2k, 3k czy gorzej na niewidzianych meczach.

## b) Aktualny sezon — wzmocnić

- dodać wyraźny current season adjustment;
- mocniej brać pod uwagę ostatnie mecze domowe;
- mierzyć, czy klub w tym sezonie sprzedaje lepiej/gorzej niż jego historyczna norma;
- aktualizować adjustment po każdym kolejnym meczu.

**Cel:** model szybciej reaguje na zmianę realiów w danym sezonie.

## c) Context meczu — rozbudować

- dodać siłę / atrakcyjność przeciwnika;
- future fixtures: czy za kilka dni jest atrakcyjniejszy mecz;
- fixture congestion / cannibalization;
- forma i pozycja obu drużyn;
- skład: kontuzje, zawieszenia, kluczowi zawodnicy — tam, gdzie mamy wiarygodne dane.

**Cel:** model rozumie, dlaczego konkretny mecz może mieć większy lub mniejszy popyt.

## d) Live demand — najmocniej rozwinąć

- zbierać inventory od pierwszego momentu sprzedaży;
- liczyć velocity, acceleration, zmianę sektorów i price areas;
- aktualizować forecast po każdym nowym znaczącym snapshotcie;
- nie ograniczać modelu tylko do T-30/T-14/T-7/T-3/T-1;
- checkpointy zostawić głównie do mierzenia jakości;
- live correction ma stale poprawiać Structural Prior, gdy sygnał jest wystarczająco wiarygodny.

**Cel:** mieć forecast, który żyje razem ze sprzedażą.

## a) Dane historyczne — dopracować, nie przebudowywać

- utrzymać obecny Structural Prior;
- sprawdzić, które historyczne cechy realnie poprawiają MAE;
- usunąć słabe / noisy features;
- lepiej ważyć nowsze sezony względem starszych.

**Cel:** mocniejszy baseline bez komplikowania modelu.

## Kolejność developmentu

1. **Walidacja obecnego modelu**
2. **b) Aktualny sezon — wzmocnić**
3. **c) Context meczu — rozbudować**
4. **d) Live demand — najmocniej rozwinąć**
5. **a) Dane historyczne — dopracować, nie przebudowywać**

`Walidacja -> b -> c -> d -> tuning a`

## E0 sector / price-area decision support — IMPLEMENTED

Current implemented flow:

`sector state -> trajectory gap -> no-action projection -> real price-area mapping -> pricing scenario -> guarded recommendation`

Implemented:

- sector trajectory and status;
- no-action public-availability projection;
- Roboticket price-area capture where available;
- mixed-price sector split;
- assumption-based price scenarios;
- guarded `DECREASE / HOLD / INCREASE / MONITOR` recommendations;
- RLS-safe dashboard caches and UI.

Pricing maturity remains:

`ASSUMPTION_BASED_SCENARIO`

No automatic price changes:

`auto_price_change_allowed = false`

No learned elasticity or causal uplift claim is allowed yet.

Club decision / execution persistence is intentionally deferred for now. Demo intervention outcomes must be explicitly simulated.

## C1 promotion

The 20-independent-completed-match rule remains a later promotion gate.

Promotion requires enough genuinely prospective independent completed events, positive uplift vs Structural Prior, acceptable degradation/tail risk, frozen reproducible package, human review and explicit promotion.

No automatic production promotion exists.

## Immediate implementation sequence

1. **Walidacja obecnego modelu.**
2. **b) Aktualny sezon — wzmocnić.**
3. **c) Context meczu — rozbudować.**
4. **d) Live demand — najmocniej rozwinąć.**
5. **a) Dane historyczne — dopracować, nie przebudowywać.**
6. Keep C1 v8 frozen and collect prospective outcomes in parallel.
7. Keep E0 pricing assumption-based and human-reviewed.
8. Keep production `live_adjustment = 0` until explicit promotion.

## Product target

> **Beyond powinien łączyć dane historyczne, aktualny sezon, context meczu i live demand, żeby forecast żył razem ze sprzedażą — a potem przekładać ten sygnał na bezpieczne decyzje sektorowe i cenowe przed kickoffem.**
