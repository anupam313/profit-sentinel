# Profit Sentinel — Pre-Agent Build Checklist
*Last updated: 2026-05-18*
*Purpose: Track all outstanding gaps that must be
resolved before each agent build begins. Update
status after every relevant session.*

---

## PRE-AGENT A GAPS
Agent A reads mart_causal_chain_daily only.
All items below must be complete before Step 9.

| # | Gap | Status | Notes |
|---|-----|--------|-------|
| A-1 | stg_shopify_inventory_levels | COMPLETE ✓ | Required for G2/G3 |
| A-2 | stg_shopify_inventory_items | COMPLETE ✓ | Required for G2/G3, D3 COGS |
| A-3 | stg_synthetic_touchpoint_journey | COMPLETE ✓ | Required for A1, A4 |
| A-4 | Staleness flags in mart_causal_chain_daily | COMPLETE ✓ | Commit c6c5818 |
| A-5 | client_id var correct in dbt_project.yml | COMPLETE ✓ | Commit 2cad0e6 |
| A-6 | generate_schema_name macro | COMPLETE ✓ | Commit 2cad0e6 |
| A-7 | Step 7 validation matrix (37 alerts) | COMPLETE ✓ | 2026-05-18. 27 PASS, 6 PARTIAL, 4 FAIL (non-blocking). See step7_gaps below |

### Step 7 Gaps (found during validation — not blocking Agent A Step 8)

| # | Gap | Impacts | Notes |
|---|-----|---------|-------|
| A-7a | `meta_cpm_change_pct`, `meta_roas_change_pct` not in mart | A2, B4 | Agent A must compute from stg_meta_ad_performance; staging proxy confirmed 68 ROAS-drop days, 109 CPM-spike days |
| A-7b | `meta_ctr_7d_avg`, `meta_cpm_7d_avg` rolling cols not in mart | B1 | Alert seeded (13 rows); mart must expose these for Agent A threshold scan |
| A-7c | `predicted_return_spike_risk`, sizing complaint cols not in mart | C1 | Alert5 seeded (8 rows); Agent A derives from stg_gorgias_tickets + stg_loop_returns |
| A-7d | `contribution_margin_change_pct`, `using_prior_year_baseline` not in mart | D1, D6 | py_* columns present (366 days); Agent A computes proxy from py_gross_revenue |
| A-7e | `loop_lifestyle_change_count`, `loop_fit_quality_count` not in mart | C7 | lifestyle keyword absent from stg_loop_returns.return_reasons; seed gap |
| A-7f | `stg_klaviyo_profiles` staging view not built | E1–E4 | Raw table has 18,200 rows; staging model needed before E-series full validation |
| A-7g | `unit_cost` NULL in stg_shopify_inventory_items | G2/G3, D3 | 1-row seed limitation; Shopify cost field not populated in seed |
| A-7h | C4 seed: only 3 days return_count > 20 (spec: > 20 days) | C4 | Seed generates low peak returns; not blocking Agent A |
| A-7i | D2 seed: discount_rate = 14.1% (spec: 20–50%) | D2 | Seed generates fewer discounted orders; not blocking Agent A |
| A-7j | E repeat_purchase_rate = 1.000 (spec: 0.25–0.45) | E2 | All-time 24-month rate ≈ 1.0 for synthetic data; metric needs 90-day window definition |

---

## PRE-AGENT B GAPS
Agent B traverses Fashion Causal Graph and reads
causal_pattern_validation. All items below must be
complete before Agent B build begins.

| # | Gap | Status | Notes |
|---|-----|--------|-------|
| B-1 | causal_pattern_validation seed rows | PENDING | Zero rows currently. Need Archetype A validated chains seeded before Agent B build |
| B-2 | candidate_signals seed rows | PENDING | Zero rows. Agent B logs unrecognised patterns here — needs at least schema validation |
| B-3 | Verification category assigned all 37 alerts | COMPLETE ✓ | Written to product_strategy.md Section 3A |
| B-4 | G1 ad set → SKU mapping decision | PENDING | Architectural gap. Two options: manual mapping table OR infer from ad set naming convention. Must decide before Agent B traverses inventory causal chain |
| B-5 | Fashion Causal Graph defined in code | PENDING | Graph exists conceptually in Blueprint. Needs Python/JSON representation for Agent B to traverse |

---

## PRE-AGENT C/D GAPS
Agent C generates action recommendations.
Agent D formats Evidence Stack and posts to Slack.

| # | Gap | Status | Notes |
|---|-----|--------|-------|
| CD-1 | Slack personal workspace created | PENDING | Step 10 |
| CD-2 | Evidence Stack message format defined | PENDING | Step 10 |
| CD-3 | Approve/Snooze/Dismiss button wiring | PENDING | Step 10 |
| CD-4 | sku_cost_master populated | PENDING | Required for D1/D3 action recommendations with accurate margin impact |
| CD-5 | permanent_dq_limitations rows seeded | PENDING | Required for Layer 0 Evidence Stack disclosures |
| CD-6 | suppression_log schema validated | PENDING | Agent D reads this for "why no alert" queries |

---

## DEFERRED — NOT BLOCKING ANY AGENT

| # | Item | Deferred To | Notes |
|---|------|-------------|-------|
| D-1 | mart_inventory_spend_daily (SKU-level) | Agent A Step 9 design | G1 full validation needs this. Build after Agent A query pattern is defined |
| D-2 | G4 back-in-stock Klaviyo waitlist | Agent A Step 9 | Needs Klaviyo waitlist flag confirmed in staging |
| D-3 | network_pattern_benchmarks rows | Step 7 (Archetype B/D) | Archetype A vertical_tag staged. B/D thin datasets deferred |
| D-4 | causal_pattern_validation cross-client rows | Month 6+ | Needs real client outcome data |

---

*Update this file at the end of every session that
resolves or adds a gap. Do not let gaps accumulate
undocumented.*
