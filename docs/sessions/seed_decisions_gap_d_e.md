# Profit Sentinel — Seed Script Design Decisions
## Gaps D and E — Complete and Confirmed
### Date: 2026-05-16

---

## IMPORTANT: HOW TO USE THIS FILE

This file works alongside `gap_abc_decisions.md` (Gap A, B, C decisions).
All three seed files (gap_abc_decisions.md, seed_decisions_gap_d_e.md, seed_decisions_gap_f_g.md), plus technical_architecture.md and product_strategy.md must be in context when writing the Claude Code seed prompt.
All decisions here are LOCKED — do not reopen without explicit instruction.

---

## GAP D — TIKTOK BAN DISRUPTION DATA SIGNATURE

### D1 — Correct Timeline (4 Phases, Not Smooth Curve)

```
Phase 1 — Hard Pause (Jan 13–19 2024, 7 days):
  Trigger: Senate Judiciary Committee hearing + credible ban vote
  TikTok paid spend: $0 (complete pause)
  New Spark Ad authorisations: frozen
  Existing Spark Ads: continue running (already authorised)
  Brand organic posting: drops from 4/week to 1/week
  Meta spend: unchanged (founder waiting to see outcome)
  Shopify direct traffic: +18% (TikTok users sharing links externally)

Phase 2 — Cautious Re-entry (Jan 20 – Feb 14 2024, 26 days):
  TikTok paid spend: 35% of December baseline
  New Spark Ad authorisations: resume slowly (creator hesitancy)
  Brand organic posting: 2/week
  Meta spend: +25% (budget partially reallocated)
  Meta enters learning phase: ROAS dips 12% for first 10 days
    then recovers to +8% above baseline by Feb 14

Phase 3 — False Recovery Interrupted (Feb 15 – Mar 12 2024):
  TikTok paid spend: 70% of December baseline
  House passes TikTok bill Mar 13 — spend pauses again 5 days
  Meta spend: normalises to +10% above December baseline

Phase 4 — Final Recovery (Mar 13 – Apr 30 2024):
  5-day pause then gradual restoration
  TikTok paid spend: 85% of December baseline by Apr 30
  Permanent shift: TikTok never returns to 100% of December baseline
  Settles at 88% permanently post-disruption
  Brand organic posting: returns to 3/week (never fully back to 4/week)
  TikTok account algorithm reach: -22% vs pre-disruption
    recovers gradually through May–June 2024
```

### D2 — Spark Ad Segmentation

```
Existing Spark Ads (authorised before Jan 13):
  Continue running throughout disruption
  Spend: ~$180/day (subset of total TikTok spend)
  Performance: stable

New Spark Ad authorisations:
  Jan 13 – Feb 10: Zero new authorisations
  Feb 11 – Mar 12: Partial (3 authorisations vs normal 8/month)
  Mar 13+: Normal pace resumes

tiktok_ad_performance must distinguish:
  campaign_type = 'spark_ad_existing' (continues)
  campaign_type = 'spark_ad_new' (frozen Jan 13 – Feb 10)
  campaign_type = 'in_feed_paid' (paused/reduced)
```

### D3 — Influencer Contract Impact (Connecting Gap C and Gap D)

```
Activation INF-2024-JAN-02 (mid-tier, Jan 20 content date):
  Content delayed to Feb 5
  Platform split: 50% TikTok + 50% Instagram Reels
  Fee paid December (COGS hit in December)
  Alert 3: diagnostic-only — attribution incomplete, content split

Activation INF-2024-FEB-01 (micro, Feb 1 content date):
  Spark Ad authorisation delayed 14 days
  Organic content only — no paid amplification for 2 weeks
  Alert 3: fires Day 21 with caveat

Activation INF-2024-MAR-02 (macro, originally Jan contract):
  Renegotiated to April 2024
  Partial fee refund ($9,000 of $18,000 returned)
  Layer 3 in Nov 2024 Alert 3: "No prior undisrupted macro 
  activation to compare — this is your first clean data point."
```

### D4 — Dark Social Surge During Disruption

```
January 15 – March 31 2024:
  Shopify direct traffic: +22% above baseline
  GA4 direct sessions: +19% above baseline
  Source: TikTok users sharing links externally
  Orders have TikTok-adjacent characteristics:
    Higher first-time customer proportion
    Product mix matches TikTok-featured SKUs
    Geographic distribution matches TikTok audience

Alert H2 fires: "Direct traffic rose 22% in January.
  Partial explanation: TikTok users sharing links externally
  during platform uncertainty. Do not interpret as
  organic search improvement."
```

### D5 — Organic Reach Deprioritisation Arc

```
TikTok organic brand account reach (indexed vs Dec 2023 = 100%):
  Jan 13–19 (hard pause, 1 post/week): 45%
  Jan 20 – Feb 14 (2 posts/week): 52%
  Feb 15 – Mar 31 (partial posting): 61%
  Apr 2024 (full posting resumed): 74%
  May 2024: 84%
  Jun 2024: 91%
  Jul 2024: 96% (never fully returns to 100%)

tiktok_organic_performance table needs:
  organic_reach_rate (normalised index vs baseline)
  posting_frequency (posts per week)
```

### D6 — Alert Interaction Map by Disruption Phase

```
Phase 1 (Jan 13–19, hard pause):
  Suppress: A3, B5, C3_tiktok, Alert3_tiktok
  Fire: H2 (DQ flag — TikTok data gap), H6 (spend dropped to zero)
  Monitor with caveat: A1 (incomplete data)

Phase 2 (Jan 20 – Feb 14, cautious re-entry):
  Suppress: A3 (still unreliable)
  Fire with caveat: A1 (confidence 55%)
  Fire: B1 (creative fatigue — Spark Ads running without rotation 5+ weeks)
  Fire: Alert 3 variant (influencer contract disruption)

Phase 3 (Feb 15 – Mar 12, false recovery):
  Fire with caveat: A3 (confidence 65%)
  Fire: B3 (TikTok organic-to-paid gap)
  Suppress: C3 on TikTok cohort (attribution unreliable)

Phase 4 Second Pause (Mar 13–19, House bill):
  Suppress: All TikTok alerts
  Fire: H2 again (second disruption event)
  brand_event_calendar entry: 'platform_disruption_v2'

Phase 4 Recovery (Apr 2024):
  All alerts resume normally
  A1 resumes full confidence
```

