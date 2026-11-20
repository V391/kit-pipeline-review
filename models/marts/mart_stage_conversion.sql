-- Stage conversion: of the deals that ever reached a stage, the share that ever reached the next
-- one (closed won after contract sent). Counts deals, not stage changes, so a deal pushed back
-- and forward again counts once. Grain: one row per created quarter and stage step.
with reached as (
    select r.deal_id, r.stage_order, d.created_quarter
    from {{ ref('int_deal_stages_reached') }} as r
    join {{ ref('fct_deals') }} as d using (deal_id)
    where r.stage_id <> 'closedlost'
),

steps as (
    select stage_id as from_stage_id, stage_label as from_stage, stage_order as from_order,
           lead(stage_id) over (order by stage_order) as to_stage_id,
           lead(stage_label) over (order by stage_order) as to_stage
    from {{ ref('stg_hubspot__pipeline_stages') }}
    where stage_id <> 'closedlost'
)

select
    f.created_quarter,
    s.from_stage,
    s.to_stage,
    count(distinct f.deal_id)                                         as deals_reached_from,
    count(distinct t.deal_id)                                         as deals_reached_to,
    round(1.0 * count(distinct t.deal_id) / count(distinct f.deal_id), 4) as conversion_rate
from steps as s
join reached as f on f.stage_order = s.from_order
left join reached as t on t.deal_id = f.deal_id and t.stage_order = s.from_order + 1
where s.to_stage_id is not null
group by 1, 2, 3, s.from_order
