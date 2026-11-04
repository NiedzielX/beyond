# Beyond — przegląd badań i plan szybkiego MVP

Data: **2026-11-03**.

Status: **RESEARCH / MVP DELIVERY SUPPLEMENT** do [roadmap v6](MAE_RESEARCH_ROADMAP_V6.md) i [planu wykonawczego](EXECUTION_PLAN_CURRENT.md). Nie zastępuje ich, nie jest precommitem nowego modelu i nie zmienia zamrożonych eksperymentów.

**Korekta priorytetu produktu, 2026-11-03:** użytkownik wymaga prognozy kolejnych dni z całego dostępnego prefiksu i codziennego przeliczania przyszłej ścieżki. Sama historia prognoz końcowej frekwencji nie spełnia tego celu. Obowiązuje uzupełniający [kontrakt daily path](DAILY_DEMAND_PATH_MVP_CONTRACT_V1.md). Poniższy pierwotny szacunek 7–10 dni dotyczył widoku endpoint/scorecard; nie jest zweryfikowaną estymacją brakującego modelu ścieżki, nowego ledgeru i scorera.

## 1. Decyzja

Budujemy demonstracyjne MVP na istniejącym backendzie, równolegle z ochroną prospective evidence i jednym ograniczonym eksperymentem ML. Nie uzależniamy demonstracji produktu od wytrenowania kolejnej sieci. Nie przedstawiamy działającej demonstracji jako dowodu przewagi predykcyjnej.

**Ograniczenie użytkownika, 2026-11-03:** na MVP nie uzyskamy partnerskich danych transakcyjnych, zwrotów, karnetów ani potwierdzonych blokad/uwolnień puli. Plan MVP i dalsze R&D opieramy na już dostępnych źródłach publicznych i ich przyszłych genuine obserwacjach. Pozyskanie partnera nie jest zadaniem ani bramką tego sprintu.

Priorytety:

1. Ustalić aktualne wyniki i jakość danych, zachowując zamrożone modele.
2. Zbudować codzienną prognozę przyszłej ścieżki publicznej dostępności/proxy z całego genuine prefiksu i połączyć z nią wykres. Końcowa frekwencja i jej MAE pozostają osobnym wynikiem; P-7 / P-3 / P-1 obecnego v1 nie ogranicza zakresu nowego daily-path MVP.
3. Poprawić przyszłą ciągłość i pokrycie publicznych obserwacji, freshness i mapowanie meczów; zbierać nowe pary trajektoria znana w cutoffie → potwierdzony outcome kolejnego niezależnego meczu. Zachować frozen eligibility i historyczne braki.
4. Jako zadanie drugorzędne wobec daily path sprawdzić zgodność celu treningowego z MAE w osobach. Nie rozpoczynać turnieju architektur.
5. Zamrażać nowych kandydatów przed ich własnym przyszłym testem i oceniać po genuine outcomes.

Nie ma podstaw do obietnicy określonego przyszłego MAE. Celem jest mierzalna poprawa na nowych meczach, a nie zerowy błąd.

## 2. Zakres i wiarygodność przeglądu

To celowany przegląd badań i materiałów autorów dotyczących danych tabelarycznych, modeli sekwencyjnych, pretrained forecasting, walidacji czasowej i niepewności. Nie jest to systematyczny przegląd całej literatury AI ani kompletny przegląd publikacji do listopada 2026.

W tej sesji bezpośrednie żądania do arXiv, NeurIPS, OTexts, JMLR, Crossref i innych wydawców były blokowane przez proxy HTTP 403. Przez GitHub API przeczytano oficjalne repozytoria autorów: README, wybrane implementacje i materiały dydaktyczne. Nie deklarujemy przeczytania niedostępnych pełnych artykułów ani niezależnej replikacji ich wyników. Repozytorium autora potwierdza deklarowany zakres metody; nie potwierdza skuteczności w Beyond. Liczby z cudzych benchmarków nie są prognozą poprawy naszego MAE.

Luka przeglądu: nie zweryfikowano pełnych prac domenowych o booking curves / demand unconstraining w hotelarstwie, lotnictwie i ticketingu. Wymagają osobnego uzupełnienia, gdy pełne teksty będą dostępne; nie zastępujemy ich przypadkowymi projektami GitHub.

