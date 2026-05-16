# Profit Sentinel — Product Strategy
*Version: Post-competitive reassessment | Status: Pre-customer discovery*
*Last updated: May 2026 — Sections 8, 11, 12 revised. All other sections unchanged.*

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
- Shopify-native fashion or apparel brand
- $2M–$10M GMV
- US-based
- Running paid ads on Meta AND TikTok (both required)
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

**The sweet spot:** A $4M DTC fashion brand with 2-3 people running operations, spending $15-25K/month on Meta and TikTok, using all 4-5 connectors in Phase 1 stack, experiencing ROAS volatility they cannot diagnose.

---

## 3. The Five Proactive Alerts

**Design principle:** For sub-$5M brands, the value is NOT detection — founders already know something is wrong. The value is cross-source EXPLANATION across data they cannot join manually.

### Alert 1: True Post-Return ROAS by Channel
**Sources:** Shopify + Meta + TikTok

"Your Meta ROAS shows 3.2 but your true post-return ROAS is 2.1 — 34% of Meta-attributed orders were returned. Your TikTok post-return ROAS is 2.6. TikTok is your more profitable channel right now."

*Why this is new information:* Founders see channel ROAS in each platform separately. They cannot see post-return blended ROAS across channels without joining Shopify returns with Meta and TikTok attribution data at order level.

### Alert 2: Root Cause of ROAS Drop Already Noticed
**Sources:** Meta + Shopify

"Your ROAS dropped this week. The cause is not CPM — CPM is flat. The Summer Linen campaign is driving customers who return at 41% vs your 18% average, wiping out the apparent ROAS."

*Why this is new information:* They know ROAS dropped. They do not know which specific campaign is driving low-quality customers. Requires joining Meta campaign attribution with Shopify return cohorts at order level.

### Alert 3: Influencer ROI Truth
**Sources:** TikTok + Shopify + refunds

"You paid $2,400 for @influencer_x. Attributed revenue was $8,200 — looks great. But 52% of those orders were returned, making true net revenue $3,936 and true ROI negative after the fee."

*Why this is new information:* Surface attribution looks profitable. Return-adjusted ROI by creator requires joining TikTok attribution with Shopify refund data at order level plus creator fee data.

### Alert 4: Contribution Margin Compression with Causal Driver
**Sources:** Shopify + Meta + TikTok

"Contribution margin dropped from 31% last month to 24% this week. The gap is entirely explained by Meta CPM rising 28% while your prices stayed flat."

*Why this is new information:* Founders see revenue. They may see ROAS. They do not see contribution margin trend with the causal driver identified automatically across sources.

### Alert 5: Sizing Complaint Velocity Predicting Return Spike
**Sources:** Gorgias + Shopify

"Gorgias tickets mentioning 'runs small' for your New Season Denim rose from 3% to 18% of tickets in 7 days. Historically for your account this precedes a return spike by 8-12 days. Add a sizing note to the product page now — before the returns hit."

*Why this is new information:* Founders read individual support tickets. They do not see velocity of complaint categories aggregated and correlated to future return spikes. Requires Gorgias + Shopify + time-series analysis.

---

## 3A. Alert Library

*Section added post-seed design session (Gaps A–G, 2026-05-16). The five core alerts in Section 3 are unchanged — they remain the product's flagship signals. This section documents the complete alert library across all groups. The original estimate was 41 alert types; the seed design session expanded the H-series from H1–H5 to H1–H19, bringing the confirmed total to 56 alert types.*

---

### Part 1 — Full Alert Library (56 alert types)

**Category key:** HA = High-Actionability | MW = Monitor-and-Wait | DO = Diagnostic-Only

#### Group A — Attribution and ROAS (A1–A6)

| ID | Alert Name | Sources Required | Category | Description |
|----|------------|-----------------|----------|-------------|
| A1 | True post-return ROAS by channel | Shopify + Meta + TikTok + Loop Returns | HA | Calculates true post-return ROAS per channel vs platform-reported ROAS; joins Shopify returns with Meta and TikTok attribution at order level — the first accurate cross-channel ROAS most founders have seen |
| A2 | Root cause of ROAS drop already noticed | Meta + Shopify + GA4 + Sentry | HA | Identifies the specific campaign or creative driving low-quality customers when overall ROAS drops; joins Meta campaign attribution with Shopify return cohorts at order level |
| A3 | Channel ROAS ranking reversal | Meta + TikTok + Shopify | HA | Detects when TikTok post-return ROAS overtakes Meta and signals budget reallocation opportunity with estimated blended ROAS improvement |
| A4 | Attribution window mismatch distorting decisions | Meta + TikTok + Shopify | DO | Fires when different attribution windows across platforms produce conflicting ROAS figures; cause is structural to how platforms report — no internal resolution path |
| A5 | Klaviyo double-attribution inflating reported revenue | Klaviyo + Shopify + Meta + TikTok | DO | Detects during collection launches when Klaviyo flow revenue overlaps with paid channel attribution on same orders; 65–75% overlap rate during launch windows is structural |
| A6 | New customer vs returning customer ROAS split | Shopify + Klaviyo | HA | Calculates ROAS separately for new and returning customer cohorts using Shopify customer_id cohort analysis; reveals true acquisition efficiency independent of attribution model |

#### Group B — Creative and Campaign Performance (B1–B5)

| ID | Alert Name | Sources Required | Category | Description |
|----|------------|-----------------|----------|-------------|
| B1 | Creative fatigue on primary ad set | Meta + TikTok | HA | Fires when ad frequency exceeds threshold and CTR declines, indicating creative rotation required within 15 minutes of ad set review |
| B2 | Ad set spending into wrong audience segment | Meta + Shopify | HA | Detects when an ad set's converting customers have characteristics misaligned with the intended audience targeting |
| B3 | TikTok organic-to-paid conversion gap | TikTok + Shopify | MW | Measures gap between organic content reach and paid spend performance; signal requires a full content cycle to confirm before action is warranted |
| B4 | UGC vs brand creative performance divergence | Meta + TikTok | MW | Tracks relative performance of UGC vs brand-produced creative across channels; monitored until a statistically significant divergence emerges |
| B5 | Campaign launch CPM spike eating new collection margin | Meta + TikTok + Shopify | MW | Detects CPM inflation at collection launch compressing contribution margin; monitored until spike persists beyond expected launch-period window |

#### Group C — Return Rate and Product Quality (C1–C7)

