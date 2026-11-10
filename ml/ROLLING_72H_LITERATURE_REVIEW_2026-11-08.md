# Beyond: weryfikacja bibliograficzna prognoz 24/48/72 h i decyzji klubu

Data: **2026-11-08**. Przegląd poprzedza wykonanie [planu rolling72](ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1.md). **Nie wykonano treningu, zmiany modelu, aktywacji ani zapisu prognoz.**

## 1. Werdykt

**Kierunek jest metodologicznie uzasadniony: prognozować przyszły przebieg na podstawie rzeczywistych obserwacji, od początku śledzenia sprzedaży i przy każdym kolejnym stanie wiedzy. Literatura nie wyznacza jednak jednego algorytmu gwarantującego najniższe MAE ani osiągnięcie około 1200 miejsc.** Ten wynik wymaga nowych danych i oceny w Beyond.

Plan wymaga doprecyzowań przed implementacją:

1. Prognozy +24/+48/+72 h są ruchome przez cały okres sprzedaży, np. P-50→P-49/P-48/P-47 oraz P-10→P-9/P-8/P-7. Model powinien uwzględniać zarówno czas do meczu, jak i horyzont prognozy [R1].
2. Pierwszym odniesieniem muszą być proste metody i historyczne krzywe zmian na porównywalnym etapie. Mały model kwantylowy jest kandydatem, nie z góry zwycięzcą [R1,R2,R3,R6].
3. Cel minimalnego MAE wspiera prognozę medianową. Przy rzadkich zmianach taka prognoza może być płaska i nadal dobrze wypadać w MAE. Dlatego obok dokładności mierzymy wykrywanie istotnego przyspieszenia/zastoju, bez usuwania spokojnych lub trudnych przypadków [R2,R3].
4. Dla decyzji sektor1/sektor10 potrzebne są porównywalne obserwacje konkretnych sektorów. Poprawna prognoza sumy stadionu sama nie identyfikuje przyszłości poszczególnych sektorów [R3 oraz wniosek projektowy].
5. Prognoza popytu przy utrzymaniu warunków i oszacowanie efektu nowej ceny/reklamy to odrębne zadania. MAE pierwszej nie dowodzi rentowności drugiego [R4,R5,R10].
6. Dowód jakości powstaje na późniejszych meczach, z cechami i etykietami dostępnymi we właściwym czasie. Tysiące zależnych odczytów nie tworzą tysięcy niezależnych meczów [R1 oraz protokół Beyond].

To **celowany przegląd** materiałów metodycznych, źródeł autorów i wybranych tekstów revenue management, z jawnym zakresem dostępu w bibliografii. Nie jest to systematyczny przegląd całej literatury AI ani potwierdzenie skuteczności konkretnego modelu na danych Beyond.

## 2. Co dokładnie prognozujemy dla klubu

Pytanie biznesowe brzmi: **jak będzie rozwijać się zainteresowanie i zapełnianie meczu w najbliższych dniach, czy przebieg jest zgodny z planem i gdzie klub powinien rozważyć reakcję?** Końcowa frekwencja pozostaje ważna; sama jej pojedyncza prognoza nie odpowiada na to pytanie.

Potrzebne są dwa powiązane wyniki:

| Wynik | Sens dla klubu | Prawda do późniejszej oceny |
|---|---|---|
| Przyszły stan i zmiana za 24/48/72 h | Oczekiwany rozwój popytu/zapełniania, docelowo per sektor, na każdym etapie sprzedaży | Rzeczywisty późniejszy stan tej samej mierzonej wielkości |
| Końcowa frekwencja | Przewidywany ostateczny wynik meczu, aktualizowany wraz z nową historią | Potwierdzona frekwencja po meczu, z opisaną definicją |

Docelowo klub może mierzyć sprzedane/uprawnione bilety. W obecnym MVP bez transakcji partnerskich obserwujemy **publiczną dostępność i jej zmiany**. Nie są one automatycznie zakupami ani wejściami na stadion. Poziom zajętości wyliczony z puli jest proxy; jego tożsamość i zakres muszą pozostawać opisane. To ograniczenie danych, nie powód do odłożenia całego MVP.

