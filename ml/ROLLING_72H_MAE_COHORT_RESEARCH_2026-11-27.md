# Rolling 72-hour cohort research — 27 November 2026

## Decision

Prepare a separate, prospective cohort for a **minimum 30 independent fixtures across at least 8 home clubs**, using the fixed **+72-hour public-inventory availability** score as the primary endpoint. Proposed fixture window: **5 December 2026–28 February 2027 (kickoff, inclusive)**. Treat the end date as a planning boundary and re-check the official published calendar before precommit; do not extend it after looking at cohort outcomes. If fewer than 30 eligible fixtures or 8 clubs qualify by the boundary, report the cohort as underpowered and stop. Do not backfill.

This is an availability-seat benchmark. Its labels cannot be described as attendance, paid sales, demand, revenue, or as the separate approximately 1,200-seat attendance-MAE goal. One fixture contributes at most one independent +72 event score; additional horizons, source receipts, or snapshots do not increase the event count.

The active MVP source lane is pinned to `roboticket/roboticket`, the public `available_total_seats` unit, a one-hour source-age limit, and immutable Roboticket admission-v2 receipts. Therefore, **a scheduled match, historical snapshots, or a Stellis record alone is not ready for this lane**. A fresh fixture must first have a verified Roboticket mapping and committed admission-v2 receipt; then its first valid post-activation source seal must be captured prospectively. Research this intake plan only; do not admit events, probe provider endpoints, activate a lane, or change production.

## Finite window and phased intake

The proposed window starts with the next official round for which fixtures are already dated, then covers the restart after the winter break. Each phase is an intake window, not a license to reconstruct earlier points.

| Phase | Proposed scope | Intake rule |
|---|---|---|
| 1 | Matchweeks 17–18 and the two rescheduled Matchweek 4 fixtures, 5–17 Dec 2026 | On/after a separately approved fresh-lane activation, admit only each fixture that obtains a current Roboticket admission-v2 receipt and passes identity/source checks. Start outreach/scouting with the four specific fixtures listed below; all other official scheduled fixtures in this phase remain candidates subject to the same prerequisites. |
| 2 | League restart, 29 Jan–28 Feb 2027 | Reconcile exact dates and kickoffs against the league and home-club calendars when published. Admit every predeclared in-window fixture meeting the same Roboticket requirements; preserve all eligible admissions in the denominator. |

Use 4 fixtures per club as an **outreach/scouting priority** to broaden sourcing; it is not an admission cap, exclusion rule, or a reason to discard eligible receipts. If one club contributes more events than expected, retain them all and report club balance. Keep the stopping rule fixed: close intake at the earlier of the 28 Feb boundary or a predeclared total admission limit in the eventual reviewed manifest; no discretionary replacement for a refusal or an awkward outcome. The numerical cap needs to be selected before activation and is not set by this research note.

The currently published winter calendar says regular play resumes 29 Jan 2027 and the autumn round ends 11–14 Dec, with two rescheduled fixtures on 16–17 Dec. It does not make later fixtures Roboticket-ready. Re-check all dates and kickoff changes at each intake batch; the league may change postponed fixtures.

## Next fixture candidates and readiness

The league and club calendars confirm these first targets:

| Fixture | Official kickoff | Current Beyond source status | Cohort disposition |
|---|---:|---|---|
| Cracovia–Widzew Łódź (MW17; supplied source ID 10896) | 5 Dec, 14:45 CET | No matching row by `ticket_events.id` or `external_event_id` in the current hosted table; no current admission-v2 receipt established by this read-only check | **Needs source mapping and Roboticket admission validation.** Do not count yet. |
| GKS Katowice–Legia Warszawa (MW17; supplied source ID 5772) | 5 Dec, 20:15 CET | No matching row by `ticket_events.id` or `external_event_id` in the current hosted table; no current admission-v2 receipt established by this read-only check | **Needs source mapping and Roboticket admission validation.** Do not count yet. |
| Motor Lublin–Lech Poznań (MW17) | 5 Dec, 17:30 CET | `ticket_event_id=25667`, provider `stellis`, external event `50505`; 2,824 historical snapshots | **NO current lane compatibility.** Stellis is outside the frozen Roboticket source family. Keep as a scouting lead only; separate source/lane review required. |
| Piast Gliwice–Jagiellonia Białystok (MW17) | 6 Dec, 17:30 CET | `ticket_event_id=25668`, provider `stellis`, external event `50502`; 1,100 historical snapshots | **NO current lane compatibility.** Stellis is outside the frozen Roboticket source family. Keep as a scouting lead only; separate source/lane review required. |

