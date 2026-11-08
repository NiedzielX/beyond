# MVP: 48–72 godziny przewagi dla klubu

Status: zaakceptowany kierunek produktu przez użytkownika, implementacja i dowód skuteczności pozostają otwarte. Data: 2026-11-08. Specyfikacja uzupełnia kanoniczny MAE_RESEARCH_ROADMAP_V6 i plan trajectory; nie zmienia zamrożonych eksperymentów ani ich bramek.

## Cel i moment rozpoczęcia

Od pierwszego rzeczywistego, poprawnego odczytu meczu Beyond ma prognozować dalszy przebieg zainteresowania. Dotyczy to także wczesnego śledzenia P-50/P-49 itd., a nie wyłącznie P-15 lub ostatnich24godzin. Każda aktualizacja używa całej historii dostępnej w chwili wydania. Nie odtwarzamy prognoz dla dawnych przegapionych okien ani historii nieznanej wówczas modelowi.

Główna wartość dla klubu: dziś przewidzieć poziom i tempo zmian za24/48/72godziny, żeby mieć48–72godziny na decyzję o cenie, promocji lub sektorze. Prognoza końcowej frekwencji jest dodatkowym wynikiem; sama liczba końcowa ani jej historia na wykresie nie realizują tego wymagania. Szersza dzienna ścieżka pozostaje celem projektu, a najbliższe72godziny są priorytetem operacyjnym MVP.

## Horyzonty obejmują całą obserwowaną sprzedaż

Pierwszy rzeczywisty odczyt po uruchomieniu sprzedaży uruchamia nową ścieżkę prognoz+24/+48/+72h, nawet przy jednym punkcie. Przy każdej kolejnej aktualizacji te horyzonty przesuwają się do przodu od nowego rzeczywistego czasu wydania. P-50→P-49/P-48/P-47 i P-15→P-14/P-13/P-12 to przykłady tej samej logiki przez cały okres sprzedaży, nie oddzielne modele dla końcówki meczu. Luki przed pierwszym pomiarem pozostają lukami; starych prognoz i frozen gates nie uzupełniamy ani nie zmieniamy.

## Logika prognozy

1. Zapisujemy prawdziwy odczyt i jego czas dostępności, źródło, zakres puli/sektorów oraz dostępne informacje o cenie/promocji. Brak informacji pozostaje brakiem.
2. Budujemy historię wyłącznie do bieżącego momentu: poziom, rzeczywiste zmiany, tempo, przyspieszenie, odstępy i jakość obserwacji oraz etap do meczu. Gdy historia jest krótka, stosujemy jawnie oznaczoną wersję początkową i stan niepewności; nie fabrykujemy wcześniejszych zmian.
3. Dla tej samej mierzonej wielkości przyszły poziom = ostatni rzeczywisty poziom + prognozowana zmiana. Ścieżka zaczyna się przy ostatniej obserwacji. Poziom końcowej frekwencji ma osobną definicję i ewentualną kalibrację.
4. Wydajemy osobne przewidywania za24/48/72godziny oraz, gdy wspierane, pozostałą dzienną ścieżkę do kickoffu. Nie generujemy pozornych punktów inventory po zakończeniu meczu.
5. Nowy rzeczywisty odczyt powoduje nowe przeliczenie pozostałej przyszłości. Poprzednia wersja zostaje niezmienna, z faktycznym czasem wydania i identyfikatorami wejść/modelu.

Przy takim samym dzisiejszym poziomie różne rzeczywiste przebiegi powinny móc dawać różne prognozy dalszych zmian. Przed zamrożeniem sprawdzamy faktyczną zależność modelu od tych danych, a nie samą obecność kolumn w wejściu. Degenerację dokumentujemy; nie dopasowujemy współczynników tylko dla wyglądu wykresu. Nie wymuszamy ruchu prognozy, jeśli nowe obserwacje nie zmieniają oczekiwania.

## Scenariusz bez interwencji

Komunikat produktu dotyczy utrzymania bieżącej ceny, promocji i zasad udostępniania puli. To jawne założenie scenariusza, nie gwarancja ani dowód przyczynowego wpływu ceny. Jeśli ceny/promocje/blokady nie są obserwowane, ich stabilność ma statusUNKNOWN; nie twierdzimy, że potrafimy ją zweryfikować lub oszacować efekt planowanej interwencji.

