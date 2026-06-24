with orders as (
    select * from {{ ref('stg_shopify_orders') }}
),

refunds as (
    select * from {{ ref('stg_shopify_refunds') }}
),

refund_amounts as (
    select
        order_id,
        count(*) as refund_count
    from refunds
    group by order_id
)

select
    o.order_date,
    count(distinct o.order_id)              as order_count,
    sum(o.gross_revenue)                    as gross_sales,
    sum(o.total_discounts)                  as total_discounts,
    sum(o.total_shipping)                   as shipping_revenue,
    count(distinct r.order_id)              as refunded_order_count,
    sum(o.gross_revenue) - sum(o.total_discounts)
                                            as net_sales_before_returns,
    sum(case when o.source_channel = 'pos'
        then o.gross_revenue else 0 end)    as pos_revenue,
    sum(case when o.tags ilike '%wholesale%'
        then o.gross_revenue else 0 end)    as b2b_revenue,
    -- is_synthetic passed THROUGH from stg_shopify_orders (already RULE-3 filtered
    -- upstream — not re-derived, not re-filtered here). Date-grain aggregate, so
    -- bool_and = true only when every order on that date is synthetic.
    bool_and(o.is_synthetic)                as is_synthetic

from orders o
left join refund_amounts r on o.order_id::text = r.order_id::text
group by o.order_date
order by o.order_date desc
