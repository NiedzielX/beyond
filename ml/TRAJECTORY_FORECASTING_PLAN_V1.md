# Beyond Ticketing — Daily Trajectory Forecasting Plan v1

Last updated: **2026-10-28**

Status: **ACCEPTED / INFRASTRUCTURE DONE / LANE B ACTIVE / RESEARCH-ONLY**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

Operational source of truth: `ml/EXECUTION_PLAN_CURRENT.md`

Production remains:

`live_adjustment = 0`

---

# Part A — Human view

## 1. What we are building

Beyond should forecast as an evolving story:

`P-60 -> ... -> genuine observed trajectory -> today -> predicted remaining path -> final attendance`

At each daily cutoff, the forecast should use only information genuinely available by that point.

This is **daily inference, not daily retuning**.

The model should understand not only the current inventory/demand proxy level, but how the event reached that level.

---

## 2. Data reality

The current genuine inventory history is short:

- 32 Ekstraklasa events with any pre-kickoff inventory observation;
- 14 clubs;
- median first observation around **P-9.3**;
- p75 around **P-14**;
- earliest around **P-30.3**;
- P-31...P-60 historical coverage currently zero.

Representative coverage:

| Horizon | Coverage |
|---|---:|
| P-30 | 3.0% |
| P-14 | 21.9% |
| P-7 | 61.5% |
| P-3 | 75.0% |
| P-1 | 95.0% |

Therefore:

> **P-60 is a collection horizon, not a requirement for a fabricated complete 60-day vector.**

We use genuine variable-length prefixes and explicit sequence lengths/masks.

Missing/hidden inventory is never converted to zero.

---

## 3. What has already been learned

The first simple engineered-feature trajectory model has already been tested.

### Lane A v1

`Structural P50 + engineered trajectory features -> Ridge residual correction`

Strict-forward result:

- incumbent event-balanced MAE: **2594.5**;
- Lane A MAE: **4153.3**;
- Delta MAE: **+1558.8**;
- **60.1% worse**;
- event improvement rate: **20%**;
- 5 independent outer test events.

Decision:

`REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`

We do not tune Lane A v1 after seeing this result.

This result says that the frozen handcrafted summary/Ridge formulation did not extract useful incremental signal from the current cohort. It does **not** prove that ordered trajectory information is useless.

---

## 4. Active question

The active experiment is Lane B v1:

> **Can the model learn something from the ordered genuine sequence that was lost by the engineered velocity/acceleration summaries?**

Lane B must beat both:

1. the structural incumbent;
2. frozen Lane A.

Only then is a prospective daily-shadow candidate worth freezing.

---

# Part B — Frozen research design

## 5. Shared feature boundary

Contract:

`ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`

Shared primary eligibility:

- P-60...P-1 cutoff;
- PIT-valid structural incumbent;
- >=4 clean genuine snapshots;
- >=24h genuine observation window;
- canonical `signal_readiness=ready`;
- no future target trajectory;
- no target outcome in inference features.

The first comparison intentionally excludes unrelated:

- odds;
- weather;
- hype/media;
- match stakes;
- Form5;
- P4 context.

The test isolates **trajectory representation**.

---

## 6. Lane A — closed benchmark

Precommit:

`ml/TRAJECTORY_LANE_A_PRECOMMIT_V1.md`

Result:

`ml/TRAJECTORY_LANE_A_RESULT_V1.md`

Machine-readable result:

`ml/results/trajectory_lane_a_ridge_residual_v1_result.json`

Lane A remains useful only as the frozen simple benchmark for Lane B.

---

## 7. Lane B — frozen small sequence model

Precommit:

`ml/TRAJECTORY_LANE_B_PRECOMMIT_V1.md`

Implementation note:

`ml/TRAJECTORY_LANE_B_IMPLEMENTATION_NOTE_V1.md`

Implementation:

`ml/demand_engine/trajectory_lane_b_v1.py`

Runner:

`ml/run_trajectory_lane_b_v1.py`

Frozen architecture:

- one-layer GRU;
- 5 sequence channels;
- hidden dimension 8;
- 8-unit MLP head;
- dropout .20;
- AdamW lr .001 / weight decay .01;
- event-balanced weighted L1 residual loss;
- 200 fixed epochs;
- gradient clipping 1.0;
- seeds 17 / 29 / 41;
- median residual prediction across all three seeds.

No architecture search.

No early stopping.

No Transformer.

No self-supervised pretraining in v1.

---

## 8. Genuine sequence representation

Lane B uses the ordered real observations available by the cutoff.

Per timestep:

1. hours to kickoff;
2. available index relative to the first genuine observation;
3. capacity-share channel only under the frozen missing-channel semantics;
4. time since previous genuine observation;
5. change in available index since previous observation.

Rules:

