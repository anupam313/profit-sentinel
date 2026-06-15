# Profit Sentinel — Product Strategy
*Version: Post-competitive reassessment | Status: Pre-customer discovery*
*Last updated: May 2026 — Sections 8, 11, 12 revised. Section 3A written May 2026. Sections 2, 3, 3B(new), 5, 7, 11, 12 updated post-MOS discovery interview May 21 2026. 2026-06-04: Section 12 — Gorgias NLP parser as core infra + text-signal action posture closed as positions; Loop-vs-native returns discovery item added (D1 Gap 6 discount-depth/S19). 2026-06-08: Gap-1 component-only ADOPTED as the working assumption (no-trustworthy-cost brands get component signals only, no margin verdict; formal sign-off at alert-language); operational-cost/fulfilment scoped feed-only (parallel to COGS); D1 Gap 6 residual pass — operational-cost/S20 closed, fulfilment estimated driver retired.*

---

## 1. Product Positioning

### Current Positioning Statement
"The first analytics platform Shopify fashion founders actually trust — because it shows its working, explains the why across data sources they cannot join manually, and delivers the recommendation before the P&L feels it."

### What Was Removed
- "Autonomous Chief Analytic Officer" — too ambitious, sets expectation product cannot meet in Phase 1
- "Synthetic Employee" — alienating language for founders
- Detection-first alert design — founders already know something is wrong; they need cross-source explanation of why

### Trust-First Framing
The core job of the product in the first 6 months is to give founders numbers they trust. Everything else — agents, causal graphs, proactive alerts, action recommendations — is built on top of that foundation. A founder who questions one number once will question everything.

### The Critical Shift
```
OLD: "Profit Sentinel detects problems before they appear in your metrics"
NEW: "Profit Sentinel explains WHY something is happening across data 
      sources you cannot join manually — and tells you what to do about it"
```

---

## 2. Target Customer — Ideal Client Profile

**Primary target:**
- Shopify-native fashion or apparel brand (Phase 1 wedge vertical — adjacent DTC verticals are Horizon 2)
- $2M–$10M GMV
- US-based
- Running paid ads on Meta AND TikTok (both required)
- Google Ads strongly preferred (increasingly equal channel to TikTok for intent-driven traffic)
- Using Klaviyo for email
- Has Gorgias for customer support (ideally with consistent tagging)
- DTC-first (not wholesale-dominant)
- Founder or small team — no dedicated data analyst

**Disqualifying criteria for Phase 1:**
- Below $1M GMV (ticket volume too low for Gorgias signals to be statistically meaningful)
- Non-Shopify platform (WooCommerce, BigCommerce — different stack)
- Single ad channel only (Meta or TikTok alone reduces cross-source value)
- Has a dedicated in-house analyst (they can do this manually)
- Physical retail dominant (different margin structure, POS complexity)
- Non-US (different tech stack in EU/ME — Phase 2)

**The sweet spot:** A $4M DTC fashion brand with 2-3 people running operations, spending $15-25K/month on Meta, TikTok, and Google Ads, using all 4-5 connectors in Phase 1 stack, experiencing ROAS volatility they cannot diagnose.

---

## 3. The Five Proactive Alerts

**Design principle:** For sub-$5M brands, the value is NOT detection — founders already know something is wrong. The value is cross-source EXPLANATION across data they cannot join manually.

**Important scope note:** These five are the Phase 1 day-one alerts — the subset that fires immediately with Phase 1 connectors only and requires no historical depth. The full alert library contains 56 alert types (A1–G4 business alerts + H1–H19 system alerts). All 56 are active in Agent A — the others fire as Phase 2 connectors come live and as historical depth accumulates. The five below are not a product limitation; they are the guaranteed day-one cross-source value for any brand onboarding with Phase 1 connectors only.

### Alert 1: True Post-Return ROAS by Channel
**Sources:** Shopify + Meta + TikTok + Google Ads

"Your Meta ROAS shows 3.2 but your true post-return ROAS is 2.1 — 34% of Meta-attributed orders were returned. Your TikTok post-return ROAS is 2.6. TikTok is your more profitable channel right now."

*Why this is new information:* Founders see channel ROAS in each platform separately. They cannot see post-return blended ROAS across channels without joining Shopify returns with Meta, TikTok, and Google Ads attribution data at order level.

*Attribution note:* ROAS computed using founder's configured attribution model (set at onboarding — see Section 5). Default: time decay, 14-day window. Founders who configure differently will see ROAS labelled with their chosen model to avoid confusion.

### Alert 2: Root Cause of ROAS Drop Already Noticed
**Sources:** Meta + TikTok + Google Ads + Shopify

"Your ROAS dropped this week. The cause is not CPM — CPM is flat. The Summer Linen campaign is driving customers who return at 41% vs your 18% average, wiping out the apparent ROAS."

*Why this is new information:* They know ROAS dropped. They do not know which specific campaign is driving low-quality customers. Requires joining Meta campaign attribution with Shopify return cohorts at order level.

### Alert 3: Influencer ROI Truth
**Sources:** TikTok + Shopify + refunds

"You paid $2,400 for @influencer_x. Attributed revenue was $8,200 — looks great. But 52% of those orders were returned, making true net revenue $3,936 and true ROI negative after the fee."

*Why this is new information:* Surface attribution looks profitable. Return-adjusted ROI by creator requires joining TikTok attribution with Shopify refund data at order level plus creator fee data.

### Alert 4: Contribution Margin Compression with Causal Driver
**Sources:** Shopify + Meta + TikTok + Google Ads

**Alert behaviour depends on COGS tier (updated 2026-05-26):**

*Tier 1/1.5 (Finaloop or Founder CSV — full margin alert):*
"Contribution margin dropped from 31% last month to 24% this week — costing
approximately $4,200 per week at current revenue. Primary driver: Meta CPM
up 28% while revenue held flat. Secondary: return rate up 3pp on Summer
Linen collection. [Suggested action per driver]."

*Tier 2/3 (Shopify derived or Founder stated — universal baseline):*
"Three cost signals are moving against you this week: Meta CPM up 28%,
return rate up 3pp on Summer Linen, discount depth up 4pp vs last month.
Combined, these are compressing your profitability — connect your cost
data for exact margin impact."

**Alert language status:** Under review — 9 gaps identified, Gap 1 locked
(COGS tier architecture). Full alert language written after all gaps resolved.

*Why this is new information:* Founders see revenue. They may see ROAS. They
do not see contribution margin trend with the causal driver identified
automatically across sources. For Tier 2/3 brands, they see which cost
signals are moving against them — a cross-source view no single platform
provides. For Tier 1/1.5 brands, they see exact margin compression with
$ weekly impact and named driver.

### Alert 5: Sizing Complaint Velocity Predicting Return Spike
**Sources:** Gorgias + Shopify

"Gorgias tickets mentioning 'runs small' for your New Season Denim rose from 3% to 18% of tickets in 7 days. Historically for your account this precedes a return spike by 8-12 days. Add a sizing note to the product page now — before the returns hit."

*Why this is new information:* Founders read individual support tickets. They do not see velocity of complaint categories aggregated and correlated to future return spikes. Requires Gorgias + Shopify + time-series analysis.

---

## 3B. Returns Intelligence — Expanded Scope
*Added May 21 2026 post-MOS discovery interview.*

Returns are a disproportionate profit lever in fashion — systematically undermonitored because boards and founders focus on net revenue, not gross-to-net reconciliation. MOS interview confirmed: returns analytics is a genuine operational pain point, not a polite acknowledgment.

Beyond the five core alerts, the following returns intelligence signals are in scope for Phase 1 build given they require no new connectors (all derivable from ReturnGo/Loop Returns + Shopify + Gorgias):

**Serial repeat offender detection**
Flag customers whose lifetime return value exceeds a configurable threshold (e.g. >$500 in returns). Actionable: founders can adjust return policy for flagged customers or implement return fee tiers.

**Return rate by SKU**
Which specific products are structural return drivers vs one-off issues. Surfaces before aggregate return rate signals — earlier intervention window.

**Return rate by acquisition channel**
Meta-acquired customers returning at 34% vs Google-acquired at 12% is a channel quality signal, not a product signal. Changes budget allocation recommendation, not product page.

**Return rate by influencer cohort**
Which influencer-attributed cohorts return disproportionately. Feeds Alert 3 (Influencer ROI Truth) but also fires independently when a pattern is confirmed across 2+ campaigns.

**Refund vs exchange rate**
How many returners convert to exchanges (retained revenue) vs full refunds (lost revenue). Tracks policy effectiveness over time.

**Return lag by SKU**
Time between purchase and return initiation. Short lag (1–3 days) = expectation mismatch (photography/copy problem). Long lag (14–21 days) = sizing issue (used and returned).

**Implementation note:** All of the above are buildable from existing Phase 1 connectors (ReturnGo/Loop Returns + Shopify + Gorgias). No new data sources required. Build priority: return rate by channel and by SKU first — they directly feed existing ROAS and margin alerts.

---

## 3C. Natural Language Query (NLQ) — Pilot Launch Feature
*Written May 2026. Required at pilot launch — not post-beta.*

### What It Is
A query interface over all connected source data. The founder types a question
in plain English; the system translates it to a mart/staging query, resolves
ambiguity if needed, and returns the answer in the requested format.

This is not a general-purpose AI assistant. It answers questions about data
Profit Sentinel has access to — nothing outside connected sources.

**Honest scope statement for founders:**
"I can answer anything about your Shopify, Meta, TikTok, Klaviyo, Gorgias,
GA4, and Sentry data. Anything outside those sources I can't see."

### Why Pilot Launch, Not Post-Beta
Proactive alerts may take days to fire on a new account. Without NLQ, the
product is invisible to the founder between onboarding and first alert. NLQ
creates active utility from day one — founder can query their data immediately
and experience the cross-source value before any alert fires. In 2026, a chat
interface is table stakes for any AI product. Launching without it feels
incomplete regardless of alert quality.

### Core Capabilities

**1. Single-source queries**
"What was my revenue last week?"
"How many units of midnight blue dress did I sell in the last 30 days?"

**2. Cross-source queries — first-class capability, not an edge case**
The mart layer was built for this. No single-source tool can answer these.
"For midnight blue dress, show me day-by-day revenue, units sold, TikTok CTR,
Meta CTR, and returns for the last 30 days."
This is a single mart_cross_source_daily query — Shopify + TikTok + Meta +
Loop Returns joined on date × SKU. Sidekick cannot do this. Triple Whale
cannot do this at SKU level across four sources simultaneously.

**3. Ambiguity resolution**
If "midnight blue" matches multiple SKUs or campaigns, system returns
candidates and asks the founder to confirm which one before querying.
Single follow-up message — not a form. Not a failure state.

**4. Output format flexibility**
Format detected from question or explicitly requested:
- Tabular (default for multi-column queries)
- CSV (if founder asks for download)
- Plain prose (if founder asks for a summary)
- Inline chart (if question implies trend — "show me day by day")

**5. Scope guard for missing connectors**
If question requires a connector not yet active:
"I don't have Finaloop connected yet — here's what I can tell you from
Shopify's cost field proxy instead. True landed cost will be available
once Finaloop is connected."

