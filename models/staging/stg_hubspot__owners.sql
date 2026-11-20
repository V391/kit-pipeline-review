select owner_id, owner_name, team
from {{ ref('hubspot_owners') }}
