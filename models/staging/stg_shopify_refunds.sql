with refunds as (
    select * from {{ source('shopify', 'shopify_order_refunds') }}
)

select
    id                                      as refund_id,
    order_id,
    cast(created_at as timestamp)           as refunded_at,
    cast(created_at as date)               as refund_date,
    note                                    as refund_note,
    restock

from refunds