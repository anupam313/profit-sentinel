# Profit Sentinel — Seed Script Design Decisions
## Gaps A, B, C — Complete and Confirmed
### Date: 2026-05-15

---

## BASELINE DEFINITION (Pre-Gap A — Critical Foundation)

Normal week for Archetype A: Premium Contemporary Womenswear, $150 AOV, $4M GMV Y1.

```
SHOPIFY:
Orders:                 180–220/week
AOV:                    $142–158 (day-of-week variance)
Return rate:            18–22% on orders placed 3 weeks prior
Refund processing:      35–45/week
Discount code usage:    12–15% of orders
New customers:          65–70% of orders
Repeat customers:       30–35% of orders
International orders:   8–12% of total
Cart abandonment:       68–74%
Avg items per order:    1.4–1.7

META:
Daily spend:            $1,100–1,300
CPM:                    $16–19 (day-of-week adjusted)
CTR:                    1.1–1.4%
ROAS (platform):        2.8–3.4x
Frequency prospecting:  1.4–1.8
Frequency retargeting:  2.1–2.6
Active ad sets:         8–12
Creative variants:      15–20

TIKTOK:
Daily spend:            $400–600
CPM:                    $8–12
ROAS (platform):        1.8–2.4x
Active Spark Ads:       2–4
Organic posts:          3–5/week

KLAVIYO:
Campaigns/week:         2–3
Open rate:              24–28%
Click rate:             2.1–2.8%
Flow revenue/week:      $4,200–5,800
New subscribers/week:   180–220
Unsubscribe rate:       0.18–0.24% per send
Net list growth/week:   +150–180

GORGIAS:
Total tickets/week:     85–110
Return intent tags:     8–12% of tickets
WISMO tags:             22–28% of tickets
Sizing questions:       14–18% of tickets
Product quality tags:   4–6% of tickets
General enquiry:        40–50% of tickets
First response time:    2–4 hours
CSAT score:             4.2–4.6/5.0

GA4:
Sessions/week:          8,500–11,000
Bounce rate:            42–48%
Pages per session:      3.2–4.1
Checkout initiation:    6.8–8.2% of sessions
Checkout completion:    58–68% of initiated
Mobile share:           54–61%

SENTRY:
Checkout error rate:    0.4–0.8% of checkout sessions
JS error rate:          1.2–1.8% of all sessions
Payment failure rate:   0.6–1.1% of checkout attempts

LOOP RETURNS:
Return initiations/wk:  35–45
Return reasons:         Sizing 52%, Style 23%, Quality 12%, Wrong item 4%, Other 9%
Exchange rate:          28–32% of returns
Refund rate:            68–72% of returns
Processing time:        6–8 days initiation to receipt
```

---

## GAP A — MONTHLY DISTRIBUTION AND SIGNAL ARCHITECTURE

### A1 — BFCM Suppression Corrected
Only CPM spike alerts + Sentry rate-limiting suppressed during BFCM.
All business alerts (A1, A3, B2, G1, D1, C1) FIRE during BFCM.
BFCM is the highest-value period for Profit Sentinel — highest alert density, not highest suppression.

### A2 — Monthly Floor Raised
Minimum 8–10 alerts per quiet month. Not 2–3.
Every month has continuous signal generation regardless of events.

### A3 — Two-System Seed Architecture
System 1: Episodic event calendar (44–50 named events across 24 months)
System 2: Continuous signal generator with weekly baseline variance per metric

### A4 — Continuous Signal Parameters (Correlated, Not Independent)
Correlation matrix for continuous signals:
```
CPM spike → ROAS lag (3-5 days):           correlation -0.72
Return rate rise → Gorgias volume (2-3d):   correlation +0.81
Return rate rise → Net revenue (7-14d):     correlation -0.68
Klaviyo open rate → Repeat purchase rate:   correlation +0.43
GA4 sessions → Shopify orders (same day):   correlation +0.76
```
System 2 must be multivariate correlated time series generator, NOT independent per-metric variance.

### A5 — Total Event Count
~390 alert-worthy events across 24 months
~220 fire as true alerts
~40 suppressed (CPM spikes during known events, sync outages, DQ suppressions)
~20 fire with caveats (medium confidence)
~110 below threshold / baseline noise

### A6 — Three-Stage Return Warning Chain
Stage 1 — Gorgias complaint velocity spike (Day 0–3 post-purchase cohort)
→ Alert 5: "Sizing complaints rising. Return spike likely in 8–12 days."
→ Sources: Gorgias only | Confidence: Medium

