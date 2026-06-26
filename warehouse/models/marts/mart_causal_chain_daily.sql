-- Primary Agent A scan table. One row per date.
-- Prior-year baseline uses 52-week rule (364 days = same weekday, year-1).
-- Columns prefixed py_ = prior year. Index columns = current / prior_year - 1.
with client_margin as (
    select blended_gross_margin_pct
    from public.client_config
    where client_id = '{{ var("client_id") }}'
),

cross_source as (
    select * from {{ ref('mart_cross_source_daily') }}
),

-- Prior year window: same weekday 52 weeks back
prior_year as (
    select
        date + interval '364 days'                          as current_date_equiv,
        gross_revenue                                       as py_gross_revenue,
        net_revenue                                         as py_net_revenue,
        order_count                                         as py_order_count,
        average_order_value                                 as py_aov,
        total_sessions                                      as py_sessions,
        avg_cvr                                             as py_cvr,
        total_ad_spend                                      as py_ad_spend,
        blended_roas                                        as py_blended_roas,
        ticket_count                                        as py_ticket_count,
        return_count                                        as py_return_count,
        sentry_error_count                                  as py_sentry_errors,
        checkout_error_count                                as py_checkout_errors
    from cross_source
),

-- Daily Meta aggregates for rolling window computation
meta_daily as (
    select
        date,
        avg(cpm) as cpm,
        avg(ctr) as ctr
    from {{ ref('stg_meta_ad_performance') }}
    group by date
),

-- Rolling 7-day Meta CPM and CTR — current window and prior window
meta_rolling as (
    select
        date,
        avg(cpm) over (order by date rows between 6 preceding and current row)   as meta_cpm_7d_avg,
        avg(cpm) over (order by date rows between 13 preceding and 7 preceding)  as meta_cpm_prior_7d_avg,
        avg(ctr) over (order by date rows between 6 preceding and current row)   as meta_ctr_7d_avg,
        avg(ctr) over (order by date rows between 13 preceding and 7 preceding)  as meta_ctr_prior_7d_avg
    from meta_daily
),

-- Daily sizing-complaint counts from Gorgias
-- C1 sizing signal sourced from the REAL Gorgias tags (jsonb array of {name}),
-- not the deprecated last_ticket_reason scalar. A ticket counts ONCE if ANY of
-- its tags is in the sizing-tag set below (quality tags excluded by design).
sizing_daily as (
    select
        ticket_date                                                              as date,
        sum(case when exists (
                select 1
                from jsonb_array_elements(tags) as e(elem)
                where elem ->> 'name' in (
                    'too small', 'too big', 'runs small', 'wrong size', 'fit',
                    'sizing', 'sizing_issue', 'sizing_issue_tops',
                    'runs small -- tops', 'fit issue -- tops', 'outerwear fit',
                    'layering issue'
                )
            ) then 1 else 0 end)                                                 as sizing_count,
        count(*)                                                                 as total_count
    from {{ ref('stg_gorgias_tickets') }}
    group by ticket_date
),

-- Rolling 7-day sizing complaint rate and prior-7d rate for velocity
sizing_rolling as (
    select
        date,
        sum(sizing_count) over w7 * 1.0
            / nullif(sum(total_count) over w7, 0)                              as sizing_complaint_rate_7d,
        sum(sizing_count) over w_prior * 1.0
            / nullif(sum(total_count) over w_prior, 0)                         as sizing_complaint_rate_prior_7d
    from sizing_daily
    window
        w7      as (order by date rows between 6 preceding and current row),
        w_prior as (order by date rows between 13 preceding and 7 preceding)
),

-- Loop return signals per day — lifestyle_change segment count
-- 'lifestyle_change' matches the exact value seeded into return_lag_segment
loop_signals as (
    select
        return_date                                                              as date,
        count(*) filter (where return_lag_segment = 'lifestyle_change')        as loop_lifestyle_change_count
    from {{ ref('stg_loop_returns') }}
    group by return_date
),

