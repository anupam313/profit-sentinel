with orders as (
    select * from {{ ref('stg_shopify_orders') }}
),

attribution as (
    select * from {{ ref('stg_shopify_order_source_attribution') }}
)

select
    o.order_date,
    count(distinct o.order_id)                          as order_count,
    sum(o.gross_revenue)                                as gross_revenue,
    sum(o.total_discounts)                              as total_discounts,
    sum(o.total_shipping)                               as shipping_revenue,
    sum(o.total_tax)                                    as total_tax,
    sum(o.gross_revenue) - sum(o.total_discounts)       as net_revenue,
    avg(o.total_price)                                  as average_order_value,
    count(distinct case
        when a.has_dedicated_connector = true
        then o.order_id end) * 100.0
        / nullif(count(distinct o.order_id), 0)         as data_completeness_pct

from orders o
left join attribution a on o.order_id::text = a.order_id::text
group by o.order_date
order by o.order_date desc