Stage 2 — Loop return initiations spike (Day 3–7 post-purchase cohort)
→ Alert C4-variant: "Return initiations confirm sizing complaint signal."
→ Sources: Loop Returns + Shopify | Confidence: High

Stage 3 — Physical return receipt RTO/RVP (Day 8–14)
→ Alert C3: SKU-level return rate confirmed
→ Sources: Shopify refunds + Loop Returns | Confidence: High (lagging, certain)
→ Agent fires at Stage 1, confirms at Stage 2, closes loop at Stage 3.
   Stage 3 = outcome confirmation not new alert.

### A7 — Loop Returns Schema Addition
`return_initiated_at` timestamp added to `loop_returns` table.
Separate from `return_received_at`.
Gap between them = leading indicator window (5–8 days typical).

### A8 — Monthly Distribution Reframed
Quiet months: 8–10 alerts
Active months: 18–22 alerts
Peak months (BFCM): 22–28 alerts

### A9 — Asymmetric ROAS Recovery Curve
Drop: 3–4 days (sharp, fast)
Recovery: 14–21 days (slow, gradual)
Negatively skewed distribution — not symmetrical variance.

### A10 — Day-of-Week CPM Rhythm
Mon–Wed: +18% above weekly average
Thu–Sun: -12% below weekly average
Embedded in continuous generator — not random.

### A11 — Weekend Return Rate Premium
Orders placed Fri–Sun return at +6pp above weekday orders.
Structural pattern — not anomaly. Must not trigger Alert C3.

### A12 — Weather Demand Suppression Events
Oct 2024: FW outerwear add-to-cart 35% below expected (unseasonably warm)
Apr 2025: SS lightweight pieces 28% below expected (cold spring)
Both: Diagnostic-only alerts — no internal causal explanation found.
Agent explicitly states: "No data-supported explanation found. Consider external factors."

### A13 — Viral Organic Moment
Month 7 (Dec 2024): Holiday gifting newsletter feature
Month 18 (Nov 2025): Celebrity organic TikTok post during BFCM
Each: GA4 direct traffic +400%, Shopify orders spike, no paid UTM, inventory depletes.
New alert variant: "Organic demand spike — do not increase ad spend."

### A14 — Checkout Abandonment Seasonality
January: +18% above baseline
BFCM: +22% above baseline
Collection launch weeks: -15% below baseline
Mid-season: ±5% baseline variance
Embedded in GA4 funnel seed data.

### A15 — BNPL Payment Mix Shift
Introduced Month 10 (March 2025).
Y1: 80% credit card. Y2 end: 65% credit card / 25% BNPL / 10% Shop Pay.
BNPL orders: AOV +30%, return rate +15–20% vs credit card.
Alert C5-variant: "BNPL customers returning at 31% vs 18% for credit card."

### A16 — Correlated Time Series Generator (Critical)
Must use correlation matrix not independent random walks.
Without this: agent learns from noise not signal.

### A17 — Post-Purchase Signal Chain + Gorgias Taxonomy
Three distinct Gorgias ticket categories with different patterns:
1. Return intent: "runs small", "doesn't fit", "want to return"
   → Leads to Alert 5 chain
2. WISMO: "where is my order", "tracking not updating"
   → Leads to fulfilment alert, NOT return alert
3. Product quality: "pilling", "colour different from photo", "seam issue"
   → Leads to Alert C3, different lag pattern
Each category has different velocity patterns, different alert implications.

### A18 — Email Fatigue Arc
BFCM both years: 18 sends in November (over-sending)
December: Klaviyo degradation begins
January: Alert E1 fires (list health degradation)
February: Recovery begins after list clean
4-month arc — tests agent's ability to trace January problem back to November cause (60-day lag).

---

## GAP B — YEAR 1 VS YEAR 2 STRUCTURAL DIFFERENCES

### B1 — Brand Growth (Non-Linear Revenue Curve)
NOT linear. Month-level targets must be defined explicitly:
```
Y1 Jun–Aug 2024:    $320–340K/month (flat, establishing)
Y1 Sep–Oct 2024:    $380–420K/month (FW momentum)
Y1 Nov 2024:        $650K (BFCM spike)
Y1 Dec 2024:        $480K (holiday gifting)
Y1 Jan–Feb 2025:    $280–310K/month (post-holiday dip)
Y1 Mar–May 2025:    $380–450K/month (SS launch)
Y2 Jun–Aug 2025:    $420–460K/month (larger brand)
Y2 Sep–Oct 2025:    $480–520K/month (FW Y2, more awareness)
Y2 Nov 2025:        $780K (BFCM Y2 stronger)
Y2 Dec 2025:        $560K
Y2 Jan–Feb 2026:    $320–360K/month
Y2 Mar–May 2026:    $480–540K/month (SS Y2 at scale)
```

