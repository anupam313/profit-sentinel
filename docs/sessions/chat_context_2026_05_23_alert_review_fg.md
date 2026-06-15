# Profit Sentinel — Chat Context
## Date: 2026-05-23
## Session: Alert Review — F-series and G-series Complete

---

## SESSION PURPOSE

Full deliberation of G-series and F-series alert language with founder.
Same depth as prior sessions — challenge thresholds, firing logic,
actionability, and founder-facing value at $2M–$10M fashion brand.
DQ Intelligence Layer designed and locked as a global architectural principle.

---

## G-SERIES — COMPLETE AND LOCKED

### G1 — Stockout During Active Spend

**Status:** COMPLETE — CRITICAL 🔴

**Key decisions locked:**

**Urgency:** CRITICAL (upgraded from HIGH) — actively burning money right now

**Dual impact framing:**
- Wasted spend: actual ad spend on zero-inventory SKUs
- Missed revenue: `clicks_to_zero_inventory_sku × historical_cvr × AOV`
- Fallback if SKU mapping unavailable: spend-only with disclosure

**Platform split:** Separate spend breakdown per channel (Meta, TikTok, Google).
If multiple channels burning spend → separate copy-paste brief per platform.

**Duration of burn:** `days_since_sku_went_oos` always shown — changes urgency.

**Variant vs full SKU detection:**
- Full SKU stockout: pause ad set + remove from catalogue
- Variant stockout (e.g. size XS only): exclude variant from catalogue feed only,
  do NOT pause full ad set
Agent D must detect which case and generate correct brief.

**Agency workflow:** Founder at this tier uses media buyer/agency — not Ads Manager.
PS generates copy-paste brief per platform. Founder forwards directly via
WhatsApp/email. No Ads Manager instructions.

**Restock ETA — one-tap:**
[ Within 7 days ] [ More than 7 days ] [ Not sure ]
- ≤7 days: pause spend, keep in catalogue
- >7 days or Not sure: pause spend AND remove from catalogue

**PS monitoring:** Every hour after alert fires. Confirms when spend stops.
Re-alerts if spend continues after 2 hours.
Disclosure: Airbyte sync lag caveat — not real-time confirmation.

**SKU list:** Top 3 visible, Show all [N] SKUs ↓ / Show less ↑

**Peak suppression:** Enabled (boolean in causal_graph.py)

**Currency:** `client_config.currency` — default USD. Never hardcoded.

---

### G2 — Inventory Depth Warning

**Status:** COMPLETE — INFORMATIONAL 🟡

**Key decisions locked:**

**Days remaining formula:**
`days_remaining = inventory_quantity / avg_daily_units_sold_7d`
Linear extrapolation only. Always display with `~` prefix.

**Trend indicators** (7d vs 14d sell-through comparison):
- Accelerating ↑: 7d > 14d by >10% → "(actual may be faster)"
- Stable →: within 10% → "(based on last 7 days average sales)"
- Slowing ↓: 7d < 14d by >10% → "(actual may be slower)"

**Product age:** Always shown from `product.created_at` — no dependency on
collection mapping. Format: "Listed [X] days ago"

**Collection tag:** Shown where available. Omitted gracefully where not.

**Markdown nudge:** Auto-added when listed >120 days AND sell-through slowing:
*"Listed [X] days ago with slowing sales — consider markdown before reordering."*

**SKU list:** Top 5 by days_remaining ascending. Show all/less expand-collapse.
If ≤5 at-risk SKUs: flat list.

**Systemic failure threshold:** If >20 SKUs in reorder window simultaneously:
Switch to systemic failure framing — different alert language.

**Supplier lead time:**
- SKU-level: `sku_cost_master.supplier_lead_time_days` — use if present
- Brand-level fallback: `client_config.supplier_lead_time_days` default 21
- One brand can have multiple suppliers with different lead times — Phase 1
  handles via per-SKU override, Phase 2 builds full supplier mapping
- Disclosure when using brand-level default: footer with settings link

**Reorder quantity:** NOT provided in Phase 1. Too many fashion nuances:
decay factor, collection lifecycle decay, markdown cadence, size curve
distortion, new collection cannibalisation. Deferred Phase 2.
Show directional trend only — accelerating/stable/slowing.

**Reorder summary:** Copy-paste format, directional only, no quantity.
Founder sends to ops team or directly to supplier via their channel of choice.

