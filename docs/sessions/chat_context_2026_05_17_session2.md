# Profit Sentinel — Chat Context
## Date: 2026-05-17 (Session 2)
## Purpose: Captures decisions, reasoning, and learning content from
## the strategy and product architecture session (not the seed execution
## session — that is in chat_context_2026_05_17.md).
## Read alongside updated technical_architecture.md and product_strategy.md.

---

## SESSION FOCUS

Two tracks ran in parallel:
1. Deep domain learning — Fashion DTC unit economics (Topic 1 of 7-topic curriculum)
2. Architectural gap identification and resolution — 25 gaps identified,
   decisions made, both .md files updated

---

## LEARNING CURRICULUM — RECOMMENDED ORDER

Seven topics identified for deep product understanding:
1. Fashion DTC unit economics and financial model ← COVERED THIS SESSION
2. Fashion business nuance of Shopify brands
3. Causal graph and knowledge graph (do before technical structure)
4. Technical structure (architecture serves the causal graph, not vice versa)
5. Data science and ML
6. Gen AI (least complex part of Profit Sentinel)
7. Customer discovery (highest-risk gap, goes last in learning order)

---

## TOPIC 1 — FASHION DTC UNIT ECONOMICS (COVERED)

### The P&L Structure
```
Gross Revenue (Shopify reports this)
- Returns & Refunds
- Discounts
= Net Revenue  ← real top line

- COGS (landed cost per unit)
= Gross Profit

- Paid Media (Meta + TikTok)
- Influencer Fees + Product Cost
- Email/SMS (Klaviyo)
= Contribution Margin  ← the number that matters most

- Fulfillment (3PL pick/pack/ship)
- Platform fees
- Returns logistics (reverse shipping + restocking)
= Contribution Margin after Fulfillment

- Salaries, rent, software, agency fees
= EBITDA
```

Critical: Shopify reports Gross Revenue. Every founder looks at this first.
It is the most misleading number on the dashboard.
Alert 1 (True post-return ROAS) exists because Meta ROAS is calculated
on Gross Revenue before returns. The real number is always lower.

### The Four Numbers That Determine Survival

**1. Return Rate by Channel**
- Fashion return rates: 25-45% normal. Above 45% = product/sizing problem.
- Not uniform: varies by channel, SKU, collection, discount depth
- Influencer-driven orders return 8-15% higher than organic
- Orders with >30% discount return at 2x the rate (buyer remorse)

**2. Contribution Margin %**
- Healthy range at $2M-$10M GMV: 35-50% after paid media, before fulfillment
- Below 30%: brand is buying revenue, not scaling
- Below 20%: existential — discount dependency has destroyed pricing integrity

**3. Blended ROAS vs Channel ROAS**
- Meta reported ROAS: 3.5-5x (typical)
- True post-return ROAS: 1.8-2.8x (typical)
- The gap is where Profit Sentinel lives
- Meta overcounts via view-through attribution and 7-day click windows

**4. Payback Period**
- CAC at this GMV tier: $45-$120
- LTV at 12 months: $180-$350 (healthy brand)
- Payback period: 3-8 months
- A brand scaling on paid media with 6-month payback is cash-flow negative
  per acquired customer for 6 months

### Fashion-Specific Mechanics That Break Standard Models

**Inventory as Capital Lock**
- Fashion brands buy inventory 4-6 months before selling
- A $3M brand may have $400K-$700K locked in inventory at any time
- Not in P&L — balance sheet item — but determines what paid media
  the brand can afford to run
- A CPM spike may force reduced spend exactly when inventory is in warehouse

**Collection Drop Economics**
- 2-4 collection launches per year (SS, FW, Resort, Pre-Fall)
- 2-3 week heat window per launch: elevated conversion, efficient CPM
- Markdown cycle starts week 6-8 when newness fades
- Clearance phase destroys CM but recovers inventory capital
- ROAS drop in week 7 of a collection is expected. In week 2, it is a signal.
- The Precision Profit Calendar encodes this distinction.

