# Profit Sentinel — Session State
## Date: 2026-06-03
## Session: D1 Gap 6 — COGS/S21 component CLOSED (second save of the day)
## Supersedes: state_2026_06_03_d1_gap6_seam2_closed.md (KEEP both — prior retained as audit trail)

---

## SESSION SUMMARY

Closed the COGS/S21 (supplier cost increase) component of D1 Gap 6 — the third of the
five S44 components, after CPM (Gap 4) and return-rate (Seam 2 + C3 this morning). The
review went well beyond a seam check: it reshaped how the margin alert behaves for brands
without trustworthy cost data, and it surfaced a challenge to a LOCKED Gap 1 decision
(recorded as a flagged proposal, NOT confirmed).

Canonical files UPDATED this session: agent_d_build_spec.md, cross_alert_orchestration.md,
technical_architecture.md, d1_validation_gates.md, pre_agent_build_checklist.md,
product_strategy.md. seed_decisions_gap_f_g.md and causal_graph.py NOT edited (S-rule
defs + code stay batched).

Two Gap-6 items remain: discount-depth/S19 and operational-cost/S20 components (untouched
— do NOT assume clean), plus the final cross-component residual-disclosure pass.

---

## WHAT CLOSED THIS SESSION — COGS / S21

The core realisation (founder-driven): contribution margin has five drivers — ad cost,
returns, discounting, mix, product cost. The first four are VISIBLE in the connected
data; product cost is NOT, unless the founder feeds it in. So a COGS-driven margin dip is
the one dip we cannot detect without a cost feed — the computed margin literally doesn't
move when real cost rises against an assumed-constant value. This makes the "ask them to
update cost when we detect a dip" idea circular, and forces the decisions below.

1. **60-day window retired → per-product sell-through** of pre-increase stock (fast
   movers reflect the new cost sooner). No fixed calendar window (No-Hardcoding).
2. **Cost-increase driver is feed-only** — detectable only for trustworthy-cost-feed
   brands (Finaloop/CSV/well-maintained Shopify cost). Structurally invisible otherwise.
3. **No margin VERDICT for no-trustworthy-COGS brands** — not even driver-only. They get
   component signals (returns/CPM/discounting). *(Tightens Gap 1 driver-only →
   component-only — FLAGGED PROPOSAL, see below.)*
4. **Cost-update ask is proactive at onboarding, never reactive** (we can't detect the
   change to trigger it). New-SKU-missing-cost = the reliable nudge; periodic cadence =
   weak lever.
5. **Staleness-decay** governs claims: full figures within the founder's own stated
   refresh rhythm → live caveat past it → no margin figure when stale. Keyed to the
   founder's rhythm, never a fixed number (the invented "90 days" was explicitly
   retracted).
6. **Revenue-weighted cost coverage**, not a blanket yes/no — speak confidently only for
   the revenue actually costed (reuse Gap 1 sku_cost_coverage_by_revenue).
7. **State-driven disclosure**, not a per-alert footnote: clean when fresh / live caveat
   when aging / no figure when stale; basis one click away even on clean alerts. A
   footnote on every alert was rejected (erodes confidence, goes blind when it matters).
8. **Honesty gap + follow-ups logged**: Shopify's cost field is a single non-retroactive
   value with no old-vs-new layers, so the phased curve needs an average-cost feed
   (Finaloop/Stocky), else narrate the phasing without a fabricated "% realized". Landed
   cost: flat 1.28 mis-scales a supplier change; duty/tariff shocks have no supplier
   event (possible missing event type). A dedicated COGS connector is DEFERRED
   (discovery-gated): no single clean source at this tier; approximate auto-COGS is more
   dangerous than honest manual COGS; off the core moat.

---

## FLAGGED PROPOSAL — AWAITING FOUNDER DECISION (NOT LOCKED)
**Tighten Gap 1 "driver-only" → "component-only" for no-trustworthy-COGS brands.** Gap 1
is a LOCKED decision; this challenges it. A margin verdict implies a computed margin we
cannot defend without trustworthy cost, so the proposal removes the verdict entirely for
those brands. Recorded as a proposal in product_strategy.md Section 12 and
cross_alert_orchestration.md; gate D1-G9 is provisional on it. Founder to confirm or
reject. Do NOT build on it until confirmed.

---