### D7 — 5 Granular brand_event_calendar Entries

```sql
-- Replace single 'platform_disruption Jan–Apr 2024' with:

1. 'TikTok Hard Pause', 'platform_disruption',
   2024-01-13 to 2024-01-19,
   suppress: ['A3','B5','C3_tiktok','Alert3_tiktok']

2. 'TikTok Cautious Re-entry', 'platform_disruption_partial',
   2024-01-20 to 2024-02-14,
   suppress: ['A3']

3. 'Meta Learning Phase Post-Reallocation', 'platform_disruption_secondary',
   2024-01-20 to 2024-01-30,
   suppress: ['A3_meta']

4. 'TikTok House Bill Second Pause', 'platform_disruption',
   2024-03-13 to 2024-03-19,
   suppress: ['A3','B5','C3_tiktok']

5. 'TikTok Organic Reach Recovery', 'platform_algorithm_change',
   2024-01-13 to 2024-06-30,
   suppress: ['B3']
```

### D8 — Permanent Post-Disruption Baseline Shift

```
Post-April 2024 permanent changes to Archetype A baseline:
  TikTok daily spend: $352/day (88% of pre-disruption $400/day)
  TikTok organic posting: 3/week (was 4/week)
  Budget allocation: Meta 72% / TikTok 13% / Other 15%
    (was Meta 70% / TikTok 15% / Other 15%)

These become the new System 2 baseline from May 2024 onward.
calibration_pass.py recalibration at Month 13–14 must detect shift.
```

### D9 — New Alert H6 — Platform Spend Gap Detected

```
Fires when: spend on connected ad platform drops >50% vs
  7-day rolling average with no corresponding pause logged
Message: "TikTok spend dropped to $0 today vs $412 daily
  average. No sale period or planned pause detected.
  If intentional, log a pause event to prevent false alerts.
  If unintentional, check TikTok Ads Manager."
Sources: tiktok_ad_performance
Confidence: High
Category: High-actionability
```

### D10 — TikTok Shop Decision

```
DECISION: Exclude TikTok Shop from Archetype A seed.
Archetype A at $150 AOV is premium — TikTok Shop skews toward
lower price points ($40–80 AOV).
Document exclusion explicitly in seed spec.
Reserve TikTok Shop for Archetype C (trend casualwear).
```

### D11 — DQ Scores by Disruption Phase

```
Jan 13–19:       tiktok_dq_score = 15 (critical — no data)
Jan 20–Feb 14:   tiktok_dq_score = 45 (poor — partial attribution)
Feb 15–Mar 12:   tiktok_dq_score = 62 (degraded — recovering)
Mar 13–19:       tiktok_dq_score = 20 (critical — second pause)
Mar 20–Apr 30:   tiktok_dq_score = 74 (fair — recovering)
May 2024+:       tiktok_dq_score = 88 (good — permanent baseline)
  Note: never returns to 95+ (organic reach never fully recovers)

DQ score gates:
  Below 50: Only H-type alerts fire. All business alerts suppressed.
  50–70: Business alerts fire with confidence cap at 60%.
  70–85: Business alerts fire with confidence cap at 75%.
  Above 85: Full confidence alerts.
```

### D12 — D13 — D20: Additional Gap D Decisions

