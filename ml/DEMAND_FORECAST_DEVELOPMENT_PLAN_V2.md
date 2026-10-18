# Beyond Ticketing — Plan developmentu modelu popytu

Ostatnia aktualizacja: **2026-10-18**

To jest canonical plan rozwoju jakości forecastu. Nazwy etapów mają pozostać proste i spójne z ustaleniami produktowymi.

## 1. Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy

Status: **historyczna walidacja na obecnie dostępnych live eventach wykonana; prospective validation trwa dalej automatycznie.**

Sprawdziliśmy model na prawdziwych held-out eventach bez używania testowanego meczu do treningu lub syntetyki.

### Leave-One-Event-Out

9 realnych held-out eventów, 30 final-24h rows.

| Training mode | Structural Prior MAE | Live window MAE | Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | 3,968.7 | 2,929.3 | 3,046.6 |
| `conservative_synthetic` | 3,968.7 | **2,261.5** | **2,213.9** |
| `stress_synthetic` | 3,968.7 | 2,498.8 | 2,481.7 |

### Syntetyczne warianty trajectory

Synthetic augmentation jest wykonywane **wyłącznie po stronie train**.

Zasady:

- held-out event jest zawsze 100% realny;
- z held-out eventu nie generujemy żadnych synthetic rows;
- synthetic row zachowuje prawdziwy outcome swojego training eventu;
- synthetic rows nie są liczone jako nowe niezależne mecze;
- jakość mierzymy wyłącznie na prawdziwych held-out eventach.

Wynik:

- conservative synthetic poprawiło LOEO window MAE o **667.8** vs real-only;
- conservative synthetic poprawiło LOEO latest-row MAE o **832.8**;
- synthetic augmentation jest więc **PROMISING_FOR_FURTHER_VALIDATION** jako regularizacja małego datasetu;
- nie jest nowym źródłem prawdy i nie zastępuje nowych realnych meczów.

### Chronological walk-forward

Na czterech późniejszych realnych eventach:

| Training mode | Structural Prior MAE | Raw Live window MAE | Raw Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | **452.8** | 2,103.7 | 2,197.3 |
| `conservative_synthetic` | **452.8** | 1,939.5 | 2,017.0 |
| `stress_synthetic` | **452.8** | **1,876.7** | **1,915.2** |

Syntetyka poprawia raw Live również chronologicznie, ale sam raw Live nadal nie powinien automatycznie zastępować Structural Prior.

### Finalna logika v8 — sprawdzona chronologicznie

Następnie przepuściliśmy te same forward conditions przez **zamrożoną, niezmienioną bramkę v8 Prior vs Live**.

Wynik dla `real_only`:

- Structural Prior MAE: **452.8**;
- raw Live MAE: **2,103.7**;
- final v8 policy MAE: **452.8**;
- v8 wybrało PRIOR w **16/16 rows**;
- worst policy degradation vs Prior: **0.0**.

Czyli na obecnych czterech forward eventach v8 poprawnie rozpoznało, że Live jest niewiarygodne i nie pogorszyło forecastu.

### Forward-event diagnostic

Dodatkowa diagnoza tych samych czterech forward eventów pokazała:

- 3 latest-row underpredictions i 1 overprediction raw Live;
- brak jednej grupy cech, której usunięcie naprawiałoby wszystkie eventy;
- `motion_velocity` pomaga jako lokalny diagnostic m.in. na Legia – Wisła, ale nie jest stabilnym globalnym rozwiązaniem;
- usunięcie `inventory_level` jest mocno szkodliwe w agregacie;
- problem jest lepiej opisany jako small-sample / event-specific distribution shift i interakcje niż jako jeden zepsuty feature.

Canonical evidence:

- `ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_WALK_FORWARD_POLICY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_FORWARD_EVENT_DIAGNOSTIC_V1_2026-10-18.md`.

### Wniosek z Walidacji obecnego modelu

Na dzisiejszym materiale:

1. Structural Prior jest mocnym bezpiecznym baseline;
2. raw Live ma realny sygnał, ale nie jest stabilne jako universal replacement;
3. train-only synthetic trajectory augmentation realnie poprawia raw Live na realnych held-out eventach;
4. zamrożona bramka v8 potrafi odciąć Live, kiedy jest niewiarygodne;
5. forward diagnostic nie uzasadnia globalnego usunięcia żadnej grupy compact features;
6. nadal nie mamy prospective scored events, więc nie znamy jeszcze prawdziwego prospective MAE;
7. v8 pozostaje frozen i `live_adjustment = 0`.

## a) Dane historyczne — dopracować, nie przebudowywać

- utrzymać obecny Structural Prior;
- sprawdzić, które historyczne cechy realnie poprawiają MAE;
- usunąć słabe / noisy features;
- lepiej ważyć nowsze sezony względem starszych.

**Cel:** mocniejszy baseline bez komplikowania modelu.

## b) Aktualny sezon — wzmocnić

