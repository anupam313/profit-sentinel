# Profit Sentinel — Seed Script Design Decisions
## Gaps F and G — Complete and Confirmed
### Date: 2026-05-16

---

## IMPORTANT: THIS FILE COVERS GAPS F AND G ONLY

Gap D (TikTok Disruption) and Gap E (Klaviyo Flow Architecture)
are in `seed_decisions_gap_d_e.md`.

Gap A, B, C decisions are in `gap_abc_decisions.md`.

All three files plus `technical_architecture.md` and `product_strategy.md`
must be in context when writing the Claude Code seed prompt.

---

## GAP F — SUPPRESSION SCENARIOS: COMPLETE SPECIFICATION

### F-Architecture — Four-State Suppression Model

```
State 1 — FIRE (full confidence):
  Signal crosses threshold AND no contextual explanation exists
  Full Evidence Stack delivered

State 2 — FIRE WITH CONTEXT (reduced confidence):
  Signal crosses threshold AND partial explanation exists
  Evidence Stack delivered WITH context note explaining what's 
  seasonally explained and what residual requires action

State 3 — SUPPRESS AND EXPLAIN:
  Signal crosses threshold BUT full explanation exists
  No alert fires. Suppression logged. Founder can query.

State 4 — SUPPRESS AND FLAG DATA:
  Signal crosses threshold BUT data quality is the explanation
  No business alert. H-series DQ alert fires instead.

brand_event_calendar extended fields:
  suppress_alerts         text[]    -- full suppression (State 3)
  context_alerts          text[]    -- partial context (State 2)
  context_explanation     text      -- what to include in Layer 2
  residual_threshold_pct  numeric   -- only fire if signal exceeds 
                                    -- seasonal explanation by this %
  confidence_decay_type   text      -- 'linear'/'step'/'exponential'
  confidence_decay_start  date
  confidence_decay_end    date
  confidence_at_peak      numeric
```

### F — Complete Suppression Scenario Library