| ID | Alert Name | Sources Required | Category | Description |
|----|------------|-----------------|----------|-------------|
| C1 | Sizing complaint velocity predicting return spike (Alert 5 — CORE) | Gorgias + Loop Returns + Shopify | HA | **Three-stage warning chain.** Stage 1: Gorgias complaint velocity spike fires 8–12 days before returns hit (confidence: Medium). Stage 2: Loop return initiations confirm the signal (confidence: High). Stage 3: SKU-level return rate confirmed on receipt — outcome confirmation, not a new alert |
| C2 | Influencer ROI after returns (Alert 3 — CORE) | TikTok + Shopify + Loop Returns + Klaviyo | HA | **Two-stage alert per activation.** Stage 1 fires Day 7 post content-live with early ROI estimate and return window caveat. Stage 2 fires Day 21 with confirmed final ROI including returns, Cohort B clean attribution, and estimated 12-month Klaviyo downstream email value from activation list signups |
| C3 | SKU-level return rate outlier | Shopify + Loop Returns | HA | Detects individual SKUs with return rates significantly above catalogue baseline; fires at Stage 3 of the C1 warning chain and independently for non-sizing quality issues |
| C4 | New collection return rate above historical baseline | Shopify + Loop Returns + Gorgias | MW | Compares new collection return rate to prior collection at equivalent point in the sales cycle for the same product category; requires a full purchase-return cycle to confirm |
| C5 | Return rate by acquisition channel outlier | Shopify + Loop Returns + Meta + TikTok | MW | Identifies channels driving customers with structurally higher return rates; trend must hold over rolling 28-day window before action is warranted |
| C6 | Exchange rate vs refund rate on returns | Loop Returns + Shopify | MW | Tracks proportion of returns converting to exchanges vs full refunds as a product fit and sizing confidence signal |
| C7 | Post-return customer reactivation rate | Shopify + Klaviyo + Loop Returns | MW | Measures whether customers who returned items repurchase within 90 days, segmented by return reason, to evaluate post-return recovery flow effectiveness |

#### Group D — Margin and Contribution (D1–D6)

| ID | Alert Name | Sources Required | Category | Description |
|----|------------|-----------------|----------|-------------|
| D1 | Contribution margin compression with causal driver (Alert 4 — CORE) | Shopify + Meta + TikTok + sku_cost_master | HA | Decomposes margin compression into components (CPM, return rate, COGS, discount depth, operational cost) using component-level suppression — BFCM CPM pressure does not mask a simultaneous defective unit return spike |
| D2 | Discount dependency deepening | Shopify | MW | Tracks proportion of orders using discount codes over rolling period to detect structural discount reliance forming before it becomes a pricing-expectation problem |
| D3 | Hero SKU margin erosion from returns | Shopify + Loop Returns + sku_cost_master | HA | Calculates true contribution margin on top-revenue SKUs after returns and fulfilment costs using landed cost from sku_cost_master |
| D4 | Landed cost increase compressing margin | sku_cost_master + Shopify | MW | Detects when supplier cost increases logged in sku_cost_master are not yet reflected in pricing decisions, creating a margin compression that worsens over 60 days as old inventory sells through |
| D5 | Klaviyo flow revenue declining | Klaviyo + Shopify | MW | Fires when revenue per email sent (normalised for list size and send frequency) drops >20% below rolling 28-day average for >5 consecutive days; primary metric is revenue per email sent, not absolute flow revenue |
| D6 | AOV declining while order volume holds | Shopify | DO | Detects AOV decline without corresponding volume decline; cause is often external (BNPL product mix, wholesale absence, seasonal shift) with insufficient data for causal explanation from Shopify alone |

#### Group E — Customer and Retention (E1–E4)

| ID | Alert Name | Sources Required | Category | Description |
|----|------------|-----------------|----------|-------------|
| E1 | Email list health degradation | Klaviyo | MW | Fires when effective open rate (human opens only, correcting for Apple MPP machine opens at ~35% of reported opens) falls below threshold; click rate is the primary metric — clicks cannot be machine-generated |
| E2 | Repeat purchase rate declining by cohort | Shopify + Klaviyo + Loop Returns | MW | Tracks repeat purchase rate by acquisition cohort with BFCM discount cohort exclusion (S31) and new-customer surge denominator correction (S33); requires a full 90-day cohort maturation window |
| E3 | High-LTV customer segment going quiet | Shopify + Klaviyo | MW | Fires when the VIP segment (3+ orders or $450+ cumulative spend) shows declining engagement and purchase frequency over rolling window |
| E4 | New customer acquisition cost exceeding LTV payback window | Shopify + Meta + TikTok + Klaviyo | MW | Monitors CAC trajectory against estimated LTV payback window; fires monitor-and-wait at first breach, escalates to structural alert if unresolved at second firing |

#### Group F — Site and Checkout Health (F1–F5)

| ID | Alert Name | Sources Required | Category | Description |
|----|------------|-----------------|----------|-------------|
| F1 | Checkout conversion rate drop by device | GA4 + Shopify + Sentry | HA | Detects device-specific checkout conversion drops indicating a rendering or UX issue that can be diagnosed and fixed within 15 minutes of investigation |
| F2 | Payment gateway failure rate spike | Sentry + GA4 + Shopify | HA | Fastest-firing alert in the system — payment failure detected in Sentry before any revenue metric moves; immediately actionable via payment gateway dashboard |
| F3 | Product page bounce rate outlier on new collection | GA4 + Shopify | DO | Detects higher-than-expected bounce rate on collection pages; cause may be external demand suppression (unseasonably warm weather reducing FW interest, competitor activity) — no internal causal data available |
| F4 | Add-to-cart rate dropping while sessions hold | GA4 + Shopify | HA | Detects product discovery or page performance problems when sessions are stable but add-to-cart conversion falls; narrows to specific product pages or device types |
| F5 | Checkout abandonment spike on specific step | GA4 + Sentry | HA | Identifies which specific checkout step is driving the abandonment increase for targeted UX or technical intervention |

#### Group G — Inventory and Supply (G1–G4)

