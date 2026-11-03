# MAE-01 incumbent error decomposition v1

Historical fixed-split replay of already exposed seasons; no new challenger, fresh holdout, prospective validation or MAE improvement claim.

Available cohort: **603 independent events / 3010 horizon rows**. Equal-event MAE **1773.89 people**, bias +14.59, median event AE 1129.28, P90 4195.79.

Common five-horizon cohort: 599 events; MAE 1784.64. Per-horizon comparisons below use these same events. No horizon is an additional independent event.

The baseline in the machine report is each frozen runtime's original PIT anchor (T-14 rolling-three mean; other horizons seasonal/history mean). It is not a newly selected challenger.

## Common-cohort horizon errors

| Horizon | Events | MAE | Signed bias |
|---|---:|---:|---:|
| T-30 | 599 | 1867.64 | +289.71 |
| T-14 | 599 | 1817.72 | -233.10 |
| T-7 | 599 | 1801.18 | +106.40 |
| T-3 | 599 | 1729.29 | -43.64 |
| T-1 | 599 | 1707.34 | -48.71 |

## horizon

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| T-30 | 599 | 119.80 | 1867.64 | +289.71 | 371.05 | 20.92% |
| T-14 | 602 | 120.55 | 1809.85 | -231.07 | 361.43 | 20.37% |
| T-7 | 603 | 120.88 | 1790.05 | +106.24 | 358.05 | 20.18% |
| T-3 | 603 | 120.88 | 1718.67 | -42.69 | 343.78 | 19.38% |
| T-1 | 603 | 120.88 | 1697.51 | -48.26 | 339.58 | 19.14% |

## home_club_key

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| lech | 34 | 34.00 | 5477.45 | -1002.61 | 308.84 | 17.41% |
| lechiagdansk | 34 | 34.00 | 3149.96 | -695.59 | 177.61 | 10.01% |
| gornikzabrze | 34 | 34.00 | 2660.65 | +150.24 | 150.02 | 8.46% |
| slask_wroclaw | 17 | 17.00 | 4841.01 | +424.35 | 136.48 | 7.69% |
| pogonszczecin | 34 | 34.00 | 1822.31 | +526.49 | 102.75 | 5.79% |
| legia | 34 | 34.00 | 1790.02 | +201.67 | 100.93 | 5.69% |
| zaglebie_lubin | 34 | 34.00 | 1683.62 | +227.83 | 94.93 | 5.35% |
| jagiellonia | 34 | 34.00 | 1536.90 | +475.49 | 86.66 | 4.89% |
| cracovia | 34 | 34.00 | 1480.34 | +227.94 | 83.47 | 4.71% |
| koronakielce | 34 | 34.00 | 1280.48 | +431.48 | 72.20 | 4.07% |
| radomiak_radom | 34 | 34.00 | 1266.27 | -627.14 | 71.40 | 4.02% |
| motorlublin | 31 | 31.00 | 1352.53 | +190.43 | 69.53 | 3.92% |
| gkskatowice | 31 | 31.00 | 1236.92 | -809.45 | 63.59 | 3.58% |
| piastgliwice | 34 | 34.00 | 1052.85 | +106.92 | 59.36 | 3.35% |
| wisla_plock | 17 | 17.00 | 1764.49 | -203.11 | 49.75 | 2.80% |
| arkagdynia | 14 | 14.00 | 1838.60 | +918.17 | 42.69 | 2.41% |
| widzewlodz | 34 | 34.00 | 662.16 | +135.98 | 37.34 | 2.10% |
| puszcza_niepolomice | 17 | 17.00 | 737.92 | +488.68 | 20.80 | 1.17% |
| termalica | 17 | 17.00 | 681.10 | -320.80 | 19.20 | 1.08% |
| stal_mielec | 17 | 17.00 | 647.79 | +302.41 | 18.26 | 1.03% |
| rakow | 34 | 34.00 | 143.25 | -59.38 | 8.08 | 0.46% |

## season

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| 2025/2026 | 303 | 303.00 | 1806.47 | -130.41 | 907.73 | 51.17% |
| 2024/2025 | 300 | 300.00 | 1740.98 | +161.04 | 866.16 | 48.83% |

