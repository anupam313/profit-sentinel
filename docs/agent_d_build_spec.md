# Profit Sentinel — Agent D Build Spec
## Scope: G-series and F-series Alert Language
## Created: 2026-05-23
## Status: Locked — G-series and F-series complete
## Last updated: 2026-06-04 — D1 Gap 6 discount-depth/S19 PARTIAL close (self-contained calls settled; interaction items deferred to the cross-component residual pass)
## Last updated: 2026-06-08 — D1 Gap 6 residual pass (Tier-1 locks): fulfilment retired (4 sites); measured-not-explained rule; all-explained two-door fire; universal go-quiet ceiling; structural-break magnitude made brand-relative; BAU pre-sale-ramp exclusion + onboarding backfill; operational-cost/S20 locked. Gap 6 remains WIP (new-vs-returning split still open).

---

## PURPOSE

This file defines the exact founder-facing alert language, urgency tiers,
revenue impact formulas, and Slack message structure Agent D must implement
for G-series and F-series alerts. It is the authoritative spec for Agent D
build session. Do not derive alert language from causal_graph.py entries
alone — this file contains deliberated language decisions that are not
captured elsewhere.

---

## URGENCY TIER SYSTEM

Agent D must format alerts differently based on urgency tier.
Three tiers defined:

| Tier | Response window | Examples | Slack format |
|------|----------------|----------|--------------|
| CRITICAL | 1–3 hours | F2 checkout errors, G1 | 🔴 bold header, revenue at risk per hour |
| HIGH | 6–24 hours | F1, F4, F5 | 🟠 header, estimated hourly impact |
| INFORMATIONAL | 24–72 hours | G2, G4, E-series | 🟡 header, projected impact |

Urgency tier is determined by:
1. Revenue impact per hour (CRITICAL if >$200/hour at average GMV)
2. Whether the problem is actively worsening vs already occurred
3. Whether founder action can stop ongoing loss vs prevent future loss

---

## REVENUE IMPACT FORMULA — STANDARD

Used across all F-series and G-series alerts where $X appears.

```
hourly_revenue_at_risk = (daily_sessions / 14) × historical_cvr × AOV
```

- `daily_sessions`: trailing 7-day avg sessions per day
- `historical_cvr`: trailing 28-day avg CVR (clean baseline — excludes major event days)
- `AOV`: trailing 28-day avg order value
- Divide by 14 = approximate active trading hours (not 24 — overnight traffic converts poorly)

**Display rule:** Always round to nearest $50. Never show false precision ($2,137 → $2,100).
**Minimum display:** If hourly_revenue_at_risk < $50, do not show revenue figure —
show "low revenue impact" instead to avoid noise.
**Currency rule:** Always use `client_config.currency` — default USD ($) for US market.
Never hardcode currency symbol anywhere in alert templates.

---

## INSUFFICIENT BASELINE — STANDARD SKIP MESSAGE

When any alert cannot fire due to insufficient clean baseline days
(fewer than 15 clean days in 28-day window after event exclusions):

**Internal log:** `scan_skipped_reason = 'insufficient_clean_baseline'`

**Founder message (one-time per alert type, not recurring):**
*"[Alert name] monitoring is active but needs more data to establish your
baseline. We'll start alerting once we have 15 days of clean signal —
typically within [X] days."*

Never show this message more than once per alert type per client.

---

## GLOBAL SKU LIST RULES — ALL ALERTS

Applies to G1, G2, G4 and any alert showing a SKU list:
- Default visible: top N SKUs (defined per alert below)
- "Show all [N] SKUs ↓" expands full list inline
- "Show less ↑" collapses back to default
- If total SKUs ≤ default visible count: flat list, no expand/collapse needed

---

## PEAK SUPPRESSION ARCHITECTURE

Suppression decision pre-baked in `causal_graph.py` as boolean per alert.
Agent B reads boolean only — no runtime decision tree.

| Alert | Peak suppression | Reason |
|-------|-----------------|--------|
| G1 | Enabled | Planned peak — stockout spend should already be managed |
| G2 | Enabled | Reorder decisions are planned not reactive |
| G3 | Deferred Phase 2 | N/A |
| G4 | DISABLED | Waitlist opportunity highest during peak — founder must know |
| F1 | Enabled | Clean baseline logic handles event exclusion |
| F2 | DISABLED | Checkout errors always critical regardless of calendar |
| F4 | DISABLED | Storefront errors always require immediate action |
| F5 | Enabled | Clean baseline logic handles event exclusion |

When suppression is active and alert is suppressed:
- Agent D does NOT send any message to the founder
- Internal log only: `suppression_log` with reason and event window

---

## G-SERIES ALERT LANGUAGE

### G1 — Stockout During Active Spend

**Urgency tier:** CRITICAL 🔴

**When it fires:** Any SKU with zero inventory AND active Meta/TikTok/Google
spend confirmed in same day. No minimum threshold — any confirmed stockout
with active spend is CRITICAL.

**Peak suppression:** Enabled — see architecture table above.

**Variant vs full SKU detection:**
- Full SKU stockout: all variants at zero inventory → pause full ad set +
  remove from catalogue
- Variant stockout: specific size/colour at zero → exclude that variant
  from catalogue feed only — do not pause full ad set
Agent D must detect which case applies and generate the correct brief.

**Duration of burn:** Calculate `days_since_sku_went_oos` from
`stg_shopify_inventory_levels`. Always show in alert — changes urgency framing.

**Platform split:** Show spend breakdown per channel separately.
If multiple channels burning spend → generate separate copy-paste brief
per channel. One brief per platform, not one combined brief.

**Missed revenue formula:**
`clicks_to_zero_inventory_sku × historical_cvr × AOV`
Fallback if SKU-level click mapping unavailable: spend-only with disclosure:
*"Missed revenue estimate unavailable — ad set to SKU mapping not configured."*

**Restock ETA — one-tap:**
After showing the alert, present:
```
When is this SKU restocking?
[ Within 7 days ]  [ More than 7 days ]  [ Not sure ]
```
ETA response changes the media buyer brief:
- ≤7 days: pause spend, keep in catalogue
- >7 days or Not sure: pause spend AND remove from active catalogue

**PS monitoring:** Checks every hour after alert fires. Confirms when spend
stops. If spend continues after 2 hours → re-alerts founder.
Disclosure: *"Confirmation subject to [Airbyte sync cadence] data lag —
not real-time."*

**Founder alert:**
```
🔴 Active Spend on Out-of-Stock SKUs — Action Required

[N] SKUs have zero inventory but are still receiving paid spend.
This has been running for [X] days.

Wasted spend (last 24hrs): $[X]
Missed revenue opportunity: $[Y]
Combined profit impact: $[Z]

[SKU Name 1] — [Full SKU stockout / Size XS only]
  Meta: $[X] | TikTok: $[X] | Google: $[X]
[SKU Name 2] — [Full SKU stockout / Size M only]
  Meta: $[X] | TikTok: $[X] | Google: $[X]
[SKU Name 3] — [Full SKU stockout / Size L only]
  Meta: $[X] | TikTok: $[X] | Google: $[X]
Show all [N] SKUs ↓

When is this restocking?
[ Within 7 days ]  [ More than 7 days ]  [ Not sure ]

─────────────────────────────
Forward to your Meta media buyer:

"Please action immediately —

[If full SKU stockout:]
Pause all ad sets and remove from active catalogue.

[If variant stockout:]
Exclude [size/colour] from product catalogue feed only —
do not pause the full ad set.

Redirect freed budget to: [SKU A], [SKU B], [SKU C]
(your top 3 in-stock SKUs by current ROAS)

Affected: Meta campaigns
Urgency: inventory confirmed zero as of [timestamp]"
─────────────────────────────
[If TikTok also burning spend — separate brief generated:]
Forward to your TikTok media buyer:

"Please action immediately —
[Same structure as above, TikTok-specific]"
─────────────────────────────

We'll check every hour and confirm once spend stops.
If spend continues after 2 hours we'll alert you again.
Note: confirmation subject to data sync lag — not real-time.
```

**Layer 2:** Per-SKU spend per channel, inventory_quantity = 0 confirmed date,
days since OOS
**Layer 3:** Last stockout-with-spend event + total wasted spend that time.
If history < 30 days: *"Insufficient history — this is your first recorded
stockout-with-spend event."*
**Layer 4:** Platform-split copy-paste briefs

---

### G2 — Inventory Depth Warning

**Urgency tier:** INFORMATIONAL 🟡

**When it fires:** `days_remaining < supplier_lead_time_days` for any active SKU.
Default supplier lead time: `client_config.supplier_lead_time_days` = 21 days.
SKU-level override: `sku_cost_master.supplier_lead_time_days` — use if present,
fall back to client_config if absent.

**Peak suppression:** Enabled — see architecture table above.

**SKU list:** Top 5 by days_remaining ascending (most urgent first).
Show all/less expand-collapse. If ≤5 at-risk SKUs: flat list.

**Threshold:** Only show SKUs where `days_remaining < supplier_lead_time_days`.
Do not show SKUs merely approaching the window.

**Systemic failure threshold:** If >20 SKUs simultaneously inside reorder window:
Switch to systemic failure framing — different alert language:
*"20+ SKUs are inside your reorder window simultaneously — this suggests
a systemic inventory planning gap, not isolated stockouts. Review your
reorder process before actioning individual SKUs."*

**Days remaining formula:**
`days_remaining = current_inventory_quantity / avg_daily_units_sold_7d`
Linear extrapolation only. Display with `~` prefix on all estimates.

**Trend indicators** (compare trailing 7d vs trailing 14d sell-through rate):
- Accelerating ↑: 7d sell-through > 14d sell-through by >10%
- Stable →: within 10% either direction
- Slowing ↓: 7d sell-through < 14d sell-through by >10%

**Trend caveats per direction:**
- Accelerating: "(based on last 7 days — actual may be faster)"
- Stable: "(based on last 7 days average sales)"
- Slowing: "(based on last 7 days — actual may be slower)"

**Product age:** Always shown from Shopify `product.created_at`.
Format: "Listed [X] days ago"

**Collection tag:** Show where available from Shopify collections.
Omit gracefully where not — never show "No collection tag" as an error.

**Markdown nudge:** Auto-added when `product_age > 120 days`
AND sell-through trend = Slowing:
*"Listed [X] days ago with slowing sales — consider markdown before reordering."*

**Display rule for avg_days_on_hand = 999:**
Never display 999. Exclude from calculations. Show separately:
*"[N] SKUs excluded — zero sales in 30+ days (likely overstock or discontinued)."*

**Lead time disclosure:** When using brand-level default (not SKU-level):
*"Lead time based on your default [X]-day setting. Update per-SKU in
Sentinel settings for more precise alerts. [link]"*

**Reorder summary — copy-paste format:**
```
─────────────────────────────
Reorder summary — [date]

[SKU name] | ~[X] days remaining | Accelerating ↑
Listed [X] days ago | Lead time: [X] days
Action: Reorder — demand still growing

[SKU name] | ~[X] days remaining | Stable →
Listed [X] days ago | Lead time: [X] days
Action: Reorder with standard quantity

[SKU name] | ~[X] days remaining | Slowing ↓
Listed [X] days ago | Lead time: [X] days
Action: Consider markdown before reordering
─────────────────────────────
```

No reorder quantity recommendation in Phase 1 — too many fashion nuances
(decay factor, collection lifecycle, markdown cadence, size curve distortion).
Deferred to Phase 2 with real client data.

**Founder alert:**
```
🟡 Inventory Running Low — Reorder Window Opening

[N] SKUs are inside your [supplier_lead_time_days]-day reorder window.

[SKU name]: ~[X] days remaining ↑ sell-through accelerating
  Listed [X] days ago | Collection: [SS25 Core if available]
  (based on last 7 days average sales — actual may be faster)

[SKU name]: ~[X] days remaining → sell-through stable
  Listed [X] days ago
  (based on last 7 days average sales)

[SKU name]: ~[X] days remaining ↓ sell-through slowing
  Listed [X] days ago
  Consider markdown before reordering
  (based on last 7 days average sales — actual may be slower)

Show all [N] SKUs ↓

[Reorder summary — copy-paste block above]

ⓘ Data note [collapsed by default — tap to expand]:
Days remaining is a linear extrapolation only. Does not account
for collection lifecycle decay, planned markdowns, or size curve
distortion. Use directionally, not as a precise forecast.
[If using brand-level lead time default: Lead time based on your
default [X]-day setting — update per-SKU for more precision. [link]]
```

**Layer 2:** Per-SKU inventory quantity, avg_daily_units_sold_7d,
sell_through_rate_7d vs sell_through_rate_14d
**Layer 3:** Last reorder date if available in Shopify purchase orders
**Layer 4:** Reorder summary copy-paste block

---

### G3 — Zero-Velocity SKU With Active Spend

**Status: `deferred_phase2`**

**Reason:**
1. SKU-level spend mapping unreliable at $2M–$10M tier — catalogue ads
   prevent clean SKU → spend attribution
2. Long-tail zero-velocity SKUs are normal in fashion — 14-day zero sales
   threshold generates high false positive rate on normal brand behaviour

**Phase 2 prerequisites before rebuilding:**
1. Reliable SKU-level spend mapping via catalogue feed integration or
   founder-managed SKU → campaign tagging
2. Per-SKU velocity baseline from 90+ days real client data
3. Dead stock detection redesigned as separate alert with own data
   dependencies and action sequence

**Customer discovery flag:** If dead stock surfaces as top-3 unsolved pain
point in interviews, prioritise G3 redesign before other Phase 2 alerts.

**No Agent D spec required for Phase 1.**

---

### G4 — Back-in-Stock Waitlist Opportunity

**Urgency tier:** INFORMATIONAL 🟡

**When it fires:**
`waitlist_count × AOV > 15% of trailing 90-day avg daily revenue`

**Peak suppression:** DISABLED — waitlist opportunity is highest during
peak events. Founder must know about this regardless of calendar.

**Discontinued SKU suppression:**
Suppress if ALL three conditions met:
- Zero sales in trailing 90 days
- Listed > 180 days
- No restock detected in last 60 days
Do NOT rely on `product_status` or `inventory_policy` — founders don't
maintain these fields consistently. Infer from behaviour only.

**Waitlist source:** Klaviyo only.
Shopify has no native waitlist — third-party apps not accessible in Phase 1.
Disclosure in collapsed footnote on every G4 alert — not just at onboarding.

**Klaviyo flow check:** Do not check flow existence — check trigger count.
If `klaviyo_back_in_stock_flow_triggered_count` in trailing 90 days = 0
despite waitlist signups existing → flag:
*"Your back-in-stock flow exists but hasn't triggered in 90 days —
check configuration before your restock arrives."*

**Recovery estimate — waitlist-age-based multiplier:**
Use founder's own historical back-in-stock CVR when ≥3 restock events
available. Otherwise use multiplier against store avg CVR:

| Waitlist age | Multiplier |
|-------------|-----------|
| < 2 weeks | 2.0–2.5x store avg CVR |
| 2–6 weeks | 1.5–2.0x store avg CVR |
| > 6 weeks | 1.0–1.5x store avg CVR |

Display as range, not single number:
*"$[X]–$[Y] in potentially recoverable revenue"*

**Restock options — 5 choices:**
```
Is a restock coming?
[ Within 2 weeks ]  [ Within 30 days ]
[ No — discontinuing ]  [ Not sure ]
[ Checking with my team — remind me tomorrow ]
```

**Follow-up logic per response:**
- Within 2 weeks: confirm Klaviyo flow active + urgency messaging guidance
- Within 30 days: same as above + pre-order option suggestion
- No — discontinuing: markdown guidance to clear remaining inventory
- Not sure: treat as >6 weeks decay, temper expectations
- Checking with team: 24-hour reminder, max 2 reminders, then defaults
  to "Not sure" action sequence. Never nags beyond 2 reminders.

**Beta-validation flag:** Review after first 3 beta clients. Cut from
active alerts if founder feedback consistently indicates no value over
Klaviyo native back-in-stock flow view.