```
S1 — Sale Period CPM Spike (REVISED — three tiers):
  CPM spike ≤40% above baseline: State 3 (expected BFCM/sale pressure)
  CPM spike 41–60% above baseline: State 2 with residual ROAS threshold
  CPM spike >60%: State 1 regardless of sale period
  Applies: July sale and BFCM both years

S2 — Collection Launch CPM Spike (REVISED — three tiers):
  Same three-tier structure as S1
  30% threshold (not 40%) — collection launches less inflationary than BFCM

S3 — Post-Holiday Return Spike (REVISED — two phases):
  Jan 1–21: State 3 (expected holiday returns)
  Jan 22–31: State 2 ("holiday explanation no longer applies. Root cause:")

S4 — Platform Disruption (TikTok):
  5 granular entries replacing 1 blunt entry (per Gap D7)

S5 — Election Period CPM Spike (REVISED — differential by campaign type):
  Prospecting CPM spike: State 3 (bidding against political advertisers)
  Retargeting CPM spike >15%: State 2 (beyond election explanation)
  Contribution margin: State 2 up to 18pp compression explained by election

S6 — Meta Attribution Window Break:
  Jan 12 – Feb 12 2026: State 3 suppress A1, A2, D1
  Post-Feb 12 2026: permanent caveat on pre/post comparison

S7 — Klaviyo Flow Modification (REVISED — metric-specific):
  Abandoned cart modification → suppress D5 on abandoned cart only
  Win-back modification → suppress E3 on win-back segment only
  Post-purchase modification → suppress E2 for 30 days (full purchase cycle)

S8 — Theme Update Sentry Spike (REVISED):
  First 48h: State 3 full suppression F1, F2
  After 48h: if errors persist on specific browser: State 2
    "Browser-specific rendering problem — test on [browser] specifically"

S9 — DQ Score Below Threshold:
  BFCM Gorgias tagging collapse: Alert 5 → State 4
  Meta CAPI failure dates: A1, A2 → confidence cap 58%
  Shopify sync outage: all alerts → H1 fires instead
  Sentry rate limiting BFCM: F1, F2 → full suppression

S10 — Back-to-School CPM Spike:
  August both years. State 3 for A3, B5.

S11 — Competitor Conquest Campaign Suppression (NEW):
  Prospecting CPM spike when retargeting CPM is stable
  = competitor activity (not platform-wide pressure)
  State 2: "Consider conquest campaign targeting competitor audiences"
  Fires: Month 9 and Month 21

S12 — iOS ATT Measurement Season (NEW):
  First 14 days of each quarter (January, April, July, October)
  All Meta ROAS alerts: ±15% uncertainty caveat added
  8 fires across 24 months (highest-frequency suppression)

S13 — Meta Learning Phase (NEW):
  Any campaign with >20% budget change or restructure
  State 3 suppression for 7–14 days
  6–8 fires across 24 months

S14 — TikTok Attribution Monthly Reset (NEW):
  Days 1–5 of each month: Alert A3 does not fire
  24 fires across 24 months

S15 — New Product Category Return Rate (NEW):
  Category-specific thresholds in client_config:
    return_rate_thresholds JSONB:
      "womenswear_casual": 0.28
      "womenswear_formal": 0.38 (Month 15+ formal occasion category)
      "menswear_casual": 0.22 (Month 20+ menswear)
      "accessories": 0.15

S16 — Influencer Campaign Return Window (NEW):
  Return rate rise ≤15pp above baseline during influencer window: State 3
  Return rate rise 16–25pp: State 2 (above expected for influencer)
  Return rate rise >25pp: State 1 (fire regardless)

S17 — Size Guide Implementation Suppression (NEW):
  14-day window post size_guide_update event
  State 3 suppress C3 (temporary return rise as customers act on info)
  Fires: Month 7, Month 14

S18 — Photography Change Return Spike (NEW):
  21-day window post photography_update event (Month 12)
  State 2 if return rate rise >8pp

S19 — Markdown Period Contribution Margin (NEW):
  Week 1–2 of markdown: State 3 for D1
  Week 3–4: State 2 — "if actual markdown depth > planned by >5pp: structural issue"

S20 — 3PL Transition Cost (NEW):
  One-time $3,950 transition costs in Month 15
  State 3 for D1 during Month 15
  Alert annotation: one-time cost excluded from structural margin

S21 — COGS Step Change (NEW):
  60-day window post supplier_cost_increase (Month 14 denim cost increase)
  State 2: "Full impact visible over 60 days as old inventory sells through"

S22 — A/B Test Suppression (NEW):
  F1, F4, F5 suppressed during active A/B tests
  Fires: Month 8, Month 14, Month 19

S23 — Klaviyo Send Traffic Spike (NEW):
  4-hour window post major campaign send to >5,000 subscribers
  F2: State 3 (server load from simultaneous traffic)
  F5: State 2 (use send-window-adjusted baseline)
  24–36 fires across 24 months (highest-frequency checkout suppression)

S24 — Shopify App Installation (NEW):
  24-hour window post app change
  F1, F2, F5 suppressed
  12–20 fires across 24 months

S25 — CDN and Hosting Event (NEW):
  3–4 Shopify infrastructure events across 24 months
  Month 4, Month 11, Month 19
  Alert H10 fires instead of business alerts

S26 — Planned Restock Stockout (NEW):
  G1 becomes State 2 decision support when confirmed restock within 7 days
  "Options: pause spend ($1,360 cost) vs continue (expected $2,400 waitlist revenue)"

S27 — Dead Inventory Write-Off (NEW):
  G2 suppressed during 48h post inventory count (January and July)

S28 — Carry-Forward Inventory (NEW):
  G2 never fires on SKUs tagged inventory_type = 'carry_forward'

S29 — Klaviyo Smart Send Time (NEW):
  D5 uses 7-day rolling revenue not daily when Smart Send Time active (Month 4+)

S30 — Klaviyo List Clean (NEW):
  D5 suppressed 14 days post list_clean event (Month 13)
  Annotation: "revenue per email sent improved — not a performance concern"

S31 — Post-BFCM Cohort Quality (NEW):
  E2 State 2 in January–February both years
  BFCM discount cohort excluded from repeat purchase rate comparison

S32 — VIP Seasonal Quiet (NEW):
  E3 suppressed November 15 – December 1 both years
  (inter-launch quiet period between FW wind-down and holiday gifting)

S33 — New Customer Surge Denominator Effect (NEW):
  E2 State 2 following viral moment or macro influencer activation
  "Denominator effect — monitor in [date when 90-day cohort matures]"
  
  VIRAL MOMENT CROSS-REFERENCES (Gap A13 events that trigger S33):
  Trigger 1 — Month 7 (December 2024): Holiday gifting newsletter feature
    800 new customers acquired in 72 hours (from ~30/day baseline)
    Total customers spikes from ~1,800 to ~2,600
    Repeat purchase rate drops from 35% to ~18% mathematically
    S33 suppresses E2 for 90 days (until December cohort matures)
    alert_log E2 entry: State 2, "New customer surge December 2024 newsletter feature.
      Denominator effect. Monitor repeat purchase rate from this cohort in March 2025."
    
  Trigger 2 — Month 18 (November 2025): Celebrity organic TikTok post during BFCM
    1,200 new customers acquired in 48 hours (exceptional viral event)
    Repeat purchase rate drops from 37% to ~14% mathematically
    S33 suppresses E2 for 90 days (until November cohort matures)
    February 2026: 90-day lookback on November cohort begins
    If repeat purchase rate from celebrity viral cohort is <20%: E2 fires normally
    If ≥20%: S33 suppression validated — celebrity audience has brand fit

S34 — Business Hours Delivery (NEW):
  Standard alerts: hold 10pm–8am, deliver 9am EST with detection timestamp
  Critical alerts (G1 active spend, F2 payment failure, E5 deliverability): immediate
  Monitor-and-wait: once per day at 9am

S35 — Duplicate Alert Root Cause (NEW):
  Alert dependency graph:
    F2 → suppresses F1, F5, A2, D1 (F2 is root, others are downstream)
    H1 → suppresses all alerts (data unreliable)
    E5 → suppresses E1, D5
    H6 → suppresses A1, A3, Alert3 for affected platform
  Root cause alert fires, downstream alerts suppressed with references

S36 — Founder Manual Override Learning (NEW):
  Dismissal reasons dropdown in Slack:
    "Already handling" → suppress 14 days, check outcome
    "Planned — not an issue" → "Add to event calendar?"
    "Data is wrong" → escalate to DQ investigation
    "Not actionable" → reduce threshold sensitivity by 10% (learning)

S37 — Recurring Calendar Rhythm (NEW):
  First Monday of each month: Meta ROAS spike (weekend pause restart)
  Last Friday of each quarter: finance reconciliation unusual orders
  January 1–3: New Year resolution traffic (suppress F3, F4)
  Valentine's week, Mother's Day week: gifting traffic suppresses D6

S38 — Explainability Threshold (NEW):
  variance_explained_pct field on all evaluated events
  >85%: State 3 (fully suppress)
  60–85%: State 2 (fire with context + residual)
  40–60%: State 1 (fire, note partial explanation)
  <40%: State 1 (fire with "no explanation found")

S39 — False Positive Learning Loop (NEW):
  24-month dataset includes:
    4 genuine false positives (alert was wrong — too sensitive)
    3 correctly dismissed correct alerts (founder was wrong to dismiss)
  alert_log distinguishes via outcome_confirmed + dismissal_reason = 'data_wrong'

  SPECIFIC FALSE POSITIVE EVENTS (seed as genuine agent errors):
  FP1 — Month 3 (August 2024): Alert B1 fires (creative fatigue)
    Reason: frequency hit 2.1 but CTR only declined 8% (not the 20% threshold)
    Founder dismisses: "data wrong — creative is fine"
    Outcome: CTR actually recovered within 3 days. Founder was correct.
    alert_log: outcome_confirmed = false, dismissal_correct = true
    
  FP2 — Month 8 (January 2025): Alert G2 fires (overstock risk on AZ-DRESS-067)
    Reason: inventory_levels showed 180 units but failed to detect 60 were reserved
      for wholesale order (SD6 draft order contamination — not filtered correctly)
    Founder dismisses: "data wrong — that stock is spoken for"
    Outcome: wholesale order shipped within 5 days. Founder correct.
    alert_log: outcome_confirmed = false, dismissal_correct = true, root_cause = 'SD6'
    
  FP3 — Month 14 (July 2025): Alert E2 fires (repeat purchase rate declining)
    Reason: BFCM Y1 cohort was being included in repeat purchase calculation
      but S31 suppression had not been correctly implemented
    Founder dismisses: "not actionable right now"
    Outcome: repeat purchase rate was genuinely declining for non-BFCM cohort.
    Founder was WRONG to dismiss. Moat 3 shows this 90 days later.
    alert_log: outcome_confirmed = true, dismissal_correct = false
    
  FP4 — Month 20 (January 2026): Alert A3 fires (channel ROAS reversal)
    Reason: TikTok attribution reset (S14) window — Days 1–5 of month
    Suppression S14 should have applied but failed (staleness event from S48)
    Founder dismisses: "TikTok always looks odd at start of month"
    Outcome: ROAS reversal was real — TikTok genuinely outperforming.
    Founder was WRONG to dismiss. Budget could have been reallocated.
    alert_log: outcome_confirmed = true, dismissal_correct = false

  CORRECTLY DISMISSED CORRECT ALERTS (founder wrong — alert was right):
  CD1 — Month 3 FP3 above (repeat purchase genuine decline dismissed)
  CD2 — Month 20 FP4 above (ROAS reversal opportunity missed)
  CD3 — Month 11 (April 2025): Alert G1 fires (stockout AZ-KNIT-022 during active spend)
    Founder dismisses: "we have stock coming"
    Restock delayed by 8 days (supplier issue). Brand spent $2,720 on ads to unavailable SKU.
    alert_log: outcome_confirmed = true, dismissal_correct = false,
      revenue_impact_missed: $2,720 wasted ad spend

S40 — Suppression Audit Trail Table (NEW):
  New table: suppression_log
  Fields: client_id, signal_detected_at, alert_type, signal_value,
    threshold_value, suppression_reason, suppression_category (S1–S50),
    suppression_state (2 or 3), variance_explained_pct, residual_signal,
    suppression_source (brand_event_calendar reference),
    would_have_fired_at, founder_queryable, created_at
  Every suppression has five mandatory explanation fields:
    detected_signal_description (what moved)
    threshold_context (why it matters)
    suppression_explanation (what explains it)
    residual_signal_description (what's unexplained — nullable for State 3)
    founder_verification_action (how founder can verify explanation)

S41 — Suppression Confidence Decay (NEW):
  Hard cutoff dates replaced with decay curves
  BFCM example:
    Nov 1–28: 100% confidence (State 3)
    Nov 29 – Dec 7: 70% confidence (State 2)
    Dec 8–14: 40% confidence (State 1 with context)
    Dec 15+: 0% (normal monitoring)

S42 — Suppression Stacking Rules (NEW):
  Rule 1: Highest confidence suppression wins as primary reason
  Rule 2: DQ suppression (S9) always overrides regardless of other suppressions
  Rule 3: State 2 + State 3 → escalates to State 3
  Rule 4: Multiple State 2 → use most conservative residual threshold
  suppression_stack JSONB field in suppression_log

  12 MULTI-SUPPRESSION EVENTS TO SEED (explicit enumeration):
  MS1  — Nov 27 2024 BFCM peak: S1 + S9 + S23 + S34 simultaneously
           (CPM spike + Gorgias DQ + Klaviyo send + business hours)
  MS2  — Nov 28 2024 BFCM + defective unit: S1 + S44 (component-level)
           (BFCM CPM suppresses, defective unit return component does NOT)
  MS3  — Nov 29 2024 post-BFCM: S1 (decay 70%) + S23 + S42 stacking test
  MS4  — Oct 15 2024 FW launch + iOS ATT: S2 + S12 simultaneously
           (Collection launch CPM + iOS ATT Q4 recalibration week 2)
  MS5  — Apr 8 2025 SS launch + iOS ATT: S2 + S12 simultaneously (Y2 equivalent)
  MS6  — Jan 13 2024 TikTok hard pause + return avalanche: S4 + S3
           (Platform disruption + post-holiday return period)
  MS7  — Nov 2024 BFCM + election aftermath: S1 + S5 overlap
           (BFCM sale period + election CPM pressure still active)
  MS8  — Aug 2024 back-to-school + app installation: S10 + S24
           (Back-to-school CPM + Shopify app change)
  MS9  — Jul 2024 summer sale + A/B test: S1 + S22
           (Sale period + checkout A/B test active)
  MS10 — Mar 2025 SS launch + meta learning phase: S2 + S13
           (Collection launch CPM + Meta budget scale-up learning phase)
  MS11 — Oct 2024 FW launch + competitor activity: S2 + S11
           (Collection launch CPM + competitor conquest detected)
  MS12 — Nov 2025 BFCM Y2 + Klaviyo restructure aftermath: S1 + S7
           (BFCM + Klaviyo flow modification effects still in recovery)

S43 — Suppression Gaming Detection (NEW):
  A/B test running >42 days without conclusion: alert fires
  Flow modification >1 per 14 days for same flow: 4th loses suppression
  brand_event_calendar entries with no corresponding data signal: flagged
  2 gaming detection scenarios seeded: Month 10 and Month 17

S44 — Cascading Suppression Failure Prevention (NEW):
  D1 decomposed into components before suppression:
    CPM contribution: suppressible by S1, S2, S5, S10
    Return rate contribution: suppressible by S3, S15, S16
    COGS contribution: suppressible by S21
    Discount depth contribution: suppressible by S19
    Operational cost contribution: suppressible by S20
  Suppression applies per component, not per alert type
  
  BFCM + DEFECTIVE UNIT SCENARIO (Month 6, November 2024) — EXACT PARAMETERS:
  Date: November 28 2024 (BFCM peak)
  S1 suppression applies to: CPM component of D1 (CPM spike 52% above baseline)
  Simultaneously: supplier shipped defective units of AZ-KNIT-031 (wrong fabric weight)
  
  Defective unit data signature:
    SKU: AZ-KNIT-031 (FW hero knitwear)
    Units affected: 180 units shipped to warehouse, all defective
    Defect detected: Gorgias quality complaints spike November 28–December 4
    Gorgias tags: 'product_quality' rising from 4% to 18% of tickets
    Loop Returns: return_reason = 'quality_issue' spikes on AZ-KNIT-031 only
    Return rate on AZ-KNIT-031: 61% (vs 22% catalogue average)
    
  What component-level suppression must detect:
    CPM component of D1: suppressed (BFCM S1 explains it — State 3)
    Return rate component of D1: NOT suppressed (defective unit, not seasonal)
    D1 fires: "Contribution margin compressed. CPM pressure is seasonal (suppressed).
      However: AZ-KNIT-031 return rate is 61% vs 22% average —
      this is a quality issue not a BFCM pattern. 180 units at risk.
      Contact supplier immediately for credit claim."
      
  If component-level suppression NOT working (failure mode being tested):
    D1 would be fully suppressed (BFCM S1 covers everything)
    Defective unit problem goes undetected for 10 days
    Brand loses supplier credit claim window
    340 returns processed without explanation
    
  Seed requirement: AZ-KNIT-031 defect event must be in brand_event_calendar
    as 'supplier_quality_event' NOT as a sale_period or seasonal event.
    This ensures S1 suppression does NOT cover the return_rate component.

S45 — Predictive Suppression (NEW):
  Pre-suppress alerts 14 days before collection launches (4 times)
  Pre-suppress alerts 7 days before sale periods (4 times)
  October 1 both years: Q4 seasonal CPM pressure pre-suppression
  Notify founder: "CPM alerts pre-suppressed for [window]. All other alerts active."
  predictive_suppression_log entries (suppression_type = 'predictive')

S46 — First-Season Learning Protocol (NEW):
  Y1 BFCM: 3 pre-event questions (when does your BFCM start?
    what is average discount depth? pre-BFCM email subscriber window?)
  Answers stored as event_profile in brand_event_calendar
  Y2 BFCM: auto-populated from Y1 actual data. No questions. More precise window.
  Demonstrates system intelligence improving each season.

  ARCHETYPE A PRE-EVENT ANSWERS (Y1 BFCM — exact seed values):
  Q1: "When does your BFCM promotion start?"
    Answer: November 20 2024 (early access for email subscribers)
    Public start: November 28 2024 (Black Friday)
    event_profile.bfcm_start_email: 2024-11-20
    event_profile.bfcm_start_public: 2024-11-28
    
  Q2: "What is your average BFCM discount depth?"
    Answer: 25% off sitewide + 30% off clearance
    event_profile.bfcm_discount_depth_standard: 0.25
    event_profile.bfcm_discount_depth_clearance: 0.30
    Impact on D1 suppression: margin alerts suppressed when margin drop
    is consistent with 25% discount applied to revenue
    
  Q3: "Do you have a pre-BFCM window for email subscribers?"
    Answer: yes — November 20 email-only access, 48 hours before public
    event_profile.bfcm_email_early_access: true
    event_profile.bfcm_email_early_access_hours: 48
    Impact: Klaviyo send spike begins November 20, not November 28
    S23 (Klaviyo send traffic suppression) must begin November 20

  Y2 BFCM auto-populated from Y1:
    brand_event_calendar Y2 BFCM entry uses Y1 event_profile values
    Suppression window: November 20–December 2 2025 (more precise than generic Nov 25–28)
    No pre-event questions sent to founder

  DEFAULT VALUES IF FOUNDER DOES NOT ANSWER (seed script fallback):
  If pre-event questions are not answered within 7 days of BFCM start:
    event_profile.bfcm_start_email: same as bfcm_start_public (no early access assumed)
    event_profile.bfcm_start_public: 2024-11-28 (Black Friday — hardcoded universal date)
    event_profile.bfcm_discount_depth_standard: 0.20 (conservative default)
    event_profile.bfcm_discount_depth_clearance: 0.25
    event_profile.bfcm_email_early_access: false
  Suppression window defaults to: November 25–December 2 (generic)
  All S1/S5/S19 suppressions use the default discount depth (0.20) for threshold calculation
  Note in suppression_log: "Using default BFCM profile — founder did not complete pre-event setup"

S47 — Multi-Stakeholder Suppression Communication (NEW):
  State 2 suppressions communicated differently by role:
    Founder: full suppression explanation + residual + verification action
    Marketing manager: simplified version with specific action items
    Agency: technical details with campaign IDs and exact metrics
  Thread_context pre-seeded conversation demonstrates multi-stakeholder example

S48 — Suppression System DQ Problem (NEW):
  brand_event_calendar new fields:
    detection_method (auto / manual / hardcoded)
    detection_lag_hours (hours after event start it was logged)
    confidence (0–1 that event is still ongoing)
    last_verified_at (when entry last confirmed current)
  4 brand_event_calendar staleness events seeded:
    Month 3: sale period end date wrong by 2 days
    Month 7: supplier delay not logged until Day 3
    Month 11: influencer campaign date entered 1 week off
    Month 19: holiday period expires Dec 25 but campaigns run to Dec 31

S49 — Time-Sensitive Suppression Override (NEW):
  3 suppression invalidation events:
    Month 4: G1 suppressed due to confirmed restock → restock delayed
      → suppression invalidated → G1 fires escalated severity
    Month 15: D5 suppressed due to flow modification → flow found broken
      → invalidated → D5 fires
    Month 20: C3 suppressed post-holiday → defect batch returns arrive
      → invalidated → C3 fires
  suppression_invalidation_check process monitors conditions throughout window

S50 — Alert Retraction Mechanism (NEW):
  H18 fires when: DQ issue discovered affecting data from alert fired in
  previous 24 hours.
  Suppression type: 'retraction' (post-hoc correction, not forward-looking suppression)
  suppression_log entry for retractions includes:
    suppression_category: 'S50_retraction'
    original_alert_log_id: references the alert being retracted
    retraction_reason: specific DQ issue that invalidated the data
    provisional_revised_value: best estimate after accounting for data gap
    full_accuracy_expected_at: when DQ issue will resolve and true figure available
  2 retraction events seeded:
    Month 6 (Nov 28 2024 BFCM): Alert A1 fired 6am → Shopify webhook fails 8am
      → H18 fires 8am: "Alert A1 ROAS figure (2.1x) may be based on incomplete data.
         Shopify webhook failed 2h after alert fired. Missing orders from 6am–8am window.
         Provisional revised ROAS range: 2.0–2.3x.
         Full accuracy when Shopify sync recovers (estimated 4–6 hours)."
    Month 13 (Jun 2025): Alert C3 fired 9am → Loop Returns freshness issue detected 11am
      → H18 fires 11am: "Alert C3 return rate (31%) may be understated.
         Loop Returns data is 18h stale due to high return volume.
         True rate may be 31–36%. Full accuracy in approximately 6 hours."
```

