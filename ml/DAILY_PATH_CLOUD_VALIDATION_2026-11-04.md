# Daily path — isolated cloud validation and bounded execution

Updated2026-11-04. Draft PR:https://github.com/NiedzielX/beyond/pull/209. Models and production flags remain unchanged.

## Verified cloud tests

Actual Actions run**41811081476**, source`b1e5e942504695e2445b72ac02dc913007584559`, passed:

- PostgreSQL16service applied the real migration;9synthetic contract tests verified capture/retries, window/lineage/flag rejection, atomic rollback, private permissions, immutable ordinary-field updates/deletes, latest valid zero-target matching, invalid/future-target rejection, idempotent scores and feed.
- Both ready/scored feeds produced by that DB passed the exact companion panel parser pinned to`3983c10403c32892d66e7c51b62107b1e2272f4f`.
- Actual Deno typecheck of the prepared Edge entry point.
- Six gateway policy/header tests; opaque Supabase keys stay in`apikey`and are not treated as JWTs. The gateway also retains exact main/repository/workflow scope and requires signed token lifetime claims/RS256.
- The actual Deno entry point ran on isolated localhost with inherited credentials removed and rejected wrong HTTP methods/unauthenticated malformed requests with405/401.

Initial PostgreSQL failures were test assertions against GENERATED ALWAYS identity columns; those fail before custom triggers. Tests were corrected to mutate ordinary fields. **No SQL/model change was needed.** Unit success does not show a production deployment or valid signed live OIDC request.

Hosted Demand Engine run**41811862372**passed269Python unit tests including9guardian checks, plus fixed historical reproductions and existing bundle integrity/runtime checks. No frozen model was refitted.

## Browser interaction verification

Companion panel source`1a6dd609473bfdbb3730d98ccfb8cb1e24e18f09`:actual Chromium run**41812968199**and TypeScript/production-build run**41812968190**passed. The isolated harness tested the actual React component:full daily points, vintage selection, refresh, keyboard inspection, zero-valued later outcome/errors, lead support warning, mobile page width, absent/HTML/invalid export and failed-input states. Zero-only prefixes now explicitly avoid implying confirmed sellout or sales. Synthetic screenshots/result artifacts belong to those test runs; no fake research feed is committed or served in production.

The initial browser tooling step failed on the moving runner; the workflow now pins supportedUbuntu24.04and captures installation diagnostics. Both actual chart/browser and app-build checks pass. The live app's new feed remains undeployed; this is isolated component behaviour, not a successful live end-to-end feed request.

Separately, the **actual immutable forecast paths**were plotted for review in private `/workspace/ops-runtime/2026-11-04-review/daily-path-review.pdf`with a feed SHA provenance file. `DAILY_PATH_INITIAL_OUTPUT_REVIEW_2026-11-04.md`records near-flat-prefix/steep-forecast and zero-only-source limitations before outcomes, without modifying predictions or claiming accuracy.

## Bounded cloud inference

The prior foreground worker stopped after2026-11-03T20:54:53Z. OnNov4a detached worker was launched; it completed09:44:27and09:59:27UTCcycles, retained57pending future-day points and verified private Storage backup. No missed issue was reconstructed. It is bounded until**2026-11-05T09:30UTC(10:30Europe/Warsaw)**and still depends on this cloud host surviving.

Inspect genuine state:

```bash
python -m ml.start_daily_inventory_path_watcher_v1 --runtime /workspace/ops-runtime/2026-11-03-daily-path --status
```

Restart only if stopped and after checking live due state:

```bash
python -m ml.start_daily_inventory_path_watcher_v1 --runtime /workspace/ops-runtime/2026-11-03-daily-path --panel-feed /workspace/BeyondTicketingPanel/public/research/daily-inventory-path-v1.json
```

The launcher refuses duplicates; HEALTHY requires live PID plus a recent successful cycle, correct frozen hash and verified backup. A launch alone is not execution proof. The default new launch is bounded23hours; exact deadline can be supplied with`--watch-until`within24hours.

First already-issued targets matureNov4at**17:00UTC(18:00Europe/Warsaw)**. Before genuine labels mature, MAE staysnull. The process runs inference/scoring; it is not a perpetual coding agent.

## Existing frozen-window protection

At10:00UTCthe existing main frozen-encoder workflow was active/configured twice hourly, but latest scheduled success was03:22UTC. An independent guardian now polls the existing read-only decision summary and can dispatch **only the existing main workflow**for an exact unrecorded0..+90minute checkpoint. Failed-input windows are recorded honestly; missed/future/pre-activation/captured checkpoints are never repaired.

Guardian runtime:`/workspace/ops-runtime/2026-11-04-frozen-window-guardian/`; private`guardian-latest.json`,`guardian-state.json`,`guardian-audit.jsonl`,`guardian.pid`. It polls every300seconds and stops byNov5 09:30UTC. Duplicate guardians, active workflow runs and10minute dispatch cooldown are checked. At its first observed cycle no checkpoint was due, so it correctly dispatched nothing.

Next genuine encoder cutoff:Korona603P-3atNov4 11:15UTC(12:15Warsaw), currently insufficient source input. A manually dispatched health check of the existing main workflow is separate from guardian due-window execution. Do not claim the guardian→workflow→successful run→expected DB record chain before that genuine checkpoint occurs. P9heartbeat DONE is not implied.

## Still blocked / not deployed

The new SQL migration, new Edge gateway and new daily GitHub schedule remain **undeployed/disabled**. The environment lacks project migration/admin binding; the saved setup draft is not applied. Isolated PostgreSQL/Deno/UI-contract tests do not remove this deployment requirement. Existing attendance lanes, historical misses, model parameters and550-seat contract remain frozen. `production_change=false`, `live_adjustment=0`.