**avg_days_on_hand = 999 display rule:** Never show 999. Show as:
*"[N] SKUs excluded — zero sales in 30+ days (likely overstock or discontinued)."*

**Peak suppression:** Enabled (boolean in causal_graph.py)

**Currency:** `client_config.currency`

---

### G3 — Zero-Velocity SKU With Active Spend

**Status:** DEFERRED PHASE 2

**Reasons:**
1. SKU-level spend mapping unreliable at $2M–$10M tier — catalogue ads
   prevent clean SKU → spend attribution. Brands don't tag consistently.
2. Long-tail zero-velocity SKUs are normal in fashion — 14-day zero sales
   threshold generates high false positive rate on normal brand behaviour.
   A $5M brand carrying 200+ SKUs will always have 20–30% with zero sales
   in any 14-day window.

**Dead stock detection** identified as a related but separate opportunity.
Requires own alert design with correct data dependencies. Not a G3 fix.

**Customer discovery flag:** If dead stock surfaces as top-3 unsolved pain
point in interviews → prioritise G3 redesign before other Phase 2 alerts.

**Phase 2 prerequisites:**
1. Reliable SKU-level spend mapping via catalogue feed or founder-managed tagging
2. Per-SKU velocity baseline from 90+ days real client data
3. Firing condition: zero velocity relative to SKU's own normal pattern,
   not absolute zero

**causal_graph.py action:** Update status to `deferred_phase2`.

---

### G4 — Back-in-Stock Waitlist Opportunity

**Status:** COMPLETE — INFORMATIONAL 🟡

**Key decisions locked:**

**Peak suppression:** DISABLED — waitlist opportunity highest during peak events.
Founder must know about this regardless of calendar.

**Firing condition:** `waitlist_count × AOV > 15% of trailing 90-day avg daily revenue`

**Discontinued SKU suppression — behaviour-based (NOT status fields):**
Suppress if ALL three:
- Zero sales in trailing 90 days
- Listed > 180 days
- No restock detected in last 60 days
Reason: founders don't maintain `product_status` or `inventory_policy` consistently.
Infer from behaviour only.

**Waitlist source:** Klaviyo only. Shopify has no native waitlist.
Third-party back-in-stock apps (Swym, Ordersify etc.) not accessible Phase 1.
Disclosure in collapsed footnote on EVERY G4 alert — not just at onboarding.

**Klaviyo flow check:** Do NOT check flow existence — check trigger count.
If `klaviyo_back_in_stock_flow_triggered_count` in trailing 90 days = 0
despite waitlist signups → flag in alert:
*"Your back-in-stock flow hasn't triggered in 90 days — check configuration
before your restock arrives."*

**Recovery estimate — waitlist-age multiplier:**
Use founder's own historical back-in-stock CVR when ≥3 restock events available.
Otherwise use multiplier ranges:

| Waitlist age | Multiplier vs store avg CVR |
|-------------|---------------------------|
| < 2 weeks | 2.0–2.5x |
| 2–6 weeks | 1.5–2.0x |
| > 6 weeks | 1.0–1.5x |

Rationale for NOT using 3-4x: fashion-specific decay factors (time decay,
size availability mismatch, newer collection competition) cap realistic
uplift at 1.5–2.5x for most scenarios.

Always display as range, never single number:
*"$[X]–$[Y] in potentially recoverable revenue"*

**Restock options — 5 choices (one-tap):**
[ Within 2 weeks ] [ Within 30 days ]
[ No — discontinuing ] [ Not sure ]
[ Checking with my team — remind me tomorrow ]

**"Checking with my team" follow-up:**
- 24-hour reminder sent
- Max 2 reminders only — never nags beyond this
- If no response after 2nd reminder → defaults to "Not sure" action sequence

**Response-based action sequences:**
- Within 2 weeks: confirm Klaviyo flow + urgency messaging guidance
- Within 30 days: same + pre-order option suggestion
- Discontinuing: markdown guidance to clear stock
- Not sure: temper expectations, decide within 48 hours
- Checking with team: 24-hour reminder, no action sequence shown yet

**Beta-validation:** Review after first 3 beta clients. Cut if no value
over Klaviyo native back-in-stock view.

---

### PEAK SUPPRESSION ARCHITECTURE — LOCKED

Pre-baked boolean per alert in causal_graph.py. Agent B reads boolean only.
No runtime decision tree — all suppression decisions made at design time.

