# Profit Sentinel — Chat Context
## Date: 2026-05-21
## Session: B-5 (Fashion Causal Graph) + B-1 (Chain Seed) Design Session

---

## Session Purpose

Design session for two interdependent pre-Agent B blockers:
- **B-5**: Fashion Causal Graph in code (`agents/causal_graph.py`)
- **B-1**: Seed remaining 34 of 56 hardcoded chains into `causal_pattern_validation`

All design decisions below are locked unless explicitly marked open.

---

## Decision 1 — Graph Architecture: Hardcoded Registry (Interpretation A) — LOCKED

**Decision:** `causal_graph.py` is a structured Python dict (chain registry), not a DAG traversal engine. Permanently — not as a stepping stone to DAG.

**Rationale locked:**
- Trust is the product's core moat. Every chain that fires has been explicitly practitioner-reviewed and approved. DAG traversal produces paths no practitioner has validated.
- Novel chain pipeline already handles scale — `candidate_signals` → practitioner review → hardcoded into registry. The registry grows via validated promotion, not algorithmic traversal.
- DAG debugging failure mode is disproportionate: one wrong edge poisons every path through it. One wrong hardcoded chain produces exactly one wrong alert type. Scope is contained.
- Supervised validation and dynamic graph traversal are incompatible design philosophies. This product requires the former.

**`causal_graph.py` structure per entry:**
```python
{
    "causal_chain_id": "B1",
    "leading_signal_column": "meta_ctr_7d_avg",
    "leading_signal_direction": "declining",
    "outcome_column": "meta_roas",
    "outcome_direction": "declining",
    "lag_days": 5,
    "corroborating_signals": ["meta_cpm_change_pct"],
    "mart_table": "mart_causal_chain_daily",
    "status": "active",          # active / active_proxy / mart_column_missing
    "routing": null,             # null for A-G series. internal / informational / founder_action_required for H-series
    "verification_category": "B" # A / B / C per technical_architecture.md Section 14
}
```

---

## Decision 2 — Missing Mart Columns: Option 2 (Build Scoped) — LOCKED

**Decision:** Build missing mart columns before writing `causal_graph.py`. Scope limited to columns that have real synthetic data to test against. Data-blocked columns (GA4 absent, real Meta/TikTok required) get `status: mart_column_missing` with comment.

**Two prerequisites before G-series columns can be built:**
1. Google Ads synthetic seed (full — see Decision 6)
2. `sku_cost_master` full seeding across all ~380 active variant SKUs with realistic costs, effective dates, and at least one cost step-change event (for D3 testing)

---

## Decision 3 — New Mart Columns Confirmed — LOCKED

### Columns to add to `mart_causal_chain_daily`

| Column | Logic | Alert(s) |
|--------|-------|---------|
| `discount_order_rate_90d` | `COUNT(orders with discount_codes not null) / COUNT(all orders)` trailing 90 days | D2 |
| `top_creative_spend_pct_by_objective` | JSONB: `{awareness: 0.82, sales: 0.67, ...}` — `MAX(creative_spend) / SUM(objective_spend)` per campaign objective, 7-day rolling. Filter by explicit objective field only. | B2 |
| `advantage_plus_spend_pct` | `SUM(spend where campaign_type = 'ADVANTAGE_PLUS') / SUM(total_spend)` | B2 |
| `repeat_customer_return_rate_7d` | `COUNT(returns where customer has >= client_config.repeat_customer_order_minimum prior orders) / COUNT(all returns)` trailing 7 days. Default threshold = 2. | C7 |
| `new_customer_return_rate_7d` | `COUNT(returns where customer has exactly 1 prior order) / COUNT(all returns)` trailing 7 days | A2, C3 |
| `stockout_sku_count` | `COUNT(SKUs where inventory_quantity = 0)` on date | G1 |
| `stockout_with_active_spend_count` | `COUNT(SKUs where inventory_quantity = 0 AND (meta_spend > 0 OR tiktok_spend > 0 OR google_spend > 0) on same date)` — Google Ads spend included | G1 |
| `avg_days_inventory_on_hand` | `AVG(COALESCE(inventory_quantity / NULLIF(daily_units_sold_7d_avg, 0), 999))` across all SKUs. Zero-velocity SKUs = 999 (not excluded). | G2 |
| `sell_through_rate_7d` | `SUM(units_sold_7d) / SUM(units_sold_7d + inventory_quantity)` | G2 |
| `top_sku_inventory_pct` | `MAX(sku_inventory_value) / SUM(all_inventory_value)` using `sku_cost_master` for value | G3 |
| `top_sku_inventory_units_pct` | `MAX(sku_inventory_units) / SUM(all_inventory_units)` — unit concentration, not just revenue | G3 |
| `back_in_stock_waitlist_count` | COUNT of Klaviyo back-in-stock flow subscribers active on date per SKU | G4 |

