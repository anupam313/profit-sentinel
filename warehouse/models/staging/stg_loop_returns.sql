with returns as (
    select * from {{ source('client_azure_co', 'loop_returns') }}
),
line_items as (
    select * from {{ source('client_azure_co', 'loop_return_line_items') }}
)
select
    r.return_id,
    r.order_id,
    r.customer_id,
    r.return_initiated_at::date             as return_date,
    r.return_initiated_at,
    r.return_received_at,
    r.return_status,
    r.refund_amount,
    r.exchange_requested,
    r.payment_method,
    r.return_lag_segment,
    r.product_id,
    count(li.line_item_id)                  as line_item_count,
    string_agg(distinct li.sku, ', ')       as skus_returned,
    min(li.return_reason_primary)           as return_reason,
    string_agg(distinct li.return_reason_primary, ', ') as return_reasons
from returns r
left join line_items li on r.return_id = li.return_id
group by
    r.return_id, r.order_id, r.customer_id,
    r.return_initiated_at, r.return_received_at,
    r.return_status, r.refund_amount, r.exchange_requested,
    r.payment_method, r.return_lag_segment, r.product_id
