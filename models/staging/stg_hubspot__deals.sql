-- One row per deal, as the CRM holds it today (the export). Renamed to plain words; nothing derived.
select
    hs_object_id                          as deal_id,
    dealname                              as deal_name,
    pipeline                              as pipeline_id,
    dealstage                             as current_stage_id,
    amount,
    createdate                            as created_at,
    closedate                             as current_close_at,
    hubspot_owner_id                      as owner_id
from {{ ref('hubspot_deals') }}