The separate 26 November probes already confirmed the direct ticket page and usable public inventory for Cracovia and GKS. A reviewed admission packet and an active new window are still pending. To admit a true +72 h opportunity for both 5 December games, start before 2 December 14:45 Warsaw, the earlier of the two match-specific cutoffs. The kickoff window start does not constrain the earlier date of prospective collection.

The four fixtures above span four home clubs, but **0/4 are ready to admit today**: two lack a mapped current fixture/admission in the checked table, and two are incompatible Stellis fixtures. They provide no counted events or clubs toward 30/8 at this point. The active source registry has one fixture, Jagiellonia–Radomiak (29 Nov), and it is in the existing window, not this proposed new cohort.

The rest of the near-term official fixture pool is concrete at league level but not currently present as a future ticket-event mapping in the checked database:

- MW17, 4–7 Dec: Wieczysta–Korona; Zagłębie Lubin–Wisła Kraków; Cracovia–Widzew; Motor–Lech; GKS–Legia; Radomiak–Raków; Pogoń–Górnik; Piast–Jagiellonia; Wisła Płock–Śląsk.
- MW18, 11–14 Dec: Wisła Płock–Raków; Legia–Pogoń; Wieczysta–Radomiak; Motor–Widzew; Śląsk–Górnik; Korona–Jagiellonia; Cracovia–Lech; GKS–Wisła Kraków; Piast–Zagłębie.
- Rescheduled MW4, 16–17 Dec: Jagiellonia–Pogoń; Wisła Płock–Lech.

These 20 scheduled fixtures are a shortlist to reconcile against fresh Roboticket receipts, not 20 admissions. At the database check time, only two different Dec 5/6 fixtures from this list had future ticket-event rows, and both were Stellis. Treat the remaining matches as schedule-confirmed, source-unverified. The spring-phase fixture pairs/dates should be attached from current official league and home-club schedules before each intake; do not rely on the framework calendar’s placeholder times.

## Conflict and source compatibility check

Read-only hosted Supabase checks (project `Beyond's Project`) were limited to the listed fixture IDs, future `public.ticket_events` rows, their snapshot counts/latest capture, the active rolling72 registries, and the five frozen managed-v3a fixture rows. No label values or attendance outcomes were queried.

- The current `rolling72-mvp-research-v1` source lane is activated 23 Nov, has `issue_until=2026-12-01 00:00 UTC`, `scoring_until=2026-12-04 06:00 UTC`, and has one registered fixture: `Jagiellonia–Radomiak`, 29 Nov (`ticket_event_id=27049`). This is the existing narrow window and must remain untouched.
- The frozen `rolling72-managed-persistence-shadow-v3a` list contains five fixtures: Cracovia–Jagiellonia (21 Nov), GKS–Lech (22 Nov), Raków–Widzew (22 Nov), Śląsk–GKS (28 Nov), and Wisła Kraków–Motor (28 Nov). No proposed Dec 5–Feb 28 fixture date overlaps these five.
- Thus the proposed start candidates have no match-date collision with the checked old windows. Re-run exact fixture-ID and kickoff overlap checks before a future admission; this research is not an admission authorization.
- The current 2026/27 `public.ticket_events` table contains 47 rows. Within the proposed Dec 2026 start shortlist, the only future mapped Ekstraklasa events found were Motor–Lech and Piast–Jagiellonia (both Stellis). Jagiellonia–Crystal Palace on 10 Dec is a non-league fixture and out of scope. Upcoming Nov 28–29 rows belong to the two protected/active windows and are excluded.
- Recent 2026/27 Ekstraklasa mapping history shows verified Roboticket fixtures across 12 home clubs, so the 8-club goal is operationally plausible; prior history is not new-cohort evidence and is not an admission for future fixtures.

