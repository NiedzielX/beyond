# T-7 Fixed Temporal Robustness v1 — Result 2026-10-18

Status: **COMPLETED / FIXED CONFIG IMPROVES 4 OF 4 ROLLING FOLDS / TAIL RISK REMAINS / NO PRODUCTION CHANGE**

Workstream:

**a2 — Historical / Structural Prior optimization — T-7 fixed-config temporal robustness**

## Evidence source

GitHub Actions run: `39159276055`  
Tested branch head: `d3b439532af04ab72f07c2c202ce1367122b9d7a`  
Artifact: `t7-fixed-temporal-robustness-v1-39159276055`  
Artifact ID: `12148660037`  
Artifact ZIP SHA256: `a8d975d63f8387a14ecb7c7dac0a2da6d1c96b1cc4af1d4d267a2dd70b0c7f2b`  
Result JSON SHA256: `0e3f6720be56dabe358cea00b3ad5edf896e4dc7f71940cb89b400f287621d54`

CI:

- compile: PASS;
- unit tests: **4/4 PASS**;
- frozen input hash assertion: PASS;
- exact Stage-3 candidate reproduction assertions: PASS;
- four rolling folds: PASS;
- 10,000-sample paired bootstrap per fold: PASS;
- artifact upload: PASS.

`promotion_allowed = false`

Production remains unchanged.

## Fixed challenger

`hist31-leaf20-l2-1`

No tuning or model selection occurred in this audit.

Exact configuration:

- HistGradientBoostingRegressor;
- loss `absolute_error`;
- learning rate 0.04;
- 300 iterations;
- max leaf nodes 31;
- min samples leaf 20;
- L2 1.0;
- seed 42;
- current T-7 base feature contract;
- `baseline_season`;
- capacity-normalized residual target.

Canonical Stage-3 JSON dependency:

`83da3d85daa7c7bc844b8cb6b63cdf47070068cdabb774d0f4c01e5a3e0258fe`

## Exact reproduction gates

The audit reproduced the Stage-3 challenger exactly:

| Season | Expected MAE | Actual MAE |
|---|---:|---:|
| 2023/24 | 2,317.3395349341 | 2,317.3395349341 |
| 2024/25 | 1,650.9668467459 | 1,650.9668467459 |
| 2025/26 | 1,773.7952605858 | 1,773.7952605858 |

Tolerance:

`1e-9`

## Rolling temporal result

| Test season | Evidence role | Incumbent MAE | Challenger MAE | Improvement | Bootstrap P(uplift > 0) | Worst degradation |
|---|---|---:|---:|---:|---:|---:|
| 2022/23 | additional pre-selection historical fold | 2,088.94 | **1,984.99** | **+103.95** | 91.8% | +6,623.99 |
| 2023/24 | development selection season | 2,476.82 | **2,317.34** | **+159.48** | 99.08% | +4,335.66 |
| 2024/25 | exposed reference | 1,777.69 | **1,650.97** | **+126.73** | 99.35% | +4,094.16 |
| 2025/26 | exposed reference | 1,802.28 | **1,773.80** | **+28.48** | 76.04% | +3,700.56 |

Summary:

- positive MAE improvement: **4/4 folds**;
- mean fold improvement: **+104.66 MAE**;
- median fold improvement: **+115.34 MAE**;
- weakest fold improvement: **+28.48 MAE**;
- strongest fold improvement: **+159.48 MAE**.

The direction of the MAE signal is therefore not limited to the Stage-3 selection season or the two reference seasons.

## Distribution quality by fold

### 2022/23

- incumbent median AE: 1,219.82;
- challenger median AE: **1,140.88**;
- incumbent p90 AE: 5,308.71;
- challenger p90 AE: **4,697.57**;
- incumbent bias: +698.15;
- challenger bias: **-167.36**;
- event improvement rate: **54.88%**.

Paired bootstrap mean-uplift 95% interval:

`[-44.91, +251.11]`

Probability mean improvement > 0:

**91.8%**.

Important tail:

`Lech – Legia`, 2022-10-01

worst degradation:

**+6,623.99 seats**.

This is the largest harmful single-event regression observed across the four-fold audit.

### 2023/24