### B2 — Ad Spend Scaling (Efficiency Inflection)
NOT linear.
$35K/month Y1 → $48K/month Y2.
Efficiency inflection at $42K/month threshold (Month 16):
→ Audience saturation begins
→ ROAS compresses 15–20% despite stable CPM
→ Alert D1 fires: audience saturation as distinct causal driver

### B3 — Founder Learning Curve (Moat 3 Demonstration)
Creative fatigue (B1): 6 alerts Y1 → 2 alerts Y2 (founder implemented weekly rotation after Month 8)
Stockout (G1): 3 alerts Y1 → 1 alert Y2 (founder built restock buffer)
Alert 5: Fires for New Season Denim Y1 → FW Knitwear Y2 (new category, same lesson)

### B4 — Schema Changes Between Years
Jan 12 2026: Meta attribution window break (already in technical_architecture.md)
March 2025 (Month 10): Gorgias tag split — "runs small" → "runs small — tops" + "runs small — bottoms"
Jan 2025 (Month 8): Shopify theme update → 48h Sentry spike (suppression test)
Jan 2026 (Month 20): Second Shopify theme update → same pattern

### B5 — Threshold Recalibration Event (Month 13–14)
Brand grown 30%. Thresholds from months 1–3 now miscalibrated.
Agent detects and fires structural alert:
"Your alert thresholds were calibrated when monthly ad spend was $35K.
Current spend is $48K. Recalibration recommended."
Tests threshold management logic.

### B6 — New SKU Category: Formal Occasion Womenswear (Month 15)
Same customer base, partial baseline transfer.
Return rate 32% vs 22% baseline (structural to sub-category, not anomalous).
Different seasonal rhythm: wedding season March–June, corporate January.
Gorgias complaints: "too casual", "not occasion-appropriate" added to taxonomy.

### B7 — New Gender Category: Men's Casualwear (Month 20)
Zero baseline transfer.
Return rate 15% vs brand average 28% — agent must not misread.
90-day monitoring window before any alerts fire.
Layer 3 explicitly states: "Insufficient history for menswear — precedent unavailable."
Meta audiences completely different — CPM benchmarks don't apply.

### B8 — Klaviyo Degradation and Recovery Arc
Month 10–12: Open rate 28% → 17% (list growth with less engaged subscribers)
Month 12: Alert E1 fires (monitor-and-wait)
Month 13: List cleaning implemented
Month 15: Open rates recover to 24%
Demonstrates product impact on retention operations.

### B9 — CAC Structural Drift (Continuous)
$52 CAC Month 1 → $71 CAC Month 24 (37% increase)
Alert E4 fires Month 12 (monitor-and-wait)
Alert E4 escalates Month 18 (structural — LTV payback window <14 days)

### B10 — Second Supplier Event (Month 20)
Different type from Month 14 (cost increase).
Month 20: Shipping delay — FW knitwear supplier delays 3 weeks.
Creates: inventory stockout signal before FW launch, missed launch window.
GA4 sessions with no inventory signal.
Tests Alert G1 in pre-launch context.

### B11 — Non-Linear Revenue Curve
(Incorporated into B1 above)

### B12 — Ad Spend Efficiency Inflection
(Incorporated into B2 above)

### B13 — Operational Change Events
Month 11: Marketing manager hired
→ Campaign structure changes, ad set naming changes
→ ROAS dips 15% for 6 weeks during learning curve
→ Suppressed: operational_change event in brand_event_calendar

Month 15: 3PL switch
→ 3-week transition: fulfilment delays, inventory discrepancy
→ Gorgias WISMO spike, Loop Returns data lags 5–7 days extra
→ Suppressed: operational_change event

Month 18: Klaviyo restructured (agency → in-house)
→ Flow IDs change, attribution breaks temporarily
→ Alert D5 fires then suppressed: flow_modification event

