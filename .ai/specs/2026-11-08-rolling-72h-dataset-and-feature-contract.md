# Rolling72: audyt danych i odtwarzalny kontrakt cech v1

Data: 2026-11-08. Status: AUDIT_DELIVERED_AND_PURE_MODULES_TESTED; integracja źródeł/persistencjaB pozostają otwarte. Kierunek zatwierdzony przez użytkownika; prace agentów równoległe jawnie autoryzowane.

## Zakres

Rozwinięcie `ml/ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1.md` i przeglądu bibliograficznego. Audytujemy rzeczywiste zachowane eksporty, kontrakt danych i istniejący feed panelu. Tworzymy odrębny, wersjonowany kontrakt wejść rolling +24/+48/+72 h od pierwszej obserwacji; bez fitu, wyboru parametrów, aktywacji lub zmiany frozen v1.

## Wymagania audytu A

- Jawny hash i zegar użytego źródła; korzystamy z cache zamiast ponownego pełnego odczytu DB.
- Liczba niezależnych meczów/klubów, pierwsze odczyty i długość prefixu. Macierz czas do kickoffu × przyszły horyzont; osobno pokrycie pierwszego odczytu i sektorów.
- Publiczna dostępność miejsc pozostaje osobnym targetem od płatnej sprzedaży i frekwencji. Początek obserwacji nie jest dowodem startu sprzedaży.
- Brakujące/ukryte pomiary pozostają brakujące; literalne zero pozostaje odczytem. Brak źródłowego czasu dostępności nie może uzyskać statusu PIT_PROVEN wyłącznie z captured_at.
- Dotychczasowe źródła mogą dać historyczną diagnostykę, a nie nowe prospective wyniki ani odtworzone przegapione prognozy.
- Oddzielny audyt panelu rozróżnia gałąź badawczą, main, wdrożony feed i realny zapis.

## Kontrakt B przed kodem

Ewentualny nowy moduł musi być osobną wersją. Z góry: obsługa jednej prawdziwej obserwacji; dowolny świadomy czas issue; cały rzeczywiście wtedy znany prefix; horyzonty od czasu issue, nie od ostatniego odczytu; brak celów inventory o/po kickoffie. Potrzebne odrębne captured_at i known_at. Nie przypisujemy starym eksportom fikcyjnych historycznych known_at. Tożsamość pomiaru obejmuje jawny zakres puli/źródła. Zmiana zakresu lub stan inactive/hidden powoduje fail-closed, bez przeskakiwania do wcześniejszej wygodnej wartości.

Cechy: ostatni poziom, obserwowana zmiana od początku, wiek prefixu, staleness, czas do kickoffu, horyzont oraz rzeczywiste dostępne okna 6/24/72 h. Brak okna jest null z metadanymi, nie zerem. Liczniki pomiarów to jakość pokrycia, nie tempo sprzedaży. Brak fitu i empirycznego MAE.

Dokładny moduł wejść B: nowe pliki `ml/demand_engine/rolling72_features_v1.py` i testy. Wymaga jawnego czasu dostępności metadanych meczu oraz `captured_at`, `known_at>=captured_at` i tożsamości pomiaru każdego odczytu. Żaden adapter nie dopisuje tych zegarów do dawnych eksportów. Odczyty przyszłe/późno znane są odfiltrowywane przed walidacją ich wartości i hashowaniem. Niedostępne jeszcze metadane meczu nie pozwalają wydać READY. Jawne inactive/hidden, zmiana pomiaru i konflikty znanych tożsamości blokują wejście; brak flag to UNKNOWN, nie potwierdzona aktywność.

W tej nowej wersji maksymalny wiek ostatniego pomiaru to6h; nie jest to wymóg6h historii. Okna6/24/72h korzystają z ostatniego pomiaru oraz rzeczywistego odczytu na/przed granicą okna, maksymalnie6h wcześniejszego; tempo dzieli przez faktyczny czas między nimi. Brak pary to null, nie zero ani interpolacja. Cały dostępny prefix zostaje zachowany. Liczba odczytów jest metadanymi jakości, poza cechami popytu. Hashe wejść są sprawdzane przed przeliczeniem cech. Horyzonty liczymy od czasu issue, cele o/po kickoffie są niedostępne. Moduł nie zwraca etykiet, nie dopasowuje modelu i nie tworzy historycznych prognoz.

Oddzielny moduł `rolling72_labels_v1.py` dopasowuje etykiety dopiero po dojrzeniu targetu. Kontrakt przed kodem: latest rzeczywisty odczyt na/przed nominalnym issue+24/48/72h, maksymalnie6h wcześniejszy, capture ściśle po issue i przed kickoffem; known_at<=available_by. Późno znane dane nie wchodzą do wcześniejszego scoring/fit cutoff. Nie interpolujemy, nie używamy odczytu po target ani cofamy się do wygodnego starszego odczytu po nieprawidłowym najnowszym znanym. Jawne konflikty ID lub zmiana tożsamości pomiaru w znanym przyszłym odcinku blokują porównywalność, także gdy klucz wrócił do poprzedniej wartości; nie jest to selekcja po błędzie, tylko reguła kontraktu pomiaru zadeklarowana przed oceną. Nie dodajemy statusu interwencji cenowej bez danych. Wynik zachowuje capture/known_at, staleness, target i source lineage; target pending, niedostępny przed kickoffem, brakujący oraz nieporównywalny są osobnymi stanami. Ta funkcja tworzy odtwarzalne pary diagnostyczne, nie ledger prospective; dotychczasowe frozen etykiety i6h tolerancje nie zmieniają się. Żadnych przyszłych wartości w cechach. Uczony model i warunkowy pickup nadal wymagają dokładnego precommitu przed fit.

