with orders as (
    select * from {{ ref('stg_shopify_orders') }}
),

attribution as (
    select * from {{ ref('stg_shopify_order_source_attribution') }}
),

returns as (
    select
        return_date,
        count(*)            as return_count,
        sum(refund_amount)  as return_refund_total
    from {{ ref('stg_loop_returns') }}
    group by return_date
),

daily_orders as (
    select
        o.order_date,
        count(distinct o.order_id)                                      as order_count,
        sum(o.gross_revenue)                                            as gross_revenue,
        sum(o.total_discounts)                                          as total_discounts,
        sum(o.total_shipping)                                           as shipping_revenue,
        sum(o.total_tax)                                                as total_tax,
        sum(o.gross_revenue) - sum(o.total_discounts)                   as net_revenue_before_returns,
        avg(o.total_price)                                              as average_order_value,
        count(distinct case when a.has_dedicated_connector = true
            then o.order_id end) * 100.0
            / nullif(count(distinct o.order_id), 0)                     as data_completeness_pct
    from orders o
    left join attribution a on o.order_id::text = a.order_id::text
    group by o.order_date
)

select
    d.order_date,
    d.order_count,
    d.gross_revenue,
    d.total_discounts,
    d.shipping_revenue,
    d.total_tax,
    d.net_revenue_before_returns,
    coalesce(r.return_refund_total, 0)                                  as return_refund_total,
    d.net_revenue_before_returns - coalesce(r.return_refund_total, 0)   as net_revenue,
    d.average_order_value,
    coalesce(r.return_count, 0)                                         as return_count,
    coalesce(r.return_count, 0) * 100.0
        / nullif(d.order_count, 0)                                      as return_rate_pct,
    d.data_completeness_pct

from daily_orders d
left join returns r on d.order_date = r.return_date
order by d.order_date desc