---

## GAP G — DQ-TO-ALERT INTERACTION MAP: COMPLETE SPECIFICATION

### G-Architecture — Multi-Dimensional DQ Model

```
REPLACES single DQ score in client_config with:

CREATE TABLE client_azure_co.dq_metric_scores (
    id                   bigint generated always as identity primary key,
    client_id            text not null,
    source               text not null,
    metric_domain        text not null,
    dq_score             numeric not null,
    dq_issues            text[],            -- specific issues affecting this domain
    alert_types_affected text[],            -- which alerts use this metric domain
    confidence_cap       numeric,           -- maximum confidence for affected alerts
    freshness_tier       text,              -- 'realtime' / 'batch' / 'daily'
    effective_from       timestamptz,
    effective_to         timestamptz,       -- null = currently active
    created_at           timestamptz default now()
);

metric_domain values:
  'orders' / 'inventory' / 'customers' / 'refunds' /
  'ad_performance' / 'attribution' / 'flow_performance' /
  'ticket_volume' / 'ticket_tags' / 'funnel_performance' /
  'error_rate' / 'cross_source_attribution'

Weighted confidence calculation per alert:
  Each alert has source weights summing to 1.0
  Alert_confidence = SUM(source_dq_score × source_weight)
  
  Example Alert A1 weights:
    Shopify orders: 0.40
    Shopify refunds: 0.25
    Meta attribution: 0.20
    TikTok attribution: 0.10
    Loop Returns: 0.05
  
  alert_log stores per-source DQ scores at firing time
  and the weighted confidence calculation
```

### G — Complete DQ Issue Library

```
SHOPIFY DQ ISSUES:

SD1 — Shopify Webhook Delivery Failure:
  3 seed events: Month 4 (6h), Month 6 BFCM (4h), Month 18 BFCM Y2 (3h)
  metric_domain: 'orders'
  dq_score during failure: 0–30
  confidence_cap: 75%
  cascade_to: Klaviyo post-purchase flows, Loop Returns matching, GA4 joins
  cascade_lag_hours: 1 | cascade_duration: 6

SD2 — Multi-Location Inventory Discrepancy:
  Monthly inter-location transfer events (48h window each)
  metric_domain: 'inventory'
  dq_score during transfer: 68
  G1 may suppress incorrectly (phantom stock). G2 may fire incorrectly.

SD3 — Returns Reconciliation Lag:
  January both years (12–36h refund data stale)
  metric_domain: 'refunds'
  dq_score January: 81
  confidence_cap: 82% on A1, C3, D1

SD4 — Customer Merge Data Loss:
  Ongoing (~4% of customers affected by merges)
  metric_domain: 'customers'
  confidence_cap: 85% on cohort analysis

SD5 — Tax Calculation Inconsistency:
  UK VAT-inclusive vs US tax-exclusive
  metric_domain: 'orders' (revenue figures)
  dq_score: 91
  confidence_cap: 90% on UK vs US revenue comparison
  dbt model must extract tax-exclusive revenue from presentment_money

SD6 — Draft Order Contamination:
  Wholesale, influencer gifting, CS replacement orders
  metric_domain: 'orders'
  filter: orders where source = 'draft_order'
  Affects: A1 (organic ROAS inflated), D6 (AOV skewed), C3 (return rate lowered)

META DQ ISSUES:

MD1 — Advantage+ Audience Overlap:
  Ongoing from Month 3 (multiple A+ campaigns running)
  metric_domain: 'ad_performance' / 'attribution'
  dq_score: 79
  confidence_cap: 80% on campaign-level ROAS

MD2 — Meta API Rate Limiting:
  3 events: Month 6 BFCM (14h), Month 9 Valentine's (6h), Month 18 BFCM Y2 (10h)
  metric_domain: 'ad_performance'
  dq_score: 65
  confidence_cap: 70%

MD3 — R&F vs Auction Campaign Incompatibility:
  Month 10 (March 2025): one R&F brand awareness campaign
  Filter R&F campaigns from Auction-based metric calculations

MD4 — Creative Hub Mockup Contamination:
  Month 2–3: 3 mockups in pipeline. Detected and filtered Month 3.
  Filter: ad_id where creative_type = 'mockup'

MD5 — Offline Conversion Upload Timing:
  Month 5 and Month 17 (pop-up events)
  ROAS figures change retroactively after upload
  alert_log records pre- and post-upload figures

TIKTOK DQ ISSUES:

TD1 — Spark Ad vs In-Feed Attribution Mixing:
  Ongoing (both types run from Month 1)
  dq_score: 78 when running both
  confidence_cap: 80% on TikTok blended ROAS
  Calculate Spark and In-Feed ROAS separately

TD2 — TikTok Data Sharing Agreement Expiry:
  Month 12 (May 2025): 4-day complete data gap
  Alert H6 fires. Brand re-authorises.

TD3 — Creator Marketplace vs Ads Manager:
  Ongoing for mid/macro activations
  Ads Manager authoritative for ROAS.
  TCM data for organic amplification metrics only.

TD4 — TikTok Attribution Window Ambiguity:
  Historical data pre-Month-1: 7-day view applied (old default)
  Month 1: window corrected to 1-day
  Pre-Month-1 ROAS figures: confidence_cap 70%

KLAVIYO DQ ISSUES:

KD1 — Property Sync Race Condition:
  4–6 flash sale events across 24 months
  dq_score: 81 during flash sales
  confidence_cap: 82% on attribution during flash sales

KD2 — Unsubscribe State Propagation Delay:
  15–60 minute lag. dq_score: 96 (minor).
  Don't attempt real-time unsubscribe monitoring.

KD3 — Revenue Currency Reporting:
  89% DQ score for international-heavy periods
  Use Shopify shop_money as authoritative revenue figure

KD4 — A/B Test Control Group Contamination:
  Month 6 A/B test: 12% contamination rate in control group
  confidence_cap: 80% on flow performance during test

KD5 — Predictive CLV Model Version Changes:
  Month 12 (May 2025): Klaviyo model update
  Detection: >15% of profiles with >20% CLV change
  confidence_cap: 80% for 30 days post-update

GORGIAS DQ ISSUES:

GD1 — Ticket Merging Attribution Loss:
  2–4% of tickets merged per month
  root_ticket_id as deduplication key

GD2 — Automated Response Contamination:
  Month 5 (October 2024): brand enables automations
  22% apparent ticket volume spike — actually automation-created
  Filter: tickets where first_response_type = 'automated' AND no human response

GD3 — Multi-Channel Ticket Deduplication:
  5% deduplication failure rate
  Deduplicate on customer_email + created_within_24h window

GD4 — CSAT Survey Response Lag:
  24–96h lag. CSAT as 7-day rolling metric only. Never real-time.

GD5 — Agent Tag Inconsistency:
  dq_score: 71–78%
  tag_normalisation table required with 40–60 entries
  Primary source of Alert 5 false positives
  Example mappings:
    'runs small' → 'sizing_issue'
    'runs small — tops' → 'sizing_issue_tops'
    'fit issue — tops' → 'sizing_issue_tops'
    'too small' → 'sizing_issue'
    'too big' → 'sizing_issue'
    'sizing' → 'sizing_issue'

GD6 — CSAT vs NPS Transition:
  Month 10 (March 2025): brand switches to NPS
  dq_score: 60 during transition month
  Trend analysis restarts from Month 10 baseline

GA4 DQ ISSUES:

GD7 — Session Stitching Failure:
  18% of purchases cross-device (mobile discover, desktop purchase)
  confidence_cap: 85% on GA4 conversion analysis
  Caveat: always included in F-series alerts

GD8 — Bot Traffic Contamination:
  5–12% of sessions. Spikes during viral moments (Gap A13).
  Filter: sessions where duration <5s AND pages=1 AND no events fired

GD9 — GA4 Enhanced Ecommerce Implementation Gaps:
  Month 1–3: add_to_cart double-firing, Shop Pay begin_checkout missing
  dq_score: 76
  Month 3: add_to_cart fixed (theme update)
  Month 8: Shop Pay GA4 event added
  H12 fires until Month 8 (GA4 purchase count vs Shopify order count gap)

GD10 — GA4 Lookback Window Data Revision:
  Data <7 days old: dq_score 81
  Data >7 days old: dq_score 96
  Cross-source alerts use minimum 7-day-old data for historical analysis

LOOP RETURNS DQ ISSUES:

LD1 — Exchange Order Attribution:
  8% of orders are exchanges (not new purchases)
  Filter from ROAS, AOV, E2 repeat purchase calculations
  order_source = 'loop_exchange' or order_note contains 'exchange'

LD2 — Partial Refund Complexity:
  12% of returns are partial (one item from multi-item order)
  Item-level COGS allocation required
  Return rate calculated at item level, not order level

LD3 — Loop Data Freshness During High Volume:
  January both years: 12–24h data lag
  confidence_cap: 80% on return-dependent alerts in January

SENTRY DQ ISSUES:

SentD1 — Sentry Event Sampling:
  10–20% sampling rate
  Multiply Sentry error rates by 1/sample_rate for estimated actual rate
  Use for trend direction, not absolute rate

SentD2 — Sentry Release Tag Inconsistency:
  Month 1–4: no release tags configured
  All Sentry alerts: diagnostic-only (cannot confirm deployment cause)
  Month 5: release tags configured (after recommendation)

CROSS-SOURCE DQ ISSUES:

XD1 — Customer Identity Resolution Failure Rate:
  Match rates:
    Shopify ↔ Klaviyo: 91%
    Shopify ↔ Meta: 47% (hashed email)
    Shopify ↔ TikTok: 31% (device-based)
    Shopify ↔ Gorgias: 84%
    Shopify ↔ Loop Returns: 96% (order ID-based)
    Klaviyo ↔ GA4: 0% (impossible without bridge)
  All cross-source alerts state match rate in Layer 2

XD2 — Timezone Normalisation:
  All timestamps normalised to UTC at ingestion
  All cross-source joins use UTC dates not source-native dates
  DST transition flag: twice per year (March, November) — 2-hour caveat window

XD3 — Revenue Reconciliation Gap:
  Normal week: claimed revenue 188% of Shopify actual
  BFCM: claimed revenue 229% of Shopify actual
  Seeded accurately per channel and period
  Alert A1 is specifically designed to resolve this gap

XD4 — Pipeline Orchestration Gap:
  Maximum gap: Sentry (real-time) vs GA4 (up to 4 days stale) = 7 days
  All cross-source joins use stalest source's time window

XD5 — Schema Evolution Incompatibility:
  Month 3: Shopify renames presentment_money structure
    18-hour staging model break. H1-variant fires.
  Month 10: Meta changes ad_set naming convention
    5-day incorrect campaign groupings. A2 fires incorrectly.
    DQ flag: "Meta schema change — campaign-level analysis may be incorrect"
  Month 21: Gorgias adds new ticket_channel field
    Additive change — no impact. H16 fires as information only.
```