**Influencer Economics Lag Structure**
- Post goes live: Day 0
- Peak engagement: Day 1-3
- Order conversion: Day 1-14
- Return decisions: Day 14-45
- Any influencer ROI measurement before day 45 is premature
- Most brands measure at day 7 and declare success/failure incorrectly

**Discount Dependency Trap**
- Once customers are trained to wait for sales, removing discounts causes
  immediate revenue drop before margin improvement appears (4-6 weeks later)
- Alert 4 must distinguish discount-driven CM compression from structural
  CM compression — they have different remedies

**Sizing as a Product Problem**
- Gorgias complaints predict return spikes 8-12 days before Loop returns arrive
- The window allows: size chart popup on PDP, fit guide in Klaviyo
  post-purchase email, CS team briefing, buying team flag before next PO
- These are $15K-$40K decisions at the $3M GMV tier

### Client-Specific Numbers Profit Sentinel Must Capture
| Metric | Why Client-Specific |
|--------|-------------------|
| COGS per SKU | Factory + freight + duty varies per brand and collection |
| Return logistics cost | 3PL reverse fee varies $4-$12 per return |
| Attribution philosophy | Last click vs assisted vs platform-reported |
| ROAS revenue definition | Gross vs net of returns; shipping included/excluded |
| Discount threshold | At what depth does discount signal loyalty vs dependency |
| Collection launch calendar | When heat windows start and end |
| Influencer measurement window | Brand's own policy (30 vs 60 days) |

---

## ARCHITECTURAL DECISIONS MADE THIS SESSION

### Decision 1 — Alert Library Is Not The Ceiling
The 41 validated alert types are the floor, not the limit.
The product is positioned as causal intelligence — a static 41-alert system
is functionally a sophisticated rule engine.
Resolution: self-extending causal graph via candidate_signals promotion pipeline.
Closed — do not reopen.

### Decision 2 — Self-Extending Graph Must Be Live From Day One
The candidate_signals table and promotion mechanism are not Horizon 2.
They are a prerequisite for the moat claim to be true.
Must be designed before Agent B is built.
New tables: candidate_signals, causal_pattern_validation.
Closed — do not reopen.

### Decision 3 — Vertical Segmentation Is Mandatory
Cross-vertical promotion explicitly prohibited.
A causal chain validated on contemporary womenswear does NOT auto-promote
for swimwear — fundamentally different seasonality, return behaviour,
and sizing complaint patterns.
vertical_tag required on: causal_pattern_validation, candidate_signals,
network_pattern_benchmarks.
Closed — do not reopen.

### Decision 4 — Verification Category (A/B/C) Required on All 41 Alert Types
Every alert must be assigned a verification_category before Agent B is built.
- Category A: Directionally verifiable in data independent of founder action
- Category B: Action-confounded — requires cross-client validation
- Category C: Structurally unverifiable — explicit uncertainty always communicated
Determines: confidence score calculation, outcome measurement, Agent D language.
OPEN DECISION: assignment for all 41 alerts (must complete before Agent B build).

### Decision 5 — Outcome Verification Is Probabilistic, Not Confirmed
Three verification mechanisms (metric trajectory, founder-reported, re-evaluation).
Must be documented explicitly: Profit Sentinel operates on probabilistic
outcome verification, not confirmed ground truth.

### Decision 6 — Financial Capacity: Action Re-Ranking, Not Suppression
capital_constraint_active in client_config re-ranks Agent C suggestions only.
Spend-increase actions demoted, not removed. Alert always fires.
Founder always sees all options. Nothing suppressed.
Closed — do not reopen.

### Decision 7 — Dismissal Reason Capture (One Tap)
When founder dismisses: "Not actionable right now, or doesn't look right?"
- "Not actionable" → capacity_constrained → excluded from precision calculations
- "Doesn't look right" → data_wrong or not_relevant → counts toward false positive tracking
New field in alert_log: dismissal_reason.

