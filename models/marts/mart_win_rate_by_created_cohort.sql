-- Win rate, definition B (cohort): of the deals CREATED in the quarter, the share won so far.
-- won / (won + lost) among that cohort's closed deals; still_open shows how unfinished the cohort is,
-- so a young cohort's rate is read with care. Grain: one row per created quarter.
select
    created_quarter                                      as cohort_quarter,
    count(*)                                             as deals_created,
    sum(case when is_won then 1 else 0 end)                       as deals_won,
    sum(case when is_lost then 1 else 0 end)                      as deals_lost,
    sum(case when not is_closed then 1 else 0 end)                as still_open,
    round(1.0 * sum(case when is_won then 1 else 0 end) / nullif(sum(case when is_closed then 1 else 0 end), 0), 4) as win_rate,
    round(1.0 * sum(case when not is_closed then 1 else 0 end) / count(*), 4)                              as share_still_open
from {{ ref('fct_deals') }}
group by 1
