with sessions as (
    select * from {{ source('client_azure_co', 'ga4_sessions_daily') }}
    where is_synthetic = {{ var('use_synthetic_data', true) }}
),
funnel as (
    select * from {{ source('client_azure_co', 'ga4_funnel_daily') }}
    where is_synthetic = {{ var('use_synthetic_data', true) }}
)
select
    s.date,
    s.channel_group,
    s.device_category,
    s.country,
    s.sessions,
    s.new_users,
    s.returning_users,
    s.bounce_rate,
    s.avg_session_duration_seconds,
    coalesce(f.add_to_cart, 0)              as add_to_cart,
    coalesce(f.checkout_initiated, 0)       as checkout_initiated,
    coalesce(f.purchase_completed, 0)       as purchase_completed,
    coalesce(f.overall_cvr, 0)             as overall_cvr,
    coalesce(f.atc_rate, 0)               as atc_rate,
    coalesce(f.checkout_rate, 0)           as checkout_rate,
    coalesce(f.purchase_rate, 0)           as purchase_rate
from sessions s
left join funnel f
    on s.date = f.date
    and s.device_category = f.device_category
