# Profit Sentinel — Chat Context
## Date: 2026-05-21
## Session: Pre-Agent B Build — B-11, B-7, B-8, B-9 Execution
## Continuation of: chat_context_2026_05_21_b5_design.md

---

## Session Purpose

Claude Code execution session. Executed the pre-Agent B build sequence:
B-11 (client_config ALTER) → B-7 (Google Ads seed) → B-8 (sku_cost_master)
→ B-9 (12 new mart columns). All four complete.

All design decisions from the prior session remain locked. This file records
only new decisions and findings made during execution.

---

## Decision 1 — B-11 Scope Expanded — LOCKED

Original B-11 spec was 6 segment columns only. Expanded during session to
include 2 Google Ads connector columns bundled in the same ALTER TABLE:

Columns added:
- `repeat_customer_order_minimum` integer default 2
- `explorer_max_orders` integer default 1
- `regular_max_orders` integer default 3
- `loyalist_max_orders` integer default 6
- `advocate_min_orders` integer default 7
- `segment_significance_min_revenue_pct` numeric default 2.0
- `google_ads_connected` boolean default false
- `last_google_ads_sync` timestamptz

`google_ads_connected` set to true for `client_azure_co` after B-7 seed.
`last_google_ads_sync` set after B-7 seed completed.

---

## Decision 2 — Google Ads API Version — LOCKED

Google Ads API v24.1 confirmed (not v17 as previously assumed in state file).
State file reference to "v17" is stale — correct version is v24.1.

Confirmed field names:
- `metrics.cost_micros` → stored as `cost_micros` bigint (RAW MICROS)
- `metrics.impressions`, `metrics.clicks`, `metrics.ctr`, `metrics.average_cpc`
- `metrics.conversions`, `metrics.conversion_value`, `metrics.conversion_value_per_cost`
- `metrics.search_impression_share`, `segments.quality_score`
- `campaign.id`, `campaign.advertising_channel_type`, `ad_group.id`

PMax carve-outs confirmed:
- `ad_group_id` / `ad_group_name` → NULL (PMax uses asset_group not ad_group)
- `search_impression_share` → NULL (unavailable at campaign level for PMax)
- `quality_score` → NULL (keyword-based metric, N/A for PMax)

---

## Decision 3 — cost_micros Storage Format — LOCKED

`connectors/seed_google_ads.py` stores spend as `cost_micros` (bigint, raw micros).

**All mart SQL that reads Google Ads spend must use:**
`SUM(cost_micros) / 1000000.0 AS google_spend`

This applies to:
- `mart_causal_chain_daily` — `stockout_with_active_spend_count` column ✓ (already applied)
- `mart_causal_chain_daily` — any future `total_google_spend` column
- Agent B — any chain that references `google_spend` directly
- B-9 mart SQL — confirmed applied correctly (verified via Check 5)

---

## Decision 4 — B-8 Reseed Decision — LOCKED

Prior `sku_cost_master` had 650 stale rows (125 SKUs, wrong structure, no
step-change rows). Decision: TRUNCATE and full reseed to spec.

All 650 rows were synthetic — no real data at risk.

---

## Decision 5 — Seed Script File Location — LOCKED

All seed scripts live in `connectors/` not `tests/`.
Pattern: `connectors/seed_{source}.py`

Prior state files and `technical_architecture.md` incorrectly reference `tests/`.
This must be corrected in `technical_architecture.md` as a pending doc update.

---

## Decision 6 — B-4 Elevated to Before B-5 — LOCKED

B-4 (ad set → SKU mapping) must be built before B-5 (causal_graph.py), not after.

Reason: `top_sku_inventory_pct` is NULL until B-4 provides the SKU alias map.
`stockout_with_active_spend_count` uses brand-level spend proxy (not SKU-level)
until B-4. G-series alert precision is degraded without this.

Revised sequence: B-10 → B-4 → B-5 → B-1 → B-2 → Agent B

---

## Decision 7 — Google Ads Real-Data Nuances — NEW RISK ITEMS IDENTIFIED

Six real-data nuances identified that synthetic data does not cover and will
cause beta failures. Assigned as B-12 (real-data hardening session).

Full details in state file section "GOOGLE ADS REAL-DATA NUANCES".

Summary of fixes required:
1. ±1 day tolerance on all cross-source date joins
2. `data_lag_hours` field in `client_config` per source
3. Attribution window permanent DQ limitation entry per source (Google + Meta)
4. `PMAX_DIAGNOSTIC_BLOCKED` permanent DQ limitation entry
5. cost_micros rounding: round to 4 decimal places at mart aggregation
6. Use `campaign_type` not `campaign_name` in all founder-facing alert text

B-12 must be completed before first beta client onboards.

---

## Execution Findings — B-9

Recorded for future debugging reference:

1. **`stg_loop_returns` uses `return_date` not `created_at`** — dbt compilation
   error caught and fixed. All Loop return joins must use `return_date`.

2. **`meta_creative_by_obj` CTE correlated subquery failure** — correlated
   subquery referencing ungrouped outer columns not allowed in PostgreSQL window
   context. Rewritten as two clean CTEs. Pattern to avoid in future mart models.

3. **`mart_causal_chain_daily` is a dbt model** — `.sql` file exists in
   `warehouse/models/marts/`. It materialises to `client_azure_co_marts` schema.
   All changes must go through dbt, not raw ALTER TABLE.

4. **Inventory columns are point-in-time only** — `shopify_inventory_levels`
   snapshot exists for 2026-05-31 only. Columns 6–11 will be NULL for all other
   dates until real client data provides daily snapshots. Not a code error.

5. **`top_sku_inventory_pct` NULL** — SKU format mismatch confirmed.
   `sku_cost_master` uses text SKU `AZR-DRESS-HERO-01-XS`.
   `shopify_inventory_levels` uses integer `inventory_item_id`.
   B-4 must build the alias map to bridge these.

---

## Open Items Entering Next Session

| Item | Status |
|------|--------|
| B-10: `mart_customer_segments_daily` | First build task next session |
| B-4: ad set → SKU mapping | Elevated — before B-5 |
| B-5: `causal_graph.py` | Designed — awaiting B-10 + B-4 |
| B-1: `causal_pattern_validation` seed | Awaiting B-5 |
| B-2: `candidate_signals` seed | Awaiting B-1 |
| B-12: real-data hardening | Before beta |
| Doc updates | Apply before B-10 (see state file) |
| B-6, D-17, D-20, S3-P3 | Carry forward — unchanged |

---

## Instructions for Next Session Start

1. Load this file + `state_2026_05_21_b9_complete.md` as context
2. Load `chat_context_2026_05_21_b5_design.md` for full design decisions
   (all B-5 and B-1 design decisions remain locked — do not reopen)
3. Apply pending document updates to `technical_architecture.md` and
   `pre_agent_build_checklist.md` before any build work
4. Then proceed to B-10