**Founder alert:**
```
🟡 Waitlist Revenue Opportunity — [SKU name]

[N] customers are waiting for this to come back in stock.

Estimated recoverable revenue:
$[X]–$[Y] based on your store's average conversion rate
([waitlist age bracket] waitlist — [multiplier range]x recovery expected)

[If founder's own history available:]
Based on your last [N] restock events: $[X]–$[Y] estimated

Waitlist age breakdown:
- < 2 weeks: [N] customers
- 2–6 weeks: [N] customers
- > 6 weeks: [N] customers

[If flow hasn't triggered in 90 days:]
⚠️ Your back-in-stock flow hasn't triggered in 90 days —
check configuration before your restock arrives.

Restock status: Last restocked [X] days ago

Is a restock coming?
[ Within 2 weeks ]  [ Within 30 days ]
[ No — discontinuing ]  [ Not sure ]
[ Checking with my team — remind me tomorrow ]

─────────────────────────────
[After founder selects Within 2 weeks:]
Action:
1. Confirm your Klaviyo back-in-stock flow is correctly configured
2. Add urgency to notification — limited restock quantity,
   first-come-first-served messaging
3. Consider early access email to longest-waiting customers first

[After founder selects Within 30 days:]
Action:
1. Same as above
2. Consider launching a pre-order now — capture intent before
   stock arrives and improve cash flow

[After founder selects No — discontinuing:]
Action:
Consider a final markdown to clear remaining inventory before
formally archiving this SKU.

[After founder selects Not sure:]
Action:
Decide within 48 hours — waitlist intent decays quickly.
At > 6 weeks, recovery rate drops significantly.

[After founder selects Checking with team:]
No action sequence shown. 24-hour reminder scheduled.
─────────────────────────────

ⓘ Data note [collapsed by default — tap to expand]:
Waitlist figures from Klaviyo only. If you capture back-in-stock
signups via a separate app, actual waitlist size may be larger.
Recovery estimate is directional — actual results depend on
email deliverability, offer strength, and time since signup.
```

**Layer 2:** waitlist_count by age bracket, AOV, revenue range calculation
**Layer 3:** Last restock event + actual recovery rate (if ≥1 prior restock)
**Layer 4:** Action sequence based on founder's restock ETA response

---

## F-SERIES ALERT LANGUAGE

### F1 — Mobile Checkout Completion Rate → CVR

**Urgency tier:** HIGH 🟠

**Activation:** Conditional — requires GA4 Enhanced Ecommerce step-level
events confirmed at onboarding.

If not confirmed:
- Status: `mart_column_missing`
- One-time developer prompt (sent once only):
  *"Mobile checkout monitoring requires GA4 funnel steps — not yet
  configured. This is your highest-risk unmonitored area. Your
  developer can enable this in under an hour."*

**Connector lifecycle:** Monthly Airbyte connector inventory check runs
automatically. When GA4 source appears that wasn't present at onboarding:
- Triggers partial re-onboarding for GA4 only
- Sends Slack message: *"We've detected GA4 is now connected. Mobile
  checkout funnel monitoring is now active — here's what we found in
  your first week of data."*
Founder does not need to remember to notify PS. Detection is automatic.

**Firing condition:**
- `mobile_checkout_completion_rate_7d` drops >10% from clean 28-day baseline
- Clean baseline excludes: major event days (is_major = true) + 3 days pre
  + 5 days post each major event
- Auto-detection of unlabelled events: exclude days where
  `daily_spend > (90d_avg_spend × 2.5)` AND
  `daily_spend > client_config.spend_event_detection_floor` (default $300)
  AND minimum 30 days spend history exists
- Session floor: 200 mobile checkout initiations in trailing 7 days
  (checkout initiations, not total sessions)
- Insufficient clean baseline: suppress if <15 clean days in 28-day window
  → log `scan_skipped_reason = 'insufficient_clean_baseline'`
  → one-time founder message per standard skip spec above

**GA4 synthetic seeding:** Seed `ga4_checkout_funnel_steps` with mobile vs
desktop completion rates → F1 status `active` in synthetic environment.
Flag for Claude Code session.

**Two-path Agent D logic:**

**Path A — Sentry errors elevated (sentry_affected_users ≥ 5):**
```
🟠 Mobile Checkout Drop — JavaScript Error Detected

Mobile checkout completion dropped from [X]% to [Y]% in the last
24 hours — [Z]% below your normal rate.
Sentry confirms [N] customers hit JavaScript errors during checkout.
Estimated impact: $[X] per hour.

Check in this order:
1. Review Sentry for the specific error — link: [sentry_dashboard_url]
2. Roll back your most recent theme change if made in last 48 hours
3. Disable your most recently installed Shopify app
4. Test checkout manually on a real mobile device
```

**Path B — Sentry silent (sentry_affected_users < 5):**
```
🟠 Mobile Checkout Drop — No JavaScript Errors Detected

Mobile checkout completion dropped from [X]% to [Y]% in the last
24 hours — [Z]% below your normal rate.
No JavaScript errors detected — the issue is likely outside our
visibility.

Check in this order:
1. Test your checkout manually on a real mobile device right now
2. Check for any recent theme or app changes in the last 48 hours
3. If no changes made — this may be a rendering or layout issue
   that Sentry cannot detect
```

**Language rule:** Never say "rendering or layout issue" as a diagnosis.
Always say "likely outside our visibility." We cannot confirm the cause
when Sentry is silent.

**Layer 2:** mobile_checkout_completion_rate_7d vs 28d clean baseline,
mobile session count, sentry_affected_users
**Layer 3:** Last time mobile completion dropped this far + what caused it
(if known from prior founder follow-up)
**Layer 4:** Path A or Path B action sequence above

---

### F2 — Checkout Error Count → CVR

**Urgency tier:** CRITICAL 🔴

**Firing condition:**
- Primary: `sentry_affected_users >= client_config.checkout_error_threshold`
  (default 5) within detection window
- NO multiplier-based threshold — affected users is the primary and only
  firing condition. 1.5x multiplier approach was explicitly rejected.
