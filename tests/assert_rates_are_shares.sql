-- Every rate is a share between 0 and 1. Returns the rows that break it.
select 'close_quarter' as mart, quarter as k, win_rate as rate from {{ ref('mart_win_rate_by_close_quarter') }} where win_rate < 0 or win_rate > 1
union all
select 'cohort', cohort_quarter, win_rate from {{ ref('mart_win_rate_by_created_cohort') }} where win_rate < 0 or win_rate > 1
union all
select 'reported', quarter, win_rate_reported from {{ ref('mart_win_rate_reported_vs_now') }} where win_rate_reported < 0 or win_rate_reported > 1
union all
select 'conversion', created_quarter || ' ' || from_stage, conversion_rate from {{ ref('mart_stage_conversion') }} where conversion_rate < 0 or conversion_rate > 1
