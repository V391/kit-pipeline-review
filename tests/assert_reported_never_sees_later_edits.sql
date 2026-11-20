-- What a quarter's review "knew" must come only from edits made before the review.
-- Returns any deal whose state at a review rests on a change made after it.
select t.quarter, t.deal_id
from {{ ref('int_deal_state_at_quarter_review') }} as t
join {{ ref('stg_hubspot__deal_history') }} as h
  on h.deal_id = t.deal_id and h.property = 'dealstage' and h.value = t.stage_id_then
group by 1, 2, t.reviewed_at
having min(h.changed_at) > t.reviewed_at
