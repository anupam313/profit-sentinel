# Profit Sentinel — Chat Context
## Date: 2026-05-23
## Session: Alert Review — E-series Complete (v2), D-series Pending

---

## SESSION PURPOSE

Continuation of E-series alert review from state_2026_05_23_e_series_eod.md.
E1 already locked. This session: E2 critiques 2/3/4 → E2 alert language →
E3 → E4. Outcome: E2/E3/E4 all dropped from Phase 1.

---

## GOVERNING PRINCIPLES — THIS SESSION

### Monitor-and-Wait Principle (NEW — established this session)
Any alert classified as Monitor-and-Wait that cannot diagnose cause
from Phase 1 connectors is dropped from Phase 1 entirely.

Reasoning chain that established this:
- Alert requires: specific action + same-day execution + diagnosable cause
- Monitor-and-Wait by definition means no immediate action exists
- Surfacing undiagnosable signals in any format (alert or weekly summary)
  damages founder trust more than omitting them
- "We see the problem but don't know why" is worse than silence for a
  product whose entire value proposition is explaining the why

### Governing Principles From Previous Session (unchanged)
- Real-Data Safety Rule: wrong alert at beta worse than missed alert
- Agency-Managed Data Rule: never rely on naming conventions
- Onboarding Question Rule: ask founder when inference unreliable

---

## E1 — FULLY LOCKED (unchanged from previous session)

See chat_context_2026_05_23_e_series.md for full E1 spec.
Do not re-open.

---

## E2 — DROPPED FROM PHASE 1

### Deliberation Summary

**Critique 2 (trajectory) was started but exposed deeper structural gaps:**

**Gap 1 — Wrong metric definition:**
- Current locked definition: trailing 90d repeat purchase rate
- Problem: distorted by acquisition volume — new customers drag denominator
  before they've had time to repeat
- Correct definition: cohort-based — of customers who bought 90–180 days ago,
  what % bought again in last 90 days?
- S33 pre-check was a patch for a bad metric. With cohort definition, S33
  is unnecessary.

**Gap 2 — Post-event demand pull-forward:**
- After BFCM, end-of-season clearance, flash sales: customers are sated,
  repeat rate naturally falls 6–8 weeks
- This is demand pull-forward, not retention failure
- Collection launch suppression was locked but post-sale suppression was
  entirely absent — systematic false positive source

**Gap 3 — Six cause buckets, none diagnosable from Phase 1 data:**
1. CRM/Operational — win-back flow broken, wrong segment
2. Product — collection underperformed, price creep, sizing degraded
3. Competitive — competitor captured the cohort (no internal signal)
4. Acquisition pollution — low-intent buyers inflated cohort temporarily
5. Macro/Seasonal — discretionary spend contraction
6. Channel mix shift — cohort moved to marketplace/retail stockist

**Narrow version tested and rejected:**
- Fast concentrated high-LTV drop (5%+ of top cohort in 2 weeks)
- Maths confirmed: ~3,000 VIP customers at $5M GMV, signal statistically
  meaningful at 150+ customer drop
- But: even concentrated fast drop requires investigate-first. Wrong Klaviyo
  win-back to customers who left due to product disappointment damages
  most valuable relationships.

**Weekly summary version tested and rejected:**
- "Important cohort not working but we don't know why" signals product
  incompleteness to a senior business person
- Vague "look at areas outside our data" language discourages rather than helps
- Specific hypotheses without data backing are not credible at beta

**Final decision: E2 dropped from Phase 1. Deferred Phase 2.**
Condition for Phase 2 rebuild: 6+ months real client outcome data,
validated founder behaviour on retention signals, ability to genuinely
explain the why not just surface the what.

---

## E3 — DROPPED FROM PHASE 1

### What It Was
High-LTV customers (top LTV decile) showing reduced email engagement
AND no purchase in 60 days.

### Why Dropped
- Same six-cause-bucket problem as E2
- VIP segment at $5M GMV = ~340 customers generating ~60% of revenue
- Wrong action (Klaviyo win-back) with a disappointed VIP is more
  damaging than no action — these are the highest-value relationships
- 60-day quiet window is slow-moving — nothing specific happened today
- Weekly summary version rejected for same reasons as E2

**Final decision: E3 dropped from Phase 1. Deferred Phase 2.**

---

## E4 — DROPPED FROM PHASE 1

### What It Was
Post-purchase email sequence (Flow 3) driving fewer repeat purchases
than prior 90-day average.

### Why Dropped
- Cannot distinguish signal from attribution noise (15–20% of flow
  revenue is low-confidence attribution)
- Cause set: content change, audience shift, offer expiry, attribution
  noise — not diagnosable from available data
- Monitor-and-Wait classification was already a warning sign
- Same structural failure as E2/E3

**Final decision: E4 dropped from Phase 1. Deferred Phase 2.**

---

## E-SERIES PHASE 1 FINAL STATE

**Only E1 is active in Phase 1.**

| Alert | Decision | Reason |
|-------|----------|--------|
| E1 | ACTIVE | Diagnosable cause, specific action (check last 3 sends) |
| E2 | PHASE 2 | Six cause buckets, none diagnosable from Phase 1 data |
| E3 | PHASE 2 | Same as E2, higher stakes with wrong action |
| E4 | PHASE 2 | Attribution noise indistinguishable from signal |

---

## D-SERIES — INITIAL READ (deliberation pending)

**D1 — Contribution Margin Compression**
Alert 4 from core five. Already locked. No deliberation needed.

**D2 — Discount Dependency Creep**
% orders using discount code rising over 90 days.
Initial read: LIKELY DROP. Reducing discount dependency is a 3-month
strategic decision, not a 9am action. Same Monitor-and-Wait failure.

**D3 — COGS Step Change Impact**
Supplier cost increase flowing to margin over 60-day window.
Initial read: QUESTIONABLE. Founder approved the supplier invoice —
they already know COGS went up. Alert tells them what they know, 60 days later.

**D4 — Fulfilment Cost Anomaly**
Per-order fulfilment cost diverging from baseline.
Initial read: STAYS. Signals 3PL billing error. Specific, verifiable,
same-day action: call 3PL and query invoice.

**D5 — Klaviyo Flow Revenue Declining**
Revenue per email sent declining across flows.
Initial read: LIKELY PHASE 2. Same diagnosis problem as E4.

**D6 — Seasonal Baseline Diagnostic**
Prevents false alerts during predictable seasonal movement.
Initial read: STAYS AS SUPPRESSION LOGIC. Not a founder-facing alert —
infrastructure only.

---

## NEXT SESSION STARTING POINT

1. Load: state_2026_05_23_e_series_v2.md (this session's state),
         chat_context_2026_05_23_e_series_v2.md (this file),
         agent_d_build_spec.md,
         technical_architecture.md,
         product_strategy.md
2. First decision: confirm Monitor-and-Wait = Phase 2 as formal rule
3. D-series deliberation: D2 → D3 → D4 confirm → D5 → D6 framing
4. Then C → B → A → H
5. Consolidated Claude Code prompt after H-series complete
