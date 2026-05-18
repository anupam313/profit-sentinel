with tiktok as (
    select * from {{ source('client_azure_co', 'tiktok_ad_performance') }}
)
select
    date,
    campaign_id,
    campaign_type,
    spend,
    impressions,
    clicks,
    purchases,
    revenue                             as attributed_revenue,
    cpm,
    ctr,
    roas,
    frequency,
    dq_score,
    _airbyte_extracted_at
from tiktok
