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
| A-7 | Step 7 validation matrix (37 alerts) | PENDING | Next session |

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
