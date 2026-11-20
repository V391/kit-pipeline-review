# Sales data models (v1: as most teams first write them)

Warehouse schema: `main`. Quarters are strings like `2026-Q2`.

## fct_deals
Deals from HubSpot.
Columns: deal_id, owner_id, amount, created_at, created_quarter, stage_id, is_closed, is_won, is_lost, closed_at, closed_quarter, days_to_close, furthest_open_stage_order, was_moved_back

## stg_hubspot__owners
Sales reps.
Columns: owner_id, owner_name, team

## mart_win_rate_by_close_quarter
Win rate by quarter.
Columns: quarter, deals_won, deals_lost, win_rate, won_amount

## mart_win_rate_by_created_cohort
Win rate by cohort.
Columns: cohort_quarter, deals_created, deals_won, deals_lost, still_open, win_rate, share_still_open

## mart_win_rate_reported_vs_now
Win rate comparison.
Columns: quarter, won_then, lost_then, win_rate_reported, won_now, lost_now, win_rate_now, change_since_reported, deals_that_moved

## mart_stage_conversion
Stage conversion rates.
Columns: created_quarter, from_stage, to_stage, deals_reached_from, deals_reached_to, conversion_rate

## mart_deal_velocity
Sales cycle.
Columns: quarter, deals_won, median_days_to_win, mean_days_to_win

## mart_open_pipeline
Open pipeline by stage.
Columns: stage, stage_order, open_deals, open_amount, weighted_amount

## mart_owner_win_rate
Win rate by rep.
Columns: quarter, owner_name, deals_won, deals_lost, win_rate

## stg_hubspot__deal_history
Deal property changes.
Columns: deal_id, property, value, changed_at, source
