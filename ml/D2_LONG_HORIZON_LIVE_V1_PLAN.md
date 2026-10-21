# Beyond Ticketing — d2 Long-Horizon Live v1 Plan

Last updated: **2026-10-21**

Status: **TRACK-B R&D / LONG72 HISTORICAL PACKAGE SEALED / FORWARD SCORING NEXT / NO PRODUCTION CHANGE**

Canonical evidence:

- `ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`;
- `ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`;
- `ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`;
- `ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`;
- `ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`;
- `ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`.

## Why this workstream exists

The original d2 problem uses final24 only.

The v2-v3 equivalence audit proved:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Therefore a new final24 tournament solely because Pre-Live v3 exists would be cosmetic.

Long-horizon R&D instead tests whether live ticket trajectory improves forecasts before final24.

## Production and Track-A boundary

Do not modify:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Production remains:

`live_adjustment = 0`

Everything in this document remains Track-B research until separate forward/prospective evidence exists.

---

# Stage A1 — additive earlier-live export — COMPLETE

Existing final24 export remains immutable:

`v7-final24 -> export_c1_alpha_v7_final24_rows_v1`

Additive research export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Contract:

- max 168h before kickoff;
- 6h buckets;
- latest source snapshot per event x bucket;
- same event/capacity eligibility as final24;
- `get_live_trajectory_features_v1_1_asof`;
- explicit coverage metadata;
- service-role/main-only access.

---

# Stage A2 — coverage/readiness — COMPLETE

Run:

`39638563805`

Coverage:

- 14 eligible labeled events;
- 13 beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Frozen independent-event threshold:

`N = 9`

Decision:

`BUILD_FIRST_LONG_HORIZON_MODEL_TO_72H`

Therefore:

- 24–48h learned research allowed;
- 48–72h learned research allowed;
- 72–168h remains diagnostic only until N>=9.

Do not lower N=9 simply to open the T-7-aware window early.

---

# Stage A3 — frozen 0–72h data + anchor — COMPLETE

Run:

`39640723942`

Artifact:

`12365352293`

Dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

Frozen set:

- 14 events;
- 130 PIT-safe rows;
- 0–24h: 50;
- 24–48h: 45;
- 48–72h: 35.

Anchor rule:

- `0<h<=24` -> T-1 checkpoint hold;
- `24<h<=72` -> T-3 checkpoint hold;
- no future checkpoint interpolation.

Current-season replay uses exact kickoff-date capacity lineage and horizon-specific PIT forecastability.

Because v2/v3 T-3 and T-1 are identical, the 0–72h anchor is valid under both freezes.

---

# Stage B1 — early-live expert selection — COMPLETE

Run:

`39642620259`

Artifact:

`12365399256`

Scope:

`24<h<=72`

Validation:

`event-level LOEO on exposed historical evidence`

Historical research lead:

`inventory-linear-extrapolation`

Overall:

- anchor MAE `3707.14`;
- raw inventory MAE `3254.68`;
- uplift `+452.46 / +12.21%`.

24–48h uplift:

`+675.33 / +18.22%`

48–72h uplift:

`+675.68 / +14.71%`

Raw inventory limitations:

- only 46.15% of events improve overall;
- bias `+1458.93 seats`;
- worst degradation `3100.60 seats` overall;
- worst degradation `3741.79 seats` in 48–72h;
- original exposed subset worsens by `485.52 MAE`.

Result:

> Useful early-live signal, but raw expert alone is too unstable to freeze as a forward research package.

---

# Stage B2 — reliability / tail governance — COMPLETE

Run:

`39644319080`

Artifact:

`12366826274`

Stage-2 JSON SHA256:

`a9daa834e15b4f313b15c3e809033b7d79e4ed4357f61a8f5071e6bf20359d8c`

Predictions SHA256:

`489ba62156f19d3b915fda1b9f1ef506fb81603d4286a01e8ad4b799c58bce4b`

Decision:

`STAGE2_RELIABILITY_POLICY_SELECTED`

Selected:

`P2-observation-maturity`

Other eligible policies:

