# Profit Sentinel — Session State
## Date: 2026-06-03
## Session: D1 Gap 6 — return-rate Seam 2 (S17/S18 vs C3) + C3 consistency check CLOSED
## Supersedes: state_2026_06_02_d1_gap6_wip.md (KEEP both — prior retained as audit trail)

---

## SESSION SUMMARY

Closed two of the six open items in D1 Gap 6: the size-guide/photography return seam
(Seam 2) and the C3 consistency check — which folded into one finding. The canonical
files were UPDATED this session (not just logged): agent_d_build_spec.md,
cross_alert_orchestration.md, technical_architecture.md, d1_validation_gates.md,
pre_agent_build_checklist.md, product_strategy.md. seed_decisions_gap_f_g.md and
causal_graph.py were deliberately NOT edited (S-rule defs and code stay batched).

Four Gap-6 items remain: COGS/S21, discount-depth/S19, operational-cost/S20 components
(untouched — do NOT assume clean), and the final cross-component residual-disclosure
consistency pass.

---

## WHAT CLOSED THIS SESSION

### Seam 2 — size-guide (S17) / photography (S18) vs C3 — CLOSED
The seam is real, not absorbed: a size-guide change does not move category mix, so it
lands wholly as Stage-2 residual; S3/S16 don't match the event, so D1 grades it
unexplained and fires while C3 suppresses (S17 State 3). Bites in the broad
(line-wide) case.

**Resolution — route through the event-calendar layer (single source of truth), do NOT
hand-duplicate S17/S18 in D1.** D1's return component consults active
`brand_event_calendar` rows of `size_guide_update` / `photography_update` and applies
the row's `residual_threshold_pct` + decay — same consumer treatment as S3/S15/S16.
Inherits S17 State-3 / S18 State-2 via suppress_alerts vs context_alerts. Component
isolation preserved (a concurrent defect still fires past the size-change explanation).

