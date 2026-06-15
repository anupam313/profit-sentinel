# Profit Sentinel — Session State
## Date: 2026-05-21
## Session: B-5 + B-1 Design (Fashion Causal Graph + Chain Seed)
## Type: Design session — no Claude Code commits this session

---

## LAST COMPLETED BUILD STEP

Step 11 — `historical_pattern_scan.py` built and executed (D-12 COMPLETE).
All 5 verification conditions passed. No new commits this session.

---

## WHAT WAS COMPLETED THIS SESSION

Pure design session. No code written. All decisions locked and recorded in
`chat_context_2026_05_21_b5_design.md`.

### Key decisions made:

1. **B-5 architecture locked** — hardcoded registry (`causal_graph.py`), not DAG.
   Permanently, not as a stepping stone. Rationale: trust moat requires every
   chain to be practitioner-validated before firing. DAG traversal is incompatible
   with this. Novel chain pipeline handles scale via promotion, not traversal.

2. **Option 2 (build missing mart columns) confirmed** — scoped to columns with
   real synthetic data to test against. Data-blocked columns get
   `status: mart_column_missing`.

3. **12 new mart columns confirmed** for `mart_causal_chain_daily` — see
   chat_context for full spec with logic, sources, and alert mappings.

4. **New mart model confirmed** — `mart_customer_segments_daily` (grain: date ×
   segment). Segments: Explorers / Regulars / Loyalists / Advocates. Boundaries
   calibrated once at onboarding from client's own order frequency distribution.
   Locked after onboarding. Fallback to vertical defaults if <500 repeat customers.

5. **`client_config` ALTER TABLE required** — 6 new columns for segment thresholds
   and significance floor. Full SQL in chat_context Decision 4.

6. **H-series architecture locked** — Option A: inside `causal_graph.py` with
   `routing` field. Three routing values: `internal` / `informational` /
   `founder_action_required`. Full classification table in chat_context Decision 5.

7. **Google Ads connector confirmed Phase 1** — full synthetic seed required before
   G-series mart columns can be tested. Fields to seed confirmed. API v17 docs
   must be read before writing seed script.

8. **Complete 56-chain column mapping done** — all chains mapped to exact mart
   column names with `leading_signal_column`, `outcome_column`, `lag_days`,
   `corroborating_signals`, `mart_table`, `status`. Full table in chat_context
   Decision 7.

---

## PRE-AGENT B BLOCKERS STATUS (UPDATED)

| Item | Status | Notes |
|------|--------|-------|
| B-1: causal_pattern_validation seed (56 chains) | PENDING | Blocked on B-5 + new mart columns |
| B-2: candidate_signals seed rows | PENDING | |
| B-4: G1 ad set → SKU mapping decision | PENDING | |
| B-5: Fashion Causal Graph in code | PENDING — designed, not built | All design decisions locked. Claude Code prompt to be written. |
| B-6: promotion_threshold values | PENDING | |
| B-7: Google Ads synthetic seed | NEW — PENDING | Prerequisite for G-series mart columns + `stockout_with_active_spend_count` |
| B-8: `sku_cost_master` full seeding | NEW — PENDING | Prerequisite for G-series mart columns |
| B-9: 12 new mart columns in `mart_causal_chain_daily` | NEW — PENDING | Prerequisite for B-5 and B-1 |
| B-10: `mart_customer_segments_daily` new model | NEW — PENDING | Prerequisite for B-5 and B-1 |
| B-11: `client_config` ALTER TABLE (6 segment columns) | NEW — PENDING | Prerequisite for B-10 |
| D-17: Novel chain review infrastructure | PENDING | |
| D-20: pending_connectors onboarding question | PENDING | |
| S3-P3: stg_klaviyo_profiles column names | PENDING | |

---

## NEW ITEMS DISCOVERED THIS SESSION

| Item | Description | Priority |
|------|-------------|----------|
| B-7 | Google Ads synthetic seed — Search, Shopping, PMax, YouTube, Discovery. Exclude Display. Read API v17 docs first. | Pre-Agent B |
| B-8 | `sku_cost_master` full seeding — all ~380 active variant SKUs, realistic costs, effective dates, one cost step-change event for D3 testing | Pre-Agent B |
| B-9 | 12 new mart columns in `mart_causal_chain_daily` — full spec in chat_context Decision 3 | Pre-Agent B |
| B-10 | `mart_customer_segments_daily` — new mart model, Explorers/Regulars/Loyalists/Advocates, onboarding-calibrated boundaries | Pre-Agent B |
| B-11 | `client_config` ALTER TABLE — 6 new segment columns | Pre-Agent B, before B-10 |

---

## RECOMMENDED BUILD SEQUENCE FOR NEXT SESSIONS

