# Beyond: plan dojścia do 48–72 godzin przewagi dla klubu

Data: **2026-11-08**. Status: **plan produktu i badań; skuteczność tezy pozostaje do sprawdzenia**.

Cel wynika z bezpośredniej instrukcji użytkownika. Ten dokument rozwija kanoniczny `MAE_RESEARCH_ROADMAP_V6.md` i plan trajectory. Specyfikacja produktu: [rolling72 MVP](../.ai/specs/2026-11-08-rolling-72h-commercial-forecast-mvp.md). Wdrożenia, bieżące liczniki i blokady pozostają w `EXECUTION_PLAN_CURRENT.md` i `NEXT_SESSION_HANDOFF.md`. Nie zmieniamy zamrożonych modeli ani ich wcześniejszych protokołów.

## Weryfikacja bibliograficzna przed wykonaniem

[Przegląd źródeł z 8 listopada](ROLLING_72H_LITERATURE_REVIEW_2026-11-08.md) wspiera konstrukcję rolling origin, prognozy bezpośrednie na różne horyzonty, zgodność P50–MAE i silne proste benchmarki. Nie potwierdza, że konkretny algorytm osiągnie 1200 miejsc. Jawnie rozróżnia pobrane teksty, materiały autorów i metadane; pełne teksty dwóch klasycznych prac booking curves pozostają niedostępne. Poniższy plan jest doprecyzowany tym przeglądem, bez fitu lub aktywacji.

Korekty: dodać warunkową krzywą/pickup jako punkt odniesienia; audytować sektory od początku; oceniać użyteczność ostrzeżeń oprócz MAE; osobno udowodnić efekt ceny/reklamy na przychód. Ścieżka ma opisywać przyszłe zapełnianie/popyt, a końcowa frekwencja pozostaje powiązanym, oddzielnie ocenianym wynikiem. Obecny publiczny proxy musi mieć uczciwą definicję.

## 1. Teza

**Rzeczywisty przebieg zainteresowania meczem — jego poziom, tempo, przyspieszenie i etap do kickoffu — zawiera informację pozwalającą lepiej przewidywać zmiany w najbliższych 48–72 godzinach niż samo utrzymanie ostatniego odczytu lub proste przedłużenie ostatniego trendu. Wykorzystanie tej informacji może dać klubowi czas na reakcję handlową.**

To hipoteza do falsyfikacji, a nie stwierdzenie już potwierdzonej dokładności. Sprawdzamy osobno:

- **tezę prognostyczną:** czy model zmniejsza błędy przyszłych odczytów +24/+48/+72 h na tych samych nowych meczach i momentach;
- **tezę produktową:** czy klub dostaje prognozę odpowiednio wcześnie i w formie pozwalającej podjąć decyzję;
- **założenie scenariusza:** przewidywanie dotyczy kontynuacji przy bieżącej cenie, promocji i zasadach udostępniania puli. Efekt zmiany tych warunków nie jest automatycznie efektem przyczynowym wyznaczonym przez ten model.

### Stały cel dokładności: jak najniższe MAE, nadal około 1200 miejsc

**Cel 48–72 godzin przewagi uzupełnia dotychczasowy cel dokładności: minimalizujemy rzeczywiste przyszłe MAE i nadal dążymy do około 1200 miejsc błędu prognozy końcowej frekwencji.** To kamień milowy badawczy, nie obietnica ani granica, poniżej której przestajemy poprawiać wynik. Samo działanie ścieżki, jej zmienność lub dostępność w panelu nie wystarcza do uznania modelu za dobry.

Równolegle minimalizujemy MAE przyszłego przebiegu dla +24/+48/+72 h i weryfikujemy przewagę wobec silnych prostych benchmarków. Te miary raportujemy osobno: niski błąd dostępności za 72 h nie dowodzi osiągnięcia około 1200 miejsc MAE końcowej frekwencji. W każdym raporcie podajemy target, horyzont, niezależne mecze, pokrycie i model. Celem jest lepsza dokładność na przyszłych meczach, bez wybierania korzystnych przykładów, zegarów lub wariantów po wyniku. Dotychczasowe frozen gates pozostają bez zmian.