-- ── Contribution Margin (Agent A: D1 signal) ──────────────────────────────
contribution_margin as (
    select
        date,
        case
            when net_revenue > 0
            then (net_revenue * (select blended_gross_margin_pct from client_margin)
                  - total_ad_spend) / net_revenue * 100
            else null
        end                                                                      as contribution_margin_pct
    from cross_source
),

contribution_margin_with_lag as (
    select
        date,
        contribution_margin_pct,
        lag(contribution_margin_pct, 7) over (order by date)                    as cm_prior_7d
    from contribution_margin
),

-- ── 3a: avg_days_to_refund ────────────────────────────────────────────────────
-- Source: stg_loop_returns (stg_loop_refunds does not exist — loop_returns is
-- the canonical refund table). return_received_at = processing/settled date.
-- Validation target: avg 6–8 days.
loop_refund_lag as (
    select
        return_initiated_at::date                                               as date,
        avg(
            extract(epoch from (return_received_at - return_initiated_at))
            / 86400.0
        )                                                                       as avg_days_to_refund
    from {{ ref('stg_loop_returns') }}
    where return_initiated_at is not null
      and return_received_at  is not null
    group by 1
),

-- ── 3b: aov_7d ───────────────────────────────────────────────────────────────
-- 7-day rolling average order value. Validation target: $142–$158.
aov_rolling as (
    select
        date,
        avg(average_order_value) over (
            order by date rows between 6 preceding and current row
        )                                                                       as aov_7d
    from (
        select order_date as date, avg(total_price) as average_order_value
        from {{ ref('stg_shopify_orders') }}
        group by 1
    ) daily_aov
),

-- ── 3c: effective_open_rate_7d ────────────────────────────────────────────────
-- Source: stg_klaviyo_email_events (not stg_klaviyo_flows — that model is a
-- per-flow aggregate with no date column).
-- open_rate per day = sum(effective_opens) / count(emails) for flow emails only.
-- ios_mpp_multiplier read from client_config — never hardcode 0.65.
-- Validation target: 0.156–0.182 (reported 0.24–0.28 × 0.65).
klaviyo_open_rate_daily as (
    select
        event_date                                                              as date,
        sum(effective_opens)::numeric / nullif(count(*), 0)                   as daily_open_rate
    from {{ ref('stg_klaviyo_email_events') }}
    where flow_id is not null
    group by 1
),
klaviyo_open_rate_rolling as (
    select
        date,
        avg(daily_open_rate) over (
            order by date rows between 6 preceding and current row
        ) * (
            select ios_mpp_multiplier
            from public.client_config
            where client_id = '{{ var("client_id") }}'
        )                                                                       as effective_open_rate_7d
    from klaviyo_open_rate_daily
),

-- ── 3d: vip_purchase_gap_days ────────────────────────────────────────────────
-- Inter-purchase gap in days between consecutive VIP orders.
-- First VIP order per customer excluded (no prior order to compare).
-- NULL on dates with no VIP repeat purchases.
-- Join: o.customer_id::text = p.profile_id (stg_klaviyo_profiles uses profile_id).
-- VIP flag: p.vip_status (not is_vip — stg_klaviyo_profiles column name).
-- LAG computed per-row in subquery, then averaged per order_date.
vip_inter_purchase as (
    select
        order_date                                                              as date,
        avg(days_since_prior_purchase)                                          as avg_inter_purchase_days
    from (
        select
            o.order_date,
            extract(epoch from (
                o.created_at - lag(o.created_at) over (
                    partition by o.customer_id
                    order by o.created_at
                )
            )) / 86400.0                                                        as days_since_prior_purchase
        from {{ ref('stg_shopify_orders') }} o
        inner join {{ ref('stg_klaviyo_profiles') }} p
            on o.customer_id::text = p.profile_id
        where p.vip_status = true
          and o.created_at is not null
    ) gaps
    where days_since_prior_purchase is not null
    group by 1
),
vip_purchase_gap as (
    select
        date,
        avg(avg_inter_purchase_days) over (
            order by date rows between 6 preceding and current row
        )                                                                       as vip_purchase_gap_days
    from vip_inter_purchase
),

