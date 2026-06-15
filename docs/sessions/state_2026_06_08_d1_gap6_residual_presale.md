# Profit Sentinel — STATE
## Session: D1 Gap 6 — operational-cost/S20 + cross-component residual pass + pre-sale handling (Tier-1 LOCKS)
## Date: 2026-06-08

---

## STATUS IN ONE LINE
Gap 6 is **still WIP**. operational-cost/S20 CLOSED and the cross-component residual pass is
substantially done (seven Tier-1 calls LOCKED below), but Gap 6 cannot close until the **two
O-24 items** (new-vs-returning return split + thin-baseline confidence) land. Those are the
only real design work left in Gap 6.

---

## WHAT CLOSED / LOCKED THIS SESSION (Tier-1 — landed in the specs now)

1. **operational-cost / S20 — LOCKED (feed-only, no estimation).** Operational cost is D1's
   5th margin-decomposition component, but it is FEED-ONLY: carrier/3PL fulfilment cost lives
   on the 3PL invoice (not connected in beta), and Shopify shows only the customer-facing
   shipping CHARGE, never the brand's cost. No operational-cost change-verdict without a real
   cost-side feed. The founder-stated `client_config` fulfilment figure (D1 weight 0.05) is a
   STATIC baseline only — it cannot move, so it can never signal compression. No weight×zone
   estimation (confident-wrong, same posture as approximate auto-COGS). Future cost-side
   detector = ONE uniform feed-agnostic build (3PL invoice OR Shopify-Shipping-Label) for all
   brands, Horizon-2, honoring the O-20 double-count trap. Known 3PL transitions ride the
   shared known-events layer (`brand_event_calendar`), narrated. Seed S20 mechanic
   (Month-15 / $3,950 / full-suppress) RETIRED. Regional/warehouse stockout is a zone-cost
   DRAG, not a suppression (G1 owns brand-wide out-of-stock-SKU spend). LOGGED seam: C10 /
   Alert 3 (Influencer ROI Truth) uses a destination-adjusted fulfilment cost that contradicts
   this lock → routed to C-series.

2. **Fulfilment estimated driver RETIRED from the live D1 alert (4 sites in agent_d).** The
   estimated `(fulfillment_cost_per_order − bau) × orders` driver, the blind-spot Step-3
   `× 1.15` test, the Known-Driver-Set entry, AND the "Disclosure Type 2 — Estimation flag"
   are all removed. Estimating fulfilment from carrier rates is the same confident-wrong error
   rejected for approximate auto-COGS, and a feed-only cost cannot move computed margin so
   cannot create a residual ("no residual to detect, we do not claim it"). Mirrored in
   tech-arch (weekly_cm cost list = feed-only; connector_gap_map note = direction not figure).
   Blind-spot Step 3 now mirrors Step 1: name fulfilment as a DIRECTION (never a figure) only
   for a trustworthy-MARGIN brand; no claim otherwise. **Note: this turned out to be 4 sites,
   not the 3 first scoped — the retired-wording scan caught the estimation-flag at the 4th.**

3. **Measured-not-explained rule — LOCKED.** A driver enters `total_measured_impact` iff it is
   MEASURED — explained, partly explained, or unexplained alike. Suppression removes a driver
   from the actionable RANKING, not from the sum; its measured dollars stay in, so an explained
   gap yields a SMALL residual, not a false blind-spot. Only feed-only INVISIBILITY (no-feed
   COGS; fulfilment) keeps a driver out of the sum, where it correctly becomes residual.
   "Explained" governs the alarm; "measured" governs the sum — orthogonal.

4. **All-explained two-door fire condition — LOCKED.** Firing needs BOTH (a) an acceptable
   residual (explainability) AND (b) at least one live, non-suppressed driver (actionability).
   A gap explained ENTIRELY by suppressed drivers has a near-zero residual but no actionable
   driver → narrate the seasonal story (or route to the suppressed-leak digest), do NOT fire.

5. **Universal go-quiet ceiling — LOCKED.** The brand-relative admissibility ceiling
   (0 admissible prior same-seasons → narrate only; 1 → State-2 max, never suppress; 2+ →
   State-3 suppress available) now caps EVERY component's silence (CPM, return-rate Stage 2,
   mix-shift) — previously only mix-shift had it. The S38 explained-away %/cut-offs (85%/60%,
   placeholders) become CONTEXT only, never the silence switch; they still feed S42 stacking /
   S39 learning. S42 stacking precedence must now key on the ceiling → O-18 / orchestration pass.

