# Profit Sentinel — CHAT CONTEXT (reasoning log)
## Session: D1 Gap 6 — operational-cost/S20 + cross-component residual pass + pre-sale handling
## Date: 2026-06-08

---

## HOW THE SESSION RAN
Resumed Gap 6 at operational-cost/S20 (per the 06-04 next-step), then ran the cross-component
residual-disclosure pass, then surfaced and closed pre-sale baseline pollution. Worked each
through three-pass critique with hard founder pushback. Seven Tier-1 calls locked and saved into
the specs; two new-mechanism designs (pre-sale detector, new-product cost collection) were fully
designed but HELD in the state file as Tier-2 to avoid a second pass over the specs before Gap 6
closes. Gap 6 stays WIP — the two O-24 items remain the only real work left.

---

## OPERATIONAL-COST / S20 — HOW EACH CALL WAS REACHED
- **Why feed-only, no verdict:** the heart of operational cost is carrier/3PL fulfilment, which
  lives on the 3PL invoice — not connected in beta. Shopify exposes the shipping CHARGE the
  customer paid (often $0 under free-ship), never the brand's cost. So there is nothing to detect
  a CHANGE against. Same structure as the COGS no-feed case: if we cannot see the cost move, we do
  not claim it moved.
- **Why the founder-stated figure can't signal:** a single static `client_config` number (weight
  0.05) is a baseline input; by definition it does not move, so it can never produce a residual
  that says "operational cost compressed." Treating it as a detector would be theatre.
- **Why no weight×zone estimation:** the founder pushed on whether we could estimate shipping cost
  from parcel weight × zone. Rejected — that is the SAME confident-wrong error we already rejected
  for approximate auto-COGS. An estimate dressed as a measurement is more dangerous than honest
  silence.
- **Why the seed S20 mechanic was retired:** the seed had a hardcoded Month-15 / $3,950 /
  full-suppression rule for a 3PL transition. That is three hardcoded constants (a month, a dollar
  figure, a state). Replaced by the shared known-events layer — a 3PL switch is a founder-known
  structural event, routed through `brand_event_calendar` and narrated as a one-time cost.
- **Why regional stockout is a drag not a suppression:** a single empty warehouse node reroutes
  (higher zone, slower) — it does not block fulfilment, so it should not suppress anything.
  Brand-wide spend-on-an-out-of-stock-SKU is already G1's job; any regional effect is a
  shipping-cost/zone drag inside this same invisible component.
- **The C10 seam (logged, not solved):** C10 / Alert 3 (Influencer ROI Truth) confidently prices
  fulfilment per destination ($19.40 vs $6.50 avg) to call an internationally-skewed cohort
  margin-negative. That directly contradicts "fulfilment is unmeasurable in beta." Can't have one
  alert pricing fulfilment while D1 holds it feed-only → routed to C-series to reconcile.

---

## FULFILMENT RETIREMENT — HOW IT WAS REACHED
- Once operational cost was locked feed-only, the existing ESTIMATED fulfilment driver in D1
  became indefensible: it estimated cost-per-order from carrier rates and applied a hardcoded
  `× 1.15` in the blind spot. The estimate is the auto-COGS error again; the `× 1.15` is a seed
  constant.
- **The "no residual" argument:** a feed-only cost does not move COMPUTED margin, so it cannot
  create the residual the blind spot is trying to diagnose. There is nothing to detect, so we do
  not claim it — identical to the COGS principle.
- **Blind-spot Step 3 revised, not deleted:** it now mirrors Step 1 — for a trustworthy-margin
  brand, name fulfilment as a DIRECTION to check (never a figure); for everyone else, no claim.
- **The 4th site:** the retired-wording scan during the save caught a "Disclosure Type 2 —
  Estimation flag" that still told the system to append the carrier-rate caveat. That made
  fulfilment FOUR sites in agent_d, not the three first scoped. Owned and corrected; the stamps
  now say four. tech-arch had two more leaks (weekly_cm cost list; connector_gap_map) — also fixed.

---

## THE RESIDUAL RULES — HOW EACH WAS REACHED
- **Measured-not-explained:** the risk was that suppressing an explained driver would drop it from
  `total_measured_impact`, leaving a large unexplained residual → a FALSE blind-spot on a gap we
  actually understood. Fix: "measured" and "explained" are orthogonal. A driver is in the sum iff
  MEASURED; suppression only removes it from the actionable ranking. Only feed-only invisibility
  removes it from the sum (and that is exactly when it SHOULD be residual).
- **All-explained two-door:** a low residual alone is not enough to fire. If every measured driver
  is suppressed (benign-explained), the residual is near-zero but there is nothing to ACT on.
  Firing then would be a confident alert with no lever. So firing needs explainability AND at least
  one live driver; otherwise narrate / route to the suppressed-leak digest.
