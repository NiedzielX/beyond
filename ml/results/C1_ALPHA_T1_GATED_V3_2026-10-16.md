# C1-alpha T-1 Gated v3 — nested LOEO result

Date: **2026-10-16**  
Status: **safer than unconditional live replacement / not yet at target MAE**

## Protocol

- 9 completed Ekstraklasa events;
- final 24h / T-1 Structural Prior;
- 30 PIT-valid rows;
- base live estimate frozen to v2 winner: `ridge_directocc_compact_generic_a10`;
- nested Leave-One-Event-Out;
- inner LOEO selects gating/blending policy;
- outer event remains untouched during policy selection;
- policy inputs: prior-vs-live disagreement, blend weight, bounded correction cap;
- no outcome-derived gate feature.

GitHub Actions run: `38887253839`  
Evidence artifact: `c1-alpha-t1-gated-v3-38887253839`

## Result

Structural Prior T-1 incumbent:

**3,968.7 MAE**

Nested gated live result:

**3,054.3 MAE**

Improvement:

- **914.4 MAE** absolute;
- **23.04% relative**.

Safety improved materially versus unconditional v2:

- v2 worst-event degradation: **4,748.6**;
- v3 worst-event degradation: **1,326.1**.

However:

- event improvement rate: **2 / 9 = 22.2%**;
- target `<1900 MAE`: **not reached**.

## Full-data deployment-policy diagnostic

When policy selection is run on all available events using inner whole-event validation, the preferred policy is:

`gate_d0.12_w1.00_cap0.25`

Meaning:

- apply live correction only when prior-vs-live disagreement is at least **12% of verified capacity**;
- when applied, use full correction;
- cap correction at **25% of capacity**.

Its inner-LOEO estimate on the full dataset is:

**2,000.5 MAE**

This is encouraging but is **not** the honest outer nested score and therefore must not be presented as validated live MAE.

## Oracle diagnostic — key finding

Non-deployable outcome-aware oracle:

- Structural Prior: **3,968.7 MAE**;
- unconditional v2 live model: **2,929.3 MAE**;
- oracle event switch `min(prior error, live error)`: **1,867.9 MAE**.

The oracle result is diagnostic only. It proves that the pair of experts already contains enough information to reach approximately the user's target ~1900 MAE **if Beyond can learn which expert to trust for a new event**.

## Decision

Do not activate v3 as production C1.

The next experiment is not another manual threshold grid.

Proceed to **C1-alpha T-1 Stacked Gate v4**:

1. generate base-live predictions out-of-fold on training events;
2. use Structural Prior prediction + base live prediction + PIT live reliability features as meta inputs;
3. train a simple strongly regularized meta model / gate on OOF predictions only;
4. apply it to an untouched outer event;
5. evaluate with nested whole-event validation.

Candidate meta approaches should remain deliberately simple:

- Ridge stacking/blending;
- logistic expert switch;
- shallow regularized tree only if useful.

The objective is to approximate the 1,867.9 oracle ceiling without leaking event outcomes into gate selection.