Zmianę ceny, promocji, zwolnienie puli lub zmianę pokrycia źródła zapisujemy, jeśli mamy rzeczywisty dowód. Wyznaczamy wtedy nową prognozę na nowych warunkach. Pierwotny scenariusz i jego rzeczywisty wynik pozostają w pamięci; nie usuwamy trudnych przypadków z metryk po wyniku. Efekt alternatywnej ceny/promocji wymaga osobnego, uzasadnionego modelu interwencji i danych; nie jest ukrytą obietnicą pierwszego MVP.

Na obecnych danych bez partnerów mierzalnym targetem jest publiczna dostępność i porównywalne zmiany widocznej puli. To nie jest potwierdzona płatna sprzedaż. Prognozy per sektor wymagają rzeczywistej, porównywalnej historii sektora; brak takiego pokrycia nie może być udawany agregatem. Przedziały prawdopodobieństwa wymagają osobnej kalibracji; nie podajemy wymyślonych poziomów pewności.

## Ocena i definicja ukończenia

- Ten sam rzeczywisty prefix i te same przyszłe cele dla modelu, persistence i zamrożonego driftu, z jawnym przecięciem pokrycia. Istniejący drift wymaga24godzin historii; jego brak na pierwszym odczycie nie oznacza wyłączenia nowego produktu ani uzupełnienia starego eksperymentu.
- MAE dla+24/+48/+72godzin oddzielnie; najpierw średnia w obrębie meczu, potem między niezależnymi meczami. Bias, błędy skrajne, pokrycie, kluby, niedostępne/krótkie historie i zmiany scenariusza pozostają widoczne. Dzienne punkty nie zwiększają liczby niezależnych meczów.
- Prognoza jest utrwalona przed rzeczywistym przyszłym odczytem. Uczciwy podział po meczach i czasie, cechy PIT-safe. Przed dopasowaniem nowej wersji zapisujemy dokładną hipotezę, cechy, parametry, trening, cutoffy i kryteria przeglądu; nowe imię wersji nie czyni odsłoniętych meczów świeżym testem.
- Panel musi pokazywać rzeczywisty prefix i rzeczywiste przyszłe punkty z wydanej wersji. Sam wykres historii końcowej frekwencji nie przechodzi tego kryterium. Nie przedłużamy linii sztucznie, nie podstawiamy końcowego wyniku, nie przeliczamy dawnych prognoz po wyniku.
- DONE wymaga pełnego przyszłego łańcucha: rzeczywisty odczyt → zapisana prognoza → panel z tą samą wersją → późniejszy rzeczywisty odczyt → ocena+24/+48/+72. Konfiguracja, przerysowany wykres i lokalny test nie są tym dowodem.

Nie uznajemy celu za osiągnięty na podstawie samego C1final24 lub jego MAE. Nie zmieniamy zamrożonego dailyv1, driftu, C1, P9 ani ich starych obserwacji/bramek. Utrzymujemyproduction_change=false/live_adjustment=0.

## Plan wykonania

Użytkownik zlecił sformułowanie tezy i zapis pełnego planu. Kanoniczne rozwinięcie: ml/ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1.md. EtapyA–Fobejmują audyt danych, feature store i baseline, jeden nowy precommitted model zmiany, rzeczywistą publikację do panelu, późniejsze cele24/48/72h i przegląd nowej próby. Hipoteza pozostaje niepotwierdzona; zapisanie planu nie jest ukończeniem MVPani aktywacją modelu.

## Doprecyzowanie użytkownika: minimalne MAE i cel około 1200 miejsc

Plan 48–72 h ma dalej minimalizować rzeczywiste przyszłe MAE; nadal dążymy do około 1200 miejsc MAE końcowej frekwencji. Cel jest kamieniem milowym, a niższe MAE jest pożądane. Nowe metryki24/48/72h mierzymy osobno dla ich targetu, porównując ten sam prefix, zegar i przyszły odczyt; nie zastępują one dowodu dokładności frekwencji. Ładna/dynamiczna ścieżka ani działający pipeline nie wystarczają. Żadnej zmiany frozen modeli, progów lub starych wyników przez to doprecyzowanie.