- P3 correction magnitude;
- P4 data quality;
- P5 combined reliability.

P2 wins by lowest overall event-balanced MAE under the fixed selector.

## Selected P2 metrics

Overall 24–72h:

- anchor MAE `3707.14`;
- P2 MAE **`3012.63`**;
- uplift **`+694.51 / +18.73%`**;
- event improvement rate **`61.54%`**;
- bias `+917.05 seats`;
- worst degradation `1488.34 seats`.

Versus raw Stage B1:

- another `242.05 seats` lower MAE;
- worst-event degradation reduced `52.00%`;
- absolute bias reduced `37.14%`.

24–48h:

- MAE `2752.56`;
- uplift `+954.58 / +25.75%`.

48–72h:

- MAE `3927.67`;
- uplift `+664.71 / +14.47%`;
- event improvement rate `70%`;
- worst degradation `2413.28 seats`.

Historical exposed subsets:

- original subset `+103.55 MAE`;
- later subset `+1640.04 MAE`.

Both signs are positive after P2 gating.

---

# Stage B3 — historical package seal — COMPLETE

Package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Manifest:

`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`

Status:

`FROZEN_HISTORICAL_RESEARCH_PACKAGE`

Exact early-live package for `24<h<=72`:

`T-3 anchor + P2 reliability * inventory-linear-extrapolation delta`

P2 observation weights:

- first `0.25`;
- second `0.60`;
- third+ `1.00`.

P2 time weights:

- 60–72h `0.75`;
- 48–60h `0.90`;
- 24–48h `1.00`.

Reliability:

`min(observation_weight, time_weight)`

Package evidence class:

`EXPOSED_HISTORICAL_R_AND_D`

Production allowed:

`false`

Forward evidence required:

`true`

---

# Stage C — forward scoring without retuning — NEXT

Purpose:

> Test whether the sealed historical package generalizes to genuinely later events while preserving exact package logic.

## Forward-scoring contract requirements

1. pin package ID + manifest hash;
2. never refit inventory extrapolation from outcome labels;
3. never change P2 weights after future results are observed;
4. create/store row predictions at their actual as-of timestamps;
5. preserve event, snapshot, capacity, anchor and package lineage;
6. only score against attendance outcome after the prediction exists;
7. keep event as independent scoring unit;
8. report overall 24–72h plus 24–48h and 48–72h;
9. report MAE, bias, event improvement rate, worst degradation and revision magnitude;
10. classify evidence explicitly.

## Evidence classes

At minimum distinguish:

- `DELAYED_LABEL_DIAGNOSTIC`: prediction lineage predates outcome availability, but event is not a clean post-package-freeze prospective sample;
- `TRUE_POST_FREEZE_PROSPECTIVE`: event/predictions occur after the sealed package cutoff and package was unchanged before outcome.

Do not count delayed-label diagnostics as true promotion evidence.

## Frozen package must not learn from scoring

Forward outcomes may:

- reveal failure modes;
- justify a future new challenger ID;
- trigger a new research cycle.

They may not:

- alter the current package weights;
- alter the current inventory expert;
- alter the current selector retrospectively.

---

# Separate future branch — 72–168h / T-7-aware R&D

The changed Pre-Live v3 T-7 package becomes materially relevant only beyond the current 72h learned boundary.

Reopen this branch only when:

`independent events with >72h valid coverage >= 9`

Then create a separate versioned target/anchor experiment. Do not mutate the sealed long72 package.

---

# Evidence rules

- no random snapshot split;
- independent unit = event;
- no future interpolation;
- no outcome-derived live features;
- no relabeling exposed historical events as unseen;
- pinned inputs/hashes for every downstream experiment;
- historical success is not production evidence;
- new forward outcomes do not retune frozen packages.

# Engineering rule

Every material experiment:

`source -> tests -> CI -> pinned inputs -> machine JSON -> artifact + hashes -> human result -> decision -> canonical docs`

## Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- Pre-Live v3 research-only;
- long72 P2 package research-only until forward evidence exists;
- production `live_adjustment = 0`.
