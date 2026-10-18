# Beyond Ticketing — Plan developmentu modelu popytu

Ostatnia aktualizacja: **2026-10-18**

To jest canonical plan rozwoju jakości forecastu.

Kolejność:

`Walidacja -> b -> c -> d -> tuning a`

## 1. Walidacja obecnego modelu

Status: **historyczna walidacja na obecnie dostępnych live eventach wykonana; prospective validation trwa dalej automatycznie.**

### C1 — Leave-One-Event-Out

9 realnych held-out eventów, 30 final-24h rows.

| Training mode | Structural Prior MAE | Live window MAE | Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | 3,968.7 | 2,929.3 | 3,046.6 |
| `conservative_synthetic` | 3,968.7 | **2,261.5** | **2,213.9** |
| `stress_synthetic` | 3,968.7 | 2,498.8 | 2,481.7 |

Synthetic augmentation jest train-only; held-out event pozostaje 100% realny. Jest `PROMISING_FOR_FURTHER_VALIDATION`, ale nie jest niezależnym evidence i nie zmienia frozen v8.

### C1 — chronological walk-forward

Na czterech późniejszych realnych eventach:

| Training mode | Structural Prior MAE | Raw Live window MAE | Raw Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | **452.8** | 2,103.7 | 2,197.3 |
| `conservative_synthetic` | **452.8** | 1,939.5 | 2,017.0 |
| `stress_synthetic` | **452.8** | **1,876.7** | **1,915.2** |

Raw Live nadal nie jest universal replacement dla Structural Prior.

### Frozen v8 policy — chronological safety check

Bez zmiany/refitu progów:

- Structural Prior MAE: **452.8**;
- raw Live MAE: **2,103.7**;
- final v8 policy MAE: **452.8**;
- PRIOR selected in **16/16 rows**;
- worst degradation vs Prior: **0.0**.

### Forward-event diagnostic

- latest raw-Live error: 3 underpredictions / 1 overprediction;
- brak jednej compact feature group, której usunięcie naprawia wszystkie eventy;
- `inventory_level` jest globalnie użyteczne;
- lokalne problemy dotyczą m.in. `motion_velocity` / `release_coverage`, ale są event-specific;
- diagnoza: small-sample generalisation + feature-state distribution shift / interakcje, nie jeden zepsuty feature.

Canonical evidence:

- `ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_WALK_FORWARD_POLICY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_FORWARD_EVENT_DIAGNOSTIC_V1_2026-10-18.md`.

Frozen v8 pozostaje bez zmian i `live_adjustment = 0`.

## a) Dane historyczne — dopracować, nie przebudowywać

Status: **DZIAŁA / TUNING DOPIERO PO d).**

- utrzymać obecny Structural Prior;
- później sprawdzić feature contribution;
- usuwać noisy features tylko na podstawie evidence;
- później przetestować mocniejsze ważenie nowszych sezonów.

## b) Aktualny sezon — wzmocnić

Status: **PRZETESTOWANE / NOT PROVEN / NIE PROMOWAĆ.**

Current Season Adjustment v1:

| Horizon | Wybrana opcja | Mean incumbent MAE | Mean adjusted MAE |
|---|---|---:|---:|
| T-30 | `NO_ADJUSTMENT` | 1,867.8 | 1,867.8 |
| T-14 | `NO_ADJUSTMENT` | 1,809.4 | 1,809.4 |
| T-7 | `season_r3-k6-a25` | **1,790.0** | 1,844.3 |
| T-3 | `NO_ADJUSTMENT` | 1,718.4 | 1,718.4 |
| T-1 | `NO_ADJUSTMENT` | 1,697.3 | 1,697.3 |

Nie dokładamy dodatkowej post-model korekty current-season. Obecne current-season features w Structural Prior zostają.

Canonical evidence:

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

## c) Context meczu — rozbudować

Status: **AUDIT + CHALLENGER WYKONANE / NOT PROVEN / NIE PROMOWAĆ.**

Audyt potwierdził, że Structural Prior już ma dużo PIT-safe contextu:

- opponent draw / pair history;
- PPG, GD/game, last-5 form obu drużyn;
- pozycje tabeli i różnice;
- top/bottom interactions;
- past rest i 14-day congestion.

Future Fixture Context v1 przetestował główną lukę: next-home-fixture timing + attractiveness/cannibalization.