| ID | Alert Name | Sources Required | Category | Description |
|----|------------|-----------------|----------|-------------|
| G1 | Stockout on hero SKU during active ad spend | Shopify + Meta + TikTok | HA | Fires when inventory depletes to zero on SKUs with active ad spend; includes cost comparison of pausing spend vs continuing into stockout with estimated waitlist revenue upside |
| G2 | Overstock risk on slow-moving SKU | Shopify + Klaviyo + Meta | MW | Fires when sell-through velocity indicates excess inventory risk before the markdown decision window closes; excludes carry-forward inventory tagged `inventory_type = 'carry_forward'` (S28) |
| G3 | New collection sell-through velocity below prior season | Shopify | MW | Compares new collection sell-through rate at equivalent points in the sales cycle vs prior season baseline for the same product category |
| G4 | Back-in-stock Klaviyo flow not triggering | Shopify + Klaviyo | HA | Detects when restocked SKUs with active Klaviyo back-in-stock waitlists are not triggering the notification flow; waitlist size predicts revenue opportunity quantified in alert |

#### Group H — Operational and Structural (H1–H19)

| ID | Alert Name | Sources Required | Category | Description |
|----|------------|-----------------|----------|-------------|
| H1 | Sync gap detected — alert reliability degraded | Airbyte metadata | DO | Fires when any source sync falls behind schedule; suppresses downstream business alerts affected by the data gap and communicates exactly which alerts are paused and when they will resume |
| H2 | DQ score below alert threshold on primary signal | Varies by affected alert | DO | Fires instead of a suppressed business alert; explains which data gap is preventing the alert from firing and what specific action would restore full alert coverage |
| H3 | Klaviyo-Shopify customer ID mismatch growing | Klaviyo + Shopify | MW | Tracks proportion of Klaviyo profiles unmatched to Shopify customers; fires when mismatch grows, reducing attribution confidence on A6, D5, E2, and E3 alerts |
| H4 | Profit Health Brief (daily scheduled summary) | All | MW | Daily scheduled summary of key metrics and active signals delivered at founder's configured morning brief time; not threshold-triggered |
| H5 | COGS coverage gap on active SKUs | sku_cost_master + Shopify | DO | Fires when active SKUs lack COGS data in sku_cost_master, suppressing D1 and D3 margin alerts until coverage is restored above 50% |
| H6 | Platform spend gap detected | Meta or TikTok | HA | Fires when spend drops >50% vs 7-day rolling average with no pause logged in brand_event_calendar; Layer 3 references prior disruption events (Y2 TikTok outage alert cites Y1 ban as precedent) |
| H7 | Loyalty-Klaviyo integration failure | Klaviyo + Shopify | HA | Fires when loyalty points sync failures are detected affecting customers; typically surfaces first as Gorgias loyalty_complaint ticket category before balance reconciliation catches it |
| H8 | Transactional email misconfigured as marketing | Klaviyo + Gorgias | HA | Fires when Gorgias tickets about missing order confirmations pattern-match Klaviyo unsubscribe events — the specific signal that transactional flows have been miscategorised as marketing flows |
| H9 | Duplicate Klaviyo profiles detected | Klaviyo | MW | Fires when duplicate profile count exceeds threshold, reducing email attribution accuracy on D5, E1, and E2; lists merge action required |
| H10 | Shopify CDN infrastructure event | GA4 + Sentry + Shopify | DO | Fires during confirmed Shopify platform-level events; suppresses F1, F2, F5 business alerts that would otherwise fire as false positives due to platform cause |
| H11 | Meta CAPI Event Match Quality degradation | Meta | HA | Fires when Meta Event Match Quality score drops below 7.0; action is to check email hashing consistency between Shopify and CAPI — recoverable within 24–48 hours |
| H12 | GA4 implementation validation gap | GA4 + Shopify | DO | Fires when GA4 purchase count deviates >5% from Shopify order count over a 7-day window; lists the specific missing event types causing the gap |
| H13 | Loop Returns-Shopify revenue reconciliation gap | Loop Returns + Shopify | DO | Fires when Loop refund total deviates >3% from Shopify refunds; action is to check Loop Returns-Shopify integration settings |
| H14 | Tag normalisation coverage below threshold | Gorgias | MW | Fires when >15% of Gorgias tickets have unmapped tags; lists the specific unmapped tags requiring addition to the tag_normalisation table — primary driver of Alert 5 false positives |
| H15 | Pipeline orchestration lag exceeded | Airbyte metadata | HA | Fires when any source sync exceeds 2× its scheduled interval; immediately caps confidence on all alerts dependent on that source at 70% and notifies founder of delivery delay |
| H16 | Schema change detected in source | Airbyte + source schemas | DO | Fires on any new, renamed, or removed column detected by schema_discovery.py; additive changes are informational, breaking changes list all affected alerts requiring manual review |
| H17 | Financial reconciliation gap detected | Meta billing + TikTok billing | DO | Fires when pipeline spend deviates from billing statement by >$1; identifies whether the gap is API rounding accumulation (informational — known Meta API behaviour) or missing records (requires action) |
| H18 | Alert retraction/revision required | Varies | HA | Fires when a DQ issue is discovered affecting data from an alert fired in the previous 24 hours; includes the original alert reference, a provisional revised value, and the estimated timeline for full accuracy |
| H19 | DQ improvement opportunity | All | DO | Proactive and scheduled (Month 1, Month 6, Month 12 of client onboarding); lists specific improvements with estimated DQ score gain and implementation time — never threshold-triggered |

---

### Part 2 — Three-Category Classification

All 56 alerts are assigned to one of three categories. The category determines firing conditions, Evidence Stack format, and Slack button options.

**1. HIGH-ACTIONABILITY**

Definition: Alert has a specific mechanism identified, a clear action the founder can take within 15 minutes, and a defined outcome to monitor.

Alerts in this category: A1, A2, A3, A6, B1, B2, C1, C2, C3, D1, D3, F1, F2, F4, F5, G1, G4, H6, H7, H8, H11, H15, H18

Evidence Stack format: Full five-layer stack delivered. Layer 4 includes a specific action and estimated outcome. Approve / Snooze 24h / Dismiss buttons always present.

**2. MONITOR-AND-WAIT**

Definition: Signal is moving but has not crossed the actionability threshold, or the cause requires a full purchase/return cycle to confirm. No immediate action exists but the trend is worth tracking.

Alerts in this category: B3, B4, B5, C4, C5, C6, C7, D2, D4, D5, E1, E2, E3, E4, G2, G3, H3, H4, H9, H14

Evidence Stack format: Layers 0–3 delivered. Layer 4 states: "No immediate action required — monitor [metric] in [timeframe]. We will alert again if [condition]." No Approve button — Snooze or Dismiss only.

**3. DIAGNOSTIC-ONLY**