**Default posture = narrate-don't-suppress** because the change-event source is
unreliable (verified against Shopify's current API surface): metaobject-modeled size
charts emit a reliable update webhook (Tier 1); Pages have none (poll+diff only);
theme/app effectively undetectable. A webhook proves an edit, not a meaningful change.

**Tier-1 auto-detect (BUILD, degrades gracefully, no discovery dependency):** silent
onboarding probe → subscribe to the metaobject update webhook if present → content-diff
for meaningfulness → low-confidence context note → surfaces only if a return-driven
margin movement would otherwise fire within `return_window_days`. Else narrate-on-
return-movement. Window = `return_window_days`, never fixed 14/21. Never silent-suppress
on an unconfirmed/undetectable edit.

**Affected-scope gap (honest):** `brand_event_calendar` had no affected-line column → a
size-guide event is brand-wide → Phase-1 quiet is brand-wide WITH DISCLOSURE, never a
silent brand-wide mute. Added `affected_category[]` column (batched).

**Action structure (corrected — was reassurance-led, now action-led):** headline = the
return signal + the action, anchored on the dominant **return reason** (sizing-fit /
quality-defect / not-as-pictured / channel over-returning). A size/photo change only
DOWNGRADES urgency to a deferred-action-with-expiry; founder "no change" → softener
stripped, action fires now. Anchoring on reason (not the founder's memory of edits)
makes it robust to a wrong "no" and to undetectable theme-coded edits.

**Softener FORBIDDEN when reason = quality/defect OR magnitude extreme** (defect can't be
masked). "Extreme" = OR of three brand-relative tests — any one defeats it:
1. **Level** — return residual in the far upper tail of the GROUP's own historical band
   (own-band method as the mix-shift grade; finest clustering-certified granularity; NOT
   blended brand average, NOT a fixed pp / fixed ×).
2. **Exposure** — units / margin $ at risk cross the upper end of the brand's
   materiality band.
3. **Trajectory** — still climbing through the return window instead of cresting.
Thin GROUP history → exposure fallback (withhold the level judgment). Withhold-when-
unsure → lean to action. Cross-brand/vertical benchmarks OUT (Phase 2; never pool
across verticals). All three provisional, outcome-calibrated.

### C3 consistency check — CLOSED as a finding (provisional lock + routing)
C3 is specified two contradictory ways: headline ("SKU return rate > 2× brand average,
7+ days" — blended average + fixed ×) DIVERGES from D1; seeded scenarios (formalwear
32% vs 22% "structural to sub-category"; menswear 15% vs 28% "must not misread" +
thin-history hold; weekend +6pp "structural — must not trigger") ALIGN with D1 in
intent but were never written into C3's stated method. The category-baseline rule (S15)
is wired ONLY to D1 today. Thin-history fallback differs: D1 → exposure (can act); C3
(seed) → 90-day monitor-and-wait.

**Provisional lock** of D1's extreme yardstick + action structure. Two reconciliation
items logged for the C-series (return-alert) review: (a) retire C3's blended-average +
fixed-2× headline, wire C3 to the same per-category baseline D1 uses; (b) decide the
shared thin-history fallback (exposure vs monitor-and-wait). The "C3 consistency check"
open item closes into this note (answer: no as written, yes in intent). Provisional
because it inherits the still-open O-19 materiality floor (Gap 8).

---

## SHOPIFY API FINDING (verified 2026-06-03 — corrects an earlier overclaim)

Earlier in the session I called size-guide change detection flatly unreliable. Accurate
statement: **no uniform source; a genuinely reliable push source exists for
metaobject-modeled size charts**, polling-or-nothing otherwise.
- Metaobjects (Shopify's standard for size charts) → create/update/delete webhooks,
  type-filterable, with updatedAt; can reference products (→ affected scope).
- Online Store Pages → NO create/update webhook (poll + diff only).
- Theme code / app → effectively undetectable.
- Product images ride the standard product-update payload (photography diff-detectable
  at product level); theme lookbook/section swaps do not.

---

## GOVERNING PRINCIPLES — LOCKED (cumulative, carried forward)
- Monitor-and-Wait (2026-05-23); Action-First (2026-05-23)
- No Margin Figure Without Reliable COGS (Gap 1); No Hardcoding (Gap 2)
- Phase-1 No-Seed (2026-06-02); Measure-Before-Build (2026-06-02); Observe-Don't-Predict
  (2026-06-02)
- **Narrate-Don't-Suppress on an unreliable/unconfirmed event (2026-06-03).** Silent
  suppression is earned only by reliable detection or founder confirmation; otherwise
  surface with context. Withholding errs toward action (the safe direction).
- **Anchor the action on the signal, not on the founder's memory (2026-06-03).** Return
  actions key off the return reason, not off whether the founder recalls changing
  something — robust to wrong denials and undetectable edits.

---

## FILES UPDATED THIS SESSION (applied; replace in project)
- **agent_d_build_spec.md** — Seam 2 resolution (event-layer routing, narrate default,
  Tier-1 detect, affected-scope caveat); action structure; "extreme" three-test; C3
  finding; Gap 6 section header + NINE GAPS table updated.
- **cross_alert_orchestration.md** — O-14 Gap-6 half: Seam 2 + C3 check CLOSED;
  C-series-review open items extended with the two C3 reconciliation items + shared
  brand-action event handling.
- **technical_architecture.md** — `size_guide_update` added to event_type list (was
  missing); `affected_category[]` column added to brand_event_calendar; brand-action
  detection note (Tier 1/2/3, content-diff, context-not-suppress, return_window_days).
- **d1_validation_gates.md** — new gates D1-G6 (extreme defeats softener), D1-G7
  (thin-history → exposure), D1-G8 (brand-action quiet must be earned).
- **pre_agent_build_checklist.md** — D-GAP6-8..11 (event routing; schema additions;
  Tier-1 detect; action + extreme test).
- **product_strategy.md** — Section 12: size-guide detection decision (Still Open) +
  metaobject-fraction question (Assumptions Not Yet Validated) + changelog stamp.

**NOT edited (intentional):** seed_decisions_gap_f_g.md (S17/S18 relabel —
context-not-suppress, brand-relative window — logged for the orchestration pass);
causal_graph.py (detection code batched post-H).

---

## D1 GAP STATUS

| Gap | Status |
|-----|--------|
| Gap 1 — COGS tier disclosure | LOCKED ✓ |
| Gap 2 — Threshold (Trigger A + B) | LOCKED ✓ |
| Gap 3 — Causal decomposition | LOCKED ✓ |
| Gap 4 — CPM → margin intermediate steps | DESIGN-COMPLETE ✓ (blocked on schema gate D1-G1) |
| Gap 5 — AOV decline retired as a driver | LOCKED ✓ 2026-06-01 |
| Gap 6 — Seasonality suppression | **WIP** — 2 dependencies CLOSED; return-rate Seam 2 + C3 check CLOSED 2026-06-03 (provisional lock, 2 C-series reconciliation items logged); COGS/discount-depth/opex untouched; final residual pass owed |
| Gap 7 — "Entirely explained" framing retired | PENDING |
| Gap 8 — No action named per driver | PENDING (inherits O-19 floor + actionability gate + digest) |
| Gap 9 — No $ revenue impact (display) | PENDING |

---

## OPEN IN GAP 6 (must close before Gap 6 is done)
1. **COGS / S21** component — untouched (seam check, not assert-clean). Rule: 60-day
   window post supplier_cost_increase, State 2. Expect the 60 days is a hardcoded guess
   → brand-relativize.
2. **discount-depth / S19** component — untouched (expect heavy interaction with the
   viral welcome-discount + auto-populated sale-calendar work).
3. **operational-cost / S20** component — untouched.
4. **Final cross-component residual-disclosure consistency pass** — confirm all five
   suppressed components feed `total_measured_impact` / the residual gate identically.

---

## PENDING CLAUDE CODE ACTIONS (accumulate — execute after H-series)
Carry forward all prior. New this session (all BATCHED, none built now):
- Brand-action event routing into D1 return component (read size_guide_update /
  photography_update rows; residual_threshold_pct + decay).
- Schema: add `size_guide_update` to event_type; add `affected_category[]` column.
- Tier-1 size-guide detection: onboarding probe + metaobject update-webhook
  subscription + content-diff meaningfulness filter.
- Return-driver action anchored on return reason + the three-test "extreme" gate.
- No consolidated Claude Code prompt until after H-series.

---

## NEXT SESSION STARTING POINT
New chat. Load: this file · agent_d_build_spec.md · cross_alert_orchestration.md ·
product_strategy.md · technical_architecture.md · d1_validation_gates.md ·
pre_agent_build_checklist.md · plus chat_context_2026_06_03_d1_gap6_seam2_closed.md.

**Resume Gap 6 at the COGS/S21 component seam check** (verify against source; do NOT
assert clean), then discount-depth/S19 → operational-cost/S20 → final cross-component
residual-disclosure pass.

Sequence after Gap 6: 7 → 8 → 9 → D1 alert language → D2 → D3 → D5 → D6 → C → B → A →
orchestration resolution pass → H → consolidated CC prompt. (No alert language until all
9 D1 gaps resolved.)

Parked post-H: clustering-coherence validation needs factors beyond return-rate
(price-band, margin-rate, discount-behaviour, size/fit-complaint, AOV).