### G — New H-Series Alerts (H11–H19)

```
H11 — Meta CAPI Event Match Quality Degradation:
  Fires when: Meta Event Match Quality score drops below 7.0
  Action: "Check email hashing consistency between Shopify and CAPI"

H12 — GA4 Implementation Validation:
  Fires when: GA4 purchase count deviates >5% from Shopify order count (7 days)
  Action: specific missing event types identified and listed

H13 — Loop Returns-Shopify Revenue Reconciliation:
  Fires when: Loop refund total deviates >3% from Shopify refunds
  Action: "Check Loop Returns-Shopify integration settings"

H14 — Tag Normalisation Coverage:
  Fires when: >15% of Gorgias tickets have unmapped tags
  Action: lists specific unmapped tags requiring addition to normalisation table

H15 — Pipeline Orchestration Lag Exceeded:
  Fires when: any source sync is >2× scheduled interval behind
  Action: business alerts using that source capped at 70% confidence

H16 — Schema Change Detected:
  Fires on: any new/renamed/removed column in any source
  Additive change: informational
  Breaking change (renamed/removed): affected alerts listed, manual review required

H17 — Financial Reconciliation Gap (NEW):
  Fires when: pipeline spend deviates from billing statement by >$1
  2 seed events: Month 4 Meta ($22 gap), Month 15 TikTok ($12 gap)
  Action: investigate API rounding or missing records

H18 — Alert Retraction/Revision (NEW):
  Fires when: DQ issue discovered affecting data from alert fired in previous 24h
  States: which alert affected, revision range, when full accuracy restored
  2 seed events: Month 6 BFCM (A1 retraction), Month 13 (C3 partial retraction)

H19 — DQ Improvement Opportunity (NEW):
  Proactive, scheduled — NOT threshold-triggered
  Fires: Month 1, Month 6, Month 12
  Content: specific action, estimated DQ improvement, time-to-implement
  Month 1: "3 addressable gaps — estimated +14 DQ points, 4 hours total"
  Month 6: "Post-BFCM DQ review — 3 improvements for next BFCM, +18 points"
  Month 12: "Annual review — top 3 persistent issues ranked by impact on accuracy"
```

### G — DQ Additional Architecture Decisions

