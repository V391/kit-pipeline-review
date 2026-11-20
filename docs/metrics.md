# Sales metrics: definitions for people and AI tools

Warehouse schema: `main`. Quarters are strings like `2026-Q2`. All data here is synthetic sample data.

Every rate is a share from 0 to 1 (0.268 is 26.8%). A change in percentage points is the difference of
two shares (0.043 is 4.3 points).

**Start here.** For a sales metric, use the mart named below. Do not recompute a metric from `fct_deals`
unless no mart answers the question: the marts hold the agreed definition.

| Question about | Use | Default reading |
|---|---|---|
| Win rate for a quarter | `mart_win_rate_by_close_quarter.win_rate` | Deals that **closed** in the quarter (by close date): won / (won + lost) |
| Win rate for deals created in a quarter | `mart_win_rate_by_created_cohort.win_rate` | Only when the question says created, cohort or "deals we opened" |
| What we reported at the time | `mart_win_rate_reported_vs_now.win_rate_reported` | As the CRM stood 7 days after the quarter ended |
| Deals won or won amount in a quarter | `mart_win_rate_by_close_quarter` | By close date |
| Stage to stage conversion | `mart_stage_conversion` | Sum the counts across created quarters, then divide |
| Days to win | `mart_deal_velocity.median_days_to_win` | Deals won in the quarter, created to closed, median |
| Open pipeline now | `mart_open_pipeline` | Deals not closed, by current stage |
| Win rate by rep | `mart_owner_win_rate` | Same as the quarter win rate, per rep |

## Win rate (default): `mart_win_rate_by_close_quarter`
Grain: one row per quarter in which deals closed.
- `win_rate` = `deals_won / (deals_won + deals_lost)` for deals whose **close date** is in `quarter`. A share from 0 to 1.
- Open deals are not in it. "Our win rate in Q2" means this column for `quarter = '2026-Q2'`.
- `deals_won`: deals won with a close date in the quarter. "How many deals did we win in Q3" is this column.
- `won_amount`: total amount of those won deals. "Closed-won amount" or "revenue won" in a quarter is this column.

## Win rate by cohort: `mart_win_rate_by_created_cohort`
Grain: one row per quarter in which deals were **created** (`cohort_quarter`).
- `win_rate` = won / (won + lost) among that quarter's created deals that have closed so far.
- `still_open` and `share_still_open`: how unfinished the cohort is. A young cohort's rate will move.
- Use only when the question is about deals created, opened or started in a period.
- Why both exist: the same quarter reads differently under each. Close-quarter answers "how did the
  quarter go"; cohort answers "how good were the deals we opened".

## Reported vs now: `mart_win_rate_reported_vs_now`
Grain: one row per quarter.
- `win_rate_reported`: the close-quarter win rate as the CRM stood at the pipeline review, 7 days after
  the quarter ended, rebuilt from property history. "What did we report for Q2" is this column.
- `win_rate_now`: the same quarter as the CRM says today.
- `change_since_reported`: now minus reported. `deals_that_moved`: deals whose quarter or outcome changed
  after the review (backdated close dates, losses logged late).

## Stage conversion: `mart_stage_conversion`
Grain: one row per **created quarter** and stage step (`from_stage` to the next stage, `to_stage`).
- Counts deals, not stage changes: a deal pushed back and forward again counts once.
- `from_stage` and `to_stage` use the stage labels: Appointment scheduled, Qualified to buy,
  Presentation scheduled, Decision maker bought in, Contract sent, Closed won.
- For all deals (not one cohort): `sum(deals_reached_to) / sum(deals_reached_from)` over the step.
  Never average `conversion_rate` across rows.
- "Of deals that reached Contract sent, what share were won": the step `from_stage = 'Contract sent'`.

## Deal velocity: `mart_deal_velocity`
Grain: one row per quarter in which deals were won (by close date).
- `median_days_to_win`: median days from created to closed, deals won in that quarter.
- For more than one quarter (a year, "so far"), compute the median from `fct_deals.days_to_close`
  where `is_won`. Never take the median or average of the quarterly medians.

## Open pipeline: `mart_open_pipeline`
Grain: one row per open stage, as of the latest export. `stage` uses the stage labels above.
- `open_amount`: total amount of open deals in that stage. `weighted_amount`: amount times the stage's
  default probability.

## Win rate by rep: `mart_owner_win_rate`
Grain: one row per close quarter and rep (`owner_name`). Same definition as the quarter win rate.

## Deals: `fct_deals`
Grain: one row per deal, as the CRM holds it today.
- `was_moved_back`: true if the deal's stage ever went down the pipeline before it closed.
  "How many deals were pushed back" is `count(*) where was_moved_back`.
- `closed_quarter`: by close date; null for open deals. `created_quarter`: by create date.
- `stage_id` uses HubSpot ids (`closedwon`, `closedlost`, `contractsent`, ...), not the labels.
