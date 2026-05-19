-- Primary Agent A scan table. One row per date.
-- Prior-year baseline uses 52-week rule (364 days = same weekday, year-1).
-- Columns prefixed py_ = prior year. Index columns = current / prior_year - 1.
with cross_source as (
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
sizing_daily as (
    select
        ticket_date                                                              as date,
        sum(case when last_ticket_reason = 'sizing_issue' then 1 else 0 end)   as sizing_count,
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
-- COGS proxy: net_revenue * 0.45 (using 55% blended gross margin for
-- contemporary womenswear Azure & Co).
-- TODO: pull blended_gross_margin_pct from public.client_config once that
--       column is added to the schema (currently absent).
contribution_margin as (
    select
        date,
        case
            when net_revenue > 0
            then (net_revenue * 0.55 - total_ad_spend) / net_revenue * 100
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
    c.ga4_data_stale

from cross_source c
left join prior_year                 p   on c.date = p.current_date_equiv::date
left join meta_rolling               mr  on c.date = mr.date
left join sizing_rolling             sr  on c.date = sr.date
left join loop_signals               ls  on c.date = ls.date
left join contribution_margin_with_lag cm on c.date = cm.date
order by c.date desc
