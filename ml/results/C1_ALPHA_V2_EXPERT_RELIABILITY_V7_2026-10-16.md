# C1-alpha v2 Expert Reliability Diagnostic v7

Date: **2026-10-16**  
Status: **completed / diagnostic only / no selector trained**

## Purpose

v7 did not run another model tournament.

It reproduced the existing v2 final-24h expert under outer Leave-One-Event-Out and created one event-level reliability profile for each held-out match to answer:

> **What PIT-observable characteristics distinguish events where Structural Prior should be trusted from events where the final-24h live expert should take over?**

Actual attendance and oracle winner are evaluation labels only. They are not predictor inputs.

## Run / artifact

GitHub Actions run: `38891888643`  
Diagnostic job: `116943285009`  
Artifact: `c1-alpha-v2-reliability-v7-38891888643`  
Artifact ID: `12042142459`  
Artifact ZIP SHA256: `25284d59617a520f9bf071a0642935273bc6a63554b0df2fe2b702343dc9ddf9`

The v7 runtime uses split service-role-only context exports to stay below PostgREST statement timeout:

- `c1-alpha-v7-events-v1`;
- `c1-alpha-v7-attendance-v1`;
- `c1-alpha-v7-sporting-v1`;
- `c1-alpha-v7-aliases-v1`;
- `c1-alpha-v7-hybrid-v1`;
- `c1-alpha-v7-final24-rows-v1`.

Verified payload:

- 9 events;
- 34 current-season attendance rows;
- 108 sporting rows;
- 20 aliases;
- 8 T-24 hybrid rows;
- 30 regularized final-24h live rows.

## Exact v2 reproduction

The hard reproduction guard passed.

- Structural Prior MAE: **3,968.7268**;
- v2 live expert MAE: **2,929.3193**;
- absolute uplift: **1,039.4074**;
- relative improvement: **26.19%**;
- non-deployable oracle prior-or-live MAE: **1,867.8561**;
- oracle winners: **PRIOR 5 / LIVE 4**.

This confirms that v7 is diagnosing the same v2 expert pair already published, not a new model variant.

## Event-level oracle labels

| Event | Prior error | v2 live window MAE | Oracle expert |
|---|---:|---:|---|
| Lech — Raków | 5,031.1 | 9,779.7 | PRIOR |
| Lech — Jagiellonia | 6,691.8 | 1,389.4 | LIVE |
| Lech — Radomiak | 11,364.5 | 4,991.9 | LIVE |
| Jagiellonia — Górnik | 86.9 | 503.8 | PRIOR |
| Pogoń — Korona | 89.1 | 1,390.8 | PRIOR |
| Cracovia — Zagłębie | 1,096.5 | 916.5 | LIVE |
| Śląsk — Lech | 9,723.4 | 2,670.6 | LIVE |
| GKS Katowice — Wieczysta | 783.4 | 2,400.0 | PRIOR |
| Legia — Wisła Kraków | 851.7 | 2,321.1 | PRIOR |

## Most useful diagnostic contrasts

These are exploratory contrasts only. They must not be presented as independently validated selector features.

### 1. Prior-vs-live disagreement

Latest absolute disagreement as share of verified capacity:

- PRIOR-winner median: **6.63 pp**;
- LIVE-winner median: **18.53 pp**.

Earliest absolute disagreement:

- PRIOR-winner median: **7.84 pp**;
- LIVE-winner median: **17.61 pp**.

This is the clearest product-semantic signal: when two independent experts materially disagree, the live trajectory may be identifying a Structural Prior miss.

### 2. Direction of the v2 live estimate through final 24h

Median live prediction slope, expressed as occupancy per hour:

- PRIOR winners: **-0.00268**;
- LIVE winners: **+0.00094**.

The four LIVE-winner events all had a non-negative/positive live-expert direction under the available final-24h evidence, while the multi-row PRIOR winners had falling live estimates.

This is a plausible reliability condition: a materially different live estimate is more credible when the observed final-24h trajectory continues to support it rather than fading.

### 3. Public availability regime

Earliest public availability share of capacity:

- PRIOR-winner median: **13.19%**;
- LIVE-winner median: **28.17%**.

Latest public availability share:

- PRIOR-winner median: **12.77%**;
- LIVE-winner median: **23.83%**.

This supports the interpretation that live evidence adds most value when substantial public inventory remains and the Structural Prior is not already effectively confirmed by near-sold-out conditions.

### 4. Structural Prior occupancy

Median Structural Prior expected occupancy:

- PRIOR winners: **80.96%**;
- LIVE winners: **69.16%**.

This is diagnostic context, not sufficient by itself for a selector.

## Signals that should NOT be used naively

The strongest raw contrast by standardized median gap was `signal_ready_row_share`, but the direction was counter-intuitive:

- PRIOR-winner median: **1.0**;
- LIVE-winner median: **0.0**.

Similarly, data-gap and feature-quality flags do not behave as simple confidence scores in this mixed historical evidence because older Lech trajectories use a different/raw-only evidence regime yet contain valuable predictive signal.

Therefore:

> **Do not use `signal_ready`, `feature_quality`, matched-vs-raw source, or `hybrid_v6` alone as the v8 expert gate.**

They remain audit/quality context.

## Single-observation events

Two events have only one usable final-24h v2 observation:

- Lech — Raków: prior/live disagreement **10.97 pp**; PRIOR wins;
- Śląsk — Lech: disagreement **28.36 pp**; LIVE wins.

With one row there is no trajectory slope. A reliability policy must therefore use a stricter disagreement requirement for single-observation events instead of pretending stability was observed.

## v8 policy design — predeclared after v7

v8 will test **one fixed, interpretable hard-switch policy**. It will not run a threshold grid.

### Multi-observation event

Use LIVE only when:

1. the latest absolute prior-vs-live disagreement is at least **10 percentage points of verified capacity**; and
2. the v2 live prediction slope across the available final-24h observations is **strictly positive**.

Otherwise use PRIOR.

### Single-observation event

Because no trajectory direction can be established, use LIVE only when absolute prior-vs-live disagreement is at least **20 percentage points of verified capacity**.

Otherwise use PRIOR.

### Why these thresholds

- **10 pp** = a deliberately material difference in expected stadium occupancy; smaller differences do not justify overriding the Structural Prior.
- **20 pp** = a deliberately stronger evidence burden when only one live observation exists and stability cannot be measured.
- positive trend = the observed live evidence continues to support the alternative live estimate rather than decaying through the final-24h window.

No outcome is used when applying the rule.

## Governance warning for v8

The v8 policy was designed **after inspecting v7 diagnostic labels on these same 9 events**.

Therefore its replay on these 9 events is **development evidence**, not an untouched validation set and not promotion evidence, even if performance is strong.

The next genuinely fresh confirmation must come from prospective 2026/27 completed events.

Production remains:

`live_adjustment = 0`

No v2-v7 result is activated automatically.
