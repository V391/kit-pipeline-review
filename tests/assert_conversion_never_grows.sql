-- A deal moved back and forward again is counted once per stage: no step can have more deals
-- reaching the next stage than reached this one.
select * from {{ ref('mart_stage_conversion') }} where deals_reached_to > deals_reached_from
