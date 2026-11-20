-- One row per deal and stage it ever reached, with the first time it got there.
-- A deal pushed back (contract sent -> presentation) and forward again still reached each stage
-- once: conversion counts deals, not stage changes.
with changes as (
    select h.deal_id, h.value as stage_id, h.changed_at
    from {{ ref('stg_hubspot__deal_history') }} as h
    where h.property = 'dealstage'
)

select
    c.deal_id,
    c.stage_id,
    s.stage_order,
    s.is_closed,
    s.is_won,
    min(c.changed_at) as first_reached_at
from changes as c
join {{ ref('stg_hubspot__pipeline_stages') }} as s using (stage_id)
group by 1, 2, 3, 4, 5
