# Context Extension v2 — Result 2026-10-18

Status: **COMPLETED / NO INCREMENTAL HISTORICAL C2 UPLIFT / NO PRODUCTION CHANGE**

Workstream:

**c2 — match context**

## Evidence source

GitHub Actions run: `39163152327`  
Tested head: `7df22ecee43040f68814cb9fd04f8c8e6db5e90f`  
Artifact: `c2-context-extension-v2-39163152327`  
Artifact ID: `12149487833`  
Artifact ZIP SHA256: `8f12266d270adb55eb24a41fb43a080640bc830b3915134d02de043dfcf7b5c7`  
Result JSON SHA256: `903362e62d15c962ad3f7969e08d09c1086d8fcbe9c1ad6a1718e0d5d92a62c`

CI:

- pinned runtime: PASS;
- compile: PASS;
- unit tests: **5/5 PASS**;
- PIT context-state tests: PASS;
- frozen a2+b2 baseline isolation: PASS;
- hard baseline reproduction assertions: PASS;
- full development/reference scoring: PASS;
- artifact upload: PASS.

`promotion_allowed = false`

Production remains unchanged.

## Baseline under test

C2 is measured incrementally over the settled historical a2+b2 stack:

- T-30: retained Structural Prior, no b2;
- T-14: retained Structural Prior, no b2;
- T-7: `hist31-leaf20-l2-1` + `ewma50-resid-k6-cap05-min3`;
- T-3: retained Structural Prior + `ewma50-resid-k2-cap05-min3`;
- T-1: retained Structural Prior + `ewma50-resid-k6-cap05-min3`.

Context candidates are compared against that full frozen historical stack, not against the old production-only baseline.

## Context families tested

### Sequence-aware sporting form

PIT-only completed-match state:

- win / unbeaten / loss streaks;
- home-only home streaks;
- last-3 vs previous-3 points acceleration;
- home-away sequence gaps.

### Continuous match-stakes / pressure

Built only from current completed-match table state:

- title pressure;
- current top-4 proximity pressure;
- current bottom-4 proximity pressure;
- direct points proximity;
- home / away / match maximum pressure.

These are transparent current-table pressure proxies, not claims about official final qualification/relegation outcomes.

Candidate groups were deliberately limited to:

- `NO_CONTEXT`;
- `sequence_only`;
- `stakes_only`;
- `sequence_stakes`.

No threshold/subset zoo was used.

## Selection protocol

Development only:

1. train 2021/22 -> evaluate 2022/23;
2. train through 2022/23 -> evaluate 2023/24.

A challenger must improve both development folds and achieve >=0.5% mean relative MAE improvement.

Only the frozen development-selected candidate is scored on exposed 2024/25 and 2025/26 references.

References cannot rescue an alternate development candidate.

## Result summary

| Horizon | Development selection | Mean reference improvement | Decision |
|---|---|---:|---|
| T-30 | `NO_CONTEXT` | 0.00 | no stable context extension |
| T-14 | `NO_CONTEXT` | 0.00 | no stable context extension |
| T-7 | `NO_CONTEXT` | 0.00 | no stable context extension |
| T-3 | `NO_CONTEXT` | 0.00 | no stable context extension |
| T-1 | `sequence_stakes` | **-36.97** | development-selected candidate fails references |

## Development diagnostics

### T-30

Mean development MAE improvement:

- sequence only: `-2.46`;
- stakes only: `-16.91`;
- sequence + stakes: `+0.64`, but folds disagree and improvement is below gate.

Result: `NO_CONTEXT`.

### T-14

All three non-zero families are development-negative:

- sequence only: `-47.08`;
- stakes only: `-53.51`;
- sequence + stakes: `-59.10`.

Result: `NO_CONTEXT`.

### T-7

All three non-zero families are development-negative:

- sequence only: `-19.82`;
- stakes only: `-15.67`;
- sequence + stakes: `-5.10`.

Result: `NO_CONTEXT`.

### T-3

Mean development gain is positive for all three families:

- sequence only: `+40.88`;
- stakes only: `+13.69`;
- sequence + stakes: `+20.15`.

However, none improves both development folds, so no candidate is eligible.

Result: `NO_CONTEXT`.

The exposed references are therefore not used to choose or rescue a T-3 context variant.

### T-1

All three context families pass the two-fold development gate.

Development mean improvements:

- sequence only: `+37.69`;
- stakes only: `+18.02`;
- sequence + stakes: **+46.76**.

Development selection freezes:

`sequence_stakes`

Reference scoring then fails:

2024/25:

- frozen a2+b2 baseline MAE: `1627.07`;
- context candidate MAE: `1672.15`;
- improvement: **-45.07**.

2025/26:

- frozen a2+b2 baseline MAE: `1695.96`;
- context candidate MAE: `1724.84`;
- improvement: **-28.88**.

Mean reference improvement:

**-36.97 MAE**.

Decision: reject. Do not post-hoc score/select `sequence_only` or `stakes_only` on references as a rescue.

## What remains in the Context Matrix

For the current 5-season historical dataset, the main remaining context categories are not suitable for another honest retrospective tournament:

- timing is already represented by calendar/kickoff features;
- opponent and pair history are already represented in Structural Prior;
- weather was historically negative;
- rivalry registry is forward research infrastructure and is not complete historical PIT truth;
- verified absences do not have complete multi-season PIT coverage;
- media/hype collection is forward-only and did not exist historically;
- search interest/social volume remain blocked or prospective;
- competition stage is not a meaningful missing historical dimension for the homogeneous Ekstraklasa league dataset.

Therefore adding another historical c2 grid would mostly create duplicated features, leakage-prone reconstruction, or post-hoc feature search against exposed seasons.

## Decision

> **Do not add sequence/stakes context to the historical Pre-Live v2 stack. Consider c2 sufficiently evaluated for the currently available five-season historical dataset. Freeze the historical Pre-Live v2 candidate stack from a2+b2, and keep rivalry/absence/hype context in prospective shadow until genuinely point-in-time evidence accumulates.**

Historical Pre-Live v2 candidate state after c2:

- T-30: retained Structural Prior; no b2; no c2;
- T-14: retained Structural Prior; no b2; no c2;
- T-7: `hist31-leaf20-l2-1` + `ewma50-resid-k6-cap05-min3`; no c2;
- T-3: retained Structural Prior + `ewma50-resid-k2-cap05-min3`; no c2;
- T-1: retained Structural Prior + `ewma50-resid-k6-cap05-min3`; no c2.

Production remains unchanged. The next engineering step is to freeze this exact **historical Pre-Live v2 candidate contract** with reproducible hashes/benchmarks before starting d2 learned live-updater work.