- **Universal go-quiet ceiling:** the inconsistency was that only mix-shift had an
  admissible-season ceiling on suppression, while CPM (via the S38 explained-away %) and
  return-rate Stage 2 could go silent on a guessed cut-off. Suppression is the HIGHEST-confidence
  claim (we are saying "this is normal, stay quiet"), so it must require comparable brand history.
  The ceiling now caps every component; the 85%/60% cut-offs become context, never the silence
  switch. This pushes the stacking-precedence question onto S42 → O-18.

---

## STRUCTURAL-BREAK SIZE — HOW IT WAS REACHED
- The flat 5pp was the problem: for a volatile brand it is noise (false breaks that discard usable
  history); for a steady brand it is too deaf (real pivots missed). Made brand-relative — a floored
  multiple of the brand's own weekly-CM volatility, the same pattern Trigger B already uses.
- **Why the 21-day DURATION stayed flat:** duration is about confirming PERMANENCE, which should be
  slow, and it is measured on BAU days so event length is irrelevant. Left unchanged but flagged to
  O-26 in case the audit wants it brand-relative too.

---

## PRE-SALE BASELINE POLLUTION — HOW IT WAS REACHED (the live find)
- Surfaced while tracing what feeds the BAU baseline: a pre-sale awareness ramp (spend up, traffic
  up, conversion soft, no discount yet) is caught by NONE of the existing exclusions. Left in BAU,
  it drags the margin band down — and because the baseline is read by Trigger A, Trigger B, the
  structural-break comparison AND the seasonal bands, a polluted baseline lowers the firing bar
  EVERYWHERE at once. This is upstream of almost everything, so it is Phase-1, not deferred.
- **Why the detector thresholds are LEARNED, not k×volatility:** the founder (and the no-hardcoding
  rule) rejected a k×volatility multiplier as a disguised constant. Reading the brand's ACTUAL past
  ramps makes no distributional assumption — it just asks "does this resemble this brand's own prior
  ramps?" Gated by the same admissibility ladder, so a brand with too little ramp history is
  disclosed, not silently trusted.
- **Why sales are data-inferred, not founder-declared:** we already refused to ask the founder for a
  sale plan (S19). A sale = volume > median AND discount depth crosses p50; the ramp is detected
  BEFORE the sale via the demand build-up. Website crawling for sale dates was rejected as brittle.
- **Why the advisory is narrate-with-context, never "cut spend":** a ramp is usually deliberate
  spend ahead of a planned sale — telling the founder to cut it would be wrong. Default is a
  no-action context note; "investigate, not cut" only when extreme.
- **New-product cost collection (the companion problem):** a pre-sale drop publishes many new SKUs
  with no cost and ~0 revenue. Realized revenue is the wrong materiality yardstick pre-sale, so
  materiality = the publication BURST itself, items ranked by LIST PRICE in a money-ranked fill
  prompt; a wave-crest debounce turns a staggered 500-SKU drop into one prompt. The 85% cost-coverage
  gate was NOT lowered — new-collection products systematically lack cost, so a partial past season
  is a biased yardstick.
- **What was ruled UNBUILDABLE in Phase 1:** a real-time safety net for a margin/discount bug during
  a brand-new sale. The separating variable is INTENT (deliberate deep sale vs a pricing bug), which
  we don't capture; only a narrow "selling below known cost" check survives, and that is feed-gated.
  Recorded so it isn't re-opened.

---

## GAP 1 COMPONENT-ONLY — WHY ADOPTED (not just left flagged)
The residual machinery assumes a computed margin. A no-trustworthy-cost brand has no defensible
margin, so it should never have entered that machinery in the first place. Rather than keep the
proposal floating and contradicting the residual pass, it was ADOPTED as the working assumption for
this pass (such brands get component signals only). It still amends a LOCKED decision, so formal
sign-off waits for the alert-language stage; enforcement already exists as gate D1-G9.

---

## THE SAVE — HOW IT WAS RUN
- Scope split: **Tier-1** (firm retirements / rule changes that would leave wrong text live) went
  into the specs now; **Tier-2** (new-mechanism designs) was HELD in full in the state file, to
  avoid touching the same specs twice before Gap 6 closes.
- Method: edits applied programmatically (Python string-replacement) on COPIES, each asserting the
  target text matched EXACTLY ONCE before replacing (halts on miss/double), then scoped-diffed
  against pristine originals. No file hand-retyped.
- The 11-check protocol earned its upgrade immediately: Check 4 (retired-wording scan) caught the
  4th fulfilment site; Check 10 (semantic read-back) caught a "3 sites" stamp that was actually 4;
  the scoped diff confirmed every changed hunk mapped to an intended edit with no collateral.

---

## CARRY-FORWARD DISCIPLINE (unchanged)
Three-pass critique before any proposal; founder test on every proposal; pushback not softened;
verify against source before proposing; no hardcoding (brand-relative or narrate); no alert language
until all 9 D1 gaps resolved; engineering specifics → consolidated Claude Code prompt after H-series;
all code batched, no code in design chats; design vs build chats separate; gloss every coded
reference in plain language; end design/critique with a completeness confidence.
