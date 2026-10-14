# Beyond Growth — Measurement v1

Status: **POC active / no external campaign execution**

## Product flow

`Demand signal → Growth recommendation → Experiment draft → Treatment / Holdout → Arm-level outcome data → Incremental tickets → Incremental revenue → Contribution → ROI`

The Growth layer is intentionally separate from the forecast model. A forecast or Growth recommendation never launches a campaign, changes a ticket price, or makes a production decision by itself.

## Experiment model

Each experiment belongs to one `ticket_event_id` and contains:

- play: `protect_yield`, `demand_activation`, `last_mile_conversion`, `monitor`, or `hold_data_quality`;
- hypothesis;
- action description;
- primary metric;
- assignment method;
- currency;
- operational minimum exposed audience per arm;
- treatment and holdout arms;
- audit history.

Experiment states:

1. `draft`
2. `planned`
3. `running`
4. `completed`
5. `cancelled`

`auto_execution_allowed = false` is enforced. Beyond currently tracks the experiment; it does not execute the campaign.

## Preferred design

Preferred v1 design: `randomized_holdout`.

Other supported labels:

- `geo_holdout`
- `quasi_experimental`
- `manual_noncausal`

Manual comparison is explicitly marked non-causal.

## Aggregate-only data contract

No customer-level PII is required by v1.

Each arm supplies cumulative checkpoints:

| Field | Meaning |
| --- | --- |
| experiment_key | Stable Beyond experiment identifier |
| arm_key | `treatment` or `holdout` |
| observed_at | Timestamp of the cumulative checkpoint |
| exposed_count | Unique audience exposed to the arm |
| purchasers_count | Purchasers attributed to the arm |
| tickets_count | Tickets purchased by the arm |
| gross_ticket_revenue | Gross ticket revenue in experiment currency |
| refunds_amount | Refunded ticket revenue |
| campaign_cost | Direct campaign cost allocated to the arm |
| source_record_key | Idempotency key for the source checkpoint |

The controlled ingest rejects cumulative regressions: exposure, purchasers, tickets, gross revenue, refunds, campaign cost, and observation timestamps may not move backwards.

## Measurement status

- `awaiting_data` — one or both arms have no observation;
- `collecting_sample` — both arms exist but at least one is below the configured exposure gate;
- `descriptive_only` — data exists but assignment is explicitly non-causal;
- `experiment_observed` — both arms passed the operational exposure gate and the design is experimental/quasi-experimental.

The default gate is **100 exposed users per arm**. This is an operational minimum only. It is **not** treated as proof of statistical significance.

## Calculations

### Ticket rate

`tickets / exposed`

### Incremental tickets on the treatment population

`(treatment ticket rate - holdout ticket rate) × treatment exposed`

### Gross revenue per exposed

`gross ticket revenue / exposed`

### Incremental gross revenue

`(treatment gross revenue per exposed - holdout gross revenue per exposed) × treatment exposed`

### Net revenue per exposed

`(gross ticket revenue - refunds) / exposed`

### Incremental net revenue

`(treatment net revenue per exposed - holdout net revenue per exposed) × treatment exposed`

### Incremental campaign cost

`treatment campaign cost - scaled holdout campaign cost`

where holdout campaign cost is scaled to the treatment population by exposure.

### Incremental contribution

`incremental net revenue - incremental campaign cost`

### ROI

`incremental contribution / incremental campaign cost`

ROI is only shown when incremental campaign cost is positive.

## Interpretation guardrail

The dashboard never converts missing outcome data into zero revenue.

Even after the operational exposure gate is met, v1 shows **raw experiment uplift** only. Statistical significance is not yet assessed and must not be implied.

## First real draft

A real, non-executing draft has been created for:

**Lech Poznań – Korona Kielce**

Play: `protect_yield`

Rationale snapshot at draft creation:

- public availability was very low versus the first observed inventory;
- no release-activity flag;
- no sector-coverage-change flag;
- live inventory history was already deep enough for a stable signal.

Experiment design:

- Treatment: 90%
- Holdout: 10%
- Assignment: randomized holdout
- Primary metric: incremental contribution

No audience was assigned and no campaign was launched by Beyond.

## Dashboard

Two product surfaces consume Growth Measurement v1:

### Event Detail

`Beyond Growth · Opportunity`

followed by:

`Growth Experiment Tracker`

### Club navigation

A dedicated `Growth` page shows the experiment portfolio for the selected club, including:

- experiment count;
- draft/running state;
- measurement status;
- incremental tickets;
- incremental contribution;
- ROI.

Missing measurements are rendered as `—`, not zero.