| Horizon | Wybrana opcja | Mean incumbent MAE | Mean challenger MAE |
|---|---|---:|---:|
| T-30 | `NO_CONTEXT_EXTENSION` | 1,867.8 | 1,867.8 |
| T-14 | `NO_CONTEXT_EXTENSION` | 1,809.4 | 1,809.4 |
| T-7 | `future_timing_attractiveness` | **1,790.0** | 1,790.9 |
| T-3 | `NO_CONTEXT_EXTENSION` | 1,718.4 | 1,718.4 |
| T-1 | `future_timing_attractiveness` | **1,697.3** | 1,712.4 |

No horizon improves mean holdout MAE; no horizon improves both reference seasons.

Dodatkowo fixture evidence ma klasę `SCHEDULE_AS_RECORDED_RETROSPECTIVE_PROXY`, bo nie mamy historycznej wersjonowanej historii terminarza.

Wniosek:

- nie dodajemy Future Fixture Context v1;
- nie budujemy schedule-history tylko po to, żeby ratować ten słaby signal;
- squad context dopiero po uzyskaniu wiarygodnego PIT feedu;
- istniejący context zostaje.

Canonical evidence:

- `ml/MATCH_CONTEXT_AUDIT_V1.md`;
- `ml/results/MATCH_CONTEXT_FUTURE_FIXTURE_V1_2026-10-18.md`.

## d) Live demand — najmocniej rozwinąć

Status: **AKTYWNY DEVELOPMENT.**

Już działa:

- live public inventory;
- trajectory / velocity / acceleration;
- release / coverage-change handling;
- C1 v8 prospective shadow;
- sector trajectories;
- price-area trajectories;
- real Roboticket price capture;
- guarded pricing recommendations;
- dashboard decision support.

Teraz rozwijamy live demand jako osobną, governowaną warstwę — **bez retunowania frozen v8**.

Priorytety:

1. wykorzystywać inventory od pierwszego momentu sprzedaży;
2. liczyć continuous trajectory zamiast myśleć wyłącznie checkpointami T-30/T-14/T-7/T-3/T-1;
3. aktualizować forecast po każdym znaczącym snapshotcie;
4. lepiej modelować wiarygodność live signal i transition Prior -> Live;
5. używać sector / price-area movement jako decision evidence, ale nie mieszać tego z potwierdzoną sprzedażą;
6. zbierać nowe prospective outcomes automatycznie;
7. nie zmieniać production `live_adjustment = 0`, dopóki nie przejdzie promotion governance.

**Cel:** forecast żyje razem ze sprzedażą, ale każda live correction jest evidence-based i bezpieczna.

# Kolejność developmentu — stan aktualny

1. **Walidacja obecnego modelu — historyczna część wykonana, prospective trwa**
2. **b) Aktualny sezon — PRZETESTOWANE / NOT PROVEN**
3. **c) Context meczu — PRZETESTOWANE / NOT PROVEN**
4. **d) Live demand — AKTYWNE**
5. **a) Dane historyczne — tuning później**

# Co jest wdrożone dzisiaj

## Structural Prior

- pięć sezonów Ekstraklasy;
- 1,530 meczów;
- 7,650 PIT horizon rows;
- T-30 / T-14 / T-7 / T-3 / T-1;
- historyczne MAE około 1.65k–1.89k na referencyjnych sezonach.

## Live demand

- inventory collection;
- full trajectory features;
- frozen C1 v8 shadow inference;
- sector/price-area trajectory and pricing context;
- production attendance forecast nadal `live_adjustment = 0`.

# Aktualna granica jakości

Stan na 2026-10-18:

- C1 v8: `EXPERIMENTAL_SHADOW`;
- prospective prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- `AWAITING_FIRST_PROSPECTIVE_SCORE`.

Nie mamy jeszcze potwierdzonego prospective live MAE.

# Zasady walidacji

- zero future leakage;
- event jest niezależną jednostką testową;
- snapshoty jednego eventu nie są niezależnymi meczami;
- żadnego random splitu snapshotów tego samego meczu między train/test;
- każda cecha musi być dostępna w danym historical as-of;
- synthetic data tylko w train, nigdy jako niezależne evidence;
- replay nie jest prospective validation;
- frozen v8 nie jest retunowane na tych samych eventach;
- production pozostaje `live_adjustment = 0` do explicit promotion.
