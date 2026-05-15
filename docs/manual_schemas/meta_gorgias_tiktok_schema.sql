-- ============================================================
-- MANUALLY DESIGNED SCHEMAS — Meta Ads, Gorgias, TikTok
-- Created: 2026-05-15
-- Authority: Airbyte GitHub JSON schemas (Meta), Gorgias API
--            reference, TikTok Business API / Supermetrics
-- ============================================================
-- Safe to use for:
--   - Synthetic data (Step 5 seed script)
--   - dbt staging and mart models on synthetic data
--   - Agent A/B/C/D testing against synthetic data
--
-- Must re-verify before:
--   - Connecting a real Meta / Gorgias / TikTok account
--   - Treating dbt output as production-accurate
--   - Activating these signals in Agent A for live clients
--
-- Design rules applied:
--   - Raw types only: text for API strings/numerics/dates,
--     jsonb for API objects/arrays, boolean for booleans
--   - No casting logic — casting lives in python_transformer.py
--   - is_synthetic + _airbyte_extracted_at on every table
--   - Schema-qualified: client_azure_co.*
-- ============================================================


-- ============================================================
-- META ADS
-- ============================================================

-- ------------------------------------------------------------
-- meta_ad_performance
-- Source: Airbyte Facebook Marketing connector — ads_insights
-- stream. Schema verified against Airbyte GitHub JSON schema:
-- source_facebook_marketing/schemas/ads_insights.json
--
-- Breaking changes applied per Section 8 of
-- technical_architecture.md:
--
-- [1] unique_actions EXCLUDED — deprecated Jan 2026. Returns
--     empty data silently. Do not include in raw table.
-- [2] cost_per_unique_action_type EXCLUDED — derived from
--     deprecated unique_actions metric.
-- [3] 10-second video view EXCLUDED — retired Jan 26 2026.
--     Not present in current Airbyte schema.
-- [4] Post/Page Reach, Video Impressions, Story Impressions
--     EXCLUDED — deprecated June 2026. Replaced by
--     full_view_impressions and full_view_reach.
-- [5] existing_customer_budget_percentage EXCLUDED — field
--     permanently removed from API (May 2026).
-- [6] attribution_setting included — critical for Jan 12 2026
--     structural break. Values: '7d_click_1d_view' (standard
--     post-break) or 'legacy' (pre-break windows no longer
--     available from API).
-- [7] stored_before_retention_limit added — boolean flag for
--     rows older than 13 months. Meta API only returns 13
--     months of unique-count data; rows beyond that only
--     exist because Supabase stored them before window closed.
-- [8] No existing_customer_budget_percentage — removed per
--     Advantage+ campaign structure change (May 2026).
--
-- Natural key: (ad_id, date_start, date_stop) — no single
-- PK column. Unique constraint covers the composite key.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS client_azure_co.meta_ad_performance (

    -- Identifiers
    account_id                          text,
    account_name                        text,
    account_currency                    text,
    campaign_id                         text,
    campaign_name                       text,
    adset_id                            text,
    adset_name                          text,
    ad_id                               text,
    ad_name                             text,

    -- Date range (API returns 'YYYY-MM-DD' strings)
    date_start                          text,
    date_stop                           text,
    created_time                        text,
    updated_time                        text,

    -- Attribution (CRITICAL — Jan 12 2026 structural break)
    -- '7d_click_1d_view': post-break standard window
    -- 'legacy': pre-break row (7d_view/28d_view — no longer
    --           available from Meta API as of Jan 12 2026)
    attribution_setting                 text,

    -- Campaign classification
    buying_type                         text,
    objective                           text,
    optimization_goal                   text,
    quality_ranking                     text,
    engagement_rate_ranking             text,
    conversion_rate_ranking             text,

    -- Core performance (text — python_transformer casts
    -- to numeric in staging; matches Airbyte type inference)
    spend                               text,
    impressions                         text,
    clicks                              text,
    ctr                                 text,
    cpm                                 text,
    cpc                                 text,
    cpp                                 text,
    reach                               text,
    frequency                           text,
    social_spend                        text,

    -- Link click metrics
    inline_link_clicks                  text,
    inline_link_click_ctr               text,
    inline_post_engagement              text,
    unique_clicks                       text,
    unique_ctr                          text,
    unique_inline_link_clicks           text,
    unique_link_clicks_ctr              text,
    cost_per_inline_link_click          text,
    cost_per_inline_post_engagement     text,
    cost_per_unique_click               text,
    cost_per_unique_inline_link_click   text,

    -- Full-view reach (replaces deprecated Page/Video
    -- Impression breakdowns — deprecated June 2026)
    full_view_impressions               text,
    full_view_reach                     text,

    -- Estimated ad recall
    estimated_ad_recallers              text,
    cost_per_estimated_ad_recallers     text,

    -- Lead gen
    qualifying_question_qualify_answer_rate text,

    -- Auction insights
    auction_bid                         text,
    auction_competitiveness             text,
    auction_max_competitor_bid          text,

    -- Canvas / Instant Experience
    canvas_avg_view_percent             text,
    canvas_avg_view_time                text,
    instant_experience_clicks_to_open   text,
    instant_experience_clicks_to_start  text,

    -- Actions and conversions (jsonb — each element is an
    -- action_type + value pair from the Meta API array)
    actions                             jsonb,
    action_values                       jsonb,
    conversions                         jsonb,
    conversion_values                   jsonb,
    converted_product_quantity          jsonb,
    converted_product_value             jsonb,
    cost_per_action_type                jsonb,
    ad_click_actions                    jsonb,
    ad_impression_actions               jsonb,

    -- ROAS (jsonb — keyed by action_type)
    purchase_roas                       jsonb,
    website_purchase_roas               jsonb,
    mobile_app_purchase_roas            jsonb,
    catalog_segment_actions             jsonb,
    catalog_segment_value               jsonb,
    catalog_segment_value_mobile_purchase_roas  jsonb,
    catalog_segment_value_omni_purchase_roas    jsonb,
    catalog_segment_value_website_purchase_roas jsonb,
    website_ctr                         jsonb,

    -- Outbound clicks (jsonb — action type breakdown)
    outbound_clicks                     jsonb,
    outbound_clicks_ctr                 jsonb,
    cost_per_outbound_click             jsonb,
    unique_outbound_clicks              jsonb,
    unique_outbound_clicks_ctr          jsonb,
    cost_per_unique_outbound_click      jsonb,
    instant_experience_outbound_clicks  jsonb,

    -- Video (ThruPlay = video_p100; 10-second excluded)
    video_play_actions                  jsonb,
    video_p25_watched_actions           jsonb,
    video_p50_watched_actions           jsonb,
    video_p75_watched_actions           jsonb,
    video_p95_watched_actions           jsonb,
    video_p100_watched_actions          jsonb,
    video_15_sec_watched_actions        jsonb,
    video_30_sec_watched_actions        jsonb,
    video_continuous_2_sec_watched_actions  jsonb,
    video_avg_time_watched_actions      jsonb,
    video_time_watched_actions          jsonb,
    video_play_curve_actions            jsonb,
    video_play_retention_0_to_15s_actions   jsonb,
    video_play_retention_20_to_60s_actions  jsonb,
    video_play_retention_graph_actions      jsonb,
    cost_per_thruplay                   jsonb,
    cost_per_2_sec_continuous_video_view    jsonb,
    cost_per_15_sec_video_view          jsonb,

    -- Meta data retention flag
    -- Set true for rows older than 13 months from today.
    -- Flags data only available because Supabase stored it
    -- before the Meta API retention window closed.
    -- Populated by post-processing step, not Airbyte.
    stored_before_retention_limit       boolean default false,

    -- Pipeline columns
    _airbyte_extracted_at               timestamptz,
    is_synthetic                        boolean default false,

    UNIQUE (ad_id, date_start, date_stop)
);