## 2. Co dokładnie ma otrzymać klub

Od pierwszego rzeczywistego, poprawnego odczytu meczu — także P-50, jeśli wtedy zaczęliśmy śledzenie — klub otrzymuje przewidywany dalszy przebieg. W każdej aktualizacji widzi:

1. Rzeczywisty przebieg znany do chwili wydania prognozy i datę ostatniego odczytu.
2. Przewidywany poziom oraz zmianę za 24, 48 i 72 godziny; w dalszym rozwoju także całą pozostałą ścieżkę dzienną do meczu.
3. Przewidywane przyspieszenie, wyhamowanie lub ryzyko odchylenia od celu klubu, jeżeli cel został wcześniej zapisany.
4. Jakość pokrycia i niepewność; liczbowy przedział prawdopodobieństwa dopiero po jego kalibracji.
5. Wersję prognozy i założenia dotyczące warunków. Po nowych odczytach dostaje nową wersję, a poprzednia pozostaje dostępna do oceny.

Gdy do meczu pozostało mniej niż 72 godziny, nie tworzymy pozornych odczytów inventory po jego zakończeniu. Prognozujemy pozostały sensowny okres, a końcową frekwencję oceniamy jako osobny target.

**Kluczowa zmiana celu:** przewidywać to, co ma się wydarzyć w kolejnych dniach, zanim klub to zaobserwuje. Historia prognoz końcowej frekwencji sama nie realizuje tej funkcji.

### Ruchome horyzonty przez cały okres sprzedaży

**+24/+48/+72 h liczymy od każdej bieżącej chwili wydania prognozy, przez cały okres obserwowanej sprzedaży.** Początek to pierwsza prawdziwa obserwacja po uruchomieniu sprzedaży, nawet jeśli jest to jedyny odczyt. Nie oznacza to, że produkt zaczyna działać dopiero72godziny przed kickoffem albo po zebraniu doby historii.

| Chwila aktualizacji — przykład | Cele tej wersji prognozy |
|---|---|
| P-50 | P-49 / P-48 / P-47 |
| P-30 | P-29 / P-28 / P-27 |
| P-15 | P-14 / P-13 / P-12 |
| P-4 | P-3 / P-2 / P-1 |

Przykłady pokazują horyzonty upływu24/48/72godzin; nie narzucają stałych dat startu lub wspólnej długości historii. Przy aktualizacji model zna wyłącznie obserwacje dostępne do tej chwili. Poprzednie prognozy zostają zachowane, a ich horyzonty nie przesuwają się po fakcie. Obsługa pierwszego odczytu jest osobną ścieżką nowej wersji, bez zmiany starych wymagań driftu/dailyv1.

Jeśli rozpoczęliśmy śledzenie później niż faktyczny start sprzedaży, zapisujemy tę lukę i zaczynamy od pierwszego realnie dostępnego pomiaru. Nie odtwarzamy brakującego początku jako prawdziwej historii ani dawnych prognoz jako prospective. Raportujemy pokrycie i błędy także według etapu sprzedaży, długości dostępnej historii i czasu do meczu.

## 3. Punkt wyjścia i konkretna luka

Zweryfikowany stan z 8 listopada, 12:28 UTC:

