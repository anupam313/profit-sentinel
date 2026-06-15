# Profit Sentinel — Session State
## Date: 2026-05-23
## Session: Alert Review — E-series (E1 Complete, E2 Partial)

---

## LAST COMPLETED SESSION
chat_context_2026_05_23_alert_review_fg.md — G-series and F-series complete.

---

## WHAT WAS COMPLETED THIS SESSION

### 1. E1 — List Health Degradation — COMPLETE

| Decision | Outcome |
|----------|---------|
| Primary signal | `effective_click_rate_28d` — 28d rolling, MPP-adjusted |
| Firing condition | ≥30% drop vs 90d baseline, ≥7 days, ≥5 sends, no calendar event |
| Unsubscribe volume | Dropped entirely |
| Spam complaint | Dropped as trigger — weekly summary only |
| Hard bounce | Dropped as trigger — weekly summary only |
| Campaign type classification | Dropped — agency naming unreliable |
| CRITICAL escalation | Deferred post-beta |
| Alert language | Written and locked |

### 2. E2 — Repeat Purchase Rate Declining — PARTIAL

| Decision | Outcome |
|----------|---------|
| Firing condition | ≥5pt drop vs 28d avg, S33 pre-check, ≥50 repeat customers |
| S33 pre-condition | `new_customer_pct_90d` surge >15% → S33 fires instead |
| Discount classification | Approach A + B sequential, 3+ order customers only |
| New customer treatment | Never excluded from denominator — always in |
| Welcome code exclusion | Onboarding confirmation → `client_config.welcome_discount_codes[]` |
| Brand event calendar | Auto-derived from discount depth + order volume in historical_pattern_scan.py |
| Launch detection | 3-source: SKU spike + spend spike + GA4 spike |
| Suppression duration | Impact score → similar-magnitude historical recovery → benchmark → 28d default |
| Sub-category classification | Dropped entirely — impact score self-calibrates |
| Unrecognised launch types | No suppression — safer to fire than suppress silently |
| Vertical tag | Single onboarding question → client_config.vertical_tag |
| At-risk segment pre-warning | Removed entirely — deferred Phase 2 |

### 3. Governing Principles Established
- Real-data safety rule — wrong alert at beta worse than missed alert
- Agency-managed data rule — never rely on naming conventions
- Onboarding question rule — ask founder when inference unreliable

---

## ALERT REVIEW STATUS

| Series | Status |
|--------|--------|
| G-series | Complete ✓ |
| F-series | Complete ✓ |
| E1 | Complete ✓ |
| E2 | Partial — critiques 2/3/4 + alert language pending |
| E3 | Pending |
| E4 | Pending |
| D-series | Pending |
| C-series | Pending |
| B-series | Pending |
| A-series | Pending |
| H-series | Pending — last |

---

## PENDING CLAUDE CODE ACTIONS
(Accumulating — execute after H-series complete)

### mart_causal_chain_daily — new columns
- `effective_click_rate_28d` — E1 primary signal
  Source: stg_klaviyo_email_events, 28d rolling × ios_mpp_multiplier
- `new_customer_pct_90d` — E2 S33 pre-condition (HARD BLOCKER for E2)
  Source: stg_shopify_orders, first-time buyers / total buyers trailing 90d

### client_config — new columns (ALTER TABLE)
- `welcome_discount_codes text[]` — onboarding confirmed welcome codes
- `collection_launch_suppression_days integer default 28`
- `discount_classification_status text default 'pending'`
  values: active / insufficient_history
- `baseline_discount_pct numeric` — derived at onboarding scan
- `e1_click_rate_drop_threshold numeric default 0.30`
- `e2_repeat_rate_minimum_customers integer default 50`
- `vertical_tag text` — set at onboarding question

### historical_pattern_scan.py — new functions
- Brand event calendar auto-derivation from discount depth + order volume
  (Approach B — event type classification using percentile bands)
- Customer discount classification (Approach A — mean + 1.5 SD outlier flag)
- Collection launch detection (3-source signature)
- Launch impact score calculation
- Suppression duration derivation per launch

### causal_graph.py
- E1: peak_suppression = enabled
- E1: leading_signal_column = effective_click_rate_28d
- E1: leading_signal_direction = declining
- E2: peak_suppression = enabled
- E2: S33 denominator check as mandatory pre-condition flag
- E2: collection_launch suppression event type

### technical_architecture.md
- Add Section 3.2f: E-series client_config ALTER TABLE
- Add effective_click_rate_28d and new_customer_pct_90d to mart column documentation
- Update brand_event_calendar documentation: auto-population from
  historical_pattern_scan.py (currently documented as manual)

---

## FILES CREATED THIS SESSION

| File | Action required |
|------|----------------|
| `agent_d_build_spec_v2.md` | REPLACE existing `agent_d_build_spec.md` in project |
| `pre_agent_build_checklist_v2.md` | REPLACE existing `pre_agent_build_checklist.md` in project |
| `technical_architecture_e_series_patch.md` | ADD to project — append to technical_architecture.md |
| `state_2026_05_23_e_series_eod.md` | ADD to project — new state file |
| `chat_context_2026_05_23_e_series.md` | ADD to project — new chat context file |

---

## NEXT SESSION STARTING POINT

1. Replace agent_d_build_spec.md and pre_agent_build_checklist.md in project
2. Add technical_architecture_e_series_patch.md, state and chat context files
3. Load all five files in new session
4. Start: E2 critique 2 (trajectory) → critique 3 (Gorgias) →
   critique 4 (revenue weighting) → E2 alert language
5. Then E3 → E4 → D → C → B → A → H
6. Write consolidated Claude Code prompt after H-series complete

