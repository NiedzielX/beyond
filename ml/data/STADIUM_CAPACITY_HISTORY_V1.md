# Stadium Capacity History v1

Last verified: **2026-10-14**

Purpose: point-in-time stadium capacity input for the historical occupancy challenger.

## Source policy

Use season-specific Ekstraklasa stadium/location tables as the primary capacity reference. Preserve explicit mid-season venue switches instead of assigning one modern capacity to every historical match.

Primary season references:

- 2021/22: https://en.wikipedia.org/wiki/2021%E2%80%9322_Ekstraklasa
- 2022/23: https://en.wikipedia.org/wiki/2022%E2%80%9323_Ekstraklasa
- 2023/24: https://en.wikipedia.org/wiki/2023%E2%80%9324_Ekstraklasa
- 2024/25: https://en.wikipedia.org/wiki/2024%E2%80%9325_Ekstraklasa
- 2025/26: https://en.wikipedia.org/wiki/2025%E2%80%9326_Ekstraklasa

Additional switch-date references:

- Puszcza Niepołomice returned to Niepołomice on 2025-03-02: https://en.wikipedia.org/wiki/Puszcza_Niepo%C5%82omice
- Arena Katowice opened for GKS on 2025-03-30: https://en.wikipedia.org/wiki/Arena_Katowice

## Explicit mid-season venue rules

### 2023/24 — Ruch Chorzów

- rounds 1–12: Piast Gliwice stadium, capacity **10,037**;
- from round 13: Stadion Śląski, capacity **55,211**.

### 2024/25 — GKS Katowice

- before 2025-03-30: old GKS stadium, capacity **6,710**;
- from 2025-03-30: Arena Katowice, capacity **15,048**.

### 2024/25 — Puszcza Niepołomice

- before 2025-03-02: Cracovia stadium, capacity **15,016**;
- from 2025-03-02: Municipal Stadium in Niepołomice, capacity **2,000**.

## Season capacity map used by v2.2

### 2021/22

- Bruk-Bet Termalica: 4,666
- Cracovia: 15,114
- Górnik Łęczna: 7,464
- Górnik Zabrze: 24,563
- Jagiellonia: 22,432
- Lech: 43,269
- Lechia Gdańsk: 43,615
- Legia: 31,800
- Piast: 10,037
- Pogoń: 9,300
- Radomiak: 4,501
- Raków: 5,500
- Stal Mielec: 6,864
- Śląsk: 45,105
- Warta: 5,383
- Wisła Kraków: 33,326
- Wisła Płock: 3,500
- Zagłębie Lubin: 16,068

### 2022/23

- Cracovia: 15,114
- Górnik Zabrze: 24,563
- Jagiellonia: 22,432
- Korona: 15,550
- Lech: 43,269
- Lechia Gdańsk: 43,615
- Legia: 31,800
- Miedź Legnica: 6,864
- Piast: 10,037
- Pogoń: 21,163
- Radomiak: 4,501
- Raków: 5,500
- Stal Mielec: 6,864
- Śląsk: 45,105
- Warta: 5,383
- Widzew: 18,018
- Wisła Płock: 4,300
- Zagłębie Lubin: 16,068

### 2023/24

- Cracovia: 15,114
- Górnik Zabrze: 24,563
- Jagiellonia: 22,432
- Korona: 15,550
- Lech: 43,269
- Legia: 31,800
- ŁKS: 18,029
- Piast: 10,037
- Pogoń: 21,163
- Puszcza: 15,114
- Radomiak: 8,840
- Raków: 5,500
- Stal Mielec: 6,864
- Śląsk: 45,105
- Warta: 5,383
- Widzew: 18,018
- Zagłębie Lubin: 16,068
- Ruch: see explicit venue switch rule above

### 2024/25

- Cracovia: 15,016
- Górnik Zabrze: 24,563
- Jagiellonia: 22,372
- Korona: 15,700
- Lech: 42,837
- Lechia Gdańsk: 41,620
- Legia: 31,006
- Motor Lublin: 15,247
- Piast: 9,913
- Pogoń: 21,163
- Radomiak: 8,840
- Raków: 5,500
- Stal Mielec: 7,000
- Śląsk: 42,771
- Widzew: 18,018
- Zagłębie Lubin: 16,086
- GKS Katowice: see explicit venue switch rule above
- Puszcza: see explicit venue switch rule above

### 2025/26

- Arka Gdynia: 15,139
- Bruk-Bet Termalica: 4,666
- Cracovia: 15,016
- GKS Katowice: 15,048
- Górnik Zabrze: 28,236
- Jagiellonia: 22,372
- Korona: 15,700
- Lech: 42,837
- Lechia Gdańsk: 41,620
- Legia: 31,006
- Motor Lublin: 15,247
- Piast: 9,913
- Pogoń: 21,163
- Radomiak: 14,440
- Raków: 5,500
- Widzew: 18,018
- Wisła Płock: 15,004
- Zagłębie Lubin: 16,086

## Quality note

This v1 layer is appropriate for historical challenger evaluation, but venue capacity remains a versioned feature. Future revisions should preserve source/version lineage and any additional intra-season construction changes rather than silently overwriting historical values.