Nie tworzymy etykiety „rzeczywista frekwencja w P-47” przez skopiowanie końcowego wyniku do wcześniejszych dni. Prognoza przyszłego stanu ma własne późniejsze obserwacje. Przełożenie proxy na końcową frekwencję trzeba oddzielnie nauczyć/skalibrować i sprawdzić. Niski MAE dostępności nie potwierdza celu około 1200 miejsc frekwencji.

## 3. Jak literatura wspiera konstrukcję prognozy

### Horyzont oraz etap sprzedaży

Materiały FPP3 rozdzielają prognozy ex ante od takich, które wykorzystują później poznane wartości wejść, oraz pokazują modele z opóźnionymi predyktorami dla konkretnego horyzontu [R1]. Praktyczny opis systemu Airbnb uwzględnia lead time, zróżnicowanie obiektów i zmianę popytu w czasie [R4].

W Beyond oznacza to funkcję:

`prognoza_stanu(t+h) = f(historia_rzeczywiście_znana_do_t, czas_do_meczu, h, kontekst_znany_do_t)`

Nie wystarczy osobny stały wynik dla meczu ani prosty model ignorujący etap sprzedaży. P-50 i P-10 mogą mieć inne tempo i inną niepewność. Dokładne przedziały etapów raportowania zapisujemy przed testem; nie wybieramy później najkorzystniejszego horyzontu.

Pokrycie danych badamy w dwóch niezależnych osiach: **czas do meczu × horyzont przyszłości**. Prognoza+72h w P-50 jest innym przypadkiem niż+72h w P-10. Dobry wynik jednej komórki nie potwierdza drugiej. Do tego raportujemy długość rzeczywiście znanej historii i klub/sektor; nie zakładamy wsparcia P-50 tylko dlatego, że model umie wyprodukować liczbę.

Prognozy bezpośrednie dla24/48/72h są rozsądnym pierwszym wariantem. Mogą być oddzielnymi głowami albo jednym modelem z horyzontem jako wejściem. Literatura nie dowodzi, że jedna z tych reprezentacji zawsze wygrywa; wybór dla pierwszego eksperymentu należy zamknąć w precommicie. Nie podajemy modelowi rzeczywistych przyszłych odczytów ani przyszłej zrealizowanej ceny/reklamy.

### Kotwica, przyrosty i ich ograniczenie

Persistence i drift są pełnoprawnymi benchmarkami, a nie atrapami [R1]. Dla tej samej dostępnościA można prognozować:

`A_hat(t+h) = A(t) + delta_hat(t,h)`

To dobrze zakotwicza przyszłą ścieżkę w ostatnim rzeczywistym odczycie. **Sama zamiana targetu na przyrost nie gwarantuje obniżenia MAE**, ponieważ przy tej samej kotwicy:

`abs(A(t+h) - [A(t)+delta_hat]) = abs([A(t+h)-A(t)] - delta_hat)`.

To własne przekształcenie algebraiczne, nie wynik nowego eksperymentu. Poprawa musi pochodzić z dodatkowej informacji lub lepszego uogólniania. Nie wystarczy przerysować krzywej lub przesunąć poziomu na wykresie.

### Rzeczywisty prefix i pełny kontekst

Feature store ma zachować cały rzeczywisty prefix i jego czasy. Pierwsza reprezentacja może go kompresować do jawnych cech: ostatni poziom, obserwowana zmiana od początku dostępnego fragmentu, dłuższy profil zmian i niedawne tempa6/24/72h. Przed fit ustalamy dokładne cechy i przeprowadzamy test rzeczywistego użycia historii; samo przekazanie całej sekwencji tego nie dowodzi.

Pierwszy odczyt **nie dowodzi daty rozpoczęcia sprzedaży**. Jeśli śledzenie zaczęło się później, cechy opisują obserwowany fragment, a nie wymyśloną sprzedaż od zera. Czas monitorowania i liczba pomiarów są także informacją o pokryciu, więc nie wolno bez audytu traktować ich jako popytu.

### Co stosujemy przy pierwszym odczycie

Z jednego punktu nie identyfikujemy lokalnego nachylenia meczu. Prognoza początkowa musi wykorzystywać wcześniej poznane zachowanie innych meczów na podobnym etapie i jawnie zaznaczać ograniczoną historię. To **propozycja modelowania dla Beyond**, nie dowiedzione w publikacjach twierdzenie o naszym MAE.