-- ------------------------------------------------------------
-- meta_campaigns
-- Source: Airbyte Facebook Marketing — campaigns stream
-- Schema: source_facebook_marketing/schemas/campaigns.json
--
-- Changes vs Airbyte schema:
-- [1] existing_customer_budget_percentage EXCLUDED —
--     permanently removed from API (Advantage+ migration).
-- [2] smart_promotion_type retained — this is the Advantage+
--     campaign type indicator (AUTOMATED_SHOPPING_ADS, etc.)
--     replaces the deprecated ASC/AAC campaign labels.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS client_azure_co.meta_campaigns (
    id                          text primary key,
    account_id                  text,
    name                        text,
    status                      text,
    configured_status           text,
    effective_status            text,
    objective                   text,
    buying_type                 text,
    bid_strategy                text,
    daily_budget                text,
    lifetime_budget             text,
    budget_remaining            text,
    spend_cap                   text,
    budget_rebalance_flag       text,
    -- Advantage+ campaign structure indicator.
    -- Values post-May 2026: AUTOMATED_SHOPPING_ADS,
    -- SMART_PROMOTION, or null for standard campaigns.
    -- ASC/AAC labels no longer appear (deprecated May 2026).
    smart_promotion_type        text,
    source_campaign_id          text,
    boosted_object_id           text,
    special_ad_category         text,
    special_ad_category_country jsonb,
    adlabels                    jsonb,
    issues_info                 jsonb,
    start_time                  text,
    stop_time                   text,
    created_time                text,
    updated_time                text,
    _airbyte_extracted_at       timestamptz,
    is_synthetic                boolean default false
);


