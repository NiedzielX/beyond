# Paired drift24 source support check — 25 November 2026

## Result and evidence boundary

This note records the source-history prerequisite for the new paired PERS–drift24 runtime in [.ai/specs/2026-11-25-rolling72-paired-drift24-runtime.md](../.ai/specs/2026-11-25-rolling72-paired-drift24-runtime.md) and its fixed parent recipe. It is not an activation, issue, score, forecast or accuracy result.

The requested single bounded read-only Supabase query for fixture `27049` did not execute. Automatic approval review initialization failed with an internal Habitat thread-store HTTP 500; the tool reported that no action was executed. No alternate route or retry was used. Therefore current seal/pair/gap counts, live job state and current cache24 runtime are **unknown** in this report. Machine-readable nulls are in [the aggregate proof JSON](ROLLING_72H_PAIRED_DRIFT24_SOURCE_SUPPORT_2026-11-25.json).

Root's handoff supplied the current operational observation: as of approximately **2026-11-25 11:50 UTC**, the first source capture was approximately **2026-11-24 15:05 UTC**, so the history was still under 24 hours old. That is a parent-provided observation, not an independently queried result. A capture at the 24-hour boundary would first be approximately available at **2026-11-25 15:05 UTC**, conditional on a valid complete pair and no intervening source break. The comparator still requires activation before a new issue opportunity; old PERS bundles cannot receive retrospective paired drift values.

Previously recorded operational evidence says cache job 24 completed a normal run in **40.340116 s at 2026-11-25 11:14 UTC**, after a prior 120 s timeout, with job definitions unchanged ([run record](../.ai/runs/2026-11-24-pers-feed-panel-and-io.md)). This is not a fresh health check of job 24 or the source/PERS jobs at this report's watermark.

## Activation checklist

Use the runtime specification as the contract; these checks do not authorize activation. Before root activates the new lane:

1. Freeze the additive runtime SQL and its exact manifest bytes/hash only after the assigned PG16 suite and independent formula/clock/label/denominator/ACL review pass. Keep source, PERS, E5/B, v5 functions, jobs and ledgers unchanged.
2. Confirm the source lane's manifest, SQL hash, issue cutoff and scoring cutoff bind exactly. A drift-ready forecast requires the full 24–30 h anchor, complete sector and membership identity, and no intervening known break. Anchor availability is not an activation or PERS-issue gate: missing support must produce paired `FALLBACK_PERS` from the first valid origin.
3. Confirm actual projection-reference, calculation-completion, issue and target clocks are independently stamped and satisfy the specified 90 s/source-age bounds. Keep targets independently kickoff-gated and labels on the shared exact source target.
4. Prepare the new service-only job to run after source capture and PERS, but leave scheduling disabled until root's activation decision. Do not write paired forecasts before activation; do not retrofit prior PERS issues.
5. At activation, verify exact manifest/hash idempotency, service-only grants, frozen release-copy hashes and status. The first scheduled future cycle must prove a new post-activation origin and actual issue clocks separately from synthetic tests.
6. Report per-horizon support, fallback, coverage and paired outcomes only from the new cohort. Until genuine labels accrue, MAE and the fixed 30-fixture/8-club review remain unknown; do not claim attendance accuracy, causality or a 1200-seat result.

## Current disposition

Local implementation and test work may continue under the runtime spec. Source-history readiness and current job health remain unverified by this bounded check. No new paired lane is active, and no new MAE result is claimed pending root activation and genuine future evidence.
