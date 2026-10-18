# Beyond Ticketing — Plan developmentu modelu popytu

Ostatnia aktualizacja: **2026-10-18**

To jest canonical plan rozwoju jakości forecastu. Nazwy etapów mają pozostać proste i spójne z ustaleniami produktowymi.

## 1. Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy

Zanim dodamy kolejne dane i features, sprawdzamy uczciwie, jak obecny model działa na meczach, których nie widział podczas treningu / tuningu.

- zrobić **Leave-One-Event-Out** na zakończonych meczach z użytecznymi live danymi;
- dla każdego testowanego meczu trenować / tunować model bez tego meczu;
- odtworzyć historyczny stan T-7 / T-3 / T-1 wyłącznie z danych dostępnych wtedy;
- porównać:
  - Structural Prior,
  - Live / C1,
  - final prediction / policy;
- policzyć MAE, bias i błędy per mecz;
- dodatkowo zrobić **chronological walk-forward**;
- nie liczyć wielu snapshotów jednego meczu jako wielu niezależnych meczów.

### Syntetyczne warianty trajectory — WYKONANE

Sprawdziliśmy, czy małą liczbę prawdziwych meczów można lepiej wykorzystać przez **train-only synthetic trajectory augmentation**.

Porównane warianty:

1. `real_only` — tylko prawdziwe dane;
2. `conservative_synthetic` — niewielkie, realistyczne perturbacje trajectory;
3. `stress_synthetic` — większe perturbacje jako stress test.

Twarde zasady zostały zachowane:

- syntetyczne dane powstawały wyłącznie z eventów treningowych;
- held-out mecz był zawsze 100% realny;
- z held-out meczu nie generowano synthetic rows;
- synthetic row zachowywał realny outcome swojego training eventu;
- synthetic rows nie zwiększały liczby niezależnych eventów;
- jakość była liczona wyłącznie na prawdziwych held-out eventach.

#### Wynik LOEO — 9 realnych eventów

| Training mode | Structural Prior MAE | Live window MAE | Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | 3,968.7 | 2,929.3 | 2,757.0 |
| `conservative_synthetic` | 3,968.7 | 2,813.4 | **2,582.1** |
| `stress_synthetic` | 3,968.7 | **2,742.4** | 2,582.3 |

W LOEO syntetyka pomaga.

#### Wynik chronological walk-forward — 4 późniejsze realne eventy

| Training mode | Structural Prior MAE | Live window MAE | Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | **1,711.0** | 4,499.9 | 4,455.0 |
| `conservative_synthetic` | **1,711.0** | 4,550.5 | 4,465.3 |
| `stress_synthetic` | **1,711.0** | **4,383.3** | **4,332.6** |

W walk-forward:

- conservative synthetic nie poprawia `real_only`;
- stress synthetic poprawia `real_only` o ok. 117 MAE, ale live model nadal bardzo mocno przegrywa ze Structural Prior;
- syntetyka jest więc ciekawym regularizatorem, ale **nie rozwiązuje problemu generalizacji**.

Decyzja:

`conservative_augmentation_signal = NOT_PROVEN`

`promotion_allowed = false`

Canonical evidence:

`ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`

### Co dalej w Walidacji obecnego modelu

Nie przechodzimy jeszcze automatycznie do b). Najpierw wyjaśniamy, dlaczego chronological walk-forward jest słaby.

Do sprawdzenia:

- które forward eventy generują największy błąd;
- czy problemem jest klub / domain shift;
- czy training history jest za mała;
- czy live trajectory ma inne coverage / phase niż dane treningowe;
- które live features są niestabilne;
- czy możemy rozpoznać sytuacje, kiedy należy zostać przy Structural Prior zamiast ufać Live/C1.

**Cel Walidacji:** uczciwie odpowiedzieć, co obecny model naprawdę umie i kiedy można ufać live correction.

## a) Dane historyczne — dopracować, nie przebudowywać

- utrzymać obecny Structural Prior;
- sprawdzić, które historyczne cechy realnie poprawiają MAE;
- usunąć słabe / noisy features;
- lepiej ważyć nowsze sezony względem starszych.

**Cel:** mocniejszy baseline bez komplikowania modelu.

## b) Aktualny sezon — wzmocnić

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

1. **Walidacja obecnego modelu**
2. **b) Aktualny sezon — wzmocnić**
3. **c) Context meczu — rozbudować**
4. **d) Live demand — najmocniej rozwinąć**
5. **a) Dane historyczne — dopracować, nie przebudowywać**

Czyli skrótowo:

`Walidacja -> b -> c -> d -> tuning a`

# Co jest wdrożone dzisiaj

## a) Dane historyczne

**TAK — działa i jest najbardziej dojrzałe.**

- pięć sezonów Ekstraklasy;
- 1,530 meczów;
- Structural Prior dla T-30 / T-14 / T-7 / T-3 / T-1;
- historyczne MAE około 1.65k–1.89k na referencyjnych sezonach 2024/25–2025/26, zależnie od horyzontu.

Do dopracowania, nie do przebudowy.

## b) Aktualny sezon

**TAK, ale częściowo — trzeba wzmocnić.**

Bieżący sezon i ostatnie mecze są już używane w części features, ale nie mamy jeszcze wystarczająco wyraźnej i silnie kontrolowanej warstwy current season adjustment.

## c) Context meczu

**CZĘŚCIOWO.**

Mamy już część danych o formie, tabeli, przeciwniku i terminarzu. Future fixtures / cannibalization oraz skład nie są jeszcze wdrożone jako pełnoprawne, kontrolowane features.

## d) Live demand

**TAK — działa, ale ma największy potencjał rozwoju.**

- zbieramy live inventory;
- mamy trajectory / velocity;
- C1 v8 działa prospectively w shadow;
- mamy sector i price-area trajectories;
- production attendance forecast nadal ma `live_adjustment = 0` do czasu świadomej promocji.

Najważniejszy kierunek: forecast aktualizowany ciągle razem z live demand, a nie tylko myślenie checkpointami.

# Aktualna granica jakości

Stan na 2026-10-18:

- C1 v8: `EXPERIMENTAL_SHADOW`;
- prospective prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- `AWAITING_FIRST_PROSPECTIVE_SCORE`.

Nie mamy jeszcze potwierdzonego prospective live MAE.

Development replay około 2.0k–2.7k oraz synthetic LOEO około 2.74k–2.81k są development evidence i nie mogą być przedstawiane jako dokładność na nowych meczach.

# Zasady walidacji

- zero future leakage;
- event jest niezależną jednostką testową;
- snapshoty jednego eventu nie są niezależnymi meczami;
- żadnego random splitu snapshotów tego samego meczu między train/test;
- każda cecha musi być dostępna w danym historical as-of;
- testowany mecz nie może wpływać na fitting ani tuning;
- porównujemy modele na tych samych event/horizon pairs;
- synthetic data może być tylko w train i nie może powstawać z held-out eventu;
- synthetic rows nie są nowymi niezależnymi eventami;
- wynik syntetycznego eksperymentu oceniamy tylko na prawdziwych held-out eventach;
- replay nie jest prospective validation;
- C1 v8 nie jest automatycznie promowany.