```
D13 — Creator Ecosystem Structural Shift:
  Content exclusivity collapsed post-disruption — all mid/macro
  activations now cross-post TikTok + Instagram Reels + YouTube Shorts
  Fee step-change: +15–20% in February 2024 (not gradual)
  Content quality decline February–March 2024: CTR -15–20%
  Alert B4 fires: "UGC creative performance declined 18% vs Q4 2023"

  SEED IMPLICATION (missing from original):
  From January 2024 onward, all mid-tier and macro influencer activations
  must have a parallel Instagram Reels post on the same content_live_date.
  That Reels post generates Shopify sessions with:
    utm_source = 'instagram' (if creator used link in bio)
    OR direct traffic (if no link — most common)
  This revenue is real but attributed incorrectly — belongs to the
  influencer activation but appears in Instagram organic metrics.
  Alert 3 Layer 2 must detect this pattern:
  "Based on session spike on Instagram on same day as TikTok activation,
   estimated additional Instagram-attributed revenue: $X.
   Not captured in TikTok UTM attribution."
  Seed requirement: influencer_sub_calendar must include
    instagram_reels_posted boolean (true from Jan 2024 onward for mid/macro)
    instagram_reels_session_lift numeric (estimated sessions from Reels post)

D14 — Klaviyo List Composition Change:
  TikTok-influenced new subscribers drop from 35% to 8% of weekly signups
  during disruption (Jan 13 – Apr 30 2024)
  klaviyo_profiles needs acquisition_channel field
  Remaining subscribers have higher open rate, higher AOV, lower return rate
  Alert E1 improvement during disruption is composition change not genuine improvement

D15 — Inventory Purchasing Decision Problem:
  SS 2024 inventory ordered Sep–Oct 2023 based on TikTok demand projections
  TikTok disruption reduces demand for TikTok-resonant SS styles
  March–April 2024: SS inventory arrives, sell-through 30–40% below projection
  Alert G2 fires April 2024 on specific SS SKUs
  June 2024: early markdown on these SKUs (8 weeks early)
  Alert D1 fires June 2024 — 9-month causal chain:
  Sep 2023 PO → Jan 2024 disruption → Mar 2024 overstock → Jun 2024 markdown

  SPECIFIC SKU IDENTIFIERS FOR OVERSTOCK SCENARIO:
  TikTok-resonant SS 2024 styles affected (chosen for seed):
    AZ-TOP-088   — cropped graphic tee (TikTok-native aesthetic, low AOV $68)
    AZ-DRESS-094 — mini dress with trend print (viral-style, $128)
    AZ-SHORT-031 — cycle shorts (athleisure crossover, $82)
  These 3 SKUs: ordered 240 units each (720 total) based on TikTok demand forecast
  Actual sell-through by Apr 30 2024: 28–32% (vs 68% projected)
  Remaining inventory: ~165 units per SKU (~495 total)
  G2 alert fires Apr 15 2024 for all three simultaneously
  Markdown applied June 1 2024: 30% off (from full price)
  Markdown contribution margin on these SKUs: 14% (vs 31% full price)
  Alert D1 June 2024 Layer 3: traces to G2 from April → traces to TikTok disruption Jan 2024

D16 — Competitive Advantage Window:
  Jan 13–19: CPM 28% lower (competitors left auction)
  Seed Scenario A: brand paused (realistic for cautious $4M brand)
  Suppression log includes suppressed positive Alert A3
  Note: "Positive ROAS signal detected but suppressed — 
  platform disruption makes comparison unreliable."

D17 — Customer Trust Dimension:
  TikTok-influenced sessions during disruption: higher quality
  Add-to-cart rate: +18% (casual browsers stayed on TikTok)
  Email signup rate from TikTok-influenced sessions: +40%
  Alert A2 variant: "TikTok traffic volume 70% below baseline
  but quality improved — add-to-cart +18%, email signup +40%"

D18 — Y2 Echo Effect (January 19 2025):
  TikTok went dark for 14 hours (actual outage, not just threat)
  Faster recovery: spend restored to 80% within 48 hours
  No Spark Ad freeze (creators had backup authorisations ready)
  Alert H6 fires and references Y1 precedent — most powerful Layer 3 
  demonstration in entire seed dataset

  EMERGENCY KLAVIYO SEND — EXACT SEED PARAMETERS:
  Date: January 19 2025, 2:30pm EST (shortly after TikTok outage confirmed)
  Subject: "Shop our collection directly — [Brand Name]"
  Segment: full active list (18,000+ subscribers)
  Open rate: 38% (highest single send of Y2 — anomalously high)
  Click rate: 8.1% (3× normal campaign click rate)
  Revenue attributed: $12,400 in 24 hours
  Klaviyo send_type: 'campaign' (not a flow)
  This send is outside normal campaign cadence — appears as anomalous
  spike in daily send frequency metric
  Alert firing: D5 monitors flow revenue only, does not fire
  Alert A5 (double attribution) does not fire — no paid ads running during outage
  Unique identifier in klaviyo_email_events: campaign_name contains 'emergency'

D19 — Accounting Timing Difference:
  TikTok Ads wallet: prepay basis. $3,500 balance at disruption.
  Balance depletes over 35 days at reduced spend ($100/day).
  April 2024: large single top-up of $4,200 (timing difference, not cost increase)
  Alert D1 must not fire on this top-up
  tiktok_ad_performance tracks spend_cash vs spend_accrued separately

  EXACT SEED PARAMETERS:
  January 13: auto-recharge disabled. Wallet balance: $3,500.
  January 13 – February 16: wallet drawn down at ~$100/day (reduced spend)
  February 17: wallet balance = $0. Brand must decide whether to top up.
  Brand tops up $1,500 (cautious — not full pre-disruption level)
  April 3: full wallet top-up of $4,200 (confidence restored)
  April 3 entry in tiktok_ad_performance:
    spend_cash: $4,200 (cash left bank account)
    spend_accrued: $0 (no ads ran on April 3 — this is a prepayment)
  Calibration_pass.py must recognise wallet top-up pattern:
    single large spend_cash with spend_accrued = 0 = prepayment, not ad cost

D20 — Founder Psychological Over-Correction:
  Post-May 2024: Meta over-allocation at 72% (optimal: 67%)
  Alert A3 fires June 2024: "TikTok ROAS has exceeded Meta ROAS
  for 3 consecutive weeks. Current Meta allocation of 72% may be
  above optimal. Reallocating to 67% Meta / 16% TikTok would
  improve blended ROAS by estimated 8–12%."

D21 — Influencer Kill Fees:
  2 cancelled January activations. Fee paid, zero revenue.
  COGS hit in margin calculation.
  Alert D1 notes as one-time cost, not structural.

D22 — SEO Organic Search Spike:
  GA4 organic sessions +19% Jan–Feb 2024 (brand name searches)
  Alert variant: "Temporary — capture via email popup"

D23 — TikTok Wallet Balance Depletion:
  See D19 for full seed parameters (exact same event).
  D23 and D19 are the same event — D19 has the complete specification.
  Do NOT seed as two separate events.

D24 — Wholesale Channel Addition:
  8% of revenue ($320K/year) from wholesale (boutiques, Faire)
  Wholesale orders delayed February 2024 (buyer caution re: TikTok concentration)
  Alert distinguishes missing wholesale from DTC AOV decline
  shopify_orders.sales_channel = 'wholesale' for these orders

  WHOLESALE ORDER CHARACTERISTICS (seed parameters):
  AOV: $800–2,400 per order (multi-unit wholesale quantities)
  Order frequency: monthly or quarterly (not daily like DTC)
  Fulfilment cost: different rate ($18–35 per order, bulk shipping)
  Return rate: <2% (retailers bear return risk)
  payment_terms: net30 or net60 (not immediate like DTC)
  
  FEBRUARY 2024 DELAYED REORDER SCENARIO:
  Expected: 2 wholesale reorders arriving February 2024
  Actual: both delayed to March 2024
  Reason: wholesale buyers cautious about brand's TikTok channel concentration
  Shopify impact: zero wholesale orders in February (vs 2 expected)
  AOV metric: drops 23% in February (high-AOV wholesale orders absent)
  Alert fires: "AOV declined 23% in February. This is entirely explained by
    absence of wholesale orders (2 expected, 0 received vs January baseline).
    DTC AOV is stable at $148. Investigate wholesale buyer relationships."
  March 2024: both delayed orders arrive simultaneously
    Creates revenue spike in March that Alert D1 must not misread

D25 — Conquest Opportunity Alert:
  Meta conquest campaign Jan 20 – Feb 10 (competitor audience)
  Lower CPM on competitor audiences during disruption
  Alert A3 variant: "Conquest outperforming standard prospecting by 22%"

D26 — Refund Status Gorgias Category:
  Fourth Gorgias ticket category: refund_status_enquiry
  Spikes January both years from warehouse congestion
  Must NOT trigger Alert 5 (different from return intent)

D27 — Triple Whale Competitive Positioning:
  DECISION: Option A — no Triple Whale for Archetype A seed
  Maximum Alert A1 impact as first accurate ROAS founder has seen
  Document Option B reconciliation logic for real pilot clients with Triple Whale

D28 — Founder Stress Alert Fatigue:
  January 13–31 2024: dismiss rate 68%, response time 31h, snooze 45%
  Tests alert fatigue detection under external stress
  System response (Category 18) fires in Week 2 of disruption

  EXACT alert_log SEED PARAMETERS for January 13–31 2024:
  alert_dismiss_rate: 68% (vs 35% normal baseline)
  alert_response_time_avg_hours: 31 (vs 4 hours normal)
  alert_snooze_rate: 45% (vs 12% normal)
  
  Specific alert_log rows during this period:
    Row 1 (Jan 14): Alert H6 fires (TikTok spend $0). Founder snoozes.
    Row 2 (Jan 15): Alert A1 fires with caveat. Founder dismisses: "data wrong"
    Row 3 (Jan 17): Alert B1 fires (creative fatigue). Founder snoozes 48h.
    Row 4 (Jan 19): Alert H2 fires (dark social surge). Founder reads, no action.
    Row 5 (Jan 22): System response fires: "You've dismissed 4 of last 5 alerts.
      Reducing alert frequency temporarily. Only critical alerts will fire
      until January 31."
    Rows 6–12 (Jan 22–31): Only H-series (critical) alerts fire.
      Business alerts suppressed by fatigue detection.
    Row 13 (Feb 1): Fatigue period ends. Normal alert frequency resumes.
    
  alert_log field additions needed:
    fatigue_period_active boolean (true Jan 22–31 2024)
    fatigue_reason text ('founder_stress_external_event')
```