6. **Structural-break SIZE made brand-relative — LOCKED.** Replace the flat 5pp with a floored
   multiple of the brand's own weekly-CM volatility (same pattern as Trigger B's
   magnitude_threshold). The ≥21-day persistence DURATION is unchanged (confirming a permanent
   shift should be slow; measured on BAU days so event duration is irrelevant) but flagged to
   the O-26 audit.

7. **Pre-sale handling — LOCKED (Phase 1, NOT deferred).** Pre-sale awareness ramps (spend up,
   traffic up, conversion soft, no discount yet) were polluting the BAU baseline — none of the
   existing exclusions (event/echo/launch/influencer/peak) caught them — dragging the margin
   band DOWN and lowering the firing bar EVERYWHERE the baseline is read (Trigger A/B,
   structural break, seasonal). FIX (landed): add `pre_sale_ramp_active` to the BAU exclusion
   list + a one-time onboarding TWO-PASS BACKFILL (pass 1 detect ramps on raw history; pass 2
   rebuild baseline excluding them). Go-live gate D1-G13 added. The DETECTOR design and the
   new-product cost-collection mechanism are **Tier-2, held in full below** (fold into the
   specs when Gap 6 closes — avoids re-touching files mid-flight).

8. **Gap 1 component-only — ADOPTED as the WORKING ASSUMPTION (not yet a locked amendment).**
   No-trustworthy-cost brands get component signals only, no margin verdict, so they do not
   enter the residual machinery. Formal sign-off deferred to the D1 alert-language stage;
   enforcement is gate D1-G9. Recorded in product_strategy + cross_alert FLAGGED-PROPOSAL block.

---

## TIER-2 DESIGNS HELD IN FULL (fold into specs when Gap 6 closes — do NOT lose)

These are fully designed but intentionally NOT written into the specs yet, to avoid a second
pass over the same files before Gap 6 is closed. Build items D-GAP6-25 / D-GAP6-27 point here.

### A) Pre-sale ramp DETECTOR
- **What it detects:** a demand build-up window BEFORE a sale — spend up, sessions/traffic up,
  conversion rate soft, no discount yet — i.e. the awareness ramp that precedes the markdown.
- **Four signals** (read together, not any single one): (1) ad spend elevated vs BAU,
  (2) sessions/traffic elevated vs BAU, (3) conversion rate soft (down) despite the traffic,
  (4) discount depth NOT yet elevated (distinguishes a ramp from the sale itself).
- **Thresholds LEARNED from the brand's own past ramps**, NOT a k×volatility multiplier (that
  was rejected as a disguised constant). Reading the brand's ACTUAL past-ramp levels makes no
  distributional assumption — it asks "does this look like this brand's own prior ramps?"
- **Admissibility ladder gate** (same 0/1/2+ ceiling used elsewhere): a brand with too little
  ramp history to learn from is DISCLOSED, not silently trusted.
- **Two jobs:** (1) exclude the ramp window from the BAU baseline; (2) mark the window for D1
  **narrate-with-context** — default is a no-action context note that NEVER says "cut spend";
  escalates to "investigate, not cut" ONLY when extreme.
- **Sales are DATA-INFERRED**, never founder-declared: a sale = volume > median AND discount
  depth crosses its p50; the pre-sale window is detected BEFORE the sale via the demand
  build-up above.
- **Website crawling for sale dates REJECTED** (brittle). If exact scheduled-sale dates are
  ever needed, prefer structured Shopify scheduled-discount ingestion (Horizon-2), not crawling.
- **Onboarding two-pass backfill** (this part DID land as a build item / gate): pass 1 detect
  ramps on raw history; pass 2 rebuild the baseline excluding them — first baseline cannot be
  certified clean until ramps are excluded.

