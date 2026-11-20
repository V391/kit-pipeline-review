-- Grain: one row per deal, as the CRM holds it today.
with deals as (
    select * from {{ ref('stg_hubspot__deals') }}
),

stages as (
    select * from {{ ref('stg_hubspot__pipeline_stages') }}
),

furthest as (
    select deal_id, max(case when not is_closed then stage_order end) as furthest_open_stage_order
    from {{ ref('int_deal_stages_reached') }}
    group by 1
),

moved_back as (
    -- A deal whose stage ever went down the pipeline before closing.
    select deal_id, count(*) > 0 as was_moved_back
    from (
        select h.deal_id, s.stage_order,
               lag(s.stage_order) over (partition by h.deal_id order by h.changed_at) as prev_order
        from {{ ref('stg_hubspot__deal_history') }} as h
        join stages as s on s.stage_id = h.value
        where h.property = 'dealstage' and not s.is_closed
    ) as ordered
    where stage_order < prev_order
    group by 1
)

select
    d.deal_id,
    d.owner_id,
    d.amount,
    d.created_at,
    {{ quarter_label('d.created_at') }}                           as created_quarter,
    d.current_stage_id                                            as stage_id,
    s.is_closed,
    s.is_won,
    s.is_closed and not s.is_won                                  as is_lost,
    case when s.is_closed then d.current_close_at end             as closed_at,
    case when s.is_closed then {{ quarter_label('d.current_close_at') }} end as closed_quarter,
    case when s.is_closed then {{ days_between('d.created_at', 'd.current_close_at') }} end as days_to_close,
    f.furthest_open_stage_order,
    coalesce(m.was_moved_back, false)                             as was_moved_back
from deals as d
join stages as s on s.stage_id = d.current_stage_id
left join furthest as f using (deal_id)
left join moved_back as m using (deal_id)
