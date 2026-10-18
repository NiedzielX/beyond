# Beyond Ticketing — Demand Forecast Development Plan v2

Ostatnia aktualizacja: **2026-10-18**

Status: **CANONICAL ACCURACY ROADMAP**

Pełne zasady eksperymentów, walidacji i CI/CD:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

## Główny cel

> **Dopracować model maksymalnie teraz i obniżyć MAE tak daleko, jak pozwalają uczciwe, reprodukowalne dane i walidacja PIT-safe.**

Nie optymalizujemy developmentu pod „zamknięcie” kolejnych literek roadmapy.

Negatywny wynik jednego challengera nie zamyka całego workstreamu.

Niższe średnie MAE również nie wystarcza do promocji, jeśli challenger tworzy nieakceptowalny tail risk.

## Docelowa architektura

### Pre-Live Model v2

`a) historia + b) current-season regime + c) match context -> najlepszy forecast przed live`

### Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> live delta / revised forecast`

## Kolejność developmentu

1. **a2 — Historical / Structural Prior optimization — ACTIVE**
2. **b2 — Current-season regime**
3. **c2 — Match context**
4. **Freeze Pre-Live v2**
5. **d2 — Continuous Live Updater**

Skrót:

`a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2`

Frozen C1 v8 prospective scoring działa równolegle i nie jest retunowane.

---

# 0. Stan wyjściowy

## Structural Prior

Obecny production incumbent działa dla wszystkich pięciu horyzontów.

| Horizon | 2024/25 historical MAE | 2025/26 historical MAE |
|---|---:|---:|
| T-30 | 1,889.4 | 1,846.3 |
| T-14 | 1,748.5 | 1,870.4 |
| T-7 | 1,777.7 | 1,802.3 |
| T-3 | 1,661.7 | 1,775.1 |
| T-1 | 1,651.7 | 1,742.8 |

Evidence base:

- 5 sezonów Ekstraklasy;
- 1,530 meczów;
- 7,650 PIT horizon rows;
- pełne verified capacity coverage.

Production:

`live_adjustment = 0`

Current Structural Prior bundle pozostaje production incumbent do explicit promotion.

## Co już ma Structural Prior

Current feature store zawiera już część a/b/c:

- historia frekwencji i rolling windows;
- current-season home mean / last / r3 / ratio;
- opponent draw;
- pair history;
- PPG / GD/game;
- last-5 form;
- tabela i gaps;
- top/bottom interactions;
- rest / congestion;
- calendar/time context.

Dlatego nowe eksperymenty muszą testować **nową informację lub lepszą reprezentację**, nie kopiować istniejące features pod inną nazwą.

---

# 1. a2 — Historical / Structural Prior optimization

Status: **ACTIVE / STAGE 1 COMPLETE / STAGE 2 NEXT**.

Cel:

> **Wycisnąć możliwie najmocniejszy baseline z obecnego historycznego evidence zanim zaczniemy uczyć kolejne warstwy korekcyjne.**

## 1.1 Stage 1 — Pre-Live Baseline Optimization v1 — COMPLETED

Canonical evidence:

`ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`

Run:

`39156711796`

Protocol:

- development train: 2021/22 + 2022/23;
- candidate selection: 2023/24 only;
- holdout 1: 2024/25, train through 2023/24;
- holdout 2: 2025/26, train through 2024/25;
- only incumbent + development-selected candidate scored on holdouts;
- exact frozen incumbent assertions;
- feature completeness gate;
- one change at a time;
- no automatic promotion.

Tested candidate families:

- feature-group ablation;
- recency weighting;
- selected model-family challengers.

### Stage-1 summary

| Horizon | Dev-selected candidate | Mean incumbent MAE | Mean selected MAE | Mean improvement | Decision |
|---|---|---:|---:|---:|---|
| T-30 | `ablate-rest_congestion` | 1,867.82 | 1,864.11 | +3.71 | retain incumbent |
| T-14 | `recency-linear_075` | 1,809.45 | 1,798.25 | +11.19 | retain incumbent; mixed seasons |
| T-7 | `model-hist_absolute_31` | 1,789.98 | **1,721.18** | **+68.81** | stage-2 robustness candidate |
| T-3 | `incumbent` | **1,718.39** | 1,718.39 | 0.00 | retain incumbent |
| T-1 | `recency-linear_075` | **1,697.28** | 1,707.36 | -10.07 | retain incumbent |

### Stage-1 conclusions

#### T-30

