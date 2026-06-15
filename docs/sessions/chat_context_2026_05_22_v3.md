# Profit Sentinel — Chat Context
## Date: 2026-05-22
## Session: v3 — Alert Review (G-series complete), B-5 executed, Discovery Interview v4

---

## Session Purpose

Two workstreams in parallel:
1. B-5 execution (`agents/causal_graph.py`) — completed at session start
2. Full causal graph alert review G→A (H-series deferred to last)
3. Discovery interview questionnaire updated to v4

---

## B-5 EXECUTION RESULTS — COMPLETE

`agents/causal_graph.py` built and verified.

| Item | Result |
|------|--------|
| Chain count | 57 confirmed (`len(FASHION_CAUSAL_GRAPH)` == 57) |
| dbt regression | PASS=65 WARN=0 ERROR=0 |
| google_spend | NOT in mart SELECT — computed in CTE only, not exposed as output column |
| google_roas | ABSENT from both marts |
| google_attributed_orders | ABSENT from both marts |
| A3 status | `active_proxy` — meta + tiktok active, google commented out |
| A4 status | `active_proxy` — google_attributed_orders and utm_coverage_rate both absent |
| A7 | Added — `mart_column_missing` (wholesale_order_rate_pct not yet built) |

Four additions incorporated into B-5:
1. Google Ads in A3 (active_proxy — google_roas absent)
2. Google Ads in A4 (active_proxy — google_attributed_orders absent)
3. `baseline_requirements` metadata field on A3 (60-day minimum per channel, soft fire)
4. A7 — Wholesale Order Contamination Warning (mart_column_missing)

---

## DISCOVERY INTERVIEW v4 — COMPLETE

Three new probes added as Section 4B (Architecture Probes):
- P1: Wholesale/DTC split — fires Architecture Risk flag if >20% wholesale with no order tagging
- P2: Social native checkout — TikTok Shop / Instagram native checkout blind spot
- P3: Gorgias tagging consistency — gates D-22 NLP classifier build

Probes do NOT feed 0–24 scoring rubric. Architecture validation only.
File: `discovery_interview_questionnaire_v4.docx`

---

## ALERT REVIEW — G-SERIES COMPLETE

All decisions locked. Consolidated Claude Code prompt to be written after
full G→A review is complete.

### G1 — Stockout During Active Spend
No change to alert logic. Post-B-4 clean.
Addition: `peak_event_suppression` (window: 14 days, multiplier: 2.0)
Event filter: `event_type IN ('sale_event','collection_drop') AND is_major = true`
Fallback windows if `is_major` absent: BFCM (Nov 1–30), Valentine's (Feb 7–14), Mother's Day (May 1–14)

### G2 — Inventory Depth Warning
Change: replace hardcoded 30-day lag with `supplier_lead_time_days` from `client_config`
Firing condition: `avg_days_on_hand < supplier_lead_time_days + 7`
Default: 21 days
Addition: `peak_event_suppression` identical to G1
New `client_config` column required: `supplier_lead_time_days integer default 21`

### G3 — Redefined (was Inventory Concentration)
Original concentration logic: DROPPED — moved to Phase 2B candidate
New definition: Zero-velocity SKU with active spend
- 0 sales in trailing 14 days AND inventory > 0 AND active spend via content_ids
New leading signal: `zero_velocity_sku_with_spend_count`
Status: `mart_column_missing` until mart column built
New mart column required: `zero_velocity_sku_with_spend_count`
Peak event suppression: DISABLED (waste is more urgent during peak)

### G4 — Back-in-Stock Waitlist
Firing gate: `waitlist_count × AOV > 15% of trailing 90-day avg daily revenue`
Non-restock suppression: suppress if days_since_last_restock > 60 OR product status = draft
Addition: `peak_event_suppression` identical to G1
Status: keep Phase 1 but beta-validate — cut if Evidence Stack adds no value over Klaviyo native
Revenue window: 90-day trailing avg (not 30-day — avoids seasonal distortion)

---

## PEAK EVENT SUPPRESSION — ARCHITECTURE DECISION

`peak_event_suppression` is a metadata field on causal_graph.py entries.
Agent B reads it at runtime and applies threshold multiplier.
`brand_event_calendar.is_major` must be verified before Agent B build.
If absent: Agent B uses hardcoded fallback windows.
Applies to: G1, G2, G4.
Does NOT apply to: G3 (intentionally disabled).

---

## ADDITIONAL ALERTS DECISIONS (pre-review session)

### A7 — Wholesale Order Contamination (NEW)
Added to causal_graph.py as mart_column_missing.
Fires when wholesale_order_rate_pct > 20% of total Shopify orders.
Connectors: Shopify only. Verification: A.
Firing frequency: onboarding then monthly.
Mart column `wholesale_order_rate_pct` not yet built.
Seed: tag ~15% of synthetic shopify_orders as wholesale (separate session).

### A3 + A4 — Google Ads Added
Both updated to include Google as third channel.
A3: `baseline_requirements` — 60-day minimum per channel, soft fire with Layer 0 disclosure
A4: google_attributed_orders flagged as missing
Both currently `active_proxy`.

### Google Ads mart gap
`google_spend` exists as CTE only — not exposed as output column in mart SELECT.
`google_roas` absent from both marts.
`google_attributed_orders` absent from both marts.
All three to be added in consolidated dbt prompt after full review.

---

## CONSOLIDATED ACTIONS — G-SERIES (to be added to consolidated prompt)

### causal_graph.py
- G1: add `peak_event_suppression` field
- G2: add `firing_rule` referencing `supplier_lead_time_days`; add `peak_event_suppression`
- G3: full entry replacement — new leading signal, mart_column_missing, suppression disabled
- G4: add `firing_rule` (15% of 90d avg daily revenue); add `non_restock_suppression`; add `peak_event_suppression`

### dbt (mart_causal_chain_daily)
- Add `zero_velocity_sku_with_spend_count` column

### client_config ALTER TABLE
- Add `supplier_lead_time_days integer default 21`

### brand_event_calendar
- Verify `is_major` boolean exists and is populated — verify only, do not alter

### product_strategy.md (after code execution)
- Update G3 alert spec to zero-velocity definition
- Mark original concentration logic as Phase 2B candidate

---

## OPEN ITEMS ENTERING NEXT SESSION

| Item | Status |
|------|--------|
| Alert review F-series | PENDING — next in sequence |
| Alert review E-series | PENDING |
| Alert review D-series | PENDING |
| Alert review C-series | PENDING |
| Alert review B-series | PENDING |
| Alert review A-series | PENDING |
| Alert review H-series | PENDING — last |
| Consolidated Claude Code prompt | PENDING — after full review complete |
| product_strategy.md updates | PENDING — after code execution |
| pre_agent_build_checklist.md update | PENDING — after code execution |