Status: **PRZETESTOWANE / NOT PROVEN / NIE PROMOWAĆ.**

Current Season Adjustment v1 został zaimplementowany i oceniony z poprawnie odizolowanym incumbentem.

Protocol:

- 18 non-zero wariantów + `NO_ADJUSTMENT`;
- wybór na 2023/24 development;
- zamrożony wybór na 2024/25 i 2025/26 reference holdouts;
- exact frozen benchmark Structural Prior jest hard-asserted.

Wynik:

| Horizon | Wybrana opcja | Mean incumbent MAE | Mean adjusted MAE |
|---|---|---:|---:|
| T-30 | `NO_ADJUSTMENT` | 1,867.8 | 1,867.8 |
| T-14 | `NO_ADJUSTMENT` | 1,809.4 | 1,809.4 |
| T-7 | `season_r3-k6-a25` | **1,790.0** | 1,844.3 |
| T-3 | `NO_ADJUSTMENT` | 1,718.4 | 1,718.4 |
| T-1 | `NO_ADJUSTMENT` | 1,697.3 | 1,697.3 |

T-7 non-zero wariant pogarsza oba holdouty (~52 i ~57 MAE). Na pozostałych horyzontach selector poprawnie wybiera `NO_ADJUSTMENT` już na development.

Wniosek:

- nie dokładamy dodatkowej post-model korekty current-season;
- bieżący sezon pozostaje używany przez obecne Structural Prior features;
- nie tunujemy dalej tej samej idei pod exposed reference seasons;
- production bez zmian.

Canonical evidence:

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

## c) Context meczu — rozbudować

Status: **NASTĘPNY AKTYWNY DEVELOPMENT.**

- dodać siłę / atrakcyjność przeciwnika;
- future fixtures: czy za kilka dni jest atrakcyjniejszy mecz;
- fixture congestion / cannibalization;
- forma i pozycja obu drużyn;
- skład: kontuzje, zawieszenia, kluczowi zawodnicy — tam, gdzie mamy wiarygodne dane.

**Cel:** model rozumie, dlaczego konkretny mecz może mieć większy lub mniejszy popyt.

## d) Live demand — najmocniej rozwinąć

- zbierać inventory od pierwszego momentu sprzedaży;
- liczyć velocity, acceleration, zmianę sektorów i price areas;
- aktualizować forecast po każdym nowym, znaczącym snapshotcie;
- nie ograniczać modelu tylko do T-30 / T-14 / T-7 / T-3 / T-1;
- checkpointy zostawić głównie do mierzenia jakości;
- live correction ma stale poprawiać Structural Prior, ale tylko gdy live signal jest wystarczająco wiarygodny;
- public inventory nadal traktować jako proxy popytu, nie potwierdzoną sprzedaż.

**Cel:** mieć forecast, który żyje razem ze sprzedażą.

# Kolejność developmentu

1. **Walidacja obecnego modelu — historyczna część wykonana, prospective trwa**
2. **b) Aktualny sezon — wzmocnić — PRZETESTOWANE / NOT PROVEN**
3. **c) Context meczu — rozbudować — AKTYWNE**
4. **d) Live demand — najmocniej rozwinąć**
5. **a) Dane historyczne — dopracować, nie przebudowywać**

Skrót pozostaje:

`Walidacja -> b -> c -> d -> tuning a`

# Co jest wdrożone dzisiaj

## a) Dane historyczne

**TAK — działa i jest najbardziej dojrzałe.**

- pięć sezonów Ekstraklasy;
- 1,530 meczów;
- Structural Prior dla T-30 / T-14 / T-7 / T-3 / T-1;
- historyczne MAE około 1.65k–1.89k na referencyjnych sezonach 2024/25–2025/26, zależnie od horyzontu.

## b) Aktualny sezon

**TAK w incumbent features; dodatkowy explicit adjustment przetestowany i odrzucony.**

Bieżący sezon i ostatnie mecze pozostają używane w Structural Prior. Current Season Adjustment v1 nie wykazał dodatkowej wartości ponad incumbent.

## c) Context meczu

**CZĘŚCIOWO — teraz rozwijamy.**

Mamy część danych o formie, tabeli, przeciwniku i terminarzu. Future fixtures / cannibalization oraz skład nie są jeszcze pełnoprawnymi kontrolowanymi features.

## d) Live demand

**TAK — działa, ale ma największy potencjał rozwoju.**

- zbieramy live inventory;
- mamy trajectory / velocity;
- C1 v8 działa prospectively w shadow;
- mamy sector i price-area trajectories;
- production attendance forecast nadal ma `live_adjustment = 0`.

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
- testowany mecz nie może wpływać na fitting ani tuning;
- synthetic data może być tylko w train i nie może powstawać z held-out eventu;
- synthetic rows nie są nowymi niezależnymi eventami;
- replay nie jest prospective validation;
- v8 nie jest retunowane na tych samych eventach;
- C1 nie jest automatycznie promowany.
