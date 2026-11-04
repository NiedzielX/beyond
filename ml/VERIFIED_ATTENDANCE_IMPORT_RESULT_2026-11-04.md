# Verified attendance history and delayed prospective outcomes

## Source and import proof

Hosted read-only source run [41840960556](https://github.com/NiedzielX/beyond/actions/runs/41840960556) retrieved six fixed public pages successfully. Actual source text, hashes and retrieval receipts are private under `/workspace/ops-runtime/2026-11-04-public-attendance-source-audit/`. Main sources: https://www.frekwencyjny.pl/kluby/wisla-krakow, https://www.frekwencyjny.pl/kluby/gornik-zabrze, https://www.frekwencyjny.pl/kluby/lech-poznan and https://www.frekwencyjny.pl/. Independently checked existing top-error labels Wisła16=33000, Lech5=37407, Górnik11=27659, Śląsk23=12391 are consistent; no old label correction.

At **2026-11-04T17:18:36.410962Z**, inserted exactly **15 absent verified `ml_match_history` records** through the existing data API, append-only. Ten completed current-season Wisła/Górnik home fixtures plus five exact completed target matches. Explicit club aliases, completed sporting fixtures, season, competition, Warsaw DST, exact kickoff and positive attendance checked. Existing same-fixture/conflicting counts are rejected, not overwritten. Original900training feature cells reproduce before and after import; frozen hashes unchanged. No historical prior rematerialization, new fit, forecast rewrite or missed-window repair.

Source retrieval occurred about13:45UTC, but **model knowledge starts at actual verification/import17:18:36UTC**. `source_observed_at` uses that actual time; original retrieval time/hash/line/GitHub run remain in `source_payload`. Historical publication time is unverified. Never claim these records were available at old forecast cutoffs.

Existing exact-match outcome-sync RPC inserted five outcomes: **6 (Lech)=36229, 443 (Cracovia)=8611, 444 (GKS)=10482, 446 (Wisła Płock)=4131, 447 (Raków)=5089**. Read-back proves all old outcomes unchanged. **445 remains blocked/missing**: source kickoff17:10UTC versus canonical17:00UTC; attendance3396 is not imported or coerced into a matching fixture. Independently verify timing before resolving.

## Actual evaluation after genuine labels

Only existing frozen scorers were executed, on forecasts already persisted before the outcomes. No retro-forecasting. DB status read17:18:38UTC:

| Existing frozen lane | Independent scored events | Incumbent MAE | Challenger / governed MAE | Interpretation |
|---|---:|---:|---:|---|
| C1 v8 original9, latest per event |16|3303.287177 prior|3428.290290 policy|Existing package; 101 prediction rows /17 forecast events unchanged |
| Frozen encoder attendance |3|923.271989|1529.709219|Early paired evidence worse by606.437230; keep frozen, no promotion |
| P9 family fallback v2 |2 (3 score rows)|1248.354372|1984.717101|Early event-balanced evidence worse by736.362730; keep separate from v1 |
| P9 v1 |0|null|null|No eligible prediction to score |

C1 raw-live MAE6540.763694, representative-window policy4134.587744. Previous C1 policy4121.454326 on11events remains its dated result: **the new3428.29 is a larger16eventcohort, not evidence of a model improvement**. The old eleven-event same-time audit remains intentionally frozen and must not silently expand. Current shared prior beats the C1policy on the16events. New20eventRidge and direct-person median both still have zero future scores/nullMAE; these newly confirmed old fixtures do not validate either Nov4freeze.

Local daily-path17:14UTC evidence concerns **available inventory**, not attendance: two independent events / two mature 24h points, learnedMAE258.941674 vs persistence326.50, delta−67.558326; one of two events improves. Motor5091 errors430.778657 vs642; second event10500 errors87.104692 vs11. Total73issued points,71pending, no missing mature labels at this snapshot. Too little evidence to claim supported generalization or retune. Keep all-zero and difficult prefixes in the denominator.

`production_change=false`, `live_adjustment=0` throughout. Updated data is available to existing C1status consumers; no panel production deployment occurred.

Private source/verification recovery contains17audit files,56,721bytes, SHA256 `cf411e24b2623d464e671f34acf38f3e2567f3d1f9c6dfc6fc56eceb0294d224`; private Storage read-back and decompression verified. No raw source exports were committed.