-- ------------------------------------------------------------
-- meta_ad_sets
-- Source: Airbyte Facebook Marketing — ad_sets stream
-- Schema: source_facebook_marketing/schemas/ad_sets.json
--
-- Changes vs Airbyte schema:
-- [1] existing_customer_budget_percentage EXCLUDED —
--     permanently removed from API (May 2026).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS client_azure_co.meta_ad_sets (
    id                      text primary key,
    account_id              text,
    campaign_id             text,
    name                    text,
    status                  text,
    effective_status        text,
    daily_budget            text,
    lifetime_budget         text,
    budget_remaining        text,
    bid_amount              text,
    bid_strategy            text,
    bid_info                jsonb,
    bid_constraints         jsonb,
    start_time              text,
    end_time                text,
    created_time            text,
    updated_time            text,
    targeting               jsonb,
    promoted_object         jsonb,
    adlabels                jsonb,
    learning_stage_info     jsonb,
    _airbyte_extracted_at   timestamptz,
    is_synthetic            boolean default false
);


-- ============================================================
-- GORGIAS
-- ============================================================

-- ------------------------------------------------------------
-- gorgias_tickets
-- Source: Gorgias API — tickets endpoint
-- Authority: developers.gorgias.com/reference/the-ticket-object
--            Airbyte Gorgias connector (cursor: updated_datetime)
--
-- Tag storage note for Alert 5 (sizing complaint velocity):
--   tags is stored as a jsonb array of {id, name} objects,
--   exactly as returned by the Gorgias API.
--   Example: [{"id": 12, "name": "sizing"},
--              {"id": 34, "name": "runs_small"}]
--   Agent B queries this via jsonb containment operators.
--   Do not flatten tags to a separate column — the full
--   object array is required for multi-tag ticket analysis.
--
-- Nested objects (customer, assignee_user, assignee_team)
-- stored as jsonb — raw API shape preserved, transformer
-- extracts specific fields into staging.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS client_azure_co.gorgias_tickets (
    id                              bigint primary key,
    created_datetime                text,
    updated_datetime                text,
    opened_datetime                 text,
    closed_datetime                 text,
    snooze_datetime                 text,
    last_message_datetime           text,
    last_received_message_datetime  text,
    -- Classification
    status                          text,   -- open | closed
    channel                         text,   -- email | chat | helpdesk | voice |
                                            -- sms | instagram | instagram_comments |
                                            -- twitter | facebook | facebook_mentions |
                                            -- whatsapp
    via                             text,   -- how the ticket was created
    subject                         text,
    external_id                     text,
    language                        text,
    from_agent                      boolean,
    is_unread                       boolean,
    spam                            boolean,
    uri                             text,
    messages_count                  integer,
    -- Customer (nested object — {id, email, name, ...})
    customer                        jsonb,
    -- Assignee (nested objects — null if unassigned)
    assignee_user                   jsonb,
    assignee_team                   jsonb,
    -- Tags array — CRITICAL for Alert 5 (sizing complaints)
    -- Raw API shape: [{id, name}, ...] — do not alter
    tags                            jsonb,
    -- Meta / custom field data (key-value store)
    meta                            jsonb,
    -- Pipeline
    _airbyte_extracted_at           timestamptz,
    is_synthetic                    boolean default false
);


-- ------------------------------------------------------------
-- gorgias_ticket_messages
-- Source: Gorgias API — messages endpoint (child of tickets)
-- Airbyte stream name: messages (cursor: created_datetime)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS client_azure_co.gorgias_ticket_messages (
    id                  bigint primary key,
    ticket_id           bigint,
    created_datetime    text,
    updated_datetime    text,
    sent_datetime       text,
    failed_datetime     text,
    deleted_datetime    text,
    opened_datetime     text,
    channel             text,
    via                 text,
    subject             text,
    body_text           text,
    body_html           text,
    stripped_text       text,
    is_from_customer    boolean,
    from_agent          boolean,
    replied_to_id       bigint,
    uri                 text,
    -- Nested objects (raw API shape)
    source              jsonb,      -- {type, from, to}
    sender              jsonb,      -- {id, email, name}
    receiver            jsonb,      -- {email, name}
    attachments         jsonb,      -- array of attachment objects
    macros_applied      jsonb,
    -- Pipeline
    _airbyte_extracted_at   timestamptz,
    is_synthetic            boolean default false
);


