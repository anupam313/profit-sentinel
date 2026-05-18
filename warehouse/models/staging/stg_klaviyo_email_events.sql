with events as (
    select * from {{ source('client_azure_co', 'klaviyo_email_events') }}
)
select
    message_id,
    profile_id,
    event_type,
    flow_id,
    campaign_id,
    flow_step,
    sent_at::date                       as event_date,
    sent_at,
    email_type,
    reported_opens,
    effective_opens,
    clicks,
    revenue_attributed,
    profit_sentinel_adjusted_revenue,
    spam_complaint_count,
    hard_bounce_count,
    inbox_placement_rate,
    hard_bounce_count > 0               as is_hard_bounce,
    spam_complaint_count > 0            as is_spam_complaint
from events