### B14 — Cohort Quality Arc
Months 1–6: Tight targeting, high brand-fit, low return rate, high LTV
Months 7–12: Scaled spend, broader targeting, marginal customers — LTV declining, return rate rising
Months 13–18: Tighter targeting, Klaviyo segmentation improves
Months 19–24: Cohort quality recovering
Alerts E2, E4, A6, D1 all interact with this arc.

### B15 — Pricing Decision (Month 15)
10% price increase on core collection (not sale items).
Conversion dips 6 weeks → recovers to 85–90% of pre-increase rate by Month 21.
Contribution margin improves from Month 16.
Alert D1 (monitor-and-wait) resolves by Month 19.
Suppressed during dip: price_change event in brand_event_calendar.

### B16 — Competitor Activity Events
Month 9 and Month 21.
Each: CPM spike + conversion drop with no internal causal explanation.
Diagnostic-only alert: "Consider external competitive activity."
Suppression test AND new alert variant.

---

## GAP C — INFLUENCER SUB-CALENDAR (COMPLETE)

### Confirmed Structure
30 total activations: 20 micro, 7 mid, 3 macro across 24 months
Y1: 12 activations | Y2: 18 activations

### Influencer Sub-Calendar Fields (Per Activation)
```
influencer_id
tier                        -- micro/mid/macro
fee_structure               -- cash/gifting/hybrid
cash_fee
package_landed_cost         -- full package (3–5 items) for gifting
packaging_shipping_cost     -- $25–60 per package
content_format              -- tryon_haul/styling/grwm/unboxing
discount_code               -- nullable
audience_fit_score          -- 1–5 (1=poor fit, 5=perfect fit)
expected_return_rate        -- derived from above factors NOT fixed by tier
activation_date
content_live_date           -- may differ from activation date
spark_ad_launched           -- boolean
spark_ad_campaign_id        -- nullable
geographic_skew             -- domestic_heavy/international_heavy/balanced
```

### C1 — 4-Week Campaign Lifecycle (Critical)
Each activation seeded across 4 distinct weeks:
```
Week 0 (Pre-launch): Brand ships gifting package. COGS hit on inventory.
Week 1 (Content live): TikTok impressions spike. Shopify sessions spike.
  Klaviyo list growth spike (non-converting browsers signing up).
  Add-to-cart rate tells you immediately if creative resonates.
Week 2 (Purchase window): Cohort A purchases (Days 1–7).
  Meta retargeting kicks in. Attribution conflict begins.
  Gorgias pre-purchase sizing questions spike.
Week 3 (Return window opens): Gorgias complaint velocity peaks.
  Loop return initiations spike. First RTO returns arriving.
Week 4 (Full picture): Cohort B purchases (Days 8–14) still arriving.
  Physical RTO hitting warehouse. Final ROI calculable.
```
Alert 3 fires after Week 4 full picture, NOT at Week 1.
Two-stage alert: Day 7 early estimate + Day 21 confirmed final.

### C2 — Gifting Package Cost
Full package landed cost (3–5 items) + packaging + shipping.
NOT just featured item COGS.
Typical: $120–240 landed cost + $25–60 packaging/shipping.

### C3 — Spark Ad Linkage
4–6 activations have corresponding Spark Ad campaigns.
Alert 3 includes Spark Ad revenue in total ROI calculation.
Creator handle links organic post → Spark Ad → attributed revenue.

### C4 — Variable Return Rates
Based on: audience_fit_score + content_format + discount_code presence.
NOT fixed by tier.
Reference rates:
  Try-on haul content: 35–45% return rate
  Styling content: 18–24% return rate
  GRWM: 25–32% return rate
  Discount code present: +8–12pp above base rate
  Audience fit score 5: -8pp below base rate
  Audience fit score 1: +15pp above base rate

### C5 — Seasonal Return Rate Adjustment
Summer/lightweight: base -4pp
Winter/outerwear: base +10pp
Holiday gifting: base +20pp
Applied on top of C4 variable rates.

### C6 — Non-Delivery Events (2–3 activations)
Late delivery: content arrives 7+ days late
Non-delivery: fee paid, content never posted
Zero/near-zero attributed revenue against real fee cost.
Alert 3 variant fires.
TikTok ban period (Jan 2024): one activation affected.

### C7 — Existing Customer Overlap
8–15% of Y2 influencer orders from existing customers (Klaviyo match).
Alert 3 adjusts: "True new customer acquisition: 123 orders vs 142 attributed."
Requires Klaviyo email match against Shopify orders.

