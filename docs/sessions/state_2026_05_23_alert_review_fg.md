# Profit Sentinel — Session State
## Date: 2026-05-23
## Session: Alert Review — F-series and G-series Complete

---

## LAST COMPLETED SESSION
chat_context_2026_05_22_v3.md — G-series alert review locked, B-5 executed,
Discovery Interview v4 complete.

---

## WHAT WAS COMPLETED THIS SESSION

### 1. G-Series Alert Review — COMPLETE
All G-series alerts reviewed, deliberated with founder, and locked.
Full decisions in chat_context_2026_05_23_alert_review_fg.md.

| Alert | Outcome |
|-------|---------|
| G1 — Stockout During Active Spend | Locked — CRITICAL, full new alert language |
| G2 — Inventory Depth Warning | Locked — INFORMATIONAL, full new alert language |
| G3 — Zero-Velocity SKU With Active Spend | Deferred Phase 2 |
| G4 — Back-in-Stock Waitlist Opportunity | Locked — INFORMATIONAL, full new alert language |

### 2. F-Series Alert Review — COMPLETE
All F-series alerts reviewed, deliberated with founder, and locked.
Full decisions in chat_context_2026_05_23_alert_review_fg.md.

| Alert | Outcome |
|-------|---------|
| F1 — Mobile Checkout Completion Rate | Locked — HIGH, conditional on GA4 |
| F2 — Checkout Error Count | Locked — CRITICAL, affected users primary condition |
| F3 — Bounce Rate → CVR | Deferred Phase 2 |
| F4 — Non-Checkout Sentry Errors | Locked — HIGH, non-checkout scope only |
| F5 — Checkout Funnel Step Drop | Locked — HIGH, conditional on GA4 step-level |

### 3. Agent D Build Spec — CREATED
File: `agent_d_build_spec.md`
Covers: G-series and F-series complete alert language, urgency tiers,
revenue formulas, Slack button specs, weekly follow-up flows.
Location: outputs directory — add to project repository.

### 4. DQ Intelligence Layer — DESIGNED AND LOCKED
File: `dq_intelligence_layer_section10.md`
Action: Append to `technical_architecture.md` as Section 10 after last line:
*"Neither Triple Whale nor Northbeam deducts returns from ROAS or connects
campaign content_ids to return velocity by SKU. B-4 builds the data
foundation for both PS differentiators."*

---

## BUILD SEQUENCE STATUS

| Step | Description | Status |
|------|-------------|--------|
| 1 | Environment setup | Complete ✓ |
| 2 | Airbyte connectors | Complete ✓ |
| 3 | Source schema registry (72 tables) | Complete ✓ |
| 4 | Staging tables | Complete ✓ |
| 5a–5i | All seed scripts + patch | Complete ✓ |
| 6 | dbt rebuild (22 models) | Complete ✓ |
| 7 | Validation (37 alerts) | Complete ✓ |
| 8 | Onboarding confirmation flow CLI | Complete ✓ |
| 9 | Agent A (LangGraph) | Complete ✓ |
| 10 | Slack delivery + Evidence Stack | Complete ✓ |
| 10.5 | Mart patch (13 columns) + vip fix | Complete ✓ |
| B-5 | Fashion Causal Graph (causal_graph.py) | Complete ✓ |
| 11 | Agent B (Causal graph traversal) | Pending |
| 12 | Agent C (Recommendation engine) | Pending |
| 13 | Agent D (Evidence Stack formatter) | Pending |

---

## ALERT REVIEW STATUS

| Series | Status |
|--------|--------|
| G-series | Complete ✓ |
| F-series | Complete ✓ |
| E-series | Pending — start here next session |
| D-series | Pending |
| C-series | Pending |
| B-series | Pending |
| A-series | Pending |
| H-series | Pending — last |

---

## PENDING CLAUDE CODE ACTIONS

These must be executed in next Claude Code session before Agent B build:

### causal_graph.py
- F2: verify `leading_signal_direction = "rising"` — correct if wrong
- F4: verify `leading_signal_direction = "rising"` — correct if wrong
- F3: update status to `deferred_phase2`
- F5: add independent firing condition note — must not re-fire on F2 threshold
- G3: update status to `deferred_phase2` — remove from active chains
- G4: set `peak_suppression: enabled: False`
- G4: update discontinued suppression logic — zero sales 90d + listed >180d
  + no restock 60d (NOT product_status or inventory_policy)
- All alerts: add `peak_suppression` boolean field per architecture table

### dbt (mart_causal_chain_daily.sql)
- Confirm `checkout_error_count` filters by `/checkout%` URL — fix if counting
  all Sentry errors
- Add `google_spend`, `google_roas`, `google_attributed_orders` columns
  (carried from G-series session)
- Add `zero_velocity_sku_with_spend_count` column (G3 — deferred but
  column still needed for future)

### technical_architecture.md
- Append `dq_intelligence_layer_section10.md` as Section 10 after last line

