# E0 Sector Decision v1 — Status + No-action Projection

Date: **2026-10-16**  
Status: **implemented / live service-role contract / Steps 3–4 complete**

## Contract

Function:

`public.get_sector_decision_v1_asof(ticket_event_id, as_of_at)`

Decision version:

`sector-decision-v1`

Status policy:

`SECTOR_STATUS_V1_HORIZON_10_15_20_MIN5`

Projection policy:

`SECTOR_NO_ACTION_PROJECTION_V1_BOUNDED_VELOCITY_BLEND`

This layer depends on:

- `sector-trajectory-v1`;
- `sector-gap-v1`.

## Sector status policy

A sector first has to pass the `sector-gap-v1` release/coverage quality gate.

If it does not, status is:

`INSUFFICIENT_SIGNAL`

For usable sectors, material normalized gap thresholds depend on time to kickoff:

- <= 24h: **10%**;
- >24h and <=72h: **15%**;
- >72h: **20%**.

A status is material only when the absolute gap is also at least **5 seats**.

Therefore:

- `UNDERPERFORMING` = positive normalized gap >= horizon threshold **and** gap >= +5 seats;
- `OUTPERFORMING` = negative normalized gap <= -horizon threshold **and** gap <= -5 seats;
- otherwise `ON_TRACK`.

The 5-seat guard was added after the first live test exposed a bad edge case: a tiny sector with only one currently available seat could show a large percentage gap and be labeled underperforming despite having no commercially meaningful inventory problem.

## Trend state

Status describes position relative to the event.

A separate trend signal describes current direction:

- `IMPROVING`;
- `WEAKENING`;
- `STABLE`;
- `FLAT`;
- `UNKNOWN`.

Trend uses 6h velocity relative to 24h velocity when available.

This allows examples such as:

- `UNDERPERFORMING + IMPROVING` — still behind, but catching up;
- `UNDERPERFORMING + WEAKENING` — behind and deteriorating;
- `OUTPERFORMING + IMPROVING` — strong sector getting stronger.

## Current active-event distribution

Across the selected current active-event sample after the 5-seat materiality guard:

- `UNDERPERFORMING`: **35** sector rows;
- `OUTPERFORMING`: **56**;
- `ON_TRACK`: **219**;
- `INSUFFICIENT_SIGNAL`: **31**.

This is a decision-support distribution, not a learned class distribution.

## No-action projection

Dashboard wording:

**Projected outcome if current trajectory continues**

The projection estimates **public availability remaining at kickoff**, not attendance and not paid sales.

Velocity hierarchy:

1. inside final 24h, when both are available: `60% × V6h + 40% × V24h`;
2. otherwise, when available: `70% × V24h + 30% × V72h`;
3. fallback V24h;
4. fallback V72h;
5. fallback V7d;
6. fallback V6h;
7. no projection when the release/coverage quality gate fails.

Projection is bounded:

`0 <= projected public availability at kickoff <= sector reference availability`

Negative velocity is allowed to imply increasing future public availability, but the projection cannot exceed the observed reference availability.

## Projection validation

Across 341 current sector rows:

- all 310 usable status rows receive a projection;
- all 31 `INSUFFICIENT_SIGNAL` rows receive no projection;
- **0 bound violations** were observed;
- no projected availability was below zero or above reference availability.

## Example live underperformers

Examples from the active-event checkpoint:

### Pogoń Szczecin — Radomiak Radom, sector D5

- current public availability: **675**;
- reference availability: **821**;
- relative gap: **+26.1%**;
- gap: approximately **+214 seats** versus proportional event progress;
- status: `UNDERPERFORMING`;
- trend: `WEAKENING`;
- projected public availability at kickoff if trajectory continues: approximately **584**;
- projection confidence: `MEDIUM`.

### Zagłębie Lubin — Jagiellonia Białystok, sector F1

- current public availability: **701**;
- reference availability: **747**;
- relative gap: **+24.8%**;
- gap: approximately **+185 seats**;
- status: `UNDERPERFORMING`;
- trend: `IMPROVING`;
- projected public availability at kickoff: approximately **625**;
- projection confidence: `MEDIUM`.

### GKS Katowice — Pogoń Szczecin, sector 1

- current public availability: **162**;
- reference availability: **237**;
- relative gap: **+41.2%**;
- gap: approximately **+98 seats**;
- status: `UNDERPERFORMING`;
- trend: `IMPROVING`;
- projected public availability at kickoff: approximately **129**;
- projection confidence: `MEDIUM`.

These examples show the intended product output: not only "sector is weak", but also the scale of the gap, current direction and projected remaining public inventory if the trajectory continues.

## Release-risk behavior

A sector with a very large apparent positive gap is not forced into `UNDERPERFORMING` when `sector-gap-v1` detects material availability-release risk or unstable coverage.

In that case:

- status = `INSUFFICIENT_SIGNAL`;
- projection = null;
- reason code identifies release/coverage risk.

This prevents recommendations from reacting to inventory mechanics as if they were demand collapse.

## Security / activation

- `SECURITY INVOKER`;
- service-role execution only;
- no automatic price action;
- no write into C1 production forecast;
- no claim of paid sales or causal intervention uplift.

## Decision

**Steps 3 and 4 are complete.**

Next:

1. expose sanitized read-only E0 event/sector surfaces for `BeyondTicketingPanel`;
2. show sector status, gap, trend and no-action projection in Event Detail;
3. audit real price data sources;
4. add explicit `PRICE_DATA_MISSING` semantics;
5. implement assumption-based pricing scenarios only after current/base price is available.
