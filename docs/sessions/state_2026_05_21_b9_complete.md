# Profit Sentinel — Session State
## Date: 2026-05-21
## Session: Pre-Agent B Build — B-11, B-7, B-8, B-9 Complete
## Type: Claude Code execution session

---

## LAST COMPLETED BUILD STEP

B-9 — 12 new columns added to `mart_causal_chain_daily`. dbt green. All 5
verification checks passed.

---

## WHAT WAS COMPLETED THIS SESSION

| Item | Result |
|------|--------|
| B-11 | `client_config` ALTER TABLE — 8 columns added (6 segment + `google_ads_connected` + `last_google_ads_sync`). All defaults confirmed. |
| B-7 | Google Ads synthetic seed — 5,117 rows, 7 campaigns, API v24.1 confirmed, PMax carve-outs applied, 14-day Shopping pause seeded (Jul 15–28 2025). File: `connectors/seed_google_ads.py` |
| B-8 | `sku_cost_master` full reseed — 428 rows (420 sku_cogs + 8 gifting packages), 380 active SKUs, 40 HERO DRESS step-change pairs for D3 testing. File: `connectors/seed_sku_cost_master.py` |
| B-9 | 12 new mart columns in `mart_causal_chain_daily` — dbt green, 730 rows, all 12 columns present. |

---

## REMAINING PRE-AGENT B BLOCKERS

| Item | Status | Notes |
|------|--------|-------|
| B-4 | PENDING — ELEVATED PRIORITY | Ad set → SKU mapping. Blocks `top_sku_inventory_pct` (currently NULL) and degrades `stockout_with_active_spend_count` to brand-level proxy. Must resolve before B-5. |
| B-10 | PENDING | `mart_customer_segments_daily` new model — Explorers/Regulars/Loyalists/Advocates |
| B-5 | PENDING — designed ✓ | `causal_graph.py` hardcoded registry. All design decisions locked in chat_context_2026_05_21_b5_design.md |
| B-1 | PENDING | `causal_pattern_validation` seed — 56 chains |
| B-2 | PENDING | `candidate_signals` seed rows |
| B-6 | PENDING | `promotion_threshold` values |
| D-17 | PENDING | Novel chain review infrastructure |
| D-20 | PENDING | `pending_connectors` onboarding question |
| S3-P3 | PENDING | `stg_klaviyo_profiles` column name fix |

**Revised sequence:**
B-10 → B-4 → B-5 → B-1 → B-2 → Agent B

---

## KNOWN LIMITATIONS FROM THIS SESSION — CARRY FORWARD

### B-9 Mart Column Limitations

**Inventory columns 6–11 (stockout_sku_count through top_sku_inventory_units_pct):**
`shopify_inventory_levels` is a point-in-time snapshot (2026-05-31 only), not a
time-series. These columns will only produce meaningful time-series data when
real client data provides daily snapshots via Airbyte. Currently populated for
one date only. This is a known data architecture limitation — not a code bug.
Agent B must not fire G-series inventory alerts until time-series coverage > 30 days.

**`top_sku_inventory_pct` = NULL:**
SKU format mismatch between `sku_cost_master` (AZR-DRESS-HERO-01-XS) and
`shopify_inventory_levels` (`inventory_item_id` integer). Blocked on B-4
(ad set → SKU mapping table, which will also carry the SKU alias map).
SQL comment in mart documents this. Status: `active_proxy` with NULL until B-4 resolves.

**`back_in_stock_waitlist_count` = 0:**
No active back-in-stock Klaviyo flow detected in synthetic data. Onboarding
check will fire missed-opportunity message if absent at real client onboarding.

**`advantage_plus_spend_pct` = 0.0:**
Expected — no ADVANTAGE_PLUS campaign type in synthetic Meta data.
Will populate with real client data.

---

## GOOGLE ADS REAL-DATA NUANCES — NOT YET HANDLED (BETA RISK)

These gaps will cause failures when real client Google Ads data connects.
Must be resolved before beta. Assigned as B-12.

| Gap | Risk | Fix required |
|-----|------|-------------|
| Data timing lag | Google Ads conversions lag 24–48 hours. Mart date joins produce false zero-conversion days. | Add ±1 day tolerance to all cross-source date joins. Add `data_lag_hours` field to `client_config` per source. |
| Attribution window mismatch | Google = last-click. Meta = 7-day click / 1-day view. Blended ROAS mixes windows — structural lie. | Add `attribution_window_note` as permanent DQ limitation entry per source. Disclose in Evidence Stack Layer 0. |
| PMax opacity | Google withholds asset-level and search term data for PMax. Agent D cannot populate Evidence Stack Layer 2 for PMax alerts. | Add permanent DQ limitation entry: `PMAX_DIAGNOSTIC_BLOCKED`. Max confidence cap on G-series PMax alerts. |
| Stockout date boundary | Google spend data for Day N arrives Day N+1. Inventory snapshot at midnight Day N. Join misses by one day. | ±1 day tolerance fix (same as timing lag fix above). |
| cost_micros rounding | Summing 50 ad sets in micros then dividing produces different results vs dividing each row. | Round to 4 decimal places at mart aggregation layer. |
| Campaign name instability | Real accounts rename/duplicate/archive campaigns. | Join on `campaign_type` not name. Any founder-facing alert must use `campaign_type` not `campaign_name`. |

---

