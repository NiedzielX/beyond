# Beyond — operational handoff

Updated **2026-11-04 11:20 UTC**. Production remains **OFF**: `production_change=false`, `live_adjustment=0`.

Read strategy and state first: `MAE_RESEARCH_ROADMAP_V6.md` → `EXECUTION_PLAN_CURRENT.md` → `PROGRESS_TRACKING.md` → `TRAJECTORY_FORECASTING_PLAN_V1.md` → this handoff. This file supplies operational state; it does not define a competing MAE strategy.

## Next actions

1. Query fresh `public.prospective_decision_summary_v1(10)` before relying on the dated snapshot below.
2. Protect the next genuine encoder checkpoint: **Górnik449 / P-3, Nov4 16:30 UTC (17:30 Warsaw)**, READY at the latest check. The existing guardian should dispatch the main workflow only if the legal window is open and unrecorded. Verify the actual run and expected DB record.
3. **Motor5091 / P9 T-48, Nov4 17:00 UTC (18:00 Warsaw)** is the next P9 checkpoint. Keep its v1/v2 contracts separate; verify its own heartbeat/workflow/DB chain. Encoder guardian evidence does not establish P9 redundancy.
4. First already-issued daily-path targets mature **today17:00 UTC (18:00 Warsaw)**. Let the frozen scorer attach genuine observations; inspect paired persistence/model errors and prefix-regime diagnostics. Missing labels stay unscored. Do not retune from early errors.
5. Continue new post-freeze drift capture. Its first targets mature at least24hours after its first eligible predicted issue; never reuse Nov3predictions as drift evidence. Review only under its precommit.
6. Verify bounded workers before **Nov5 09:30 UTC (10:30 Warsaw)**. They stop then and depend on this cloud host surviving. A later session may renew a stopped worker within its bounds; inspect live legal windows first. No historical issue backfill.

## Actual evidence at11:20UTC

| Lane | Attempts | Predictions / points | Scores | State |
|---|---:|---:|---:|---|
| Frozen encoder attendance |9|5predictions|0|Korona603/P-3 captured honestly as insufficient input |
| P9v1 |6|0|0|Separate frozen lane |
| P9v2 |5|3predictions|0|Separate frozen lane |
| Local daily inventory v1 |8|4events /57future points|0|New Korona issue failed prefix-span gate |
| Fixed genuine24-hour drift |1|0points|0|First legal issue captured; same insufficient prefix span |

### Existing live models — do not omit these scores

Fresh DB read2026-11-04T11:42UTC from `dashboard_c1_shadow_v8_status_v1`: package`c1-shadow-v8-frozen-2026-10-16-n9`,101prediction rows /17events /11scored events. Latest-row MAE:structural prior4314.722244, raw live7127.992602, governed policy4121.454326. Representative-window policyMAE4971.620552. Latest scoreOct25; six tracked completed Oct30–Nov2fixtures still have no outcome. These are existing persisted live-shadow evaluations, distinct from historical research replay and from the new zero-score lanes above.

The actual latest main-panel version is `beyond-demand-engine-v1-structural-prior-shadow`. Reproducing `modelPerformanceService`'s latest-per-event rule from stored forecasts givesMAE4314.727273on11events;1313rows /24forecast events at the read. All adjustments0; no evaluated latest row was after kickoff or label confirmation. The0scores in the decision-summary RPC's newer encoder/P9lanes do not describe this older pipeline orC1v8.

Rows with zero scored targets mean **MAE=null**, not zero error. Inventory-path error and final-attendance error are different targets. Public availability is not confirmed paid sales or attendance.

### Full guardian chain: proven for one fail-closed encoder checkpoint

Korona603/P-3 cutoff11:15UTC:

- guardian dispatch11:18:58.798931UTC;
- [main workflow41819915267](https://github.com/NiedzielX/beyond/actions/runs/41819915267), created11:19:02UTC, completedSUCCESS11:19:53UTC;
- DB-derived preflight confirms `MODEL_INPUT_INSUFFICIENT`, attempted11:19:48.745719UTC, no prediction;
- fresh decisionRPC11:20:35UTC confirms encoder9/5/0 and unchanged production flags.

Details and private proof hash: `FROZEN_WINDOW_GUARDIAN_EVIDENCE_2026-11-04.md`. This proves guardian→existing encoder workflow→success→expected DB attempt. READY prediction/scoring, P9heartbeat, and deployment of the new daily-path SQL are separate evidence requirements. Historical missed windows remain missing.

## Cloud runtimes

All are bounded until **2026-11-05T09:30Z**, perform inference/scoring or window protection, and are **not an autonomous coding service**. Read current PID/launch files instead of trusting historical tool-session IDs.

| Process | Runtime directory under`/workspace/ops-runtime/` | Latest verified state |
|---|---|---|
| Daily v1worker, PID143488 | `2026-11-03-daily-path/` | Live process, recent model-matched cycle and byte-verified private backup; new issue captured11:15:09UTC |
| Encoder guardian, PID146478 | `2026-11-04-frozen-window-guardian/` | Genuine legal-window dispatch at11:18:58UTC; successful run/DB proof above |
| Drift worker, PID154636 | `2026-11-04-drift-comparator/` | Post-launch cycle verified; automatic legal capture11:19:58UTC, private backup verified |

Daily v1health:

```bash
python -m ml.start_daily_inventory_path_watcher_v1 --runtime /workspace/ops-runtime/2026-11-03-daily-path --status
```

HEALTHY requires actual process state, a recent successful cycle after launch, matching artifact, private read-back and valid deadline. Zombie/exited children are rejected. Do not kill an unrelated PID or start duplicates.

Drift status: inspect `watcher-launch.json`, actual PID state, `latest-cycle.json` and verified backup; its forecast artifact must match the persisted freeze. Initial driftPID154243failed DNS because its filtered environment omitted required cloud proxy settings. The corrected launch inherited the working environment and completed a new cycle; the failed launch remains recorded. See `.ai/lessons/2026-11-04-cloud-proxy-and-exited-workers.md`.

## Frozen daily artifacts and important limitation

- Learned daily v1: `artifacts/daily_inventory_path_v1.json`, SHA`1137e257494583374f768622feca343f2dd7d634ef2446198703f8c27fbd9525`, fitted once on16completed events /1,239rows. No refit.
- The exact pre-outcome audit reconciled all57issued points within9.10e-13places. **All120relative-value-history coefficients are0**; nine negative global/count/mask terms remain. Latest level and maximum prefix value still enter anchor/scale. Receiving a full prefix is not proof of learned value dynamics. Read `DAILY_PATH_COEFFICIENT_AUDIT_2026-11-04.md` before accuracy/mechanism claims. No measured error is inferred from this audit.
- Separate fixed comparator: `artifacts/daily_inventory_drift_comparator_v1.json`, SHA`332f6fd37bc2a09ce665668ef3c9c23d8d34ec3613f18435ec729d95d3bb43cf`, genuinely frozenNov4 11:06:27UTC after source publication. No fit or parameter search. **Predictor and precommit content hashes are now fixed under this version.**
- Comparator protocol: `DAILY_INVENTORY_DRIFT_COMPARATOR_PRECOMMIT_V1.md`. Genuine24-hour anchor,6-hour tolerance, actual elapsed-time velocity, zero clipping only; allows rises/declines/flat paths. Separate immutable ledger and`drift-v1/`private backup namespace. Score from the exact matching immutable v1target and recompute errors. First review requires8independent events with genuine+1labels from5clubs; no automatic activation.

Read-only prefix diagnostics keep the original full-cohort event-balanced headline. Zero-only/constant-positive/varying groups and reconciled contributions are descriptive; event counts across vintage groups can overlap. Commands/results are linked from the coefficient audit and `.ai/runs/2026-11-04-postgres-and-cloud-continuation.md`.

## Completed checks and deployment blockers

- Hosted Demand Engine **41819264406**: **312unit checks** plus original historical reproductions, bundle integrity and exact runtime checks. Includes13drift,6coefficient,8prefix-diagnostic and9worker-lifecycle cases.
- Isolated cloud chain **41819264228**: actual PostgreSQL16migration/contracts, sourceSQL→features, DB→pinned panel parser, Deno typecheck/policy/negative HTTP checks.20SQL+13adaptertests. Synthetic correctness evidence, not project deployment or model accuracy.
- Panel functional source`1a6dd609`: Chromium **41812968199**, TypeScript/build **41812968190** passed. Actual chart includes observed prefix, daily future points, vintages, matched scores and honest zero/missing/error states. Its new live feed remains undeployed.
- Source-statev2: `DAILY_INVENTORY_SOURCE_STATE_CONTRACT_V2.md`. Receipt/capture/known-time and active/visible-state contract plus seven-field adapter passed isolated integration. RPC remains undeployed and is not wired into frozen models. Do not join current flags onto history or append new columns to frozen fitting frames.
- **Project migration/admin binding is absent.** New daily-path SQL/Edge/managed schedule and live panel feed remain blocked; saved cloud setup draft is not applied. Do not ask for secrets in chat or mistake a working data-role binding for project admin access.
- Attendance labels remain a separate ingestion/evidence blocker. History last verified onNov3endedOct25; tracked Oct30–Nov2fixtures lacked confirmed outcomes then. Fresh11:20RPCstill reports0attendance scores. Do not invent outcomes.

Reviewable source: [backend draft PR209](https://github.com/NiedzielX/beyond/pull/209), stacked on208; [panel draft PR8](https://github.com/NiedzielX/BeyondTicketingPanel/pull/8). Main was not merged or changed. Actual-path review PDF/provenance remain private at`/workspace/ops-runtime/2026-11-04-review/`.

## Constraints to carry forward

Existing attendance/P9/SSP/Form5 policies, models and550-seat comparison remain frozen. All missed prospective windows stay missing, including historical event443P9T-24/encoderP-1 and event6P9T-48. Do not weaken support or reinterpret source zeros to repair eligibility. Korona hidden availability remains unknown; Widzew literal zero remains zero; Wisła Kraków VAO rights contract remains fail-closed.

MAE-01 diagnostic and MAE-02 weighting rejection are complete; MAE-03 context audit remainsDATA_BOUND. Follow the execution plan for new research. Do not repeat closed/exposed searches, and do not spend another session rerunning unchanged isolated checks. Next evidence is a genuine new forecast/outcome pair, not a more persuasive picture.

## Latest user research priority: C1 live MAE toward1,200

Read `C1_LIVE_MAE_1200_PLAN_V1.md`. Current C1policyMAE4121.45on11scored events;4events account for83.45%of error. Even an outcome-aware selector between current prior/live forecasts yields4103.05, not1200. Basic ranking/oracle diagnostic complete; underlying causes are not established. Next research task:matched-cohort audit of actual bad-event inputs/labels/anchor contracts and existing D2, then one separately precommitted challenger. No old-model retuning, cosmeticv3T1replacement, subgroup deletion or paid-sales claim.

## C1 audit execution —2026-11-04 12:20UTC

Read `C1_LIVE_MATCHED_AUDIT_RESULT_V1.md`: reusable fresh read-only exporter→audit executed;11events/44rows, C1policy4121.45vsD2P2 5157.52at identical persisted times. No train/serve mismatch found. Missing Wisła/Górnikseason-history inputs confirmed, their causal improvement unproven.18history checks+6outcomes remain unverified; public sites unreachable from this host. Private sources/results stay outside Git. New training-support-only challenger precommitted in `C1_TRAINING_EXPANSION_PRECOMMIT_V1.md`, pending implementation/fit at this entry; do not conflate it with an active upgraded C1. No old frozen artifacts or forecasts changed.

### C1 training-support challenger actually frozen —12:27UTC

See `C1_TRAINING_EXPANSION_RESULT_V1.md`. New separate20event/74rowpackage frozen once12:26:39UTC, estimatorSHA04dbdf1e5b8846782194f2ca1e833078a10238d1c9ca151b8391a869449027ba; original30features/Ridge10/policy unchanged. No training-MAEclaim. Current DBinference12:27returns0eligiblecandidates/0predictions/0scores; MAEnull. Privatefreeze/input/lineagebackupbyteverified. Prepared separate bounded collector untilNov6 20:30UTC; startup proof pending at this entry. FirsteligiblewindowNov5 17:00, later than oldworkersdeadline. Candidate needs genuinefuturepairedforecasts and30newscored events/8clubs. No oldmodel/score/gateway/productionwrites.