| Element | Co mamy | Czego to jeszcze nie dowodzi |
|---|---|---|
| Live C1 | MAE 3653,47 na 21 meczach; działa w ostatnich 24 h | Przewagi 48–72 h i prognoz od początku śledzenia |
| Median 26 shadow | MAE 1873,22 na 4 nowych meczach | Potwierdzonej przewagi lub dokładności modelu live |
| Daily path v1 | Rzeczywiste prefixy, zapisane przyszłe punkty, scoring | Zamierzonej wyuczonej dynamiki: audyt znalazł 120 zerowych współczynników wartości historii |
| Stały drift 24 h | Rzeczywista kotwica i zmiana z ostatniej doby; oddzielny frozen eksperyment | Działania przy pierwszym odczycie lub przewagi na szerokiej próbie |
| Wspólna ocena inventory | 16 celów/4 mecze: drift 13,29; persistence 175,29; daily 259,34 | Takiego samego błędu sprzedaży lub frekwencji; reprezentatywnej walidacji 72 h |
| Zielona linia w dotychczasowym wykresie | Historia `forecast_observations.final_p50` | Przyszłej ścieżki inventory albo wyników median 26 |

Istniejące modele i ich wyniki zachowujemy jako dowód. Nie poprawiamy dawnych prognoz ani nie wybieramy po wyniku ich najkorzystniejszego momentu. Osobny guardian częstszych aktualizacji C1 pozostaje nieukończonym, nieaktywnym zadaniem pomocniczym; częstotliwość uruchomień nie zastępuje logiki 72 h.

## 4. Jak ma działać model

### Jedna obserwowalna wielkość i prognoza dalszej zmiany

Na MVP używamy dostępnych danych publicznych o miejscach. Dla publicznej dostępności A:

`prognoza_A(t+h) = ostatni_rzeczywisty_odczyt_A(t) + model_zmiany(prefix_do_t, h)`

Model dostaje wyłącznie dane znane w chwili wydania. Horyzont jest wejściem; wyznacza bezpośrednie prognozy +24/+48/+72 h, bez traktowania własnych prognoz pośrednich jako rzeczywistych obserwacji. Dalsze punkty dzienne korzystają z tego samego kontraktu, jeżeli wspiera je zakres treningu.

Ścieżka tej samej wielkości zaczyna się od prawdziwego ostatniego odczytu. Płatnej sprzedaży i frekwencji nie utożsamiamy z dostępnością. Widoczne zajęcie można przedstawiać tylko przy spójnym, opisanym przeliczeniu puli. Frekwencja wymaga osobnego przełożenia i niezależnej oceny.

### Pierwszy odczyt i stopniowo rosnąca historia

Nie czekamy na P-15 ani ostatnich 24 h. Przy pierwszym odczycie znamy poziom i etap do meczu, ale jeszcze nie znamy lokalnego tempa. Nowa wersja ma obsługiwać taki początek, korzystając z informacji z wcześniejszych meczów i oznaczając krótką historię. Gdy tej informacji nie wystarcza, jawny wariant początkowy jest benchmarkiem o ograniczonej informacji, a nie rzekomą znajomością trendu.

Wraz z nowymi obserwacjami dokładamy rzeczywiste zmiany i tempo. Nie wypełniamy brakującej historii wymyślonymi odczytami. Nie obniżamy wymagań istniejącego driftu ani daily v1: nowy początek wymaga nowej wersji kontraktu.

### Minimalny pierwszy kandydat

Przed uczonym kandydatem dodajemy osobno precommitted warunkową krzywą/pickup: ostatni rzeczywisty poziom plus historyczna zmiana na porównywalnym etapie i horyzoncie, oparta wyłącznie na treningu. Dla krótkich historii współdzielimy informację między meczami i nie udajemy znanego lokalnego tempa. To hipoteza baseline Beyond, nie reprodukcja niedostępnej publikacji.

Jedna nowa wersja medianowej prognozy zmiany, z małym globalnym modelem drzewiastym kwantylowym, jest pierwszym uczonym kandydatem. Literatura uzasadnia jego porównanie, a nie zakładanie zwycięstwa. Ma ująć zależność tempa od etapu do meczu i nieliniowe wyhamowanie/przyspieszenie. Nie zaczynamy turnieju architektur. Dokładny zbiór cech, parametry i cutoff zostaną zapisane w precommicie **przed fit**.