-- ── 3e: ga4_pdp_bounce_rate ──────────────────────────────────────────────────
-- TODO: requires stg_ga4_pages staging model with page_path column.
-- No ga4_pages source table exists in client_azure_co schema (sources declared
-- in all_sources.yml: ga4_sessions_daily, ga4_funnel_daily, ga4_checkout_errors).
-- Column set to NULL on all dates. Will populate when GA4 page-level data is
-- available. Validation: count(ga4_pdp_bounce_rate) = 0 expected (correct).

-- ── 3f: send_frequency_7d ────────────────────────────────────────────────────
-- Source: stg_klaviyo_email_events (not stg_klaviyo_flows — that model has no
-- date column and no emails_sent column; it is a per-flow lifetime aggregate).
-- daily_sends = count of flow emails dispatched per day.
-- Validation target: > 0.
send_frequency_rolling as (
    select
        date,
        avg(daily_sends) over (
            order by date rows between 6 preceding and current row
        )                                                                       as send_frequency_7d
    from (
        select event_date as date, count(*) as daily_sends
        from {{ ref('stg_klaviyo_email_events') }}
        where flow_id is not null
        group by 1
    ) s
),

-- ── 3g: new_customer_rate_7d and blended_cac_7d ──────────────────────────────
-- customer_order_index not in stg_shopify_orders — derived with row_number().
-- blended_cac_7d: date-level join only. No order-level attribution.
-- Read as 7d rolling average only. Single-day values are meaningless.
-- Validation: new_customer_rate_7d target 0.65–0.70. blended_cac_7d target $15–25.
customer_order_index_cte as (
    select
        order_id,
        order_date,
        customer_id,
        row_number() over (
            partition by customer_id order by order_date, order_id
        )                                                                       as customer_order_index
    from {{ ref('stg_shopify_orders') }}
),
new_customer_daily as (
    select
        order_date                                                              as date,
        count(*)                                                                as total_orders,
        count(*) filter (where customer_order_index = 1)                       as new_customer_orders
    from customer_order_index_cte
    group by 1
),
cac_ad_spend_daily as (
    select
        coalesce(m.date, t.date)                                               as date,
        coalesce(m.meta_spend, 0) + coalesce(t.tiktok_spend, 0)               as total_ad_spend
    from (
        select date, sum(spend) as meta_spend
        from {{ ref('stg_meta_ad_performance') }}
        group by 1
    ) m
    full outer join (
        select date, sum(spend) as tiktok_spend
        from {{ ref('stg_tiktok_ad_performance') }}
        group by 1
    ) t on m.date = t.date
),
cac_rolling as (
    select
        nc.date,
        avg(nc.new_customer_orders::numeric / nullif(nc.total_orders, 0)) over (
            order by nc.date rows between 6 preceding and current row
        )                                                                       as new_customer_rate_7d,
        sum(coalesce(ad.total_ad_spend, 0)) over (
            order by nc.date rows between 6 preceding and current row
        ) / nullif(
            sum(nc.new_customer_orders) over (
                order by nc.date rows between 6 preceding and current row
            ), 0
        )                                                                       as blended_cac_7d
    from new_customer_daily nc
    left join cac_ad_spend_daily ad on nc.date = ad.date
),

-- ── 3h: mobile/desktop checkout completion rates ──────────────────────────────
-- TODO: requires stg_ga4_devices staging model with device_category column.
-- No ga4_devices source table exists in client_azure_co schema.
-- Both columns set to NULL on all dates. GA4 has 0 rows in synthetic data anyway.
-- Validation: 0 populated rows expected (correct for both columns).