```
G-Add-1 — DQ Issue Interdependency Cascades:
  dq_events fields: cascade_to, cascade_lag_hours, cascade_duration
  
  6 CASCADING CHAINS WITH EXACT TIMING VALUES:
  
  Chain 1 — BFCM Shopify webhook failure (SD1 → KD cascade, LD cascade, GA4 cascade):
    Primary: SD1 (Shopify webhook, 4 hours, BFCM)
    cascade_to: ['KD_flow_trigger', 'LD_order_match', 'GA4_session_join']
    cascade_lag_hours: 1    (Klaviyo sync runs hourly — misses the gap)
    cascade_duration_hours: 6 (downstream sources take 6h to fully recover after primary)
    Effect: post-purchase flows don't fire, Loop Returns can't match orders, GA4 joins break

  Chain 2 — Meta CAPI failure → Alert A1 data gap → Alert D1 calculation error:
    Primary: Meta CAPI deduplication failure (3 dates in Y1)
    cascade_to: ['A1_data_gap', 'D1_margin_calc_error']
    cascade_lag_hours: 24   (Meta CAPI failures take 24h to propagate to attribution data)
    cascade_duration_hours: 72 (attribution data remains corrupted until next Meta sync cycle)
    Effect: A1 fires with wrong ROAS, D1 margin calculation uses incorrect attributed spend

  Chain 3 — Klaviyo flow modification → Shopify revenue discrepancy → D5:
    Primary: Klaviyo flow modification (Month 9 abandoned cart rebuild)
    cascade_to: ['shopify_revenue_discrepancy', 'D5_false_decline']
    cascade_lag_hours: 2    (Klaviyo revenue discrepancy appears on next Shopify sync)
    cascade_duration_hours: 336 (14 days — duration of flow_modification suppression window)
    Effect: Shopify order revenue doesn't match Klaviyo claimed flow revenue for 2 weeks

  Chain 4 — Loop high volume lag → Shopify refund reconciliation → A1 confidence:
    Primary: LD3 (Loop data freshness, January both years)
    cascade_to: ['shopify_refund_reconciliation', 'A1_confidence_degraded']
    cascade_lag_hours: 12   (Loop lag is 12-24h; Shopify refunds then can't reconcile)
    cascade_duration_hours: 36 (resolves when Loop catches up + reconciliation runs)
    Effect: A1 true post-return ROAS is based on incomplete return data

  Chain 5 — GA4 implementation gap → Sentry error correlation failure → F2 accuracy:
    Primary: GD9 (GA4 Enhanced Ecommerce gaps, Month 1-8)
    cascade_to: ['sentry_correlation_failure', 'F2_checkout_accuracy_degraded']
    cascade_lag_hours: 0    (immediate — GA4 missing events means cross-source join fails instantly)
    cascade_duration_hours: 5256 (220 days = Month 1 through Month 8 when fixed)
    Effect: F2 payment gateway alert can't correlate Sentry errors to GA4 checkout sessions

  Chain 6 — Schema evolution incompatibility → multiple source misalignment:
    Primary: XD5 (Meta schema change Month 10 — ad_set naming convention)
    cascade_to: ['A2_misattribution', 'B1_wrong_frequency', 'B5_wrong_cpm']
    cascade_lag_hours: 0    (immediate — dbt model produces wrong groupings from first run)
    cascade_duration_hours: 120 (5 days until dbt model manually fixed)
    Effect: A2, B1, B5 all fire on incorrect campaign groupings

G-Add-2 — DQ False Recovery Problem:
  Recovery tail seeded for every DQ event (not instant restoration)
  Fields: recovery_duration_hours, recovery_dq_curve (JSONB), 
          backlog_order_count, backlog_processing_lag
  Example SD1 recovery: Hour 0–6: 0–30, Hour 6–8: 60–75, Hour 8–12: 85–90, Hour 12+: 96

G-Add-3 — Undetectable DQ Issues:
  External validation check 1: expected record count validation
    If deviation >20%: H16-variant "possible silent truncation"
  External validation check 2: financial reconciliation (H17)
  External validation check 3: DST transition flag
    Twice per year (March, November): 2-hour timestamp caveat window

  FINANCIAL RECONCILIATION GAP MECHANISM (missing from original):
  How the gap is generated in seed data:
  Meta API returns spend figures rounded to 2 decimal places per row.
  Actual billing uses 6 decimal places per impression event.
  Formula: rounding_error_per_row = actual_micro_spend - round(actual_micro_spend, 2)
  Over 18,420 ad rows: cumulative rounding error = $18–26 (approx $22 for Month 4)
  
  Seed implementation:
    meta_ad_performance.spend: rounded to 2 decimal places (what API returns)
    meta_billing_statement.total_spend: exact 6-decimal figure (from Finaloop)
    Gap: meta_billing_statement - sum(meta_ad_performance.spend) = $22.14
    H17 fires: "Pipeline Meta spend $18,420.00, billing shows $18,442.14.
      Difference: $22.14. This is consistent with API rounding accumulation.
      No missing records detected. This is a known limitation of Meta's API."
  
  Month 4 (Sep 2024): Meta gap $22.14 — H17 fires as informational
  Month 15 (Aug 2025): TikTok gap $11.87 — H17 fires as informational
  Both: H17 severity = 'informational' (not 'warning') because mechanism is understood

G-Add-8 — Consent and Privacy DQ Layer:
  GDPR deletion requests: 2–4 per month from Month 1
  shopify_customers fields: gdpr_deleted_at, gdpr_deletion_marker = true
  
  EXACT CROSS-SOURCE ORPHAN STRUCTURE:
  When a GDPR deletion request is processed, each source handles differently:
  
  Shopify (PARTIAL deletion):
    shopify_customers row: deleted (customer_id no longer exists)
    shopify_orders rows: RETAINED but customer_id set to null
      gdpr_deletion_marker = true on affected orders
    shopify_order_line_items: retained (no PII)
    Result: orphaned orders with null customer_id — revenue data intact, customer gone
  
  Klaviyo (FULL deletion):
    klaviyo_profiles row: deleted entirely
    klaviyo_email_events rows: deleted entirely (contains email)
    Result: all flow attribution for this customer is lost
    Impact on D5: flow revenue for deleted customer's orders cannot be attributed
    
  Gorgias (FULL deletion):
    gorgias_tickets rows: deleted entirely (contains email, name)
    Result: historical ticket data for this customer removed
    Impact on Alert 5: this customer's sizing complaints removed from velocity calculation
    
  Loop Returns (PARTIAL deletion):
    loop_returns rows: customer_email nulled, customer_id nulled
    return_reason and SKU data: RETAINED (no PII)
    Result: orphaned return records with no customer linkage
    Impact on C3/C7: return exists but cannot be linked to customer cohort
    
  GA4 (FULL deletion):
    GA4 deletes user-level data on request (takes 30 days to process)
    session data: retained but user_id removed
    Result: sessions appear as anonymous after deletion
    
  SEED REQUIREMENT:
  Monthly GDPR deletion batch: 2–4 customers deleted per month from Month 1
  For each deleted customer, seed the asymmetric orphan structure above:
    Shopify: order rows retained, customer_id = null, gdpr_deletion_marker = true
    Klaviyo: profile and event rows removed
    Gorgias: ticket rows removed
    Loop: return rows retained, customer fields nulled
  Alert logic: all customer-dependent metrics must filter gdpr_deletion_marker
  Layer 2 caveat on any cohort analysis:
    "Excludes [N] customers who exercised GDPR deletion rights.
     Cohort analysis may understate figures by up to [X]%."
  DQ score model: 97 - (0.5 × monthly_deletion_count)
    Example: 4 deletions/month → DQ score 95 for customer-dependent metrics

G-Add-4 — DQ Communication Asymmetry:
  Scenario A: DQ issue detected, no active business alerts affected.
    H-series alert fires. Low urgency.
    "FYI: Shopify sync is 8 hours behind."
  Scenario B: DQ issue detected, alert in queue to fire today.
    H-series alert fires. High urgency.
    "Critical: Shopify sync 8h behind. Alert A1 cannot fire accurately.
     Expect A1 once sync recovers."
  Scenario C: DQ issue discovered post-alert (alert already fired).
    H18 (Alert Retraction) fires immediately.
    "Critical: Shopify sync failed 2h after Alert A1 fired.
     Alert A1 may be incomplete. Treat as provisional."

  SEED EVENTS WITH EXACT alert_log PARAMETERS:
  
  Scenario A — Month 2 (July 22 2024):
    DQ event: Shopify sync 8h behind (minor delay, no orders missing)
    No business alerts queued at this time
    H15 fires: severity = 'informational'
    alert_log entry: {alert_type: 'H15', severity: 'informational',
      scenario: 'A_no_active_alerts', sync_lag_hours: 8,
      business_alerts_queued: 0, action_required: false}
    
  Scenario B — Month 9 (February 18 2025):
    DQ event: Shopify sync 10h behind (webhook queue backup from Valentine's volume)
    Alert A2 was queued to fire at 9am that morning
    H15 fires: severity = 'high'
    Alert A2 suppressed for 12 hours
    Sync recovers 9pm. A2 fires at 9pm with note:
      "Delivered 12h late — Shopify sync delay on February 18."
    alert_log entries:
      {alert_type: 'H15', severity: 'high', scenario: 'B_alert_in_queue',
       queued_alert_type: 'A2', delivery_delayed_hours: 12}
      {alert_type: 'A2', delivered_at: '2025-02-18 21:00',
       delivery_delayed_hours: 12, delay_reason: 'shopify_sync_lag'}
    
  Scenario C: Already seeded — Month 6 BFCM (A1 retraction) and Month 13 (C3 partial)

G-Add-5 — DQ Benchmarks in network_pattern_benchmarks:
  Per source: median, P25 (poor), P75 (good), BFCM typical
  Reference values:
    Shopify: median 94, P25 87, P75 97, BFCM 81
    Meta: median 82, P25 71, P75 89, BFCM 68
    TikTok: median 79, P25 68, P75 86, BFCM 71
    Klaviyo: median 91, P25 84, P75 95, BFCM 79
    Gorgias: median 77, P25 68, P75 83, BFCM 61
    GA4: median 84, P25 76, P75 90, BFCM 81
    Loop Returns: median 89, P25 82, P75 93, BFCM 74
    Sentry: median 88, P25 80, P75 93, BFCM 72
  Every H-series alert references relevant benchmark in Layer 2

G-Add-6 — Proactive DQ Improvement Recommendations (H19):
  Fires at Month 1, Month 6, Month 12 on schedule
  Month 1 example actions: Sentry release tags, GA4 Shop Pay event, 
    Gorgias CSAT→NPS switch
  Month 6: pre-authorise 6 months TikTok Spark Ads, increase Nov Airbyte frequency,
    pre-build BFCM Gorgias tag normalisation
  Month 12: Meta CAPI first-party data (47%→71% match rate),
    Gorgias agent tag training (74%→89% coverage),
    GA4 User ID implementation (31%→18% cross-device gap)

G-Add-7 — Data Lineage Tracking:
  New table: alert_data_lineage
  Fields: alert_log_id, source, metric_name, metric_value,
    source_row_ids (text[]), source_query (SQL), row_count,
    date_range_start, date_range_end
  Every true positive alert has corresponding lineage rows
  manifest.json includes lineage row IDs alongside alert_log IDs
  Enables founder verification: "show me the orders in this ROAS figure"

G-Add-9 — Real-Time vs Batch DQ Tiers:
  freshness_tier field on dq_metric_scores: 'realtime' / 'batch' / 'daily'
  Real-time critical alerts (G1, F2, H6, E5): need <30 minute freshness
  15-minute polling for hero SKU inventory (top 20 SKUs by ad spend)
  Freshness mismatch caps confidence regardless of other DQ scores

G-Add-10 — Permanent DQ Limitations Table:
  New table: permanent_dq_limitations (in public schema)
  5 permanent limitations seeded:
    1. Dark social attribution: 15–20% orders unattributable (is_resolvable: false)
    2. Cross-device session gap: 18% journeys unstitched (is_resolvable: partial)
    3. View-through attribution uncertainty: TikTok view-through unverifiable
    4. Influencer offline amplification: systematic understatement
    5. GDPR deletion historical gap: progressively less complete over time
  Each has caveat_text included in affected alert Layer 2 as structural note
  NOT framed as DQ warning (fixable) — framed as measurement system limitation
```

### G — DQ Temporal Distribution

```
High-DQ-issue periods:
  January both years: SD3, LD3, GD1 peak, GA4 lookback revisions
    4–5 simultaneous DQ issues
  BFCM both years: SD1, MD2, GD2, SentD1, KD1, LD3
    5–6 simultaneous issues — highest DQ stress period
  Each collection launch: SD1, MD2, GD2, XD4
    3–4 simultaneous issues

Low-DQ-issue periods:
  August both years: 1–2 minor ongoing only
  May both years: 1–2 minor ongoing only

Sustained background DQ issues (always present):
  XD1 (identity resolution), XD2 (timezone), XD3 (revenue reconciliation),
  GD5 (Gorgias tag inconsistency), SD6 (draft order contamination),
  GD7 (GA4 session stitching), SentD1 (Sentry sampling)
```

### G — Suppression Count Distribution by Temporal Cluster

```
CONFIRMED: suppression_log row counts by period across 24 months.
Seed script must generate approximately these volumes:

BFCM periods (Nov both years — 4 weeks each):
  Active suppression scenarios simultaneously: 7–8
  suppression_log rows per BFCM period: 180–220
  Breakdown: S1 (CPM), S9 (DQ/Gorgias), S23 (Klaviyo send ×daily),
    S24 (app changes), S34 (business hours), S35 (root cause dedup),
    S37 (recurring calendar), S42 (stacking multi-suppression)
  Note: highest suppression density in dataset — critical test of stacking rules

January periods (both years — first 3 weeks):
  Active suppression scenarios simultaneously: 4–5
  suppression_log rows: 80–110 per January
  Breakdown: S3 (post-holiday returns), S27 (inventory write-offs),
    S31 (BFCM cohort quality), S34 (business hours), S37 (Jan 1–3 calendar)

Collection launch periods (Apr and Oct both years — 2 weeks each):
  Active simultaneously: 3–4
  suppression_log rows: 60–80 per launch period
  Breakdown: S2 (CPM), S22 (A/B test if active), S23 (Klaviyo sends),
    S37 (calendar rhythm)

Quiet periods (Aug and May both years):
  Active simultaneously: 1–2
  suppression_log rows: 15–25 per quiet month
  Mostly S12 (iOS ATT), S14 (TikTok monthly reset), S37 (recurring)

Total suppression_log rows across 24 months: 1,800–2,400
Total predictive_suppression entries: 200–280
(These are in addition to business alert_log rows)
```

### G — Weighted Confidence Calculation for All Alert Types

