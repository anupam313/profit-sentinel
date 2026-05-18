-- SKU-level return rate. Agent A uses this to detect return spikes by product.
with sold as (
    select
        sku,
        sum(quantity)           as units_sold,
        sum(gross_line_revenue) as gross_revenue_sold,
        count(distinct order_id) as orders_with_sku
    from {{ ref('stg_shopify_order_line_items') }}
    where sku is not null
    group by sku
),

returned as (
    select
        li.sku,
        sum(li.quantity)                                    as units_returned,
        count(distinct li.return_id)                        as return_count,
        sum(r.refund_amount) / nullif(count(li.line_item_id), 0) as avg_refund_per_return,
        mode() within group (order by li.return_reason_primary) as primary_return_reason,
        mode() within group (order by r.return_lag_segment)     as dominant_lag_segment
    from {{ source('client_azure_co', 'loop_return_line_items') }} li
    inner join {{ ref('stg_loop_returns') }} r on li.return_id = r.return_id
    where li.sku is not null
    group by li.sku
),

costs as (
    -- Most recent active cost record per SKU
    select distinct on (sku)
        sku,
        landed_cost
    from {{ source('client_azure_co', 'sku_cost_master') }}
    where is_synthetic = {{ var('use_synthetic_data', true) }}
    order by sku, effective_from desc
)

select
    s.sku,
    s.units_sold,
    s.gross_revenue_sold,
    s.orders_with_sku,
    coalesce(r.units_returned, 0)                               as units_returned,
    coalesce(r.return_count, 0)                                 as return_count,
    coalesce(r.units_returned, 0) * 100.0
        / nullif(s.units_sold, 0)                               as return_rate_pct,
    r.avg_refund_per_return,
    r.primary_return_reason,
    r.dominant_lag_segment,
    c.landed_cost,
    coalesce(r.units_returned, 0) * coalesce(c.landed_cost, 0) as estimated_return_cost

from sold s
left join returned r  on s.sku = r.sku
left join costs c     on s.sku = c.sku
order by return_rate_pct desc nulls last
