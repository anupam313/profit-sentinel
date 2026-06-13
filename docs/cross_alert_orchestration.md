# Profit Sentinel — Cross-Alert Orchestration Ledger
## Created: 2026-05-31 (D1 Gap 4 session)
## Status: LIVING DOCUMENT — capture phase, not resolution phase
## Updated: 2026-06-09 (C-series review — O-6 + O-30 resolved, O-31 added + earlier mirror-sync) — O-6 returns router RESOLVED-IN-PLACE: C-chain owns + always fires standalone, D1 references (never re-alerts), shared abnormal-returns yardstick mandatory, sequel-not-duplicate timing, no-warning fallback = carry cost not reason, dollar magnitude parked O-28, S35 ratification + agent_d L2166 tightening → orchestration pass. O-29 logged (returns-reference founder wording → alert-language stage, collaborative). O-30 RESOLVED (cohort-based predict-then-check — in-flight vs next cohort; directional-not-stat-sig; dials/yardstick → C3). O-31 added (GENERAL all-alerts rule: deterministic skeleton frozen at beta; dials instrumented-then-calibrated, never self-tuned; Evidence-Stack Layers 2/3 consume these dials). Earlier same-day (mirror-sync): O-26 scope extended — design-ownership map must enumerate STATUS-mirror homes; pre_agent D-16 + header and d1_gates header + G12 note corrected to the cogs_parked closeout. | prior: 2026-06-08 (Gap 6 closeout → COGS parked) — O-24a retired; test-data-constant check closed-clean; O-24b reframed + blocked on the new COGS foundation (O-28); all-explained gate + residual-band cutoffs blocked on O-28; O-28 COGS foundation added (own section, parked, discovery-blocked); Gap 6 does NOT lock — parked; build pivots D→C (C-series next). Earlier same-day (residual pass): O-14/O-18/O-24/O-26 updated; C10/Alert-3 fulfilment seam → C-series; building-vs-burning → Horizon-2; Gap-1 component-only adopted as working assumption.

---

## PURPOSE

A single persistent record of every point where two or more alerts in the
41-type library share a **root cause**, a **data signal**, a **delivery
moment**, or a **baseline**, and therefore risk: contradictory verdicts to
the same founder, duplicate messages about one event, or one alert
suppressing/escalating another incorrectly.

This file exists because orchestration is a cross-cutting concern that spans
every series and can only be *resolved* once all four review series
(D → C → B → A) are specified. The review runs bottom-up, so the last input
(A-series) is not available until the A review. Therefore:

- **This file CAPTURES touchpoints as each series is reviewed.**
- **Resolution happens in a dedicated pass AFTER A-series.**
- Resolving a touchpoint now — before B and A are specified — would force
  re-litigation later and violates the "do not resolve prematurely"
  discipline.

Sequence (corrected 2026-05-31): D → C → B → A → **orchestration resolution
pass** → H → consolidated Claude Code prompt.
(The post-A placement is a hard dependency: orchestration needs A-series
specified. It is NOT "pre-H." H does not depend on it; the only fixed
constraint is that the consolidated Claude Code prompt comes after H.)

---

## BUILD METHOD

- **Phase 1 (this version):** canonical-spec deep pass. Sources:
  `product_strategy.md` Section 3D (full 41-type definitions),
  `agent_d_build_spec.md` (G/F/E1 locked language + D1 Gaps 1–3),
  `technical_architecture.md` (shared mart columns, causal_graph entries,
  suppression infrastructure).
- **Phase 2 (pending):** sweep every state/context file as a targeted
  gap-check against this skeleton. Append anything missing with a source
  citation. Confirms-the-skeleton findings need no entry.

Completeness of Phase 1: **Medium.** Known touchpoints captured reliably.
Latent collisions inside B-series and A-series cannot be fully surfaced until
those series are reviewed in detail — which is the structural reason the
resolution pass is post-A.

---

## STATUS LEGEND

- **RESOLVED-IN-PLACE** — decision locked; no action needed in the post-A pass
  beyond consistency verification.
- **OPEN** — touchpoint identified; resolution deferred to the relevant series
  review or the post-A pass.
- **DEFERRED-DEP** — involves a Phase-2-deferred alert that still has live
  dependencies other alerts rely on. Must not be lost.
- **EXISTING-LOCKED** — an orchestration rule already present in the canonical
  spec before this ledger existed. Captured here so it is not overlooked.

---

## CORRECTIONS LOGGED THIS SESSION

1. The four-cause ROAS diagnoser ("which of CPM inflation / creative fatigue /
   checkout errors / SKU return rate") is **A2** (Root Cause of ROAS Drop
   Already Noticed), NOT A1. A1 is True Post-Return ROAS by Channel. Earlier
   in the D1 Gap 4 deliberation it was referred to as "A1" — incorrect.
2. `product_strategy.md` Group A heading reads "A1–A6" but **A7** (Wholesale
   Order Contamination Warning) exists in the body. Doc inconsistency — flag
   for the consolidated doc pass.

---

# TOUCHPOINT CLUSTERS

---

## CLUSTER 1 — Paid-Media Cost / CPM
### Alerts: D1 (CPM driver) · B1 · B4 · B2 · B5 · A2

**Shared signal:** CPM, CTR, frequency, reach, effective CPA.
Mart columns: `meta_cpm_change_pct` (confirmed), `ga4_cvr_change_pct`
(confirmed). **CTR delta and frequency delta NOT present as mart columns**
(see Sub-Decision 2, Open Items below).

**Collision risk:** D1's "CPM inflation" component, B1 (creative fatigue:
CTR↓ + CPM↑ + frequency↑), B4 (audience saturation: frequency↑ + reach
growth↓ + CPM↑), and A2 (names CPM inflation + creative fatigue as two of its
four ROAS-drop causes) all interrogate *why paid cost rose*. Three+ alert
types diagnosing one phenomenon on different thresholds → risk of
contradictory verdicts in the same week.

**RESOLVED-IN-PLACE (Sub-Decision 1, 2026-05-31):**
- D1 is a **router, not a diagnostician** for the CPM bucket. D1 owns
  attribution of the effective-CPA rise to margin (the $ impact). It does NOT
  independently compute creative-fatigue vs audience-saturation.
- D1's account-specific branch **reads B1/B4 leading-signal trajectory**
  (data-derived: normalized vs persists), NOT click/feedback state.
- **B-series always fires standalone.** D1 references; B1/B4 diagnose.
- **Shared CPM baseline is mandatory** across B-series and D1. They may differ
  on actionability; they must NEVER differ on whether the signal exists.
- Escalation (signal fired earlier, still active, now cost $X) is gated by the
  seasonal-norm check — persistence within seasonal range does NOT escalate.
- Dip-and-rise edge case locked: continuous elevation = same instance →
  escalate; cleared-then-rose (sustained normal between readings) = new
  instance → fresh diagnosis. "Sustained normal" threshold is brand-volatility-
  derived (function of the CPM baseline SD), multiplier outcome-calibrated
  per client. No fixed day count.

**OPEN (post-A resolution pass):**
- **Canonical surface per root cause.** If B1 fires standalone Tuesday AND D1
  references it Monday, does the founder get two messages about one event?
  Decision needed: does a tactical alert ever suppress, or is D1's reference
  framed so it reads as continuity not duplication? Cannot resolve until
  B-series reviewed.
- **A2 three-way overlap.** A2 also diagnoses CPM inflation + creative fatigue
  as ROAS-drop causes. A2 is reviewed in the A-series. The D1 ↔ B1/B4 ↔ A2
  relationship is the core of this cluster and is the single most important
  reason the resolution pass is post-A.
- **B2 / B5 interactions.** B2 (spend concentration) and B5 (learning-phase
  disruption) can both *cause* a CPM/CPA move. B5 explicitly makes ROAS
  "temporarily unreliable" — D1 and A-series reading ROAS/CPA during a B5
  window need a B5-aware caveat. Capture; resolve at B-series.

---

## CLUSTER 2 — Baseline Structural Break (Agency Change)
### Alerts: ALL paid-media alerts (D1, B1, B4, B2, A1, A2, A3, A5)

**Shared concern:** A change of media agency (or in-housing, or major
restructure) resets CPM/CTR/frequency/spend-structure baselines. Every alert
calibrated on paid-media history breaks at this boundary. Comparing across it
produces false escalations the first month of a new agency relationship.

**Design (aligned 2026-05-31, NOT yet fully specified):**
- This is a **baseline structural-break alert**, NOT agency detection. We
  never assert "you changed agencies."