```
CONFIRMED: Every alert type has source weights. alert_log stores
per-source DQ scores at firing time AND the weighted confidence calculation.

The weights reflect how much each source's accuracy affects the alert conclusion.

FORMAT: source: weight (must sum to 1.0 per alert)

ALERT A1 — True Post-Return ROAS by Channel:
  shopify_orders: 0.40
  shopify_refunds: 0.25
  meta_attribution: 0.20
  tiktok_attribution: 0.10
  loop_returns: 0.05

ALERT A2 — Root Cause of ROAS Drop:
  meta_ad_performance: 0.50
  shopify_orders: 0.30
  ga4_sessions: 0.15
  sentry_errors: 0.05

ALERT A3 — Channel ROAS Ranking Reversal:
  meta_ad_performance: 0.45
  tiktok_ad_performance: 0.45
  shopify_orders: 0.10

ALERT 3 (C2) — Influencer ROI after Returns:
  tiktok_ad_performance: 0.30
  shopify_orders: 0.30
  loop_returns: 0.25
  klaviyo_profiles: 0.15
  (klaviyo weight for downstream email value estimation)

ALERT 4 (D1) — Contribution Margin Compression:
  shopify_orders: 0.30
  shopify_inventory_items: 0.25 (COGS)
  meta_ad_performance: 0.20
  tiktok_ad_performance: 0.10
  loop_returns: 0.10
  client_config: 0.05 (fulfilment cost)

ALERT 5 (C1) — Sizing Complaint Velocity:
  gorgias_tickets: 0.55
  loop_returns: 0.30
  shopify_orders: 0.15

ALERT B1 — Creative Fatigue:
  meta_ad_performance: 0.85
  tiktok_ad_performance: 0.15

ALERT D5 — Klaviyo Flow Revenue Declining:
  klaviyo_email_events: 0.70
  shopify_orders: 0.30
  (shopify used to validate Klaviyo attributed revenue figures)

ALERT E1 — List Health Degradation:
  klaviyo_email_events: 0.80
  klaviyo_profiles: 0.20

ALERT E2 — Repeat Purchase Rate Declining:
  shopify_orders: 0.60
  klaviyo_profiles: 0.25
  loop_returns: 0.15
  (returns affect denominator of repeat purchase cohort)

ALERT E3 — High-LTV Customers Going Quiet:
  shopify_orders: 0.50
  klaviyo_email_events: 0.35
  klaviyo_profiles: 0.15

ALERT F1 — Checkout Conversion by Device:
  ga4_sessions: 0.55
  shopify_orders: 0.30
  sentry_errors: 0.15

ALERT F2 — Payment Gateway Failure:
  sentry_errors: 0.60
  ga4_sessions: 0.25
  shopify_orders: 0.15

ALERT G1 — Stockout During Active Spend:
  shopify_inventory_levels: 0.50
  meta_ad_performance: 0.30
  tiktok_ad_performance: 0.20

ALERT G2 — Overstock Risk:
  shopify_inventory_levels: 0.60
  shopify_orders: 0.30
  klaviyo_email_events: 0.10
  (Klaviyo back-in-stock waitlist indicates demand presence)

ALERT H1 — Sync Gap:
  airbyte_sync_metadata: 1.00
  (pure pipeline health — no business source weights)

ALERT H6 — Platform Spend Gap:
  meta_ad_performance: 0.50 OR tiktok_ad_performance: 0.50
  (whichever platform triggered the alert — weight goes to 1.0 for that platform)

CONFIDENCE FLOOR RULES (apply after weighted calculation):
  If ANY single source has dq_score = 0: overall confidence = 0 (State 4)
  If primary source (highest weight) has dq_score < 50: cap overall at 55%
  If weighted confidence < 60%: suppress alert, fire H-series DQ alert instead
  If weighted confidence 60–79%: fire with explicit confidence shown in Layer 2
  If weighted confidence ≥ 80%: fire at full confidence

EXAMPLE CALCULATION during January return avalanche for Alert A1:
  shopify_orders: dq=96 × 0.40 = 38.4
  shopify_refunds: dq=78 × 0.25 = 19.5 (refund lag — SD3)
  meta_attribution: dq=71 × 0.20 = 14.2 (iOS ATT recalibration — S12)
  tiktok_attribution: dq=88 × 0.10 = 8.8
  loop_returns: dq=78 × 0.05 = 3.9 (high volume lag — LD3)
  Weighted total: 84.8
  Result: Alert A1 fires at 85% confidence
  Layer 2 caveat: "Return data may be 12–36h stale. ROAS may revise upward."
```

### G — DQ Improvement Arc (Resolution Events with Specific Score Values)

```
Each resolution event must update dq_metric_scores at the resolution date.
Format: source | metric_domain | dq_score BEFORE → dq_score AFTER | H-series alert stops

Month 3 (August 2024): GA4 add_to_cart double-firing fixed (theme update)
  GA4 | funnel_performance | 76 → 87
  Alert H12 fires less frequently after fix (GA4 purchase count closer to Shopify)

Month 5 (October 2024): Sentry release tags configured
  Sentry | error_attribution | 79 → 91
  Alert SentD2 (diagnostic-only Sentry alerts) resolved
  F2, F1 alerts can now confirm deployment-specific errors

Month 8 (January 2025): Shop Pay GA4 event added
  GA4 | funnel_performance | 87 → 94
  H12 stops firing — GA4 purchase count now within 2% of Shopify orders

Month 9 (February 2025): Gorgias automation contamination filtered
  Gorgias | ticket_volume | 82 → 91
  Alert 5 (C1) false positive rate reduces
  GD2 no longer active

Month 10 (March 2025): Klaviyo-Shopify customer ID mismatch improving
  Klaviyo | customers | 88 → 92
  H3 fires less frequently
  Alert A6 confidence improves from 85% → 90% cap

Month 12 (May 2025): Meta CAPI Event Match Quality improved
  Meta | attribution | 82 → 89
  H11 stops firing
  A1 Meta attribution weight confidence improves
  Alert A1 confidence cap improves from 80% → 87% for Meta component

Month 13 (June 2025): tag_normalisation table updated (after H14 fires repeatedly)
  Gorgias | ticket_tags | 74 → 83
  H14 firing frequency drops from weekly to monthly
  Alert 5 (C1) false positive rate drops 40% (as confirmed in design spec)

Month 15 (August 2025): Multi-location inventory discrepancy resolved (3PL switch)
  Shopify | inventory | 68 → 89
  SD2 no longer active (single-location 3PL = no inter-location transfers)
  Alert G1 and G2 confidence improves

Month 18 (November 2025): Klaviyo-Shopify mismatch fully resolved (post-restructure)
  Klaviyo | customers | 92 → 97
  H3 stops firing entirely
  Alert A6 confidence cap removed (full confidence restored)
  Match rate Shopify ↔ Klaviyo: 91% → 96%

Month 20 (January 2026): GA4 implementation fully validated
  GA4 | funnel_performance | 94 → 97
  H12 stops firing permanently
  F1, F4, F5 can fire at full confidence on GA4 funnel data

OVERALL DQ TRAJECTORY (blended across all sources):
  Month 1:  weighted avg dq_score = 81 (multiple implementation gaps active)
  Month 6:  weighted avg dq_score = 78 (BFCM stress — temporary dip)
  Month 8:  weighted avg dq_score = 84 (Shop Pay fix + Sentry tags)
  Month 13: weighted avg dq_score = 88 (list of fixes accumulated)
  Month 18: weighted avg dq_score = 91 (Klaviyo fully resolved)
  Month 24: weighted avg dq_score = 93 (near full maturity)

This trajectory must be seeded in dq_metric_scores as time-series rows
(one row per source per metric_domain per resolution date).
The seed script generates these rows automatically when it processes
each resolution event — not as static values.
```

---

## ADDITIONAL ARCHITECTURE DECISIONS FROM GAP DISCUSSIONS

### New Tables Required (Not in technical_architecture.md yet)