### GA4 seeding
- Seed `ga4_checkout_funnel_steps` with mobile vs desktop completion rates
- F1 and F5 status → `active` in synthetic after seeding

### Sentry Airbyte sync
- Set cadence to 1-hour minimum

### client_config
- Add `checkout_error_threshold integer default 5`
- Add `spend_event_detection_floor integer default 300`
- Add `supplier_lead_time_days integer default 21` (carried from G-series)
- Add `peak_hours_start` and `peak_hours_end` (removed from F1 — verify
  if still needed elsewhere)

### Staging verification
- Confirm `stg_shopify_script_tags` or `stg_shopify_themes` exists —
  determines Agent D F4 auto-surface of recent theme/app changes

### Onboarding architecture
- Add monthly Airbyte connector inventory check
- New connector detected → partial re-onboarding trigger
- Gap message resolved automatically — no founder manual action required

---

## KEY ARCHITECTURAL DECISIONS LOCKED THIS SESSION

### Urgency tier system
| Tier | Alerts | Format |
|------|--------|--------|
| CRITICAL 🔴 | F2, G1 | Per-hour revenue at risk |
| HIGH 🟠 | F1, F4, F5 | Per-hour estimated impact |
| INFORMATIONAL 🟡 | G2, G4 | Projected/daily impact |

### Revenue impact formula (standard)
`hourly_revenue_at_risk = (daily_sessions / 14) × historical_cvr × AOV`
Round to nearest $50. Never show if < $50.
Currency: always `client_config.currency` — default USD. Never hardcode.

### Clean baseline definition (F1, F5)
28-day rolling baseline excluding:
- Major event days (is_major = true) ± 3 days pre / 5 days post
- Auto-detected spend spike days: `daily_spend > 90d_avg × 2.5`
  AND `daily_spend > client_config.spend_event_detection_floor` ($300 default)
  AND minimum 30 days spend history
Minimum 15 clean days required — suppress if fewer

### Peak suppression architecture
Boolean per alert in causal_graph.py. Agent B reads boolean only.
No runtime decision tree.

### F2 firing condition
`sentry_affected_users >= client_config.checkout_error_threshold` (default 5)
URL filter: `/checkout%` paths only — not tags
Window: 1-hour check first, 3-hour check if 1-hour doesn't trigger
No multiplier — affected users is primary and only condition

### F5 — GA4 step-level
Fires when specific step abandonment > 2x clean baseline
Independent from F2 — different firing condition, different source
When both fire: F2 = main alert (CRITICAL), F5 = thread reply

### G1 — dual impact
Wasted spend + missed revenue opportunity both shown
Platform-split copy-paste brief per channel
Variant vs full SKU detection changes action sequence
PS monitors every hour — no founder reply required

### G2 — directional only
Days remaining = `inventory_quantity / avg_daily_units_sold_7d`
`~` prefix on all estimates. Trend indicator per SKU.
Product age always shown from `product.created_at`
No reorder quantity — deferred Phase 2

### G4 — waitlist-age multiplier
| Age | Multiplier |
|-----|-----------|
| < 2 weeks | 2.0–2.5x store CVR |
| 2–6 weeks | 1.5–2.0x store CVR |
| > 6 weeks | 1.0–1.5x store CVR |
Replace with founder's own data when ≥3 restock events available

### DQ Intelligence Layer principles
- No confidence tags on clean firing alerts
- Structural limitations: collapsed "ⓘ Data note" footnote on every firing
- Gap quantification: range only, upper bound ≤3x lower bound
- One gap opportunity per weekly summary — progressive disclosure
- Connector lifecycle: monthly Airbyte check → auto partial re-onboarding

---

## DEFERRED TO PHASE 2

| Item | Reason |
|------|--------|
| G3 — Zero-velocity SKU with spend | SKU-level spend mapping unreliable + long-tail normal in fashion |
| F3 — Bounce rate → CVR | Blended bounce rate not actionable without source-level GA4 |
| Reorder quantity recommendation (G2) | Too many fashion nuances — decay, lifecycle, size curve |
| Payment method specific recommendations (F5) | Need per-client Shopify payment config |
| F5 peer benchmark percentages | Need 5+ real clients with follow-up responses |
| SKU-level spend attribution (G1 missed revenue) | Catalogue feed integration required |

---

## FILES CREATED THIS SESSION

| File | Location | Action required |
|------|----------|----------------|
| `agent_d_build_spec.md` | outputs/ | Add to project repository |
| `dq_intelligence_layer_section10.md` | outputs/ | Append to technical_architecture.md |
| `state_2026_05_23_alert_review_fg.md` | outputs/ | Add to project repository |
| `chat_context_2026_05_23_alert_review_fg.md` | outputs/ | Add to project repository |

---

## NEXT SESSION STARTING POINT

1. Add all four files above to project repository
2. Append Section 10 to technical_architecture.md in Claude Code
3. Execute pending Claude Code actions listed above
4. Continue alert review — start with E-series
5. E → D → C → B → A → H (H-series last)
6. Write consolidated Claude Code prompt after H-series complete