-- ── 3i: post_purchase_flow_revenue_7d ────────────────────────────────────────
-- Flow identification: join stg_klaviyo_email_events (event_date, flow_id,
-- revenue_attributed) to stg_klaviyo_flows (flow_id, flow_type, flow_name).
-- Filters on flow_type = 'post_purchase' OR name pattern where type is NULL.
-- 9 of 14 flows are unnamed (A-7h seed limitation) — if revenue = 0, that is
-- expected. Validation: document % of total klaviyo_revenue captured.
post_purchase_rolling as (
    select
        date,
        sum(post_purchase_revenue) over (
            order by date rows between 6 preceding and current row
        )                                                                       as post_purchase_flow_revenue_7d
    from (
        select
            e.event_date                                                        as date,
            sum(e.revenue_attributed) filter (
                where f.flow_type = 'post_purchase'
                   or lower(f.flow_name) like '%post%purchase%'
                   or lower(f.flow_name) like '%post_purchase%'
            )                                                                   as post_purchase_revenue
        from {{ ref('stg_klaviyo_email_events') }} e
        left join {{ ref('stg_klaviyo_flows') }} f on e.flow_id = f.flow_id
        where e.flow_id is not null
        group by 1
    ) pp
),

-- ── Google Ads daily spend ────────────────────────────────────────────────────
-- cost_micros confirmed in raw microcurrency: divide by 1,000,000 for USD.
-- Source: google_ads_performance (no staging model exists yet for Google Ads).
google_spend_daily as (
    select
        date_day                                                                  as date,
        sum(cost_micros) / 1000000.0                                             as google_spend
    from {{ var('client_schema') }}.google_ads_performance
    group by date_day
),

-- ── Discount order rate, 90-day trailing ─────────────────────────────────────
-- Phase C: routed through filtered stg_shopify_orders, which now exposes
-- discount_codes as a pass-through. This narrows the population vs the old raw
-- read — staging excludes cancelled/voided orders AND synthetic rows (the latter
-- only when client_config.use_synthetic_data is off).
discount_daily as (
    select
        date(created_at)                                                         as date,
        count(*) filter (
            where discount_codes is not null
              and discount_codes::text != '[]'
        )::numeric                                                               as discounted_orders,
        count(*)                                                                 as total_orders
    from {{ ref('stg_shopify_orders') }}
    group by 1
),
discount_rate_rolling as (
    select
        date,
        sum(discounted_orders) over (
            order by date rows between 89 preceding and current row
        ) / nullif(
            sum(total_orders) over (
                order by date rows between 89 preceding and current row
            ), 0
        )                                                                        as discount_order_rate_90d
    from discount_daily
),

-- ── Meta creative spend concentration by objective ────────────────────────────
-- meta_ad_sets objective join pending: meta_ad_sets has no objective column.
-- Objective sourced from meta_ad_performance.objective (all NULL in synthetic data).
-- Returns NULL for all rows until live Meta data includes objective values.
meta_ad_obj_daily as (
    select
        date_start::date                                                         as date,
        objective,
        ad_id,
        sum(spend::numeric)                                                      as ad_spend
    from {{ var('client_schema') }}.meta_ad_performance
    where spend ~ '^[0-9]+(\.[0-9]+)?$'
      and objective is not null
      and objective != 'ADVANTAGE_PLUS'
    group by 1, 2, 3
),
meta_obj_share as (
    select
        date,
        objective,
        max(ad_spend)                                                            as top_spend,
        sum(ad_spend)                                                            as obj_total
    from meta_ad_obj_daily
    group by date, objective
),
meta_creative_by_obj as (
    select
        date,
        case when count(*) > 0
             then jsonb_object_agg(objective, round(top_spend / nullif(obj_total, 0), 4))
             else null
        end                                                                      as top_creative_spend_pct_by_objective
    from meta_obj_share
    group by date
),

-- ── Advantage+ spend share, daily ────────────────────────────────────────────
-- Objective = 'ADVANTAGE_PLUS' not present in synthetic data → 0.0 for all rows.
advantage_plus_daily as (
    select
        date_start::date                                                         as date,
        sum(case when objective = 'ADVANTAGE_PLUS' then spend::numeric else 0 end)
        / nullif(sum(spend::numeric), 0)                                         as advantage_plus_spend_pct
    from {{ var('client_schema') }}.meta_ad_performance
    where spend ~ '^[0-9]+(\.[0-9]+)?$'
    group by date_start::date
),

