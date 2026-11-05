# Panel ingestion freshness — investigation and production correction

November5,2026. User screenshot showed Motor–Raków(Oct27)waiting for kickoff and Radomiak–Śląsk(Nov2)as current alerts. Source investigation and correction:[merged PR9](https://github.com/NiedzielX/BeyondTicketingPanel/pull/9).

## Cause, verified against live public data

Public browser-role request15:37UTCreturned133exact rows; the dashboard projection had been refreshed seconds earlier. It contained26nonexcluded/noncompleted records, including2elapsedunresolved candidates. Fresh15:52:31UTCread confirms133rows and the same two stale semantic states. This is not established as anHTTPcache problem.

- Motor48812has291raw observations, latestOct27 18:23UTC, no canonical ticket_event. Source candidate remains`discovered`; the dashboard's generic raw-buffer branch maps it toBUFFERING_AWAITING_KICKOFFand emits a pending-fixture diagnosis. That text does not independently establish the candidate's actual gate/reason.
- Radomiak48101has0inventory observations and no canonical ticket_event. Source candidate remains`hidden_availability`,has_active_stage=false,show_available_tickets_count=false,lastseenNov2. Hidden data remain unknown, not zero sales/attendance.
- RefreshSQLapplies elapsed status only to tracked events. Candidate branches lack that transition. Promotion deliberately considers future kickoff only, so old unresolved candidates are retained. Do not retro-promote them or infer that a scheduled fixture was played.
- Frontend previously filtered onlyCOMPLETED_TRACKEDand loaded once on mount. Its header used the first projection row's refreshed_at, not actual inventory freshness; the metric copy overclaimed collector activity from saved snapshot existence.

## Delivered behavior

Current monitoring filters actual elapsed scheduled times at read time and counts only current/unknown-date eligible records. A separate **Minione nierozwiązane**view/banner retains the2old issues, timestamps, raw counts and diagnoses. It says their scheduled time elapsed, without asserting a played/completed match. Missing/invalid/unconfirmed dates remain visible.

The panel refreshes every60seconds while visible, on return/focus, and via a manual button. Failed refresh keeps the last good rows with a visible warning/retry, rather than silently presenting stale data as current. It separates successful browser read, oldest projection refresh and per-row real inventory/raw/discovery timestamps. Projection age above20minutes warns visibly. Requests explicitly bypass browser caching; source buffers and DBrows are unchanged. Copy no longer asserts an active collector or a working pipeline solely from a status/count.

## Actual release, separate from model and PR8work

The release branch was based directly on then-current panelmain67a2082f63e5d23ce0000275026b72ed7c2eb2a2. Only9ingestionfix/test/workflowfileswere reviewed; no daily-path/C1card bundle fromPR8, no SQL, model, source schedule, snapshot/outcome or prospective-contract change.

Final reviewed head**39b4ff9847ea748f13e1e08f57f06b7b7ae40814**has successful hosted TypeScript/build,9pure contracts and actual Chromium component tests, including7synthetic refresh/history/error scenarios. Final-head runs42058663894and42058664064succeeded. VercelPreview7578232366succeeded. LocalnpmregistryHTTP403prevented a local build; hosted results are actual success, not a claim about local execution.

Normal draft→ready/head-pinned merge succeeded**15:50:31UTC**, yielding panelmain**cfb3d675d7fbb2cd4c6fc008f73c019ab33beb40**. No force/ref/review bypass. Main's tree exactly equals reviewedhead; its authentic signed Gitobject was imported only after its exact object hash matched. Existingmainworkflow42059061853andChromium42059061759bothsucceeded.

**VercelProduction deployment7578292659SUCCESS at15:50:46UTC**, exact mergedmainSHA. Deployment URL:https://beyond-ticketing-panel-4zzf11tos-n-b334.vercel.app. Public production entry:https://beyond-ticketing-panel.vercel.app/. This proves the exact corrected artifact was deployed toProduction. Direct productionURLretrieval fromthishoststillreturnsURLError, so no direct liveDOMinspection is claimed. ComponentDOMtests are hosted synthetic correctness tests, not screenshots ofproductiondata.

A separate actual Nodeexecution of the exact shipped time-partition contract on fresh133publicbrowserrows gives**24current/2elapsedunresolved**, preserves every source row, and retains both old observation times. This verifies real-data classification without pretending it is a direct productionDOMobservation.

## Evidence and next state

Private proofs:`/workspace/ops-runtime/2026-11-05-panel-ingestion-freshness/`:actual data/read receipts, source candidate rows, final-head/mainjob steps, merge/check/deployment/integrity receipts and exact read-time real-data contract result. Private31filebackup135051bytes,SHA`ad77322aa3e78d3b9d9b975cb41a2e75c64332baa5e3842460d843654eb0eb48`, namespace`panel-ingestion-freshness-v1/`, was independently fetched, decompressed, hash-checked and restored; ProductionSHA/status validated from restored receipts. Failed artifact-download/directURLprobes remain disclosed; no downloaded screenshot claim.

The isolated release changes UIingestionmonitoring only. Modelproduction flags remainfalse/0; actual persistedC1v8still17scored/MAE3248.807865at15:52read. Frozen26collector remains0scores/nullMAEand healthy. PR8dailyfeed/C1cardwork remains separate/unmerged; newdaily-pathSQL/Edge/managedfeedstillrequiresadminbinding. P9fresh-new-rowacceptance remains pending next449T48window16:30UTC; no historicalmissbackfill.
