# Beyond Ticketing — d2 Long-Horizon Live v1 Plan

Last updated: **2026-10-21**

Status: **ACTIVE TRACK-B R&D / LONG72 STAGE1 COMPLETE / STAGE2 ACTIVE / NO PRODUCTION CHANGE**

Parent evidence:

- `ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`;
- `ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`;
- `ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`;
- `ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`.

Active contract:

`ml/D2_LONG72_STAGE2_RELIABILITY_GATING_V1.md`

## Why this workstream exists

The original d2 problem uses the final 24 hours and anchors rows on T-1.

The v2-v3 equivalence audit proved:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

So another final24 tournament merely because v3 has a new freeze ID would be cosmetic.

Long-horizon R&D therefore asks a materially different question:

> **Can live ticket trajectory improve attendance forecasting before the final 24 hours?**

## Production and Track-A boundary

Do not modify:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Production remains:

`live_adjustment = 0`

Everything in this document is Track-B research until separate promotion evidence exists.

---

# Stage A1 — additive earlier-live export — COMPLETE

Do not mutate:

`v7-final24 -> export_c1_alpha_v7_final24_rows_v1`

Additive research route:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Contract:

- maximum 168h before kickoff;
- 6h buckets;
- latest source snapshot per event x bucket;
- same eligible-event and verified-capacity rules as final24;
- same `get_live_trajectory_features_v1_1_asof` PIT feature function;
- explicit per-event coverage metadata.

The export is service-role / main-only gateway protected.

---

# Stage A2 — coverage/readiness audit — COMPLETE

Canonical result:

`ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`

Main run:

`39638563805`

Observed C1-eligible labeled event coverage:

- 14 total eligible events;
- 13 with valid PIT data beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Inherited minimum independent-event threshold:

`N = 9`

Decision:

`BUILD_FIRST_LONG_HORIZON_MODEL_TO_72H`

Therefore:

- 24–48h = learned research allowed;
- 48–72h = learned research allowed;
- 72–168h = diagnostic only until N>=9.

Do not lower the N=9 threshold simply to open T-7 earlier.

---

# Stage A3 — frozen 0–72h data + anchor contract — COMPLETE

Canonical result:

`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`

Main run:

`39640723942`

Artifact ID:

`12365352293`

Dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

Frozen set:

- 14 independent events;
- 130 rows;
- 0–24h: 50;
- 24–48h: 45;
- 48–72h: 35.

Anchor rule:

- `0<h<=24` -> T-1 checkpoint hold;
- `24<h<=72` -> T-3 checkpoint hold;
- no future checkpoint interpolation.

The current-season replay uses exact kickoff-date capacity lineage and horizon-specific PIT forecastability.

V2 and v3 are equivalent in this 0–72h anchor contract because both retain identical T-3/T-1 packages.

The changed v3 T-7 anchor is intentionally not used until the 72–168h learned band satisfies the independent-event threshold.

---

# Stage B1 — early-live model tournament — COMPLETE

Canonical result:

`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`

Run:

`39642620259`

Artifact ID:

`12365399256`

Scope:

`24<hours_to_kickoff<=72`

Independent validation unit:

`event`

Method:

`Leave-One-Event-Out`

All labels are exposed historical R&D evidence. LOEO protects event independence but is not a temporal holdout.

## Stage-1 candidate set

- anchor zero correction;
- train-fold bias;
- inventory linear extrapolation;
- Ridge alpha 10;
- Ridge alpha 30;
- Huber;
- conservative HGB.

No external model zoo / Chronos sweep was opened for this first early-live tournament.

## Stage-1 decision

Historical research lead:

`inventory-linear-extrapolation`

Overall 24–72h:

- anchor MAE `3707.14`;
- inventory MAE `3254.68`;
- gain `+452.46 / +12.21%`.

24–48h:

- gain `+675.33 / +18.22%`.

48–72h:

- anchor MAE `4592.38`;
- inventory MAE `3916.71`;
- gain `+675.68 / +14.71%`.

## Stage-1 limitations

Raw inventory is not ready to freeze as an early-live package:

- event improvement rate `46.15%` overall;
- event-balanced bias `+1458.93 seats`;
- overall worst event degradation `3100.60 seats`;
- 48–72h worst degradation `3741.79 seats`;
- original exposed subset worsens by `485.52 MAE`;
- later exposed subset improves by `1953.22 MAE`.

The signal is useful but heterogeneous and tail-risky.

---

# Stage B2 — reliability / tail-risk gating — ACTIVE

Predeclared contract:

`ml/D2_LONG72_STAGE2_RELIABILITY_GATING_V1.md`

Stage B2 keeps the Stage-B1 expert fixed.

Frozen expert:

`inventory-linear-extrapolation`

Reliability formula:

`final_delta = reliability * frozen_inventory_delta`

No model retraining and no same-data hyperparameter search.

## Fixed policies

- P0 anchor;
- P1 raw inventory;
- P2 observation maturity;
- P3 correction magnitude;
- P4 data quality;
- P5 combined reliability.

## Advancement gates

A new policy advances only when all gates pass:

1. positive MAE uplift overall 24–72h;
2. positive uplift 24–48h;
3. positive uplift 48–72h;
4. >=50% retained raw uplift overall;
5. >=50% retained raw uplift 24–48h;
6. >=50% retained raw uplift 48–72h;
7. >=25% reduction in overall worst-event degradation;
8. >=25% reduction in 48–72h worst-event degradation;
9. >=25% reduction in absolute bias;
10. positive historical uplift on original exposed subset;
11. positive historical uplift on later exposed subset.

If nobody passes:

`RAW_INVENTORY_RETAINED_NO_STAGE2_POLICY_PASSED`

This closes only the fixed Stage-B2 reliability policy set. It does not close the long-horizon workstream.

Do not relax gates after results are visible.

---

# Next after Stage B2

If a Stage-2 policy is selected:

1. seal a versioned long72 historical research package;
2. define a separate forward/prospective scoring contract;
3. keep final24 Track-A Ridge/P2 unchanged;
4. score new events without retuning;
5. require new evidence before any promotion discussion.

If Stage B2 fails:

1. retain raw inventory only as the Stage-1 historical research lead;
2. diagnose failure mechanism using already-produced row evidence;
3. open a materially different reliability/target hypothesis under a new ID;
4. do not tune the fixed Stage-B2 policies against the same exposed outcomes.

Independently, when 72–168h reaches N>=9:

- reopen the T-7-aware live problem under a separate contract;
- use the changed Pre-Live v3 T-7 anchor where it is genuinely PIT-valid.

---

# Evidence rules

- no random snapshot split;
- independent unit = event;
- no future interpolation;
- no outcome-derived live features;
- no relabeling exposed historical events as unseen;
- append-only newer events do not mutate frozen experiments;
- pinned artifacts/hashes before every downstream experiment;
- a successful historical R&D run is not production evidence.

---

# Engineering rule

Every material experiment:

`source -> tests -> CI -> pinned inputs -> machine JSON -> artifact + hashes -> human result -> decision -> canonical docs`

## Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- v3 research-only;
- long-horizon work research-only;
- production `live_adjustment = 0`.