Do benchmarków dodajemy osobno wersjonowaną **warunkową krzywą/pickup**: ostatni poziom plus historyczna zmiana dla tego etapu i horyzontu, z łączeniem informacji między meczami, gdy klub/sektor ma mało danych. Sposób grupowania, wygładzania i braków trzeba ustalić przed oceną. Nie wolno budować tej krzywej z przyszłych wyników badanego meczu.

Klasyczne prace o booking horizon i porównaniu metod hotelowych są właściwą bibliografią domenową [R12,R13], ale w tej sesji zweryfikowano jedynie ich rekordy bibliograficzne. **Nie nazywamy proponowanego baseline odtworzeniem ich algorytmów ani nie przypisujemy im nieprzeczytanych wyników.**

Obecny frozen drift wymagający doby historii pozostaje bez zmian. „Od pierwszego odczytu” jest kontraktem nowej wersji, a nie zgodą na rozluźnienie starej eligibility lub dopisanie dawnych prognoz.

### Pierwszy uczony kandydat

Mały globalny model drzewiasty kwantylowy, korzystający wspólnie z meczów i horyzontu, jest uzasadnionym kandydatem dla tabeli cech [R6]. Nie wynika stąd jego przewaga na kilkunastu meczach, nad krzywą bookingową ani nad prostym trendem. Abstrakty dwóch badań hotelowych wskazują różnych zwycięzców w odmiennych danych i metrykach [R14,R15]; przewaga ANN w R15 jest opisana przez MAPE. Nie jest to bezpośrednie porównanie MAE ani wynik, który wolno przenieść na Beyond.

Kolejność to: wspólna definicja targetu → persistence/drift/warunkowa krzywa → jeden nowy kandydat → uczciwy test. Nowy Transformer lub model foundation pozostaje opcjonalnym późniejszym porównaniem. Zero-shot nie oznacza, że z jednego odczytu można wiarygodnie poznać lokalną dynamikę [R11].

## 4. Minimalizacja MAE i użyteczność ostrzeżeń

Dla absolutnego błędu właściwym funkcjonałem prognozy punktowej jest mediana warunkowa, a dla błędu kwadratowego średnia [R2]. P50 dla przyszłego stanu jest więc zgodne z celem minimalnego MAE. To nie jest powód do powrotu do samej mediany końcowej frekwencji.

Oficjalny przewodnik M5 wyjaśnia jednak, że przy popycie z wieloma zerami MAE może premiować prognozy bliskie zeru; dlatego ich zadanie prognozowania średniego popytu używało RMSSE [R3, część Evaluation]. **Beyond zachowuje MAE**, zgodnie z celem użytkownika. Dodajemy rozliczenie, czy model daje operacyjnie przydatne wyprzedzenie.

Raport nowej wersji obejmuje:

- MAE osobno +24/+48/+72 h na wszystkich kwalifikujących się wydaniach, z niezależnymi meczami jako jednostką;
- bias, P90/worst error, kluby/sektory, etap do meczu i długość historii;
- porównanie z persistence, drift na wspólnym pokryciu i warunkową krzywą;
- trafność, fałszywe alarmy i rzeczywiste wyprzedzenie ostrzeżeń o przyspieszeniu/zastoju;
- kalibrację ryzyka i przedziałów, kiedy dane wystarczą do ich rzetelnej oceny.

Reguły ostrzegania i istotności biznesowej ustalamy przed testem, na danych treningowych lub wcześniej zapisanych celach klubu. Nie wybieramy po wyniku tylko aktywnych dni, korzystnych klubów lub dobrego wariantu prognozy. Przekroje spokojnych/aktywnych dni są diagnostyką, nie podmianą głównego mianownika.

Cel około 1200 miejsc dla frekwencji pozostaje kamieniem milowym; literatura nie stanowi dowodu, że jest osiągalny na obecnych źródłach. Dla72h trzeba jawnie wskazać mierzony stan i jego własny benchmark. Nie przenosimy wyniku 13 miejsc dostępności na obietnicę błędu frekwencji.

## 5. Sektory i wspólny model meczu

R3 pokazuje znaczenie grupowania danych i ocen na różnych poziomach, ale pochodzi z retailu, nie z biletów. **Decyzja dla Beyond**: najpierw audyt tożsamości i pokrycia sektorów; potem współdzielony model z kontekstem sektora/klubu i rozsądnym łączeniem informacji. Nie trenujemy niezależnego rozbudowanego modelu dla każdego skąpego sektora.