Ablating rest/congestion improves both reference seasons numerically, but only by +7.25 and +0.17 MAE. The event improvement rate remains below 50%, one median worsens, and worst-event degradation reaches +1,162.

**Decision: no champion change.**

#### T-14

Linear newer-season weighting improves 2024/25 by +31.38 MAE but worsens 2025/26 by -9.00. Mean is +11.19.

**Decision: directional recency evidence only; no champion change and no holdout retuning.**

#### T-7

`model-hist_absolute_31` is the only material stage-1 lead:

- development improvement: **+97.36 MAE**;
- 2024/25 improvement: **+105.55 MAE**;
- 2025/26 improvement: **+32.06 MAE**;
- mean reference improvement: **+68.81 MAE**;
- median AE improves both reference seasons;
- p90 improves on 2024/25 and is roughly neutral on 2025/26.

However:

- worst degradation 2024/25: **+3,685.74** on `Śląsk Wrocław – Raków`;
- worst degradation 2025/26: **+4,233.11** on `Lech – Arka Gdynia`.

**Decision: advance to robustness stage 2, no champion change yet.**

#### T-3

Incumbent wins development.

**Decision: retain incumbent.**

#### T-1

Linear recency wins development but mean reference MAE is **10.07 worse** and reference seasons disagree.

**Decision: challenger not proven; retain incumbent.**

## 1.2 Stage 2 — T-7 Hist31 robustness / fixed blend — NEXT

Question:

> Can we keep a meaningful part of the T-7 Hist31 MAE improvement while reducing severe event-level degradation?

Required candidates must be predeclared before scoring reference holdouts.

At minimum test:

- incumbent only;
- fixed incumbent/Hist31 blends;
- Hist31 only.

Recommended fixed challenger form:

`prediction(alpha) = (1-alpha) * incumbent + alpha * hist31`

with a small predeclared alpha set such as:

- 0.25;
- 0.50;
- 0.75;
- 1.00.

Selection:

- 2023/24 development only;
- primary metric MAE;
- exact deterministic tie rule;
- tail diagnostics reported but reference holdouts may not choose alpha.

Required output:

- MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- event improvement rate;
- worst-event degradation;
- exact worst-event identity;
- development-selected alpha;
- unchanged result on both reference seasons.

No automatic promotion.

## 1.3 Remaining a2 research after T-7 stage 2

Stage 1 does not exhaust a2.

Still justified:

### Additional model-family comparison

Where technically appropriate and pinned/reproducible, evaluate:

- CatBoost;
- LightGBM;
- XGBoost;
- regularized linear / GAM-style alternatives;
- validated ensembles.

Do not add dependencies only for complexity. Each family must have a clear reason and the same evidence protocol.

### Feature contribution follow-up

Stage-1 ablation is evidence about current model behavior, not proof that removed information is globally useless.

Follow up only where:

- effect is material;
- development and references are directionally coherent;
- a better representation of the feature group is plausible.

### Recency weighting follow-up

T-14 shows mild mixed evidence that newer-season weighting may matter.

Do not tune weights against exposed references. Any next recency experiment must predeclare a new policy family and select only on development.

### Residual / club calibration

Check for stable PIT-safe club residual structure.

Any calibration must:

- shrink low sample sizes;
- avoid club memorization;
- be evaluated out-of-sample;
- report per-club and tail behavior.

## Exit condition a2

a2 kończy się dopiero, gdy:

- główne feature groups mają contribution evidence;
- sensowne recency policies zostały sprawdzone;
- current model families + uzasadnione challengers zostały porównane;
- material leads mają robustness/tail analysis;
- per-horizon champion jest jawnie wybrany;
- pełny scorecard i artefakty są zapisane;
- champion changes, jeśli jakiekolwiek, przechodzą explicit freeze/promotion step.

---

# 2. b2 — Current-season regime

Status: **PARTIALLY TESTED / NOT EXHAUSTED**.

## Co już zrobiono

`Current Season Adjustment v1` testował:

`historical norm -> current-season mean/r3 delta -> bounded post-model correction`

Wynik:

- T-30/T-14/T-3/T-1: `NO_ADJUSTMENT`;
- T-7: development winner pogorszył oba reference holdouts;
- no positive mean holdout improvement;
- no production change.

Evidence:

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

Wniosek:

> **Nie promujemy tego mechanizmu. Nie uznajemy b) za zakończone.**

## 2.1 Residual regime index — priority after a2

Po zamrożeniu championa z a2 zbudować historyczny PIT residual:

`residual = actual attendance - incumbent prediction available before that match`

oraz:

