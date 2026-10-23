# P11 — Match Attractiveness / Commercial Context v1 Plan

Last updated: **2026-10-23**

Status: **LITERATURE-GROUNDED DATA/EXPERIMENT PLAN — NO MODEL RESULT**

Production remains:

`live_adjustment = 0`

## 1. Objective

Add PIT-safe demand context that is materially different from the existing attendance-history / sporting-form / fixture-spacing signal.

Priority principle:

> Prefer variables closest to the economic mechanism of match demand and with defensible as-of semantics before adding weaker/noisier attention proxies.

Priority order:

1. **P11a — market-implied match quality / outcome uncertainty / stakes**;
2. **P11b — price / promotion context**;
3. **P11c — lineup / star strength / verified absences**;
4. **P11d — weather and media/search/social attention**.

Every family is a separate ablation/version. No family is silently added to another experiment after results are visible.

---

# 2. Existing Beyond infrastructure — reuse, do not duplicate

## Sporting form / table / timing

Already present in the structural PIT feature store, including:

- PPG;
- table rank / rank gap;
- recent form;
- goal-difference state;
- rest/congestion;
- timing/seasonality;
- opponent-demand and home-opponent history.

These are controls, not new P11 features.

## Rivalry

Existing:

`ml/global/sql/verified_rivalry_map_v1.sql`

Properties:

- positively verified rivalry relations only;
- missing map entry = unknown, never “not rivalry”;
- append/propagate with verified evidence;
- context research only.

P11 must consume this contract rather than create a second rivalry label source.

## Match stakes

Existing shadow pipeline:

`ml/global/sql/thesportsdb_stakes_shadow_pipeline_v2.sql`

Properties:

- completed-match-only standings reconstruction;
- fail closed on incomplete historical round cache;
- current score is research/shadow only;
- does not modify production forecast.

P11 should first validate the existing stakes score against verified/manual references and freeze a version before using it as a model feature.

## Verified absences

Existing:

`ml/global/sql/verified_absence_registry_v1.sql`

Important semantics:

- verified absence only;
- missing player = unknown, not confirmed available;
- valid-from / valid-until windows;
- no demand score unless salience/certainty/novelty are supported.

This is the correct starting point for P11c.

## Pricing

Existing append-only evidence:

`supabase/sql/roboticket_price_observations_v1.sql`

Includes:

- `sector_price_area_observations_v1`;
- `ticket_price_observations_v1`;
- captured-at timestamp;
- event/snapshot linkage;
- price area/type matrix;
- zero-price types preserved.

P11b therefore starts with **coverage/readiness and feature design**, not a new price scraper.

---

# 3. P11a — Market-implied quality / outcome uncertainty / stakes

## 3.1 Highest-priority missing source: PIT odds

There is currently no canonical versioned odds capture in the repo.

Required design before modeling:

- append-only snapshots;
- `ticket_event_id`;
- bookmaker/source identity;
- market type;
- home/draw/away decimal odds;
- captured_at / source observed time;
- raw source reference;
- no overwriting of earlier snapshots;
- normalized implied probabilities with overround retained separately;
- exact mapping confidence from source fixture to Beyond event.

Never use closing odds for T-7/T-3/T-1 unless those exact odds were already captured at the forecast cutoff.

## 3.2 Candidate derived features

From a 1X2 market snapshot known by `as_of_at`:

- implied home/draw/away probabilities;
- favorite probability;
- favorite-vs-underdog probability spread;
- entropy of normalized 1X2 probabilities;
- expected match balance / uncertainty;
- market-implied home strength;
- market movement since an earlier PIT snapshot, only when both snapshots were already available.

Odds should be interpreted as a compact external expectation signal, not causal truth.

## 3.3 Stakes/rivalry combination

First P11a ablation should keep components visible separately:

- market probabilities/uncertainty;
- verified stakes score;
- verified rivalry flag.

Do not immediately collapse them into one opaque attractiveness score. Individual ablation is required before combination.

---

# 4. P11b — Price / promotion context

## 4.1 First task: readiness audit

Before selecting a model feature, measure:

- independent events with any price observations;
- clubs/providers covered;
- earliest hours-to-kickoff coverage;
- number of distinct real price points per event;
- stability of price-area/type mapping;
- events with price changes;
- events with obvious complimentary / zero-price categories;
- whether observed public price is comparable across clubs/providers.

## 4.2 Candidate PIT features after readiness

Potential simple features:

- minimum positive visible price;
- median visible positive price;
- inventory-weighted visible price where the linkage is valid;
- price range / dispersion;
- share of inventory in low/mid/high price bands;
- price change since previous PIT cutoff;
- explicit promotion/discount flag only from verified evidence.

Do not infer “promotion” solely from a lower price without a valid baseline and source semantics.

---

# 5. P11c — Lineup / star strength / verified absences

The verified absence registry is only the evidence layer. P11c still needs a PIT-safe player-strength representation.

Candidate future design:

- player salience learned or externally supported using only prior information;
- expected/confirmed starter strength at `as_of_at`;
- count/weight of verified unavailable high-salience players;
- novelty of the absence;
- home vs away absence impact separately.

Rules:

- later-announced absence cannot backfill an earlier forecast;
- final lineup cannot be used for T-7/T-3 if it was unknown then;
- missing evidence remains unknown;
- avoid hand-scored player importance after attendance outcome is known.

---

# 6. P11d — Weather and attention

Retained as later context families:

- weather **forecast as known at the PIT cutoff**, never realized weather for an earlier prediction;
- media/search/social attention captured append-only with source timestamp.

These remain behind P11a–c unless their data coverage becomes materially stronger first.

---

# 7. Validation contract

For every P11 family:

1. freeze feature definition and PIT semantics before model result inspection;
2. audit independent-event coverage and variance first;
3. use controlled ablation against the same incumbent/folds;
4. match/event remains the independent unit;
5. no random snapshot split;
6. report match/event-balanced MAE;
7. report bias, median AE, P90, worst degradation, event/fold improvement rate;
8. paired event/match-block uncertainty for `ΔMAE`;
9. interpret with Governance v2;
10. no direct production activation.

---

# 8. Literature rationale

Primary attendance-demand references:

- Schreyer & Ansari (2022), *Stadium Attendance Demand Research: A Scoping Review*, DOI `10.1177/15270025211000404`;
- Martins & Cró (2018), *The Demand for Football in Portugal: New Insights on Outcome Uncertainty*, DOI `10.1177/1527002516661602`.

Recurring demand mechanisms relevant to Beyond include:

- expected contest quality;
- outcome uncertainty;
- team success;
- rivalry/stakes;
- star power;
- ticket price;
- timing;
- weather;
- promotions/substitutes.

---

# 9. Immediate development order

1. **P11a odds-source technical spike** — identify a source with timestamped historical/current 1X2 observations and legally/operationally usable access;
2. design append-only odds observation schema + event mapping + overround-normalized features;
3. audit stakes-shadow validation and rivalry coverage;
4. run price-observation readiness audit on existing tables;
5. audit absence coverage/salience readiness;
6. precommit the first P11a ablation only after source/coverage is proven.

## Decision

> **P11 development starts with PIT odds/quality/uncertainty because that is the clearest missing demand signal. Existing rivalry, stakes, absence and pricing infrastructure must be reused and hardened, not rebuilt.**
