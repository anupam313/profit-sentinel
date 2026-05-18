-- meta_ad_performance stores all numeric fields as text (Airbyte Meta connector behavior).
-- Casts here are necessary because python_transformer.py is not yet built.
-- purchase_roas is jsonb: [{"action_type": "omni_purchase", "value": "3.14"}]
with meta as (
    select * from {{ source('client_azure_co', 'meta_ad_performance') }}
    where is_synthetic = {{ var('use_synthetic_data', true) }}
)
select
    date_start::date                                            as date,
    campaign_id,
    campaign_name,
    adset_id,
    adset_name,
    ad_id,
    ad_name,
    attribution_setting,
    spend::numeric                                              as spend,
    impressions::numeric                                        as impressions,
    clicks::numeric                                             as clicks,
    nullif(ctr, '')::numeric                                    as ctr,
    nullif(cpm, '')::numeric                                    as cpm,
    nullif(cpc, '')::numeric                                    as cpc,
    nullif(reach, '')::numeric                                  as reach,
    nullif(frequency, '')::numeric                              as frequency,
    (purchase_roas -> 0 ->> 'value')::numeric                  as purchase_roas,
    stored_before_retention_limit,
    _airbyte_extracted_at
from meta
