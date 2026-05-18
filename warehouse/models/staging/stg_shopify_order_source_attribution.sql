with orders as (
    select * from {{ source('client_azure_co', 'shopify_orders') }}
)

select
    id as order_id,
    source_name,
    app_id,
    tags,

    case
        when source_name = 'web'           then 'shopify_web'
        when source_name = 'pos'           then 'shopify_pos'
        when source_name = 'draft_orders'  then 'shopify_draft'
        when source_name = 'recharge'      then 'recharge'
        when source_name = 'tiktok'        then 'tiktok_shop'
        when source_name = 'wholesale'     then 'wholesale_portal'
        when tags ilike '%wholesale%'      then 'wholesale_portal'
        when tags ilike '%b2b%'            then 'wholesale_portal'
        when tags ilike '%subscription%'   then 'recharge_likely'
        when app_id is not null            then 'unknown_app_' || app_id::text
        else                               'unclassified'
    end as order_source_system,

    case
        when source_name in ('web', 'pos', 'draft_orders') then 'high'
        when source_name in ('recharge', 'tiktok')         then 'high'
        when tags ilike '%wholesale%'                       then 'medium'
        when tags ilike '%subscription%'                    then 'medium'
        when app_id is not null                             then 'low'
        else                                                'low'
    end as attribution_confidence,

    case
        when source_name in ('web', 'pos', 'draft_orders') then true
        else false
    end as has_dedicated_connector

from orders
