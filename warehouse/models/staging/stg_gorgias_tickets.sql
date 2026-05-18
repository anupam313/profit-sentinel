with tickets as (
    select * from {{ source('client_azure_co', 'gorgias_tickets') }}
)
select
    ticket_id,
    customer_id,
    klaviyo_profile_id,
    created_at::date                            as ticket_date,
    created_at,
    resolved_at,
    status,
    channel,
    subject,
    first_response_at,
    first_response_type,
    resolved_by,
    csat_score,
    nps_score,
    priority_queue                              as is_vip,
    last_ticket_reason,
    ticket_count_lifetime,
    resolution_hours,
    resolved_at is not null                     as is_resolved,
    case
        when resolution_hours <= 4  then 'fast'
        when resolution_hours <= 24 then 'standard'
        when resolution_hours <= 72 then 'slow'
        else                             'unresolved_or_very_slow'
    end                                         as resolution_tier
from tickets