-- ── Repeat / new customer return rates ───────────────────────────────────────
-- Source: stg_loop_returns (empty in synthetic data → NULL for all dates).
-- repeat_customer_order_minimum read from client_config (default = 2).
-- Joins to customer_order_index_cte (defined above) for per-customer order ranking.
return_customer_daily as (
    select
        lr.return_date                                                           as date,
        count(*) filter (
            where coi.customer_order_index >= (
                select repeat_customer_order_minimum
                from public.client_config
                where client_id = '{{ var("client_id") }}'
            )
        )::numeric                                                               as repeat_customer_returns,
        count(*) filter (
            where coi.customer_order_index = 1
        )::numeric                                                               as new_customer_returns,
        count(*)                                                                 as total_returns
    from {{ ref('stg_loop_returns') }} lr
    left join customer_order_index_cte coi
        on coi.order_id::text = lr.order_id
    group by 1
),
return_customer_rolling as (
    select
        date,
        sum(repeat_customer_returns) over w7
            / nullif(sum(total_returns) over w7, 0)                             as repeat_customer_return_rate_7d,
        sum(new_customer_returns) over w7
            / nullif(sum(total_returns) over w7, 0)                             as new_customer_return_rate_7d
    from return_customer_daily
    window w7 as (order by date rows between 6 preceding and current row)
),

-- ── Inventory snapshot metrics (columns 6–11) ─────────────────────────────────
-- shopify_inventory_levels is a point-in-time snapshot, not a daily time-series.
-- Only snapshot dates (2026-05-31 in synthetic data) produce non-NULL values;
-- all historical mart rows return NULL for inventory-derived columns.
-- available = inventory_quantity. inventory_item_id matches variant_id in this schema.
inventory_snapshot_base as (
    select
        date(updated_at)                                                         as date,
        inventory_item_id,
        available
    from {{ ref('stg_shopify_inventory_levels') }}        -- Phase C: filtered staging
    where available is not null
),
units_sold_daily as (
    select
        date(o.created_at)                                                       as date,
        li.variant_id                                                            as inventory_item_id,
        sum(li.quantity)                                                         as units_sold
    from {{ ref('stg_shopify_order_line_items') }} li     -- Phase C: filtered staging
    inner join {{ ref('stg_shopify_orders') }} o
        on o.order_id::text = li.order_id                 -- stg order_id is bigint vs text → cast
    group by 1, 2
),
units_sold_rolling as (
    select
        date,
        inventory_item_id,
        sum(units_sold) over (
            partition by inventory_item_id
            order by date
            rows between 6 preceding and current row
        ) / 7.0                                                                  as daily_units_sold_7d_avg,
        sum(units_sold) over (
            partition by inventory_item_id
            order by date
            rows between 6 preceding and current row
        )::numeric                                                               as units_sold_7d
    from units_sold_daily
),
inventory_metrics as (
    select
        i.date,
        count(distinct i.inventory_item_id) filter (
            where i.available = 0
        )                                                                        as stockout_sku_count,
        -- B-4 pending: SKU-level ad set mapping not yet built. Brand-level spend proxy used.
        count(distinct i.inventory_item_id) filter (
            where i.available = 0
              and (
                  coalesce(cs.meta_spend, 0) > 0
                  or coalesce(cs.tiktok_spend, 0) > 0
                  or coalesce(gsd.google_spend, 0) > 0
              )
        )                                                                        as stockout_with_active_spend_count,
        -- Agent D must display 999 as "zero-velocity SKU — likely overstock or discontinued".
        -- Never display as raw number.
        avg(
            coalesce(
                i.available::numeric / nullif(u.daily_units_sold_7d_avg, 0),
                999
            )
        )                                                                        as avg_days_inventory_on_hand,
        sum(coalesce(u.units_sold_7d, 0))
            / nullif(
                sum(coalesce(u.units_sold_7d, 0)) + sum(i.available),
                0
            )                                                                    as sell_through_rate_7d,
        -- top_sku_inventory_pct: NULL — sku_cost_master SKU format (AZR-*) does not map
        -- to shopify_inventory_levels (no sku column; inventory_item_id only).
        -- Requires sku_alias_map or sku_cost_master reseed using shopify variant SKUs.
        null::numeric                                                            as top_sku_inventory_pct,
        max(i.available)::numeric
            / nullif(sum(i.available), 0)                                       as top_sku_inventory_units_pct
    from inventory_snapshot_base i
    left join cross_source cs on cs.date = i.date
    left join google_spend_daily gsd on gsd.date = i.date
    left join units_sold_rolling u
        on u.inventory_item_id = i.inventory_item_id
       and u.date = i.date
    group by i.date
),