- exact timestamp duplicates keep the highest snapshot ID;
- maximum one genuine observation per integer hour-to-kickoff bucket;
- no interpolation;
- no forward-fill;
- no fabricated daily points;
- padding requires explicit length/mask semantics.

For the frozen v1 cohort, persisted Lane A checkpoints did not carry populated capacity-normalized inventory. Lane B therefore does not introduce that sequence signal after Lane A's result; see the implementation note.

---

# Part C — Validation

## 9. Independent unit

Event/match is the independent unit.

`N events x M prefixes` still means `N` independent attendance outcomes.

All prefixes from one event remain in the same fold.

---

## 10. Frozen strict-forward folds

Contract:

`ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`

Cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

Frozen cohort:

- 10 labeled events;
- 19 persisted checkpoint rows;
- 5 strict-forward outer test events.

Fold registry SHA256:

`fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`

Rules:

- only earlier-kickoff events train a later target;
- same-kickoff events stay together;
- minimum 5 earlier train events;
- minimum 4 earlier train clubs;
- all event prefixes inherit the event fold;
- random daily-row CV is prohibited.

The cohort is frozen before Lane B result. Do not add newer events after seeing the answer.

---

## 11. Event-balanced training and scoring

If an event contributes `n_e` prefix rows in training:

`row_weight = 1 / n_e`

Each independent event therefore contributes total training weight 1.

Headline scoring:

1. calculate error for each tested cutoff;
2. average cutoff errors within each event;
3. average event-level errors across independent events.

This prevents long trajectories from dominating because they have more rows.

Horizon-specific MAE is still reported separately.

---

# Part D — Evidence infrastructure

## 12. Daily prospective evidence backend

Live private tables:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Live scoring functions:

- `public.score_daily_trajectory_completed_v1()`;
- `public.daily_trajectory_mae_by_horizon_v1()`.

Every prospective forecast will be persisted before outcome exposure.

No current development result activates these as production forecasts.

---

## 13. Frozen historical development export

RPC:

`public.export_trajectory_development_rows_v1(bigint[])`

OIDC gateway:

`trajectory_research_export_v1`

The gateway accepts GitHub OIDC only for:

- repository `NiedzielX/beyond`;
- ref `refs/heads/main`;
- audience `beyond-trajectory-research`.

No Supabase service-role key is stored in GitHub.

Current frozen export validates to:

- **10 events**;
- **19 rows**.

The runner fails closed on identity mismatch.

---

# Part E — Current execution

## 14. Completed

- [x] PIT trajectory feature store;
- [x] exact P-N dataset builder;
- [x] leakage tests;
- [x] coverage audit;
- [x] immutable prospective evidence backend;
- [x] MAE-by-horizon backend;
- [x] feature contract v1;
- [x] strict-forward validation contract v1;
- [x] frozen 10-event cohort;
- [x] shared A/B dataset materializer;
- [x] Lane A precommit;
- [x] Lane A executable learner;
- [x] Lane A strict-forward result;
- [x] Lane A rejected without post-result tuning;
- [x] Lane B precommit;
- [x] Lane B executable GRU;
- [x] Lane B protocol CI guards;
- [x] frozen development export RPC;
- [x] GitHub OIDC export gateway;
- [x] Lane B GitHub Actions workflow;
- [x] Demand Engine smoke CI green after Lane B changes.

---

## 15. Active next step

**Finish the frozen Lane B v1 strict-forward run.**

Then:

### If Lane B beats incumbent + Lane A

- review worst-event downside;
- review seed spread/stability;
- freeze a separate prospective daily-shadow candidate;
- start genuine immutable daily inference before future outcomes;
- keep production OFF.

### If Lane B beats Lane A but not incumbent

- sequence representation may contain useful signal;
- do not promote;
- diagnose why the structural prior remains stronger.

### If Lane B fails both

- do not tune v1;
- do not launch a broad neural architecture sweep on the same outer events;
- diagnose data/proxy/representation failure;
- any changed experiment becomes a separately precommitted v2.

---

# 16. Relationship to P9

P9 remains separate.

P9 asks:

`fixed curve similarity -> historical neighbors -> residual correction at T-48/T-24`

Daily trajectory Lane B asks:

`ordered genuine variable-length sequence -> sequence representation -> evolving residual forecast`

Do not merge their evidence.

---

# 17. Product direction

The future dashboard should distinguish:

1. observed inventory/demand proxy;
2. current as-of boundary;
3. predicted remaining proxy path;
4. predicted final attendance P10/P50/P90.

Conceptually:

`observed prefix | today | predicted remaining path -> final attendance`

New genuine observations replace previous expectations as time advances.

Inventory proxy must never be presented as confirmed paid ticket sales.

---

# 18. Research decision

> **Sequence research remains justified despite Lane A's failure because Lane B tests a materially different hypothesis: ordered representation rather than handcrafted summaries.**

But the evidence standard does not change:

> **Controlled model risk is accepted; leakage, post-result tuning and false independence are not.**
