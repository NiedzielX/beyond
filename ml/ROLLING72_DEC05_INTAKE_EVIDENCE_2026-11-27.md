# Rolling72 Dec 5 intake evidence — 27 November

## Current evidence

| Fixture | Roboticket offer | Kickoff (Warsaw) | Retained inventory probe | Evidence status |
|---|---:|---|---|---|
| Cracovia–Widzew | 10896 | 5 Dec, 14:45 | 6,846 available; 25 sectors; 25 price-area rows; observed 26 Nov 11:05:11Z | Source compatibility only |
| GKS Katowice–Legia Warszawa | 5772 | 5 Dec, 20:15 | 1,907 available; 17 sectors; 17 price-area rows; observed 26 Nov 11:08:00Z | Source compatibility only |

The exact normalized payload hashes and probe clocks are retained in
`ROBOTICKET_CRACOVIA_10896_INVENTORY_PROBE_2026-11-26.json` and
`ROBOTICKET_GKS_5772_INVENTORY_PROBE_2026-11-26.json`. The intake spec records
independent schedule/direct-page agreement for both. Its latest database
observation says GKS is `discovered`, with no admission or registered ticket
event; the spec likewise requires a current Cracovia duplicate/admission
check before proceeding. These dated probes do not establish present inventory,
current DB state, alias validity, collection readiness, or admission.

## Fresh source packet and identity checks — 27 Nov

Root retained the public round-17 TheSportsDB response and exact event
responses for this intake. The independent event IDs are **2490337**
(Cracovia–Widzew) and **2490338** (GKS–Legia). Both event lookups and both
direct ticket pages returned HTTP 200. Their raw bytes and receipts are held
privately under `/tmp/beyond-dec05-source-2026-11-27`; the round response and
receipt are there as well. The individual receipt files bind request URL,
completion time, byte count and SHA-256. The schedule lookups completed 27 Nov
at 11:56:13Z and the direct pages at 11:56:15Z. The hosted league-shadow lookup
matched both events, and five exact active alias rows were matched, including
**Legia Warsaw**.

These checks supply candidate identity evidence for plan preparation. They do
not constitute the final just-in-time runtime recheck or a committed admission.
Root is running the existing `buildRoboticketAdmissionPlan` workflow against
the retained packet. Preserve its preparation result and exact acquisition-index
hash with the receipts; do not submit from a stale plan if the ten-minute
freshness limit has elapsed. Do not copy or publish raw response bodies.

## Existing procedure and precedent

Use `ml/roboticket_admission_plan_v1.ts` for read-only evidence composition and
`ml/roboticket_admission_request_v2.ts` for the exact explicit admission-v2
request. The plan consumes the original acquisition-index bytes plus indexed
ticket HTML, TheSportsDB response, active alias export and dated league shadow;
it verifies hashes and separates request/response/source clocks. The v1 source
registry validator is an offline consistency check after the admission response
and runtime evidence exist. It cannot establish that a database write occurred.

The 15 Nov result (`ROBOTICKET_CONTROLLED_ADMISSION_PREPARATION_RESULT_2026-11-15.md`)
is a six-fixture example, but its acquisition index and source bodies live only
in `/tmp` and are not reusable evidence for these offers. On 24 Nov, Jagiellonia
5520 was admitted using a refreshed direct page and provider response whose
actual GET completion time was retained; RPC accepted receipt 6 / ticket event
27049 at 14:53:30.470686Z with zero backfill and no model activation. That run
also explicitly excluded 1,113 legacy-buffer rows. Apply those clock and
forward-only controls to each new identity; do not reuse or re-clock the old
index, probe receipt, or legacy candidate buffers.

## Gaps before admission

The source packet, hosted shadow matches and five active alias matches are now
available for offline plan construction. Still required: retain the generated
acquisition index and successful preparation result; run a fresh runtime
recheck no more than 10 minutes before request submission; and perform current
duplicate/admission and candidate-buffer checks for both identities. The 26
Nov inventory probes are insufficient substitutes for current inventory and
readiness. Admission RPC result and committed registration readback remain
pending. The new prospective lane's manifest, pinned issue/score deadlines,
78-hour grace, damped-trend freeze and cohort/window design are separate
deliverables; this intake preparation does not admit either fixture or open
that lane.

## Action sequence

1. Finish and preserve the existing plan output and acquisition index for the
   retained round/event/ticket packet. Keep raw bodies private and unchanged;
   record actual GET completion clocks separately from provider HTTP `Date`
   values.
2. Run the existing admission-plan CLI against that index, the freshly read
   active aliases and the dated shadow export. Confirm exact home/away aliases,
   Roboticket offer IDs, independent league event IDs, kickoff instants and
   direct-page H1 identities; require preparation-only output with no rejects.
3. Perform current read-only duplicate/admission, candidate-buffer and
   collector-mode checks. Reject any identity already admitted or bound to a
   different fixture. Ensure historical candidate buffers cannot be promoted.
4. Within 10 minutes before submission, repeat the runtime direct-page,
   provider, alias, shadow and database identity checks. Use genuine source
   completion clocks. Submit only through the existing
   admission-v2 path, with backfill zero and model activation/live adjustment
   disabled. Capture the exact request, response, receipt, and committed
   registration readback.
5. Verify registration is committed before allowing a normal collector run.
   Only later captures may enter the opportunity ledger. Keep the two fixtures
   distinct stable admission identities and report actual readiness, late
   starts and coverage gaps.

This is local, offline preparation only. No admission request was built or
submitted, no hosted state was read or changed, and no commit was made.

## Fresh plan result

The four retained HTTP bodies, five active aliases and two current shadow
records were passed through `buildRoboticketAdmissionPlan`. Both exact
offers returned `PREPARATION_REQUIRES_RUNTIME_RECHECK` with
`SOURCE_EVIDENCE_COMPOSED`. This is a preparation receipt for the pair/date
and source bindings. A fresh source/runtime check, admission write and the
new lane's committed registration are still required.
