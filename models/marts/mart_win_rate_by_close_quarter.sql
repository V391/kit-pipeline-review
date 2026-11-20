-- Win rate, definition A (the default): of the deals that CLOSED in the quarter (by close date),
-- the share that were won. won / (won + lost). Open deals are not in it.
-- Grain: one row per quarter.
select
    closed_quarter                                       as quarter,
    sum(case when is_won then 1 else 0 end)                       as deals_won,
    sum(case when is_lost then 1 else 0 end)                      as deals_lost,
    round(1.0 * sum(case when is_won then 1 else 0 end) / nullif(count(*), 0), 4) as win_rate,
    sum(case when is_won then amount end)                    as won_amount
from {{ ref('fct_deals') }}
where is_closed
group by 1
