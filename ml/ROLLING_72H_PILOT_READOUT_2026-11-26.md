# Beyond, odczyt pilotażu 26 listopada 2026

W E5 MAE prognozy publicznej dostępności spadł względem PERS o około 58%,
48% i 31% dla +24, +48 i +72 godzin. Odczyt o 11:40 czasu Warszawy obejmował
odpowiednio 490, 300 i 127 ocen na dwóch meczach. Każdy mecz ma równą wagę.
Dla +72 h Śląsk–GKS przeszedł z około 1085 do 745 miejsc błędu,
a Wisła–Motor utrzymała około 9 miejsc. Przewaga wynika z jednego meczu.
[Odczyt E5](ROLLING_72H_E5_SNAPSHOT_2026-11-26.json)

Okno 48–72 h odpowiada realnej pracy klubów. Badanie FC Barcelony wykorzystywało
sprzedaż, karnety i wejścia na stadion z 99 meczów. Two Circles opisuje
prognozowanie popytu na podstawie wieloletnich danych o biletach z rynku
pierwotnego i wtórnego. Te przykłady pokazują użycie biznesowe i przewagę
danych klubowych. Nie podają porównywalnego MAE dla publicznej puli miejsc.
[FC Barcelona](https://doi.org/10.1007/s10994-023-06499-3)
[Two Circles](https://twocircles.com/us/articles/forecasting-attendances-to-drive-better-ticket-sales-and-marketing-strategies/)

1. Raportuj PERS–drift24 osobno na każdym horyzoncie, wraz z pokryciem,
   błędami poszczególnych meczów, zmianami puli i udziałem powrotów do PERS.
   Do oceny przewagi użyj ustalonej reguły dla +72 h: co najmniej 30 nowych
   meczów z 8 klubów, co najmniej 10% niższy MAE i ujemny cały 95% przedział
   różnicy. MAE +24/+48 nie może wzrosnąć.
2. W kolejnym osobnym eksperymencie porównaj jeden prosty wariant, np.
   tłumiony trend lub historyczną zmianę dostępną dla etapu sprzedaży.
   Wybierz mechanizm na podstawie rozkładu błędów i oceń go w nowej kohorcie.
3. Do pilotażu klubowego przygotuj import agregatów sprzedaży netto, zwrotów,
   zmian puli, karnetów i skanów wejść. Na tej podstawie mierz osobno
   prognozy sprzedaży i końcowej frekwencji. Pozwoli to ocenić cel około
   1200 miejsc MAE dla frekwencji i odróżniać sprzedaż od otwarcia sektora.
4. Panel powinien podać zakres prognozy, świeżość danych i powód alertu.
   W pilotażu zapisuj decyzje klubu i wyprzedzenie alertów. Skuteczność
   ceny, promocji lub reklamy badaj osobno na zaplanowanej próbie kontrolnej.

## Odczyt po uruchomieniu

O 12:00 czasu Warszawy raport wykazał jedną parę na każdym horyzoncie.
Wszystkie trzy pary użyły PERS z powodu zmiany zestawu sektorów.
Zera dojrzałych celów dają pustą metrykę pokrycia i brak MAE.
[Zapytanie diagnostyczne](../supabase/ops/rolling72_mvp_paired_drift24_v1_support_report.sql)
· [Odczyt Supabase](ROLLING_72H_PAIRED_SUPPORT_2026-11-26.json)

Weryfikacja kandydatów w bazie zwróciła `discovered` dla Raków–Piast,
Górnik–Wisła Płock i Cracovia–Widzew, bez wpisu meczu,
zweryfikowanego terminarza w bazie lub wpisu dopuszczenia. Liga potwierdza
27 listopada o 18:00 i 20:30 dla dwóch pierwszych spotkań.
Od obecnego odczytu mogą wnieść co najwyżej +24 h przed rozpoczęciem.
Klub potwierdza 5 grudnia o 14:45 dla Cracovia–Widzew. Ten mecz jest
pierwszym z tej listy z zapasem na pełne trzy horyzonty. Kolejny krok
to powiązanie terminu z konkretną ofertą Roboticket i sprawdzenie puli.
Obecne okno wydań wygasa 1 grudnia o 01:00, a ocen 4 grudnia o 07:00 czasu
Warszawy. Dłuższy pilotaż wymaga oddzielnego planu okna.
[Ekstraklasa](https://ekstraklasa.org/aktualnosci/terminarz-16-kolejki-202627/)
· [Cracovia](https://www.cracovia.pl/posts/poznalismy-date-meczu-z-widzewem-lodz/6519)

[Kontrakt agregatów klubowych i rejestru decyzji](ROLLING_72H_CLUB_PILOT_DATA_V1.md)
jest gotowy do uzgodnienia ze źródłem danych klubu.

Późniejszy odczyt strony biletu powiązał ofertę Roboticket 10896 z Cracovia–Widzew
Łódź, 5 grudnia 2026 o 14:45. Nagłówek strony odpowiada komunikatowi klubu.
Zapisaliśmy SHA-256 odpowiedzi strony biletu
`18259a174b608b32ad270e90169b4418bee4c99fd3e29e53b052ce755c0d2a55`.
Odczyt puli i dopuszczenie kolejnego meczu nadal czekają na weryfikację.
[Roboticket](https://bilety.cracovia.pl/Stadium/Index?eventId=10896)
