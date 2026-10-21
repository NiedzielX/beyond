# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-21**

Status: **FROZEN LIVE EVIDENCE LANES + PARALLEL MAE-FIRST CHALLENGER R&D**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V3.md`

## Production boundary

Production remains:

`live_adjustment = 0`

Nothing in this document activates production automatically.

---

# 1. Track A — frozen final24 evidence lane

Pre-Live anchor:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Frozen final24 package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + P2_reliability(t) * ridge_a10_delta(t)`

Track A is immutable while delayed-label and genuine post-freeze evidence accumulate.

Pre-Live v3 T-1 is exactly equivalent to v2 T-1 on the frozen replay, so no cosmetic retrain is required.

---

# 2. Frozen long72 evidence lane

Package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Scope:

`24 < hours_to_kickoff <= 72`

Architecture:

1. frozen T-3 checkpoint anchor;
2. `inventory-linear-extrapolation` expert;
3. raw correction cap `±0.10` occupancy;
4. `P2-observation-maturity` reliability.

Historical development metrics:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- uplift `+694.51 / +18.73%`;
- 24–48h uplift `+954.58 / +25.75%`;
- 48–72h uplift `+664.71 / +14.47%`;
- event improvement rate `61.54%`;
- worst event degradation `1488.34`;
- bias `+917.05`.

These remain historical exposed research metrics.

---

# 3. Long72 prospective implementation contract

Use two phases.

## Phase A — forecast materialization before label

For each newly eligible event / as-of point, persist immutably:

- event ID;
- kickoff;
- `as_of_at`;
- frozen T-3 anchor;
- raw inventory extrapolation;
- P2 observation/time reliability;
- frozen P2 forecast;
- source snapshot identity;
- feature/data lineage;
- package ID;
- code/model/data hashes;
- materialization timestamp.

The materialized row must not depend on final attendance.

## Phase B — outcome join after label

After final attendance exists:

- join it to the previously persisted forecast;
- compute absolute and signed error;
- append scorecard evidence;
- do not recompute the forecast.

This distinction is mandatory for genuine post-freeze prospective evidence.

---

# 4. Long72 scorecard

Track:

- event-balanced MAE 24–72h;
- anchor MAE;
- absolute and relative uplift;
- 24–48h MAE/uplift;
- 48–72h MAE/uplift;
- bias;
- median AE;
- P90 AE;
- event improvement rate;
- worst-event degradation;
- independent event count;
- evidence class.

Keep historical-exposed and true prospective evidence separate.

---

# 5. Live R&D does not wait for evidence accumulation

Do not retune frozen Track A or long72 packages.

Instead create new challenger IDs and develop in parallel.

Priority live-R&D sequence:

1. forward-event validation ordered by kickoff;
2. MAE-native residual objectives;
3. structural + live residual architecture;
4. forecast combination between structural/context/live sources;
5. reliability/shrinkage selected inside development folds;
6. event-block uncertainty around `ΔMAE`.

The relevant live-ticket question is:

> **Does PIT live inventory lower MAE after the strongest structural/global forecast has already explained historical demand?**

Do not use an obsolete weak baseline as the main benchmark.

---

# 6. 72–168h boundary

Long-horizon export remains additive and PIT-safe.

Last audited coverage above 72h:

`8` independent events.

Predeclared research-start floor:

`N>=9`

At the threshold:

1. freeze exact event/as-of identities;
2. define the PIT-safe T-7 anchor transition;
3. open a separate challenger cycle;
4. start with simple / strongly regularized and MAE-native candidates;
5. use event-safe plus forward-event validation;
6. do not modify long72 P2.

`N=9` opens research only; it does not establish production readiness.

---

# 7. Production promotion

Neither historical LOEO uplift nor a new R&D champion automatically changes production.

Promotion requires:

- genuine future evidence;
- lower prospective MAE;
- acceptable bias/tail behavior;
- reproducible frozen lineage;
- explicit reviewed activation.

Until then:

`live_adjustment = 0`

## Immediate instruction

> **Finish immutable long72 two-phase prospective scoring, but do not wait on labels. In parallel develop new live challengers as MAE-first residual/ensemble corrections over the strongest structural/global forecast.**