Definition: Alert fires but a critical source to fully explain the cause is not connected, OR the cause is external (weather, competitor activity, platform change) and is not present in our data. Alert fires with an explicit "insufficient data for causal explanation" note and a path to improve coverage.

Alerts in this category: A4, A5, D6, F3, H1, H2, H5, H10, H12, H13, H16, H17, H19

Evidence Stack format: Layers 0–2 delivered. Layer 3 states: "No historical precedent available in current data." Layer 4 states the specific additional source or configuration required to upgrade this alert to High-Actionability. Confidence floor: 50%.

---

### Part 3 — Minimum Connector Requirements

An alert group only fires if all required connectors are active and meet their minimum DQ score threshold. If a required connector is missing or its DQ score falls below 50, the relevant H-series DQ alert fires instead.

| Alert Group | Required Connectors |
|-------------|---------------------|
| A — Attribution and ROAS | Shopify + Meta + TikTok + Loop Returns |
| B — Creative and Campaign | Meta + TikTok + Shopify |
| C — Returns and Quality | Shopify + Gorgias + Loop Returns |
| D — Margin and Contribution | Shopify + Meta + TikTok + sku_cost_master |
| E — Customer and Retention | Shopify + Klaviyo |
| F — Site and Checkout | GA4 + Sentry + Shopify |
| G — Inventory and Supply | Shopify + Klaviyo + Meta |
| H — Operational and Structural | Varies — Airbyte metadata + relevant source connector |

**Note on sku_cost_master:** There is no Finaloop Airbyte connector (no public API). COGS data enters via Finaloop CSV export → sku_cost_master table. Target coverage: 75% of active SKUs. Alerts D1 and D3 suppress and fire H5 when coverage falls below 50%.

---

### Part 4 — Confidence Score Floors

Every alert has a minimum confidence score below which it does not fire. Instead, the relevant H-series DQ alert fires. Minimum confidence floors:

- **High-Actionability alerts:** 60% minimum. Fires with explicit caveat in Layer 0 when confidence is 60–79%. Fires normally at 80%+.
- **Monitor-and-Wait alerts:** 70% minimum. Requires cleaner data before trend monitoring is statistically meaningful.
- **Diagnostic-Only alerts:** 50% minimum. Fires to flag data gaps even with poor DQ — its primary purpose is surfacing coverage problems, not causal explanation.

Confidence is calculated as a weighted average of source DQ scores. Each alert type has defined source weights summing to 1.0. Example for Alert A1 (True post-return ROAS by channel):

```
Shopify orders:       weight 0.40
Shopify refunds:      weight 0.25
Meta attribution:     weight 0.20
TikTok attribution:   weight 0.10
Loop Returns:         weight 0.05
```

Full source weight tables for all 56 alert types are defined in `docs/sessions/seed_decisions_gap_f_g.md` — Gap G (Weighted Confidence Calculation for All Alert Types section).

**Confidence gate rules (applied after weighted calculation):**

| Condition | Result |
|-----------|--------|
| Any single source DQ score = 0 | Overall confidence = 0. Alert suppressed. State 4. |
| Primary source (highest weight) DQ score < 50 | Cap overall confidence at 55% |
| Weighted confidence < 60% | Suppress alert. Fire relevant H-series DQ alert instead |
| Weighted confidence 60–79% | Fire with explicit confidence percentage shown in Layer 0 |
| Weighted confidence ≥ 80% | Fire at full confidence. No caveat required |

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
Founder sees something genuinely useful about their own business BEFORE being asked to configure anything.

### Five Components in Sequence

**Component 1 — Progressive Insight Generation (Minutes 0-20)**
Airbyte sync runs in background. dbt models trigger individually as tables land. Insights fire from minute 2 without waiting for full sync.
```
~2 min:  shopify_orders lands → "847 orders, busiest day March 3rd"
~4 min:  line_items lands → "Top 3 SKUs by revenue..."
~6 min:  refunds lands → "14.6% return rate, 3 SKUs drive 67% of returns"
~10 min: products lands → "Midnight Blue Dress has 31% return rate vs 12% average"
~18 min: Full sync → Complete 90-day Profit Audit fires
```
Each insight has explicit table dependencies — never fires on incomplete data.

**Critical onboarding requirement (added May 2026):** The cross-source moment must be visible by minute 10 — before the full audit fires. Specifically: a Meta CPM to Shopify return rate correlation that Shopify Sidekick cannot produce. This is the moment that distinguishes Profit Sentinel from Sidekick Pulse in the founder's mind. Do not bury this in the full audit.

**Component 2 — Source Attribution Model**
Before any validation, every Shopify order classified by originating system using source_name, app_id, tags. `has_dedicated_connector` flag on every order. Unknown app_ids trigger Shopify Partner API lookup.

**Component 3 — Three-Bucket Validation**
Validates metrics using Shopify's own published formula on raw transaction data. Works on all Shopify plans (no ShopifyQL required).

*Bucket 1 — Structural Gap (<0.5%):* Shopify's own fraud filtering. Accept and explain. No founder action.

*Bucket 2 — Segmentation Gap (any size):* Founder defines metric differently (B2B exclusions, shipping inclusion etc.). Automated diagnosis → one-click fix → client_config updated → dbt reruns. If automated fails: free text → Claude interprets → structured filter object → preview shown → applied on confirmation.

*Bucket 3 — Missing Connector Gap (any size):* Orders from systems not yet onboarded. Three options: Include as-is / Exclude from metrics / Add to connector waitlist. connector_waitlist table becomes product roadmap ranked by revenue at stake.

**Component 4 — Dynamic Semantic Confirmation (3-7 Questions)**
Always asked (3): shipping in revenue, exchange handling, alert sensitivity.
Conditional (up to 4 additional): gift card timing (if detected), B2B exclusion (if detected), POS inclusion (if detected), currency (if multi-currency detected).

Each answer writes directly to `client_config`. Pre-populated from data — founder confirms or adjusts.

**Component 5 — Go Live (30-60 minutes)**
1. Slack bot connection (one token paste, 5 minutes)
2. Sentinel Sensitivity — defaults from 90-day historical data (10 minutes)
3. Morning brief time preference (10 seconds)

### Resumable State
All onboarding progress in `onboarding_state` JSONB in `client_config`. Updated after every single step. Founder closes browser mid-onboarding → returns next day → resumes exactly where dropped off. Sync never reruns. Answers preserved.