- median AE: 1,288.41 -> **1,103.63**;
- p90 AE: 5,598.34 -> **5,448.81**;
- bias: -504.93 -> **-31.75**;
- event improvement rate: **53.20%**;
- bootstrap 95% interval: **[+28.45, +294.77]**;
- bootstrap P(uplift > 0): **99.08%**;
- worst degradation: **+4,335.66**.

### 2024/25

- median AE: 1,091.35 -> **926.00**;
- p90 AE: 4,767.84 -> **4,396.22**;
- bias: +133.90 -> **+13.05**;
- event improvement rate: **53.33%**;
- bootstrap 95% interval: **[+25.27, +226.26]**;
- bootstrap P(uplift > 0): **99.35%**;
- worst degradation: **+4,094.16**.

### 2025/26

- median AE: 1,153.15 -> **1,051.76**;
- p90 AE: 3,965.92 -> **3,753.08**;
- bias: +78.86 -> **-5.43**;
- event improvement rate: **53.14%**;
- bootstrap 95% interval: **[-50.93, +107.07]**;
- bootstrap P(uplift > 0): **76.04%**;
- worst degradation: **+3,700.56**.

The weakest season remains 2025/26: point MAE improves, but the paired uncertainty interval crosses zero.

## Club consistency

Across club-season cells with at least 10 scored home events:

- reported cells: **72**;
- cells with lower challenger MAE: **47**;
- cells worse/equal: **25**;
- improvement rate: **65.28%**.

This is broader than a one-club effect, but not universal.

## Harmful regression frequency

Rates of event-level challenger degradation versus incumbent:

### 2022/23

- >500 seats: 19.53%;
- >1,000: 13.47%;
- >2,000: 4.38%;
- >3,000: 2.02%.

### 2023/24

- >500: 15.15%;
- >1,000: 7.41%;
- >2,000: 3.03%;
- >3,000: 1.68%.

### 2024/25

- >500: 13.00%;
- >1,000: 7.33%;
- >2,000: 1.67%;
- >3,000: 0.67%.

### 2025/26

- >500: 15.51%;
- >1,000: 6.27%;
- >2,000: 0.99%;
- >3,000: 0.66%.

Tail frequency improves materially in later folds, but severe failures are not eliminated.

## Interpretation

Positive evidence:

1. Fixed config improves MAE in **all four** rolling seasons.
2. The additional 2022/23 fold, which did not select the Stage-3 config, is also positive (+103.95 MAE).
3. Median AE improves in all four folds.
4. p90 AE improves in all four folds.
5. Bias becomes materially closer to zero in all four folds.
6. 65% of reportable club-season cells improve.
7. 2023/24 and 2024/25 paired bootstrap intervals are entirely positive.

Remaining risk:

1. The earliest fold has a **+6.62k** worst harmful regression.
2. 2025/26 uplift is small and bootstrap uncertainty crosses zero.
3. Event improvement rate is only ~53–55%, meaning value comes from magnitude, not winning most events by a large margin.
4. 25/72 reportable club-season cells are not improved.
5. These are historical folds; 2023/24 selected the model and 2024/25–2025/26 were already exposed references.

## Decision

> **The Stage-3 T-7 challenger passes the broader historical directionality test: its MAE improvement is positive in 4/4 rolling folds and is not confined to the original development/reference window. It is credible enough to freeze as the current historical T-7 Pre-Live candidate configuration, but not to replace production from historical evidence alone.**

Freeze meaning here:

- stop tuning T-7 estimator hyperparameters on the current historical reference set;
- preserve `hist31-leaf20-l2-1` unchanged as the T-7 candidate for later Pre-Live v2 integration / prospective comparison;
- do not claim production promotion;
- do not hide the remaining tail-risk evidence.

Production remains:

`structural-prior-runtime-v1-t7-gbr-base`

and globally:

`live_adjustment = 0`

## Next a2 direction

T-7 estimator search should stop unless genuinely new data or a materially new hypothesis appears.

Continue a2 on the weaker/unresolved horizons rather than micro-tuning T-7 further:

- T-30;
- T-14;
- T-3;
- T-1.

Use stronger multi-fold selection instead of one-season winner selection, then freeze per-horizon historical candidates before b2.
