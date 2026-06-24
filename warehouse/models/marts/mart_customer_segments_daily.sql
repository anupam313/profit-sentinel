{{ config(materialized='table') }}

with

date_spine as (
    select generate_series(
        '2024-06-01'::date,
        '2026-05-31'::date,
        interval '1 day'
    )::date as date
),

all_segments as (
    select unnest(array['explorer', 'regular', 'loyalist', 'advocate']) as segment
),

all_date_segments as (
    select d.date, s.segment
    from date_spine d
    cross join all_segments s
),

seg_config as (
    select
        explorer_max_orders,
        regular_max_orders,
        loyalist_max_orders,
        advocate_min_orders
    from public.client_config
    where client_id = '{{ var("client_id") }}'
),

-- Rank all orders per customer chronologically
customer_order_ranked as (
    select
        customer_id,
        order_id,
        order_date,
        row_number() over (
            partition by customer_id
            order by order_date, order_id
        ) as order_seq
    from {{ ref('stg_shopify_orders') }}
    where not coalesce(is_cancelled, false)
),

-- When a customer places multiple orders on the same day, take the highest seq
-- (their segment after ALL orders on that date)
customer_daily_max_seq as (
    select
        customer_id,
        order_date,
        max(order_seq) as max_seq
    from customer_order_ranked
    group by customer_id, order_date
),

-- Compute segment validity windows per customer.
-- A window covers [window_start, window_end) — the period the customer holds
-- their current segment. window_end = next order date, NULL = still in segment.
customer_segment_windows as (
    select
        cds.customer_id,
        cds.order_date                                                  as window_start,
        lead(cds.order_date) over (
            partition by cds.customer_id
            order by cds.order_date
        )                                                               as window_end,
        case
            when cds.max_seq <= sc.explorer_max_orders  then 'explorer'
            when cds.max_seq <= sc.regular_max_orders   then 'regular'
            when cds.max_seq <= sc.loyalist_max_orders  then 'loyalist'
            else                                             'advocate'
        end                                                             as segment
    from customer_daily_max_seq cds
    cross join seg_config sc
),

-- Count customers per segment per date based on their validity window.
-- A customer in window [W_start, W_end) is counted on every spine date in that range.
segment_customer_daily as (
    select
        d.date,
        w.segment,
        count(distinct w.customer_id) as segment_customer_count
    from date_spine d
    inner join customer_segment_windows w
        on  d.date >= w.window_start
        and (w.window_end is null or d.date < w.window_end)
    group by d.date, w.segment
),

-- Net revenue per order (gross revenue minus discounts; before returns)
orders_net as (
    select
        order_id,
        customer_id,
        order_date,
        coalesce(gross_revenue, 0) - coalesce(total_discounts, 0) as net_revenue
    from {{ ref('stg_shopify_orders') }}
    where not coalesce(is_cancelled, false)
),

-- Assign each order to the customer's segment AT the time of the order.
-- Uses the same validity windows so attribution is point-in-time correct.
order_segment as (
    select
        o.order_id,
        o.order_date,
        o.customer_id,
        o.net_revenue,
        w.segment
    from orders_net o
    inner join customer_segment_windows w
        on  o.customer_id  = w.customer_id
        and o.order_date  >= w.window_start
        and (w.window_end is null or o.order_date < w.window_end)
),

-- Daily order count and revenue per segment (used for rolling windows)
daily_segment_stats as (
    select
        order_date  as date,
        segment,
        count(*)         as daily_orders,
        sum(net_revenue) as daily_revenue
    from order_segment
    group by order_date, segment
),

-- Rolling 90d revenue per segment (for segment_pct_of_total_revenue)
rolling_revenue_90d as (
    select
        ads.date,
        ads.segment,
        sum(coalesce(dss.daily_revenue, 0)) over (
            partition by ads.segment
            order by ads.date
            rows between 89 preceding and current row
        ) as revenue_90d
    from all_date_segments ads
    left join daily_segment_stats dss
        on dss.date = ads.date and dss.segment = ads.segment
),

total_revenue_90d as (
    select
        date,
        sum(revenue_90d) as total_rev_90d
    from rolling_revenue_90d
    group by date
),

-- Returns attributed to the segment of the original order at return time
returns_with_segment as (
    select
        lr.return_date,
        os.segment
    from {{ ref('stg_loop_returns') }} lr
    inner join order_segment os
        on os.order_id::text = lr.order_id
),

daily_segment_returns as (
    select
        return_date as date,
        segment,
        count(*)    as daily_returns
    from returns_with_segment
    group by return_date, segment
),

-- Rolling 7d metrics: return rate and AOV per segment
rolling_7d_metrics as (
    select
        ads.date,
        ads.segment,
        sum(coalesce(dsr.daily_returns, 0)) over (
            partition by ads.segment
            order by ads.date
            rows between 6 preceding and current row
        )                                                          as returns_7d,
        sum(coalesce(dss.daily_orders, 0)) over (
            partition by ads.segment
            order by ads.date
            rows between 6 preceding and current row
        )                                                          as orders_7d,
        sum(coalesce(dss.daily_revenue, 0)) over (
            partition by ads.segment
            order by ads.date
            rows between 6 preceding and current row
        )                                                          as revenue_7d
    from all_date_segments ads
    left join daily_segment_returns dsr
        on dsr.date = ads.date and dsr.segment = ads.segment
    left join daily_segment_stats dss
        on dss.date = ads.date and dss.segment = ads.segment
)

select
    ads.date,
    '{{ var("client_id") }}'::text                                     as client_id,
    ads.segment,

    -- Surrogate key for uniqueness testing
    ads.date::text || '|' || '{{ var("client_id") }}' || '|' || ads.segment
                                                                       as segment_key,

    coalesce(scd.segment_customer_count, 0)                            as segment_customer_count,

    -- % of total active customers across all segments on this date
    coalesce(scd.segment_customer_count, 0)::numeric
        / nullif(
            sum(coalesce(scd.segment_customer_count, 0)) over (partition by ads.date),
            0
        )                                                              as segment_pct_of_total_customers,

    -- % of trailing 90-day revenue (revenue attributed to segment at order time)
    coalesce(rr90.revenue_90d, 0)::numeric
        / nullif(tr90.total_rev_90d, 0)                               as segment_pct_of_total_revenue,

    -- segment_avg_roas requires ad-to-customer attribution not available at
    -- segment grain without B-4 (ad set → SKU mapping). Set NULL until B-4.
    null::numeric                                                      as segment_avg_roas,

    -- Return rate: 0.0 (not NULL) when no returns in 7d window
    coalesce(
        r7.returns_7d::numeric / nullif(r7.orders_7d, 0),
        0.0
    )                                                                  as segment_return_rate_7d,

    -- AOV: NULL (not 0.0) when no orders in 7d window — no orders ≠ zero AOV
    case
        when r7.orders_7d > 0 then r7.revenue_7d / r7.orders_7d
        else null
    end                                                                as segment_aov_7d,

    false                                                              as any_source_stale,
    current_timestamp                                                  as data_as_of

from all_date_segments ads
left join segment_customer_daily scd
    on scd.date = ads.date and scd.segment = ads.segment
left join rolling_revenue_90d rr90
    on rr90.date = ads.date and rr90.segment = ads.segment
left join total_revenue_90d tr90
    on tr90.date = ads.date
left join rolling_7d_metrics r7
    on r7.date = ads.date and r7.segment = ads.segment
