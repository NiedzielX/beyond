# Plan: C1 live w kierunku MAE 1 200 miejsc

Data: 2026-11-04. Status: plan R&D, bez zmiany modelu, parametrów i produkcji. Uzupełnia `MAE_RESEARCH_ROADMAP_V6.md` i `EXECUTION_PLAN_CURRENT.md`. C1 v8 pozostaje zamrożonym benchmarkiem; nowy challenger otrzyma osobną wersję i precommit przed treningiem.

## Cel i punkt wyjścia

Cel użytkownika: zbliżyć MAE prognozy końcowej frekwencji z danych live do **1 200 miejsc**, zachowując użyteczną dynamikę prognozy. To wymaga około **70,9% redukcji** wobec obecnego latest-row MAE 4 121,45. To cel badawczy, nie obietnica wyniku ani gwarancja błędu pojedynczego meczu. MAE przyszłej dostępności miejsc jest osobnym targetem.

Źródło: odczyt `dashboard_c1_shadow_v8_events_v1` i `dashboard_c1_shadow_v8_status_v1`, 11 ocenionych meczów, pakiet `c1-shadow-v8-frozen-2026-10-16-n9`. Oficjalny latest-row MAE: baza 4 314,72, surowy live 7 127,99, polityka 4 121,45. Window MAE polityki: 4 971,62. Ostatnie zapisane oceny: 2026-10-25.

## Co już wynika z audytu

| Mecz | Bezwzględny błąd polityki | Udział w sumie błędów |
|---|---:|---:|
| Wisła Kraków–Raków, event16 |17 009,69|37,52%|
| Lech–Korona, event5 |7 669,07|16,92%|
| Górnik–Piast, event11 |7 160,62|15,79%|
| Śląsk–Wieczysta, event23 |5 993,33|13,22%|

Te cztery mecze odpowiadają za **83,45%** sumy błędów. Pozostają w ocenie; nie tworzymy dobrego wyniku przez usunięcie trudnych przypadków lub klubów. Duży błąd nie jest sam w sobie dowodem błędnego labelu, pojemności czy źródła.

W 10 z 11 meczów polityka wybrała PRIOR, w jednym LIVE. Nawet nieosiągalny w praktyce selektor, który po wyniku wybiera mniejszy błąd z obecnych dwóch prognoz dla każdego meczu, miałby MAE **4 103,05**. To diagnostyka z użyciem znanych outcomes, nigdy prognoza do wdrożenia. Pokazuje ograniczenie samego wyboru między tymi ekspertami na tym zbiorze: potrzebujemy trafniejszych prognoz składowych.

Surowy C1 używa 30 cech i był dopasowany na 9 niezależnych meczach /30wierszach. To ograniczenie wsparcia dla uogólniania, nie dowód jednej przyczyny błędów. Istniejące diagnostyki wskazywały heterogeniczny drift; nie wspierają globalnego usunięcia jednej cechy ani prostego stałego offsetu.

## Kolejność pracy

### 1. Ustalić przyczyny dużych pomyłek i uzupełnić prawdziwe wyniki

Zbudować tabelę wszystkich 11 meczów: actual i jego źródło/definicja, timestamps, prior/raw/policy, wybrany ekspert, horizon, wersja bazy, pojemność użyta w prognozie, zakres historii, missingness i sygnały zmiany źródła. Cztery największe przypadki sprawdzić dokładniej: zgodność meczu i rozgrywek, poziom popytu, dane sezonu, stadion/pojemność, pochodzenie cech i zgodność trening–inference. Oddzielić ustaloną przyczynę od hipotezy.

Pozyskać potwierdzone frekwencje sześciu zakończonych spotkań Oct30–Nov2 ze źródeł, które można wskazać. Zachować faktyczną datę potwierdzenia. To dołączenie wyników do istniejących prognoz, nie odtwarzanie dawnych missed observations ani nowych prognoz po wyniku.

Wynik: audyt wejść i błędów, lista potwierdzonych problemów oraz jedna pierwsza falsyfikowalna hipoteza. Nie zmieniać istniejących prognoz lub frozen scoringu.

### 2. Porównać to, co już mamy, na identycznych przypadkach

Zestawić obecny prior, raw C1, politykę C1 i istniejący zamrożony D2 residual/P2 na wspólnych poprawnych punktach final24. Sprawdzić zgodność użytego anchora z odpowiednim zamrożonym pakietem Pre-Live. Raportować dokładne przecięcie pokrycia; brak zgodnego wejścia pozostaje brakiem.