### Decision 8 — Dismissed Alert Outcome Follow-Up
When action_taken = dismiss AND outcome confirms alert was correct:
followup_queued flips true. Agent D sends follow-up to original Slack thread.
No new data model. Uses existing alert_log fields.

### Decision 9 — Alert Delivery Timing Optimisation
Agent D learns Slack engagement patterns per founder.
Non-critical alerts held for high-attention windows.
H-series (critical) alerts NEVER held.
New fields in client_config: delivery_timing_enabled,
last_engagement_pattern, delivery_timing_preference.

### Decision 10 — Pre-Fire Uncertainty Communication (Agent D Requirement)
Every alert must include plain English uncertainty statement.
Format: "I'm [X]% confident. What I'm less certain about: [specific element]."
Enforced at Agent D level same as Evidence Stack structure.

### Decision 11 — Return Timing Segmentation Required in Loop Staging
Days 1-3: impulse_regret | Days 7-14: fit_quality | Days 21-30: lifestyle_change
Add return_lag_segment to Loop staging tables.
Different root cause and remedy per segment.

### Decision 12 — Return Reason Contamination
Loop reason codes unreliable. Gorgias complaint text more accurate.
When both exist for same order, Agent B weights Gorgias over Loop.

### Decision 13 — Influencer Profile Table
New table: influencer_profile — creator-level, cross-campaign.
Tracks: campaign history, return-adjusted ROAS by season, category performance,
audience decay indicator, relationship tier.
seed_tiktok.py must seed creator-level data across multiple campaigns per creator.

### Decision 14 — Planning Mode Withdrawn Entirely
Forward-looking planning intelligence is out of scope. Not Horizon 2.
Profit Sentinel's job is profitability monitoring, not planning advisory.
Closed — do not reopen.

### Decision 15 — Competitor/Auction Pressure Deferred to Horizon 2
Meta auction_competitiveness and vertical_cpm_benchmarks wiring into
Evidence Stack Layer 2 deferred post-beta.
Revisit at Month 6 with real client data.
Closed for beta — do not reopen until Month 6.

### Decision 16 — Agency Tier Is A Product, Not Just Pricing
Product experience defined: portfolio health score, cross-portfolio anomaly
detection, white-label alert delivery, agency-level suppression,
benchmark by portfolio vs vertical vs brand.
Build at Month 3 before first agency pitch.

---

## OPEN DECISIONS OUTSTANDING AFTER THIS SESSION

| Open Decision | Blocks |
|---------------|--------|
| Verification category for all 41 alerts | Agent B build |
| Promotion threshold values (per-client and cross-network) | Agent B build |
| Dismissal reason threshold (churn signal definition) | Agent C design |
| causal_pattern_validation seed data | Agent B historical context |

---

## DOCUMENTS UPDATED THIS SESSION

### technical_architecture.md
- 4 new public schema tables: causal_pattern_validation, candidate_signals,
  founder_preference_profile, influencer_profile
- client_config: 5 new fields
- alert_log: 4 new fields
- Section 14 (new): full alert verification architecture

### product_strategy.md
- Section 3A (new): alert library placeholder with verification_category requirement
- Section 7: agency tier product design specification
- Section 12: 5 new closed decisions, 2 new open decisions,
  2 new unvalidated assumptions
- Section 13: design principles 9 and 10

### Blueprint v8
- No changes. Nothing in this session touched GTM, pricing, moats,
  or competitive positioning.

---

## CONTEXT FOR NEXT SESSION

Remaining learning topics:
2. Fashion business nuance of Shopify brands
3. Causal graph and knowledge graph
4. Technical structure
5. Data science and ML
6. Gen AI
7. Customer discovery

Next build action (from state_2026_05_17.md):
seed_meta.py consuming seed_manifest_shopify.json.

Pre-Agent B design tasks outstanding:
- Verification category assignment for all 41 alerts
- causal_pattern_validation seed data
- candidate_signals promotion threshold finalisation
