# Beyond Ticketing — Daily Trajectory Forecasting Plan v1

Last updated: **2026-11-08**

Status: **ACCEPTED DESIGN / INFRASTRUCTURE DONE / ORIGINAL LANES CLOSED / PARALLEL VERSIONED R&D**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V6.md`

Operational source of truth: `ml/EXECUTION_PLAN_CURRENT.md`

Production remains:

`live_adjustment = 0`

Interpretation update: this document retains the original 2026-10-28 Lane A/B design and frozen architecture/fold details. The execution plan and progress tracker resolve their current status: original supervised Lane A/B results are closed. Historical instructions to finish Lane B v1 are not current execution requests. Frozen lanes remain protected while new, separately versioned and precommitted MAE experiments run in parallel under roadmap v6.

Research loop: `baseline -> new information -> simple challenger -> event-grouped/PIT-safe MAE -> freeze -> prospective shadow -> genuine outcomes`.

---

## Rolling72 — November 8: coverage audited, input/label code prepared

[Stage A result and remaining gates](ROLLING_72H_STAGE_A_RESULT_2026-11-08.md), [reproducible aggregates](ROLLING_72H_COVERAGE_AUDIT_2026-11-08.json). Cached November7source:38fixtures/16clubs/29,063snapshotrows. First-observation+72h has19fixtures/13clubs; earlyP-50support has only1fixture/1club. These are **historical capture-time matches**, not PIT-proven validation, issued forecasts or new MAE. Missing ingestion clocks, stable-pool proof and per-sector histories remain unresolved in this export.

Separate `rolling72_features_v1` and `rolling72_labels_v1` implement arbitrary actual issue times, one-point prefixes, declared knowledge clocks, real6/24/72h history features and later genuine24/48/72h label matching. Frozen versions/ledgers remain unchanged. Prepared and tested code is not live ingestion, a fitted challenger, a deployed panel feed or proven prospective improvement. The old panel parser also rejects this new contract; an explicit new feed/version is required.

**Next:** receipt-bound source adapter and versioned feature persistence, then exact benchmark/candidate precommit before fit. Preserve the diagnostic cohort as exposed and the30new-fixture/8-club review rule. Never invent old known_at clocks to turn cached historical rows into PIT evidence. No DBwrite, worker renewal, production activation or1200MAE achievement is claimed; defaultsfalse/0.

## Latest product priority — November 8: 48–72 hours to act

**Literature checkpoint before implementation:** [targeted review](ROLLING_72H_LITERATURE_REVIEW_2026-11-08.md) and [source-access registry](ROLLING_72H_LITERATURE_SOURCES_2026-11-08.json). Keep MAE/P50 aligned, add a separately precommitted conditional booking-curve baseline, audit sector coverage, evaluate advance warning quality, and separate forecast accuracy from causal price/ad revenue effects. No algorithm or1200MAE is guaranteed. Direct publisher access was403blocked; classic booking papersR12/R13remain metadata-only, explicitly not full-text verified. The completed capture-time coverage audit and new input/label contract are recorded above; no new fit, activation, worker renewal or DBwrite occurred.

**Whole sales lifecycle:** rolling +24/+48/+72 h forecasts start with the first genuine observed datum after sales open, including the one-observation case, and are re-issued throughout tracking. At P-50 the targets are P-49/P-48/P-47; at P-15 they are P-14/P-13/P-12. These are future horizons, not a final72h eligibility window or a requirement for24h of prior history. Preserve late-start/missing-history gaps and immutable issue times; existing frozen cold-start gates stay unchanged.

**Accuracy remains a core objective:** minimise genuine prospective event-balanced MAE and continue targeting **about 1200 seats attendance MAE** as a research milestone, with lower better. The rolling24/48/72h product adds forward commercial value; it does not replace the existing accuracy goal. Report each horizon/target/cohort separately and never substitute a low inventory-path score for attendance accuracy. No frozen gates, estimators or parameters change.

Full thesis, staged delivery and evaluation: [rolling72 commercial forecast plan](ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1.md). Coverage audit A is recorded above; the next step is source-clock integration and exact benchmark/candidate precommit before model fitting. The next72hours are the MVP decision horizon from the first genuine observation, not a restriction to the final72hours before kickoff.

The user clarified the MVP again: **from the first genuine observation of a tracked match, forecast the next24/48/72hours and update from the full history actually known now**. This applies from early tracking, includingP-50, through kickoff. P-15is an example, not an eligibility cutoff; final24C1alone does not implement this product. Clubs need48–72hours to act on expected demand/sector changes if price/promotion/pool conditions remain as assumed.

Contract and DONE: [.ai rolling72spec](../.ai/specs/2026-11-08-rolling-72h-commercial-forecast-mvp.md). The path of the same measured variable starts from the last real observation; preserve each actual issue, predict future changes, then score against genuine later observations at+24/+48/+72. A first-observation/short-history route needs a separately versioned contract; never weaken old daily/drift/C1gates. Unknown interventions stayUNKNOWN; public availability does not prove paid sales or a causal price effect. Sector claims require actual comparable sector data. Attendance and inventory targets remain separately evaluated.

**Immediate product work:** audit existing dataset/model/serving against that contract, specify one new version before fitting, verify actual use of trajectory information, and prove real observation→persisted future path→panel→later observation→score. The historical final-attendance chart readsforecast_observations.final_p50and is not that path or median26. Existing dailyv1had zero relative-value-history coefficients; neither passing full prefixes nor a decorative plot proves learned dynamics. Keep existing frozen artifacts, exposed cohorts, missed observations and review gates unchanged.

The live-refresh guardian was a supporting operational WIP. It is **untested, unpublished, inactive and deferred**; source preserved privately, SDDremains open. No collectors were renewed or old source slots re-run during this scope clarification. This rolling72product acceptance is the current MVP priority; the existing terminal-attendance objective continues within its own lane. No new model/fit/deployment or measured72hour advantage is claimed. Defaultsfalse/0.

# Part A — Human view

## 1. What we are building

Beyond should forecast as an evolving story:

`P-60 -> ... -> genuine observed trajectory -> today -> predicted remaining path -> final attendance`

At each daily cutoff, the forecast should use only information genuinely available by that point.

This is **daily inference, not daily retuning**.

The model should understand not only the current inventory/demand proxy level, but how the event reached that level.

---

## 2. Data reality

The historical coverage snapshot from the original 2026-10-28 design was short:

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

## 4. Original Lane B v1 question — historical

The original Lane B v1 experiment asked:

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

## 15. Original next-step decision tree — historical

The original instruction was to finish the frozen Lane B v1 strict-forward run. That work is closed; consult `EXECUTION_PLAN_CURRENT.md` and `PROGRESS_TRACKING.md` for its result and later versions. Do not rerun or tune v1 because this historical design describes it.

The branches below record the original decision tree. Current new research must instead precommit its own baseline, new information/mechanism, candidate version and event-grouped/PIT-safe evaluation. It proceeds in parallel and preserves all existing frozen contracts.

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