-- ── B-4: Campaign-SKU Return Rate (7-day rolling) ─────────────────────────
-- For each date: fraction of 7d returns whose product_id matches a SKU
-- actively promoted via Meta or TikTok content_ids on that date.
-- NULL when no content_ids are available for the trailing 7 days.
promoted_content_ids as (
    select
        date_start::date                                                         as ref_date,
        unnest(content_ids)                                                      as product_id
    from {{ var('client_schema') }}.meta_ad_performance
    where content_ids is not null
      and (
            is_synthetic = false
            or (select use_synthetic_data from public.client_config
                where client_id = '{{ var("client_id") }}') = true
        )
    union all
    select
        date                                                                     as ref_date,
        unnest(content_ids)                                                      as product_id
    from {{ var('client_schema') }}.tiktok_ad_performance
    where content_ids is not null
),
daily_promoted_skus as (
    select distinct ref_date, product_id
    from promoted_content_ids
),
campaign_sku_returns as (
    select
        dps.ref_date,
        -- numerator: 7d returns whose product_id is a promoted SKU
        count(distinct lr.return_id)                                             as promo_returns_7d,
        -- denominator: all 7d returns
        (
            select count(distinct r2.return_id)
            from {{ ref('stg_loop_returns') }} r2
            where r2.return_date between dps.ref_date - interval '6 days'
                                     and dps.ref_date
        )                                                                        as total_returns_7d
    from daily_promoted_skus dps
    left join {{ ref('stg_loop_returns') }} lr
        on lr.product_id = dps.product_id
       and lr.return_date between dps.ref_date - interval '6 days'
                               and dps.ref_date
    group by dps.ref_date
),
campaign_sku_return_rate as (
    select
        ref_date                                                                 as date,
        case
            when total_returns_7d > 0
            then round(promo_returns_7d::numeric / total_returns_7d, 4)
            else null
        end                                                                      as campaign_sku_return_rate_7d
    from campaign_sku_returns
)