## SHOPIFY COST-FIELD FACTS (verified 2026-06-03)
- "Cost per item" is a single manual value per variant, usually product cost only
  (freight/duties excluded), and is NOT retroactive (update it, past sales don't change).
- Shopify allows only one cost per product — no old-vs-new cost layers (FIFO/average
  lives in accounting/Stocky, not Shopify). So the phase-in curve isn't computable from
  Shopify alone.

---

## GOVERNING PRINCIPLES — LOCKED (cumulative, carried forward)
- Monitor-and-Wait; Action-First; No Margin Figure Without Reliable COGS (Gap 1);
  No Hardcoding; Phase-1 No-Seed; Measure-Before-Build; Observe-Don't-Predict.
- Narrate-Don't-Suppress on an unreliable/unconfirmed event (2026-06-03).
- Anchor the action on the signal, not on the founder's memory (2026-06-03).
- **Feed-only honesty on cost (2026-06-03):** never assert a margin figure or a
  cost-increase driver on cost we can't trust; disclose staleness by state, decay claims
  as cost ages, and degrade to component signals rather than fabricate.

---

## FILES UPDATED THIS SESSION (applied; replace in project)
- **agent_d_build_spec.md** — COGS/S21 component RESOLVED subsection; Gap 6 header +
  status + NINE GAPS row updated.
- **cross_alert_orchestration.md** — O-14 COGS half CLOSED; Gap 1 FLAGGED PROPOSAL +
  COGS cross-cutting rules block added.
- **technical_architecture.md** — client_config: cogs_refresh_rhythm_days +
  cogs_last_confirmed_at fields; staleness-decay / feed-only / per-product sell-through
  notes; refresh-rhythm onboarding question.
- **d1_validation_gates.md** — gates D1-G9 (no margin figure without trustworthy feed),
  D1-G10 (staleness-decay), D1-G11 (revenue-weighted coverage).
- **pre_agent_build_checklist.md** — D-GAP6-12..15 (sell-through; feed-only/no-verdict;
  onboarding capture + staleness-decay + coverage; state-driven disclosure).
- **product_strategy.md** — fixed the 60-day orphan in the D3 description; Section 12:
  COGS scoping decision + Gap 1 FLAGGED PROPOSAL; changelog stamp.

**NOT edited (intentional):** seed_decisions_gap_f_g.md (S21 relabel — retire 60-day,
feed-only scope — logged for the orchestration pass); causal_graph.py (code batched
post-H).

---

## D1 GAP STATUS

| Gap | Status |
|-----|--------|
| Gap 1 — COGS tier disclosure | LOCKED ✓ (component-only tightening FLAGGED, not confirmed) |
| Gap 2 — Threshold (Trigger A + B) | LOCKED ✓ |
| Gap 3 — Causal decomposition | LOCKED ✓ |
| Gap 4 — CPM → margin intermediate steps | DESIGN-COMPLETE ✓ (blocked on schema gate D1-G1) |
| Gap 5 — AOV decline retired as a driver | LOCKED ✓ |
| Gap 6 — Seasonality suppression | **WIP** — dependencies + return-rate (Seam 2 + C3) + COGS/S21 CLOSED 2026-06-03; discount-depth/S19 + operational-cost/S20 untouched; final residual pass owed |
| Gap 7 — "Entirely explained" framing retired | PENDING |
| Gap 8 — No action named per driver | PENDING (inherits O-19 floor + actionability gate + digest) |
| Gap 9 — No $ revenue impact (display) | PENDING |

---

## OPEN IN GAP 6 (must close before Gap 6 is done)
1. **discount-depth / S19** component — untouched (expect heavy interaction with the
   viral welcome-discount + auto-populated sale-calendar work). NEXT.
2. **operational-cost / S20** component — untouched.
3. **Final cross-component residual-disclosure consistency pass** — confirm all five
   suppressed components feed `total_measured_impact` / the residual gate identically.

---

## PENDING CLAUDE CODE ACTIONS (accumulate — execute after H-series)
Carry forward all prior (incl. Seam 2 batch). New this session (BATCHED, none built now):
- COGS S21 per-product sell-through (replace 60-day window).
- Feed-only gate on the cost-increase driver; no-margin-verdict path for
  no-trustworthy-COGS brands (PENDING founder confirmation of the Gap 1 tightening).
- client_config fields: cogs_refresh_rhythm_days, cogs_last_confirmed_at.
- Onboarding cost-capture flow + new-SKU-missing-cost detector.
- Staleness-decay + revenue-weighted coverage + state-driven disclosure logic.
- No consolidated Claude Code prompt until after H-series.

---

## NEXT SESSION STARTING POINT
New chat. Load: this file · agent_d_build_spec.md · cross_alert_orchestration.md ·
product_strategy.md · technical_architecture.md · d1_validation_gates.md ·
pre_agent_build_checklist.md · plus chat_context_2026_06_03_d1_gap6_cogs_closed.md.

**FIRST: decide the FLAGGED Gap 1 proposal** (component-only vs driver-only for
no-trustworthy-COGS brands) — gate D1-G9 and the no-verdict path depend on it.

**Then resume Gap 6 at the discount-depth/S19 component seam check** (verify against
source; do NOT assert clean), then operational-cost/S20 → final cross-component
residual-disclosure pass.

Sequence after Gap 6: 7 → 8 → 9 → D1 alert language → D2 → D3 → D5 → D6 → C → B → A →
orchestration resolution pass → H → consolidated CC prompt. (No alert language until all
9 D1 gaps resolved.)

Parked post-H: clustering-coherence validation needs factors beyond return-rate
(price-band, margin-rate, discount-behaviour, size/fit-complaint, AOV).
