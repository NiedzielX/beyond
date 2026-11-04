# Beyond — operational handoff

Updated **2026-11-04 17:36 UTC**. Production remains **OFF**: `production_change=false`, `live_adjustment=0`.

Read strategy and state first: `MAE_RESEARCH_ROADMAP_V6.md` → `EXECUTION_PLAN_CURRENT.md` → `PROGRESS_TRACKING.md` → `TRAJECTORY_FORECASTING_PLAN_V1.md` → this handoff. This file supplies operational state; it does not define a competing MAE strategy.

## Current execution snapshot — 2026-11-04 17:36 UTC

This supersedes earlier dated operational counters. Existing frozen models, review gates, historical misses and production flags remain unchanged.

| Lane / target | Latest genuine evidence | Current interpretation |
|---|---|---|
| Original C1 v8 attendance | 101 prediction rows / 17 events / 16 scored; policy MAE 3428.29, prior 3303.29, raw 6540.76 | Five delayed genuine outcomes expanded the cohort; the old 4121.45 on 11 events is not a model-improvement comparison |
| Expanded Ridge20 attendance | Frozen once at 12:26 UTC; 0 future predictions / 0 scores / null MAE | Collect only new final24 observations |
| Direct-person median attendance | Frozen once at 13:44 UTC; separate verified worker cycle; 0 predictions / 0 scores / null MAE | Same 20-event / 74-row training information; no training-MAE claim |
| Frozen encoder attendance | 10 attempts / 6 predictions / 3 scores; MAE 1529.71 vs 923.27 | Early worse results; no promotion or retuning |
| P9 v1 / v2 attendance | v1: 7 / 0 / 0; v2: 6 attempts / 3 predictions / 3 score rows across 2 events | v2 event MAE 1984.72 vs 1248.35; keep lanes separate |
| Daily v1 inventory | 2 mature points / 2 events; MAE 258.94 vs persistence 326.50; 71 points pending at 17:14 | Availability is a separate target; 1 of 2 events improves; too early for a decision |
| Fixed drift inventory | 5 attempts / 16 future points / 0 scores at 17:27; 2 READY issues | Actual post-freeze forecasts now exist; no drift-MAE claim |

### Completed data work and remaining source boundary

Inserted 15 verified absent history records at actual knowledge time 17:18:36 UTC and synced five exact outcomes: 6, 443, 444, 446, 447. Old outcomes and forecast counts remain unchanged; 900 original training cells reproduce before and after import. Event445 remains missing because source and canonical kickoff differ by 10 minutes. See `VERIFIED_ATTENDANCE_IMPORT_RESULT_2026-11-04.md`.

The existing history view / C1 export / structural Edge feed omit source knowledge timestamps. A separate guard now preserves actual availability and connects to the unchanged frozen feature builder. Actual Górnik449 / T-3 input audit: unfiltered season_home_n=6 versus correctly known=1 at the 16:30 cutoff. All 15 new records are excluded before ingestion and available at the later actual read. The registered PKO competition alias is handled explicitly. This is tested input integration, **not deployed serving enforcement**. Never regenerate old priors using newly obtained history. See `ATTENDANCE_KNOWLEDGE_TIME_AUDIT_V1.md`.

### Automation and immediate next actions

1. Finish the separately versioned raw-source export → per-cutoff guard → unchanged predictor integration and its release verification. Do not change frozen collectors to repair old evidence.
2. Protect Widzew7372 / P-3 at **19:15 UTC (20:15 Warsaw)** and Wisła448 / P9 T-48 at **19:30 UTC (20:30 Warsaw)**. Invalid or absent inventory remains a coverage failure.
3. P9 heartbeat run41873299368 succeeded but child41873320229 failed on a non-ready zero-neighbor freeze. Main-based draft PR212 fixes only that negative path; hosted contract tests pass. An actual in-window local DB attempt was recorded at17:17 UTC. **P9 redundancy remains NOT DONE** until corrected hosted execution succeeds and produces the expected DB record. No main merge occurred. See `P9_NONREADY_OPERATIONAL_FIX_2026-11-04.md`.
4. The distinct positive encoder chain is proven: guardian → mainrun41867901421 SUCCESS → Górnik449/P-3 immutable prediction_id6 at16:31:16 UTC. This does not prove the P9 chain.
5. Original daily/drift/guardian workers stop **Nov5 09:30 UTC**; both C1 research collectors stop **Nov6 20:30 UTC** and depend on this host. Median PID200395 has an actual post-launch capture → scorer → verified private backup cycle and a separate byte-verified restore. Inspect process state and current cycles before renewal. First possible new C1 final24 window: **Nov5 17:00 UTC (18:00 Warsaw)**. First review remains 30 new scored events / 8 clubs.

Panel PR8 has a successful Preview and an independent C1 accuracy card. Its public browser-role endpoint now returns the actual16-event / 3428.29 result. Production main and the new daily-path livefeed deployment remain unchanged / pending. No production activation: `production_change=false`, `live_adjustment=0`.