- Trigger: a paid-media baseline shift **beyond anything in the brand's
  history**, **sustained past the seasonal-norm gate**.
- Output: surface the cost reality (e.g. CPM running X% above prior normal
  since [date]) PLUS a question ("did something change on the media side —
  new agency, in-housed, restructure?"). Every answer branch is useful:
  - "Yes, new agency" → restart baseline cleanly (treat as structural break,
    same mechanism as the Jan-12-2026 attribution break).
  - "No" → real unexplained cost event → escalate (this is what D1 is for).
  - No answer → hold old baseline, disclose uncertainty.
- **NOT detected at onboarding** (agencies churn continuously). Detected only
  on observed unprecedented baseline shift.
- Founder-declared is primary resolution; data-derived campaign-structure
  churn (mass new ad_set/campaign IDs + simultaneous archival) may *prompt the
  question* but NEVER triggers a silent auto-reset (same false-positive
  discipline as action-trace inference, which was rejected).

**OPEN (cross-paid-media; likely resolved at B or A review):**
- Which alert "owns" the baseline-break surface, or is it a shared
  infrastructure event that re-baselines all paid-media alerts at once?
- Reuses the structural-break mechanism already built for Jan-12-2026
  attribution change — confirm one mechanism serves both.

---

## CLUSTER 3 — Conversion / Checkout (CVR outcome)
### Alerts: F2 · F1 · F5 · F4 · A2 · D1 (CVR-side funnel leg)

**Shared signal/outcome:** checkout/site CVR. F-series pinpoints *where*
(F1 device, F5 step, F4 page-load, F2 payment gateway).

**EXISTING-LOCKED rule (product_strategy.md line 519):**
> **When F2 fires, suppress F1, F5, A2, and D1.**
F2 (payment gateway failure) is treated as root cause; the others are
downstream symptoms. This is the first cross-alert suppression rule in the
canon and it directly governs D1.

**Interaction with D1 (NEW — captured this session):**
- D1's proposed funnel decomposition (CPM-side → CTR-side → CVR-side, Gap 4
  branch 1) includes a **CVR-side leg**. When a CPA rise is driven by CVR
  collapse, D1 reroutes internally to conversion drivers.
- The F2 suppression rule means: **if F2 is the cause of the CVR collapse, D1
  does not fire at all** — so D1's CVR-side leg must check F2 state first and
  defer. The CVR-side branch is moot when F2 fired.
- **OPEN:** general CVR decline NOT caused by a checkout error (e.g. gradual
  mobile CVR erosion). Is that D1's CVR-side leg, or F1/F5's territory? F2
  suppression only covers the payment-gateway case. Resolve at the
  orchestration pass (F-series already locked, so this can be drafted earlier
  if useful).

**Note:** F2 delivery bypasses the 9am business-hours hold (immediate). D1 is
weekly (Trigger A) / informational (Trigger B). The cadence mismatch means F2
suppression of D1 applies at D1 render time, reading F2 firing state in the
alert week.

---

## CLUSTER 4 — Returns Chain
### Alerts: C1 → C4 → C3 (three-stage) · C5 · C6 · C2 · C7 · D1 (return driver) · A1 · A6

**Shared signal:** `return_rate_pct`, `campaign_sku_return_rate_7d`,
`return_reason`, Loop return cohorts.

**Internal C-series structure (already designed):**
- **Three-stage return-warning chain:** C1 (Gorgias sizing-complaint velocity,
  Day 0, predicts 8–12 days early) → C4 (Loop return-initiation spike, Stage 2)
  → C3 (confirmed SKU return-rate outlier, Stage 3 = outcome confirmation, not
  a new signal).
- **C5 (return-reason contamination)** governs Agent B weighting: when Loop
  reason codes diverge from Gorgias text, Agent B weights Gorgias text over
  Loop codes. This is a cross-source arbitration rule already in spec.
- C6 (high-return new collection), C2 (influencer ROI after returns,
  two-stage Day 7 / Day 21), C7 (repeat-customer return rate).

**Collision risk with D1 and A-series:**
- D1's **return-rate driver** consumes the same return signal as the C-chain.
  Same pattern as D1 ↔ B1/B4: when C1/C3/C6 already fired on a return event,
  D1's return driver should **reference, not re-alert** — adopted: the same
  router treatment as Cluster 1 (see RESOLVED-IN-PLACE below).
- A1 (post-return ROAS) and A6 (return-adjusted revenue by cohort) consume Loop
  return data for the same cohorts.

**RESOLVED-IN-PLACE (O-6, C-series review 2026-06-09) — returns router:**
- D1 is a **router, not a diagnostician** for the return signal, mirroring
  Sub-Decision 1 (CPM). The C-chain (C1/C3/C6) **owns** the return story and
  **always fires standalone**; D1 **references** it and never raises its own
  return alarm.
- **Shared "abnormal-returns" definition (yardstick) is mandatory** across the
  C-chain and D1 — they may differ on what to do, never on whether returns are
  abnormal. (The shared yardstick itself is the next open item — C3 abnormality
  reconcile, below.) NOTE: "same yardstick," NOT "same sentence" — the two
  alerts share a *measurement*, not wording.
- **Returns-specific timing rule (not needed for CPM):** the C-chain fires
  *early* (Gorgias sizing-complaint velocity predicts ~8–12 days before returns
  land); D1's margin hit appears *weeks later*, once refunds process. So D1's
  reference reads as a **sequel, not a duplicate** — the earlier return warning
  has now landed as realised lost profit. (Exact founder-facing wording is
  deferred — see O-29.)
- **No-warning fallback:** if returns rise for a reason the C-chain does not
  track (no C-alert fired), D1 may carry the return *cost* but must **not**
  diagnose the *reason* (sizing/quality) — that stays the C-chain's job.
- **COGS boundary:** the *dollar* margin D1 attaches to a return needs the
  returned unit's cost, which is **parked behind O-28**. O-6 settles the
  ownership/reference rule only (pure returns data — order/customer/date/cohort,
  all frozen); the dollar magnitude stays parked.
- **S35-graph ratification + agent_d sync:** formal ratification into the S35
  causal graph rides the orchestration pass (as O-13 does for the CPM router).
  agent_d L2166 carries a coarse "C-chain return-driver router remains open"
  reference inside a 3-item orchestration-pass bundle (with B-series canonical
  surface + A2 overlap, both still open) — it is tightened when the orchestration
  pass ratifies the bundle, NOT patched piecemeal now.

**RESOLVED-IN-PLACE (O-30, C-series review 2026-06-09) — returns prevented-outcome:**
- The C-chain is a **prediction** (early Gorgias sizing-complaint velocity) →
  **check** (later Loop confirmation). A founder fix can stop the predicted
  spike, so "no spike" alone cannot separate a *successful* warning from a
  *false* one. The honest unit is the **cohort, not "did the founder act."**
- **Two cohorts decide it:** the *in-flight* cohort (orders already shipped when
  the warning fired — a fix cannot rescue these, so they test whether the warning
  was real) and the *next* cohort (orders placed after — they test whether a fix
  worked). Judge only once the in-flight cohort's return window has matured (reuse
  the existing Loop return-lag windows + the cohort-maturity gate; no new fixed
  clock).
- **Outcomes:** (1) in-flight does NOT come back high → the warning didn't
  convert; stay quiet, log against our own accuracy — we do NOT claim prevention
  here (can't tell it from a false alarm). (2) in-flight DOES come back high →
  warning was right, confirmed-spike alert fires as normal; then the next cohort:
  back to normal → "returns appear to have settled since the change" (continuity,
  not credit); still high → "returns still elevated — not resolved."
- **Leans on cohort OUTCOME, not action detection** — we cannot reliably see the
  founder's action (no clean product-state/price history; Loop reason codes
  unreliable), so a visible action is a corroborator, never the trigger.
- **Directional, never naked-directional, never stat-sig at this tier.** Per-SKU
  counts are too thin for significance tests; confidence comes from cross-source
  agreement + a fair (apple-to-apple) comparison, not a p-value. The fair-comparison
  yardstick, the brand-relative materiality band, the roll-up grain
  (SKU→style→category), and the readable-cohort minimum are the **shared returns
  yardstick — owned by the C3 reconcile (next), inherited here, NOT redefined.**
  When even a rolled-up cohort is unreadable, fall back to the leading complaint
  signal as an explicit "early / unconfirmed watch," and make no
  prevention/vindication claim.
- **Honesty boundary:** the cohort before/after is still observational (season,
  mix, traffic shift between cohorts) → "appears to have / coincided with," never
  "your action saved $X" (CD-16). Dollar magnitude **parked behind O-28**, as O-6.