## Odbiór

Raport A z odtwarzalnymi agregatami i granicami dowodu; konkretne blokady i następny krok B/C/D. Dla nowego kodu testy przyczynowych granic: zmiana przyszłego payloadu nie wpływa na wejście; późno znany stary odczyt nie przecieka; pierwszy odczyt/P-50; horyzont od issue; zmiana zakresu/ukrycie; null/zero; spójność hashów. Aktualne canonical docs i log dostają wynik, a nie deklarację ukończenia całego MVP.

Production_change=false; live_adjustment=0. Żadnego DB write, re-fit, deploy, backfill, odnowienia wygasłych workerów ani automatycznego wyboru zwycięzcy.

## Wynik wykonania

Raport i agregaty: `ml/ROLLING_72H_STAGE_A_RESULT_2026-11-08.md`, `ml/ROLLING_72H_COVERAGE_AUDIT_2026-11-08.json`. Kod audytu odtworzył wszystkie pierwotne macierze z zachowanego eksportu. Wdrożono osobne moduły wejść/cech i etykiet, bez adaptera fikcyjnych historycznych zegarów.243testy lokalnePASS, w tym41nowychrolling72. SDD pozostaje aktywne: brak prawdziwego źródło→versionedfeaturestore połączenia, dopasowania kandydata, nowego ledgeru/feedu, deploy i prospectiveMAE. Nie ma podstaw do oznaczenia całegoB/MVPjakoDONE.

## Kolejny krok B: receipt-bound adapter i lokalny store (przed kodem)

Moduł `ml/rolling72_receipt_store_v1.py` przyjmuje wyłącznie oryginalny, zahashowany public-export-v1 z rzeczywistymi exported_at/retrieved_at. Cały odczyt jest konserwatywnie znany **najpóźniej w retrieved_at**, nie w każdym dawnym capture. Dokładna wersja metadanych meczu również jest znana dopiero z tego receipt. Nie pozwalamy budować issue przed retrieved_at ani wyprowadzać starej wiedzy z dzisiejszego eksportu. Clocks oznaczamy jawnie jako knowledge upper bound. Nie jest to adapter historycznego PIT ani dowód pierwotnego immutable raw. Nie certyfikuje stałej puli ani braku interwencji. Measurement scope to jawnie nazwana publiczna dostępność, nie potwierdzone zakupy.

Pure preparation nie tworzy forecastów. LokalnySQLite store zapisuje wyłącznie receipt lineage, immutableissues i wiersze cech24/48/72 wraz ze statusami. Brakujące/niedostępne horyzonty nie są zero. Idempotentne powtórzenie tych samych bajtów nie dopisuje wierszy. Konflikt tej samej pary event/issue jest błędem, nigdyUPDATE/REPLACE. CLI wystawia tylko actualwall-clockissue; nie ma opcji backdate i nie zapisuje predykcji/scorów. Jedna transakcja albo rollback. Odrębny plik pozaGit; nie otwieramy starych ledgerów. Oryginalny rawexport pozostaje prywatny, store zachowuje hash i jawne ograniczenia.

Testy: receiptcutoffprzedissue, brakujące/niepoprawne clocks, hash/sourcezmieniony, znany-po-receipt snapshot, jedenpunkt, źródłowyUNKNOWN/zero, późniejsza nowa wersja bez zmiany starej, idempotencja/konflikt/rollback, brak produkcyjnych/nietargetowychwrites. Na starym cache nie udajemy świeżej dodatniej prognozy; spodziewany fail-closedstale/pastkickoff zostaje odnotowany.

Receipt adapter/store również wykonane:13nowychtestówPASS, 256łącznie. Rzeczywisty CLI na starym cache utrwalił38failedissues/114statusrows i zeroforecastów w osobnymSQLite; integralnośćPASS. Odbiór świeżej dodatniej ścieżki i benchmarków nadal otwarty; spec pozostaje aktywne.

Po3małychGETSupabaseuzyskano rzeczywisty dodatni przypadek:14:14:57UTC2READYinputs→6feature rows→immutablelokalnystore, retry0insert,38wcześniejszychfailedinputs zachowanych, checkpoint/integrityPASS. Oryginalne rawreceipts pozaGit; source gaps jawne. Próg źródło→cechy→localstorejest dowiedziony; benchmarki/fit/persistedforecasts/panel/prospectiveMAEnadal otwarte. Spec pozostaje aktywne dla benchmarkówB.