## attendance_bucket

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| 10k-<20k | 264 | 264.00 | 1807.06 | +284.24 | 791.15 | 44.60% |
| 20k+ | 101 | 101.00 | 3369.65 | -1749.47 | 564.40 | 31.82% |
| 5k-<10k | 159 | 159.00 | 1040.89 | +298.66 | 274.46 | 15.47% |
| <5k | 79 | 79.00 | 1098.15 | +797.07 | 143.87 | 8.11% |

## actual_fill_bucket

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| normal:50-<85% | 268 | 268.00 | 1912.55 | +155.96 | 850.02 | 47.92% |
| low:<50% | 114 | 114.00 | 2268.49 | +1573.19 | 428.87 | 24.18% |
| near:85-<95% | 115 | 115.00 | 1614.44 | -996.17 | 307.89 | 17.36% |
| sellout-prone:95-100% | 99 | 99.00 | 1117.02 | -965.11 | 183.39 | 10.34% |
| above-capacity | 7 | 7.00 | 319.78 | -319.78 | 3.71 | 0.21% |

## baseline_fill_bucket

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| normal:50-<85% | 390 | 342.20 | 1939.12 | +142.39 | 1096.79 | 61.83% |
| low:<50% | 136 | 107.80 | 2734.14 | -906.19 | 463.63 | 26.14% |
| near:85-<95% | 138 | 81.20 | 1331.80 | +543.89 | 175.07 | 9.87% |
| sellout-prone:95-100% | 75 | 57.20 | 441.54 | +190.52 | 33.63 | 1.90% |
| above-capacity | 16 | 14.60 | 184.04 | -139.82 | 4.77 | 0.27% |

## week_part

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| weekend | 411 | 411.00 | 1884.51 | -115.76 | 1284.47 | 72.41% |
| weekday | 192 | 192.00 | 1537.08 | +293.62 | 489.42 | 27.59% |

## season_phase

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| mid | 198 | 198.00 | 1825.65 | +622.86 | 599.47 | 33.79% |
| early | 189 | 189.00 | 1889.51 | -341.59 | 592.23 | 33.39% |
| late | 216 | 216.00 | 1625.28 | -231.33 | 582.19 | 32.82% |

## opponent_draw_bucket

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| above:1.1+ | 391 | 383.00 | 1709.88 | -63.83 | 1072.89 | 60.48% |
| typical:.9-<1.1 | 216 | 203.20 | 2037.44 | +83.05 | 658.97 | 37.15% |
| below:.9 | 14 | 11.80 | 1380.80 | -68.24 | 30.36 | 1.71% |
| unknown | 8 | 5.00 | 1280.42 | -923.85 | 11.66 | 0.66% |

## opponent_position_bucket

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| middle | 428 | 327.97 | 1831.75 | +124.15 | 992.07 | 55.93% |
| bottom4 | 205 | 140.20 | 1939.72 | -83.50 | 419.75 | 23.66% |
| top4 | 197 | 134.83 | 1700.11 | -19.60 | 362.07 | 20.41% |

## history_support_bucket

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| 30+ | 509 | 507.60 | 1862.65 | +18.19 | 1571.48 | 88.59% |
| 10-<30 | 78 | 73.60 | 1297.77 | -3.30 | 161.44 | 9.10% |
| <10 | 25 | 21.80 | 1194.60 | -24.06 | 40.97 | 2.31% |

## error_direction

Each contribution uses the original equal-event weight and sums to overall MAE within this dimension. Conditional MAE reweights the events present in the segment. An event can cross PIT context buckets across horizons, so segment event counts can overlap.

| Segment | Events | Effective event weight | Conditional MAE | Bias | Contribution to total MAE | Error share |
|---|---:|---:|---:|---:|---:|---:|
| over | 423 | 314.07 | 1463.11 | +1463.11 | 894.24 | 50.41% |
| under | 385 | 278.53 | 1586.94 | -1586.94 | 879.65 | 49.59% |
| exact | 12 | 10.40 | 0.00 | +0.00 | 0.00 | 0.00% |

## Largest event errors

Associations only; causes remain unassessed without supporting source/trajectory evidence.