Pierwsza rodzina informacji: ostatni poziom, obserwowana zmiana i dłuższy profil od początku dostępnego fragmentu, rzeczywiste zmiany i nachylenia dla dostępnych okien 6/24/72 h, porównanie krótszego i dłuższego tempa, czas do kickoffu i horyzont przewidywania. Brakujące okno pozostaje brakujące. Pokrycie, wiek, zmiany źródła i liczba odczytów są kontrolą jakości; liczba uruchomień collectora nie może udawać popytu. Ceny, promocje i kolejne rodziny informacji dodajemy tylko, gdy są rzeczywiście dostępne w czasie i wynika z nich oddzielna hipoteza.

Przed freeze sprawdzamy, czy model faktycznie używa zmian historii: przy tym samym ostatnim poziomie różne przebiegi mogą dać różne przyszłe wyniki. Taki test mechanizmu nie zastępuje oceny błędów. Jeśli model znów wyzeruje sygnał lub przegra z baseline, zapisujemy wynik zamiast ręcznie poprawiać krzywą.

## 5. Etapy wykonania i ich odbiór

| Etap | Konkretna praca | Warunek przejścia |
|---|---|---|
| A. Kontrakt i audyt danych | Jeden target, zakres puli/źródła, mapowanie i historia sektorów, prefixy od początku, cele +24/+48/+72; liczba niezależnych meczów, braki i pierwsze odczyty | Wiemy, które przykłady są poprawne i co oznacza ich pomiar; brak przecieku przyszłości |
| B. Feature store i benchmarki | Wersjonowane, odtwarzalne cechy znane w danej chwili; persistence, istniejący drift na jego prawidłowym pokryciu oraz osobna warunkowa krzywa/pickup | Ten sam issue i przyszły cel dla porównania; wartości i czasy dają się odtworzyć |
| C. Jedna nowa wersja modelu | Precommit, jeden zadeklarowany kandydat, walidacja po meczach i w czasie, audyt reakcji na historię | Uczciwy wynik wobec baseline, zapisane odrzucenia i brak retuningu na odsłoniętych testach |
| D. Przyszły przebieg i panel | Zapis przed targetem, rzeczywisty prefix oraz przyszłe punkty z tej samej wersji; aktualizacja i zachowanie vintages | Łańcuch rzeczywisty odczyt→prognoza→trwały zapis→panel działa; konfiguracja i test lokalny nie wystarczają |
| E. Ocena po 24/48/72 h | Dopiero później dopisujemy rzeczywisty wynik, błędy i raport horyzontów | Weryfikowalne pary prognoza–przyszły odczyt; żadnej prognozy stworzonej po wyniku |
| F. Przegląd i decyzja | Zamrożony raport na zadeklarowanej nowej próbie; MAE, bias, ogony, kluby, pokrycie i scenariusze | Potwierdzenie/odrzucenie hipotezy; osobny przegląd przed jakąkolwiek aktywacją produkcyjną |

Warstwa danych ma korzystać z przyrostowego odczytu i wspólnego kontraktu cech. Nie wracamy do wielokrotnego pobierania całej historii co kwadrans. Na początek wymagamy codziennych rzeczywistych aktualizacji; później zwiększamy częstotliwość tam, gdzie świeże dane i decyzje klubu to uzasadniają, bez zmiany tożsamości dawnych wydań.