### C8 — Cross-Activation Learning (Deliberate Variation)
3 micro activations: audience_fit_score=5, return rate 14–16%, ROI strongly positive
3 micro activations: audience_fit_score=2, return rate 35–40%, ROI negative
Pattern detectable by Month 18 for Moat 2 validation.

### C9 — Influencer Fraud Scenarios (2 activations)
Activation 1: Bought followers — near-zero Shopify UTM traffic despite high impressions.
  Alert: "0.013% CTR vs your 0.8% average — audience may not be real."
Activation 2: Engagement pod — high engagement, zero conversion.
  Diagnostic-only alert: "Engagement metrics inconsistent with conversion data."

### C10 — Geographic Mismatch (1–2 mid-tier activations)
International-skewed audience (55% US vs brand average 88%).
Fulfilment cost per order: $19.40 vs brand average $6.50.
Alert 3 fires with destination-adjusted fulfilment cost showing true margin-negative ROI.

### C11 — Sale Period Timing Bias (2 activations)
Overlap with summer sale or BFCM period.
Alert 3 flags: "67% of attributed orders used discount code. 
  True margin 31% lower than reported."

### C12 — TikTok Algorithm Change Q3 2024
TikTok organic reach: -35% July–September 2024 across all activations.
Suppression test — Alert 3 identifies platform cause not influencer underperformance.
brand_event_calendar entry: 'platform_algorithm_change' July 15 2024.

### C13 — Klaviyo Downstream Value (Critical Differentiator)
Each activation: non-converting visitors who sign up to Klaviyo list tagged with influencer UTM.
12-month email-attributed revenue traceable back to original influencer activation.
Alert 3 Layer 2: "Immediate attributed revenue: $12,000.
  Estimated 12-month email value from list signups: $4,200.
  True total ROI: 40.5x."
This is unique — no competitor shows this.

### C14 — Competitor Saturation (1 macro Y2 activation)
Pre-campaign competitor posting detected.
Lower CTR/conversion than expected.
Alert: "Check whether this creator posted for competing brands in prior 30 days."

### C15 — Inventory Whiplash (Post-Macro)
After each macro activation:
→ Stockout of featured sizes during campaign (Alert G1)
→ Return avalanche of same sizes 14 days later (Alert G2)
S and M sell out → returns of S and M arrive → overstock in S and M.
Two-alert chain seeded per macro activation.

### C16 — Creator Fee Inflation
Y2 fees 30% higher than Y1 for same tier.
Alert 3 in Y2: "ROI compressed vs Y1. Fee inflation of 28% is primary driver —
  performance metrics consistent with Y1."

### C17 — Attribution Model Architecture
Context-dependent attribution by alert type:
```
Alert A1:  Shopify source UTM (last meaningful click) — most conservative
Alert A5:  Order-level deduplication — first touchpoint wins on conflicts
Alert A3:  TikTok UTM + 14-day window, exclude Meta last-click on same order
Alert A6:  Shopify customer_id cohort analysis — attribution model irrelevant
```
Confirmation flow question (business framing, not technical):
"When a customer sees your TikTok content then buys after clicking a Meta ad,
 do you consider that a TikTok sale, a Meta sale, or both?"
Stored as `attribution_philosophy`: last_click / assisted / platform_reported

### C18 — Touchpoint Journey Table
New synthetic table:
```sql
CREATE TABLE client_azure_co.synthetic_touchpoint_journey (
    order_id            text not null,
    touchpoint_sequence integer not null,
    channel             text,
    touchpoint_date     date,
    touchpoint_type     text,  -- 'impression'/'click'/'email_open'
    campaign_id         text,
    influencer_id       text   -- nullable
);
```
35–45% of orders have multi-touch journeys seeded explicitly:
  20%: TikTok impression Day 1 → Meta click Day 3–5
  10%: Klaviyo email open → Meta retargeting click Day 2
  8%: TikTok influencer Day 1 → Direct visit Day 6
  7%: Three-channel journey (TikTok → Klaviyo → Meta)

### C19 — Attribution Confidence Scoring
Single clean UTM: Full confidence
Two-channel contested: Cap at 75%
Three-channel contested: Cap at 60%
No UTM (dark social): Cap at 50%
Dark social: 15–20% of orders permanently unattributable — flagged explicitly.

---

## ADDITIONAL STRUCTURAL DECISIONS (Categories 11–20)

