with tickets as (
    select * from {{ source('client_azure_co', 'gorgias_tickets') }}
),
tags_agg as (
    -- One row per ticket: tags as a jsonb array of {name} objects (mirrors the
    -- real Gorgias API tag shape). Aggregated here so the join below is 1:1.
    select
        ticket_id,
        jsonb_agg(jsonb_build_object('name', tag)) as tags
    from {{ source('client_azure_co', 'gorgias_ticket_tags') }}
    group by ticket_id
)
select
    t.ticket_id,
    t.customer_id,
    t.klaviyo_profile_id,
    t.created_at::date                          as ticket_date,
    t.created_at,
    t.resolved_at,
    t.status,
    t.channel,
    t.subject,
    t.first_response_at,
    t.first_response_type,
    t.resolved_by,
    t.csat_score,
    t.nps_score,
    t.priority_queue                            as is_vip,
    t.last_ticket_reason,
    t.ticket_count_lifetime,
    t.resolution_hours,
    t.resolved_at is not null                   as is_resolved,
    case
        when t.resolution_hours <= 4  then 'fast'
        when t.resolution_hours <= 24 then 'standard'
        when t.resolution_hours <= 72 then 'slow'
        else                             'unresolved_or_very_slow'
    end                                         as resolution_tier,
    coalesce(ta.tags, '[]'::jsonb)              as tags
from tickets t
left join tags_agg ta on ta.ticket_id = t.ticket_id