**OPEN — resolve at C-SERIES REVIEW (next session series):**
- C-chain ↔ A1/A6 shared Loop cohort logic.
- **C3 abnormality method — reconcile to D1 (added 2026-06-03, from Gap 6 Seam 2).**
  C3 is specified two contradictory ways: its headline ("SKU return rate > 2× brand
  average, sustained 7+ days" — blended average + fixed multiplier) DIVERGES from D1's
  group-against-own-band method, while its seeded scenarios (formalwear 32% vs 22%
  "structural to sub-category"; menswear 15% vs 28% "must not misread" + thin-history
  hold; weekend +6pp "structural — must not trigger") ALIGN with D1 in intent. Two items:
  (a) retire C3's blended-average + fixed-2× headline and wire C3 to the same
  per-category baseline D1 uses (the category-baseline rule S15 is wired only to D1
  today); (b) decide the shared thin-history fallback — D1 falls back to the
  units-at-risk/exposure test (can still act), C3's seed says 90-day monitor-and-wait
  (waits). Must converge so D1 and C3 cannot disagree on the same return movement.
  (c) per O-31, the shared yardstick must define what to INSTRUMENT (log cohort
  sizes, founder actions, outcomes) so its dials — band, roll-up grain, readable-
  cohort minimum — are settable from beta evidence, not guessed; ship the skeleton
  deterministic with the dials tagged "calibrate from logged data."
- **Size-guide / photography brand-action return events — shared handling (added
  2026-06-03).** D1's return component now consults active `brand_event_calendar` rows
  of `size_guide_update` / `photography_update` and applies the row's
  `residual_threshold_pct` + decay (the event row is the single source of truth; this is
  how S17/S18 reach D1 without hand-duplication). C3 reads the same rows. Confirm at C
  review that both consume identical row semantics; the S17/S18 S-rule relabel
  (context-not-suppress, window = `return_window_days` not fixed 14/21) is logged for the
  orchestration pass (seed_decisions_gap_f_g.md NOT edited mid-design).

- **C10 / Alert 3 (Influencer ROI Truth) destination-fulfilment-cost seam (added 2026-06-08, from Gap 6 operational-cost/S20).** Scenario C10 fires Alert 3 using a *destination-adjusted fulfilment cost* ($19.40/order vs $6.50 avg) to flag an internationally-skewed influencer cohort as margin-negative. This CONTRADICTS the operational-cost lock: fulfilment cost is feed-only (no 3PL feed in beta) and zone/weight estimation is rejected as confident-wrong. Reconcile at C review: either Alert 3's destination-cost read inherits the same feed-only/directional honesty (likely), or it surfaces a defensible zone-cost basis that must then ALSO be available to D1. Cannot have Alert 3 confidently pricing fulfilment while D1 holds it unmeasurable.

**FLAGGED PROPOSAL — awaiting founder decision (added 2026-06-03, from Gap 6 COGS). NOT
LOCKED. Do not build on this until confirmed.**
- **Tighten Gap 1 "driver-only" → "component-only" for no-trustworthy-COGS brands.** Gap
  1 (LOCKED) currently gives brands without reliable cost a *driver-only* margin alert.
  The COGS review argues this is closer to corrupt than honest: a margin VERDICT implies
  a computed margin we cannot defend without trustworthy cost. Proposal: such brands get
  NO margin verdict — only the component signals that need no cost (returns / CPM /
  discounting). This challenges a locked decision, so it is recorded as a proposal only,
  pending the founder's explicit confirmation. If confirmed it amends Gap 1. **UPDATE 2026-06-08 (Gap 6 residual pass): ADOPTED as the WORKING ASSUMPTION** — the residual pass proceeds under component-only (no-trustworthy-cost brands do not enter the residual machinery); formal sign-off deferred to the D1 alert-language stage (gate D1-G9), per the no-alert-language-until-9-gaps rule. Not yet a locked amendment to Gap 1.

**COGS cross-cutting rules (added 2026-06-03, from Gap 6 COGS — apply wherever D1 cost
is consumed):**
- Cost-increase detection is **feed-only** (trustworthy Finaloop/CSV/Shopify cost);
  structurally invisible otherwise (the other four margin drivers are visible, COGS is
  the one held at a stale/assumed value, so a COGS-driven dip produces no residual).
- **Staleness-decay**: claims narrow as cost ages past the founder's own stated refresh
  rhythm (full figures → caveat → no figure); keyed to the founder's rhythm, never a
  fixed interval.
- **Revenue-weighted cost coverage**: speak confidently only for the revenue actually
  costed (reuse Gap 1 `sku_cost_coverage_by_revenue`).
- Cost-update ask is **proactive at onboarding**, never a reactive alert; new-SKU-
  missing-cost ping is the reliable nudge.
- S21 60-day window **retired → per-product sell-through**; S-rule relabel logged for the
  orchestration pass (seed_decisions_gap_f_g.md NOT edited mid-design).

---

## CLUSTER 5 — Paid-Spend Waste
### Alerts: G1 · A1 · A2 · A3

**Shared signal:** Meta/TikTok spend against specific SKUs/channels.

**Collision risk:** G1 (stockout during active spend) IS also a ROAS event —
spend burning on a zero-inventory SKU distorts that SKU's/channel's ROAS,
which is exactly what A1/A2/A3 measure. A ROAS drop that A2 would try to
diagnose may actually be a G1 stockout.

**OPEN (post-A; G1 already locked):**
- Should G1 firing gate or annotate A2's ROAS-drop diagnosis (i.e. "this ROAS
  drop is stockout-driven, see G1" rather than A2 attributing it to CPM/
  creative)? Parallel to the F2→A2 suppression already locked. Strong
  candidate for an analogous "G1 is root cause → annotate A-series" rule.
  Resolve at A-series / orchestration pass.

---

## CLUSTER 6 — Wholesale / Baseline Contamination
### Alerts: A7 · D1 · A1 · return-rate alerts · A5 (CAC)

**Shared concern:** A7 (wholesale contamination) detects wholesale orders
>20% of total Shopify orders, which contaminates blended ROAS, return rate,
AND contribution margin — the exact inputs to D1, A1, and the C/return alerts.

**Cross-reference already noted:** D1 Gap 3, SKU-mix Scenario 5 (wholesale
order distortion) states wholesale "should be tagged and excluded from BAU
baseline." A7 is the alert that detects the contamination condition.

**OPEN (post-A; A7 in A-series):**
- When A7 fires (or wholesale flag is set), should D1 / A1 / return-rate
  alerts disclose a contamination caveat or suppress margin/ROAS figures until
  wholesale is excluded from baseline? Resolve at A-series.

---

## CLUSTER 7 — Seasonality & Event Suppression (shared infrastructure)
### Alerts: D1 · D6 · B-series (Q4 CPM) · C6 · collection-launch · peak suppression

**Shared infrastructure:** `brand_event_calendar`, collection-launch
suppression, peak suppression, seasonal same-week-prior-year baseline, the
post-sale demand-pull-forward suppression gap (identified in E2 deferral).

**Touchpoints:**
- **D6 (Seasonal Baseline Diagnostic)** exists specifically to explain
  metrics by seasonal pattern and prevent false alerts during cyclical moves.
  D6 conceptually overlaps with the seasonal-norm gate used in D1 (CPM
  escalation), B-series (Q4 CPM inflation), and C6 (new-collection returns).
  Open question: is D6 the single seasonal authority other alerts consult, or
  does each alert run its own seasonal check? Resolve at orchestration pass.
- **Collection-launch echo:** D1 Layer-0 Pattern 2 (collection launch echo),
  C6 (new collection returns), and the collection-launch suppression logic
  (locked under E2, deferred) all key off the same launch events. Shared
  detection must be consistent.
- **Gap 6 dependencies** (organic-viral detection fix; SKU-mix seasonal
  suppression) are D1-internal but touch the same launch/seasonal
  infrastructure — keep visible.

**OPEN.**

---

## CLUSTER 8 — Attribution / Traffic Diagnostics
### Alerts: A4 · F3 · (Jan-12-2026 structural break)

**Shared concern:** A4 (attribution model inconsistency across Meta/TikTok/
Shopify UTMs) and F3 (external traffic / dark-social surge) both surface
attribution/traffic ambiguity; both Diagnostic-Only. The Jan-12-2026 Meta
attribution structural break (conversions structurally 15–40% lower) affects
any ROAS/attribution reading.