**Aktualizacja wykonania8listopada:** [audyt A](ROLLING_72H_STAGE_A_RESULT_2026-11-08.md) ustalił pokrycie, a nowe moduły wejść/etykiet wdrożono w kodzie z testami. To historyczne capture-time support, bez dowodu dawnych knowledge clocks i bez nowego MAE. Receipt-bound adapter i lokalny immutablefeaturestore są też zaimplementowane: realny starycachepoprawnie dał zeroREADY/forecasts. Najbliżej jest **dokończenie B**: świeży ograniczony odczyt, dodatni przypadek źródło→store i benchmarki na tych samych issue/targetach. Następnie powstaje konkretny precommit etapu C; ten plan sam nie jest zgodą na dowolny fit lub tuning. Bieżące uprawnienia wdrożeniowe i blokady servingu sprawdzamy przed etapem D. Przygotowany kod/preview pozostaje oznaczony jako niewdrożony, dopóki nie ma dowodu rzeczywistego feedu.

## 6. Jak sprawdzamy tezę

Podstawowe porównanie: ten sam mecz, rzeczywisty czas wydania, prefix, miernik puli i przyszły target. Wszystkie prefixy meczu pozostają razem w podziale trening/test. Stare odsłonięte mecze służą development/diagnostyce, a nie nowej niezależnej walidacji.

Pokrycie i jakość sprawdzamy w macierzy **czas do meczu × horyzont prognozy**, z osobnym rozliczeniem długości historii i sektorów. P-50/+72h nie staje się zweryfikowane przez wynik P-10/+72h. Pierwszy odczyt nie jest dowodem daty otwarcia sprzedaży; luki wcześniejszego okresu zostają opisane.

Mierzymy osobno +24, +48, +72 h; **+72 h jest głównym horyzontem nowego celu produktu**. Najpierw uśredniamy błędy wewnątrz meczu, potem między meczami. Raport zawiera MAE, signed bias, P90/worst error, poprawę względem zarejestrowanych benchmarków, liczbę niezależnych meczów i klubów oraz braki. Wspólny wynik na dostępności nie zastępuje MAE frekwencji.

Przy rzadkich zmianach niski MAE może wynikać z trafnego przewidywania braku zmiany; nie wolno wymuszać dynamiki dla wyglądu. Równolegle oceniamy wcześniej zdefiniowane ostrzeżenia o przyspieszeniu/zastoju: precision/recall, fałszywe alarmy i rzeczywiste 48–72 h wyprzedzenia. Reguły powstają przed testem; nie usuwamy spokojnych/trudnych dni z głównego MAE. Oceniamy także etap sprzedaży, pierwsze odczyty i pokrycie sektorów.

Przy wynikach per sektor uwzględniamy, że mediana sumy nie musi być sumą median. Spójność agregacji projektujemy i sprawdzamy, a nie uznajemy za darmową poprawę MAE. Bez wiarygodnej historii sektora nie wydajemy pozornej prognozy dla niego. Predykcji niezaspokojonego popytu nie utożsamiamy z obserwacją zerowej dostępności.

Plan pierwszego przyszłego przeglądu nowej wersji: **30 nowych niezależnych meczów z co najmniej 8 klubów**, niezawartych w treningu. To zaplanowany próg nowego protokołu, nie zmiana istniejących frozen gates ani gwarancja mocy statystycznej. Włączamy wszystkie kwalifikujące się wyniki dostępne przy osiągnięciu progu; nie zatrzymujemy się na dogodnym MAE.

Przed pierwszym fit precommit utrwali: pierwotną metrykę 72 h, wszystkie punkty wejścia/targetu, reguły pokrycia, dokładne porównania i guardrails 48/24 h, bias i ogonów. Dowód przewagi wymaga niższego paired event-balanced MAE wobec persistence oraz driftu na jego wspólnym pokryciu, z 95% przedziałem różnicy wyznaczonym bootstrapem po meczach (10000 resampli, seed 42). Wczesne wyniki pozostają opisowe. Wyniki początkowych krótkich historii pokazujemy osobno, zachowując je także w ogólnym rozliczeniu produktu; nie usuwamy ich dla poprawy MAE.

