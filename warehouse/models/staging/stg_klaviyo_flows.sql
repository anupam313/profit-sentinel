-- Klaviyo flows staging model.
-- Source: stg_klaviyo_email_events grouped by flow_id (14 distinct flows).
-- Flow metadata (name, type, trigger) resolved via klaviyo_flow_id_history
-- for the 5 flows that were remapped during the Nov 2025 agency→in-house restructure.
-- Revenue and engagement metrics are aggregated directly from email events.
with flow_metrics as (
    select
        flow_id,
        count(*)                                                                as total_recipients,
        sum(revenue_attributed)                                                 as total_revenue,
        sum(effective_opens)::numeric / nullif(count(*), 0)                    as open_rate,
        sum(clicks)::numeric       / nullif(count(*), 0)                       as click_rate,
        count(*) filter (where revenue_attributed > 0)::numeric
            / nullif(count(*), 0)                                               as conversion_rate,
        min(sent_at)                                                            as created_at
    from {{ ref('stg_klaviyo_email_events') }}
    where flow_id is not null
    group by flow_id
),

flow_history as (
    select
        flow_id_old,
        flow_name
    from {{ source('client_azure_co', 'klaviyo_flow_id_history') }}
)

select
    fm.flow_id,
    fh.flow_name,

    -- flow_type derived from name where available; NULL otherwise
    case fh.flow_name
        when 'Welcome Series'                  then 'welcome'
        when 'Abandoned Cart'                  then 'abandoned_cart'
        when 'Post-Purchase'                   then 'post_purchase'
        when 'Win-Back'                        then 'win_back'
        when 'Back-in-Stock'                   then 'back_in_stock'
        when 'Browse Abandonment'              then 'browse_abandonment'
        when 'SMS Welcome + Abandoned Cart'    then 'sms'
        when 'VIP / High-LTV Customer'         then 'vip'
        when 'Post-Return Recovery'            then 'post_return'
        when 'Loyalty / Rewards'               then 'loyalty'
        when 'Collection Launch Announcement'  then 'collection'
        when 'Pre-Launch Waitlist'             then 'waitlist'
        when 'Size Guide / Fit Education'      then 'educational'
        when 'Birthday / Gift Card'            then 'birthday'
        when 'Sunset / Re-engagement'          then 'sunset'
        else null
    end                                                                         as flow_type,

    -- trigger_type derived from name where available
    case fh.flow_name
        when 'Welcome Series'                  then 'list_join'
        when 'Abandoned Cart'                  then 'checkout_started'
        when 'Post-Purchase'                   then 'order_placed'
        when 'Win-Back'                        then 'inactivity_60d'
        when 'Back-in-Stock'                   then 'restock'
        when 'Browse Abandonment'              then 'product_viewed'
        when 'SMS Welcome + Abandoned Cart'    then 'sms_subscribe'
        when 'VIP / High-LTV Customer'         then 'vip_threshold'
        when 'Post-Return Recovery'            then 'refund_processed'
        when 'Loyalty / Rewards'               then 'points_earned'
        when 'Collection Launch Announcement'  then 'segment_trigger'
        when 'Pre-Launch Waitlist'             then 'waitlist_signup'
        when 'Size Guide / Fit Education'      then 'page_view'
        when 'Birthday / Gift Card'            then 'birthday_minus7'
        when 'Sunset / Re-engagement'          then 'inactivity_180d'
        else null
    end                                                                         as trigger_type,

    'active'                                                                    as status,
    fm.total_recipients,
    fm.total_revenue,
    fm.total_revenue / nullif(fm.total_recipients, 0)                          as revenue_per_recipient,
    fm.open_rate,
    fm.click_rate,
    fm.conversion_rate,
    true                                                                        as is_synthetic,
    fm.created_at

from flow_metrics fm
left join flow_history fh on fm.flow_id = fh.flow_id_old