**Notes:**
- `top_creative_spend_pct_by_objective`: Advantage+ campaigns tracked separately via `advantage_plus_spend_pct` because Meta does not expose objective-level ad set boundaries for these campaigns.
- `avg_days_inventory_on_hand` 999 flag: In Agent D Evidence Stack, display 999 as "zero-velocity SKU — likely overstock or discontinued." Never display as raw number. Carry this spec into Agent D build session.
- `repeat_customer_return_rate_7d`: threshold pulled from `client_config.repeat_customer_order_minimum` (default 2). Requires ALTER TABLE on `client_config` — see Decision 4.
- `stockout_with_active_spend_count`: Google Ads spend column name must be confirmed against Google Ads API v17 docs before seeding. Do not hardcode column name.
- `back_in_stock_waitlist_count`: if no active back-in-stock Klaviyo flow detected at onboarding, queue one-time missed-opportunity message to founder (onboarding completion flow, not live alert stream): *"You have no back-in-stock flow set up in Klaviyo. Brands at your GMV tier typically recover significant revenue per restock event from waitlist customers."* Do not repeat after onboarding.

### New mart model required: `mart_customer_segments_daily`

**Grain:** date × segment

**Segments:** Explorers / Regulars / Loyalists / Advocates

**Segment boundaries:** Calibrated once at onboarding by `historical_pattern_scan.py` using k-means or percentile breakpoints on order frequency distribution from client's own data. Written to `client_config`. Locked after onboarding — never auto-adjusted post-onboarding. Founder can manually override.

**Fallback:** If repeat customer count < 500 at onboarding, use vertical defaults. Inform founder: *"We don't yet have enough repeat purchase history to calibrate your segments precisely — using contemporary womenswear defaults. We'll recalibrate after 6 months of data."*

**Default boundaries (contemporary womenswear):**
- Explorer: 1 order (`client_config.explorer_max_orders` default 1)
- Regular: 2–3 orders (`client_config.regular_max_orders` default 3)
- Loyalist: 4–6 orders (`client_config.loyalist_max_orders` default 6)
- Advocate: 7+ orders (`client_config.advocate_min_orders` default 7)

**Columns per segment:**
- `segment_customer_count` — absolute number
- `segment_pct_of_total_customers` — population share
- `segment_pct_of_total_revenue` — revenue share
- `segment_avg_roas` — revenue attributed / acquisition cost for cohort
- `segment_return_rate_7d`
- `segment_aov_7d`

**Minimum significance threshold:** `client_config.segment_significance_min_revenue_pct` default 2%. If `segment_pct_of_revenue < 2%`, Agent B suppresses segment-specific alerts for that segment. Fires informational note instead: *"Your [Segment] segment is currently too small to generate reliable signals — X% of customers, Y% of revenue."*

**Alerts that use this model:** C7, E2, E3, A2 (new customer return rate component)

---

## Decision 4 — `client_config` ALTER TABLE Requirements — LOCKED

Add the following columns before mart build session:

```sql
ALTER TABLE public.client_config
    ADD COLUMN IF NOT EXISTS repeat_customer_order_minimum integer default 2,
    ADD COLUMN IF NOT EXISTS explorer_max_orders integer default 1,
    ADD COLUMN IF NOT EXISTS regular_max_orders integer default 3,
    ADD COLUMN IF NOT EXISTS loyalist_max_orders integer default 6,
    ADD COLUMN IF NOT EXISTS advocate_min_orders integer default 7,
    ADD COLUMN IF NOT EXISTS segment_significance_min_revenue_pct numeric default 2.0;
```

