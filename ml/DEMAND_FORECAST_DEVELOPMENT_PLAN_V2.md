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

Syntetyka poprawia więc raw Live również chronologicznie, ale sam raw Live nadal nie powinien automatycznie zastępować Structural Prior.

### Finalna logika v8 — sprawdzona chronologicznie

Następnie przepuściliśmy te same forward conditions przez **zamrożoną, niezmienioną bramkę v8 Prior vs Live**.

Wynik dla `real_only`:

- Structural Prior MAE: **452.8**;
- raw Live MAE: **2,103.7**;
- final v8 policy MAE: **452.8**;
- v8 wybrało PRIOR w **16/16 rows**;
- worst policy degradation vs Prior: **0.0**.

Czyli na obecnych czterech forward eventach v8 poprawnie rozpoznało, że Live jest niewiarygodne i nie pogorszyło forecastu.

Canonical evidence:

- `ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_WALK_FORWARD_POLICY_VALIDATION_V1_2026-10-18.md`.

### Wniosek z Walidacji obecnego modelu

Na dzisiejszym materiale:

1. Structural Prior jest mocnym bezpiecznym baseline;
2. raw Live ma realny sygnał, ale nie jest stabilne jako universal replacement;
3. train-only synthetic trajectory augmentation realnie poprawia raw Live na realnych held-out eventach;
4. zamrożona bramka v8 potrafi odciąć Live, kiedy jest niewiarygodne;
5. nadal nie mamy prospective scored events, więc nie znamy jeszcze prawdziwego prospective MAE;
6. v8 pozostaje frozen i `live_adjustment = 0`.

**Walidacja historyczna na aktualnie dostępnych danych jest wystarczająca, żeby przejść do b) Aktualny sezon, jednocześnie zbierając prospective evidence w tle.**

## a) Dane historyczne — dopracować, nie przebudowywać

- utrzymać obecny Structural Prior;
- sprawdzić, które historyczne cechy realnie poprawiają MAE;
- usunąć słabe / noisy features;
- lepiej ważyć nowsze sezony względem starszych.

**Cel:** mocniejszy baseline bez komplikowania modelu.

## b) Aktualny sezon — wzmocnić

Status: **NASTĘPNY AKTYWNY DEVELOPMENT.**

- dodać wyraźny current season adjustment;
- mocniej brać pod uwagę ostatnie mecze domowe;
- mierzyć, czy klub w tym sezonie sprzedaje lepiej / gorzej niż jego historyczna norma;
- aktualizować ten adjustment po każdym kolejnym meczu.

**Cel:** model szybciej reaguje na zmianę realiów w danym sezonie.

## c) Context meczu — rozbudować

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
2. **b) Aktualny sezon — wzmocnić — AKTYWNE**
3. **c) Context meczu — rozbudować**
4. **d) Live demand — najmocniej rozwinąć**
5. **a) Dane historyczne — dopracować, nie przebudowywać**

Skrót:

`Walidacja -> b -> c -> d -> tuning a`

# Co jest wdrożone dzisiaj

## a) Dane historyczne

**TAK — działa i jest najbardziej dojrzałe.**

- pięć sezonów Ekstraklasy;
- 1,530 meczów;
- Structural Prior dla T-30 / T-14 / T-7 / T-3 / T-1;
- historyczne MAE około 1.65k–1.89k na referencyjnych sezonach 2024/25–2025/26, zależnie od horyzontu.

## b) Aktualny sezon

**TAK, ale częściowo — teraz wzmacniamy.**

Bieżący sezon i ostatnie mecze są już używane w części features, ale nie mamy jeszcze wystarczająco wyraźnej warstwy current season adjustment.

## c) Context meczu

**CZĘŚCIOWO.**

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
