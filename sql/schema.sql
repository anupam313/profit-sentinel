-- =====================================================================
-- Profit Sentinel — schema DDL snapshot
-- Generated: 2026-07-27
-- Method: Postgres catalog query (information_schema + pg_catalog),
--         NOT pg_dump.
-- This is a POINT-IN-TIME SNAPSHOT, not a live migration file.
-- Scope: every base table in public, plus client_azure_co base tables
--        that do NOT carry an _airbyte_raw_id column (Airbyte recreates
--        its own raw source tables on sync).
-- Excludes: comments, triggers, and grants. Grants and RLS are covered
--           by connectors/_harden_public_schema.py, not this file.
-- Types come from information_schema.columns; constraints from
--   pg_get_constraintdef; indexes from pg_indexes (constraint-backed
--   indexes omitted, they are recreated by the ADD CONSTRAINT lines).
-- NOTE: per-table order (CREATE -> constraints -> indexes); FK forward
--   references mean this may need reordering to execute top-to-bottom.
-- =====================================================================

-- ---------------------------------------------------------------------
-- public.alert_log
-- ---------------------------------------------------------------------
CREATE TABLE public.alert_log (
    id bigint GENERATED ALWAYS AS IDENTITY,
    created_at timestamp with time zone DEFAULT now(),
    alert_type text,
    signal_source text,
    confidence_score numeric,
    evidence_stack_json jsonb,
    thread_ts text,
    channel_id text,
    action_taken text,
    outcome text,
    fatigue_period_active boolean DEFAULT false,
    fatigue_reason text,
    dismissal_correct boolean,
    revenue_impact_missed numeric,
    delivery_delayed_hours integer,
    delay_reason text,
    klaviyo_native_revenue numeric,
    profit_sentinel_adjusted_revenue numeric,
    alert_instance_number integer DEFAULT 1,
    escalation_level integer DEFAULT 1,
    suppression_type text,
    client_id text,
    fired_at timestamp with time zone,
    should_fire boolean,
    signal_value numeric,
    threshold_value numeric,
    threshold_direction text,
    layer1_headline text,
    layer2_context text,
    layer3_precedent text,
    suppressed boolean DEFAULT false,
    suppression_category text,
    outcome_confirmed boolean,
    is_synthetic boolean DEFAULT false,
    severity text DEFAULT 'standard'::text,
    verification_category text,
    signal_date date,
    sources_used text[],
    action_taken_at timestamp with time zone,
    dismissal_reason text
);

ALTER TABLE public.alert_log ADD CONSTRAINT alert_log_pkey PRIMARY KEY (id);

CREATE INDEX alert_log_created_at_idx ON public.alert_log USING btree (created_at);