**OPEN (low priority; both Diagnostic-Only):** ensure A4/F3 don't both fire on
the same UTM/traffic anomaly with overlapping language. Resolve at A-series.

---

# DEFERRED-WITH-LIVE-DEPENDENCIES

## E2 — Repeat Purchase Rate Declining (DEFERRED Phase 2)
**Status: DEFERRED-DEP.**

E2 the *alert* is deferred (deferred 2026-05-23: wrong metric definition; no
post-sale suppression; six cause buckets, none diagnosable from Phase 1 data;
both narrow and weekly-summary versions tested and rejected). But E2 carries
**locked infrastructure** that live alerts depend on:
- **Discount classification architecture (LOCKED)**
- **Collection-launch detection & suppression (LOCKED)** — referenced by D1
  (Layer-0 collection-launch echo) and C6.
- **New-customer-pct mart column (LOCKED)**

**Action:** these sub-components must remain built and maintained even though
E2 does not fire. `agent_d_build_spec.md` currently shows E2 as both
"PARTIAL LOCK" (sub-sections) and "DEFERRED" (final table) — an internal
contradiction to reconcile in the consolidated doc pass: relabel as
"locked infrastructure under a Phase-2-deferred alert."

## D4 — Fulfilment Cost Anomaly (DEFERRED Phase 2)
**Status: DEFERRED-DEP.** Deferred (no 3PL billing data in beta). But D1's
fulfilment-cost driver and blind-spot-diagnostic Step 3 reference fulfilment
cost estimation. D1 uses carrier-rate *estimates* with an estimation flag;
D4's invoiced-cost path is the deferred piece. Keep the distinction explicit.

## E3 / E4 (DEFERRED Phase 2)
No current live dependencies identified in Phase 1. Re-check in Phase 2 sweep.

---

# RESOLVED-IN-PLACE SUMMARY (for post-A verification only)

| # | Touchpoint | Resolution | Locked |
|---|-----------|-----------|--------|
| 1 | D1 ↔ B1/B4 CPM diagnosis | D1 routes & reads B-series trajectory; B-series always fires; shared CPM baseline; seasonal-gated escalation; dip-and-rise rule | 2026-05-31 |
| 2 | F2 → F1/F5/A2/D1 | F2 root cause → suppress the four | EXISTING (pre-ledger) |

---

# OPEN ITEMS REGISTER (resolution owners)

| # | Touchpoint | Resolve at |
|---|-----------|-----------|
| O-1 | Canonical surface per root cause (does B1 standalone + D1 reference = 2 msgs?) | B-series review |
| O-2 | D1 ↔ B1/B4 ↔ A2 three-way CPM overlap | A-series → orchestration pass |
| O-3 | B2 / B5 ROAS-unreliability caveats for D1 & A-series | B-series review |
| O-4 | Baseline structural-break (agency) — surface ownership & mechanism reuse | B or A review |
| O-5 | General CVR decline (non-checkout-error): D1 CVR leg vs F1/F5. **ALSO (added Gap 4 2026-05-31): F2-vs-S44 precedence** — S35 suppresses all of D1 when F2 fires, but S44 component logic implies F2 should suppress only D1's conversion component, leaving CPM/return-rate free. F2 case not worked in S44 example. D1 Step 0 F2 branch cannot finalise until ratified. | orchestration pass (F locked) |
| O-6 | D1 return driver ↔ C-chain (apply router pattern) | **RESOLVED-IN-PLACE 2026-06-09** (C-chain owns + always fires standalone; D1 references, never re-alerts; shared abnormal-returns yardstick mandatory; sequel-not-duplicate timing; no-warning fallback = carry cost, not reason; dollar magnitude parked O-28; S35 ratification + agent_d L2166 tightening → orchestration pass; founder wording → O-29). |
| O-7 | C-chain ↔ A1/A6 shared Loop cohorts | C-series → A-series |
| O-8 | G1 stockout → annotate/gate A2 ROAS diagnosis | A-series |
| O-9 | A7 wholesale contamination → caveat/suppress D1/A1/return figures | A-series |
| O-10 | D6 as single seasonal authority vs per-alert seasonal checks | orchestration pass |
| O-11 | **Shared launch-detector rewrite (expanded Gap 6, 2026-06-02).** Separate `organic_viral` from `collection_launch` — different metrics (new-SKU *count* vs single-SKU *revenue*) and different recovery clocks. Fix the spec self-contradiction ("spend optional" vs "no-spend required"). C6 is *corrupted* by the conflation (it watches a viral existing SKU as a new collection); E2 is *double-suppressed* (launch logic + S33) — verified that neither C6 nor E2 relies on viral being actively suppressed. Detector is shared D1/C6/E2 and lives in causal_graph.py (batched post-H). **S33-window / D1-cadence alignment:** D1 consumes S33's surge *event*, NOT its 90-day repeat-tracking window. | orchestration pass |
| O-12 | A4 / F3 overlapping attribution-anomaly diagnostics | A-series |

---

# SUB-DECISION 2 — DATA DEPENDENCY (carried from D1 Gap 4)

Funnel decomposition (CPM-side → CTR-side → CVR-side) needs CTR, CVR, and
(only if D1 ever diagnosed fatigue itself — it does NOT, per Sub-Decision 1)
frequency deltas at D1 render time.

**Schema check result (2026-05-31):**
- `meta_cpm_change_pct` — PRESENT in mart_causal_chain_daily ✓
- `ga4_cvr_change_pct` — PRESENT (referenced) ✓
- **CTR delta (`meta_ctr_change_pct` or equiv) — NOT PRESENT** ✗
- frequency delta — NOT PRESENT (but NOT required by D1: creative-fatigue/
  saturation diagnosis routed to B1/B4 per Sub-Decision 1, which reduces D1's
  data needs)

**Decision required from founder (one line):**
- (a) Add a CTR delta mart column → enables true three-way CPM/CTR/CVR funnel
  split; logged as a mart-column debt item with the Gap 3 batch, OR
- (b) Constrain D1's funnel logic to a two-way CPM-side vs CVR-side split,
  inferring CTR-side as the residual → no new column.

Recommended close timing: after this orchestration file, per agreed sequence.

---

═══════════════════════════════════════════════════════════════════════
# PHASE 2 FINDINGS — STATE/CONTEXT SWEEP (2026-05-31)
═══════════════════════════════════════════════════════════════════════

**Headline: the canonical-spec pass missed an entire pre-existing
orchestration architecture.** It lives in the seed-decision files
(`seed_decisions_gap_f_g.md`, `seed_decisions_gap_d_e.md`,
`gap_abc_decisions.md`), not in `product_strategy.md` / `agent_d_build_spec.md`
/ `technical_architecture.md`. Running Phase 2 was the difference between an
orchestration file that would have re-invented existing locked machinery and
one that builds on it. Findings below are HIGH priority.

---

## P2-FINDING 1 — The S-Series: 50 locked suppression rules (S1–S50)
### Source: seed_decisions_gap_f_g.md lines 56–490

There is a complete, locked suppression-rule series the spec pass never saw.
This is the actual orchestration backbone. Categories:

- **Event/seasonal suppression (S1–S33, S37, S45):** CPM-spike suppression for
  sale periods (S1), collection launches (S2), elections (S5), back-to-school
  (S10); post-holiday return spikes (S3); platform disruption (S4); attribution
  breaks (S6); Klaviyo flow modification (S7); A/B tests (S22); Klaviyo sends
  (S23); app installs (S24); etc. Many map directly to the per-alert
  `suppression` notes already in Section 3D (e.g. F1/F5 cite S22/S23/S24;
  G2 cites S27/S28) — **so Section 3D was already referencing the S-series
  without defining it.** That coupling was invisible in the spec pass.
- **Delivery timing (S34):** business-hours hold 10pm–8am, deliver 9am EST.
  Critical alerts bypass: **G1, F2, E5**. (Confirms G1/F2 immediate delivery
  and adds E5.)
- **Suppression governance (S40–S50):** audit trail table (S40), confidence
  decay (S41), gaming detection (S43), predictive pre-suppression (S45),
  override (S49), retraction (S50).

**Status: EXISTING-LOCKED.** Action: the post-A orchestration pass must treat
the S-series as the substrate, not design a new suppression scheme. Every
cluster above needs cross-referencing to its governing S-rules.

---

## P2-FINDING 2 — S35: master alert-dependency graph (ALREADY EXISTS)
### Source: seed_decisions_gap_f_g.md lines 227–233

The cross-alert suppression hierarchy we thought we were designing is already
locked as **S35 — Duplicate Alert Root Cause**:

```
F2 → suppresses F1, F5, A2, D1   (F2 root; others downstream)
H1 → suppresses ALL alerts        (data unreliable)
E5 → suppresses E1, D5
H6 → suppresses A1, A3, Alert3 for affected platform
Root cause alert fires, downstream alerts suppressed WITH REFERENCES.
```

**This is the single most important Phase 2 find.** Two consequences:

1. **"Suppressed with references" IS the router-with-reference pattern** we
   derived in Sub-Decision 1 for D1↔B1/B4. Our pattern is therefore consistent
   with — and an *extension of* — existing locked architecture, not a new
   invention. **But D1↔B1/B4 is NOT in the S35 graph.** S35 has F2→D1; it does
   not encode B1/B4↔D1. So Sub-Decision 1 should be registered as a **proposed
   S35 addition** (D1 reads B1/B4 trajectory + references), to be ratified into
   S35 at the orchestration pass — keeping one canonical dependency graph
   rather than a parallel rule.
2. **H-series sits at the top of the suppression hierarchy** (H1 suppresses
   all; H6 suppresses paid-channel alerts per platform). This is why H is last
   and why the consolidated prompt is post-H: H governs whether anything fires
   at all. Confirms the sequencing rule from first principles.

**Status: EXISTING-LOCKED (graph) + OPEN (D1↔B1/B4 addition to it).**
Supersedes the way Cluster 1 / Cluster 3 framed the F2→D1 rule — it is part of
S35, not a standalone line.

---

## P2-FINDING 3 — S44 + S42: D1 component-level suppression (CORE to D-series)
### Source: seed_decisions_gap_f_g.md lines 322–397

**S44 — Cascading Suppression Failure Prevention** decomposes D1 into
components BEFORE suppression, and suppression applies **per component, not
per alert type**:

```
D1 CPM contribution         → suppressible by S1, S2, S5, S10  (seasonal CPM)
D1 return-rate contribution → suppressible by S3, S15, S16
D1 COGS contribution        → suppressible by S21
D1 discount-depth contrib.  → suppressible by S19
D1 operational-cost contrib → suppressible by S20
```

**Direct collision with our active D1 work — flag hard:**
- The **seasonal-norm gate** we designed in Sub-Decision 1 for the D1 CPM
  driver/escalation is, architecturally, the **S1/S2/S5/S10 suppression of the
  CPM component of D1, governed by S44**. We were partially re-deriving an
  existing mechanism. The Gap 4 CPM logic and Gap 6 seasonality work must be
  written as *consumers of S44 component suppression*, not as a fresh seasonal
  check. **This should be reconciled when we resume Gap 4/Gap 6, not deferred.**
- S44's worked example (BFCM + defective unit, Nov 28 2024, AZ-KNIT-031) is
  exactly the D1 partial-fire case: CPM component suppressed as seasonal, but
  return-rate component fires because a defective unit is not seasonal. This is
  the canonical test for D1 component suppression and should be referenced in
  the D1 spec.

**S42 — Suppression Stacking Rules** governs multiple simultaneous
suppressions: highest-confidence suppression is primary; **DQ suppression (S9)
always overrides** (ties to H-series precedence); State 2 + State 3 → State 3;
multiple State 2 → most conservative residual. 12 multi-suppression events
(MS1–MS12) seeded.

**Status: EXISTING-LOCKED. Reconcile with D1 Gap 4/Gap 6 IN-LINE (high
priority) — this changes how we finish D1.**

---

## P2-FINDING 4 — Alerts beyond the Section 3D canon (E5, E6, …)
### Source: seed_decisions_gap_d_e.md lines 701–725, 977–980

- **E5 — Deliverability Risk:** leading indicator (fires before deliverability
  degrades — spam complaint rate approaching Gmail threshold; action: suppress
  unengaged before next send). Real, designed, with its own architecture, S34
  critical-delivery status, S35 suppression role (suppresses E1, D5), and an
  E30 benchmark. **NOT in the Section 3D E-group (which lists only E1–E4).**
- **E6 — Klaviyo Revenue Seasonality** (monthly targets) also present.

**Namespace collision (P2-FINDING 5) makes the exact count uncertain** — do not
assume "E1–E40 alerts." But E5 at minimum is a genuine live alert absent from
the canonical library, in the S35 graph, that no current Section 3D entry
covers.

**Status: OPEN — canon reconciliation.** E5 (and E6) must either be added to
the Section 3D library or the seed files reconciled to it. Flag for the
consolidated doc pass. E5 has live suppression dependencies (suppresses E1, D5)
so it cannot be silently dropped.

---

## P2-FINDING 5 — Three colliding alert-numbering namespaces (DOC INTEGRITY)
### Source: gap_abc_decisions.md vs product_strategy.md vs seed files

There are at least three different things all labelled "A1", "A2", etc.:

1. **Section 3D 41-type library:** A1=Post-Return ROAS, A2=ROAS-drop root cause,
   … (the alert IDs we use in deliberation).
2. **gap_abc_decisions.md "Gap A/B/C decisions":** A1=BFCM Suppression
   Corrected, A2=Monthly Floor Raised, A6=Three-Stage Return Chain, … These are
   **seed-script design decisions, NOT alerts.** Same labels, unrelated meaning.
3. **seed_decisions extended numbering:** E5, E6, E30, S1–S50, plus E7–E40 /
   B6–B16 / A8–A18 strings that are a mix of scenarios, decisions, and possibly
   alerts.

**Risk:** any future instruction like "check A6" is ambiguous across three
namespaces — a real source of the "retrieval errors downstream" failure mode.
**Status: OPEN — doc integrity.** Recommend a namespace convention
(e.g. ALERT-A6 vs DEC-A6 vs S-rule) adopted in the consolidated doc pass.
Low build-risk, high sanity-risk.

---

## P2-FINDING 6 — Signal co-movement matrix (feeds D1 Layer-0 interaction check)
### Source: gap_abc_decisions.md lines 101–105 (A4), A16 correlated generator

Locked correlation structure between signals:
```
CPM spike → ROAS lag (3–5d):          −0.72
Return rate rise → Gorgias volume (2–3d): +0.81
Return rate rise → Net revenue (7–14d):   −0.68
Klaviyo open rate → Repeat purchase:      +0.43
GA4 sessions → Shopify orders (same day): +0.76
```

**Relevance:** these are the empirical co-movements that D1's Layer-0
interaction patterns (creative fatigue = CPM↑+CVR↓+returns↑) and the
multivariate sweep are detecting. The hardcoded interaction patterns should be
consistent with this matrix. Return→Gorgias +0.81 underpins the C1→C4→C3 chain
(Cluster 4). **Status: reference for Cluster 1 & Cluster 4; verify consistency
at the orchestration pass.**

---

## P2-FINDING 7 — Additional event-suppression touchpoints (lower priority)
### Source: seed_decisions_gap_d_e.md, seed_decisions_gap_f_g.md

- `influencer_gift_shipment` event suppresses **G1** (gifted units aren't
  active-spend stockouts). [gap_d_e 615]
- `klaviyo_ab_test` / `flow_modification` events suppress **D5**. [gap_d_e 628,
  632; gap_abc 299]
- Outlook/ESP error suppresses **F1, F2** for 48h. [gap_d_e 1002]
- S7 (Klaviyo flow modification) suppresses **E1** on the unsubscribe-volume
  metric only — metric-specific suppression, not whole-alert. [gap_d_e 1047]
- TikTok platform disruption (S4) suppresses **A3, B5, C3(TikTok), Alert3
  (TikTok)**. [gap_d_e 131, 163]
- S33 (new-customer surge) suppresses **E2** 90 days. [gap_f_g 210, 217]

**Status: EXISTING-LOCKED, captured for completeness.** Most are event→alert,
already encoded in `brand_event_calendar` logic. The metric-specific
suppression pattern (S7→E1 volume only) is notable — it's the same
component-level granularity as S44 and may generalise.

---

## PHASE 2 — UPDATED OPEN ITEMS (append to register)

