# Profit Sentinel — Session State
## Date: 2026-06-10
## Session: C3 returns-baseline FOUNDATION — defining "abnormal" and "big enough"

---

## READ-ME FIRST (honest scope of this file)

This is a **continuity file**, NOT a canonical save. The live link to the project
files dropped mid-session and the files are read-only in this environment, so the
**11-check save protocol was NOT run** (it operates on the canonical files; nothing
canonical was written this session). Canonical line-count handles are therefore
UNCHANGED: agent_d=2710, technical_architecture=3815, cross_alert=840,
product_strategy=1416, d1_validation_gates=386, pre_agent=389, save_protocol=149.

NEXT SESSION must: (1) reload canonical files + this file + the matching chat_context
file, (2) re-verify line counts, (3) write the AGREED items below into the canonical
files via the real 11-check save protocol. Until then, every "AGREED" item lives only
in these two continuity files.

Status labels used throughout:
- **AGREED** = explicitly signed off by Anupam in conversation; to be logged to
  canonical files next session. (Not yet "locked" in the ledger sense — nothing is.)
- **OPEN** = unresolved; each carries "what closes it."
- **OPEN-METHOD** = the *value* can wait for data, but the *method* to set it is itself
  unworked — this is design work, not a deferred number.
- **PARKED** = blocked on COGS (O-28); do not touch.
- **RETIRED** = a prior answer (mine, this session) that was reversed; recorded dead so
  it is not resurrected.

---

## THE ONE LOAD-BEARING OPEN ITEM (next session opens here)

**O1 — GROUPING METHOD. OPEN, LOAD-BEARING. Most important unresolved decision.**
How products are grouped is the foundation the entire return-alert spine stands on.
Anupam's concern, captured as raised (do not paraphrase away next session):
- Earlier sessions discussed an **LLM-based clustering** mechanism that used **return
  behaviour** to club products together. That now looks potentially **circular** — we
  would be forming the groups using the very signal (return behaviour) we then judge
  against.
- The **shared-return-reason-profile** coherence test agreed this session (A25) may be
  **too thin for small brands** — reason data coverage is uneven, and small brands may
  never have enough to judge coherence.
- Anupam's words: this is "by far the most important decision" in the thread because
  "a lot of downstream alerts depend on this" and "we can't go wrong here."

What O1 closes / unblocks: O2 (granularity), O3 (new-grouping & stability), O4 (thin-
history convergence), O6 (reason-profile mechanism), the grouping level inside A19/A29,
and the C3-headline retirement in O9. **Default assumption: the whole return-alert
definition is PROVISIONAL pending O1** (see "Provisional-pending-grouping" section).

---

## AGREED THIS SESSION (to log to canonical files next session)