---

## Decision 5 — H-Series Architecture: Option A — LOCKED

H-series chains (H1–H19) are inside `causal_graph.py` with a `routing` field.

**Three routing categories:**

| Routing value | Meaning | Example alerts |
|---------------|---------|---------------|
| `internal` | PS infrastructure problem — internal Slack only, never founder-facing unless outage >1 sync cycle | H1 (Airbyte sync gap), H12 (schema column change) |
| `informational` | Source platform problem outside founder's control — brief message, not an alert | H7 (API rate limit), H10 (Shopify infrastructure event), H16 (Meta attribution break) |
| `founder_action_required` | Founder's own configuration causing data quality loss — missed opportunity framing, not error framing | H6 (paid spend zero), H8 (Sentry instrumentation broken), H15 (Gorgias tagging drop) |

**Category 1 (internal) message protocol:**
- Message fires on detection: *"We've detected an issue with your data pipeline. We're working on it and will update you once it's resolved."*
- No time estimates. No technical detail.
- Resolution message: *"Your data pipeline is back to normal. All alerts are live again."*
- Internal alert to PS team fires immediately with full technical detail.
- Do NOT send if resolved within one sync cycle — founder never sees transient failures.

**Category 2 (informational) message format:**
Brief, factual, no action required. Example: *"Meta's API is experiencing delays. Your channel data may be up to 6 hours behind. We'll alert you once it's resolved."*

**Category 3 (founder_action_required) message format:**
Missed opportunity framing. Example: *"Your Gorgias tagging rate dropped 40% this week — I can no longer reliably predict return spikes from complaint data. This usually means agents aren't tagging tickets. Worth a 5-minute fix."*

---

## Decision 6 — Google Ads Connector: Phase 1, Full Seed Required — LOCKED

Google Ads confirmed as Phase 1 connector as of May 21 2026 (per product_strategy_updated.md).

**Seed data to include:**
- Search campaigns
- Shopping campaigns
- Performance Max (PMax)
- YouTube campaigns
- Discovery / Demand Gen campaigns
- **Exclude:** Display network

