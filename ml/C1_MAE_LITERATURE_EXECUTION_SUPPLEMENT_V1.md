# C1 MAE — uzupełnienie planu po ocenie literatury

2026-11-04. Użytkownik zaakceptował zapisanie tego planu i dalsze wykonanie. Uzupełnia `C1_LIVE_MAE_1200_PLAN_V1.md` oraz roadmap v6; nie zmienia żadnego zamrożonego modelu, bramki lub protokołu.

## Cel i kolejność

Obniżyć rzeczywiste MAE końcowej frekwencji w kierunku1200miejsc. Rozszerzenie treningu C1z9do20meczów jest kontrolowanym pierwszym eksperymentem, a nie kompletnym programem ani dowodem osiągnięcia celu. Codzienna przyszła dostępność miejsc jest osobnym targetem i metryką.

1. **Kompletność i poziom bazy.** Zweryfikować wcześniejsze domowe frekwencje Wisły/Górnika oraz sześć brakujących wynikówOct30–Nov2. Rzeczywiste priory największych błędów miały season_home_n=0. Po uzyskaniu wiarygodnych źródeł zachować pochodzenie i faktyczny czas pozyskania, porównać wpływ na nowy wersjonowany research; nie regenerować dawnych prognoz lub missed observations. Zewnętrzna weryfikacja pozostaje zablokowana przez dostęp do źródeł. Dane partnerów nie są warunkiemMVP.
2. **Cel treningowy live zgodny z MAE.** Najpierw audyt nowości i algebraicznego celu. C1Ridge używa kwadratowego błędu direct occupancy; MAEw osobach odpowiada medianie warunkowej. Osobny, dokładnie zdefiniowany eksperyment medianowy może być uzasadniony po tym audycie. Trzeba przed fit ustalić cechy, transformację targetu, regularizację, wagi, clipping, komparatory i nowy strumień przyszły. Nie przedstawiać ponownego uruchomienia starych modeli jako nowości.
3. **Rzeczywisty sygnał dynamiki.** Sprawdzić dodatkową informację z genuine prefiksu i horyzontu: tempo, zmiana tempa, plateau/surge i zmiany obserwowalności źródła. Zamrożony dziennyv1ma120zerowych współczynników historii względnej; działa osobny fixed24h-drift comparator. Kolejny learner wymaga własnej hipotezy/precommitu i porównania z persistence/drift na identycznych nowych targetach. Nie powtarzać odrzuconych LaneA/B/GRU na odsłoniętych outer events. Lepsza ścieżka inventory nie dowodzi automatycznie lepszej frekwencji.
4. **Ocena i decyzja.** Wszystkie prefiksy meczu razem; czasowe rozdzielenie treningu od testu; porównania na tych samych chwilach. Raportować latest/window MAE, horyzonty, coverage/missing, bias, P90/worst i niepewność różnicy.30nowych meczów/8klubów jest pierwszym przeglądem obecnego nowego kandydata, nie gwarancją precyzji. Nie zmieniać jego bootstrapu/bramek po wynikach. Przedziały niepewności są osobnym produktem; conformal nie obniża sam punktowegoMAE.

Kandydat `c1-training-expansion-v1-frozen-2026-11-04-n20` pozostaje bez zmian i zbiera przyszłe dowody równolegle. Kolejny eksperyment otrzyma inną wersję i precommit przed fit;20obecnych meczów pozostaje training/exposed, nigdy świeżym holdoutem.

## Co archiwum już wyklucza

- StructuralT-1już używa `absolute_error`; nie proponujemy „włączyćMAE” w całej bazie.
- Capacity-weighting w structuralMAE-02pogorszył development i został odrzucony; nie powtarzamy go jako nowego odkrycia.
- C1tournamentv1/v2obejmował już robust/L1tree challengers i club-aware variants. Samo użycieL1, modelu klubowego lub nowszej nazwy nie jest nową hipotezą. W sprawdzonychC1v1/v2nie znaleziono wykonanego liniowego `QuantileRegressor`; starsza roadmapv3go proponowała, co nie jest dowodem wykonania. Nowość konkretnego eksperymentu wymaga dalszego sprawdzenia kontraktu, nie tylko nazwy klasy.
- D2residual/P2ma5157,52MAEna identycznychC1chwilach wobec4121,45; nie promujemy go z wcześniejszego porównania na późniejszych danych.

## Literatura i granice wniosków

Ponownie przeczytano materiały autorówFPP3 o [ocenie prognoz punktowych](https://github.com/robjhyndman/fpp3_slides/blob/main/5-8-evaluating_point.Rmd), [rolling-origin validation](https://github.com/robjhyndman/fpp3_slides/blob/main/5-10-tscv.Rmd) oraz README [tabular benchmark](https://github.com/LeoGrin/tabular-benchmark). Zależność MAE–mediana jest własnością straty, nie gwarancją przewagi skończonego learnera nad Ridge.

Istniejący `AI_LITERATURE_REVIEW_AND_MVP_PLAN_2026-11-03.md` opisuje celowany przegląd materiałów autorów, nie cały stan literatury do2026. Pełne prace domenowe o booking curves/demand unconstraining nie zostały zweryfikowane. Uzupełnić tę lukę, zachowując rozróżnienie transakcji, dostępności i frekwencji; nie przenosić wyników hoteli/retail lub pretrained benchmarków na obiecaną poprawęBeyond. Nie uruchamiać turniejuTransformerów bez uzasadnionej luki reprezentacji.

## Równoległa aktualizacja panelu

Wykres realnej obserwowanej historii→dziś→modelowe przyszłe dni i zachowane vintages jest przygotowany w panelPR8. Dodajemy czytelny oddzielny wynik istniejącegoC1v8z aktualnego publicznego read-only dashboardu. Rozróżniać kod/testy, VercelPreview, wdrożenieProduction i faktycznie podłączony livefeed. Brak outcome pozostaje brakiemMAE. Aktualizacja prezentacji nie aktywuje modelu ani nie dowodzi accuracy.

`production_change=false`, `live_adjustment=0`.

## Wykonanie — 17:36 UTC

Punkt 1 częściowo wykonany: 15 rekordów / 5 potwierdzonych outcomes, event445 zablokowany. Czas wiedzy w bazie zachowany, ale starszy konsument go usuwa. Kolejne konkretne zadanie to wersjonowana integracja kontroli known-at (`ATTENDANCE_KNOWLEDGE_TIME_AUDIT_V1.md`), bez zmiany modeli lub backfill. Punkt 2 wykonany do freeze osobnej mediany (`C1_SEAT_MEDIAN_RESULT_V1.md`), przyszłe MAE nadal null. Punkt 3 ma dwa pierwsze wyniki inventory v1 i 16 nowych punktów drift bez ocen; żadnego retuningu. Zamrożone review gates pozostają bez zmian. To postęp wykonania zaakceptowanego planu, nie nowa strategia lub deklaracja osiągnięcia 1200.