Sektor1 i sektor10 muszą mieć prawdziwe osobne obserwacje, spójne mapowanie i historię puli. Sama suma stadionu nie wystarcza do odtworzenia ich przyszłości. Gdy danych brak, produkt mówi o braku pokrycia; nie rozdziela sumy arbitralnie.

Ważne matematycznie: **mediana sumy nie musi być sumą median**. Nie wolno obiecać, że niezależne P50 sektorów po dodaniu automatycznie dają optymalne P50 stadionu. Spójność można projektować przez wspólne scenariusze/dystrybucje albo jawną konstrukcję bottom-up, a jej wpływ na MAE trzeba zmierzyć. Nie stosujemy automatycznie metod optymalnych dla MSE jako rzekomo optymalnych dla MAE.

Równie ważne: zero dostępnych miejsc jest poprawną obserwacją podaży, ale nie oznacza zerowego niezaspokojonego popytu. Zmiana puli, blokada lub zwolnienie miejsc może zmienić proxy bez zakupu. Nie zmieniamy dawnych zer i ich frozen scoringu; ograniczenia latentnego popytu opisujemy oddzielnie.

## 6. Jak uczciwie sprawdzić prognozę w P-50, P-10 i dalej

FPP3 uzasadnia ocenę z przesuwanym początkiem prognozy i rozdzielenie treningu od późniejszych wyników [R1]. Dla Beyond potrzebne są dodatkowo grupy meczowe, bo prefixy jednego meczu są zależne.

1. Zamrażamy definicję przykładu: mecz/sektor, rzeczywisty czas wydania, historia znana do niego, target i horyzont.
2. W treningu są tylko przykłady, których rzeczywisty target i jego dostępność były znane przed cutoffem danego fitu. Przykład+72h nie staje się dostępny tylko dlatego, że minął jego dzień wydania.
3. Wszystkie prefixy testowego meczu pozostają poza dopasowaniem/preprocessingiem i doborem parametrów. Jego wcześniejsza historia może być wejściem wydanej prognozy, ale nie staje się ukrytym treningiem na tym samym meczu.
4. Porównujemy identyczne issue/targety; osobno pokazujemy brakujące źródła, krótki start, dojrzałe cele i scenariusze interwencji.
5. Parametry wybieramy wewnątrz treningu. Stare odsłonięte mecze pozostają development/diagnostyką; nowa nazwa nie tworzy holdoutu.
6. Po zamrożeniu zapisujemy przyszłe prognozy przed wynikiem, zachowując wszystkie vintages i rzeczywiste luki.

MAE liczymy najpierw wewnątrz meczu, potem między meczami. Główne horyzonty i koszyki etapu sprzedaży są zapisane przed testem. Raportujemy także wrażliwość na powtarzające się kluby i kolejki; nie udajemy niezależności tysięcy snapshotów.

Próg 30 nowych meczów/8klubów jest **planem pierwszego przeglądu Beyond**, a nie progiem dowiedzionym przez literaturę. Nie gwarantuje wąskiego przedziału ani 1200 MAE. Bootstrap jest po meczach, z jawnym ograniczeniem małej liczby klubów i możliwej zależności w czasie. Istniejących frozen bootstrapów/bramek nie zmieniamy tą uwagą.

## 7. Niepewność

P50 nie daje samodzielnie prawdopodobieństwa, że sektor będzie poniżej planu. Do ostrzeżeń potrzebna jest dystrybucja lub skalibrowane przedziały, oceniane przez coverage, szerokość i właściwy score [R1,R7,R8].

Standardowe gwarancje conformal nie przenoszą się automatycznie na zależne, zmieniające się dane. Metody czasowe istnieją [R8], ale także wymagają założeń i odpowiednich residuals. Conformal sam z siebie nie obniża punktowego MAE. Cztery mecze nie potwierdzają kalibracji per klub/sektor/horyzont.

Scenariusz „utrzymujemy cenę/promocję” ma własne założenia. Przedziały warunkowe nie obejmują automatycznie niepewności nieznanych przyszłych predyktorów [R1, sekcja7.6]. To trzeba ujawnić zamiast pokazywać arbitralną pewność.

## 8. Od prognozy do ceny i reklamy