### Historical Evidence Reconstruction (Pre-Build Validation)
Before committing to full build: find one real historical signal in a willing founder's data (CPM spike, return rate jump from 3-6 months ago). Reconstruct the Evidence Stack using their actual numbers — real CPM trajectory, real historical precedent from their account. Present it. Ask: "If you had received this message at the time, would you have acted on it?" If yes, proceed. If they wanted more information — note what's missing and add it before writing a line of code.

---

## 6. Four Durable Moats

### Moat 1 — Precision Profit Calendar (Build: Month 6)
**What:** Automatic business rhythm learning from 6-12 months of operational data. No founder input.

**How built technically:**
- Launch detection: weeks where orders spike >2 SD above 8-week rolling average
- Sale period detection: weeks where discount code usage >15% AND AOV drops >10%
- Return window detection: median lag between order date and refund date per launch
- Creative fatigue cycle: average days between Meta creative launches and frequency >3.0 or CTR -20%

**Switching cost:** Moving to a competitor means starting the calendar from zero. After 12 months the system knows this brand's business rhythm better than any new hire. Surfaced to founders at month 6 as a named discovery making the switching cost explicit and visible.

### Moat 2 — Fashion Intelligence Network (Build: Month 12)
**What:** Cross-client causal pattern validation — which chains are real vs spurious, validated across real operating decisions of 20+ fashion brands over 12+ months.

**How built technically:**
- Outcome logging from day one: every alert logs signal values at firing and target metric 7 and 14 days later
- `causal_pattern_validation` table: pattern_id, times_fired, times_outcome_confirmed, confirmation_rate, exception_conditions (anonymised cross-client)
- Evidence Stack Layer 3 evolution: "3 of 4 times in your account" → "3 of 4 in your account AND 71% of similar fashion brands in our network"

**Why competitors cannot replicate:** Requires same connector set + same vertical focus + same time + explicit outcome tracking per alert. A competitor starting at month 18 faces all four simultaneously. This is the flywheel that gets harder to replicate the longer it runs.

### Moat 3 — Founder Decision DNA (Build: Month 6)
**What:** Complete record of every recommendation, whether founder acted, what action, what outcome.

**How built technically:**
- Online tracking: every Approve/Snooze/Dismiss logged against alert_id in alert_log
- Offline tracking: Monday Slack message per open alert — "Did you take any action? [Yes] [No] [Not relevant]" — free text stored
- Shopify change detection: if recommendation says "add sizing note" and Shopify products API shows SKU description modified within 72 hours, infer action taken
- Outcome monitoring: target metric monitored 14 days regardless of action visibility

**Compounding effect:** After 12 months: "You have dismissed creative fatigue alerts 5 times. In 4 of those cases ROAS declined within 7 days. This is instance 6 — consider acting." No new tool has this history. Switching cost becomes tangible when made visible in the product.

### Moat 4 — Boutique Agency Intelligence Layer (Build: Month 12)
**What:** Cross-portfolio intelligence for boutique fashion-specialist agencies (10-30 brands). Not large generalist agencies — they are Triple Whale's territory.

**How built technically:**
- Agency command centre accumulates cross-brand operational patterns specific to their portfolio
- Portfolio intelligence: which causal patterns hold across their client mix, what CPM threshold applies to their portfolio style, which influencer tier produces lower-returning customers in their price band
- This intelligence lives nowhere else — requires Profit Sentinel's cross-brand data layer

**Institutional switching cost:** If agency moves to competitor, entire portfolio intelligence library disappears. 18 months of cross-portfolio validation lost. Agency with 20 brands on Profit Sentinel is not switching — the library is their competitive advantage.

**GTM note:** Target boutique fashion-specialist agencies 10-30 brands specifically. Pitch: "Cross-portfolio intelligence your current tools cannot produce, at lower total cost than per-brand pricing, delivered as a competitive advantage you can name to your clients."

---

## 7. Licensing Model

### Access Model
- All plans: Unlimited Slack members in alert channel, unlimited readers of morning brief and alerts, unlimited Approve/Snooze/Dismiss button actions
- What is limited: Active query generation (NL questions to agent), Slack conversational thread depth

### Three Tiers

**Growth — $299/month**
- Target: Brands under $2M GMV
- Connectors: Shopify + Meta + Klaviyo (3 sources)
- Query users: 2 designated (can @mention Sentinel and ask questions)
- Token budget: 500K tokens/month shared
- Alerts: Daily brief + 3 signal categories

**Scale — $799/month**
- Target: Brands $2M-$15M GMV
- Connectors: All Phase 1 (7 sources)
- Query users: 5 designated
- Token budget: 2M tokens/month shared
- Alerts: All alert types + benchmarks + 12-month history

**Strategic — $1,500+/month**
- Target: Omni-channel brands $5M+
- Connectors: All Phase 1 + Action Layer + Finaloop
- Query users: Unlimited
- Token budget: 5M tokens/month + fair use guardrail
- Extra: Auto-pause ads, update Shopify tags, agency command centre

### Query User Model (Not Per-Seat)
A query user is not a seat. It is a Slack user ID that can initiate new queries to the agent. Everyone else in the channel reads alerts and approves actions — they just cannot initiate new queries. Implementation: 20 lines of Slack Bolt code checking if incoming message user_id is in `query_user_slack_ids` array in client_config.

### Agency Tier — $2,500/month base
- 10 brands included at Scale tier
- Additional brands: $199/month each
- Portfolio command centre included
- Cross-portfolio intelligence unique to their client mix

### Token Cost Management
- Agent A runs as pure Python — zero LLM calls for threshold scanning
- Query result cache with 6-hour TTL (reduces token consumption 30-40%)
- Soft limits at 80% of budget (upgrade prompt, no hard cutoff)
- Scheduled autonomous functions never cut off — only founder-initiated queries subject to limits
- Fair use guardrail on Strategic tier: >10 queries/hour from same client triggers pause

---

## 8. Competitive Positioning
*Section updated May 2026 following competitive reassessment. Blueprint v8 Section 7 contains the full competitive landscape table and feature comparison matrix. This section covers positioning decisions and closed strategic choices.*

### The Competitive Window
The window to establish the Fashion Intelligence Network as a validated moat is 9–12 months, not the 18–24 months assumed in earlier versions. Moby 2 (Triple Whale, launched April 2026) has shipped proactive anomaly detection, Slack delivery, approval-gated autonomous budget actions, and threshold-based alert templates. Proactive alerting is now table stakes for any analytics product launching in 2026. The differentiator is the quality and specificity of what is detected and explained — not the existence of the detection mechanism.