---

## GAP E — KLAVIYO FLOW ARCHITECTURE: COMPLETE SPECIFICATION

### E1 — Complete 15-Flow Architecture

```
Flow 1 — Welcome Series (existing spec, confirmed)
  3 emails: Day 0, Day 3, Day 7
  Attribution window: 5 days per email
  Revenue per subscriber: $12–18
  Alert connection: E1, D5

Flow 2 — Abandoned Cart (existing spec, confirmed)
  2 emails: 1 hour, 24 hours post-abandonment
  Cart abandonment rate: 72%
  Recovery rate: 8% of abandoned carts
  Alert connection: D5, G4

Flow 3 — Post-Purchase (existing spec, confirmed)
  3 emails: Day 3, Day 14, Day 45
  Alert connection: E2, C7

Flow 4 — Win-Back (existing spec, confirmed)
  2 emails: Day 60, Day 90 of inactivity
  Win-back rate: 12%
  Alert connection: E3

Flow 5 — Back-in-Stock (existing spec, confirmed)
  1 email: immediate on restock
  Conversion rate: 18%
  Alert connection: G4, G2

Flow 6 — Browse Abandonment (existing spec, confirmed)
  1 email: 4 hours post-browse
  Conversion rate: 3.2% → 5.8% after Month 16 personalisation
  Alert connection: F3, D5

Flow 7 — SMS Welcome + Abandoned Cart (NEW):
  SMS subscribers: 4,200 Y1 start → 7,800 Y2 end
  SMS abandoned cart: 30 minutes (before email at 1 hour)
  SMS conversion rate abandoned cart: 14% (vs 8% email)
  SMS opt-out rate: 4.2% per send
  Double-attribution DQ issue on 3–5% of recoveries
  klaviyo_sms_events table needed (distinct from email events)

Flow 8 — VIP / High-LTV Customer Flow (NEW):
  Trigger: 3rd purchase OR $450 cumulative spend
  VIP list Y1: 340 customers | Y2: 580 customers
  VIP open rate: 48%
  VIP repurchase rate: 71% within 90 days
  VIP return rate: 11% (lowest cohort)
  Alert connection: E3 reframed around VIP specifically

Flow 9 — Post-Return Recovery Flow (NEW):
  Trigger: Loop Returns refund processed
  Implemented: Month 8 (January 2025)
  3 emails: Day 3 (product recommendations by return reason),
             Day 10 (10% recovery offer), Day 21 (new arrivals)
  Pre-Month-8 repurchase rate: 8%
  Post-Month-8 repurchase rate: 19%
  Clearest Moat 3 demonstration in Klaviyo dataset

Flow 10 — Loyalty / Rewards Flow (NEW):
  Points earned notification: immediate post-purchase
  Redemption reminder: Day 30 if points unused
  Tier upgrade: triggered by cumulative spend threshold
  Open rate: 52% (highest of all flows)
  D5 misfire risk when loyalty redemption accelerates
  Exclude loyalty revenue from D5 calculation

Flow 11 — Collection Launch Announcement Flow (NEW):
  4 emails over 14 days at each collection launch
  Fires: April and October both years (4 times total)
  Double-attribution 65–75% overlap during launch window
  Alert A5 fires during each launch period

Flow 12 — Pre-Launch Waitlist Flow (NEW):
  Trigger: waitlist signup on /coming-soon page
  3 emails: immediate, 3 days before launch, launch day 6am
  Waitlist size SS 2024: 840 subscribers
  Conversion rate: 28% (highest of any Klaviyo segment)
  Open rate: 67%
  Predictive alert: waitlist size predicts collection demand

Flow 13 — Size Guide / Fit Education Flow (NEW):
  Trigger: GA4 size_guide_page_view → no add_to_cart within 24h
  1 email: Day 1 with sizing recommendations
  Open rate: 41% | Conversion rate: 12%
  Return rate on conversions: 14% (vs 22% average)
  Downstream complement to Alert 5

Flow 14 — Birthday / Gift Card Flow (NEW):
  Birthday data coverage: 34% of list
  Email 7 days before birthday: 15% off code, 14-day expiry
  Open rate: 62% | Conversion rate: 18%
  AOV on birthday purchases: $168 (vs $142 baseline)
  D5 variant when birthday data coverage drops after form change

Flow 15 — Sunset / Re-engagement (NEW):
  Trigger: no open or click in 180 days AND no purchase in 90 days
  2 emails: Day 0 and Day 7
  ~180 subscribers/month enter flow
  ~140 suppressed (unsubscribed automatically)
  ~40 re-engaged
  BFCM subscribers sunset 180 days later (June both years)
  Alert E1 must distinguish sunset suppressions from organic unsubscribes
```

