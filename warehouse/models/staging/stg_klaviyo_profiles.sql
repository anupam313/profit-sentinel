-- Klaviyo profiles staging model.
-- Source: client_azure_co.shopify_customers (9,509 rows).
-- NOTE: The seed's klaviyo_profiles table (18,200 rows including non-purchasers)
-- was not properly persisted — the Airbyte-format table pre-existed with different
-- schema, so the seed's custom columns (profile_id, signup_source, etc.) were lost.
-- This model sources from shopify_customers as the best available customer identifier.
-- Non-purchaser subscribers (email-only) are not recoverable without re-seeding.
--
-- sunset_eligible: uses last_order_date as proxy for email engagement recency
-- (email event profile_ids are UUIDs that do not join to Shopify customer IDs).
with customers as (
    select
        id::text                                                                as profile_id,
        email,
        created_at,
        total_spent                                                             as cumulative_spend,
        orders_count                                                            as total_order_count
    from {{ source('client_azure_co', 'shopify_customers') }}
    where id is not null
),

order_dates as (
    select
        customer_id::text                                                       as profile_id,
        min(order_date)                                                         as first_order_date,
        max(order_date)                                                         as last_order_date
    from {{ ref('stg_shopify_orders') }}
    where not is_cancelled
    group by customer_id
)

select
    c.profile_id,
    c.email,
    c.created_at,
    c.total_order_count,
    c.cumulative_spend,

    -- vip_status: high-value customer flag used by Agent A VIP alert suppression
    (c.cumulative_spend > 500 or c.total_order_count >= 5)                     as vip_status,

    -- sunset_eligible: proxy via last order date; true email engagement recency
    -- requires a profile_id join to stg_klaviyo_email_events which is not possible
    -- with the current data — Shopify customer IDs (numeric) do not match Klaviyo
    -- profile UUIDs in email events.
    (od.last_order_date < current_date - interval '180 days'
        or od.last_order_date is null)                                          as sunset_eligible,

    -- loyalty_tier derived from cumulative lifetime spend
    case
        when c.cumulative_spend >= 1500 then 'platinum'
        when c.cumulative_spend >= 500  then 'gold'
        when c.cumulative_spend >= 100  then 'silver'
        else                                 'bronze'
    end                                                                         as loyalty_tier,

    true                                                                        as is_synthetic,

    od.first_order_date,
    od.last_order_date

from customers c
left join order_dates od on c.profile_id = od.profile_id