### What Remains Defensible
Four claims survive competitive scrutiny and are the anchor for every sales conversation:

**Fashion Causal Graph with validated accuracy rates.** No competitor encodes fashion-vertical causal chains: sizing-curve reasoning, return-reason-to-margin-lag modelling, influencer-post-to-return-cohort attribution, fit-complaint NLP from Gorgias. The graph structure is replicable in 3–6 months. The validated accuracy rates per pattern per context, accumulated through time in the vertical with outcome tracking from day one, are not. This is the moat.

**Gorgias sentiment chain.** Triple Whale has no Gorgias connector. Polar has no Gorgias connector. Alert 5 — sizing complaint velocity predicting return spike 8–12 days before it hits the P&L — is structurally impossible in any competing tool today. Tag normalisation and brand-specific lag calibration require fashion-vertical domain work that generalist tools will not prioritise. Build and calibrate before competitors prioritise.

**Slack as complete interaction surface.** Triple Whale delivers summaries to Slack but does not do full conversational thread reasoning with persistent alert context. Polar has no Slack-primary posture. This is a UX moat with a 6–12 month window, not an IP moat.

**Price positioning under Triple Whale and Polar.** $299 Growth and $799 Scale tiers undercut where agent capabilities live in incumbents. This is an acquisition wedge, not a durable moat. Use it to reach 20 beta clients.

### What Has Been Dropped
The following claims have been removed from all Profit Sentinel materials:

- **Cultural architecture gap** — Triple Whale rebuilt their platform from the ground up around Moby 2. This claim is no longer accurate and must not appear in any investor or sales materials.
- **Proactive agent architecture as differentiator** — Both Triple Whale and Polar now deliver proactive agents. This is table stakes.
- **Cross-client benchmark network effect as a moat** — Competitors have more total data. Only a moat against new entrants smaller than Profit Sentinel.

### Shopify Sidekick — Closed Strategic Decision
*Decision closed May 2026: Build alongside Sidekick. Not inside it, not against it.*

**Rationale:** Sidekick Pulse (Shopify Winter 2026 Edition) proactively surfaces recommendations inside the Shopify admin for free. Sidekick App Extensions (developer preview) may eventually allow third-party data inside the Sidekick interface. The structural limitation today is Shopify-only data — Sidekick cannot join Meta, TikTok, Gorgias, and Shopify simultaneously. That is not a roadmap item Shopify can fix cheaply or quickly; it requires commercial partnerships with Meta and TikTok who have their own platform ambitions.

**What "alongside" means operationally:**
1. Onboarding must produce a visible cross-source moment by minute 10 — specifically a Meta CPM to Shopify return rate correlation — before the founder has time to wonder whether Sidekick is sufficient. This is a product requirement, not a marketing claim.
2. Slack positioning is the explicit alternative to Sidekick's admin-bound interface. Founders already in Slack for team operations do not want to investigate a profit signal inside the Shopify admin. "The complete interaction surface for your business, in Slack" is not anti-Sidekick messaging — it is a different workflow proposition that Sidekick structurally cannot match.
3. Monitor App Extensions developer preview quarterly. If Shopify enables genuine cross-source data inside Sidekick via third-party connectors, revisit the inside-Sidekick option at that point.

**What not to do:** Do not position against Sidekick explicitly. Positioning against a free native tool invites a response Shopify can make cheaply. Let cross-source causal explanation make Sidekick's Shopify-only scope self-evident to founders without saying it.

### vs Triple Whale (Primary Competitor)

**What Triple Whale Moby 2 can do (updated May 2026):**
- Proactive anomaly detection with Slack delivery
- Approval-gated autonomous budget actions (Meta, Google, TikTok, Pinterest)
- Threshold-based alert templates (Sentinel Sensitivity equivalent now live)
- Cross-platform analysis across Meta, Google, Klaviyo
- Post-return ROAS by channel (when asked)
- Conversational queries via Moby chat

**What Triple Whale cannot do:**
- Gorgias connector does not exist — sizing complaint velocity signal structurally unavailable
- Fashion-specific causal reasoning — generic across 60,000 brands in all verticals
- Brand-specific historical precedent in alerts — uses GMV benchmarks, not brand-own data
- Full Slack conversational thread reasoning with persistent alert context
- Cross-client validated causal accuracy rates per pattern per fashion context

**Honest window:** 9–12 months before Moby 2 closes most of the generic proactive alerting gap. Speed to 20 clients and Fashion Intelligence Network data accumulating is the only response that matters.

### vs Polar Analytics (Updated May 2026)
Polar now has a semantic layer applying an ecommerce ontology to all metric definitions, five named AI agents, anomaly flagging, and an MCP endpoint. Warehouse-native, 45+ connectors, 3,700+ merchants. Remaining gaps: no fashion vertical specificity, no Gorgias connector, pricing scales steeply above $5M GMV ($1,020/month at $6M GMV), agents are productivity tools not a single autonomous agent with fashion-specific reasoning, no Slack-primary interaction surface.

### vs Shopify Sidekick Pulse
Free, zero setup, native to every Shopify store. Shopify-data only — cannot join Meta, TikTok, Gorgias, Klaviyo simultaneously. No cross-source causal reasoning. No return-adjusted attribution. No fashion-specific signal chains. Founders will arrive at Profit Sentinel having already experienced Sidekick. Onboarding must immediately demonstrate value Sidekick cannot provide. See Sidekick decision above.

### vs Northbeam
Attribution-only scope. No operational signals. Enterprise pricing ($12K-$255K/year). Different buyer. Not direct competition for sub-$10M brands.

### vs Shopify Analytics Native
Free. Zero setup. But: no cross-channel data, no causal reasoning, no proactive alerts, no return RCA. Profit Sentinel uses Shopify's own numbers as the validated foundation then adds all intelligence Shopify lacks.

---

## 9. Phase 1 Connectors