### Period / sale handling (Foundation Q1 — core)
- **A1.** Period definition is **inherited, not new**. C3 reuses the existing
  data-derived event calendar ("Approach B"), O-23 (uncorroborated/one-off sale windows
  → narrate-don't-suppress), O-24a (NO sale-to-sale comparator — too context-sensitive),
  the three brand-relative tests (level / exposure / trajectory), and order-cohort keying
  (O-30). Q1's comparability worry **dissolves** into locked machinery; nothing invented.
  *(Provisional pending O1 — uses group/category.)*

### Anomaly / materiality definition (the heart of this session)
- **A18.** **Anomaly** = the group's return RATE is *clearly above its own robust
  historical band* (rarity-against-own-history). Robust band = middle-of-range (IQR-style
  percentiles), NOT mean/SD. *(Provisional pending O1.)*
- **A19.** **Trust gate** = the confidence band around the observed return rate
  (standard error = sqrt(rate*(1-rate)/orders)); the gate passes only when the
  *pessimistic end* of that band still sits above the top of the normal band. One test
  does **abnormality + data-sufficiency + maturity** at once. Inherently proportion-aware
  (thin data → wide band → fails on its own). An **absolute hard minimum** sits beneath it
  (one expensive return never fires alone). **Sales value never waives the trust gate.**
  Confidence-level width = strict pilot-start dial. *(Provisional pending O1 — grouping
  level.)*
- **A17.** **Materiality ("big enough to bother")** = EITHER return *volume* OR
  returned-order *sales value* crosses a brand-relative bar (either-or). Sits BEHIND the
  trust gate and the anomaly test; size alone never fires. *(Provisional pending O1.)*
- **A16.** Size the problem on **sales value, not cost** — order sale value is clean,
  complete, current; COGS misses SKUs and goes stale. **No cost dependency now or later**
  for this alert. (Caveat: a deep-discounted item under-sizes on sales value — conservative
  direction, accepted; the volume half of A17 catches the discounted-defect case.)
- **A30.** Trust gate is **proportion-aware** (returns relative to orders, via the
  confidence band of A19) — NOT a flat count. Handles slow brands and the luxury-coat
  low-volume-high-value case. *(Merged into A19; kept as a named anchor.)*
- **A21.** **Trajectory** = a *cohort return-RATE curve* (is this order-cohort's
  cumulative return rate still climbing deep into the window when it should taper) — NEVER
  an absolute count for the shape (absolute count is polluted by promotion timing). Sits
  behind an absolute size gate (A17). *(Provisional pending O1 for grain.)*
- **A22.** **New products (no history):** silent **watch — no alert** until a
  history-free signal crosses the size gate; then a **size/direction** alert worded
  honestly ("new, no normal yet; X returns on Y orders, still climbing — look before
  scaling spend"); full rate-vs-own-history machinery switches on once history exists.
  Narration order: **raw numbers first, founder's-own-language second, internal cluster
  never.** *(Provisional pending O1.)*
- **A29.** The **inside-the-group concentration check is load-bearing** (paired with
  grouping): real categories are Pareto-shaped, so a group average can look fine while one
  or two products drive the returns. *(Provisional pending O1.)*

### Grouping (what's agreed; mechanism is OPEN under O1)
- **A23.** **Peer groups for new products: DROPPED** (overengineering — new products are
  handled by A22; thin non-new products roll up the ladder A24).
- **A24.** **Coarser group = the brand's own product → style → type ladder** (built from
  Shopify's own structure). **Lower rungs (a product + its variants) trusted by
  construction**; merchandising/collection rungs are *candidates* needing validation.
- **A25.** Grouping coherence judged by **shared return-reason profile, NOT similar return
  rates** (rate-spread test RETIRED — categories are Pareto-shaped). Stay at the structural
  level when reason data is too thin to judge. *(Mechanism = O6, OPEN.)*
- **A26.** **Alert grain follows brand size**: small brands ($1.5–2M) read at
  collection/type level, not SKU level (a small brand has too few orders/product to clear
  the trust gate at SKU level — math: ~60 orders/product/year at $1.5M). Be upfront about
  this with founders.
- **A3.** **SKU-concentration is a first-class signal**: concentration-not-rate, gated by
  readable-minimum + exposure, run as a down-drill **even on in-band categories**
  (sharpens the open roll-up-grain item). *(Provisional pending O1.)*

### Contamination (bad past stretch inflating the benchmark)
- **A4.** Robust band by construction (CONFIRMED in agent_d: IQR percentile method by
  reference to the mix-shift seasonal grade; NO z-score/SD) + existing admissibility/
  season-count guards + **lean on the band-independent doors** (trajectory & exposure don't
  need the historical level) + **disclose the flat-sustained sliver** (the one case data
  alone can't fix). **NO founder onboarding question** (killed — CFO-led GTM, refine-not-
  gate). "Keep vs exclude" demoted to **minor** (A6). *(Provisional pending O1.)*

### Tuning / calibration
- **A5.** **No auto-exclusion at beta**: log fired events; never auto-reshape forward
  baselines; calibrate by deliberate human decision (O-31).
- **A27.** **Asymmetric tuning objective**: false alarms far costlier than misses. Freeze
  all sensitivity dials at pilot start; log every fire/near-fire/held-back + 7- and 14-day
  outcome; **loosen only on logged evidence, by deliberate human decision; never auto-tune
  the live system.**
- **A28.** **Calibration register + "won't-run-while-unset" rule** — principle/STRUCTURE
  locked now (a register lists every dial with what it controls, its setting-METHOD, the
  conservative/strict default, and a status flag; the alert cannot go live for a brand
  while any dial it depends on is "unset"). Detailed build scheduled with the pre-beta
  instrumentation pass. Register carries a per-dial **method status** (see dials below).

### Hardcoding cleanup
- **A2.** Echo-period **1.5× / 1.3×** constants → add to **O-26** (one-time consistency
  audit) hardcoded-constant cleanup list. (Anupam's orders-placed-cohort approach means C3
  itself introduces no new hardcoding; the 1.5/1.3 is a margin-baseline relic.)

### Connectors / data / GTM
- **A8.** **3PL: NOT in beta.** Demand-driven post-discovery (build the 1–2 connectors the
  real beta brands actually use; ShipBob/ShipHero have clean billing APIs but no native
  Airbyte connector). Add a **3PL/self-fulfil question to the Respondent.io discovery**.
- **A9.** **Supplier-credit connector: REJECTED** — off-platform (email/spreadsheets/debit
  notes/portals; claim window lives in the supplier contract). Surface the lever; don't
  track it.
- **A12.** **Agentic posture for beta = prepare the action, don't execute it** (assemble
  copy-paste/deep-linked actions; never auto-pause spend or pull SKUs). Supervised
  one-click execution = a Horizon-2 fork (different product bet).
- **A13.** **Cross-category common-cause = RETIRED as primary** (no detector exists;
  delivery-delay cause is invisible without 3PL). Ranking of simultaneous fires =
  top-one-or-two by exposure-and-open-lever + a single digest tail (O-19(E)). True common-
  cause synthesis = Horizon-2 (needs 3PL).
- **A14.** **Loop return-outcome field** (refund / exchange / store-credit / shop-now +
  exchange-target SKU) → ADD to `stg_loop_returns` (capability confirmed via Loop docs;
  currently NOT ingested — verified absence). Schema item for the engineering batch.
- **A15.** **Ad-platform product-data bundle** (one logged bundle, acted in engineering
  batch): (1) per-platform product-data fact sheet; (2) **Google synthetic seed is STALE**
  — it models PMAX as withholding product data, but the live Google Ads API now exposes
  per-product spend/conversions for Shopping AND PMAX (and expands to all campaign types
  2026-06-15) → refresh seed with product-level rows; (3) `campaign_sku_return_rate_7d`
  should READ Google (currently Meta+TikTok only); (4) "pause spend on a SKU" prepared
  action degrades gracefully — clean on Google/TikTok-Shop (per-SKU spend), NOT on Meta DPA
  (per-product spend is a black box; Meta gives product *conversions*, not spend). Honest
  scoping required in alert language.

### Principles / process (homes = product_strategy.md, at the principles pass)
- **A10.** **Refine-not-gate**: founder/CFO onboarding questions may *refine* the product,
  never *gate* core function (the Profit Audit must run data-only before a founder/CFO
  engages). → product_strategy.md at principles pass.
- **A11.** **Onboarding-question audit** → AFTER the causal graph; apply a running
  refine-not-gate filter to any new question proposed in the meantime.

---

## OPEN ITEMS (with what closes each + dependency order)

- **O1 — GROUPING METHOD (load-bearing).** See top of file. **Closes:** the grouping
  decision (LLM-clustering vs return-behaviour vs structural; circularity worry; small-
  brand thinness). **ROOT dependency — do first.**
- **O2 — Grouping granularity** (how finely to draw levels). Coupled to O1.
- **O3 — New-category / new-product-grouping rules + group stability over time**
  (Foundation Q4, Q5). Coupled to O1.
- **O6 — Reason-profile coherence MECHANISM** (how to measure "shared return-reason
  profile" + thin-data fallback). Coupled to O1.
- **O9 — GUARDED BUNDLE (cannot close as separate clean locks — found this session):**
  - **Lever-availability gate** = O-19(D). Guards required: visibility may only *promote*,
    never *suppress* (Meta per-SKU spend is a black box, so "no visible spend" ≠ "no
    spend"); defect-reason OR high-exposure overrides lever-absence; operate at variant
    grain. Asymmetric: surface-the-lever when invisible; digest only when genuinely nothing.
  - **Exposure hard-gate.** Guards required: pin exposure to **units or refund-revenue
    (COGS-independent), NOT margin-$** (else inherits the O-28 parking); state the
    fire-chain — full history: level OR trajectory; thin: exposure+trajectory; both
    unavailable: O-30 early/unconfirmed watch (no fire). Modulator (exposure lowers the
    anomaly bar) = post-beta; beta uses hard gate + rank-by-exposure only.
  - **C3 headline retirement (reconcile item a).** Retire the old "SKU return rate > 2×
    brand average" headline and wire C3 to the shared per-category baseline (S15) — but
    ONLY *together with* the SKU-concentration down-drill (A3) in place (else a single-hot-
    SKU regression window opens); coupled to reconcile item (b) = O4; and to O1 (S15's grain
    is unsettled until grouping resolves — sharing S15 guarantees C3 & D1 move together).
    **Preserve the old "sustained ≥7 days" persistence gate** — do not lose it in the swap.
  - **Dependency:** O9 needs O1 first (grouping/denominator). 
- **O4 — Thin-history fallback convergence (reconcile item b).** C3's thin-history
  behaviour (its old "90-day wait") must converge with the margin alert's exposure-test
  fallback. **Closes when** the exposure hard-gate (O9) + grouping (O1) are settled.
- **O5 — Return-band WINDOW** (rolling-recent vs same-season-anchored). Genuinely unpinned;
  the IQR method was borrowed from a once-a-year margin grade and return rate is observed
  continuously. Independent-ish of O1.
- **O7 — Recency-window dial METHOD** (how to derive "recent-enough orders" window from
  data). OPEN-METHOD (value deferred; method only sketched). Carried to next session per
  Anupam.
- **O8 — Size-gate fraction dial METHOD** (a fraction of *what* baseline, over *what*
  window; starting value is a deliberate human-set conservative judgment, not a computed
  number). OPEN-METHOD. Carried to next session per Anupam.

**Dependency order (no deadlock found if O1 goes first):**
O1 → O2 → O6 → O9 → O4 ; with O5, O7, O8 workable in parallel (largely grouping-
independent).

---

## PROVISIONAL-PENDING-GROUPING (inverted tag — assume contamination, whitelist the clean)

**Grouping-INDEPENDENT (safe regardless of O1):** A16, A27, A28, A14, A15, A8, A9, A10,
A11, A12, A2, A13, A23. (A21's *principle* is safe; its *grain* is not.)

**Grouping-DEPENDENT — PROVISIONAL until O1 closes:** A1, A3, A4, A17, A18, A19, A20,
A22, A24, A25, A26, A29 (and A21's grain). Most of the return-alert spine sits here.
**This is the honest, uncomfortable state: the bulk of the "abnormal/big-enough"
definition is provisional on a grouping decision that is still open.**

---

## RETIRED THIS SESSION (recorded dead — do NOT resurrect)
- **R1.** Four separate period bands (BAU/pre-sale/sale/post-sale) → replaced by
  event-calendar window + group-own-band.
- **R2.** Compare sale to prior comparable sales / build a "sale band" → retracted (O-24a:
  prior-sale comparator too context-sensitive).
- **R3.** Cross-sectional / leave-one-out common-shock category comparison → retracted as
  unnecessary (group-own-band + event window handle it).
- **R4.** Common-cause-first ranking → retracted (no detector; delivery invisible) →
  top-by-exposure + digest.
- **R5.** Rate-spread coherence test for grouping → dropped (categories Pareto-shaped) →
  shared-reason-profile (A25).
- **R6.** "Multiplier × spread" upper line for abnormal → replaced by rarity-against-own-
  history percentile (A18).
- **R7.** Flat absolute count floor → replaced by proportion-aware trust gate + hard
  minimum (A19/A30).
- **R8.** Cost/margin to size the return problem → replaced by sales value (A16).
- **R9.** Onboarding founder question (for contamination; for junk-grouping) → killed
  (CFO-led GTM; refine-not-gate A10).
- **R10.** Close lever-gate + exposure-gate + C3(a) as three clean separate locks →
  reversed to the guarded bundle O9.
- **R11.** Exposure modulator (lowers anomaly bar) → deferred post-beta; beta = hard gate +
  rank-by-exposure.
- **R12.** Per-product peer groups for new products → dropped (A23).

---

## UNVERIFIED-CLAIM REGISTER (believed but not fully file-confirmed — check before building)
- **U2.** Loop API exposes 4 outcomes + exchange-target SKU — web-confirmed, not file; build
  the ingestion (A14).
- **U3.** Google synthetic seed STALE vs live PMAX product reporting — web+file; needs seed
  refresh (A15). Candidate O-26 entry.
- **U4.** Exposure threshold inherits **O-19** (materiality floor, Gap 8) — O-19 calibration
  is itself OPEN.
- **U5.** Return-band IQR method borrowed from the once-a-year mix-shift seasonal grade and
  applied to a continuously-observed return rate — window transfer not pinned (= O5).
- **U6.** content_id coverage figures (Meta sales-only; TikTok 35/25/40; Google
  shopping-only/PMAX-withheld) are SYNTHETIC seed values — real-client coverage will differ
  (Google better, per U3).
- **U7.** ShipBob/ShipHero expose per-shipment cost via API; no native Airbyte connector —
  web-confirmed, not acted.

---

## CROSS-FILE PENDING EDITS (decisions obligating edits to files not opened this session)
- **X1. product_strategy.md** (principles pass): refine-not-gate (A10), prepare-not-execute
  (A12), demand-driven-connectors (A8).
- **X2. Discovery interview / Respondent.io**: add 3PL/self-fulfil question (A8).
- **X3. cross_alert_orchestration.md**: C3 reconcile (a)(b); O-19(D) lever-gate guards +
  evidence; echo 1.5/1.3 → O-26; ad-platform-product-data bundle as an item; Loop field as
  schema item; calibration register reference. (C3 close = TWO-FILE save with agent_d.)
- **X4. agent_d_build_spec.md**: C3 provisional-lock area (~line 2480); SKU-concentration
  into roll-up-grain; trust-gate/anomaly/materiality definitions; trajectory cohort-rate;
  new-product staging.
- **X5. technical_architecture.md**: Loop resolution-type field on `stg_loop_returns`;
  Google seed refresh (PMAX product rows); `campaign_sku_return_rate_7d` to read Google;
  calibration-register home.
- **X6. O-26 list**: echo 1.5/1.3; Google-seed-staleness candidate.

---

## PARKED (do not touch)
- **P1.** All cost/COGS work (O-28): the margin alert (D1 verdict), any margin/profit
  number, and margin-$ exposure. The return-alert definition above is deliberately built to
  be COGS-independent (counts + sales value only).

---

## CONFIDENCE / CONTENTION (firmness; * = Anupam pushed back and I reversed — watch for re-reversal)
- **High, hard to reopen:** A16*, A23*, A25*, A8*, A9*, A1, A18, A19, A21, A27, A28.
- **Medium, lightly held / refined late:** A17, A22, A24, A26, A3.
- **Settled by my reversal this session (* items + R-list):** treat as firm but flagged —
  R2, R3, R4, R5, R6, R7, R8, R9, R10, R11 were all reversals; A16/A23/A25 were Anupam-
  driven corrections of my errors.

---

## NEXT-SESSION START POINT (definition-of-done: a cold reader can resume from here)
1. Reload canonical files + this state file + chat_context_2026_06_10_c3_foundation_
   abnormal_bigenough.md. Re-verify line counts (handles above).
2. Write the AGREED items into canonical files via the full 11-check save protocol
   (two-file save for C3: cross_alert + agent_d). Clear the cross-file pending-edits (X1–X6)
   as their files come into scope.
3. **OPEN O1 FIRST — the grouping method** (LLM-clustering vs return-behaviour circularity;
   small-brand reason-thinness). Everything tagged "provisional pending O1" is unsafe to
   build until this resolves. Three passes, one item, explicit sign-off.
4. Then O2 → O6 → O9 (guarded bundle) → O4; O5/O7/O8 in parallel.
5. Remaining Foundation questions after Q1: Q2 (granularity = O2), Q3 (make abnormal/thin
   concrete — largely covered by this session's A-items, pending O1), Q4/Q5 (new grouping
   & stability = O3).
6. Then the rest of C3's sub-list → O-7 (returns ↔ influencer cohorts) → C10 → B → A →
   orchestration resolution → H → consolidated Claude Code prompt. D-series resumes only
   after O-28 unblocks COGS.
