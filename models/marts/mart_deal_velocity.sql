-- Deal velocity: days from created to closed, for deals WON, by the quarter they closed.
-- Median, not mean: a few long deals would pull a mean far off. Grain: one row per close quarter.
select
    closed_quarter                                                  as quarter,
    count(*)                                                        as deals_won,
    percentile_cont(0.5) within group (order by days_to_close)      as median_days_to_win,
    round(avg(days_to_close), 1)                                    as mean_days_to_win
from {{ ref('fct_deals') }}
where is_won
group by 1