| Alert | Peak suppression | Reason |
|-------|-----------------|--------|
| G1 | Enabled | Planned peak — spend should already be managed |
| G2 | Enabled | Reorder decisions are planned not reactive |
| G3 | Deferred Phase 2 | N/A |
| G4 | DISABLED | Waitlist opportunity highest during peak |
| F1 | Enabled | Clean baseline logic handles event exclusion |
| F2 | DISABLED | Checkout errors always critical |
| F4 | DISABLED | Storefront errors always require action |
| F5 | Enabled | Clean baseline logic handles event exclusion |

When suppressed: internal log only (`suppression_log`). No founder message.

---

## F-SERIES — COMPLETE AND LOCKED

### F1 — Mobile Checkout Completion Rate → CVR

**Status:** COMPLETE — HIGH 🟠 — conditional on GA4

**Key decisions locked:**

**Activation:** Conditional — requires GA4 Enhanced Ecommerce step-level
events confirmed at onboarding.
- Not confirmed: `mart_column_missing` + one-time developer prompt
- Connector lifecycle: monthly Airbyte inventory check auto-detects when
  GA4 connects post-onboarding → partial re-onboarding triggered automatically

**GA4 seeding:** Seed `ga4_checkout_funnel_steps` → F1 status `active`
in synthetic. Flag for Claude Code.

**Firing threshold:** 10% drop from clean 28-day baseline.

**Clean baseline definition:**
- Exclude major event days (is_major = true) ± 3 days pre / 5 days post
- Auto-detect unlabelled events: `daily_spend > 90d_avg × 2.5`
  AND `daily_spend > client_config.spend_event_detection_floor` ($300 default)
  AND minimum 30 days spend history
- Minimum 15 clean days required — suppress if fewer
- Session floor: 200 mobile checkout initiations (not total sessions)

**Why 10% threshold (not 8%):** Same-weekday baseline rejected (new launch
decay, sale spike contamination). Clean 28-day baseline with event exclusion
is cleaner — allows tighter 10% threshold.

**Two-path Agent D logic:**
- Path A (Sentry elevated ≥5 affected users): JavaScript error framing
- Path B (Sentry silent): "Outside our visibility" framing

**Language rule:** Never say "rendering or layout issue" — we cannot confirm
this. Always say "likely outside our visibility."

**Sentry role in F1:** Corroborating only. Sentry tells us if errors exist.
F1 fires on mobile completion rate drop regardless of Sentry.

---

### F2 — Checkout Error Count → CVR

**Status:** COMPLETE — CRITICAL 🔴

**Key decisions locked:**

**Primary firing condition:**
`sentry_affected_users >= client_config.checkout_error_threshold` (default 5)

**No multiplier:** 1.5x multiplier approach explicitly rejected.
Checkout errors should be near-zero. Multiplier logic inappropriate for
near-zero baseline signals. Affected users is the only condition.

**URL filter:** `/checkout%` URL path matching — NOT Sentry tags.
Reason: brands at this tier don't configure Sentry tags consistently.
URL path is deterministic — Shopify checkout always at `/checkout` or `/checkouts/`.

**Window logic:**
- Check 1: 1-hour rolling — fire immediately if threshold crossed
- Check 2: 3-hour rolling — fire if 1-hour didn't trigger
- Always state which window triggered in alert body

**Sentry sync cadence:** 1-hour minimum (upgraded from 6-hour).
Daily sync makes F2 a post-mortem not an alert.

**`leading_signal_direction`:** Must be `rising` — verify in causal_graph.py.
Bug risk — currently may be set to `declining`.

**Threshold footer:** Always appended — current threshold + settings link.
Founder must know default is 5 and can change it.

**Peak suppression:** DISABLED.

**Revenue display:** Per-hour figure (CRITICAL tier).

---

### F3 — Bounce Rate → CVR

**Status:** DEFERRED PHASE 2

**Original definition rejected:** `total_sessions` declining → `avg_cvr` declining
was causally wrong. Session volume doesn't cause CVR to drop.

**Redefined chain also deferred:** Even with `avg_bounce_rate` as leading signal,
blended bounce rate across all traffic sources is not actionable. Founder
cannot determine which campaign/creative caused the bounce without source-level
breakdown. B-series covers paid traffic quality upstream.

**Revisit condition:** GA4 Enhanced Ecommerce with UTM passthrough confirmed
AND source-level bounce rate available per campaign.

---