**Current credible counts:** ready to admit = **0**; official near-term league fixtures shortlisted = **20**; of those, 2 have Stellis rows explicitly incompatible with the frozen Roboticket lane and 2 named priority candidates still lack current ticket-event/admission records. No fixture has been admitted to this planned cohort.

## Low-cost intake and reporting contract

1. Before activation, freeze a versioned manifest, finite issue/scoring deadlines, the Roboticket-only source contract, exact +72 target rule, eligibility/refusal statuses, and maximum admission count. Existing issue/scoring deadlines or registries are not to be edited or reused.
2. At each batch, reconcile the official league schedule, home-club schedule, ticket-event identity, Roboticket club/source registration, provider event identity, and committed admission-v2 receipt. A missing or ambiguous identity stays unadmitted.
3. Admit only future public home-fixture events inside the frozen window. Start collection only after the new lane’s actual activation; do not import ordinary historical snapshots, old admission rows, or missed cutoff points. Do not change the fixed `available_total_seats` unit or silently treat hidden/unavailable inventory as zero.
4. Include a +72 prediction only when its actual issue is after the committed source read and calculation and its target remains strictly before kickoff. Score only from a later genuine source observation valid at the target (maximum 6-hour age under the current PERS contract), preserving the first accepted label and all refusals, missing labels, scope changes, and out-of-window candidates.
5. Primary MAE: mean absolute error per independent fixture at +72, then equal weight across fixtures. Report admitted events, clubs, coverage, scoreable labels, event-balanced MAE, signed bias, event improvement rate against the predeclared comparator, median event delta, and P90/worst degradation. No labels means no MAE; fewer than 30 events or 8 clubs is a collection result, not a benchmark claim.
6. Keep production `live_adjustment=0` and `production_change=false`. No automatic promotion follows this study.

## Schedule references

- Ekstraklasa, [Matchweek 17 schedule](https://ekstraklasa.org/aktualnosci/terminarz-17-kolejki-202627/) — exact Dec 4–7 pairings and kickoff times.
- Ekstraklasa, [Matchweek 18 and postponed Matchweek 4 schedule](https://ekstraklasa.org/aktualnosci/terminarz-18-kolejki-oraz-terminy-meczow-zaleglych/) — exact Dec 11–17 dates; confirms last 2026 matches and Jan 29 restart.
- Cracovia, [Cracovia–Widzew match page](https://www.cracovia.pl/games/254/cracovia-widzew-lodz) and [official calendar](https://www.cracovia.pl/games) — confirms 5 Dec 14:45, 13 Dec home match, and current spring home/away calendar entries.
- GKS Katowice, [GKS–Legia match page](https://www.gkskatowice.eu/game/3203-gks-katowice-legia-warszawa_2026-12-05) and [official team fixture calendar](https://www.gkskatowice.eu/terminarz/pilkarze) — confirms 5 Dec 20:15 and 13 Dec home match.
- Ekstraklasa, [2026/27 framework schedule](https://ekstraklasa.org/aktualnosci/terminarz-pko-bank-polski-ekstraklasy-w-sezonie-2026-27/) — confirms 29 Jan restart, 22 May season end, and the potential for rescheduled-match changes.

## Repository/database reads used

`public.ticket_events` was joined to `public.snapshots` only for per-fixture counts and latest capture timestamps, and to the active private rolling72 registries for the window check. Scoped SQL used explicit date bounds (`2026-11-27` through `2027-04-01`, and a second future-ticket scan with a 120-row cap); additional reads were restricted to active lane/registry rows and the five frozen v3a fixtures. No writes, provider probes, admission RPC calls, attendance reads, or outcome/label-value queries were performed.
