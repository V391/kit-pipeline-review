-- The same quarter's win rate (definition A), as the pipeline review reported it and as the CRM says
-- today. The gap is the backdated and late edits made after the review. Grain: one row per quarter.
with then_ as (
    select
        quarter,
        sum(case when closed_in_quarter_then and stage_id_then = 'closedwon' then 1 else 0 end)  as won_then,
        sum(case when closed_in_quarter_then and stage_id_then = 'closedlost' then 1 else 0 end) as lost_then
    from {{ ref('int_deal_state_at_quarter_review') }}
    group by 1
),

now_ as (
    select quarter, deals_won as won_now, deals_lost as lost_now, win_rate as win_rate_now
    from {{ ref('mart_win_rate_by_close_quarter') }}
),

moved as (
    -- Deals counted in the quarter at the review but not now, or now but not then.
    select t.quarter, count(*) as deals_that_moved
    from {{ ref('int_deal_state_at_quarter_review') }} as t
    left join {{ ref('fct_deals') }} as d using (deal_id)
    where t.closed_in_quarter_then <> coalesce(d.closed_quarter = t.quarter, false)
       or (t.closed_in_quarter_then and t.stage_id_then <> d.stage_id)
    group by 1
)

select
    n.quarter,
    t.won_then,
    t.lost_then,
    round(1.0 * t.won_then / nullif(t.won_then + t.lost_then, 0), 4) as win_rate_reported,
    n.won_now,
    n.lost_now,
    n.win_rate_now,
    round(n.win_rate_now - 1.0 * t.won_then / nullif(t.won_then + t.lost_then, 0), 4) as change_since_reported,
    coalesce(m.deals_that_moved, 0) as deals_that_moved
from now_ as n
left join then_ as t using (quarter)
left join moved as m using (quarter)