`demand_ratio = actual / expected`

Na poprzednich zakończonych home matches tego samego sezonu testować:

- mean residual;
- median residual;
- EWMA residual;
- rolling r3 / r5;
- mean/median demand ratio;
- robust residual po ograniczeniu wpływu ekstremów.

Cel:

> mierzyć, czy klub w tym sezonie **systematycznie bije lub nie dowozi naszego własnego forecastu**, a nie tylko czy ma inną surową średnią niż historycznie.

## 2.2 Reliability / shrinkage

Testować sample-size-aware reliability.

Przykład hierarchii:

`club current season -> club historical residual -> league current season -> zero`

Nie pozwalać 1–2 meczom wywołać dużej korekty.

## 2.3 Season-stage effect

Jawnie ocenić, kiedy current-season signal staje się użyteczny:

- po 2 home matches;
- po 3–5;
- po 6+;
- późna faza sezonu.

## Exit condition b2

Workstream można uznać za wystarczająco przebadany dopiero po:

- residual-regime challengers;
- shrinkage variants;
- sample-size diagnostics;
- per-horizon result;
- per-season holdout result;
- explicit decision from the full scorecard.

---

# 3. c2 — Match context

Status: **AUDITED + ONE CHALLENGER TESTED / NOT EXHAUSTED**.

## Co już mamy

Structural Prior już ma PIT-safe:

- opponent draw / pair history;
- PPG;
- GD/game;
- last-5 form;
- table positions/gaps;
- top/bottom interactions;
- rest / congestion.

## Co już przetestowano

`Future Fixture Context v1`:

- next-home timing;
- next-home attractiveness;
- bounded cannibalization proxy.

Wynik:

- brak positive mean holdout improvement;
- brak poprawy obu reference seasons dla któregokolwiek horyzontu;
- evidence class `SCHEDULE_AS_RECORDED_RETROSPECTIVE_PROXY`;
- no production change.

Evidence:

- `ml/MATCH_CONTEXT_AUDIT_V1.md`;
- `ml/results/MATCH_CONTEXT_FUTURE_FIXTURE_V1_2026-10-18.md`.

Wniosek:

> **Future Fixture Context v1 jest NOT PROVEN. To nie zamyka c).**

## 3.1 Match stakes

Przetestować PIT-safe reprezentacje:

- title-race relevance;
- European qualification relevance;
- relegation relevance;
- direct-table-rival signal;
- points-gap pressure;
- late-season importance.

## 3.2 Sequence-aware form

Obecne last-5 aggregate może gubić kolejność.

Testować:

- winning streak;
- unbeaten streak;
- losing streak;
- recent points acceleration/deceleration;
- home-only streak, jeśli evidence uzasadnia.

## 3.3 Rivalry / exceptional opponent draw

Tam, gdzie istnieje deterministic and maintainable mapping:

- derby;
- rivalry;
- exceptional national opponent draw;
- opponent demand percentile.

Zakaz ręcznego labelowania na podstawie znanej frekwencji.

## 3.4 Squad context

Potencjalne features:

- injuries;
- suspensions;
- expected XI;
- key-player availability.

Warunek:

- reliable historical PIT source;
- known publication/availability timestamp;
- brak backfillu z final/current source.

Jeżeli takiego źródła nie ma, blocker ma zostać jawnie zapisany zamiast tworzenia fake historical signal.

## 3.5 Future fixtures

Nie retunować tego samego v1 na tych samych exposed holdouts.

Nowy future-fixture experiment musi mieć materialnie inny hypothesis/contract.

## Exit condition c2

c2 można zamknąć dopiero, gdy:

- bezpieczne, realne candidate gaps są jawnie wymienione;
- zostały przetestowane albo mają udokumentowany data blocker;
- nie ma ukrytego „może kiedyś dodamy X” bez statusu;
- scorecard i decyzje są zachowane.

---

# 4. Freeze Pre-Live Model v2

Po a2+b2+c2 wybieramy per-horizon champion.

Freeze musi zawierać:

- model ID;
- feature-contract ID;
- data version;
- train seasons;
- weighting;
- hyperparameters;
- imputation;
- calibration;
- random seed;
- artifact hash;
- benchmark scorecard;
- known limitations.

Pre-Live v2 staje się stabilnym incumbentem dla następnej generacji live correction.

Nie uczymy d2 przeciwko baseline, który równolegle się zmienia.

---

# 5. d2 — Continuous Live Updater

Status: **AFTER PRE-LIVE v2 FREEZE; live infrastructure and frozen C1 prospective collection continue now**.