To diagnostyka już odsłoniętych 11 meczów, bez retuningu i bez przedstawiania jej jako nowej walidacji. Samo podmienienie nazwy v2 na v3 nie rozwiązuje problemu: dla istniejącego final24 anchor T-1 v2/v3 jest dokładnie równoważny (`D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1.md`). D2 residual/P2 już istnieje; nie nazywać powtórzenia tego samego eksperymentu nowym odkryciem.

Wynik: ustalenie, czy główna strata powstaje w poziomie bazy, korekcie live, kontrakcie danych czy polityce, oraz uczciwy benchmark dla następnej wersji.

### 3. Jeden nowy challenger po diagnozie

Najpierw poprawić lub wzmocnić część odpowiadającą za dominującą stratę, w osobnej wersji:

- jeśli potwierdzi się problem danych/mapowania/pojemności: wersjonowany kontrakt i poprawne nowe wejścia;
- jeśli błędny jest poziom bazy: jeden challenger strukturalny/warunkowy przeciw odpowiedniemu silnemu anchorowi, z cechami znanymi przed meczem;
- jeśli baza jest właściwa, lecz brakuje sygnału specyficznego dla meczu: niewielki model residual `actual - anchor`, dodający jedną nową, uzasadnioną rodzinę informacji;
- dynamikę sprawdzać przez rzeczywiste zmiany 1d/3d/7d, nachylenie, przyspieszenie, wiek i pokrycie źródła. Najpierw prosty benchmark, dopiero uzasadniony model sekwencyjny.

Precommit przed fit: hipoteza, konkretna nowa informacja/mechanizm, feature list, parametry, trening/cutoffy i ocena. Medianowy cel w miejscach jest kandydatem do sprawdzenia, nie ponownym testem odrzuconego capacity-weightingu. Chronologiczne podziały po meczach, dobór parametrów wewnątrz treningu. Wyniki tych 11 meczów są odsłonięte i nie stają się fresh holdout po zmianie nazwy modelu.

Nie zaczynać kolejnego turnieju Ridge/GRU/C2 ani zmieniać progu v8 na podstawie obecnych błędów. Korzystać z dawnych odrzuceń. Partner transactions nie są wymagane; prognozy publicznego inventory nie zastępują frekwencji. Pogoda/hype nie są pierwszym zadaniem bez nowego PIT-safe wsparcia i hipotezy związanej z błędem.

### 4. Zamrozić i sprawdzić na nowych meczach

Nowe prognozy zapisać przed wynikiem, równolegle z bazą i C1 v8, na tych samych momentach i wejściach. Zachować vintages. Raportować latest-row MAE, event-balanced window MAE, T-24/T-6/T-1 gdy dostępne w kontrakcie, bias, P90/worst error, pokrycie, kluby i zdarzenia niezależne. Nie wybierać po wyniku najlepszego momentu prognozy.

Dla nowego celu 1 200 proponowany pierwszy przegląd: co najmniej 30 nowych ocenionych meczów /8klubów, z przedziałem niepewności liczonym po meczach. To pragmatyczna propozycja do precommitu nowego kandydata, nie dowód, że taka próba zapewni wystarczającą precyzję, i nie zmiana istniejących bramek v8/encoder/P9. Nie wykluczać trudnych klubów dla spełnienia celu.

Pierwszym sukcesem jest powtarzalna poprawa względem obu właściwych benchmarków, wraz z kontrolą bias/tail i pokrycia. Etapy 3 000 →2 000 →około1 200 mogą służyć jako cele przeglądu, nie przewidywane wyniki kolejnych sprintów. Celu nie uznajemy za osiągnięty na podstawie dopasowania do obecnych 11 meczów, metryki na łatwym podzbiorze lub samego training fit.

## Najbliższe konkretne zadanie

**Audyt matched-cohort wykonany:** `C1_LIVE_MATCHED_AUDIT_RESULT_V1.md`. D2na tych samych chwilach5157,52vsC1 4121,45; zgodność numerycznaC1potwierdzona; brakuje wcześniejszej historii sezonu Wisły/Górnika. Zewnętrzna weryfikacja źródeł i6nowych outcomes nadal zablokowane. Kolejny osobny eksperyment precommitted: `C1_TRAINING_EXPANSION_PRECOMMIT_V1.md`,9→20meczów treningowych przy stałych cechach/parametrach/polityce; tylko przyszły test może wykazać poprawę. Nie kolejne prace nad schedulowaniem poza ochroną zagrożonych okien.

Plan nie gwarantuje 1 200 miejsc. Wyznacza testowalną drogę do tego celu i punkty, w których uczciwy wynik może odrzucić hipotezę. `production_change=false`, `live_adjustment=0`; frozen v8, D2, encoder, P9 i historyczne braki pozostają bez zmian.
