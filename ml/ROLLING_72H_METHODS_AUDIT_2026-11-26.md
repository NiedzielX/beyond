# Audyt metod prognozowania Beyond

Przegląd niezależnego agenta i weryfikacja źródeł przez integratora, 26 listopada 2026.

| Element | Wniosek |
|---|---|
| PERS | Standardowy benchmark naiwny. Ostatnia dostępna obserwacja jest prognozą na każdy horyzont. Zachować jako stały punkt odniesienia. |
| Drift24 | Własny benchmark krótkiego trendu. Zwykły drift w podręczniku liczy średnią zmianę z całej historii. Krótkie okno może szybciej uchwycić zmianę tempa i mocniej przenieść jednorazowy skok na +72 h. |
| Zmiana puli | Powrót do PERS przy nieporównywalnych sektorach ma sens. Raportować cały wynik z powrotami i osobno ich udział. Wynik na stabilnej puli służy diagnostyce. |
| Ocena | Rolling origin, wspólne znaczniki czasu, wspólne etykiety i MAE ważone równo po meczu są odpowiednie. Przedział liczony przez losowanie całych meczów, nie punktów. Analiza po wyłączeniu jednego meczu i jednego klubu pokazuje koncentrację wyniku. |
| Próg 30/8 | To ustalony próg projektu, a nie norma branżowa. O wyniku decydują także 10% zysku, przedział i pozostałe horyzonty. |
| Model następny | Jeden wariant tłumionego trendu z tą samą dostępnością danych i tym samym powrotem do PERS. Oceniać również bezpośrednio względem drift24. Po wejściu danych klubowych rozważyć historyczny przyrost sprzedaży dla etapu cyklu. |

Najnowszy odczyt E5 z 26 listopada zawiera +72 h dla dwóch meczów. Poprawa
31% dotyczy publicznej dostępności, a jej całość pochodzi z jednego meczu.
Świeża seria i E5 mają osobne kohorty. Próg około 1200 MAE dotyczy
potwierdzonej końcowej frekwencji. [Odczyt pilotażu](ROLLING_72H_PILOT_READOUT_2026-11-26.md)

Bibliografia i zakres stosowania:

- Hyndman i Athanasopoulos, *Forecasting: Principles and Practice*, rozdziały
  o naiwnym benchmarku, drift i walidacji z przesuwającą się datą prognozy.
  [Proste metody](https://otexts.com/fpp3/simple-methods.html) · [Walidacja szeregów](https://otexts.com/fpp3/tscv.html)
- Tashman (2000), porównanie metod oceny poza próbą i rolling origin.
  [DOI](https://doi.org/10.1016/S0169-2070(00)00065-0)
- Gardner i McKenzie (1985), uzasadnienie tłumienia trendu wraz z horyzontem.
  Inspiracja mechanizmem, bez kalibracji konkretnego tłumienia dla Beyond.
  [DOI](https://doi.org/10.1287/mnsc.31.10.1237)
- Weatherford i Kimes (2003), porównanie pickup i wygładzania w zarządzaniu
  rezerwacjami hotelowymi. Uzasadnia przyszły benchmark dla obserwowanych
  rezerwacji/sprzedaży, bez przenoszenia rezultatu na mecze.
  [Cornell](https://ecommons.cornell.edu/entities/publication/046131d9-289a-4ee2-8249-23c59a5362f0)
- Conlon i Mortimer (2008), wpływ obserwowalności puli na estymację popytu
  przy ograniczonej podaży. Uzasadnia oddzielne źródła stanów i transakcji.
  [NBER](https://www.nber.org/papers/w14315)
- Badanie FC Barcelony uzasadnia praktyczne okno decyzji 48–72 h. Używa
  wewnętrznych danych o biletach, karnetach i wejściach, więc jego błędy
  nie stanowią porównania z E5. [DOI](https://doi.org/10.1007/s10994-023-06499-3)