- URL filter: `/checkout%` paths only
- Filter method: URL path matching — NOT Sentry tags (brands at this tier
  don't tag consistently)
- Window check 1: 1-hour rolling — fire immediately if threshold crossed
- Window check 2: 3-hour rolling — fire if 1-hour window didn't trigger
- Sentry sync cadence required: 1-hour minimum
- No peak suppression — checkout errors during BFCM are more urgent, not less

**`leading_signal_direction`:** Must be `rising` — verify in causal_graph.py.
If currently set to `declining` this is a bug — correct immediately.

**Window disclosure:** Always state which window triggered.
"in the last 1 hour" vs "in the last 3 hours" — different urgency,
founder must know.

**Threshold footer:** Always appended to every F2 alert.
*"This alert fires when [client_config.checkout_error_threshold] or more
customers encounter checkout errors. You can adjust this threshold in
your Sentinel settings. [link_to_settings]"*

**Revenue impact:** Use standard formula. Show per-hour figure (CRITICAL tier).

**Founder alert:**
```
🔴 Checkout Errors — Active Revenue Loss

[N] customers hit checkout errors in the last [1 hour / 3 hours].
Estimated revenue at risk: $[X] per hour.

Error summary: [error type if available from Sentry]
Pages affected: [checkout URL paths]
Affected browsers/devices: [if available from Sentry]

Check in this order:
1. Review Sentry for error details — link: [sentry_issue_url]
2. Test checkout manually right now on mobile and desktop
3. Roll back any theme changes made in the last 48 hours
4. Check Shopify Payments status — [shopify_payments_status_url]
5. Disable most recently installed app if no theme changes made

We'll check every hour and confirm once errors stop.

─────────────────────────────
This alert fires when [N] or more customers encounter checkout
errors. Adjust in Sentinel settings. [link]
```

**Layer 2:** sentry_affected_users count, error URLs, browser/device breakdown
**Layer 3:** Last checkout error event + revenue lost that time
**Layer 4:** Ordered action sequence above

---

### F3 — Bounce Rate → CVR

**Status: `deferred_phase2`**

**Reason:** Blended bounce rate insufficient for actionable founder alert
without source-level GA4 breakdown. B-series covers paid traffic quality
upstream. Founder cannot action "bounce rate up, CVR down" without knowing
which traffic source caused it.

**Revisit condition:** GA4 Enhanced Ecommerce with UTM passthrough confirmed
at onboarding AND source-level bounce rate available per campaign.

**No Agent D spec required for Phase 1.**

---

### F4 — Non-Checkout Sentry Errors → CVR

**Urgency tier:** HIGH 🟠

**Scope:** Non-checkout Sentry errors ONLY.
Agent D must compute: `total_sentry_error_count - checkout_error_count`
This prevents F2 and F4 firing simultaneously on the same event.

**`leading_signal_direction`:** Must be `rising` — verify in causal_graph.py.
Same bug risk as F2 — correct if wrong.

**Firing condition:**
- `sentry_affected_users >= client_config.checkout_error_threshold` (default 5)
  in 24-hour window — non-checkout URLs only
- Corroborating: `ga4_pdp_bounce_rate` — may be NULL if GA4 absent
  Treat NULL as unconfirmed, not a failed gate. Alert fires regardless.

**Claude Code flag:** Confirm whether `stg_shopify_script_tags` or
`stg_shopify_themes` exists in staging. If yes, Agent D can surface
most recent theme/app change date automatically in the alert body.

**Transparency rule:** Never claim to know the cause. Always ordered
checklist. Never say "the cause is X" — say "check X first."
Never say "rendering or layout issue" — say "outside our visibility."

**Founder alert:**
```
🟠 Storefront Errors Detected — Conversion Impact

JavaScript errors spiked on your product pages in the last 24 hours,
affecting [N] customers. CVR dropped from [X]% to [Y]%.
Estimated impact: $[X] per hour.

Pages affected: [top 3 URLs from Sentry with error counts]
[If stg_shopify_themes available: Most recent theme change: [date]]
[If stg_shopify_script_tags available: Most recently installed app: [name, date]]

Check in this order:
1. Any theme changes in the last 48 hours — roll back if yes
2. Any recently installed or updated apps — disable most recent first
3. If neither — this may be a third-party widget or browser update
   outside our visibility

Share this error log with your developer: [sentry_issue_url]
```

**Layer 2:** sentry_affected_users (non-checkout), affected URLs,
ga4_pdp_bounce_rate if available
**Layer 3:** Last non-checkout error spike + CVR impact that time
**Layer 4:** Ordered action sequence above + Sentry link

---

### F5 — Checkout Funnel Step Drop → CVR

**Urgency tier:** HIGH 🟠

**Source:** GA4 Enhanced Ecommerce step-level events ONLY.
Sentry is corroborating signal only — not primary source.
F5 measures WHERE in checkout customers drop. F2 measures THAT errors exist.
These are complementary, not duplicate.

**Activation:** Conditional — GA4 step-level events confirmed at onboarding.
- Confirmed: `active`
- Not confirmed: `mart_column_missing`
  One-time developer prompt: *"GA4 checkout step tracking isn't configured —
  we can't identify which specific step is losing customers.
  Your developer can enable this in 30 minutes."*

**F5 independence from F2:** F5 must have its own firing condition tied
specifically to GA4 step-level abandonment rate. Must NOT re-fire on
the same threshold as F2.

**When F2 and F5 fire simultaneously:** F2 takes priority as separate
CRITICAL alert. F5 fires as a thread reply to F2:
*"Step-level data confirms the [step name] specifically — [X]% abandonment
vs your [Y]% normal rate."*

**Firing condition:**
- Specific checkout step abandonment rate > 2x that step's own clean baseline
- Same clean baseline logic as F1 (28-day, major event exclusion ±3/5 days,
  spend detection 2.5x 90d avg, min 30 days spend history)
- Minimum: 50 sessions reaching that specific step in trailing 24 hours
- Insufficient clean baseline: suppress → log `scan_skipped_reason`

**Traffic quality vs technical failure discrimination:**
Check spend composition before firing:
- If `awareness_campaign_spend_pct` increased >30% in same 24-hour window
  AND step drop is at checkout INITIATION step only:
  → Traffic quality framing (Path B)
- All other cases: technical failure framing (Path A)

**Sentry corroboration:**
- `sentry_affected_users ≥ 5` in same window → high confidence technical
- `sentry_affected_users < 5` → non-technical cause likely

**Step-specific checklists:**

**Initiation step — Path A (technical, Sentry elevated):**
```
🟠 Checkout Entry Drop — Possible Technical Issue

[X]% of customers who added to cart did not reach checkout today —
[Y]% above your normal rate. Sentry confirms [N] errors.
Estimated impact: $[X] per hour.

Check in this order:
1. Cart page rendering on mobile — test manually right now
2. "Proceed to checkout" button — confirm it loads correctly
3. Any recent theme changes affecting cart page
4. Share error log with developer: [sentry_url]
```

**Initiation step — Path B (traffic quality):**
```
🟡 Checkout Entry Drop — Likely Traffic Quality

[X]% of customers who added to cart did not reach checkout today.
Your awareness campaign spend increased significantly in the same
window — this is likely low-intent traffic, not a technical issue.

Check in this order:
1. Review audience targeting on campaigns launched in last 48 hours
2. Check if broad/awareness audiences are driving add-to-cart
   without purchase intent
3. No immediate technical action required
```

**Shipping step (Sentry silent):**
```
🟠 Checkout Drop at Shipping Step

[X]% of customers abandoned at the shipping step today —
[Y]% above your normal rate. No JavaScript errors detected.

Commonly caused by (check in this order):
1. Unexpected shipping cost — confirm free shipping threshold
   is visible before checkout begins
2. No express delivery option available
3. International shipping restrictions not clearly communicated
4. Recent change to shipping rates or zones in Shopify

We'll follow up in your weekly summary to understand what you found.
```

**Payment step (Sentry silent):**
```
🟠 Checkout Drop at Payment Step

[X]% of customers abandoned at the payment step today —
[Y]% above your normal rate. No JavaScript errors detected.

Commonly caused by (check in this order):
1. Check if your preferred payment methods are all active in
   Shopify Payments — particularly any recently added or removed options
2. Discount code field visible — customers may be leaving to find a code
3. Price anxiety at final confirmation — consider urgency messaging
   (stock count, offer expiry)
4. Recent theme change affecting payment UI on mobile

We'll follow up in your weekly summary to understand what you found.
```

**Payment method language rule:** Never hardcode specific payment method
names (Shop Pay, Klarna, Apple Pay etc.). Generic language only.
Specific method recommendations deferred to Phase 2.

**Peer benchmark language rule:**
- At launch: "Commonly caused by" framing — no percentages
- After 5+ real clients with follow-up responses logged: replace with
  actual percentages from real client data
- Never use synthetic data percentages in founder-facing language

**Weekly follow-up Slack message:**
Sent 7 days after F5 fires. One message per F5 firing event.

```
Following up on last week's checkout drop at [step name]:

What did you find? (tap to respond)

[ Technical issue — fixed ]
[ Shipping/payment friction — adjusted ]
[ Traffic quality — targeting changed ]
[ Checking with my team — remind me tomorrow ]
[ Still investigating ]
[ Not sure ]
```

**Slack button spec:**
- action_id: `f5_followup_response`
- Values: `technical_fixed` / `friction_adjusted` / `traffic_quality` /
  `checking_with_team` / `still_investigating` / `unknown`
- Response stored in `alert_log` against original F5 alert_id
- Feeds causal graph confidence scoring over time
- "Checking with my team": 24-hour reminder, max 2 follow-ups,
  then defaults to `unknown` if no response

**Layer 2:** Step-level abandonment rate vs baseline, session count at
that step, sentry_affected_users, awareness_campaign_spend_pct
**Layer 3:** Last time this step dropped this far + what founder found
(from prior follow-up response if available)
**Layer 4:** Step-specific checklist above

---

## SHARED AGENT D RULES — ALL ALERTS

### Currency
Always use `client_config.currency` — default USD ($) for US market.
Never hardcode any currency symbol in alert templates.

### Threshold footer
Any alert with a founder-configurable threshold must include a one-line
footer with current threshold value and settings link.
Format: *"This alert fires at [threshold]. Adjust in Sentinel settings. [link]"*

### Layer 0 disclosure — active_proxy alerts
When alert status is `active_proxy`, prepend to alert:
*"Note: [signal name] is estimated — [true signal] data not yet available.
Treat directionally, not as precise measurement."*

### Collapsed footnote — structural limitations
For alerts with permanent data limitations (not fixable by connecting
a new source): show "ⓘ Data note" collapsed by default. Tap to expand.
Applies on every firing of the alert — not just at onboarding.
Do not show as a warning banner or confidence tag on the main alert body.

### Sentry URL generation
- Sentry issue_id available: link to `sentry.io/issues/{issue_id}`
- Not available: link to Sentry project dashboard
- Never link to raw API endpoint

### Revenue impact display
- CRITICAL tier: per-hour figure
- HIGH tier: per-hour figure
- INFORMATIONAL tier: daily or projected figure
- Always round to nearest $50
- Never show if < $50 — use "low revenue impact" instead

### Show all / Show less
Standard expand-collapse on all SKU lists.
"Show all [N] SKUs ↓" / "Show less ↑"
Flat list when total ≤ default visible count.

---

## CLAUDE CODE FLAGS — PENDING VERIFICATION

| Flag | Action required |
|------|----------------|
| `checkout_error_count` SQL scope | Read `mart_causal_chain_daily.sql` — confirm filtering by `/checkout%` URL or counting all Sentry errors. If all Sentry errors: fix to URL filter |
| `stg_shopify_script_tags` / `stg_shopify_themes` | Confirm if table exists in staging — if yes, Agent D surfaces recent theme/app change date in F4 alert automatically |
| F2 `leading_signal_direction` | Verify = "rising" in causal_graph.py — correct if "declining" (bug) |
| F4 `leading_signal_direction` | Verify = "rising" in causal_graph.py — correct if "declining" (bug) |
| GA4 funnel step seeding | Seed `ga4_checkout_funnel_steps` with mobile vs desktop completion rates → F1 and F5 status `active` in synthetic |
| Sentry Airbyte sync cadence | Set to 1-hour minimum — daily sync makes F2 a post-mortem not an alert |
| G3 causal_graph.py | Update status to `deferred_phase2` — remove from active chains |
| G4 peak_suppression | Set to `enabled: False` in causal_graph.py — currently incorrect |
| Monthly Airbyte connector check | Build scheduled check: new connector detected → partial re-onboarding trigger → gap message resolved automatically |

---

## OPEN DECISIONS — NOT YET LOCKED

| Item | Status |
|------|--------|
| Peer benchmark percentages for F5 | Deferred — need 5+ real clients with follow-up responses |
| Payment method specific recommendations | Deferred Phase 2 |
| F3 full redefinition | Deferred Phase 2 — needs source-level GA4 |
| G3 redesign | Deferred Phase 2 — needs SKU-level spend mapping + 90d real data |
| G4 beta-validation cut decision | Review after first 3 beta clients |
| `spend_event_detection_floor` calibration | Beta-calibrate with first 3 real clients (default $300) |
| F1/F5 firing threshold calibration | Beta-calibrate with first 3 real clients |
| Reorder quantity recommendation for G2 | Deferred Phase 2 — decay factor, collection lifecycle, size curve too complex for Phase 1 |
| G4 waitlist multiplier calibration | Replace with founder's own data when ≥3 restock events available |

---

## E-SERIES ALERT LANGUAGE
## Status: E1 Locked — E2–E4 Pending
## Session: 2026-05-23

---

## ARCHITECTURAL DECISIONS — E-SERIES (ALL ALERTS)

### Klaviyo data constraints (real-data validated)
- `stg_klaviyo_flows` has no date column — all time-series Klaviyo CTEs use `stg_klaviyo_email_events`
- `stg_klaviyo_profiles` column names: `profile_id` (not `customer_id`), `vip_status` (not `is_vip`)
- Klaviyo Airbyte sync cadence: 6 hours — all E-series alerts have inherent 6-hour data lag. Disclose in alert footer when relevant.
- All open rate calculations use `effective_open_rate = reported_open_rate × ios_mpp_multiplier` (default 0.65). Never raw reported_open_rate.
- Click rate is primary engagement metric — immune to Apple MPP inflation, cannot be machine-generated.
- Campaign type classification from raw Klaviyo data is UNRELIABLE at this GMV tier — agency-managed accounts use inconsistent naming conventions. Never fire or diagnose based on campaign_type inference from Klaviyo campaign names.

---

## E1 — List Health Degradation

**Status:** LOCKED — INFORMATIONAL 🟡

**Urgency tier:** INFORMATIONAL 🟡
CRITICAL escalation (spam complaint rate) — DEFERRED to post-beta. Not at launch.

**Primary signal:** `effective_click_rate_28d`
- 28-day rolling effective click rate
- Drops ≥30% below trailing 90-day baseline
- Persists ≥7 consecutive days
- Minimum 5 campaign sends in 28-day window
- No `brand_event_calendar` event active that explains the drop
All conditions required. If any not met → silent skip, log `scan_skipped_reason`.

**When it fires — Agent B diagnosis:**
Surface last 3 campaign send dates + raw click rates from `stg_klaviyo_email_events`.
No campaign type classification. Founder identifies outlier themselves.

**Dropped entirely (do not implement):**
- Unsubscribe volume as trigger or signal
- Hard bounce rate as trigger
- Spam complaint rate as trigger or corroborating signal
- Campaign type classification
- BFCM sunset suppression (irrelevant now unsubscribe dropped)
- E1 CRITICAL escalation path

**Deferred to weekly summary (not alerts):**
- Spam complaint rate trend
- Hard bounce rate trend

**Peak suppression:** Enabled — brand_event_calendar events suppress E1.

**Pending mart column:**
- `effective_click_rate_28d` — add to `mart_causal_chain_daily`
- Source: `stg_klaviyo_email_events`, 28-day rolling, adjusted by `ios_mpp_multiplier`

**Founder alert:**
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

**Layer 2:** effective_click_rate_28d value, 90-day baseline, last 3 campaign send dates + click rates
**Layer 3:** Last time click rate dropped this far + what recovered it (from prior follow-up if available)
**Layer 4:** Founder-directed — no prescriptive checklist. Raw data surfaced, founder investigates.


---

## E-SERIES ALERT LANGUAGE
## Status: E1 Locked — E2–E4 Pending
## Session: 2026-05-23

---

## ARCHITECTURAL DECISIONS — E-SERIES (ALL ALERTS)

### Klaviyo data constraints (real-data validated)
- `stg_klaviyo_flows` has no date column — all time-series Klaviyo CTEs use `stg_klaviyo_email_events`
- `stg_klaviyo_profiles` column names: `profile_id` (not `customer_id`), `vip_status` (not `is_vip`)`
- Klaviyo Airbyte sync cadence: 6 hours — all E-series alerts have inherent 6-hour data lag. Disclose in alert footer when relevant.
- All open rate calculations use `effective_open_rate = reported_open_rate × ios_mpp_multiplier` (default 0.65). Never raw reported_open_rate.
- Click rate is primary engagement metric — immune to Apple MPP inflation, cannot be machine-generated.
- Campaign type classification from raw Klaviyo data is UNRELIABLE — agency-managed accounts use inconsistent naming. Never fire or diagnose based on campaign_type inference.

---

## E1 — List Health Degradation

**Status:** LOCKED — INFORMATIONAL 🟡

**Primary signal:** `effective_click_rate_28d`

**Firing condition (ALL required):**
- Drops ≥30% below trailing 90-day baseline
- Persists ≥7 consecutive days
- Minimum 5 campaign sends in 28-day window
- No `brand_event_calendar` event active

If any condition not met → silent skip, log `scan_skipped_reason`.

**Agent B diagnosis when fires:**
Last 3 campaign send dates + raw click rates from `stg_klaviyo_email_events`.
No campaign type classification. Founder identifies outlier themselves.

**Dropped permanently:**
- Unsubscribe volume as trigger
- Hard bounce rate as trigger
- Spam complaint rate as trigger or corroborating signal
- Campaign type classification
- BFCM sunset suppression
- E1 CRITICAL escalation path

**Deferred to weekly summary:**
- Spam complaint rate trend
- Hard bounce rate trend

**Pending mart column:**
`effective_click_rate_28d` — add to `mart_causal_chain_daily`
Source: `stg_klaviyo_email_events`, 28-day rolling × `ios_mpp_multiplier`

**Founder alert:**
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

## E2 — Repeat Purchase Rate Declining

**Status:** LOCKED PARTIAL — firing condition and denominator logic locked. Alert language pending E2 structural critique completion.

**Urgency tier:** INFORMATIONAL 🟡

**Primary signal:** `repeat_purchase_rate_90d` (already exists in mart — commit b44ae63)

**Firing condition:**
- `repeat_purchase_rate_90d` drops ≥5 percentage points below trailing 28-day average
- `new_customer_pct_90d` has NOT surged >15% in same window (if yes → S33 fires, not E2)
- Minimum 50 repeat customers in 90-day window — below this suppress, log `scan_skipped_reason = 'insufficient_repeat_customer_count'`
- No brand_event_calendar event active

**S33 check is mandatory pre-condition — Agent B runs this before firing E2 every time.**

---

## E2 — DISCOUNT CLASSIFICATION ARCHITECTURE (LOCKED)

### Purpose
Exclude discount-motivated repeat customers from E2 denominator to prevent false positives from sale-event cohorts inflating total buyer count.

### Scope
- Applies to repeat customers with 3+ lifetime orders ONLY
- New customers (1-2 orders) are NEVER classified as discount-motivated — always stay in denominator
- First-time buyers during sales are new customers, not discount seekers — classification requires purchase pattern evidence

### Step 1 — Auto-derive Brand Event Calendar (Approach B)
Runs at onboarding via `historical_pattern_scan.py`. Updates monthly.

**Event day qualification:**
```
qualifying_day = daily_order_count > median(daily_order_count)
                 across all days with orders > 0
```
Days below median order volume → excluded from event classification (too sparse).

**Event type classification (percentile-based, no hardcoded thresholds):**
```
Type 1 (deep sale)     = avg_discount_depth > p75 of all qualifying event days
Type 2 (moderate sale) = avg_discount_depth between p50 and p75
Type 3 (BAU)           = avg_discount_depth below p50
```

**Real-time forward detection:**
New sale events detected in real-time when:
- Daily order volume > median AND
- Average discount depth crosses p50 threshold
Type assigned by which percentile band discount depth falls into.
Thresholds recalibrated monthly at each incremental scan to prevent threshold creep.

**Known limitations:**
- BFCM days in median calculation cause slight upward bias — not a blocker at this GMV tier
- Gap 2 closed: real-time detection uses onboarding-derived thresholds applied forward

### Step 2 — Welcome Discount Code Exclusion
At onboarding confirmation flow: founder confirms which discount codes are welcome-only codes (e.g. WELCOME10, FIRST15).
Written to `client_config.welcome_discount_codes[]`.
Orders using these codes excluded from discount depth calculations in Step 1 and Step 3.

### Step 3 — Customer Classification (Approach A)
Applies only to customers with 3+ lifetime orders.

```
customer_discount_ratio = sum(order_discount_amount) / sum(order_subtotal)
                          across all lifetime orders
                          excluding welcome_discount_codes orders

brand_discount_mean = mean(customer_discount_ratio) across all 3+ order customers
brand_discount_sd   = standard_deviation(customer_discount_ratio)

discount_motivated = customer_discount_ratio > brand_discount_mean + (1.5 × brand_discount_sd)
```

**Known limitation:** At brands with low discount variance, 1.5 SD is tighter — more customers flagged. At high variance brands, fewer flagged. Self-calibrating by design. Beta validation required — flagged in pre_agent_build_checklist.md.

### Denominator Rule
```
e2_denominator = all buyers in 90-day window
                 EXCLUDING discount_motivated customers (3+ orders, ratio > mean + 1.5 SD)
                 NEVER excluding new customers (1-2 orders)
```

### New Client Data Sufficiency
If historical order data < 12 months → insufficient to derive stable thresholds.
Action: proceed without discount exclusion, log `discount_classification_status = 'insufficient_history'` in client_config. Disclose in E2 alert footnote.

---

## E2 — PENDING ITEMS (not yet locked)
- Alert language (pending structural critique completion)
- Segment breakdown spec (mart_customer_segments_daily join)
- Gorgias cross-reference spec
- `new_customer_pct_90d` mart column confirmation


---

## E2 — COLLECTION LAUNCH DETECTION AND SUPPRESSION (LOCKED)

### Collection Launch Auto-Detection
Runs in `historical_pattern_scan.py` at onboarding and monthly incremental scan.
Writes confirmed launch events to `brand_event_calendar` automatically.
No founder input required. No hardcoded dates.

**Detection criteria (ALL three required within same 7-day window):**
```
1. New SKU cluster: ≥5 new product_ids created in Shopify within 7-day window
2. Paid spend spike: any connected ad channel spend >40% vs prior 7-day average
3. Traffic spike: GA4 sessions >30% vs prior 7-day average
```
Klaviyo campaign send and TikTok strengthen confidence when connected — not required.
Minimum viable detection: Shopify + any one ad channel + GA4.
Every ICP client ($2M–$10M GMV, running paid ads) will have these three.

**Written to brand_event_calendar as:**
```
event_type: 'collection_launch'
start_date: detected launch date
confidence: high (all 3 signals) / medium (2 signals)
```

### Post-Launch E2 Suppression Window
**Not a fixed number — derived from brand's own historical data:**

```
collection_launch_suppression_days = 
    median(days from launch detection until 
           repeat_purchase_rate_90d returns to 
           within 2 percentage points of pre-launch baseline)
    across all detected launches for this brand
```

Written to `client_config.collection_launch_suppression_days`.
Recalibrated at each monthly incremental scan as more launches accumulate.

**Fallback hierarchy:**
1. Brand's own median (requires ≥2 detected launches)
2. Cross-client vertical benchmark from `network_pattern_benchmarks` (requires ≥3 beta clients)
3. Default: 28 days (midpoint of realistic range, consistent with 28-day baseline architecture)

**Suppression behaviour:**
When collection launch detected → E2 suppressed for `collection_launch_suppression_days`.
Internal log: `suppression_reason = 'post_collection_launch'`
No founder message during suppression — silent.

---

## E2 — NEW CUSTOMER PCT MART COLUMN (LOCKED)

**`new_customer_pct_90d`** — add to `mart_causal_chain_daily`

```sql
new_customer_pct_90d = 
    COUNT(DISTINCT customer_id 
          WHERE order_number = 1 
          AND order_date >= date - 90)
    /
    COUNT(DISTINCT customer_id 
          WHERE order_date >= date - 90)
```

Source: `stg_shopify_orders`
No external dependency. Internal build only.
Required for S33 pre-condition check before E2 fires.


---

## E-SERIES ARCHITECTURAL DECISIONS (ALL ALERTS)

### Klaviyo data constraints — real-data validated
- `stg_klaviyo_flows` has no date column — all time-series CTEs use `stg_klaviyo_email_events`
- `stg_klaviyo_profiles` columns: `profile_id` (not `customer_id`), `vip_status` (not `is_vip`)
- Klaviyo sync cadence: 6 hours — inherent lag on all E-series alerts
- All open rate calculations: `effective_open_rate = reported_open_rate × ios_mpp_multiplier` (default 0.65)
- Click rate is primary engagement metric — immune to Apple MPP, cannot be machine-generated
- Campaign type classification: NEVER use — agency naming conventions unreliable at this GMV tier

---

## E1 — List Health Degradation — LOCKED

**Status:** LOCKED — INFORMATIONAL 🟡

**Firing condition (ALL four required):**
- `effective_click_rate_28d` drops ≥30% below trailing 90-day baseline
- Persists ≥7 consecutive days
- Minimum 5 campaign sends in 28-day window
- No `brand_event_calendar` event active
If any condition not met → silent skip, log `scan_skipped_reason`

**Agent B when fires:** Last 3 campaign send dates + raw click rates
from `stg_klaviyo_email_events`. No classification. Founder investigates.

**Dropped permanently:**
Unsubscribe volume, hard bounce rate, spam complaint rate,
campaign type classification, BFCM sunset suppression, CRITICAL escalation path

**Weekly summary only:** Spam complaint trend, hard bounce trend

**Peak suppression:** Enabled

**Pending mart column:** `effective_click_rate_28d` in `mart_causal_chain_daily`
Source: `stg_klaviyo_email_events`, 28d rolling × `ios_mpp_multiplier`

**causal_graph.py:**
- peak_suppression: enabled
- leading_signal_column: effective_click_rate_28d
- leading_signal_direction: declining

**Founder alert:**
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

## E2 — Repeat Purchase Rate Declining — ALERT DEFERRED PHASE 2 / INFRASTRUCTURE LOCKED

**Status (reconciled 2026-05-31):** The E2 *alert* was DEFERRED to Phase 2 in
the E-series review (2026-05-23). Reasons: wrong metric definition (cohort
basis required, not trailing-90d rate); absent post-sale demand-pull-forward
suppression; six possible cause buckets, none diagnosable from Phase 1 data.
Both the narrow (concentrated VIP-drop) and weekly-summary versions were tested
and rejected. Phase 2 rebuild condition: 6+ months real outcome data + ability
to explain the *why*. See state_2026_05_23_e_series_v2.md.

**The E2 alert does NOT fire in Phase 1.** Critiques 2/3/4 and alert language
are NOT pending — they are cancelled with the deferral.

**However, the infrastructure below remains LOCKED and LIVE as a cross-alert
dependency** (see cross_alert_orchestration.md, E2 DEFERRED-DEP entry):
discount classification architecture, collection-launch detection/suppression,
and the new-customer-pct mart column are referenced by live alerts (D1 Layer-0
collection-launch echo; C6). These stay built. What follows is that
infrastructure, retained under a deferred alert — not a shippable Phase 1 alert.

**Historical note (superseded):** the firing condition + denominator
architecture below were locked before the deferral. They are preserved for the
Phase 2 rebuild and for the dependencies above, not as an active firing path.

**Firing condition (ALL required):**
- `repeat_purchase_rate_90d` drops ≥5 percentage points below trailing 28-day average
- `new_customer_pct_90d` surge ≤15% in same window (else → S33 fires instead)
- Minimum 50 repeat customers in 90-day window
- No `brand_event_calendar` event active
S33 check is mandatory pre-condition — runs before E2 every time.

**Discount Classification Architecture:**

Scope: 3+ lifetime order customers only. New customers never excluded.

Step 1 — Auto-derive Brand Event Calendar (Approach B):
- Qualifying day: daily_order_count > median(daily_order_count)
- Type 1: avg_discount_depth > p75 of qualifying days
- Type 2: avg_discount_depth p50–p75
- Type 3: BAU below p50
- Real-time: order volume > median AND discount crosses p50 → event day
- Monthly recalibration to prevent threshold creep

Step 2 — Welcome Code Exclusion:
- Onboarding confirmation → `client_config.welcome_discount_codes[]`
- Excluded from all discount calculations

Step 3 — Customer Classification (Approach A):
- `customer_discount_ratio = sum(discounts) / sum(subtotal)` excluding welcome codes
- `discount_motivated = ratio > mean + (1.5 × SD)` across all 3+ order customers

Denominator rule:
- Exclude discount_motivated customers (3+ orders)
- NEVER exclude new customers (1-2 orders)

Data sufficiency: <12 months → no exclusion, disclose in footnote

**Launch Detection and Suppression:**

Detection (ALL three in same 7-day window):
1. SKU spike: above mean(daily_sku_additions) + 2 SD
2. Spend spike: >40% vs prior 7-day average (any connected channel)
3. GA4 sessions: >30% vs prior 7-day average

Suppression duration:
- Known historical launches: actual measured recovery days
- New launches: mean recovery of similar impact score (±30% band)
- Fallback: vertical benchmark → 28 days default
Written to `client_config.collection_launch_suppression_days`

Sub-category classification: DROPPED. Impact score self-calibrates.
Unrecognised launch types: NO suppression — safer to fire than suppress silently.

**Vertical tag:** Single onboarding question → `client_config.vertical_tag`

**Pending for next session:**
- Critique 2: trajectory (gradual vs sudden)
- Critique 3: Gorgias cross-reference
- Critique 4: revenue impact weighting by segment LTV
- Alert language


---

## D-SERIES ALERT LANGUAGE SPEC
## Status: Gap review in progress — Gaps 1 and 2 locked 2026-05-26
## Updated: 2026-05-31 — Tier 0 added, D4 deferred to Phase 2
## Do not write final D1 alert language until all 9 gaps resolved

---

## D4 — FULFILMENT COST ANOMALY: DEFERRED TO PHASE 2

D4 is NOT active in beta. Agent D must not format any D4 alert.
Agent A must not activate D4 scan logic.

Reason: D4 requires per-order fulfilment cost from the brand's 3PL.
Shopify fulfillment API does not contain this — it contains only
customer-facing shipping charges or Shopify-label costs, not what
the brand paid its 3PL. No 3PL connector exists in beta. No supply
chain connector of any kind exists in beta.

D4 remains in the alert library for Phase 2 design. Prerequisite for
reactivation: 3PL connector strategy defined and at least one 3PL
connector built with per-order billing data accessible.

---

## D1 — CONTRIBUTION MARGIN COMPRESSION WITH CAUSAL DRIVER

### Status
Gap review in progress. 9 gaps identified.
Gap 1 (COGS tier disclosure) locked 2026-05-26. Updated 2026-05-31 — Tier 0 added.
Gap 2 (threshold definition — Trigger A and Trigger B) locked 2026-05-26.
Gaps 3–9 pending. Full alert language to be written after all gaps resolved.

### Urgency Tier
- **Trigger A (step change):** HIGH (🟠) — discrete unexplained drop vs structural baseline
- **Trigger B (slow bleed):** INFORMATIONAL (🟡) — trajectory signal, not acute crisis
- Exception: if primary driver is a checkout error or stockout already covered
  by F-series or G-series → D1 suppressed (covered by higher-priority alert)
- If Trigger A and Trigger B would both fire in the same week → Trigger A only

### Mandatory Pre-Conditions (Agent D — ALL must pass before formatting any D1)

**Pre-condition 1 — Sparse BAU check:**
1. Read client_config.sparse_bau_profile
2. If true → D1 does not fire. No message to founder. Internal log only.
3. If false → continue to pre-condition 2.

**Pre-condition 2 — Echo period check:**
1. Read brand_event_calendar.echo_period_active for current date
2. If true → D1 suppressed. Log to suppression_log. No founder message.
3. If false → continue to pre-condition 3.

**Pre-condition 3 — Structural break check:**
1. Read client_config.structural_break_detected
2. If true → D1 suppressed pending baseline recalibration.
   Log to suppression_log with reason = 'structural_break_in_progress'.
3. If false → continue to pre-condition 4.

**Pre-condition 4 — COGS tier check (Updated 2026-05-31 — five tiers):**
1. Read client_config.cogs_tier_active
2. If 'finaloop' or 'founder_csv' → FULL MARGIN ALERT template
3. If 'shopify_derived' → DRIVER-ONLY template
4. If 'founder_stated_per_order' → DRIVER-ONLY template WITH mandatory
   cost basis disclosure prepended:
   "Based on your stated $[client_config.founder_stated_cogs_per_order]
   all-in cost per order. Connect Finaloop or upload a cost file for
   SKU-level accuracy."
5. If 'founder_stated' or NULL → DRIVER-ONLY template, no cost figure shown
6. NEVER mix templates. One or the other. Never hybrid.

**Pre-condition 5 — Trigger identification:**
1. Determine which trigger fired: Trigger A (step change) or Trigger B (slow bleed)
2. Trigger A → HIGH urgency template
3. Trigger B → INFORMATIONAL urgency template
4. Log trigger_type to alert_log

### Trigger A — Firing Architecture (Locked Gap 2)

**What fires Trigger A:**
- Current 7-day CM (complete clean week: all 7 days, ≥1 Saturday, ≥1 Sunday)
- Falls below: p25(BAU CM) − adaptive_threshold
- Where: adaptive_threshold = MIN(MAX(bau_cm_daily_sd × 2.0, 3pp), 8pp)
- All exclusion flags clear
- Minimum 20 BAU days in structural baseline

**What is the baseline:**
- IQR band (p25–p75) of daily CM across verified BAU days
- BAU days: no event, no echo, no launch suppression, no influencer campaign active, no
  pre-sale ramp window (ADDED 2026-06-08, Gap 6 residual pass — see pre-sale handling held in
  the session state file; an unmarked pre-sale ramp carries elevated spend + soft conversion
  and would drag the BAU margin band DOWN, lowering the firing bar everywhere this baseline is
  read — Trigger A/B, structural break, seasonal bands). A one-time onboarding two-pass backfill
  must identify and exclude historical ramps before the first baseline is certified clean
  (pass 1: detect ramps on raw history; pass 2: rebuild the baseline excluding them).
- Trailing 90 days (not 180 — seasonal contamination risk)
- Recalculated weekly

**Echo period model (locked):**
- Opens: daily_return_count ≥ 1.5× structural_bau_return_rate
- Closes: rolling 7-day avg return < 1.3× BAU for 7 consecutive days
- Hysteresis prevents oscillation from secondary return waves
- Event-type caps: 21 days standard events, 45 days peak events (BFCM etc.)

**Structural break detection (locked; magnitude made brand-relative 2026-06-08):**
- 30-day rolling comparison of recent vs prior BAU p50
- If shift > break_magnitude AND both bounds moved same direction AND persisted ≥21 BAU days:
  structural_break_detected = true → baseline resets → founder notified retrospectively
- `break_magnitude` is brand-relative, NOT a flat 5pp: a multiple of the brand's own weekly
  CM volatility, floored so it cannot get absurdly small for ultra-steady brands (same pattern
  as Trigger B's magnitude_threshold). A flat 5pp was either noise for a volatile brand (false
  breaks that discard usable history) or too deaf for a steady one (real pivots missed). The
  ≥21-day persistence is UNCHANGED (confirming a PERMANENT shift should be slow and is measured
  on BAU days, so event duration is irrelevant); the 21-day duration is flagged to the O-26
  consistency audit for review, not changed here.

### Trigger B — Firing Architecture (Locked Gap 2)

**What fires Trigger B:**
- Mann-Kendall trend test on complete BAU weekly CM: significant downward trend (p < 0.10)
- Theil-Sen slope < −magnitude_threshold
- Where: magnitude_threshold = MIN(MAX(bau_weekly_cm_sd × 0.20, 0.2pp), 0.5pp)
- Minimum 8 complete same-season BAU weeks in bau_week_registry
- All suppression conditions clear

**What is a complete BAU week:**
- All 7 Monday–Sunday days pass all BAU exclusion filters
- No public holiday falls within the week
- Eliminates day-mix contamination — every qualifying week has same composition

**When Trigger B is disabled:**
- sparse_bau_profile = true (no meaningful BAU exists)
- Available history < 12 months (seasonal_profile = 'undetected')
- Internal log only: d1_trigger_b_disabled = true, trigger_b_disabled_reason

**Activation lag:**
- Event-heavy brands may take 3–6 months to accumulate 8 complete BAU weeks
- Acceptable — Trigger A handles point-in-time detection in interim
- Surface activation lag as insight in Profit Audit, not as product limitation

### Universal Baseline Alert (Tier 2/3 — all brands)
Locked from Gap 1. Final language pending Gap 8 (action) and Gap 9 ($ impact).
Current draft:
"Three cost signals are moving against you this week:
[Driver 1 with specific verifiable numbers], [Driver 2], [Driver 3].
Connect your cost data for exact margin impact."

### Full Margin Alert (Tier 1/1.5)
NOT YET WRITTEN. Pending Gaps 3–9 deliberation.
Path: Gap 3 (driver decomposition) → Gap 4 (causal chain) → Gap 5 (AOV) →
Gap 6 (seasonality) → Gap 7 (retire "entirely explained") → Gap 8 (action) →
Gap 9 ($ impact) → write final language.

### Nine Gaps — Status
| Gap | Description | Status |
|-----|-------------|--------|
| 1 | COGS tier disclosure | LOCKED ✓ |
| 2 | Threshold — Trigger A step change + Trigger B slow bleed | LOCKED ✓ |
| 3 | Causal decomposition must cover all drivers | PENDING |
| 4 | CPM → margin causal chain needs intermediate steps | PENDING |
| 5 | AOV decline missing from driver set | LOCKED ✓ 2026-06-01 — standalone AOV driver RETIRED; see "GAP 5 — AOV DECLINE: RETIRED AS A D1 DRIVER" |
| 6 | Seasonality suppression for Q4 CPM spikes | PENDING |
| 7 | "Entirely explained" framing must be retired | PENDING |
| 8 | No action named per driver | PENDING |
| 9 | No $ revenue impact | PENDING |

### Known Driver Set (Gap 5 LOCKED 2026-06-01)
- CPM rise (Meta/TikTok/Google) — high confidence
- Return rate increase (Shopify + Loop) — high confidence
- Discount depth increase (Shopify) — medium confidence
- Fulfilment cost increase — RETIRED 2026-06-08 (Gap 6 residual pass): feed-only, not estimated from carrier rates; re-enters only with a real cost-side feed (3PL/label), Horizon-2
- COGS increase (sku_cost_master) — low confidence (Tier 2/3 only)
- AOV decline — RETIRED as a standalone driver (Gap 5, 2026-06-01). D1 fires on
  CM *rate*; pure basket-size / list-price AOV decline does not move CM%. The
  margin-relevant slices of an AOV decline are already decomposed into the
  discount-depth and SKU-mix-shift drivers — a standalone AOV driver would
  double-count and corrupt the Pre-condition 6 residual gate. See "GAP 5 — AOV
  DECLINE: RETIRED AS A D1 DRIVER" below.

### What Was Retired (from original design)
- "Entirely explained by X" framing — mathematically imprecise, dangerous at beta
- Single driver named without decomposing full gap
- Margin % stated without COGS basis disclosure
- No action — diagnosis without prescription
- No $ weekly impact
- Fixed comparison windows (same 7 days, 4 weeks ago) — breaks in fashion DTC
- Fixed pp thresholds — not brand-adaptive
- Linear regression for slow bleed — non-linear data, unreliable at small N

---

## E-SERIES FINAL STATUS (from 2026-05-23 review)

| Alert | Phase 1 Status | Rationale |
|-------|---------------|-----------|
| E1 — List Health Degradation | ACTIVE ✓ | Diagnosable cause, specific action |
| E2 — Repeat Purchase Rate Declining | DEFERRED Phase 2 | Cannot diagnose cause; weekly summary also rejected |
| E3 — High-LTV Customers Going Quiet | DEFERRED Phase 2 | Same diagnosis problem; wrong action damages most valuable relationships |
| E4 — Post-Purchase Flow Conversion | DEFERRED Phase 2 | Attribution noise indistinguishable from signal |

All E2/E3/E4 architecture cancelled. See state_2026_05_23_e_series_v2.md.

---

## D1 GAP 3 — CAUSAL DECOMPOSITION
## Principles 1–4 Locked 2026-05-31

---

### PRE-CONDITIONS UPDATE — Additional checks added to Agent D D1 formatting

Pre-conditions 1–5 from Gaps 1 and 2 carry forward unchanged.
New additions from Gap 3:

**Pre-condition 6 — Residual gate check:**
1. Run all driver decomposition formulas
2. Calculate total_measured_impact vs total_cm_gap
3. residual_pct = (total_cm_gap − total_measured_impact) / total_cm_gap
4. residual_pct < 0.40 → fire D1 normally (continue)
5. residual_pct 0.40–0.70 → fire D1 with elevated disclosure,
   drop urgency one tier (HIGH → INFORMATIONAL, CRITICAL → HIGH)
6. residual_pct > 0.70 → DO NOT fire standard D1.
   Run blind spot diagnostic instead. Log internally.

**Measured-not-explained rule (ADDED 2026-06-08, Gap 6 residual pass).** A driver enters
`total_measured_impact` if and only if it is MEASURED — explained, partly explained, or
unexplained alike. Suppression (a benign event explains it) removes the driver from the
actionable ranking, NOT from `total_measured_impact`; its measured dollars stay in the sum,
so an explained gap yields a SMALL residual rather than a false blind-spot. Only feed-only
INVISIBILITY (no-feed COGS; fulfilment) keeps a driver out of the sum, where it correctly
becomes residual. Never a silent zero. "Explained" governs the alarm; "measured" governs the
sum — they are orthogonal.

**All-explained two-door fire condition (ADDED 2026-06-08, Gap 6 residual pass).** A low
residual is necessary but NOT sufficient to fire. Firing requires BOTH: (a) residual is
acceptable (explainability) AND (b) at least one driver is live — not State-3 suppressed
(actionability). A gap explained ENTIRELY by suppressed drivers has a near-zero residual but
no actionable driver: narrate the seasonal story (or route to the suppressed-leak digest), do
NOT fire. The residual gate measures explainability; actionability is the separate door.

**Pre-condition 7 — Layer 0 interaction check:**
Before listing drivers, check for interaction patterns:
1. Check three hardcoded patterns (below)
2. If no hardcoded match: check candidate_signals for approved
   interaction patterns for this client (pattern_type = 'interaction'
   AND practitioner_approved = true AND driver_combination matches
   current active drivers — exact array match, order-independent)
3. Match found → prepend Layer 0 to alert output
4. No match → proceed to Layer 1 directly

---

### PRINCIPLE 1 — Revenue-Side / Cost-Side Split

Internal decomposition logic only. Never surfaces as founder-facing label.
Determines calculation order and confidence tier assignment internally.

**Founder-facing output contains:**
- Drivers ranked by measured CM impact
- Live-vs-passed status per driver (current 24–48 hour read vs alert-week data)
- Reversibility indicator (locked in vs still actionable)

**Agent D requirement:**
Reads both alert-week window data AND current 24–48 hour data per driver
before formatting any D1 output.
- Driver normalised in last 24–48h → framing: "this passed — pattern to prevent recurrence"
- Driver still elevated → framing: act now

---

### PRINCIPLE 2 — Inline Disclosure Rules (replaces two-axis confidence table)

Three disclosure types only. Applied per driver at render time.

**Disclosure Type 1 — Data staleness (runtime check per driver):**

| Source | Acceptable staleness | Action if exceeded |
|--------|---------------------|--------------------|
| Sentry | 2 hours | Re-trigger sync before firing F2/F4 |
| Shopify | 6 hours | append "(data from [N] hours ago)" |
| Meta/TikTok | 24 hours | append "(data from [N] hours ago)" |
| Klaviyo | 6 hours | append "(data from [N] hours ago)" |
| GA4 | 48 hours | append "(data from [N] hours ago)" |
| Loop Returns | 24 hours | append "(data from [N] hours ago)" |
| Gorgias | 6 hours | append "(data from [N] hours ago)" |

Reads existing `any_source_stale` + `last_synced_at`. No new columns needed.

**Disclosure Type 2 — Estimation flag (static per driver type):**
- Fulfilment cost: estimation-flag RETIRED 2026-06-08 (Gap 6 residual pass) — the estimated fulfilment driver is removed (feed-only), so there is no estimated fulfilment figure to flag; reintroduce a disclosure only when a real cost-side feed (3PL/label) lands
- COGS Tier 2/3: handled by template split from Gap 1 — driver-only, no margin figure

**Disclosure Type 3 — Data completeness (per-client, runtime):**
- If Loop Returns connected AND return_reason field < 60% populated:
  append to return rate driver:
  "(return reason data incomplete — SKU-level breakdown unavailable)"

No causal confidence taxonomy. Causal confidence governed by
causal_pattern_validation tier only. No second framework.

---

### THREE-LAYER OUTPUT STRUCTURE — D1

#### Layer 0 — Interaction Check (fires first when triggered)

**Hardcoded Pattern 1 — Creative Fatigue:**
Condition: meta_cpm_change_pct > BAU AND ga4_cvr_change_pct < 0
           AND return_rate_pct > BAU return rate — all in same alert week
Output: "These three signals are moving together — this pattern typically
reflects paid creative fatiguing rather than three separate problems.
Check ad frequency and CTR decay before investigating each driver separately."

**Hardcoded Pattern 2 — Collection Launch Echo:**
Condition: return_rate_pct > BAU AND blended_discount_depth_pct > BAU
           AND brand_event_calendar has launch event within last 14–21 days
Output: "Return rate and discount depth are both elevated following your
recent [collection name] launch. Check whether launch-driven orders are
returning at higher rates before adjusting your discount strategy."

**Hardcoded Pattern 3 — Platform Cost Shock:**
Condition: CPM rising across ≥2 channels simultaneously
           (any of: Meta + TikTok, Meta + Google, TikTok + Google)
Output: "CPM is rising across [channels] simultaneously — more consistent
with a platform-wide cost event than a brand-specific creative problem.
Check industry CPM benchmarks before making campaign changes."

**AI-Discovered Interaction Patterns:**
- Stored in candidate_signals: pattern_type = 'interaction',
  driver_combination = text[] of mart column names
- Promotion: ≥5 historical instances at ≥70% hit rate
  → practitioner review (MANDATORY gate — not optional)
  → practitioner_approved = true → absorbs into live pattern library
- calendar_clustered = true patterns: flagged prominently at review,
  not blocked, but reviewed first
- Cross-network: same combination across ≥3 brands of same vertical_tag
  → hardcoded into global interaction library
- No match in any pattern → no Layer 0 fires. Safer than spurious warning.

#### Layer 1 — Driver List

**Ranking:** by measured CM impact ($ per week, Tier 1/1.5)
or measured delta magnitude only (Tier 2/3).

**Per-driver output format:**
```
[Driver name]: [measured delta] vs your normal range
Impact: $[CM impact per week]   ← Tier 1/1.5 only
Status: [Still active / Normalised as of [timestamp]]
[Inline disclosure if applicable — Principle 2]
```

**CM Impact Conversion Formulas (Tier 1/1.5 only):**

Isolation principle: each formula holds all other variables at BAU
to isolate that driver's contribution independently.

CPM driver:
```
effective_cpa_this_week = total_spend_this_week / shopify_orders_this_week
effective_cpa_bau       = same on BAU baseline
cm_impact = (effective_cpa_this_week − effective_cpa_bau) × orders_this_week
```
Footnote always: "CPA calculated on total orders — paid channel CPA impact may be higher"

Return rate driver:
```
cm_impact = (return_rate_this_week − return_rate_bau)
            × orders_this_week
            × avg_net_refund_value
```
avg_net_refund_value = AVG(actual refund amount) from Loop/Shopify refunds — NOT AOV
Return rate always appended: "Return rate spike reflects orders placed [N] days ago —
the underlying cause may have already changed."

Discount depth driver:
```
cm_impact = (discount_depth_this_week − discount_depth_bau)
            × gross_revenue_this_week
```

Fulfilment cost driver — RETIRED 2026-06-08 (Gap 6 residual pass).
The estimated `(fulfillment_cost_per_order_this_week − bau) × orders` driver is removed.
Fulfilment cost is feed-only (carrier/3PL invoice not connected in beta); estimating it from
carrier rates is the same confident-wrong error rejected for approximate auto-COGS, and a
feed-only cost that does not move computed margin cannot create a residual ("no residual to
detect, we do not claim it" — COGS principle). No fulfilment driver enters the decomposition
until a real cost-side feed (3PL invoice or Shopify-Shipping-Label) is connected; then it is
a measured driver, not an estimate. Free-ship economics remain revenue-side (Gap 5 lock),
never summed with carrier cost (O-20 double-count trap).

SKU mix shift driver (Tier 1/1.5 only — all conditions below must pass):
```
margin_weighted_revenue_this_week =
    SUM(orders × sku_price × sku_margin_pct) / SUM(orders × sku_price)
cm_impact = (margin_weighted_revenue_bau_pct − margin_weighted_revenue_this_week_pct)
            × gross_revenue_this_week
```

SKU mix shift pre-conditions (ALL must pass before surfacing):
1. sku_cost_coverage_by_revenue ≥ 0.85
   (SUM revenue for SKUs with unit_cost / total revenue this week)
2. Single largest revenue SKU this week has unit_cost populated
3. No active event in brand_event_calendar (including echo period)
4. No active promotion on shifted category
   (blended_discount_depth for that category not elevated vs BAU)
5. Revenue share shift > margin_mix_shift_threshold
   = MAX(bau_margin_weighted_revenue_sd × 1.5, 1.5pp floor) — NO CEILING
6. Seasonality typicality (Gap 6 — Dependency 1; supersedes the prior binary rule):
   Compute seasonal_typicality_state by event-anchored IQR percentile position in the
   brand's own prior same-season MARGIN band. Spend-reallocation disqualifier runs
   first; admissibility = post-structural-break AND cost-coverage ≥ 0.85; state ceiling
   by admissible-season count (0 → narrate, 1 → State-2 max, 2+ → full).
   State 3 → suppress (driver does not surface). State 2 / State 1 → surface; the
   State-2-vs-State-1 framing is handled downstream at the D1 alert-language pass.
   Retires the prior "± 1 SD / ≥ 12-month / suppress-if-within-range" rule.
7. founder_category populated (category_source not NULL)

Output at category level only — never at SKU level.
"Your [founder_category] drove [X]% of revenue this week
vs [Y]% normally. At their margin profile, this mix shift
cost approximately $[Z] this week."

SKU-level spend misallocation sub-finding (within CPM section):
When CPM is a named driver AND Tier 1/1.5:
- Check: blended_roas within 10% of BAU AND margin_weighted_roas >15% below BAU
- If both true → append to CPM section:
  "Your media spend shifted toward lower-margin SKUs this week.
   [Category/SKU] at [X]% margin received [Y]% of spend vs [Z]% normally.
   Forward to your media buyer: [specific reallocation brief]."
- Tier 2/3: spend concentration shift stated, no margin figures

#### Layer 2 — Residual Disclosure

Always present. Gap defined as: CM this week vs p25 of BAU baseline
(the threshold that fired Trigger A — gap is exactly what caused the alert).

| Residual | Framing |
|----------|---------|
| < 40% | "Measured drivers account for most of the compression." |
| 40–70% | "A portion of the compression comes from a driver we can't fully measure yet. [Specific connector named from connector_gap_map.] Urgency downgraded one tier." |
| > 70% | Standard D1 does not fire. Blind spot diagnostic runs instead. |

---

### BLIND SPOT DIAGNOSTIC

Runs when residual > 70%. D1 standard alert does not fire.
Five-step structured check. Target: < 10% of cases reach Step 5.

**Step 1 — COGS check:**
cogs_tier_active = Tier 2 or Tier 3:
→ "Most likely cause: a cost change in your product costs, landed costs,
   or supplier pricing — not visible in your connected data.
   Check purchase orders and supplier invoices for changes in the last 14 days.
   [connector_gap_map: recommended_connector]"
Tier 1 or 1.5: COGS is measured. Continue to Step 2.

**Step 2 — SKU mix check (Tier 1/1.5 only):**
Run margin_weighted_revenue formula even if below normal threshold.
Shift detected → surface as finding with direction only.
No shift / not applicable → continue to Step 3.

**Step 3 — Fulfilment cost check (REVISED 2026-06-08, Gap 6 residual pass):**
The estimated `> bau × 1.15` test is RETIRED — it relied on a carrier-rate estimate (rejected,
same as approximate auto-COGS) plus a hardcoded 1.15, and a feed-only cost that does not move
computed margin cannot create the residual being diagnosed. Mirror Step 1 instead:
→ ONLY for a brand with a trustworthy MARGIN feed that books fulfilment, name it as a
   DIRECTION, never a figure: "Part of this may be a cost we don't decompose per order —
   fulfilment or landed cost. [connector_gap_map: 3pl_invoice]". For all other brands, make
   NO fulfilment claim. No estimated number, no 1.15 threshold.
Not applicable → continue to Step 4.

**Step 4 — Data integrity check:**
Any source sync gap > acceptable threshold in alert week:
→ "Part of the gap may reflect a data sync issue rather than a real margin move."
   Log: potential_false_positive = true. No margin figure stated.
All sources clean → continue to Step 5.

**Step 5 — Genuine structural unknown (target < 10% of cases):**
→ "We can see your margin compressed this week but the driver isn't visible
   in your connected data. The most likely cause is a cost change in your
   supply chain or fulfilment not yet captured.
   Review your [recommended_connector from connector_gap_map] for changes this week."

---

### NEW SCHEMA — connector_gap_map

```sql
CREATE TABLE public.connector_gap_map (
    id                       bigint generated always as identity primary key,
    missing_driver           text not null,
    -- values: cogs / sku_mix / fulfillment_invoice /
    --         payment_processing / structural_unknown
    cogs_tier                text not null,
    -- values: tier1 / tier1_5 / tier2 / tier3 / any
    residual_band            text not null,
    -- values: high (40–70%) / very_high (>70%)
    likely_cause_description text not null,
    recommended_connector    text not null,
    action_brief             text not null,
    created_at               timestamptz default now()
);
```

Seed rows at launch:
| missing_driver | cogs_tier | residual_band | likely_cause_description | recommended_connector | action_brief |
|---|---|---|---|---|---|
| cogs | tier2 | very_high | Supplier or landed cost change not visible | finaloop | Check purchase orders and supplier invoices last 14 days |
| cogs | tier3 | very_high | Supplier or landed cost change not visible | founder_csv | Check purchase orders and supplier invoices last 14 days |
| sku_mix | tier2 | high | Revenue mix shifted toward lower-margin products | sku_cost_master | Upload a product cost CSV to identify which SKUs are driving compression |
| fulfillment_invoice | any | high | 3PL rate change or carrier surcharge not in Shopify | 3pl_invoice | Review your 3PL invoice this week for rate changes |

---

### NEW SCHEMA — candidate_signals additions

```sql
ALTER TABLE public.candidate_signals
    ADD COLUMN IF NOT EXISTS pattern_type        text default 'bivariate',
    -- values: bivariate / interaction
    ADD COLUMN IF NOT EXISTS driver_combination  text[];
    -- array of mart column names for interaction patterns
    -- example: ARRAY['meta_cpm_change_pct','ga4_cvr_change_pct','return_rate_pct']
```

---

### NEW SCHEMA — client_config additions (Gap 3)

```sql
ALTER TABLE public.client_config
    -- SKU mix shift driver
    ADD COLUMN IF NOT EXISTS margin_mix_shift_threshold          numeric,
    -- Formula: MAX(bau_margin_weighted_revenue_sd × 1.5, 1.5pp floor)
    -- NO CEILING. NULL until first baseline computation. Recalibrated monthly.
    ADD COLUMN IF NOT EXISTS bau_margin_weighted_revenue_sd      numeric,
    ADD COLUMN IF NOT EXISTS bau_category_revenue_share_sd       numeric,
    ADD COLUMN IF NOT EXISTS sku_cost_coverage_by_revenue        numeric,
    -- Revenue coverage rate: SUM(revenue for SKUs with unit_cost) / total revenue
    -- Recomputed weekly. Gates margin-weighted formula at 0.85 floor.

    -- CPM diagnostic tree
    ADD COLUMN IF NOT EXISTS creative_fatigue_frequency_multiplier  numeric default 1.20,
    ADD COLUMN IF NOT EXISTS creative_fatigue_ctr_floor             numeric default 0.90,
    ADD COLUMN IF NOT EXISTS cpm_noise_threshold                    numeric default 0.10;
    -- 10% CPM rise minimum to surface CPM as a driver
```

---

### NEW SCHEMA — sku_cost_master additions (Gap 3)

```sql
ALTER TABLE public.sku_cost_master
    ADD COLUMN IF NOT EXISTS founder_category               text,
    -- Founder-facing DISPLAY label ONLY — never the internal grouping key,
    --   never product_type.
    -- Display source: most-specific Shopify collection (fewest total SKUs this
    --   SKU belongs to) when collection coverage is adequate; otherwise defaults
    --   to the AI label.
    ADD COLUMN IF NOT EXISTS ai_inferred_category           text,
    -- AI category grouping (Claude API from title, tags, product_type, vendor,
    --   collection membership).
    -- INTERNAL GROUPING USES THIS AI CLUSTERING DIRECTLY, for every brand — no
    --   founder rename is required to group or to compute alerts. Founder rename
    --   is a DISPLAY GATE ONLY and never blocks internal grouping or alert
    --   computation.
    --   (Retires the prior "Mandatory founder rename before any alert uses this
    --   label".)
    ADD COLUMN IF NOT EXISTS category_inference_confidence  numeric,
    -- REDEFINED (Gap 6): a cross-signal AGREEMENT score — how strongly the
    --   independent signals (title, tags, product_type, vendor, collection
    --   membership) agree on the SKU's category. NOT a raw model self-report.
    --   Range 0.0–1.0; provisional threshold 0.70 (to be calibrated).
    ADD COLUMN IF NOT EXISTS category_source                text default 'collection';
    -- values: collection / ai_inferred / manual
    --   collection  = founder_category DISPLAY label from a Shopify collection
    --   ai_inferred = AI clustering (the internal grouping basis; also the
    --                 default display label when rename is skipped)
    --   manual      = founder relabelled in onboarding UI (DISPLAY only)
    -- product_type retired as a display label — retained only as an AI-inference
    --   input and as a low-agreement INTERNAL-grouping fallback.
```

---

### NEW ONBOARDING SCRIPT — connectors/category_inference.py

Runs at onboarding Step 6, after historical_pattern_scan.py. Silent completion —
internal grouping is automatic. The only founder-facing touch is an OPTIONAL,
non-blocking display-label rename prompt.

Logic:
1. Query collection membership for all active SKUs.
2. Run AI clustering (Claude API: title, tags, product_type, vendor, collection
   membership) → ai_inferred_category per SKU. INTERNAL GROUPING USES THESE AI
   CLUSTERS DIRECTLY for every brand, regardless of collection coverage.
   Collection-first internal grouping is OVERRIDDEN: collections in this segment
   are frequently promotional ("Bestsellers", "Sale", "New Arrivals") and are
   unsafe as grouping keys. Collection feeds the DISPLAY label only.
3. Assign the DISPLAY label founder_category:
   → collection coverage ≥ 0.70 → founder_category = most-specific collection
     (fewest total SKUs); category_source = 'collection'
   → otherwise → founder_category defaults to the ai_inferred_category label;
     category_source = 'ai_inferred'
   (Display choice only — internal grouping remains the AI clusters either way.)
4. OPTIONAL display-rename prompt in the onboarding checklist:
   "We've grouped your products into categories —
    do these names match how you think about your business?
    Rename any that don't." (display-only, non-blocking)
   Founder-renamed labels refine the DISPLAY label only; category_source = 'manual'.
5. Founder skips/declines the optional rename:
   → keep the AI labels for display; category_source stays 'ai_inferred'
   → internal grouping AND category-level D1 output PROCEED — rename is never a
     blocker
   (Retires the prior "Founder declines rename step → category_source = 'manual'
    (pending) → category-level D1 output suppressed for this client".)
6. Cross-signal agreement < 0.70 for a SKU → fall back to product_type for
   INTERNAL grouping of that SKU only — NEVER displayed as a founder-facing label.
7. Per-brand output granularity is set by the CLUSTERING-QUALITY GATE (return-rate
   coherence; go-live gate D1-G3 in d1_validation_gates.md): category-granular D1,
   or brand-level-with-disclosure (the explicit low-quality path — never a silent
   coarse fallback).

New SKUs after onboarding: inherit the display label from collection if available,
else NULL until a manual re-trigger.

---

### HISTORICAL_PATTERN_SCAN.PY — Multivariate Sweep Extension

New capability added alongside existing bivariate sweep.
SEPARATE code path — do not merge with bivariate sweep.

What it does at onboarding:
1. Identify all weeks where ≥2 drivers moved in same direction
   simultaneously (each driver > 1.5× its BAU SD)
2. Test whether known outcome (D1 trigger, ROAS drop >15%,
   return spike >2× BAU) followed within 7 days
3. Count instances, compute hit rate
4. ≥5 instances at ≥70% hit rate:
   → Write to candidate_signals:
     pattern_type = 'interaction'
     driver_combination = [array of mart column names]
     source = 'historical_scan'
     promotion_status = 'candidate'
   → Route to practitioner review queue

Practitioner review gate: MANDATORY.
No AI-discovered interaction pattern absorbs into live pattern library
without practitioner_approved = true.
calendar_clustered = true: flagged prominently, not blocked.

---

### GAP 4 — D1 CPM DIAGNOSIS CHAIN (S44 / S35 CONSUMER MODEL) — DESIGN-COMPLETE

Status: DESIGN-COMPLETE, blocked on one schema change (see ship-blocker below).
Closes Gap 4 by folding in Sub-Decisions 1, 1a, 2 (previously held only in the
state file) and reconciling them against the pre-existing suppression
architecture (O-14). The chain does NOT invent seasonal logic; it CONSUMES the
S-series. Go-live gate: `d1_validation_gates.md`.

**Design intent (plain statement):** the CPM→margin chain runs in five steps —
alert-level gate → funnel attribution → seasonal read → cross-channel check →
account-specific handoff. Only the seasonal step changed under O-14: D1 stops
running its own seasonal check and reads the verdict the S-series already
produces, per component. This guarantees D1 and the B-series can never disagree
on whether a CPM move is seasonally explained.

**Step 0 — Alert-level gate (consume S35 + H-series; runs before decomposition):**
- H1 fires (data unreliable) → D1 does not run at all.
- DQ / S9 → State 4; per S42 this overrides all other suppressions.
- F2 fires (payment-gateway failure) → CONFLICT, unresolved in canon:
  S35 literal text suppresses all of D1; S44's component logic implies F2 should
  suppress only D1's conversion-side component, leaving CPM and return-rate free.
  The F2 case is not worked in the S44 example. **Routed to O-5 (orchestration
  pass). Gap 4 closes WITH this as a documented dependency — Step 0's F2 branch
  is not finalised here.**

**Step 1 — Funnel attribution = the S44 decomposition itself:**
- Decompose the effective-CPA rise two ways: acquisition-cost-side (CPM delta)
  vs conversion-side (GA4 CVR delta). This is Sub-Decision 2 (LOCKED) and is
  literally S44's "decompose D1 into components before suppression" for the
  acquisition leg. CTR is out of scope (routed to B1/B4 — Sub-Decision 1).

**Step 2 — Seasonal = READ the CPM-component suppression_state (O-14 fix):**
- D1 does NOT compute a seasonal-norm gate. It reads `suppression_state` for the
  CPM component, produced by the S44 → S38 → S41 pipeline (S1/S2/S5/S10 are the
  seasonal rules that can suppress the CPM component):
  - State 3 (S38 >85% explained-away) → narrate seasonal-explained; do NOT rank
    CPM as an actionable margin driver. D1 may STILL fire on another component
    (the S44 BFCM + AZ-KNIT-031 worked example: CPM suppressed, return-rate fires).
  - State 2 (S38 60–85%) → fire CPM with seasonal context + residual; this is the
    escalation-eligible state.
  - State 1 (S38 <60%) → rank CPM as a driver normally.
- **Universal go-quiet ceiling (ADDED 2026-06-08, Gap 6 residual pass).** The S38
  explained-away % may NEVER produce silence (State 3) on its own. Every component's go-quiet
  state is CAPPED by the brand-relative admissibility ceiling defined for seasonal typicality
  (0 admissible prior same-seasons → narrate only; 1 → State-2 max, never suppress; 2+ →
  State 3 available). The explained-away % becomes CONTEXT shown to the founder (and still
  feeds S42 stacking / S39 learning) — it is no longer the silence switch. This applies to ALL
  components (CPM here, return-rate Stage 2, mix-shift), removing the inconsistency where only
  mix-shift carried the ceiling. Silence requires comparable brand history, not a guessed
  cut-off; the 85%/60% cut-offs stay placeholders pending calibration and, capped this way,
  can no longer cause silence alone. (Stacking precedence on this ceiling → orchestration pass.)
- **Escalation = S41 state decay while the signal persists**, NOT a bespoke
  "sustained" timer. Per S42, a D1 escalation is subordinate to any active
  suppression stack and triggers only once the stacked state decays to ≤ State 2
  (proposed resolution of O-18 — ratify at orchestration pass).
- **Sub-Decision 1a clarification (NOT a reopening):** the "sustained normal"
  concept splits into two distinct jobs — (a) seasonal-explanation fade = S41
  decay (now consumed, not owned by D1); (b) instance identity (same instance
  persisting vs cleared-then-rose) = the brand-volatility (CPM baseline SD)
  threshold, which remains D1-internal and unchanged. 1a survives intact, now
  scoped only to (b).
- **Render-time read:** D1 reads `suppression_state` AS OF the alert week, never
  a cached value (staleness risk — see FP4 / S48). Same discipline already locked
  for reading F2 state at render time (Cluster 3).
- **"Explained ≠ can't act" anchor (forward to Gap 8):** a State-3 (seasonal) CPM
  component does NOT suppress the already-locked SKU-level spend-misallocation
  sub-finding (this spec, "SKU-level spend misallocation sub-finding"). Seasonal
  CPM can still carry an action ("you're overspending into inflated CPMs").
  Full resolution of the seasonal-but-actionable tension is deferred to Gap 8;
  logged here so it is not lost.

**Step 3 — Cross-channel platform cost shock (D1-internal — no S-rule covers it):**
- Layer 0 Pattern 3 (CPM rising across ≥2 channels = platform-wide event, not a
  brand-specific creative problem). No existing S-rule covers data-derived
  multi-channel co-movement (S1/S2/S5/S10 are calendar-driven; S12 = iOS ATT;
  S4 = TikTok-specific). Keep as a D1 mechanism.
- Verify consistency against the A4 co-movement matrix (O-17, orchestration pass).
- Candidate for promotion to an S-rule at the orchestration pass — low priority,
  logged not built.

**Step 4 — Account-specific handoff = consume S35 (+ proposed D1↔B1/B4 addition):**
- D1 references B1/B4 leading-signal trajectory and hands the funnel packet to
  the media buyer; it never manufactures a creative-fatigue/saturation verdict
  (Sub-Decision 1, LOCKED). This consumes the S35 dependency graph plus the
  proposed D1↔B1/B4 addition (O-13), ratified into S35 at the orchestration pass.

**S38 thresholds are placeholders.** The 85% / 60% explained-away cut-offs that
drive State 3/2/1 are unvalidated for a $2M–$10M fashion brand's seasonal CPM
behaviour. Treat as placeholders pending outcome calibration on real client data;
do not hardcode as final. (Analytical reasoning — customer discovery may surface
that real BFCM spikes cluster at a different number.)

**SHIP-BLOCKER (schema) — do NOT build now; enforced by test:**
`suppression_log` (technical_architecture.md) keys suppression by `alert_type`
only — there is NO component column. S44 (locked decision) requires per-component
suppression for D1. As built today the table cannot record "CPM component →
State 3, return-rate component → State 1" — so S44 is aspirational for D1 until a
component discriminator is added (`alert_component text`, or multi-row per
evaluation). This is a Claude Code schema change that stays BATCHED (post-H, no
code now). It is promoted to a D1 go-live GATE — enforced by the BFCM +
AZ-KNIT-031 acceptance test in `d1_validation_gates.md`, which fails by
construction if the component field is absent. A failing test, not a priority
label, is the mechanism that prevents D1 shipping without it.

**Gap 4 closes the alert's INTERNAL steps only.** External coordination (B-series
canonical-surface ownership, A2 three-way overlap, C-chain return-driver router)
remains open and is owned by the orchestration pass. The Gap 4 close does not
imply external coordination is settled.

---

### GAP 5 — AOV DECLINE: RETIRED AS A D1 DRIVER (LOCKED 2026-06-01)

Status: LOCKED. Closes Gap 5. No new mart column, no new S-component, no Phase-1
build. Three live outcomes (driver retired; Gaps 7/9 forward note; shipping
deferral) plus one routing (category shift → Gap 8).

**Core decision — retire standalone "AOV decline."**
D1 fires on contribution-margin *rate* (CM%, the pp-based Trigger A/B thresholds
in Gap 2), not margin dollars. A pure basket-size decline (fewer units, same
product, same margin %) or a pure list-price cut does NOT move CM% and is out of
scope by definition — that is a revenue/volume story, not margin compression.
Decompose any AOV decline and its margin-relevant slices are:
- discount / price effect → already the **discount-depth driver** (S19 component)
- mix effect (orders shifting to cheaper SKUs) → already the **SKU-mix-shift
  driver** (margin-weighted)
- basket-size effect and pure list-price effect → do not move CM%; not drivers.
Adding a standalone AOV driver would double-count discount + mix into
`total_measured_impact` and corrupt the Pre-condition 6 residual gate (residual
shrinks artificially → D1 fires at inflated coverage/urgency). Retired for that
reason, documented here so it is not re-raised.

**S-series reconciliation (done the Gap 4 way).**
S44 decomposes D1 into exactly five components — CPM, return-rate, COGS,
discount-depth, operational-cost. There is NO AOV component and NO S-rule
(S1–S50) touches AOV. AOV is confirmed NOT a suppressible D1 component. S44 stays
at five components; nothing added.

**Forward note to Gap 7 / Gap 9 (display logic).**
Founders watch AOV. When AOV moves materially but CM% holds, the alert must
proactively acknowledge it rather than appear blind — e.g. "AOV fell [X]% this
week, but your margin rate held — this is a volume/mix story, not margin
compression." This is a Gap 7 (retire "entirely explained" framing) and Gap 9
(display) concern, not a Gap 5 driver. Logged for resolution in 7/9; not designed
here. Does not gate the Gap 5 close.

**Shipping / free-ship economics — DEFERRED to the 3PL integration.**
Two corrections made during Gap 5 and recorded so they are not re-litigated:
(1) shipping subsidy is revenue-*forgone* (revenue side), NOT a cost — it does
not fold into the operational-cost component; (2) the gradual "AOV drifts toward
the free-ship threshold" mechanism is third-order. External data (2026 carrier
GRIs ~5.9% headline / 10–20% effective; ~67% of retailers resetting thresholds;
~10% per-order absorption at $75 AOV / $8 carrier cost) confirms the real
step-change driver is **carrier cost on the cost side**, which PS cannot see
until 3PL / Shopify-Shipping-Label data is connected, while threshold changes are
founder-known and low alert value. Logged as a future **cost-side
carrier-cost-change detector** (a fulfilment-driver enrichment, NOT an AOV driver,
NOT a revenue-side fold). No Phase-1 build, no behavioural threshold inference, no
cohort-capture groundwork. **3PL double-count trap (carry forward):** when real
carrier cost lands, the `shipping_lines.discount_allocations` revenue-side proxy
is DROPPED, never summed with carrier cost — they measure the same free-ship event
from opposite sides of the margin identity. (Mirrored as O-20 in
cross_alert_orchestration.md.)

**Founder-driven category (ASP) shift — ROUTED to Gap 8, not closed here.**
The margin-weighted mix-shift driver already correctly stays silent on a
margin-*neutral* ASP shift (lower average selling price at equal/higher margin
rate — common in fashion, where basics/accessories out-margin premium outerwear).
The case that genuinely compresses CM% is a founder-*intended* shift to a
lower-margin category — that is the "explained ≠ can't act" open decision
(product_strategy Section 12), owned by Gap 8. Deciding it inside Gap 5 would be
premature closure. Gap 8 inherits three concrete items (mirrored as O-19 in
cross_alert_orchestration.md):
- **Finding A — suppression hole:** the mix-shift pre-conditions check
  *promotion*-driven shifts (pre-condition 4) but NOT *paid-spend-reallocation*-
  driven shifts — the most common way a founder drives a category shift. Worse,
  the existing SKU-level spend-misallocation sub-finding would currently
  false-fire on an intentional push ("your spend shifted toward lower-margin
  SKUs").
- **Finding B — the discriminator Gap 8 needs:** spend-by-category co-moving with
  revenue-by-category in the same direction is the signal that separates
  "founder drove this" from "this happened to us."
- **Materiality floor:** Gap 8 must set a floor below which the intentional-shift
  trade is not surfaced at all.

**Claude Code impact:** effectively nil from Gap 5. Earlier shipping-schema
verification items drop with the deferral and move into the future 3PL workstream.
No batched change originates here.

---

### GAP 6 — SEASONALITY SUPPRESSION (WIP — 2 dependencies CLOSED; return-rate Seam 2 + C3 check + COGS/S21 CLOSED; discount-depth/S19 PARTIAL; opex OPEN)

Status: WIP. The two named dependencies (SKU mix-shift, organic-viral) are RESOLVED.
The return-rate component of the O-14 reconciliation: Seam 2 (S17/S18 vs C3) and the
C3 consistency check are now RESOLVED (2026-06-03, see below). COGS/S21 is now RESOLVED
(2026-06-03, see below). discount-depth/S19 is PARTIAL (2026-06-04, see below) — its
self-contained calls are settled; its interaction-dependent calls are deferred to the
final residual pass. Still PARTIAL overall because operational-cost/S20 is untouched and
must NOT be assumed clean, and two S19 items are owed the residual pass. A final
cross-component residual-disclosure consistency pass is owed before Gap 6 closes.

**Phase-1 No-Seed Principle (governs this whole section).** A threshold may not be
a guessed constant used to *suppress*. It is either derived from the brand's own
admissible history, or — where there is no history and no cross-client benchmark
(Phase 1) — the system NARRATES and does not suppress. Seed-blending returns only in
Phase 2 when the Fashion Intelligence Network supplies a real benchmark. Concretely
for the return-rate component: S15 expected-rate thresholds stay dormant in Phase 1
(no trustworthy seed pre-benchmark); S16 tiers are brand-own-data; S3 dates are
event-derived, never hardcoded.

---

#### Dependency 1 — SKU mix-shift seasonal suppression — RESOLVED

Grade the mix-shift driver on its **margin impact** (CM%), NOT the category-share
shift, and grade it by **IQR percentile position inside the brand's own prior
same-season margin band**. NO z-score / NO ±SD: a brand observes a given season
~once per year, so small-n is the permanent regime (not a cold-start phase to grow
out of), and category share is the wrong quantity — D1 cares about CM%.

- **State carried in a separate `seasonal_typicality_state` field**, mapped to the
  same State 3/2/1 labels and decayed by S41. MUST NOT be written into
  `variance_explained_pct` (that field means seasonal *attribution*; typicality is a
  different quantity — overloading it corrupts S42 stacking and S39 learning).
- **Spend-reallocation disqualifier runs BEFORE the seasonal grade.** A shift that
  co-moves with a deliberate spend reallocation is not eligible for seasonal
  suppression at all. (A piece of Gap 8 Finding B pulled forward; the boundary —
  keep in Gap 6 or return it wholly to Gap 8 — is still the founder's call, logged
  unresolved.)
- **Admissibility — a prior season counts only if BOTH:** (a) no structural break
  separates it from now (reuse the locked structural-break rule; a pivot/category
  addition discards pre-break seasons), AND (b) cost coverage ≥ 0.85 for those weeks.
- **State ceiling by admissible-season count:** 0 → no band → narrate/disclose
  fallback; 1 → fragile band → State-2 ceiling (fire-with-context, NEVER suppress);
  2+ → full band → State 3 available. Suppression (State 3) is the HIGHEST-confidence
  claim, not the lowest — a fragile band removes the right to suppress.
- **Event-anchored band, NOT calendar-anchored.** "Prior-year same season" = the
  same N weeks relative to the prior-year launch in `brand_event_calendar` (match
  S2/S46), so the CPM and mix-shift seasonal lenses can never point at different weeks
  for the same launch (O-14 guarantee).
- **Per-event prior-year coverage**, not per-account history: a NEW drop type has no
  analog even for a 2-year-old brand → fallback for that event.
- One calibrated **sensitivity multiplier** at the State-2↔State-1 edge — provisional
  placeholder, outcome-calibrated, guardrailed (Gap 2 pattern). NOT a 6th S44
  component (Gap 5 locked S44 at five).

(Retires the prior "≥12 months history / suppress within ±1 SD / adaptive threshold
below 12 months" rule entirely.)

---

#### Dependency 2 — Organic-viral detection — RESOLVED (D1-scoped part; rewrite routed to O-11)

**Reframe: NOT blanket suppression.** Blanket suppression is wrong because the
concurrent discount-depth compression (new-customer welcome codes) is the one
actionable lever, and suppression would hide it. D1-scoped behaviour is: (a) exclude
the surge days from the BAU baseline, plus (b) a concurrent discount-depth read
surfaced WITH viral context, gated by the O-19 materiality + actionability floor.

- **Detect via S33's brand-level new-customer-pct surge signal (>15% surge), NOT a
  single-SKU `+2SD` revenue test.** Virality is multi-product / brand-level; the seed
  scenarios are themselves brand-level (800 / 1,200 new customers).
- **Founder confirmation is the organic-vs-engineered discriminator** (a no-spend
  signal can misread an engineered push). If unconfirmed, default to
  provisionally-locked-and-tracking — confirmation is not a blocking dead-end.
- **DROPPED:** forward 30/60/90 repeat tracking in D1 (no actionability for a one-off,
  non-repeatable event); any viral-specific returns model (returns flow through the
  normal return-rate component); overlap handling (an artifact of the abandoned echo
  model). Repeat maturation stays entirely with S33/E2.
- **S33's 20% viral-cohort repeat-rate cutoff is HARDCODED → make brand-relative**
  (below the brand's own new-customer-cohort repeat-rate band). Logged against S33 for
  the orchestration pass.
- **Routed to O-11 (shared launch-detector rewrite — NOT a Gap 6 edit; batched to
  causal_graph.py):** separate `organic_viral` from `collection_launch` (different
  metrics — new-SKU *count* vs single-SKU *revenue*; different recovery clocks); fix
  the spec self-contradiction; C6 is corrupted by the conflation (it watches a viral
  existing SKU as a new collection); E2 is double-suppressed (launch logic + S33).
  Neither C6 nor E2 relies on viral being actively suppressed (verified). Detector is
  shared D1/C6/E2.

(Retires the prior "spend optional → single-SKU +2SD → collection_launch_suppression_active
= true → D1 suppressed for return_window_days" rule entirely.)

---

#### Return-rate component (O-14) — TWO-STAGE CONSUMPTION (PARTIAL)

Unlike CPM's one-stage consumption, the return-rate component is consumed in two
stages:

- **Stage 1 — expected return rate by category mix = S15's real job.** S15 is a
  BASELINE-SETTER (a *level*), not a suppression state-producer (a *delta*). A new
  high-return category (e.g. formalwear ~38%) raises the resting expectation
  permanently; treating S15 as a decaying suppressor would either fire forever or
  blanket-mute a category and miss a real defect inside it.
- **Stage 2 — grade the RESIDUAL** (actual − expected) via S3/S16 → S38 → S41. D1
  reads only the Stage-2 verdict. The Stage-2 go-quiet state is subject to the universal
  admissibility ceiling (ADDED 2026-06-08): the S38 % cannot suppress without 2+ admissible
  comparable seasons — same rule as the CPM component.

**S15 reclassified** from "suppression rule" to "baseline rule" in how D1 uses it.
This diverges from S44's literal listing of S15 in the return bucket; resolved on the
D1 side now, and LOGGED for the orchestration pass (S-series semantics) — see
cross_alert_orchestration.md.

**S3 re-anchored** (post-holiday rule): retire the hardcoded Jan 1–21 / Jan 22 cliff.
Derive the brand's actual holiday SELLING window from its own revenue concentration +
`brand_event_calendar`, width-matched, then push it forward by the brand's
`return_window_days` — that is the expected return-spike window. State 3 across it;
**S41 owns the decay** (no date cliff). A first holiday with no prior year →
narrate/disclose (per-event coverage gate).

**Phase-1 No-Seed application (return-rate):** S15 expected-rate thresholds dormant in
Phase 1; S16 tiers brand-own; S3 dates event-derived.

**Component isolation already PROVEN:** the S44 Nov-2024 BFCM-plus-defective-units
worked example shows CPM suppressed (seasonal) while return-rate FIRES (defect, not
seasonal) — the core consumer pattern is sound for this bucket.

#### Seam 2 — S17/S18 (size-guide / photography) vs C3 — RESOLVED (2026-06-03)

**The seam is real, not absorbed by the two-stage model.** A size-guide change does
not move the category mix, so Stage 1 (S15 expected level) is unchanged and the whole
size-guide-driven return movement lands as positive residual. Stage 2 grades that
residual via S3 (post-holiday) / S16 (influencer window) — neither matches a
`size_guide_update` / `photography_update` event — so D1 grades it UNEXPLAINED and
surfaces it, while C3 has suppressed the same movement (S17 State 3). Confirmed
contradiction. It bites in the broad-update case (a line-wide size-guide overhaul),
where the movement aggregates to category CM%; a single-SKU transient stays under the
O-19 materiality floor and D1 stays quiet on its own.

**Resolution — route through the event-calendar layer, do NOT hand-duplicate S17/S18
inside D1.** The `brand_event_calendar` row is the single source of truth for an
event's suppression: it carries `suppress_alerts` (State 3), `context_alerts`
(State 2), `residual_threshold_pct` ("only fire if the signal exceeds the explanation
by this %"), and a decay window. S17/S18 are the human-readable encoding of
`size_guide_update` / `photography_update` rows. So D1's return component, when grading
its Stage-2 residual, MUST consult active rows of those event types and apply that
row's `residual_threshold_pct` + decay — the same consumer treatment it already gives
S3/S15/S16. This makes "add S17/S18 to the D1 return bucket" correct in EFFECT but
implemented where there is one source of truth (no duplicate-logic drift), and it
inherits the S17-State-3 / S18-State-2 asymmetry for free via suppress vs context. The
S44 component-isolation guarantee is preserved: `residual_threshold_pct` is the residual
gate, so a concurrent defect on the same SKUs still fires past the size-guide
explanation. No blanket mute.

**Default posture = narrate-don't-suppress, because the change-event source is
unreliable (verified against Shopify's current API surface, 2026-06-03):**
- No uniform source exists. A size guide stored as a **metaobject** (Shopify's standard
  for size charts) DOES emit a reliable update webhook, filterable by type, with an
  updated-at timestamp — and metaobjects can reference specific products, giving
  affected scope in the best case. A size guide stored as an **Online Store Page** emits
  NO create/update webhook (detectable only by polling + diff). A size guide baked into
  **theme code / an app** is effectively undetectable.
- A webhook proves an EDIT, not a MEANINGFUL change (a typo fires the same event as a
  re-measurement). So an edit is a lead, never a verdict.

**Tier-1 auto-detect path (BUILD — degrades gracefully, no discovery dependency):**
1. Silent onboarding probe → if a size-chart metaobject exists, subscribe to its update
   notifications. No founder touch. If not (Page/theme/app) → fall back to
   narrate-on-return-movement, no auto-detect.
2. On an edit, content-diff the size/measurement values → a meaningfulness magnitude
   (typo ≈ 0; re-measurement high). This REPLACES per-edit founder pinging. Cutoff is a
   provisional placeholder, outcome-calibrated — not hardcoded.
3. Writes a quiet, low-confidence "recent size-chart change" context note — invisible by
   default. Surfaces ONLY if a return-driven margin movement would otherwise fire a D1
   driver within the brand's return window. No movement → founder never hears of it.
4. Window = the brand's `return_window_days`, NOT a fixed 14/21 days; the note decays
   over that window (S41).
5. NEVER silent-suppress: a return spike beyond what a size change explains still fires.
   Photography: product-image swaps are diff-detectable via the standard product-update
   payload; theme lookbook/section swaps are not — same narrate fallback.

**Affected-scope gap (honest):** `brand_event_calendar` has no affected-line/category
column today, so a size-guide event is brand-wide → D1 would go quiet brand-wide for the
window (over-suppression on unaffected lines). Phase-1 behaviour = brand-wide WITH
DISCLOSURE (narrate the window), NEVER silent brand-wide mute. Clean fix = add an
`affected_category[]` column (BATCHED schema change; see technical_architecture.md +
pre_agent_build_checklist.md).

#### Action structure for the return driver — anchored on the return REASON

The headline is ALWAYS the return signal + the action; a recent size/photo change is
only a **timing modifier** that can DOWNGRADE urgency, never replace the action.
- Action is anchored on the dominant **return reason** (Loop reason codes / Gorgias
  text): *sizing-fit* → fit-guidance / "runs small" flag / next-run pattern grading;
  *quality / defect* → time-critical: supplier credit claim while the window is open,
  QA the batch, consider pulling the SKU + pausing spend feeding it; *not as pictured* →
  photography / description fix; *one channel over-returning* → reallocate spend off that
  source. This action exists whether or not anything was changed.
- A recent size/photo change, when the reason is sizing-coded AND modest, downgrades to
  a **deferred action with a hard expiry**: "may be customers reacting to clearer
  sizing — watch through [return-window end]; if it keeps climbing, treat it as the
  lever above." If the founder says **no change** → the softener is stripped, urgency
  stays, the ranked action fires now. Nothing was hidden, so nothing is lost.
- Anchoring on REASON (not on the founder's memory of edits) makes this robust to a
  wrong "no" and to undetectable theme-coded edits.
- If neither Loop nor Gorgias is connected → say so ("reason data not connected, can't
  rank the fix"); never invent a reason.

**Softener FORBIDDEN when the reason is quality/defect OR the magnitude is extreme**
(the defect-can't-be-masked rule). "Extreme" is the OR of three brand-relative tests —
any one defeats the softener:
1. **Level** — the return residual sits in the far upper tail of the GROUP's own
   historical band (same own-band method as the mix-shift seasonal grade; at the finest
   granularity the clustering-quality gate certifies for this brand; NOT the blended
   brand average, NOT a fixed pp / fixed ×).
2. **Exposure** — units (or margin $) at risk cross the upper end of the brand's
   materiality band (deferring a high-volume problem is what costs money).
3. **Trajectory** — still climbing through the return window instead of cresting (a real
   size-guide reaction settles; a sustained climb contradicts the story at any level).

Thin GROUP history (can't form a level band) → fall back to the **exposure** test, and
withhold the level judgment. Withhold-when-unsure (lean to action — the safe direction).
"Vertical" / cross-brand benchmarks are explicitly OUT of scope here (Phase-2 network
layer; never pool across verticals); the extreme test is strictly brand-own-data. All
three are provisional placeholders, outcome-calibrated.

#### C3 consistency check — RESOLVED into a finding (2026-06-03)

The return alert (C3) is specified TWO contradictory ways:
- **Headline (product_strategy.md):** "SKU return rate > 2× brand average, sustained
  7+ days" — blended brand average + fixed 2× multiplier. This is exactly the
  brand-level, hardcoded yardstick rejected for D1. As written it DIVERGES.
- **Seeded scenarios (gap_abc_decisions.md):** require the opposite — formalwear 32% vs
  22% blend is "structural to the sub-category, not anomalous"; menswear 15% vs 28%
  blend "must not misread", 90-day hold, "insufficient history"; weekend +6pp is
  "structural — must not trigger." This is group-aware baseline + thin-history withhold,
  which ALIGNS with D1's method in intent — but it was never written into C3's stated
  method, and the category-baseline rule (S15) is wired ONLY to D1 today (C3's stated
  method does not reference it).
- **Thin-history fallback differs even where they align in spirit:** D1 → exposure test
  (can still act); C3 (per seed) → 90-day monitor-and-wait (waits). A real design fork.

**Resolution: PROVISIONAL LOCK of D1's extreme yardstick + action structure**, tagged
with two reconciliation items for the C-series (return-alert) review (logged in
cross_alert_orchestration.md): (a) retire C3's "blended average + fixed 2×" headline and
wire C3 to the same per-category baseline D1 uses, so the two alerts share one
computation; (b) decide the shared thin-history fallback (exposure vs monitor-and-wait).
The "C3 consistency check" open item closes into this same note — answer: no as written,
yes in intent. Provisional because it also inherits the O-19 materiality floor (Gap 8),
still open.

**Schema follow-ups (BATCHED, not built now):** `size_guide_update` is MISSING from the
`brand_event_calendar` event_type list — add it; add `affected_category[]`; write both
brand-action types as CONTEXT (narrate), never silent SUPPRESS. Detection code (probe,
metaobject webhook subscription, content-diff) → pending Claude Code action, post-H.

#### COGS / S21 (supplier cost increase) component — RESOLVED (2026-06-03)

The supplier-cost rule (S21) eases the margin alert during a "supplier raised costs"
window. Reviewing it surfaced two seams and an honesty gap — it is NOT D1-vs-another-
alert (no other alert consumes cost), it is D1-vs-reality and D1-vs-the-cost-tiers.

**1. Retire the fixed 60-day window → per-product sell-through.** Old stock does not
clear on a calendar; it clears at each SKU's own velocity. A fixed 60 days is too slow
for fast movers (the new cost already fully hit weeks ago while the alert still says
"gradual") and too fast for slow movers (declares full impact at day 61 while cheaper
old stock is still selling). The window is **per-product sell-through of the pre-increase
stock**, not a hardcoded 60 days (same No-Hardcoding family as the size-guide window).

**2. The cost-increase driver is feed-only.** "A supplier raised your costs → margin
compressing" is detectable ONLY for brands with a **trustworthy cost feed** (well-
maintained Finaloop / CSV / Shopify cost field). For every other brand it is
**structurally invisible** — contribution margin's other four drivers (ad cost, returns,
discounting, mix) are all visible in the connected data, but a COGS increase moves the
one input we hold at a stale/assumed value, so computed margin does not move and there is
no residual to detect. We do not claim it.

**3. No margin VERDICT for brands without a trustworthy cost feed.** They do not get a
"your margin is compressing" alert at all — not even driver-only — because that implies a
margin figure we cannot defend. They get the **component signals** that need no cost
(returns up, CPM up, discounting deeper), each true and verifiable. *(This tightens the
Gap 1 "driver-only" decision to "component-only"; recorded as a FLAGGED PROPOSAL awaiting
founder decision — see cross_alert_orchestration.md and product_strategy.md Section 12.
Do NOT treat as locked.)*

**4. The cost-update ask is proactive, never reactive.** We cannot detect a COGS change,
so we cannot trigger an alert that says "your cost changed, go update it." The ask lives
at onboarding as a one-time negotiated agreement (cost-basis confirmation, CSV for
gaps/wrong values, ping permission, the founder's own stated refresh rhythm) — see
technical_architecture.md. The **new-SKU-missing-cost** ping is the reliable nudge
(event-triggered, low-friction); a periodic/cadence ping is the weak lever and the
alert's honesty does not rest on it.

**5. Staleness-decay governs what the alert may claim.** Fresh/confirmed cost → full
margin numbers. Cost aged past the founder's own stated refresh rhythm → the alert STOPS
stating a margin figure and drops to component signals until reconfirmed. Keyed to the
founder's stated rhythm, never a fixed number.

**6. Revenue-weighted cost coverage, not a blanket yes/no.** "Is your Shopify cost
right?" is treated as WHICH SKUs carry a cost, weighted by revenue (reuse the Gap 1
`sku_cost_coverage_by_revenue` logic). The alert speaks confidently only for the revenue
it can actually cost.

**7. Disclosure is state-driven, not on every alert.** No footnote when cost is
fresh/trusted (the basis stays one click away); a specific live caveat when aging
("based on cost from [date], ~N months old — send an update and I'll re-run"); no margin
figure at all when stale. A footnote on EVERY alert was rejected — it erodes confidence
and goes blind on the day staleness actually matters. The footnote is the visible face of
the staleness-decay.

**Honesty gap + follow-ups (logged, not solved):** "impact builds as old stock sells
through" implies cost-layer tracking (old-cost vs new-cost units). Shopify's cost field
is a single manual value with no layers and is not retroactive, so the phased curve is
only computable from an average-cost feed (Finaloop / Stocky), not Shopify alone — absent
that, narrate the phasing, do not fabricate a "% realized" number. Landed cost: a flat
1.28 multiplier mis-scales a supplier change, and duty/tariff shocks are COGS events with
no `supplier_cost_increase` behind them (possibly a missing event type). A dedicated COGS
connector is DEFERRED (discovery-gated): no single clean source at this tier, and an
approximate auto-COGS is more dangerous than honest manual COGS — see
product_strategy.md Section 12.

**Untouched (do NOT assume clean):** operational-cost/S20. Plus a final
cross-component residual-disclosure consistency pass (confirm all five suppressed
components feed `total_measured_impact` / the residual gate identically). discount-depth/S19
is now PARTIAL — see immediately below.

#### discount-depth / S19 (markdown-period margin) component — PARTIAL CLOSE (2026-06-04)

S19 eases the margin alert during a markdown (sale) window. Reviewing it confirmed the
core tension of the whole alert: discounting is the one margin driver the founder *sets
themselves*, so an alert that says "your discounting got deeper" reports a deliberate
decision back to them. The self-contained calls below are SETTLED; two interaction-
dependent calls are DEFERRED to the residual pass (they are not discounting problems —
they are cross-component problems).

**SETTLED this session:**

1. **Discount is a margin CONTRIBUTOR, not a standalone alert.** There is NO standalone
   "your discount is deep" alert — it fails the founder-utility test (the founder set the
   depth and already knows it), the same reason the standalone discount alert was killed
   earlier. The "can we flag a sale as *too deep*" question is a NON-ITEM (deleted, not
   deferred): flagging a deliberate founder decision gives the founder nothing.

2. **Cost-feed-only for the dollar figure; depth-terms for everyone else.** The DOLLAR
   margin impact of discounting is feed-only (needs trustworthy cost, same as the COGS
   driver). But discount *depth* is computed straight from order data and needs no cost —
   so for a non-trustworthy-cost brand the honest contribution is DIRECTIONAL and UNSIZED
   ("discounting deepened by N points, which pushes margin down"), consistent with the
   COGS no-verdict/component posture. (Corrects an earlier over-claim that the discount
   contribution needed cost — only the dollar magnitude does, not the depth.)

3. **Source decomposition rides a REAL trigger, not a discount threshold.** When D1
   actually fires (Trigger A step-change or Trigger B drift) and discounting is a leading
   contributor, decompose the *effective* discount by source — code vs automatic vs
   shipping — so the founder sees what the stack actually gave away. Every input is
   data-derived (Shopify exposes each discount's type); NO founder code-tagging is asked,
   and there is NO "deeper than intended/than history" judgment (no defensible baseline
   exists without founder intent or a sale-to-sale comparison, both rejected). The
   decomposition itself is the founder-can't-see-it value; it rides the legitimate margin
   trigger, never a discount-specific threshold.

4. **Planned sales suppressed via the shared known-events suppression**, never a
   discount-specific calendar window (retires the "week 1–2 suppress / weeks 3–4 fire if
   >5pp over plan / 0.20 default" mechanic — fixed windows + fixed pp + a hardcoded 20%
   fallback, all No-Hardcoding violations, and "over plan" needs a plan we do not
   capture). An UNCONFIRMED / panic markdown is NARRATED-with-context, never silently
   suppressed — so a panic clearance cannot hide behind looking like a planned sale.

**DEFERRED to the final cross-component residual pass (named so none is lost):**

- **New-vs-existing customer split for a suppressed sale's downstream returns.** A sale
  pulls in new customers, who return more, so suppressing the discount component while
  firing on the returns residual would raise a naïve returns alarm that is just the
  ordinary downstream of the sale. The fix is the new-vs-existing split (each customer
  classified from their own history) — NOT any sale-to-sale comparison. Sale-to-sale
  comparison is REJECTED (which sale / what depth / what mix / what category is
  unanswerable); the demand-weighted-discount heuristic is REJECTED at this brand tier
  (4–8 sales/yr is too few to fit a discount→return curve; product mix drives returns
  more than depth/traffic; and it is circular for the slow-creep case it would need to
  catch). Note the baseline caveat: new- AND existing-customer return rates both rise
  during a sale (bigger, more speculative baskets), so the split tells you *who*, not
  whether the level is abnormal — which is why this stays a residual-pass item, not a
  live judgment.

- **Thin-baseline confidence handling.** Busy brands have few clean non-sale days, so the
  baseline band is noisy. Treat as a confidence problem, not a firing problem: below a
  brand-relative clean-day sufficiency bar, surface with an explicit "based on limited
  clean-trading history" caveat at a lower confidence tier (feed the existing
  confidence-tier mechanism), rather than going silent or firing at full confidence.

**Return-lag reality (governs scope):** sale-window returns are a TRAILING read (a sale's
own returns arrive weeks later; returns seen *during* a sale are mostly the prior period's
orders), so they do NOT belong in the acute margin alert. A separate, mutable, sale-period
informational channel — delivery-cohort-anchored complaint pulse, NOT a return-rate
readout, with a representativeness gate and a hard "no number the founder's existing
dashboards already show" rule — is logged as a PARALLEL Horizon-2/probationary item (see
technical_architecture.md and pre_agent_build_checklist.md). It does NOT reopen this
component.

**Orphaned `margin_floor_pct` flagged.** The locked D1 trigger is fully brand-relative
(Trigger A: a drop below the brand's own baseline band scaled to its own volatility;
Trigger B: a downward trend in its own weekly CM) — it does NOT fire on an absolute floor.
The `client_config.margin_floor_pct` field (default 5%) is NOT wired into the locked
firing logic; it is a relic of the pre-Gap-2 "alert if margin < X%" design, and the
"calibrate to ~28%" note reflects that superseded thinking. Routed to the post-Gap-6
full-consistency audit for removal/revision (see cross_alert_orchestration.md).

**Build items (BATCHED, post-H — see technical_architecture.md + pre_agent_build_checklist.md):**
per-item discount staging that reads Shopify's per-line discount allocations (NEVER the
`total_discount` / `discountedTotalSet` summary fields — Shopify recommends allocations
and the summary fields return empty/zero) and captures discount *type* (automatic vs code)
for the decomposition.

---

### Operational-cost / S20 component — LOCKED 2026-06-08 (Gap 6 residual pass)

Operational cost is the fifth D1 margin-decomposition component. Locked:
- **Feed-only, no change-verdict in beta.** Carrier/3PL fulfilment cost (8–12% of revenue)
  lives on the 3PL invoice, not connected in beta. Shopify exposes the shipping CHARGE
  (customer-paid, often $0), never the brand's cost. No operational-cost change-verdict without
  a real cost-side feed.
- **Founder-stated figure is a STATIC baseline only.** The `client_config` fulfilment-cost
  field (D1 source-weight 0.05) is a static input; it cannot move, so it can never produce a
  residual signalling operational-cost compression — not a change-detector. Same honesty
  posture as COGS Tier 2/3.
- **No estimation.** Do NOT estimate shipping cost from weight×zone (confident-wrong, same
  reason as rejected approximate auto-COGS).
- **Uniform 3PL build, Horizon-2.** The future cost-side carrier/fulfilment detector is ONE
  feed-source-agnostic build (3PL invoice OR Shopify-Shipping-Label), for ALL brands, not a
  self-ship carve-out. Honors the O-20 double-count trap.
- **Known transitions via the shared known-events layer.** A 3PL switch is a founder-known
  structural event → routed through `brand_event_calendar` and narrated ("one-time cost
  excluded from structural margin"). RETIRES the seed S20 mechanic (Month-15 / $3,950 /
  full-suppression — hardcoded month, dollar, and state).
- **Regional/warehouse stockout is NOT a suppression** — a single empty node reroutes (higher
  zone, slower), does not block fulfilment; brand-wide spend-on-an-out-of-stock-SKU is owned by
  G1; any regional effect is a shipping-cost/zone DRAG inside this same invisible component.
- **Cross-alert seam LOGGED:** C10 / Alert 3 (Influencer ROI Truth) uses a destination-adjusted
  fulfilment cost that contradicts this feed-only lock — routed to the C-series reconciliation
  (cross_alert_orchestration.md).

### D1 NINE GAPS — UPDATED STATUS

| Gap | Status |
|-----|--------|
| Gap 1 — COGS tier disclosure | LOCKED ✓ 2026-05-26 — driver-only for no-trustworthy-cost brands; tightening to COMPONENT-ONLY adopted 2026-06-08 as the working assumption, formal sign-off routed to the D1 alert-language stage (gate D1-G9) |
| Gap 2 — Threshold (Trigger A + Trigger B) | LOCKED ✓ 2026-05-26 |
| Gap 3 — Causal decomposition (Principles 1–4) | LOCKED ✓ 2026-05-31 |
| Gap 4 — CPM → margin causal chain intermediate steps | DESIGN-COMPLETE ✓ 2026-05-31 — blocked on 1 schema change (suppression_log component column); go-live gate in d1_validation_gates.md |
| Gap 5 — AOV decline missing from driver set | LOCKED ✓ 2026-06-01 — standalone AOV driver retired; margin-relevant slices already in discount-depth + mix-shift; shipping/free-ship economics deferred to 3PL; category-shift routed to Gap 8 |
| Gap 6 — Seasonality suppression | WIP — Gap 6 does NOT lock; parked behind the COGS foundation (see below). 2 dependencies CLOSED; return-rate Seam 2 (S17/S18 vs C3) + C3 consistency check CLOSED 2026-06-03; **COGS/S21 component CLOSED 2026-06-03**; **discount-depth/S19 PARTIAL 2026-06-04** (no standalone discount alert; discount = margin contributor, dollar-figure feed-only / depth-terms directional otherwise; source decomposition rides a real trigger; planned sales via shared known-events suppression, panic markdowns narrated; orphaned margin_floor_pct flagged); **operational-cost/S20 CLOSED 2026-06-08**; **residual pass LOCKED 2026-06-08** — measured-not-explained rule, all-explained two-door fire, universal go-quiet ceiling, fulfilment retired (4 sites), structural-break magnitude brand-relative, BAU pre-sale-ramp exclusion + onboarding backfill, pre-sale-ramp handling (design held in state file). **CLOSEOUT STATUS 2026-06-08 (residual_presale → cogs_parked):** (1) **O-24a new-vs-returning return split — RETIRED** (Stage 2 already owns return-rate suppression; no actionable lever; prior-sale comparator too context-sensitive; periodic digest → Horizon-2). (2) **Test-data-constant verification — CLOSED, verified clean** (no live test constants in suppression paths; only hits = retired-S20 description + O-26 audit log). (3) **O-24b thin-baseline confidence — REFRAMED + BLOCKED ON COGS FOUNDATION** (now a cost-regime/versioned-COGS question, not a day-count question; cannot resolve until COGS foundation settles). (4) **All-explained edge-case actionability gate + residual-band brand-relative cutoffs — BLOCKED ON COGS FOUNDATION** (both operate on the margin residual). **→ Gap 6 remains WIP, parked; reopens only after the COGS foundation (new O-item, discovery-blocked) is worked. Build moves to C-series next.** |
| Gap 7 — "Entirely explained" framing retired | PENDING |
| Gap 8 — No action named per driver | PENDING |
| Gap 9 — No $ revenue impact display logic | PENDING |

Full D1 alert language to be written after all 9 gaps resolved.