### F4 — Non-Checkout Sentry Errors → CVR

**Status:** COMPLETE — HIGH 🟠

**Key decisions locked:**

**Scope:** Non-checkout Sentry errors ONLY.
Formula: `total_sentry_error_count - checkout_error_count`
Prevents simultaneous firing with F2 on same checkout error event.

**`leading_signal_direction`:** Must be `rising` — same bug risk as F2.

**Corroborating signal:** `ga4_pdp_bounce_rate` — NULL if GA4 absent.
Treat NULL as unconfirmed, not failed gate. Alert fires regardless.

**Transparency principle:** Never claim to know the cause. Ordered checklist only.
Never say "the cause is X" — say "check X first."
Never say "rendering or layout issue" — say "outside our visibility."

**Sentry link:** Always included for developer — `sentry.io/issues/{issue_id}`

**Claude Code flag:** Confirm `stg_shopify_script_tags` or `stg_shopify_themes`
exists — if yes, Agent D auto-surfaces most recent theme/app change date.

**Why we keep F4 separate from F2:**
- F2 = checkout errors → revenue stopping NOW → 1-hour window → CRITICAL
- F4 = product page errors → revenue leaking → 24-hour window → HIGH
Different urgency, different page scope, different action sequence.

---

### F5 — Checkout Funnel Step Drop → CVR

**Status:** COMPLETE — HIGH 🟠 — conditional on GA4 step-level

**Key decisions locked:**

**Source:** GA4 Enhanced Ecommerce step-level ONLY. Sentry is corroborating.
F5 answers WHERE customers drop. F2 answers THAT errors exist. Complementary.

**Activation:** Conditional — GA4 step-level confirmed at onboarding.
- Not confirmed: `mart_column_missing` + one-time developer prompt

**F5 independence from F2:** Own firing condition tied to GA4 step abandonment.
Must NOT re-fire on F2 threshold.
When both fire simultaneously: F2 = main CRITICAL alert, F5 = thread reply.

**Firing condition:** Step abandonment rate > 2x that step's own clean baseline.
Same clean baseline logic as F1.
Minimum: 50 sessions reaching that specific step in trailing 24 hours.

**Traffic quality discrimination:**
- Awareness spend increased >30% AND drop at initiation step → traffic quality framing
- All other cases → technical failure framing
Reason: aggressive top-of-funnel spend brings low-intent traffic that drops
at initiation without a technical issue. F5 must not misdiagnose this as
a checkout problem.

**Device segmentation rejected** as discrimination method — poor quality traffic
hits both devices equally. Spend composition is the correct discriminator.

**Step-specific checklists:** Different checklist per step.
- Initiation: cart page rendering, proceed button, theme changes
- Shipping: unexpected costs, no express option, international restrictions
- Payment: payment methods, discount code field, price anxiety, theme changes

**Payment method rule:** Never hardcode specific names (Shop Pay, Klarna etc.).
Generic language only. Phase 2 builds per-client payment method spec.

**Peer benchmark rule:** "Commonly caused by" framing at launch — no percentages
until 5+ real clients with follow-up responses logged.

**Weekly follow-up — 6 options (Slack buttons):**
[ Technical issue — fixed ]
[ Shipping/payment friction — adjusted ]
[ Traffic quality — targeting changed ]
[ Checking with my team — remind me tomorrow ]
[ Still investigating ]
[ Not sure ]

action_id: `f5_followup_response`
Responses stored in `alert_log` → feeds causal graph confidence over time.
"Checking with my team": 24-hour reminder, max 2 follow-ups, then defaults
to `unknown`.

---

## F-SERIES GLOBAL DECISIONS — LOCKED

### Clean baseline definition (F1, F5)
28-day rolling, excluding:
- Major event days (is_major = true) ± 3 days pre / 5 days post
- Auto-detected spend spikes: `daily_spend > 90d_avg × 2.5`
  AND `daily_spend > client_config.spend_event_detection_floor` ($300 default)
  AND minimum 30 days spend history required before auto-detection activates
Minimum 15 clean days — suppress if fewer, log `scan_skipped_reason`

### Spend event detection threshold
`daily_spend > (90d_avg_spend × 2.5)` — self-calibrating, no hardcoded floor
`spend_event_detection_floor` ($300 default) prevents near-zero spend brands
from false-flagging on trivial spend amounts.
Both conditions must be true.
Beta-calibrate $300 floor with first 3 real clients.