**Pierwszy użyteczny produkt:** prognoza status quo i ostrzeżenie, że przy obecnych założeniach sektor może za 48–72 h odbiegać od wcześniej zapisanego celu lub oczekiwanego przebiegu. Klub dostaje czas na decyzję.

**Następny osobny wynik:** ile zmieni konkretna reklama lub nowa cena i czy zwiększy przychód/zysk. To wymaga historii rzeczywistych działań, ekspozycji na ceny, odpowiednich założeń identyfikacji i testu efektu. Klasyczne pricing/learning rozdziela uczenie popytu i optymalizację decyzji [R5]. EconML jawnie wymaga założeń o obserwowaniu zmiennych wpływających jednocześnie na działanie i wynik [R10]. Sama regresja ceny na sprzedaż nie zapewnia tej identyfikacji.

Przykład błędu: klub obniża ceny właśnie na mecze ze słabym popytem. Model korelacyjny może uznać, że niższa cena powoduje słabą sprzedaż. Selektywne stosowanie rekomendacji przez zarządcę tworzy kolejną zależność — problem opisany także w Airbnb [R4].

R4 opisuje estymację booking probability, osobny model strategii, dedykowane metryki oraz testy A/B. Autorzy wskazują, że pewne podejścia oparte na oszacowanej krzywej popytu nie optymalizowały przychodu w ich testach online. **To nie dowód porażki takich metod zawsze; to mocny powód, aby nie utożsamiać jakości prognozy z jakością decyzji.**

Od początku warto zapisywać również ręcznie: scenariusz, rekomendację, rzeczywiście wykonaną cenę/promocję, sektor, czas i — jeśli dostępny — budżet. Nie wymaga to pełnej integracji transakcyjnej jako warunku demonstracji. Estymacja skutku wymaga później rzeczywistej zmienności/eksperymentu; brak informacji pozostaje UNKNOWN.

Ocena działań dotyczy przyrostowego przychodu lub marży, kosztu reklamy, ograniczeń puli oraz możliwego przesunięcia popytu między sektorami i w czasie. Dla decyzji przychodowej potrzebna jest wartość oczekiwana/ryzyko wyniku, a nie sama mediana o najmniejszym MAE. Nie uruchamiamy automatycznej polityki cenowej ani bandyty/RL na obecnym dowodzie.

## 9. Zmieniona kolejność wykonania

| Kolejność | Zadanie | Dowód przed przejściem dalej |
|---|---|---|
| 0 — ten przegląd | Ustalić co uzasadnia literatura i co pozostaje hipotezą | Jawne źródła i zakres dostępu; brak obietnicy algorytmu/1200 |
| A | Audyt targetu, pierwszego odczytu,24/48/72h, etapów do meczu i sektorów | Rzeczywiste pokrycie, znaczenie pomiaru i znane-at-czasu źródła |
| B | Feature store i wspólne baseline: persistence, frozen drift, osobna warunkowa krzywa | Ten sam issue/target i prawdziwe braki; brak dopisywania dawnych forecastów |
| C | Jeden globalny kandydat P50 przyszłej zmiany, z zamkniętym precommitem | Rzetelna walidacja, audyt użycia historii i zachowanie negatywnych wyników |
| D | Utrwalanie przyszłych wersji i panel z obserwacjami/przyszłością | Rzeczywisty odczyt→prognoza→zapis→panel, także początek krótkiej historii |
| E | Odczyty po24/48/72h, MAE/ryzyko i ocena wyprzedzenia | Zamrożone mianowniki, brak leakage, realne późniejsze obserwacje |
| F | Przegląd skuteczności i jakości ostrzeżeń | Przewaga wobec silnych benchmarków oraz risk/coverage guards |
| G | Osobny etap testowania ceny i reklamy | Dane o rzeczywistych działaniach i identyfikowalny/eksperymentalny efekt na przychód |

A–F pozostaje pierwszym celem MVP; G jest niezbędne przed obietnicą skutecznego automatycznego wyboru ceny/reklamy. Dane partnerskie nie są warunkiem uruchomienia A–F na jasno nazwanych źródłach publicznych. Modeli frozen, starych prognoz i zasad oceny nie zmieniamy.

## 10. Bibliografia i faktyczny zakres weryfikacji

Poniższe linki DOI/arXiv identyfikują publikacje. W kolumnie dostępu podajemy **co rzeczywiście przeczytano**, a nie co tylko istnieje pod linkiem.

