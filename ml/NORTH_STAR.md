# Beyond Ticketing — Product & ML North Star

Last updated: **2026-10-18**

## Single objective

Build the best possible **live demand decision system** for football ticketing.

Beyond must not only forecast final attendance. It must tell the club:

1. where the event is likely to finish;
2. which sector / price area is underperforming or outperforming;
3. what is likely to remain publicly available if the current trajectory continues;
4. which commercial action is worth testing — especially price;
5. eventually, what happened after the club acted.

The forecasting layer remains the analytical foundation. Product value is created when that forecast becomes a useful decision before kickoff.

## Core product question

For every active event and every point in time before kickoff:

> **What is happening, why is it happening, where is the problem/opportunity, what happens if nothing changes, and what should the club test now?**

## Model-development workstreams — canonical wording

Use these names consistently:

- **a) Dane historyczne — dopracować, nie przebudowywać**;
- **b) Aktualny sezon — wzmocnić**;
- **c) Context meczu — rozbudować**;
- **d) Live demand — najmocniej rozwinąć**.

Before further development:

- **Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy.**

## a) Dane historyczne — dopracować, nie przebudowywać

Historical Structural Prior remains the baseline.

Use historical point-in-time evidence to estimate expected final demand, but do not rebuild this layer without evidence.

Development focus:

- keep current Structural Prior;
- check which historical features really improve MAE;
- remove weak / noisy features;
- weight newer seasons better than older seasons.

**Cel:** mocniejszy baseline bez komplikowania modelu.

## b) Aktualny sezon — wzmocnić

Adapt the long-term baseline to the club's current-season reality.

Development focus:

- explicit current season adjustment;
- stronger use of recent home matches;
- measure whether the club is above/below its historical norm this season;
- update the adjustment after every completed match.

**Cel:** model szybciej reaguje na zmianę realiów w danym sezonie.

## c) Context meczu — rozbudować

Explain why this particular fixture should differ from the club baseline.

Development focus:

- opponent attractiveness / strength;
- future fixtures;
- fixture congestion / cannibalization;
- form / league position of both teams;
- injuries, suspensions and key players where reliable point-in-time data exists.

**Cel:** model rozumie, dlaczego konkretny mecz może mieć większy lub mniejszy popyt.

## d) Live demand — najmocniej rozwinąć

Interpret what is happening in ticketing now.

Development focus:

- public inventory from the earliest sales moment;
- velocity;
- acceleration;
- sector / price-area movement;
- scarcity;
- release / replenishment activity;
- anomalies;
- source quality;
- forecast update after every meaningful new snapshot.

T-30 / T-14 / T-7 / T-3 / T-1 remain quality-measurement checkpoints, not the only moments when the forecast can change.

**Cel:** mieć forecast, który żyje razem ze sprzedażą.

## Live correction

Live correction is part of **d) Live demand**, not a separate development workstream.

Conceptually:

`Live Forecast = Structural Prior + reliable live correction`

The live layer should revise the Structural Prior only when the live signal is reliable enough.

## Sector / price-area decision layer

Current implemented direction:

`sector diagnosis -> no-action projection -> real price-area scenario -> guarded recommendation`

Public seat-map inventory is a **demand proxy, not confirmed paid sales**. Sector projections and event attendance must not be forced into a false 1:1 mapping.

## Dynamic pricing

Dynamic pricing decision support is a first-class product capability.

Current E0 supports assumption-based scenarios and guarded recommendations. It does **not** claim learned elasticity or causal uplift.

Automatic production price changes are not allowed:

`auto_price_change_allowed = false`

Mixed-price sectors must be split into real price areas instead of using a fake weighted executable price.

## Current evidence boundary

Historical Structural Prior is mature and benchmarked.

C1 v8 is still `EXPERIMENTAL_SHADOW`.

As of 2026-10-18:

- prospective prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- there is no confirmed prospective live MAE yet.

Development replay around ~2.0k–2.7k is promising evidence, not production accuracy.

## Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy

Before more model complexity, run:

1. **Leave-One-Event-Out** with the tested event excluded from fitting/tuning;
2. **chronological walk-forward**;
3. strict reconstruction of only the features available at each historical forecast timestamp;
4. paired comparison of Structural Prior vs Live/C1 vs final prediction.

**Cel:** ustalić, czy obecny live model jest faktycznie bliżej ~2k, ~3k czy gorzej na niewidzianych historycznych meczach.

## Business horizon priority

1. **T-30** — planning / major intervention;
2. **T-14** — strong pricing / demand intervention window;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final estimate / calibration.

Early actionability remains first-class even though live reasoning should become continuous between these checkpoints.

## Evaluation dimensions

### Forecast quality

- MAE;
- WAPE;
- median absolute error;
- bias;
- worst-event degradation;
- stability across clubs / seasons / horizons.

### Live demand quality

- forecast revision quality;
- incremental uplift over Structural Prior;
- first-detection lead time;
- stability under release / coverage changes.

### Sector decision quality

- correctness of underperformance direction;
- sector no-action projection error;
- false alarm rate;
- time-to-action;
- price-area recommendation consistency.

### Pricing / intervention quality

Before learned pricing:

- scenario consistency;
- guardrail adherence;
- recommendation stability;
- explicit separation of simulated vs observed outcomes.

After real intervention evidence matures:

- incremental tickets;
- incremental revenue / contribution;
- ROI;
- price elasticity calibration;
- uplift uncertainty;
- recommendation expected value.

## Kolejność developmentu

Canonical roadmap:

`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`

1. **Walidacja obecnego modelu**
2. **b) Aktualny sezon — wzmocnić**
3. **c) Context meczu — rozbudować**
4. **d) Live demand — najmocniej rozwinąć**
5. **a) Dane historyczne — dopracować, nie przebudowywać**

`Walidacja -> b -> c -> d -> tuning a`

In parallel:

- collect prospective C1 evidence without retuning frozen v8;
- keep E0 pricing assumption-based / human-reviewed until real intervention evidence exists;
- calibrate probabilistic P10/P50/P90 when the evidence supports it.

## Product value statement

**Beyond powinien łączyć dane historyczne, aktualny sezon, context meczu i live demand, żeby forecast żył razem ze sprzedażą — a potem przekładać ten sygnał na bezpieczne decyzje sektorowe i cenowe przed kickoffem.**
