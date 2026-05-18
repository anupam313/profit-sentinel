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
    c.return_count * 100.0 / nullif(c.order_count, 0)          as return_rate_pct,

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

    -- ── YoY Indices (Agent A compares these against thresholds) ───────────────
    case when p.py_gross_revenue > 0
        then (c.gross_revenue - p.py_gross_revenue) / p.py_gross_revenue
        else null end                                           as revenue_yoy_index,

    case when p.py_order_count > 0
        then (c.order_count - p.py_order_count)::numeric / p.py_order_count
        else null end                                           as order_count_yoy_index,

    case when p.py_sessions > 0
        then (c.total_sessions - p.py_sessions)::numeric / p.py_sessions
        else null end                                           as sessions_yoy_index,

    case when p.py_blended_roas > 0
        then (c.blended_roas - p.py_blended_roas) / p.py_blended_roas
        else null end                                           as roas_yoy_index,

    -- ── Seasonality Flag ──────────────────────────────────────────────────────
    -- BFCM window: Nov 22 – Dec 2
    extract(month from c.date) = 11 and extract(day from c.date) >= 22 or
    extract(month from c.date) = 12 and extract(day from c.date) <= 2   as is_bfcm_period,

    -- Meta attribution break (Jan 12 2026: 7d_view + 28d_view deprecated)
    c.date >= date '2026-01-12'                                 as post_meta_attribution_break

from cross_source c
left join prior_year p on c.date = p.current_date_equiv::date
order by c.date desc
