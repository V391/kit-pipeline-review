-- Every change to a deal's stage or close date, with when the change was made in the CRM.
-- changed_at is when someone edited it, not the date the edit claims (a backdated close date
-- is changed today to a value in the past).
select
    deal_id,
    property,
    value,
    "timestamp" as changed_at,
    source
from {{ ref('hubspot_deal_property_history') }}
where property in ('dealstage', 'closedate')
