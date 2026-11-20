-- Open pipeline as of the export: deals not yet closed, by their current stage.
-- weighted_amount uses the stage's default probability. Grain: one row per open stage.
select
    s.stage_label                                  as stage,
    s.stage_order,
    count(d.deal_id)                               as open_deals,
    coalesce(sum(d.amount), 0)                     as open_amount,
    round(coalesce(sum(d.amount * s.probability), 0), 2) as weighted_amount
from {{ ref('stg_hubspot__pipeline_stages') }} as s
left join {{ ref('fct_deals') }} as d on d.stage_id = s.stage_id
where not s.is_closed
group by 1, 2