Based on dependencies surfaced this session:

```
Session A (Claude Code):
  1. client_config ALTER TABLE (B-11) — 6 segment columns
  2. Google Ads API v17 docs read — confirm field names
  3. Google Ads synthetic seed (B-7)
  4. sku_cost_master full seeding (B-8)
  5. dbt rebuild — confirm green

Session B (Claude Code):
  6. 12 new mart columns in mart_causal_chain_daily (B-9)
  7. mart_customer_segments_daily new model (B-10)
  8. dbt rebuild — confirm green
  9. Validate new columns against synthetic data

Session C (Claude Code):
  10. causal_graph.py (B-5) — using locked column mapping
  11. causal_pattern_validation seed remaining 34 chains (B-1)
  12. candidate_signals seed rows (B-2)

Then: Agent B build
```

---

## KNOWN SCHEMA DRIFT — CARRY FORWARD (UNCHANGED)

- `alert_log` column: `alert_type` (NOT `signal_type`)
- `alert_log` column: `evidence_stack_json` (NOT `evidence_stack`)
- `signal_value` + `threshold_value` are separate numerics (NOT `signal_values` jsonb)
- `client_id` throughout: `client_azure_co` (NOT `azure_co`)
- Airbyte drops columns not in schema on every sync → `is_synthetic` lives in
  staging tables (`stg_*`) for Airbyte sources
- Meta attribution window hard break: January 12 2026
- `brand_event_calendar` has zero rows in synthetic data
- `stg_klaviyo_profiles` columns: `profile_id` (not `customer_id`),
  `vip_status` (not `is_vip`)
- `stg_loop_refunds` not present — use `stg_loop_returns`
- `stg_meta_ad_performance` has no `attributed_revenue` — proxy: spend × purchase_roas
- `stg_klaviyo_flows` has no date column — use `stg_klaviyo_email_events`
- GA4 tables absent in synthetic data — NULL mart columns expected
- `dq_metric_scores.score_date` stored as `timestamptz` not `date`
- `public.onboarding_messages` — live table, created by `historical_pattern_scan.py`

---

## AGENT D SPECIFICATION NOTE — CARRY FORWARD

`avg_days_inventory_on_hand` value of 999 must be displayed in Evidence Stack as
"zero-velocity SKU — likely overstock or discontinued." Never display as raw number.
Carry into Agent D build session as a mandatory display rule.

---

## BUILD SEQUENCE STATUS

| Step | Description | Status |
|------|-------------|--------|
| 1 | Environment setup | Complete ✓ |
| 2 | Airbyte connectors | Complete ✓ |
| 3 | Source schema registry (72 tables) | Complete ✓ |
| 4 | Staging tables | Complete ✓ |
| 5a–5h | All seed scripts | Complete ✓ |
| 5i | patch_script_final.py | Complete ✓ |
| 6 | dbt rebuild (22 models) | Complete ✓ |
| 7 | Validation (37 alerts) | Complete ✓ |
| 8 | Onboarding confirmation flow CLI | Complete ✓ |
| 9 | Agent A (LangGraph) | Complete ✓ |
| 10 | Slack delivery + Evidence Stack | Complete ✓ |
| 10.5 | Mart patch (13 columns) + vip fix | Complete ✓ |
| 11 | historical_pattern_scan.py | Complete ✓ |
| 11.5a | client_config ALTER TABLE (B-11) | Pending |
| 11.5b | Google Ads seed (B-7) | Pending |
| 11.5c | sku_cost_master full seed (B-8) | Pending |
| 11.5d | 12 new mart columns (B-9) | Pending |
| 11.5e | mart_customer_segments_daily (B-10) | Pending |
| 11.5f | causal_graph.py (B-5) | Pending — designed ✓ |
| 11.5g | causal_pattern_validation seed (B-1) | Pending |
| 11.5h | candidate_signals seed (B-2) | Pending |
| 12 | Agent B (Causal graph traversal) | Pending |
| 13 | Agent C (Recommendation engine) | Pending |
| 14 | Agent D (Evidence Stack formatter) | Pending |

---

## FILES TO UPDATE AFTER THIS SESSION

| File | Action | Changes |
|------|--------|---------|
| `chat_context_2026_05_21_b5_design.md` | ADD to project knowledge | This session's design decisions |
| `state_2026_05_21_b5_design.md` | ADD to project knowledge | This file |
| `pre_agent_build_checklist.md` | REPLACE | B-7 through B-11 added, routing field documented |
| `technical_architecture.md` | REPLACE | `mart_customer_segments_daily` DDL + `causal_graph.py` structure |
| `product_strategy_updated.md` | REPLACE | Customer segment nomenclature + onboarding calibration logic |