| # | Touchpoint | Resolve at |
|---|-----------|-----------|
| O-13 | Ratify Sub-Decision 1 (D1↔B1/B4) as an addition to the S35 graph | orchestration pass |
| O-14 | Reconcile D1 seasonal-norm gate with S44 component suppression | **RESOLVED IN-LINE (Gap 4, 2026-05-31)** — D1 CPM chain rewritten as S44→S38→S41 consumer + S35 consumer (see agent_d_build_spec.md "GAP 4 — D1 CPM DIAGNOSIS CHAIN"). **Gap-6 half: PARTIAL.** CPM done (Gap 4). Return-rate two-stage consumption designed (Stage 1 S15 baseline-setter, Stage 2 residual via S3/S16→S38→S41); **Seam 2 [S17/S18 vs C3] CLOSED 2026-06-03** (size-guide/photography events routed through the `brand_event_calendar` event layer — row's `residual_threshold_pct` + decay; narrate-don't-suppress default; Tier-1 metaobject auto-detect; action anchored on return reason; "extreme" = group-own-band / exposure / trajectory; affected_category column batched); **C3 consistency check CLOSED 2026-06-03** as a finding (C3 specified two contradictory ways — provisional lock of D1's yardstick + 2 reconciliation items logged for C-series review above). **COGS/S21 component CLOSED 2026-06-03** (60-day window retired → per-product sell-through; cost-increase driver is feed-only — detectable only for brands with a trustworthy cost feed, structurally invisible otherwise; no margin VERDICT for no-trustworthy-COGS brands → component signals only [Gap 1 tightening flagged as a PROPOSAL, not locked — see below]; staleness-decay governs claims; revenue-weighted cost coverage; state-driven disclosure not per-alert footnote; landed-cost/duties gap + dedicated COGS connector deferred discovery-gated). **discount-depth/S19 component PARTIAL 2026-06-04** (no standalone discount alert — founder sets depth; discount is a margin CONTRIBUTOR, dollar figure feed-only / directional depth-terms otherwise; effective-discount source decomposition [code/automatic/shipping, data-derived] rides a real D1 trigger, never a discount threshold, no founder code-tagging; planned sales suppressed via the shared known-events layer not a discount-specific window [retires week-1-2/weeks-3-4/>5pp/0.20-default]; unconfirmed/panic markdowns narrated-not-suppressed [adopts O-23 for this component]; new-vs-existing return split + thin-baseline confidence DEFERRED to O-24; orphaned margin_floor_pct flagged → O-25). operational-cost/S20 CLOSED 2026-06-08 (feed-only, no change-verdict, seed S20 retired); residual pass IN PROGRESS 2026-06-08 (measured-not-explained rule; all-explained two-door fire; universal go-quiet ceiling; fulfilment estimated driver retired; structural-break magnitude brand-relative; BAU pre-sale-ramp exclusion + onboarding backfill; pre-sale-ramp handling held in state file); STILL OPEN: new-vs-returning split + thin-baseline confidence (O-24 a/b) → Gap 6 remains WIP. Closes when Gap 6 closes. |
| O-15 | E5/E6 (and any other non-canon alerts) → add to Section 3D or reconcile | consolidated doc pass |
| O-16 | Three-namespace collision → adopt naming convention | consolidated doc pass |
| O-17 | Verify Layer-0 interaction patterns vs A4 co-movement matrix | orchestration pass |
| O-18 | S42 stacking precedence vs Sub-Decision-1 escalation (does a stacked seasonal suppression outrank a D1 escalation?). **PROPOSED RESOLUTION (Gap 4 2026-05-31): yes — D1 escalation is subordinate to the stack; it fires only when the stacked state decays to ≤ State 2 via S41. Ratify the general stacking question at the pass. EXTENDED 2026-06-08 (Gap 6 residual pass): the universal go-quiet ceiling now caps every component's suppression state by admissible-season count, so S42 stacking precedence must key on this ceiling — the explained-score % can no longer cause silence on its own.** | orchestration pass |
| O-19 | **D1 Gap 8 inheritance (added Gap 5, 2026-06-01; extended Gap 6, 2026-06-02)** — founder-driven category (ASP) shift under "explained ≠ can't act". Items: (A) **suppression hole** — mix-shift pre-conditions check promotion-driven shifts but NOT paid-spend-reallocation-driven ones, and the SKU-level spend-misallocation sub-finding would false-fire on an intentional push; (B) **founder-vs-organic discriminator** — spend-by-category co-moving with revenue-by-category is the separating signal; (C) **materiality floor** below which the intentional-shift trade is not surfaced; (D) **viral concurrent-discount surface (Gap 6)** — the organic-viral discount-depth read needs this same materiality floor PLUS an **actionability gate**: is a lever still available? (Harder than magnitude; may degrade to "surface the lever, founder judges.") (E) **weekly digest of suppressed (expected) leaks (Gap 6)** — show magnitude + reason, never the internal mechanics, gated by suppression confidence; belongs here and in Gap 9 ($-impact display). | D1 Gap 8 (+ Gap 9 for digest) |
| O-20 | **3PL double-count trap (added Gap 5, 2026-06-01)** — shipping/free-ship economics deferred to the 3PL integration as a cost-side carrier-cost-change detector. When real carrier cost lands, the `shipping_lines.discount_allocations` revenue-side proxy is DROPPED, NOT summed with carrier cost — same free-ship event measured from opposite sides of the margin identity. NOT an AOV driver, NOT a revenue-side fold into operational-cost. | 3PL integration |
| O-21 | **S15 relabel (added Gap 6, 2026-06-02)** — in how D1 consumes it, S15 is a return-rate **baseline-setter** (a *level*), not a suppression state-producer (a *delta*). This diverges from S44's literal listing of S15 in the return bucket. Resolved on the D1 side now; the S-series-semantics relabel is logged here. NOTE: the S-rule definition itself is NOT edited this session (seed_decisions_gap_f_g.md untouched). | orchestration pass |
| O-22 | **S33 20%-cutoff → brand-relative (added Gap 6, 2026-06-02)** — S33's hardcoded 20% viral-cohort repeat-rate cutoff must become brand-relative (below the brand's own new-customer-cohort repeat-rate band). Logged for the S-series semantics pass; S-rule definition not edited this session. | orchestration pass |
| O-23 | **brand_event_calendar confound guard (added Gap 6, 2026-06-02)** — Approach-B auto-population (qualify high-order-volume days, classify by the brand's own discount-depth p50/p75, cluster consecutive days) will mislabel an unplanned competitor-reaction markdown or a viral-driven discount as a planned `sale_period` and let it earn suppression. Require corroboration / founder-confirm before treating a detected window as a *planned* seasonal event; uncorroborated → narrate-don't-suppress. | orchestration pass |
| O-24 | **Final cross-component residual-disclosure consistency pass (added Gap 6, 2026-06-02; extended 2026-06-04).** **CLOSEOUT 2026-06-08 (cogs_parked session):** (a) **new-vs-returning customer split — RETIRED.** Stage 2 (S17/S18 vs C3) already owns suppression/narration of the return-rate component after a known sale; the split produces no actionable lever (founder cannot un-return), and the prior-sale comparator is too context-sensitive at this brand tier (each sale differs on pricing depth, quality cohort, delivery delay, competitive context, design novelty). New-vs-returning composition, if ever surfaced, belongs in a periodic digest → Horizon-2 (alongside the sale-period informational channel). NOT a suppression gate, NOT an alert. (b) **thin-baseline confidence — REFRAMED + BLOCKED ON COGS FOUNDATION (O-28).** No longer a clean-day count question; it is a cost-regime/versioned-COGS question. The honest resolution ("component-only mode until the cost-regime-consistent window supports a margin verdict") is *defined by* the COGS foundation, so O-24b cannot close until O-28 is worked. **LOCKED earlier this pass (unchanged):** (i) measured-not-explained rule; (ii) all-explained two-door fire; (iii) universal go-quiet ceiling; (iv) fulfilment estimated driver retired (4 sites agent_d + tech-arch); (v) structural-break magnitude brand-relative; (vi) BAU pre-sale-ramp exclusion + onboarding two-pass backfill; (vii) pre-sale-ramp handling design (held in state file). **STILL BLOCKED (on O-28 COGS foundation):** O-24b thin-baseline confidence; the all-explained edge-case actionability gate; whether residual-band cutoffs are brand-relative — all three operate on the margin residual and cannot settle without the COGS decision. **Test-data-constant verification CLOSED — verified clean this session** (no live test constants wired into suppression paths; only matches were the retired-S20 mechanic description and the O-26 audit log). **→ Gap 6 does NOT close; it is parked behind O-28. Build moves to C-series.** | Gap 6 closeout — BLOCKED on O-28 |
| O-25 | **Orphaned `margin_floor_pct` cleanup (added 2026-06-04)** — `client_config.margin_floor_pct` (default 5%, "calibrate to ~28%" note) is NOT wired into the locked D1 Trigger A/B firing logic (which is fully brand-relative); it is a relic of the pre-Gap-2 absolute-floor design. Remove or consciously re-scope. Same latent-inconsistency class as the category parallel-copy cascade. | post-Gap-6 consistency audit (O-26) |
| O-26 | **Full design-consistency audit + design-ownership map (added 2026-06-04; logged, NOT folded into the save protocol)** — one-time sweep of EVERY locked decision across all canonical files (not just retired phrases), and build a map of which file is authoritative for each decision and which files carry mirror copies. Motivated by the 06-02 category cascade (4th/5th stale parallel copies; two source-of-truth files disagreeing) and reinforced by today's orphaned-floor find. The map becomes the input that makes save-protocol check 8 (cross-file consistency) mechanical rather than best-effort. **Runs AFTER Gap 6 closes** (do not pull forward). **ADDED 2026-06-08 (Gap 6 residual pass) — the audit must also cover: the launch-detector "≥5 new product_ids in 7 days" hardcoded count (make brand-relative); the structural-break ≥21-day persistence duration (review whether it should be brand-relative like the magnitude now is); the S38 explained-away 85%/60% placeholder cut-offs (now capped by the admissibility ceiling so they cannot cause silence alone, but still want outcome calibration).** **ADDED 2026-06-09 (mirror-sync find) — the design-ownership map must enumerate STATUS-mirror homes, not just decision homes.** The 2026-06-08 cogs_parked Phase-0 Check-8 mirror list recorded Gap-6 status as living in agent_d + cross_alert only; it also lived (stale) in pre_agent_build_checklist D-16 + header AND d1_validation_gates header + the D1-G12 "NOT gated here" note. Both were corrected by the 2026-06-09 mirror-sync save; the O-14 stale tail (this file) is still carried. Lesson: a hand-built mirror list misses status mirrors — the map must list which files carry a status copy of each decision. | after Gap 6 closes |
| O-27 | **Evidence-stack action-layer posture (added 2026-06-04)** — for text-derived / qualitative signals (Gorgias parser output, etc.), Layer 4 is "summarise faithfully + link to source," NOT a recommended action: the action depends on context we don't hold (margin, inventory, positioning) and can't verify after the fact. Decided **case-by-case per signal** against a consistent two-part test — can we ground the action in data we hold, AND can we verify whether acting worked? Both yes → an action layer is honest; either no → summarise and leave judgment to the founder. Log each signal's landing + why. NOT generalised by fiat. | per-signal, revisited at each alert's review |
| O-28 | **COGS FOUNDATION — own section, PARKED, DISCOVERY-BLOCKED (added 2026-06-08, cogs_parked session).** Elevated above Gap 6 / D1: this is a foundational data-model question feeding EVERY margin-bearing alert (D1/D2/D3…), not a D1 detail. A profit-monitoring product must compute historical profit; whether it can depends on cost data the Shopify API does not supply. **VERIFIED THIS SESSION (Shopify data-layer facts, evidence-backed):** (1) historical order *line items* freeze SKU string + title + price + quantity at sale time and SURVIVE product/variant deletion; (2) the *link* to the live product/variant object (and the cost field behind it) is LOST on deletion — `cost per item` is current-only and not in the Order API, deleted-variant cost is unrecoverable; (3) therefore cross-source baselines (marketing/ROAS, returns, Klaviyo) join on order/customer/date/channel — all frozen — and DO NOT fall flat on deleted SKUs; only per-SKU **cost/margin** degrades, and Shopify cost was never our source anyway. **PROVISIONAL DIRECTION (NOT locked, NOT to be authored into technical_architecture.md until worked):** versioned/season-regime cost model (`sku_cost_version`: sku_string, cost, regime_label/start/end, source_tier) joined on **SKU string** (survives deletion), not variant ID; season/regime granularity accepted (founders think Spring/Fall, not exact dates — coarser than reality already); mandatory **coverage disclosure** (% of historical revenue cost-covered); uncostable orders run **component-only**, never imputed; **multiple-file ingestion** (per season / per category) + a normalisation step for heterogeneous founder formats; prompt-the-founder fallback for high-revenue unmatched SKUs (industry-standard, cf. BeProfit). **THE HARD UNKNOWN (discovery-gated):** what fraction of ICP founders can actually supply usable historical versioned cost — NOT answerable by analysis or search; needs founder conversations. De-risk idea: instrument onboarding to MEASURE the reconstruction rate on the first real brands. **BLOCKS:** O-24b, the all-explained actionability gate, residual-band-cutoff brand-relativity, and Gap 6 lock. **Detailed messy-ingestion-tolerance spec deferred to its own dedicated session.** | dedicated COGS session, after discovery (or after revenue-side work, on a stated assumption with eyes open) |
| O-29 | **Returns-reference founder-facing wording (deferred from O-6, 2026-06-09).** Exactly how D1's "sequel" reference to an earlier C-chain return warning should READ to a founder so it lands as continuity, not noise — and whether it may name a dollar figure (depends on O-28). NOT a design question; it is alert-language, written only after all design gaps close, by standing rule. **Collaborative — written WITH Anupam, not drafted solo.** Validation is a real-founder/beta question, not analysis. | alert-language stage (after all gaps close) — collaborative |
| O-30 | **Returns predict-then-check / prevented-outcome — RESOLVED-IN-PLACE 2026-06-09.** Handled by cohort-based predict-then-check: the in-flight cohort (orders shipped pre-warning) tests whether the warning was real; the next cohort tests whether a fix worked; judged only when both cohorts are readable (existing Loop return-lag windows + cohort-maturity gate, no new clock). Outcomes: in-flight flat → quiet miss, no prevention claim; in-flight high → confirmed spike fires, then next cohort settles ("appears to have settled since the change") or stays high ("not resolved"). Leans on cohort OUTCOME, not action detection (action = corroborator only — no clean action history, Loop reason codes unreliable). Directional, never naked-directional, never stat-sig at this tier (confidence = cross-source agreement + fair comparison). Fair-comparison yardstick + materiality band + roll-up grain (SKU→style→category) + readable-cohort minimum = shared returns yardstick, owned by C3 reconcile (inherited, not redefined); unreadable cohort → leading-signal "early/unconfirmed watch," no spike claim. Honesty "appears to have," never "$X saved" (CD-16); dollar parked O-28. | RESOLVED-IN-PLACE 2026-06-09 |
| O-31 | **Dial calibration & system-freeze discipline — GENERAL, all dial-bearing alerts (added 2026-06-09, C-series review).** The live system stays DETERMINISTIC and FROZEN during beta — causal chains, alert logic, and comparison rules do NOT self-tune in production (self-adapting behaviour breaks the deterministic-trust moat and is undebuggable on live client data). Only the **dials** (readable-cohort minimums, materiality-band multipliers, roll-up aggressiveness, etc.) are calibrated, and they are set by a DELIBERATE evidence step: instrument first (log each fired alert + its cohort sizes + whether the founder acted + the actual outcome), then set dials from logged evidence against pre-agreed criteria — never in ad-hoc conversation, never continuously. **Evidence-Stack link:** Layers 2 (verifiable numbers) and 3 (own-history precedent) CONSUME these dials; the Stack presents but cannot vouch for them, so its numbers are trustworthy only once the dials are calibrated-and-frozen per this rule. Self-proposing dials with one-click human approval are legitimate but **post-beta only**. Per-alert dial + instrumentation lists are filled in as each series is reviewed, pointing back here (not restated). | permanent home: principles doc (product_strategy / technical_architecture), authored at the pre-beta instrumentation stage; ledger is interim home |

## PHASE 2 — REVISED RESOLVED-IN-PLACE NOTE
The F2→D1 rule (previously listed as resolved row 2) is **part of S35**, not a
standalone rule. Re-cite as S35. Sub-Decision 1 is consistent with S35's
"suppress with references" model but is a *proposed addition* to S35, not yet
in the graph — moved to O-13.

## PHASE 2 — COMPLETENESS REASSESSMENT
Phase 1 alone would have been **materially incomplete** — it missed S1–S50,
S35, S42, S44, and E5. With Phase 2, completeness on *existing* orchestration
architecture is now **High**. Completeness on *latent* B/A-series collisions
remains **Medium** (structural — needs the B and A reviews). The two-phase
method worked exactly as intended: Phase 1 built the skeleton, Phase 2 found
the load-bearing walls the skeleton didn't know existed.

═══════════════════════════════════════════════════════════════════════

# CHANGELOG

- **2026-05-31 (Phase 1)** — File created. Canonical-spec deep pass. 8 clusters,
  3 deferred-dep alerts, 2 resolved-in-place, 12 open items. Sub-Decision 2
  schema check recorded. Corrections logged (A2 vs A1; A7 heading).
- **2026-05-31 (Phase 2)** — State/context sweep. 7 findings added. Discovered
  the S1–S50 suppression series, S35 master dependency graph, S42 stacking,
  S44 D1 component-level suppression, E5/E6 non-canon alerts, three-namespace
  collision, A4 co-movement matrix. Open items extended to O-18. Two findings
  flagged for IN-LINE resolution during D1 Gap 4/6 (O-14) rather than deferral.
- **2026-05-31 (Gap 4 close)** — O-14 RESOLVED IN-LINE for Gap 4: D1 CPM chain
  rewritten as a consumer of S44→S38→S41 (seasonal) and S35 (handoff), not fresh
  mechanisms. O-5 extended with the F2-vs-S44 precedence conflict. O-18 given a
  proposed resolution (escalation subordinate to the stack). O-13 and O-17
  unchanged, carried to the orchestration pass. Gap 6 half of O-14 still open.
- **2026-06-01 (Gap 5 close)** — D1 Gap 5 LOCKED. Standalone AOV driver retired
  (margin-relevant slices already in discount-depth + mix-shift; confirmed no AOV
  component in S44, no S-rule touches AOV). Two new open items added: O-19 (Gap 8
  inheritance — Findings A/B + materiality floor for founder-driven category
  shift) and O-20 (3PL double-count trap — shipping subsidy deferred to 3PL as a
  cost-side detector; revenue-side proxy dropped not summed when carrier cost
  lands). No S-graph change, no schema change originates from Gap 5. Gap 6 (incl.
  the Gap-6 half of O-14) is next.
- **2026-06-02 (Gap 6 WIP — spec-update pass)** — Mechanical propagation of the
  D1 Gap 6 WIP decisions (2 dependencies CLOSED, return-rate PARTIAL). O-11
  expanded (shared launch-detector rewrite: organic_viral vs collection_launch,
  spec self-contradiction, C6 corruption, E2 double-suppression, detector shared
  D1/C6/E2 + batched, S33-event-not-window alignment). O-14 Gap-6 half marked
  PARTIAL (CPM done; return-rate partial with Seam 2 + C3 check open;
  COGS/discount-depth/operational-cost untouched). O-19 extended with (D) viral
  concurrent-discount surface (materiality floor + actionability gate) and (E)
  weekly digest of suppressed leaks (→ Gap 9). Four open items added: O-21 (S15
  baseline-setter relabel), O-22 (S33 20%-cutoff → brand-relative), O-23
  (brand_event_calendar confound guard), O-24 (final cross-component
  residual-disclosure consistency pass — Gap 6 closeout). No S-rule definition
  edited (seed_decisions_gap_f_g.md untouched — reclassifications logged here for
  the orchestration pass). No schema or S-graph change originates here.
- **2026-06-04 (Gap 6 WIP — discount-depth/S19 PARTIAL close)** — O-14 Gap-6 half
  updated: discount-depth/S19 component PARTIAL (no standalone discount alert; discount
  is a margin contributor, dollar figure feed-only / directional depth-terms otherwise;
  effective-discount source decomposition rides a real D1 trigger; planned sales via the
  shared known-events layer not a discount-specific window; panic markdowns
  narrated-not-suppressed [adopts O-23 for this component]). Two items DEFERRED to O-24
  (new-vs-existing return split; thin-baseline confidence). Three open items added: O-25
  (orphaned margin_floor_pct cleanup), O-26 (full design-consistency audit + ownership
  map — logged NOT folded into the save protocol; runs after Gap 6 closes), O-27
  (evidence-stack action-layer posture: summarise-and-link for text signals, decided
  case-by-case per signal against the groundable+verifiable test, not generalised). A
  separate sale-period informational channel + the Gorgias NLP parser were specced as
  PARALLEL items (see technical_architecture.md / pre_agent_build_checklist.md), not
  Gap 6. No S-rule definition edited (seed_decisions_gap_f_g.md untouched). No schema or
  S-graph change originates here; build items batched post-H.
- **2026-06-08 (Gap 6 residual pass — Tier-1 locks saved)** — operational-cost/S20 CLOSED
  (feed-only, no change-verdict; founder-stated figure static-baseline only; no zone estimation;
  uniform 3PL build Horizon-2; known transitions via shared known-events layer; seed S20 mechanic
  retired; regional stockout is a zone-cost drag, not a suppression). Residual pass IN PROGRESS:
  LOCKED — measured-not-explained rule; all-explained two-door fire; universal go-quiet ceiling
  (admissibility ceiling caps ALL components, explained-score → context only); fulfilment estimated
  driver retired (4 sites in agent_d + tech-arch CM/blind-spot/connector notes); structural-break
  MAGNITUDE made brand-relative (duration flagged to O-26); BAU baseline now excludes pre-sale ramp
  windows + a one-time onboarding two-pass backfill. Tier-2 (HELD IN FULL in the session state file,
  folded into specs when Gap 6 closes): pre-sale-ramp detector (4-signal, thresholds learned from
  the brand's own past ramps, admissibility-ladder-gated, two jobs — BAU exclusion + D1
  narrate-with-context) and new-product cost-collection mechanism (burst-gate drip+departure;
  wave-crest debounce; materiality = burst itself; list-price-ranked fill prompt; partial-but-scoped
  live alert; publication trigger timed by demand build-up; crawling rejected; scheduled-discount
  ingestion noted as future option). Routed: C10/Alert-3 destination-fulfilment-cost seam → C-series;
  S42 stacking-on-ceiling → O-18/orchestration pass; launch-detector 5/7 + structural-break 21-day
  duration + explained-score placeholders → O-26; building-vs-burning pre-sale advisory → Horizon-2
  park (off critical path, not data-blocked). Gap-1 component-only ADOPTED as working assumption
  (formal sign-off at alert-language, gate D1-G9). save_protocol.md upgraded to 11 checks (Phase 0
  decision capture + Check 10 semantic read-back + Check 11 decision/routing landing). **Gap 6
  remains WIP** — new-vs-returning return split + thin-baseline confidence (O-24 a/b) still open. No
  S-rule definition edited (seed_decisions_gap_f_g.md untouched); no schema/S-graph change originates
  here; build items batched post-H.
- **2026-06-08 (Gap 6 closeout → COGS PARKED, build pivots to C-series)** — O-24a new-vs-returning
  return split RETIRED (Stage 2 already owns return-rate suppression; no actionable lever; prior-sale
  comparator too context-sensitive; new-vs-returning composition → Horizon-2 digest if ever). "Recently
  -connected brand = thin history" reasoning RETIRED (full Shopify history available on connection).
  Test-data-constant verification CLOSED — verified clean (grep/view: only the retired-S20 description
  + the O-26 audit log; no live test constants in suppression paths). O-24b thin-baseline confidence
  REFRAMED (day-count → cost-regime/versioned-COGS) + BLOCKED on the new COGS foundation; the
  all-explained edge-case actionability gate + residual-band-cutoff brand-relativity likewise BLOCKED
  (all three operate on the margin residual). **COGS elevated to its own foundational section = O-28,
  PARKED + DISCOVERY-BLOCKED** — it feeds every margin alert, not just D1. Verified Shopify facts:
  historical order lines freeze SKU/title/price/qty and survive product deletion; only the product-object
  link + cost field are lost on deletion; cross-source baselines (marketing/returns/Klaviyo) join on
  order/customer/date/channel and DO NOT fall flat on deleted SKUs — only per-SKU cost/margin degrades,
  and Shopify cost was never our source. Provisional COGS direction (NOT locked, NOT authored into
  tech-arch): SKU-string-join versioned/season-regime cost, coverage disclosure, component-only for
  uncostable orders, multiple-file ingestion + normalisation, prompt-the-founder fallback. Hard unknown
  (discovery-gated): the founder version-reconstruction rate — only customer discovery closes it; de-risk
  by instrumenting onboarding to measure it on first real brands. **Gap 6 does NOT lock — parked behind
  O-28.** Build sequence pivots: **D-series PARKED → C-series NEXT** (revenue-side, COGS-independent;
  also higher in Blueprint priority). No spec design authored this session — status/routing only;
  technical_architecture.md / product_strategy.md / pre_agent / d1_validation_gates deliberately
  untouched (COGS is parked-open, not designed). No S-rule definition edited. **This save was
  self-verified WITHOUT founder content review** — the persisted Phase-0 ledger (in the context file)
  is the audit trail for the next session to re-check.
