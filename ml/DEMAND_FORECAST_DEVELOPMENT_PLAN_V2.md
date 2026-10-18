# Beyond Ticketing — Demand Forecast Development Plan v2

Ostatnia aktualizacja: **2026-10-18**

Status: **CANONICAL ACCURACY ROADMAP**

Pełne zasady eksperymentów, walidacji i CI/CD:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

## Główny cel

> **Dopracować model maksymalnie teraz i obniżyć MAE tak daleko, jak pozwalają uczciwe, reprodukowalne dane i walidacja PIT-safe.**

Nie optymalizujemy developmentu pod „zamknięcie” kolejnych literek roadmapy.

Negatywny wynik jednego challengera nie zamyka całego workstreamu.

## Docelowa architektura

### Pre-Live Model v2

`a) historia + b) current-season regime + c) match context -> najlepszy forecast przed live`

### Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> live delta / revised forecast`

## Nowa kolejność developmentu

1. **a2 — Historical / Structural Prior optimization**
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

Status: **ACTIVE NEXT**.

Cel:

> **Wycisnąć możliwie najmocniejszy baseline z obecnego historycznego evidence zanim zaczniemy uczyć kolejne warstwy korekcyjne.**

## 1.1 Feature contribution / ablation

Dla każdego horyzontu osobno zmierzyć contribution grup:

- home demand history;
- current-season demand features obecne już w Prior;
- opponent demand;
- pair history;
- sporting form;
- table context;
- calendar / timing;
- rest / congestion;
- importance interactions;
- capacity/normalization-related signals.

Wymagania:

- incumbent benchmark hard-asserted;
- jedna zmiana kontraktu naraz, chyba że testujemy z góry zdefiniowaną grupę;
- brak usuwania features wyłącznie na podstawie in-sample importance;
- decyzja na podstawie development + holdout evidence.

## 1.2 Recency weighting

Przetestować jawne candidate policies:

- uniform;
- linear recency;
- exponential decay;
- bounded newer-season emphasis.

Każda policy musi mieć zamrożone parametry przed final holdout scoringiem.

## 1.3 Model-family challengers

Obecni championi:

- ExtraTrees;
- GradientBoosting;
- HistGradientBoosting.

Przetestować challengers, jeżeli implementacja pozostaje reprodukowalna:

- CatBoost;
- LightGBM;
- XGBoost;
- regularized linear/GAM-style baseline;
- ensemble wyłącznie z niezależnie zwalidowanych kandydatów.

Nie promować modelu tylko dlatego, że jest bardziej złożony.

## 1.4 Horizon-specific optimization

T-30/T-14/T-7/T-3/T-1 mogą mieć inne:

- feature subsets;
- estimator;
- recency weighting;
- regularization;
- calibration.

Nie wymuszać jednego wspólnego modelu dla wygody technicznej.

## 1.5 Residual / club calibration

Sprawdzić, czy incumbent zostawia stabilny club-specific residual.

Każda kalibracja:

- PIT-safe;
- shrinkowana przy małej próbce;
- oceniana out-of-sample;
- nie może być prostym memorizingiem klubu/sezonu.

## Exit condition a2

Nie ma jednego z góry ustalonego „winnera”.

a2 kończy się dopiero, gdy:

- główne feature groups mają contribution evidence;
- sensowne recency policies zostały sprawdzone;
- co najmniej current model family + uzasadnione challengers zostały porównane;
- per-horizon champion jest jawnie wybrany;
- pełny scorecard i artefakty są zapisane.

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

## 2.1 Residual regime index — priorytet

Po zamrożeniu championa z a2 zbudować historyczny PIT residual:

`residual = actual attendance - incumbent prediction available before that match`

oraz wariant ratio:

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
- decision based on full scorecard.

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

## 5.1 Nie ograniczamy się do pięciu checkpointów

T-30/T-14/T-7/T-3/T-1 służą do mierzenia jakości.

Nowy live model może aktualizować forecast przy każdym meaningful snapshotcie.

Feature:

`continuous time_to_kickoff`

musi umożliwiać wykorzystanie np. T-32, T-25, T-20, T-11.5, T-4.2.

## 5.2 Start od pierwszego usable sales evidence

Jeżeli sprzedaż ruszyła przed T-30, zbieramy i wykorzystujemy wcześniejsze trajectory.

## 5.3 Preferowane target formulations

Testować co najmniej:

### A. Delta vs Pre-Live

`target = final attendance - Pre-Live v2 prediction`

### B. Remaining demand

Model ma przewidywać, ile demand pozostało od aktualnego stanu do kickoffu.

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

# 6. Current C1 evidence — zachować jako boundary

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

**Start a2 — Pre-Live Model v2 baseline optimization.**

First implementation should build a reproducible per-horizon baseline optimization harness that can run:

- feature-group ablation;
- recency-weight challengers;
- current incumbent model specs;
- selected model-family challengers;
- one standardized scorecard;
- exact incumbent regression assertions.

Do not start a new d2 learned live model before the Pre-Live v2 freeze unless the work is purely infrastructure/prospective data collection and does not change the learned production path.
