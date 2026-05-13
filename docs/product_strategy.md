# Profit Sentinel — Product Strategy
*Version: Post-critique redesign | Status: Pre-customer discovery*

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

### vs Triple Whale (Primary Competitor)

**What Triple Whale Moby can do:**
- Cross-platform analysis across Meta, Google, Klaviyo
- Post-return ROAS by channel (when asked)
- Anomaly flagging in marketing data
- Conversational queries via Moby chat
- Moby Agents can be configured to run scheduled analyses

**What Triple Whale cannot do:**
- Gorgias connector does not exist in their stack — sizing complaint velocity signal unavailable
- Fashion-specific causal reasoning — generic across 60,000 brands in all verticals
- Fully autonomous firing without user configuration — Moby requires user to ask or configure agents
- Slack-native conversational thread — their interface is dashboard-bound
- Cross-client operational data (they have GMV benchmarks but not validated causal accuracy rates)

**Honest assessment of differentiation:**
- Post-return ROAS by channel: Triple Whale can answer this. **Thin differentiation on pure pull queries.**
- Gorgias sentiment chain: Triple Whale cannot do this. **Real but fragile** — they could add connector.
- Proactive firing: Triple Whale moving in this direction. **Time-limited differentiator — 12-18 month window.**
- Fashion Causal Graph with validated accuracy rates: Cannot replicate without same vertical time. **Most durable differentiator.**

**The honest window:** 12-18 months before Triple Whale closes most of the generic gap. Speed to 20 clients and Fashion Intelligence Network data is the critical priority.

### vs Northbeam
Attribution-only scope. No operational signals. Enterprise pricing ($12K-$255K/year). Different buyer. Not direct competition for sub-$10M brands.

### vs Polar Analytics
Dashboard-first despite AI features. No fashion vertical specificity. Pricing scales steeply above $5M GMV. No early warning alerts.

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

### Objective
Validate or pivot the Profit Sentinel product hypothesis. Three possible outcomes:
1. Proceed — hypotheses validated, build as designed
2. Refine — core is right but specific elements need adjustment
3. Pivot — fundamental problem with core premise

### Target Profile for Interviews
- Shopify fashion founder or co-founder (not CMO, not analyst)
- $1M-$10M GMV, DTC-first, US-based
- Running Meta + TikTok
- Has at least Klaviyo and Gorgias
- No full-time data analyst

### Five Interview Sections

**Section 1 — Decision-Making Reality**
Q1: "Walk me through the last time something went wrong — a ROAS drop, return spike. How did you find out? How long after it started?"
Q2: "When you notice something is wrong, what's your process for figuring out why? Step by step."
Q3: "Tell me about a decision in the last 3 months you later wished you'd made differently. What information would have changed it?" *(Most important question)*

**Section 2 — The Scenario Test (Core Hypothesis)**
Read exactly: "It's 8am Tuesday. You get a Slack message: 'Your CPM on Midnight Blue Dress has risen 39% over 72 hours — Day 1 $18.40, Day 2 $21.20, Day 3 $25.60. Verify in Meta Ads Manager right now. This pattern preceded a ROAS decline 3 of 4 times in your account — most recently October 14th when ROAS dropped from 3.4 to 2.1 in 6 days. Recommend reducing budget 30% today.' What do you do?"

Four response types:
- **Type A** (acts immediately): High fit. Core early adopter.
- **Type B** (verifies then acts): Medium-high fit. Evidence Stack addresses this.
- **Type C** (defers to agency): Medium fit. Agency channel opportunity.
- **Type D** (waits to see): Low fit now. Needs to experience preventable loss first.

**Section 3 — Data Sources and Quality**
- Which of the 7 connectors do they use?
- Do they tag Gorgias tickets consistently? *(Critical — Gorgias chain only works with consistent tagging)*
- What fires first when something goes wrong — Meta, Shopify, support inbox, or elsewhere?

**Section 4 — Signal Validation**
Read the 5 alert types. For each: "Is this something you already know, could figure out but it takes time, or genuinely cannot see today?" Their ranking = build priority order.

**Section 5 — Pivot Detection**
Q: "If I could give you one piece of information about your business you don't currently have — just one — what would it be?"
*The answer to this question is the most important signal in the entire discovery process.*

### Scoring Rubric
7 signals × 0/1/3 points = max 21 points
- 15-21: Strong fit — prioritise for beta
- 8-14: Medium fit — later cohort
- 0-7: Weak fit — do not prioritise

### Pivot Signals to Watch
- Majority score Type C or D on scenario test
- 10+ founders say all five insights are already obvious to them
- Gorgias tagging is inconsistent in 10+ brands (invalidates sentiment chain)
- 10+ founders say their one missing piece is something not in current product scope

---

## 12. Open Decisions and Deferred Items

**Deferred to post-pilot:**
- Full licensing enforcement (query user tracking in client_config added later)
- Agency command centre UI
- Action Layer (auto-pause ads, update Shopify tags)
- Benchmark comparisons (need 20+ clients in same subcategory for statistical validity)
- Supply chain connectors (fragmented market, Shopify inventory covers critical signal)
- Recharge subscription connector
- BNPL connectors (Affirm, Afterpay, Klarna)
- EU geographic expansion (GDPR compliance, EU data residency node)
- Middle East expansion

**Still open / not yet decided:**
- Exact Slack bot framework version and deployment platform
- Whether GA4 uses server-side tracking (Littledata) or client-side GTM for real clients
- Exact format of the Python CLI confirmation flow for testing
- Whether to use Railway or Vercel for agent hosting in production
- Sentry instrumentation requirement — mandatory or advisory during onboarding

**Assumptions not yet validated by customer discovery:**
- Founders will act on proactive AI alerts before they can see the problem themselves
- Gorgias tagging is consistent enough across target segment for sentiment signal to work
- The 8-14 day causal lag between Gorgias complaints and return spikes holds for most fashion brands
- $299/month price point is the right entry (may be too low or too high depending on perceived value)
- Slack is the right delivery channel (not email, not mobile app, not Shopify admin)

---

## 13. The Non-Negotiable Design Principles

1. **Trust before intelligence.** Numbers must be validated and trusted before any alert fires.

2. **Cross-source explanation, not detection.** Founders know something is wrong. We tell them why across sources they cannot join manually.

3. **Show the working.** Every metric has a "Show me the maths" drill-down. Every alert has verifiable raw numbers in Layer 2. Transparency is the trust mechanism.

4. **No dead ends in onboarding.** Every gap type has a resolution path. Every resolution path has a fallback. Missing connectors become waitlist entries not error states.

5. **Slack is the complete interaction surface.** Not a notification channel. Operational interaction — alerts, follow-ups, queries, approvals — all happen in Slack. Web app is configuration and audit only.

6. **Agent A never calls Claude.** Threshold scanning is pure Python. No LLM calls in the hot path. Claude is called only for natural language formatting and conversational responses.

7. **Data quality gates before inference.** No confident wrong statement. Signal-level DQ scores determine whether alerts fire, fire with caveat, or are suppressed and replaced with fix guidance.
