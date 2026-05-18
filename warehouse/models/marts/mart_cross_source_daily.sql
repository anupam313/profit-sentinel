-- One row per date. All major signals from 8 sources, aggregated for Agent A scanning.
with revenue as (
    select order_date as date, gross_revenue, net_revenue, order_count, average_order_value
    from {{ ref('mart_net_revenue_daily') }}
),

meta as (
    select
        date,
        sum(spend)          as meta_spend,
        avg(purchase_roas)  as meta_roas
    from {{ ref('stg_meta_ad_performance') }}
    group by date
),

tiktok as (
    select
        date,
        sum(spend)  as tiktok_spend,
        avg(roas)   as tiktok_roas
    from {{ ref('stg_tiktok_ad_performance') }}
    group by date
),

klaviyo as (
    select
        event_date                          as date,
        count(*)                            as emails_sent,
        sum(effective_opens)                as email_opens,
        sum(clicks)                         as email_clicks,
        sum(revenue_attributed)             as klaviyo_revenue,
        sum(hard_bounce_count)              as hard_bounces,
        sum(spam_complaint_count)           as spam_complaints
    from {{ ref('stg_klaviyo_email_events') }}
    group by event_date
),

gorgias as (
    select
        ticket_date                         as date,
        count(*)                            as ticket_count,
        avg(resolution_hours)               as avg_resolution_hours,
        count(*) filter (where is_vip)      as vip_ticket_count,
        avg(csat_score)                     as avg_csat
    from {{ ref('stg_gorgias_tickets') }}
    group by ticket_date
),

ga4 as (
    select
        date,
        sum(sessions)                       as total_sessions,
        avg(overall_cvr)                    as avg_cvr,
        avg(bounce_rate)                    as avg_bounce_rate
    from {{ ref('stg_ga4_sessions') }}
    group by date
),

ga4_errors as (
    select
        date,
        sum(error_count)                    as checkout_error_count,
        sum(affected_sessions)              as checkout_error_sessions
    from {{ ref('stg_ga4_checkout_errors') }}
    group by date
),

sentry as (
    select
        date,
        sum(error_count)                    as sentry_error_count,
        sum(affected_users)                 as sentry_affected_users
    from {{ ref('stg_sentry_errors') }}
    group by date
),

returns as (
    select
        return_date                         as date,
        count(*)                            as return_count,
        sum(refund_amount)                  as return_refund_total
    from {{ ref('stg_loop_returns') }}
    group by return_date
),

date_spine as (
    select distinct date from ga4
    union
    select distinct order_date from {{ ref('stg_shopify_orders') }}
)

select
    ds.date,

    -- Revenue
    coalesce(r.gross_revenue, 0)                                        as gross_revenue,
    coalesce(r.net_revenue, 0)                                          as net_revenue,
    coalesce(r.order_count, 0)                                          as order_count,
    r.average_order_value,

    -- Advertising
    coalesce(m.meta_spend, 0)                                           as meta_spend,
    m.meta_roas,
    coalesce(t.tiktok_spend, 0)                                         as tiktok_spend,
    t.tiktok_roas,
    coalesce(m.meta_spend, 0) + coalesce(t.tiktok_spend, 0)            as total_ad_spend,
    case
        when coalesce(m.meta_spend, 0) + coalesce(t.tiktok_spend, 0) > 0
        then coalesce(r.gross_revenue, 0) /
             (coalesce(m.meta_spend, 0) + coalesce(t.tiktok_spend, 0))
        else null
    end                                                                 as blended_roas,

    -- Email
    coalesce(k.emails_sent, 0)                                          as emails_sent,
    coalesce(k.email_opens, 0)                                          as email_opens,
    coalesce(k.klaviyo_revenue, 0)                                      as klaviyo_revenue,
    coalesce(k.hard_bounces, 0)                                         as email_hard_bounces,

    -- Support
    coalesce(g.ticket_count, 0)                                         as ticket_count,
    g.avg_resolution_hours,
    coalesce(g.vip_ticket_count, 0)                                     as vip_ticket_count,
    g.avg_csat,

    -- GA4
    coalesce(ga.total_sessions, 0)                                      as total_sessions,
    ga.avg_cvr,
    ga.avg_bounce_rate,
    coalesce(ge.checkout_error_count, 0)                                as checkout_error_count,

    -- Sentry
    coalesce(se.sentry_error_count, 0)                                  as sentry_error_count,
    coalesce(se.sentry_affected_users, 0)                               as sentry_affected_users,

    -- Returns
    coalesce(ret.return_count, 0)                                       as return_count,
    coalesce(ret.return_refund_total, 0)                                as return_refund_total

from date_spine ds
left join revenue        r   on ds.date = r.date
left join meta           m   on ds.date = m.date
left join tiktok         t   on ds.date = t.date
left join klaviyo        k   on ds.date = k.date
left join gorgias        g   on ds.date = g.date
left join ga4            ga  on ds.date = ga.date
left join ga4_errors     ge  on ds.date = ge.date
left join sentry         se  on ds.date = se.date
left join returns        ret on ds.date = ret.date
order by ds.date desc
