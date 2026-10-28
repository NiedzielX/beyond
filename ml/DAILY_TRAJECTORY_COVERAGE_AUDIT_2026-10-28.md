# Beyond Ticketing — Daily Trajectory Coverage Audit

Date: **2026-10-28**

Status: **CURRENT DATA-REALITY AUDIT**

Purpose: quantify how much genuine PIT inventory trajectory actually exists before choosing the first daily trajectory models.

This is a coverage audit only. It does not use attendance targets and is not model evidence.

---

## Executive read

The current database does **not** contain anything close to complete P-60 -> P-1 inventory trajectories.

Across Ekstraklasa ticket events with genuine inventory observations:

- events with at least one genuine pre-kickoff inventory snapshot: **32**;
- clubs represented: **14**;
- median first observed inventory point: **P-9.3**;
- 25th percentile first observed point: **P-5.6**;
- 75th percentile first observed point: **P-14.0**;
- earliest observed event begins around **P-30.3**.

Therefore waiting for a conventional large, complete P-60 sequence dataset would take a long time.

The accepted response is **not** to fabricate earlier history. It is to support genuine **variable-length prefixes + explicit missingness/masks** and continue collecting forward.

---

## Coverage at representative daily horizons

| Horizon | Eligible event cutoffs | With genuine snapshot by cutoff | Coverage | Fresh <=24h | Events with >=4 visible snapshots |
|---|---:|---:|---:|---:|---:|
| P-30 | 33 | 1 | 3.0% | 1 | 1 |
| P-21 | 32 | 2 | 6.3% | 2 | 2 |
| P-14 | 32 | 7 | 21.9% | 7 | 7 |
| P-10 | 30 | 12 | 40.0% | 10 | 12 |
| P-7 | 26 | 16 | 61.5% | 16 | 16 |
| P-5 | 26 | 19 | 73.1% | 19 | 18 |
| P-3 | 24 | 18 | 75.0% | 18 | 18 |
| P-2 | 21 | 17 | 81.0% | 17 | 17 |
| P-1 | 20 | 19 | 95.0% | 19 | 19 |

For P-31 through P-60, the current audit found **0 genuine snapshots available by those cutoffs**.

---

## What this changes in the trajectory plan

### 1. P-60 remains the canonical collection horizon, not a minimum input requirement

The system should continue creating/checking daily cutoffs from P-60 to P-1, but a model must not require a fabricated full 60-day vector.

A valid event may begin its genuine observed prefix at P-20, P-12, P-7 or later.

### 2. Sequence models must support variable-length prefixes

Lane B must use one of the following explicit mechanisms:

- sequence lengths + packed/padded sequences;
- attention masks;
- an equivalent missingness-aware design.

Zero-padding must never be interpreted as genuine zero inventory.

### 3. Missingness is information, not a value

Keep separate:

- no public inventory observed yet;
- stale observation;
- genuine observed inventory value;
- hidden/unknown inventory.

Do not impute unknown inventory to zero.

### 4. Early horizons are collection-first

P-30/P-21 currently have too little independent trajectory coverage for meaningful attendance-model claims.

They remain valuable prospective collection horizons, but early research evidence will naturally be concentrated later until forward coverage accumulates.

### 5. First model comparison should expose support by horizon

Every Lane A / Lane B result must show event and club counts next to MAE.

A lower P-14 MAE on a handful of events must not be presented as equivalent evidence to a later horizon with materially greater independent-event coverage.

---

## Implication for the accepted high-risk sequence decision

This audit strengthens the reason to test small sequence models early rather than waiting for complete trajectories, but it also strengthens the safeguards.

The first sequence experiments should:

- stay small and strongly regularized;
- consume genuine variable-length prefixes;
- use event-grouped validation;
- compare against Lane A on identical events/cutoffs;
- treat self-supervised trajectory learning as representation learning, not as additional independent attendance labels;
- remain research/shadow-only until prospective evidence exists.

---

## Data contract already implemented

Canonical builder:

`ml/demand_engine/daily_trajectory_dataset.py`

It:

- creates exact P-N cutoffs;
- reuses the existing PIT-safe live trajectory feature store;
- preserves missing rows rather than inventing history;
- rejects future target snapshots;
- only attaches structural priors that genuinely existed by the cutoff.

PIT/leakage tests:

`ml/demand_engine/test_daily_trajectory_dataset.py`

Demand Engine smoke CI passed after integration on 2026-10-28.

---

## Prospective evidence backend already live

Supabase private ledgers:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Controlled RPCs:

- `public.record_daily_trajectory_attempt_v1(...)`;
- `public.insert_daily_trajectory_prediction_v1(...)`;
- `public.score_daily_trajectory_completed_v1()`;
- `public.daily_trajectory_mae_by_horizon_v1()`.

Direct service-role inserts are not allowed; service role has read-only table access and controlled RPC execution. Anonymous/authenticated execution of the SECURITY DEFINER write/score RPCs is revoked.

No daily trajectory prediction has been fabricated or persisted as part of this infrastructure work.

Canonical SQL contract:

`supabase/sql/daily_trajectory_prospective_evidence_v1.sql`