### Źródła i wpływ na decyzje

| Źródło | Co rzeczywiście sprawdzono | Wniosek dla Beyond i ograniczenie |
|---|---|---|
| Hyndman i Athanasopoulos, *Forecasting: Principles and Practice*, 3rd ed. — materiały autorów: [point accuracy](https://github.com/robjhyndman/fpp3_slides/blob/main/5-8-evaluating_point.Rmd), [rolling origin](https://github.com/robjhyndman/fpp3_slides/blob/main/5-10-tscv.Rmd), [distributional scores](https://github.com/robjhyndman/fpp3_slides/blob/main/5-9-eval-distributions.Rmd) | Tekst materiałów: rozdzielenie testu od developmentu, walidacja czasowa, pinball / Winkler / CRPS. | Ocena na nowych danych i osobno dla horyzontów; nie tylko training fit. Wszystkie prefiksy meczu muszą pozostać razem. |
| Grinsztajn, Oyallon, Varoquaux, *Why do tree-based models still outperform deep learning on tabular data?*, NeurIPS 2022 — [oficjalny benchmark](https://github.com/LeoGrin/tabular-benchmark), [publikacja](https://arxiv.org/abs/2207.08815) | README, identyfikacja publikacji i struktura replikacji benchmarku. | Proste modele tabelaryczne są istotnym punktem odniesienia. Nie wynika z tego, że dowolne drzewo wygra na dziesięciu trajectory outcomes. |
| Zeng et al., *Are Transformers Effective for Time Series Forecasting?*, AAAI 2023 — [kod autorów](https://github.com/cure-lab/LTSF-Linear), [publikacja](https://arxiv.org/abs/2205.13504) | README: Linear / NLinear / DLinear i porównania na przygotowanych benchmarkach. | Złożoność nie zastępuje silnego baseline. Wynik nie dowodzi nieskuteczności wszystkich Transformerów ani nie uzasadnia ponownego strojenia odrzuconego Ridge v1. |
| Nie et al., *A Time Series is Worth 64 Words*, ICLR 2023 — [PatchTST](https://github.com/yuqinie98/PatchTST), [publikacja](https://arxiv.org/abs/2211.14730) | README: patching i oddzielne tryby supervised / self-supervised. | Badania reprezentacji sekwencji są zasadne. Beyond ma już SSP; kolejny Transformer nie zastąpi testu jego użyteczności dla frekwencji. |
| Hollmann et al., *Accurate predictions on small data with a tabular foundation model*, Nature 2025 — [TabPFN](https://github.com/PriorLabs/TabPFN), [DOI](https://doi.org/10.1038/s41586-024-08328-6) | Oficjalne README, identyfikator publikacji i informacje o wersjach/licencjach. | Możliwy późniejszy, pojedynczy comparator. Pretraining nie tworzy niezależnych etykiet meczów ani nie usuwa temporal leakage. Wersję i warunki użycia trzeba przypiąć przed testem. |
| Ansari et al., *Chronos* (2024), *Chronos-2* (2025) — [repozytorium autorów](https://github.com/amazon-science/chronos-forecasting), [Chronos](https://arxiv.org/abs/2403.07815), [Chronos-2](https://arxiv.org/abs/2510.15821) | README: pretrained forecasting, nowsza obsługa covariates i multivariate. | Opcjonalny benchmark przyszłej trajektorii proxy; prognoza inventory nie jest automatycznie prognozą frekwencji lub płatnej sprzedaży. |
| Das et al., *A decoder-only foundation model for time-series forecasting*, ICML 2024 — [TimesFM](https://github.com/google-research/timesfm), [publikacja](https://arxiv.org/abs/2310.10688) | README projektu i aktualne informacje o modelach/licencjach. | Alternatywa badawcza, nie krytyczna zależność MVP. Nie przenosić wyników generic benchmarku na ticketing. Warunki użycia zależą od checkpointu. |
| Aksu et al., *GIFT-Eval* (2024) — [oficjalny benchmark](https://github.com/SalesforceAIResearch/gift-eval), [publikacja](https://arxiv.org/abs/2410.10393) | README: wiele domen/częstotliwości, metryki probabilistyczne i jawne informacje o leakage. | Potrzebne są baseline, reprodukowalne splity i kontrola ekspozycji danych; miejsce w leaderboardzie nie zastępuje testu Beyond. |
| M4 i M5 — [repozytorium M4](https://github.com/Mcompetitions/M4-methods), [repozytorium M5](https://github.com/Mcompetitions/M5-methods) | README organizatorów: dane, baseline, osobne prognozy punktowe i przedziałowe, kod oceny; M5 rozdziela validation/evaluation. | Zachować reprodukowalność i rozdział accuracy/uncertainty. M5 ocenia retail sales m.in. przez WRMSSE/WSPL; wyników nie przeliczać na attendance MAE Beyond. Nie weryfikowano tu liczbowych przewag zwycięzców. |
| Romano, Patterson, Candès, *Conformalized Quantile Regression* (2019) — [kod autorów](https://github.com/yromano/cqr), [publikacja](https://arxiv.org/abs/1905.03222) | README i kod rozdzielający kalibrację od fitowania oraz mierzący coverage i długość przedziału. | Osobna warstwa niepewności po zebraniu odpowiednich residuals. Standardowe marginalne gwarancje wymagają założeń, które nie przenoszą się automatycznie na zależne mecze i drift. |
| Gibbs i Candès, *Adaptive Conformal Inference Under Distribution Shift* (2021) — [kod autorów](https://github.com/isgibbs/AdaptiveConformal), [publikacja](https://arxiv.org/abs/2106.00170) | Implementacja sekwencyjnej aktualizacji miscoverage po wyniku. | Monitorować zmianę błędów w czasie. Adaptacja to osobny wersjonowany protokół, nie cicha zmiana frozen v1. Long-run coverage nie gwarantuje trafności konkretnego meczu. |
| Xu i Xie, *Conformal Prediction Interval for Dynamic Time-series* (2021) — [EnbPI](https://github.com/hamrel-cxu/EnbPI), [publikacja](https://proceedings.mlr.press/v139/xu21h.html); Zaffran et al., *Adaptive Conformal Predictions for Time Series* (2022) — [kod autorów](https://github.com/mzaffran/AdaptiveConformalPredictionsTimeSeries), [publikacja](https://arxiv.org/abs/2202.07282) | README i konfiguracje badań zależności czasowych, kalibracji oraz sequential/random split. | Nie traktować dziennych prefiksów jak IID. Na małej próbie nie rozpoczynać kolejnego turnieju kalibratorów. Conformal sam z siebie nie obniża punktowego MAE. |

## 3. Co już mamy, a co jest faktycznym ograniczeniem

Dokumenty operacyjne opisują stan z **2026-10-30**; nie odświeżano w tym przeglądzie live DB ani Actions. Nie uznajemy dawnych liczników, terminów ani watchdogu za stan z 3 listopada.

Gotowe elementy obejmują:

- [PIT daily dataset](demand_engine/daily_trajectory_dataset.py), [feature store trajektorii](demand_engine/live_trajectory_feature_store.py);
- [immutable attempts / predictions / scores i MAE by horizon](../supabase/sql/daily_trajectory_prospective_evidence_v1.sql);
- [event-balanced prospective evaluator](../supabase/sql/prospective_attendance_eval_v1.sql);
- [dashboard SQL surfaces](../supabase/sql/dashboard_p9_mae_lifecycle_v1.sql).

Wykorzystujemy istniejący feature store i attendance ledger. Nowa ścieżka wymaga jednak osobnego lub rozszerzonego ledgeru z rozróżnieniem issued_as_of_at i target_at oraz nowego daily-target scorera; istniejący zapis końcowej frekwencji ich nie zastępuje. Nie budujemy ponownie gotowej infrastruktury attendance ani platformy ciągłego retrainingu.

Structural Prior ma udokumentowaną historię **1 530 meczów / 5 sezonów / 7 198 eligible horizon rows** ([materializer](STRUCTURAL_PRIOR_MATERIALIZER_V1.md)). Zamknięte trajectory development miało **10 meczów / 19 wierszy / 5 outer test events**. To różne zbiory; nie należy mówić, że cały Beyond ma tylko dziesięć meczów danych.

Wąskie gardło trajectory to wiarygodne pary: **dane dostępne przed cutoffem → późniejszy rzeczywisty outcome**. Więcej snapshotów tych samych meczów nie zwiększa liczby niezależnych attendance outcomes.

W pierwotnym przeglądzie audytowano tylko repo beyond. Następnie 2026-11-03 sprawdzono także kod `/workspace/BeyondTicketingPanel`: główny wykres pokazuje historię końcowego P50, a miniwykres łączy obserwowany proxy prostą z końcową prognozą. Nie są to modelowe przewidywania kolejnych dni. Konkretny flow i luki są opisane w [kontrakcie daily path](DAILY_DEMAND_PATH_MVP_CONTRACT_V1.md); nie potwierdzono zgodności tego checkoutu z wdrożonym wydaniem panelu.

## 4. Produkt: co dokładnie prognozujemy

Obecny [outcome sync](../supabase/sql/ticket_event_outcome_history_sync_v1.sql) używa `reported_match_attendance`. To nie jest automatycznie liczba sprzedanych netto biletów ani liczba zeskanowanych wejść.

| Wielkość | Warunek uczciwej prezentacji |
|---|---|
| Końcowa frekwencja | Prognoza i wynik muszą mieć tę samą jawną definicję attendance. |
| Sprzedaż netto w czasie | Potrzebne rzeczywiste, timestampowane transakcje i zwroty/anulowania; jawne zasady karnetów i darmowych wejść. |
| Publiczna dostępność miejsc | To obserwacja inventory/proxy; zmiana może oznaczać sprzedaż, blokadę, rezerwację lub uwolnienie puli. |
| Przyszła ścieżka proxy | Oddzielny target i test względem genuine przyszłych obserwacji; final-attendance head sam nie dowodzi jakości takiej ścieżki. |

Najbliższe MVP: **obserwowana historia → dziś → prognozowana dynamika dostępności/popytu na kolejne dni**, z codzienną aktualizacją. Prognoza końcowej frekwencji jest osobnym wynikiem. Prawdziwe dane sprzedażowe są potencjalnym rozszerzeniem **po MVP**, jeśli staną się dostępne. Bez etykiet sprzedaży netto nie raportujemy zweryfikowanego MAE sprzedaży netto; można mierzyć MAE przyszłych publicznych obserwacji i oddzielnie MAE frekwencji.

Import prawdziwych danych historycznych może wzbogacić osobny research retrospektywny przy zweryfikowanej dostępności cech w czasie. Nie może naprawiać dawnych missed prospective rows ani udawać prognoz zapisanych przed wynikiem.

## 5. Kolejność dostarczania — daily-path MVP

Poprzedni szacunek 7–10 dni dotyczył demonstracji endpoint/scorecard. Po doprecyzowaniu pełnej ścieżki nie jest aktualną estymacją całości. Poniżej obowiązuje kolejność rezultatów; termin implementacji wymaga audytu danych i zakresu nowego ledgeru. Termin dowiedzenia jakości zależy dodatkowo od przyszłych obserwacji i meczów. Otwarte legalne okno istniejącego eksperymentu zawsze ma pierwszeństwo.

| Kolejność | Rezultat | Kryterium ukończenia |
|---|---|---|
| 1 | Aktualny evidence/data audit | Świeży read decision RPC; ocena istniejących frozen lanes oraz rzeczywistego pokrycia prefixów i przyszłych daily targets. Brak retuningu i naprawiania historii. |
| 2 | Precommit daily-path lane | Jawny publiczny target, reguła target-observation matching, issue cutoff i lead, baseline, jeden kandydat, event-grouped/PIT-safe evaluation i nieobejrzany przyszły strumień. |
| 3 | Dataset i predictor przyszłych dni | Zmienna długość genuine prefixu, future-target masks, persistence baseline i jeden direct multi-horizon challenger. MAE po lead time i event-balanced path MAE. |
| 4 | Immutable path ledger i dzienne inference/scoring | Osobne issued_as_of_at i target_at, codzienne prognozy przyszłych punktów, zachowane vintages, score po genuine obserwacjach. Osobna lane bez zmian frozen v1. |
| 5 | Jeden ekran w istniejącym panelu | Oś rzeczywistego czasu/P-N, obserwowany prefix, granica dziś/as-of, rzeczywista predicted future path, porównanie dawnej prognozy z obserwacją. Oddzielnie endpoint attendance i jego scorecard. |
| 6, drugorzędne R&D | Objective-alignment audit | Sprawdzona nowość wobec archiwum; jeden horyzont i osobny precommit/future validation. Nie zastępuje budowy daily path. |

Cały plan zakłada brak partnerskiego feedu sprzedażowego. Gdy nowy path challenger nie pokonuje baseline, raportujemy ten wynik; baseline musi być oznaczony jako baseline, a końcowa frekwencja nie zastępuje nieudowodnionej ścieżki.

### Minimalny ekran inwestorski

- Jeden mecz: prognoza frekwencji, horyzont, chwila utworzenia i ostatnia znana obserwacja.
- Główny wykres: obserwowana dostępność/proxy → dziś/as-of → rzeczywiste modelowe przewidywania kolejnych dni. Zachowana historia wydanych ścieżek pozwala ocenić wczorajszą prognozę po dzisiejszej obserwacji.
- Osobno historia rewizji końcowej frekwencji; nie łączyć jej z publiczną dostępnością w jedną udawaną krzywą sprzedaży.
- Po meczu: actual, AE incumbent, AE challenger, Delta AE.
- Scorecard po horyzontach: MAE incumbent / challenger / Delta, liczba niezależnych meczów i klubów, prediction coverage, fail-closed/missing, bias i tail error.
- Wyraźne rozróżnienie historical research, prospective collecting i evidence review ready; challenger jako shadow.
- Pokazać przedział tylko z istniejącą metodą i lineage albo oznaczyć brak kalibracji. Opcjonalne kolumny P10/P90 w SQL nie są dowodem działających przedziałów.

## 6. Najtańsza konkretna hipoteza ML: zgodność celu z MAE w osobach

**Aktualizacja wykonania2026-11-04:** poniższy pierwotny pomysł structural capacity-weighting został już wykonany i odrzucony w `MAE02_SEAT_WEIGHTED_MEDIAN_RESULT_V1.md`; nie traktować go jako nadal nieuruchomionego zadania. Nowe zaakceptowane uzupełnienie: `C1_MAE_LITERATURE_EXECUTION_SUPPLEMENT_V1.md`. Bieżący target-free audyt dotyczy ekspertaC1Ridge, a nie powtórzenia structuralweightingu: `C1_OBJECTIVE_GEOMETRY_AUDIT_RESULT_V1.md`.


To **proponowany ograniczony audit/ablation celu**, nie nowa informacja trajectory, nie precommit i nie zgoda na modyfikację frozen runtime. Priorytet trajectory z roadmap v6 pozostaje bez zmian.

W [structural_prior_runtime.py](demand_engine/structural_prior_runtime.py) trening używa:

`r_i = (attendance_i - baseline_i) / capacity_i`

oraz `model.fit(x_train, y_train)` bez `sample_weight`. Predykcja wraca do osób przez:

`attendance_hat_i = baseline_i + capacity_i * r_hat_i`

Dla T-14 / T-3 / T-1 estimator ma już `loss="absolute_error"`. Nie proponujemy więc po prostu „zacząć używać MAE”. T-7 używa Huber, T-30 ExtraTrees; nie mieszać tych zmian w jeden test.

Przy L1 na residual ratio empiryczny cel wynosi:

`sum_i abs(r_i - r_hat_i) = sum_i abs(seat_error_i) / capacity_i`

Natomiast dla jednego wiersza na mecz/horyzont waga:

`w_i = capacity_i / mean_training_capacity`

powoduje, że część L1 straty jest proporcjonalna do sumy błędów w osobach. To równość dla nieobciętej predykcji; ten sam istniejący clipping do pojemności należy zachować i raportować. Wagi nie zmieniają zasad równego ważenia meczów w ewaluacji.

Proponowany, jeszcze nieuruchomiony test:

1. Sprawdzić stare plany/wyniki, czy capacity-weighted objective był już badany. Wstępny search w runtime i dokumentach Structural Prior nie znalazł takiego wariantu; to nie dowód pełnego audytu archiwum.
2. Jeden horyzont **T-3**, wybrany z powodów metodologicznych: obecny estimator już używa L1. Nie wybierać najlepszego horyzontu po porównaniu wyników.
3. Roboczy ID `structural-seat-mae-alignment-v1`; identyczne cechy, baseline, estimator, hiperparametry i data boundary, jedyna ablation to opisane wagi. Sprawdzić unikalność event/horizon oraz PIT dostępność cech i etykiet.
4. Istniejący zamrożony incumbent pozostaje obowiązkowym comparator. Dodatkowy kontrolny research fit bez wag musi mieć identyczny training manifest, aby odizolować mechanizm od ewentualnej zmiany danych/runtime.
5. Historyczne, już obejrzane sezony to development/diagnostyka. Żaden ich wynik nie zostaje nazwany nowym untouched testem. Przed runem zdefiniować niezależny przyszły strumień, moment freeze i review schedule.
6. Po sprawdzeniu implementacji fitować osobny artifact raz, uruchamiać osobne shadow inference i nie reagować retuningiem na pierwsze wyniki. Nowa lane wymaga własnego protokołu zapisu i oceny.
7. Oceniać MAE w osobach, bias, tail error oraz podziały według klubów/pojemności. Nie wybierać wag, capów lub regularyzacji na starych exposed holdoutach.

Dlaczego to hipoteza, nie naprawa: ważony i nieważony problem mają ten sam idealny warunkowy medianowy cel przy odpowiednich założeniach; różnice dotyczą skończonej klasy modeli, regularyzacji i empirycznych trade-offów między stadionami. Wagi mogą pogorszyć wyniki części klubów. Algebra zgodności straty nie dowodzi poprawy out-of-sample.

## 7. Główne nowe R&D trajectory

Obowiązuje pętla:

`baseline → nowa informacja → prosty challenger → event-grouped/PIT-safe MAE → freeze → prospective shadow → genuine outcomes`

W MVP nową informację zbieramy z obecnych źródeł publicznych: genuine trajektorie kolejnych meczów, ich potwierdzone outcomes i jawnie dostępne metadane źródła. Zmiany dostępności nie są potwierdzeniem zakupów, zwrotów ani uwolnień puli. Samo dodanie nazw `releases`, `velocity`, `capacity normalization` nie jest nowością — te pojęcia występują już w feature store i wcześniejszych planach.

Główna nowa praca teraz: osobny eksperyment **prefix → wartości przyszłych dni**, jego dataset, issued/target ledger, daily scorer i wykres, zgodnie z [kontraktem daily path](DAILY_DEMAND_PATH_MVP_CONTRACT_V1.md). Targetem jest obserwowalna publiczna dostępność/proxy; ten model nie wymaga structural attendance prior jako warunku wejścia. Równolegle chronimy i oceniamy istniejące frozen attendance lanes oraz poprawiamy przyszłe zbieranie. Nie czekamy z tym na partnera.

Oddzielny, drugorzędny **residual attendance challenger** nad Structural Prior lub objective-alignment audit z §6 musi mieć konkretną nową hipotezę informacyjną lub mechanizm oraz osobny precommit i niezależną przyszłą ewaluację. Nie zastępuje modelu daily path. Nowe publiczne mecze mogą dostarczyć ewaluacji; sam przyrost snapshotów nie uzasadnia powtórzenia zamkniętych Lane A/B. Wybór dokładnej rodziny, parametrów i capów należy zapisać przed wynikami; ten przegląd nie wybiera ich post-hoc. Pozyskanie danych partnerskich nie jest warunkiem rozpoczęcia takiego R&D.

Chronos / TimesFM / TabPFN mogą później być jednym ograniczonym comparator, z przypiętym checkpointem, budżetem i poprawnym mapowaniem targetu. Nie są zależnością demonstracji. Nie uruchamiać jednocześnie turnieju GRU/LSTM/TCN/Transformer/AutoML.

Pogoda, hype i odds pozostają późniejszymi oddzielnymi hipotezami. Nie wznawiać już odrzuconych mechanizmów na tych samych wynikach. Nowa informacja o pogodzie oznacza m.in. prognozę rzeczywiście dostępną w cutoffie, nie późniejszą pogodę zaobserwowaną.

## 8. Jak wiarygodnie mierzymy dokładność attendance lanes

Poniższe jednostki i kontrakt 550 miejsc dotyczą frekwencji. Nowy model daily path mierzy MAE wybranej obserwowalnej wielkości po lead time i event-balanced path MAE według [własnego kontraktu](DAILY_DEMAND_PATH_MVP_CONTRACT_V1.md); nie dziedziczy automatycznie progów attendance.

1. Challenger i incumbent na **tych samych** event/horizon rows, z jawnym eligibility. Osobno pokazać całą osiągalną coverage i fallback incumbent, żeby odmowa prognozowania trudnych meczów nie udawała poprawy.
2. Liczyć AE w osobach. Dla summary z wieloma horyzontami najpierw średnia w meczu, następnie równa średnia między meczami. Osobno obligatoryjny MAE po horyzontach.
3. Wszystkie prefiksy meczu w jednym foldzie; chronologia i etykiety dostępne w chwili treningu, nie tylko wcześniejszy kickoff. Nie używać random-row CV ani dopisywania starych missed observations.
4. Raportować Delta MAE, signed bias, medianę i P90 AE, improvement rate, worst-event degradation, N meczów i klubów oraz source freshness/missingness.
5. Dla obecnych lanes obowiązuje [zamrożony kontrakt biznesowy](BUSINESS_MEANINGFUL_FORECAST_GAIN_V1.md): poprawa co najmniej **550 miejsc per oceniany horyzont** i wszystkie risk guards. Nie jest to wynik z literatury ani obiecana poprawa. Nowy protokół musi jawnie ustalić swoją aplikację kontraktu przed outcomes, bez obniżania progu obecnych lanes.
6. **8 niezależnych meczów / 5 klubów** to najwcześniejszy review, nie dowód stabilności ani automatyczna produkcja. Nie zatrzymywać testu przy pierwszym korzystnym wyniku. Przed formalnym wnioskiem o precyzji oszacowania potrzebna jest większa próba i jawna analiza niepewności; nie wymyślać arbitralnego magicznego N.
7. Ewentualne bootstrapy na poziomie meczów/bloków czasowych są zależne od założeń i słabe przy małym N lub powtarzających się klubach. Nie bootstrapować snapshotów jako niezależnych attendance outcomes.

### Przedziały

Obecny [frozen trajectory runner](run_trajectory_frozen_encoder_shadow_v1.py) zapisuje `challenger_p50`; sam schemat dopuszczający P10/P90 nie dowodzi ich prognozowania. Istniejący [conformal adapter](demand_engine/intervals.py) wymaga out-of-sample residuals tego samego modelu/protokołu.

Rozwijać uncertainty osobno i wersjonować. Dla nominalnego przedziału P10–P90 oceniać empirical 80% coverage, szerokość i interval score; dla kwantyli pinball loss. Szeroki przedział może zwiększać coverage bez zwiększania użyteczności. Przy ośmiu meczach coverage zmienia się skokami po 12,5 p.p.; nie deklarować na tej podstawie skalibrowanych przedziałów per klub/horyzont. Warstwa conformal nie zmienia automatycznie punktowego MAE.

## 9. Dwie odrębne definicje DONE

**MVP demonstracyjne:** jeden działający widok na prawdziwych niezmiennych danych, modelowe wartości przyszłych dni i codzienne rewizje zachowane w path ledgerze, jawny target, as-of i pochodzenie, poprawnie policzony path scorecard, rozróżnienie baseline/challenger i brak udawanej sprzedaży lub przedziałów. Endpoint attendance jest osobno. Można pokazać stan collecting; nie można nazwać go dowiedzioną przewagą. Sam wykres końcowego P50 nie spełnia daily-path DONE.

**Potwierdzona przewaga ML:** genuinely prospective wyniki tego samego zamrożonego kandydata, spełniony właściwy evidence gate i kontrakt efektu, risk guards oraz przegląd ograniczeń próby. Dopiero potem osobna decyzja o produkcji. Prognozowanie frekwencji nie dowodzi przyrostu sprzedaży; revenue uplift wymaga oddzielnego eksperymentu produktowego/causal.

Przez cały ten plan pozostają: `production_change=false`, `live_adjustment=0`, fail-closed, brak backfillu missed prospective windows, brak refitu frozen v1. Działające YAML i successful Actions nie są samodzielnie dowodem danych w DB ani jakości ML.