### E-Alert3-TwoStage — Two-Stage Alert 3 Design (Critical — Missing from Original)

```
Alert 3 (Influencer ROI after returns) fires in TWO stages per activation.
This was confirmed explicitly and is the core Alert 3 architecture.

STAGE 1 — Early ROI Estimate (Day 7 post content_live_date):
  Fires: 7 days after influencer content goes live
  Data used: Cohort A purchases only (TikTok UTM, 0–7 day window)
  Return data: NOT included (return window still open)
  Message format: "Early ROI estimate for @[influencer]:
    Attributed revenue (Day 7): $[X]
    Fee paid: $[Y]
    Apparent ROI: [X/Y]x
    ⚠️ Return window still open (14 days). This figure will revise.
    Estimated final ROI after returns: $[X × (1 - expected_return_rate)]"
  Confidence: Medium (explicitly stated as estimate)
  alert_log: alert_type = 'Alert3_stage1', should_fire = true

STAGE 2 — Confirmed Final ROI (Day 21 post content_live_date):
  Fires: 21 days after influencer content goes live
  Data used: Cohort A + Cohort B purchases (0–14 day window)
  Return data: INCLUDED (most returns processed by Day 21)
  Klaviyo downstream value: INCLUDED (12-month estimated email revenue)
  Message format: "Final ROI confirmed for @[influencer]:
    Total attributed revenue (14-day window): $[X]
    Returns processed: [N] units, $[R] refunded
    Post-return revenue: $[X-R]
    Klaviyo list signups from activation: [N] subscribers
    Estimated 12-month email value: $[K]
    True total ROI: $[X-R+K] / $[fee] = [ratio]x
    vs Stage 1 estimate: [ratio]x"
  Confidence: High
  alert_log: alert_type = 'Alert3_stage2', should_fire = true

SEED REQUIREMENT:
  Every influencer activation in the sub-calendar must have TWO alert_log rows:
    - Alert3_stage1 at (content_live_date + 7 days)
    - Alert3_stage2 at (content_live_date + 21 days)
  manifest.json must include both rows per activation.
  Non-delivery activations (D6): Stage 1 fires with near-zero revenue,
    Stage 2 confirms. Both rows seeded.
  Disrupted activations (INF-2024-JAN-02): Stage 1 fires as diagnostic-only
    (attribution incomplete), Stage 2 fires with caveat.
```

### E-GiftingCOGS — sku_cost_master for Influencer Gifting Packages

```
CONFIRMED DECISION: Gifting-only influencer deals use FULL PACKAGE landed cost.

For each gifting-only or hybrid activation, seed in sku_cost_master:
  record_type: 'influencer_gifting_package'
  influencer_id: [activation ID]
  activation_date: [date package shipped]
  items_included: 3–5 items
  package_landed_cost: $120–240 (all items at landed cost)
  packaging_cost: $25–60 (branded box, tissue, handwritten note)
  shipping_cost: $18–45 (express to creator for pre-content-date delivery)
  total_package_cost: sum of above three
  featured_item_sku: SKU actually shown in TikTok content
  non_featured_item_skus: list of other SKUs in package

ALERT 3 cost calculation by deal type:
  Cash deal: total_cost = cash_fee
  Gifting deal: total_cost = total_package_cost
  Hybrid deal: total_cost = cash_fee + total_package_cost

INVENTORY IMPACT:
  All items in package deplete inventory_levels on shipment date.
  Seeded as inventory_adjustment with reason = 'influencer_gift'.
  NOT a Shopify order. Alert G1 must not fire on these depletions.
  brand_event_calendar: 'influencer_gift_shipment' suppresses G1.
```

### E2 — 8 Flow Modification Events

```
Month 3 (Aug 2024): Welcome series personalised by signup source
  Open rate improves. Revenue per recipient +23%.
  No alert fires.

Month 6 (Nov 2024): Abandoned cart A/B test
  2-email vs 3-email sequence. Runs 6 weeks.
  D5 appears to fire — actually A/B test splitting performance.
  brand_event_calendar: 'klaviyo_ab_test' — suppresses D5.

Month 9 (Feb 2025): Abandoned cart rebuilt
  New 3-email sequence. Revenue drops 34% for 2 weeks.
  Alert D5 fires. Suppressed: flow_modification event.

Month 11 (Apr 2025): Post-purchase segmented
  VIPs: exclusive early access. Standard: 10% off.
  Revenue per recipient +18%. No alert fires.

Month 13 (Jun 2025): Win-back trigger changed
  60 days → 45 days inactivity trigger.
  E3 appears to fire — suppressed 3 weeks post-change.

Month 16 (Sep 2025): Browse abandonment personalised
  Conversion rate 3.2% → 5.8%.
  Positive performance alert fires: "Flow update improved
  conversion by 82%. Estimated additional revenue: $2,100/month."

Month 18 (Nov 2025): Klaviyo restructured (agency → in-house)
  Flow IDs change. Attribution breaks 2 weeks.
  Alert D5 fires then suppressed: flow_modification event.

Month 21 (Feb 2026): SMS flows added to abandoned cart
  SMS fires at 30 minutes (before email at 1 hour).
  Double-attribution on 5% of abandoned cart recoveries.
```

### E3 — Segmentation Architecture (7 Core Segments)

