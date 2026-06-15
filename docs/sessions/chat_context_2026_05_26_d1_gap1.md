# Profit Sentinel — Chat Context
## Date: 2026-05-26
## Version: v1
## Session: Alert Review — D1 Gap 1 Complete

---

## SESSION PURPOSE

Continue alert review from state_2026_05_23_e_series_v2.md.
D-series initial read completed last session. This session:
full three-pass critique of D1, nine gaps identified, Gap 1 deliberated
and locked. Next session starts at D1 Gap 2.

---

## GOVERNING PRINCIPLES

### Monitor-and-Wait Principle (Established 2026-05-23)
Monitor-and-Wait alerts without diagnosable cause from Phase 1
connectors → dropped from Phase 1 or deferred Phase 2.

### Action-First Principle (Reinforced D1 deliberation)
Alert requires: specific action + same-day execution + diagnosable
cause. Missing any of these → not an alert.

### No Margin Figure Without Reliable COGS (NEW — this session)
Never state margin % or $ margin impact unless COGS is Tier 1 or 1.5.
Tier 2/3 → driver-only cost pressure alert. No margin figure.
Rationale: wrong margin figure at beta destroys trust faster than
no margin figure. A founder who checks our 31% against their P&L
and finds it wrong will never trust Profit Sentinel again.

---

## D1 THREE-PASS CRITIQUE SUMMARY

### What D1 Was (Original Design)
Alert: "Contribution margin dropped from 31% last month to 24% this week.
The gap is entirely explained by Meta CPM rising 28% while your prices
stayed flat."

**Missing from original:** No action. No $ impact. No COGS basis disclosed.
Causal claim is imprecise. Five-driver framework is incomplete.

### Nine Gaps Identified

1. COGS tier disclosure — margin figure untrustworthy without basis
2. Threshold undefined — what drop magnitude, what window
3. Causal decomposition incomplete — one driver named, others ignored
4. CPM → margin chain needs intermediate steps — direct claim is wrong
5. AOV decline missing from driver set — significant fashion-specific driver
6. Seasonality suppression — Q4 CPM spikes are planned, not alerts
7. "Entirely explained" framing dangerous — must be retired
8. No action named — diagnosis without prescription
9. No $ revenue impact — % drop creates no urgency or prioritisation basis

### Practitioner Layer Key Findings
- Most $2M–$10M fashion founders do not compute CM formally — they
  look at revenue and ad spend and call the gap "profit"
- COGS architecture is three-tier in current design but Tier 2 uses
  1.28 multiplier as assumption — actual multipliers range 1.10–1.50
- Five causal drivers have very different confidence levels:
  CPM (high), return rate (high), discount depth (medium),
  fulfilment cost (medium), COGS (low)
- A DTC CFO never presents margin without disclosing COGS assumption

### Structural Critique Key Findings
- "Entirely explained by CPM" is mathematically imprecise — CPM rise
  compresses ROAS, which reduces revenue efficiency, which compresses
  margin. Intermediate steps matter. Founder will push back.
- AOV decline completely absent from five-driver framework
- No "entirely explained" scenario is realistic — decompose all drivers
  with % contribution each
- Threshold undefined — fashion margins fluctuate 2–4pp naturally

---

## D1 GAP 1 DELIBERATION PATH

### Opening Challenge
Q: "Should D1 fire at all on Tier 2 or Tier 3 COGS?"
A: Challenged and refined — don't need to suppress the alert entirely,
   but must never state a margin figure without reliable COGS.

### Key Insight: CSV Upload As Tier 1.5
Most founders have COGS in Excel, updated per PO or per season.
CSV upload path creates a new Tier 1.5 that is:
- More reliable than Shopify-derived (Tier 2)
- More accessible than Finaloop (Tier 1, ~$200–500/month)
- Genuinely differentiated — no tool at this price point ingests
  founder CSV with fuzzy SKU matching and reconciliation output

### CSV Validation Flow Deliberated
Full flow established covering:
- File format, column detection, currency handling (including multi-currency
  within same file — reject if no currency column), landed vs ex-factory,
  zero/negative values, duplicate SKUs, version conflicts
