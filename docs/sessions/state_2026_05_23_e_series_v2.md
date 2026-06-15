# Profit Sentinel — Session State
## Date: 2026-05-23
## Session: Alert Review — E-series Complete, D-series Pending

---

## LAST COMPLETED SESSION
state_2026_05_23_e_series_eod.md — E1 complete, E2 partial.

---

## WHAT WAS DECIDED THIS SESSION

### Governing Principle Established — CRITICAL
**Monitor-and-Wait alerts that cannot diagnose cause with Phase 1
connectors are dropped from Phase 1 entirely.**

Rationale:
- Surfacing unexplained signals damages founder trust more than omitting them
- A weekly summary saying "your VIP segment is churning and we don't know why"
  is worse than no summary — it signals product incompleteness
- Phase 1 credibility rests entirely on the five core alerts where full
  cross-source explanation and a specific action exist
- Alerts require: specific action + same-day execution + diagnosable cause
  from available data. If any of these fail → Phase 2 or drop entirely.

---

## E-SERIES FINAL STATUS

### E1 — List Health Degradation — COMPLETE ✓ LOCKED
No changes from previous session. See chat_context_2026_05_23_e_series.md
for full spec.

### E2 — Repeat Purchase Rate Declining — DROPPED FROM PHASE 1
**Decision: Removed from alert stack entirely. Deferred Phase 2.**

Deliberation path:
1. Metric definition was wrong — trailing 90d rate distorted by acquisition
   volume. Cohort-based definition (90–180d buyers → % repurchased in 90d)
   is correct but still fails the action test.
2. Post-event demand pull-forward (BFCM, end-of-season sales) creates
   systematic false positives with no suppression logic.
3. Six distinct cause buckets identified — CRM, product, competitive,
   acquisition pollution, macro, channel mix shift. Cannot diagnose reliably
   from Phase 1 connectors.
4. Action is always investigate-first, never act-first.
5. Weekly summary also rejected — "we see the problem but don't know why"
   damages trust more than omitting the signal.

**Build actions — CANCEL ALL E2 ARCHITECTURE:**
- Cancel: S33 pre-check logic
- Cancel: Discount classification architecture (Approach A + B)
- Cancel: Welcome discount code exclusion flow
- Cancel: Collection launch detection and suppression
- Cancel: E2 firing condition logic
- Cancel: historical_pattern_scan.py E2 functions
- Cancel: causal_graph.py E2 entries

**Retain:**
- `new_customer_pct_90d` mart column — useful for other alerts and Phase 2
- `vertical_tag` client_config column — used elsewhere
- `welcome_discount_codes` client_config column — used elsewhere

**causal_graph.py:** Mark E2 as `status: deferred_phase2`

### E3 — High-LTV Customers Going Quiet — DROPPED FROM PHASE 1
**Decision: Removed from alert stack entirely. Deferred Phase 2.**

Deliberation path:
1. VIP segment at $5M GMV = ~340 customers. Signal is real and material.
2. But action is always investigate-first — wrong Klaviyo win-back to a VIP
   who left due to product disappointment damages the most valuable relationship.
3. Same six-cause-bucket problem as E2. Cannot diagnose cause from Phase 1
   connectors.
4. 60-day quiet window is slow-moving by definition — nothing changed today
   that makes it an alert.
5. Weekly summary also rejected — same trust damage argument.

**causal_graph.py:** Mark E3 as `status: deferred_phase2`

### E4 — Post-Purchase Flow Conversion Declining — DROPPED FROM PHASE 1
**Decision: Removed from alert stack entirely. Deferred Phase 2.**

Deliberation path:
1. Flow revenue declining has same diagnosis problem — content change,
   audience shift, offer expiry, or attribution noise (15–20% of flow
   revenue flagged low confidence).
2. Cannot distinguish signal from attribution noise without deeper
   flow-level data not available in Phase 1.
3. Monitor-and-Wait classification was already a signal this doesn't
   clear the alert bar.

**causal_graph.py:** Mark E4 as `status: deferred_phase2`

---

## E-SERIES PHASE 1 SUMMARY

| Alert | Status |
|-------|--------|
| E1 — List Health Degradation | ACTIVE — Phase 1 ✓ |
| E2 — Repeat Purchase Rate Declining | DEFERRED — Phase 2 |
| E3 — High-LTV Customers Going Quiet | DEFERRED — Phase 2 |
| E4 — Post-Purchase Flow Conversion Declining | DEFERRED — Phase 2 |

---

## PENDING CLAUDE CODE ACTIONS
(Accumulating — execute after H-series complete)

