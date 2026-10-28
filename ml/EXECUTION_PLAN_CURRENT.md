# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-28**

Status: **CURRENT SOURCE OF TRUTH**

Production: `live_adjustment = 0`

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

---

# 0. Read this first — where we are now

The plan has two parallel tracks.

## Track 1 — protect real prospective evidence

Do not disturb P7, P9, Form5, Long72 or current evidence-collection contracts.

## Track 2 — improve MAE with trajectory modelling

Infrastructure is done.

The first simple trajectory model, **Lane A Ridge v1**, has already been tested and **failed**:

- incumbent event-balanced MAE: **2594.5**;
- Lane A MAE: **4153.3**;
- Delta MAE: **+1558.8**;
- relative change: **+60.1% worse**;
- strict-forward independent test events: **5**.

Decision:

`Lane A v1 = REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`

We do **not** tune it after seeing the result.

The active model-development task is now:

> **Lane B v1 — test whether a genuine ordered trajectory sequence can beat both the structural incumbent and the failed engineered-feature Lane A benchmark.**

Lane B precommit and executable GRU learner are already in the repository.

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Primary metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired:

`Delta MAE < 0`

For Lane B we additionally care about:

`Delta MAE B_vs_A = Lane B MAE - frozen Lane A MAE`

Row count, snapshots, model parameters and number of daily prefixes are **not** independent evidence.

---

# 2. Non-negotiable rules

1. Event/match is the independent unit.
2. All prefixes from one event stay in one fold.
3. No random daily-row/snapshot CV.
4. No future target trajectory at an earlier cutoff.
5. No target attendance during prediction construction.
6. No manufactured booking/inventory history.
7. No gate relaxation merely to obtain coverage.
8. Frozen learners are not retuned after outer/prospective outcomes.
9. Genuine prospective evidence outranks favorable historical research evidence.
10. No research result activates production automatically.

---

# 3. Protect current prospective evidence first

Whenever a genuine prospective window is imminent, it takes priority over trajectory R&D.

## P9 v1

Historical state:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

First genuine attempt:

- event443 Cracovia–Motor T-48;
- cutoff 2026-10-28 17:00 UTC;
- result `PIT_SUPPORT_INSUFFICIENT`;
- 1 genuine attempt / 0 predictions / 0 scored.

This is correct fail-closed behaviour.

Do not lower support and do not retro-predict.

## P9 Family Fallback v2

Separately precommitted/deployed.

- same exact five v1 neighbors;
- unchanged support threshold;
- Structural fallback only under the frozen rule;
- never retro-predict event443;
- never pool v1/v2 evidence.

## Form5

First legal prospective T-24 capture:

**event443 — 2026-10-29 17:00 UTC**.

## P7

Latest verified:

- 53 immutable prediction rows;
- 6 independent events;
- 0 scored;
- no retuning.

## P11 / P4a

Continue genuine evidence accumulation only.

## Long72

Frozen / low priority.

- 5 scored events;
- MAE 6082.40 -> 6039.39;
- 43.01 / 0.71% point gain;
- do not retune.

---

# 4. Near-term windows to protect

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- event6 Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- event443 Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- event444 GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**;
- event445 Zagłębie–Korona T-48: **2026-10-31 17:00 UTC**;
- event447 Raków–Pogoń T-48: **2026-10-31 19:30 UTC**.

Event448 remains an inventory watch.

Unknown inventory is never converted to zero.

---

# 5. Daily trajectory infrastructure — DONE

The infrastructure phase is complete.

## Canonical PIT dataset / representations

- `ml/demand_engine/live_trajectory_feature_store.py`;
- `ml/demand_engine/daily_trajectory_dataset.py`;
- `ml/demand_engine/trajectory_feature_contract_v1.py`;
- `ml/demand_engine/trajectory_shared_dataset_v1.py`.

## Validation

- `ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`;
- `ml/demand_engine/trajectory_validation_folds_v1.py`.

## Prospective evidence backend

Live Supabase tables:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Live backend supports:

- immutable daily attempts;
- immutable daily predictions;
- post-outcome scoring;
- MAE by horizon.

## Research bundle access

Service-role-only RPC:

`public.get_trajectory_research_event_bundle_v1(ticket_event_id)`

Canonical SQL:

`supabase/sql/trajectory_research_event_bundle_v1.sql`

Anonymous/authenticated execution is revoked.

---

# 6. Data reality — trajectory history is genuinely short

Current genuine pre-kickoff inventory sample:

- 32 events;
- 14 clubs;
- median first observation around **P-9.3**;
- p75 around **P-14**;
- earliest observed event around **P-30.3**;
- P-31...P-60 historical coverage currently zero.

Representative snapshot coverage:

| Horizon | Coverage |
|---|---:|
| P-30 | 3.0% |
| P-14 | 21.9% |
| P-7 | 61.5% |
| P-3 | 75.0% |
| P-1 | 95.0% |

Decision:

> **P-60 is a collection horizon, not a requirement for a fake complete 60-day vector.**

Lane B therefore uses genuine variable-length sequences.

No interpolation or forward-fill merely to make the neural input convenient.

---

# 7. Frozen feature contract

Contract:

`ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`

Shared primary gate:

- P-60...P-1;
- PIT-valid structural incumbent;
- >=4 clean snapshots;
- >=24h observed trajectory;
- canonical `signal_readiness=ready`;
- no future target snapshot/outcome.

## Lane A representation

Engineered scalar trajectory summaries + structural P50.

## Lane B representation