- Founder-provided FX rate at upload — never live rates
- Historical inactive SKUs retained with active = false

### SKU Matching Problem
100s of SKUs in CSV cannot be reviewed during onboarding.
Three-stage solution:
1. Exact matches → write silently
2. Fuzzy matches → reconciliation output file only, never auto-write
3. COGS owner reviews offline, re-uploads corrected version → exact
   matching only on re-upload

Reconciliation output file also serves as internal COGS owner reference.

### COGS Owner Flow Deliberated
- Collected during onboarding contextually, not as a form field
- Always CC founder — never exclusive routing to COGS owner
- US business days only, US federal holiday calendar hardcoded
- Escalation cadence: Day 0/5/10/15/20 with hard stop after Day 20
- Opt-out button suppresses existing SKU reminders, new SKUs still cycle
- Post opt-out: one-time note in weekly summary only
- Second consecutive miss pattern: accelerate escalation to Day 5

### COGS Knowledge Reality Check
Challenge: Do all founders maintain COGS diligently?
Answer: No — loose assumption. Finance/buying background founders yes.
Creative/marketing background founders often no. CSV upload is an
enhancement for founders who have data, not a prerequisite for D1.

This reinforces: D1 must fire even with zero COGS data, as driver-only
cost pressure alert. Universal baseline, not COGS-gated.

---

## D1 GAP 1 — LOCKED DECISIONS

**4-tier COGS architecture** — see full spec in state file.

**Universal baseline alert** — driver-only, no margin %, no $ impact,
for all Tier 2/3 brands. Full margin alert for Tier 1/1.5 only.

**CSV upload service** — /connectors/cogs_csv_processor.py to be built.
Not a trivial engineering task — fuzzy matching, reconciliation output,
multi-file handling, currency conversion. Flag as non-trivial build.

**H20 new H-series alert** — new SKU COGS gap, founder_action_required
routing, fresh escalation cycle per batch.

**Agent D pre-condition** — read cogs_tier_active before formatting D1.
One template or the other — never hybrid.

---

## WHAT D1 ALERT LOOKS LIKE (CURRENT DESIGN — BEING REVISED)

**Tier 1/1.5 (target state — after all 9 gaps resolved):**
Not yet written — pending Gaps 2–9 deliberation.

**Tier 2/3 universal baseline (locked from Gap 1):**
"Three cost signals are moving against you this week:
[Driver 1 with specific numbers], [Driver 2], [Driver 3].
Connect your cost data for exact margin impact."

**Action:** To be added in Gap 8 deliberation.
**$ impact:** To be added in Gap 9 deliberation (Tier 1/1.5 only).

---

## D-SERIES INITIAL READ (From Previous Session)

| Alert | Initial Read |
|-------|-------------|
| D1 | In progress — Gap 1 locked |
| D2 — Discount Dependency Creep | LIKELY DROP — Monitor-and-Wait, no 9am action |
| D3 — COGS Step Change Impact | QUESTIONABLE — founder already knows COGS changed |
| D4 — Fulfilment Cost Anomaly | LIKELY STAYS — call 3PL today |
| D5 — Klaviyo Flow Revenue Declining | LIKELY PHASE 2 — same problem as E4 |
| D6 — Seasonal Baseline Diagnostic | STAYS AS SUPPRESSION LOGIC only |

---

## NEXT SESSION STARTING POINT

1. Load: state_2026_05_26_d1_gap1.md, this file,
         agent_d_build_spec.md, technical_architecture.md,
         product_strategy.md
2. Start: D1 Gap 2 — Threshold definition
   Key question: what magnitude of drop, over what window, clears
   the noise floor? Fashion margins fluctuate 2–4pp naturally.
3. Work through Gaps 3–9 in order
4. Write D1 alert language after all 9 gaps resolved
5. Then D2 → D3 → D4 → D5 → D6 → C → B → A → H
6. Consolidated Claude Code prompt after H-series only