### Cat 11 — Measurement Validity
ROAS revenue definition must be asked in confirmation flow:
"Do you include or exclude shipping revenue in ROAS? Gross or net of returns?"
Stored as `roas_revenue_definition` in client_config.
Alert naming: Use "Media Contribution Margin" not "Contribution Margin."

### Cat 12 — Statistical Validity
Use rolling 28-day window not static 3-month baseline.
Apply day-of-week adjustment before calculating thresholds.
Use median absolute deviation (MAD) not standard deviation.
Recalibrate thresholds monthly.

### Cat 13 — Causal Inference (Critical)
Seed multi-causal events: 8 events where two mechanisms operate simultaneously.
Seed confounded events: 4 events where apparent cause ≠ real cause.
Seed reversed causation: 2 events where direction of causation is opposite to graph assumption.
Seed no-causation events: 6 events where correlation exists but neither causes the other.

### Cat 14 — Human Behaviour
Thread_context must include:
- Confirmation bias leading to wrong approval (with outcome)
- Alert timing held vs immediate comparison
- Founder challenging numbers — agent defending with verifiable proof

### Cat 15 — PII Masking
All customer references use synthetic_customer_id throughout.
Separate lookup table for email matching (never passed to LLM).
Alert confidence reduced when PII masking limits match rate:
"Attribution confidence limited by PII masking — 43% of attributed orders linked."

### Cat 16 — API Scope Variability
Onboarding checks API scopes explicitly.
Missing scopes surfaced as prioritised setup actions.
Negative onboarding scenario: Shopify connected but read_inventory not granted.
`read_analytics`, `read_inventory`, `read_price_rules`, `read_reports` all checked.

### Cat 17 — Multi-Currency
All timestamps in source-appropriate timezone, converted to UTC before storage.
`presentment_money` in GBP/CAD/AUD for international orders.
Daily exchange rate variation ±0.8–1.2%.
DEBT-001 must be resolved before seeding.

### Cat 18 — Repeat Alert Escalation
First firing: Full Evidence Stack
Second firing (48h, same pattern): Shorter format + current vs initial metric
Third firing (72h): Escalation with estimated revenue impact
Post-third dismissal: "Should we stop monitoring this signal?"
6 scenarios across 24 months where same alert fires 3+ times.
alert_log tracks alert_instance_number and escalation_level.

### Cat 19 — External Benchmark Tables
Three new tables:
```sql
vertical_cpm_benchmarks       -- weekly CPM by vertical (seeded 2024–2026)
carrier_service_events         -- known carrier disruptions by date/zone
platform_algorithm_changes     -- dated log of Meta/TikTok/Google changes
```
These make Layer 2 Evidence Stack dramatically stronger.

### Cat 20 — Seasonal Business Model
`business_model_type` field in client_config:
  year_round / seasonal_heavy / event_driven
Seasonal brands: threshold calibration uses Q4 data not Q1.
Margin alerts suppressed Q1–Q3 for seasonal_heavy brands.
Asked as first confirmation flow question — determines calibration approach.

---

## REMAINING GAPS TO RESOLVE

Gaps D through G (original list):
- Gap D: TikTok ban data signature
- Gap E: Klaviyo flow architecture
- Gap F: Suppression scenarios list
- Gap G: DQ-to-alert interaction map

Plus:
- Gap H: Pull query scenarios (deferred to Step 10)
- Gap 1–6 resolutions (threshold calibration, outcome logging, onboarding scenario, 
  negative onboarding, Precision Profit Calendar table, thread context)

---

## KEY ARCHITECTURE DECISIONS (Locked)

- Archetype A only for Step 5 seed. B and D added in Step 7 as thin 6-month datasets.
- Archetype A: Premium Contemporary Womenswear, $150 AOV, $4M GMV Y1 → $5.2M GMV Y2
- Y1: June 2024 – May 2025 | Y2: June 2025 – May 2026
- COGS: Finaloop CSV path via sku_cost_master table. 75% coverage. Landed cost multiplier 1.28.
- Fulfilment: Weight-based formula. Brand-paid returns at $4.20 avg.
- Three archetype decision: A primary, B and D thin datasets Step 7.
- Manifest format: synthetic_data_manifest.json per event calendar entry.
- brand_event_calendar table: drives suppression logic in Agent A.
- No Finaloop Airbyte connector (no public API). Use CSV export → sku_cost_master.
- sku_cost_master table: effective dating for supplier cost changes.
- Alert fatigue arc: Months 6–9 rising dismiss rates. System self-calibrates Month 8.
