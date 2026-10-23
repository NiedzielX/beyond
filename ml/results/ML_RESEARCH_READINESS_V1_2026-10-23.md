# ML Research Readiness v1 — 2026-10-23

## Purpose

The remaining roadmap is data-bound. This checkpoint defines objective trigger points without inventing an arbitrary sample floor for P4 before any labeled context outcomes exist.

## Canonical readiness RPC

`public.ml_research_readiness_v1()`

The function is read-only from a modelling perspective and changes no forecast.

## Hard triggers

### P7 Long168

Research starts only when:

`independent_events_gt_72h >= 9`

At the trigger:

1. freeze exact event and as-of identities first;
2. persist the frozen manifest/hash;
3. only then open the 72–168h challenger cycle.

Current state:

- independent events >72h: `8`;
- rows >72h: `110`;
- trigger: `false`.

### Long72 genuine prospective score

Trigger when:

`scored_genuine_events >= 1`

Current state:

- reproducible forecast rows: `48`;
- genuine scored events: `0`;
- trigger: `false`.

The first score is an evidence review trigger only. It must not be used to retune the frozen package.

### P4 next-opponent availability

Trigger when:

`next_opponent_ready_rows >= 1`

Current state:

- next-opponent sidecar rows: `48`;
- READY rows: `0`;
- trigger: `false`.

When the first READY row appears, inspect feature availability and variation before predeclaring any ablation sample floor. Do not choose the floor after seeing model performance.

## Fixture-context evidence growth

Current Long72 fixture-context state:

- sidecar rows: `48`;
- READY: `46`;
- two original pre-schedule rows remain permanently unavailable.

This confirms the evidence pipeline is collecting successfully even though no final attendance label is available yet.

## Why no P4 N-threshold is declared yet

The correct minimum independent-event count depends on whether the new context features actually vary across events.

For example, a nominal N=9 is not useful if all nine events have the same fixture-density value or no observed next-home fixture.

Therefore the sequence is precommitted as:

1. first genuine labeled/READY context appears;
2. inspect only feature availability/variation and independent-event coverage;
3. declare the ablation sample floor before fitting/comparing any context challenger;
4. freeze that gate;
5. only then run P4 model selection.

This avoids both leakage and outcome-driven threshold selection.

## Production boundary

- no forecast change;
- no frozen package change;
- no model selection;
- `live_adjustment = 0`.