```
Segment 1 — Active Subscribers (opens/clicks last 90 days)
  Y1: 8,400 of 18,000 (47%) | Y2: 13,200 of 28,000 (47%)
  Alert: E1 fires if drops below 40%

Segment 2 — Engaged Non-Purchasers
  Y1: 3,200 | Y2: 4,800
  Alert: if grows faster than purchasers — conversion gap signal

Segment 3 — VIP (3+ orders OR $450+ spend)
  Y1: 340 | Y2: 580
  Alert: E3 (high-LTV going quiet)

Segment 4 — At-Risk (2+ purchases, no purchase 91–180 days)
  Y1: 420 | Y2: 680
  Alert: leading indicator of E2 (repeat purchase decline)

Segment 5 — Lapsed (no purchase 181+ days)
  Y1: 890 | Y2: 1,240
  Alert: lagging indicator confirming E2

Segment 6 — TikTok-Acquired (UTM source contains tiktok)
  Y1: 2,100 | Y2: 3,400
  Engagement drops 22% during TikTok disruption — exclude from
  E1 calculation during disruption period

Segment 7 — High-Return-Rate Customers (return rate >35%)
  Y1: 280 | Y2: 390
  Alert: if growing faster than list — acquisition quality signal
  New alert: "High-return-rate segment grew 39% while list grew 22%"

Segment membership seeded as time-series data (dynamic, not static flags)
```

### E4 — Flow Revenue Attribution Model

```
15–20% of flow-attributed revenue flagged as attribution_confidence = 'low'
Specifically: non-promotional emails (care instructions, review requests)
  that cannot plausibly have driven a purchase.
D5 must distinguish genuine flow revenue decline from attribution noise.
```

### E5 — Deliverability Architecture

```
Deliverability fields in klaviyo_email_events:
  spam_complaint_count (per campaign)
  hard_bounce_count (per campaign)
  inbox_placement_rate (estimated)

Deliverability arc:
  Y1 Month 1–8: healthy (open 24–28%, spam 0.03–0.05%, inbox 91–94%)
  Y1 Month 9–12: degradation (open 17–21%, spam 0.07–0.09%)
  Y1 Month 13: list clean — recovery
  BFCM both years: spam 0.08–0.11% temporarily

New Alert E5 — Deliverability Risk:
  "Your spam complaint rate has reached 0.08% — at Gmail's threshold.
   Emails will start landing in spam within 7 days.
   Immediate action: suppress unengaged subscribers before next send."
  Fires BEFORE deliverability degrades (leading indicator)
```

### E6 — Klaviyo Revenue Seasonality (Monthly Targets)

```
January:   $3,200–4,100/week
February:  $4,800–6,200/week (Valentine's)
March:     $5,100–6,800/week (SS teaser)
April:     $8,200–11,400/week (SS launch)
May:       $5,400–7,100/week (Mother's Day)
June:      $3,800–5,200/week (markdown)
July:      $7,800–10,200/week (summer sale)
August:    $3,400–4,600/week (quietest)
September: $5,200–6,900/week (FW teaser)
October:   $7,400–9,800/week (FW launch)
November:  $18,000–24,000/week (BFCM)
December:  $9,200–12,400/week (holiday)

D5 uses seasonally-adjusted benchmarks NOT flat baseline.
Same-week-prior-year comparison from Month 13+.
```

### E7 — Form Architecture (6 Form Types)

```
Form 1 — Exit Intent Popup:
  Offer: 10% off. Trigger: mouse toward browser close.
  Conversion: 2.8% of eligible sessions.
  Subscriber LTV 12mo: $142 | Return rate: 26%

Form 2 — Footer Signup:
  Offer: "Join our community" (no discount).
  Conversion: 0.4% of sessions.
  Subscriber LTV 12mo: $218 | Return rate: 18%

Form 3 — Collection Launch Waitlist:
  Conversion: 34% (very high intent)
  Subscriber LTV 12mo: $267 | Return rate: 16%

Form 4 — Post-Purchase Guest Checkout Signup:
  Conversion: 41% (already a customer)
  Subscriber LTV 12mo: $312 | Return rate: 19%

Form 5 — TikTok Link-in-Bio:
  Conversion: 8.2% | LTV: $167 | Return rate: 24%

Form 6 — Gorgias Post-Resolution:
  After 4–5 CSAT score resolution.
  Conversion: 22% | LTV: $289 | Return rate: 14%

Monthly signup source distribution:
  Exit intent: 45% | Footer: 12% | Waitlist: 8% (spikes 35% at launches)
  Post-purchase guest: 18% | TikTok: 14% | Gorgias post-resolution: 3%

New Alert: "68% of new subscribers are discount-motivated (exit intent).
  Historical data shows 35% lower LTV vs footer or waitlist subscribers."

signup_source and signup_form_id fields on all klaviyo_profiles.
```

### E8 — Post-iOS 15 Open Rate Reliability (Critical)

```
Apple MPP: pre-loads tracking pixels regardless of human open.
Apple Mail users: ~52% of Archetype A list (premium womenswear skews iOS)
MPP enabled: ~68% of Apple Mail users
Result: ~35% of reported "opens" are machine-generated

Required fields in klaviyo_email_events:
  reported_opens (what Klaviyo shows — includes machine opens)
  effective_opens (reported_opens × 0.65 — human opens only)

ALL Alert E1 logic uses effective_open_rate NOT reported_open_rate.
Click rate is primary engagement metric (clicks cannot be machine-generated).
Flow revenue excludes orders where only engagement signal was machine open.
```

### E9 — Klaviyo-Gorgias Bidirectional Integration

```
Direction 1 — Gorgias pushes to Klaviyo profiles:
  last_ticket_reason, last_ticket_resolved_at, ticket_count_lifetime, 
  csat_score_last fields synced to klaviyo_profiles
  35–40% of customers have at least one Gorgias ticket in profile

  Flow trigger modifications by Gorgias data:
    ticket_count_lifetime > 2 AND last_ticket_reason = 'sizing'
      → size guide flow on next browse
    csat_score_last < 3
      → win-back with recovery offer (not standard win-back)
    last_ticket_reason = 'return'
      → post-return recovery flow trigger

Direction 2 — Klaviyo pushes to Gorgias sidebar:
  Agent sees Klaviyo email history, open/click behaviour, segment membership
  VIP customers (Segment 3) get priority queue routing in Gorgias
  New alert: "VIP customer (3+ orders) has unresolved Gorgias ticket for 18h"
```

### E10 — Compliance and Legal Layer