| Connector | Key Signals | Coverage at Target Tier | Connection | Key DQ Issues |
|---|---|---|---|---|
| **Shopify** | Orders, returns, SKU data, inventory, COGS proxy | 100% | Airbyte native | Null source_name (8%), null shipping JSON (12%), sync outage gaps |
| **Meta Ads** | CPM trajectory, ROAS, creative frequency, ad set spend | 92% | Airbyte native | iOS modeled conversions, API vs UI reach mismatch, attribution window changes |
| **TikTok Ads** | Creator performance, Spark Ads ROAS, CPM | 78% | TikTok Marketing API | UTM stripping (100% → Direct in GA4), creator fee missing |
| **Klaviyo** | Flow revenue, unsubscribe rate, list health | 88% | Airbyte native | Duplicate profiles (12%), null campaign revenue (18%) |
| **Gorgias** | Sentiment tag velocity, complaint categories | 71% | Airbyte native | Inconsistent tags (25%), missing tags (30%), peak period tag drop |
| **GA4** | Checkout funnel, bounce rate, session quality | 95% | Custom Python | 20% order loss rate, UTM stripping, 72-hour delay |
| **Sentry** | Checkout error rate, JS errors, payment failures | 45% | Custom Python | Rate limiting during BFCM, stale instrumentation post theme-update |

**On Sentry (45% coverage):** Despite low coverage, non-negotiable in Phase 1. Provides single fastest-firing signal — a checkout JS error at 9am shows before any revenue metric moves. Onboarding checks for instrumentation and flags as required setup if missing.

**On GA4 and Sentry:** Both use conditional activation. Only activates if properly instrumented. Onboarding checks during sync. If not ready, flagged as setup action. GA4 checkout alerts use Shopify order volume as fallback signal if GA4 not instrumented.

---

## 10. Vertical Expansion Sequence

Governed by one principle: only enter verticals where causal graph transfer >70% and Shopify standardisation advantage holds.

| Vertical | Entry Month | Graph Transfer | Why | SOM at Maturity |
|---|---|---|---|---|
| Fashion US | Month 1 | — | Launch market | $11.1M ARR Year 3 |
| Beauty & Cosmetics | Month 18 | 82% | Near-identical stack. Shade/formula returns = sizing returns. Meta/TikTok dependent. | $10.1M ARR |
| Sports & Activewear | Month 24 | 74% | Similar influencer attribution complexity. High returns on sizing/fit. | $3.0M ARR |
| Home & Garden | Month 30 | 55% | Similar attribution but different seasonality. Pinterest significant. 6-month expansion not 3. | $2.4M ARR |
| Health & Supplements | Month 30 | 60% | Subscription-heavy (Recharge prerequisite). Churn not returns as primary leak. | $1.7M ARR |
| Pet Care | Month 36 | 50% | Lowest transfer. LTV decay not returns. Only after Health & Supplements. | $980K ARR |

**Grand total at maturity (all verticals, 3 geographies):**
- TAM: $1.85B
- SAM: $883.5M
- SOM: $32.7M ARR

---

## 11. Customer Discovery Framework
*Section fully revised May 2026. Previous version replaced. Competitive reality testing added. Sidekick detection added. Scoring rubric updated to 8 signals.*

### Objective
Validate or pivot the Profit Sentinel product hypothesis. Three possible outcomes:
1. Proceed — hypotheses validated, build as designed
2. Refine — core is right but specific elements need adjustment
3. Pivot — fundamental problem with core premise

### Target Profile for Interviews
- Shopify fashion founder or co-founder (not CMO, not analyst, not agency)
- $1M–$10M GMV, DTC-first, US-based
- Running Meta + TikTok
- Has at least Klaviyo and a customer support tool
- No full-time data analyst

### Interview Rules
- Read Section 3 scenario and Section 5 signals exactly as written. Do not paraphrase.
- Do not mention Profit Sentinel until the interview is complete.
- Stay neutral throughout. The only acceptable follow-up is: "That's interesting, tell me more."
- Record verbatim notes on Q3, Q11, and the Section 3 scenario response. These three answers matter more than everything else combined.
- Duration: 45–60 minutes.

---

### Section 1 — Decision-Making Reality
*Objective: Understand how founders actually diagnose problems today. No product mention.*

**Q1.** "Walk me through the last time something went wrong with your business — a ROAS drop, a return spike, a bad week. How did you find out something was wrong? How long after it started did you notice?"

*Listen for: lag time between signal and awareness, which platform they noticed it in first, whether they noticed it themselves or someone told them.*

**Q2.** "When you know something is wrong, what do you actually do to figure out why? Take me through your process step by step."

*Listen for: how many tabs they open, whether they join data manually, how long root cause takes, whether they give up before finding it.*

**Q3.** "Tell me about a decision in the last three months you later wished you'd made differently. What happened, and what information would have changed that decision at the time?"

*Most important question in the interview. Do not rush past it. The answer tells you what they actually value — not what they think you want to hear. Write it down verbatim.*

**Q4.** "When you get an alert or notification from any of your tools — Meta, Shopify, Klaviyo, anything — what do you actually do with it? Walk me through what happens."

*Listen for: alert fatigue, dismissal rate, whether they investigate or ignore, what would make them act versus ignore, whether they have been burned by a false positive.*

---

### Section 2 — Competitive Reality
*Objective: Understand what tools they already have and how well those tools are working. Detect Sidekick awareness and Triple Whale usage.*

**Q5.** "What analytics or reporting tools are you currently using to understand your business performance? How often do you look at them, and what do you actually use them for day-to-day?"

*Listen for: Triple Whale, Polar, native Shopify Analytics, GA4, agency dashboards. Note which they mention first — that is the one they actually use.*

**Q6.** "Have you come across Shopify Sidekick or Sidekick Pulse? If yes — have you used it, and what did you think?"

*Score the response:*
- *Unaware: note as baseline — Sidekick has not reached them yet*
- *Aware, not using: probe why not*
- *Using, satisfied: high Sidekick suppression risk — flag as potential disqualifying signal for early beta*
- *Using, unsatisfied: open door — probe what is missing and why*

**Q7.** "If I told you there was a tool that could tell you why your ROAS dropped — not just that it dropped, but the specific cause traced across your ad data, your Shopify returns, and your customer support tickets — would that be something you'd want? What would make you trust or distrust that answer?"

*Listen for: desire to verify numbers themselves, skepticism about AI accuracy, whether they ask how it works or just whether it works, trust signals (raw numbers, historical precedent from their own data).*

---

### Section 3 — The Scenario Test
*Objective: Test the core product hypothesis. Read exactly as written. Pause after reading. Let them answer fully before asking anything else.*

**Read this word for word:**

