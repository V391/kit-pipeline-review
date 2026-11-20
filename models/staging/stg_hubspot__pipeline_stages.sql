select
    stage_id,
    label                                  as stage_label,
    display_order                          as stage_order,
    probability,
    stage_id in ('closedwon', 'closedlost') as is_closed,
    stage_id = 'closedwon'                  as is_won
from {{ ref('hubspot_pipeline_stages') }}