Pierwsze nowe cele 72 h mogą dojrzeć dopiero 72 godziny po rzeczywistym wydaniu prognozy. Działającą demonstrację można uruchomić wcześniej, ale nie przedstawiać jej jako potwierdzonej przewagi modelu. Zebranie 30 meczów zależy od prawdziwego kalendarza i pokrycia; liczba odczytów nie skraca tego wymogu.

## 7. Cena, promocja i zmiana warunków

Pierwsza wersja działa na obecnych publicznych danych; brak transakcji partnerskich nie blokuje samego prognozowania. Ogranicza natomiast wnioski o rzeczywistej sprzedaży i przyczynach zmian.

Scenariusz produktu brzmi: „przy utrzymaniu obecnych warunków”. Jeśli nie obserwujemy cen/promocji/blokad, stabilność ma status UNKNOWN. Nie udajemy, że brak danych dowodzi braku interwencji. Gdy potwierdzona zmiana warunków nadejdzie, zapisujemy ją i wydajemy nową prognozę, zachowując pierwotną. Nie wykluczamy po wyniku trudnych przypadków ze wskaźników. Osobne przekroje „potwierdzony brak zmiany”, „zmiana”, „nieznane” są diagnostyką z uprzednio zdefiniowaną regułą, a nie sposobem wyboru dobrego wyniku.

Prognoza efektu alternatywnej ceny albo konkretnej promocji wymaga osobnego modelu i odpowiednich danych. Nie obiecujemy jej na podstawie samego modelu dalszego przebiegu.

Od początku przygotowujemy dziennik scenariusza, rekomendacji i rzeczywiście wykonanej interwencji: czas, sektor, cena/promocja, dostępny budżet i zakres puli. Początkowo może to być zapis ręczny; integracja partnera nie jest wymogiem demonstracji. Model może wskazywać ryzyko odchylenia sektora od planu; stwierdzenie, że konkretna reklama/cena zwiększy przychód, wymaga późniejszego badania efektu.

Poza etapami A–F jest osobny etap G: ocena działań cenowych/reklamowych na przyrostowym przychodzie lub marży, z uwzględnieniem kosztu reklamy i przenoszenia popytu między sektorami/w czasie. Potrzebna jest identyfikowalna zmienność działań lub odpowiednio zaprojektowany eksperyment. Nie maksymalizujemy przychodu przez podstawienie samej mediany zamiast wartości oczekiwanej/ryzyka ani nie deklarujemy optymalnej ceny na podstawie korelacji. To nie zmienia głównego celu najmniejszego MAE prognoz.

## 8. Definicja ukończenia MVP

MVP realizuje obietnicę funkcjonalną, gdy na rzeczywistym meczu:

- działa od pierwszej poprawnej obserwacji, ze zdefiniowaną obsługą krótkiej historii;
- wydaje i zapisuje przewidywania +24/+48/+72 h przed ich wynikami;
- panel pokazuje te same rzeczywiste obserwacje, czas wydania, przyszłe punkty i jakość danych;
- nowy odczyt aktualizuje dalszą przyszłość bez przepisywania poprzedniej wersji;
- późniejsze rzeczywiste odczyty tworzą ocenę dla każdego horyzontu;
- klub widzi oczekiwaną zmianę, założenia scenariusza i granice informacji, z czasem na decyzję.

**Potwierdzenie przewagi prognostycznej jest osobnym wynikiem etapu F.** Nie uznajemy go za osiągniętego przez wygląd wykresu, poprawne uruchomienie workflow, cztery mecze z niskim MAE albo samą końcową prognozę frekwencji. Cel około 1200 miejsc MAE końcowej frekwencji pozostaje obowiązującym celem badawczym; trafność ścieżki 24/48/72 h jest dodatkowo oceniana osobno i nie zastępuje tego wyniku.

Produkcyjne domyślne ustawienia pozostają `production_change=false`, `live_adjustment=0`. Ten zapis dokumentuje plan; nie aktywuje nowego modelu, nie zmienia starych prognoz i nie uruchamia procesu bezterminowego.