| ID | Źródło | Rzeczywiście zweryfikowany materiał i granica wniosków |
|---|---|---|
| R1 | Hyndman, R.J.; Athanasopoulos, G., *Forecasting: Principles and Practice*, 3rd ed.; [materiały autorów](https://github.com/robjhyndman/fpp3_slides) | Pełne pliki źródłowe slajdów5.2,5.8,5.9,5.10,7.6,7.8,8.2: benchmarki, MAE, kwantyle, rolling origin, scenariusze i kauzalność. Nie cały podręcznik. |
| R2 | [scikit-learn: model evaluation](https://github.com/scikit-learn/scikit-learn/blob/main/doc/modules/model_evaluation.rst), część Scoring rules; przywołuje Gneiting, *Making and Evaluating Point Forecasts*, [arXiv0912.0902](https://arxiv.org/abs/0912.0902), publikacja [DOI](https://doi.org/10.1198/jasa.2011.r10138) | Odczytano techniczną dokumentację funkcjonałów i strat. Nie pobrano pełnego artykułu Gneitinga; nie przypisujemy mu szczegółów niezweryfikowanych w tej sesji. |
| R3 | M5 Competition, *Competitors’ Guide* (2020), [plik organizatorów](https://github.com/Mcompetitions/M5-methods/blob/master/M5-Competitors-Guide.pdf) | Pobrano pełny PDF; odczytano opis danych, hierarchii i Evaluation, w tym jawne uzasadnienie RMSSE wobec median/zer. To benchmark retailu, nie wynik Beyond. |
| R4 | Ye,P. et al. (2018), *Customized Regression Model for Airbnb Dynamic Pricing*, KDD, [DOI10.1145/3219819.3219830](https://doi.org/10.1145/3219819.3219830) | Pobrano pełny oryginalny PDF ze [studenckiego archiwum kursu](https://github.com/changyaochen/Columbia_IERO_E4601/tree/master/paper); odczytano abstrakt i fragmenty sekcji1–4 dotyczące lead time, identyfikacji elasticity, częściowej adopcji, metryk i A/B. Nie replikowano wyników. |
| R5 | den Boer,A.V., *Dynamic Pricing and Learning*, rozprawa doktorska, [kopiaPDF w archiwum kursu](https://github.com/changyaochen/Columbia_IERO_E4601/tree/master/paper) | Pobrano159-stronicowy tekst, odczytano wybrane fragmenty wprowadzenia, przeglądu i dyskusji uczenia/eksploracji. Data utworzenia kopiiPDF:2012-09-17; nie traktujemy jej jako niezależnej weryfikacji daty obrony/publikacji. Nie przeczytano wszystkich dowodów. |
| R6 | Grinsztajn,L.; Oyallon,E.; Varoquaux,G. (2022), *Why do tree-based models still outperform deep learning on typical tabular data?*, [repo autorów](https://github.com/LeoGrin/tabular-benchmark), [arXiv2207.08815](https://arxiv.org/abs/2207.08815) | README i zakres benchmarku/reprodukcji; pełny artykuł niedostępny przez proxy. Uzasadnia sens komparatora tabelarycznego, nie jego przewagę lokalną. |
| R7 | Romano,Y.; Patterson,E.; Candès,E.J. (2019), *Conformalized Quantile Regression*, [kod i opis autorów](https://github.com/yromano/cqr), [arXiv1905.03222](https://arxiv.org/abs/1905.03222) | README: rozdzielenie prognozy od kalibracji i zakres marginalnych gwarancji. Pełnego artykułu nie pobrano; nie przenosimy gwarancji na nasz zależny szereg bez założeń. |
| R8 | Xu,C.; Xie,Y. (2021), *Conformal Prediction Interval for Dynamic Time-series*, [repoEnbPI](https://github.com/hamrel-cxu/EnbPI), [publikacjaPMLR139](https://proceedings.mlr.press/v139/xu21h.html) | README, opis sekwencyjnej metody i reprodukcji; bez lokalnej replikacji i bez przeczytania pełnej publikacji. |
| R9 | Angelopoulos,A.N.; Bates,S. (2021), *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*, [materiały autorów](https://github.com/aangelopoulos/conformal-prediction), [arXiv2107.07511](https://arxiv.org/abs/2107.07511) | README i opis przykładów; nie pełny tekst. Użyte jako mapa zagadnień niepewności, nie dowód naszej coverage. |
| R10 | EconML, [DML](https://github.com/py-why/EconML/blob/main/doc/spec/estimation/dml.rst) i [forest estimators](https://github.com/py-why/EconML/blob/main/doc/spec/estimation/forest.rst) | Pobrano dokumentację źródłową. Odczytano formalne założenia, unconfoundedness oraz przykład wielu popytów/cen i cross-price elasticity. Nie przeczytano wszystkich cytowanych w niej artykułów. |
| R11 | Ansari,A.F. et al., *Chronos* (2024) i *Chronos-2* (2025), [repo autorów](https://github.com/amazon-science/chronos-forecasting), [raport2510.15821](https://arxiv.org/abs/2510.15821) | README autorów z zakresem zero-shot/covariates. Deklaracji benchmarków autorów nie replikowano ani nie przeniesiono na Beyond. |
| R12 | Weatherford,L.R.; Kimes,S.E. (2003), *A comparison of forecasting methods for hotel revenue management*, IJF19,401–415, [DOI](https://doi.org/10.1016/S0169-2070(02)00011-0) | Metadane/cytowanie w dostępnych rekordach bibliograficznych. **Nie odczytano pełnego tekstu ani abstraktu oryginału.** Nie przywołujemy jego liczbowych wyników. |
| R13 | Haensel,A.; Koole,G. (2011), *Booking horizon forecasting with dynamic updating: A case study of hotel reservation data*, IJF27(3),942–960, [DOI](https://doi.org/10.1016/j.ijforecast.2010.10.004) | Tytuł, autorzy, DOI i strony potwierdzone w dostępnych rekordach bibliograficznych. **Pełny tekst/abstrakt oryginału nie zostały odczytane.** To istotna pozostała luka domenowa. |
| R14 | *Forecasting hotel daily room demand with transformed data using time series methods* (2023), JRPM22,44–56, [DOI](https://doi.org/10.1057/s41272-021-00363-6) | Kopia metadanych i abstraktu wydawcy/Scopus w publicznym zbiorze, nie pełny tekst. Wynik pojedynczego hotelu nie jest dowodem transferu. |
| R15 | *Hotel daily demand forecasting for high-frequency and complex seasonality data: a case study in Thailand* (2020), JRPM19,8–25, [DOI](https://doi.org/10.1057/s41272-019-00221-6) | Kopia metadanych i abstraktu. Inny zwycięzca niżR14w innym zadaniu/danych; nie używamy tych abstraktów do wyboru modelu Beyond. |

## 11. Granice weryfikacji i zachowanie dowodów

Bezpośrednie żądania do Crossref, DOI, OTexts, arXiv i OpenReview były blokowane przez proxyHTTP403, także po przyznaniu dostępu sieciowego i próbie poza sandboxem. Weryfikację wykonano na dostępnych przez GitHub API materiałach autorów, przewodniku organizatorów, zapisanych kopiach oryginalnychPDF i jawnie wskazanych kopiach abstraktów/metadanych. Nie deklarujemy, że niedostępne teksty zostały przeczytane.

W szczególności **domenowy przegląd booking curves nie jest pełnotekstowo zamknięty**: R12/R13 pozostają bibliografią do uzupełnienia. Propozycja warunkowej krzywej jest prostą, testowalną hipotezą Beyond, a nie udowodnioną lokalnie reprodukcją tych prac. Przegląd uzasadnia metodologię, kontrakty i rozdzielenie zadań; nie potwierdza konkretnej recepty lub docelowego MAE.

Prywatne materiały i rachunki dostępu: `/workspace/ops-runtime/2026-11-08-rolling72-literature/`. Zapisano URL, repo/path, identyfikatory blobów, rozmiary i SHA256 dostępnych plików. Git zawiera raport i rejestr bibliografii, nie kopie pełnych cudzych publikacji. Pierwszy pusty odczyt dużego plikuM5przez Contents API zastąpiono odczytem pełnego bloba i kontrolą rozmiaru; nie potraktowano pustego pliku jako przeczytanej pracy.

Żaden wynik bibliograficzny nie aktywuje modelu. Dotychczasowe frozen lanes, parametry, obserwacje, bramki i defaults `production_change=false`, `live_adjustment=0` pozostają bez zmian.