## 5.1 Continuous time

T-30/T-14/T-7/T-3/T-1 służą do mierzenia jakości.

Nowy live model może aktualizować forecast przy każdym meaningful snapshotcie poprzez continuous `time_to_kickoff`.

## 5.2 Start od pierwszego usable sales evidence

Jeżeli sprzedaż ruszyła przed T-30, zbieramy i wykorzystujemy wcześniejsze trajectory.

## 5.3 Preferowane target formulations

### A. Delta vs Pre-Live

`target = final attendance - Pre-Live v2 prediction`

### B. Remaining demand

Model przewiduje, ile demand pozostało od aktualnego stanu do kickoffu.

### C. Reliability-weighted blend

Dynamiczna waga Pre-Live vs Live zależna od jakości evidence.

Direct final-attendance live expert może pozostać benchmarkiem, ale nie jest domyślną architekturą.

## 5.4 Reliability

Jawnie modelować/wykorzystywać:

- observation count;
- observation span;
- time-to-kickoff;
- velocity;
- acceleration;
- trajectory stability;
- coverage completeness;
- release events;
- sector consistency;
- price-area consistency;
- disagreement with Pre-Live;
- scrape/data-quality flags.

## 5.5 Inventory interpretation

Public seat-map inventory jest demand proxy, nie confirmed paid sales.

Model musi chronić się przed pomyleniem:

- demand;
- ticket release;
- sector opening/closure;
- coverage change;
- scrape anomaly.

## 5.6 Frozen v8

C1 v8 pozostaje frozen comparator / prospective shadow.

Nie retunować v8 jako część d2.

---

# 6. Current C1 evidence — boundary

Current historical evidence:

- real-only Live LOEO: **2,929.3 MAE**;
- conservative synthetic LOEO: **2,261.5 MAE**;
- stress synthetic LOEO: **2,498.8 MAE**;
- four-event chronological Prior: **452.8 MAE**;
- four-event chronological raw Live: **2,103.7 MAE**;
- frozen v8 final: **452.8 MAE**, PRIOR in **16/16 rows**.

Interpretation:

- synthetic augmentation pomaga raw Live;
- raw Live nie jest universal replacement;
- v8 potrafił odrzucić słaby Live na obecnych forward events;
- nie wiemy jeszcze, czy równie dobrze rozpozna przyszłe przypadki, gdy Live jest lepszy;
- potrzebujemy fresh prospective completed events.

Production pozostaje:

`live_adjustment = 0`

---

# 7. Mandatory accuracy scorecard

Każdy material challenger raportuje co najmniej:

- MAE;
- median AE;
- bias;
- WAPE, jeśli meaningful;
- p90 AE / tail metric;
- worst-event degradation vs incumbent;
- exact worst-event identity for material challengers;
- share events improved;
- result per horizon;
- result per season;
- result per club, gdy próbka pozwala;
- event count;
- row count.

Live additionally:

- event-level MAE;
- window MAE;
- latest-row MAE;
- revision rate;
- maximum harmful revision;
- live-use/blend rate;
- conditional quality by observation count / time-to-kickoff where possible.

---

# 8. CI/CD — bez pomijania szczegółów

Każdy material experiment musi przejść pełny chain:

`code -> tests/checks -> CI workflow -> artifact -> metrics -> result doc -> decision -> canonical docs update`

Mandatory:

1. committed source;
2. executable CI;
3. pinned dependencies;
4. deterministic seeds;
5. exact input artifacts/data version;
6. exact feature definitions;
7. exact as-of rules;
8. exact train/dev/holdout;
9. exclusions + reason;
10. imputation/normalization;
11. caps/weights/shrinkage/thresholds;
12. hyperparameters;
13. PIT/leakage assertions;
14. incumbent benchmark assertion;
15. machine-readable artifact;
16. run/artifact ID + hash where available;
17. committed result in `ml/results/`;
18. explicit promote/reject/retain/insufficient-evidence decision;
19. docs synchronized with the result;
20. no production promotion without explicit governance.

No undocumented local/manual result becomes canonical.

No silent retuning on the same holdout.

No random split of snapshots from the same event.

Synthetic data is train-only and not independent evidence.

CI green does not mean CD to production.

---

# 9. Immediate next task

**Implement T-7 Hist31 robustness / fixed-blend stage 2.**

Do not modify the current production T-7 champion yet.

Stage 2 must be development-selected, fully reproducible and specifically test whether the +68.81 mean reference MAE lead can be retained with materially safer event-level behavior.
