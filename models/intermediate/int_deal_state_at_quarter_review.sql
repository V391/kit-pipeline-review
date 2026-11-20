-- What the CRM said about each deal at each quarter's pipeline review: the stage and close date as
-- they stood `reported_after_days` after the quarter ended. Rebuilt from property history, so a
-- close date backdated later does not leak into what was known at the time.
with quarters as (
    select distinct date_trunc('quarter', cast(value as timestamp)) as quarter_start
    from {{ ref('stg_hubspot__deal_history') }}
    where property = 'closedate'
),

reviews as (
    select
        quarter_start,
        cast(quarter_start + interval '3 months' as timestamp) as next_quarter_start,
        cast(quarter_start + interval '3 months' + interval '{{ var("reported_after_days") }} days' as timestamp) as reviewed_at
    from quarters
),

history as (
    select * from {{ ref('stg_hubspot__deal_history') }}
),

stage_then as (
    select r.quarter_start, h.deal_id, h.value as stage_id,
           row_number() over (partition by r.quarter_start, h.deal_id order by h.changed_at desc) as rn
    from reviews as r
    join history as h on h.property = 'dealstage' and h.changed_at <= r.reviewed_at
),

close_then as (
    select r.quarter_start, h.deal_id, cast(h.value as timestamp) as close_at,
           row_number() over (partition by r.quarter_start, h.deal_id order by h.changed_at desc) as rn
    from reviews as r
    join history as h on h.property = 'closedate' and h.changed_at <= r.reviewed_at
)

select
    r.quarter_start,
    {{ quarter_label('r.quarter_start') }} as quarter,
    r.reviewed_at,
    s.deal_id,
    s.stage_id                             as stage_id_then,
    c.close_at                             as close_at_then,
    s.stage_id in ('closedwon', 'closedlost')
        and c.close_at >= r.quarter_start
        and c.close_at <  r.next_quarter_start as closed_in_quarter_then
from reviews as r
join stage_then as s on s.quarter_start = r.quarter_start and s.rn = 1
left join close_then as c on c.quarter_start = r.quarter_start and c.deal_id = s.deal_id and c.rn = 1