```sql
-- brand_event_calendar (drives ALL suppression logic — S1-S50)
-- This is the most critical table in the suppression architecture
CREATE TABLE client_azure_co.brand_event_calendar (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    event_name              text not null,
    event_type              text not null,   -- 'collection_launch'/'sale_period'/
                                            -- 'retail_holiday'/'influencer_campaign'/
                                            -- 'supplier_event'/'platform_disruption'/
                                            -- 'klaviyo_ab_test'/'klaviyo_feature_activation'/
                                            -- 'email_template_update'/'operational_change'/
                                            -- 'supplier_quality_event'/'bfcm_sunset_spike'/
                                            -- 'photography_update'/'size_guide_update'/
                                            -- 'influencer_gift_shipment'/'price_change'/
                                            -- 'platform_disruption_partial'/
                                            -- 'platform_disruption_secondary'/
                                            -- 'platform_algorithm_change'
    start_date              date not null,
    end_date                date not null,
    suppress_alerts         text[],         -- alert types: full suppression (State 3)
    context_alerts          text[],         -- alert types: partial context (State 2)
    context_explanation     text,           -- what to include in Layer 2 for State 2
    residual_threshold_pct  numeric,        -- fire if signal exceeds seasonal explanation by this %
    confidence_decay_type   text,           -- 'linear'/'step'/'exponential'
    confidence_decay_start  date,
    confidence_decay_end    date,
    confidence_at_peak      numeric default 1.0,
    detection_method        text default 'auto',  -- 'auto'/'manual'/'hardcoded'
    detection_lag_hours     integer,        -- hours after event start it was logged
    confidence              numeric default 1.0,  -- 0-1 that event is still ongoing
    last_verified_at        timestamptz,
    is_recurring            boolean default false,
    recurrence_rule         text,           -- 'annual'/'monthly'/null
    auto_detected           boolean default true,
    detected_from           text,           -- source that triggered auto-detection
    event_profile           jsonb,          -- S46: stores pre-event answers (BFCM profile etc.)
    suppression_type        text default 'reactive',  -- 'reactive'/'predictive'
    is_synthetic            boolean default true,
    created_at              timestamptz default now()
);

-- network_pattern_benchmarks (cross-client pattern validation — Moat 2)
CREATE TABLE public.network_pattern_benchmarks (
    id                          bigint generated always as identity primary key,
    alert_type                  text not null,
    archetype                   text not null,    -- 'premium_womenswear'/'athleisure' etc.
    metric_name                 text,             -- e.g. 'open_rate'/'roas'/'return_rate'
    pattern_description         text,
    benchmark_median            numeric,          -- median value for this archetype
    benchmark_p25               numeric,          -- poor performance threshold
    benchmark_p75               numeric,          -- good performance threshold
    benchmark_bfcm_typical      numeric,          -- BFCM-period typical (for DQ benchmarks)
    network_confirmation_rate   numeric,          -- 0-1: confirmed in X% of similar brands
    sample_size                 integer,          -- anonymised brand count
    period_type                 text,             -- 'annual'/'bfcm'/'launch_period'/'quiet'
    last_updated                timestamptz default now(),
    created_at                  timestamptz default now()
);

-- sku_cost_master (COGS source — three-tier approach)
CREATE TABLE client_azure_co.sku_cost_master (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    shopify_variant_id      text not null,
    sku                     text not null,
    record_type             text not null,  -- 'sku_cogs'/'influencer_gifting_package'
    supplier_cost           numeric,        -- ex-factory cost only
    landed_cost             numeric,        -- supplier_cost × landed_cost_multiplier
    landed_cost_source      text,           -- 'finaloop_export'/'derived'/'manual'
    -- Gifting package fields (when record_type = 'influencer_gifting_package'):
    influencer_id           text,           -- nullable
    package_landed_cost     numeric,        -- full package (3-5 items) at landed cost
    packaging_cost          numeric,        -- branded box, tissue, handwritten note
    shipping_cost           numeric,        -- express to creator
    total_package_cost      numeric,        -- sum of above three
    featured_item_sku       text,           -- SKU actually shown in TikTok content
    non_featured_item_skus  text[],         -- other SKUs in package
    effective_from          date not null,
    effective_to            date,           -- null = currently active
    is_synthetic            boolean default true,
    created_at              timestamptz default now(),
    updated_at              timestamptz default now()
);

-- alert_log new fields (additions to existing alert_log table)
-- These fields must be ADDED to the existing alert_log table in technical_architecture.md
-- They are NOT a new table — they are ALTER TABLE additions:
ALTER TABLE client_azure_co.alert_log ADD COLUMN IF NOT EXISTS
    fatigue_period_active       boolean default false,
    fatigue_reason              text,           -- 'founder_stress_external_event'/'alert_accumulation'
    dismissal_correct           boolean,        -- null = unknown, true = founder right, false = founder wrong
    revenue_impact_missed       numeric,        -- estimated $ impact when correct alert wrongly dismissed
    delivery_delayed_hours      integer,        -- if alert held for business hours or DQ wait
    delay_reason                text,           -- 'shopify_sync_lag'/'business_hours'/'dq_wait'
    klaviyo_native_revenue      numeric,        -- Klaviyo's own attributed revenue figure
    profit_sentinel_adjusted_revenue numeric,   -- Profit Sentinel's deduplicated figure
    alert_instance_number       integer default 1,  -- 1=first firing, 2=second, etc.
    escalation_level            integer default 1,  -- 1=standard, 2=elevated, 3=critical
    suppression_type            text;           -- 'reactive'/'predictive'/null

-- Suppression audit trail
CREATE TABLE client_azure_co.suppression_log (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    signal_detected_at      timestamptz not null,
    alert_type              text not null,
    signal_value            numeric,
    threshold_value         numeric,
    suppression_reason      text not null,
    suppression_category    text not null,      -- S1–S50 reference
    suppression_state       integer,            -- 2 (State 2) or 3 (State 3)
    suppression_type        text default 'reactive', -- 'reactive'/'predictive'/'retraction'
    variance_explained_pct  numeric,
    residual_signal         numeric,
    suppression_source      text,               -- brand_event_calendar entry reference
    suppression_stack       jsonb,              -- all simultaneous suppressions + stacking rule applied
    would_have_fired_at     timestamptz,
    detected_signal_description text,
    threshold_context       text,
    suppression_explanation text,
    residual_signal_description text,
    founder_verification_action text,
    original_alert_log_id   bigint,            -- for S50 retractions: the alert being retracted
    retraction_reason       text,              -- for S50 retractions
    provisional_revised_value numeric,         -- for S50 retractions
    full_accuracy_expected_at timestamptz,     -- for S50 retractions
    founder_queryable       boolean default true,
    created_at              timestamptz default now()
);

-- Data lineage tracking
CREATE TABLE client_azure_co.alert_data_lineage (
    id                  bigint generated always as identity primary key,
    alert_log_id        bigint references alert_log(id),
    source              text not null,
    metric_name         text not null,
    metric_value        numeric,
    source_row_ids      text[],
    source_query        text,
    row_count           integer,
    date_range_start    date,
    date_range_end      date,
    created_at          timestamptz default now()
);

-- Permanent DQ limitations
CREATE TABLE public.permanent_dq_limitations (
    id                  bigint generated always as identity primary key,
    limitation_name     text not null,
    affected_sources    text[],
    affected_alerts     text[],
    estimated_impact    text,
    estimated_magnitude text,
    caveat_text         text,
    is_resolvable       boolean default false,
    resolution_path     text
);

-- Klaviyo flow ID history (for agency transition)
CREATE TABLE client_azure_co.klaviyo_flow_id_history (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    old_flow_id         text not null,
    new_flow_id         text,
    flow_name           text not null,
    change_reason       text,
    effective_from      date not null,
    effective_to        date,
    created_at          timestamptz default now()
);

-- Touchpoint journey (from Gap C attribution)
CREATE TABLE client_azure_co.synthetic_touchpoint_journey (
    order_id            text not null,
    touchpoint_sequence integer not null,
    channel             text,
    touchpoint_date     date,
    touchpoint_type     text,
    campaign_id         text,
    influencer_id       text
);

-- TikTok organic performance
CREATE TABLE client_azure_co.tiktok_organic_performance (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    date                date not null,
    organic_reach_rate  numeric,
    posting_frequency   numeric,
    impressions         bigint,
    video_views         bigint,
    engagement_rate     numeric,
    created_at          timestamptz default now()
);

-- Tag normalisation
CREATE TABLE client_azure_co.tag_normalisation (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    raw_tag             text not null,
    canonical_tag       text not null,
    category            text,
    created_at          timestamptz default now()
);

-- Predictive suppression log (extension of suppression_log)
-- Add suppression_type = 'predictive' to suppression_log
-- Add signal_detected_at = null for predictive entries

-- klaviyo_sms_events, meta_billing_statement, tiktok_billing_statement,
-- and dq_events DDLs are defined below in this section.

-- SMS events (distinct from email events)
CREATE TABLE client_azure_co.klaviyo_sms_events (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    profile_id          text not null,
    event_type          text not null,  -- 'sms_sent' / 'sms_delivered' / 
                                        -- 'sms_clicked' / 'sms_opted_out'
    flow_id             text,           -- nullable (null for campaigns)
    campaign_id         text,           -- nullable (null for flows)
    message_type        text,           -- 'welcome' / 'abandoned_cart' / 'campaign'
    sent_at             timestamptz,
    delivered_at        timestamptz,
    clicked_at          timestamptz,
    opted_out_at        timestamptz,
    attributed_order_id text,           -- nullable
    attributed_revenue  numeric,
    is_synthetic        boolean default true,
    created_at          timestamptz default now()
);

-- Meta billing statement (for financial reconciliation H17)
CREATE TABLE client_azure_co.meta_billing_statement (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    statement_month         date not null,   -- first day of billing month
    total_spend_exact       numeric(18,6),   -- 6 decimal places (exact billing)
    total_spend_api         numeric(10,2),   -- 2 decimal places (API rounded)
    rounding_gap            numeric(10,6),   -- total_spend_exact - total_spend_api
    currency                text default 'USD',
    statement_date          date,
    source                  text default 'finaloop',  -- where billing figure came from
    is_synthetic            boolean default true,
    created_at              timestamptz default now()
);

-- TikTok billing statement (same structure)
CREATE TABLE client_azure_co.tiktok_billing_statement (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    statement_month         date not null,
    total_spend_exact       numeric(18,6),
    total_spend_api         numeric(10,2),
    rounding_gap            numeric(10,6),
    currency                text default 'USD',
    statement_date          date,
    source                  text default 'finaloop',
    is_synthetic            boolean default true,
    created_at              timestamptz default now()
);

-- DQ events (for cascade tracking)
CREATE TABLE client_azure_co.dq_events (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    source                  text not null,
    dq_issue_code           text not null,  -- 'SD1', 'MD2', 'GD5' etc.
    metric_domain           text not null,  -- which metric domain affected
    started_at              timestamptz not null,
    resolved_at             timestamptz,    -- null = still active
    peak_severity           integer,        -- 0-100 (100 = complete failure)
    recovery_duration_hours integer,
    recovery_dq_curve       jsonb,          -- hour: dq_score pairs during recovery
    backlog_order_count     integer,        -- for webhook failures
    backlog_processing_lag  integer,        -- hours to process backlog
    cascade_to              text[],         -- downstream dq_issue_codes triggered
    cascade_lag_hours       integer,
    cascade_duration_hours  integer,
    alerts_suppressed       text[],         -- alert types suppressed during this event
    alerts_capped           jsonb,          -- {alert_type: confidence_cap_value}
    is_synthetic            boolean default true,
    created_at              timestamptz default now()
);
```

### client_config Additions from Gaps D, E, F, G

```
attribution_philosophy          text     -- 'last_click'/'assisted'/'platform_reported'
roas_revenue_definition         text     -- 'gross'/'net_shipping'/'post_return'
return_rate_thresholds          jsonb    -- category-specific thresholds
klaviyo_monthly_cost            jsonb    -- time-series with effective dates
frequency_capping_enabled       boolean  -- with effective_from date
business_model_type             text     -- 'year_round'/'seasonal_heavy'/'event_driven'
tiktok_shop_active              boolean
tiktok_wallet_balance           numeric
spend_cash_vs_accrued_tracking  boolean
dst_transition_caveat_active    boolean
gdpr_deletion_count_monthly     integer  -- for DQ score calculation
```

### Consolidated influencer_sub_calendar Fields (All Gaps Combined)

```
All fields required per influencer activation row.
Fields combined from Gap C (gap_abc_decisions.md) plus Gaps D and E additions.

CORE FIELDS (Gap C):
  influencer_id               text       -- unique ID e.g. 'INF-2024-JAN-02'
  tier                        text       -- 'micro' / 'mid' / 'macro'
  fee_structure               text       -- 'cash' / 'gifting' / 'hybrid'
  cash_fee                    numeric    -- nullable if gifting-only
  content_format              text       -- 'tryon_haul'/'styling'/'grwm'/'unboxing'
  discount_code               text       -- nullable
  audience_fit_score          integer    -- 1–5 (1=poor fit, 5=perfect fit)
  expected_return_rate        numeric    -- derived: fit score + format + discount
  activation_date             date       -- when deal signed / package shipped
  content_live_date           date       -- when TikTok post goes live
  spark_ad_launched           boolean
  spark_ad_campaign_id        text       -- nullable

GIFTING PACKAGE FIELDS (Gap E — E-GiftingCOGS):
  package_landed_cost         numeric    -- full package (3–5 items) at landed cost
  packaging_cost              numeric    -- branded box, tissue, handwritten note ($25–60)
  shipping_cost               numeric    -- express to creator for pre-date delivery ($18–45)
  total_package_cost          numeric    -- sum of above three (used for Alert 3 ROI)
  featured_item_sku           text       -- SKU actually shown in TikTok content
  non_featured_item_skus      text[]     -- other SKUs in package (not shown)

GEOGRAPHIC AND SEASONAL FIELDS:
  geographic_skew             text       -- 'domestic_heavy'/'international_heavy'/'balanced'
  season                      text       -- 'SS'/'FW'/'BFCM'/'valentines'/'holiday_gifting'
  seasonal_return_rate_adj    numeric    -- pp adjustment to expected_return_rate

TIKTOK DISRUPTION FIELDS (Gap D — D13):
  instagram_reels_posted      boolean    -- true for mid/macro from Jan 2024 onward
  instagram_reels_session_lift numeric   -- estimated additional Shopify sessions from Reels

ALERT 3 TWO-STAGE FIELDS:
  stage1_alert_date           date       -- content_live_date + 7 days
  stage2_alert_date           date       -- content_live_date + 21 days
  cohort_a_revenue            numeric    -- 0–7 day TikTok UTM attributed revenue
  cohort_b_revenue            numeric    -- 8–14 day TikTok UTM attributed revenue
  returns_processed_count     integer    -- returns by Day 21
  returns_refund_value        numeric    -- total refund value by Day 21
  klaviyo_signups             integer    -- non-converting visitors who subscribed
  klaviyo_12mo_est_value      numeric    -- estimated 12-month email revenue from signups

  COHORT B CONTESTED ATTRIBUTION EXCLUSION LOGIC:
  Cohort B orders (Day 8–14 TikTok UTM) must be split into two sub-groups:
  
  Sub-group B1 — Clean TikTok attribution (include in Alert 3 ROI):
    order has TikTok UTM source in Days 8–14
    AND no Meta click event for same customer in same window
    Seed flag: cohort_b_clean = true
    
  Sub-group B2 — Contested attribution (flag separately, exclude from ROI):
    order has TikTok UTM source in Days 8–14
    AND also has Meta click event for same customer within 14 days
    Seed flag: cohort_b_contested = true
    Alert 3 Layer 2 note: "X orders in Days 8–14 have both TikTok UTM and 
      Meta click — excluded from TikTok ROI to avoid double-counting.
      These orders are credited to Meta in Alert A1 calculations."
    
  Realistic contested proportion: 20–30% of Cohort B orders
  Seed implementation: synthetic_touchpoint_journey table identifies these
  cohort_b_revenue field: sum of B1 only (clean TikTok)
  cohort_b_contested_revenue: sum of B2 (reported separately in alert)

SPECIAL SCENARIO FLAGS:
  is_fraud_scenario           boolean    -- bought followers / engagement pod test
  fraud_type                  text       -- 'bought_followers' / 'engagement_pod'
  is_non_delivery             boolean    -- content late or never posted
  delivery_delay_days         integer    -- actual vs contracted content date gap
  is_disrupted                boolean    -- TikTok disruption affected
  disruption_type             text       -- 'content_delayed'/'platform_switch'/'renegotiated'
  competitor_saturation       boolean    -- pre-campaign competitor posting detected
  existing_customer_overlap_pct numeric  -- % of attributed orders from existing customers
```