> "It's 8am Tuesday. You get a Slack message: 'Your Meta ROAS shows 3.2 this week but your true post-return ROAS is 2.1 — 34% of Meta-attributed orders were returned. Your TikTok post-return ROAS is 2.6. TikTok is your more profitable channel right now. Your CPM on the Midnight Blue Dress ad set has also risen 39% in 72 hours — Day 1 $18.40, Day 2 $21.20, Day 3 $25.60. This pattern preceded a ROAS decline 3 of 4 times in your account — most recently the week of October 14th when ROAS dropped from 3.4 to 2.1 within 6 days. Recommend reducing this ad set budget by 30% today.' What do you do?"

**After they respond fully, ask:** "What would make you more confident in that recommendation? What would make you ignore it?"

*Score response type:*
- *Type A — acts immediately: strong fit. Core early adopter.*
- *Type B — verifies then acts: medium-high fit. Evidence Stack addresses this.*
- *Type C — defers to their agency: medium fit. Note agency relationship strength. Agency channel opportunity.*
- *Type D — waits to see what happens: low fit. Needs to experience a preventable loss first.*

---

### Section 4 — Data Sources and Stack Reality
*Objective: Validate connector availability and data quality assumptions.*

**Q8.** "Which of these do you use? For each one, tell me how central it is to how you actually run the business."

*Read each one: Shopify, Meta Ads, TikTok Ads, Klaviyo, Gorgias, GA4, Loop Returns. Note which they use and how deeply.*

**Q9.** "For your customer support tool — do you tag or categorise tickets? For example, do you track how many complaints are about sizing, shipping, or product quality separately? How consistently does your team actually do that?"

*Critical question. If the answer is "not really" or "inconsistently," Alert 5 does not work for this founder regardless of what support tool they use. Note carefully and score it.*

**Q10.** "When something goes wrong in your business — a bad week, a spike in returns, a ROAS drop — what fires first? What is the first place you actually see it?"

*Listen for: Meta dashboard, Shopify dashboard, support inbox, agency report, bank account. The answer tells you which signal arrives earliest in their workflow and whether Profit Sentinel's early warning would actually be early for them.*

---

### Section 5 — Signal Validation
*Objective: Validate the five alerts against real founder pain. Get build priority from their ranking. Read each signal exactly as written.*

**Say this first:** "For each of the following, tell me: is this something you already know, something you could figure out but it takes time and effort, or something you genuinely cannot see today?"

**Signal 1:** "Your Meta ROAS shows 3.2 but your true post-return ROAS is 2.1 — because 34% of Meta-attributed orders were returned. Your TikTok post-return ROAS is 2.6. TikTok is actually your more profitable channel right now."

**Signal 2:** "Your ROAS dropped this week. The cause is not your CPM — CPM is flat. One specific campaign is driving customers who return at 41% versus your 18% average, and that's wiping out the apparent ROAS."

**Signal 3:** "You paid a specific amount for an influencer. The attributed revenue looked profitable. But 52% of those orders were returned, making the true ROI negative after the fee."

**Signal 4:** "Your contribution margin dropped from 31% last month to 24% this week. The entire gap is explained by Meta CPM rising 28% while your prices stayed flat."

**Signal 5:** "Support tickets mentioning sizing complaints for a specific product rose from 3% to 18% of tickets in 7 days. Historically for your account, this precedes a return spike by 8 to 12 days."

**After all five:** "If you could only have one of these five — the one that would have the biggest impact on your profitability right now — which one is it and why?"

*Their answer to this final question is your build priority order. Write it verbatim.*

---

### Section 6 — Pivot Detection
*Objective: Detect whether the product hypothesis is fundamentally wrong or needs refinement.*

**Q11.** "If I could give you one piece of information about your business that you don't currently have — just one — what would it be?"

*Most important signal in the entire discovery process. If 6+ founders give answers outside the five alerts, that is a pivot signal. Write it verbatim.*

**Q12.** "If a tool gave you the root cause of a profit problem — with the data proof — but you had to verify it yourself before acting, would you? Or would you need it to just tell you what to do and trust it?"

*Listen for: verification appetite (Evidence Stack users) versus recommendation appetite (Action Layer users). Both are valid customers but at different tiers.*

**Q13.** "Is there anything about how you currently run the business — how you make decisions, what tools you use, what your team looks like — that I should understand before we finish?"

*Open door for anything missed. Take whatever they give you.*

---

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
*Section updated May 2026. Two decisions closed since previous version.*

### Closed Decisions (Do Not Reopen Without New Evidence)

**Sidekick strategy — CLOSED May 2026:** Build alongside Sidekick. Not inside it, not against it. Full rationale in Section 8. Monitor App Extensions developer preview quarterly. Reopen only if Shopify enables genuine cross-source data via third-party connectors inside Sidekick.

**Geographic focus — CLOSED May 2026:** US Shopify fashion market only for Phase 1. All other geographies are Phase 2+. India was evaluated as a brainstorming exercise and not pursued. The US Gold Stack (Shopify + Meta + TikTok + Klaviyo + Gorgias) is the only market where all five alerts can fire at full strength. Non-US expansion follows US validation, not precedes it.

### Deferred to Post-Pilot
- Full licensing enforcement (query user tracking in client_config added later)
- Agency command centre UI
- Action Layer (auto-pause ads, update Shopify tags)
- Benchmark comparisons (need 20+ clients in same subcategory for statistical validity)
- Supply chain connectors (fragmented market, Shopify inventory covers critical signal)
- Recharge subscription connector
- BNPL connectors (Affirm, Afterpay, Klarna)
- EU geographic expansion (GDPR compliance, EU data residency node)
- Middle East expansion

### Still Open — Do Not Resolve Without New Evidence
- Exact Slack bot framework version and deployment platform
- Whether GA4 uses server-side tracking (Littledata) or client-side GTM for real clients
- Exact format of the Python CLI confirmation flow for testing
- Whether to use Railway or Vercel for agent hosting in production
- Sentry instrumentation requirement — mandatory or advisory during onboarding

### Assumptions Not Yet Validated by Customer Discovery
- Founders will act on proactive AI alerts before they can see the problem themselves
- Gorgias tagging is consistent enough across target segment for sentiment signal to work
- The 8–14 day causal lag between Gorgias complaints and return spikes holds for most fashion brands
- $299/month price point is the right entry (may be too low or too high depending on perceived value)
- Slack is the right delivery channel (not email, not mobile app, not Shopify admin)
- Founders not currently satisfied with Sidekick Pulse will actively seek cross-source analytics (added May 2026)

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
