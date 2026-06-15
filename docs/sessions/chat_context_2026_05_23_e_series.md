# Profit Sentinel — Chat Context
## Date: 2026-05-23
## Session: Alert Review — E-series (E1 Complete, E2 Partial)

---

## SESSION PURPOSE

Full deliberation of E-series alert language with founder.
E1 fully locked. E2 firing condition and denominator architecture locked.
E2 alert language, critiques 2/3/4 pending — start here next session.

---

## GOVERNING PRINCIPLES ESTABLISHED THIS SESSION

### Real-Data Safety Rule
All alert decisions must be validated against what real Klaviyo/Shopify data
actually provides — not synthetic seed data patterns. A wrong alert at beta
is worse than a missed alert. Trust is the only asset at beta stage.

### Agency-Managed Data Rule
Brands at $2M–$10M GMV are predominantly agency-managed. Never rely on:
- Consistent campaign naming conventions in Klaviyo
- Consistent product taxonomy in Shopify
- Clean collection naming patterns
Any logic depending on these will break on real client data.

### Onboarding Question Rule
Where data inference is unreliable due to agency-managed inconsistency →
ask the founder one precise question at onboarding. Reserve inference for
signals where data is genuinely clean and reliable.

---

## E1 — List Health Degradation — FULLY LOCKED

**Status:** LOCKED — INFORMATIONAL 🟡

**Primary signal:** `effective_click_rate_28d`

**Firing condition (ALL four required):**
- Drops ≥30% below trailing 90-day baseline
- Persists ≥7 consecutive days
- Minimum 5 campaign sends in 28-day window
- No `brand_event_calendar` event active

If any condition not met → silent skip, log `scan_skipped_reason`.

**Agent B diagnosis when fires:**
Surface last 3 campaign send dates + raw click rates from
`stg_klaviyo_email_events`. No campaign type classification.
Founder identifies outlier themselves.

**Dropped permanently — do not implement:**
- Unsubscribe volume as trigger or signal
- Hard bounce rate as trigger
- Spam complaint rate as trigger or corroborating signal
- Campaign type classification (agency naming conventions unreliable)
- BFCM sunset suppression (irrelevant — unsubscribe dropped)
- E1 CRITICAL escalation path (deferred post-beta)

**Deferred to weekly summary only:**
- Spam complaint rate trend
- Hard bounce rate trend

**Peak suppression:** Enabled — brand_event_calendar suppresses E1.

**Pending mart column:**
`effective_click_rate_28d` — add to `mart_causal_chain_daily`
Source: `stg_klaviyo_email_events`, 28-day rolling × `ios_mpp_multiplier`

**causal_graph.py entry:**
- E1: `peak_suppression: enabled`
- E1: `leading_signal_column: effective_click_rate_28d`
- E1: `leading_signal_direction: declining`

**Founder alert language:**
```
🟡 Email Engagement Declining

Your effective click rate dropped to [X]% —
[Y]% below your 90-day average of [Z]%.

Last 3 campaigns:
• [Campaign send date 1]: [X]% click rate
• [Campaign send date 2]: [X]% click rate
• [Campaign send date 3]: [X]% click rate

One of these is likely driving the drop — check content,
offer, and audience on the outlier.

ⓘ Click rate adjusted for Apple Mail Privacy Protection.
This alert fires at ≥30% drop vs your 90-day baseline.
Adjust in Sentinel settings. [link]
```

---

## E2 — Repeat Purchase Rate Declining — PARTIALLY LOCKED

**Status:** FIRING CONDITION AND DENOMINATOR ARCHITECTURE LOCKED.
Alert language PENDING. Critiques 2, 3, 4 PENDING.
Start next session here.

### Firing Condition (LOCKED)
- `repeat_purchase_rate_90d` drops ≥5 percentage points below trailing 28-day average
- `new_customer_pct_90d` has NOT surged >15% in same window
  (if yes → S33 fires instead — denominator effect explanation)
- Minimum 50 repeat customers in 90-day window
  (below → suppress, log `scan_skipped_reason = 'insufficient_repeat_customer_count'`)
- No `brand_event_calendar` event active

**S33 pre-condition is mandatory — Agent B runs this before E2 every time.**

### Discount Classification Architecture (LOCKED)

**Scope:** Repeat customers with 3+ lifetime orders ONLY.
New customers (1-2 orders) NEVER classified as discount-motivated.
First-time buyers during sales are new customers — not discount seekers.

**Step 1 — Auto-derive Brand Event Calendar (Approach B)**
Runs in `historical_pattern_scan.py` at onboarding + monthly.

Event day qualification:
```
qualifying_day = daily_order_count > median(daily_order_count)
                 across all days with orders > 0
```

Event type classification (percentile-based — no hardcoded thresholds):
```
Type 1 (deep sale)     = avg_discount_depth > p75 of qualifying event days
Type 2 (moderate sale) = avg_discount_depth p50–p75
Type 3 (BAU)           = avg_discount_depth below p50
```

Real-time forward detection:
- Daily order volume > median AND avg discount depth crosses p50 → event day
- Type assigned by percentile band
- Thresholds recalibrated monthly to prevent threshold creep