**Fields to seed (confirm exact names against Google Ads API v17 before seeding):**
- `spend`, `impressions`, `clicks`, `ctr`
- `campaign_id`, `ad_group_id` (equivalent of adset_id)
- `attributed_conversions`, `attributed_revenue`
- `average_cpc`
- `search_impression_share` (campaign level only — not available at ad group level for PMax)
- `conversion_value_per_cost` (Google's ROAS equivalent)
- `campaign_type` — Search / Shopping / PMax / YouTube / Discovery
- `quality_score`

**Prerequisite action:** Read Google Ads API v17 documentation before writing seed script. Confirm field names for PMax — reporting has specific limitations vs standard campaigns.

**Discovery interview validation item:** Add probe to subsequent interviews: *"What percentage of your Google spend goes to YouTube vs Search vs Shopping?"* If consistently <5% YouTube across 5+ interviews, deprioritise YouTube in seed and mart. Currently included based on practitioner judgment (~10–20% of Google budget at this GMV tier).

---

## Decision 7 — Complete 56-Chain Column Mapping — LOCKED

### Confirmed active chains (leading signal column exists in mart today)

| Chain | Leading signal | Outcome | Lag | Corroborating | Notes |
|-------|---------------|---------|-----|--------------|-------|
| A1 | `blended_roas` | `net_revenue` | 0 | `return_rate_pct` | |
| A2 | `meta_cpm_change_pct` | `meta_roas` | 3 | `meta_ctr_7d_avg`, `return_rate_pct`, `checkout_error_count` | |
| A3 | `meta_roas` | `tiktok_roas` | 0 | `meta_spend`, `tiktok_spend` | |
| A4 | `meta_spend` | `avg_cvr` | 0 | none | Proxy — `utm_coverage_rate` missing |
| A5 | `blended_cac_7d` | `rolling_repeat_purchase_rate_90d` | 7 | `new_customer_rate_7d` | |
| A6 | `return_rate_pct` | `net_revenue` | 21 | `avg_days_to_refund` | |
| B1 | `meta_ctr_7d_avg` | `meta_roas` | 5 | `meta_cpm_change_pct` | |
| B2 | `top_creative_spend_pct_by_objective` | `blended_roas` | 7 | `advantage_plus_spend_pct` | New column — build first |
| B3 | `tiktok_roas` | `tiktok_spend` | 7 | none | Proxy — `tiktok_organic_reach_7d` missing |
| B4 | `meta_cpm_change_pct` | `meta_roas` | 7 | `meta_ctr_7d_avg` | Proxy — `meta_frequency_7d` missing |
| B5 | `meta_spend` | `meta_roas` | 3 | `meta_ctr_7d_avg` | Proxy — `meta_learning_phase_active` missing |
| C1 | `sizing_complaint_velocity_pct` | `return_rate_pct` | 10 | `sizing_complaint_rate_7d` | |
| C2 | `return_rate_pct` | `tiktok_roas` | 21 | `avg_days_to_refund` | Brand-level proxy — creator-level in `influencer_profile` |
| C3 | `return_rate_pct` | `net_revenue` | 7 | `avg_days_to_refund` | Brand-level proxy — SKU-level in `mart_return_rate_by_sku` |
| C4 | `return_count` | `return_rate_pct` | 3 | `sizing_complaint_velocity_pct` | |
| C5 | `loop_lifestyle_change_count` | `return_rate_pct` | 0 | `sizing_complaint_rate_7d` | Proxy — `return_reason_mismatch_rate` missing |
| C6 | `return_rate_pct` | `net_revenue` | 14 | `return_count` | Agent B must check `brand_event_calendar` for collection context |
| C7 | `repeat_customer_return_rate_7d` | `rolling_repeat_purchase_rate_90d` | 14 | `loop_lifestyle_change_count` | New column — build first |
| D1 | `contribution_margin_chg_pct` | `contribution_margin_pct` | 7 | `meta_cpm_change_pct`, `return_rate_pct` | |
| D2 | `discount_order_rate_90d` | `contribution_margin_pct` | 30 | `average_order_value` | New column — build first |
| D3 | `contribution_margin_chg_pct` | `contribution_margin_pct` | 60 | `net_revenue` | Proxy — `cogs_change_detected` missing |
| D4 | `net_revenue` | `contribution_margin_pct` | 7 | `order_count` | Proxy — `per_order_fulfilment_cost_7d` missing |
| D5 | `post_purchase_flow_revenue_7d` | `klaviyo_revenue` | 14 | `effective_open_rate_7d` | |
| D6 | `contribution_margin_chg_pct` | `contribution_margin_pct` | 0 | `is_bfcm_period` | Uses `py_*` prior-year columns |
| E1 | `email_hard_bounces` | `effective_open_rate_7d` | 14 | `send_frequency_7d` | Proxy — `email_spam_complaint_rate_7d` missing |
| E2 | `rolling_repeat_purchase_rate_90d` | `net_revenue` | 30 | `new_customer_rate_7d` | |
| E3 | `vip_purchase_gap_days` | `rolling_repeat_purchase_rate_90d` | 60 | `effective_open_rate_7d` | Full signal in `mart_customer_segments_daily` |
| E4 | `post_purchase_flow_revenue_7d` | `rolling_repeat_purchase_rate_90d` | 28 | `effective_open_rate_7d` | |
| F1 | `mobile_checkout_completion_rate_7d` | `avg_cvr` | 3 | `sentry_error_count` | `mart_column_missing` — GA4 absent, data-blocked |
| F2 | `checkout_error_count` | `avg_cvr` | 0 | `sentry_error_count`, `sentry_affected_users` | |
| F3 | `total_sessions` | `avg_cvr` | 0 | `avg_bounce_rate` | Proxy — `direct_traffic_pct_7d` missing |
| F4 | `sentry_error_count` | `avg_cvr` | 1 | `ga4_pdp_bounce_rate` | Proxy — `avg_page_load_ms_7d` missing |
| F5 | `checkout_error_count` | `avg_cvr` | 1 | `mobile_checkout_completion_rate_7d` | `mart_column_missing` — step-level GA4 funnel absent |
| G1 | `stockout_with_active_spend_count` | `total_ad_spend` | 0 | `meta_spend`, `tiktok_spend` | New column — build first. Google Ads seed prerequisite. |
| G2 | `avg_days_inventory_on_hand` | `net_revenue` | 30 | `sell_through_rate_7d` | New columns — build first. sku_cost_master seed prerequisite. |
| G3 | `top_sku_inventory_pct` | `net_revenue` | 0 | `top_sku_inventory_units_pct` | New columns — build first |
| G4 | `back_in_stock_waitlist_count` | `klaviyo_revenue` | 0 | none | New column — build first |

### H-series chains (system table routing — separate Agent B code path)

| Chain | Leading signal source | Routing |
|-------|----------------------|---------|
| H1 | `dq_metric_scores` — sync gap | `internal` |
| H2 | `dq_metric_scores` — traffic source shift | `informational` |
| H3 | `dq_metric_scores` — UTM coverage | `founder_action_required` |
| H4 | `dq_metric_scores` — Klaviyo/Shopify revenue gap | `informational` |
| H5 | `dq_metric_scores` — GA4/Shopify order gap | `informational` |
| H6 | `dq_metric_scores` — spend zero | `founder_action_required` |
| H7 | `dq_events` — API rate limit | `informational` |
| H8 | `dq_metric_scores` — Sentry zero errors | `founder_action_required` |
| H9 | `dq_events` — CAPI dedup failure | `founder_action_required` |
| H10 | `dq_events` — Shopify platform event | `informational` |
| H11 | `dq_metric_scores` — DQ below threshold | `internal` |
| H12 | `schema_versions` — column type change | `internal` |
| H13 | `dq_metric_scores` — DQ improving | `internal` |
| H14 | `dq_events` — cascade DQ chain | `internal` |
| H15 | `dq_metric_scores` — Gorgias tagging drop | `founder_action_required` |
| H16 | `dq_events` — Meta attribution break | `informational` |
| H17 | `permanent_dq_limitations` — iOS ATT modeled conversion | `informational` |
| H18 | `permanent_dq_limitations` — Klaviyo open rate unreliable | `informational` |
| H19 | `permanent_dq_limitations` — permanent DQ limitation active | `informational` |

---

## Decision 8 — Mart Column Gap Classification — LOCKED

**Proxy-acceptable (active_proxy status — no new columns needed, proxy fires with uncertainty disclosure):**
- A4 (utm_coverage_rate), B3 (tiktok_organic_reach), B4 (meta_frequency), B5 (meta_learning_phase), C5 (return_reason_mismatch), D3 (cogs_change), D4 (fulfilment_cost), E1 (spam_complaint_rate), F3 (direct_traffic_pct), F4 (page_load_ms)

**Data-blocked (mart_column_missing — column structure exists, NULL until real connector data):**
- F1, F5 (GA4 funnel step data)

**Build required before B-5 (new columns, synthetic data testable):**
- B2 columns, C7, D2, G1, G2, G3, G4 (see Decision 3)

**New mart model required:**
- `mart_customer_segments_daily` — build before Agent B (see Decision 3)

---

## Decisions Still Open Entering Next Session

| Item | Status |
|------|--------|
| Build sequence for all new prerequisites — Google Ads seed, sku_cost_master seed, new mart columns, `mart_customer_segments_daily`, then B-5 + B-1 | Needs sequencing session |
| Google Ads API v17 field name verification | Must read docs before seed script |
| Discovery interview YouTube spend probe | Add to next interview |
| B-4 (G1 ad set → SKU mapping) | Still pending from prior session |
| B-6 (promotion_threshold values) | Still pending from prior session |
| D-17 (novel chain review infrastructure) | Still pending |
| D-20 (pending_connectors onboarding question) | Still pending |
| S3-P3 (stg_klaviyo_profiles column names) | Still pending |

---

## Documents to Update After This Session

| Document | Changes required |
|----------|----------------|
| `pre_agent_build_checklist.md` | All new blockers from this session as named items |
| `technical_architecture.md` | `mart_customer_segments_daily` DDL + `causal_graph.py` structure definition with `routing` field |
| `product_strategy_updated.md` | Customer segment nomenclature + onboarding calibration logic |
| `state_2026_05_21.md` | New state file — build state after today's design decisions |