-- ------------------------------------------------------------
-- gorgias_tags
-- Source: Gorgias API — tags endpoint
-- Airbyte stream name: tags (cursor: created_datetime)
--
-- This is the tag catalogue. Ticket-level tag membership is
-- stored in gorgias_tickets.tags (jsonb array). This table
-- is the dimension table for tag metadata (name, colour).
-- Alert 5 uses this to resolve tag IDs to display names.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS client_azure_co.gorgias_tags (
    id                  bigint primary key,
    name                text,
    created_datetime    text,
    updated_datetime    text,
    uri                 text,
    -- Decoration: {bgcolor, color, emoji} for Gorgias UI
    decoration          jsonb,
    -- Pipeline
    _airbyte_extracted_at   timestamptz,
    is_synthetic            boolean default false
);


-- ============================================================
-- TIKTOK
-- ============================================================

-- ------------------------------------------------------------
-- tiktok_ad_performance
-- Source: TikTok Business API — Ads Report (daily granularity)
-- Authority: TikTok API for Business portal, Supermetrics
--            TikTok Ads field reference (387 metrics confirmed)
--
-- Spark Ads / creator attribution fields required for:
--   Alert 3 — Influencer ROI after returns
--   Fields: is_spark_ad, spark_ad_type, identity_id,
--           identity_type, identity_authorized_bc_id, post_id
--
-- Natural key: (ad_id, stat_time_day) — no single-column PK.
-- ad_id is TikTok's ad-level identifier.
-- stat_time_day is the reporting date ('YYYY-MM-DD').
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS client_azure_co.tiktok_ad_performance (

    -- Identifiers / dimensions
    advertiser_id               text,
    campaign_id                 text,
    campaign_name               text,
    campaign_type               text,   -- REGULAR | IOS14 | APP_INSTALL
    objective_type              text,   -- TRAFFIC | CONVERSIONS | APP_PROMOTION | etc.
    adgroup_id                  text,   -- TikTok's ad group (equivalent to ad set)
    adgroup_name                text,
    ad_id                       text,
    ad_name                     text,
    stat_time_day               text,   -- 'YYYY-MM-DD' reporting date

    -- Core performance (text — transformer casts to numeric)
    spend                       text,
    impressions                 text,
    clicks                      text,
    ctr                         text,
    cpc                         text,
    cpm                         text,
    reach                       text,
    frequency                   text,

    -- Conversion
    conversions                 text,
    conversion_rate             text,
    cost_per_conversion         text,
    result                      text,   -- primary optimisation result count
    result_rate                 text,
    cost_per_result             text,
    real_time_conversions       text,
    real_time_conversion_rate   text,

    -- Video engagement
    video_play_actions          text,   -- total video starts
    video_watched_2s            text,   -- 2-second video views
    video_watched_6s            text,   -- 6-second video views
    average_video_play          text,   -- avg seconds per view
    average_video_play_per_user text,
    video_views_p25             text,
    video_views_p50             text,
    video_views_p75             text,
    video_views_p100            text,   -- ThruPlay (watched to end
                                        -- or 6s+ for short videos)

    -- Social engagement
    likes                       text,
    comments                    text,
    shares                      text,
    follows                     text,
    profile_visits              text,
    engagements                 text,

    -- App events
    app_install                 text,
    cost_per_app_install        text,

    -- Spark Ads / creator attribution
    -- Required for Alert 3 (influencer ROI after returns).
    -- is_spark_ad: true when the ad runs on a creator's
    --   organic TikTok post (Spark Ad format).
    -- spark_ad_type: SELF_OWNED (brand's own post) or
    --   AUTHORIZED (creator-authorized post).
    -- identity_id: TikTok identity ID of the creator whose
    --   post is being promoted.
    -- identity_type: how the identity is authorised
    --   (CUSTOMIZED_USER | AUTH_CODE | TT_USER | BC_AUTH_TT).
    -- identity_authorized_bc_id: Business Center ID used
    --   when identity_type = BC_AUTH_TT.
    -- post_id: original TikTok video post ID used in the ad.
    is_spark_ad                 boolean,
    spark_ad_type               text,
    promotion_type              text,
    identity_id                 text,
    identity_type               text,
    identity_authorized_bc_id   text,
    post_id                     text,

    -- Creative metadata
    video_id                    text,
    creative_format             text,   -- SINGLE_VIDEO | CAROUSEL
    landing_page_url            text,
    utm_source                  text,
    utm_medium                  text,
    utm_campaign                text,

    -- Pipeline
    _airbyte_extracted_at       timestamptz,
    is_synthetic                boolean default false,

    UNIQUE (ad_id, stat_time_day)
);