```
GDPR (EU/UK customers — 8–12% of international orders):
  Double opt-in required
  Confirmation email conversion: 48% (52% don't confirm — never enter list)
  EU/UK confirmed subscribers: higher engagement (actively chose to subscribe)
  consent_method field on profiles: 'double_optin' vs 'single_optin'

CCPA (California customers):
  ccpa_opt_out = true: cannot be synced to Meta Custom Audience
  Slightly reduces Meta retargeting audience size

CAN-SPAM unsubscribe lag:
  Klaviyo processes immediately but Shopify sync lags
  Creates Gorgias compliance_complaint ticket type
  2–4 compliance_complaint tickets per month

Fields added to klaviyo_profiles:
  consent_method, consent_timestamp, ccpa_opt_out, gdpr_consent
```

### E11 — Additional Gap E Decisions (E11–E40)

```
E11 — Klaviyo Plan Cost Changes:
  Month 1: 18,000 contacts → $400/month (20K tier)
  Month 10: 23,000 contacts → $700/month (25K tier)
  Month 18: 27,000 contacts → $1,100/month (50K tier)
  klaviyo_monthly_cost time-series in client_config with effective dates
  Alert D1 accounts for plan cost increases explicitly

E12 — Zero-Party Data Collection:
  Month 6 (Nov 2024): preference survey launched
  34% response rate over 4 weeks
  Fields captured: style_occasion, fit_preference, budget_preference
  28% of list declares $200+ budget vs current max product $185
  New strategic alert: "28% of subscribers declared $200+ budget.
    Expanding price ceiling could capture additional revenue."

E13 — Klaviyo AI Features:
  Month 4: Smart Send Time enabled
    2-week learning period with temporary open rate decline
    14-day suppression window for E1 post-activation
    8–12% sustained open rate improvement after
  Month 8: AI subject lines adopted for 40% of campaigns
    12–18% higher open rate on AI-subject campaigns
  Month 15: Predictive Sending enabled
    Frequency decreases for some, increases for others
    D5 uses send-efficiency metric not raw send volume

E14 — Klaviyo-Meta Audience Sync:
  Klaviyo syncs 'browsed but didn't buy' segment to Meta
  meta_ad_performance campaigns tagged: audience_source = 'klaviyo_sync'
  Alert A1 Layer 2: "Meta retargeting ROAS partially explained by
    Klaviyo audience sync — these customers were already brand-engaged"

E15 — Referral Programme Integration:
  Launched Month 5 (October 2024)
  12% of customers participate
  Referrer reward: $20 store credit. Referee: 15% off first purchase
  Effective CAC: $42 (vs $67 Meta CAC)
  Referred customer LTV 12mo: $298 (second highest acquisition source)
  New alert: "Referral programme is your highest-ROI acquisition channel.
    Only 12% of customers enrolled — underscaled vs Meta spend."

E16 — Frequency Capping Architecture:
  Y1 BFCM: frequency capping DISABLED → email fatigue arc
  Y2 BFCM: frequency capping ENABLED after Alert E5 drove action
  Y1 Nov: 18–22 emails per subscriber across flows + campaigns
  Y2 Nov: 8–10 emails per subscriber (capped)
  frequency_capping_enabled boolean in client_config with effective dates
  Moat 3 demonstration: Y1 problem → alert → Y2 improvement

E17 — Transactional vs Marketing Email Boundary:
  Month 3–4: order confirmation misconfigured as marketing flow
  Unsubscribed customers stop receiving order confirmations
  Alert H8: "Gorgias tickets about missing order confirmations
    from recently unsubscribed customers. Check Klaviyo flow settings."
  email_type field: 'transactional' vs 'marketing' in klaviyo_email_events
  Transactional email click revenue: attribution_confidence = 'low'

E18 — Account Hygiene Events:
  Month 8: 840 duplicate profiles detected (4.7% of list)
    Alert H9: "840 duplicate profiles. Recommend merge."
  Month 12: Suppressed profiles accidentally reactivated
    Spam complaint rate spikes 0.04% → 0.18%
    Alert E5 fires at maximum severity: emergency
  Month 1–18: Invalid email accumulation
    Hard bounce rate: 0.4% (Month 1) → 1.4% (Month 16) → 0.5% (Month 18 post-clean)
    Alert E1-variant fires Month 16: "Hard bounce rate 1.4% — run list validation"

E19 — Reviews Integration:
  review_submitted boolean in klaviyo_email_events (post-purchase Day 14)
  Review submitters: 6% future return rate vs 31% non-engagers
  Alert E3 Layer 2 references review behaviour for VIP recovery targeting

E20 — Agency Transition Data Loss (Month 18):
  Week 1: API key change → 48h Klaviyo sync gap → H1-variant fires
  Week 2: 3 flows paused for investigation → D5 fires
  Week 3: Flow IDs change — historical attribution mapping breaks
  New table: klaviyo_flow_id_history (tracks flow ID changes with effective dates)

E21 — Unsubscribe Destination States:
  Three states: subscribed / unsubscribed_marketing / unsubscribed_all
  State 3 customers: zero Klaviyo engagement but continued Shopify purchases
  Alert A6 must exclude State 3 from Klaviyo-based LTV scoring

E22 — BNPL Revenue Recognition in Klaviyo:
  Afterpay/Klarna introduced Month 10 (Gap A15)
  Klaviyo attributes full BNPL order value on Day 1
  Cash received over 6 weeks
  Alert D5 variant during BFCM: "Klaviyo revenue $24,000,
    cash received $8,400 — BNPL instalment lag"

E23 — Email Content IP Risk Event:
  Month 14: photographer takedown notice for welcome series images
  Welcome series paused 3 days
  340 subscribers miss Email 1 → lower first-purchase conversion
  Alert: "Send retroactive welcome to 340-subscriber cohort.
    Estimated revenue recovery: $4,100"

E24 — Smart Send Time Performance Arc (detailed):
  Month 4 activation: 2-week temporary open rate decline (learning)
  brand_event_calendar: 'klaviyo_feature_activation'
  14-day suppression window for E1 post-activation
  After learning: 8–12% sustained open rate improvement

E25 — Multi-Brand Architecture Problem (Month 20):
  Men's casualwear added to same Klaviyo account
  Womenswear customers receive menswear recommendations
  Unsubscribe rate: 3.2% per send (14.5× baseline)
  Alert E1-variant: "Unsubscribe spike from menswear 
    recommendations to womenswear customers — segmentation failure"

E26 — Loyalty-Klaviyo Feedback Loop Failures:
  Month 7: Points sync lag during December 2024 peak
    34 customers affected — H7 fires
  Month 12: Points expiry without warning — 42 customers
    loyalty_complaint Gorgias ticket category
  Month 19: Tier upgrade notification failure during BFCM Y2
    28 customers reached VIP but didn't receive VIP welcome
  New Alert H7: "Loyalty-Klaviyo integration failure — N customers affected"

E27 — Klaviyo Export Discrepancy Design:
  alert_log stores both klaviyo_native_revenue AND profit_sentinel_adjusted_revenue
  Gap = double-attribution amount (18–32% during active campaigns)
  Every Klaviyo alert includes explanation of calculation difference

E28 — Klaviyo as Signal Amplifier:
  mart_cross_source_daily must include Klaviyo engagement metrics as 
  standard columns alongside all other sources
  Agent B always has Klaviyo context when traversing causal graph
  Not a separate join — integrated into the base cross-source mart

E29 — Sunset Flow Interaction with BFCM:
  See detailed parameters below (E29 BFCM Sunset Timing section)

E30 — Deliverability Benchmark Comparison:
  network_pattern_benchmarks includes Klaviyo deliverability benchmarks
  Premium womenswear typical: spam complaint 0.03–0.05%, inbox placement 91–94%
  Context added to every E5 alert

E31 — Post-Purchase Signal Chain (Gorgias ticket categories):
  Three distinct Gorgias categories with different flow triggers:
  1. Return intent → size guide flow, Alert 5 chain
  2. WISMO (where is my order) → fulfilment alert, NOT return alert
  3. Product quality → Alert C3, different lag
  Fourth category (added E26): compliance_complaint
  Fifth category (added D26): refund_status_enquiry

E33 — Klaviyo Template and Design System Events:

  EVENT 1 — Month 5 (October 3 2024): Mobile-first email redesign for FW launch
    Before: single-column, not mobile-optimised, 85KB average
    After: mobile-first, new brand fonts via web fonts
    Post-redesign signatures:
      Mobile click rate: 1.8% → 2.9% (improvement)
      Outlook rendering: BROKEN for 3 days (CSS not supported in Outlook)
    Alert fires Day 3: F1-variant: "Click rate dropped 34% on Outlook clients
      (8% of your audience). Outlook doesn't render your new CSS.
      Add Outlook-specific fallback styles."
    brand_event_calendar: 'email_template_update' October 3 2024
    Suppresses F1, F2 for 48h. After 48h: Outlook error persists → State 2.
    klaviyo_email_events additions: email_file_size_kb, outlook_compatible boolean

  EVENT 2 — Month 15 (August 8 2025): Video GIF addition
    Email file size: 85KB → 340KB average
    Post-GIF signatures:
      Mobile open rate: declines 12% (3.8s load vs 1.2s before)
      Spam score: increases (large file size triggers spam filters)
    Alert E1-variant fires Week 2: "Mobile open rate declined 12%.
      Email file size 340KB — large files load slowly on mobile.
      Consider optimising GIF sizes or using animated PNGs."
    brand_event_calendar: 'email_template_update' August 8 2025

E32 — Klaviyo Industry Benchmarking:
  network_pattern_benchmarks Klaviyo entries:
    Welcome series open rate: 38–44%
    Abandoned cart open rate: 45–52%
    Post-purchase Day 3 open rate: 58–64%
    Win-back open rate: 12–18%
    Campaign open rate: 22–28%
    Flow revenue as % of total: 28–35%
    SMS abandoned cart recovery: 12–16%
    List growth rate monthly: 3.2–4.8% of current list
    Revenue per email sent: $0.08–0.14

  PRIMARY D5 METRIC — REVENUE PER EMAIL SENT (missing rationale):
  Formula: total_klaviyo_revenue / total_emails_sent in period
  Why this metric and NOT absolute flow revenue:
    Normalises for list size AND send frequency simultaneously.
    A brand that cuts send frequency by 30% will show lower absolute revenue
    but the same or higher revenue per email sent — which is healthy.
    A brand whose revenue per email sent declines while send volume holds
    is the genuine problem D5 should detect.
  Benchmark: $0.08–0.14 for premium womenswear at this tier.
  Alert D5 fires when: revenue_per_email_sent drops >20% below
    rolling 28-day average AND stays below for >5 consecutive days.

E29 — BFCM Sunset Timing (explicit month mapping — missing from original):
  BFCM November Y1 (Month 6): large influx of low-quality subscribers
  180 days later = May 2025 (Month 12): elevated sunset flow activity
  Alert E1 in May 2025: MUST distinguish between:
    a) Organic unsubscribes (problem signal — investigate)
    b) Sunset flow automated suppressions (health maintenance — positive)
  seed_event: 'bfcm_sunset_spike' in brand_event_calendar
    start_date: 2025-05-01, end_date: 2025-05-31
    suppress: ['E1']  -- suppresses E1 alert on the unsubscribe VOLUME metric only
    context_explanation: 'BFCM subscriber cohort reaching 180-day sunset threshold.
      Automated suppressions account for elevated unsubscribe volume.
      Check ticket_category = sunset_suppressed vs organic_unsubscribe in 
      klaviyo_email_events before acting on E1.'
    
  BFCM November Y2 (Month 18): same pattern
  180 days later = May 2026 (Month 24): second sunset spike
  Same suppression logic applies.
  
  Seed requirement: Klaviyo subscriber records for BFCM cohort must have
    acquisition_date in November both years
    engagement_score: low (BFCM discount-motivated — open rates 12–15%)
    sunset_eligible: true at Day 180
  These subscribers enter Flow 15 (Sunset) in May both years.
```

---

## IMPORTANT: THIS FILE COVERS GAPS D AND E ONLY

Gap F (Suppression Scenarios) and Gap G (DQ-to-Alert Interaction Map)
are in `seed_decisions_gap_f_g.md`.

Gap A, B, C decisions are in `gap_abc_decisions.md`.

All three files plus `technical_architecture.md` and `product_strategy.md`
must be in context when writing the Claude Code seed prompt.