## Earlier13:25UTC action snapshot — superseded above

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

The three original processes below are bounded until **2026-11-05T09:30Z**, perform inference/scoring or window protection, and are **not an autonomous coding service**. Read current PID/launch files instead of trusting historical tool-session IDs.

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

## C1 MAE1200 execution — current at12:40UTC

- Matched audit completed: `C1_LIVE_MATCHED_AUDIT_RESULT_V1.md`. All11events/44genuine C1-time representatives; C1policyMAE4121.45vsD2P2 5157.52. C1numerical parity/900original training cells verified. No D2promotion. Wisła/Górnikzero season-home-history confirmed; its causal MAEbenefit remains unproven. External sites unreachable,18history checks+6outcomes remain null/unverified.
- New independent experiment: `C1_TRAINING_EXPANSION_PRECOMMIT_V1.md` / `C1_TRAINING_EXPANSION_RESULT_V1.md`. One20event/74row/11clubfit, same30features/Ridge10/preprocessing/policy. Frozen12:26:39UTC, estimatorSHA04dbdf1e5b8846782194f2ca1e833078a10238d1c9ca151b8391a869449027ba. All20are training, never prospective holdout. No training-MAEclaim or oldv8mutation.
- **Separate cloud collector ACTIVE:** PID169529, `/workspace/ops-runtime/2026-11-04-c1-training-expansion/`, started12:37:36UTC, interval900s, deadline **Nov6 20:30UTC**. Actual process stateSsl and post-launch12:37:41UTCcycle verified: currentcollector→bothfrozenruntimes→scorer→private read-back. Current0eligible/0forecasts/0scores, MAEnull. This is actual no-due health proof, not positive forecast/DB proof or a managed scheduler. Collector/scorer implementation hashes locked in `collection-contract.json`; do not edit these helpers under this version after collection starts.
- Private forecast/attempt/input/score recovery namespace`c1-expansion-v1/`cannot change originaldaily/driftlatestmanifests. First post-launchcompressedbackupSHA3d31d87cd4cb9e9e0d90ee781d2596a35781ce35a34b9ca46795fee447a101e9; actualbyte-readbackverified. Separate initialprivatefreeze/training/inputbackupSHA6fa1dcb191aeda5fe69e5303045dd94412d51a42007c72d564da0260aa0b2357.
- First upcoming final24windows: **Motor5091 Nov5 17:00UTC**, Wisła448 Nov5 19:30UTC. Existing workers stopNov5 09:30UTC; theirdeadlinewasnotchanged. Newcollector survivesonlywhilethishostsurvives. Check launch/PID/source-lock/recentcycle/backup before renewal; don'tduplicateorbackfill.
- Raw positive input follows the actual SQLschema: `collect_c1_training_expansion_v1` resolves omitted prior.target_as_of_at and verifies identicalpriorID/values/times, then calls unchangedfrozencapture. Scorer accepts onlylaterconfirmedoutcomes, neverinventorylabels. Firstreview30newscored events/8clubs withpaireduncertainty; firstreviewimmutable. Earlyresultsdescriptive.
- Review: draft [PR210](https://github.com/NiedzielX/beyond/pull/210), stacked on209. Local354unitchecks passed; source4fe12fc hosted DemandEngine41830872028passed includingnewartifactintegrity, collection/scoringguards and priorreproductions. No merge/main/production/gatewaywrites. Source verification, relational/managed deployment and actual future positive-capture/scoring evidence remainpending.

## Latest authorized continuation and panel status —13:25UTC

Savedacceptedresearchsupplement:`C1_MAE_LITERATURE_EXECUTION_SUPPLEMENT_V1.md`. Target-freeobjectiveauditcomplete:`C1_OBJECTIVE_GEOMETRY_AUDIT_RESULT_V1.md`;20/74privateframehashverified, equal-eventmasscorrect, capacitylossgeometryquantified, nofit/inference/targetparsing/trainingMAE. Sixnewtests/backend360checks pass. C1L1treesalreadytested; structuralweightingalreadyrejected. Next:newexactmedian-linearobjectiveprecommitbeforefit, notcosmeticrepeat; existing20eventcandidate/collectorunchanged.

PanelPR8source dbc71a39 passedTypeScript/build41837200916andactualcomponentChromium41837200785. NewC1cardreadsexistingpublicview, realbrowserroleGETvalidated11scored/MAE4121.454326. VercelPreview7547081765SUCCESS at13:20:39UTC: https://beyond-ticketing-panel-2no5gkfi3-n-b334.vercel.app/. LatestProduction/mainstill67a2082f,Oct28deployment; noProductionpromotion. Newdaily-pathpermanentfeedstillundeployed/adminbindingblocked; directsiteURLunreachablefromhost,noDOMinspectionclaim. Evidence:`PANEL_PREVIEW_STATUS_2026-11-04.md`. DistinguishsuccessfulfrontendPreviewfromstillmissingmanagedbackendfeed.
