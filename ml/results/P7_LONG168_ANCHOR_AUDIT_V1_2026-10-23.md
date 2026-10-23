# P7 Long168 T-7 Anchor Audit v1 — 2026-10-23

## Status

**PASS — REAL 8-EVENT HISTORICAL PIT REPLAY AUDIT COMPLETE / NO CHALLENGER FIT**

Workflow:

- `P7 Long168 Executor v1`;
- run id: `39967794585`;
- main commit: `ba85b29cf270e4db83b21fecd8f99aa40567e1af`;
- event: `push`.

The audit ran automatically after the P7 executor was merged to `main`.

The real tournament steps were skipped because this was not an explicit `workflow_dispatch -> mode=execute` run and the research gate remains below nine independent events.

Production remained unchanged:

`live_adjustment = 0`

## Current Long168 gate

At audit time:

- independent events with valid observations >72h: `8`;
- P7 research-start threshold: `9`;
- real P7 tournament: **NOT RUN**.

Audited events:

`1, 3, 4, 5, 11, 15, 18, 19`

## Anchor audit result

Status:

`P7_T7_ANCHOR_REPLAY_READY`

Evidence class:

`historical_pit_replay`

Persisted forecast claim:

`false`

Counts:

- independent event count: `8`;
- anchor count: `8`;
- skipped target-attendance invariance events: `0`.

Anchor package SHA256:

`7e21831d4da724cd6906ccb34688eb8f4fadd39923054510dea1b33162862362`

## Target-attendance invariance

Status:

**PASS**

Checked event IDs:

`1, 3, 4, 5, 11, 15, 18, 19`

No exact attendance row event IDs:

`[]`

Sentinel attendance used by the mutation gate:

`999999999.0`

Tolerance:

`1e-9`

For every audited target event, changing that event's exact-kickoff attendance to the sentinel value left its replayed T-7 P50 unchanged within the required tolerance.

This confirms that the target event's final attendance is excluded from its T-7 Structural Prior replay by the chronological cutoff.

## Frozen artifact byte validation

The workflow verified the actual repository bytes before replay.

T-7 Structural Prior artifact:

- file: `structural_prior_t7_v1.joblib`;
- SHA256: `97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`.

Historical runtime:

- file: `historical_runtime_v1.csv.gz`;
- SHA256: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Both byte-level gates passed.

## Replay lineage

Artifact version:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Support versions:

- events: `c1-alpha-v7-events-v1`;
- attendance: `c1-alpha-v7-attendance-v1`;
- sporting: `c1-alpha-v7-sporting-v1`;
- aliases: `c1-alpha-v7-aliases-v1`;
- Long168: `d2-long-horizon-168-rows-v1`.

Support semantic SHA256:

`fe62811e376d8c7432b6ee18bb37d2081901068ff42c77075479f7aec6402297`

Replay rules:

- attendance: current-season attendance rows with kickoff strictly before the T-7 cutoff only;
- sporting: completed fixture date strictly before the T-7 cutoff local date;
- target event actual stripped from event metadata: `true`.

This remains historical factual replay evidence, not system-as-known persistence.

## Export / audit hashes

Long168 export JSON SHA256:

`e033a7146df00ccb1a821499e699909ec4a39935a2b26fc09df37ce223ad71b4`

Anchor audit JSON SHA256:

`54bbaaba2c890e2072197fa71a0ffff6dba88750b788536258e1cbb052018e18`

Uploaded artifact:

- artifact id: `12507727407`;
- name: `p7-long168-anchor-audit-v1-39967794585`;
- artifact ZIP digest: `sha256:ff4dffbb07d53c452a6b5a739b2fe027fe8569bf2cc31d552d10bb64c408f6bc`;
- retention: 90 days.

## Scientific interpretation

This audit closes the remaining **anchor execution uncertainty** for the currently available historical P7 event set:

- the frozen T-7 artifacts are exactly the expected bytes;
- all 8 eligible events can be replayed;
- no target event is skipped;
- the target final attendance does not influence its T-7 anchor;
- replayed anchors are explicitly classified as historical PIT replay, not persisted forecasts.

It does **not** answer whether a 72–168h live challenger improves MAE.

No learned P7 candidate was fitted and no leaderboard was opened.

## Next action

Do nothing model-selection-related while the gate remains `8/9`.

When `public.ml_research_readiness_v1()` reports `P7_LONG168_START = true`:

1. explicitly dispatch `.github/workflows/p7-long168-executor-v1.yml` with `mode=execute`;
2. freeze exact Long168 identities first;
3. verify the T-7 anchor package against the frozen event set;
4. only then attach labels;
5. run strict forward-event fixed-candidate evaluation;
6. calculate event-block uncertainty;
7. persist the research decision;
8. keep production unchanged.

## Decision

**ANCHOR REPLAY PATH VALIDATED — WAIT FOR NINTH INDEPENDENT >72H EVENT.**
