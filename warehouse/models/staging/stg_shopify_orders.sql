with orders as (
    select * from {{ source('shopify', 'shopify_orders') }}
)

select
    id                                              as order_id,
    cast(created_at as timestamp)                   as created_at,
    cast(created_at as date)                        as order_date,
    order_number,
    coalesce(
        cast(total_line_items_price as numeric), 0
    )                                               as gross_revenue,
    coalesce(
        cast(total_discounts as numeric), 0
    )                                               as total_discounts,
    coalesce(
        cast(
            total_shipping_price_set::jsonb
            -> 'shop_money' ->> 'amount'
        as numeric), 0
    )                                               as total_shipping,
    coalesce(
        cast(total_tax as numeric), 0
    )                                               as total_tax,
    coalesce(
        cast(total_price as numeric), 0
    )                                               as total_price,
    financial_status,
    fulfillment_status,
    source_name                                     as source_channel,
    (customer::jsonb ->> 'id')::bigint              as customer_id,
    tags,
    cancelled_at,
    cancelled_at is not null                        as is_cancelled,
    email

from orders
where cancelled_at is null
  and financial_status != 'voided'