| Fixture | Actual attendance | Mean AE across horizons | Signed bias | Error share |
|---|---:|---:|---:|---:|
| 2025/2026 / 2025-08-24 / lechiagdansk / arkagdynia | 37500 | 25101.72 | -25101.72 | 2.35% |
| 2025/2026 / 2025-10-19 / lech / pogonszczecin | 39496 | 11949.78 | -11949.78 | 1.12% |
| 2024/2025 / 2025-02-23 / lech / zaglebie_lubin | 16610 | 11022.38 | +11022.38 | 1.03% |
| 2024/2025 / 2025-03-29 / slask_wroclaw / lech | 33546 | 10003.65 | -10003.65 | 0.94% |
| 2025/2026 / 2026-02-15 / lech / piastgliwice | 14638 | 9959.39 | +9959.39 | 0.93% |
| 2024/2025 / 2024-09-22 / lech / slask_wroclaw | 34285 | 9957.62 | -9957.62 | 0.93% |
| 2025/2026 / 2026-03-22 / lech / termalica | 36239 | 9585.21 | -9585.21 | 0.90% |
| 2025/2026 / 2026-05-17 / lechiagdansk / legia | 35000 | 9495.59 | -9495.59 | 0.89% |
| 2024/2025 / 2025-05-03 / slask_wroclaw / zaglebie_lubin | 29987 | 9373.85 | -9373.85 | 0.88% |
| 2024/2025 / 2025-04-05 / slask_wroclaw / motorlublin | 26361 | 8902.52 | -8902.52 | 0.83% |
| 2024/2025 / 2024-09-14 / cracovia / pogonszczecin | 2800 | 8594.45 | +8594.45 | 0.80% |
| 2025/2026 / 2026-05-08 / lech / arkagdynia | 41598 | 8529.53 | -8529.53 | 0.80% |
| 2025/2026 / 2026-01-31 / lech / lechiagdansk | 17827 | 7876.64 | +7876.64 | 0.74% |
| 2024/2025 / 2025-03-30 / gkskatowice / gornikzabrze | 15048 | 7786.12 | -7786.12 | 0.73% |
| 2025/2026 / 2025-09-28 / lech / jagiellonia | 35299 | 7575.99 | -7575.99 | 0.71% |
| 2025/2026 / 2025-11-23 / lech / radomiak | 33877 | 7491.10 | -7491.10 | 0.70% |
| 2024/2025 / 2024-09-14 / lech / jagiellonia | 32365 | 6660.40 | -6660.40 | 0.62% |
| 2024/2025 / 2024-07-21 / lech / gornikzabrze | 19620 | 6609.04 | +6609.04 | 0.62% |
| 2024/2025 / 2024-10-06 / slask_wroclaw / cracovia | 14482 | 6494.86 | +6494.86 | 0.61% |
| 2024/2025 / 2024-08-25 / slask_wroclaw / legia | 36208 | 6453.45 | -3828.25 | 0.60% |
| 2024/2025 / 2025-05-24 / lech / piastgliwice | 41109 | 6448.99 | -6448.99 | 0.60% |
| 2025/2026 / 2025-08-23 / gornikzabrze / gkskatowice | 28236 | 6408.29 | -6408.29 | 0.60% |
| 2024/2025 / 2025-04-05 / lech / koronakielce | 37457 | 6403.75 | -6403.75 | 0.60% |
| 2025/2026 / 2026-02-01 / legia / koronakielce | 14585 | 6398.03 | +6398.03 | 0.60% |
| 2025/2026 / 2025-07-20 / gornikzabrze / lechiagdansk | 24890 | 6208.33 | -6208.33 | 0.58% |
| 2024/2025 / 2025-05-03 / lech / puszcza_niepolomice | 25226 | 6133.54 | +6133.54 | 0.57% |
| 2024/2025 / 2025-02-15 / slask_wroclaw / widzewlodz | 13096 | 6125.55 | +6125.55 | 0.57% |
| 2024/2025 / 2025-05-14 / pogonszczecin / motorlublin | 13662 | 6002.12 | +6002.12 | 0.56% |
| 2024/2025 / 2024-08-18 / slask_wroclaw / koronakielce | 14081 | 5995.01 | +5995.01 | 0.56% |
| 2024/2025 / 2024-08-25 / lech / pogonszczecin | 29156 | 5834.79 | -5834.79 | 0.55% |

## Reproduction and limits

All 10 frozen horizon/season MAEs reproduced within absolute tolerance 1e-7. Source/artifact hashes verified before and after; no models saved or replaced.

- Already exposed test seasons; not fresh confirmatory evidence
- PIT replay of archived fixture times/capacity does not establish historical publication timestamps
- Outcome-conditioned attendance/fill bins are descriptive only
- No historical booking curves; event shocks and causal error attribution unassessed
- Ekstraklasa-only historical cohort differs from current prospective events

`production_change=false`, `live_adjustment=0`.
