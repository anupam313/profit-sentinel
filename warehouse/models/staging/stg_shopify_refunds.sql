with refunds as (
    select
        *,
        -- is_synthetic DERIVED from the seed isolation predicate (id < 1e12).
        (id < 1000000000000) as is_synthetic
    from {{ source('client_azure_co', 'shopify_order_refunds') }}
)

select
    id                                      as refund_id,
    order_id,
    cast(created_at as timestamp)           as refunded_at,
    cast(created_at as date)               as refund_date,
    note                                    as refund_note,
    restock,
    is_synthetic

from refunds
-- RULE 3 (per-client form): synthetic rows visible only when toggle is on
where (
    is_synthetic = false
    or (select use_synthetic_data from public.client_config
        where client_id = '{{ var("client_id") }}') = true
)
