# Rolling72 — działająca ścieżka od pierwszego punktu

24 listopada zakończono wdrożenie nowego strumienia źródeł oraz generatora
PERS dla Jagiellonii–Radomiaka. [PR229](https://github.com/NiedzielX/beyond/pull/229)
zawiera źródła; [PR230](https://github.com/NiedzielX/beyond/pull/230) dodaje
prognozy, późniejsze oceny i osobny harmonogram. PR230 zależy od PR229.

Normalny kolektor zapisał snapshot48698 o15:05:04.618UTC. Zadanie źródłowe
zatwierdziło jego pierwszy seal o15:09:00.332706UTC. Osobne zadanie wystawiło
pakiet1 o15:10:00.174414UTC, po zakończeniu odczytu i obliczenia wartości.
Nie wywoływano ręcznie kolektora, capture ani issuance. Nie importowano1113
starych punktów bufora i nie rekonstruowano prognozy wstecz.

| Horyzont | Cel w Europe/Warsaw | Prognozowana dostępność PERS |
|---|---|---:|
| +24 h | 25 listopada,16:10 | 6707 |
| +48 h | 26 listopada,16:10 | 6707 |
| +72 h | 27 listopada,16:10 | 6707 |

PERS utrzymuje ostatnią zaobserwowaną wartość; działa także bez wcześniejszej
historii i dla prawdziwego zera. Każda kolejna nowa obserwacja może tworzyć
nowe wydanie. Cel po kickoffie jest osobno oznaczany jako poza zakresem,
bez blokowania krótszych horyzontów. To dostępność, nie sprzedaż lub frekwencja.

Scorer zachowuje pierwszą zaakceptowaną etykietę, odmawia cofania się do
starszego odczytu za nowszym błędnym źródłem i liczy event-balanced MAE
osobno dla24/48/72. Nowa lane ma obecnie **zero etykiet i nieznane MAE**.
Nie dowodzi poprawy jakości ani realizacji celu1200miejsc frekwencji.

Dziesięć testów PostgreSQL16 przeszło u autora i ponownie na dokładnych
plikach wydania (2,480s). Niezależny przegląd PASS. CI45421353629 przeszło
dla kodu296bd74. Siedem wdrożonych funkcji ma identyczne treści jak testowane;
47wcześniejszych funkcji pozostało bez zmian. Weryfikacja hosted potwierdziła
RLS oraz dostęp do RPC wyłącznie dla roli serwisowej. Nowe zadanie44 zachowało
wszystkie37wcześniejszych zadań; testy jego guardów i niezależny review PASS.

Pilot w lokalnej przeglądarce połączył się przez rzeczywisty relay, Edge i SQL.
Automatyczny polling pobrał nowszy receipt2649→2651 i wydanie334→336, bez
ręcznego odświeżania, podmiany zegara i błędów JavaScript. Włączenie proxy
dotyczyło lokalnego procesu Node. Nie potwierdzono publicznego dostępu do
chronionego wdrożenia Vercel ani prezentacji nowej lane PERS w tym pilocie.

Dowody: [pierwszy punkt i prognozy](ROLLING_72H_JAGIELLONIA_FRESH_SOURCE_PROOF_2026-11-24.json),
[wdrożenie PERS](ROLLING_72H_MVP_PERSISTENCE_PROOF_2026-11-24.json),
[odczyt przeglądarki](ROLLING_72H_PROTECTED_PILOT_BROWSER_PROOF_2026-11-24.json),
[automatyczny polling](ROLLING_72H_PROTECTED_PILOT_AUTOMATIC_PROOF_2026-11-24.json).

Równoległy odczyt zamrożonego E5:141ocen+24h z2meczów; MAE PERS139,55,
drift690,87, drift2475,95, common_flow6194,23. To mała ujawniona kohorta
availability; nie dostrajano modeli. [Pełny snapshot](ROLLING_72H_E5_SCORE_SNAPSHOT_2026-11-24.md).

Następny development: chroniony feed i panel dla nowej lane PERS oraz nowych
fixture; potem porównania przyszłych metod na wspólnych współrzędnych.
Pierwsze E5+48 pozostaje dzisiaj około17:15Warszawa, pierwsze nowe PERS+24
jutro około16:10. Nie czekamy na te etykiety z implementacją feedu.