### Flash Sale Schedule (for KD1 Race Condition Seed Events)

```
KD1 (Klaviyo property sync race condition) requires 4–6 flash sale events.
Exact schedule for Archetype A:

Flash Sale 1: Month 2 (July 14 2024)
  Duration: 24 hours
  Discount: 20% off selected styles
  Klaviyo send: 10am EST to full active list
  Race condition window: 10am–12pm EST (2 hours post-send)
  Orders in window: ~45 (Klaviyo and Shopify receive events simultaneously)

Flash Sale 2: Month 5 (October 21 2024) — Pre-FW launch clearance
  Duration: 48 hours
  Discount: 30% off SS clearance
  Klaviyo send: 9am EST
  Race condition window: 9am–11am EST both days

Flash Sale 3: Month 6 (November 20 2024) — BFCM early access
  Duration: 8 hours (email subscriber early access before public)
  Discount: 25% off sitewide
  Klaviyo send: 6am EST
  Race condition window: 6am–8am EST (highest volume flash sale)
  Note: this overlaps with BFCM S46 pre-event suppression window

Flash Sale 4: Month 12 (May 14 2025) — Mother's Day flash
  Duration: 12 hours
  Discount: 25% off gifting styles
  Race condition window: 10am–12pm EST

Flash Sale 5: Month 18 (November 20 2025) — Y2 BFCM early access
  Same structure as Flash Sale 3 (Y2)

Flash Sale 6: Month 22 (March 2026) — SS Y2 launch flash
  Duration: 24 hours
  Discount: 15% off new arrivals (smaller discount — brand testing non-deep-discount strategy)
  Race condition window: 9am–11am EST

For each flash sale: seed 3–5 specific order IDs where both Klaviyo purchase event
and Shopify order event arrive within the same 30-second window.
KD1 DQ flag fires for these specific orders.
Attribution in these orders: random assignment between campaign and flow.
```

### Source Table Schema Additions Required

```
These fields must be added to existing source table schemas before seeding.
They are NOT in the original technical_architecture.md schema definitions.

TIKTOK_AD_PERFORMANCE additions (Gap D — D2):
  campaign_type   text    -- 'spark_ad_existing'/'spark_ad_new'/'in_feed_paid'
  spend_cash      numeric -- actual cash paid (may differ from spend_accrued)
  spend_accrued   numeric -- ads that actually ran (accrual basis)
  buying_type     text    -- 'auction' / 'reach_and_frequency'

META_AD_PERFORMANCE additions (Gap D, Gap G):
  spend_cash      numeric -- actual cash paid
  spend_accrued   numeric -- ads that actually ran
  audience_source text    -- nullable: 'klaviyo_sync' if audience from Klaviyo
  buying_type     text    -- 'auction' / 'reach_and_frequency'
  event_match_quality_score numeric -- Meta EMQ score (for H11)

KLAVIYO_EMAIL_EVENTS additions (Gap E):
  email_type          text    -- 'transactional' / 'marketing'
  reported_opens      integer -- includes Apple MPP machine opens
  effective_opens     integer -- reported_opens × 0.65 (human opens only)
  review_submitted    boolean -- for post-purchase Day 14 emails
  spam_complaint      boolean -- per send
  hard_bounce         boolean -- per send
  inbox_placement_rate numeric -- estimated per campaign

KLAVIYO_PROFILES additions (Gap E):
  signup_source           text    -- form type (Form 1–6)
  signup_form_id          text
  acquisition_channel     text    -- 'tiktok_influenced'/'meta'/'organic' etc.
  consent_method          text    -- 'double_optin' / 'single_optin'
  consent_timestamp       timestamptz
  ccpa_opt_out            boolean
  gdpr_consent            boolean
  subscription_state      text    -- 'subscribed'/'unsubscribed_marketing'/'unsubscribed_all'
  vip_status              boolean
  cumulative_spend        numeric
  loyalty_points          integer -- synced from loyalty app
  loyalty_tier            text    -- 'standard' / 'vip'
  engagement_score        numeric -- 0–100 (for sunset flow eligibility)
  sunset_eligible         boolean -- true at 180 days no engagement
  last_ticket_reason      text    -- synced from Gorgias
  last_ticket_resolved_at timestamptz
  ticket_count_lifetime   integer
  csat_score_last         numeric
  style_occasion          text    -- from zero-party survey (Month 6+)
  fit_preference          text    -- from zero-party survey
  budget_preference       text    -- from zero-party survey

SHOPIFY_ORDERS additions (Gap D, Gap G):
  sales_channel           text    -- 'web'/'wholesale'/'draft_order'/'loop_exchange'
  gdpr_deletion_marker    boolean -- true if customer was GDPR-deleted
  spend_cash_vs_accrued   text    -- for TikTok wallet entries: 'prepayment'/'ad_spend'

SHOPIFY_CUSTOMERS additions (Gap G):
  gdpr_deleted_at         timestamptz -- null if not deleted
  gdpr_deletion_marker    boolean

GORGIAS_TICKETS additions (Gap D, Gap E):
  ticket_category         text    -- 'return_intent'/'wismo'/'product_quality'/
                                  -- 'compliance_complaint'/'refund_status_enquiry'/
                                  -- 'loyalty_complaint'
  first_response_type     text    -- 'automated' / 'human'
  root_ticket_id          text    -- for merged tickets: points to original

LOOP_RETURNS additions:
  return_initiated_at     timestamptz -- when customer submitted return (Stage 2 signal)
  return_received_at      timestamptz -- when warehouse received item (Stage 3 signal)
  Note: gap between these two = the leading indicator window (5–8 days)
```

### Three-Stage Return Warning Chain — Cross-Reference Note

```
The three-stage return warning chain (confirmed in Gap A) affects multiple
Gap E and Gap G entries. This note connects them explicitly.

STAGE 1 — Gorgias complaint velocity (Day 0–3 post-purchase):
  Sources: gorgias_tickets.ticket_category = 'return_intent'
  Alert: Alert 5 (C1) fires
  Gap E connection: Flow 13 (Size Guide) is the recommended action when Stage 1 fires
  Gap G connection: GD5 (agent tag inconsistency) is the primary false positive risk
    for Stage 1. tag_normalisation table must canonicalise return intent tags.

STAGE 2 — Loop return initiations (Day 3–7 post-purchase):
  Sources: loop_returns.return_initiated_at (new field above)
  Alert: Alert C4-variant fires confirming Stage 1 signal
  Gap G connection: LD3 (Loop data freshness during high volume) affects Stage 2
    reliability in January. confidence_cap 80% on Stage 2 during January.
  Note: Stage 2 is NOT affected by LD3's return_received_at lag —
    return_initiated_at is recorded immediately when customer submits.

STAGE 3 — Physical RTO/RVP receipt (Day 8–14):
  Sources: loop_returns.return_received_at AND shopify refund processed
  Alert: Alert C3 fires as confirmed signal
  Gap G connection: LD3 (Loop data freshness) DOES affect Stage 3 during January.
    Physical returns arrive at warehouse, processing lags 12–24h.
    SD3 (Shopify returns reconciliation lag) also affects Stage 3 — 12–36h delay.
  Gap E connection: Flow 9 (Post-Return Recovery) trigger is Stage 3 event.
    Loop Returns refund processed → Flow 9 fires Day 3 post-refund.

ALERT 3 RELATIONSHIP TO THE THREE STAGES:
  Alert 3 Stage 1 (Day 7) fires after purchase window closes — uses Cohort A only.
  Alert 3 uses return data from Stage 3 (physical receipt) for final ROI.
  Alert 3 Stage 2 (Day 21) waits for most Stage 3 returns to complete.
  Alert 3 does NOT reference Stage 1 or Stage 2 signals directly.
```

### Synthetic Data Manifest Extensions

```
manifest.json must include per event:
  event_id
  event_name
  event_date
  alert_type_expected
  should_fire (boolean)
  suppression_reason (nullable)
  suppression_state (1/2/3/4 — nullable if fires)
  variance_explained_pct (nullable)
  source_row_ids (dict mapping source to row IDs)
  lineage_row_ids (list of alert_data_lineage IDs)
  suppression_log_id (nullable — if suppressed)
  dq_scores_at_event (dict of source → dq_score)
  cascade_events (list of downstream events triggered)
```

---

## WHAT REMAINS BEFORE CLAUDE CODE SEED PROMPT

All six original gaps are now resolved:
- Gap D: TikTok disruption — COMPLETE
- Gap E: Klaviyo flow architecture — COMPLETE  
- Gap F: Suppression scenarios — COMPLETE
- Gap G: DQ-to-alert interaction map — COMPLETE
- Gap 1 (threshold calibration): resolved in Gap A discussions
- Gap 2 (outcome logging): resolved in Gap A discussions
- Gap 3 (onboarding scenario): resolved in Gap A discussions
- Gap 4 (negative onboarding): resolved in Gap A discussions
- Gap 5 (Precision Profit Calendar table): resolved in Gap A discussions
- Gap 6 (thread context): resolved in Gap A discussions

Additional architecture decisions from gap discussions:
- Alert library (41 alert types): defined in chat — needs product_strategy.md update
- Three-category alert classification: high-actionability / monitor-and-wait / diagnostic-only
- Influencer sub-calendar: fully defined in Gap C
- Schema changes calendar: defined across gaps
- SKU lifecycle calendar: defined in Gap A/B discussions
- Calibration pass design: defined in Gap resolutions
- Three archetype decision: A primary, B and D thin in Step 7
- Finaloop: no connector — CSV export via sku_cost_master table
- COGS tiering: three-tier onboarding approach
- Confirmation flow: 5 questions (revised from 8)

NEXT STEP: Write Claude Code seed prompt using all three seed decision files:
  1. gap_abc_decisions.md (Gaps A, B, C)
  2. seed_decisions_gap_d_e.md (Gaps D, E)
  3. seed_decisions_gap_f_g.md (Gaps F, G — this file)
Plus: technical_architecture.md and product_strategy.md
All five files must be searched before writing any seed script code.
