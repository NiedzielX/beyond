# Beyond — Claude instructions

Read and follow root `AGENTS.md`. The canonical ML read order is:

1. `ml/MAE_RESEARCH_ROADMAP_V6.md`;
2. `ml/EXECUTION_PLAN_CURRENT.md`;
3. `ml/PROGRESS_TRACKING.md`;
4. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`;
5. `ml/NEXT_SESSION_HANDOFF.md`;
6. then implementation, workflows and live state. Read `.ai/lessons.md` before implementation.

## Mandatory shared working records

- Write material change/experiment specifications in `.ai/specs/YYYY-MM-DD-slug.md`, with acceptance criteria and links to canonical `ml/` contracts. Move completed specifications with evidence to `.ai/specs/implemented/`; move withdrawn/superseded ones to `.ai/specs/archive/`. Partially deployed work remains active.
- Maintain `.ai/runs/YYYY-MM-DD-slug.md` for every logical autonomous run: goal, changes, validation, evidence, blockers and next action. Update it while working and before handing off; routine steps do not require stopping the run.
- Use `.ai/lessons.md` as the long-term memory index and `.ai/lessons/` for focused findings. Read existing findings before implementing; record useful bug fixes, rejected hypotheses and operating constraints with evidence and limits.
- Keep names dated and descriptive. Never store secrets or private source exports in Git. Keep these records and canonical execution status consistent. Documentation requirements do not add an approval gate to authorized work.

Keep existing models, parameters and evidence contracts frozen unless the authoritative plan authorizes a separate experiment. New version names do not make exposed events fresh. No retrospective prospective forecasts. Missing/hidden observations are not zero. Distinguish public inventory, paid sales and attendance. Keep `production_change=false` and `live_adjustment=0`. Claim end-to-end automation only with successful workflow and expected persisted-record evidence.

Current MVP acceptance is `ml/ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1.md`: from the first genuine observation, forecast the next24/48/72hours and preserve each issue for later real-outcome scoring. Do not substitute final24C1, a terminal-attendance chart or hypothetical price effects for that product. Frozen lanes and their original gates remain unchanged.

Persistent user goal: the lowest honest prospective MAE, still aiming for approximately 1200 seats attendance MAE. Rolling24/48/72h forecasting complements this accuracy goal. Report targets/horizons/cohorts separately; do not claim the 1200 attendance milestone from another target or favorable subset. Existing frozen gates and parameters remain unchanged.

Whole-sales-lifecycle rule: after sales open, the first genuine observation (even one point) starts rolling+24/+48/+72h forecasts. Re-issue throughout the observed sales period, e.g.P-50→P-49/P-48/P-47 andP-15→P-14/P-13/P-12. Do not turn these horizons into a final72h activation window or invent the missed beginning of sales. Preserve existing frozen eligibility contracts; the first-observation route belongs to a new version.

Read `ml/ROLLING_72H_LITERATURE_REVIEW_2026-11-08.md` before rolling72implementation. Preserve its source-access limits and distinguish MAE forecasting, sector-specific early warnings and causal price/ad revenue effects. The review changed no frozen model/gate and confirms no guaranteed1200result.

## Agent resource budget

User preference confirmed November10: use at most one parallel sub-agent, default model `gpt-6-luna` with a narrow self-contained task and no full-history fork. The parent owns integration, publication and final validation. Do not launch heavier agents or increase parallelism unless the user changes this preference. Read the current canonical sections in order and the exact relevant precommit; avoid copying unrelated historical logs into sub-agent context.
