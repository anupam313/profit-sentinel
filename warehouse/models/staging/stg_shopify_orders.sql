with orders as (
    select
        *,
        -- is_synthetic DERIVED from the seed isolation predicate. Raw shopify_*
        -- carries no is_synthetic column (DEBT-006); seed_shopify isolates its
        -- rows with id < 1e12, so that predicate IS the synthetic flag.
        (id < 1000000000000) as is_synthetic
    from {{ source('client_azure_co', 'shopify_orders') }}
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
    email,
    discount_codes,                                 -- pass-through for mart_causal re-route (Phase C)
    is_synthetic

from orders
where cancelled_at is null
  and financial_status != 'voided'
  -- RULE 3 (per-client form): synthetic rows are exposed only when THIS client's
  -- toggle is on. Never the connector-staging `= var('use_synthetic_data')` form.
  and (
      is_synthetic = false
      or (select use_synthetic_data from public.client_config
          where client_id = '{{ var("client_id") }}') = true
  )