### mart_causal_chain_daily — new columns
- `effective_click_rate_28d` — E1 primary signal
  Source: stg_klaviyo_email_events, 28d rolling × ios_mpp_multiplier
- `new_customer_pct_90d` — retain for future use and Phase 2
  Source: stg_shopify_orders, first-time buyers / total buyers trailing 90d

### client_config — new columns (ALTER TABLE)
- `welcome_discount_codes text[]` — retain, used outside E2
- `vertical_tag text` — retain, used outside E2
- `e1_click_rate_drop_threshold numeric default 0.30`

### CANCELLED — do not build (E2 architecture)
- `collection_launch_suppression_days` — cancelled with E2
- `discount_classification_status` — cancelled with E2
- `baseline_discount_pct` — cancelled with E2
- `e2_repeat_rate_minimum_customers` — cancelled with E2
- historical_pattern_scan.py: brand event calendar auto-derivation — cancelled
- historical_pattern_scan.py: customer discount classification — cancelled
- historical_pattern_scan.py: collection launch detection — cancelled
- historical_pattern_scan.py: launch impact score calculation — cancelled
- historical_pattern_scan.py: suppression duration derivation — cancelled

### causal_graph.py
- E1: peak_suppression = enabled
- E1: leading_signal_column = effective_click_rate_28d
- E1: leading_signal_direction = declining
- E2: status = deferred_phase2
- E3: status = deferred_phase2
- E4: status = deferred_phase2

### agent_d_build_spec.md
- Remove E2 firing condition section
- Remove E2 discount classification architecture section
- Remove E2 launch detection and suppression section
- Remove E2 pending items section
- Remove E3 alert language (not yet written — nothing to remove)
- Remove E4 alert language (not yet written — nothing to remove)
- Add note: E2/E3/E4 deferred Phase 2 per alert review 2026-05-23

### product_strategy.md
- Update Group E section: E1 active Phase 1, E2/E3/E4 deferred Phase 2
- Add governing principle: Monitor-and-Wait alerts without diagnosable
  cause from Phase 1 connectors are deferred to Phase 2

### technical_architecture.md
- Add Section 3.2f: E-series client_config ALTER TABLE (E1 only)
- Add effective_click_rate_28d and new_customer_pct_90d to mart
  column documentation
- Update brand_event_calendar documentation: auto-population from
  historical_pattern_scan.py (currently documented as manual) —
  NOTE: this was designed for E2. With E2 dropped, confirm if
  brand_event_calendar auto-population is still needed for other alerts
  before building.

---

## D-SERIES — INITIAL READ (NOT YET LOCKED)

Session paused before D-series deliberation. Initial read completed:

| Alert | Initial Read | Needs Deliberation |
|-------|-------------|-------------------|
| D1 — Contribution Margin Compression | STAYS — Alert 4, core five | No — already locked |
| D2 — Discount Dependency Creep | LIKELY DROP — Monitor-and-Wait, no immediate action | Yes |
| D3 — COGS Step Change Impact | QUESTIONABLE — founder already knows COGS changed | Yes |
| D4 — Fulfilment Cost Anomaly | STAYS — specific, verifiable, same-day action (call 3PL) | Minor confirmation needed |
| D5 — Klaviyo Flow Revenue Declining | LIKELY PHASE 2 — same diagnosis problem as E4 | Yes |
| D6 — Seasonal Baseline Diagnostic | STAYS AS SUPPRESSION LOGIC — not a founder-facing alert | Confirm framing only |

**Emerging pattern:** Monitor-and-Wait actionability classification
reliably predicts which alerts fail the founder action test. Consider
establishing as formal rule before D-series deliberation.

---

## ALERT REVIEW STATUS

| Series | Status |
|--------|--------|
| G-series | Complete ✓ |
| F-series | Complete ✓ |
| E1 | Complete ✓ |
| E2 | DROPPED — Phase 2 |
| E3 | DROPPED — Phase 2 |
| E4 | DROPPED — Phase 2 |
| D-series | Pending — initial read done |
| C-series | Pending |
| B-series | Pending |
| A-series | Pending |
| H-series | Pending — last |

---

## NEXT SESSION STARTING POINT

1. Load: state_2026_05_23_e_series_v2.md,
         chat_context_2026_05_23_e_series_v2.md,
         agent_d_build_spec.md,
         technical_architecture.md,
         product_strategy.md
2. Confirm governing principle: Monitor-and-Wait = Phase 2 as formal rule
3. Start D-series deliberation from D2
4. Then C → B → A → H
5. Write consolidated Claude Code prompt after H-series complete