**Step 2 — Welcome Discount Code Exclusion**
Onboarding confirmation: founder confirms welcome-only codes (e.g. WELCOME10)
Written to `client_config.welcome_discount_codes[]`
Excluded from all discount depth calculations

**Step 3 — Customer Classification (Approach A)**
Applies only to 3+ lifetime order customers:
```
customer_discount_ratio = sum(order_discount_amount) / sum(order_subtotal)
                          excluding welcome_discount_codes orders

discount_motivated = customer_discount_ratio > mean + (1.5 × SD)
                     across all 3+ order customers
```

**Denominator Rule:**
```
e2_denominator = all buyers in 90-day window
                 EXCLUDING discount_motivated customers (3+ orders)
                 NEVER excluding new customers (1-2 orders)
```

**Data sufficiency:** < 12 months history → proceed without exclusion,
log `discount_classification_status = 'insufficient_history'`,
disclose in E2 alert footnote.

### Launch Detection and Suppression Architecture (LOCKED)

**3-source detection (ALL required within same 7-day window):**
1. New SKU cluster: spike above `mean(daily_sku_additions) + 2 SD`
   in any 7-day window
2. Paid spend spike: any connected ad channel >40% vs prior 7-day average
3. GA4 sessions spike: >30% vs prior 7-day average

Minimum viable: Shopify + any one ad channel + GA4.
Every ICP client will have these three.

**Launch impact score:**
```
impact_score = weighted combination of:
  - SKU spike magnitude vs brand baseline
  - Spend spike magnitude vs brand baseline
  - GA4 traffic spike magnitude vs brand baseline
```

**Suppression duration derivation:**
```
For known historical launches (confirmed at onboarding):
  suppression_days = actual measured recovery days from historical data

For new unknown launches:
  base_suppression = mean(recovery_days) for historical launches
                     WHERE impact_score BETWEEN
                     new_launch_impact_score × 0.7
                     AND new_launch_impact_score × 1.3

Fallback hierarchy:
  1. Brand's own similar-magnitude launch history (≥2 similar launches)
  2. Vertical benchmark from network_pattern_benchmarks
  3. Default: 28 days
```

Written to `client_config.collection_launch_suppression_days`
Recalibrated monthly.

**Sub-category classification: DROPPED ENTIRELY.**
Impact score self-calibrates suppression duration by launch size automatically.
No classification needed. No founder prompts post-onboarding.

**No suppression for unrecognised launch types** (TikTok Shop, pop-up etc.)
Safer to fire E2 and be wrong than suppress silently.

### Vertical Tag Identification (LOCKED)
Single onboarding question — one tap:
"Which best describes your brand?"
[ Contemporary womenswear ] [ Premium/luxury ] [ Activewear ]
[ Swimwear ] [ Basics/essentials ] [ Multi-category ]
Writes to `client_config.vertical_tag`

### New mart columns needed (LOCKED)
- `effective_click_rate_28d` — E1 primary signal
- `new_customer_pct_90d` — E2 S33 pre-condition (HARD BLOCKER for E2)

### New client_config columns needed (LOCKED)
- `welcome_discount_codes text[]`
- `collection_launch_suppression_days integer default 28`
- `discount_classification_status text default 'pending'`
- `baseline_discount_pct numeric`
- `e1_click_rate_drop_threshold numeric default 0.30`
- `e2_repeat_rate_minimum_customers integer default 50`
- `vertical_tag text`

---

## E2 — PENDING FOR NEXT SESSION

### Critique 2: Trajectory Signal
Aligned in principle — not yet written as build spec.
Sudden drop (concentrated last 7 days) vs gradual decline (spread 4+ weeks).
Agent B queries mart across last 8 weekly points at runtime — no new mart column.
Characterises as "sudden" vs "gradual" in plain English in alert body.

### Critique 3: Gorgias Cross-Reference
Aligned in principle — not yet written as build spec.
Automatic when elevated complaints found for churning segment.
Silent when absent — do NOT say "no elevated complaints."
Disclose: "Based on [X]% of orders with support data" (70% coverage, B-4).

### Critique 4: Revenue Impact Weighting
Aligned in principle — not yet written as build spec.
Weight by segment LTV — losing 5 Advocates ≠ losing 50 Explorers.
Agent B derives at runtime from mart_customer_segments_daily.
Formula:
  revenue_at_risk = churning_segment_count
                    × segment_avg_aov_7d
                    × (365 / avg_inter_purchase_days_for_segment)
Round to nearest $50.

### Alert language
NOT YET WRITTEN. Write after critiques 2/3/4 locked.

---

## NEXT SESSION STARTING POINT

1. Load: agent_d_build_spec_v2.md, pre_agent_build_checklist_v2.md,
   technical_architecture_e_series_patch.md, state_2026_05_23_e_series_eod.md
2. Replace existing project files with v2/patch versions
3. Start: E2 critique 2 (trajectory signal) → lock → critique 3 → lock →
   critique 4 → lock → write E2 alert language → lock
4. Then: E3, E4, D, C, B, A, H series

