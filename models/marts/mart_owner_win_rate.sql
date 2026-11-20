-- Win rate (definition A) by owner and close quarter. Grain: one row per owner and quarter.
select
    d.closed_quarter                                     as quarter,
    o.owner_name,
    sum(case when d.is_won then 1 else 0 end)                     as deals_won,
    sum(case when d.is_lost then 1 else 0 end)                    as deals_lost,
    round(1.0 * sum(case when d.is_won then 1 else 0 end) / count(*), 4) as win_rate
from {{ ref('fct_deals') }} as d
join {{ ref('stg_hubspot__owners') }} as o using (owner_id)
where d.is_closed
group by 1, 2