-- ---------------------------------------------------------------------
-- public.brand_event_calendar
-- ---------------------------------------------------------------------
CREATE TABLE public.brand_event_calendar (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    event_name text NOT NULL,
    event_type text NOT NULL,
    start_date date NOT NULL,
    end_date date,
    suppress_alerts text[],
    context_alerts text[],
    context_explanation text,
    residual_threshold_pct numeric,
    confidence_decay_type text,
    confidence_decay_start date,
    confidence_decay_end date,
    confidence_at_peak numeric,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE public.brand_event_calendar ADD CONSTRAINT brand_event_calendar_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.candidate_signals
-- ---------------------------------------------------------------------
CREATE TABLE public.candidate_signals (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    vertical_tag text,
    signal_description text,
    leading_signal_column text NOT NULL,
    outcome_column text NOT NULL,
    signal_values jsonb,
    sources_involved text[],
    first_detected_at date,
    instance_count integer DEFAULT 0,
    observable_instance_count integer DEFAULT 0,
    hit_rate numeric,
    cross_client_instance_count integer DEFAULT 0,
    outcome_confirmed_count integer DEFAULT 0,
    outcome_rejected_count integer DEFAULT 0,
    promotion_status text DEFAULT 'candidate'::text,
    source text,
    client_specific boolean DEFAULT true,
    calendar_clustered boolean DEFAULT false,
    confound_unresolved boolean DEFAULT false,
    single_client_core boolean DEFAULT false,
    seasonal_confound_risk boolean DEFAULT false,
    practitioner_approved boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

ALTER TABLE public.candidate_signals ADD CONSTRAINT candidate_signals_client_id_leading_signal_column_outcome_c_key UNIQUE (client_id, leading_signal_column, outcome_column);
ALTER TABLE public.candidate_signals ADD CONSTRAINT candidate_signals_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.causal_pattern_validation
-- ---------------------------------------------------------------------
CREATE TABLE public.causal_pattern_validation (
    id bigint GENERATED ALWAYS AS IDENTITY,
    causal_chain_id text NOT NULL,
    vertical_tag text NOT NULL,
    signal_type text,
    instance_count integer DEFAULT 0,
    observable_instance_count integer DEFAULT 0,
    confirmed_count integer DEFAULT 0,
    false_positive_count integer DEFAULT 0,
    confidence_rate numeric,
    hit_rate numeric,
    threshold_at_scan_time jsonb,
    confidence_tier text,
    last_promoted_at timestamp with time zone,
    historical_scan_seeded boolean DEFAULT false,
    scan_skipped_reason text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

ALTER TABLE public.causal_pattern_validation ADD CONSTRAINT causal_pattern_validation_causal_chain_id_vertical_tag_key UNIQUE (causal_chain_id, vertical_tag);
ALTER TABLE public.causal_pattern_validation ADD CONSTRAINT causal_pattern_validation_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.client_config
-- ---------------------------------------------------------------------
CREATE TABLE public.client_config (
    client_id text NOT NULL,
    brand_name text NOT NULL,
    shopify_store_url text NOT NULL,
    shopify_store_id text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    primary_product_category text DEFAULT 'fashion_general'::text,
    gmv_tier text DEFAULT 'growth'::text,
    approximate_annual_gmv numeric,
    brand_price_point text DEFAULT 'mid'::text,
    primary_sales_channel text DEFAULT 'dtc'::text,
    founded_year integer,
    onboarding_state jsonb DEFAULT '{"go_live": false, "last_active": null, "current_step": "not_started", "sync_completed": false, "gap_resolutions": [], "slack_connected": false, "steps_completed": [], "semantic_answers": {}, "questions_remaining": [], "validation_completed": false, "attribution_completed": false, "sensitivity_configured": false}'::jsonb,
    onboarding_step text DEFAULT 'not_started'::text,
    is_live boolean DEFAULT false,
    go_live_date timestamp with time zone,
    shopify_connected boolean DEFAULT false,
    meta_connected boolean DEFAULT false,
    tiktok_connected boolean DEFAULT false,
    klaviyo_connected boolean DEFAULT false,
    gorgias_connected boolean DEFAULT false,
    ga4_connected boolean DEFAULT false,
    sentry_connected boolean DEFAULT false,
    loop_returns_connected boolean DEFAULT false,
    finaloop_connected boolean DEFAULT false,
    google_ads_connected boolean DEFAULT false,
    okendo_connected boolean DEFAULT false,
    yotpo_connected boolean DEFAULT false,
    attentive_connected boolean DEFAULT false,
    postscript_connected boolean DEFAULT false,
    amazon_connected boolean DEFAULT false,
    tiktok_shop_connected boolean DEFAULT false,
    xero_connected boolean DEFAULT false,
    quickbooks_connected boolean DEFAULT false,
    hotjar_connected boolean DEFAULT false,
    pinterest_connected boolean DEFAULT false,
    last_shopify_sync timestamp with time zone,
    last_meta_sync timestamp with time zone,
    last_tiktok_sync timestamp with time zone,
    last_klaviyo_sync timestamp with time zone,
    last_gorgias_sync timestamp with time zone,
    last_ga4_sync timestamp with time zone,
    last_sentry_sync timestamp with time zone,
    last_loop_returns_sync timestamp with time zone,
    last_finaloop_sync timestamp with time zone,
    last_google_ads_sync timestamp with time zone,
    last_amazon_sync timestamp with time zone,
    include_shipping_in_revenue boolean DEFAULT false,
    gift_card_revenue_timing text DEFAULT 'when_sold'::text,
    exclude_tax_from_revenue boolean DEFAULT true,
    include_tips_in_revenue boolean DEFAULT false,
    preorder_revenue_timing text DEFAULT 'order_date'::text,
    exclude_b2b_orders boolean DEFAULT false,
    b2b_tag_values text[] DEFAULT ARRAY['wholesale'::text, 'b2b'::text],
    include_pos_orders boolean DEFAULT true,
    excluded_source_systems text[] DEFAULT ARRAY[]::text[],
    exclude_cancelled_before_fulfilment boolean DEFAULT true,
    exchange_handling_method text DEFAULT 'refund_plus_new_order'::text,
    count_exchanges_as_returns boolean DEFAULT false,
    return_window_days integer DEFAULT 30,
    return_window_confirmed boolean DEFAULT false,
    extended_return_window_skus text[] DEFAULT ARRAY[]::text[],
    restocking_fee_pct numeric DEFAULT 0,
    cogs_source text DEFAULT 'shopify_cost_field'::text,
    cogs_confidence_level text DEFAULT 'low'::text,
    shopify_cost_field_coverage_pct numeric DEFAULT 0,
    include_payment_fees_in_cogs boolean DEFAULT true,
    payment_fee_pct numeric DEFAULT 2.9,
    fulfilment_cost_source text DEFAULT 'none'::text,
    fulfilment_cost_fixed numeric DEFAULT 0,
    fulfilment_cost_pct numeric DEFAULT 0,
    include_return_shipping_in_cogs boolean DEFAULT true,
    return_shipping_cost_fixed numeric DEFAULT 0,
    target_contribution_margin_pct numeric DEFAULT 30,
    meta_attribution_window text DEFAULT '7d_click_1d_view'::text,
    tiktok_attribution_window text DEFAULT '7d_click_1d_view'::text,
    google_ads_attribution_window text DEFAULT '30d_click'::text,
    use_data_driven_attribution boolean DEFAULT false,
    slack_bot_token text,
    slack_workspace_id text,
    slack_alert_channel_id text,
    slack_morning_brief_channel_id text,
    slack_query_channel_ids text[] DEFAULT ARRAY[]::text[],
    query_user_slack_ids text[] DEFAULT ARRAY[]::text[],
    alert_approval_required boolean DEFAULT true,
    morning_brief_time text DEFAULT '08:00'::text,
    reporting_timezone text DEFAULT 'America/New_York'::text,
    reporting_currency text DEFAULT 'USD'::text,
    fiscal_year_start_month integer DEFAULT 1,
    week_start_day text DEFAULT 'monday'::text,
    suppress_all_alerts boolean DEFAULT false,
    suppress_until timestamp with time zone,
    suppressed_alert_types text[] DEFAULT ARRAY[]::text[],
    sale_period_active boolean DEFAULT false,
    sale_period_ends_at timestamp with time zone,
    alert_sensitivity text DEFAULT 'medium'::text,
    return_rate_threshold_pp numeric DEFAULT 3.0,
    cpm_spike_threshold_pct numeric DEFAULT 20.0,
    margin_floor_pct numeric DEFAULT 5.0,
    ga4_funnel_drop_threshold numeric DEFAULT 8.0,
    sentry_error_threshold_pct numeric DEFAULT 2.0,
    gorgias_sentiment_threshold numeric DEFAULT 15.0,
    roas_drop_threshold_pct numeric DEFAULT 15.0,
    influencer_return_rate_threshold numeric DEFAULT 35.0,
    contribution_margin_drop_threshold numeric DEFAULT 5.0,
    min_order_count_for_alerts integer DEFAULT 5,
    min_sessions_for_ga4_alerts integer DEFAULT 500,
    min_tickets_for_gorgias_alerts integer DEFAULT 20,
    min_ad_spend_for_cpm_alerts numeric DEFAULT 500,
    min_influencer_revenue_for_alerts numeric DEFAULT 2000,
    thresholds_last_calculated_at timestamp with time zone,
    thresholds_manually_overridden boolean DEFAULT false,
    sensitivity_review_due_at timestamp with time zone,
    sensitivity_review_completed_at timestamp with time zone,
    dismissed_alert_counts jsonb DEFAULT '{}'::jsonb,
    dq_score_shopify numeric DEFAULT 0,
    dq_score_meta numeric DEFAULT 0,
    dq_score_tiktok numeric DEFAULT 0,
    dq_score_klaviyo numeric DEFAULT 0,
    dq_score_gorgias numeric DEFAULT 0,
    dq_score_ga4 numeric DEFAULT 0,
    dq_score_sentry numeric DEFAULT 0,
    dq_score_loop_returns numeric DEFAULT 0,
    dq_scores_updated_at timestamp with time zone,
    min_dq_score_to_alert numeric DEFAULT 60,
    pricing_tier text DEFAULT 'growth'::text,
    billing_start_date timestamp with time zone,
    trial_end_date timestamp with time zone,
    is_trial boolean DEFAULT true,
    max_query_users integer DEFAULT 2,
    monthly_token_budget integer DEFAULT 500000,
    tokens_used_this_month integer DEFAULT 0,
    token_budget_reset_at timestamp with time zone,
    agency_client_ids text[] DEFAULT ARRAY[]::text[],
    use_synthetic_data boolean DEFAULT false,
    blended_gross_margin_pct numeric DEFAULT 0.55,
    ios_mpp_multiplier numeric DEFAULT 0.65,
    historical_scan_status text DEFAULT 'pending'::text,
    historical_scan_completed boolean DEFAULT false,
    historical_scan_completed_at timestamp with time zone,
    last_historical_scan_at timestamp with time zone,
    gmv_derived_annual numeric,
    gmv_derived_at timestamp with time zone,
    meta_lookback_days integer,
    tiktok_lookback_days integer,
    shopify_lookback_days integer,
    klaviyo_lookback_days integer,
    gorgias_lookback_days integer,
    loop_lookback_days integer,
    sentry_lookback_days integer,
    ga4_lookback_days integer,
    pending_connectors text[] DEFAULT '{}'::text[],
    repeat_customer_order_minimum integer DEFAULT 2,
    explorer_max_orders integer DEFAULT 1,
    regular_max_orders integer DEFAULT 3,
    loyalist_max_orders integer DEFAULT 6,
    advocate_min_orders integer DEFAULT 7,
    segment_significance_min_revenue_pct numeric DEFAULT 2.0,
    segment_calibration_status text DEFAULT 'pending'::text
);

ALTER TABLE public.client_config ADD CONSTRAINT client_config_pkey PRIMARY KEY (client_id);

-- ---------------------------------------------------------------------
-- public.config_change_log
-- ---------------------------------------------------------------------
CREATE TABLE public.config_change_log (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    changed_at timestamp with time zone DEFAULT now(),
    field_name text NOT NULL,
    old_value text,
    new_value text,
    changed_by text,
    reason text
);

ALTER TABLE public.config_change_log ADD CONSTRAINT config_change_log_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.founder_preference_profile
-- ---------------------------------------------------------------------
CREATE TABLE public.founder_preference_profile (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    alert_type text NOT NULL,
    total_fired integer DEFAULT 0,
    approved_count integer DEFAULT 0,
    snoozed_count integer DEFAULT 0,
    dismissed_count integer DEFAULT 0,
    dismissed_correct_count integer DEFAULT 0,
    dismissed_incorrect_count integer DEFAULT 0,
    capacity_constrained_count integer DEFAULT 0,
    avg_response_time_minutes numeric,
    last_updated timestamp with time zone DEFAULT now()
);

ALTER TABLE public.founder_preference_profile ADD CONSTRAINT founder_preference_profile_client_id_alert_type_key UNIQUE (client_id, alert_type);
ALTER TABLE public.founder_preference_profile ADD CONSTRAINT founder_preference_profile_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.influencer_profile
-- ---------------------------------------------------------------------
CREATE TABLE public.influencer_profile (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    creator_id text NOT NULL,
    platform text NOT NULL,
    follower_count integer,
    follower_tier text,
    campaigns_run integer DEFAULT 0,
    first_campaign_date date,
    last_campaign_date date,
    return_adjusted_roas_avg numeric,
    return_adjusted_roas_by_season jsonb,
    category_performance jsonb,
    audience_decay_indicator boolean DEFAULT false,
    relationship_tier text DEFAULT 'one-off'::text,
    total_fee_paid numeric DEFAULT 0,
    total_net_revenue_attributed numeric DEFAULT 0,
    lifetime_return_adjusted_roi numeric,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

ALTER TABLE public.influencer_profile ADD CONSTRAINT influencer_profile_client_id_creator_id_platform_key UNIQUE (client_id, creator_id, platform);
ALTER TABLE public.influencer_profile ADD CONSTRAINT influencer_profile_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.network_pattern_benchmarks
-- ---------------------------------------------------------------------
CREATE TABLE public.network_pattern_benchmarks (
    id bigint GENERATED ALWAYS AS IDENTITY,
    alert_type text NOT NULL,
    archetype text NOT NULL,
    metric_name text,
    pattern_description text,
    benchmark_median numeric,
    benchmark_p25 numeric,
    benchmark_p75 numeric,
    benchmark_bfcm_typical numeric,
    network_confirmation_rate numeric,
    sample_size integer,
    period_type text,
    last_updated timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now(),
    vertical_tag text
);

ALTER TABLE public.network_pattern_benchmarks ADD CONSTRAINT network_pattern_benchmarks_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.onboarding_messages
-- ---------------------------------------------------------------------
CREATE TABLE public.onboarding_messages (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    message_variant text NOT NULL,
    message_text text NOT NULL,
    generated_at timestamp with time zone DEFAULT now(),
    sent boolean DEFAULT false
);

ALTER TABLE public.onboarding_messages ADD CONSTRAINT onboarding_messages_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.permanent_dq_limitations
-- ---------------------------------------------------------------------
CREATE TABLE public.permanent_dq_limitations (
    id bigint GENERATED ALWAYS AS IDENTITY,
    limitation_name text NOT NULL,
    affected_sources text[],
    affected_alerts text[],
    estimated_impact text,
    estimated_magnitude text,
    caveat_text text,
    is_resolvable boolean DEFAULT false,
    resolution_path text
);

ALTER TABLE public.permanent_dq_limitations ADD CONSTRAINT permanent_dq_limitations_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.schema_versions
-- ---------------------------------------------------------------------
CREATE TABLE public.schema_versions (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    table_name text NOT NULL,
    column_name text NOT NULL,
    old_type text,
    new_type text,
    change_type text NOT NULL,
    detected_at timestamp with time zone DEFAULT now(),
    is_resolved boolean DEFAULT false,
    resolved_at timestamp with time zone
);

ALTER TABLE public.schema_versions ADD CONSTRAINT schema_versions_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.source_schema_registry
-- ---------------------------------------------------------------------
CREATE TABLE public.source_schema_registry (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    source_name text NOT NULL,
    table_name text NOT NULL,
    column_name text NOT NULL,
    raw_data_type text NOT NULL,
    target_data_type text NOT NULL,
    transformation text NOT NULL,
    json_path text,
    default_value text,
    is_nullable boolean DEFAULT true,
    is_removed boolean DEFAULT false,
    last_validated timestamp with time zone DEFAULT now()
);

ALTER TABLE public.source_schema_registry ADD CONSTRAINT source_schema_registry_client_id_table_name_column_name_key UNIQUE (client_id, table_name, column_name);
ALTER TABLE public.source_schema_registry ADD CONSTRAINT source_schema_registry_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.suppression_log
-- ---------------------------------------------------------------------
CREATE TABLE public.suppression_log (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    signal_detected_at timestamp with time zone,
    alert_type text,
    signal_value numeric,
    threshold_value numeric,
    suppression_reason text,
    suppression_category text,
    suppression_state integer,
    variance_explained_pct numeric,
    residual_signal numeric,
    suppression_source text,
    would_have_fired_at timestamp with time zone,
    founder_queryable boolean DEFAULT true,
    detected_signal_description text,
    threshold_context text,
    suppression_explanation text,
    residual_signal_description text,
    founder_verification_action text,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE public.suppression_log ADD CONSTRAINT uq_suppression_log_signal UNIQUE (client_id, alert_type, would_have_fired_at);
ALTER TABLE public.suppression_log ADD CONSTRAINT suppression_log_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- public.thread_context
-- ---------------------------------------------------------------------
CREATE TABLE public.thread_context (
    id bigint GENERATED ALWAYS AS IDENTITY,
    thread_ts text,
    channel_id text,
    alert_id bigint,
    alert_context_json jsonb,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE public.thread_context ADD CONSTRAINT thread_context_thread_ts_key UNIQUE (thread_ts);
ALTER TABLE public.thread_context ADD CONSTRAINT thread_context_pkey PRIMARY KEY (id);
ALTER TABLE public.thread_context ADD CONSTRAINT thread_context_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES alert_log(id);

CREATE INDEX thread_context_thread_ts_idx ON public.thread_context USING btree (thread_ts);

-- ---------------------------------------------------------------------
-- client_azure_co.alert_data_lineage
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.alert_data_lineage (
    id bigint GENERATED ALWAYS AS IDENTITY,
    alert_log_id bigint,
    source text NOT NULL,
    metric_name text NOT NULL,
    metric_value numeric,
    source_row_ids text[],
    source_query text,
    row_count integer,
    date_range_start date,
    date_range_end date,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.alert_data_lineage ADD CONSTRAINT alert_data_lineage_pkey PRIMARY KEY (id);
ALTER TABLE client_azure_co.alert_data_lineage ADD CONSTRAINT alert_data_lineage_alert_log_id_fkey FOREIGN KEY (alert_log_id) REFERENCES alert_log(id);

-- ---------------------------------------------------------------------
-- client_azure_co.brand_event_calendar
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.brand_event_calendar (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    event_name text NOT NULL,
    event_type text NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    suppress_alerts text[],
    context_alerts text[],
    context_explanation text,
    residual_threshold_pct numeric,
    confidence_decay_type text,
    confidence_decay_start date,
    confidence_decay_end date,
    confidence_at_peak numeric DEFAULT 1.0,
    detection_method text DEFAULT 'auto'::text,
    detection_lag_hours integer,
    confidence numeric DEFAULT 1.0,
    last_verified_at timestamp with time zone,
    is_recurring boolean DEFAULT false,
    recurrence_rule text,
    auto_detected boolean DEFAULT true,
    detected_from text,
    event_profile jsonb,
    suppression_type text DEFAULT 'reactive'::text,
    is_synthetic boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.brand_event_calendar ADD CONSTRAINT brand_event_calendar_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.dq_events
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.dq_events (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    source text NOT NULL,
    dq_issue_code text NOT NULL,
    metric_domain text NOT NULL,
    started_at timestamp with time zone NOT NULL,
    resolved_at timestamp with time zone,
    peak_severity integer,
    recovery_duration_hours integer,
    recovery_dq_curve jsonb,
    backlog_order_count integer,
    backlog_processing_lag integer,
    cascade_to text[],
    cascade_lag_hours integer,
    cascade_duration_hours integer,
    alerts_suppressed text[],
    alerts_capped jsonb,
    is_synthetic boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.dq_events ADD CONSTRAINT dq_events_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.dq_metric_scores
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.dq_metric_scores (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    source text NOT NULL,
    metric_domain text NOT NULL,
    dq_score numeric NOT NULL,
    dq_issues text[],
    alert_types_affected text[],
    confidence_cap numeric,
    freshness_tier text,
    effective_from timestamp with time zone,
    effective_to timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.dq_metric_scores ADD CONSTRAINT dq_metric_scores_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.ga4_checkout_errors
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.ga4_checkout_errors (
    id bigint GENERATED ALWAYS AS IDENTITY,
    date date NOT NULL,
    hour integer,
    error_type text,
    device_category text,
    error_count integer,
    affected_sessions integer,
    is_synthetic boolean DEFAULT true,
    _airbyte_extracted_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.ga4_checkout_errors ADD CONSTRAINT ga4_checkout_errors_date_hour_error_type_device_category_key UNIQUE (date, hour, error_type, device_category);
ALTER TABLE client_azure_co.ga4_checkout_errors ADD CONSTRAINT ga4_checkout_errors_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.ga4_funnel_daily
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.ga4_funnel_daily (
    id bigint GENERATED ALWAYS AS IDENTITY,
    date date NOT NULL,
    device_category text,
    sessions_entered integer,
    product_page_views integer,
    add_to_cart integer,
    checkout_initiated integer,
    checkout_payment_info integer,
    purchase_completed integer,
    product_page_rate numeric,
    atc_rate numeric,
    checkout_rate numeric,
    payment_completion_rate numeric,
    purchase_rate numeric,
    overall_cvr numeric,
    is_synthetic boolean DEFAULT true,
    _airbyte_extracted_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.ga4_funnel_daily ADD CONSTRAINT ga4_funnel_daily_date_device_category_key UNIQUE (date, device_category);
ALTER TABLE client_azure_co.ga4_funnel_daily ADD CONSTRAINT ga4_funnel_daily_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.ga4_sessions_daily
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.ga4_sessions_daily (
    id bigint GENERATED ALWAYS AS IDENTITY,
    date date NOT NULL,
    sessions integer,
    new_users integer,
    returning_users integer,
    bounce_rate numeric,
    avg_session_duration_seconds numeric,
    channel_group text,
    device_category text,
    country text,
    is_synthetic boolean DEFAULT true,
    _airbyte_extracted_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.ga4_sessions_daily ADD CONSTRAINT ga4_sessions_daily_date_channel_group_device_category_count_key UNIQUE (date, channel_group, device_category, country);
ALTER TABLE client_azure_co.ga4_sessions_daily ADD CONSTRAINT ga4_sessions_daily_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.google_ads_performance
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.google_ads_performance (
    id bigint GENERATED ALWAYS AS IDENTITY,
    date_day date NOT NULL,
    campaign_id text NOT NULL,
    campaign_name text,
    campaign_type text,
    ad_group_id text,
    ad_group_name text,
    cost_micros bigint,
    impressions bigint,
    clicks bigint,
    ctr numeric,
    average_cpc numeric,
    conversions numeric,
    conversion_value numeric,
    conversion_value_per_cost numeric,
    search_impression_share numeric,
    quality_score integer,
    is_synthetic boolean DEFAULT true,
    _airbyte_extracted_at timestamp with time zone DEFAULT now(),
    data_completeness_flag varchar,
    attribution_window varchar NOT NULL,
    attribution_window_note varchar NOT NULL,
    diagnostic_block_reason varchar,
    max_confidence_cap double precision DEFAULT 1.0,
    reporting_delay_flag boolean DEFAULT false,
    ad_set_split_row boolean DEFAULT false,
    campaign_name_history text[],
    campaign_name_is_stable boolean DEFAULT true,
    campaign_objective varchar,
    product_id text,
    reason_product_id_null varchar,
    video_view_rate numeric,
    video_quartile_p25_rate numeric,
    video_quartile_p50_rate numeric,
    video_quartile_p75_rate numeric,
    video_quartile_p100_rate numeric,
    average_cpv numeric
);

ALTER TABLE client_azure_co.google_ads_performance ADD CONSTRAINT google_ads_performance_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.gorgias_tag_normalisation
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.gorgias_tag_normalisation (
    raw_tag text NOT NULL,
    canonical_tag text NOT NULL,
    category text,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.gorgias_tag_normalisation ADD CONSTRAINT uq_gorgias_tag_normalisation UNIQUE (raw_tag);

-- ---------------------------------------------------------------------
-- client_azure_co.gorgias_tags
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.gorgias_tags (
    id bigint NOT NULL,
    name text,
    created_datetime text,
    updated_datetime text,
    uri text,
    decoration jsonb,
    _airbyte_extracted_at timestamp with time zone,
    is_synthetic boolean DEFAULT false
);

ALTER TABLE client_azure_co.gorgias_tags ADD CONSTRAINT gorgias_tags_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.klaviyo_flow_id_history
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.klaviyo_flow_id_history (
    flow_id_old text,
    flow_id_new text,
    flow_name text,
    client_id text,
    effective_from date,
    effective_to date,
    reason text,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.klaviyo_flow_id_history ADD CONSTRAINT uq_klaviyo_flow_id_history UNIQUE (flow_id_old, effective_from);

-- ---------------------------------------------------------------------
-- client_azure_co.meta_ad_performance
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.meta_ad_performance (
    account_id text,
    account_name text,
    account_currency text,
    campaign_id text,
    campaign_name text,
    adset_id text,
    adset_name text,
    ad_id text,
    ad_name text,
    date_start text,
    date_stop text,
    created_time text,
    updated_time text,
    attribution_setting text,
    buying_type text,
    objective text,
    optimization_goal text,
    quality_ranking text,
    engagement_rate_ranking text,
    conversion_rate_ranking text,
    spend text,
    impressions text,
    clicks text,
    ctr text,
    cpm text,
    cpc text,
    cpp text,
    reach text,
    frequency text,
    social_spend text,
    inline_link_clicks text,
    inline_link_click_ctr text,
    inline_post_engagement text,
    unique_clicks text,
    unique_ctr text,
    unique_inline_link_clicks text,
    unique_link_clicks_ctr text,
    cost_per_inline_link_click text,
    cost_per_inline_post_engagement text,
    cost_per_unique_click text,
    cost_per_unique_inline_link_click text,
    full_view_impressions text,
    full_view_reach text,
    estimated_ad_recallers text,
    cost_per_estimated_ad_recallers text,
    qualifying_question_qualify_answer_rate text,
    auction_bid text,
    auction_competitiveness text,
    auction_max_competitor_bid text,
    canvas_avg_view_percent text,
    canvas_avg_view_time text,
    instant_experience_clicks_to_open text,
    instant_experience_clicks_to_start text,
    actions jsonb,
    action_values jsonb,
    conversions jsonb,
    conversion_values jsonb,
    converted_product_quantity jsonb,
    converted_product_value jsonb,
    cost_per_action_type jsonb,
    ad_click_actions jsonb,
    ad_impression_actions jsonb,
    purchase_roas jsonb,
    website_purchase_roas jsonb,
    mobile_app_purchase_roas jsonb,
    catalog_segment_actions jsonb,
    catalog_segment_value jsonb,
    catalog_segment_value_mobile_purchase_roas jsonb,
    catalog_segment_value_omni_purchase_roas jsonb,
    catalog_segment_value_website_purchase_roas jsonb,
    website_ctr jsonb,
    outbound_clicks jsonb,
    outbound_clicks_ctr jsonb,
    cost_per_outbound_click jsonb,
    unique_outbound_clicks jsonb,
    unique_outbound_clicks_ctr jsonb,
    cost_per_unique_outbound_click jsonb,
    instant_experience_outbound_clicks jsonb,
    video_play_actions jsonb,
    video_p25_watched_actions jsonb,
    video_p50_watched_actions jsonb,
    video_p75_watched_actions jsonb,
    video_p95_watched_actions jsonb,
    video_p100_watched_actions jsonb,
    video_15_sec_watched_actions jsonb,
    video_30_sec_watched_actions jsonb,
    video_continuous_2_sec_watched_actions jsonb,
    video_avg_time_watched_actions jsonb,
    video_time_watched_actions jsonb,
    video_play_curve_actions jsonb,
    video_play_retention_0_to_15s_actions jsonb,
    video_play_retention_20_to_60s_actions jsonb,
    video_play_retention_graph_actions jsonb,
    cost_per_thruplay jsonb,
    cost_per_2_sec_continuous_video_view jsonb,
    cost_per_15_sec_video_view jsonb,
    stored_before_retention_limit boolean DEFAULT false,
    _airbyte_extracted_at timestamp with time zone,
    is_synthetic boolean DEFAULT false,
    campaign_objective varchar,
    attribution_type varchar,
    click_only_purchase_value numeric,
    content_ids text[],
    conversion_value numeric,
    date_day date
);

ALTER TABLE client_azure_co.meta_ad_performance ADD CONSTRAINT meta_ad_performance_ad_id_date_start_date_stop_key UNIQUE (ad_id, date_start, date_stop);

-- ---------------------------------------------------------------------
-- client_azure_co.meta_ad_sets
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.meta_ad_sets (
    id text NOT NULL,
    account_id text,
    campaign_id text,
    name text,
    status text,
    effective_status text,
    daily_budget text,
    lifetime_budget text,
    budget_remaining text,
    bid_amount text,
    bid_strategy text,
    bid_info jsonb,
    bid_constraints jsonb,
    start_time text,
    end_time text,
    created_time text,
    updated_time text,
    targeting jsonb,
    promoted_object jsonb,
    adlabels jsonb,
    learning_stage_info jsonb,
    _airbyte_extracted_at timestamp with time zone,
    is_synthetic boolean DEFAULT false
);

ALTER TABLE client_azure_co.meta_ad_sets ADD CONSTRAINT meta_ad_sets_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.meta_billing_statement
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.meta_billing_statement (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    statement_month date NOT NULL,
    total_spend_exact numeric(18,6),
    total_spend_api numeric(10,2),
    rounding_gap numeric(10,6),
    currency text DEFAULT 'USD'::text,
    statement_date date,
    source text DEFAULT 'finaloop'::text,
    is_synthetic boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.meta_billing_statement ADD CONSTRAINT meta_billing_statement_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.meta_campaigns
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.meta_campaigns (
    id text NOT NULL,
    account_id text,
    name text,
    status text,
    configured_status text,
    effective_status text,
    objective text,
    buying_type text,
    bid_strategy text,
    daily_budget text,
    lifetime_budget text,
    budget_remaining text,
    spend_cap text,
    budget_rebalance_flag text,
    smart_promotion_type text,
    source_campaign_id text,
    boosted_object_id text,
    special_ad_category text,
    special_ad_category_country jsonb,
    adlabels jsonb,
    issues_info jsonb,
    start_time text,
    stop_time text,
    created_time text,
    updated_time text,
    _airbyte_extracted_at timestamp with time zone,
    is_synthetic boolean DEFAULT false
);

ALTER TABLE client_azure_co.meta_campaigns ADD CONSTRAINT meta_campaigns_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.sentry_errors_daily
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.sentry_errors_daily (
    id bigint GENERATED ALWAYS AS IDENTITY,
    date date NOT NULL,
    hour integer,
    error_type text NOT NULL,
    environment text DEFAULT 'production'::text,
    release_version text,
    error_count integer NOT NULL,
    affected_users integer,
    p50_duration_ms numeric,
    p95_duration_ms numeric,
    browser text,
    device_category text,
    url_path text,
    resolved boolean DEFAULT false,
    is_synthetic boolean DEFAULT true,
    _airbyte_extracted_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.sentry_errors_daily ADD CONSTRAINT sentry_err_natural_key UNIQUE (date, hour, error_type, browser, device_category, url_path);
ALTER TABLE client_azure_co.sentry_errors_daily ADD CONSTRAINT sentry_errors_daily_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.sku_cost_master
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.sku_cost_master (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    shopify_variant_id text NOT NULL,
    sku text NOT NULL,
    record_type text NOT NULL,
    supplier_cost numeric,
    landed_cost numeric,
    landed_cost_source text,
    influencer_id text,
    package_landed_cost numeric,
    packaging_cost numeric,
    shipping_cost numeric,
    total_package_cost numeric,
    featured_item_sku text,
    non_featured_item_skus text[],
    effective_from date NOT NULL,
    effective_to date,
    is_synthetic boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    category_id text,
    category_full_name text,
    category_inference_confidence numeric,
    category_source text,
    taxonomy_version text,
    category_grouping_key text
);

ALTER TABLE client_azure_co.sku_cost_master ADD CONSTRAINT sku_cost_master_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.stg_gorgias_tags
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.stg_gorgias_tags (
    _airbyte_extracted_at timestamp with time zone,
    created_datetime timestamp with time zone,
    decoration jsonb,
    id bigint,
    is_synthetic boolean,
    name text,
    updated_datetime timestamp with time zone,
    uri text
);

-- ---------------------------------------------------------------------
-- client_azure_co.stg_gorgias_ticket_messages
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.stg_gorgias_ticket_messages (
    _airbyte_extracted_at timestamp with time zone,
    attachments jsonb,
    body_html text,
    body_text text,
    channel text,
    created_datetime timestamp with time zone,
    deleted_datetime timestamp with time zone,
    failed_datetime timestamp with time zone,
    from_agent boolean,
    id bigint,
    is_from_customer boolean,
    is_synthetic boolean,
    macros_applied jsonb,
    opened_datetime timestamp with time zone,
    receiver jsonb,
    replied_to_id bigint,
    sender jsonb,
    sent_datetime timestamp with time zone,
    source jsonb,
    stripped_text text,
    subject text,
    ticket_id bigint,
    updated_datetime timestamp with time zone,
    uri text,
    via text
);

-- ---------------------------------------------------------------------
-- client_azure_co.stg_gorgias_tickets
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.stg_gorgias_tickets (
    _airbyte_extracted_at timestamp with time zone,
    assignee_team jsonb,
    assignee_user jsonb,
    channel text,
    closed_datetime timestamp with time zone,
    created_datetime timestamp with time zone,
    customer jsonb,
    external_id text,
    from_agent boolean,
    id bigint,
    is_synthetic boolean,
    is_unread boolean,
    language text,
    last_message_datetime timestamp with time zone,
    last_received_message_datetime timestamp with time zone,
    messages_count integer,
    meta jsonb,
    opened_datetime timestamp with time zone,
    snooze_datetime timestamp with time zone,
    spam boolean,
    status text,
    subject text,
    tags jsonb,
    updated_datetime timestamp with time zone,
    uri text,
    via text
);

-- ---------------------------------------------------------------------
-- client_azure_co.stg_loop_return_line_items
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.stg_loop_return_line_items (
    _airbyte_extracted_at timestamp with time zone,
    barcode text,
    condition jsonb,
    consolidation_destination_id text,
    consolidation_tracking text,
    discount numeric,
    disposition jsonb,
    exchange_variant text,
    is_synthetic boolean,
    line_item_id text,
    outcome text,
    parent_return_reason text,
    price numeric,
    product_id text,
    provider_line_item_id text,
    provider_restock_location_id text,
    refund numeric,
    refund_item numeric,
    refund_tax numeric,
    return_comment text,
    return_id text,
    return_reason text,
    returned_at timestamp with time zone,
    sku text,
    tax numeric,
    title text,
    variant_id text,
    return_lag_segment text
);

-- ---------------------------------------------------------------------
-- client_azure_co.stg_loop_returns
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.stg_loop_returns (
    _airbyte_extracted_at timestamp with time zone,
    carrier text,
    created_at timestamp with time zone,
    currency text,
    customer text,
    destination_id text,
    edited_at timestamp with time zone,
    exchange_credit_total numeric,
    exchange_discount_total numeric,
    exchange_product_total numeric,
    exchange_tax_total numeric,
    exchange_total numeric,
    exchanges jsonb,
    gift_card text,
    gift_card_order_id text,
    gift_card_order_name text,
    handling_fee numeric,
    id text,
    is_synthetic boolean,
    label_rate text,
    label_status text,
    label_updated_at timestamp with time zone,
    label_url text,
    labels jsonb,
    multi_currency boolean,
    order_id text,
    order_name text,
    order_number text,
    origin_country text,
    origin_country_code text,
    outcome text,
    package_reference text,
    provider_order_id text,
    provider_order_number text,
    refund numeric,
    return_credit_total numeric,
    return_discount_total numeric,
    return_method jsonb,
    return_product_total numeric,
    return_tax_total numeric,
    return_total numeric,
    state text,
    status_page_url text,
    tracking_number text,
    type text,
    updated_at timestamp with time zone,
    upsell text,
    return_lag_segment text
);

-- ---------------------------------------------------------------------
-- client_azure_co.stg_meta_ad_performance
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.stg_meta_ad_performance (
    _airbyte_extracted_at timestamp with time zone,
    account_currency text,
    account_id text,
    account_name text,
    action_values jsonb,
    actions jsonb,
    ad_click_actions jsonb,
    ad_id text,
    ad_impression_actions jsonb,
    ad_name text,
    adset_id text,
    adset_name text,
    attribution_setting text,
    auction_bid text,
    auction_competitiveness text,
    auction_max_competitor_bid text,
    buying_type text,
    campaign_id text,
    campaign_name text,
    canvas_avg_view_percent text,
    canvas_avg_view_time timestamp with time zone,
    catalog_segment_actions jsonb,
    catalog_segment_value jsonb,
    catalog_segment_value_mobile_purchase_roas jsonb,
    catalog_segment_value_omni_purchase_roas jsonb,
    catalog_segment_value_website_purchase_roas jsonb,
    clicks text,
    conversion_rate_ranking text,
    conversion_values jsonb,
    conversions jsonb,
    converted_product_quantity jsonb,
    converted_product_value jsonb,
    cost_per_15_sec_video_view jsonb,
    cost_per_2_sec_continuous_video_view jsonb,
    cost_per_action_type jsonb,
    cost_per_estimated_ad_recallers numeric,
    cost_per_inline_link_click numeric,
    cost_per_inline_post_engagement numeric,
    cost_per_outbound_click jsonb,
    cost_per_thruplay jsonb,
    cost_per_unique_click numeric,
    cost_per_unique_inline_link_click numeric,
    cost_per_unique_outbound_click jsonb,
    cpc text,
    cpm text,
    cpp text,
    created_time timestamp with time zone,
    ctr text,
    date_start timestamp with time zone,
    date_stop timestamp with time zone,
    engagement_rate_ranking text,
    estimated_ad_recallers text,
    frequency text,
    full_view_impressions text,
    full_view_reach text,
    impressions text,
    inline_link_click_ctr text,
    inline_link_clicks text,
    inline_post_engagement text,
    instant_experience_clicks_to_open text,
    instant_experience_clicks_to_start text,
    instant_experience_outbound_clicks jsonb,
    is_synthetic boolean,
    mobile_app_purchase_roas jsonb,
    objective text,
    optimization_goal text,
    outbound_clicks jsonb,
    outbound_clicks_ctr jsonb,
    purchase_roas jsonb,
    qualifying_question_qualify_answer_rate text,
    quality_ranking text,
    reach text,
    social_spend text,
    spend text,
    stored_before_retention_limit boolean,
    unique_clicks text,
    unique_ctr text,
    unique_inline_link_clicks text,
    unique_link_clicks_ctr text,
    unique_outbound_clicks jsonb,
    unique_outbound_clicks_ctr jsonb,
    updated_time timestamp with time zone,
    video_15_sec_watched_actions jsonb,
    video_30_sec_watched_actions jsonb,
    video_avg_time_watched_actions jsonb,
    video_continuous_2_sec_watched_actions jsonb,
    video_p100_watched_actions jsonb,
    video_p25_watched_actions jsonb,
    video_p50_watched_actions jsonb,
    video_p75_watched_actions jsonb,
    video_p95_watched_actions jsonb,
    video_play_actions jsonb,
    video_play_curve_actions jsonb,
    video_play_retention_0_to_15s_actions jsonb,
    video_play_retention_20_to_60s_actions jsonb,
    video_play_retention_graph_actions jsonb,
    video_time_watched_actions jsonb,
    website_ctr jsonb,
    website_purchase_roas jsonb
);

-- ---------------------------------------------------------------------
-- client_azure_co.stg_meta_ad_sets
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.stg_meta_ad_sets (
    _airbyte_extracted_at timestamp with time zone,
    account_id text,
    adlabels jsonb,
    bid_amount numeric,
    bid_constraints jsonb,
    bid_info jsonb,
    bid_strategy text,
    budget_remaining text,
    campaign_id text,
    created_time timestamp with time zone,
    daily_budget text,
    effective_status text,
    end_time timestamp with time zone,
    id text,
    is_synthetic boolean,
    learning_stage_info jsonb,
    lifetime_budget timestamp with time zone,
    name text,
    promoted_object jsonb,
    start_time timestamp with time zone,
    status text,
    targeting jsonb,
    updated_time timestamp with time zone
);

-- ---------------------------------------------------------------------
-- client_azure_co.stg_meta_campaigns
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.stg_meta_campaigns (
    _airbyte_extracted_at timestamp with time zone,
    account_id text,
    adlabels jsonb,
    bid_strategy text,
    boosted_object_id text,
    budget_rebalance_flag text,
    budget_remaining text,
    buying_type text,
    configured_status text,
    created_time timestamp with time zone,
    daily_budget text,
    effective_status text,
    id text,
    is_synthetic boolean,
    issues_info jsonb,
    lifetime_budget timestamp with time zone,
    name text,
    objective text,
    smart_promotion_type text,
    source_campaign_id text,
    special_ad_category text,
    special_ad_category_country jsonb,
    spend_cap text,
    start_time timestamp with time zone,
    status text,
    stop_time timestamp with time zone,
    updated_time timestamp with time zone
);

-- ---------------------------------------------------------------------
-- client_azure_co.stg_tiktok_ad_performance
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.stg_tiktok_ad_performance (
    _airbyte_extracted_at timestamp with time zone,
    ad_id text,
    ad_name text,
    adgroup_id text,
    adgroup_name text,
    advertiser_id text,
    app_install text,
    average_video_play text,
    average_video_play_per_user text,
    campaign_id text,
    campaign_name text,
    campaign_type text,
    clicks text,
    comments text,
    conversion_rate text,
    conversions text,
    cost_per_app_install numeric,
    cost_per_conversion numeric,
    cost_per_result numeric,
    cpc text,
    cpm text,
    creative_format text,
    ctr text,
    engagements text,
    follows text,
    frequency text,
    identity_authorized_bc_id text,
    identity_id text,
    identity_type text,
    impressions text,
    is_spark_ad boolean,
    is_synthetic boolean,
    landing_page_url text,
    likes text,
    objective_type text,
    post_id text,
    profile_visits text,
    promotion_type text,
    reach text,
    real_time_conversion_rate timestamp with time zone,
    real_time_conversions timestamp with time zone,
    result text,
    result_rate text,
    shares text,
    spark_ad_type text,
    spend text,
    stat_time_day timestamp with time zone,
    utm_campaign text,
    utm_medium text,
    utm_source text,
    video_id text,
    video_play_actions text,
    video_views_p100 text,
    video_views_p25 text,
    video_views_p50 text,
    video_views_p75 text,
    video_watched_2s text,
    video_watched_6s text
);

-- ---------------------------------------------------------------------
-- client_azure_co.synthetic_customer_pii_lookup
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.synthetic_customer_pii_lookup (
    synthetic_customer_id text NOT NULL,
    hashed_email text,
    klaviyo_match_flag boolean DEFAULT false
);

ALTER TABLE client_azure_co.synthetic_customer_pii_lookup ADD CONSTRAINT synthetic_customer_pii_lookup_pkey PRIMARY KEY (synthetic_customer_id);

-- ---------------------------------------------------------------------
-- client_azure_co.synthetic_touchpoint_journey
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.synthetic_touchpoint_journey (
    order_id text NOT NULL,
    touchpoint_sequence integer NOT NULL,
    channel text,
    touchpoint_date date,
    touchpoint_type text,
    campaign_id text,
    influencer_id text
);

-- ---------------------------------------------------------------------
-- client_azure_co.tag_normalisation
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.tag_normalisation (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    raw_tag text NOT NULL,
    canonical_tag text NOT NULL,
    category text,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.tag_normalisation ADD CONSTRAINT tag_normalisation_pkey PRIMARY KEY (id);

-- ---------------------------------------------------------------------
-- client_azure_co.tiktok_billing_statement
-- ---------------------------------------------------------------------
CREATE TABLE client_azure_co.tiktok_billing_statement (
    id bigint GENERATED ALWAYS AS IDENTITY,
    client_id text NOT NULL,
    statement_month date NOT NULL,
    total_spend_exact numeric(18,6),
    total_spend_api numeric(10,2),
    rounding_gap numeric(10,6),
    currency text DEFAULT 'USD'::text,
    statement_date date,
    source text DEFAULT 'finaloop'::text,
    is_synthetic boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE client_azure_co.tiktok_billing_statement ADD CONSTRAINT tiktok_billing_statement_pkey PRIMARY KEY (id);

