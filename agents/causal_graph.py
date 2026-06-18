"""
Fashion Causal Graph — Profit Sentinel B-5

Hardcoded registry of 57 validated causal chains.

Architecture: structured dict (permanently not DAG). Each entry is
practitioner-reviewed. Novel chains are discovered via candidate_signals
→ practitioner review → promoted here. Never replace with algorithmic
traversal — trust requires explicit validation per Decision 1.

Mart column status confirmed 2026-05-22 (before writing this file):
  google_spend:             NOT in mart_causal_chain_daily SELECT.
                            Computed in google_spend_daily CTE but used
                            only in inventory_metrics (stockout logic).
                            Not an output column.
  google_roas:              ABSENT from both mart models.
  google_attributed_orders: ABSENT from both mart models.

  A3 status: active_proxy  — google_roas absent; meta + tiktok only until built.
  A4 status: active_proxy  — google_attributed_orders absent; utm_coverage_rate
                             also absent (original proxy condition unchanged).

cost_micros note: google_spend at mart layer = SUM(cost_micros)/1000000.0.
Conversion is done in the mart CTE. Do NOT divide again in Agent B logic.
"""

from typing import Any, Dict, List, Optional

FASHION_CAUSAL_GRAPH: Dict[str, Dict[str, Any]] = {

    # ── A-SERIES: Channel & Revenue Signals ──────────────────────────────────

    "A1": {
        "causal_chain_id":          "A1",
        "leading_signal_column":    "blended_roas",
        "leading_signal_direction": "declining",
        "outcome_column":           "net_revenue",
        "outcome_direction":        "declining",
        "lag_days":                 0,
        "corroborating_signals":    ["return_rate_pct"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "C",
    },

    "A2": {
        "causal_chain_id":          "A2",
        "leading_signal_column":    "meta_cpm_change_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           "meta_roas",
        "outcome_direction":        "declining",
        "lag_days":                 3,
        "corroborating_signals":    [
            "meta_ctr_7d_avg",
            "return_rate_pct",
            "checkout_error_count",
        ],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "A3": {
        # Channel ROAS Ranking Reversal — meta + tiktok active; google pending.
        # google_roas ABSENT from mart_causal_chain_daily — status active_proxy.
        # google_spend ABSENT from mart SELECT (intermediate CTE only).
        # When google_roas and google_spend are added to the mart SELECT,
        # update corroborating_signals and change status to "active".
        # Baseline check: Agent B must verify min_days non-NULL data per channel
        # before including that channel in the ranking comparison (soft fire —
        # alert fires on channels with sufficient history, excluded channels get
        # Layer 0 disclosure in Agent D Evidence Stack).
        "causal_chain_id":          "A3",
        "leading_signal_column":    "meta_roas",
        "leading_signal_direction": "declining",
        "outcome_column":           "tiktok_roas",
        "outcome_direction":        "any",
        "lag_days":                 0,
        "corroborating_signals":    [
            "tiktok_roas",
            "meta_spend",
            "tiktok_spend",
            # "google_roas",   -- not yet in mart SELECT; add when B-9 extended
            # "google_spend",  -- not yet in mart SELECT (intermediate CTE only)
        ],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
        "baseline_requirements": {
            "meta":   {"min_days": 60, "column": "meta_roas"},
            "tiktok": {"min_days": 60, "column": "tiktok_roas"},
            "google": {"min_days": 60, "column": "google_roas"},
        },
    },

    "A4": {
        # Attribution Model Inconsistency.
        # utm_coverage_rate absent — proxy status from original design.
        # google_attributed_orders absent from mart — add when B-9 extended.
        "causal_chain_id":          "A4",
        "leading_signal_column":    "meta_spend",
        "leading_signal_direction": "rising",
        "outcome_column":           "avg_cvr",
        "outcome_direction":        "any",
        "lag_days":                 0,
        "corroborating_signals":    [
            # "utm_coverage_rate",          -- absent (original proxy condition)
            # "google_attributed_orders",   -- not yet in mart; add when B-9 extended
        ],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "A5": {
        "causal_chain_id":          "A5",
        "leading_signal_column":    "blended_cac_7d",
        "leading_signal_direction": "rising",
        "outcome_column":           "rolling_repeat_purchase_rate_90d",
        "outcome_direction":        "declining",
        "lag_days":                 7,
        "corroborating_signals":    ["new_customer_rate_7d"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "A6": {
        "causal_chain_id":          "A6",
        "leading_signal_column":    "return_rate_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           "net_revenue",
        "outcome_direction":        "declining",
        "lag_days":                 21,
        "corroborating_signals":    ["avg_days_to_refund"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "A7": {
        # Wholesale Order Contamination Warning.
        # mart_column_missing: wholesale_order_rate_pct not yet in mart_causal_chain_daily.
        # Build: derive from shopify_orders where order_tags ILIKE '%wholesale%'
        #        or sales_channel = 'wholesale_portal'
        # Seed: tag ~15% of synthetic shopify_orders rows as wholesale before activating.
        "causal_chain_id":          "A7",
        "leading_signal_column":    "wholesale_order_rate_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           "blended_roas",
        "outcome_direction":        "any",
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "mart_column_missing",
        "routing":                  None,
        "verification_category":    "A",
        "firing_rule":              "threshold",
        "threshold_value":          0.20,
        "threshold_direction":      "above",
        "fire_frequency":           "onboarding_then_monthly",
        "alert_rationale":          (
            "Wholesale orders exceeding 20% of total Shopify orders contaminate "
            "blended ROAS, return rate, and contribution margin figures. "
            "Founder may be optimising paid spend against a distorted baseline."
        ),
    },

    # ── B-SERIES: Creative & Campaign Signals ────────────────────────────────

    "B1": {
        "causal_chain_id":          "B1",
        "leading_signal_column":    "meta_ctr_7d_avg",
        "leading_signal_direction": "declining",
        "outcome_column":           "meta_roas",
        "outcome_direction":        "declining",
        "lag_days":                 5,
        "corroborating_signals":    ["meta_cpm_change_pct"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "B2": {
        "causal_chain_id":          "B2",
        "leading_signal_column":    "top_creative_spend_pct_by_objective",
        "leading_signal_direction": "rising",
        "outcome_column":           "blended_roas",
        "outcome_direction":        "declining",
        "lag_days":                 7,
        "corroborating_signals":    ["advantage_plus_spend_pct"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "B3": {
        # Proxy: tiktok_organic_reach_7d absent — brand-level ROAS used.
        "causal_chain_id":          "B3",
        "leading_signal_column":    "tiktok_roas",
        "leading_signal_direction": "declining",
        "outcome_column":           "tiktok_spend",
        "outcome_direction":        "declining",
        "lag_days":                 7,
        "corroborating_signals":    [],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "B4": {
        # Proxy: meta_frequency_7d absent.
        "causal_chain_id":          "B4",
        "leading_signal_column":    "meta_cpm_change_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           "meta_roas",
        "outcome_direction":        "declining",
        "lag_days":                 7,
        "corroborating_signals":    ["meta_ctr_7d_avg"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "B5": {
        # Proxy: meta_learning_phase_active absent — not seedable synthetically.
        "causal_chain_id":          "B5",
        "leading_signal_column":    "meta_spend",
        "leading_signal_direction": "rising",
        "outcome_column":           "meta_roas",
        "outcome_direction":        "declining",
        "lag_days":                 3,
        "corroborating_signals":    ["meta_ctr_7d_avg"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    # ── C-SERIES: Returns & Product Quality Signals ──────────────────────────

    "C1": {
        "causal_chain_id":          "C1",
        "leading_signal_column":    "sizing_complaint_velocity_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           "return_rate_pct",
        "outcome_direction":        "rising",
        "lag_days":                 10,
        "corroborating_signals":    ["sizing_complaint_rate_7d"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "C",
    },

    "C2": {
        # Brand-level proxy — creator-level signal in influencer_profile (not yet built).
        "causal_chain_id":          "C2",
        "leading_signal_column":    "return_rate_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           "tiktok_roas",
        "outcome_direction":        "declining",
        "lag_days":                 21,
        "corroborating_signals":    ["avg_days_to_refund"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "C3": {
        # Brand-level proxy — SKU-level signal in mart_return_rate_by_sku.
        "causal_chain_id":          "C3",
        "leading_signal_column":    "return_rate_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           "net_revenue",
        "outcome_direction":        "declining",
        "lag_days":                 7,
        "corroborating_signals":    ["avg_days_to_refund"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "C4": {
        "causal_chain_id":          "C4",
        "leading_signal_column":    "return_count",
        "leading_signal_direction": "rising",
        "outcome_column":           "return_rate_pct",
        "outcome_direction":        "rising",
        "lag_days":                 3,
        "corroborating_signals":    ["sizing_complaint_velocity_pct"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "C5": {
        # Proxy: return_reason_mismatch_rate absent.
        "causal_chain_id":          "C5",
        "leading_signal_column":    "loop_lifestyle_change_count",
        "leading_signal_direction": "rising",
        "outcome_column":           "return_rate_pct",
        "outcome_direction":        "rising",
        "lag_days":                 0,
        "corroborating_signals":    ["sizing_complaint_rate_7d"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "C6": {
        # Agent B must check brand_event_calendar for collection launch context
        # before firing — collection launches make return rate spikes expected.
        "causal_chain_id":          "C6",
        "leading_signal_column":    "return_rate_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           "net_revenue",
        "outcome_direction":        "declining",
        "lag_days":                 14,
        "corroborating_signals":    ["return_count"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "C",
    },

    "C7": {
        "causal_chain_id":          "C7",
        "leading_signal_column":    "repeat_customer_return_rate_7d",
        "leading_signal_direction": "rising",
        "outcome_column":           "rolling_repeat_purchase_rate_90d",
        "outcome_direction":        "declining",
        "lag_days":                 14,
        "corroborating_signals":    ["loop_lifestyle_change_count"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "C",
    },

    # ── D-SERIES: Margin & Financial Signals ─────────────────────────────────

    "D1": {
        "causal_chain_id":          "D1",
        "leading_signal_column":    "contribution_margin_chg_pct",
        "leading_signal_direction": "declining",
        "outcome_column":           "contribution_margin_pct",
        "outcome_direction":        "declining",
        "lag_days":                 7,
        "corroborating_signals":    ["meta_cpm_change_pct", "return_rate_pct"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "D2": {
        "causal_chain_id":          "D2",
        "leading_signal_column":    "discount_order_rate_90d",
        "leading_signal_direction": "rising",
        "outcome_column":           "contribution_margin_pct",
        "outcome_direction":        "declining",
        "lag_days":                 30,
        "corroborating_signals":    ["average_order_value"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "D3": {
        # Proxy: cogs_change_detected absent — sku_cost_master step-change used as proxy.
        "causal_chain_id":          "D3",
        "leading_signal_column":    "contribution_margin_chg_pct",
        "leading_signal_direction": "declining",
        "outcome_column":           "contribution_margin_pct",
        "outcome_direction":        "declining",
        "lag_days":                 60,
        "corroborating_signals":    ["net_revenue"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "D4": {
        # Proxy: per_order_fulfilment_cost_7d absent.
        "causal_chain_id":          "D4",
        "leading_signal_column":    "net_revenue",
        "leading_signal_direction": "rising",
        "outcome_column":           "contribution_margin_pct",
        "outcome_direction":        "declining",
        "lag_days":                 7,
        "corroborating_signals":    ["order_count"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "D5": {
        "causal_chain_id":          "D5",
        "leading_signal_column":    "post_purchase_flow_revenue_7d",
        "leading_signal_direction": "declining",
        "outcome_column":           "klaviyo_revenue",
        "outcome_direction":        "declining",
        "lag_days":                 14,
        "corroborating_signals":    ["effective_open_rate_7d"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "D6": {
        # BFCM seasonality chain — uses py_* prior-year baseline columns.
        "causal_chain_id":          "D6",
        "leading_signal_column":    "contribution_margin_chg_pct",
        "leading_signal_direction": "declining",
        "outcome_column":           "contribution_margin_pct",
        "outcome_direction":        "declining",
        "lag_days":                 0,
        "corroborating_signals":    ["is_bfcm_period"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    # ── E-SERIES: Retention & Email Signals ──────────────────────────────────

    "E1": {
        # Proxy: email_spam_complaint_rate_7d absent.
        "causal_chain_id":          "E1",
        "leading_signal_column":    "email_hard_bounces",
        "leading_signal_direction": "rising",
        "outcome_column":           "effective_open_rate_7d",
        "outcome_direction":        "declining",
        "lag_days":                 14,
        "corroborating_signals":    ["send_frequency_7d"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "E2": {
        "causal_chain_id":          "E2",
        "leading_signal_column":    "rolling_repeat_purchase_rate_90d",
        "leading_signal_direction": "declining",
        "outcome_column":           "net_revenue",
        "outcome_direction":        "declining",
        "lag_days":                 30,
        "corroborating_signals":    ["new_customer_rate_7d"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "E3": {
        # Full VIP signal in mart_customer_segments_daily; proxy available in
        # mart_causal_chain_daily via vip_purchase_gap_days.
        "causal_chain_id":          "E3",
        "leading_signal_column":    "vip_purchase_gap_days",
        "leading_signal_direction": "rising",
        "outcome_column":           "rolling_repeat_purchase_rate_90d",
        "outcome_direction":        "declining",
        "lag_days":                 60,
        "corroborating_signals":    ["effective_open_rate_7d"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "C",
    },

    "E4": {
        "causal_chain_id":          "E4",
        "leading_signal_column":    "post_purchase_flow_revenue_7d",
        "leading_signal_direction": "declining",
        "outcome_column":           "rolling_repeat_purchase_rate_90d",
        "outcome_direction":        "declining",
        "lag_days":                 28,
        "corroborating_signals":    ["effective_open_rate_7d"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    # ── F-SERIES: Conversion & Technical Signals ─────────────────────────────

    "F1": {
        # mart_column_missing: mobile_checkout_completion_rate_7d requires
        # stg_ga4_devices (ga4_devices source absent from synthetic data).
        "causal_chain_id":          "F1",
        "leading_signal_column":    "mobile_checkout_completion_rate_7d",
        "leading_signal_direction": "declining",
        "outcome_column":           "avg_cvr",
        "outcome_direction":        "declining",
        "lag_days":                 3,
        "corroborating_signals":    ["sentry_error_count"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "mart_column_missing",
        "routing":                  None,
        "verification_category":    "B",
    },

    "F2": {
        "causal_chain_id":          "F2",
        "leading_signal_column":    "checkout_error_count",
        "leading_signal_direction": "rising",
        "outcome_column":           "avg_cvr",
        "outcome_direction":        "declining",
        "lag_days":                 0,
        "corroborating_signals":    ["sentry_error_count", "sentry_affected_users"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "F3": {
        # Proxy: direct_traffic_pct_7d absent.
        "causal_chain_id":          "F3",
        "leading_signal_column":    "total_sessions",
        "leading_signal_direction": "declining",
        "outcome_column":           "avg_cvr",
        "outcome_direction":        "declining",
        "lag_days":                 0,
        "corroborating_signals":    ["avg_bounce_rate"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "F4": {
        # Proxy: avg_page_load_ms_7d absent.
        "causal_chain_id":          "F4",
        "leading_signal_column":    "sentry_error_count",
        "leading_signal_direction": "rising",
        "outcome_column":           "avg_cvr",
        "outcome_direction":        "declining",
        "lag_days":                 1,
        "corroborating_signals":    ["ga4_pdp_bounce_rate"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active_proxy",
        "routing":                  None,
        "verification_category":    "B",
    },

    "F5": {
        # mart_column_missing: step-level GA4 checkout funnel absent.
        "causal_chain_id":          "F5",
        "leading_signal_column":    "checkout_error_count",
        "leading_signal_direction": "rising",
        "outcome_column":           "avg_cvr",
        "outcome_direction":        "declining",
        "lag_days":                 1,
        "corroborating_signals":    ["mobile_checkout_completion_rate_7d"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "mart_column_missing",
        "routing":                  None,
        "verification_category":    "B",
    },

    # ── G-SERIES: Inventory Signals ──────────────────────────────────────────

    "G1": {
        # stockout_with_active_spend_count includes google_spend via the
        # inventory_metrics CTE (google_spend_daily joined internally).
        "causal_chain_id":          "G1",
        "leading_signal_column":    "stockout_with_active_spend_count",
        "leading_signal_direction": "rising",
        "outcome_column":           "total_ad_spend",
        "outcome_direction":        "declining",
        "lag_days":                 0,
        "corroborating_signals":    ["meta_spend", "tiktok_spend"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "G2": {
        # avg_days_inventory_on_hand = 999 means zero-velocity SKU.
        # Agent D must display 999 as "zero-velocity SKU — likely overstock
        # or discontinued." Never display the raw value 999 to the founder.
        "causal_chain_id":          "G2",
        "leading_signal_column":    "avg_days_inventory_on_hand",
        "leading_signal_direction": "declining",
        "outcome_column":           "net_revenue",
        "outcome_direction":        "declining",
        "lag_days":                 30,
        "corroborating_signals":    ["sell_through_rate_7d"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "G3": {
        "causal_chain_id":          "G3",
        "leading_signal_column":    "top_sku_inventory_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           "net_revenue",
        "outcome_direction":        "declining",
        "lag_days":                 0,
        "corroborating_signals":    ["top_sku_inventory_units_pct"],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    "G4": {
        "causal_chain_id":          "G4",
        "leading_signal_column":    "back_in_stock_waitlist_count",
        "leading_signal_direction": "rising",
        "outcome_column":           "klaviyo_revenue",
        "outcome_direction":        "rising",
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "mart_causal_chain_daily",
        "status":                   "active",
        "routing":                  None,
        "verification_category":    "B",
    },

    # ── H-SERIES: System & Data Quality Signals ──────────────────────────────
    # H-series uses a separate Agent B code path (routing field is non-null).
    # These are event-driven, not continuous causal chains. outcome_column and
    # outcome_direction are None — Agent B dispatches on routing value alone.
    #
    # Routing categories (Decision 5):
    #   internal               — PS infrastructure; never founder-facing unless
    #                            outage exceeds one sync cycle.
    #   informational          — Platform event outside founder's control;
    #                            brief message, no action required.
    #   founder_action_required — Founder's own config causing DQ loss;
    #                            missed opportunity framing, not error framing.

    "H1": {
        # Airbyte sync gap — source data stops arriving.
        "causal_chain_id":          "H1",
        "leading_signal_column":    "last_sync_hours_ago",
        "leading_signal_direction": "rising",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_metric_scores",
        "status":                   "active",
        "routing":                  "internal",
        "verification_category":    "A",
    },

    "H2": {
        # Traffic source shift — sudden channel mix change may indicate UTM break.
        "causal_chain_id":          "H2",
        "leading_signal_column":    "traffic_source_shift_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_metric_scores",
        "status":                   "active",
        "routing":                  "informational",
        "verification_category":    "A",
    },

    "H3": {
        # UTM coverage drop — paid traffic landing without UTM parameters.
        "causal_chain_id":          "H3",
        "leading_signal_column":    "utm_coverage_rate",
        "leading_signal_direction": "declining",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_metric_scores",
        "status":                   "active",
        "routing":                  "founder_action_required",
        "verification_category":    "A",
    },

    "H4": {
        # Klaviyo/Shopify revenue gap — significant divergence between systems.
        "causal_chain_id":          "H4",
        "leading_signal_column":    "klaviyo_shopify_revenue_gap_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_metric_scores",
        "status":                   "active",
        "routing":                  "informational",
        "verification_category":    "A",
    },

    "H5": {
        # GA4/Shopify order gap — GA4 purchase events diverging from Shopify orders.
        "causal_chain_id":          "H5",
        "leading_signal_column":    "ga4_shopify_order_gap_pct",
        "leading_signal_direction": "rising",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_metric_scores",
        "status":                   "active",
        "routing":                  "informational",
        "verification_category":    "A",
    },

    "H6": {
        # Paid spend drops to zero — potential campaign pause or billing issue.
        "causal_chain_id":          "H6",
        "leading_signal_column":    "spend_zero_days_streak",
        "leading_signal_direction": "rising",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_metric_scores",
        "status":                   "active",
        "routing":                  "founder_action_required",
        "verification_category":    "A",
    },

    "H7": {
        # API rate limit event — source platform throttling Airbyte connector.
        "causal_chain_id":          "H7",
        "leading_signal_column":    "api_rate_limit_event",
        "leading_signal_direction": "any",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_events",
        "status":                   "active",
        "routing":                  "informational",
        "verification_category":    "A",
    },

    "H8": {
        # Sentry zero errors for sustained streak — instrumentation may be broken.
        "causal_chain_id":          "H8",
        "leading_signal_column":    "sentry_zero_error_streak",
        "leading_signal_direction": "rising",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_metric_scores",
        "status":                   "active",
        "routing":                  "founder_action_required",
        "verification_category":    "A",
    },

    "H9": {
        # Meta CAPI dedup failure — server-side conversion events firing twice.
        "causal_chain_id":          "H9",
        "leading_signal_column":    "capi_dedup_failure_rate",
        "leading_signal_direction": "rising",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_events",
        "status":                   "active",
        "routing":                  "founder_action_required",
        "verification_category":    "A",
    },

    "H10": {
        # Shopify platform event — outage or degradation on Shopify's infrastructure.
        "causal_chain_id":          "H10",
        "leading_signal_column":    "shopify_platform_event_detected",
        "leading_signal_direction": "any",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_events",
        "status":                   "active",
        "routing":                  "informational",
        "verification_category":    "A",
    },

    "H11": {
        # Overall DQ score drops below acceptable threshold.
        "causal_chain_id":          "H11",
        "leading_signal_column":    "overall_dq_score",
        "leading_signal_direction": "declining",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_metric_scores",
        "status":                   "active",
        "routing":                  "internal",
        "verification_category":    "A",
    },

    "H12": {
        # Schema column type change — Airbyte or source platform changed a field type.
        "causal_chain_id":          "H12",
        "leading_signal_column":    "column_type_change_detected",
        "leading_signal_direction": "any",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "schema_versions",
        "status":                   "active",
        "routing":                  "internal",
        "verification_category":    "A",
    },

    "H13": {
        # DQ score improving — internal signal only, no founder-facing message.
        "causal_chain_id":          "H13",
        "leading_signal_column":    "overall_dq_score",
        "leading_signal_direction": "rising",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_metric_scores",
        "status":                   "active",
        "routing":                  "internal",
        "verification_category":    "A",
    },

    "H14": {
        # Cascade DQ failure — multiple sources failing simultaneously.
        "causal_chain_id":          "H14",
        "leading_signal_column":    "cascade_dq_event_count",
        "leading_signal_direction": "rising",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_events",
        "status":                   "active",
        "routing":                  "internal",
        "verification_category":    "A",
    },

    "H15": {
        # Gorgias ticket tagging rate drops — C1 (sizing complaint → return spike)
        # cannot fire reliably without accurate tags.
        "causal_chain_id":          "H15",
        "leading_signal_column":    "gorgias_tagging_rate",
        "leading_signal_direction": "declining",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_metric_scores",
        "status":                   "active",
        "routing":                  "founder_action_required",
        "verification_category":    "A",
    },

    "H16": {
        # Meta attribution model break — deprecated view window changed by Meta.
        "causal_chain_id":          "H16",
        "leading_signal_column":    "meta_attribution_break_detected",
        "leading_signal_direction": "any",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "dq_events",
        "status":                   "active",
        "routing":                  "informational",
        "verification_category":    "A",
    },

    "H17": {
        # Permanent DQ limitation: iOS ATT modeled conversion active.
        # Informs founder that Meta conversions include modeled (estimated) data.
        "causal_chain_id":          "H17",
        "leading_signal_column":    "ios_att_modeled_conversion_active",
        "leading_signal_direction": "any",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "permanent_dq_limitations",
        "status":                   "active",
        "routing":                  "informational",
        "verification_category":    "A",
    },

    "H18": {
        # Permanent DQ limitation: Klaviyo open rate inflated by Apple MPP.
        "causal_chain_id":          "H18",
        "leading_signal_column":    "klaviyo_open_rate_unreliable",
        "leading_signal_direction": "any",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "permanent_dq_limitations",
        "status":                   "active",
        "routing":                  "informational",
        "verification_category":    "A",
    },

    "H19": {
        # Any permanent DQ limitation active — catch-all disclosure trigger.
        "causal_chain_id":          "H19",
        "leading_signal_column":    "permanent_dq_limitation_active",
        "leading_signal_direction": "any",
        "outcome_column":           None,
        "outcome_direction":        None,
        "lag_days":                 0,
        "corroborating_signals":    [],
        "mart_table":               "permanent_dq_limitations",
        "status":                   "active",
        "routing":                  "informational",
        "verification_category":    "A",
    },
}


def get_chain(chain_id: str) -> Dict[str, Any]:
    """Return a single chain entry by ID. Raises KeyError if not found."""
    return FASHION_CAUSAL_GRAPH[chain_id]


def active_chains() -> Dict[str, Dict[str, Any]]:
    """Return all chains with status 'active'."""
    return {k: v for k, v in FASHION_CAUSAL_GRAPH.items() if v["status"] == "active"}


def chains_by_mart(mart_table: str) -> Dict[str, Dict[str, Any]]:
    """Return all chains that read from a given mart table."""
    return {
        k: v for k, v in FASHION_CAUSAL_GRAPH.items()
        if v["mart_table"] == mart_table
    }
