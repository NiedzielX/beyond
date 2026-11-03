# Daily inventory path v1 — implementation precommit

Recorded **2026-11-03 16:29 UTC**, before fetching this lane's development export or fitting/evaluating a candidate. New target/mechanism; all previous attendance and SSP results remain exposed. Existing frozen artifacts, workflows and production flags are unchanged.

## Scope and target

Implement a research-only daily prefix → future-day public `available_total` path, independent of attendance priors. No private transactions required. `available_total` is publicly observed inventory, not net paid sales. No automatic production promotion or claimed accuracy improvement.

Initial delivery is executable local/cloud research tooling: read-only export, dataset/coverage audit, one candidate, persistence baseline, immutable local shadow ledger, JSON future-path payload and panel rendering support. A local ledger or a successful CLI is not proof of deployed Supabase persistence or a daily GitHub scheduler. Those require separate deployment and full-chain verification.

## Daily dataset

- Issue cutoffs `kickoff_at - N*24h`, N=60…1. Future targets are each remaining daily cutoff strictly before kickoff: lead=1…N-1. P-1 can have an attempt with no remaining daily targets; never invent a post-kickoff inventory label.
- Inputs use the full genuine available prefix from P-60 through issue time, not the attendance v1 168h cap. Deterministic duplicate handling: highest snapshot ID at exact timestamp, then latest real observation per UTC hour. Preserve actual timestamps, no interpolation/forward-fill. Daily model compression retains the latest real observation in each of 60 backwards 24h bins and an explicit observation mask; it does not create daily observations.
- Initial input eligibility: at least 4 hourly-deduplicated observations spanning at least 24h, latest no older than 6h. Missing/non-finite/negative values, explicitly inactive or hidden source states and source/measurement changes fail closed. A genuine explicit zero is valid for this new inventory target; no division by first inventory. Frozen attendance v1's separate gates are untouched.
- Measurement identity must be explicit and preserved. Historical public snapshots may lack source-state metadata; mark that limitation and never infer hidden states or purchase/release causes from counts.
- Target rule: latest genuine observation at or before target time, no older than 6h, under the same measurement identity. Ties choose greatest snapshot ID. Only targets captured by the declared export/training cutoff are eligible labels. Missing labels remain unscored; report eligible/possible counts.

## Candidate fixed before results

Model ID `daily-inventory-direct-median-v1`; baseline `daily-inventory-persistence-v1`.

- One pooled direct quantile-linear residual model (`QuantileRegressor`, quantile=.5, alpha=.01, solver=highs); no parameter or architecture search. Each lead is predicted directly, not recursively fed in as an observed input.
- Prefix-only scale=max(1, maximum prefix available_total). Target=(future available_total - latest available_total)/scale. Decode with latest + scale*prediction and clip only at zero. Do not force monotonicity or use inferred future capacity.
- Features: prefix context of length125: constant1, issue days-to-kickoff/60, observed prefix span in days/60, latest staleness in days, log1p(prefix count)/log1p(1440), then60 backwards daily-bin values (relative to latest, divided by scale) and their60 masks. With h=lead_days/7, concatenate h*context and h²*context (250features); fit without an intercept. Empty bins have numerical zero plus mask=0; genuine zero retains mask=1. The latest bin includes issue time; no future observation enters a feature.
- Training weights proportional to scale / labeled training-row count for the event, normalized to mean one. This aligns ratio L1 with equal-event inventory error in seats. Duplicate event/issue/lead training identities are rejected. Fit only labels and prefixes available by the declared training cutoff.
- Minimum fit support: five distinct training events. Save JSON coefficients, feature/version contract, training event IDs, cutoff, dataset manifest and artifact hash. No refits of existing artifacts.

## Evaluation and exposure

Development export and offline replay are **retrospective diagnostics only**, including events previously used in other experiments. Never call them untouched/prospective or select a revised v1 from their results.

Deterministic diagnostic split: event-level chronological 70/30 split by kickoff (same-kickoff events stay together). Fit earlier group only using labels available by the first eligible test issue cutoff; if fewer than five train events remain, report insufficient evidence instead of changing the split/gates. No random prefix split. Test events are absent from training. The optional final research fit uses completed events only, with all labels bounded by the explicit fit cutoff; subsequent previews are not prospective evidence.

Report paired baseline/candidate MAE and signed bias on identical targets; within-event mean errors first, then equal-event mean. Report lead +1/+3/+7 separately, complete lead support, event/club counts, label/prediction coverage and tail errors. These inventory-path metrics are separate from attendance MAE and its frozen 550-seat gate. No new business or production gate is asserted from a first diagnostic result.

Genuine prospective evaluation begins only after an artifact is frozen and an attempt is written within issue time…+90min for a target event excluded from fitting. Retain every forecast vintage. Input source cutoff and model-training cutoff must not exceed issue time; target snapshots are attached later only for scoring. Any future scientific claim must define an additional pre-outcome review/sample contract; this implementation precommit does not promise production eligibility.

## Local immutable ledger and payload

- Separate issue attempts and points keyed by event, issue time, model version, target time. Include exact execution time, source/data/model hashes, original prefix lineage and `production_change=false`.
- Prospective writes outside the legal issue window are rejected. Idempotent identical retries are accepted; conflicting retries are rejected, not overwritten. No retrospective preview can be inserted as prospective evidence.
- Point payload: ticket_event_id, issued_as_of_at, target_at, lead_days, model_version, predicted_available_total, baseline_available_total, source/data/model identity and evidence_kind.
- Score against subsequent genuine labels under the same deterministic matching contract. Score records preserve target snapshot identity. Revisions create a new issue vintage and do not replace earlier predictions or scores.

## Verification

Meaningful tests cover future-input leakage, full prefixes beyond 168h, missing/hidden/zero semantics, gaps and target tolerance, source changes, same-event grouping and temporal training bounds, equal-event metrics, decoded learned multi-day outputs, artifact roundtrip, exact legal-window boundaries, idempotency/conflicts and preservation of older daily vintages. No result on synthetic test data is advertised as model accuracy.

Implementation refinement recorded **2026-11-03 before the first real development export, real-data fit or evaluation**: the initial additive lead feature was insufficient to represent prefix-dependent future slopes. It is replaced by the explicit lead×prefix and lead²×prefix basis above, without an intercept. This is a structural model-capability correction from code inspection, not selection from forecast errors. Synthetic tests only had been run; no real-result-driven alpha/cap/architecture search occurred. All other dataset/evidence rules remain unchanged.