Genuine ordered snapshot sequence + structural P50/global quality context.

Sequence rules:

- genuine observations only;
- exact timestamp dedupe;
- max one real observation per integer hour-to-kickoff bucket;
- no interpolation;
- no forward-fill;
- explicit sequence length/padding mask;
- padded zero is not genuine zero inventory.

No odds, weather, hype, match-stakes, Form5 or P4 context enters this first A/B comparison.

---

# 8. Frozen validation contract

Contract:

`ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`

Primary validation:

- strict expanding temporal event folds;
- train only on earlier-kickoff events;
- same-kickoff events held out together;
- minimum 5 earlier train events;
- minimum 4 earlier train clubs;
- every prefix from an event inherits the event fold.

Current frozen development cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

Cohort:

- 10 labeled events;
- 5 expanding outer test events;
- frozen fold-registry SHA256:
  `fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`.

Do not change this registry after seeing Lane A/B outer results.

---

# 9. Lane A v1 — DONE / REJECTED

Precommit:

`ml/TRAJECTORY_LANE_A_PRECOMMIT_V1.md`

Implementation:

`ml/demand_engine/trajectory_lane_a_v1.py`

Result:

`ml/TRAJECTORY_LANE_A_RESULT_V1.md`

Machine-readable result:

`ml/results/trajectory_lane_a_ridge_residual_v1_result.json`

## Result

| Metric | Result |
|---|---:|
| Independent outer test events | 5 |
| Outer test prefix rows | 14 |
| Incumbent event-balanced MAE | 2594.5 |
| Lane A event-balanced MAE | 4153.3 |
| Delta MAE | **+1558.8** |
| Relative change | **+60.1% worse** |
| Event improvement rate | 20% |
| Worst event degradation | +4166.4 |

By horizon:

| Horizon | Incumbent | Lane A | Delta |
|---|---:|---:|---:|
| T-7 | 3399.0 | 4490.9 | +1091.9 |
| T-3 | 2667.9 | 4224.7 | +1556.8 |
| T-1 | 2314.9 | 3727.8 | +1412.9 |

Decision:

> **Reject Lane A v1 as a candidate. Keep it frozen as the simple benchmark.**

No post-result alpha/feature tuning.

---

# 10. Lane B v1 — ACTIVE

Precommit:

`ml/TRAJECTORY_LANE_B_PRECOMMIT_V1.md`

Implementation:

`ml/demand_engine/trajectory_lane_b_v1.py`

Model:

- one-layer GRU;
- input dimension 5;
- hidden dimension 8;
- small MLP head;
- AdamW;
- weighted MAE residual loss;
- 200 fixed epochs;
- seeds 17 / 29 / 41;
- median prediction across seeds;
- event-balanced row weights.

No architecture search.

No Transformer.

No self-supervised pretraining in Lane B v1.

## Lane B must answer two questions

1. Does Lane B beat the structural incumbent?
2. Does Lane B beat frozen Lane A on exactly the same outer test identities?

Advance only if both are true and seed/downside diagnostics are acceptable.

---

# 11. Immediate execution order

## Evidence protection

1. Protect imminent P9/Form5 windows.
2. Score P7/P9 only after genuine outcomes.
3. Keep P11/P4a collection healthy.

## Trajectory R&D

4. Validate current repository CI after Lane A/B implementation.
5. Materialize the frozen cohort through the service-role research bundle path.
6. Run **Lane B v1** on the frozen strict-forward folds.
7. Persist machine-readable and human-readable Lane B result.
8. Compare Lane B vs incumbent and Lane B vs frozen Lane A.
9. If Lane B fails, do not tune v1 after the result; diagnose before creating v2.
10. If Lane B wins, freeze a separate prospective daily-shadow candidate before future outcomes.
11. Continue collecting longer genuine trajectories forward.
12. Derive the business minimum meaningful Delta MAE independently.

Production promotion remains a separate reviewed decision.

---

# 12. Agent decision rules

## If Lane B beats both incumbent and Lane A

- review event downside and seed stability;
- freeze candidate parameters;
- start prospective daily shadow inference before future outcomes;
- do not activate production.

## If Lane B beats Lane A but not incumbent

- sequence representation is interesting but not useful enough yet;
- do not promote;
- diagnose why structural anchor remains superior.

## If Lane B fails both

- do not launch a broad GRU/LSTM/Transformer sweep on the same outer events;
- diagnose data/proxy/representation first;
- any materially changed experiment becomes v2.

## If historical research wins but prospective evidence later loses

Prospective evidence wins.

---

# 13. Milestones

### Completed

- [x] daily PIT dataset and tests;
- [x] coverage audit;
- [x] immutable daily evidence backend;
- [x] MAE-by-horizon backend;
- [x] Trajectory Feature Contract v1;
- [x] strict-forward Validation Fold Contract v1;
- [x] frozen 10-event development cohort/folds;
- [x] Lane A precommit;
- [x] Lane A executable learner;
- [x] Lane A strict-forward result;
- [x] Lane A rejected without post-result tuning;
- [x] Lane B precommit;
- [x] Lane B executable GRU learner;
- [x] service-role research event bundle RPC.

### Next

- [ ] Lane B strict-forward result;
- [ ] Lane B decision;
- [ ] first frozen prospective daily trajectory candidate, only if justified;
- [ ] first genuine daily trajectory prediction;
- [ ] first genuine daily trajectory score;
- [ ] enough independent events for meaningful prospective Delta MAE;
- [ ] business meaningful Delta MAE threshold;
- [ ] production review only after the above evidence.