select
    c.date,

    -- ── Revenue ──────────────────────────────────────────────────────────────
    c.gross_revenue,
    c.net_revenue,
    c.order_count,
    c.average_order_value,

    -- ── Ad Spend & ROAS ───────────────────────────────────────────────────────
    c.meta_spend,
    c.meta_roas,
    c.tiktok_spend,
    c.tiktok_roas,
    c.total_ad_spend,
    c.blended_roas,

    -- ── Meta Rolling Signals (Agent A: A2 ROAS root cause, B1 creative fatigue, B4 CPM spike)
    (mr.meta_cpm_7d_avg - mr.meta_cpm_prior_7d_avg)
        / nullif(mr.meta_cpm_prior_7d_avg, 0) * 100                            as meta_cpm_change_pct,
    mr.meta_ctr_7d_avg,
    mr.meta_ctr_prior_7d_avg,

    -- ── Email ─────────────────────────────────────────────────────────────────
    c.emails_sent,
    c.email_opens,
    c.klaviyo_revenue,
    c.email_hard_bounces,

    -- ── Support ───────────────────────────────────────────────────────────────
    c.ticket_count,
    c.avg_resolution_hours,
    c.vip_ticket_count,
    c.avg_csat,

    -- ── Sizing Complaints (Agent A: C1 sizing complaint → return spike) ───────
    sr.sizing_complaint_rate_7d,
    (sr.sizing_complaint_rate_7d - sr.sizing_complaint_rate_prior_7d)
        / nullif(sr.sizing_complaint_rate_prior_7d, 0) * 100                   as sizing_complaint_velocity_pct,

    -- ── GA4 ───────────────────────────────────────────────────────────────────
    c.total_sessions,
    c.avg_cvr,
    c.avg_bounce_rate,
    c.checkout_error_count,

    -- ── Sentry ────────────────────────────────────────────────────────────────
    c.sentry_error_count,
    c.sentry_affected_users,

    -- ── Returns ───────────────────────────────────────────────────────────────
    c.return_count,
    c.return_refund_total,
    c.return_count * 100.0 / nullif(c.order_count, 0)                          as return_rate_pct,

    -- ── Loop Return Signals (Agent A: lifestyle_change segment) ───────────────
    coalesce(ls.loop_lifestyle_change_count, 0)                                 as loop_lifestyle_change_count,

    -- ── Repeat Purchase Rate (Agent A: E2 signal) ─────────────────────────────
    -- Sourced from mart_cross_source_daily via the cross_source CTE above.
    -- NULL when fewer than 1 customer had a first order in the trailing 90 days.
    c.rolling_repeat_purchase_rate_90d,

    -- ── Contribution Margin (Agent A: D1 signal) ──────────────────────────────
    cm.contribution_margin_pct,
    case
        when cm.cm_prior_7d is not null and cm.cm_prior_7d != 0
        then (cm.contribution_margin_pct - cm.cm_prior_7d) / cm.cm_prior_7d * 100
        else null
    end                                                                          as contribution_margin_chg_pct,

    -- ── Prior Year Baseline (52-week rule) ───────────────────────────────────
    p.py_gross_revenue,
    p.py_net_revenue,
    p.py_order_count,
    p.py_aov,
    p.py_sessions,
    p.py_cvr,
    p.py_ad_spend,
    p.py_blended_roas,
    p.py_ticket_count,
    p.py_return_count,
    p.py_sentry_errors,
    p.py_checkout_errors,

    -- ── Prior Year Baseline Availability (Agent A: D1, D6 context flag) ──────
    p.py_gross_revenue is not null                                              as using_prior_year_baseline,

    -- ── YoY Indices (Agent A compares these against thresholds) ───────────────
    case when p.py_gross_revenue > 0
        then (c.gross_revenue - p.py_gross_revenue) / p.py_gross_revenue
        else null end                                                           as revenue_yoy_index,

    case when p.py_order_count > 0
        then (c.order_count - p.py_order_count)::numeric / p.py_order_count
        else null end                                                           as order_count_yoy_index,

    case when p.py_sessions > 0
        then (c.total_sessions - p.py_sessions)::numeric / p.py_sessions
        else null end                                                           as sessions_yoy_index,

    case when p.py_blended_roas > 0
        then (c.blended_roas - p.py_blended_roas) / p.py_blended_roas
        else null end                                                           as roas_yoy_index,

    -- ── Seasonality Flag ──────────────────────────────────────────────────────
    -- BFCM window: Nov 22 – Dec 2
    extract(month from c.date) = 11 and extract(day from c.date) >= 22 or
    extract(month from c.date) = 12 and extract(day from c.date) <= 2         as is_bfcm_period,

    -- Meta attribution break (Jan 12 2026: 7d_view + 28d_view deprecated)
    c.date >= date '2026-01-12'                                                as post_meta_attribution_break,

    -- ── Data Freshness (propagated from mart_cross_source_daily) ─────────────
    -- Agent A checks any_source_stale and meta_data_stale before firing alerts.
    -- If stale: suppress and write H1 to alert_log instead.
    c.any_source_stale,
    c.data_as_of,
    c.meta_data_stale,
    c.shopify_data_stale,
    c.ga4_data_stale,

    -- ── Leading Indicator and Outcome Columns (Session 3, 2026-05-19) ─────────
    -- Required by historical_pattern_scan.py before it can run.

    -- 3a: avg days from return initiation to return processed (loop_returns)
    lrl.avg_days_to_refund,

    -- 3b: 7-day rolling average order value
    aov.aov_7d,

    -- 3c: iOS-adjusted 7d rolling open rate (multiplier from client_config)
    kor.effective_open_rate_7d,

    -- 3d: 7d rolling avg days since last VIP purchase
    vpg.vip_purchase_gap_days,

    -- 3e: PDP bounce rate — NULL: no ga4_pages source table in client_azure_co.
    -- TODO: add ga4_pages source and stg_ga4_pages model with page_path column.
    null::numeric                                                                as ga4_pdp_bounce_rate,

    -- 3f: 7d rolling count of flow emails dispatched per day
    sfr.send_frequency_7d,

    -- 3g: new customer rate and blended CAC — 7d rolling, date-level join only
    cr.new_customer_rate_7d,
    cr.blended_cac_7d,

    -- 3h: device-level checkout rates — NULL: no ga4_devices source table.
    -- TODO: add ga4_devices source and stg_ga4_devices model with device_category.
    null::numeric                                                                as mobile_checkout_completion_rate_7d,
    null::numeric                                                                as desktop_checkout_completion_rate_7d,

    -- 3i: 7d rolling post-purchase flow revenue
    ppr.post_purchase_flow_revenue_7d,

    -- ── B-9: New columns ─────────────────────────────────────────────────────

    -- Discount rate, 90-day trailing
    dr.discount_order_rate_90d,

    -- Meta creative concentration by objective (jsonb). NULL in synthetic data —
    -- meta_ad_sets objective join pending; all objectives NULL in synthetic rows.
    mco.top_creative_spend_pct_by_objective,

    -- Advantage+ spend share. 0.0 in synthetic data (no ADVANTAGE_PLUS objective rows).
    coalesce(ap.advantage_plus_spend_pct, 0)                                    as advantage_plus_spend_pct,

    -- Return rates by customer type. NULL until stg_loop_returns has rows.
    rcr.repeat_customer_return_rate_7d,
    rcr.new_customer_return_rate_7d,

    -- Inventory signals. NULL for historical dates (snapshot, not time-series).
    im.stockout_sku_count,
    im.stockout_with_active_spend_count,
    im.avg_days_inventory_on_hand,
    im.sell_through_rate_7d,
    im.top_sku_inventory_pct,
    im.top_sku_inventory_units_pct,

    -- Back-in-stock waitlist. No active back-in-stock Klaviyo flow detected in
    -- synthetic data. Onboarding check fires missed-opportunity message if absent.
    0::integer                                                                   as back_in_stock_waitlist_count,

    -- ── B-4: Campaign SKU Return Rate (7-day) ─────────────────────────────────
    -- Fraction of 7d returns attributable to actively promoted SKUs via
    -- Meta/TikTok content_ids. NULL when no content_ids present in trailing 7d.
    csr.campaign_sku_return_rate_7d

from cross_source c
left join prior_year                 p   on c.date = p.current_date_equiv::date
left join meta_rolling               mr  on c.date = mr.date
left join sizing_rolling             sr  on c.date = sr.date
left join loop_signals               ls  on c.date = ls.date
left join contribution_margin_with_lag cm on c.date = cm.date
left join loop_refund_lag            lrl on c.date = lrl.date
left join aov_rolling                aov on c.date = aov.date
left join klaviyo_open_rate_rolling  kor on c.date = kor.date
left join vip_purchase_gap           vpg on c.date = vpg.date
left join cac_rolling                cr  on c.date = cr.date
left join send_frequency_rolling     sfr on c.date = sfr.date
left join post_purchase_rolling      ppr on c.date = ppr.date
left join discount_rate_rolling      dr  on c.date = dr.date
left join meta_creative_by_obj       mco on c.date = mco.date
left join advantage_plus_daily       ap  on c.date = ap.date
left join return_customer_rolling    rcr on c.date = rcr.date
left join inventory_metrics          im  on c.date = im.date
left join campaign_sku_return_rate   csr on c.date = csr.date
order by c.date desc