## PENDING DOCUMENT UPDATES — APPLY IN NEXT SESSION BEFORE BUILDING

Claude Code must apply these changes as the FIRST step of the next session,
before starting B-10:

| Document | Change required |
|----------|----------------|
| `technical_architecture.md` | 1. Seed scripts live in `connectors/` not `tests/` — update all references. 2. Add inventory columns 6–11 point-in-time caveat. 3. Add B-4 dependency note on `top_sku_inventory_pct`. 4. Add Google Ads real-data nuances section (6 items above). |
| `pre_agent_build_checklist.md` | 1. Mark B-11, B-7, B-8, B-9 COMPLETE. 2. Elevate B-4 to ELEVATED PRIORITY. 3. Add B-12 (real-data hardening before beta). 4. Update sequence: B-10 → B-4 → B-5 → B-1 → B-2 → Agent B. |

---

## GOOGLE ADS SEED — KEY FACTS FOR DOWNSTREAM USE

- File: `connectors/seed_google_ads.py`
- Table: `client_azure_co.google_ads_performance`
- API version confirmed: v24.1
- Spend stored as: `cost_micros` (bigint — RAW MICROS, not converted)
- **All mart SQL reading google_spend must divide cost_micros by 1,000,000**
- Rows: 5,117 (7 campaigns × 731 days)
- Campaign types: SEARCH / SHOPPING / PERFORMANCE_MAX / VIDEO / DEMAND_GEN
- PMax carve-outs: `ad_group_id` = NULL, `search_impression_share` = NULL, `quality_score` = NULL
- 14-day zero-spend window: G_SHOP_001 paused Jul 15–28 2025 (Shopping campaign)
- `last_google_ads_sync` set on `client_config` for `client_azure_co`

---

## SKU COST MASTER — KEY FACTS FOR DOWNSTREAM USE

- File: `connectors/seed_sku_cost_master.py`
- Table: `client_azure_co.sku_cost_master`
- Rows: 428 total (420 sku_cogs + 8 gifting packages)
- Active SKUs: 380 (effective_to IS NULL)
- SKU format: `AZR-{CATEGORY}-{STYLE}-{SIZE}` — does NOT match `inventory_item_id` integer in `shopify_inventory_levels`. B-4 must build alias map.
- Cost step-change: 40 HERO DRESS SKUs, two rows each. Old row effective_to = 2025-08-31. New row effective_from = 2025-09-01. Supplier cost +18–22%. Used for D3 chain testing.
- Landed cost = supplier_cost × 1.28
- 8 gifting packages match 8 TikTok influencer campaigns (INF_001–INF_008)

---

## KNOWN SCHEMA DRIFT — CARRY FORWARD

- `alert_log` column: `alert_type` (NOT `signal_type`)
- `alert_log` column: `evidence_stack_json` (NOT `evidence_stack`)
- `signal_value` + `threshold_value` are separate numerics (NOT `signal_values` jsonb)
- `client_id` throughout: `client_azure_co` (NOT `azure_co`)
- Airbyte drops columns not in schema on sync → `is_synthetic` lives in `stg_*` for Airbyte sources
- Meta attribution window hard break: January 12 2026
- `brand_event_calendar` has zero rows in synthetic data
- `stg_klaviyo_profiles` columns: `profile_id` (not `customer_id`), `vip_status` (not `is_vip`)
- `stg_loop_refunds` not present — use `stg_loop_returns`
- `stg_loop_returns` exposes `return_date` not `created_at`
- `stg_meta_ad_performance` has no `attributed_revenue` — proxy: spend × purchase_roas
- `stg_klaviyo_flows` has no date column — use `stg_klaviyo_email_events`
- GA4 tables absent in synthetic data — NULL mart columns expected
- `dq_metric_scores.score_date` stored as `timestamptz` not `date`
- `public.onboarding_messages` — live table, created by `historical_pattern_scan.py`

---

## AGENT D DISPLAY RULES — CARRY FORWARD

- `avg_days_inventory_on_hand` = 999 must display as "zero-velocity SKU — likely overstock or discontinued." Never as raw number.
- PMax alerts: Evidence Stack Layer 2 incomplete by design. Agent D must disclose: "Google does not provide asset-level reporting for Performance Max campaigns — diagnostic detail is limited for this campaign type."

---

## BUILD SEQUENCE STATUS

| Step | Description | Status |
|------|-------------|--------|
| 1–10.5 | All prior steps | Complete ✓ |
| 11 | historical_pattern_scan.py | Complete ✓ |
| 11.5a | client_config ALTER TABLE (B-11) | Complete ✓ |
| 11.5b | Google Ads seed (B-7) | Complete ✓ |
| 11.5c | sku_cost_master full seed (B-8) | Complete ✓ |
| 11.5d | 12 new mart columns (B-9) | Complete ✓ |
| 11.5e | mart_customer_segments_daily (B-10) | NEXT |
| 11.5f | B-4: ad set → SKU mapping | PENDING — ELEVATED |
| 11.5g | causal_graph.py (B-5) | PENDING — designed ✓ |
| 11.5h | causal_pattern_validation seed (B-1) | PENDING |
| 11.5i | candidate_signals seed (B-2) | PENDING |
| 11.5j | Real-data hardening (B-12) | PENDING — before beta |
| 12 | Agent B | PENDING |
| 13 | Agent C | PENDING |
| 14 | Agent D | PENDING |
