-- Required for A1 (contested channel attribution)
-- and A4 (attribution model inconsistency detection).
-- 35-45% of orders have multi-touch journeys.
-- Agent B reads this via staging to resolve
-- contested attributions before firing A1/A4.
-- No is_synthetic filter: table is entirely synthetic by definition.
with journeys as (
    select * from {{ source('client_azure_co', 'synthetic_touchpoint_journey') }}
)
select
    order_id,
    touchpoint_sequence,
    channel,
    touchpoint_date,
    touchpoint_type,
    campaign_id,
    influencer_id,
    touchpoint_sequence = 1     as is_first_touch,
    influencer_id is not null   as is_influencer_touch
from journeys
