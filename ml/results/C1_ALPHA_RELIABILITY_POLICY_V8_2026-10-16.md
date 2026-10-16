# C1-alpha Reliability Policy v8 — fixed PIT-safe expert switch

Date: **2026-10-16**  
Status: **development candidate / prospective validation required / not production**

## Purpose

v8 evaluates one fixed, interpretable policy for choosing between:

- the frozen T-1 Structural Prior; and
- the existing v2 final-24h live expert `ridge_directocc_compact_generic_a10`.

The policy was predeclared after the v7 reliability diagnostic. v8 does **not** fit or tune a selector.

## Fixed policy

Policy ID:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

At every PIT row inside the final 24h:

### One live observation available

Use LIVE only when:

`abs(prior occupancy - live occupancy) >= 20 percentage points`

Otherwise use PRIOR.

### Two or more live observations available

Use LIVE only when both are true:

1. current absolute prior/live disagreement is at least **10 percentage points of verified capacity**; and
2. v2 live prediction slope, calculated only from observations available up to the current PIT row, is **strictly positive**.

Otherwise use PRIOR.

No future final-24h row is used in an earlier decision.

## Run / artifact

GitHub Actions run: `38894352140`  
Evaluation job: `116951285176`  
Artifact: `c1-alpha-reliability-policy-v8-38894352140`  
Artifact ID: `12043541318`  
Artifact ZIP SHA256: `243909d5091aca49212aa3075db981fa2cb42833206ea769702e70ca962a47f9`

Dataset:

- 9 completed current-domain Ekstraklasa events;
- 30 regularized PIT-valid final-24h rows;
- v2 live expert trained under outer Leave-One-Event-Out;
- current Structural Prior replayed from frozen runtime.

Hard reproduction guards passed:

- Structural Prior MAE: **3,968.7268**;
- v2 live expert MAE: **2,929.3193**;
- prior/live oracle MAE: **1,867.8561**.

## v8 development result

Across equal-weighted event window MAE:

- Structural Prior: **3,968.7**;
- v2 live expert: **2,929.3**;
- **v8 policy: 2,713.3**;
- non-deployable oracle: **1,867.9**.

v8 vs Structural Prior:

- absolute uplift: **1,255.5**;
- relative improvement: **31.63%**;
- gap to oracle: **845.4**;
- event improvement rate: **3/9 = 33.33%**;
- live selected on **5/30 rows = 16.67%**;
- worst event degradation vs Prior: only **203.3**.

The low event-improvement rate is expected from a conservative gate: on five events it intentionally preserves the Structural Prior unchanged instead of replacing an already strong prior.

## Latest available row before kickoff

This is the most product-relevant diagnostic because it reflects the decision at the latest observed PIT point for each completed event.

- Structural Prior latest-row MAE: **3,968.7**;
- v2 live latest-row MAE: **3,046.6**;
- **v8 latest-row MAE: 1,998.1**.

Latest-row v8 therefore reaches the vicinity of the ~1.9k target on the development evidence while remaining fully PIT-safe.

It is **not** a fresh validation result.

## Event behaviour

| Event | Prior event MAE | v2 live event MAE | v8 event MAE | Latest expert |
|---|---:|---:|---:|---|
| Lech — Raków | 5,031.1 | 9,779.7 | **5,031.1** | PRIOR |
| Lech — Jagiellonia | 6,691.8 | 1,389.4 | **3,613.0** | LIVE |
| Lech — Radomiak | 11,364.5 | 4,991.9 | **9,993.6** | LIVE |
| Jagiellonia — Górnik | 86.9 | 503.8 | **86.9** | PRIOR |
| Pogoń — Korona | 89.1 | 1,390.8 | **89.1** | PRIOR |
| Cracovia — Zagłębie | 1,096.5 | 916.5 | **1,299.8** | LIVE |
| Śląsk — Lech | 9,723.4 | 2,670.6 | **2,670.6** | LIVE |
| GKS Katowice — Wieczysta | 783.4 | 2,400.0 | **783.4** | PRIOR |
| Legia — Wisła Kraków | 851.7 | 2,321.1 | **851.7** | PRIOR |

The only event-level degradation relative to Prior is Cracovia — Zagłębie, by approximately **203** on the event-window metric.

## Latest-row decisions

At the latest available row the policy selects LIVE for:

- Lech — Jagiellonia: 17.04 pp disagreement, positive slope;
- Lech — Radomiak: 12.67 pp disagreement, positive slope;
- Cracovia — Zagłębie: 20.02 pp disagreement, positive slope;
- Śląsk — Lech: 28.36 pp disagreement with only one observation, therefore the stricter 20 pp single-observation rule applies.

It preserves PRIOR for:

- Lech — Raków: only one observation and 10.97 pp disagreement — below the 20 pp burden;
- Jagiellonia — Górnik: only 0.70 pp latest disagreement;
- Pogoń — Korona: 6.43 pp disagreement;
- GKS Katowice — Wieczysta: 6.63 pp disagreement;
- Legia — Wisła Kraków: disagreement is material at 13.07 pp, but the live trajectory slope is negative.

## Governance interpretation

v8 is the strongest current **decision policy candidate**, but this replay is development evidence only.

Why:

- the rule was designed after inspecting v7 labels on the same 9 completed events;
- therefore these 9 events are not an untouched validation set for the v8 thresholds;
- the ~1,998 latest-row MAE must not be advertised as an independently validated production metric.

The next valid evidence must come from **future 2026/27 events whose outcomes were not known when v8 was frozen**.

## Decision

1. **Freeze the v8 rule exactly as written. Do not tune 10 pp / 20 pp / positive-slope thresholds on these 9 events again.**
2. Treat v8 as `EXPERIMENTAL_SHADOW` only.
3. Keep production `live_adjustment = 0`.
4. Fit/freeze one v2 live-expert artifact on the currently available completed training events for prospective shadow inference.
5. Persist prospective v8 decisions, reason codes, prior/live predictions and timestamps before outcomes are known.
6. Evaluate every newly completed event against the frozen v8 package.
7. Reconsider promotion only after sufficient genuinely prospective independent evidence.

This is now the canonical C1-alpha candidate for prospective validation.