### B) New-product cost-collection mechanism
- **Burst-gate trigger:** fires on a drip + departure pattern (new-product publication arriving
  in a burst that departs from the brand's normal publication rhythm), brand-relative, NO fixed
  count.
- **Wave-crest debounce:** a staggered drop (e.g. 500 SKUs published over several days) is
  captured in ONE prompt at the crest, not as hundreds of pings.
- **Materiality = the burst itself**, NOT realized revenue — new products have ~0 revenue
  pre-sale, so realized revenue is the wrong yardstick. Inside the prompt, rank the missing-cost
  items by LIST PRICE (the best available proxy for what will matter once they sell).
- **Partial-but-scoped live alert:** a money-ranked fill prompt asking for the costs that will
  matter most first; the alert proceeds partially rather than blocking.
- **Describe-don't-suppress** for thin past coverage.
- **Trigger on new-product publication** (timed by the demand build-up / publication event).
- **85% cost-coverage gate NOT lowered:** new-collection products systematically lack cost, so
  a partial past season is a biased yardstick — keep the bar.

### C) Materiality math (new products, pre-sale)
- Because realized revenue ≈ 0 before the sale, materiality is the **publication burst**
  (count/velocity of new SKUs departing from rhythm), and the per-item ordering inside the fill
  prompt is by **list price**, not revenue. Once the products sell, normal revenue-weighting
  resumes.

### D) Off-critical-path / rejected (recorded so they aren't re-opened)
- **"Building-vs-burning" pre-sale advisory → Horizon-2 park.** Off the critical path, NOT
  data-blocked (historical ramps ARE available at onboarding). Revisit post-H.
- **Real-time safety net for a margin/discount bug during a novel sale → CONCLUDED UNBUILDABLE
  in Phase 1.** The separating variable is INTENT, which we do not capture; only a narrow
  "selling below known cost" check survives, and that is feed-gated. Do not re-attempt in
  Phase 1.

---

## CORRECTIONS LOGGED (own them, carry forward)
- **Fulfilment retirement was 4 sites, not 3.** The retired-wording scan (Check 4) caught the
  "Disclosure Type 2 — Estimation flag" as a 4th live site after the first three were handled.
  All four are now retired; the changelog stamp and Gap-6 status line say "4 sites."
- **tech-arch had two extra fulfilment leaks** beyond the agent_d sites: the `weekly_cm` cost
  list named "fulfilment costs" as included (now feed-only), and the connector_gap_map needed a
  direction-not-figure note. Both fixed. (Reinforces O-26: mirrors hide in non-obvious places.)
- **The estimation error generalises:** estimating fulfilment from carrier rates is the SAME
  confident-wrong failure as approximate auto-COGS. Feed-only is the honest posture for any cost
  we cannot see move.

---

## FILES UPDATED THIS SESSION (applied; replace in project)
- **agent_d_build_spec.md** — fulfilment retired (4 sites: driver, blind-spot Step 3, known-
  driver entry, estimation-flag); measured-not-explained rule + all-explained two-door (Pre-cond
  6); universal go-quiet ceiling (CPM Step 2) + return Stage-2 pointer; structural-break
  magnitude brand-relative; BAU pre-sale-ramp exclusion + onboarding backfill; operational-cost/
  S20 LOCK block; Gap 1 status line (component-only working assumption); Gap 6 status line;
  header stamp.
- **technical_architecture.md** — header stamp; qualifying-BAU-day `pre_sale_ramp_active`
  exclusion + onboarding two-pass backfill; structural-break SQL magnitude brand-relative;
  connector_gap_map direction-not-figure note; weekly_cm fulfilment feed-only.
- **cross_alert_orchestration.md** — header Updated line; C10/Alert-3 fulfilment-cost seam →
  C-series; FLAGGED-PROPOSAL component-only ADOPTED as working assumption; O-18 universal-ceiling
  stacking; O-24 residual-pass IN PROGRESS (locked items + new-vs-returning still open); O-26 +3
  audit items (launch-detector 5/7, structural-break 21-day duration, S38 placeholders); O-14
  master tracker tail; 2026-06-08 session-log entry (incl. building-vs-burning → Horizon-2).
- **pre_agent_build_checklist.md** — header stamp; D-12g magnitude brand-relative; D-16 Gap-6
  tracker; D-33 blind-spot step-3 revised; D-22 D4 cross-ref; new rows D-GAP6-24 (fulfilment
  retired), D-GAP6-25 (BAU pre-sale exclusion + backfill), D-GAP6-26 (structural-break magnitude),
  D-GAP6-27 (operational-cost/S20 feed-only).
- **product_strategy.md** — header stamp; Gap-1 component-only ADOPTED as working assumption;
  operational-cost/fulfilment feed-only scoping bullet (parallel to COGS).
- **d1_validation_gates.md** — header stamp; D1-G5 scope extended to the CPM explained-away path
  (universal ceiling); deferred-note updated; new GATE D1-G13 (BAU baseline excludes pre-sale
  ramps + onboarding backfill before D1 ships).

## FILES ADDED THIS SESSION
- **save_protocol.md** — UPGRADED earlier this session from 9 to **11 checks** (added Phase 0
  Decision Capture; Check 10 semantic read-back; Check 11 decision+routing landing reconciliation;
  original Checks 1–9 un-renumbered to preserve external "Check 8" refs). Present in outputs at
  149 lines. **Any "nine checks" reference in older files now means ELEVEN.**
- **state_2026_06_08_d1_gap6_residual_presale.md** — this file.
- **chat_context_2026_06_08_d1_gap6_residual_presale.md** — reasoning log.

**NOT edited (intentional):** seed_decisions_gap_f_g.md / seed_decisions_gap_d_e.md /
gap_abc_decisions.md (S-rule defs — parked for the orchestration pass); causal_graph.py and all
detector/SQL/transformer code (batched to the consolidated Claude Code prompt, post-H).

---

## SANITY HANDLES (post-edit line counts — next session's first check)
- agent_d_build_spec.md = **2710** (was 2635)
- technical_architecture.md = **3815** (was 3790)
- cross_alert_orchestration.md = **749** (was 723)
- pre_agent_build_checklist.md = **389** (was 385)
- product_strategy.md = **1416** (was 1415)
- d1_validation_gates.md = **383** (was 350)
- save_protocol.md = **149** (was 84 — upgraded to 11 checks)
If any updated file shows its OLD count, the wrong/older copy is mounted → STOP.

---

## D1 GAP STATUS
| Gap | Status |
|-----|--------|
| Gap 1 — COGS tier disclosure | LOCKED ✓ (component-only tightening ADOPTED 2026-06-08 as working assumption; formal sign-off at alert-language, gate D1-G9) |
| Gap 2 — Threshold (Trigger A + B) | LOCKED ✓ |
| Gap 3 — Causal decomposition | LOCKED ✓ |
| Gap 4 — CPM → margin intermediate steps | DESIGN-COMPLETE ✓ (blocked on schema gate D1-G1) |
| Gap 5 — AOV decline retired as a driver | LOCKED ✓ |
| Gap 6 — Seasonality suppression | **WIP** — dependencies + return-rate (Seam 2 + C3) + COGS/S21 CLOSED; discount-depth/S19 PARTIAL; **operational-cost/S20 CLOSED 2026-06-08**; **residual pass IN PROGRESS 2026-06-08** (7 Tier-1 calls locked); **new-vs-returning split + thin-baseline confidence STILL OPEN** |
| Gap 7 — "Entirely explained" framing retired | PENDING |
| Gap 8 — No action named per driver | PENDING |
| Gap 9 — No $ revenue impact (display) | PENDING |

---

## STILL OPEN IN GAP 6 (the only work left before Gap 6 closes)
1. **New-vs-returning customer return split** for a suppressed sale's downstream returns. A sale
   pulls in new customers who return more, so suppressing the discount component while firing on
   the returns residual would raise a naïve alarm. Split each return by the customer's OWN history
   (NOT sale-to-sale comparison — rejected; NOT a demand-weighted-discount heuristic — rejected at
   this tier). Caveat: both new- and returning-customer return rates rise during a sale, so the
   split tells you *who*, not whether the level is abnormal. (O-24 item a.)
2. **Thin-baseline confidence handling.** Below a brand-relative clean-day sufficiency bar, surface
   with a limited-history caveat at LOWER confidence — not silent, not full confidence. (O-24 item b.)

When both land, Gap 6 closes and the Tier-2 designs above get folded into the specs.

---

## NEXT SESSION STARTING POINT
New chat. Load: this file · save_protocol.md (now 11 checks) · agent_d_build_spec.md ·
technical_architecture.md · cross_alert_orchestration.md · product_strategy.md ·
d1_validation_gates.md · pre_agent_build_checklist.md · plus
chat_context_2026_06_08_d1_gap6_residual_presale.md.

**FIRST:** run save_protocol Phase B sanity handles on load (counts above). Confirm the project
copy of save_protocol.md is 149 lines (11 checks), not the old 84.
**THEN:** close Gap 6 — work the two O-24 items (new-vs-returning return split, then thin-baseline
confidence). These are cross-component, so they are genuinely residual-pass work.
**THEN:** fold the Tier-2 designs above (pre-sale detector, new-product cost collection, materiality
math) into agent_d + tech-arch + pre_agent, and run the post-Gap-6 design-consistency audit (O-26)
incl. the orphaned `margin_floor_pct` removal (O-25) and the three audit items added 2026-06-08.

After Gap 6: 7 → 8 → 9 → D1 alert language → D2 → D3 → D5 → D6 → C (incl. C10/Alert-3
fulfilment-cost reconciliation) → B → A → orchestration resolution pass → H → consolidated Claude
Code prompt.

**Post-Gap-6 (logged, do not pull forward):** O-26 full design-consistency audit + design-ownership
map (feeds save-protocol Check 8); C-series parked items; clustering-coherence validation factors;
the building-vs-burning advisory (Horizon-2).