**6. Inline alert surfacing**
If an NLQ answer crosses an alert threshold (e.g., founder asks about
return rate for a SKU and it's above threshold), surface the relevant
alert inline in the same response. NLQ and alerts reinforce each other —
not separate surfaces.

### What It Cannot Answer
- Anything requiring connectors not yet active
- Competitive intelligence ("what is my competitor doing?")
- Real-time external data ("what's trending on TikTok right now?")
- Qualitative brand perception ("is my brand seen as premium?")
- Predictive questions without sufficient historical depth (improves
  after historical_pattern_scan.py completes — typically same day
  for brands at $2M–$10M GMV)

### Historical Depth on Day 1
historical_pattern_scan.py runs at onboarding. For a $2M–$10M brand,
scan completes within the first sync cycle. Layer 3 historical context
available same day for most brands. If asked about historical patterns
before scan completes: "I'm working from your last [N] days of synced
data — historical context will deepen as I learn your account."

### Build Placement
Parallel workstream to Agent D (Step 13) — reuses the same LLM formatting
layer. Not a separate build step. Architecture spec to be defined in Agent D
design session.

---

## 3D. Alert Library — Full 41-Type Specification
*Written May 2026. Replaces placeholder. All decisions locked.*

### Overview
41 alert types across 8 groups (A–H). Each alert has:
- A unique code (A1, B3, H7 etc.)
- A plain-English name
- **Actionability classification:** High-Actionability / Monitor-and-Wait / Diagnostic-Only
- **Verification category:** A (directionally verifiable) / B (action-confounded) / C (structurally unverifiable)
- Minimum connectors required to fire
- Confidence score floor (below this, alert is suppressed)
- DQ source weights (how each source's quality affects alert confidence)

**Verification category definitions (full spec in technical_architecture.md Section 14):**
- **A:** Outcome observable in data independent of founder action. Can reach 95% precision fastest.
- **B:** Action-confounded — founder's action changes outcome, making direct verification impossible. Requires cross-client validation.
- **C:** Structurally unverifiable. Agent D always communicates explicit uncertainty in plain English. May never reach 95% precision.

**H-series note:** H1–H19 are system health and DQ alerts. The original "41 types" counted A–G groups only (business alerts). H-series was extended to H19 in May 2026 session. Total alert codes: 57 (A1–G4 = 38 business alerts, H1–H19 = 19 system alerts).

---

### Group A — ROAS and Channel Performance (A1–A7)

**A1 — True Post-Return ROAS by Channel**
- Actionability: High-Actionability
- Verification: A
- What it detects: Blended ROAS hiding channel-level gaps. Post-return ROAS on Meta vs TikTok diverges >20% when measured net of Loop returns.
- Connectors required: Shopify + Meta + TikTok + Loop Returns
- Confidence floor: 65%
- DQ weights: shopify_orders 0.40, shopify_refunds 0.25, meta_attribution 0.20, tiktok_attribution 0.10, loop_returns 0.05

**A2 — Root Cause of ROAS Drop Already Noticed**
- Actionability: High-Actionability
- Verification: A
- What it detects: ROAS drop already visible to founder. Explains which of four causes is responsible: CPM inflation, creative fatigue, checkout errors, or SKU return rate outlier.
- Connectors required: Meta + Shopify + GA4 + Sentry
- Confidence floor: 70%
- DQ weights: meta_ad_performance 0.50, shopify_orders 0.30, ga4_sessions 0.15, sentry_errors 0.05

**A3 — Channel ROAS Ranking Reversal**
- Actionability: High-Actionability
- Verification: A
- What it detects: Meta and TikTok have swapped relative ROAS ranking — historically stronger channel now underperforming.
- Connectors required: Meta + TikTok + Google Ads + Shopify
- Confidence floor: 65%
- DQ weights: meta_ad_performance 0.35, tiktok_ad_performance 0.35, google_ads 0.20, shopify_orders 0.10
- Suppression: Suppress during TikTok platform disruption events (brand_event_calendar type: platform_disruption)

**A4 — Attribution Model Inconsistency Detected**
- Actionability: Diagnostic-Only
- Verification: C
- What it detects: Same order attributed differently across Meta, TikTok, and Shopify UTMs. Surfaces the gap — does not resolve it.
- Connectors required: Meta + TikTok + Google Ads + GA4 + Shopify
- Confidence floor: 50%

**A5 — Blended CAC Exceeding LTV Threshold**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: 90-day blended CAC has crossed the founder-configured LTV threshold in client_config.ltv_cac_warning_threshold.
- Connectors required: Meta + TikTok + Shopify
- Confidence floor: 70%

**A6 — Return-Adjusted Revenue by Channel Cohort**
- Actionability: Diagnostic-Only
- Verification: A
- What it detects: Revenue attributed to a channel cohort drops materially once Loop return data applied (21-day cohort lookback).
- Connectors required: Shopify + Loop Returns + Meta + TikTok
- Confidence floor: 60%

**A7 — Wholesale Order Contamination Warning**
- Actionability: High-Actionability
- Verification: A
- What it detects: Wholesale orders exceeding 20% of total Shopify orders — blended ROAS, return rate, and contribution margin figures are contaminated by non-DTC revenue. Founder may be optimising paid spend against a distorted baseline.
- Connectors required: Shopify only
- Confidence floor: 80%
- DQ weights: shopify_orders 1.0
- Note: Fires once at onboarding if threshold crossed, then monthly. Not a continuous alert.

---

### Group B — Creative and Campaign Health (B1–B5)

**B1 — Creative Fatigue Signal**
- Actionability: High-Actionability
- Verification: B
- What it detects: CTR declining while CPM holds flat or rises. Frequency rising. Pattern matches creative fatigue in prior Meta/TikTok cycles.
- Connectors required: Meta (primary) + TikTok
- Confidence floor: 60%
- DQ weights: meta_ad_performance 0.85, tiktok_ad_performance 0.15

**B2 — Ad Spend Concentration Risk**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: >60% of total paid spend concentrated in one ad set or creative — single point of failure risk if creative fatigues or ad set enters learning phase.
- Connectors required: Meta + TikTok
- Confidence floor: 70%

**B3 — TikTok Organic-to-Paid Gap**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: TikTok organic reach declining while paid spend holds — organic-paid flywheel weakening. Indicates content quality issue not spend issue.
- Connectors required: TikTok organic + TikTok ads
- Confidence floor: 55%

**B4 — Audience Saturation Signal**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: Frequency rising, reach growth slowing, CPM rising — audience pool exhausted before creative is exhausted. Different remedy from B1.
- Connectors required: Meta
- Confidence floor: 65%

**B5 — Campaign Learning Phase Disruption**
- Actionability: High-Actionability
- Verification: A
- What it detects: Budget or bid change has pushed campaign back into learning phase — ROAS temporarily unreliable. Fires within 24h of learning phase trigger.
- Connectors required: Meta + TikTok
- Confidence floor: 80%
- Suppression: Suppress during platform disruption events

---

### Group C — Returns and Product Quality (C1–C7)

**C1 — Sizing Complaint Velocity (Alert 5)**
- Actionability: High-Actionability
- Verification: A
- What it detects: Gorgias sizing complaint rate rising faster than normal. Predicts return spike 8–12 days before Loop returns arrive.
- Connectors required: Gorgias + Shopify + Loop Returns
- Confidence floor: 65%
- DQ weights: gorgias_tickets 0.55, loop_returns 0.30, shopify_orders 0.15
- **Open decision:** Validate Gorgias tag consistency in customer discovery before relying on this alert — see Section 12.

**C2 — Influencer ROI After Returns (Alert 3)**
- Actionability: High-Actionability
- Verification: B
- What it detects: Influencer campaign ROAS drops materially when Loop return data applied to attributed cohort.
- Two-stage design:
  - Stage 1: Day 7 post-activation (early estimate, Cohort A only, return window still open). Confidence floor: 55%
  - Stage 2: Day 21 (confirmed, Cohort A+B, returns + Klaviyo downstream value). Confidence floor: 70%
- Connectors required: TikTok + Shopify + Loop Returns + Klaviyo
- DQ weights: tiktok_ad_performance 0.30, shopify_orders 0.30, loop_returns 0.25, klaviyo_profiles 0.15
- Note: Every influencer activation requires two alert_log rows (Stage 1 and Stage 2).

**C3 — SKU Return Rate Outlier Confirmed**
- Actionability: High-Actionability
- Verification: A
- What it detects: Specific SKU return rate >2x brand average sustained 7+ days. Stage 3 of three-stage return warning chain — outcome confirmation, not new signal.
- Connectors required: Shopify + Loop Returns
- Confidence floor: 75%

**C4 — Return Initiation Spike Confirms Complaint Signal**
- Actionability: Monitor-and-Wait
- Verification: A
- What it detects: Loop return initiations spiking in same SKU cohort as Gorgias complaint velocity. Stage 2 of three-stage return warning chain.
- Connectors required: Loop Returns + Shopify
- Confidence floor: 70%

**C5 — Return Reason Contamination Warning**
- Actionability: Diagnostic-Only
- Verification: C
- What it detects: Loop return reason codes diverging from Gorgias complaint text for same order cohort. Agent B weights Gorgias text over Loop codes when this fires.
- Connectors required: Gorgias + Loop Returns
- Confidence floor: 50%

**C6 — High Return Rate New Collection**
- Actionability: High-Actionability
- Verification: A
- What it detects: Return rate on new collection exceeds brand historical average by >15pp within first 14 days. Early enough for product page intervention.
- Connectors required: Shopify + Loop Returns
- Confidence floor: 70%

**C7 — Repeat Customer Return Rate Rising**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: Repeat customers (2+ orders) returning at higher rate than first-time customers. Signals product quality or sizing consistency issue, not acquisition targeting issue.
- Connectors required: Shopify + Loop Returns + Klaviyo profiles
- Confidence floor: 65%

---

### Group D — Contribution Margin and Profitability (D1–D6)

**D1 — Contribution Margin Compression (Alert 4)**
- Actionability: High-Actionability
- Verification: B
- What it detects: Contribution margin compressing below founder-configured floor. Root cause decomposed into five components: CPM inflation, rising return rate, COGS increase, discount depth increase, operational cost increase. Component-level suppression applies.
- Connectors required: Shopify + Meta + TikTok + Loop Returns + sku_cost_master
- Confidence floor: 65%
- DQ weights: shopify_orders 0.30, shopify_inventory_items 0.25, meta_ad_performance 0.20, tiktok_ad_performance 0.10, loop_returns 0.10, client_config 0.05
- **Seasonality:** Use same-week-prior-year baseline. Fall back to 90-day rolling median if <52 weeks of data. Never mix baselines within one alert.

**D2 — Discount Dependency Creep**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: Percentage of orders using a discount code rising over trailing 90 days above client_config threshold.
- Connectors required: Shopify
- Confidence floor: 70%

**D3 — COGS Step Change Impact**
- Actionability: Monitor-and-Wait
- Verification: A
- What it detects: Supplier cost increase (from sku_cost_master effective dating) flowing through to margin compression, phased over each product's own sell-through of pre-increase stock (not a fixed 60-day window — retired 2026-06-03, Gap 6 COGS). Detectable only for brands with a trustworthy cost feed; structurally invisible otherwise.
- Connectors required: Shopify + sku_cost_master
- Confidence floor: 75%

**D4 — Fulfilment Cost Anomaly**
- Actionability: High-Actionability
- Verification: A
- What it detects: Per-order fulfilment cost diverging from client_config configured baseline. Signals 3PL billing error or volume tier change.
- Connectors required: Shopify + client_config
- Confidence floor: 70%

**D5 — Klaviyo Flow Revenue Declining**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: Revenue per email sent declining across one or more Klaviyo flows over trailing 28 days. Primary metric: revenue per email sent (not open rate — iOS 15 unreliability).
- Connectors required: Klaviyo + Shopify
- Confidence floor: 60%
- DQ weights: klaviyo_email_events 0.70, shopify_orders 0.30
- Suppression: 14 days post list_clean event; 7-day rolling during Smart Send Time active.

**D6 — Seasonal Baseline Diagnostic**
- Actionability: Diagnostic-Only
- Verification: C
- What it detects: Current period metrics explained by seasonal pattern from prior year — no structural issue. Prevents false alerts during predictable cyclical movements.
- Connectors required: Shopify (12+ months history)
- Confidence floor: 60%

---

### Group E — Customer Retention and Lifecycle (E1–E4)

**E1 — List Health Degradation**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: Klaviyo deliverability metrics declining: bounce rate rising, spam complaint rate rising, unsubscribe rate rising over trailing 30 days.
- Connectors required: Klaviyo
- Confidence floor: 65%
- DQ weights: klaviyo_email_events 0.80, klaviyo_profiles 0.20
- Suppression rule: When E5 (deliverability crisis) fires, E1 is suppressed — E5 is root cause.

**E2 — Repeat Purchase Rate Declining**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: 90-day repeat purchase rate declining below client_config threshold. BFCM discount cohort excluded from denominator (S31). Denominator effect (S33) fires instead when new customer surge explains the decline.
- Connectors required: Shopify + Klaviyo profiles
- Confidence floor: 65%
- DQ weights: shopify_orders 0.60, klaviyo_profiles 0.25, loop_returns 0.15

**E3 — High-LTV Customers Going Quiet**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: Customers in top LTV decile showing reduced email engagement AND no purchase in 60 days. Leading indicator of churn in most valuable segment.
- Connectors required: Shopify + Klaviyo
- Confidence floor: 60%
- DQ weights: shopify_orders 0.50, klaviyo_email_events 0.35, klaviyo_profiles 0.15
- Suppression: S32 (VIP seasonal quiet — Nov 15–Dec 1 both years)

**E4 — Post-Purchase Flow Conversion Declining**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: Post-purchase email sequence (Flow 3) driving fewer repeat purchases than prior 90-day average. Signals content or timing issue in the retention sequence.
- Connectors required: Klaviyo + Shopify
- Confidence floor: 60%

---

### Group F — Technical and Conversion (F1–F5)

**F1 — Checkout Conversion by Device**
- Actionability: High-Actionability
- Verification: A
- What it detects: Mobile checkout conversion materially below desktop conversion AND below this client's own historical mobile baseline. Not a benchmark comparison — client-specific.
- Connectors required: GA4 + Shopify + Sentry
- Confidence floor: 70%
- DQ weights: ga4_sessions 0.55, shopify_orders 0.30, sentry_errors 0.15
- Suppression: During active A/B tests (S22), post Shopify app installation 24h (S24), post Klaviyo campaign send 4h (S23)

**F2 — Payment Gateway Failure**
- Actionability: High-Actionability
- Verification: A
- What it detects: Sentry payment_gateway_timeout errors rising above baseline. Immediate revenue impact.
- Connectors required: Sentry + GA4 + Shopify
- Confidence floor: 75%
- DQ weights: sentry_errors 0.60, ga4_sessions 0.25, shopify_orders 0.15
- Delivery: Immediate — bypasses 9am business hours hold.
- Suppression rule: F2 is root cause — when F2 fires, suppress F1, F5, A2, D1.

**F3 — External Traffic Disruption**
- Actionability: Diagnostic-Only
- Verification: C
- What it detects: GA4 traffic source mix shift not explained by campaign changes. Dark social surge, platform algorithm change, or external event driving unexplained direct traffic.
- Connectors required: GA4 + Meta + TikTok
- Confidence floor: 50%

**F4 — Page Load Performance Degradation**
- Actionability: High-Actionability
- Verification: A
- What it detects: Sentry or GA4 indicating page load time degradation on key pages (PDP, cart, checkout) correlated with conversion drop.
- Connectors required: GA4 + Sentry
- Confidence floor: 65%
- Suppression: S24 (post app install 24h)

**F5 — Checkout Step Drop-Off Spike**
- Actionability: High-Actionability
- Verification: A
- What it detects: GA4 funnel showing unusual drop-off at a specific checkout step — not at overall conversion level. Pinpoints which step is the issue.
- Connectors required: GA4 + Shopify
- Confidence floor: 70%
- Suppression: S22, S23, S24

---

### Group G — Inventory Intelligence (G1–G4)

**G1 — Stockout During Active Spend**
- Actionability: High-Actionability
- Verification: A
- What it detects: A SKU is out of stock while Meta or TikTok is actively spending against it. Immediate budget waste.
- Connectors required: Shopify inventory + Meta + TikTok
- Confidence floor: 80%
- DQ weights: shopify_inventory_levels 0.50, meta_ad_performance 0.30, tiktok_ad_performance 0.20
- Delivery: Immediate — bypasses 9am hold.
- Note: Becomes State 2 (decision support) when confirmed restock within 7 days.

**G2 — Overstock Risk Signal**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: Days of inventory on hand exceeding client_config threshold while sell-through rate declining.
- Connectors required: Shopify inventory + Klaviyo
- Confidence floor: 65%
- DQ weights: shopify_inventory_levels 0.60, shopify_orders 0.30, klaviyo_email_events 0.10
- Suppression: S27 (post inventory count 48h), S28 (carry-forward inventory tag)

**G3 — Inventory Concentration Risk**
- Actionability: Monitor-and-Wait
- Verification: B
- What it detects: >40% of total inventory value concentrated in one SKU family or category — single-SKU demand risk.
- Connectors required: Shopify inventory + sku_cost_master
- Confidence floor: 65%

**G4 — Back-in-Stock Revenue Opportunity**
- Actionability: High-Actionability
- Verification: A
- What it detects: SKU with active Klaviyo back-in-stock waitlist has just been restocked. Revenue window: 48 hours before waitlist excitement fades.
- Connectors required: Shopify inventory + Klaviyo
- Confidence floor: 75%
- Delivery: Immediate.

---

### Group H — Data Quality and System Health (H1–H19)

H-series alerts are system health and DQ alerts. Confidence floors are not threshold-based — they are near-certain when triggered. Delivery rules differ from business alerts.

**H1 — Airbyte Sync Gap**
- Actionability: Diagnostic-Only | Verification: A
- All business alerts suppressed until resolved (root cause rule S35).
- Delivery: Immediate.

**H2 — Unexplained Traffic Source Shift**
- Actionability: Diagnostic-Only | Verification: C
- Direct traffic rising unexpectedly — likely dark social, platform disruption, or unlogged PR event.

**H3 — UTM Coverage Degrading**
- Actionability: Diagnostic-Only | Verification: A
- Percentage of orders with valid UTM parameters declining. Attribution quality degrading.
- Connectors required: Shopify + GA4

**H4 — Klaviyo-Shopify Revenue Attribution Gap**
- Actionability: Diagnostic-Only | Verification: A
- Klaviyo-reported revenue diverging >20% from Shopify order revenue for same period.

**H5 — GA4-Shopify Order Count Gap**
- Actionability: Diagnostic-Only | Verification: A
- GA4 purchase events diverging >15% from Shopify order count. Ad blocker impact or GA4 instrumentation issue.

**H6 — Paid Spend Dropped to Zero**
- Actionability: High-Actionability | Verification: A
- Meta or TikTok spend dropped to zero on a day when campaigns expected to be active.
- Delivery: Immediate.

**H7 — API Rate Limit During Peak**
- Actionability: Diagnostic-Only | Verification: A
- Airbyte or custom connector hitting API rate limits — data completeness affected during peak period.

**H8 — Sentry Instrumentation Gap**
- Actionability: High-Actionability | Verification: A
- Sentry error count drops to zero for 14+ consecutive days — likely instrumentation broken after theme update.
- Delivery: Immediate.

**H9 — Meta CAPI Deduplication Failure**
- Actionability: Diagnostic-Only | Verification: A
- Meta CAPI and pixel both reporting same events — deduplication failing, inflating reported conversions.

**H10 — Shopify Infrastructure Event**
- Actionability: Diagnostic-Only | Verification: A
- Shopify platform event (from platform_algorithm_changes table) explaining anomalous data pattern.

**H11 — DQ Score Below Alert Threshold**
- Actionability: Diagnostic-Only | Verification: A
- Weighted DQ score for a specific alert type has dropped below 60% — that alert type suppressed until resolved.

**H12 — New DQ Issue Detected**
- Actionability: High-Actionability | Verification: A
- schema_discovery.py has detected a new column type change or removal in a source table.

**H13 — DQ Improvement Confirmed**
- Actionability: Diagnostic-Only | Verification: A
- A previously flagged DQ issue has been resolved — DQ score improving for affected alert types.

**H14 — Cascade DQ Chain Detected**
- Actionability: Diagnostic-Only | Verification: A
- A DQ issue in one source causing downstream DQ degradation in dependent alert types. Surfaces root source, not just symptoms.

**H15 — Gorgias Tag Inconsistency Warning**
- Actionability: High-Actionability | Verification: A
- Gorgias ticket tagging rate dropped >20% — sizing complaint velocity signal (C1/Alert 5) becoming unreliable.

**H16 — Meta Attribution Window Break**
- Actionability: Diagnostic-Only | Verification: A
- Structural break in Meta attribution data at January 12 2026 boundary. Any ROAS comparison spanning this date must include caveat in Evidence Stack Layer 2.

**H17 — iOS ATT Modeled Conversion Threshold**
- Actionability: Diagnostic-Only | Verification: A
- Meta modeled conversion percentage rising above 40% of iOS conversions — attribution reliability degrading for iOS cohort.

**H18 — Klaviyo Open Rate Reliability Warning**
- Actionability: Diagnostic-Only | Verification: C
- iOS 15 machine open inflation making open rate an unreliable primary metric. Surfaces when open rate is being used as a decision input.

**H19 — Permanent DQ Limitation Disclosure**
- Actionability: Diagnostic-Only | Verification: C
- One or more permanent structural data limitations active for this client (from permanent_dq_limitations table). Disclosed in Evidence Stack Layer 0 of affected alert types.

---

### Summary Table — All Alert Types

| Code | Name | Actionability | Verif. | Conf. Floor |
|------|------|--------------|--------|-------------|
| A1 | True Post-Return ROAS by Channel | High | A | 65% |
| A2 | Root Cause of ROAS Drop | High | A | 70% |
| A3 | Channel ROAS Ranking Reversal | High | A | 65% |
| A4 | Attribution Model Inconsistency | Diagnostic | C | 50% |
| A5 | Blended CAC vs LTV Threshold | Monitor | B | 70% |
| A6 | Return-Adjusted Revenue by Cohort | Diagnostic | A | 60% |
| B1 | Creative Fatigue Signal | High | B | 60% |
| B2 | Ad Spend Concentration Risk | Monitor | B | 70% |
| B3 | TikTok Organic-to-Paid Gap | Monitor | B | 55% |
| B4 | Audience Saturation Signal | Monitor | B | 65% |
| B5 | Campaign Learning Phase Disruption | High | A | 80% |
| C1 | Sizing Complaint Velocity | High | A | 65% |
| C2 | Influencer ROI After Returns (Stage 1) | High | B | 55% |
| C2 | Influencer ROI After Returns (Stage 2) | High | B | 70% |
| C3 | SKU Return Rate Outlier Confirmed | High | A | 75% |
| C4 | Return Initiation Spike Confirmed | Monitor | A | 70% |
| C5 | Return Reason Contamination | Diagnostic | C | 50% |
| C6 | High Return Rate New Collection | High | A | 70% |
| C7 | Repeat Customer Return Rate Rising | Monitor | B | 65% |
| D1 | Contribution Margin Compression | High | B | 65% |
| D2 | Discount Dependency Creep | Monitor | B | 70% |
| D3 | COGS Step Change Impact | Monitor | A | 75% |
| D4 | Fulfilment Cost Anomaly | High | A | 70% |
| D5 | Klaviyo Flow Revenue Declining | Monitor | B | 60% |
| D6 | Seasonal Baseline Diagnostic | Diagnostic | C | 60% |
| E1 | List Health Degradation | Monitor | B | 65% |
| E2 | Repeat Purchase Rate Declining | Monitor | B | 65% |
| E3 | High-LTV Customers Going Quiet | Monitor | B | 60% |
| E4 | Post-Purchase Flow Declining | Monitor | B | 60% |
| F1 | Checkout Conversion by Device | High | A | 70% |
| F2 | Payment Gateway Failure | High | A | 75% |
| F3 | External Traffic Disruption | Diagnostic | C | 50% |
| F4 | Page Load Performance | High | A | 65% |
| F5 | Checkout Step Drop-Off Spike | High | A | 70% |
| G1 | Stockout During Active Spend | High | A | 80% |
| G2 | Overstock Risk Signal | Monitor | B | 65% |
| G3 | Inventory Concentration Risk | Monitor | B | 65% |
| G4 | Back-in-Stock Revenue Opportunity | High | A | 75% |
| H1 | Airbyte Sync Gap | Diagnostic | A | — |
| H2 | Unexplained Traffic Source Shift | Diagnostic | C | — |
| H3 | UTM Coverage Degrading | Diagnostic | A | — |
| H4 | Klaviyo-Shopify Attribution Gap | Diagnostic | A | — |
| H5 | GA4-Shopify Order Count Gap | Diagnostic | A | — |
| H6 | Paid Spend Dropped to Zero | High | A | — |
| H7 | API Rate Limit During Peak | Diagnostic | A | — |
| H8 | Sentry Instrumentation Gap | High | A | — |
| H9 | Meta CAPI Deduplication Failure | Diagnostic | A | — |
| H10 | Shopify Infrastructure Event | Diagnostic | A | — |
| H11 | DQ Score Below Alert Threshold | Diagnostic | A | — |
| H12 | New DQ Issue Detected | High | A | — |
| H13 | DQ Improvement Confirmed | Diagnostic | A | — |
| H14 | Cascade DQ Chain Detected | Diagnostic | A | — |
| H15 | Gorgias Tag Inconsistency Warning | High | A | — |
| H16 | Meta Attribution Window Break | Diagnostic | A | — |
| H17 | iOS ATT Modeled Conversion Threshold | Diagnostic | A | — |
| H18 | Klaviyo Open Rate Reliability | Diagnostic | C | — |
| H19 | Permanent DQ Limitation Disclosure | Diagnostic | C | — |

*H-series confidence floors left blank — system health alerts are not threshold-based.*

---
# Profit Sentinel — Product Strategy
## PATCH: Section 3C Addition (May 21 2026)
## Instruction: Insert Section 3C immediately after Section 3B (NLQ) and before Section 3D (Alert Library)
## All other sections unchanged.

---

## 3E. Customer Segment Intelligence — Architecture Decision (Added May 21 2026)

*Locked May 21 2026. Do not reopen segment boundary methodology without new evidence.*

### Segment Nomenclature

Four segments apply across all fashion DTC clients. Names are intentional —
founder-facing, intuitive, and map to real CRM behaviour:

| Segment | Default order range | Behaviour profile |
|---------|-------------------|------------------|
| **Explorers** | 1 order | First purchase, brand relationship unestablished. Highest return rate — purchase is exploratory. Acquisition targeting quality signal. |
| **Regulars** | 2–3 orders | Building brand relationship. Return rate stabilising. Indicates product-market fit starting to form. |
| **Loyalists** | 4–6 orders | Trust established. Lowest return rate. Brand advocates in the making. Highly sensitive to product quality or sizing consistency changes. |
| **Advocates** | 7+ orders | Power users. Buy experimentally because they trust the brand — return rate may rise again here. Highest LTV. Loss of even a small number materially impacts annual revenue. |

Default boundaries are for **contemporary womenswear**. Other vertical defaults:

| Vertical | Explorer | Regular | Loyalist | Advocate |
|----------|---------|---------|---------|---------|
| Contemporary womenswear | 1 | 2–3 | 4–6 | 7+ |
| Swimwear | 1 | 2–4 | 5–9 | 10+ |
| Activewear | 1 | 2–5 | 6–11 | 12+ |
| Basics/essentials | 1 | 2–6 | 7–14 | 15+ |

*Note: Swimwear and activewear have higher natural repeat frequencies — boundaries
adjusted upward to prevent trivial Loyalist classifications.*

### Onboarding Calibration (One-Time, Locked After)

Segment boundaries are calibrated once at onboarding by `historical_pattern_scan.py`
using the client's own order frequency distribution. Not adjusted month-to-month.

**Why onboarding calibration, not static defaults:**
A swimwear brand with 15+ repeat orders per Loyalist and a fast-fashion brand
with 5+ repeat orders per Loyalist are both correct for their context. Static
defaults applied uniformly produce meaningless segments. Onboarding calibration
means every alert referencing a segment is grounded in that brand's actual
customer economics.

**Why calibration is locked after onboarding:**
Month-to-month boundary shifts would produce unexplained metric movements
that are model artefacts, not business signals. A Loyalist segment that shrinks
because the algorithm recalibrated is not an actionable finding. Trust requires
stable definitions the founder can internalise and act on.

**Calibration method:**
1. Query all customers with 2+ orders from Shopify staging
2. Compute percentile breakpoints at p33, p66, p90 of order frequency
3. If natural cluster gaps exist (>20% frequency jump at breakpoint), use
   cluster boundaries instead of percentile defaults
4. Write computed thresholds to `client_config` segment columns
5. Lock — founder can manually override in settings if business model changes

**Fallback condition:**
If repeat customer count < 500 at onboarding: skip calibration, use vertical
defaults, inform founder: *"We don't yet have enough repeat purchase history to
calibrate your customer segments precisely — using contemporary womenswear defaults.
We'll recalibrate after 6 months of data."*

### What Is Tracked Per Segment

Per segment per day in `mart_customer_segments_daily`:

- `segment_customer_count` — absolute number of customers
- `segment_pct_of_total_customers` — population share
- `segment_pct_of_total_revenue` — revenue share (trailing 90 days)
- `segment_avg_roas` — revenue attributed to cohort / acquisition cost for cohort
- `segment_return_rate_7d` — trailing 7-day return rate for segment
- `segment_aov_7d` — average order value for segment

### Minimum Significance Threshold

`client_config.segment_significance_min_revenue_pct` (default 2%).

If a segment contributes <2% of revenue, Agent B suppresses segment-specific alerts
for that segment and sends an informational note instead:
*"Your [Segment] segment is currently too small to generate reliable signals —
X% of customers, Y% of revenue."*

Rationale: A Loyalist segment at 0.3% of customers contributing 0.8% of revenue
is a rounding error. Firing C7 or E3 on this segment would produce noise, not
intelligence.

### Alerts That Use Segment Data

| Alert | How segment data is used |
|-------|------------------------|
| C7 — Repeat Customer Return Rate Rising | Fires per segment — identifies whether return rate is rising in Regulars (sizing issue) vs Loyalists (product quality change) |
| E2 — Repeat Purchase Rate Declining | Segment breakdown identifies which cohort is churning first |
| E3 — High-LTV Customers Going Quiet | Loyalist and Advocate engagement monitoring — vip_purchase_gap_days + segment engagement score |
| A2 — Root Cause of ROAS Drop | `new_customer_return_rate_7d` as Explorer cohort signal — high Explorer return rate = acquisition targeting problem, not product problem |

### New Customer Return Rate — Acquisition Quality Signal

`new_customer_return_rate_7d` tracks Explorer segment return rate specifically.

This is structurally different from brand-average return rate. If Explorer return
rate diverges significantly above brand average for Loyalists, the signal is:
*"You are acquiring customers who are not a good fit for your product."*

The correct response is to reduce budget on acquisition campaigns producing
high-return Explorer cohorts — not to fix the product. This distinction is what
no single-source tool can surface: it requires joining Meta/TikTok campaign
attribution with Shopify return data at order level, segmented by customer order
history from Shopify.

This column becomes a component input to A2 (root cause of ROAS drop) — high
Explorer return rate is the fifth root cause path, in addition to CPM inflation,
creative fatigue, checkout errors, and SKU return rate outlier.

### What This Is Not

Segment intelligence is not a CRM feature. Profit Sentinel does not send emails,
manage flows, or create audiences. The output is always an alert or insight that
the founder acts on using their existing tools (Klaviyo, Meta, TikTok). Profit
Sentinel identifies the segment problem; the founder resolves it in the tool that
owns that customer relationship.

---
## 4. Evidence Stack Format

Every alert follows exactly this 5-layer structure. Enforced at Agent D level — no alert can be delivered without all layers.

### Layer 0 — Data Quality Score
```
DATA QUALITY — before you act on this alert
Shopify data:    ████████░░  82% complete
Meta data:       ██████░░░░  61% complete
                 UTMs broken on 39% of campaigns
Overall confidence: MEDIUM
Reason: Meta attribution gaps limit causal certainty
```
Three rules:
- Above 80%: Full Evidence Stack fires normally
- 60-80%: Fires with caveat "Medium confidence — data gaps noted"
- Below 60%: Alert suppressed, replaced with data quality fix notification

### Layer 1 — What
Specific signal detected. No jargon, no percentage-of-percentage language.
"CPM on your 'Midnight Blue Dress' TikTok ad set has risen 38% over the last 48 hours."

### Layer 2 — Why We Are Confident
**Must show actual raw metric values that founder can verify themselves in 30 seconds.**
"CPM trajectory: Day 1 $18.40 → Day 2 $21.20 → Day 3 $25.60 (+39% in 72h). Data last refreshed: 2 hours ago. Confidence score: 87%. Verify in Meta Ads Manager → Ad Set Insights — these figures match exactly."

### Layer 3 — Historical Precedent
**Must reference specific historical date and outcome from this brand's own data.**
"This pattern preceded a ROAS decline in 3 of the last 4 occurrences for your account. Most recently: week of October 14th — CPM rose 31%, ROAS dropped from 3.4 to 2.1 within 6 days. The two prior instances showed similar lead times of 5-7 days. One instance (March) did not result in a decline — that week coincided with a Meta platform-wide CPM spike affecting multiple brands."

### Layer 4 — Suggested Action
"Reduce budget by 30% on 'Midnight Blue Dress' ad set. Estimated ROAS recovery: +0.4 within 5 days."

**Buttons:** ✓ Approve   ⏸ Snooze 24h   ✕ Dismiss

---

## 5. Onboarding Architecture

### Design Principle
Every gap type has a resolution path. Every resolution path has a fallback. Missing connectors become waitlist entries — not error states. Onboarding never dead-ends.

**Cross-source moment by minute 10 (Design Principle 8):** Onboarding must surface a cross-source insight that Shopify Sidekick cannot replicate before the founder completes setup. This is a hard product requirement — not a nice-to-have.

### The Six Confirmation Questions
These six questions run after staging completes, before marts run for the first time. Answers write to client_config. A definition change later triggers dbt full-refresh recomputing all historical marts.

1. **COGS tier confirmation:** (updated 2026-05-26 — 4-tier architecture)

   Step 1: "Do you have Finaloop set up?"
   → Yes: set cogs_tier_active = 'finaloop'. Full margin alerts enabled.

   Step 2 (if no Finaloop): "Do you maintain cost-per-item in Shopify for
   all your products? Is it your landed cost (including freight and duties)?"
   → Yes + landed: cogs_tier_active = 'shopify_derived', cogs_shopify_confirmed = true,
     cogs_shopify_landed = true
   → Yes + ex-factory: cogs_tier_active = 'shopify_derived', cogs_shopify_confirmed = true.
     Ask: "What multiplier covers your freight and duties? (Common range: 1.10–1.50.
     Our default is 1.28.)" → write to cogs_multiplier_confirmed
   → No: offer CSV upload path immediately.
     "Many founders keep costs in a spreadsheet — you can upload your SKU cost file
     and we'll match it to your Shopify catalogue."
     → If upload: cogs_tier_active = 'founder_csv' after reconciliation complete
     → If no upload: cogs_tier_active = 'founder_stated'. Ask blended margin %.

   Step 3 (if CSV upload chosen): Collect cogs_owner_contact contextually
   after fuzzy/unmatched SKUs detected (not as upfront form field):
   "We found [X] SKUs we couldn't confidently match. Who should we send
   these to for offline review? [Enter email]"
   → Send reconciliation file immediately to that contact
   → CC founder on all subsequent COGS gap communications

   → Writes: cogs_tier_active, cogs_source, cogs_confidence_level,
             cogs_shopify_confirmed, cogs_shopify_landed, cogs_multiplier_confirmed,
             cogs_owner_contact
   → Determines: which D1 alert template fires (full margin vs driver-only)

2. **Business model type:** "Is your business year-round, seasonally heavy, or event-driven?"
   → Writes: business_model_type
   → Determines: which baseline comparison method is used for margin alerts

3. **Attribution model:** "When measuring ROAS, which attribution model do you want as your baseline? We'll compute all models but will use this one for alerts and recommendations."

   Options presented with one-line explanation each:
   - **Last touch** — Full credit to the final click before purchase. Simplest, but undervalues brand awareness spend.
   - **First touch** — Full credit to first interaction. Good for measuring how new customers enter your funnel.
   - **Linear** — Equal credit across all touchpoints in the journey.
   - **Time decay** — More credit to touchpoints closer to purchase. *(Recommended for fashion — considered purchase with multi-week journey.)*
   - **Position-based** — 40% to first touch, 40% to last touch, 20% distributed across middle.
   - **Linear (clicks + deterministic views)** — Separates click attribution from view-through. Most sophisticated; closest to truth for Meta-heavy brands.
   - **Custom weights** — Define your own distribution across touchpoints.

   Default if no selection: **time decay**.
   → Writes: attribution_model, attribution_model_label
   → All ROAS alerts display the configured model label so founders always know which methodology underlies the number.
   → Non-default choice: displayed prominently in every ROAS alert header — "ROAS computed using [model] attribution."

4. **Attribution window:** "How many days between first brand interaction and purchase do you want us to count? Fashion brands typically have 7–21 day consideration windows."

   Options: 1 day / 7 days / 14 days / 21 days / 28 days / Custom
   Default if no selection: **14 days** *(working assumption — validate across remaining discovery interviews).*
   → Writes: attribution_window_days
   → Determines: how far back PS looks when attributing an order to a touchpoint

   **Design rationale for questions 3 and 4:** Attribution model and window are foundational — they determine every ROAS and margin number the product surfaces. A founder who doesn't trust the attribution methodology will not trust any alert built on top of it (validated: MOS interview, May 21 2026). Presenting all options with plain-English logic allows educated founders to configure precisely and less experienced founders to understand why the default exists. Recommended defaults clearly marked. Selection is not a prerequisite to proceed — defaults apply if skipped.

5. **ROAS revenue definition:** "Do you include or exclude shipping revenue in ROAS? And do you measure ROAS gross of returns or net?"
   Options: Exclude shipping / Include shipping; Gross of returns (default) / Net of returns
   Default if no selection: exclude shipping, gross of returns.
   → Writes: roas_revenue_definition, roas_net_of_returns
   → Determines: how Alert A1 computes post-return ROAS denominators and how all channel ROAS figures are presented throughout the product
   → Note: "Net of returns" is the more accurate figure for true profitability; "gross of returns" matches what founders see natively in Meta and TikTok Ads Manager. Both are computed — this setting determines which is the primary display value.

6. **Alert sensitivity:** "How sensitive should alerts be? Conservative (fewer, higher confidence), Medium, or Aggressive (more alerts, lower threshold)?"
   → Writes: alert_sensitivity
   → Adjusts: all threshold values in client_config by sensitivity multiplier

### Historical Pattern Scan (Step 7 of Onboarding — runs after confirmation questions)

After the six confirmation questions and dbt full-refresh, `historical_pattern_scan.py` runs automatically before the first live alert fires. This is not optional — it is a required onboarding step.

**Two run modes:**
- **Full sweep (onboarding):** Runs asynchronously after dbt full-refresh. Completes silently — no founder-facing message. `historical_scan_status` in `client_config` updated on completion. `last_historical_scan_at` written.
- **Monthly incremental:** Scheduled 1st of each month. Scans only data since `last_historical_scan_at`. New novel pairs validated against full history before storing.

**What it does — known chain validation (56 chains):**
- Scans full available history per connector: Shopify/Klaviyo/Gorgias/Loop → account creation; Meta → 13 months; GA4 → post-July 2023; TikTok → 24 months; Sentry → 90 days
- Hit definition: leading signal AND outcome both cross their live-agent thresholds within lag ± 2 days. Binary — 1 or 0 per instance. Denominator is observable instances only (outcome window fully closed).
- Writes `observable_instance_count`, `hit_rate`, and `confidence_tier` to `causal_pattern_validation` with `historical_scan_seeded = true`
- Confidence tiers: candidate (<4 observable instances OR <70% hit rate) / provisional (4–9 observable AND ≥70%) / core (≥10 observable AND ≥80%)
- Category B (action-confounded) patterns carry explicit Layer 0 disclosure regardless of tier

**What it does — novel chain discovery (beyond 56):**
- Completely separate code path from known chain validation — no merging at any stage
- Unconstrained bivariate sweep across all mart column pairs
- Sparsity filter: leading signal must have crossed threshold ≥4 times — pairs below this not stored
- All candidates written to `candidate_signals` — nothing auto-promotes
- Pre-filters: calendar dispersion check (>60% trigger dates in fashion calendar windows → `calendar_clustered = true`) + effect size minimum (outcome must move ≥50% of live-agent threshold)
- Two promotion tracks: Track 1 (cross-client convergence — deferred to post-10-client milestone, DEBT-T1) / Track 2 (single-client depth, ≥10 instances, ≥80% hit rate → `single_client_core = true` → practitioner review → `practitioner_approved = true` → core behaviour for that client only, permanently `client_specific`)
- Novel chains are vertical-specific in both tracks — no cross-vertical promotion ever
- `client_specific` set to false only after re-scan confirms chain post-practitioner-approval (not at approval)
- Monthly practitioner digest (internal, not founder-facing): shortlisted candidates after pre-filtering, <10 items/month. Deferred until 5+ beta clients.

**Why this matters:**
- Evidence Stack Layer 3 (historical precedent) is populated from real brand data on day one — not generic benchmarks
- Brands with 5+ years of Shopify/Gorgias/Klaviyo history produce significantly higher confidence scores at launch than brands with 12 months of data
- Single-client depth track (Track 2) creates a disproportionate switching cost moat — brand-specific causal intelligence deepens over time and cannot be replicated by any cross-client benchmark

### Three-Bucket Revenue Validation
Before confirmation questions, the system validates revenue against three gap types:

- **Bucket 1 — Structural Gap (<0.5%):** Shopify post-processing (fraud filtering, bot removal). Accept and explain transparently. No action required.
- **Bucket 2 — Segmentation Gap (any size):** Founder defines metric differently from Shopify default. One-click resolution. client_config updated. dbt reruns.
- **Bucket 3 — Missing Connector Gap (any size):** Orders from systems not yet onboarded. Revenue at stake quantified. Founder chooses: include as-is, exclude, or add to connector waitlist.

---

### Onboarding Completion Message

Delivered in Slack after historical_pattern_scan.py completes. Two variants.

**Headline lookback rule:** Use the deepest single-source lookback (Shopify/Klaviyo as anchor — almost always longest). Per-source limitations handled silently in the scan. Short-history connectors (e.g. recently-added Gorgias) do not reduce the headline lookback number — their chains simply produce lower instance counts.

**$ leakage display rule:** Show dollar section only if total quantifiable leakage ≥1% of derived annual GMV AND at least 2 distinct patterns contribute. GMV derived from Shopify total order revenue in scan window — not founder-stated. If threshold not met, suppress dollar section entirely without explanation.

**Variant 1 — $ threshold crossed:**
```
Welcome to Profit Sentinel, [Brand Name].

We've analysed your last [X] months of data across Shopify, Meta, Klaviyo, and TikTok.

In the last 12 months, we identified $[X] in profit at risk across [N] patterns in your business:

→ [Pattern in plain English with $ impact]
→ [Pattern in plain English with $ impact]
→ [Pattern in plain English with $ impact]

From today, Profit Sentinel is your dedicated profit guard. One objective: protect and 
grow your margin. We'll only reach out when something genuinely threatens your 
profitability — no noise, no dashboards.

When an alert arrives, you'll see exactly what's happening, why, and what to do. Hit 
Agree, Snooze, or Disagree — every tap teaches Profit Sentinel your business. The more 
you respond, the sharper and more personalised your alerts become.

You can also ask me anything about your business directly — "What was my best performing 
SKU last month?" or "Why did my ROAS drop last week?" — I'll answer instantly from your 
connected sources.

For patterns I haven't seen before in your data, I'll tell you what I see and flag that 
I'm still learning the cause — I get sharper the longer I run.

We're watching. You'll hear from us when it matters.
```

**Variant 2 — $ threshold not crossed (suppressed without explanation):**
```
Welcome to Profit Sentinel, [Brand Name].

We've analysed your last [X] months of data across Shopify, Meta, Klaviyo, and TikTok. 
Profit Sentinel is now calibrated to your business — your thresholds, your patterns, 
your history.

From today, we're your dedicated profit guard. One objective: protect and grow your 
margin. We'll only reach out when something genuinely threatens your profitability — 
no noise, no dashboards.

When an alert arrives, you'll see exactly what's happening, why, and what to do. Hit 
Agree, Snooze, or Disagree — every tap teaches Profit Sentinel your business. The more 
you respond, the sharper and more personalised your alerts become.

You can also ask me anything about your business directly — "What was my best performing 
SKU last month?" or "Why did my ROAS drop last week?" — I'll answer instantly from your 
connected sources.

For patterns I haven't seen before in your data, I'll tell you what I see and flag that 
I'm still learning the cause — I get sharper the longer I run.

We're watching. You'll hear from us when it matters.
```

**Implementation notes:**
- Connector list in headline is dynamic — only shows connected sources
- "Your first alert will fire" language only used if ≥1 chain is at provisional or core tier
- "Why did my ROAS drop?" in NLQ example is accurate at pilot — Agent B handles causal reasoning
- Causal NLQ questions for chains not yet in the 56 return: "I can see X happened but I don't yet have enough data to identify the cause — I'm tracking it"

---

## 6. Pricing Architecture

*(Unchanged from previous version)*

---

## 7. Connector Prioritisation Framework

### Phase 1 Connectors (Day-One — Required for Five Core Alerts)
*Updated May 21 2026 — Google Ads added as first-class Phase 1 connector.*

- Shopify (orders, refunds, inventory, products)
- Meta Ads
- TikTok Ads
- **Google Ads** *(added May 21 2026 — equal channel importance for intent-driven traffic; required for complete channel ROAS comparison in Alert 1 and Alert 2)*
- Klaviyo
- Gorgias
- GA4
- Sentry
- ReturnGo / Loop Returns

**Google Ads rationale:** Google Ads captures high-intent search traffic — customers actively looking for what the brand sells. Unlike Meta and TikTok (interruption channels), Google is intent-driven, producing a structurally different customer profile. Return rates, ROAS, and LTV differ meaningfully between Google-acquired and social-acquired cohorts. Omitting Google Ads from Phase 1 makes Alert 1 (channel ROAS comparison) structurally incomplete. API is mature, well-documented, and widely integrated — lowest incremental build cost of all ad connectors.

**Data seeding note:** Google Ads requires its own synthetic seed data set for product testing (same pattern as Meta and TikTok seeds). Existing seeds are not affected — Google Ads seeds independently.

---

## 8. Competitive Positioning

*(Revised May 2026 — Sections rewritten post-Moby 2 launch)*

### The Competitive Reality (May 2026)
Triple Whale launched Moby 2 in April 2026 — a conversational AI layer on top of their existing attribution and analytics stack. This closes a positioning gap that previously existed. The competitive landscape now requires more precise differentiation.

### Four Surviving Defensible Claims

**Claim 1 — Cross-source causal intelligence, not reporting.**
Moby 2 answers questions about data already in Triple Whale. It does not join Gorgias + Loop Returns + Shopify at the order level to surface a sizing complaint predicting a return spike 10 days before it hits. The causal graph traversal across all 8 sources is structurally different from an LLM layer on top of attribution reporting.

**Claim 2 — Proactive, not reactive.**
Triple Whale (and Moby 2) is query-driven — you ask, it answers. Profit Sentinel pushes alerts before the founder notices the problem. The core hypothesis is that founders will act on proactive intelligence they didn't ask for. This is the product thesis, not a feature.

**Claim 3 — Fashion vertical depth.**
The Precision Profit Calendar, return lag segmentation, influencer ROI after returns, sizing complaint velocity — these are calibrated first for fashion brands. The causal graph architecture is vertical-first, not horizontal — starting with fashion, extensible to adjacent DTC verticals in Horizon 2 after beta validation. Generic e-commerce tools apply horizontal logic to every vertical equally. Profit Sentinel does not.

**Claim 4 — Evidence Stack transparency.**
Every alert shows its working: raw verifiable numbers, specific historical precedent from this brand's own data, plain-English uncertainty communication. This is a trust mechanism, not a UI feature.

### Three Dropped Claims (Do Not Use)
- "No other tool joins these sources" — Moby 2 partially closes this gap
- "Autonomous profit management" — too ambitious for Phase 1
- "Replaces your analyst" — alienating language

### Sidekick Strategy — CLOSED
Build alongside Sidekick. Not inside it, not against it. Cross-source moment visible by minute 10 is the differentiator. Slack is the explicit alternative to Sidekick's admin-bound interface. Monitor App Extensions developer preview quarterly.

---

## 9. The Fashion Intelligence Network (Moat 2)

*(Unchanged from previous version)*

---

## 10. Founder Decision DNA (Moat 3)

*(Unchanged from previous version)*

---

## 11. Customer Discovery Framework

*Section rewritten May 2026. v2 framework. Interview questionnaire updated to v3 post-MOS session May 21 2026.*

### Interview Protocol Updates (v3 — May 21 2026)
- Target interview duration extended to **45 minutes** (was 30 minutes — consistently insufficient)
- Pre-interview screener **removed** — adds friction before relationship established; context questions folded into warm-up conversation
- Scenario test split into **spoken setup + chat paste protocol** — reading full scenario aloud is too complex for real-time comprehension
- Q3 reframed to **financial/margin decisions specifically** — open-ended version produces product/ops rabbit holes
- Section 3 signals **compressed to one sentence each** for faster founder response
- **Tool stack section added** (Section 4) — 9 categories, top 3–4 tools each, with "none/manual" option
- Scoring: **Slack-first signal replaced** with delivery surface fit
- Referral close rewritten — warmer, explicitly asks for warm intro, no cold-name escape hatch
- GMV question removed — available via public signals

### Delivery Surface Finding (MOS Interview — May 21 2026)
MOS founder explicitly stated Shopify app store as preferred surface. Checks 3–4 Shopify apps daily. Trusts Shopify-sourced data more than third-party aggregators. Slack described as "too crowded."

**Status of open decision on Slack as delivery channel:** Partially invalidated by one interview. Not sufficient to close — requires 5+ interviews to establish pattern. If 6+ of 10 founders confirm same preference, Shopify-native delivery becomes a build requirement. Monitor in every subsequent interview.

### Before the Interview:
- Target: Shopify fashion brand, $2M–$10M GMV, US-based, running Meta + TikTok
- Duration: 45 minutes maximum
- Recording: Ask permission. Take notes regardless.
- Frame: "I'm not pitching anything. I'm trying to understand how you make decisions."

**For hot leads (personal connects):**
- Open with explicit disarming: "The most useful thing you can do is tell me if I'm building the wrong thing."
- Push harder on Q3 and Q11 — personal connects will give polished answers by default. You have permission to ask for the real one.
- Score them using the rubric regardless of the relationship. A personal connect who scores 8/24 is not a beta candidate.
- Do not demo or hint at the product mid-interview.

### The Six Sections

**Section 1 — Context (5 minutes)**

Q1. "Walk me through how you currently track whether the business is profitable week to week. What do you look at, how often, and what tools do you use?"

*Listen for: manual tab-switching, which metrics they actually monitor vs which they think they should.*

Q2. "What's the last profit or margin problem you caught — and how did you find it?"

*Listen for: lag between problem starting and founder noticing. More than 3 days = scoring signal.*

**Section 2 — Pain Identification (10 minutes)**

Q3. "Tell me about a specific decision you wish you'd made differently in the last 6 months — ideally something where you had the wrong information or found out too late."

*This is the most important question in the interview. Write the answer verbatim.*

Q4. "When your ROAS drops, what's your current process for figuring out why?"

*Listen for: how many tools they open, whether they ever get to a definitive root cause.*

Q5. "How do you currently measure whether an influencer campaign was actually profitable — after returns?"

*Listen for: whether they measure this at all, and whether they account for returns.*

**Section 3 — Competitive Reality (5 minutes)**

Q6. "Are you using Shopify Sidekick or Pulse? What do you use it for?"

*Sidekick detection question. Listen for: whether they find it sufficient, what they use it for vs what they wish it did.*

**Section 4 — Scenario Test (10 minutes)**

Q7. "I'm going to describe a scenario and I want your honest first reaction."

*Scenario:* "You get a Slack message at 9am: 'Your sizing complaint tickets for the Spring Linen collection rose from 4% to 22% of all tickets in the last 7 days. Based on your account history, this typically precedes a return spike of 15–20% within 10 days. Suggested action: add a size guide to the product page now.' How do you react?"

*Score responses:*
- Type A: "I'd act on that immediately" — high actionability
- Type B: "I'd want to verify the numbers first, then act" — Evidence Stack user
- Type C: "I'd need to understand how it calculated that" — needs trust-building
- Type D: "I don't trust AI alerts" — product hypothesis fails for this founder

Q8. "What would need to be true about the alert for you to act on it without verifying it yourself?"

*Listen for: what trust signals matter most (data transparency, historical accuracy, confidence score).*

**Section 5 — Current Stack and Signal Gaps (10 minutes)**

Q9. "Walk me through your current tech stack — everything you use to run the business."

*Confirm: Shopify, Meta, TikTok, Klaviyo, Gorgias (or equivalent). Note any missing connectors.*

Q10. "Of the five things I'm about to describe, which ones are invisible to you today — you genuinely don't know the answer without manually pulling data?"
- True post-return ROAS by channel
- Which specific campaign is driving your ROAS drop
- Whether your influencer campaigns are profitable after returns
- What's compressing your contribution margin this week
- Whether sizing complaints are predicting your next return spike

*Score: 2+ genuinely invisible = strong signal.*

**Section 6 — Signal Gap and Wrap (5 minutes)**

Q11. "If I could give you one piece of information about your business that you don't currently have — just one — what would it be?"

*Most important signal in the entire discovery process. If 6+ founders give answers outside the five alerts, that is a pivot signal. Write it verbatim.*

Q12. "If a tool gave you the root cause of a profit problem — with the data proof — but you had to verify it yourself before acting, would you? Or would you need it to just tell you what to do and trust it?"

*Listen for: verification appetite (Evidence Stack users) versus recommendation appetite (Action Layer users).*

Q13. "Is there anything about how you currently run the business — how you make decisions, what tools you use, what your team looks like — that I should understand before we finish?"

### Scoring Rubric
8 signals × 0/1/3 points = max 24 points

| Signal | What to Score |
|---|---|
| Lag awareness | More than 3 days between problem starting and founder noticing |
| Manual root cause | Describes opening multiple tabs and joining data manually |
| Scenario response | Type A or B on the scenario test |
| Stack fit | Uses Shopify + Meta + TikTok + structured support tool with ticket tagging |
| Support tagging | Tags tickets consistently by complaint category |
| Signal gap | At least 2 of the 5 signals are genuinely invisible to them today |
| Cross-source hunger | Q7 response shows desire for joined cross-source explanation |
| Sidekick gap | Not currently satisfied with Sidekick as sufficient |

**Score interpretation:**
- 19–24: Priority beta candidate — onboard first cohort
- 12–18: Strong second cohort — note what signal is missing
- 6–11: Later cohort or repositioning candidate
- 0–5: Do not prioritise

### Pivot Signals — When to Stop and Reassess
Stop and reassess the core product hypothesis if any of these occur across 10 interviews:

- Majority of founders score Type C or D on the scenario test
- More than 6 founders say all five signals are already visible to them
- More than 6 founders say Sidekick is sufficient for their current needs
- Support ticket tagging is inconsistent in more than 7 of 10 brands
- The answer to Q11 is outside the five alerts in more than 6 interviews
- More than 6 founders describe an agency as their primary decision-maker on ad spend

---

## 12. Open Decisions and Deferred Items
*Section updated May 2026. Two decisions closed since previous version. 2026-06-02: two further closed positions added (suppressed-leak weekly digest; Phase-1/2 category sequencing). 2026-06-03: size-guide/photography detection decision + metaobject-fraction question added (Gap 6 Seam 2); COGS feed-only scoping decision + Gap 1 component-only FLAGGED PROPOSAL added (Gap 6 COGS). 2026-06-04: Gorgias NLP parser confirmed core infra + text-signal action posture (summarise-and-link, case-by-case) CLOSED as positions; Loop-vs-Shopify-native returns split added as a discovery item (Gap 6 discount-depth/S19).*

### Closed Decisions (Do Not Reopen Without New Evidence)

**COGS architecture — UPDATED 2026-05-31 (originally locked 2026-05-26):**
Five-tier COGS architecture. Tier 0 (Founder-Stated Blended Per-Order Cost)
added as the realistic fallback for the majority of founders who cannot produce
a per-SKU cost CSV. Tier 1 (Finaloop) corrected — Finaloop has NO public API;
the Tier 1 path is a manual CSV export from Finaloop uploaded to PS, not an
API connector. Monitor quarterly for Finaloop API release.
Tier 1.5 (Founder CSV) / Tier 2 (Shopify confirmed) / Tier 3 (no data)
unchanged from 2026-05-26 lock.
D4 (Fulfilment Cost Anomaly) DEFERRED to Phase 2 — cannot fire reliably in
beta without 3PL billing data. Shopify fulfillment API does not contain brand
3PL costs. No 3PL or supply chain connector exists in beta.
CSV is the only COGS ingestion path in beta.
Finaloop adoption rate in ICP is UNVALIDATED — must confirm in discovery.
If fewer than 5 of 10 brands use Finaloop, Tier 0 and Tier 3 are the primary
beta paths. Add "Do you use Finaloop, QuickBooks, or Xero?" to discovery
interview before next session.

**Sidekick strategy — CLOSED May 2026:** Build alongside Sidekick. Not inside it, not against it. Full rationale in Section 8. Monitor App Extensions developer preview quarterly. Reopen only if Shopify enables genuine cross-source data via third-party connectors inside Sidekick.

**Geographic focus — CLOSED May 2026:** US Shopify fashion market only for Phase 1. All other geographies are Phase 2+. India was evaluated as a brainstorming exercise and not pursued. The US Gold Stack (Shopify + Meta + TikTok + Klaviyo + Gorgias) is the only market where all five alerts can fire at full strength. Non-US expansion follows US validation, not precedes it.

**Planning mode — CLOSED May 2026:** Forward-looking planning intelligence (pre-launch advisory, budget allocation advisory, inventory commitment advisory) is explicitly out of scope. Not Horizon 2. Not on the roadmap. Profit Sentinel's job is profitability monitoring, not planning advisory. The boundary is: real-time and historical signals only. No forward projections as a product mode.

**Competitor / auction pressure in Evidence Stack — CLOSED for beta, deferred to Horizon 2:** Meta `auction_competitiveness` field and `vertical_cpm_benchmarks` wiring into Layer 2 deferred until post-beta. Reason: beta goal is 70%+ alert action rate on five core alerts. Adding noisy auction pressure signals before real client outcome data exists adds complexity at the moment precision is most critical. Revisit at Month 6 with real client data to calibrate against.

**Alert suppression based on financial capacity — CLOSED May 2026:** Profit Sentinel does NOT suppress alerts based on inferred financial capacity. `capital_constraint_active` in `client_config` re-ranks Agent C action suggestions only — spend-increase actions demoted, not removed. Alert always fires. Founder always sees all options. Suppressing a correct alert because the system inferred the founder couldn't fund it causes invisible harm and is worse than an unactionable alert.

**Attribution model and window — CLOSED for onboarding design, May 21 2026:** Full attribution model flexibility offered at onboarding across six models plus custom weights. Default: time decay, 14-day window. Default window of 14 days is a working assumption pending validation across remaining discovery interviews — if consistent founder data suggests a different default, update `client_config` default value only; the onboarding question and option set are locked. See Section 5 for full rationale.

**Suppressed-leak weekly digest — CLOSED as a position 2026-06-02 (build sequenced to Gap 8 + Gap 9):** When a driver is suppressed (e.g. a seasonal CPM spike graded State 3, or an expected return-rate level from a high-return category), the suppressed magnitude is not discarded — it is surfaced to the founder in a periodic (weekly) digest that shows the **magnitude and the plain-English reason**, never the internal suppression mechanics or rule IDs, and gated by suppression confidence (a low-confidence suppression is not asserted to the founder as "expected"). The resolved position is that "suppressed" must never mean "invisible." This is distinct from — and complementary to — the still-open "explained ≠ can't act" question in the Still Open subsection below: that question is whether an *individual* suppressed driver surfaces an inline action; this digest is the separate mechanism for showing the running *magnitude* of what was suppressed. Build is sequenced, not open: the surfacing logic is inherited by D1 Gap 8, and the $-impact display is part of Gap 9. See cross_alert_orchestration.md O-19.

**Category intelligence — Phase 1 vs Phase 2 sequencing — CLOSED 2026-06-02:** Internal AI clustering is used NOW (Phase 1) to group SKUs into categories for D1's internal grouping — no founder rename required, with a clustering-quality gate deciding per-brand whether category-level diagnosis is reliable or D1 falls back to brand-level-with-disclosure (see technical_architecture.md). DEFERRED to the multi-client / Fashion Intelligence Network phase (Phase 2): confident classification of a genuinely NEW category, and sub-category depth. Single-brand data cannot reliably name or validate a new-category split or a fine sub-category taxonomy — that requires cross-client pattern accumulation. The resolved position: cluster internally now; defer confident new-category naming and sub-category granularity to the network phase.

### Deferred to Post-Pilot
- Full licensing enforcement (query user tracking in client_config added later)
- Agency command centre UI
- Action Layer (auto-pause ads, update Shopify tags)
- Benchmark comparisons (need 20+ clients in same subcategory for statistical validity)
- Supply chain connectors (fragmented market, no dominant tool at $2M–$10M GMV tier; Shopify inventory API covers critical stockout signal without external connector; dedicated supply chain connectors relevant at Strategic tier only)
- D4 Fulfilment Cost Anomaly (deferred Phase 2 — Shopify fulfillment API does not contain 3PL billing data; cannot fire reliably without a 3PL connector; 3PL connector strategy undefined)
- Finaloop API connector (deferred indefinitely — Finaloop has no public API as of May 2026; monitor quarterly; CSV export path is the only available integration)
- 3PL connector of any kind (deferred Phase 2 — market fragmented across ShipBob, ShipMonk, Whiplash, custom 3PLs; no dominant connector at this GMV tier)
- Recharge subscription connector
- BNPL connectors (Affirm, Afterpay, Klarna)
- EU geographic expansion (GDPR compliance, EU data residency node)
- Middle East expansion
- **Shopify notification layer with agree/disagree/snooze feedback loop** *(deferred May 21 2026 — Shopify's native notification API has limited interactivity; may require in-app notification surface within Shopify app to get feedback clicks reliably. Validate API capabilities before committing to architecture. Email alerts remain primary delivery in Phase 1. The feedback loop — agree/disagree signals calibrating per-account alert thresholds — is a core intelligence mechanism; worth building correctly rather than quickly.)*

**Gorgias NLP parser as core infrastructure, and the text-signal action posture — CLOSED as positions 2026-06-04 (from D1 Gap 6 discount-depth/S19):** (1) The Gorgias text parser is NOT Horizon-2 — multiple alerts rest on Gorgias text (sizing-complaint velocity, return-reason context, the retrospective sale review, the sale-period channel), and ticket tagging is unreliable at this tier and worst during sales (stretched support, resolution-time KPI), so the parser — read the customer's own words, not the tags — is upstream core infra, built pre-beta. This is the answer to the long-standing Gorgias tag-consistency concern for Alert 5 (parse text rather than trust tags), though the complaint→return lag assumption and whether tickets exist at usable volume remain discovery questions (see Assumptions and the Alert-5 open decision in Section 3). (2) For text-derived / qualitative signals the alert's action layer is "summarise faithfully + link to the source tickets," NOT a recommended founder action — the right action depends on context we don't hold (margin, inventory, positioning) and can't verify afterwards (the Amazon-review-summary model). Decided CASE-BY-CASE per signal against a consistent test — can we ground the action in data we hold AND verify whether acting worked — and explicitly NOT generalised across the product by fiat. See cross_alert_orchestration.md O-27 and technical_architecture.md 2026-06-04 appendix.

### Still Open — Do Not Resolve Without New Evidence
- **Paid-media baseline structural-break alert (agency change)** *(added 2026-05-31 — when an unprecedented, sustained, above-seasonal-norm shift in paid-media baselines is observed, surface the cost reality plus a question: "did something change on the media side — new agency, in-housed, restructure?" NOT agency detection; we never assert a change. NOT asked at onboarding (agencies churn). Founder-declared resolution primary; data-derived campaign-structure churn may prompt the question but never triggers a silent auto-reset. Reuses the Jan-12-2026 structural-break mechanism. Surface-ownership across paid-media alerts is a cross-alert orchestration item — see cross_alert_orchestration.md Cluster 2.)*
- **Alert library canon reconciliation — E5/E6 (and any other non-Section-3D alerts)** *(added 2026-05-31 — E5 Deliverability Risk and E6 Klaviyo Revenue Seasonality exist in the seed-decision files with live suppression dependencies (E5 suppresses E1, D5 per S35; E5 is a critical/immediate-delivery alert per S34) but are absent from the Section 3D 41-type library, which lists only E1–E4. Reconcile: add to the library or align the seed files. E5 cannot be silently dropped — it has dependents. See cross_alert_orchestration.md P2-FINDING 4.)*
- **Alert-numbering namespace convention** *(added 2026-05-31 — at least three colliding namespaces use the same labels: Section 3D alert IDs (A1=Post-Return ROAS), gap_abc_decisions.md seed *design decisions* (A1=BFCM Suppression Corrected), and seed-file extended numbering. "Check A6" is ambiguous across three meanings — a retrieval-error risk. Adopt a convention (e.g. ALERT-A6 / DEC-A6 / S-rule) in the consolidated doc pass. See cross_alert_orchestration.md P2-FINDING 5.)*
- **Seasonal explanation vs. actionability ("explained ≠ can't act")** *(added 2026-05-31 from D1 Gap 4 — the suppression model (S38) goes quiet when a metric move is "explained away" by a calendar event, e.g. a BFCM CPM spike. But "explained" is not the same as "nothing to do": a seasonal CPM spike can still be actionable ("you're overspending into inflated ad prices; pull back"). D1 currently keeps the SKU-level spend-misallocation finding alive even under State-3 seasonal suppression, but the general question — should a seasonal-suppressed driver still surface an action — is unresolved. Inherited as a design input by D1 Gap 8 (no action named per driver). Product question, not only engineering. See agent_d_build_spec.md "GAP 4 — D1 CPM DIAGNOSIS CHAIN", Step 2. **UPDATED 2026-06-01 (D1 Gap 5 close):** the founder-driven category (ASP) shift case is confirmed to live HERE under this decision, not in Gap 5. The margin-weighted mix-shift driver already stays silent on margin-neutral ASP shifts; the case that genuinely compresses CM% is a founder-intended shift to a lower-margin category, which Gap 8 must decide (suppress vs fire-with-context). Gap 8 inherits three items logged at the Gap 5 close: a suppression hole (mix-shift checks promotion-driven but not spend-reallocation-driven shifts), a founder-vs-organic discriminator (spend-by-category / revenue-by-category co-movement), and a materiality floor. See agent_d_build_spec.md "GAP 5 — AOV DECLINE: RETIRED AS A D1 DRIVER" and cross_alert_orchestration.md O-19.)*
- Exact Slack bot framework version and deployment platform
- Whether GA4 uses server-side tracking (Littledata) or client-side GTM for real clients
- Exact format of the Python CLI confirmation flow for testing
- Whether to use Railway or Vercel for agent hosting in production
- Sentry instrumentation requirement — mandatory or advisory during onboarding
- Promotion threshold values — exactly how many validated instances (per-client and cross-network) are required before a candidate signal promotes to a validated alert type
- Dismissal reason threshold — at what ratio of `capacity_constrained` dismissals does the system flag that a founder may be systematically unable to act on a category of alerts
- **Shopify-native vs. web app as primary delivery surface** *(added May 21 2026 — MOS confirmed Shopify app store preference; one data point, not a pattern. Decision threshold: 6+ of 10 interviews. Risk: Shopify app store visibility accelerates competitive discovery; web app risks lower adoption. Monitor every subsequent interview.)*
- **Attribution window default (14 days)** *(added May 21 2026 — working assumption based on MOS founder's stated 15-day window. Single data point. Validate explicitly in remaining 9 discovery interviews.)*
- **Returns intelligence build priority within Phase 1 sequence** *(added May 21 2026 — serial offenders, SKU-level and channel-level return rate confirmed buildable from existing connectors. Exact sequence position not yet determined. Add to technical_architecture.md build sequence discussion.)*
- **Size-guide / photography change detection — narrate-don't-suppress, Tier-1 auto-detect to be built without discovery** *(added 2026-06-03 from D1 Gap 6 Seam 2. Decided: build the Tier-1 auto-detect path [silent onboarding probe → if the size chart is a Shopify metaobject, subscribe to its update webhook; content-diff for meaningfulness; otherwise narrate on return movement], since discovery interviews are not available. Default posture is narrate-with-context, never silent suppression, because the change-event source is unreliable across the segment; silent quiet is earned only by reliable detection or founder confirmation. Window = brand return window, not a fixed 14/21 days. Affected-line scope deferred to a batched schema column. See agent_d_build_spec.md GAP 6 Seam 2.)*
- **COGS / supplier-cost handling — scoped to trustworthy-cost-feed brands** *(added 2026-06-03 from D1 Gap 6 COGS. Decided: the supplier-cost-increase driver and any margin figure are feed-only — detectable only for brands with a trustworthy cost feed [well-maintained Finaloop/CSV/Shopify cost]; structurally invisible otherwise, because the other four margin drivers are visible while COGS is held at a stale/assumed value. 60-day window retired → per-product sell-through. Cost basis captured once at onboarding [Shopify-cost confirmation, CSV for gaps, ping permission, founder's own refresh rhythm]; updates requested proactively, never via a reactive alert; new-SKU-missing-cost is the reliable nudge. Staleness-decay narrows claims as cost ages [full figures → caveat → no figure], keyed to the founder's stated rhythm. Disclosure is state-driven, not a per-alert footnote. Dedicated COGS connector DEFERRED [discovery-gated]: no single clean source at this tier, and approximate auto-COGS is more dangerous than honest manual COGS. See agent_d_build_spec.md GAP 6 COGS.)*
- **WORKING ASSUMPTION (adopted 2026-06-08, Gap 6 residual pass) — Gap 1 "driver-only" tightened to "component-only" for no-trustworthy-COGS brands** *(originally a flagged proposal added 2026-06-03 from D1 Gap 6 COGS. Gap 1 [Closed Decisions] gives brands without reliable cost a driver-only margin alert. Tightening: such brands get NO margin verdict at all — only the component signals that need no cost [returns / CPM / discounting] — because a margin verdict implies a computed margin we cannot defend without trustworthy cost. ADOPTED 2026-06-08 as the working assumption for the residual pass: such brands do not enter the residual machinery at all. This still amends a LOCKED decision, so formal sign-off is deferred to the D1 alert-language stage; enforcement is gate D1-G9 [no margin figure without a trustworthy cost feed]. Not yet a locked amendment to Gap 1.)*
- **Operational cost / fulfilment — scoped feed-only** *(added 2026-06-08 from D1 Gap 6 operational-cost/S20. Decided: operational cost is a margin component but feed-only — carrier/3PL fulfilment cost lives on the 3PL invoice [not connected in beta] and Shopify shows only the customer-facing shipping charge, not the brand's cost. We make NO operational-cost change-verdict without a real cost-side feed, and never estimate it from weight×zone [confident-wrong, same posture as COGS]. The founder-stated fulfilment figure is a static baseline only. Known 3PL transitions are narrated via the shared known-events layer. The estimated fulfilment driver inside D1 is retired; a future cost-side detector is one uniform feed-agnostic build [3PL invoice or Shopify shipping label], Horizon-2. See agent_d_build_spec.md operational-cost/S20 lock + cross_alert_orchestration.md.)*

- **Loop vs Shopify-native returns split across the ICP** *(added 2026-06-04 from D1 Gap 6 — Shopify's native returns have matured [admin returns, returnless refunds, self-serve, native exchanges] and the new Shopify Returns API now carries returns/reasons/exchanges natively, so returns ingestion is built Shopify-primary with the Loop API as enrichment. How many target brands run Loop vs native-only sets how much of the richer exchange / Shop-Now enrichment we can rely on. Not a blocker [the Shopify surface covers the baseline either way], but a clean discovery question. Shopify is NOT replacing Loop — Loop is the management/exchange-conversion layer on Shopify's rails — but the threshold at which a brand needs Loop is rising. See technical_architecture.md 2026-06-04 appendix.)*

### Assumptions Not Yet Validated by Customer Discovery
- Founders will act on proactive AI alerts before they can see the problem themselves
- Gorgias tagging is consistent enough across target segment for sentiment signal to work
- The 8–14 day causal lag between Gorgias complaints and return spikes holds for most fashion brands
- $299/month price point is the right entry (may be too low or too high depending on perceived value)
- Slack is the right delivery channel (not email, not mobile app, not Shopify admin)
- Founders not currently satisfied with Sidekick Pulse will actively seek cross-source analytics (added May 2026)
- Alert delivery timing optimisation — that holding non-critical alerts for high-attention windows improves action rate vs. immediate delivery
- Dismissed alert outcome follow-up — that surfacing "you dismissed this and it was correct" builds trust rather than creating friction
- **Finaloop adoption rate in ICP** *(added May 2026 — assumed to be significant based on Blueprint language "rapidly becoming de facto" but completely unvalidated. If fewer than 5 of 10 discovery interviews confirm Finaloop use, Tier 0 and Tier 3 are the primary COGS paths in beta and full margin alerts will not fire for most clients. Add "What do you use for bookkeeping — Finaloop, QuickBooks, Xero, or something else?" to discovery interview Section 4 tool stack immediately.)*
- **Landed cost multiplier default of 1.28 is representative** *(added May 2026 — 1.28 is an assumption covering freight, duties, and fulfilment. Real multiplier varies significantly by sourcing country, shipping method, and 3PL contract. Validate against first 3 beta client actual landed costs before treating as reliable.)*
- **14-day attribution window is the right default for fashion DTC** *(added May 21 2026 — based on one founder's stated purchase consideration window. May vary by brand price point, channel mix, product category.)*
- **Shopify app store is the preferred delivery surface for the target segment** *(added May 21 2026 — confirmed by one founder. Not yet a validated pattern.)*
- **Attribution model flexibility at onboarding improves trust without increasing abandonment** *(added May 21 2026 — assumed. Not tested. If onboarding completion rate drops materially when attribution questions are present, consider moving to post-onboarding settings.)*
- **Returns analytics depth (serial offenders, SKU-level, channel-level) is valued by founders beyond basic return rate** *(added May 21 2026 — MOS confirmed strong interest. Requires validation across remaining interviews.)*
- **Share of target segment that stores size guides as Shopify metaobjects** *(added 2026-06-03 — decides how often the Tier-1 size-guide auto-detect path actually applies vs the narrate-on-return-movement fallback. Metaobject = reliable update webhook + possible affected-scope; Page/theme/app = no clean signal. The build degrades gracefully either way [each brand self-selects into the path that works], so this is not a blocker — but the fraction determines how much value Tier-1 delivers. A clean thing to check in discovery if interviews become available.)*

---

## 13. The Non-Negotiable Design Principles

1. **Trust before intelligence.** Numbers must be validated and trusted before any alert fires.

2. **Cross-source explanation, not detection.** Founders know something is wrong. We tell them why across sources they cannot join manually.

3. **Show the working.** Every metric has a "Show me the maths" drill-down. Every alert has verifiable raw numbers in Layer 2. Transparency is the trust mechanism.

4. **No dead ends in onboarding.** Every gap type has a resolution path. Every resolution path has a fallback. Missing connectors become waitlist entries not error states.

5. **Slack is the complete interaction surface.** Not a notification channel. Operational interaction — alerts, follow-ups, queries, approvals — all happen in Slack. Web app is configuration and audit only.

6. **Agent A never calls Claude.** Threshold scanning is pure Python. No LLM calls in the hot path. Claude is called only for natural language formatting and conversational responses.

7. **Data quality gates before inference.** No confident wrong statement. Signal-level DQ scores determine whether alerts fire, fire with caveat, or are suppressed and replaced with fix guidance.

8. **Cross-source moment visible by minute 10.** Onboarding must produce a cross-source insight that Shopify Sidekick cannot replicate before the founder has completed setup. This is a product requirement enforced at the onboarding architecture level. (Added May 2026.)

9. **Alert precision over alert volume.** The 41 validated alert types are the floor, not the ceiling. The self-extending graph adds new alert types only after per-client and cross-network validation thresholds are met. A new alert type that fires without validated causal chain is a rule engine output, not intelligence. Never add alert types to increase product comprehensiveness — add them because real outcome data validated a new causal chain.

10. **Intellectual honesty in every alert.** Agent D communicates uncertainty in plain English on every alert — not just a confidence score number. A founder who sees the system acknowledge what it doesn't know trusts the system more than one that always projects false certainty. The Evidence Stack is a trust mechanism; pre-fire uncertainty communication is how that trust is earned alert by alert.