### GA4 dependency
F1: mobile checkout completion rate — needs GA4 step-level events
F5: funnel step abandonment — needs GA4 step-level events
Both conditional activation at onboarding.
Connector lifecycle check auto-detects GA4 connection post-onboarding.

---

## DQ INTELLIGENCE LAYER — LOCKED

### What it is
Platform-wide architectural component. Four responsibilities:
1. Per-source gap detection at onboarding and monthly
2. Per-alert confidence scoring at fire time
3. Gap quantification with revenue impact estimate
4. Proactive gap alerts separate from causal chain alerts

### Core principles locked

**No confidence tags on clean alerts:**
High-confidence alerts fire cleanly — no tags, scores, or banners.
Confidence infrastructure invisible when data is good.

**Structural limitation disclosure:**
Collapsed "ⓘ Data note" footnote — collapsed by default, tap to expand.
Shown on EVERY firing of affected alert — not just at onboarding.
One-time onboarding disclosure is insufficient — founders forget.

**Gap quantification:**
- Always a range — never a single number
- Upper bound must not exceed 3x lower bound — if wider, show
  "insufficient data to estimate"
- Primary source: founder's own historical data
- Fallback: multiplier ranges (labelled as directional estimates)
- Never use external industry benchmarks in founder-facing language

**Progressive disclosure:**
- One gap opportunity per weekly summary — ranked by dollar impact
- Never surface multiple gaps simultaneously — founder overwhelm → no action
- Once gap resolved: confirm to founder, surface next gap in following summary

**Connector lifecycle:**
Monthly Airbyte inventory check runs automatically.
New source detected → partial re-onboarding → gap message resolved.
No founder action required.

**Marketing attribution — structural limitation:**
SKU-level spend attribution via Meta/TikTok/Google API is permanently
limited in Phase 1. Cannot be fixed by better tagging. Catalogue ads
allocate spend dynamically — brand doesn't control SKU-level allocation.
Channel-level ROAS alerts: HIGH CONFIDENCE — no footnote needed.
SKU-level spend alerts: permanent structural limitation footnote.

**Agent B / Agent D responsibility split:**
Agent B reads `permanent_dq_limitations` before traversing chains.
Passes limitation metadata to `alert_log`. Does NOT make confidence decisions.
Agent D reads metadata at render time. Owns ALL founder-facing confidence
communication.

### File created
`dq_intelligence_layer_section10.md` — ready to append to
`technical_architecture.md` as Section 10 after last line:
*"Neither Triple Whale nor Northbeam deducts returns from ROAS or connects
campaign content_ids to return velocity by SKU. B-4 builds the data
foundation for both PS differentiators."*

---

## AGENT D BUILD SPEC — CREATED

File: `agent_d_build_spec.md`
Covers complete G-series and F-series alert language including:
- Exact Slack message format per alert
- Urgency tier system
- Revenue impact formulas
- Step-specific checklists (F5)
- Weekly follow-up Slack button specs
- Shared Agent D rules
- All Claude Code flags pending verification

---

## GLOBAL DECISIONS APPLICABLE ACROSS ALL SERIES

### Currency
Always `client_config.currency` — default USD ($) for US market.
Never hardcode currency symbol in any alert template.

### SKU list expand/collapse
"Show all [N] SKUs ↓" / "Show less ↑" — standard across all alerts.
Flat list when total ≤ default visible count.

### Revenue display
- Round to nearest $50
- Never show if < $50 — use "low revenue impact"
- CRITICAL and HIGH tiers: per-hour figure
- INFORMATIONAL tier: daily or projected figure

### Sidekick / Triple Whale / Northbeam competitive note
None of these tools:
- Connect Sentry errors to revenue impact
- Provide checkout error → revenue translation in plain English
- Segment funnel performance by traffic source at step level
This is confirmed PS white space for F-series alerts.

---

## OPEN ITEMS ENTERING NEXT SESSION

| Item | Status |
|------|--------|
| E-series alert review | PENDING — start here |
| D-series alert review | PENDING |
| C-series alert review | PENDING |
| B-series alert review | PENDING |
| A-series alert review | PENDING |
| H-series alert review | PENDING — last |
| Consolidated Claude Code prompt | PENDING — after H-series complete |
| Claude Code pending actions (listed in state file) | PENDING |
| product_strategy.md updates | PENDING — after code execution |
| pre_agent_build_checklist.md update | PENDING — after code execution |
